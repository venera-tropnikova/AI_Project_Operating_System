# -*- coding: utf-8 -*-
"""
AI POS Knowledge Base — Sources storage contour.

Stores originals in system storage (not inside user projects).
No extraction / semantic analysis in this contour.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "ai-pos.knowledge_sources/v1"
SCHEMA_VERSION = 1
STATUS_ADDED = "added"
ORIGIN_FILE = "file"

ALLOWED_TYPES = frozenset(
    {"pdf", "docx", "md", "txt", "pptx", "png", "jpg", "jpeg", "webp"}
)
IMAGE_TYPES = frozenset({"png", "jpg", "jpeg", "webp"})
DOC_TYPES = frozenset({"pdf", "docx", "md", "txt", "pptx"})

TYPE_LABELS_RU = {
    "pdf": "PDF",
    "docx": "Документ Word",
    "md": "Текст Markdown",
    "txt": "Текст",
    "pptx": "Презентация",
    "png": "Изображение",
    "jpg": "Изображение",
    "jpeg": "Изображение",
    "webp": "Изображение",
}

STATUS_LABELS_RU = {
    STATUS_ADDED: "Добавлен",
}

_LOCK = threading.RLock()
_SAFE_NAME_RE = re.compile(r"[^\w.\-()+ ]+", re.UNICODE)

def knowledge_root() -> Path:
    local = (os.environ.get("LOCALAPPDATA") or "").strip()
    if local:
        return Path(local) / "AI_POS" / "knowledge"
    # Fallback when LOCALAPPDATA is unavailable
    home = Path.home()
    return home / ".ai-pos-system" / "knowledge"

def sources_index_path(root: Path | None = None) -> Path:
    return (root or knowledge_root()) / "sources.json"

def files_dir(root: Path | None = None) -> Path:
    return (root or knowledge_root()) / "files"

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def _empty_index() -> dict[str, Any]:
    return {"schema": SCHEMA, "version": SCHEMA_VERSION, "sources": []}

def _ensure_storage(root: Path | None = None) -> Path:
    base = root or knowledge_root()
    files_dir(base).mkdir(parents=True, exist_ok=True)
    idx = sources_index_path(base)
    if not idx.is_file():
        idx.write_text(
            json.dumps(_empty_index(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return base

def _load_index(root: Path | None = None) -> dict[str, Any]:
    base = _ensure_storage(root)
    path = sources_index_path(base)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return _empty_index()
    if not isinstance(data, dict):
        return _empty_index()
    sources = data.get("sources")
    if not isinstance(sources, list):
        data["sources"] = []
    data["schema"] = SCHEMA
    data["version"] = SCHEMA_VERSION
    return data

def _save_index(data: dict[str, Any], root: Path | None = None) -> None:
    base = _ensure_storage(root)
    path = sources_index_path(base)
    payload = {
        "schema": SCHEMA,
        "version": SCHEMA_VERSION,
        "sources": list(data.get("sources") or []),
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

def _ext_type(path: Path) -> str | None:
    ext = path.suffix.lower().lstrip(".")
    if ext in ALLOWED_TYPES:
        return ext
    return None

def _safe_filename(name: str) -> str:
    raw = Path(str(name or "file")).name.strip() or "file"
    cleaned = _SAFE_NAME_RE.sub("_", raw).strip(" ._")
    return cleaned[:180] or "file"

def _new_id(prefix: str = "ks") -> str:
    return f"{prefix}_" + uuid.uuid4().hex[:12]

def _public_source(item: dict[str, Any]) -> dict[str, Any]:
    src_type = str(item.get("type") or "")
    status = str(item.get("status") or STATUS_ADDED)
    if status not in STATUS_LABELS_RU:
        status = STATUS_ADDED
    out = {
        "id": item.get("id"),
        "title": item.get("title"),
        "type": src_type,
        "type_label": TYPE_LABELS_RU.get(src_type, src_type or "Файл"),
        "added_at": item.get("added_at"),
        "status": status,
        "status_label": STATUS_LABELS_RU.get(status, "Добавлен"),
        "origin_kind": ORIGIN_FILE,
        "origin_label": item.get("origin_label"),
        "file_ref": item.get("file_ref"),
        "size": int(item.get("size") or 0),
        "is_image": src_type in IMAGE_TYPES,
    }
    if out["is_image"] and out.get("id"):
        out["preview_url"] = f"/api/knowledge/sources/file?id={out['id']}"
    return out

def list_sources() -> dict[str, Any]:
    with _LOCK:
        data = _load_index()
        items = [
            _public_source(s)
            for s in (data.get("sources") or [])
            if isinstance(s, dict) and s.get("id")
        ]
        # Newest first
        items.sort(key=lambda x: str(x.get("added_at") or ""), reverse=True)
        return {
            "ok": True,
            "message": None,
            "sources": items,
            "storage_path": str(knowledge_root()),
        }

def get_source(source_id: str) -> dict[str, Any]:
    sid = str(source_id or "").strip()
    if not sid:
        return {"ok": False, "message": "Не указан источник.", "source": None}
    with _LOCK:
        data = _load_index()
        for s in data.get("sources") or []:
            if isinstance(s, dict) and str(s.get("id")) == sid:
                return {"ok": True, "message": None, "source": _public_source(s)}
    return {"ok": False, "message": "Источник не найден.", "source": None}

def resolve_source_file(source_id: str) -> tuple[Path | None, dict[str, Any] | None]:
    """Return absolute path to stored original, or error payload."""
    sid = str(source_id or "").strip()
    if not sid:
        return None, {"ok": False, "message": "Не указан источник."}
    with _LOCK:
        base = _ensure_storage()
        data = _load_index(base)
        for s in data.get("sources") or []:
            if not isinstance(s, dict) or str(s.get("id")) != sid:
                continue
            rel = str(s.get("file_ref") or "").replace("\\", "/").lstrip("/")
            if not rel or ".." in Path(rel).parts:
                return None, {"ok": False, "message": "Файл источника недоступен."}
            path = (base / rel).resolve()
            try:
                path.relative_to(base.resolve())
            except ValueError:
                return None, {"ok": False, "message": "Файл источника недоступен."}
            if not path.is_file():
                return None, {"ok": False, "message": "Файл источника не найден."}
            return path, None
    return None, {"ok": False, "message": "Источник не найден."}

def content_type_for(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "md": "text/markdown; charset=utf-8",
        "txt": "text/plain; charset=utf-8",
    }.get(ext, "application/octet-stream")

def add_source_from_path(file_path: str) -> dict[str, Any]:
    raw = str(file_path or "").strip()
    if not raw:
        return {"ok": False, "message": "Не выбран файл.", "source": None, "wrote": False}
    src = Path(raw)
    try:
        src = src.expanduser().resolve()
    except OSError:
        return {
            "ok": False,
            "message": "Не удалось открыть выбранный файл.",
            "source": None,
            "wrote": False,
        }
    if not src.is_file():
        return {
            "ok": False,
            "message": "Файл не найден.",
            "source": None,
            "wrote": False,
        }
    file_type = _ext_type(src)
    if not file_type:
        return {
            "ok": False,
            "message": (
                "Этот тип файла пока нельзя добавить. "
                "Подходят: PDF, Word, Markdown, текст, презентация и изображения PNG, JPG, WEBP."
            ),
            "source": None,
            "wrote": False,
        }
    try:
        size = int(src.stat().st_size)
    except OSError:
        return {
            "ok": False,
            "message": "Не удалось прочитать файл.",
            "source": None,
            "wrote": False,
        }

    source_id = _new_id()
    safe_name = _safe_filename(src.name)
    title = Path(safe_name).stem or safe_name
    rel_ref = f"files/{source_id}/{safe_name}"

    with _LOCK:
        base = _ensure_storage()
        dest_dir = base / "files" / source_id
        dest_path = dest_dir / safe_name
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dest_path))
        except OSError:
            try:
                if dest_dir.is_dir():
                    shutil.rmtree(dest_dir, ignore_errors=True)
            except OSError:
                pass
            return {
                "ok": False,
                "message": "Не удалось сохранить файл в базе знаний.",
                "source": None,
                "wrote": False,
            }

        record = {
            "id": source_id,
            "title": title,
            "type": file_type,
            "added_at": _utc_now_iso(),
            "status": STATUS_ADDED,
            "origin_kind": ORIGIN_FILE,
            "origin_label": src.name,
            "file_ref": rel_ref.replace("\\", "/"),
            "size": size,
        }
        data = _load_index(base)
        sources = [s for s in (data.get("sources") or []) if isinstance(s, dict)]
        sources.append(record)
        data["sources"] = sources
        try:
            _save_index(data, base)
        except OSError:
            shutil.rmtree(dest_dir, ignore_errors=True)
            return {
                "ok": False,
                "message": "Не удалось сохранить сведения об источнике.",
                "source": None,
                "wrote": False,
            }

        return {
            "ok": True,
            "message": None,
            "source": _public_source(record),
            "wrote": True,
            "storage_path": str(base),
        }

def delete_source(source_id: str, *, confirm: bool = False) -> dict[str, Any]:
    if not confirm:
        return {
            "ok": False,
            "message": "Удаление не выполнено: нужно явное подтверждение.",
            "wrote": False,
        }
    sid = str(source_id or "").strip()
    if not sid:
        return {"ok": False, "message": "Не указан источник.", "wrote": False}

    with _LOCK:
        base = _ensure_storage()
        data = _load_index(base)
        sources = [s for s in (data.get("sources") or []) if isinstance(s, dict)]
        found = None
        kept: list[dict[str, Any]] = []
        for s in sources:
            if str(s.get("id")) == sid:
                found = s
            else:
                kept.append(s)
        if found is None:
            return {"ok": False, "message": "Источник не найден.", "wrote": False}

        data["sources"] = kept
        try:
            _save_index(data, base)
        except OSError:
            return {
                "ok": False,
                "message": "Не удалось обновить список источников.",
                "wrote": False,
            }

        folder = base / "files" / sid
        if folder.is_dir():
            shutil.rmtree(folder, ignore_errors=True)

        return {
            "ok": True,
            "message": "Источник удалён из базы знаний.",
            "wrote": True,
            "id": sid,
        }

def pick_knowledge_file(title: str = "Выберите файл для базы знаний") -> dict[str, Any]:
    """Native file dialog (thread-safe). Returns path or cancelled."""
    import subprocess
    import sys

    title_text = (title or "Выберите файл").strip() or "Выберите файл"
    # Tk filetypes: (label, pattern)
    script = (
        "import tkinter as tk\n"
        "from tkinter import filedialog\n"
        "root = tk.Tk()\n"
        "root.withdraw()\n"
        "try:\n"
        "    root.attributes('-topmost', True)\n"
        "except Exception:\n"
        "    pass\n"
        "path = filedialog.askopenfilename(\n"
        f"    title={title_text!r},\n"
        "    filetypes=[\n"
        "        ('Документы и изображения',\n"
        "         '*.pdf *.docx *.md *.txt *.pptx *.png *.jpg *.jpeg *.webp'),\n"
        "        ('PDF', '*.pdf'),\n"
        "        ('Word', '*.docx'),\n"
        "        ('Markdown', '*.md'),\n"
        "        ('Текст', '*.txt'),\n"
        "        ('Презентации', '*.pptx'),\n"
        "        ('Изображения', '*.png *.jpg *.jpeg *.webp'),\n"
        "        ('Все файлы', '*.*'),\n"
        "    ],\n"
        ")\n"
        "print(path or '', end='')\n"
        "try:\n"
        "    root.destroy()\n"
        "except Exception:\n"
        "    pass\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        err = (completed.stderr or "").strip().splitlines()
        detail = err[-1] if err else "диалог недоступен"
        return {
            "ok": False,
            "message": f"Не удалось открыть выбор файла: {detail}",
            "path": None,
            "cancelled": False,
        }
    path_raw = (completed.stdout or "").strip()
    if not path_raw:
        return {
            "ok": False,
            "message": "Выбор файла отменён.",
            "path": None,
            "cancelled": True,
        }
    path = Path(path_raw)
    if not path.is_file():
        return {
            "ok": False,
            "message": "Выбранный файл недоступен.",
            "path": path_raw,
            "cancelled": False,
        }
    return {
        "ok": True,
        "message": None,
        "path": str(path.resolve()),
        "cancelled": False,
    }
