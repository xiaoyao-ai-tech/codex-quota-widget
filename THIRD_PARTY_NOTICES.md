# Third-party dependencies / 第三方依赖

This repository's own code is licensed under MIT. Dependencies keep their own licenses.

本项目自身代码采用 MIT；第三方依赖及其组件保留自身许可证，MIT 不替代这些条款。

| Dependency | Use | License information |
| --- | --- | --- |
| PySide6-Essentials 6.12.0 | Windows default Qt interface | Installed package declares `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`; see [Qt for Python licensing](https://doc.qt.io/qtforpython-6/licenses.html) |
| shiboken6 6.12.0 | PySide6 runtime dependency | Distributed with Qt for Python; see its installed license files and [Qt for Python](https://doc.qt.io/qtforpython-6/) |
| Qt libraries and bundled components | GUI, fonts, platform integration | Component-specific terms; see [Qt licensing](https://doc.qt.io/qt-6/licensing.html) and the license files in the installed wheel |

Windows Qt dependencies are installed separately with pip; this repository does not bundle their binaries. macOS and Windows `--classic` do not require Qt. Tk, when used, is supplied by the Python installation and retains the Tcl/Tk license.

Windows 的 Qt 依赖由使用者通过 pip 单独安装；仓库不内置这些二进制。macOS 与 Windows `--classic` 不需要 Qt；Tk 由 Python 环境提供并保留 Tcl/Tk 许可证。

If distributing an application with Qt/PySide binaries, preserve the applicable license texts and notices and comply with the selected license, including replacement/relinking and source obligations where applicable. See Qt's [LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations). This project currently distributes source only; it provides no standalone Windows EXE or bundled Qt installer.

如果以后打包分发包含 Qt/PySide 的应用，需随包保留相应许可与声明，并核对所选许可证的替换、重新链接和源码提供等要求。当前仅提供源码，不发布独立 Windows EXE 或内置 Qt 的安装包。
