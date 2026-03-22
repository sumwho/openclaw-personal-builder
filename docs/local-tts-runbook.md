# Local TTS Runbook

## Current Status

- Chinese Kokoro synthesis works.
- English synthesis works through Piper.
- English requests that prefer Kokoro currently fall back to Piper.
- OpenClaw can discover `local-tts` from `.openclaw-dev/workspace/skills/local-tts/` after the local config seed step runs.

## Deployment Base Directory

All TTS deployment artifacts live under the selected deployment base directory:

```text
${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}
```

Key paths:

- `skills/local-tts/` inside this repo is the source skill definition
- `.openclaw-dev/workspace/skills/local-tts/` is the OpenClaw workspace copy that is actually discovered by `openclaw skills`
- `config/config.yaml`
- `models/piper/`
- `runtime/audio/`
- `runtime/temp/`
- `runtime/cache/`
- `runtime/logs/`
- `runtime/venv/tts-gateway/`
- `services/tts-gateway/`
- `<base_dir>/skills/local-tts/` as the deployed removable package copy
- `scripts/setup.sh`
- `scripts/start.sh`
- `scripts/stop.sh`
- `scripts/clean.sh`

## Prerequisites

- A supported Python interpreter: `3.11`, `3.12`, or `3.13`
- `ffmpeg`, preferably exposed at `<base_dir>/bin/ffmpeg`
- Local TTS venv already created under `runtime/venv/tts-gateway`
- If you deploy outside the default path, export `OPENCLAW_TTS_BASE_DIR=/your/base/dir`

Default deployment:

```sh
bash scripts/setup.sh
```

Custom deployment base directory:

```sh
OPENCLAW_TTS_BASE_DIR=/your/base/dir \
PYTHON_BIN=/opt/homebrew/bin/python3.12 \
bash scripts/setup.sh
```

Seed the local OpenClaw config so the workspace skill is synced:

```sh
make gui-gateway
```

## Verify Runtime

Check Python:

```sh
${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/runtime/venv/tts-gateway/bin/python --version
```

Check ffmpeg:

```sh
${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/bin/ffmpeg -version | head -n 2
```

Check config:

```sh
sed -n '1,200p' ${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/config/config.yaml
```

## Start

Best-effort background start:

```sh
bash ${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/scripts/start.sh
```

If you want direct foreground diagnostics:

```sh
OPENCLAW_TTS_CONFIG=${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/config/config.yaml \
HF_HOME=${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/runtime/cache/huggingface \
XDG_CACHE_HOME=${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/runtime/cache/xdg \
PIP_CACHE_DIR=${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/runtime/cache/pip \
TMPDIR=${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/runtime/temp \
${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/runtime/venv/tts-gateway/bin/python \
  -m uvicorn local_tts_gateway.main:app \
  --app-dir ${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/services/tts-gateway/src \
  --host 127.0.0.1 \
  --port 28641
```

For non-default deployments, keep `OPENCLAW_TTS_CONFIG` pointed at the deployed `config/config.yaml`. If you start `uvicorn` without that variable, the app falls back to the default config path.

## Stop

```sh
bash ${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/scripts/stop.sh
```

## Health Checks

```sh
curl -s http://127.0.0.1:28641/health
curl -s http://127.0.0.1:28641/voices
```

Expected behaviors:

- `/health` returns `status=ok`
- `/voices` returns `default_zh` and `default_en`
- Both voices list `kokoro` and `piper`

## OpenClaw Skill Checks

Verify that OpenClaw sees the workspace skill:

```sh
OPENCLAW_STATE_DIR=.openclaw-dev/state-live \
OPENCLAW_CONFIG_PATH=.openclaw-dev/config.json \
openclaw skills list
```

Inspect the resolved skill location:

```sh
OPENCLAW_STATE_DIR=.openclaw-dev/state-live \
OPENCLAW_CONFIG_PATH=.openclaw-dev/config.json \
openclaw skills info local-tts
```

Expected behaviors:

- `local-tts` is listed as ready
- the source is `openclaw-workspace`
- the resolved `SKILL.md` path is `.openclaw-dev/workspace/skills/local-tts/SKILL.md`

## Synthesis Checks

Chinese Kokoro:

```sh
curl -s -X POST http://127.0.0.1:28641/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "这是 Kokoro 中文验证。",
    "voice": "default_zh",
    "lang": "zh",
    "format": "wav",
    "speed": 1.0,
    "engine": "kokoro"
  }'
```

English Piper:

```sh
curl -s -X POST http://127.0.0.1:28641/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "This is a local fallback synthesis test.",
    "voice": "default_en",
    "lang": "en",
    "format": "wav",
    "speed": 1.0,
    "engine": "piper"
  }'
```

English Kokoro current behavior:

```sh
curl -s -X POST http://127.0.0.1:28641/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Kokoro primary engine validation.",
    "voice": "default_en",
    "lang": "en",
    "format": "wav",
    "speed": 1.0,
    "engine": "kokoro"
  }'
```

Current expected result: request succeeds but `engine_used` may be `piper`.

Direct skill invocation from the workspace copy:

```sh
python3 .openclaw-dev/workspace/skills/local-tts/scripts/invoke_tts.py \
  --text '请朗读这段测试文本。' \
  --lang zh \
  --voice default_zh
```

Expected result: the script returns `success=true` and writes audio to `runtime/audio/` under the selected deployment base directory.

## Logs

Background stdout:

```sh
sed -n '1,200p' ${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/runtime/logs/tts-gateway-stdout.log
```

Application log:

```sh
sed -n '1,200p' ${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/runtime/logs/tts-gateway.log
```

## Cleanup

Runtime-only cleanup:

```sh
bash ${OPENCLAW_TTS_BASE_DIR:-/Volumes/ExtendStorage/openclaw}/scripts/clean.sh
```

This keeps:

- `models/`
- `services/`
- `skills/`
- `config/`

## Known Gaps

- English Kokoro is not fully local yet and may still fall back to Piper.
- Background start should be upgraded to `launchd` for production reliability.
- Host-managed dependencies are not yet fully vendored into the deployment base directory.
