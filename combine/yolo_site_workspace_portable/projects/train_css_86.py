from pathlib import Path

import torch
from ultralytics import YOLO


def main() -> None:
    data_yaml = Path(
        r"D:\env\yolo_site_workspace\datasets"
        r"\css\data_css.yaml"
    )

    project_dir = Path(
        r"D:\env\yolo_site_workspace\runs\train"
    )

    if not data_yaml.exists():
        raise FileNotFoundError(f"找不到数据集配置文件：{data_yaml}")

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA不可用，请检查PyTorch和PyCharm解释器。")

    print(f"PyTorch版本：{torch.__version__}")
    print(f"CUDA版本：{torch.version.cuda}")
    print(f"训练显卡：{torch.cuda.get_device_name(0)}")
    print(f"数据配置：{data_yaml}")

    # 必须使用 .pt 预训练权重，而不是 .yaml 随机初始化
    model = YOLO("yolo26m.pt")

    model.train(
        data=str(data_yaml),

        # 基础训练设置
        epochs=100,
        imgsz=640,
        batch=-1,
        device=0,
        workers=2,

        # 优化器和学习率
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        cos_lr=True,

        # 早停与保存
        patience=20,
        save=True,
        save_period=10,

        # 数据增强：因为Roboflow已做重度离线增强，所以适当减弱
        mosaic=0.0,
        mixup=0.0,
        degrees=0.0,
        shear=0.0,
        perspective=0.0,
        translate=0.05,
        scale=0.20,
        fliplr=0.5,
        flipud=0.0,
        hsv_h=0.01,
        hsv_s=0.30,
        hsv_v=0.20,

        # 性能和复现
        amp=True,
        cache="disk",
        seed=0,
        deterministic=True,

        # 输出目录
        project=str(project_dir),
        name="yolo26m_css_v28_baseline",
        exist_ok=False,
        plots=True,
    )


if __name__ == "__main__":
    main()