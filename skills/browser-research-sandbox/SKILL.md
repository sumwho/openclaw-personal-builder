---
name: browser-research-sandbox
description: Use when the user wants web information lookup through a constrained local research browser path, and the task should avoid exposing repository files, local chat state, cookies, or other host context to remote sites. This skill is for read-only search and page retrieval, not for login flows, posting, purchases, or account actions.
---

# Browser Research Sandbox

Use this skill for web lookup when the goal is information retrieval only.

Do not use it for:

- account login
- sending messages or posting content
- purchases, payments, or form submission
- uploading local files
- browsing local services such as `localhost`, `127.0.0.1`, or private RFC1918 addresses

## Safety Model

The preferred execution path is `scripts/browser_research.py`.

It enforces these boundaries by default:

- runs in a fresh subprocess with a scrubbed environment
- creates an ephemeral sandbox home under `.openclaw-dev/browser-research-sandbox/`
- prefers headless Chrome / Chromium with a temporary profile when available
- blocks local and private-network URLs
- accepts only a search query or a remote URL as input
- performs read-only retrieval and returns plain text / JSON

Current implementation detail:

- On this macOS host, real headless browser execution works more reliably with an isolated temporary `HOME` than with `sandbox-exec`.
- If Chrome / Chromium is unavailable, the helper falls back to the stricter `sandbox-exec` plus HTTP retrieval path.

Important limitation:

- This is a practical containment layer for routine research, not a formal zero-leak proof. It avoids handing the subprocess local context and blocks local targets, but it is not a replacement for a dedicated VM or container boundary.

## Workflow

1. Decide whether the user needs:
   - a web search, or
   - a direct fetch of a known public page
2. Keep the query narrow and do not include local file contents, secrets, or conversation history.
3. Prefer `search` first, then `fetch` the most relevant result if needed.
4. Return concise findings with source URLs.
5. If the task needs authentication, private SaaS access, uploads, or local service access, do not use this skill.

## Invocation

Search:

```sh
python3 skills/browser-research-sandbox/scripts/browser_research.py search --query "OpenClaw Gmail Pub/Sub docs" --limit 5
```

Fetch a page:

```sh
python3 skills/browser-research-sandbox/scripts/browser_research.py fetch --url "https://docs.openclaw.ai/automation/gmail-pubsub" --max-chars 6000
```

## Output Handling

- The script returns JSON.
- For `search`, use the `results` array.
- For `fetch`, use `title`, `url`, and `text`.
- Always cite the returned `url` values in your answer.

## Notes

- The helper is intentionally conservative. It is meant to replace ad hoc browsing for factual lookup, not to automate arbitrary browser behavior.
- If the user needs a stronger boundary, move the same pattern into a dedicated VM or container instead of widening this skill.
