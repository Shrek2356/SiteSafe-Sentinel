"""复盘学习Agent：接收人工确认、沉淀案例库、统计误报并生成班前交底材料。

边界：本Agent只写案例库与统计建议，不直接修改视觉结论；
阈值调整建议需人工在配置中生效（保持视觉层不可被下游改写的原则）。
"""
from __future__ import annotations

import json
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional

from site_safety.agents.schemas import CaseRecord, DetectionEvent, ThresholdProposal


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class ReviewLearningAgent:
    def __init__(self, case_library_path: str | Path) -> None:
        self.case_library_path = Path(case_library_path)
        self.case_library_path.parent.mkdir(parents=True, exist_ok=True)

    # ---------- 人工确认回流 ----------

    def ingest_confirmation(
        self,
        event: DetectionEvent,
        risk_id: str,
        verdict: Literal["confirmed", "rejected"],
        *,
        reviewer: str,
        comment: str = "",
        lessons: Optional[List[str]] = None,
    ) -> CaseRecord:
        finding = next((r for r in event.risks if r.risk_id == risk_id), None)
        if finding is None:
            raise ValueError(f"事件{event.event_id}中不存在风险{risk_id}")
        record = CaseRecord(
            case_id=f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
            event_id=event.event_id,
            risk_id=risk_id,
            risk_name_zh=finding.risk_name_zh,
            model_verified=finding.verified,
            model_confidence=finding.confidence,
            human_verdict=verdict,
            reviewer=reviewer,
            comment=comment,
            image_path=event.media.image_path,
            crop_path=finding.geometry.crop_path,
            recorded_at=_now_iso(),
            lessons=lessons or [],
        )
        with self.case_library_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.model_dump(), ensure_ascii=False) + "\n")
        # 回写事件复核状态
        event.review.status = verdict
        event.review.reviewer = reviewer
        event.review.reviewed_at = record.recorded_at
        event.review.comment = comment
        return record

    def load_cases(self) -> List[CaseRecord]:
        if not self.case_library_path.is_file():
            return []
        cases = []
        for line in self.case_library_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                cases.append(CaseRecord.model_validate(json.loads(line)))
        return cases

    # ---------- 统计与阈值建议 ----------

    def false_alarm_stats(self) -> Dict[str, dict]:
        """按risk_id统计模型verified结论被人工驳回的比例。"""
        stats: Dict[str, dict] = {}
        grouped: Dict[str, List[CaseRecord]] = defaultdict(list)
        for case in self.load_cases():
            if case.model_verified:
                grouped[case.risk_id].append(case)
        for risk_id, cases in grouped.items():
            rejected = sum(1 for c in cases if c.human_verdict == "rejected")
            stats[risk_id] = {
                "risk_name_zh": cases[0].risk_name_zh,
                "model_verified_count": len(cases),
                "human_rejected_count": rejected,
                "false_alarm_rate": round(rejected / len(cases), 3),
            }
        return stats

    def threshold_suggestions(self, *, false_alarm_threshold: float = 0.30) -> List[dict]:
        """误报率超阈值的风险给出建议（仅建议，不自动生效）。"""
        suggestions = []
        for risk_id, stat in self.false_alarm_stats().items():
            if (
                stat["model_verified_count"] >= 5
                and stat["false_alarm_rate"] >= false_alarm_threshold
            ):
                suggestions.append(
                    {
                        "risk_id": risk_id,
                        "risk_name_zh": stat["risk_name_zh"],
                        "false_alarm_rate": stat["false_alarm_rate"],
                        "suggestion": (
                            "误报率偏高：建议提高该风险最低确认置信度，或在风险目录中"
                            "细化其观察要点/干扰项描述后复测。"
                        ),
                    }
                )
        return suggestions

    def build_threshold_proposals(
        self,
        *,
        false_alarm_threshold: float = 0.30,
        min_samples: int = 5,
        exclude_risk_ids: Optional[set] = None,
    ) -> List[ThresholdProposal]:
        """把误报统计转成结构化阈值调整提案（pending状态，待人工审批）。

        建议值取"被驳回案例的最高模型置信度 + 0.05"（上限0.95）：
        使当前所有已知误报都会被降级转人工，同时尽量少伤真阳性。
        """
        exclude = exclude_risk_ids or set()
        rejected_conf: Dict[str, List[float]] = defaultdict(list)
        for case in self.load_cases():
            if case.model_verified and case.human_verdict == "rejected":
                rejected_conf[case.risk_id].append(case.model_confidence)
        proposals: List[ThresholdProposal] = []
        for risk_id, stat in self.false_alarm_stats().items():
            if risk_id in exclude:
                continue
            if (
                stat["model_verified_count"] < min_samples
                or stat["false_alarm_rate"] < false_alarm_threshold
            ):
                continue
            highest_rejected = max(rejected_conf.get(risk_id, [0.0]))
            proposed = round(min(0.95, highest_rejected + 0.05), 2)
            proposals.append(
                ThresholdProposal(
                    proposal_id=f"TP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
                    risk_id=risk_id,
                    risk_name_zh=stat["risk_name_zh"],
                    false_alarm_rate=stat["false_alarm_rate"],
                    sample_count=stat["model_verified_count"],
                    proposed_min_verified_confidence=proposed,
                    rationale=(
                        f"模型确认{stat['model_verified_count']}例中被人工驳回"
                        f"{stat['human_rejected_count']}例（误报率{stat['false_alarm_rate']:.0%}）；"
                        f"被驳回案例最高置信度{highest_rejected:.2f}，"
                        f"建议将该风险自动确认下限提高到{proposed:.2f}。"
                    ),
                    created_at=_now_iso(),
                )
            )
        return proposals

    # ---------- 班前安全交底 ----------

    def generate_briefing(
        self,
        events: List[DetectionEvent],
        *,
        title: str = "班前安全交底",
        recent_case_count: int = 5,
    ) -> str:
        """基于事件与案例库生成Markdown交底材料。"""
        confirmed_risk_counter: Counter = Counter()
        for event in events:
            for finding in event.risks:
                if finding.verified:
                    confirmed_risk_counter[finding.risk_name_zh] += 1
        cases = [c for c in self.load_cases() if c.human_verdict == "confirmed"]
        lines = [f"# {title}", "", f"生成时间：{_now_iso()}", ""]
        lines.append("## 近期高发风险")
        lines.append("")
        if confirmed_risk_counter:
            for name, count in confirmed_risk_counter.most_common(10):
                lines.append(f"- {name}：{count}次")
        else:
            lines.append("- 暂无已确认风险记录")
        lines.extend(["", "## 典型案例回顾", ""])
        if cases:
            for case in cases[-recent_case_count:]:
                lines.append(
                    f"- [{case.risk_name_zh}] {case.comment or '已人工确认'}"
                    + (f"（经验：{'；'.join(case.lessons)}）" if case.lessons else "")
                )
        else:
            lines.append("- 案例库暂无人工确认案例")
        lines.extend(
            [
                "",
                "## 今日重点提醒",
                "",
                "- 进入现场必须正确佩戴安全帽，高处作业系挂安全带并高挂低用；",
                "- 临边、洞口防护设施不得擅自拆除，发现缺失立即上报；",
                "- 吊装作业半径内严禁站人，服从信号工指挥；",
                "- 保持安全通道畅通，材料按平面布置图定点堆放。",
                "",
            ]
        )
        return "\n".join(lines)
