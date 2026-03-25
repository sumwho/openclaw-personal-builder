#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_SRC="${REPO_ROOT}/services/tts-gateway"
SKILL_SRC="${REPO_ROOT}/skills/local-tts"
CONFIG_TEMPLATE="${REPO_ROOT}/config/config.yaml.example"
FORCE_RENDER_CONFIG="${OPENCLAW_TTS_FORCE_CONFIG_RENDER:-0}"
MELO_GIT_REF="${OPENCLAW_TTS_MELO_GIT_REF:-209145371cff8fc3bd60d7be902ea69cbdb7965a}"
MELO_TARBALL_URL="https://codeload.github.com/myshell-ai/MeloTTS/tar.gz/${MELO_GIT_REF}"

pick_python_bin() {
    if [[ -n "${PYTHON_BIN:-}" ]]; then
        printf '%s\n' "${PYTHON_BIN}"
        return 0
    fi

    local candidate
    for candidate in python3.12 python3.11 python3.13 python3; do
        if command -v "${candidate}" >/dev/null 2>&1; then
            printf '%s\n' "${candidate}"
            return 0
        fi
    done

    echo "python3" 
}

verify_python_version() {
    local python_bin="$1"

    "${python_bin}" - <<'PY'
import sys

major, minor = sys.version_info[:2]
if major != 3 or minor < 11 or minor >= 14:
    raise SystemExit(
        "Local TTS setup requires Python 3.11, 3.12, or 3.13. "
        f"Detected {major}.{minor}. Set PYTHON_BIN to a supported interpreter inside the removable base workflow."
    )
PY
}

render_config() {
    local output_path="$1"

    BASE_DIR_VALUE="${BASE_DIR}" CONFIG_TEMPLATE_PATH="${CONFIG_TEMPLATE}" CONFIG_OUTPUT_PATH="${output_path}" python3 - <<'PY'
from pathlib import Path
import os

template_path = Path(os.environ["CONFIG_TEMPLATE_PATH"])
output_path = Path(os.environ["CONFIG_OUTPUT_PATH"])
base_dir = os.environ["BASE_DIR_VALUE"]

content = template_path.read_text(encoding="utf-8")
content = content.replace("__BASE_DIR__", base_dir)
output_path.write_text(content, encoding="utf-8")
PY
}

warn_if_config_base_dir_differs() {
    local config_path="$1"

    CONFIG_PATH_TO_CHECK="${config_path}" EXPECTED_BASE_DIR="${BASE_DIR}" python3 - <<'PY'
from pathlib import Path
import os
import sys
import yaml

config_path = Path(os.environ["CONFIG_PATH_TO_CHECK"])
expected_base_dir = os.environ["EXPECTED_BASE_DIR"]
data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
configured_base_dir = str(data.get("base_dir", ""))
if configured_base_dir and configured_base_dir != expected_base_dir:
    print(
        f"Warning: {config_path} is configured for base_dir={configured_base_dir}, "
        f"but OPENCLAW_TTS_BASE_DIR={expected_base_dir}.",
        file=sys.stderr,
    )
PY
}

install_melo_tts() {
    local python_bin="$1"
    local requirements_path="${BASE_DIR}/services/tts-gateway/requirements-melo.txt"

    "${python_bin}" -m pip install -r "${requirements_path}"
    "${python_bin}" -m pip install --no-build-isolation --no-deps "${MELO_TARBALL_URL}"
}

mkdir -p \
    "${BASE_DIR}/models/kokoro" \
    "${BASE_DIR}/models/piper" \
    "${BASE_DIR}/models/xtts" \
    "${BASE_DIR}/runtime/audio" \
    "${BASE_DIR}/runtime/temp" \
    "${BASE_DIR}/runtime/cache" \
    "${BASE_DIR}/runtime/logs" \
    "${BASE_DIR}/runtime/venv" \
    "${BASE_DIR}/config" \
    "${BASE_DIR}/services" \
    "${BASE_DIR}/skills" \
    "${BASE_DIR}/bin" \
    "${BASE_DIR}/scripts"

rm -rf "${BASE_DIR}/services/tts-gateway"
cp -R "${SERVICE_SRC}" "${BASE_DIR}/services/tts-gateway"

rm -rf "${BASE_DIR}/skills/local-tts"
cp -R "${SKILL_SRC}" "${BASE_DIR}/skills/local-tts"

cp "${REPO_ROOT}/scripts/start.sh" "${BASE_DIR}/scripts/start.sh"
cp "${REPO_ROOT}/scripts/stop.sh" "${BASE_DIR}/scripts/stop.sh"
cp "${REPO_ROOT}/scripts/clean.sh" "${BASE_DIR}/scripts/clean.sh"
cp "${REPO_ROOT}/scripts/setup.sh" "${BASE_DIR}/scripts/setup.sh"
chmod +x "${BASE_DIR}/scripts/"*.sh

if [[ "${FORCE_RENDER_CONFIG}" == "1" || ! -f "${BASE_DIR}/config/config.yaml" ]]; then
    render_config "${BASE_DIR}/config/config.yaml"
else
    warn_if_config_base_dir_differs "${BASE_DIR}/config/config.yaml"
fi

VENV_DIR="${BASE_DIR}/runtime/venv/tts-gateway"
MELO_VENV_DIR="${BASE_DIR}/runtime/venv/melo"
PYTHON_BIN="$(pick_python_bin)"
verify_python_version "${PYTHON_BIN}"

rm -rf "${VENV_DIR}"
rm -rf "${MELO_VENV_DIR}"
"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

export HF_HOME="${BASE_DIR}/runtime/cache/huggingface"
export XDG_CACHE_HOME="${BASE_DIR}/runtime/cache/xdg"
export PIP_CACHE_DIR="${BASE_DIR}/runtime/cache/pip"
export NLTK_DATA="${BASE_DIR}/runtime/cache/nltk_data"
export HOME="${BASE_DIR}/runtime/cache/home"
export TMPDIR="${BASE_DIR}/runtime/temp"
mkdir -p "${HF_HOME}" "${XDG_CACHE_HOME}" "${PIP_CACHE_DIR}" "${NLTK_DATA}" "${HOME}" "${TMPDIR}"

python -m pip install --upgrade pip
python -m pip install -r "${BASE_DIR}/services/tts-gateway/requirements.txt"
python -m pip install -e "${BASE_DIR}/services/tts-gateway"
deactivate

"${PYTHON_BIN}" -m venv "${MELO_VENV_DIR}"
source "${MELO_VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
install_melo_tts python
python -m pip install -e "${BASE_DIR}/services/tts-gateway"
python -m local_tts_gateway.engines.patch_melo_install
deactivate

cat <<EOF
Local TTS package deployed under:
  ${BASE_DIR}

Next steps:
  1. Put Kokoro and Piper models under ${BASE_DIR}/models
  2. Review ${BASE_DIR}/config/config.yaml
  3. Start the gateway with ${BASE_DIR}/scripts/start.sh

Notes:
  - Override the deployment root with OPENCLAW_TTS_BASE_DIR=/your/path
  - Regenerate config.yaml for a new base dir with OPENCLAW_TTS_FORCE_CONFIG_RENDER=1
  - MeloTTS uses a dedicated runtime venv at ${MELO_VENV_DIR} to avoid conflicting with Kokoro dependencies
EOF
