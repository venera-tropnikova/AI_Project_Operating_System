#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI POS Local Bridge (MVP v0.3).

Serves the UI and exposes a tiny localhost API:
- Orchestrator refresh-insight (unchanged contract)
- Project folder pick / preview / create / inspect (Passport bootstrap)
- Desktop shortcut creation (reuses tools/create_ai_pos_shortcut.ps1)
- Project task history read (facts only; does not accept tasks)
- Project passport read/write (.ai-pos/project_passport.json)
- Capture Service façade (window list / capture / shot serve)

Does not determine stage. Does not replace Analyzer / Stage Engine.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from project_stage_engine import STAGE_MODEL as ENGINE_STAGE_MODEL
from knowledge_base import (
    add_source_from_path,
    content_type_for,
    delete_source,
    get_source,
    list_sources,
    pick_knowledge_file,
    resolve_source_file,
)
from project_structure_map import build_structure_map
from project_setup_actions import (
    apply_project_setup,
    get_project_setup_status,
    preview_project_setup,
)
from urllib.parse import parse_qs, urlparse

import capture_service


ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = Path(__file__).resolve().parent
ORCHESTRATOR = TOOLS_DIR / "refresh_project_insight.py"
SHORTCUT_SCRIPT = TOOLS_DIR / "create_ai_pos_shortcut.ps1"
TEMPLATE_DIR = ROOT / "Projects" / "TEMPLATE"
ANALYSIS_REL = Path(".ai-pos") / "project_analysis.json"
HISTORY_REL = Path(".ai-pos") / "history" / "history.json"
HISTORY_SHOTS_REL = Path(".ai-pos") / "history" / "shots"
HISTORY_SCHEMA = "ai-pos-task-history"
HISTORY_VERSION = 1
PASSPORT_REL = Path(".ai-pos") / "project_passport.json"
PASSPORT_SCHEMA = "ai-pos.project_passport/v1"
PASSPORT_VERSION = 1
PASSPORT_REQUIRED_FIELDS = (
    "name",
    "summary",
    "goal",
    "audience",
    "expected_result",
    "status",
)
_PASSPORT_LOCK = threading.Lock()

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
_SHOT_LOCK = threading.Lock()


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


def find_cursor_executable() -> Path | None:
    """Locate Cursor desktop app or CLI without inventing a custom protocol."""
    for name in ("cursor", "cursor.cmd", "Cursor"):
        found = shutil.which(name)
        if found:
            path = Path(found)
            if path.is_file():
                return path

    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA") or ""
        candidates = [
            Path(local) / "Programs" / "cursor" / "Cursor.exe",
            Path(local) / "Programs" / "Cursor" / "Cursor.exe",
            Path(os.environ.get("ProgramFiles") or "") / "Cursor" / "Cursor.exe",
        ]
        for path in candidates:
            if path.is_file():
                return path
    else:
        for path in (
            Path("/usr/local/bin/cursor"),
            Path.home() / "Applications" / "Cursor.app" / "Contents" / "Resources" / "app" / "bin" / "code",
            Path("/Applications/Cursor.app/Contents/Resources/app/bin/cursor"),
            Path("/Applications/Cursor.app/Contents/MacOS/Cursor"),
        ):
            if path.is_file():
                return path
    return None


