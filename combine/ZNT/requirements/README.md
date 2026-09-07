# requirement

本目录集中存放 Python 依赖清单，避免在多个地方找 `requirements.txt`。

## 文件

| 文件 | 用途 |
|------|------|
| `detect-bridge.txt` | 仅桥接服务（Mock 演示也够用） |
| `detect-full.txt` | 模式 2/3 完整检测（含 open_clip 等） |
| `../requirements.txt` | 根目录统一安装入口，转发到 `detect-full.txt` |
| `setup_env.bat` | 为真实检测创建完整 `env/`；Demo通常无需执行 |
| `check_weights.bat` | 检查权重是否放到位 |
| `preflight_check.py` | 自动识别环境、GPU、CUDA、模型路径并给出阻断项 |
| `deployment-manifest.json` | 可机读的推荐环境和模型清单 |
| `DEPLOYMENT_GUIDE.md` | 新部署者完整安装、下载、配置和验收指南 |
| `TESTED_ENVIRONMENT.md` | 当前实际跑通的软件、CUDA、GPU与模型组合 |

## 推荐

桌面版 1.1：优先双击交付包根目录 `SiteSafe-Sentinel.exe`，无需 Node 或另装基础 Python。展示素材开关位于“系统设置 → 工作台与展示”。下文 `npm` 与浏览器启动步骤只针对源代码开发，不是桌面展示的必需步骤。

> Windows 建议把交付包解压到短目录（如 `E:\ZNT_Submission`）。两层同名长目录可能使 `lxml` 安装或运行时掩码写入超过传统路径长度限制。

1. 只做Demo展示时，直接双击 **`start-platform.bat`** 并选择模式1；随包的 `python-runtime/` 已包含基础环境
2. PC前端依赖已随包提供；仅当目标电脑没有可用Node.js时才需安装 [Node.js LTS](https://nodejs.org/)
3. 真实检测再运行 **`部署助手.bat`**，根据提示准备Python/CUDA和外部模型
4. `setup_env.bat full` 会为真实检测创建 `env/`；它不会修改随包Demo运行时
5. Full 模式按 `DEPLOYMENT_GUIDE.md` 取得独立模型分卷，放置 Qwen、mmproj、SAM3 和项目 YOLO 权重
6. 在前端模型设置页更新路径并保存初始化配置
7. 再次运行 `部署助手.bat`，无 ERROR 后双击 **`start-platform.bat`**

## 展示素材与真实数据

当前交付版默认保留预编辑的八张案例、工地风险点、检测框与掩码，并与真实接口数据合并显示，便于没有模型或摄像头时完整展示系统能力。正式生产构建若只希望显示真实数据，请在构建 PC 前端前设置：

```bat
set VITE_ENABLE_PRESENTATION_ASSETS=false
cd pc-admin
npm run build
```

该开关只影响前端展示素材，不会改变业务数据库、YOLO、Qwen、SAM3 或 Agent 的真实链路。

## 本机已有 conda 环境 `torch` 时

不必重建 `env/`。`start-platform.bat` 会按顺序查找：

1. 仓库根目录 `env\Scripts\python.exe`（完整检测环境）
2. 随包 `python-runtime\python.exe`（Demo环境）
3. `D:\Anaconda\envs\torch\python.exe` 或系统 `python`

也可手动安装完整依赖：

```bat
D:\Anaconda\envs\torch\python.exe -m pip install -r requirements\detect-full.txt
```

## 关于 PyTorch / CUDA

`detect-full.txt` **不强制指定** torch 版本（避免装错 CPU/CUDA）。  
模式 2/3 需要本机已安装带 CUDA 的 PyTorch（你当前 `torch` 环境已满足）。  
只运行 Demo 时不需要安装Python、PyTorch或CUDA，直接使用随包 `python-runtime`。  
需要 Offline/Cloud 真实检测时，先按官方说明安装匹配自己显卡的 torch，再执行 `setup_env.bat full`。

## 模型文件交付边界

代码/演示压缩包保留八张案例、检测框、掩码和报告等展示证据，但**不包含模型权重**。Qwen、mmproj、SAM3、两套项目 YOLO 和可选 CLIP 通过独立模型分卷交付。部署助手会检查实际路径；没有模型分卷时只能选择 Demo，不能把预编辑结果当作新图片的真实推理结果。
