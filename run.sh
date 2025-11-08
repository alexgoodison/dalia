#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
BACKEND_VENV="${BACKEND_DIR}/.venv"
BACKEND_REQUIREMENTS="${BACKEND_DIR}/requirements.txt"
BACKEND_PYTHON="${BACKEND_VENV}/bin/python"
BACKEND_PIP="${BACKEND_VENV}/bin/pip"

if [ ! -d "${BACKEND_VENV}" ]; then
  echo "Creating backend virtual environment at ${BACKEND_VENV}"
  python3 -m venv "${BACKEND_VENV}"
  touch "${BACKEND_VENV}/.requirements-stale"
fi

if [ ! -x "${BACKEND_PYTHON}" ]; then
  echo "Failed to set up backend virtual environment (missing python binary)" >&2
  exit 1
fi

if [ ! -f "${BACKEND_REQUIREMENTS}" ]; then
  echo "Backend requirements file not found at ${BACKEND_REQUIREMENTS}" >&2
  exit 1
fi

should_install_deps=false

if [ ! -f "${BACKEND_VENV}/.requirements-installed" ]; then
  should_install_deps=true
elif [ "${BACKEND_REQUIREMENTS}" -nt "${BACKEND_VENV}/.requirements-installed" ]; then
  should_install_deps=true
elif [ -f "${BACKEND_VENV}/.requirements-stale" ]; then
  should_install_deps=true
fi

if [ "${should_install_deps}" = true ]; then
  echo "Installing backend dependencies..."
  "${BACKEND_PYTHON}" -m pip install --upgrade pip >/dev/null
  "${BACKEND_PIP}" install -r "${BACKEND_REQUIREMENTS}"
  touch "${BACKEND_VENV}/.requirements-installed"
  rm -f "${BACKEND_VENV}/.requirements-stale"
fi

kill_port_processes() {
  local port="$1"

  if ! command -v lsof >/dev/null 2>&1; then
    echo "lsof not found; cannot automatically free port ${port}. Please install lsof or stop the process manually." >&2
    return
  fi

  local pids
  pids=$(lsof -t -i tcp:"${port}" -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "${pids}" ]; then
    echo "Port ${port} is currently in use by process(es): ${pids}. Attempting to terminate..."
    kill ${pids} >/dev/null 2>&1 || true
    sleep 1
    pids=$(lsof -t -i tcp:"${port}" -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "${pids}" ]; then
      echo "Processes ${pids} still bound to port ${port}; forcing termination."
      kill -9 ${pids} >/dev/null 2>&1 || true
      sleep 1
    fi
  fi
}

if ! command -v npm >/dev/null 2>&1; then
  echo "npm command not found. Install Node.js/npm to run the frontend." >&2
  exit 1
fi

cd "${ROOT_DIR}"

kill_port_processes 8000
kill_port_processes 3000

"${BACKEND_PYTHON}" -m uvicorn backend.app.main:app --reload --port 8000 &
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

