#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}"
CONFIG_PATH="${OPENCLAW_TTS_CONFIG:-${BASE_DIR}/config/config.yaml}"
VENV_DIR="${BASE_DIR}/runtime/venv/tts-gateway"
VENV_PYTHON="${VENV_DIR}/bin/python"
PID_FILE="${BASE_DIR}/runtime/tts-gateway.pid"
LOG_FILE="${BASE_DIR}/runtime/logs/tts-gateway-stdout.log"
HOST="${OPENCLAW_TTS_HOST:-127.0.0.1}"

if [[ ! -x "${VENV_PYTHON}" ]]; then
    echo "Missing virtual environment: ${VENV_DIR}" >&2
    exit 1
fi

if [[ -f "${PID_FILE}" ]]; then
    existing_pid="$(cat "${PID_FILE}")"
    if ps -p "${existing_pid}" >/dev/null 2>&1; then
        echo "TTS gateway already running with pid ${existing_pid}" >&2
        exit 0
    fi
    rm -f "${PID_FILE}"
fi

export OPENCLAW_TTS_CONFIG="${CONFIG_PATH}"
export HF_HOME="${BASE_DIR}/runtime/cache/huggingface"
export XDG_CACHE_HOME="${BASE_DIR}/runtime/cache/xdg"
export PIP_CACHE_DIR="${BASE_DIR}/runtime/cache/pip"
export TMPDIR="${BASE_DIR}/runtime/temp"
mkdir -p "${BASE_DIR}/runtime/logs" "${BASE_DIR}/runtime/cache" "${BASE_DIR}/runtime/temp"

PORT="$(
"${VENV_PYTHON}" - <<'PY'
import os
import yaml
from pathlib import Path

config_path = Path(os.environ["OPENCLAW_TTS_CONFIG"])
with config_path.open("r", encoding="utf-8") as handle:
    data = yaml.safe_load(handle) or {}
print(data.get("gateway_port", 28641))
PY
)"

nohup "${VENV_PYTHON}" -m uvicorn local_tts_gateway.main:app \
    --app-dir "${BASE_DIR}/services/tts-gateway/src" \
    --host "${HOST}" \
    --port "${PORT}" \
    < /dev/null >"${LOG_FILE}" 2>&1 &

PID="$!"
disown "${PID}" 2>/dev/null || true
sleep 2

if ! kill -0 "${PID}" >/dev/null 2>&1; then
    echo "TTS gateway failed to stay up. Check ${LOG_FILE}" >&2
    exit 1
fi

echo "${PID}" > "${PID_FILE}"
echo "TTS gateway started on ${HOST}:${PORT} (pid ${PID})"
