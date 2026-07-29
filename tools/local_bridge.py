#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI POS Local Bridge (MVP v0.3).

Serves the UI and exposes a tiny localhost API:
- Orchestrator refresh-insight (unchanged contract)
- Project folder pick / preview / create / inspect (Passport bootstrap)
- Desktop shortcut creation (reuses tools/create_ai_pos_shortcut.ps1)

Does not determine stage. Does not replace Analyzer / Stage Engine.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = Path(__file__).resolve().parent
ORCHESTRATOR = TOOLS_DIR / "refresh_project_insight.py"
SHORTCUT_SCRIPT = TOOLS_DIR / "create_ai_pos_shortcut.ps1"
TEMPLATE_DIR = ROOT / "Projects" / "TEMPLATE"
ANALYSIS_REL = Path(".ai-pos") / "project_analysis.json"

RESULT_PREFIX = "AI_POS_ORCHESTRATOR_RESULT="
SHORTCUT_RESULT_PREFIX = "AI_POS_SHORTCUT_RESULT="
SHORTCUT_FAILED_MESSAGE = (
    "Не удалось создать ярлык. "
    "Попробуйте запустить create_ai_pos_shortcut.cmd в папке программы."
)
MODE_NORMAL = "NORMAL"
MODE_DIAGNOSTIC = "DIAGNOSTIC"
MODE_BLOCKED = "BLOCKED"
RC_ANALYZER_FAILED = "ANALYZER_FAILED"
RC_PROJECT_ROOT_INVALID = "PROJECT_ROOT_INVALID"

API_KEYS = ("ok", "analysis", "message", "mode", "reason_codes")

_PICK_LOCK = threading.Lock()
_SHORTCUT_LOCK = threading.Lock()


def parse_orchestrator_result(stdout: str) -> dict[str, Any] | None:
    for line in reversed((stdout or "").splitlines()):
        line = line.strip()
        if line.startswith(RESULT_PREFIX):
            raw = line[len(RESULT_PREFIX) :]
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return None
            if isinstance(data, dict) and data.get("mode"):
                return data
    return None


def api_result(
    *,
    ok: bool,
    analysis: dict[str, Any] | None,
    message: str | None,
    mode: str,
    reason_codes: list[str] | None = None,
) -> dict[str, Any]:
    """Normalized POST /api/refresh-insight payload (exactly five fields)."""
    return {
        "ok": bool(ok),
        "analysis": analysis,
        "message": message,
        "mode": mode,
        "reason_codes": list(reason_codes or []),
    }


