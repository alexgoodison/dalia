#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn is not installed or not on PATH. Activate your backend virtualenv first." >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm command not found. Install Node.js/npm to run the frontend." >&2
  exit 1
fi

cd "${ROOT_DIR}"

python -m uvicorn backend.app.main:app --reload --port 8000 &
UVICORN_PID=$!

cd "${ROOT_DIR}/frontend"
npm run dev &
NEXT_PID=$!

cleanup() {
  kill "${UVICORN_PID}" >/dev/null 2>&1 || true
  kill "${NEXT_PID}" >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

wait

