from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from site_safety.adapters.base import CLIPAdapter, MLLMAdapter, SAM3Adapter
from site_safety.adapters.bridge import BridgeCLIPAdapter, BridgeSAM3Adapter
from site_safety.adapters.mock import MockCLIPAdapter, MockMLLMAdapter, MockSAM3Adapter
from site_safety.adapters.openai_compatible_mllm import OpenAICompatibleMLLMAdapter
from site_safety.pipeline.orchestrator import TrainingFreeInspector


def _env_value(name: str, fallback: str = "") -> str:
    return os.getenv(name, fallback)


def _build_openai_compatible_adapter(config: Dict[str, Any]) -> OpenAICompatibleMLLMAdapter:
    return OpenAICompatibleMLLMAdapter(
        api_key=_env_value(config["api_key_env"]),
        base_url=_env_value(config["base_url_env"]),
        model=_env_value(config["model_env"]),
        system_prompt=config.get("system_prompt", ""),
        timeout_seconds=float(config.get("timeout_seconds", 120)),
        temperature=float(config.get("temperature", 0.1)),
        use_response_format=bool(config.get("use_response_format", True)),
        payload_extra=config.get("payload_extra", {}),
        max_retries=int(config.get("max_retries", 2)),
        trust_env=bool(config.get("trust_env", True)),
    )


def build_report_adapter(
    config: Dict[str, Any],
    project_root: str | Path,
) -> Optional[MLLMAdapter]:
    load_dotenv(Path(project_root) / ".env")
    report_cfg = config.get("report_llm", {})
    if not report_cfg.get("enabled", False):
        return None
    if report_cfg.get("backend") == "openai_compatible":
        return _build_openai_compatible_adapter(report_cfg)
    raise ValueError(f"Unknown report LLM backend: {report_cfg.get('backend')}")


def build_inspector(config: Dict[str, Any], project_root: str | Path) -> TrainingFreeInspector:
    load_dotenv(Path(project_root) / ".env")
    mllm_cfg = config["mllm"]
    if mllm_cfg["backend"] == "mock":
        mllm: MLLMAdapter = MockMLLMAdapter()
    elif mllm_cfg["backend"] == "openai_compatible":
        mllm = _build_openai_compatible_adapter(mllm_cfg)
    else:
        raise ValueError(f"Unknown MLLM backend: {mllm_cfg['backend']}")

    sam_cfg = config["sam3"]
    if sam_cfg["backend"] == "mock":
        sam3: SAM3Adapter = MockSAM3Adapter()
    elif sam_cfg["backend"] == "bridge":
        sam3 = BridgeSAM3Adapter(
            module_name=sam_cfg["bridge_module"],
            class_name=sam_cfg["bridge_class"],
            init_kwargs=sam_cfg.get("init_kwargs", {}),
        )
    else:
        raise ValueError(f"Unknown SAM3 backend: {sam_cfg['backend']}")

    clip: Optional[CLIPAdapter] = None
    clip_cfg = config.get("clip", {})
    if clip_cfg.get("enabled", False):
        if clip_cfg.get("backend") == "mock":
            clip = MockCLIPAdapter()
        elif clip_cfg.get("backend") == "bridge":
            clip = BridgeCLIPAdapter(
                module_name=clip_cfg["bridge_module"],
                class_name=clip_cfg["bridge_class"],
                init_kwargs=clip_cfg.get("init_kwargs", {}),
            )
        else:
            raise ValueError(f"Unknown CLIP backend: {clip_cfg.get('backend')}")

    report_llm = build_report_adapter(config, project_root)

    return TrainingFreeInspector(
        config=config,
        mllm=mllm,
        sam3=sam3,
        clip=clip,
        report_llm=report_llm,
        project_root=project_root,
    )
