#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}"
PID_FILE="${BASE_DIR}/runtime/tts-gateway.pid"

if [[ ! -f "${PID_FILE}" ]]; then
    echo "No TTS gateway pid file found."
    exit 0
fi

PID="$(cat "${PID_FILE}")"
if ps -p "${PID}" >/dev/null 2>&1; then
    kill -TERM "${PID}"
    sleep 1
    if ps -p "${PID}" >/dev/null 2>&1; then
        kill -KILL "${PID}"
    fi
    echo "Stopped TTS gateway pid ${PID}"
else
    echo "Process ${PID} is not running."
fi

rm -f "${PID_FILE}"
