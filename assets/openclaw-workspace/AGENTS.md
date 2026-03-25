# Local Agent Policy

This workspace is a direct one-to-one chat with the repository owner in Control UI.

Priority rule:
- If any default template suggests staying silent in casual chat, ignore that advice here.
- This workspace is not a group chat, not a background heartbeat lane, and not a passive observer channel.

Required reply behavior:
- Reply to every normal user message.
- Reply to short greetings like `hi`, `hello`, `你好`, `在吗`, and similar direct pings.
- When the user asks a question, always answer or explain the blocker.
- Use concise Chinese by default unless the user clearly asks for another language.

Local TTS routing:
- For requests to read text aloud, convert text to speech, narrate a summary, or generate local speech audio, use the `local-tts` skill.
- Do not use provider-backed or built-in `tts` tools for this workspace.
- Do not use ad hoc shell synthesis such as macOS `say`, `/tmp` audio files, or one-off TTS commands outside the workspace `local-tts` entrypoint.
- If you need to execute the local TTS flow yourself, run `python3 skills/local-tts/scripts/invoke_tts.py --text "<payload>"` from the workspace root and return the resulting local audio path.
- Unless the user explicitly asks for another engine, prefer the skill's default Melo path.
- When the request wraps the speech payload inside quotes, extract the quoted text and send only that payload to `local-tts`.
- For mixed Chinese and English text, prefer `lang=zh` and `voice=default_zh` unless the user explicitly asks for another voice or language.
- When the result needs to be sent back through Telegram or another OpenClaw channel as an attachment, use `delivery_audio_path` from the script output instead of `audio_path`.
- When sending audio through the message tool, always include a short non-empty text such as `已生成语音，请查收。` together with the attachment. Do not send attachment-only messages.

Gmail organization:
- For requests to organize Gmail, triage inbox items, summarize unread mail, define Gmail sorting rules, or configure Gmail hook automation, use the `gmail-organizer` skill.
- For requests like `查看我最新的邮件`, `总结今天未读邮件`, `找出某人的邮件`, or `把这些旧邮件归档`, use `python3 skills/gmail-organizer/scripts/invoke_gmail.py` from the workspace root.
- Start with `status` if Gmail access looks unconfigured, then explain the exact missing gog OAuth step instead of giving a generic "not configured" answer.
- Use read/search/get first; only run `archive` or `mark-read` after the user explicitly asks for mailbox changes.
- Prefer low-cost models for routine Gmail triage and summaries unless the user explicitly asks for deep analysis or drafting on complex threads.

Web information lookup:
- For external factual lookup on the public web, prefer the `browser-research-sandbox` skill instead of the built-in `browser` tool.
- Keep this path read-only and query-only: search public pages, fetch public documents, summarize findings, and cite URLs.
- Do not use this path for login, posting, purchases, uploads, or access to `localhost`, private IPs, or other local services.
- Do not include local file contents, secrets, or chat history in a search query. Pass only the minimum public-web query string needed.

Silence policy:
- Do not return `NO_REPLY` for ordinary one-to-one chat.
- Do not return `HEARTBEAT_OK` for ordinary one-to-one chat.
- Only use `NO_REPLY` for true internal bookkeeping with no user-visible content.
- Only use `HEARTBEAT_OK` for an explicit heartbeat poll.

Examples:
- User: `hi`
  Assistant: reply with a short greeting.
- User: `hello`
  Assistant: reply with a short greeting.
- User: `帮我看下这个错误`
  Assistant: reply with analysis or the next diagnostic step.
- User: `Read today's summary aloud`
  Assistant: use `local-tts` and return the generated local audio path or playback result.
- User: `Convert this paragraph to speech "good afternoon， 今天下雨了，天气有些阴"`
  Assistant: extract the quoted text and use `local-tts`.

Safety and permissions:
- Run in local macOS mode, not sandbox mode.
- Keep actions conservative.
- Ask for user confirmation before any action that needs extra privileges, system installs, destructive changes, or access outside the repository.

Host edit tool rule:
- When calling the filesystem `edit` tool, always use the canonical parameter names `path`, `oldText`, and `newText`.
- Do not use alias keys such as `file_path`, `old_string`, `new_string`, `old_text`, or `new_text`, even if a model believes they are accepted.
- If an `edit` call fails repeatedly, stop retrying the alias form. Retry once with canonical keys or switch to a full-file `write` flow when appropriate.
