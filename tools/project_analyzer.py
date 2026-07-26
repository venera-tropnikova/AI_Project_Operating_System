#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal MVP project_analyzer.

Reads .ai-pos/project_stage.json and writes .ai-pos/project_analysis.json.
Does not determine or modify stage.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from project_stage_engine import (  # noqa: E402
    MARKERS,
    atomic_write_text,
    is_substantive,
    resolve_marker_file,
)


SCHEMA = "ai-pos.project_analysis/v1"
ANALYZER_ID = "project_analyzer_mvp_min"
STAGE_REL = Path(".ai-pos") / "project_stage.json"
ANALYSIS_REL = Path(".ai-pos") / "project_analysis.json"

STAGE_EXPLANATIONS = {
    "IDEA": (
        "Проект на стадии идеи: содержательного описания цели ещё нет "
        "(или есть только заглушки)."
    ),
    "INTAKE": (
        "Проект на стадии подключения: базовый контекст есть, "
        "но состав проекта ещё слабо описан."
    ),
    "DISCOVERY": (
        "Проект на стадии изучения: контекст и структура появляются, "
        "но содержательный план работ ещё не зафиксирован."
    ),
    "PLANNING": (
        "Проект на стадии планирования: есть содержательный контекст и план, "
        "но явного каркаса работающего приложения ещё не видно."
    ),
    "EXECUTION": (
        "Проект на стадии выполнения: есть план/контекст и признаки "
        "работающего приложения (index.html и js/ или css/)."
    ),
}

KNOWN_DOCS = tuple(
    dict.fromkeys(
        MARKERS["context"] + MARKERS["roadmap"] + MARKERS["structure"]
    )
)


def load_stage(root: Path) -> dict:
    path = root / STAGE_REL
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing {path}. Run Stage Engine first. "
            "Analyzer does not determine stage."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Invalid stage payload in {path}: expected object")
    if not data.get("stage"):
        raise ValueError(
            f"No stage field in {path}. Analyzer does not determine stage."
        )
    return data


def list_project_files(root: Path) -> list[str]:
    names: list[str] = []
    for path in sorted(root.iterdir()):
        if path.name.startswith("."):
            continue
        if path.is_file():
            names.append(path.name)
    return names


def classify_known_docs(root: Path) -> tuple[list[str], list[str]]:
    substantive: list[str] = []
    stubs: list[str] = []
    for name in KNOWN_DOCS:
        resolved = resolve_marker_file(root, name)
        if not resolved:
            continue
        path, label = resolved
        if is_substantive(path):
            substantive.append(label)
        else:
            stubs.append(label)
    return substantive, stubs


def build_stage_explanation(stage: dict) -> str:
    stage_id = str(stage.get("stage"))
    label = stage.get("stage_label") or stage_id
    confidence = stage.get("confidence_state") or "UNKNOWN"
    evidence = stage.get("evidence") or []

    substantive_bits = [
        item.get("text")
        for item in evidence
        if isinstance(item, dict) and str(item.get("code", "")).endswith("_SUBSTANTIVE")
    ]
    stub_bits = [
        item.get("text")
        for item in evidence
        if isinstance(item, dict) and str(item.get("code", "")).endswith("_STUB")
    ]

    parts = [
        f"Стадия «{label}» ({stage_id}) уже назначена Stage Engine "
        f"с уверенностью {confidence}."
    ]
    meaning = STAGE_EXPLANATIONS.get(stage_id)
    if meaning:
        parts.append(meaning)
    if substantive_bits:
        parts.append("Основание: " + "; ".join(str(x) for x in substantive_bits[:4] if x) + ".")
    if stub_bits:
        parts.append(
            "Заглушки учтены, но не повысили стадию: "
            + "; ".join(str(x) for x in stub_bits[:4] if x)
            + "."
        )
    if not substantive_bits and not stub_bits:
        parts.append(
            "В project_stage.json мало evidence — показана только зафиксированная стадия."
        )
    return " ".join(parts)


