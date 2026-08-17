# 工地安全智能检测与 Agent 协同平台——比赛提交版

## 项目定位

本系统构建“实时视觉初筛—MLLM开放风险识别—SAM3风险定位—证据核验—Agent闭环处置”的工地安全智能工作流。核心异常理解由多模态大模型完成，YOLO负责低成本注意力初筛，SAM3负责像素级定位，可选CLIP接口用于候选语义辅助；Agent系统负责推理、工单、规范检索和复盘学习。

## 快速启动

Windows 建议直接解压到短目录，例如 `E:\ZNT_Submission`。不要再套两层同名长目录，否则可能触发传统路径长度限制，导致依赖安装或运行时Mask写入失败。

1. 进入 `combine\ZNT`。
2. Demo展示已内置便携 Python、便携 Node.js、前后端基础依赖，可直接运行 `start-platform.bat` 并选择模式1；首次启动不会执行 pip/npm 下载。
3. 只有本地真实检测才需要运行 `部署助手.bat`，配置 CUDA 环境及外置模型权重。
4. 运行 `start-platform.bat`，选择演示、本地离线或云端模式。
5. 演示结束运行 `stop-platform.bat`。

比赛演示可直接使用包内八张案例，不需要重新运行模型。真实检测需在设置页配置本地模型路径或兼容的云端API。

详细部署要求见 `combine\ZNT\requirements\DEPLOYMENT_GUIDE.md`。
