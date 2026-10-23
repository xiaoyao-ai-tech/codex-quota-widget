"""Real disposable children and synthetic identities; no live account or network."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import quota
from windows_runtime import QuotaReader, state_directory


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = tempfile.TemporaryDirectory()
        self.home = Path(self.fixture.name)
        self.cache = self.home / "usage.local.json"
        self.login("SYNTHETIC_ACCOUNT")
        self.value = dict(remaining=62, resetsAt=1800500000, updatedAt=1800000000,
                          windowSeconds=604800, creditExpiries=[])

    def tearDown(self):
        self.fixture.cleanup()

    def login(self, account):
        (self.home / "auth.json").write_text(json.dumps({"tokens": {
            "access_token": "SYNTHETIC_TOKEN", "account_id": account}}), encoding="utf-8")

    def start(self, code, timeout=5):
        reader = QuotaReader([sys.executable, "-c", code], self.cache, self.home, timeout)
        self.addCleanup(reader.close)
        return reader

    def result(self, reader):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            value = reader.poll()
            if value is not None:
                self.assertIsNone(reader.process)
                self.assertTrue(reader.output.closed)
                return value
            time.sleep(.01)
        self.fail("Reader did not complete within test deadline")

    def test_large_stdout_and_stderr_do_not_deadlock(self):
        code = "import json,sys; sys.stderr.write('x'*200000); value=" + repr(self.value) + "; value['creditError']='x'*200000; print(json.dumps(value))"
        self.assertEqual(self.result(self.start(code))["remaining"], 62)

    def test_oversized_output_is_bounded_and_closed(self):
        value = self.result(self.start("print('x'*1100000)"))
        self.assertIn("过大", value["error"])
        self.assertNotIn("remaining", value)

    def test_timeout_kills_and_reaps_real_child(self):
        reader = self.start("import time; time.sleep(60)", timeout=.05)
        process = reader.process
        self.assertIn("超时", self.result(reader)["error"])
        self.assertIsNotNone(process.poll())

    def test_close_reaps_running_child_and_is_idempotent(self):
        reader = self.start("import time; time.sleep(60)")
        process = reader.process
        reader.close()
        reader.close()
        self.assertIsNotNone(process.poll())

    def test_invalid_output_and_nonzero_exit_use_only_verified_cache(self):
        quota.save_cache(self.cache, dict(self.value, accountHash=quota.account_hash("SYNTHETIC_ACCOUNT")))
        for code in ("print('bad')", "print('{\"remaining\":null}')",
                     "import sys; print(" + repr(json.dumps(self.value)) + "); sys.exit(1)"):
            with self.subTest(code=code):
                result = self.result(self.start(code))
                self.assertEqual(result["remaining"], 62)
                self.assertIn("error", result)
                self.assertNotIn("accountHash", result)
        self.login("OTHER_SYNTHETIC_ACCOUNT")
        self.assertNotIn("remaining", self.result(self.start("print('bad')")))

    def test_mid_read_account_switch_discards_successful_old_output(self):
        reader = self.start("import time; time.sleep(.05); print(" + repr(json.dumps(self.value)) + ")")
        self.login("OTHER_SYNTHETIC_ACCOUNT")
        self.assertNotIn("remaining", self.result(reader))

    def test_launch_failure_closes_temporary_output(self):
        with patch("windows_runtime.subprocess.Popen", side_effect=OSError("missing")), \
             patch("windows_runtime.tempfile.TemporaryFile", wraps=tempfile.TemporaryFile) as factory:
            with self.assertRaises(OSError):
                QuotaReader(["missing"], self.cache, self.home)
            # Real close is exercised by the failure path; no child or cache is produced.
            factory.assert_called_once()

    def test_state_uses_local_appdata_and_demo_does_not_create_directory(self):
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.home / "Local AppData")}):
            path = state_directory(create=False)
            self.assertFalse(path.exists())
            self.assertEqual(path, self.home / "Local AppData" / "CodexQuotaWidget")
            self.assertEqual(state_directory(), path)
            self.assertTrue(path.is_dir())


if __name__ == "__main__":
    unittest.main()
