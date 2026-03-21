# OpenClaw Local Test Environment

This repository provides a safe local test environment scaffold for working with an upstream OpenClaw source tree and your legally obtained game assets. It also includes a local-first TTS package and OpenClaw skill integration for localhost speech generation.

## Layout

- `src/openclaw-upstream/` — ignored checkout of the upstream source tree
- `src/tools/` — helper scripts used inside the container
- `assets/game-data/` — ignored directory for local game assets
- `docs/` — setup and usage documentation
- `tests/` — environment, unit, and integration checks

## Commands

- `make build-image` — build the Docker image with pinned tooling
- `make build` — configure and build the upstream project in an isolated container
- `make test` — run `ctest` inside the container
- `make run OPENCLAW_RUN_BIN=path/to/binary` — run a built executable
- `make shell` — open an interactive shell in the container
- `make gui-doctor` — validate the local OpenClaw CLI environment
- `make gui-gateway` — start the local Gateway on macOS
- `make gui-stop` — stop the local Gateway started from this repo
- `make gui-dashboard` — open the local Control UI
- `make gui-tui` — open the terminal UI against the local Gateway
- `make tts-setup` — deploy the local TTS package under the configured base dir, defaulting to `/Volumes/ExtendStorage/openclaw`
- `make tts-start` — start the local TTS gateway on `127.0.0.1`
- `make tts-stop` — stop the local TTS gateway
- `make tts-clean` — clear generated audio, temp files, cache, and logs while keeping models intact

## Quick Start

1. Put the upstream source tree in `src/openclaw-upstream/`.
2. Put your local game data in `assets/game-data/`.
3. Build the image with `make build-image`.
4. Build the project with `make build`.
5. Run tests with `make test`.

See `docs/setup.md` for the build workflow and safety notes.
For local macOS operation, Qwen integration, and troubleshooting, see `docs/runbook.md`.
For a structured OpenClaw learning path, see `docs/learning/README.md`.
For the local speech stack and OpenClaw skill integration, see `docs/local-tts.md`.
For custom TTS deployments, pass `OPENCLAW_TTS_BASE_DIR=/your/base/dir` to `make tts-setup`, `make tts-start`, `make tts-stop`, and `make tts-clean`.
