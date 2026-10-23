"""Offline reader lifecycle checks for the Qt UI; never reads real login data."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
HAS_QT = importlib.util.find_spec("PySide6") is not None
if HAS_QT:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from windows_glass import GlassWidget
    from quota import QuotaError


@unittest.skipUnless(HAS_QT, "Optional Windows Qt dependency is not installed")
class GlassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.material = patch("windows_glass.acrylic", return_value=False)
        self.material.start()
        self.folder = tempfile.TemporaryDirectory()
        self.paths = patch("windows_glass.state_directory", return_value=Path(self.folder.name))
        self.paths.start()
        self.widget = GlassWidget(Path("synthetic-home"), demo=True)
        self.widget.timer.stop()

    def tearDown(self):
        self.widget.close()
        self.material.stop()
        self.paths.stop()
        self.folder.cleanup()

    def test_demo_never_reads_private_files_or_spawns_reader(self):
        with patch("windows_glass.QuotaReader", side_effect=AssertionError("No reader in demo")), \
             patch("windows_glass.quota.auth", side_effect=AssertionError("No login in demo")), \
             patch("windows_glass.quota.read_cache", side_effect=AssertionError("No cache in demo")):
            widget = GlassWidget(Path("synthetic-home"), demo=True)
            widget.refresh()
            widget.tick()
            widget.close()
        self.assertIsNone(widget.reader)
        self.assertEqual(list(Path(self.folder.name).iterdir()), [])

    def test_reader_failure_clears_old_display(self):
        reader = MagicMock()
        reader.poll.return_value = {"error": "读取超时，请重试"}
        self.widget.reader = reader
        self.widget.poll_reader()
        self.assertIsNone(self.widget.reader)
        self.assertNotIn("remaining", self.widget.data)
        self.assertTrue(self.widget.refresh_button.isEnabled())

    def test_closing_reaps_active_reader_once(self):
        reader = MagicMock()
        self.widget.reader = reader
        self.widget.close()
        self.widget.close()
        reader.close.assert_called_once()
        self.assertIsNone(self.widget.reader)

    def test_theme_pin_and_minimize(self):
        self.widget.show()
        for _ in range(3):
            self.widget.cycle_theme()
            self.widget.tick()
        self.widget.toggle_pin()
        self.assertFalse(self.widget.pinned)
        self.widget.showMinimized()
        self.widget.showNormal()
        self.assertFalse(self.widget.isMinimized())

    def test_windows_single_instance_releases_after_close(self):
        if os.name != "nt":
            self.skipTest("Native Windows mutex requires Windows")
        from windows_runtime import InstanceLock
        first = InstanceLock()
        try:
            self.assertFalse(first.duplicate)
            second = InstanceLock()
            self.assertTrue(second.duplicate)
        finally:
            first.close()
        third = InstanceLock()
        try:
            self.assertFalse(third.duplicate)
        finally:
            third.close()


if __name__ == "__main__":
    unittest.main()
