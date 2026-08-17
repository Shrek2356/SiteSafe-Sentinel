from pathlib import Path

import torch
from ultralytics import YOLO


def main() -> None:
    # 训练得到的最佳权重
    model_path = Path(
        r"D:\env\yolo_site_workspace\runs\train"
        r"\yolo26m_css_v28_baseline\weights\best.pt"
    )

    # 数据集配置文件
    data_yaml = Path(
        r"D:\env\yolo_site_workspace\datasets"
        r"\css\data_css.yaml"
    )

    # 测试结果输出目录
    project_dir = Path(
        r"D:\env\yolo_site_workspace\runs\test"
    )

    if not model_path.exists():
        raise FileNotFoundError(f"找不到模型权重：{model_path}")

    if not data_yaml.exists():
        raise FileNotFoundError(f"找不到数据配置文件：{data_yaml}")

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA不可用，请检查PyTorch和PyCharm解释器。")

    print("=" * 70)
    print(f"测试模型：{model_path}")
    print(f"数据配置：{data_yaml}")
    print(f"PyTorch版本：{torch.__version__}")
    print(f"CUDA版本：{torch.version.cuda}")
    print(f"测试显卡：{torch.cuda.get_device_name(0)}")
    print("=" * 70)

    model = YOLO(str(model_path))

    metrics = model.val(
        data=str(data_yaml),

        # 使用data_css.yaml中的test划分
        split="test",

        # 与训练保持一致
        imgsz=640,

        # 测试批量，显存不足时改为4
        batch=8,
        device=0,
        workers=2,

        # 低阈值用于计算完整PR曲线和mAP
        conf=0.001,
        iou=0.7,

        # 输出图表
        plots=True,
        verbose=True,

        # 保存目录
        project=str(project_dir),
        name="yolo26m_css_v28_test",
        exist_ok=True,
    )

    print("\n" + "=" * 70)
    print("总体测试结果")
    print(f"Precision：{metrics.box.mp:.4f}")
    print(f"Recall：{metrics.box.mr:.4f}")
    print(f"mAP@0.5：{metrics.box.map50:.4f}")
    print(f"mAP@0.5:0.95：{metrics.box.map:.4f}")
    print("=" * 70)

    # 输出各类别mAP@0.5:0.95
    print("\n各类别 mAP@0.5:0.95：")
    for class_id, class_map in enumerate(metrics.box.maps):
        class_name = model.names[class_id]
        print(f"{class_id:2d} {class_name:<20s}: {class_map:.4f}")


if __name__ == "__main__":
    main()