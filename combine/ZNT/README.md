# 筑安智巡 · SiteSafe-Sentinel

本目录是平台的应用根目录。当前 `main` 中的 **PC 前端版本为 1.5.3**；公开 Windows 安装版仍为 **v1.5.2**。项目介绍、下载与源码快速启动见[仓库首页](../../README.md)。

详细的模型分工、数据流程和操作入口见[系统架构与使用说明](./docs/系统架构与使用说明.md)。

## 选择你的使用方式

| 来源／用途 | 启动方式 |
|------------|----------|
| GitHub Releases 安装版 | 下载 v1.5.2 EXE，安装后使用桌面快捷方式 |
| 完整便携交付包 | 完整解压后，双击包根目录 `SiteSafe-Sentinel.exe` |
| 已完成本地构建的源码 | 从本目录打开 `desktop-dist/SiteSafe-Sentinel.exe` |
| 从源码体验演示 | 按[仓库首页的源码步骤](../../README.md#源码演示)安装依赖，在本目录运行 `start-sitesafe-demo.bat` |
| 源码浏览器兼容入口 | 从本目录运行 `start-platform.bat`；需先准备运行依赖 |
| 仅开发前端页面 | `pc-admin/` 中运行 `npm ci`、`npm run dev`；不自动启动后台 |

GitHub 源码包不包含已构建 EXE 和前端 `dist`。仓库里的基础 Python 文件也不等于完整业务依赖环境；从源码开发需要安装依赖。完整桌面交付包则提供 Demo 运行环境，不需要系统 Node、GPU 或模型。

## 主要模块

| 目录 | 内容 |
|---|---|
| `pc-admin/` | 深蓝工业／黑白水墨主题工作台、三维工地、检测与处置界面 |
| `detectmodel/Site_Safety_OpenRisk/` | 检测桥、开放风险管线、业务接口、规范检索与 Agent |
| `desktop/` | Windows 窗口、服务生命周期、桌面构建及安装包装 |
| `big-screen/`、`mobile/` | 大屏与移动端源码，分别安装依赖和启动 |
| `requirements/` | 演示与真实检测环境、模型配置、部署自检 |

## 运行与配置

关闭旧版窗口后再启动新版，避免全局单实例或端口冲突。桌面默认配置是 `desktop-settings.json`，服务默认端口为前端 5173、业务 8800、检测桥 8810。

先查看预置案例可直接进入“检测结果汇总”。新图片真实检测需要另行准备完整 Python、推理引擎及模型权重；从“系统设置 → 桌面与连接”和“模型规则配置”更新本机路径与服务配置。不要把开发者电脑的路径作为固定部署路径。

## 文档

- [v1.5.2 更新与升级说明](./docs/桌面版v1.5.2更新说明.md)
- [版本变更记录](../../CHANGELOG.md)
- [桌面开发、构建与打包](./desktop/README.md)
- [环境与模型依赖](./requirements/README.md)
- [完整部署指南](./requirements/DEPLOYMENT_GUIDE.md)
- [接口对接指南](./docs/对接指南.md)
- [YOLO－VLM－前端整合](./docs/YOLO-VLM-前端接口整合说明.md)

## License

本项目为**源码可见的专有软件，并非开源软件**。获得仓库访问权限仅限于非商业评估、比赛评审和内部测试，不自动授予公开、修改、再分发、生产部署、商业使用、模型训练或竞品开发权利。

完整授权条款见仓库根目录的 [`LICENSE`](../../LICENSE)，第三方组件说明见 [`THIRD_PARTY_NOTICE.md`](../../THIRD_PARTY_NOTICE.md)。第三方框架、模型、数据、字体、图片、角色素材及商标仍归各自权利人所有。
