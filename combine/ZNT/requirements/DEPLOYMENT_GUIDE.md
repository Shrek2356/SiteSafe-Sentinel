# ZNT 新部署者智能引导与 Requirement

只做比赛展示时可直接运行 **`start-platform.bat`** 并选择 Demo：包内已经带好便携 Python、Node.js 和基础依赖，不需要安装软件或联网下载。只有配置 Offline/Cloud 真实检测时，才先运行 **`部署助手.bat`**；助手会检查 GPU、CUDA PyTorch、`llama-server` 和各模型路径。

## 1. 三种部署模式

| 模式 | 适用场景 | 必需组件 |
|---|---|---|
| Demo | 展会或无 GPU 电脑预览界面 | 随包便携运行时；不需要模型权重或另装 Python/Node |
| Offline | 数据不出本机，完整本地推理 | NVIDIA GPU、CUDA PyTorch、Qwen GGUF+mmproj、llama.cpp、两套 YOLO、SAM3 |
| Cloud | 使用更强在线 VLM，本地完成定位 | 多模态 API、NVIDIA GPU、CUDA PyTorch、两套 YOLO、SAM3 |

## 2. 推荐环境

| 项目 | 最低可尝试 | 推荐演示/开发 | 正式试点建议 |
|---|---:|---:|---:|
| 操作系统 | Windows 10 x64 | Windows 11 x64 | 固定补丁版本的 Windows/Linux 服务器 |
| Python | Demo 使用随包 3.12.10 | Demo 使用随包 3.12.10；真实检测推荐 3.10.x | 3.10.x 独立虚拟环境 |
| Node.js | Demo 使用随包版本 | Demo 使用随包版本 | 构建后静态部署，不在生产机常驻 Vite |
| CPU | 4 核 | 8 核以上 | 16 核以上 |
| 内存 | Demo 8 GB；Offline 32 GB | 32–64 GB | 64 GB 以上 |
| NVIDIA 显存 | Cloud 8 GB；Offline 12 GB | Offline 16 GB 以上 | L40S 48 GB、A100/H100 80 GB 等 |
| 可用磁盘 | 20 GB | 35 GB 以上 | 100 GB 以上并规划结果归档 |

12 GB 显存属于可尝试下限；Qwen、SAM3 和 YOLO 并发时可能触发显存不足。当前已验证基线为 Python 3.10、PyTorch 2.11+cu128、本地 8B Q4 模型和 RTX 5060 Ti。换机不要求版本逐字相同，但 CUDA 驱动、PyTorch 和显卡架构必须匹配。

## 3. 模型与运行时下载清单

### 3.1 本地 Qwen（Offline 必需）

- `Qwen3-VL-8B-Instruct-Q4_K_M.gguf`，当前文件约 4.68 GB。
- 与该 GGUF **同仓库、同修订版本配套**的 `mmproj-BF16.gguf`，当前文件约 1.08 GB。
- `llama-server.exe`，来自 llama.cpp Windows CUDA release，并加入 `PATH`。
- 不能把其他 Qwen 版本的 mmproj 与当前 GGUF 混用。
- 默认上下文为 8192、单 slot；修改模型后要重新执行八图回归，不应只凭接口能返回就认定兼容。

参考来源：

- Qwen GGUF：<https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-GGUF>
- llama.cpp：<https://github.com/ggml-org/llama.cpp/releases>

### 3.2 SAM3（Offline/Cloud 必需）

- SAM3 代码仓库目录，当前约 75 MB。
- `sam3.pt`，当前约 3.21 GB。
- 权重可能受许可证或访问审批约束；部署者需自行确认商用许可。
- 安装方式：先安装 CUDA PyTorch，再在项目环境执行 `python -m pip install -e <SAM3仓库路径>`。

参考来源：<https://github.com/facebookresearch/sam3>

### 3.3 两套 YOLO（Offline/Cloud 必需）

- `yolo26m_css_v28_baseline_best.pt`
- `yolo26m_construction_site_best.pt`

这是项目训练产物，不存在可保证同等效果的公共下载替代品。当前代码/演示压缩包不携带模型文件，由交付方通过**独立模型分卷**提供；部署者应核对文件名、大小与 SHA-256。缺少时只能使用 Demo，或在已配置 VLM 的情况下执行不含实时 YOLO 筛查的人工/周期全面审计，不能宣称实时链路完整。

### 3.4 CLIP（可选）

- `ViT-L-14.pt`，当前约 0.87 GB。
- 生产配置默认 `clip_enabled=false`，没有该文件不阻断主链。
- 仅在需要 ROI/Mask 语义一致性实验时启用，启用后应重新评估延迟和误报。

参考来源：<https://github.com/mlfoundations/open_clip>

## 4. 真实检测的软件依赖安装顺序

