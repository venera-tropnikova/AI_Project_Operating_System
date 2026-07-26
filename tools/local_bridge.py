#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI POS Local Bridge (MVP v0.2).

Serves the UI and exposes a tiny localhost API that runs the Orchestrator
and returns project_analysis payload to the browser.

Does not determine stage. Does not replace Analyzer / Stage Engine.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = Path(__file__).resolve().parent
ORCHESTRATOR = TOOLS_DIR / "refresh_project_insight.py"
ANALYSIS_REL = Path(".ai-pos") / "project_analysis.json"


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

    analysis: dict[str, Any] | None = None
    analysis_path = project_path / ANALYSIS_REL
    if analysis_path.is_file():
        try:
            loaded = json.loads(analysis_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                analysis = loaded
        except json.JSONDecodeError:
            analysis = None

    if completed.returncode != 0:
        detail = None
        if analysis and analysis.get("error"):
            detail = str(analysis.get("error"))
        elif completed.stderr:
            detail = completed.stderr.strip().splitlines()[-1]
        return {
            "ok": False,
            "analysis": analysis,
            "message": user_facing_error(detail),
        }

    if not analysis:
        return {
            "ok": False,
            "analysis": None,
            "message": "Анализ не получен. Повторите обновление.",
        }

    if analysis.get("valid") is False or analysis.get("status") == "invalid":
        return {
            "ok": False,
            "analysis": analysis,
            "message": user_facing_error(
                str(analysis.get("error") or "Анализ недействителен.")
            ),
        }

    return {"ok": True, "analysis": analysis, "message": None}


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
                },
            )
            return
        if path in {"/", "/index.html"}:
            self.path = "/index.html"
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/refresh-insight":
            self.send_error(404, "Unknown API endpoint")
            return

        try:
            body = self._read_json_body()
        except ValueError as exc:
            self._send_json(
                400,
                {
                    "ok": False,
                    "analysis": None,
                    "message": "Некорректный запрос на обновление анализа.",
                    "detail": str(exc),
                },
            )
            return

        project_path_raw = str(body.get("project_path") or "").strip()
        if not project_path_raw:
            self._send_json(
                400,
                {
                    "ok": False,
                    "analysis": None,
                    "message": "Укажите рабочую папку проекта и повторите обновление.",
                },
            )
            return

        root = Path(project_path_raw).expanduser()
        try:
            root = root.resolve()
        except OSError:
            self._send_json(
                400,
                {
                    "ok": False,
                    "analysis": None,
                    "message": "Не удалось открыть рабочую папку проекта.",
                },
            )
            return

        if not root.exists() or not root.is_dir():
            self._send_json(
                400,
                {
                    "ok": False,
                    "analysis": None,
                    "message": "Рабочая папка проекта не найдена. Проверьте путь и повторите.",
                },
            )
            return

        result = run_refresh(root)
        status = 200 if result.get("ok") else 422
        self._send_json(status, result)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI POS local bridge: UI + refresh-insight API"
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
