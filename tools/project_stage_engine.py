#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal MVP Stage Engine (temporary).

Determines one of: IDEA | INTAKE | DISCOVERY | PLANNING | EXECUTION
using file presence AND a simple substantive-content check.
Stub/template files (title-only, placeholders) do not raise the stage.
EXECUTION is set when planning markers exist and a runtime app signal is present.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = "ai-pos.project_stage/v1"
ENGINE_ID = "project_stage_engine_mvp_min"

MIN_BODY_CHARS = 80
MIN_BODY_LINES = 2
STUB_MARKER_RE = re.compile(
    r"(?i)\bTODO\b|\bTBD\b|заполните"
)

MARKERS = {
    "context": ("PROJECT_CONTEXT.md", "README.md"),
    "roadmap": ("ROADMAP.md",),
    "structure": (
        "ARCHITECTURE.md",
        "DESIGN_RULES.md",
        "DATA_SCHEMA.md",
        "DECISIONS.md",
    ),
}

# Root first, then docs/ (pilot: Мой день keeps structure docs under docs/).
MARKER_LOCATIONS = ("", "docs")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def path_exists(root: Path, relative: str) -> bool:
    return (root / relative).is_file()


def strip_front_matter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :]
    return text


def body_lines(text: str) -> list[str]:
    text = strip_front_matter(text)
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.match(r"^#{1,6}\s+", line):
            continue
        lines.append(line)
    return lines


def has_explicit_stub_marker(text: str) -> bool:
    return STUB_MARKER_RE.search(text) is not None


