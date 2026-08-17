# 登录动画素材接口

将同一段静音、可循环的登录动画导出为以下文件名：

- `jr-safety-system.webm`：首选，建议 VP9/WebM；
- `jr-safety-system.mp4`：兼容回退，建议 H.264/MP4。

建议规格：16:9、1920×1080、24fps、约6秒。网页使用
`autoplay + muted + playsinline`播放一次，并在5.5秒处暂停保留完成画面。素材不存在或加载失败时，登录页会自动显示
嘉然静态图和六模块巡检动效，无需修改Vue代码。
