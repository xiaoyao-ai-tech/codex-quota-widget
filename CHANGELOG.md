# 更新记录

**最近更新：2026-10-23（北京时间）**

## 尚未正式发布（Unreleased）

以下改动已合入源码，尚未发布带版本号的 GitHub Release 或通用安装包。按改进批次倒序记录，同日更新也分别列出。

| 更新日期 | 改进内容 | 带来的变化 | 详情 |
| --- | --- | --- | --- |
| 2026-10-23 | **新增 Windows 支持** | 提供 Qt 毛玻璃界面、可选 Tk 界面、三套配色和启动脚本；修复读取卡顿、超时与退出清理，状态存入用户目录。Windows / macOS CI 通过。 | [PR #2](https://github.com/xiaoyao-ai-tech/codex-quota-widget/pull/2) |
| 2026-10-23 | **调整 macOS 缓存位置** | 缓存移到用户 Application Support 目录，移动应用不再依赖源码位置；旧缓存保留、不自动导入，首次需联网刷新。Python 环境仍需保留。 | [PR #1](https://github.com/xiaoyao-ai-tech/codex-quota-widget/pull/1) |
| 2026-10-23 | **首次公开与项目规范整理** | 提供 macOS 额度、重置卡、倒计时与版本提示；修复退出进程残留、未知卡片误报和损坏安装检测；补齐 MIT 许可、隐私、贡献文档、源码打包与 CI。 | [项目说明](README.zh-CN.md) |

Windows 暂无托盘菜单和 Codex 版本提示；实机毛玻璃、高 DPI、多显示器等仍需验证。完整支持范围及限制见 [支持说明](docs/SUPPORT.md)，依赖许可见 [第三方依赖说明](THIRD_PARTY_NOTICES.md)。

后续每次改进增加一行并更新顶部日期；正式发布时，再按实际版本号和发布日期归档。应用包内部的 `1.0` / 构建号 `1` 不代表已经正式发布。
