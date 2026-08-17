from pathlib import Path

import torch
from ultralytics import YOLO


def main() -> None:
    model_path = Path(
        r"D:\env\yolo_site_workspace\runs\train"
        r"\yolo26m_construction_site_640-2"
        r"\weights\best.pt"
    )

    data_yaml = Path(
        r"D:\env\yolo_site_workspace\datasets\ConstructionSite_export"
        r"\data_construction_site.yaml"
    )

    project_dir = Path(
        r"D:\env\yolo_site_workspace\runs\test"
    )

    if not model_path.exists():
        raise FileNotFoundError(f"找不到最佳权重：{model_path}")

    if not data_yaml.exists():
        raise FileNotFoundError(f"找不到数据配置：{data_yaml}")

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA不可用。")

    print("=" * 70)
    print(f"测试模型：{model_path}")
    print(f"数据配置：{data_yaml}")
    print(f"测试显卡：{torch.cuda.get_device_name(0)}")
    print("注意：当前验证集和测试集使用相同图片。")
    print("=" * 70)

    model = YOLO(str(model_path))

    metrics = model.val(
        data=str(data_yaml),
        split="test",

        imgsz=640,
        batch=8,
        device=0,
        workers=2,

        # 用于计算完整PR曲线和mAP
        conf=0.001,
        iou=0.7,

        plots=True,
        verbose=True,

        project=str(project_dir),
        name="yolo26m_construction_site_test",
        exist_ok=True,
    )

    print("\n" + "=" * 70)
    print("共享验证/测试集评价结果")
    print(f"Precision：{metrics.box.mp:.4f}")
    print(f"Recall：{metrics.box.mr:.4f}")
    print(f"mAP@0.5：{metrics.box.map50:.4f}")
    print(f"mAP@0.5:0.95：{metrics.box.map:.4f}")
    print("=" * 70)

    print("\n各类别 mAP@0.5:0.95：")

    for class_id, class_map in enumerate(metrics.box.maps):
        class_name = model.names[class_id]

        print(
            f"{class_id:2d} "
            f"{class_name:<30s} "
            f"{float(class_map):.4f}"
        )


if __name__ == "__main__":
    main()