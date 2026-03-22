#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}"

find "${BASE_DIR}/runtime/audio" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
find "${BASE_DIR}/runtime/temp" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
find "${BASE_DIR}/runtime/cache" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
find "${BASE_DIR}/runtime/logs" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
rm -f "${BASE_DIR}/runtime/tts-gateway.pid"

mkdir -p \
    "${BASE_DIR}/runtime/audio" \
    "${BASE_DIR}/runtime/temp" \
    "${BASE_DIR}/runtime/cache" \
    "${BASE_DIR}/runtime/logs"

echo "Cleaned runtime artifacts under ${BASE_DIR}/runtime"
