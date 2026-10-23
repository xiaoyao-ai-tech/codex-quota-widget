"""Offline Windows display and reader lifecycle regressions; synthetic data only."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from windows_widget import Widget, countdown, presentation, reader_command
from quota import QuotaError, account_hash


class WindowsTests(unittest.TestCase):
    def data(self, **fields):
        return dict(remaining=60, resetsAt=1800500000, windowSeconds=604800,
                    updatedAt=1800000000, creditExpiries=[], **fields)

    def test_expired_window_never_assumes_restored_quota(self):
        value = presentation(self.data(), 1800500001)
        self.assertEqual(value["percent"], "60%")
        self.assertIn("历史", value["budget"])
        self.assertIn("确认", value["reset"])

    def test_unknown_cards_and_missing_quota_are_not_zero(self):
        self.assertEqual(presentation({}, 1800000000)["percent"], "—")
        value = self.data()
        value["creditExpiries"] = None
        self.assertIn("未知", presentation(value, 1800000000)["cards"])
        self.assertIn("无可用卡", presentation(self.data(), 1800000000)["cards"])

    def test_stale_and_failed_reads_disable_daily_budget(self):
        self.assertIn("历史", presentation(self.data(), 1800000181)["budget"])
        self.assertIn("历史", presentation(self.data(), 1799999939)["budget"])
        value = self.data(error="network")
        self.assertIn("历史", presentation(value, 1800000000)["budget"])

    def test_expired_cards_excluded_and_urgent_cards_flagged(self):
        value = self.data()
        value["creditExpiries"] = [1799999999, 1800000100]
        display = presentation(value, 1800000000)
        self.assertIn("1 张", display["cards"])
        self.assertTrue(display["urgent"])
        self.assertEqual(countdown(-1), "0天 00:00:00")

    def test_cli_custom_home_reads_same_account_cache_without_network(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            (home / "auth.json").write_text(json.dumps({"tokens": {
                "access_token": "SYNTHETIC_TOKEN", "account_id": "SYNTHETIC_ACCOUNT"}}), encoding="utf-8")
            cache = home / "usage.local.json"
            cache.write_text(json.dumps(self.data(accountHash=account_hash("SYNTHETIC_ACCOUNT"))), encoding="utf-8")
            command = reader_command(cache, home)
            command.remove("--refresh")
            result = subprocess.run(command, capture_output=True, check=True)
            value = json.loads(result.stdout)
            self.assertEqual(value["remaining"], 60)
            self.assertNotIn("accountHash", value)
            self.assertNotIn(b"SYNTHETIC", result.stdout)

    def test_invalid_display_payload_does_not_crash_timer(self):
        for value in (None, [], {"remaining": None}, {"remaining": 4},
                      dict(self.data(), remaining=float("nan")),
                      dict(self.data(), creditExpiries=["bad"]),
                      dict(self.data(), error=[])):
            with self.subTest(value=value):
                self.assertEqual(presentation(value, 1800000000)["percent"], "—")
        value = dict(self.data(), resetsAt=253402300799)
        self.assertIn("60%", presentation(value, 1800000000)["percent"])

    def test_card_thresholds(self):
        for seconds, urgent, critical in ((86400, False, False), (10800, True, False), (10799, True, True)):
            value = dict(self.data(), creditExpiries=[1800000000 + seconds])
            display = presentation(value, 1800000000)
            self.assertEqual((display["urgent"], display["critical"]), (urgent, critical))

    def test_closing_reaps_reader_once(self):
        widget = Widget.__new__(Widget)
        widget.reader = MagicMock()
        reader = widget.reader
        widget.root, widget.instance = MagicMock(), MagicMock()
        widget.demo, widget.closed = True, False
        widget.close()
        widget.close()
        reader.close.assert_called_once()
        self.assertIsNone(widget.reader)
        widget.root.destroy.assert_called_once()


@unittest.skipUnless(os.name == "nt", "Native Tk smoke test requires Windows")
class TkSmokeTests(unittest.TestCase):
    def test_demo_controls_and_exit_without_private_state(self):
        import tkinter as tk
        with tempfile.TemporaryDirectory() as folder, \
             patch("windows_widget.state_directory", return_value=Path(folder)), \
             patch("windows_widget.quota.auth", side_effect=AssertionError("No login in demo")):
            root = tk.Tk()
            widget = Widget(root, Path("synthetic-home"), demo=True)
            try:
                root.update()
                widget.cycle_theme()
                widget.toggle_pin()
                root.iconify()
                root.update()
                root.deiconify()
                root.update()
                self.assertIsNone(widget.reader)
                self.assertEqual(list(Path(folder).iterdir()), [])
            finally:
                widget.close()


if __name__ == "__main__":
    unittest.main()
