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
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
ENGINE = TOOLS / "project_stage_engine.py"
ANALYZER = TOOLS / "project_analyzer.py"
ORCH = TOOLS / "refresh_project_insight.py"
TEMPLATE = ROOT / "Projects" / "TEMPLATE"
MINI = ROOT / "Projects" / "FIXTURES" / "mini_filled"

sys.path.insert(0, str(TOOLS))
from local_bridge import (  # noqa: E402
    API_KEYS,
    LocalBridgeHandler,
    RC_PROJECT_ROOT_INVALID as BRIDGE_RC_PROJECT_ROOT_INVALID,
    run_refresh,
)
from refresh_project_insight import (  # noqa: E402
    MODE_BLOCKED,
    MODE_DIAGNOSTIC,
    MODE_NORMAL,
    RESULT_PREFIX,
    RC_ANALYZER_FAILED,
    RC_ANALYSIS_JSON_MISSING,
    RC_PROJECT_ROOT_INVALID,
    RC_STAGE_ENGINE_FAILED,
    parse_result_line,
    run_insight,
)


def run(
    cmd: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        env=env,
    )


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expect(cond: bool, message: str, failures: list[str]) -> None:
    if not cond:
        failures.append(message)
        print(f"FAIL: {message}")
    else:
        print(f"OK:   {message}")


def orch_mode_from_cli(completed: subprocess.CompletedProcess[str]) -> dict:
    parsed = parse_result_line(completed.stdout or "")
    return parsed or {}


def expect_api_shape(payload: dict, label: str, failures: list[str]) -> None:
    keys = tuple(sorted(payload.keys()))
    expect(keys == tuple(sorted(API_KEYS)), f"{label} API shape keys", failures)
    for key in API_KEYS:
        expect(key in payload, f"{label} has field {key}", failures)


def post_refresh_insight(port: int, project_path: str) -> tuple[int, dict]:
    data = json.dumps({"project_path": project_path}).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/refresh-insight",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body)


