---
name: gmail-organizer
description: Use when the user wants OpenClaw to read recent Gmail messages on demand, summarize or organize inbox activity, propose archive/reply/follow-up buckets, perform safe Gmail cleanup actions, or set up the built-in Gmail Pub/Sub hook automation through gogcli and OpenClaw webhooks.
---

# Gmail Organizer

Use this skill for three classes of work:

1. On-demand inbox reading
2. Inbox triage and summarization
3. Gmail hook setup for automatic OpenClaw-triggered processing

## Workflow

1. Decide whether the user wants:
   - to read recent or specific emails right now,
   - inbox organization and summaries, or
   - local Gmail automation setup
2. For immediate Gmail reads and safe mailbox actions, use `scripts/invoke_gmail.py` from the workspace root. Start with `status` when setup may be incomplete.
3. For routine inbox triage, prefer a lower-cost model profile unless the user asks for deep reasoning or nuanced drafting.
4. Keep Gmail external-content safety protections enabled by default. Do not suggest `hooks.gmail.allowUnsafeExternalContent: true` unless the user is explicitly debugging trusted mail flows.
5. For automation setup, use the built-in OpenClaw Gmail integration:
   - `openclaw webhooks gmail setup --account <email>`
   - `openclaw webhooks gmail run`
6. When suggesting an inbox triage output, structure it into actionable buckets:
   - urgent / needs reply
   - important but can wait
   - FYI / read later
   - archive / low value
7. When asked to propose automation behavior, keep mappings simple and explicit:
   - `hooks.presets: ["gmail"]`
   - one `hooks.mappings[]` entry for message templating and delivery
   - cheap model override for routine inbox processing
8. Do not mutate the mailbox unless the user explicitly asks. Read/search/summary is safe by default; `archive` and `mark-read` require clear intent.

## Immediate Read Path

Use these commands from the workspace root:

```sh
python3 skills/gmail-organizer/scripts/invoke_gmail.py status
python3 skills/gmail-organizer/scripts/invoke_gmail.py latest --limit 5 --unread-only
python3 skills/gmail-organizer/scripts/invoke_gmail.py search --query 'from:boss newer_than:7d'
python3 skills/gmail-organizer/scripts/invoke_gmail.py get --message-id <id>
```

Safe mailbox actions:

```sh
python3 skills/gmail-organizer/scripts/invoke_gmail.py mark-read --query 'label:inbox older_than:14d'
python3 skills/gmail-organizer/scripts/invoke_gmail.py archive --ids <id1> <id2>
```

If the helper returns `oauth_credentials_missing`, tell the user to finish gog OAuth setup:

```sh
gog auth credentials set /path/to/credentials.json
gog auth add you@gmail.com --services gmail --gmail-scope full
```

## Recommended Triage Format

Use concise output with one line per email:

- sender
- subject
- why it matters
- recommended action: reply / follow up / archive / ignore

If the user asks for reply help, add a short draft reply after the triage section.

## Commands

Recommended first-time setup:

```sh
openclaw webhooks gmail setup --account you@example.com
```

Run the Gmail watcher manually:

```sh
openclaw webhooks gmail run
```

## Mapping Pattern

Use a simple Gmail hook mapping like this when the user wants inbox summaries routed into OpenClaw:

```json5
{
  hooks: {
    enabled: true,
    token: "OPENCLAW_HOOK_TOKEN",
    presets: ["gmail"],
    mappings: [
      {
        match: { path: "gmail" },
        action: "agent",
        wakeMode: "now",
        name: "Gmail",
        sessionKey: "hook:gmail:{{messages[0].id}}",
        messageTemplate: "New email from {{messages[0].from}}\nSubject: {{messages[0].subject}}\n{{messages[0].snippet}}\n{{messages[0].body}}",
        model: "qwen/qwen3.5-flash",
        deliver: true,
        channel: "last"
      }
    ],
    gmail: {
      thinking: "off"
    }
  }
}
```

## Notes

- OpenClaw’s built-in Gmail path uses `gog` plus Gmail Pub/Sub and webhook mappings; do not invent a separate Gmail transport if the built-in integration is sufficient.
- The helper script is the preferred path for on-demand Gmail reads in chat. Use the webhook path for background automation.
- `gog` requires OAuth client credentials before any Gmail read/search calls will work. A logged-in `gcloud` account alone is not sufficient.
- For routine mailbox organization, `qwen/qwen3.5-flash` or `qwen/qwen3.5-plus` is usually enough.
- Move to a stronger model only when the task involves delicate drafting, conflict-heavy threads, contract language, or ambiguous stakeholder intent.
- If the user wants a Telegram/DM-facing summary instead of a passive hook, add `deliver: true` and set `channel` / `to` explicitly.