def build_needs_attention(stage: dict, substantive: list[str], stubs: list[str]) -> list[str]:
    items: list[str] = []
    presence = stage.get("presence") or {}
    stage_stubs = list(presence.get("stub_files") or stubs)

    for name in stage_stubs:
        items.append(f"Заглушка (не содержательный документ): {name}")

    has_substantive_context = any(name in substantive for name in MARKERS["context"])
    has_substantive_roadmap = any(name in substantive for name in MARKERS["roadmap"])
    known = set(substantive) | set(stage_stubs)
    context_present = any(name in known for name in MARKERS["context"])

    # Missing core context only when no context file exists at all (stubs already listed).
    if not has_substantive_context and not context_present:
        items.append("Нет содержательного PROJECT_CONTEXT.md или README.md")

    if (
        stage.get("stage") in {"IDEA", "INTAKE", "DISCOVERY"}
        and not has_substantive_roadmap
        and "ROADMAP.md" not in known
    ):
        items.append("Нет содержательного ROADMAP.md")

    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def build_next_step(stage: dict) -> dict:
    raw = stage.get("next_step") or {}
    if not isinstance(raw, dict):
        raw = {}
    text = str(raw.get("text") or "").strip()
    action_hint = str(raw.get("action_hint") or "").strip()
    if not text:
        text = "Уточнить следующий шаг в Stage Engine"
        action_hint = action_hint or "refresh_stage"
    return {
        "text": (
            f"{text} "
            f"(шаг взят из project_stage.json, Analyzer его не заменяет)."
        ),
        "action_hint": action_hint or "follow_stage_next_step",
    }


def build_analysis(root: Path, stage: dict) -> dict:
    files = list_project_files(root)
    substantive, stubs = classify_known_docs(root)

    presence = stage.get("presence") or {}
    for key in ("context_hits", "roadmap_hits", "structure_hits"):
        for name in presence.get(key) or []:
            if name in substantive:
                continue
            path = root / name
            if path.is_file() and is_substantive(path):
                substantive.append(name)

    return {
        "schema": SCHEMA,
        "project_path": str(root.resolve()),
        "stage": stage["stage"],
        "confidence_state": stage.get("confidence_state"),
        "stage_explanation": build_stage_explanation(stage),
        "what_is_present": substantive,
        "needs_attention": build_needs_attention(stage, substantive, stubs),
        "next_step": build_next_step(stage),
        "analyzer": ANALYZER_ID,
        "project_files_top_level": files,
        "notes": (
            "Analyzer does not assign stage. "
            "Fields stage and confidence_state are copied from project_stage.json."
        ),
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_analysis(root: Path, payload: dict) -> Path:
    out_path = root / ANALYSIS_REL
    payload = dict(payload)
    payload.setdefault("status", "ok")
    payload.setdefault("valid", True)
    atomic_write_text(
        out_path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )
    return out_path


def invalidate_analysis(root: Path, error: str) -> Path:
    """
    Mark analysis invalid instead of leaving a previously successful file
    looking current. Safer than silent delete: operator sees an explicit
    failure marker rather than ambiguity between "never ran" and "failed".
    """
    out_path = root / ANALYSIS_REL
    payload = {
        "schema": SCHEMA,
        "project_path": str(root.resolve()),
        "status": "invalid",
        "valid": False,
        "stage": None,
        "confidence_state": None,
        "error": error,
        "invalidated_at": utc_now_iso(),
        "analyzer": ANALYZER_ID,
        "notes": (
            "Analysis is not current. Analyzer failed before producing a valid result. "
            "Do not treat this file as an active project summary."
        ),
    }
    atomic_write_text(
        out_path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )
    return out_path


def print_result(payload: dict, out_path: Path) -> None:
    print("Project Analyzer (MVP minimal)")
    print(f"Project:     {payload['project_path']}")
    print(f"Stage:       {payload['stage']} (from project_stage.json)")
    print(f"Confidence:  {payload['confidence_state']}")
    print(f"Present:     {', '.join(payload['what_is_present']) or '—'}")
    attention = payload["needs_attention"]
    print(f"Attention:   {len(attention)} item(s)")
    for item in attention[:6]:
        print(f"  - {item}")
    print(f"Next step:   {payload['next_step']['text']}")
    print(f"Written:     {out_path}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Minimal AI POS analyzer: write .ai-pos/project_analysis.json"
    )
    parser.add_argument("project_path", help="Path to the project root directory")
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

    try:
        stage = load_stage(root)
        payload = build_analysis(root, stage)
        out_path = write_analysis(root, payload)
    except FileNotFoundError as exc:
        message = str(exc)
        print(f"Error: {message}", file=sys.stderr)
        invalid_path = invalidate_analysis(root, message)
        print(f"Analysis invalidated: {invalid_path}", file=sys.stderr)
        return 2
    except ValueError as exc:
        message = str(exc)
        print(f"Error: {message}", file=sys.stderr)
        invalid_path = invalidate_analysis(root, message)
        print(f"Analysis invalidated: {invalid_path}", file=sys.stderr)
        return 2
    except OSError as exc:
        message = str(exc)
        print(f"Error: {message}", file=sys.stderr)
        try:
            invalid_path = invalidate_analysis(root, message)
            print(f"Analysis invalidated: {invalid_path}", file=sys.stderr)
        except OSError:
            pass
        return 2

    print_result(payload, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