def simple_result(
    *,
    ok: bool,
    message: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": bool(ok), "message": message}
    payload.update(extra)
    return payload


def user_facing_error(raw: str | None) -> str:
    """Hide internal artifact names from end-user messages."""
    text = (raw or "").strip()
    if not text:
        return "Не удалось обновить анализ. Проверьте рабочую папку проекта и повторите."
    lowered = text.lower()
    if (
        "project_stage.json" in lowered
        or "project_analysis.json" in lowered
        or ".ai-pos" in lowered
    ):
        if "missing" in lowered or "нет" in lowered or "not found" in lowered:
            return (
                "Не удалось обновить анализ: данные проекта ещё не готовы. "
                "Проверьте рабочую папку и повторите."
            )
        if "invalid" in lowered or "json" in lowered:
            return "Не удалось обновить анализ: внутренние данные проекта повреждены."
        return "Не удалось обновить анализ. Повторите попытку."
    return text


def _analysis_is_valid(analysis: dict[str, Any] | None) -> bool:
    if not analysis:
        return False
    if analysis.get("valid") is False:
        return False
    if analysis.get("status") == "invalid":
        return False
    stage = analysis.get("stage")
    if stage is None or stage == "":
        return False
    return True


def run_refresh(project_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(ORCHESTRATOR), str(project_path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    orch = parse_orchestrator_result(completed.stdout or "")
    mode = str((orch or {}).get("mode") or "")
    reason_codes = list((orch or {}).get("reason_codes") or [])
    if not mode:
        # Fallback if structured line missing (should not happen on current orchestrator).
        mode = MODE_BLOCKED if completed.returncode != 0 else MODE_NORMAL

    # BLOCKED: never expose on-disk analysis (prevents stale STAGE_ENGINE_FAILED etc.).
    if mode == MODE_BLOCKED:
        detail = None
        if completed.stderr:
            detail = completed.stderr.strip().splitlines()[-1]
        return api_result(
            ok=False,
            analysis=None,
            message=user_facing_error(detail)
            if detail
            else "Не удалось обновить анализ. Повторите попытку.",
            mode=MODE_BLOCKED,
            reason_codes=reason_codes,
        )

    analysis: dict[str, Any] | None = None
    analysis_path = project_path / ANALYSIS_REL
    if analysis_path.is_file():
        try:
            loaded = json.loads(analysis_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                analysis = loaded
        except json.JSONDecodeError:
            analysis = None

    valid = _analysis_is_valid(analysis)
    analyzer_failed = RC_ANALYZER_FAILED in reason_codes

    # ANALYZER_FAILED: never ok:true from a leftover/stale analysis file.
    if analyzer_failed:
        detail = None
        if analysis and not valid and analysis.get("error"):
            detail = str(analysis.get("error"))
        elif completed.stderr:
            detail = completed.stderr.strip().splitlines()[-1]
        return api_result(
            ok=False,
            analysis=None if valid or analysis is None else analysis,
            message=user_facing_error(detail)
            if detail
            else "Анализ не получен. Повторите обновление.",
            mode=MODE_DIAGNOSTIC,
            reason_codes=reason_codes,
        )

    # Existing ok semantics unchanged: true only with valid analysis.
    if valid and mode == MODE_NORMAL:
        return api_result(
            ok=True,
            analysis=analysis,
            message=None,
            mode=MODE_NORMAL,
            reason_codes=reason_codes,
        )

    if valid and mode == MODE_DIAGNOSTIC:
        return api_result(
            ok=True,
            analysis=analysis,
            message=None,
            mode=MODE_DIAGNOSTIC,
            reason_codes=reason_codes,
        )

    detail = None
    if analysis and analysis.get("error"):
        detail = str(analysis.get("error"))
    elif completed.stderr:
        detail = completed.stderr.strip().splitlines()[-1]

    if mode == MODE_DIAGNOSTIC:
        return api_result(
            ok=False,
            analysis=analysis,
            message=user_facing_error(detail)
            if detail
            else "Анализ не получен. Повторите обновление.",
            mode=MODE_DIAGNOSTIC,
            reason_codes=reason_codes,
        )

    # Compatible fallback (legacy exit without mode / incomplete analysis).
    if not analysis:
        return api_result(
            ok=False,
            analysis=None,
            message="Анализ не получен. Повторите обновление.",
            mode=mode or MODE_DIAGNOSTIC,
            reason_codes=reason_codes,
        )

    return api_result(
        ok=False,
        analysis=analysis,
        message=user_facing_error(
            str(analysis.get("error") or detail or "Анализ недействителен.")
        ),
        mode=mode or MODE_DIAGNOSTIC,
        reason_codes=reason_codes,
    )


def slugify_project_name(name: str) -> str:
    text = (name or "").strip()
    if not text:
        return "new-project"
    # Keep letters/digits/space/_/-; collapse the rest.
    text = re.sub(r"[^\w\s\-]+", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text.strip())
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:80] or "new-project"


def resolve_existing_dir(raw: str) -> Path | None:
    text = str(raw or "").strip()
    if not text:
        return None
    path = Path(text).expanduser()
    try:
        path = path.resolve()
    except OSError:
        return None
    if not path.exists() or not path.is_dir():
        return None
    return path


def template_relative_paths(template_dir: Path | None = None) -> list[str]:
    root = template_dir or TEMPLATE_DIR
    if not root.is_dir():
        return []
    items: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            items.append(path.relative_to(root).as_posix())
    return items


def preview_new_project(parent_path: str, project_name: str) -> dict[str, Any]:
    parent = resolve_existing_dir(parent_path)
    if parent is None:
        return simple_result(
            ok=False,
            message="Родительская папка не найдена. Выберите существующую папку.",
        )
    folder_name = slugify_project_name(project_name)
    project_path = parent / folder_name
    exists = project_path.exists()
    non_empty = False
    if exists and project_path.is_dir():
        non_empty = any(project_path.iterdir())
    elif exists:
        non_empty = True
    files = template_relative_paths()
    if not files:
        return simple_result(
            ok=False,
            message="Не найден шаблон Projects/TEMPLATE.",
            parent_path=str(parent),
            folder_name=folder_name,
            project_path=str(project_path),
        )
    return simple_result(
        ok=True,
        message=None,
        parent_path=str(parent),
        folder_name=folder_name,
        project_path=str(project_path),
        exists=exists,
        non_empty=non_empty,
        template_files=files,
        can_create=not exists,
    )


def inspect_project_folder(project_path: str) -> dict[str, Any]:
    root = resolve_existing_dir(project_path)
    if root is None:
        return simple_result(
            ok=False,
            message="Папка проекта не найдена. Выберите существующую папку.",
        )
    expected = template_relative_paths()
    present: list[str] = []
    missing: list[str] = []
    for rel in expected:
        target = root / Path(rel)
        if target.is_file():
            present.append(rel)
        else:
            missing.append(rel)
    entries = sorted(
        p.name for p in root.iterdir() if not p.name.startswith(".")
    )[:40]
    return simple_result(
        ok=True,
        message=None,
        project_path=str(root),
        present_files=present,
        missing_files=missing,
        top_entries=entries,
        has_ai_pos=(root / ".ai-pos").is_dir(),
        wrote=False,
    )


def create_project_folder(
    *,
    parent_path: str,
    project_name: str,
    confirm: bool,
) -> dict[str, Any]:
    if not confirm:
        return simple_result(
            ok=False,
            message="Создание на диске возможно только после явного подтверждения.",
            wrote=False,
        )
    preview = preview_new_project(parent_path, project_name)
    if not preview.get("ok"):
        preview["wrote"] = False
        return preview
    if preview.get("exists"):
        return simple_result(
            ok=False,
            message=(
                "Папка уже существует. Выберите другое имя или подключите "
                "существующий проект без перезаписи."
            ),
            project_path=preview.get("project_path"),
            wrote=False,
        )
    if not TEMPLATE_DIR.is_dir():
        return simple_result(
            ok=False,
            message="Не найден шаблон Projects/TEMPLATE.",
            wrote=False,
        )

    target = Path(str(preview["project_path"]))
    try:
        shutil.copytree(TEMPLATE_DIR, target)
    except OSError as exc:
        return simple_result(
            ok=False,
            message=f"Не удалось создать папку проекта: {exc}",
            project_path=str(target),
            wrote=False,
        )

    copied = template_relative_paths(target)
    return simple_result(
        ok=True,
        message="Папка проекта создана, шаблон скопирован.",
        parent_path=preview.get("parent_path"),
        folder_name=preview.get("folder_name"),
        project_path=str(target),
        copied_files=copied,
        wrote=True,
    )


def pick_directory(title: str = "Выберите папку") -> dict[str, Any]:
    """Native folder dialog via a short-lived subprocess (thread-safe for Bridge)."""
    title_text = (title or "Выберите папку").strip() or "Выберите папку"
    script = (
        "import tkinter as tk\n"
        "from tkinter import filedialog\n"
        "root = tk.Tk()\n"
        "root.withdraw()\n"
        "try:\n"
        "    root.attributes('-topmost', True)\n"
        "except Exception:\n"
        "    pass\n"
        f"path = filedialog.askdirectory(title={title_text!r}, mustexist=True)\n"
        "print(path or '', end='')\n"
        "try:\n"
        "    root.destroy()\n"
        "except Exception:\n"
        "    pass\n"
    )
    with _PICK_LOCK:
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    if completed.returncode != 0:
        err = (completed.stderr or "").strip().splitlines()
        detail = err[-1] if err else "диалог папки недоступен"
        return simple_result(
            ok=False,
            message=f"Не удалось открыть выбор папки: {detail}",
            path=None,
            cancelled=False,
        )
    path_raw = (completed.stdout or "").strip()
    if not path_raw:
        return simple_result(
            ok=False,
            message="Выбор папки отменён.",
            path=None,
            cancelled=True,
        )
    resolved = resolve_existing_dir(path_raw)
    if resolved is None:
        return simple_result(
            ok=False,
            message="Выбранная папка недоступна.",
            path=path_raw,
            cancelled=False,
        )
    return simple_result(
        ok=True,
        message=None,
        path=str(resolved),
        cancelled=False,
    )


def parse_shortcut_result(stdout: str) -> dict[str, Any] | None:
    for line in reversed((stdout or "").splitlines()):
        line = line.strip()
        if line.startswith(SHORTCUT_RESULT_PREFIX):
            try:
                data = json.loads(line[len(SHORTCUT_RESULT_PREFIX) :])
            except json.JSONDecodeError:
                return None
            return data if isinstance(data, dict) else None
    return None


def find_powershell() -> str | None:
    system_root = os.environ.get("SystemRoot") or "C:\\Windows"
    builtin = (
        Path(system_root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    )
    if builtin.is_file():
        return str(builtin)
    return shutil.which("powershell")


def create_desktop_shortcut() -> dict[str, Any]:
    """Desktop shortcut for AI POS: same script as the manual create_ai_pos_shortcut.cmd."""
    if os.name != "nt":
        return simple_result(ok=False, message="Создание ярлыка доступно только в Windows.")
    if not SHORTCUT_SCRIPT.is_file():
        return simple_result(ok=False, message=SHORTCUT_FAILED_MESSAGE)
    powershell = find_powershell()
    if powershell is None:
        return simple_result(ok=False, message=SHORTCUT_FAILED_MESSAGE)

    with _SHORTCUT_LOCK:
        try:
            completed = subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(SHORTCUT_SCRIPT),
                    "-NoPause",
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdin=subprocess.DEVNULL,
                timeout=60,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError):
            return simple_result(ok=False, message=SHORTCUT_FAILED_MESSAGE)

    # Script console output may arrive in the OEM code page: trust only the ASCII result line.
    result = parse_shortcut_result(completed.stdout or "")
    if completed.returncode != 0 or not result or result.get("ok") is not True:
        if (result or {}).get("reason") == "LAUNCHER_MISSING":
            return simple_result(
                ok=False,
                message="Не удалось создать ярлык: в папке программы нет файла запуска AI POS.",
            )
        return simple_result(ok=False, message=SHORTCUT_FAILED_MESSAGE)

    icon_missing = bool(result.get("icon_missing"))
    message = "Готово. Ярлык AI POS создан на рабочем столе."
    if icon_missing:
        message += " Использована стандартная иконка."
    return simple_result(
        ok=True,
        message=message,
        icon_missing=icon_missing,
        shortcut_path=str(result.get("lnk") or ""),
    )


class LocalBridgeHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid JSON body: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def do_OPTIONS(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            return
        self.send_error(404)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "service": "ai-pos-local-bridge",
                    "orchestrator": ORCHESTRATOR.name,
                    "template": str(TEMPLATE_DIR),
                },
            )
            return
        if path in {"/", "/index.html"}:
            self.path = "/index.html"
        return SimpleHTTPRequestHandler.do_GET(self)

    def _handle_refresh_insight(self, body: dict[str, Any]) -> None:
        project_path_raw = str(body.get("project_path") or "").strip()
        if not project_path_raw:
            self._send_json(
                400,
                api_result(
                    ok=False,
                    analysis=None,
                    message="Укажите рабочую папку проекта и повторите обновление.",
                    mode=MODE_BLOCKED,
                    reason_codes=[RC_PROJECT_ROOT_INVALID],
                ),
            )
            return

        root = Path(project_path_raw).expanduser()
        try:
            root = root.resolve()
        except OSError:
            self._send_json(
                400,
                api_result(
                    ok=False,
                    analysis=None,
                    message="Не удалось открыть рабочую папку проекта.",
                    mode=MODE_BLOCKED,
                    reason_codes=[RC_PROJECT_ROOT_INVALID],
                ),
            )
            return

        if not root.exists() or not root.is_dir():
            self._send_json(
                400,
                api_result(
                    ok=False,
                    analysis=None,
                    message="Рабочая папка проекта не найдена. Проверьте путь и повторите.",
                    mode=MODE_BLOCKED,
                    reason_codes=[RC_PROJECT_ROOT_INVALID],
                ),
            )
            return

        result = run_refresh(root)
        status = 200 if result.get("ok") else 422
        self._send_json(status, result)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            body = self._read_json_body()
        except ValueError:
            if path == "/api/refresh-insight":
                self._send_json(
                    400,
                    api_result(
                        ok=False,
                        analysis=None,
                        message="Некорректный запрос на обновление анализа.",
                        mode=MODE_BLOCKED,
                        reason_codes=[],
                    ),
                )
            else:
                self._send_json(
                    400,
                    simple_result(ok=False, message="Некорректный JSON-запрос."),
                )
            return

        if path == "/api/refresh-insight":
            self._handle_refresh_insight(body)
            return

        if path == "/api/pick-folder":
            title = str(body.get("title") or "Выберите папку")
            result = pick_directory(title)
            status = 200 if result.get("ok") else 400
            if result.get("cancelled"):
                status = 200
            self._send_json(status, result)
            return

        if path == "/api/preview-new-project":
            result = preview_new_project(
                str(body.get("parent_path") or ""),
                str(body.get("project_name") or ""),
            )
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/inspect-project-folder":
            result = inspect_project_folder(str(body.get("project_path") or ""))
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/create-desktop-shortcut":
            result = create_desktop_shortcut()
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/create-project":
            confirm = body.get("confirm") is True
            result = create_project_folder(
                parent_path=str(body.get("parent_path") or ""),
                project_name=str(body.get("project_name") or ""),
                confirm=confirm,
            )
            status = 200 if result.get("ok") else 400
            self._send_json(status, result)
            return

        self.send_error(404, "Unknown API endpoint")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI POS local bridge: UI + project bootstrap + refresh-insight API"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Bind port (default: 8080)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if not ORCHESTRATOR.is_file():
        print(f"Error: orchestrator not found: {ORCHESTRATOR}", file=sys.stderr)
        return 1

    server = ThreadingHTTPServer((args.host, args.port), LocalBridgeHandler)
    print("AI POS Local Bridge")
    print(f"UI:  http://{args.host}:{args.port}/")
    print(f"API: http://{args.host}:{args.port}/api/refresh-insight")
    print(f"API: http://{args.host}:{args.port}/api/pick-folder")
    print(f"API: http://{args.host}:{args.port}/api/preview-new-project")
    print(f"API: http://{args.host}:{args.port}/api/inspect-project-folder")
    print(f"API: http://{args.host}:{args.port}/api/create-project")
    print(f"API: http://{args.host}:{args.port}/api/create-desktop-shortcut")
    print("Stop with Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
