#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
state_root="${repo_root}/.openclaw-dev"
state_dir="${OPENCLAW_STATE_DIR:-${state_root}/state-live}"
config_path="${OPENCLAW_CONFIG_PATH:-${state_root}/config.json}"
gateway_port="${OPENCLAW_GATEWAY_PORT:-18789}"
gateway_bind="${OPENCLAW_GATEWAY_BIND:-}"
dashboard_no_open="${OPENCLAW_DASHBOARD_NO_OPEN:-0}"
launchd_label="${OPENCLAW_LAUNCHD_LABEL:-ai.openclaw.gateway}"
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

list_gateway_pids() {
    lsof -tiTCP:"${gateway_port}" -sTCP:LISTEN 2>/dev/null || true
}

stop_gateway() {
    local user_domain="gui/$(id -u)"
    local service_target="${user_domain}/${launchd_label}"
    local service_present=0
    local pids remaining

    if launchctl print "${service_target}" >/dev/null 2>&1; then
        service_present=1
    fi

    if [[ "${service_present}" -eq 1 ]]; then
        echo "Stopping supervised OpenClaw gateway service ${service_target}"
        if ! run_openclaw gateway stop; then
            echo "openclaw gateway stop failed, falling back to launchctl bootout for ${service_target}" >&2
        fi
        sleep 1
    fi

    if launchctl print "${service_target}" >/dev/null 2>&1; then
        echo "Gateway service still loaded, forcing launchctl bootout for ${service_target}"
        launchctl bootout "${service_target}" >/dev/null 2>&1 || true
        sleep 1
    fi

    pids="$(list_gateway_pids)"
    if [[ -n "${pids}" ]]; then
        echo "Stopping local OpenClaw gateway on port ${gateway_port} (pid: ${pids})"
        kill -TERM ${pids} 2>/dev/null || true
        sleep 1
        remaining="$(list_gateway_pids)"
        if [[ -n "${remaining}" ]]; then
            echo "Gateway still running after SIGTERM, forcing stop (pid: ${remaining})"
            kill -KILL ${remaining} 2>/dev/null || true
        fi
    fi

    if launchctl print "${service_target}" >/dev/null 2>&1; then
        echo "Gateway service is still loaded after stop attempts: ${service_target}" >&2
        exit 1
    fi

    remaining="$(list_gateway_pids)"
    if [[ -n "${remaining}" ]]; then
        echo "Gateway still listening on port ${gateway_port} after stop attempts (pid: ${remaining})" >&2
        exit 1
    fi

    if [[ "${service_present}" -eq 0 && -z "${pids:-}" ]]; then
        echo "No local OpenClaw gateway is listening on port ${gateway_port}."
    else
        echo "OpenClaw gateway stopped on port ${gateway_port}"
    fi
}

case "${command_name}" in
    doctor)
        run_openclaw doctor
        ;;
    gateway)
        run_gateway
        ;;
    stop)
        stop_gateway
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
        echo "Usage: $0 {doctor|gateway|stop|dashboard|tui}" >&2
        exit 1
        ;;
esac
