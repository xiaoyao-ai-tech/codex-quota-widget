"""Shared Windows state and bounded reader lifecycle; no GUI dependency."""
import ctypes
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

import quota


def state_directory(create=True):
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    folder = base / "CodexQuotaWidget"
    if create:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


class InstanceLock:
    def __init__(self, enabled=True):
        self.handle, self.duplicate = None, False
        if os.name == "nt" and enabled:
            self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            self.kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
            self.kernel.CreateMutexW.restype = ctypes.c_void_p
            self.kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            self.kernel.CloseHandle.restype = ctypes.c_int
            ctypes.set_last_error(0)
            self.handle = self.kernel.CreateMutexW(None, False, "Local\\CodexQuotaWidgetWindows")
            if not self.handle:
                raise OSError("无法创建应用实例锁")
            self.duplicate = ctypes.get_last_error() == 183
            if self.duplicate:
                self.close()

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def valid_snapshot(value):
    if not isinstance(value, dict):
        return False
    if any(value.get(key) is not None and not isinstance(value[key], str)
           for key in ("error", "creditError")):
        return False
    if "remaining" not in value:
        return isinstance(value.get("error"), str)
    if not quota.finite_number(value["remaining"], 0, 100):
        return False
    if any(not quota.finite_number(value.get(key), 1, 253402300799)
           for key in ("resetsAt", "updatedAt")):
        return False
    cards = value.get("creditExpiries")
    return cards is None or (isinstance(cards, list) and
        all(quota.finite_number(item, 1, 253402300799) for item in cards))


class QuotaReader:
    """Poll a child without PIPE backpressure; only bounded output reaches the UI."""
    LIMIT = 1024 * 1024

    def __init__(self, command, cache, home, timeout=35):
        self.cache, self.home, self.timeout = cache, home, timeout
        self.process = None
        self.output = tempfile.TemporaryFile(mode="w+b")
        try:
            try:
                self.identity = quota.account_hash(quota.auth(home)[1])
            except quota.QuotaError:
                self.identity = None
            self.process = subprocess.Popen(command, stdout=self.output, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.started = time.monotonic()
        except Exception:
            self.output.close()
            raise

    def close(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.process.kill()
            # This reader launches no descendants and has no pipe handles to drain.
            self.process.wait(timeout=2)
            self.process = None
        self.output.close()

    def fallback(self, message):
        try:
            value = quota.read_cache(self.cache, self.home)
        except quota.QuotaError:
            value = {}
        value.pop("accountHash", None)
        value["error"] = message
        return value

    def poll(self):
        if self.process is None:
            return None
        code = self.process.poll()
        oversized = os.fstat(self.output.fileno()).st_size > self.LIMIT
        timed_out = code is None and time.monotonic() - self.started >= self.timeout
        if code is None and not (oversized or timed_out):
            return None
        try:
            if oversized or timed_out or code != 0:
                raise ValueError()
            self.output.seek(0)
            value = json.loads(self.output.read(self.LIMIT + 1).decode("utf-8"))
            if not valid_snapshot(value):
                raise ValueError()
            if "remaining" in value and (self.identity is None or
                    quota.account_hash(quota.auth(self.home)[1]) != self.identity):
                raise quota.QuotaError("Codex 账号已变化，请重新刷新")
            return {key: value[key] for key in ("remaining", "resetsAt", "updatedAt",
                    "creditExpiries", "creditError", "error") if key in value}
        except (ValueError, UnicodeError, quota.QuotaError):
            return self.fallback("读取超时，请重试" if timed_out else
                                 "读取输出过大，请重试" if oversized else "读取失败，请重试")
        finally:
            self.close()
