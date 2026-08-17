from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from site_safety.factory import build_inspector
from site_safety.utils.config import load_yaml


def make_demo_image(path: Path) -> None:
    image = Image.new("RGB", (960, 640), (185, 190, 195))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 470, 960, 640), fill=(105, 105, 105))
    draw.rectangle((410, 290, 560, 580), fill=(60, 80, 130))
    draw.ellipse((445, 250, 525, 330), fill=(210, 170, 130))
    draw.rectangle((360, 120, 610, 235), fill=(145, 100, 55))
    draw.line((485, 0, 485, 120), fill=(30, 30, 30), width=8)
    image.save(path, quality=92)


def main() -> None:
    root = Path(__file__).resolve().parent
    image_path = root / "sample_data" / "demo_site.jpg"
    image_path.parent.mkdir(exist_ok=True)
    make_demo_image(image_path)
    config = load_yaml(root / "configs" / "default.yaml")
    config["mllm"]["backend"] = "mock"
    config["sam3"]["backend"] = "mock"
    config["clip"]["enabled"] = True
    config["clip"]["backend"] = "mock"
    inspector = build_inspector(config, root)
    result = inspector.inspect(image_path, root / "outputs" / "mock_demo")
    print("Mock demo completed:")
    print(root / "outputs" / "mock_demo" / "summary.md")
    print(result.final_report.overall_summary if result.final_report else "No final report")


if __name__ == "__main__":
    main()
