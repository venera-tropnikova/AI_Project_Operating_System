#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal MVP v0.1 regression / smoke checks.

Does not change Stage Engine rules. Verifies vertical slice behaviour.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
ENGINE = TOOLS / "project_stage_engine.py"
ANALYZER = TOOLS / "project_analyzer.py"
ORCH = TOOLS / "refresh_project_insight.py"
TEMPLATE = ROOT / "Projects" / "TEMPLATE"
MINI = ROOT / "Projects" / "FIXTURES" / "mini_filled"


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expect(cond: bool, message: str, failures: list[str]) -> None:
    if not cond:
        failures.append(message)
        print(f"FAIL: {message}")
    else:
        print(f"OK:   {message}")


def main() -> int:
    failures: list[str] = []
    py = sys.executable

    print("=== 1) TEMPLATE -> IDEA via orchestrator ===")
    r = run([py, str(ORCH), str(TEMPLATE)])
    expect(r.returncode == 0, "orchestrator TEMPLATE exit 0", failures)
    stage = load_json(TEMPLATE / ".ai-pos" / "project_stage.json")
    analysis = load_json(TEMPLATE / ".ai-pos" / "project_analysis.json")
    expect(stage.get("stage") == "IDEA", "TEMPLATE stage is IDEA", failures)
    expect(analysis.get("stage") == "IDEA", "TEMPLATE analysis stage copied", failures)
    expect(analysis.get("valid") is True, "TEMPLATE analysis valid", failures)
    expect(
        analysis.get("stage") == stage.get("stage"),
        "Analyzer stage matches Engine stage",
        failures,
    )

    print("=== 2) mini_filled -> PLANNING ===")
    r = run([py, str(ORCH), str(MINI)])
    expect(r.returncode == 0, "orchestrator mini_filled exit 0", failures)
    stage = load_json(MINI / ".ai-pos" / "project_stage.json")
    analysis = load_json(MINI / ".ai-pos" / "project_analysis.json")
    expect(stage.get("stage") == "PLANNING", "mini_filled stage is PLANNING", failures)
    expect(analysis.get("valid") is True, "mini_filled analysis valid", failures)
    expect(
        "PROJECT_CONTEXT.md" in (analysis.get("what_is_present") or []),
        "mini_filled reports substantive context",
        failures,
    )

    print("=== 3) relative project path from another cwd ===")
    rel = os.path.relpath(MINI, ROOT)
    r = run([py, str(ENGINE), rel], cwd=ROOT)
    expect(r.returncode == 0, "engine accepts relative path", failures)
    expect(
        load_json(MINI / ".ai-pos" / "project_stage.json").get("stage") == "PLANNING",
        "relative path still PLANNING",
        failures,
    )

    print("=== 4) missing project_stage.json -> Analyzer error + invalid analysis ===")
    stage_path = MINI / ".ai-pos" / "project_stage.json"
    bak = MINI / ".ai-pos" / "project_stage.json.smoke_bak"
    if bak.exists():
        bak.unlink()
    stage_path.replace(bak)
    try:
        r = run([py, str(ANALYZER), str(MINI)])
        expect(r.returncode == 2, "analyzer missing stage exit 2", failures)
        inv = load_json(MINI / ".ai-pos" / "project_analysis.json")
        expect(inv.get("valid") is False, "analysis marked invalid", failures)
        expect(inv.get("status") == "invalid", "analysis status invalid", failures)
        expect(inv.get("stage") is None, "invalid analysis has no stage", failures)
    finally:
        if bak.exists():
            bak.replace(stage_path)
        run([py, str(ANALYZER), str(MINI)])

    print("=== 5) corrupt project_stage.json -> Analyzer error + invalid ===")
    stage_path = MINI / ".ai-pos" / "project_stage.json"
    bak = MINI / ".ai-pos" / "project_stage.json.smoke_bak"
    if bak.exists():
        bak.unlink()
    stage_path.replace(bak)
    stage_path.write_text("{ not-json", encoding="utf-8")
    try:
        r = run([py, str(ANALYZER), str(MINI)])
        expect(r.returncode == 2, "analyzer corrupt json exit 2", failures)
        inv = load_json(MINI / ".ai-pos" / "project_analysis.json")
        expect(inv.get("valid") is False, "corrupt path marks analysis invalid", failures)
    finally:
        if stage_path.exists():
            stage_path.unlink()
        if bak.exists():
            bak.replace(stage_path)
        run([py, str(ORCH), str(MINI)])

    print("=== 6) atomic write leaves no .tmp after success ===")
    r = run([py, str(ENGINE), str(TEMPLATE)])
    expect(r.returncode == 0, "engine rewrite TEMPLATE", failures)
    tmp = TEMPLATE / ".ai-pos" / "project_stage.json.tmp"
    expect(not tmp.exists(), "no leftover stage tmp", failures)
    tmp_a = TEMPLATE / ".ai-pos" / "project_analysis.json.tmp"
    run([py, str(ANALYZER), str(TEMPLATE)])
    expect(not tmp_a.exists(), "no leftover analysis tmp", failures)

    print("=== 7) .ai-pos not treated as project marker docs ===")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ai = root / ".ai-pos"
        ai.mkdir()
        # Trap: generated-looking names only inside .ai-pos must not raise stage.
        (ai / "PROJECT_CONTEXT.md").write_text(
            "Fake context inside .ai-pos that should be ignored.\n" * 5,
            encoding="utf-8",
        )
        (ai / "ROADMAP.md").write_text(
            "Fake roadmap inside .ai-pos that should be ignored.\n" * 5,
            encoding="utf-8",
        )
        r = run([py, str(ENGINE), str(root)])
        expect(r.returncode == 0, "engine on empty project ok", failures)
        st = load_json(root / ".ai-pos" / "project_stage.json")
        expect(st.get("stage") == "IDEA", ".ai-pos docs do not create PLANNING", failures)

    print("=== 8) docs/ markers are discovered ===")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        docs = root / "docs"
        docs.mkdir()
        (docs / "PROJECT_CONTEXT.md").write_text(
            "Context stored under docs for pilot-like layouts.\n"
            "This should be discovered by Stage Engine.\n",
            encoding="utf-8",
        )
        (docs / "ARCHITECTURE.md").write_text(
            "Architecture notes live under docs/ARCHITECTURE.md.\n"
            "Engine must see this structure marker.\n",
            encoding="utf-8",
        )
        (root / "ROADMAP.md").write_text(
            "1. Keep docs discovery working.\n"
            "2. Then continue the current task.\n",
            encoding="utf-8",
        )
        r = run([py, str(ENGINE), str(root)])
        expect(r.returncode == 0, "engine docs/ layout ok", failures)
        st = load_json(root / ".ai-pos" / "project_stage.json")
        expect(st.get("stage") == "PLANNING", "docs/ markers can reach PLANNING", failures)
        hits = (st.get("presence") or {}).get("context_hits") or []
        struct = (st.get("presence") or {}).get("structure_hits") or []
        expect(
            any(h.endswith("PROJECT_CONTEXT.md") for h in hits),
            "docs/PROJECT_CONTEXT.md counted",
            failures,
        )
        expect(
            any(h.endswith("ARCHITECTURE.md") for h in struct),
            "docs/ARCHITECTURE.md counted",
            failures,
        )

    print("=== 9) runtime app + roadmap => EXECUTION ===")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "README.md").write_text(
            "Demo app with enough context text for substantive README.\n"
            "Second line keeps the marker valid.\n",
            encoding="utf-8",
        )
        (root / "ROADMAP.md").write_text(
            "1. Build screens.\n2. Verify runtime detection.\n",
            encoding="utf-8",
        )
        (root / "index.html").write_text("<!doctype html><title>app</title>\n", encoding="utf-8")
        (root / "js").mkdir()
        (root / "js" / "app.js").write_text("console.log('ok');\n", encoding="utf-8")
        r = run([py, str(ENGINE), str(root)])
        expect(r.returncode == 0, "engine runtime layout ok", failures)
        st = load_json(root / ".ai-pos" / "project_stage.json")
        expect(st.get("stage") == "EXECUTION", "runtime + roadmap => EXECUTION", failures)
        expect(
            st.get("confidence_state") == "CONFIRMED",
            "EXECUTION with context+runtime is CONFIRMED",
            failures,
        )
        codes = [e.get("code") for e in (st.get("evidence") or [])]
        expect("APP_RUNTIME_SIGNAL" in codes, "APP_RUNTIME_SIGNAL present", failures)
        expect(
            not (st.get("conflicting_evidence") or []),
            "no stage-ceiling conflict on EXECUTION",
            failures,
        )

    print("=== 10) TODO in rich docs does not force stub; TODO-only stays stub ===")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "PROJECT_CONTEXT.md").write_text(
            "# PROJECT_CONTEXT\n\n"
            "This project tracks daily planning for a personal assistant.\n"
            "TODO: add screenshots later.\n"
            "The main goal is a stable local workflow.\n",
            encoding="utf-8",
        )
        (root / "ROADMAP.md").write_text(
            "# ROADMAP\n\n"
            "1. Finish intake documents.\n"
            "2. Define the first executable task.\n"
            "TBD more milestones after review.\n",
            encoding="utf-8",
        )
        r = run([py, str(ENGINE), str(root)])
        expect(r.returncode == 0, "engine rich+TODO ok", failures)
        st = load_json(root / ".ai-pos" / "project_stage.json")
        expect(st.get("stage") == "PLANNING", "rich docs with TODO -> PLANNING", failures)
        expect(
            "PROJECT_CONTEXT.md" in (st.get("presence") or {}).get("context_hits", []),
            "context with TODO counted substantive",
            failures,
        )

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "PROJECT_CONTEXT.md").write_text(
            "# PROJECT_CONTEXT\n\nTODO\nTBD\nзаполните\n",
            encoding="utf-8",
        )
        r = run([py, str(ENGINE), str(root)])
        expect(r.returncode == 0, "engine TODO-only ok", failures)
        st = load_json(root / ".ai-pos" / "project_stage.json")
        expect(st.get("stage") == "IDEA", "TODO-only context stays IDEA", failures)
        expect(
            "PROJECT_CONTEXT.md" in (st.get("presence") or {}).get("stub_files", []),
            "TODO-only file listed as stub",
            failures,
        )

    print()
    if failures:
        print(f"SMOKE FAILED: {len(failures)} check(s)")
        return 1
    print("SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