def is_substantive(path: Path) -> bool:
    """
    Minimal non-AI content check:
    - ignore YAML front matter;
    - ignore markdown headings and empty lines;
    - substantive if remaining body has >= 80 chars OR >= 2 body lines;
    - TODO / TBD / «заполните» do not automatically force stub:
      after removing those markers, the same thresholds apply.
      Marker-only / near-empty leftovers stay stub.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False

    lines = body_lines(text)
    if not lines:
        return False

    if has_explicit_stub_marker(text):
        cleaned_lines: list[str] = []
        for line in lines:
            cleaned = STUB_MARKER_RE.sub("", line)
            cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:;\t")
            if cleaned:
                cleaned_lines.append(cleaned)
        lines = cleaned_lines
        if not lines:
            return False

    body = "\n".join(lines).strip()
    if not body:
        return False

    if len(body) >= MIN_BODY_CHARS:
        return True
    if len(lines) >= MIN_BODY_LINES:
        return True
    return False


def resolve_marker_file(root: Path, name: str) -> tuple[Path, str] | None:
    """Return (path, relative_label) for the first existing marker location."""
    for location in MARKER_LOCATIONS:
        path = root / name if location == "" else root / location / name
        if path.is_file():
            label = name if location == "" else f"{location}/{name}"
            return path, label
    return None


def classify_marker_files(root: Path, names: tuple[str, ...]) -> tuple[list[str], list[str]]:
    substantive: list[str] = []
    stubs: list[str] = []
    for name in names:
        resolved = resolve_marker_file(root, name)
        if not resolved:
            continue
        path, label = resolved
        if is_substantive(path):
            substantive.append(label)
        else:
            stubs.append(label)
    return substantive, stubs


def has_runtime_app_signal(root: Path) -> bool:
    """Pilot signal: working web app layout without claiming EXECUTION stage yet."""
    has_entry = (root / "index.html").is_file()
    has_assets = (root / "js").is_dir() or (root / "css").is_dir()
    return has_entry and has_assets


def collect_presence(root: Path) -> dict:
    context_sub, context_stubs = classify_marker_files(root, MARKERS["context"])
    roadmap_sub, roadmap_stubs = classify_marker_files(root, MARKERS["roadmap"])
    structure_sub, structure_stubs = classify_marker_files(root, MARKERS["structure"])

    all_stubs = context_stubs + roadmap_stubs + structure_stubs

    return {
        "context_hits": context_sub,
        "roadmap_hits": roadmap_sub,
        "structure_hits": structure_sub,
        "context_stubs": context_stubs,
        "roadmap_stubs": roadmap_stubs,
        "structure_stubs": structure_stubs,
        "stub_files": all_stubs,
        "has_context": bool(context_sub),
        "has_roadmap": bool(roadmap_sub),
        "structure_count": len(structure_sub),
        "has_any_stub": bool(all_stubs),
        "has_any_file_marker": bool(context_sub or roadmap_sub or structure_sub or all_stubs),
        "has_runtime_app": has_runtime_app_signal(root),
    }


def determine_stage(
    presence: dict,
) -> tuple[str, str, str, list[dict], list[dict], list[dict], dict]:
    """
    Same stage ladder as before, but only substantive files count.

    IDEA — no substantive context and no substantive ROADMAP
    Returns: stage, label, confidence, evidence, blockers, conflicting, next_step
    """
    evidence: list[dict] = []
    blockers: list[dict] = []
    conflicting: list[dict] = []

    has_context = presence["has_context"]
    has_roadmap = presence["has_roadmap"]
    structure_count = presence["structure_count"]

    for name in presence["context_hits"]:
        evidence.append(
            {
                "code": "FILE_CONTEXT_SUBSTANTIVE",
                "text": f"Содержательный контекст: {name}",
                "trust": "system-confirmed",
                "source": "fs",
            }
        )
    for name in presence["context_stubs"]:
        evidence.append(
            {
                "code": "FILE_CONTEXT_STUB",
                "text": f"Контекст-заглушка (не повышает стадию): {name}",
                "trust": "system-confirmed",
                "source": "fs",
            }
        )
    for name in presence["structure_hits"]:
        evidence.append(
            {
                "code": "FILE_STRUCTURE_SUBSTANTIVE",
                "text": f"Содержательный структурный документ: {name}",
                "trust": "system-confirmed",
                "source": "fs",
            }
        )
    for name in presence["structure_stubs"]:
        evidence.append(
            {
                "code": "FILE_STRUCTURE_STUB",
                "text": f"Структурная заглушка (не повышает стадию): {name}",
                "trust": "system-confirmed",
                "source": "fs",
            }
        )
    for name in presence["roadmap_hits"]:
        evidence.append(
            {
                "code": "FILE_ROADMAP_SUBSTANTIVE",
                "text": f"Содержательный план: {name}",
                "trust": "system-confirmed",
                "source": "fs",
            }
        )
    for name in presence["roadmap_stubs"]:
        evidence.append(
            {
                "code": "FILE_ROADMAP_STUB",
                "text": f"План-заглушка (не повышает стадию): {name}",
                "trust": "system-confirmed",
                "source": "fs",
            }
        )

    if not has_context and not has_roadmap:
        stage = "IDEA"
        label = "Идея"
        # If we only see stubs, we are sure there is no real content yet.
        confidence = "CONFIRMED" if presence["has_any_stub"] or not presence["has_any_file_marker"] else "PROVISIONAL"
        if not presence["context_hits"] and not presence["roadmap_hits"] and not presence["stub_files"]:
            evidence.append(
                {
                    "code": "NO_MARKERS",
                    "text": "Не найдены PROJECT_CONTEXT.md / README.md / ROADMAP.md в корне или docs/",
                    "trust": "system-confirmed",
                    "source": "fs",
                }
            )
        elif presence["has_any_stub"] and not has_context and not has_roadmap:
            blockers.append(
                {
                    "text": "Есть файлы-заглушки; нужно заполнить содержательный PROJECT_CONTEXT.md или README.md"
                }
            )
        else:
            blockers.append({"text": "Нужно указать цель проекта и базовые документы"})
        if not blockers:
            blockers.append({"text": "Нужно указать цель проекта и базовые документы"})
        next_step = {
            "text": "Заполнить PROJECT_CONTEXT.md или README.md реальным описанием цели",
            "action_hint": "create_context",
        }
    elif has_context and structure_count == 0 and not has_roadmap:
        stage = "INTAKE"
        label = "Подключение"
        confidence = "CONFIRMED"
        blockers.append({"text": "Мало содержательных документов о составе проекта"})
        next_step = {
            "text": "Добавить содержательный структурный документ (например ARCHITECTURE.md)",
            "action_hint": "add_structure_doc",
        }
    elif has_context and structure_count >= 1 and not has_roadmap:
        stage = "DISCOVERY"
        label = "Изучение"
        confidence = "CONFIRMED"
        blockers.append({"text": "Нет содержательного ROADMAP.md — план работ ещё не зафиксирован"})
        next_step = {
            "text": "Просмотреть найденные документы и заполнить ROADMAP.md",
            "action_hint": "add_roadmap",
        }
    else:
        # ROADMAP present (planning ladder). Runtime app => EXECUTION (pilot: Мой день).
        if presence.get("has_runtime_app"):
            evidence.append(
                {
                    "code": "APP_RUNTIME_SIGNAL",
                    "text": "Обнаружены признаки работающего приложения: index.html и js/ или css/",
                    "trust": "system-confirmed",
                    "source": "fs",
                }
            )
            stage = "EXECUTION"
            label = "Выполнение"
            confidence = "CONFIRMED" if has_context else "PROVISIONAL"
            if not has_context:
                blockers.append(
                    {
                        "text": "Приложение уже есть, но содержательный контекст ещё неполный"
                    }
                )
                next_step = {
                    "text": "Заполнить PROJECT_CONTEXT.md / README и зафиксировать текущую задачу модуля",
                    "action_hint": "add_context",
                }
            else:
                next_step = {
                    "text": "Продолжить текущую задачу модуля и проверить результат",
                    "action_hint": "continue_module_task",
                }
        else:
            stage = "PLANNING"
            label = "Планирование"
            confidence = "CONFIRMED" if has_context else "PROVISIONAL"
            if not has_context:
                blockers.append(
                    {"text": "Есть содержательный ROADMAP, но нет содержательного контекста"}
                )
                next_step = {
                    "text": "Заполнить PROJECT_CONTEXT.md и уточнить текущую задачу",
                    "action_hint": "add_context",
                }
            else:
                next_step = {
                    "text": "Определить текущую задачу для исполнения",
                    "action_hint": "define_task",
                }

    # Runtime app without roadmap/planning ladder yet — do not jump to EXECUTION.
    if presence.get("has_runtime_app") and stage in {"IDEA", "INTAKE", "DISCOVERY"}:
        evidence.append(
            {
                "code": "APP_RUNTIME_SIGNAL",
                "text": "Обнаружены признаки работающего приложения: index.html и js/ или css/",
                "trust": "system-confirmed",
                "source": "fs",
            }
        )
        conflicting.append(
            {
                "code": "RUNTIME_BEFORE_PLAN",
                "text": (
                    "Есть каркас приложения, но содержательный ROADMAP ещё не зафиксирован; "
                    "стадия остаётся ранней."
                ),
                "trust": "system-confirmed",
                "source": "stage_engine",
            }
        )
        if confidence == "CONFIRMED":
            confidence = "PROVISIONAL"

    return stage, label, confidence, evidence, blockers, conflicting, next_step


def build_result(root: Path, presence: dict) -> dict:
    stage, label, confidence, evidence, blockers, conflicting, next_step = determine_stage(
        presence
    )
    return {
        "schema": SCHEMA,
        "stage": stage,
        "stage_label": label,
        "confidence_state": confidence,
        "evidence": evidence,
        "conflicting_evidence": conflicting,
        "blockers": blockers,
        "next_step": next_step,
        "inappropriate_actions": [],
        "detected_at": utc_now_iso(),
        "source_freshness": {
            "snapshot_at": utc_now_iso(),
            "state_at": None,
            "stale": False,
        },
        "workstreams": [],
        "global_stage": stage,
        "dominant_stage": stage,
        "blocking_stage": stage,
        "override": None,
        "engine": ENGINE_ID,
        "project_root": str(root.resolve()),
        "mvp_note": (
            "Temporary minimal Stage Engine (IDEA..EXECUTION). "
            "Only substantive files raise stage; stubs do not. "
            "EXECUTION requires roadmap ladder + runtime app signal."
        ),
        "presence": {
            "context_hits": presence["context_hits"],
            "roadmap_hits": presence["roadmap_hits"],
            "structure_hits": presence["structure_hits"],
            "context_stubs": presence["context_stubs"],
            "roadmap_stubs": presence["roadmap_stubs"],
            "structure_stubs": presence["structure_stubs"],
            "stub_files": presence["stub_files"],
            "has_runtime_app": presence.get("has_runtime_app", False),
            "marker_locations": list(MARKER_LOCATIONS),
        },
        "substantive_rules": {
            "min_body_chars": MIN_BODY_CHARS,
            "min_body_lines": MIN_BODY_LINES,
        },
    }


def atomic_write_text(path: Path, text: str) -> None:
    """Write via filename.tmp then atomic replace of the target file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def write_stage_json(root: Path, payload: dict) -> Path:
    out_dir = root / ".ai-pos"
    out_path = out_dir / "project_stage.json"
    atomic_write_text(
        out_path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )
    return out_path


def print_result(payload: dict, out_path: Path) -> None:
    print("Project Stage Engine (MVP minimal)")
    print(f"Project:     {payload['project_root']}")
    print(f"Stage:       {payload['stage']} ({payload['stage_label']})")
    print(f"Confidence:  {payload['confidence_state']}")
    stubs = payload.get("presence", {}).get("stub_files") or []
    if stubs:
        print(f"Stubs:       {', '.join(stubs)}")
    print(f"Next step:   {payload['next_step']['text']}")
    if payload["blockers"]:
        print("Blockers:")
        for item in payload["blockers"]:
            print(f"  - {item['text']}")
    print(f"Written:     {out_path}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Minimal AI POS Stage Engine: write .ai-pos/project_stage.json"
    )
    parser.add_argument(
        "project_path",
        help="Path to the project root directory",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.project_path).expanduser().resolve()

    if not root.exists():
        print(f"Error: path does not exist: {root}", file=sys.stderr)
        return 1
    if not root.is_dir():
        print(f"Error: path is not a directory: {root}", file=sys.stderr)
        return 1

    presence = collect_presence(root)
    payload = build_result(root, presence)
    out_path = write_stage_json(root, payload)
    print_result(payload, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
