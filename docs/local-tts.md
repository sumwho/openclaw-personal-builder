# OpenClaw Local TTS Package

## Goals

- Local-only TTS on Apple Silicon macOS
- Primary engine: Kokoro MLX
- Fallback engine: Piper
- Single removable deployment base directory, defaulting to `/Volumes/ExtendStorage/openclaw`
- Localhost-only FastAPI gateway for OpenClaw integration

## Project Structure

After `scripts/setup.sh`, the deployed tree under the chosen deployment base directory is:

```text
${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/
├── models/
│   ├── kokoro/
│   ├── piper/
│   └── xtts/
├── runtime/
│   ├── audio/
│   ├── temp/
│   ├── cache/
│   ├── logs/
│   └── venv/
├── config/
│   └── config.yaml
├── services/
│   └── tts-gateway/
├── skills/
│   └── local-tts/
├── bin/
└── scripts/
    ├── setup.sh
    ├── start.sh
    ├── stop.sh
    └── clean.sh
```

The OpenClaw skill also exists in two repository-local locations:

```text
repo source skill:
skills/local-tts/

workspace skill used by OpenClaw:
.openclaw-dev/workspace/skills/local-tts/
```

`src/tools/openclaw_seed_config.mjs` syncs `skills/local-tts/` into `.openclaw-dev/workspace/skills/local-tts/` whenever the local OpenClaw config is seeded. The deployed copy under `<base_dir>/skills/local-tts/` is part of the removable package, but OpenClaw discovers the workspace copy.

## Assumptions

- `mlx-audio` provides `python -m mlx_audio.tts.generate` for Kokoro MLX synthesis.
- Piper fallback is available either through the `piper-tts` Python package in the gateway venv or an explicit local binary path such as `<base_dir>/bin/piper`.
- `ffmpeg` can be exposed inside the base directory as `<base_dir>/bin/ffmpeg`, even if the underlying binary is installed by Homebrew.

These assumptions are isolated to the engine adapters and config file so they can be replaced without touching the HTTP API or the skill.

## Current Verified Behavior

- Chinese requests can complete on Kokoro.
- English requests can complete on Piper.
- English requests that prefer Kokoro may fall back to Piper.
- `models/kokoro/` is created during setup, but Kokoro is still resolved through the configured MLX model reference and runtime cache behavior.
- `openclaw skills list` can discover `local-tts` from `.openclaw-dev/workspace/skills/local-tts/`.
- The workspace copy of `scripts/invoke_tts.py` can successfully generate audio through the local gateway.

## Setup

```sh
bash scripts/setup.sh
```

Deploy into a different deployment base directory:

```sh
OPENCLAW_TTS_BASE_DIR=/your/base/dir bash scripts/setup.sh
```

Recommended dependency install notes for Apple Silicon:

- Use Python `3.11`, `3.12`, or `3.13` for the TTS venv. `3.12` is the preferred baseline. If your default `python3` is `3.14`, run setup as `PYTHON_BIN=/opt/homebrew/bin/python3.12 bash scripts/setup.sh`.
- Keep the virtual environment inside `<base_dir>/runtime/venv/tts-gateway`
- Keep Hugging Face cache inside `<base_dir>/runtime/cache/huggingface`
- Keep `TMPDIR` inside `<base_dir>/runtime/temp`
- Recommended: symlink or place `ffmpeg` at `<base_dir>/bin/ffmpeg` so the gateway config never points outside the base directory

## OpenClaw Skill Discovery

Seed the local OpenClaw config so the workspace skill is synced:

```sh
make gui-gateway
```

Then verify discovery:

```sh
OPENCLAW_STATE_DIR=.openclaw-dev/state-live \
OPENCLAW_CONFIG_PATH=.openclaw-dev/config.json \
openclaw skills list
```

```sh
OPENCLAW_STATE_DIR=.openclaw-dev/state-live \
OPENCLAW_CONFIG_PATH=.openclaw-dev/config.json \
openclaw skills info local-tts
```

Expected result: `local-tts` is reported as a workspace skill and resolves to `.openclaw-dev/workspace/skills/local-tts/SKILL.md`.

## Start and Stop

```sh
${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/scripts/start.sh
${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/scripts/stop.sh
```

If you deploy outside the default location, export `OPENCLAW_TTS_BASE_DIR` before using the deployed scripts.

## Curl Tests

Health:

```sh
curl http://127.0.0.1:28641/health
```

Voices:

```sh
curl http://127.0.0.1:28641/voices
```

Verified Kokoro path:

```sh
curl -X POST http://127.0.0.1:28641/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "这是今天的总结。",
    "voice": "default_zh",
    "lang": "zh",
    "format": "mp3",
    "speed": 1.0,
    "engine": "kokoro"
  }'
```

Verified Piper path:

```sh
curl -X POST http://127.0.0.1:28641/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Today'\''s summary is ready.",
    "voice": "default_en",
    "lang": "en",
    "format": "mp3",
    "speed": 1.0,
    "engine": "piper"
  }'
```

Current English Kokoro behavior:

```sh
curl -X POST http://127.0.0.1:28641/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Kokoro primary engine validation.",
    "voice": "default_en",
    "lang": "en",
    "format": "mp3",
    "speed": 1.0,
    "engine": "kokoro"
  }'
```

Current expected result: the request succeeds, but `engine_used` may be `piper`.

Direct workspace skill invocation:

```sh
python3 .openclaw-dev/workspace/skills/local-tts/scripts/invoke_tts.py \
  --text '请朗读这段测试文本。' \
  --lang zh \
  --voice default_zh
```

Expected result: the script returns `success=true` and writes an audio file under `${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/runtime/audio/`.

## Future Extension Points

- Add an `xtts` adapter under `services/tts-gateway/src/local_tts_gateway/engines/`
- Add streaming endpoints without changing the batch `/v1/audio/speech` contract
- Move normalization rules into a separate module if language-specific complexity grows
- Add queueing and per-engine worker pools if concurrency requirements increase

## Related Docs

- Review follow-up list: `docs/local-tts-todo.md`
- Operational runbook: `docs/local-tts-runbook.md`
