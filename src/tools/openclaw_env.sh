#!/usr/bin/env bash

set -euo pipefail

command_name="${1:-}"

source_dir="${OPENCLAW_SRC_DIR:-/workspace/src/openclaw-upstream}"
asset_dir="${OPENCLAW_ASSET_DIR:-/workspace/assets/game-data}"
build_dir="${OPENCLAW_BUILD_DIR:-/workspace/.build/openclaw}"
cache_dir="${OPENCLAW_CACHE_DIR:-/workspace/.cache/openclaw}"
run_bin="${OPENCLAW_RUN_BIN:-}"

require_dir() {
    local dir_path="$1"
    local label="$2"

    if [[ ! -d "${dir_path}" ]]; then
        echo "Missing ${label}: ${dir_path}" >&2
        exit 1
    fi
}

require_file() {
    local file_path="$1"
    local label="$2"

    if [[ ! -f "${file_path}" ]]; then
        echo "Missing ${label}: ${file_path}" >&2
        exit 1
    fi
}

configure_project() {
    require_dir "${source_dir}" "source directory"
    require_dir "${asset_dir}" "asset directory"
    require_file "${source_dir}/CMakeLists.txt" "CMake project file"

    mkdir -p "${build_dir}" "${cache_dir}"

    cmake \
        -S "${source_dir}" \
        -B "${build_dir}" \
        -G Ninja \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo
}

build_project() {
    configure_project
    cmake --build "${build_dir}"
}

test_project() {
    build_project
    ctest --test-dir "${build_dir}" --output-on-failure
}

run_project() {
    build_project

    if [[ -z "${run_bin}" ]]; then
        echo "OPENCLAW_RUN_BIN is not set." >&2
        echo "Example: make run OPENCLAW_RUN_BIN=./.build/openclaw/openclaw" >&2
        exit 1
    fi

    if [[ ! -x "${run_bin}" ]]; then
        echo "Run target is not executable: ${run_bin}" >&2
        exit 1
    fi

    "${run_bin}"
}

case "${command_name}" in
    build)
        build_project
        ;;
    test)
        test_project
        ;;
    run)
        run_project
        ;;
    *)
        echo "Usage: $0 {build|test|run}" >&2
        exit 1
        ;;
esac

