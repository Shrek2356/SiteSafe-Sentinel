"""ZNT deployment preflight and guided environment checker (stdlib only)."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DETECT_ROOT = ROOT / "detectmodel" / "Site_Safety_OpenRisk"
SETTINGS_PATH = DETECT_ROOT / "configs" / "runtime_initial_settings.json"
MANIFEST_PATH = Path(__file__).with_name("deployment-manifest.json")
REPORT_PATH = ROOT / "runtime" / "deployment_preflight.json"

BASE_DEPENDENCIES = {
    "fastapi": "FastAPI",
    "uvicorn": "Uvicorn",
    "multipart": "python-multipart",
    "dotenv": "python-dotenv",
    "httpx": "HTTPX",
    "psutil": "psutil",
    "yaml": "PyYAML",
    "pydantic": "Pydantic",
    "PIL": "Pillow",
    "numpy": "NumPy",
    "sklearn": "scikit-learn (RAG index)",
    "pypdf": "pypdf (PDF standards)",
    "docx": "python-docx (DOCX standards)",
}
FULL_DEPENDENCIES = {
    "cv2": "OpenCV",
    "ultralytics": "Ultralytics/YOLO",
}


def command_output(command: list[str]) -> str:
    executable = shutil.which(command[0])
    if executable:
        command = [executable, *command[1:]]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False)
        return (result.stdout or result.stderr or "").strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def version_tuple(text: str) -> tuple[int, ...]:
    values: list[int] = []
    for part in text.lstrip("v").split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        if not digits:
            break
        values.append(int(digits))
    return tuple(values)


def dependency_info(mode: str) -> dict[str, Any]:
    expected = dict(BASE_DEPENDENCIES)
    if mode in {"offline", "cloud"}:
        expected.update(FULL_DEPENDENCIES)
    missing = [label for module, label in expected.items() if importlib.util.find_spec(module) is None]
    return {"ready": not missing, "missing": missing, "checked": list(expected.values())}


def gpu_info() -> dict[str, Any]:
    query = command_output(
        ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"]
    )
    if not query:
        return {"available": False, "devices": []}
    devices = []
    for line in query.splitlines():
        parts = [item.strip() for item in line.split(",")]
        if len(parts) >= 3:
            devices.append(
                {"name": parts[0], "vram_mb": int(float(parts[1])), "driver": parts[2]}
            )
    return {"available": bool(devices), "devices": devices}


def torch_info() -> dict[str, Any]:
    try:
        import torch

        return {
            "installed": True,
            "version": str(torch.__version__),
            "cuda_build": str(torch.version.cuda),
            "cuda_available": bool(torch.cuda.is_available()),
        }
    except Exception as exc:  # the checker must survive a broken torch install
        return {"installed": False, "error": f"{type(exc).__name__}: {exc}"}


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else default
    except (OSError, ValueError, json.JSONDecodeError):
        return default


def resolve_model_path(value: str) -> Path:
    path = Path(os.path.expandvars(os.path.expanduser(value)))
    return path if path.is_absolute() else DETECT_ROOT / path


def collect(mode: str) -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH, {})
    settings = load_json(SETTINGS_PATH, {})
    gpu = gpu_info()
    torch = torch_info() if mode in {"offline", "cloud"} else {
        "installed": importlib.util.find_spec("torch") is not None,
        "cuda_available": False,
        "skipped": True,
        "note": "Demo mode does not require or initialize PyTorch/CUDA.",
    }
    dependencies = dependency_info(mode)
    node_text = command_output(["node", "--version"])
    npm_text = command_output(["npm", "--version"])
    disk = shutil.disk_usage(ROOT)
    physical_ram_gb = None
    try:
        import psutil

        physical_ram_gb = round(psutil.virtual_memory().total / 1024**3, 1)
    except Exception:
        pass

    model_checks: dict[str, Any] = {}
    for key, spec in manifest.get("models", {}).items():
        configured = str(settings.get(key) or "")
        path = resolve_model_path(configured) if configured else None
        exists = bool(path and (path.is_file() or (key == "sam3_repo_path" and path.is_dir())))
        required = mode in spec.get("required_for", [])
        model_checks[key] = {
            "label": spec.get("label", key),
            "configured": configured,
            "resolved": str(path) if path else "",
            "exists": exists,
            "required": required,
            "source": spec.get("source", ""),
        }

    sam_repo_value = str(settings.get("sam3_repo_path") or "")
    sam_repo = resolve_model_path(sam_repo_value) if sam_repo_value else None
    model_checks["sam3_repo_path"] = {
        "label": "SAM3 source repository",
        "configured": sam_repo_value,
        "resolved": str(sam_repo) if sam_repo else "",
        "exists": bool(sam_repo and sam_repo.is_dir()),
        "required": mode in {"offline", "cloud"},
        "source": "https://github.com/facebookresearch/sam3",
    }

    max_vram_gb = max((d["vram_mb"] for d in gpu["devices"]), default=0) / 1024
    # Demo 交付包固定使用已验证的 Python 3.12 便携运行时；完整 GPU 环境仍推荐 3.10。
    python_ok = sys.version_info[:2] in {(3, 10), (3, 12)}
    node_ok = bool(node_text) and version_tuple(node_text)[:1] in {(20,), (22,), (24,)}
    llama_server = shutil.which("llama-server") or shutil.which("llama-server.exe")
    issues: list[dict[str, str]] = []

    if dependencies["missing"]:
        issues.append({
            "level": "error",
            "message": "当前 Python 缺少依赖：" + ", ".join(dependencies["missing"])
            + "。请运行 requirements\\setup_env.bat 并选择对应模式。",
        })

    if not python_ok:
        issues.append({"level": "warning", "message": "请使用完整检测环境的 Python 3.10，或随包 Demo 的 Python 3.12 便携运行时。"})
    if not node_ok:
        issues.append({"level": "error", "message": "未找到可用 Node.js；推荐安装 Node.js 20/22 LTS。"})
    elif not npm_text:
        issues.append({"level": "error", "message": "Node.js 可用但 npm 不可用；请修复 Node.js 安装或 PATH。"})
    if mode in {"offline", "cloud"} and not torch.get("cuda_available"):
        issues.append({"level": "error", "message": "完整检测需要 CUDA 版 PyTorch，当前 Python 未检测到可用 CUDA。"})
    if mode == "offline" and max_vram_gb < 12:
        issues.append({"level": "error", "message": "本地离线模式建议至少 12 GB 显存，推荐 16 GB 以上。"})
    if mode == "cloud" and max_vram_gb < 8:
        issues.append({"level": "warning", "message": "云端视觉模式仍需本地运行 YOLO/SAM3，建议至少 8 GB 显存。"})
    if mode == "offline" and not llama_server:
        issues.append({"level": "error", "message": "未找到 llama-server.exe；本地 Qwen 无法由平台自动启动。"})
    if disk.free / 1024**3 < 20:
        issues.append({"level": "warning", "message": "剩余磁盘不足 20 GB；模型、环境和结果文件可能无法完整落盘。"})
    for check in model_checks.values():
        if check["required"] and not check["exists"]:
            issues.append({"level": "error", "message": f"缺少 {check['label']}：{check['resolved'] or '尚未配置'}"})

    if mode == "demo":
        recommendation = "演示模式可运行：无需模型权重和 NVIDIA GPU，只验证前端、业务后端与 Mock 链路。"
    elif mode == "cloud":
        recommendation = "云端视觉模式：配置兼容的多模态 API，同时在本地保留 YOLO、SAM3 和 CUDA PyTorch。"
    else:
        recommendation = "本地离线模式：Qwen GGUF + 匹配 mmproj + llama.cpp + YOLO + SAM3 全部在本机运行。"

    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": mode,
        "recommendation": recommendation,
        "system": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
            "python_executable": sys.executable,
            "node": node_text or None,
            "npm": npm_text or None,
            "ram_gb": physical_ram_gb,
            "disk_free_gb": round(disk.free / 1024**3, 1),
            "gpu": gpu,
            "torch": torch,
            "dependencies": dependencies,
            "llama_server": llama_server,
        },
        "models": model_checks,
        "issues": issues,
        "ready": not any(item["level"] == "error" for item in issues),
    }


def print_report(report: dict[str, Any]) -> None:
    system = report["system"]
    print("\n=== ZNT 新部署智能引导 ===")
    print(f"模式: {report['mode']}  |  {'可继续部署' if report['ready'] else '存在阻断项'}")
    print(report["recommendation"])
    print(f"Python: {system['python']}  ({system['python_executable']})")
    print(f"Node/npm: {system['node'] or '未安装'} / {system['npm'] or '未安装'}")
    print(f"内存/磁盘: {system['ram_gb'] or '未知'} GB / 剩余 {system['disk_free_gb']} GB")
    devices = system["gpu"]["devices"]
    print("GPU: " + ("; ".join(f"{d['name']} ({d['vram_mb']/1024:.1f} GB)" for d in devices) or "未检测到 NVIDIA GPU"))
    torch = system["torch"]
    if torch.get("skipped"):
        print("PyTorch: Demo 模式无需检查")
    else:
        print(f"PyTorch: {torch.get('version', '未安装')} | CUDA可用: {torch.get('cuda_available', False)}")
    dependencies = system["dependencies"]
    print("Python依赖: " + ("已就绪" if dependencies["ready"] else "缺少 " + ", ".join(dependencies["missing"])))
    print(f"llama-server: {system['llama_server'] or '未找到'}")
    print("\n模型与组件:")
    for check in report["models"].values():
        tag = "OK" if check["exists"] else ("缺失" if check["required"] else "可选未配")
        required = "必需" if check["required"] else "可选"
        print(f"  [{tag}] {check['label']} ({required})")
        if check["resolved"]:
            print(f"       {check['resolved']}")
        if not check["exists"] and check["source"]:
            print(f"       来源/说明: {check['source']}")
    print("\n诊断:")
    if report["issues"]:
        for item in report["issues"]:
            print(f"  [{item['level'].upper()}] {item['message']}")
    else:
        print("  未发现问题。可运行 start-platform.bat。")
    print("\n详细步骤: requirements\\DEPLOYMENT_GUIDE.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="ZNT deployment preflight")
    parser.add_argument("--mode", choices=["demo", "offline", "cloud"], default="offline")
    parser.add_argument("--save", action="store_true", help="save machine-readable report")
    args = parser.parse_args()
    report = collect(args.mode)
    print_report(report)
    if args.save:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n报告已保存: {REPORT_PATH}")
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