def open_in_cursor(project_path: str) -> dict[str, Any]:
    """Open Cursor with the project folder. Does not auto-send a chat prompt."""
    raw = str(project_path or "").strip()
    if not raw:
        return simple_result(
            ok=False,
            message="Не указана рабочая папка проекта. Задайте её в настройках проекта.",
        )

    root = resolve_existing_dir(raw)
    if root is None:
        return simple_result(
            ok=False,
            message="Папка проекта не найдена. Проверьте путь в настройках проекта.",
        )

    cursor = find_cursor_executable()
    if cursor is None:
        return simple_result(
            ok=False,
            message="Cursor не найден на этом компьютере. Установите Cursor или добавьте его в PATH.",
        )

    try:
        popen_kwargs: dict[str, Any] = {
            "cwd": str(root),
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True,
        }
        if os.name == "nt":
            # Detach from Local Bridge process tree on Windows.
            popen_kwargs["creationflags"] = (
                getattr(subprocess, "DETACHED_PROCESS", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )
        else:
            popen_kwargs["start_new_session"] = True

        subprocess.Popen([str(cursor), str(root)], **popen_kwargs)
    except OSError:
        return simple_result(
            ok=False,
            message="Не удалось открыть Cursor. Проверьте установку программы и повторите.",
        )

    return simple_result(
        ok=True,
        message="Cursor открыт. Вставьте задание в чат.",
        project_path=str(root),
    )


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


def _history_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_history_entry(raw: Any) -> dict[str, Any] | None:
    """Keep only display fields for a completed-task fact. Invalid rows are skipped."""
    if not isinstance(raw, dict):
        return None
    entry_id = _history_text(raw.get("id"))
    accepted_at = _history_text(raw.get("accepted_at"))
    task_name = _history_text(raw.get("task_name"))
    if not entry_id or not accepted_at or not task_name:
        return None
    visual_raw = raw.get("visual")
    visual: dict[str, Any] | None = None
    if isinstance(visual_raw, dict):
        file_name = _history_text(visual_raw.get("file"))
        visual = {
            "required": bool(visual_raw.get("required")),
            "kind": _history_text(visual_raw.get("kind")) or None,
            "file": file_name or None,
            "skip_reason": _history_text(visual_raw.get("skip_reason")) or None,
        }
    review_raw = raw.get("review")
    review = None
    if isinstance(review_raw, dict):
        try:
            items_total = int(review_raw.get("items_total") or 0)
            items_confirmed = int(review_raw.get("items_confirmed") or 0)
        except (TypeError, ValueError):
            items_total = 0
            items_confirmed = 0
        review = {
            "items_total": items_total,
            "items_confirmed": items_confirmed,
        }
    return {
        "id": entry_id,
        "accepted_at": accepted_at,
        "task_id": _history_text(raw.get("task_id")) or None,
        "task_name": task_name,
        "module_id": _history_text(raw.get("module_id")) or None,
        "module_name": _history_text(raw.get("module_name")) or None,
        "goal": _history_text(raw.get("goal")),
        "expected_result": _history_text(raw.get("expected_result")),
        "result_summary": _history_text(raw.get("result_summary")),
        "verification_summary": _history_text(raw.get("verification_summary")),
        "next_step": _history_text(raw.get("next_step")),
        "review": review,
        "visual": visual,
    }


def read_project_history(project_path: str) -> dict[str, Any]:
    """
    Read completed-task facts from <project>/.ai-pos/history/history.json.

    Client passes only the project working folder. The journal path is assembled
    on the server and never accepted from the client.
    """
    root = resolve_existing_dir(project_path)
    if root is None:
        return simple_result(
            ok=False,
            message="Рабочая папка проекта не найдена. Проверьте путь в настройках проекта.",
            project_name=None,
            entries=[],
        )

    history_path = root / HISTORY_REL
    try:
        resolved_root = root.resolve()
        resolved_history = history_path.resolve()
        resolved_history.relative_to(resolved_root / ".ai-pos" / "history")
    except (OSError, ValueError):
        return simple_result(
            ok=False,
            message="Не удалось открыть историю проекта. Повторите попытку.",
            project_name=None,
            entries=[],
        )

    if not resolved_history.is_file():
        return simple_result(
            ok=True,
            message=None,
            project_name=None,
            entries=[],
        )

    try:
        loaded = json.loads(resolved_history.read_text(encoding="utf-8"))
    except OSError:
        return simple_result(
            ok=False,
            message="Не удалось прочитать историю проекта. Повторите попытку.",
            project_name=None,
            entries=[],
        )
    except json.JSONDecodeError:
        return simple_result(
            ok=False,
            message="История проекта повреждена. Записи сейчас недоступны.",
            project_name=None,
            entries=[],
        )

    if not isinstance(loaded, dict):
        return simple_result(
            ok=False,
            message="История проекта повреждена. Записи сейчас недоступны.",
            project_name=None,
            entries=[],
        )

    schema = _history_text(loaded.get("schema"))
    version = loaded.get("version")
    entries_raw = loaded.get("entries")
    if schema != HISTORY_SCHEMA or version != HISTORY_VERSION or not isinstance(entries_raw, list):
        return simple_result(
            ok=False,
            message="История проекта повреждена. Записи сейчас недоступны.",
            project_name=None,
            entries=[],
        )

    entries: list[dict[str, Any]] = []
    for item in entries_raw:
        normalized = _normalize_history_entry(item)
        if normalized is not None:
            entries.append(normalized)

    # Newest first for the current-task screen.
    entries.sort(key=lambda row: row.get("accepted_at") or "", reverse=True)

    return simple_result(
        ok=True,
        message=None,
        project_name=_history_text(loaded.get("project_name")) or None,
        entries=entries,
    )


def _passport_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_passport_modules(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    modules: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = _passport_text(item.get("name"))
        if not name:
            continue
        mod_id = _passport_text(item.get("id")) or None
        description = _passport_text(item.get("description"))
        status = _passport_text(item.get("status"))
        row: dict[str, Any] = {
            "id": mod_id,
            "name": name,
            "description": description or None,
        }
        if status:
            row["status"] = status
        modules.append(row)
    return modules


def normalize_project_passport(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    schema = _passport_text(raw.get("schema"))
    version = raw.get("version")
    if schema != PASSPORT_SCHEMA or version != PASSPORT_VERSION:
        return None

    capabilities_raw = raw.get("capabilities")
    capabilities: list[str] = []
    if isinstance(capabilities_raw, list):
        for item in capabilities_raw:
            text = _passport_text(item)
            if text:
                capabilities.append(text)

    missing_raw = raw.get("missing_fields")
    missing_fields: list[str] = []
    if isinstance(missing_raw, list):
        for item in missing_raw:
            key = _passport_text(item)
            if key and key not in missing_fields:
                missing_fields.append(key)

    project_id = _passport_text(raw.get("project_id"))

    return {
        "schema": PASSPORT_SCHEMA,
        "version": PASSPORT_VERSION,
        "project_id": project_id,
        "name": _passport_text(raw.get("name")),
        "summary": _passport_text(raw.get("summary")),
        "goal": _passport_text(raw.get("goal")),
        "audience": _passport_text(raw.get("audience")),
        "expected_result": _passport_text(raw.get("expected_result")),
        "capabilities": capabilities,
        "status": _passport_text(raw.get("status")),
        "modules": _normalize_passport_modules(raw.get("modules")),
        "missing_fields": missing_fields,
    }


def compute_missing_passport_fields(passport: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in PASSPORT_REQUIRED_FIELDS:
        if not _passport_text(passport.get(key)):
            missing.append(key)
    return missing


def build_project_passport(
    *,
    project_id: str = "",
    name: str = "",
    summary: str = "",
    goal: str = "",
    audience: str = "",
    expected_result: str = "",
    capabilities: list[str] | None = None,
    status: str = "",
    modules: list[dict[str, Any]] | None = None,
    missing_fields: list[str] | None = None,
) -> dict[str, Any]:
    passport = normalize_project_passport(
        {
            "schema": PASSPORT_SCHEMA,
            "version": PASSPORT_VERSION,
            "project_id": project_id,
            "name": name,
            "summary": summary,
            "goal": goal,
            "audience": audience,
            "expected_result": expected_result,
            "capabilities": capabilities or [],
            "status": status,
            "modules": modules or [],
            "missing_fields": missing_fields if missing_fields is not None else [],
        }
    )
    assert passport is not None
    if missing_fields is None:
        passport["missing_fields"] = compute_missing_passport_fields(passport)
    return passport


def resolve_project_passport_path(
    project_path: str,
) -> tuple[Path | None, Path | None, dict[str, Any] | None]:
    root = resolve_existing_dir(project_path)
    if root is None:
        return None, None, simple_result(
            ok=False,
            message="Рабочая папка проекта не найдена. Проверьте путь в настройках проекта.",
            passport=None,
        )
    try:
        resolved_root = root.resolve()
        passport_path = (root / PASSPORT_REL).resolve()
        passport_path.parent.relative_to(resolved_root / ".ai-pos")
    except (OSError, ValueError):
        return None, None, simple_result(
            ok=False,
            message="Не удалось открыть паспорт проекта. Повторите попытку.",
            passport=None,
        )
    return resolved_root, passport_path, None


def read_project_passport(project_path: str) -> dict[str, Any]:
    """Read descriptive project passport from <project>/.ai-pos/project_passport.json."""
    _root, passport_path, err = resolve_project_passport_path(project_path)
    if err is not None or passport_path is None:
        return err or simple_result(ok=False, message="Не удалось открыть паспорт проекта.", passport=None)

    if not passport_path.is_file():
        return simple_result(
            ok=True,
            message=None,
            passport=None,
            exists=False,
        )

    try:
        loaded = json.loads(passport_path.read_text(encoding="utf-8"))
    except OSError:
        return simple_result(
            ok=False,
            message="Не удалось прочитать паспорт проекта. Повторите попытку.",
            passport=None,
        )
    except json.JSONDecodeError:
        return simple_result(
            ok=False,
            message="Паспорт проекта повреждён. Откройте настройки и сохраните сведения заново.",
            passport=None,
        )

    passport = normalize_project_passport(loaded)
    if passport is None:
        return simple_result(
            ok=False,
            message="Паспорт проекта повреждён. Откройте настройки и сохраните сведения заново.",
            passport=None,
        )

    return simple_result(
        ok=True,
        message=None,
        passport=passport,
        exists=True,
    )


def write_project_passport(project_path: str, passport_raw: Any) -> dict[str, Any]:
    """Write project passport. Does not touch Stage Engine, history, or PROJECT_CONTEXT.md."""
    root, passport_path, err = resolve_project_passport_path(project_path)
    if err is not None or root is None or passport_path is None:
        return err or simple_result(ok=False, message="Не удалось сохранить паспорт проекта.", passport=None)

    if isinstance(passport_raw, dict):
        payload = dict(passport_raw)
        payload["schema"] = PASSPORT_SCHEMA
        payload["version"] = PASSPORT_VERSION
        if "missing_fields" not in payload:
            payload["missing_fields"] = compute_missing_passport_fields(
                {
                    "name": payload.get("name"),
                    "summary": payload.get("summary"),
                    "goal": payload.get("goal"),
                    "audience": payload.get("audience"),
                    "expected_result": payload.get("expected_result"),
                    "status": payload.get("status"),
                }
            )
        passport = normalize_project_passport(payload)
    else:
        passport = None

    if passport is None:
        return simple_result(
            ok=False,
            message="Не удалось сохранить паспорт: проверьте заполненные поля.",
            passport=None,
        )

    with _PASSPORT_LOCK:
        try:
            passport_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = passport_path.with_suffix(".json.tmp")
            tmp_path.write_text(
                json.dumps(passport, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            tmp_path.replace(passport_path)
        except OSError:
            return simple_result(
                ok=False,
                message="Не удалось сохранить паспорт проекта. Проверьте права доступа.",
                passport=None,
            )

    return simple_result(
        ok=True,
        message="Сведения о проекте сохранены.",
        passport=passport,
        exists=True,
        wrote=True,
    )


def engine_stage_model() -> list[dict[str, str]]:
    model: list[dict[str, str]] = []
    for item in ENGINE_STAGE_MODEL:
        stage_id = str(item.get("id") or "").strip()
        label = str(item.get("label") or "").strip()
        if stage_id and label:
            model.append({"id": stage_id, "label": label})
    return model


def normalize_stage_model(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list) or not raw:
        return engine_stage_model()
    model: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        stage_id = str(item.get("id") or "").strip()
        label = str(item.get("label") or "").strip()
        if stage_id and label:
            model.append({"id": stage_id, "label": label})
    return model if model else engine_stage_model()


def read_project_stage(project_path: str) -> dict[str, Any]:
    """
    Read Stage Engine state for the project folder.
    stage_model always comes from the engine model (file may omit it on older writes).
    """
    root = resolve_existing_dir(project_path)
    if root is None:
        return simple_result(
            ok=False,
            message="Рабочая папка проекта не найдена. Проверьте путь в настройках проекта.",
            stage=None,
            stage_label=None,
            stage_model=engine_stage_model(),
            exists=False,
        )

    stage_path = root / Path(".ai-pos") / "project_stage.json"
    model = engine_stage_model()
    if not stage_path.is_file():
        return simple_result(
            ok=True,
            message=None,
            stage=None,
            stage_label=None,
            stage_model=model,
            exists=False,
        )

    try:
        loaded = json.loads(stage_path.read_text(encoding="utf-8"))
    except OSError:
        return simple_result(
            ok=False,
            message="Не удалось прочитать состояние проекта. Повторите попытку.",
            stage=None,
            stage_label=None,
            stage_model=model,
            exists=True,
        )
    except json.JSONDecodeError:
        return simple_result(
            ok=False,
            message="Файл состояния проекта повреждён.",
            stage=None,
            stage_label=None,
            stage_model=model,
            exists=True,
        )

    if not isinstance(loaded, dict):
        return simple_result(
            ok=False,
            message="Файл состояния проекта повреждён.",
            stage=None,
            stage_label=None,
            stage_model=model,
            exists=True,
        )

    stage = str(loaded.get("stage") or "").strip() or None
    stage_label = str(loaded.get("stage_label") or "").strip() or None
    if not stage_label and stage:
        for item in model:
            if item["id"] == stage:
                stage_label = item["label"]
                break
    file_model = normalize_stage_model(loaded.get("stage_model"))

    return simple_result(
        ok=True,
        message=None,
        stage=stage,
        stage_label=stage_label,
        stage_model=file_model,
        exists=True,
        confidence_state=str(loaded.get("confidence_state") or "").strip() or None,
    )


def resolve_project_shots_dir(project_path: str) -> tuple[Path | None, Path | None, dict[str, Any] | None]:
    """Return (project_root, shots_dir, error_payload)."""
    root = resolve_existing_dir(project_path)
    if root is None:
        return None, None, simple_result(
            ok=False,
            message="Рабочая папка проекта не найдена. Проверьте путь в настройках проекта.",
        )
    try:
        resolved_root = root.resolve()
        shots_dir = (resolved_root / HISTORY_SHOTS_REL).resolve()
        shots_dir.relative_to(resolved_root / ".ai-pos" / "history")
    except (OSError, ValueError):
        return None, None, simple_result(
            ok=False,
            message="Не удалось открыть папку снимков проекта. Повторите попытку.",
        )
    return resolved_root, shots_dir, None


def safe_shot_basename(name: str) -> str | None:
    text = _history_text(name)
    if not text or "/" in text or "\\" in text or text in {".", ".."}:
        return None
    base = Path(text).name
    if base != text:
        return None
    if not base.lower().endswith(".png"):
        return None
    if not re.fullmatch(r"[A-Za-z0-9._\-]+\.png", base):
        return None
    return base


def shot_filename(prefix: str = "shot") -> str:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    safe_prefix = re.sub(r"[^A-Za-z0-9_\-]+", "-", (prefix or "shot").strip())[:40].strip("-") or "shot"
    return f"{stamp}-{safe_prefix}.png"


def list_capture_windows(*, exclude_title: str = "") -> dict[str, Any]:
    result = capture_service.list_windows(exclude_title=exclude_title)
    if result.get("ok") is True:
        result.setdefault("message", None)
        result.setdefault("windows", [])
    return result


def probe_capture_window(hwnd: str) -> dict[str, Any]:
    return capture_service.probe_window(str(hwnd or "").strip())


def capture_project_window(
    *,
    project_path: str,
    hwnd: str,
    label: str = "result",
) -> dict[str, Any]:
    root, shots_dir, err = resolve_project_shots_dir(project_path)
    if err is not None:
        return err
    assert root is not None and shots_dir is not None
    hwnd_text = str(hwnd or "").strip()
    if not hwnd_text:
        return simple_result(ok=False, message="Сначала выберите окно приложения.")

    probe = capture_service.probe_window(hwnd_text)
    if probe.get("ok") is not True:
        return simple_result(
            ok=False,
            message=probe.get("message") or "Не удалось проверить выбранное окно.",
        )
    if probe.get("available") is False:
        return simple_result(
            ok=False,
            message="Сохранённое окно больше недоступно. Выберите окно снова.",
            need_reselect=True,
        )

    with _SHOT_LOCK:
        try:
            shots_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            return simple_result(
                ok=False,
                message="Не удалось создать папку для снимков. Проверьте права доступа.",
            )
        filename = shot_filename(label)
        output_path = shots_dir / filename
        result = capture_service.capture_window(hwnd_text, output_path)

    if result.get("ok") is not True:
        return simple_result(
            ok=False,
            message=result.get("message") or "Не удалось сделать снимок. Повторите попытку.",
            need_reselect=bool(result.get("need_reselect")),
        )
    if not output_path.is_file():
        return simple_result(ok=False, message="Снимок не был сохранён. Повторите попытку.")

    rel = f"shots/{filename}"
    return simple_result(
        ok=True,
        message="Снимок сохранён.",
        visual={
            "required": True,
            "kind": "capture",
            "file": rel,
            "window_hwnd": str(result.get("hwnd") or hwnd_text),
            "window_title": _history_text(result.get("title")) or None,
            "process_name": _history_text(result.get("process_name")) or None,
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "width": result.get("width"),
            "height": result.get("height"),
            "bytes": result.get("bytes"),
            "skip_reason": None,
        },
    )


def attach_project_shot(
    *,
    project_path: str,
    image_base64: str,
    filename_hint: str = "",
) -> dict[str, Any]:
    root, shots_dir, err = resolve_project_shots_dir(project_path)
    if err is not None:
        return err
    assert root is not None and shots_dir is not None
    raw = (image_base64 or "").strip()
    if "," in raw and raw.lower().startswith("data:"):
        raw = raw.split(",", 1)[1]
    if not raw:
        return simple_result(ok=False, message="Не удалось прочитать файл снимка.")
    try:
        data = base64.b64decode(raw, validate=False)
    except Exception:
        return simple_result(ok=False, message="Не удалось прочитать файл снимка.")
    if len(data) < 100:
        return simple_result(ok=False, message="Файл снимка слишком маленький.")
    if len(data) > 12 * 1024 * 1024:
        return simple_result(ok=False, message="Снимок слишком большой. Выберите файл меньше 12 МБ.")
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return simple_result(
            ok=False,
            message="Нужен снимок в формате PNG.",
        )

    hint = Path(_history_text(filename_hint) or "attachment").stem
    filename = shot_filename(hint or "attachment")
    with _SHOT_LOCK:
        try:
            shots_dir.mkdir(parents=True, exist_ok=True)
            output_path = shots_dir / filename
            output_path.write_bytes(data)
        except OSError:
            return simple_result(
                ok=False,
                message="Не удалось сохранить снимок. Проверьте права доступа.",
            )

    return simple_result(
        ok=True,
        message="Снимок прикреплён.",
        visual={
            "required": True,
            "kind": "attachment",
            "file": f"shots/{filename}",
            "window_hwnd": None,
            "window_title": None,
            "process_name": None,
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "width": None,
            "height": None,
            "bytes": len(data),
            "skip_reason": None,
        },
    )


def resolve_shot_file(project_path: str, file_name: str) -> tuple[Path | None, dict[str, Any] | None]:
    root, shots_dir, err = resolve_project_shots_dir(project_path)
    if err is not None:
        return None, err
    assert shots_dir is not None
    # Accept "shots/name.png" or bare "name.png".
    raw = _history_text(file_name).replace("\\", "/")
    if raw.startswith("shots/"):
        raw = raw[6:]
    base = safe_shot_basename(raw)
    if base is None:
        return None, simple_result(ok=False, message="Снимок не найден.")
    try:
        target = (shots_dir / base).resolve()
        target.relative_to(shots_dir)
    except (OSError, ValueError):
        return None, simple_result(ok=False, message="Снимок не найден.")
    if not target.is_file():
        return None, simple_result(ok=False, message="Снимок не найден.")
    return target, None


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

    def _send_bytes(
        self,
        status: int,
        body: bytes,
        *,
        content_type: str,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
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

    def end_headers(self) -> None:  # noqa: N802
        # index.html embeds CSS; avoid browsers keeping a stale connect/create shell.
        req_path = urlparse(getattr(self, "path", "") or "").path
        if req_path in {"/", "/index.html"} or str(req_path).endswith(".html"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
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
        if path == "/api/project-history/shot":
            query = parse_qs(parsed.query or "")
            project_path = (query.get("project_path") or [""])[0]
            file_name = (query.get("file") or [""])[0]
            target, err = resolve_shot_file(project_path, file_name)
            if err is not None or target is None:
                self._send_json(404 if (err or {}).get("message") else 400, err or simple_result(ok=False, message="Снимок не найден."))
                return
            try:
                body = target.read_bytes()
            except OSError:
                self._send_json(
                    400,
                    simple_result(ok=False, message="Не удалось открыть снимок."),
                )
                return
            self._send_bytes(200, body, content_type="image/png")
            return
        if path == "/api/knowledge/sources/file":
            query = parse_qs(parsed.query or "")
            source_id = (query.get("id") or [""])[0]
            target, err = resolve_source_file(source_id)
            if err is not None or target is None:
                self._send_json(
                    404 if (err or {}).get("message") else 400,
                    err or simple_result(ok=False, message="Файл источника не найден."),
                )
                return
            try:
                body = target.read_bytes()
            except OSError:
                self._send_json(
                    400,
                    simple_result(ok=False, message="Не удалось открыть файл источника."),
                )
                return
            self._send_bytes(200, body, content_type=content_type_for(target))
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


        if path == "/api/knowledge/sources/list":
            result = list_sources()
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/knowledge/sources/pick":
            with _PICK_LOCK:
                result = pick_knowledge_file(
                    str(body.get("title") or "Выберите файл для базы знаний")
                )
            status = 200 if result.get("ok") or result.get("cancelled") else 400
            self._send_json(status, result)
            return

        if path == "/api/knowledge/sources/add":
            result = add_source_from_path(str(body.get("file_path") or ""))
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/knowledge/sources/get":
            result = get_source(str(body.get("id") or ""))
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/knowledge/sources/delete":
            confirm = body.get("confirm")
            if isinstance(confirm, str):
                confirm = confirm.strip().lower() in {"1", "true", "yes", "да"}
            else:
                confirm = bool(confirm)
            result = delete_source(str(body.get("id") or ""), confirm=confirm)
            self._send_json(200 if result.get("ok") else 400, result)
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

        if path == "/api/project-structure/map":
            result = build_structure_map(
                str(body.get("project_path") or ""),
                include_recommendations=False,
            )
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/project-structure/setup-preview":
            result = preview_project_setup(
                str(body.get("project_path") or ""),
                user_info=body.get("user_info"),
            )
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/project-structure/setup":
            confirm = body.get("confirm")
            if isinstance(confirm, str):
                confirm = confirm.strip().lower() in {"1", "true", "yes", "да"}
            else:
                confirm = bool(confirm)
            result = apply_project_setup(
                str(body.get("project_path") or ""),
                confirm=confirm,
                user_info=body.get("user_info"),
            )
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/project-structure/setup-status":
            result = get_project_setup_status(str(body.get("project_path") or ""))
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/open-in-cursor":
            result = open_in_cursor(str(body.get("project_path") or ""))
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/create-desktop-shortcut":
            result = create_desktop_shortcut()
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/project-history/read":
            result = read_project_history(str(body.get("project_path") or ""))
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/project-passport/read":
            result = read_project_passport(str(body.get("project_path") or ""))
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/project-stage/read":
            result = read_project_stage(str(body.get("project_path") or ""))
            self._send_json(200 if result.get("ok") else 400, result)
            return
        if path == "/api/project-passport/write":
            result = write_project_passport(
                str(body.get("project_path") or ""),
                body.get("passport"),
            )
            self._send_json(200 if result.get("ok") else 400, result)
            return


        if path == "/api/capture/windows":
            result = list_capture_windows(
                exclude_title=str(body.get("exclude_title") or "")
            )
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/capture/probe":
            result = probe_capture_window(str(body.get("hwnd") or ""))
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/capture/window":
            result = capture_project_window(
                project_path=str(body.get("project_path") or ""),
                hwnd=str(body.get("hwnd") or ""),
                label=str(body.get("label") or "result"),
            )
            self._send_json(200 if result.get("ok") else 400, result)
            return

        if path == "/api/capture/attach":
            result = attach_project_shot(
                project_path=str(body.get("project_path") or ""),
                image_base64=str(body.get("image_base64") or ""),
                filename_hint=str(body.get("filename") or ""),
            )
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
    print(f"API: http://{args.host}:{args.port}/api/open-in-cursor")
    print(f"API: http://{args.host}:{args.port}/api/create-project")
    print(f"API: http://{args.host}:{args.port}/api/create-desktop-shortcut")
    print(f"API: http://{args.host}:{args.port}/api/project-history/read")
    print(f"API: http://{args.host}:{args.port}/api/project-stage/read")
    print(f"API: http://{args.host}:{args.port}/api/project-passport/read")
    print(f"API: http://{args.host}:{args.port}/api/project-passport/write")
    print(f"API: http://{args.host}:{args.port}/api/capture/windows")
    print(f"API: http://{args.host}:{args.port}/api/capture/window")
    print(f"API: http://{args.host}:{args.port}/api/capture/attach")
    print(f"API: http://{args.host}:{args.port}/api/project-history/shot")
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
