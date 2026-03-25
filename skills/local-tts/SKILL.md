---
name: local-tts
description: Use when the user wants OpenClaw to convert local text into speech through the localhost TTS gateway, save generated audio under the deployed local TTS runtime/audio path inside the deployment base directory, or trigger practical speech tasks such as reading summaries or paragraphs aloud in Chinese or English.
metadata: {"openclaw":{"always":true}}
---

# Local TTS

Use this skill when the user wants speech output from the local FastAPI gateway running on `127.0.0.1`.

## Workflow

1. Confirm the gateway is expected at `http://127.0.0.1:28641`.
2. Extract the actual text the user wants spoken. If the request wraps the content in quotes, pass the quoted content instead of the wrapper instruction.
3. For mixed Chinese plus English text, prefer `--lang zh --voice zh_mix_en`. For pure Chinese text, prefer `--lang zh --voice default_zh`.
4. Call `scripts/invoke_tts.py` with text and optional `voice`, `lang`, `format`, and `engine`.
5. Prefer Melo unless the user explicitly asks for another engine.
5. Return the generated audio path from the configured deployment base directory's `runtime/audio/`.
6. If the audio must be sent back through Telegram or another OpenClaw channel attachment flow, use `delivery_audio_path` from the script output, not the raw `audio_path`.
7. When sending the attachment through the message tool, always include a short non-empty text such as `已生成语音，请查收。` or `Audio generated. See attached file.`.

## Invocation

Default Chinese summary:

```sh
python3 skills/local-tts/scripts/invoke_tts.py --text "请朗读今天的总结。" --lang zh --voice default_zh --engine melo
```

Paragraph to speech:

```sh
python3 skills/local-tts/scripts/invoke_tts.py --text "Convert this paragraph to speech." --lang en --voice default_en --format mp3 --engine melo
```

Mixed Chinese and English:

```sh
python3 skills/local-tts/scripts/invoke_tts.py --text "good afternoon， 今天下雨了，天气有些阴" --lang zh --voice zh_mix_en --format mp3 --engine melo
```

## Notes

- Keep requests local only. Do not target non-loopback hosts.
- Use logical voice names from the deployed `config/config.yaml`.
- For code-switching Chinese plus English text, `zh_mix_en` is the explicit voice alias for the Melo Chinese `(mix EN)` path.
- If Melo or Kokoro fails, the gateway may fall back automatically according to its configured engine order.
- `scripts/invoke_tts.py` will automatically prefer the longest quoted span as the payload text, default mixed Chinese/English text to `zh` / `zh_mix_en` when `lang` and `voice` are omitted, keep pure Chinese on `default_zh`, request `engine=melo` unless another engine is passed explicitly, attempt to start the local gateway if it is not already listening, and stage a Telegram-safe copy under the OpenClaw state media directory as `delivery_audio_path`.
- The default deployment base directory is `/Volumes/ExtendStorage/openclaw`, but operators may override it with `OPENCLAW_TTS_BASE_DIR`.
