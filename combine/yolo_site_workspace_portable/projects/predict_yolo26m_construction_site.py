from __future__ import annotations

from pathlib import Path

import torch
from ultralytics import YOLO


def main() -> None:
    # 训练得到的最佳权重
    model_path = Path(
        r"D:\env\yolo_site_workspace\runs\train"
        r"\yolo26m_construction_site_640-2"
        r"\weights\best.pt"
    )

    # 要预测的图片目录
    test_images = Path(
        r"D:\env\yolo_site_workspace\datasets\ConstructionSite_export"
        r"\images\test"
    )

    # 预测结果输出目录
    project_dir = Path(
        r"D:\env\yolo_site_workspace\runs\predict"
    )

    run_name = "yolo26m_construction_site_visual"

    if not model_path.exists():
        raise FileNotFoundError(
            f"找不到模型权重：{model_path}\n"
            "请检查训练结果文件夹名称是否正确。"
        )

    if not test_images.exists():
        raise FileNotFoundError(
            f"找不到测试图片目录：{test_images}"
        )

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA不可用，请检查PyTorch、显卡驱动和PyCharm解释器。"
        )

    print("=" * 70)
    print(f"模型权重：{model_path}")
    print(f"预测图片：{test_images}")
    print(f"使用显卡：{torch.cuda.get_device_name(0)}")
    print(f"输出目录：{project_dir / run_name}")
    print("=" * 70)

    model = YOLO(str(model_path))

    results = model.predict(
        source=str(test_images),

        # 与训练分辨率保持一致
        imgsz=640,

        # 实际展示时的置信度阈值
        conf=0.25,

        # 非极大值抑制的IoU阈值
        iou=0.7,

        # 使用第0块GPU
        device=0,

        # 保存带框图片
        save=True,

        # 保存YOLO格式预测标签
        save_txt=True,

        # 在预测标签中保存置信度
        save_conf=True,

        # 是否保存裁剪后的目标
        save_crop=False,

        # 是否在框上显示类别名称和置信度
        show_labels=True,
        show_conf=True,

        # 结果目录
        project=str(project_dir),
        name=run_name,

        # 文件夹已存在时直接覆盖使用
        exist_ok=True,

        # 不在运行时弹出图片窗口
        show=False,

        verbose=True,
    )

    print("\n" + "=" * 70)
    print(f"预测完成，共处理 {len(results)} 张图片。")
    print(f"结果保存在：{project_dir / run_name}")
    print("=" * 70)


if __name__ == "__main__":
    main()