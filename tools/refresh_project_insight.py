#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal MVP Orchestrator.

Only coordinates:
  Stage Engine → Analyzer

Does not determine stage, analyze the project, or make product decisions.

Completes every run in one mode: NORMAL | DIAGNOSTIC | BLOCKED
(see Governance/ORCHESTRATOR.md §5).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


TOOLS_DIR = Path(__file__).resolve().parent
STAGE_ENGINE = TOOLS_DIR / "project_stage_engine.py"
ANALYZER = TOOLS_DIR / "project_analyzer.py"

RESULT_PREFIX = "AI_POS_ORCHESTRATOR_RESULT="

MODE_NORMAL = "NORMAL"
MODE_DIAGNOSTIC = "DIAGNOSTIC"
MODE_BLOCKED = "BLOCKED"

# Closed reason_code list (ORCHESTRATOR.md §5).
RC_ANALYZER_FAILED = "ANALYZER_FAILED"
RC_ANALYSIS_JSON_MISSING = "ANALYSIS_JSON_MISSING"
RC_ANALYSIS_INVALID = "ANALYSIS_INVALID"
RC_OPTIONAL_ADAPTER_UNAVAILABLE = "OPTIONAL_ADAPTER_UNAVAILABLE"  # reserved
RC_STAGE_TTL_REUSED = "STAGE_TTL_REUSED"  # reserved
RC_PROJECT_ROOT_INVALID = "PROJECT_ROOT_INVALID"
RC_STAGE_ENGINE_FAILED = "STAGE_ENGINE_FAILED"
RC_STAGE_JSON_MISSING = "STAGE_JSON_MISSING"
RC_STAGE_JSON_INVALID = "STAGE_JSON_INVALID"
RC_REQUIRED_INPUT_JSON_MISSING = "REQUIRED_INPUT_JSON_MISSING"  # reserved


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "AI POS orchestrator: run Stage Engine then Analyzer "
            "for one project path"
        )
    )
    parser.add_argument("project_path", help="Path to the project root directory")
    return parser.parse_args(argv)


def run_component(script: Path, project_path: Path) -> int:
    completed = subprocess.run(
        [sys.executable, str(script), str(project_path)],
        check=False,
    )
    return int(completed.returncode)


def stage_json_path(root: Path) -> Path:
    return root / ".ai-pos" / "project_stage.json"


def analysis_json_path(root: Path) -> Path:
    return root / ".ai-pos" / "project_analysis.json"


def load_json_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def validate_stage_payload(data: dict[str, Any] | None) -> bool:
    if not data:
        return False
    stage = data.get("stage")
    return stage is not None and stage != ""


def analysis_is_valid(data: dict[str, Any] | None) -> bool:
    if not data:
        return False
    if data.get("valid") is False:
        return False
    if data.get("status") == "invalid":
        return False
    stage = data.get("stage")
    if stage is None or stage == "":
        return False
    return True


def resolve_project_root(project_path: str | Path) -> tuple[Path | None, list[str]]:
    try:
        root = Path(project_path).expanduser().resolve()
    except OSError:
        return None, [RC_PROJECT_ROOT_INVALID]
    if not root.exists() or not root.is_dir():
        return None, [RC_PROJECT_ROOT_INVALID]
    return root, []


def decide_mode(reason_codes: list[str]) -> str:
    blocked = {
        RC_PROJECT_ROOT_INVALID,
        RC_STAGE_ENGINE_FAILED,
        RC_STAGE_JSON_MISSING,
        RC_STAGE_JSON_INVALID,
        RC_REQUIRED_INPUT_JSON_MISSING,
    }
    diagnostic = {
        RC_ANALYZER_FAILED,
        RC_ANALYSIS_JSON_MISSING,
        RC_ANALYSIS_INVALID,
        RC_OPTIONAL_ADAPTER_UNAVAILABLE,
        RC_STAGE_TTL_REUSED,
    }
    if any(code in blocked for code in reason_codes):
        return MODE_BLOCKED
    if any(code in diagnostic for code in reason_codes):
        return MODE_DIAGNOSTIC
    return MODE_NORMAL


