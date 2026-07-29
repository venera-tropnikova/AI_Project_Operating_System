#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI POS Capture Service (MVP).

Technology-neutral façade for listing windows and capturing a window image.
The first Windows backend uses tools/capture_window.ps1. Local Bridge depends
only on this module, not on PowerShell directly.

Does not accept tasks. Does not write history.json.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any, Protocol

RESULT_PREFIX = "AI_POS_CAPTURE_RESULT="
TOOLS_DIR = Path(__file__).resolve().parent
DEFAULT_PS_ADAPTER = TOOLS_DIR / "capture_window.ps1"

_CAPTURE_LOCK = threading.Lock()


class CaptureBackend(Protocol):
    def list_windows(self, *, exclude_title: str = "") -> dict[str, Any]:
        ...

    def probe_window(self, hwnd: str) -> dict[str, Any]:
        ...

    def capture_window(self, hwnd: str, output_path: Path) -> dict[str, Any]:
        ...


def _simple(*, ok: bool, message: str | None = None, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": bool(ok), "message": message}
    payload.update(extra)
    return payload


def find_powershell() -> str | None:
    system_root = os.environ.get("SystemRoot") or "C:\\Windows"
    builtin = (
        Path(system_root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    )
    if builtin.is_file():
        return str(builtin)
    return shutil.which("powershell")


def parse_capture_result(stdout: str) -> dict[str, Any] | None:
    for line in reversed((stdout or "").splitlines()):
        line = line.strip()
        if line.startswith(RESULT_PREFIX):
            raw = line[len(RESULT_PREFIX) :]
            if raw == "FILE":
                return {"ok": True, "_file_marker": True}
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return None
            return data if isinstance(data, dict) else None
    return None


class UnavailableCaptureBackend:
    """Backend used when capture is not available on this OS."""

    def list_windows(self, *, exclude_title: str = "") -> dict[str, Any]:
        return _simple(
            ok=False,
            message="Снимок окна на этой системе пока недоступен.",
            windows=[],
        )

    def probe_window(self, hwnd: str) -> dict[str, Any]:
        return _simple(
            ok=False,
            available=False,
            message="Снимок окна на этой системе пока недоступен.",
        )

    def capture_window(self, hwnd: str, output_path: Path) -> dict[str, Any]:
        return _simple(
            ok=False,
            message="Снимок окна на этой системе пока недоступен.",
        )


class PowerShellCaptureBackend:
    """First Windows implementation of Capture Service."""

    def __init__(self, script_path: Path | None = None) -> None:
        self.script_path = script_path or DEFAULT_PS_ADAPTER

    def _run(self, args: list[str]) -> dict[str, Any]:
        if os.name != "nt":
            return _simple(ok=False, message="Снимок окна доступен только в Windows.")
        if not self.script_path.is_file():
            return _simple(ok=False, message="Не удалось выполнить снимок. Повторите попытку.")
        powershell = find_powershell()
        if powershell is None:
            return _simple(ok=False, message="Не удалось выполнить снимок. Повторите попытку.")

        import tempfile

        # mkstemp leaves the file open; on Windows that blocks PowerShell writes.
        fd, result_name = tempfile.mkstemp(prefix="ai_pos_capture_", suffix=".json")
        os.close(fd)
        result_file = Path(result_name)
        cmd = [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.script_path),
            *args,
            "-ResultPath",
            str(result_file),
        ]
        with _CAPTURE_LOCK:
            try:
                completed = subprocess.run(
                    cmd,
                    cwd=str(TOOLS_DIR),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdin=subprocess.DEVNULL,
                    timeout=60,
                    check=False,
                )
            except (subprocess.TimeoutExpired, OSError):
                try:
                    result_file.unlink(missing_ok=True)
                except OSError:
                    pass
                return _simple(ok=False, message="Не удалось выполнить снимок. Повторите попытку.")

        marker = parse_capture_result(completed.stdout or "")
        result: dict[str, Any] | None = None
        try:
            if result_file.is_file():
                raw = result_file.read_text(encoding="utf-8")
                loaded = json.loads(raw)
                if isinstance(loaded, dict):
                    result = loaded
        except (OSError, json.JSONDecodeError):
            result = None
        finally:
            try:
                result_file.unlink(missing_ok=True)
            except OSError:
                pass

        if result is None:
            if marker and not marker.get("_file_marker"):
                result = marker
        if result is None:
            return _simple(ok=False, message="Не удалось выполнить снимок. Повторите попытку.")
        if result.get("ok") is not True and "message" not in result:
            result["message"] = "Не удалось выполнить снимок. Повторите попытку."
        return result

    def list_windows(self, *, exclude_title: str = "") -> dict[str, Any]:
        result = self._run(["-Action", "List", "-ExcludeTitle", exclude_title or ""])
        if result.get("ok") is True and not isinstance(result.get("windows"), list):
            result["windows"] = []
        return result

    def probe_window(self, hwnd: str) -> dict[str, Any]:
        return self._run(["-Action", "Probe", "-Hwnd", str(hwnd or "")])

    def capture_window(self, hwnd: str, output_path: Path) -> dict[str, Any]:
        return self._run(
            [
                "-Action",
                "Capture",
                "-Hwnd",
                str(hwnd or ""),
                "-OutputPath",
                str(output_path),
            ]
        )


def get_capture_backend() -> CaptureBackend:
    """Resolve the active capture backend. Replaceable without changing Local Bridge."""
    override = (os.environ.get("AI_POS_CAPTURE_BACKEND") or "").strip().lower()
    if override in {"none", "unavailable", "off"}:
        return UnavailableCaptureBackend()
    if os.name == "nt":
        return PowerShellCaptureBackend()
    return UnavailableCaptureBackend()


_BACKEND: CaptureBackend | None = None


def capture_backend() -> CaptureBackend:
    global _BACKEND
    if _BACKEND is None:
        _BACKEND = get_capture_backend()
    return _BACKEND


def list_windows(*, exclude_title: str = "") -> dict[str, Any]:
    return capture_backend().list_windows(exclude_title=exclude_title)


def probe_window(hwnd: str) -> dict[str, Any]:
    return capture_backend().probe_window(hwnd)


def capture_window(hwnd: str, output_path: Path) -> dict[str, Any]:
    return capture_backend().capture_window(hwnd, output_path)
