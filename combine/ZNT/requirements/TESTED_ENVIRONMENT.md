# 已验证环境快照

该文件用于告诉新部署者“什么组合已经实际跑通过”，不是强制锁死所有版本。

| 组件 | 已验证版本/配置 |
|---|---|
| 操作系统 | Windows 10/11 x64（本机 build 26200） |
| Python | 3.10.20 x64 |
| PyTorch | 2.11.0+cu128 |
| torchvision | 0.26.0+cu128 |
| CUDA runtime | 12.8 |
| GPU | NVIDIA GeForce RTX 5060 Ti 16 GB |
| FastAPI | 0.140.0 |
| Uvicorn | 0.51.0 |
| Pydantic | 2.13.4 |
| Ultralytics | 8.4.106 |
| OpenCV | 5.0.0 |
| OpenCLIP | 3.3.0 |
| Node.js | 24.14.0（开发机）；新部署优先 20/22 LTS |
| Qwen | Qwen3-VL-8B-Instruct Q4_K_M GGUF + BF16 mmproj |
| Qwen上下文 | 8192，单 slot |
| SAM3 | `sam3.pt`，CUDA 实际推理通过 |

## 兼容原则

- PyTorch、torchvision 和 CUDA 必须作为一组匹配，不要分别随意升级。
- Qwen GGUF 与 mmproj 必须来自同一模型版本和修订。
- 更换任一视觉模型、量化等级、上下文或推理后端后，至少重跑八张示例。
- 更换最终算法配置后，应重跑 58 张正样本与 40 张控制候选全量回归。
- Node 24 在当前开发机可用，但长期交付优先选择 LTS 版本。
