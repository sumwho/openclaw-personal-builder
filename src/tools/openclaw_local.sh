#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
state_root="${repo_root}/.openclaw-dev"
state_dir="${OPENCLAW_STATE_DIR:-${state_root}/state-live}"
config_path="${OPENCLAW_CONFIG_PATH:-${state_root}/config.json}"
gateway_port="${OPENCLAW_GATEWAY_PORT:-18789}"
gateway_bind="${OPENCLAW_GATEWAY_BIND:-}"
dashboard_no_open="${OPENCLAW_DASHBOARD_NO_OPEN:-0}"
command_name="${1:-}"
env_local_path="${repo_root}/.env.local"

load_env_local_defaults() {
    local line key value

    [[ -f "${env_local_path}" ]] || return 0

    while IFS= read -r line || [[ -n "${line}" ]]; do
        [[ -n "${line}" ]] || continue
        [[ "${line}" =~ ^[[:space:]]*# ]] && continue
        [[ "${line}" == *=* ]] || continue

        key="${line%%=*}"
        value="${line#*=}"

        key="${key#"${key%%[![:space:]]*}"}"
        key="${key%"${key##*[![:space:]]}"}"

        export "${key}=${value}"
    done < "${env_local_path}"
}

load_env_local_defaults

mkdir -p "${state_dir}" "${state_root}/logs"

export OPENCLAW_STATE_DIR="${state_dir}"
export OPENCLAW_CONFIG_PATH="${config_path}"

shim_option="--import=${repo_root}/src/tools/openclaw_network_shim.mjs"
if [[ -n "${NODE_OPTIONS:-}" ]]; then
    export NODE_OPTIONS="${shim_option} ${NODE_OPTIONS}"
else
    export NODE_OPTIONS="${shim_option}"
fi

node "${repo_root}/src/tools/openclaw_seed_config.mjs" "${config_path}" "${state_root}"

run_openclaw() {
    command openclaw "$@"
}

run_gateway() {
    local gateway_args=(gateway run --allow-unconfigured --port "${gateway_port}")

    if [[ -n "${gateway_bind}" ]]; then
        gateway_args+=(--bind "${gateway_bind}")
    fi

    run_openclaw "${gateway_args[@]}"
}

case "${command_name}" in
    doctor)
        run_openclaw doctor
        ;;
    gateway)
        run_gateway
        ;;
    dashboard)
        if [[ "${dashboard_no_open}" == "1" ]]; then
            run_openclaw dashboard --no-open
        else
            run_openclaw dashboard
        fi
        ;;
    tui)
        run_openclaw tui --url "ws://127.0.0.1:${gateway_port}"
        ;;
    *)
        echo "Usage: $0 {doctor|gateway|dashboard|tui}" >&2
        exit 1
        ;;
esac
