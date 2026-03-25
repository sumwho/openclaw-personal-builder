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
- `make gmail-config` — seed repo-local Gmail hook config and `.env.local` placeholders
- `make gmail-run` — run the Gmail Pub/Sub watcher through OpenClaw
- `make gmail-check` — show Gmail watcher host dependency status
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
For Gmail automation and inbox organization setup, see `skills/gmail-organizer/` and `docs/gmail-organizer.md`.
For custom TTS deployments, pass `OPENCLAW_TTS_BASE_DIR=/your/base/dir` to `make tts-setup`, `make tts-start`, `make tts-stop`, and `make tts-clean`.

## Local TTS Integration Notes

- `make tts-setup` deploys the TTS gateway package under `${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}`.
- `skills/local-tts/` in this repo is the source skill definition that gets synced into `.openclaw-dev/workspace/skills/local-tts/` by `src/tools/openclaw_seed_config.mjs`.
- OpenClaw discovers the skill from the workspace copy, not from the deployed base directory alone.
- After `make gui-gateway`, verify discovery with `openclaw skills list` and `openclaw skills info local-tts`.
