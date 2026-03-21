---
name: local-tts
description: Use when the user wants OpenClaw to convert local text into speech through the localhost TTS gateway, save generated audio under the deployed local TTS runtime/audio path inside the deployment base directory, or trigger practical speech tasks such as reading summaries or paragraphs aloud in Chinese or English.
---

# Local TTS

Use this skill when the user wants speech output from the local FastAPI gateway running on `127.0.0.1`.

## Workflow

1. Confirm the gateway is expected at `http://127.0.0.1:28641`.
2. Call `scripts/invoke_tts.py` with text and optional `voice`, `lang`, `format`, and `engine`.
3. Return the generated audio path from the configured deployment base directory's `runtime/audio/`.

## Invocation

Default Chinese summary:

```sh
python3 skills/local-tts/scripts/invoke_tts.py --text "请朗读今天的总结。" --lang zh --voice default_zh
```

Paragraph to speech:

```sh
python3 skills/local-tts/scripts/invoke_tts.py --text "Convert this paragraph to speech." --lang en --voice default_en --format mp3
```

## Notes

- Keep requests local only. Do not target non-loopback hosts.
- Use logical voice names from the deployed `config/config.yaml`.
- If Kokoro fails, the gateway may fall back to Piper automatically.
- The default deployment base directory is `/Volumes/ExtendStorage/openclaw`, but operators may override it with `OPENCLAW_TTS_BASE_DIR`.
