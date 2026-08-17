from pathlib import Path

import torch
from ultralytics import YOLO


def main() -> None:
    model_path = Path(
        r"D:\env\yolo_site_workspace\runs\train"
        r"\yolo26m_css_v28_baseline\weights\best.pt"
    )

    test_images = Path(
        r"C:\Users\yan1\Desktop\111"
    )

    if not model_path.exists():
        raise FileNotFoundError(f"找不到模型：{model_path}")

    if not test_images.exists():
        raise FileNotFoundError(f"找不到测试图片目录：{test_images}")

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA不可用。")

    model = YOLO(str(model_path))

    model.predict(
        source=str(test_images),
        imgsz=640,
        conf=0.25,
        iou=0.7,
        device=0,

        save=True,
        save_txt=True,
        save_conf=True,

        project=r"D:\env\yolo_site_workspace\runs\predict",
        name="yolo26m_css_v28_test_7",
        exist_ok=True,
    )


if __name__ == "__main__":
    main()