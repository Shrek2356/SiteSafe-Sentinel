# SiteSafe-Sentinel 独立桌面版

当前版本 **1.3.0**。统一雾白／石墨蓝与青绿语义配色，优化导航、检测模式、案例、图表与明暗主题；保留 v1.2 的欢迎引导、搜索、本页指南和连接诊断。使用说明见 `../docs/桌面版v1.3视觉升级与使用指南.md`。

## 用户启动

`desktop-dist/SiteSafe-Sentinel.exe` 是独立窗口入口。它会：

1. 显示原生桌面窗口和启动页，不弹出浏览器。
2. 启动内嵌PC前端、8800业务后台和8810检测桥。
3. 默认使用Demo档，不需大模型权重。
4. 关闭窗口时停止由EXE启动的子服务和本地Qwen。

不会接管或关闭原先已运行的共享服务。修改 Python、模式或端口可在“系统设置 → 桌面与连接”完成，保存后重启。普通模型路径与 Qwen 启停仍在“模型规则配置”。

EXE不内置大模型、数据库和可变配置，必须与以下目录同级分发：

- `python-runtime/`
- `pc-admin/dist/`
- `detectmodel/Site_Safety_OpenRisk/`
- `desktop-settings.json`

系统不再依赖用户的Chrome/Firefox窗口，但Windows需有Microsoft Edge WebView2 Runtime。Windows 10/11和Microsoft 365设备通常已预装。

## 运行档位

编辑根目录`desktop-settings.json`：

- `demo`：Mock检测，无权重。
- `offline`：本地YOLO + Qwen + SAM3/CLIP。
- `standard`：云端视觉API + 本地SAM3/CLIP。

真实检测时，将`backend_python`改为已安装CUDA/PyTorch和完整检测依赖的Python路径。模型路径仍可在前端“模型规则配置”中修改。

## 开发调试

```powershell
desktop\.venv\Scripts\python.exe desktop\desktop_app.py --profile demo
```

## 重新构建

双击`desktop/build-desktop-exe.bat`。构建环境与业务运行环境分离，生成文件位于`desktop-dist/SiteSafe-Sentinel.exe`。构建会写入产品名称、版本号和应用图标；对外正式分发时如需消除 Windows SmartScreen 的“未知发布者”提示，还需要使用团队自己的代码签名证书签名。

先验证便携目录版，再考虑将所有资源压入单文件安装包。模型权重应始终外置，便于更新和不同GPU配置。

## 生成便携交付包

构建前端与 EXE 后，执行 `desktop/pack-release.ps1 -Destination <输出目录>`；脚本拒绝覆盖已有交付目录，并生成 SHA256 文件清单。本版包含源码、完整 `public` 素材及 `dist` 构建产物，不再以压缩包大小为优先约束。修改前端时在 `pc-admin` 安装开发依赖后构建；普通使用者无需这些操作。旧版精简包仍可用 `restore-frontend-assets.ps1` 恢复公共素材。