以下步骤仅用于 Offline/Cloud，不适用于开箱即用的 Demo：

1. 安装 NVIDIA 驱动，并确认 `nvidia-smi` 可运行。
2. 安装 Python 3.10 x64，创建独立 `env`。
3. 按 PyTorch 官方安装器选择匹配驱动的 CUDA 版 PyTorch：<https://pytorch.org/get-started/locally/>。
4. 执行 `python -m pip install -r requirements/detect-full.txt`。
5. 安装 SAM3：`python -m pip install -e <SAM3仓库>`。
6. 前端展示沿用随包 Node.js 与 `node_modules`，无需另外安装；二次开发时才建议安装 Node.js LTS。
7. 安装 llama.cpp CUDA 版，将 `llama-server.exe` 所在目录加入 `PATH`。
8. 放置模型权重，运行 `部署助手.bat`。
9. 在前端“模型规则配置 → 模型部件与运行时”选择真实路径并保存为初始化配置。
10. 执行 `start-platform.bat`，先做健康检查，再跑一张和八张示例回归。

也可以从 ZNT 根目录使用统一入口安装：

```bat
python -m pip install -r requirements.txt
```

## 5. 建议的交付目录

```text
ZNT/
├─ start-platform.bat
├─ 部署助手.bat
├─ python-runtime/                 # Demo随包运行时
├─ node-runtime/                   # 前端随包运行时
├─ requirements/
├─ detectmodel/Site_Safety_OpenRisk/
├─ pc-admin/
├─ models/                         # 可与代码包分卷交付
│  ├─ qwen/Qwen3-VL-8B-Instruct-Q4_K_M.gguf
│  ├─ qwen/mmproj-BF16.gguf
│  ├─ sam3/sam3.pt
│  ├─ yolo/yolo26m_css_v28_baseline_best.pt
│  ├─ yolo/yolo26m_construction_site_best.pt
│  └─ clip/ViT-L-14.pt             # 可选
└─ third_party/
   ├─ llama.cpp/
   └─ sam3-main/
```

模型权重必须作为独立分卷交付，并附 SHA-256 校验表和许可证说明；代码/演示 zip 本身不包含权重。不要把旧电脑的绝对路径当作新部署默认值；首次运行应通过前端路径选择器更新并保存初始化配置。

## 6. 前端配置与云端 API

- Offline：填写 Qwen GGUF、mmproj、本地 endpoint、SAM3 仓库/权重和 YOLO 权重路径。
- Cloud：在模型配置页选择云端模式，填写 OpenAI-compatible 多模态 endpoint、模型名和 API key；API key 不应写入源码或截图。
- Demo：只验证页面与 Mock 数据，不能作为真实检测结果。
- CLIP 通过独立开关启用；默认关闭不会影响当前主链。
- 当前比赛展示包默认合并包内预编辑案例、风险点、检测框和掩码；生产构建可设置 `VITE_ENABLE_PRESENTATION_ASSETS=false` 关闭这些展示素材。
- 换机后旧电脑绝对路径会被部署助手标记；在“模型规则配置”中执行自动发现、重新选择路径并保存初始化配置即可，不需要修改源码。

## 7. 部署验收

- `部署助手.bat` 无 ERROR。
- `http://127.0.0.1:8800/api/health` 返回正常。
- `http://127.0.0.1:8810/api/detect/health` 返回检测桥能力与模型状态。
- Qwen `/v1/models` 可访问；前端显示 Qwen 在线。
- 上传一张图能生成结构化风险报告；需要定位的风险能返回 overlay/mask。
- 第 8 张倒地人员能够证明 VLM 开放发现没有被 YOLO 训练类别封闭。
- 工单、通知、人工复核和规范检索能够从真实 DetectionEvent 继续运行。
- 记录 GPU、模型版本、配置哈希和结果目录，便于复现。

## 8. 常见阻断项

| 现象 | 优先检查 |
|---|---|
| 检测桥未启动 | Python 路径、FastAPI 依赖、8810 端口和 detect-8810 窗口日志 |
| Qwen 无法启动 | `llama-server.exe` 是否在 PATH、GGUF/mmproj 是否匹配、8080 端口 |
| `torch.cuda.is_available()` 为 False | 安装了 CPU 版 torch，或驱动与 CUDA wheel 不匹配 |
| SAM3 导入失败 | SAM3 仓库未 editable install、权重路径错误、依赖缺失 |
| CUDA OOM | 关闭 CLIP、避免并发、缩小上下文/ROI 数，或换更大显存 GPU |
| YOLO 不触发未知异常 | 正常设计；依赖周期性全面审计或 VLM 开放发现兜底 |
| 前端可开但无真实结果 | 可能处于 Demo/Mock；确认检测档位和 8810 health |
