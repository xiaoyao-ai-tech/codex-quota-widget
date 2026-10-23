"""Render synthetic Qt previews and exercise window controls without account access."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".build/windows-previews"))
    parser.add_argument("--offscreen", action="store_true")
    args = parser.parse_args()
    if args.offscreen:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6.QtWidgets import QApplication
    from windows_glass import GlassWidget, PALETTES
    app = QApplication([])
    widget = GlassWidget(Path("synthetic-unused-home"), demo=True)
    try:
        args.output.mkdir(parents=True, exist_ok=True)
        widget.show()
        for theme in PALETTES:
            widget.theme = theme
            widget.apply_theme()
            widget.tick()
            app.processEvents()
            if not widget.grab().save(str(args.output / f"windows-{theme}.png")):
                raise RuntimeError("Could not save demo preview")
        widget.toggle_pin()
        widget.showMinimized()
        app.processEvents()
        widget.showNormal()
        app.processEvents()
        if widget.isMinimized() or widget.pinned:
            raise RuntimeError("Window restore/pin smoke check failed")
        print("3 synthetic previews and Qt window smoke checks passed")
    finally:
        widget.close()


if __name__ == "__main__":
    main()
