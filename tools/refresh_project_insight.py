#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal MVP Orchestrator.

Only coordinates:
  Stage Engine → Analyzer

Does not determine stage, analyze the project, or make product decisions.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
STAGE_ENGINE = TOOLS_DIR / "project_stage_engine.py"
ANALYZER = TOOLS_DIR / "project_analyzer.py"


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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.project_path).expanduser().resolve()

    def emit(*args: object) -> None:
        print(*args, flush=True)

    emit("AI POS Orchestrator (MVP minimal)")
    emit(f"Project: {root}")

    emit("--- Stage Engine ---")
    stage_code = run_component(STAGE_ENGINE, root)
    if stage_code != 0:
        print(
            "Orchestrator stopped: Stage Engine failed. Analyzer was not started.",
            file=sys.stderr,
            flush=True,
        )
        return stage_code

    emit("--- Analyzer ---")
    analyzer_code = run_component(ANALYZER, root)
    if analyzer_code != 0:
        print(
            "Orchestrator stopped: Analyzer failed.",
            file=sys.stderr,
            flush=True,
        )
        return analyzer_code

    stage_path = root / ".ai-pos" / "project_stage.json"
    analysis_path = root / ".ai-pos" / "project_analysis.json"
    # ASCII markers for Windows consoles that cannot print "✓".
    emit("[OK] Stage updated")
    emit("[OK] Analysis updated")
    emit(f"Stage JSON:    {stage_path}")
    emit(f"Analysis JSON: {analysis_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