def _dedupe(codes: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            ordered.append(code)
    return ordered


def remove_analysis_artifact(path: Path) -> None:
    """Drop previous-run analysis so the current run cannot reuse it."""
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        # Best-effort: Bridge still refuses ok:true on ANALYZER_FAILED.
        pass


def analyzer_script_from_env() -> Path | None:
    raw = (os.environ.get("AI_POS_ANALYZER_SCRIPT") or "").strip()
    if not raw:
        return None
    return Path(raw)


def run_insight(
    project_path: str | Path,
    *,
    stage_engine: Path | None = None,
    analyzer: Path | None = None,
) -> dict[str, Any]:
    """
    Run Engine → Analyzer and return structured orchestrator result.

    mode: NORMAL | DIAGNOSTIC | BLOCKED
    reason_codes: closed list from ORCHESTRATOR.md §5
    """
    engine_script = stage_engine or STAGE_ENGINE
    analyzer_script = analyzer or analyzer_script_from_env() or ANALYZER

    root, reasons = resolve_project_root(project_path)
    result: dict[str, Any] = {
        "mode": MODE_BLOCKED,
        "reason_codes": list(reasons),
        "project_path": str(project_path),
        "stage_engine_exit": None,
        "analyzer_exit": None,
        "stage_path": None,
        "analysis_path": None,
    }
    if root is None:
        result["reason_codes"] = _dedupe(result["reason_codes"])
        result["mode"] = decide_mode(result["reason_codes"])
        return result

    result["project_path"] = str(root)
    stage_path = stage_json_path(root)
    analysis_path = analysis_json_path(root)
    result["stage_path"] = str(stage_path)
    result["analysis_path"] = str(analysis_path)

    stage_code = run_component(engine_script, root)
    result["stage_engine_exit"] = stage_code
    if stage_code != 0:
        result["reason_codes"].append(RC_STAGE_ENGINE_FAILED)
        result["reason_codes"] = _dedupe(result["reason_codes"])
        result["mode"] = decide_mode(result["reason_codes"])
        return result

    stage_data = load_json_object(stage_path)
    if stage_data is None:
        if not stage_path.is_file():
            result["reason_codes"].append(RC_STAGE_JSON_MISSING)
        else:
            result["reason_codes"].append(RC_STAGE_JSON_INVALID)
        result["reason_codes"] = _dedupe(result["reason_codes"])
        result["mode"] = decide_mode(result["reason_codes"])
        return result
    if not validate_stage_payload(stage_data):
        result["reason_codes"].append(RC_STAGE_JSON_INVALID)
        result["reason_codes"] = _dedupe(result["reason_codes"])
        result["mode"] = decide_mode(result["reason_codes"])
        return result

    # Current run must not reuse analysis from a previous successful pass.
    remove_analysis_artifact(analysis_path)

    analyzer_code = run_component(analyzer_script, root)
    result["analyzer_exit"] = analyzer_code
    if analyzer_code != 0:
        result["reason_codes"].append(RC_ANALYZER_FAILED)

    analysis_data = load_json_object(analysis_path)
    if analysis_data is None:
        if not analysis_path.is_file():
            result["reason_codes"].append(RC_ANALYSIS_JSON_MISSING)
        else:
            result["reason_codes"].append(RC_ANALYSIS_INVALID)
    elif not analysis_is_valid(analysis_data):
        result["reason_codes"].append(RC_ANALYSIS_INVALID)

    result["reason_codes"] = _dedupe(result["reason_codes"])
    result["mode"] = decide_mode(result["reason_codes"])
    return result


def emit_result_line(result: dict[str, Any]) -> None:
    print(RESULT_PREFIX + json.dumps(result, ensure_ascii=False), flush=True)


def parse_result_line(stdout: str) -> dict[str, Any] | None:
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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    def emit(*parts: object) -> None:
        print(*parts, flush=True)

    emit("AI POS Orchestrator (MVP minimal)")
    emit(f"Project: {args.project_path}")

    result = run_insight(args.project_path)
    mode = result["mode"]
    codes = result.get("reason_codes") or []

    if mode == MODE_BLOCKED:
        if RC_PROJECT_ROOT_INVALID in codes:
            print(
                "Orchestrator BLOCKED: project root is invalid.",
                file=sys.stderr,
                flush=True,
            )
        elif RC_STAGE_ENGINE_FAILED in codes:
            print(
                "Orchestrator BLOCKED: Stage Engine failed. Analyzer was not started.",
                file=sys.stderr,
                flush=True,
            )
        elif RC_STAGE_JSON_MISSING in codes or RC_STAGE_JSON_INVALID in codes:
            print(
                "Orchestrator BLOCKED: project_stage.json missing or invalid. "
                "Analyzer was not started.",
                file=sys.stderr,
                flush=True,
            )
        else:
            print("Orchestrator BLOCKED.", file=sys.stderr, flush=True)
        emit(f"Mode: {mode}")
        emit(f"Reason codes: {', '.join(codes) if codes else '—'}")
        emit_result_line(result)
        return 1

    if mode == MODE_DIAGNOSTIC:
        print(
            "Orchestrator DIAGNOSTIC: non-blocking problems present.",
            file=sys.stderr,
            flush=True,
        )
        emit("[OK] Stage updated")
        emit("[WARN] Analysis incomplete or invalid")
        emit(f"Stage JSON:    {result.get('stage_path')}")
        emit(f"Analysis JSON: {result.get('analysis_path')}")
        emit(f"Mode: {mode}")
        emit(f"Reason codes: {', '.join(codes) if codes else '—'}")
        emit_result_line(result)
        return 0

    emit("[OK] Stage updated")
    emit("[OK] Analysis updated")
    emit(f"Stage JSON:    {result.get('stage_path')}")
    emit(f"Analysis JSON: {result.get('analysis_path')}")
    emit(f"Mode: {mode}")
    emit_result_line(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
