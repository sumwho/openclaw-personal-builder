# Bootstrap Notes

This chat is interactive and user-facing.

- Normal direct messages require a visible assistant reply.
- Do not suppress replies for greetings or short questions.
- If a tool is needed, explain the action briefly, then use the tool.
- For any TTS or "read aloud" request, prefer the workspace `local-tts` skill.
- Prefer the default Melo engine path unless the user explicitly asks for another engine.
- Do not fall back to built-in or provider-backed TTS tools in this workspace.
- Do not use macOS `say`, `/tmp` audio outputs, or ad hoc shell pipelines for TTS; use `python3 skills/local-tts/scripts/invoke_tts.py` when execution is required.
- If TTS output is delivered back into Telegram or another OpenClaw message channel, attach `delivery_audio_path` and include a short non-empty text message. Do not send media-only tool messages.
- For Gmail inbox organization or Gmail hook setup, prefer the workspace `gmail-organizer` skill.
- For immediate Gmail reads or inbox cleanup, prefer `python3 skills/gmail-organizer/scripts/invoke_gmail.py` over generic memory or read tools.
- For public-web factual lookup, prefer the workspace `browser-research-sandbox` skill over the built-in `browser` tool.
- Keep browser-research use read-only. Do not use it for login flows, posting, payments, uploads, or local/private-network targets.
- For filesystem edits, use the canonical `edit` tool arguments `path`, `oldText`, and `newText`. Do not use alias keys like `file_path`, `old_string`, `new_string`, `old_text`, or `new_text`.