def main() -> int:
    failures: list[str] = []
    py = sys.executable

    print("=== 1) TEMPLATE -> IDEA via orchestrator ===")
    r = run([py, str(ORCH), str(TEMPLATE)])
    expect(r.returncode == 0, "orchestrator TEMPLATE exit 0", failures)
    orch = orch_mode_from_cli(r)
    expect(orch.get("mode") == MODE_NORMAL, "TEMPLATE mode NORMAL", failures)
    expect(orch.get("reason_codes") == [], "TEMPLATE reason_codes empty", failures)
    expect(RESULT_PREFIX in (r.stdout or ""), "TEMPLATE emits result line", failures)
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
    orch = orch_mode_from_cli(r)
    expect(orch.get("mode") == MODE_NORMAL, "mini_filled mode NORMAL", failures)
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

    print("=== 11) orchestrator modes NORMAL / DIAGNOSTIC / BLOCKED ===")
    r = run([py, str(ORCH), str(TEMPLATE)])
    orch = orch_mode_from_cli(r)
    expect(r.returncode == 0, "mode NORMAL exit 0", failures)
    expect(orch.get("mode") == MODE_NORMAL, "mode NORMAL set", failures)

    r = run([py, str(ORCH), str(ROOT / "no_such_project_root_for_smoke")])
    orch = orch_mode_from_cli(r)
    expect(r.returncode != 0, "mode BLOCKED exit nonzero", failures)
    expect(orch.get("mode") == MODE_BLOCKED, "mode BLOCKED set", failures)
    expect(
        RC_PROJECT_ROOT_INVALID in (orch.get("reason_codes") or []),
        "BLOCKED reason PROJECT_ROOT_INVALID",
        failures,
    )

    with tempfile.TemporaryDirectory() as td:
        fail_analyzer = Path(td) / "fail_analyzer.py"
        fail_analyzer.write_text(
            "import sys\nprint('smoke fail analyzer', file=sys.stderr)\nsys.exit(2)\n",
            encoding="utf-8",
        )

        # NORMAL first — leaves a valid analysis on disk.
        r = run([py, str(ORCH), str(MINI)])
        expect(r.returncode == 0, "preflight NORMAL exit 0", failures)
        expect(
            orch_mode_from_cli(r).get("mode") == MODE_NORMAL,
            "preflight NORMAL mode",
            failures,
        )
        expect(
            load_json(MINI / ".ai-pos" / "project_analysis.json").get("valid") is True,
            "preflight valid analysis present",
            failures,
        )

        insight = run_insight(MINI, analyzer=fail_analyzer)
        expect(insight.get("mode") == MODE_DIAGNOSTIC, "mode DIAGNOSTIC set", failures)
        expect(
            RC_ANALYZER_FAILED in (insight.get("reason_codes") or []),
            "DIAGNOSTIC reason ANALYZER_FAILED",
            failures,
        )
        expect(
            RC_ANALYSIS_JSON_MISSING in (insight.get("reason_codes") or []),
            "DIAGNOSTIC clears prior analysis artifact",
            failures,
        )
        expect(
            not (MINI / ".ai-pos" / "project_analysis.json").is_file(),
            "stale analysis file removed after ANALYZER_FAILED",
            failures,
        )
        expect(
            load_json(MINI / ".ai-pos" / "project_stage.json").get("stage") == "PLANNING",
            "DIAGNOSTIC keeps valid stage from Engine",
            failures,
        )

        # Bridge path: stale valid analysis on disk + fail-analyzer → ok:false.
        run([py, str(ANALYZER), str(MINI)])
        expect(
            load_json(MINI / ".ai-pos" / "project_analysis.json").get("valid") is True,
            "valid analysis on disk before Bridge fail-run",
            failures,
        )
        os.environ["AI_POS_ANALYZER_SCRIPT"] = str(fail_analyzer)
        try:
            bridge = run_refresh(MINI)
        finally:
            os.environ.pop("AI_POS_ANALYZER_SCRIPT", None)

        expect(bridge.get("ok") is False, "Bridge ok:false on ANALYZER_FAILED", failures)
        expect(bridge.get("mode") == MODE_DIAGNOSTIC, "Bridge mode DIAGNOSTIC", failures)
        expect(
            RC_ANALYZER_FAILED in (bridge.get("reason_codes") or []),
            "Bridge reason ANALYZER_FAILED",
            failures,
        )
        expect(
            bridge.get("analysis") is None
            or (bridge.get("analysis") or {}).get("valid") is False,
            "Bridge analysis null or invalid",
            failures,
        )
        expect_api_shape(bridge, "DIAGNOSTIC Bridge", failures)

    # Restore mini analysis after failing analyzer stub.
    run([py, str(ORCH), str(MINI)])
    normal_bridge = run_refresh(MINI)
    expect_api_shape(normal_bridge, "NORMAL Bridge", failures)
    expect(normal_bridge.get("mode") == MODE_NORMAL, "NORMAL Bridge mode", failures)
    expect(normal_bridge.get("ok") is True, "NORMAL Bridge ok", failures)

    blocked_root = run_refresh(ROOT / "no_such_project_root_for_smoke")
    expect_api_shape(blocked_root, "BLOCKED root Bridge", failures)
    expect(blocked_root.get("mode") == MODE_BLOCKED, "BLOCKED root mode", failures)
    expect(blocked_root.get("analysis") is None, "BLOCKED root analysis null", failures)
    expect(
        RC_PROJECT_ROOT_INVALID in (blocked_root.get("reason_codes") or []),
        "BLOCKED root reason",
        failures,
    )

    print("=== 12) API contract shape + STAGE_ENGINE_FAILED no stale ===")
    # STAGE_ENGINE_FAILED via in-process orch result + Bridge packaging (no env-hook).
    with tempfile.TemporaryDirectory() as td:
        fail_engine = Path(td) / "fail_engine.py"
        fail_engine.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
        expect(
            load_json(MINI / ".ai-pos" / "project_analysis.json").get("valid") is True,
            "stale valid analysis present before STAGE_ENGINE_FAILED",
            failures,
        )
        real_run = subprocess.run

        def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            if len(cmd) >= 2 and "refresh_project_insight.py" in str(cmd[1]):
                result = run_insight(cmd[2], stage_engine=fail_engine)
                out = RESULT_PREFIX + json.dumps(result, ensure_ascii=False) + "\n"
                return subprocess.CompletedProcess(
                    args=cmd,
                    returncode=1,
                    stdout=out,
                    stderr="Orchestrator BLOCKED: Stage Engine failed.\n",
                )
            return real_run(cmd, **kwargs)  # type: ignore[arg-type]

        subprocess.run = fake_run  # type: ignore[assignment]
        try:
            engine_blocked = run_refresh(MINI)
        finally:
            subprocess.run = real_run  # type: ignore[assignment]

        expect_api_shape(engine_blocked, "STAGE_ENGINE_FAILED Bridge", failures)
        expect(engine_blocked.get("mode") == MODE_BLOCKED, "STAGE_ENGINE_FAILED mode", failures)
        expect(
            RC_STAGE_ENGINE_FAILED in (engine_blocked.get("reason_codes") or []),
            "STAGE_ENGINE_FAILED reason",
            failures,
        )
        expect(
            engine_blocked.get("analysis") is None,
            "STAGE_ENGINE_FAILED analysis null (no stale)",
            failures,
        )
        expect(engine_blocked.get("ok") is False, "STAGE_ENGINE_FAILED ok false", failures)

    # HTTP 400 path pre-check: full five-field shape.
    port = 18082
    server = ThreadingHTTPServer(("127.0.0.1", port), LocalBridgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)
    try:
        status, payload = post_refresh_insight(
            port, str(ROOT / "no_such_project_root_http400")
        )
        expect(status == 400, "HTTP 400 for missing project root", failures)
        expect_api_shape(payload, "HTTP 400", failures)
        expect(payload.get("mode") == MODE_BLOCKED, "HTTP 400 mode BLOCKED", failures)
        expect(payload.get("analysis") is None, "HTTP 400 analysis null", failures)
        expect(
            payload.get("reason_codes") == [BRIDGE_RC_PROJECT_ROOT_INVALID],
            "HTTP 400 reason PROJECT_ROOT_INVALID",
            failures,
        )
        expect(payload.get("ok") is False, "HTTP 400 ok false", failures)
    finally:
        server.shutdown()
        server.server_close()

    # Restore mini after fake engine path.
    run([py, str(ORCH), str(MINI)])

    print()
    if failures:
        print(f"SMOKE FAILED: {len(failures)} check(s)")
        return 1
    print("SMOKE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
