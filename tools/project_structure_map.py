# -*- coding: utf-8 -*-
"""
Read-only project structure map for AI POS.

Builds a folder/file tree with Russian purpose hints and categories.
Does not delete, move, rename, or write anything.
Does not determine stage or touch Passport / Analyzer.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

UNKNOWN_PURPOSE = "Назначение требует уточнения"

# Categories (stable ids for UI)
CAT_ARCHITECTURE = "architecture"
CAT_CODE = "code"
CAT_DATA = "data"
CAT_IMAGES = "images"
CAT_DOCS = "documents"
CAT_MATERIALS = "materials"
CAT_SERVICE = "service"
CAT_BACKUPS = "backups"
CAT_UNKNOWN = "unknown"

CATEGORY_LABELS = {
    CAT_ARCHITECTURE: "Архитектура",
    CAT_CODE: "Код",
    CAT_DATA: "Данные",
    CAT_IMAGES: "Изображения",
    CAT_DOCS: "Документы",
    CAT_MATERIALS: "Материалы",
    CAT_SERVICE: "Служебные файлы",
    CAT_BACKUPS: "Резервные копии",
    CAT_UNKNOWN: "Без подтверждённого назначения",
}

# User-facing sections for «Понятная карта» (category id -> section).
USER_SECTIONS: list[dict[str, str]] = [
    {
        "id": "layout",
        "category": CAT_ARCHITECTURE,
        "title": "Устройство проекта",
        "description": (
            "Как устроен проект: правила, схемы и ключевые настройки. "
            "Помогает понять общую логику без просмотра всех файлов."
        ),
    },
    {
        "id": "app",
        "category": CAT_CODE,
        "title": "Работа приложения",
        "description": (
            "Страницы, стили и скрипты, из которых собрана работа приложения. "
            "Именно эти файлы обычно отвечают за то, что видит пользователь."
        ),
    },
    {
        "id": "info",
        "category": CAT_DATA,
        "title": "Информация проекта",
        "description": (
            "Списки, записи и данные, которые приложение показывает или использует. "
            "Сюда входят тексты, календари, справочники и похожие файлы."
        ),
    },
    {
        "id": "materials",
        "category": CAT_MATERIALS,
        "title": "Материалы пользователя",
        "description": (
            "Ваши материалы и исходники, добавленные к проекту: референсы, "
            "кейсы и рабочие вложения."
        ),
    },
    {
        "id": "images",
        "category": CAT_IMAGES,
        "title": "Изображения",
        "description": (
            "Картинки, иконки и другие изображения проекта. "
            "Они нужны для оформления и наглядности."
        ),
    },
    {
        "id": "documents",
        "category": CAT_DOCS,
        "title": "Документы",
        "description": (
            "Описания, инструкции и текстовые документы. "
            "По ним можно понять цели проекта и как с ним работать."
        ),
    },
    {
        "id": "service",
        "category": CAT_SERVICE,
        "title": "Файлы AI POS и Git",
        "description": (
            "Служебные файлы AI POS и система версий Git. "
            "Обычно их не нужно менять вручную — система ведёт их сама."
        ),
    },
    {
        "id": "backups",
        "category": CAT_BACKUPS,
        "title": "Резервные копии",
        "description": (
            "Сохранённые копии файлов. "
            "Их лучше хранить отдельно от рабочих файлов, чтобы не править устаревшие версии."
        ),
    },
    {
        "id": "unknown",
        "category": CAT_UNKNOWN,
        "title": "Требуют пояснения",
        "description": (
            "Элементы, назначение которых пока не удалось определить уверенно. "
            "Их стоит подписать или уточнить, чтобы структура оставалась понятной."
        ),
    },
]

# Dir name (lower) -> (category, purpose)
KNOWN_DIRS: dict[str, tuple[str, str]] = {
    "src": (CAT_CODE, "Исходные файлы проекта"),
    "js": (CAT_CODE, "Основные функции приложения"),
    "css": (CAT_CODE, "Оформление интерфейса"),
    "styles": (CAT_CODE, "Оформление интерфейса"),
    "scripts": (CAT_CODE, "Вспомогательные скрипты"),
    "app": (CAT_CODE, "Основные файлы приложения"),
    "lib": (CAT_CODE, "Вспомогательные модули"),
    "components": (CAT_CODE, "Части интерфейса"),
    "assets": (CAT_IMAGES, "Изображения и материалы проекта"),
    "images": (CAT_IMAGES, "Изображения проекта"),
    "img": (CAT_IMAGES, "Изображения проекта"),
    "icons": (CAT_IMAGES, "Иконки интерфейса"),
    "docs": (CAT_DOCS, "Документация проекта"),
    "doc": (CAT_DOCS, "Документация проекта"),
    "documentation": (CAT_DOCS, "Документация проекта"),
    "data": (CAT_DATA, "Данные для работы приложения"),
    "db": (CAT_DATA, "Хранение записей"),
    "database": (CAT_DATA, "Хранение записей"),
    "fixtures": (CAT_DATA, "Примеры для проверки"),
    "materials": (CAT_MATERIALS, "Материалы проекта"),
    "references": (CAT_MATERIALS, "Образцы и референсы"),
    "uploads": (CAT_MATERIALS, "Загруженные материалы"),
    "portfolio-projects": (CAT_MATERIALS, "Кейсы портфолио"),
    "architecture": (CAT_ARCHITECTURE, "Устройство проекта"),
    "design": (CAT_ARCHITECTURE, "Правила оформления"),
    "design-preview": (CAT_ARCHITECTURE, "Превью оформления"),
    ".ai-pos": (CAT_SERVICE, "Данные AI POS о проекте"),
    ".git": (CAT_SERVICE, "История изменений"),
    ".github": (CAT_SERVICE, "Настройки GitHub"),
    ".vscode": (CAT_SERVICE, "Настройки редактора"),
    ".cursor": (CAT_SERVICE, "Настройки Cursor"),
    "node_modules": (CAT_SERVICE, "Внешние библиотеки"),
    "__pycache__": (CAT_SERVICE, "Служебный кэш"),
    ".venv": (CAT_SERVICE, "Окружение Python"),
    "venv": (CAT_SERVICE, "Окружение Python"),
    "backup": (CAT_BACKUPS, "Резервные копии"),
    "backups": (CAT_BACKUPS, "Резервные копии"),
    "archive": (CAT_BACKUPS, "Архив резервных копий"),
    "archives": (CAT_BACKUPS, "Архив резервных копий"),
    "dist": (CAT_SERVICE, "Готовая сборка"),
    "build": (CAT_SERVICE, "Результаты сборки"),
    "public": (CAT_CODE, "Публичные файлы"),
    "static": (CAT_CODE, "Статические файлы"),
    "tests": (CAT_CODE, "Проверки качества"),
    "test": (CAT_CODE, "Проверки качества"),
    "tools": (CAT_CODE, "Инструменты разработки"),
}

# Exact file name (lower) -> (category, purpose)
KNOWN_FILES: dict[str, tuple[str, str]] = {
    "index.html": (CAT_CODE, "Запуск главной страницы приложения"),
    "calendar.html": (CAT_CODE, "Страница календаря"),
    "day.html": (CAT_CODE, "Экран «Мой день»"),
    "birthdays.html": (CAT_CODE, "Страница поздравлений"),
    "history.html": (CAT_CODE, "Историческая справка"),
    "history.json": (CAT_DATA, "Историческая справка"),
    "important-dates.html": (CAT_CODE, "Важные даты"),
    "profile.html": (CAT_CODE, "Страница профиля"),
    "readme.md": (CAT_DOCS, "Описание проекта и запуск"),
    "changelog.md": (CAT_DOCS, "История изменений проекта"),
    "license": (CAT_DOCS, "Лицензия проекта"),
    "license.md": (CAT_DOCS, "Лицензия проекта"),
    "package.json": (CAT_ARCHITECTURE, "Список зависимостей"),
    "package-lock.json": (CAT_SERVICE, "Фиксация версий"),
    "requirements.txt": (CAT_ARCHITECTURE, "Список зависимостей"),
    "pyproject.toml": (CAT_ARCHITECTURE, "Настройки проекта"),
    "architecture.md": (CAT_ARCHITECTURE, "Устройство проекта"),
    "project_context.md": (CAT_DOCS, "Цели проекта"),
    "roadmap.md": (CAT_DOCS, "План развития"),
    "design_rules.md": (CAT_ARCHITECTURE, "Правила оформления"),
    "data_schema.md": (CAT_ARCHITECTURE, "Схема записей"),
    "decisions.md": (CAT_DOCS, "Журнал решений"),
    "project_passport.md": (CAT_DOCS, "Паспорт проекта"),
    "project_rules.md": (CAT_DOCS, "Правила проекта"),
    "project_memory.md": (CAT_DOCS, "Память проекта"),
    "project_glossary.md": (CAT_DOCS, "Словарь проекта"),
    "project_decision_log.md": (CAT_DOCS, "Журнал решений"),
    "design_philosophy.md": (CAT_DOCS, "Идея оформления"),
    "history_content_standard.md": (CAT_DOCS, "Правила исторических текстов"),
    "readme_ai.md": (CAT_DOCS, "Подсказки для ИИ"),
    ".gitignore": (CAT_SERVICE, "Исключения для Git"),
    "favicon.ico": (CAT_IMAGES, "Иконка сайта"),
    "favicon.svg": (CAT_IMAGES, "Иконка сайта"),
    "manifest.json": (CAT_ARCHITECTURE, "Настройки приложения"),
    "style.css": (CAT_CODE, "Оформление интерфейса"),
    "app.js": (CAT_CODE, "Основные функции приложения"),
    "data.js": (CAT_DATA, "Тексты и списки"),
    "weather.js": (CAT_CODE, "Получение прогноза погоды"),
    "calendar-events.json": (CAT_DATA, "Праздники и памятные даты"),
    "calendar-events-ru.json": (CAT_DATA, "Праздники и памятные даты"),
    "calendar-events-ru-movable.json": (CAT_DATA, "Переходящие праздники"),
    "history-events-ru.json": (CAT_DATA, "Исторические события"),
    "discovery-of-the-day.json": (CAT_DATA, "Открытия дня"),
    "smile-of-the-day.json": (CAT_DATA, "Улыбка дня"),
    "thoughts-ru.json": (CAT_DATA, "Мысли дня"),
    "project_passport.json": (CAT_SERVICE, "Паспорт проекта AI POS"),
    "project_stage.json": (CAT_SERVICE, "Стадия проекта"),
    "project_analysis.json": (CAT_SERVICE, "Результат анализа"),
}

SKIP_DESCEND: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
}

MAX_DEPTH = 6
MAX_ENTRIES = 800

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp"}
CODE_EXT = {
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".py",
    ".css",
    ".scss",
    ".sass",
    ".html",
    ".htm",
    ".vue",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".cs",
}
DOC_EXT = {".md", ".txt", ".pdf", ".rtf", ".doc", ".docx"}
DATA_EXT = {".json", ".csv", ".tsv", ".sqlite", ".db", ".yaml", ".yml", ".xml"}
BACKUP_MARKERS = ("backup", "bak", "copy", "копия", "~")


def _norm_name(name: str) -> str:
    return str(name or "").strip().lower()


def classify_entry(name: str, is_dir: bool) -> tuple[str, str, bool]:
    """
    Returns (category, purpose, confirmed).
    confirmed=False → purpose must be UNKNOWN_PURPOSE for UI contract.
    """
    key = _norm_name(name)
    if is_dir:
        if key in KNOWN_DIRS:
            cat, purpose = KNOWN_DIRS[key]
            return cat, purpose, True
        if any(m in key for m in BACKUP_MARKERS):
            return CAT_BACKUPS, "Резервные копии", True
        return CAT_UNKNOWN, UNKNOWN_PURPOSE, False

    if key in KNOWN_FILES:
        cat, purpose = KNOWN_FILES[key]
        return cat, purpose, True

    suffix = Path(name).suffix.lower()
    stem = Path(name).stem.lower()
    if any(m in key or m in stem for m in (".bak", ".backup")) or key.endswith("~"):
        return CAT_BACKUPS, "Резервная копия", True
    if any(m in stem for m in BACKUP_MARKERS):
        return CAT_BACKUPS, "Резервная копия", True

    # Name heuristics before generic extension fallbacks.
    if "weather" in stem or "погод" in stem:
        return CAT_CODE, "Получение прогноза погоды", True
    if "history" in stem or "истори" in stem:
        if suffix in {".html", ".htm"}:
            return CAT_CODE, "Историческая справка", True
        return CAT_DATA, "Историческая справка", True
    if "calendar" in stem or "календар" in stem:
        if suffix in {".html", ".htm"}:
            return CAT_CODE, "Страница календаря", True
        return CAT_DATA, "Праздники и памятные даты", True
    if "birthday" in stem or "поздрав" in stem:
        return CAT_CODE, "Страница поздравлений", True
    if stem in {"day", "moy-den", "my-day"} or "мой-день" in stem:
        return CAT_CODE, "Экран «Мой день»", True

    if suffix in IMAGE_EXT:
        return CAT_IMAGES, "Изображение", True
    if suffix in {".html", ".htm"}:
        return CAT_CODE, "Страница приложения", True
    if suffix in {".css", ".scss", ".sass"}:
        return CAT_CODE, "Оформление интерфейса", True
    if suffix in {".js", ".mjs", ".cjs"}:
        return CAT_CODE, "Функции экрана", True
    if suffix == ".py":
        return CAT_CODE, "Инструмент разработки", True
    if suffix in CODE_EXT:
        return CAT_CODE, "Функции приложения", True
    if suffix in DOC_EXT:
        return CAT_DOCS, "Документ проекта", True
    if suffix in DATA_EXT:
        return CAT_DATA, "Справочная информация", True
    if suffix in {".bat", ".cmd", ".ps1"}:
        return CAT_SERVICE, "Запуск проекта", True
    if key.startswith(".") or suffix in {".log", ".tmp", ".cache"}:
        return CAT_SERVICE, "Служебный файл", True
    return CAT_UNKNOWN, UNKNOWN_PURPOSE, False


def _peek_text(path: Path, limit: int = 1800) -> str:
    try:
        if not path.is_file() or path.stat().st_size > 400_000:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")[:limit].lower()
    except OSError:
        return ""


USAGE_SCAN_EXT = {".html", ".htm", ".js", ".mjs", ".cjs", ".css", ".md"}
USAGE_SKIP_PARTS = SKIP_DESCEND | {"node_modules", ".git", "__pycache__"}


def _iter_tree_nodes(nodes: list[dict[str, Any]]):
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        yield node
        children = node.get("children")
        if isinstance(children, list):
            yield from _iter_tree_nodes(children)


def _build_usage_index(root: Path, basenames: set[str]) -> dict[str, list[str]]:
    """Map lower(basename) -> relative paths of files that mention it."""
    index: dict[str, list[str]] = {b: [] for b in basenames}
    if not basenames or not root.is_dir():
        return index

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in USAGE_SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in USAGE_SCAN_EXT:
            continue
        try:
            if path.stat().st_size > 250_000:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        for base in basenames:
            if len(base) < 4:
                continue
            if (
                f'"{base}"' in text
                or f"'{base}'" in text
                or f"/{base}" in text
                or f"./{base}" in text
                or base in text
            ):
                index[base].append(rel)
    return index


def _load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _confirm_json_purpose(
    path: Path,
    name: str,
    usage_refs: list[str],
    root: Path,
) -> tuple[str, str, bool] | None:
    data = _load_json(path)
    if data is None:
        return None
    key = _norm_name(name)

    rel_lower = str(path).replace("\\", "/").lower()
    if isinstance(data, dict):
        items = data.get("items")
        if isinstance(items, list) and items:
            sample = [i for i in items[:10] if isinstance(i, dict)]
            captions = [
                i for i in sample if isinstance(i.get("caption"), str) and i.get("caption")
            ]
            if captions and len(captions) >= max(1, min(3, len(sample))):
                smile_js = root / "js" / "smile-of-the-day.js"
                used_by_smile = False
                if smile_js.is_file():
                    try:
                        sj = smile_js.read_text(encoding="utf-8", errors="ignore").lower()
                    except OSError:
                        sj = ""
                    if key in sj or "smile-of-the-day.json" in sj:
                        used_by_smile = True
                if used_by_smile or any("smile-of-the-day" in r for r in usage_refs):
                    return (
                        CAT_DATA,
                        "Тексты для блока „Настроение дня“",
                        True,
                    )

        # Calendar-like event payloads referenced by calendar scripts/pages.
        if any(
            k in data
            for k in ("events", "holidays", "dates", "calendar")
        ) or (
            isinstance(data.get("items"), list)
            and any(
                isinstance(i, dict) and ("date" in i or "title" in i)
                for i in (data.get("items") or [])[:5]
            )
        ):
            if any("calendar" in r for r in usage_refs):
                return CAT_DATA, "Праздники и памятные даты", True

        if key.startswith("project_") and key.endswith(".json"):
            if any(".ai-pos" in r or r.endswith("local_bridge.py") for r in usage_refs) or (
                path.parent.name == ".ai-pos"
            ):
                if "passport" in key:
                    return CAT_SERVICE, "Паспорт проекта AI POS", True
                if "stage" in key:
                    return CAT_SERVICE, "Стадия проекта", True
                if "analysis" in key:
                    return CAT_SERVICE, "Результат анализа", True

        report_keys = ("results", "checks", "issues", "findings", "summary", "ok", "errors")
        if any(k in data for k in report_keys) and (
            "report" in key or "_audit" in rel_lower or "/_qa" in rel_lower
        ):
            return CAT_SERVICE, "Служебный отчёт проверки", True

    return None


def _confirm_html_purpose(
    path: Path,
    name: str,
    usage_refs: list[str],
    rel: str = "",
) -> tuple[str, str, bool] | None:
    text = _peek_text(path, 5000)
    if not text or ("<html" not in text and "<!doctype" not in text):
        return None
    key = _norm_name(name)
    rel_norm = (rel or name).replace("\\", "/")

    if key == "index.html" and ("/" not in rel_norm):
        return CAT_CODE, "Запуск главной страницы приложения", True

    # Secondary / nested pages need to be referenced from the project.
    if not usage_refs and key != "index.html":
        return None

    if key == "index.html" and usage_refs:
        return CAT_CODE, "Страница приложения", True
    if any(m in text for m in ("мой день", "my day")) and "day" in key:
        return CAT_CODE, "Экран «Мой день»", True
    if any(m in text for m in ("календар", "calendar")) and "calendar" in key:
        return CAT_CODE, "Экран «Календарь»", True
    if any(m in text for m in ("день рожден", "birthday", "поздравлен")) and (
        "birthday" in key or "поздрав" in key
    ):
        return CAT_CODE, "Экран поздравлений", True
    if any(m in text for m in ("историческ", "history")) and "history" in key:
        return CAT_CODE, "Историческая справка", True
    if "important" in key or "важн" in key:
        if any(m in text for m in ("важн", "important", "дат")):
            return CAT_CODE, "Важные даты", True
    if "profile" in key and any(m in text for m in ("профиль", "profile")):
        return CAT_CODE, "Экран профиля", True
    if usage_refs and ("<body" in text or "<main" in text or "<div" in text):
        return CAT_CODE, "Страница приложения", True
    return None


def _confirm_js_purpose(
    path: Path,
    name: str,
    usage_refs: list[str],
) -> tuple[str, str, bool] | None:
    text = _peek_text(path, 6000)
    if not text:
        return None
    key = _norm_name(name)
    if not usage_refs and key not in {"app.js"}:
        # Script must be included somewhere, except obvious app entry names with DOM work.
        if "document.getelementbyid" not in text and "queryselector" not in text:
            return None

    if any(m in text for m in ("погод", "weather", "forecast", "open-meteo", "openweather")):
        if usage_refs or key == "weather.js":
            return CAT_CODE, "Работа блока «Погода»", True
    if "smile-of-the-day" in key or (
        "smile-of-the-day.json" in text and any(m in text for m in ("smile-caption", "smile-card"))
    ):
        if usage_refs or key == "smile-of-the-day.js":
            return CAT_CODE, "Показ блока «Настроение дня»", True
    if usage_refs and ("{" in text or "function" in text or "=>" in text):
        return CAT_CODE, "Работа приложения", True
    return None


def _confirm_css_purpose(path: Path, usage_refs: list[str]) -> tuple[str, str, bool] | None:
    text = _peek_text(path, 3000)
    if not text:
        return None
    if "{" in text and "}" in text and usage_refs:
        return CAT_CODE, "Оформление интерфейса", True
    if "{" in text and "}" in text and path.parent.name.lower() in {"css", "styles"}:
        return CAT_CODE, "Оформление интерфейса", True
    return None


def _confirm_doc_purpose(path: Path, name: str) -> tuple[str, str, bool] | None:
    text = _peek_text(path, 4000)
    if not text:
        return None
    key = _norm_name(name)
    if key.startswith("readme") and any(
        m in text for m in ("проект", "запуск", "install", "start", "описан")
    ):
        return CAT_DOCS, "Описание проекта", True
    if key.startswith("changelog") or "changelog" in text[:200]:
        return CAT_DOCS, "История изменений проекта", True
    if key.startswith("roadmap"):
        return CAT_DOCS, "План развития проекта", True
    if len(text.strip()) > 40:
        return CAT_DOCS, "Документ проекта", True
    return None


def _confirm_file_purpose(
    root: Path,
    node: dict[str, Any],
    usage_index: dict[str, list[str]],
) -> tuple[str, str, bool]:
    """
    Confirm purpose by content + usage. Name is only a hint for which checks to try.
    """
    name = str(node.get("name") or "")
    rel = str(node.get("path") or name).replace("\\", "/")
    path = root / rel
    if not path.is_file():
        return CAT_UNKNOWN, UNKNOWN_PURPOSE, False

    key = _norm_name(name)
    suffix = Path(name).suffix.lower()
    usage_refs = [
        r
        for r in (usage_index.get(key) or [])
        if r.replace("\\", "/") != rel
    ]

    # Content type: images are confirmed by format; no name-based "screen" labels.
    if suffix in IMAGE_EXT:
        return CAT_IMAGES, "Изображение", True

    if suffix in {".bak"} or key.endswith("~") or ".backup." in key:
        return CAT_BACKUPS, "Резервная копия", True

    if key == ".gitignore":
        text = _peek_text(path, 2000)
        if text and ("#" in text or "/" in text or "*" in text):
            return CAT_SERVICE, "Исключения для Git", True

    if suffix in {".bat", ".cmd", ".ps1"}:
        text = _peek_text(path, 2000)
        if text and any(
            m in text for m in ("start ", "python", "http", "echo ", "@echo", "powershell")
        ):
            return CAT_SERVICE, "Запуск проекта", True

    if suffix == ".json":
        found = _confirm_json_purpose(path, name, usage_refs, root)
        if found:
            return found

    if suffix in {".html", ".htm"}:
        found = _confirm_html_purpose(path, name, usage_refs, rel=rel)
        if found:
            return found

    if suffix in {".js", ".mjs", ".cjs"}:
        found = _confirm_js_purpose(path, name, usage_refs)
        if found:
            return found

    if suffix in {".css", ".scss", ".sass"}:
        found = _confirm_css_purpose(path, usage_refs)
        if found:
            return found

    if suffix in {".md", ".txt"}:
        found = _confirm_doc_purpose(path, name)
        if found:
            return found

    if suffix in {".py"} and path.parent.name.lower() in {"tools", "scripts"}:
        text = _peek_text(path, 2000)
        if text and ("def " in text or "import " in text):
            return CAT_CODE, "Инструмент разработки", True

    # AI POS service files inside .ai-pos by location + content shape.
    if ".ai-pos" in Path(rel).parts and suffix == ".json":
        found = _confirm_json_purpose(path, name, usage_refs, root)
        if found:
            return found
        if "passport" in key:
            return CAT_SERVICE, "Паспорт проекта AI POS", True
        if "stage" in key:
            return CAT_SERVICE, "Стадия проекта", True
        if "analysis" in key:
            return CAT_SERVICE, "Результат анализа", True

    return CAT_UNKNOWN, UNKNOWN_PURPOSE, False


def _refine_dir_purposes_from_children(tree: list[dict[str, Any]]) -> None:
    """Confirm folder purposes from confirmed children (content of the folder)."""
    dirs = [n for n in _iter_tree_nodes(tree) if n.get("kind") == "dir"]
    dirs.sort(
        key=lambda n: str(n.get("path") or "").replace("\\", "/").count("/"),
        reverse=True,
    )
    for node in dirs:
        if node.get("purpose_confirmed"):
            continue
        children = [c for c in (node.get("children") or []) if isinstance(c, dict)]
        if not children:
            continue
        files = [c for c in children if c.get("kind") == "file"]
        subdirs = [c for c in children if c.get("kind") == "dir"]
        if files and all(c.get("purpose_confirmed") for c in files):
            cats = {str(c.get("category") or "") for c in files}
            if cats == {CAT_IMAGES} and not subdirs:
                node["category"] = CAT_IMAGES
                node["category_label"] = CATEGORY_LABELS[CAT_IMAGES]
                node["purpose"] = "Изображения проекта"
                node["purpose_confirmed"] = True
                continue
            if cats == {CAT_DATA} and not subdirs:
                node["category"] = CAT_DATA
                node["category_label"] = CATEGORY_LABELS[CAT_DATA]
                node["purpose"] = "Данные для работы приложения"
                node["purpose_confirmed"] = True
                continue
            if cats == {CAT_CODE} and not subdirs:
                node["category"] = CAT_CODE
                node["category_label"] = CATEGORY_LABELS[CAT_CODE]
                node["purpose"] = "Файлы приложения"
                node["purpose_confirmed"] = True
                continue
        # Folder of materials: confirmed files/dirs that are images or materials.
        if children and all(c.get("purpose_confirmed") for c in children):
            cats = {str(c.get("category") or "") for c in children}
            if cats and cats <= {CAT_IMAGES, CAT_MATERIALS, CAT_DATA}:
                node["category"] = CAT_MATERIALS
                node["category_label"] = CATEGORY_LABELS[CAT_MATERIALS]
                node["purpose"] = "Материалы проекта"
                node["purpose_confirmed"] = True


def _finalize_file_purposes(root: Path, tree: list[dict[str, Any]]) -> dict[str, int]:
    """Confirm file purposes after tree walk; recount categories."""
    files = [n for n in _iter_tree_nodes(tree) if n.get("kind") == "file"]
    basenames = {_norm_name(str(n.get("name") or "")) for n in files if n.get("name")}
    usage_index = _build_usage_index(root, basenames)

    for node in files:
        category, purpose, confirmed = _confirm_file_purpose(root, node, usage_index)
        if not confirmed:
            purpose = UNKNOWN_PURPOSE
            category = CAT_UNKNOWN
        node["category"] = category
        node["category_label"] = CATEGORY_LABELS.get(category, CATEGORY_LABELS[CAT_UNKNOWN])
        node["purpose"] = purpose
        node["purpose_confirmed"] = bool(confirmed)

    _refine_dir_purposes_from_children(tree)

    counts: dict[str, int] = {}
    for node in _iter_tree_nodes(tree):
        cat = str(node.get("category") or CAT_UNKNOWN)
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _safe_sorted_children(path: Path) -> list[Path]:
    try:
        children = list(path.iterdir())
    except OSError:
        return []
    dirs = sorted((p for p in children if p.is_dir()), key=lambda p: p.name.lower())
    files = sorted((p for p in children if p.is_file()), key=lambda p: p.name.lower())
    return dirs + files


def _format_size_label(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} Б"
    if size_bytes < 1024 * 1024:
        value = size_bytes / 1024
        text = f"{value:.1f}".rstrip("0").rstrip(".")
        return f"{text} КБ"
    value = size_bytes / (1024 * 1024)
    text = f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{text} МБ"


def _entry_meta(path: Path, *, is_dir: bool) -> tuple[str | None, int | None, str | None]:
    """
    Returns (mtime ISO local, size bytes or None for dirs, size_label or None for dirs).
    """
    try:
        st = path.stat()
    except OSError:
        return None, None, None
    mtime = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
    if is_dir:
        return mtime, None, None
    size = int(st.st_size)
    return mtime, size, _format_size_label(size)


def _walk(
    path: Path,
    *,
    rel: str,
    depth: int,
    counters: dict[str, int],
    category_counts: dict[str, int],
) -> dict[str, Any] | None:
    if counters["entries"] >= MAX_ENTRIES:
        counters["truncated"] = True
        return None
    is_dir = path.is_dir()
    name = path.name
    if is_dir:
        category, purpose, confirmed = classify_entry(name, True)
        if not confirmed:
            purpose = UNKNOWN_PURPOSE
            category = CAT_UNKNOWN
    else:
        # File purposes are confirmed later by content + usage (not by name).
        category, purpose, confirmed = CAT_UNKNOWN, UNKNOWN_PURPOSE, False

    counters["entries"] += 1
    if is_dir:
        counters["folders"] += 1
    else:
        counters["files"] += 1
    category_counts[category] = category_counts.get(category, 0) + 1

    mtime, size, size_label = _entry_meta(path, is_dir=is_dir)
    node: dict[str, Any] = {
        "name": name,
        "path": rel.replace("\\", "/"),
        "kind": "dir" if is_dir else "file",
        "category": category,
        "category_label": CATEGORY_LABELS.get(category, CATEGORY_LABELS[CAT_UNKNOWN]),
        "purpose": purpose,
        "purpose_confirmed": confirmed,
        "mtime": mtime,
        "size": size,
        "size_label": size_label,
        "children": [],
    }

    if not is_dir:
        return node

    node["nested_file_count"] = 0
    if depth >= MAX_DEPTH:
        counters["truncated"] = True
        return node
    if name in SKIP_DESCEND:
        node["children_skipped"] = True
        return node

    nested_files = 0
    for child in _safe_sorted_children(path):
        if counters["entries"] >= MAX_ENTRIES:
            counters["truncated"] = True
            break
        child_rel = child.name if not rel else f"{rel}/{child.name}"
        child_node = _walk(
            child,
            rel=child_rel,
            depth=depth + 1,
            counters=counters,
            category_counts=category_counts,
        )
        if child_node is not None:
            node["children"].append(child_node)
            if child_node.get("kind") == "file":
                nested_files += 1
            else:
                nested_files += int(child_node.get("nested_file_count") or 0)
    node["nested_file_count"] = nested_files
    return node


def _flatten_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []

    def visit(node: dict[str, Any]) -> None:
        if not node:
            return
        flat.append(
            {
                "name": node.get("name") or "",
                "path": node.get("path") or "",
                "kind": node.get("kind") or "file",
                "category": node.get("category") or CAT_UNKNOWN,
                "purpose": node.get("purpose") or UNKNOWN_PURPOSE,
                "purpose_confirmed": bool(node.get("purpose_confirmed")),
            }
        )
        for child in node.get("children") or []:
            if isinstance(child, dict):
                visit(child)

    for item in nodes or []:
        if isinstance(item, dict):
            visit(item)
    return flat


def _build_user_sections(
    tree: list[dict[str, Any]],
    category_counts: dict[str, int],
) -> list[dict[str, Any]]:
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for item in _flatten_nodes(tree):
        cat = str(item.get("category") or CAT_UNKNOWN)
        by_cat.setdefault(cat, []).append(
            {
                "name": item["name"],
                "path": item["path"],
                "kind": item["kind"],
                "purpose": item["purpose"],
                "purpose_confirmed": item["purpose_confirmed"],
            }
        )

    sections: list[dict[str, Any]] = []
    for spec in USER_SECTIONS:
        cat = spec["category"]
        items = by_cat.get(cat, [])
        count = int(category_counts.get(cat, 0) or len(items))
        if count <= 0 and not items:
            continue
        sections.append(
            {
                "id": spec["id"],
                "category": cat,
                "title": spec["title"],
                "description": spec["description"],
                "count": count if count > 0 else len(items),
                "items": items,
            }
        )
    return sections


# Template / AI POS docs checked in root or docs/ (same locations as Stage Engine markers).
AI_POS_DOC_CHECKS: list[tuple[str, str, str]] = [
    (
        "PROJECT_CONTEXT.md",
        "Добавить описание проекта (PROJECT_CONTEXT.md)",
        "файл с целью и контекстом проекта",
    ),
    (
        "ROADMAP.md",
        "Добавить план развития (ROADMAP.md)",
        "файл с планом ближайших шагов",
    ),
    (
        "ARCHITECTURE.md",
        "Добавить описание архитектуры (ARCHITECTURE.md)",
        "файл об устройстве проекта",
    ),
    (
        "DESIGN_RULES.md",
        "Добавить правила оформления (DESIGN_RULES.md)",
        "файл с правилами дизайна",
    ),
    (
        "DECISIONS.md",
        "Добавить журнал решений (DECISIONS.md)",
        "файл с принятыми решениями",
    ),
    (
        "DATA_SCHEMA.md",
        "Добавить описание данных (DATA_SCHEMA.md)",
        "файл со схемой данных",
    ),
]

DOC_LOCATIONS = ("", "docs")

BUCKET_SETUP = "can_setup"
BUCKET_REVIEW = "needs_review"
BUCKET_INSUFFICIENT = "insufficient"

BUCKET_LABELS = {
    BUCKET_SETUP: "Можно настроить",
    BUCKET_REVIEW: "Требуется проверить",
    BUCKET_INSUFFICIENT: "Сведений недостаточно",
}


def _proposal(
    *,
    pid: str,
    title: str,
    reason: str,
    kind: str,
    bucket: str,
    setup_allowed: bool = False,
    evidence: list[str] | None = None,
    paths: list[str] | None = None,
    target: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": pid,
        "title": title,
        "reason": reason,
        "kind": kind,
        "bucket": bucket,
        "setup_allowed": bool(setup_allowed),
    }
    if evidence:
        item["evidence"] = evidence
    if paths:
        item["paths"] = paths
    if target:
        item["target"] = target
    return item


def _find_named_file(root: Path, filename: str) -> list[str]:
    """Return relative paths where filename exists (root and docs/ only)."""
    hits: list[str] = []
    key = filename.lower()
    for loc in DOC_LOCATIONS:
        path = root / loc / filename if loc else root / filename
        if path.is_file():
            rel = str(path.relative_to(root)).replace("\\", "/")
            hits.append(rel)
            continue
        folder = root / loc if loc else root
        if not folder.is_dir():
            continue
        try:
            for child in folder.iterdir():
                if child.is_file() and child.name.lower() == key:
                    hits.append(str(child.relative_to(root)).replace("\\", "/"))
                    break
        except OSError:
            continue
    return hits


def _md_has_substance(path: Path) -> bool:
    text = _peek_text(path, 4000)
    if not text:
        return False
    body = [
        ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")
    ]
    return len(body) >= 2


def _passport_has_substance(root: Path) -> tuple[bool, str, list[str]]:
    """Passport confirmed only with real filled fields / substantive markdown."""
    evidence: list[str] = []
    md_hits = _find_named_file(root, "PROJECT_PASSPORT.md")
    for rel in md_hits:
        if _md_has_substance(root / rel):
            return True, rel, [f"present: {rel}"]
        evidence.append(f"stub: {rel}")

    pj = root / ".ai-pos" / "project_passport.json"
    if pj.is_file():
        evidence.append("present: .ai-pos/project_passport.json")
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            data = None
        if isinstance(data, dict):
            filled = []
            for key in ("name", "summary", "goal", "audience", "expected_result"):
                val = data.get(key)
                if isinstance(val, str) and val.strip():
                    filled.append(key)
            if filled:
                return True, ".ai-pos/project_passport.json", evidence + [
                    "filled: " + ", ".join(filled)
                ]
            missing = data.get("missing_fields")
            if isinstance(missing, list) and missing:
                evidence.append("missing_fields: " + ", ".join(str(x) for x in missing[:8]))
    return False, "", evidence


def _content_source_for_missing_doc(root: Path, filename: str) -> dict[str, str] | None:
    """
    Real project data that can seed a missing required doc.
    Returns None when inventing content would be required.
    """
    key = filename.lower()
    # PROJECT_CONTEXT can be seeded from substantive README or filled passport.
    if key == "project_context.md":
        for readme_name in ("README.md", "readme.md", "README.txt"):
            path = root / readme_name
            if path.is_file() and _md_has_substance(path):
                return {
                    "source": readme_name,
                    "target": f"docs/{filename}",
                    "filename": filename,
                }
        ok, rel, _ev = _passport_has_substance(root)
        if ok and rel:
            return {
                "source": rel,
                "target": f"docs/{filename}",
                "filename": filename,
            }
    return None


def _proposal_extra(item: dict[str, Any], **extra: Any) -> dict[str, Any]:
    item.update(extra)
    return item


def _root_dir_names(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    try:
        return {p.name.lower() for p in root.iterdir()}
    except OSError:
        return set()


def _file_fingerprint(path: Path) -> str | None:
    """Content fingerprint for duplicate confirmation. None if unreadable."""
    try:
        if not path.is_file():
            return None
        size = path.stat().st_size
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            remaining = min(size, 2_000_000)
            while remaining > 0:
                chunk = fh.read(min(65536, remaining))
                if not chunk:
                    break
                digest.update(chunk)
                remaining -= len(chunk)
            if size > 2_000_000:
                fh.seek(max(0, size - 65536))
                digest.update(fh.read(65536))
                digest.update(str(size).encode("ascii"))
        return f"{size}:{digest.hexdigest()}"
    except OSError:
        return None


def _purpose_by_path(tree: list[dict[str, Any]]) -> dict[str, tuple[str, bool]]:
    out: dict[str, tuple[str, bool]] = {}
    for node in _iter_tree_nodes(tree):
        if node.get("kind") != "file":
            continue
        path = str(node.get("path") or "").replace("\\", "/")
        if not path:
            continue
        out[path] = (
            str(node.get("purpose") or UNKNOWN_PURPOSE),
            bool(node.get("purpose_confirmed")),
        )
    return out


def _classify_same_name_groups(
    root: Path,
    tree: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Same basename is not enough.
    - content match or same confirmed purpose → review as real overlap
    - otherwise → informational «одноимённые в разных разделах», no fix advice
    """
    by_name: dict[str, list[str]] = {}
    for node in _iter_tree_nodes(tree):
        if node.get("kind") != "file":
            continue
        name = str(node.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in {"thumbs.db", ".ds_store", "desktop.ini"}:
            continue
        path = str(node.get("path") or name).replace("\\", "/")
        by_name.setdefault(key, []).append(path)

    purposes = _purpose_by_path(tree)
    content_or_purpose: list[dict[str, Any]] = []
    name_only: list[dict[str, Any]] = []

    for name, paths in sorted(by_name.items(), key=lambda item: (-len(item[1]), item[0])):
        if len(paths) < 2:
            continue
        fps: dict[str, list[str]] = {}
        for rel in paths:
            fp = _file_fingerprint(root / rel)
            if fp:
                fps.setdefault(fp, []).append(rel)
        content_groups = [g for g in fps.values() if len(g) >= 2]
        confirmed_purposes: dict[str, list[str]] = {}
        for rel in paths:
            purpose, confirmed = purposes.get(rel, (UNKNOWN_PURPOSE, False))
            if confirmed and purpose != UNKNOWN_PURPOSE:
                confirmed_purposes.setdefault(purpose, []).append(rel)
        purpose_groups = [g for g in confirmed_purposes.values() if len(g) >= 2]

        if content_groups or purpose_groups:
            details: list[str] = []
            for group in content_groups[:3]:
                details.append("одинаковое содержимое: " + ", ".join(group[:4]))
            for purpose, group in list(confirmed_purposes.items())[:3]:
                if len(group) >= 2:
                    details.append(f"одинаковое назначение «{purpose}»: " + ", ".join(group[:4]))
            content_or_purpose.append(
                {
                    "name": name,
                    "paths": paths,
                    "details": details,
                }
            )
        else:
            name_only.append({"name": name, "paths": paths})

    return content_or_purpose, name_only


def _is_confirmed_backup_file(root: Path, rel: str) -> bool:
    """Backup confirmed by name markers + readable non-empty (or empty) file on disk."""
    path = root / rel
    if not path.is_file():
        return False
    key = path.name.lower()
    if not (
        ".backup." in key
        or key.endswith(".bak")
        or key.endswith(".backup")
        or key.endswith("~")
        or ".backup" in key
    ):
        return False
    try:
        return path.stat().st_size >= 0
    except OSError:
        return False


def _collect_confirmed_backups(root: Path, tree: list[dict[str, Any]]) -> list[str]:
    """Confirmed backups still in the working area (not already under archive/)."""
    paths: list[str] = []
    for node in _iter_tree_nodes(tree):
        if node.get("kind") != "file":
            continue
        rel = str(node.get("path") or "").replace("\\", "/")
        if not rel:
            continue
        # Already archived — do not propose moving again.
        if rel == "archive" or rel.startswith("archive/"):
            continue
        if _is_confirmed_backup_file(root, rel):
            paths.append(rel)
    seen: set[str] = set()
    out: list[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _collect_unconfirmed(tree: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for node in _iter_tree_nodes(tree):
        if node.get("purpose_confirmed"):
            continue
        path = str(node.get("path") or node.get("name") or "").replace("\\", "/")
        if path:
            paths.append(path)
    return paths


def _empty_diagnostics() -> dict[str, Any]:
    return {
        "can_setup": [],
        "needs_review": [],
        "insufficient": [],
        "setup_actions": [],
        "bucket_labels": dict(BUCKET_LABELS),
    }


def _build_recommendations(
    root: Path,
    tree: list[dict[str, Any]],
    counters: dict[str, int],
    category_counts: dict[str, int],
) -> list[dict[str, Any]]:
    """Backward-compatible flat list: setup items first, then review, then insufficient."""
    diag = _build_diagnostics(root, tree, counters, category_counts)
    return list(diag.get("can_setup") or []) + list(diag.get("needs_review") or []) + list(
        diag.get("insufficient") or []
    )


def _build_diagnostics(
    root: Path,
    tree: list[dict[str, Any]],
    counters: dict[str, int],
    category_counts: dict[str, int],
) -> dict[str, Any]:
    """
    Read-only diagnostics. Never writes to disk.
    Buckets:
      - can_setup: confirmed actions allowed for Stage C
      - needs_review: facts to inspect (no auto-setup)
      - insufficient: analysis gaps (not setup actions)
    """
    can_setup: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    insufficient: list[dict[str, Any]] = []
    names = _root_dir_names(root)

    # --- Confirmed backups → Stage C setup only ---
    confirmed_backups = _collect_confirmed_backups(root, tree)
    has_archive = "archive" in names or "archives" in names or "backups" in names
    if confirmed_backups and not has_archive:
        can_setup.append(
            _proposal(
                pid="folder_archive",
                title="Создать папку archive для резервных копий",
                reason=(
                    f"Подтверждены резервные копии ({len(confirmed_backups)}): "
                    + ", ".join(confirmed_backups[:6])
                    + (f" и ещё {len(confirmed_backups) - 6}" if len(confirmed_backups) > 6 else "")
                    + ". Папки archive в корне нет — её нужно создать перед переносом."
                ),
                kind="create_folder",
                bucket=BUCKET_SETUP,
                setup_allowed=True,
                target="archive",
                evidence=["missing: archive"] + confirmed_backups[:20],
                paths=["archive"],
            )
        )
    if confirmed_backups:
        can_setup.append(
            _proposal(
                pid="backups_to_archive",
                title=(
                    f"Перенести {len(confirmed_backups)} подтверждённые резервные копии "
                    "в archive"
                ),
                reason=(
                    "По имени и наличию на диске подтверждены резервные копии: "
                    + ", ".join(confirmed_backups)
                    + ". Их можно перенести в папку archive, без удаления."
                ),
                kind="move_archive",
                bucket=BUCKET_SETUP,
                setup_allowed=True,
                target="archive",
                evidence=confirmed_backups,
                paths=confirmed_backups,
            )
        )

    # --- Missing structure / docs → review only (not Stage C yet) ---
    if ".ai-pos" not in names:
        needs_review.append(
            _proposal(
                pid="folder_ai_pos",
                title="Нет служебной папки AI POS (.ai-pos)",
                reason=(
                    "В корне проекта нет папки .ai-pos. "
                    "Это наблюдение для проверки; автоматическая настройка пока не включена."
                ),
                kind="review",
                bucket=BUCKET_REVIEW,
                evidence=["missing: .ai-pos"],
            )
        )

    if "docs" not in names:
        root_md: list[str] = []
        try:
            root_md = [
                p.name
                for p in root.iterdir()
                if p.is_file() and p.suffix.lower() == ".md"
            ]
        except OSError:
            root_md = []
        if len(root_md) >= 4:
            needs_review.append(
                _proposal(
                    pid="folder_docs",
                    title="Много документов в корне без папки docs",
                    reason=(
                        f"В корне {len(root_md)} markdown-файлов, папки docs нет. "
                        "Стоит проверить, нужна ли отдельная папка документов."
                    ),
                    kind="review",
                    bucket=BUCKET_REVIEW,
                    evidence=[f"root_md_count={len(root_md)}", "missing: docs"],
                )
            )

    # Required project docs: only root / docs/ (not portfolio-projects/ etc.).
    for filename, _title, human in AI_POS_DOC_CHECKS:
        hits = [h for h in _find_named_file(root, filename) if _md_has_substance(root / h)]
        if hits:
            continue
        weak_hits = _find_named_file(root, filename)
        source = _content_source_for_missing_doc(root, filename)
        evidence = [f"missing: {filename}", f"missing: docs/{filename}"]
        if weak_hits:
            evidence.append("found_but_empty: " + ", ".join(weak_hits))
        # Informational: nested copies are not project docs.
        nested = root / "portfolio-projects" / filename
        if nested.is_file():
            evidence.append(
                "ignored_nested: portfolio-projects/"
                + filename
                + " (не документ всего проекта)"
            )

        needs_review.append(
            _proposal_extra(
                _proposal(
                    pid=f"doc_missing_{filename.lower().replace('.', '_')}",
                    title=f"Не найден обязательный документ: {filename}",
                    reason=(
                        f"Нет содержательного {human} («{filename}») в корне или docs/. "
                        "Вложенные папки вроде portfolio-projects/ не засчитываются."
                    ),
                    kind="review",
                    bucket=BUCKET_REVIEW,
                    evidence=evidence,
                ),
                mandatory=True,
            )
        )

        if source:
            can_setup.append(
                _proposal_extra(
                    _proposal(
                        pid=f"create_doc_{filename.lower().replace('.', '_')}",
                        title=f"Создать {filename} из данных проекта",
                        reason=(
                            f"Есть реальный источник «{source['source']}». "
                            f"Можно создать «{source['target']}» без выдуманных сведений."
                        ),
                        kind="create_doc",
                        bucket=BUCKET_SETUP,
                        setup_allowed=True,
                        target=source["target"],
                        evidence=[f"source: {source['source']}", f"target: {source['target']}"],
                        paths=[source["target"]],
                    ),
                    content_source=source["source"],
                    filename=filename,
                    mandatory=True,
                )
            )
        else:
            insufficient.append(
                _proposal_extra(
                    _proposal(
                        pid=f"doc_need_user_{filename.lower().replace('.', '_')}",
                        title=f"Нужны сведения для создания {filename}",
                        reason=(
                            f"Обязательный документ «{filename}» отсутствует в корне/docs/, "
                            "а достаточных данных проекта для его заполнения нет. "
                            "Запросите сведения у пользователя — пустой файл создаваться не будет."
                        ),
                        kind="need_user",
                        bucket=BUCKET_INSUFFICIENT,
                        evidence=evidence,
                    ),
                    mandatory=True,
                )
            )

    arch_hits = _find_named_file(root, "ARCHITECTURE.md")
    if arch_hits:
        for rel in arch_hits[:1]:
            if not _md_has_substance(root / rel):
                needs_review.append(
                    _proposal_extra(
                        _proposal(
                            pid="architecture_stub",
                            title="Описание архитектуры почти пустое",
                            reason=(
                                f"Файл «{rel}» найден, но почти без содержания. "
                                "Нужна проверка и заполнение."
                            ),
                            kind="review",
                            bucket=BUCKET_REVIEW,
                            evidence=[rel, "body_lines<2"],
                        ),
                        mandatory=True,
                    )
                )

    passport_ok, passport_rel, passport_evidence = _passport_has_substance(root)
    if not passport_ok:
        insufficient.append(
            _proposal_extra(
                _proposal(
                    pid="passport_need_user",
                    title="Нужны сведения паспорта проекта",
                    reason=(
                        "Паспорт не подтверждён: нет содержательного PROJECT_PASSPORT.md "
                        "и в .ai-pos/project_passport.json нет заполненных полей "
                        "(название, цель, результат и т.п.). "
                        "Запросите сведения у пользователя."
                    ),
                    kind="need_user",
                    bucket=BUCKET_INSUFFICIENT,
                    evidence=passport_evidence
                    or [
                        "missing: PROJECT_PASSPORT.md",
                        "missing_or_empty: .ai-pos/project_passport.json",
                    ],
                ),
                mandatory=True,
            )
        )
    elif passport_rel:
        # Keep silent when ok — no noise in review.
        pass

    # --- Same-name groups ---
    confirmed_overlap, name_only = _classify_same_name_groups(root, tree)
    if confirmed_overlap:
        samples = []
        for item in confirmed_overlap[:5]:
            detail = "; ".join(item.get("details") or []) or ", ".join(item["paths"][:3])
            samples.append(f"{item['name']}: {detail}")
        needs_review.append(
            _proposal(
                pid="duplicates_confirmed",
                title=(
                    f"Файлы с совпадающим содержимым или назначением "
                    f"({len(confirmed_overlap)} групп)"
                ),
                reason=(
                    "Совпадение подтверждено по содержимому или одинаковому назначению. "
                    "Примеры: " + " | ".join(samples)
                ),
                kind="review_duplicates",
                bucket=BUCKET_REVIEW,
                evidence=[
                    f"{i['name']}:{'|'.join(i['paths'][:6])}" for i in confirmed_overlap[:15]
                ],
            )
        )
    if name_only:
        samples = []
        for item in name_only[:6]:
            samples.append(f"{item['name']} → {', '.join(item['paths'][:3])}")
        needs_review.append(
            _proposal(
                pid="same_name_different_sections",
                title="Одноимённые файлы в разных разделах проекта",
                reason=(
                    "Имена совпадают, но содержимое и назначение не подтверждены как одинаковые. "
                    "Это не рекомендация исправлять — только факт для сведения. "
                    "Примеры: " + "; ".join(samples)
                    + ("…" if len(name_only) > 6 else "")
                ),
                kind="info",
                bucket=BUCKET_REVIEW,
                evidence=[f"{i['name']}:{'|'.join(i['paths'][:6])}" for i in name_only[:20]],
            )
        )

    if "index.html" not in names and "src" not in names and "app" not in names:
        needs_review.append(
            _proposal(
                pid="entry_missing",
                title="Не найдена очевидная точка входа",
                reason=(
                    "В корне нет index.html и нет папок src / app. "
                    "Требуется проверка, с какого файла начинается приложение."
                ),
                kind="review",
                bucket=BUCKET_REVIEW,
                evidence=["missing: index.html", "missing: src", "missing: app"],
            )
        )

    if counters.get("truncated"):
        needs_review.append(
            _proposal(
                pid="map_truncated",
                title="Карта проекта показана частично",
                reason=(
                    "Обход остановлен по лимиту. "
                    f"Папок: {counters.get('folders', 0)}, файлов: {counters.get('files', 0)}."
                ),
                kind="info",
                bucket=BUCKET_REVIEW,
                evidence=[
                    f"folders={counters.get('folders', 0)}",
                    f"files={counters.get('files', 0)}",
                    "truncated=true",
                ],
            )
        )

    # --- Unconfirmed purposes: analysis only, not a setup action ---
    unconfirmed = _collect_unconfirmed(tree)
    if unconfirmed:
        sample = ", ".join(unconfirmed[:8])
        more = len(unconfirmed) - 8
        insufficient.append(
            _proposal(
                pid="unconfirmed_purposes",
                title=f"Назначение не подтверждено ({len(unconfirmed)} элементов)",
                reason=(
                    "Это результат анализа, не действие настройки. "
                    "Элементы оставлены без изменений. Примеры: "
                    + sample
                    + (f" и ещё {more}" if more > 0 else "")
                    + "."
                ),
                kind="analysis",
                bucket=BUCKET_INSUFFICIENT,
                evidence=unconfirmed[:40],
            )
        )

    setup_actions = [item for item in can_setup if item.get("setup_allowed")]
    return {
        "can_setup": can_setup,
        "needs_review": needs_review,
        "insufficient": insufficient,
        "setup_actions": setup_actions,
        "bucket_labels": dict(BUCKET_LABELS),
    }


def build_structure_map(
    project_path: str,
    *,
    include_recommendations: bool = False,
) -> dict[str, Any]:
    """
    Read-only structure map.
    Never writes to disk.
    """
    raw = str(project_path or "").strip()
    if not raw:
        return {
            "ok": False,
            "message": "Не указана рабочая папка проекта.",
            "wrote": False,
        }
    root = Path(raw)
    if not root.exists() or not root.is_dir():
        return {
            "ok": False,
            "message": "Папка проекта не найдена. Проверьте путь в настройках проекта.",
            "wrote": False,
        }

    counters = {"folders": 0, "files": 0, "entries": 0, "truncated": False}
    category_counts: dict[str, int] = {}
    tree: list[dict[str, Any]] = []

    for child in _safe_sorted_children(root):
        if counters["entries"] >= MAX_ENTRIES:
            counters["truncated"] = True
            break
        node = _walk(
            child,
            rel=child.name,
            depth=1,
            counters=counters,
            category_counts=category_counts,
        )
        if node is not None:
            tree.append(node)

    category_counts = _finalize_file_purposes(root, tree)

    payload: dict[str, Any] = {
        "ok": True,
        "message": None,
        "wrote": False,
        "project_path": str(root.resolve()),
        "folder_count": counters["folders"],
        "file_count": counters["files"],
        "truncated": bool(counters["truncated"]),
        "categories": [
            {
                "id": key,
                "label": CATEGORY_LABELS.get(key, key),
                "count": category_counts.get(key, 0),
            }
            for key in (
                CAT_ARCHITECTURE,
                CAT_CODE,
                CAT_DATA,
                CAT_IMAGES,
                CAT_DOCS,
                CAT_MATERIALS,
                CAT_SERVICE,
                CAT_BACKUPS,
                CAT_UNKNOWN,
            )
            if category_counts.get(key, 0) > 0
        ],
        "tree": tree,
        "user_sections": _build_user_sections(tree, category_counts),
    }
    if include_recommendations:
        diagnostics = _build_diagnostics(root, tree, counters, category_counts)
        payload["diagnostics"] = diagnostics
        payload["recommendations"] = (
            list(diagnostics.get("can_setup") or [])
            + list(diagnostics.get("needs_review") or [])
            + list(diagnostics.get("insufficient") or [])
        )
        payload["setup_actions"] = list(diagnostics.get("setup_actions") or [])
    else:
        payload["diagnostics"] = _empty_diagnostics()
        payload["recommendations"] = []
        payload["setup_actions"] = []
    return payload
