#!/usr/bin/env bash
# AI POS portable launcher (macOS / Linux)
# Run from anywhere after moving the AI POS folder; no absolute paths required.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -f "tools/local_bridge.py" ]]; then
  echo "Не найден tools/local_bridge.py рядом с этим файлом."
  echo "Убедитесь, что вы запускаете start_ai_pos.sh из корня AI POS."
  exit 1
fi

pick_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi
  return 1
}

if ! PY="$(pick_python)"; then
  echo "Для запуска AI POS установите Python 3"
  exit 1
fi

open_browser() {
  sleep 1
  if command -v open >/dev/null 2>&1; then
    open "http://127.0.0.1:8080/" || true
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://127.0.0.1:8080/" >/dev/null 2>&1 || true
  fi
}

open_browser &

echo "AI POS запускается..."
echo "Остановка: Ctrl+C"
echo

exec "$PY" "tools/local_bridge.py" --host 127.0.0.1 --port 8080
