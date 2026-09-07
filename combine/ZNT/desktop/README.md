# SiteSafe-Sentinel 独立桌面版

## 用户启动

`desktop-dist/SiteSafe-Sentinel.exe` 是独立窗口入口。它会：

1. 显示原生桌面窗口和启动页，不弹出浏览器。
2. 启动内嵌PC前端、8800业务后台和8810检测桥。
3. 默认使用Demo档，不需大模型权重。
4. 关闭窗口时停止由EXE启动的子服务和本地Qwen。

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
