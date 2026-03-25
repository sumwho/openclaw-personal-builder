# Gmail Organizer

## Scope

This repository now includes a repo-local Gmail organization path for OpenClaw:

- a workspace skill: `skills/gmail-organizer/`
- a repo-local config seeder: `src/tools/openclaw_gmail_config.py`
- `make` entrypoints for setup and runtime

The design uses OpenClaw's built-in Gmail integration through:

- `openclaw webhooks gmail setup`
- `openclaw webhooks gmail run`

It does not introduce a custom Gmail transport.

## What It Does

The repo-local Gmail configuration prepares:

- `hooks.enabled=true`
- `hooks.presets=["gmail"]`
- one Gmail mapping for agent-driven inbox processing
- low-cost default model for Gmail hook runs: `qwen/qwen3.5-flash`
- `thinking: "off"` for routine inbox triage
- env-backed hook secrets:
  - `OPENCLAW_HOOK_TOKEN`
  - `GMAIL_PUSH_TOKEN`

The default mapping routes Gmail events into an agent run with:

- `wakeMode: "now"`
- `sessionKey: "hook:gmail:{{messages[0].id}}"`
- a compact message template containing sender, subject, snippet, and body
- `deliver: true`
- `channel: "last"`

This means the summary can return to the most recent active chat surface, which is useful for Telegram-driven use.

For direct chat-driven Gmail work, the repo also includes a local helper:

```sh
python3 skills/gmail-organizer/scripts/invoke_gmail.py status
python3 skills/gmail-organizer/scripts/invoke_gmail.py latest --limit 5 --unread-only
python3 skills/gmail-organizer/scripts/invoke_gmail.py search --query 'from:boss newer_than:7d'
python3 skills/gmail-organizer/scripts/invoke_gmail.py get --message-id <id>
```

Use that helper for:

- `查看我最新的邮件`
- `总结今天未读邮件`
- `找出来自某人的邮件`
- `把这些旧邮件归档`

## Commands

Seed repo-local config and env values:

```sh
make gmail-config
```

Check host dependencies:

```sh
make gmail-check
```

Run the Gmail watcher:

```sh
make gmail-run
```

## Required Host Dependencies

Current machine status:

- `openclaw`: installed
- `gog`: installed
- `gcloud`: installed
- `tailscale`: optional and currently not installed

Only `gog` and `gcloud` are required for the local non-Tailscale path currently wired by `make gmail-run`. If Homebrew does not link `gcloud` into `/opt/homebrew/bin`, the Makefile falls back to `/opt/homebrew/share/google-cloud-sdk/bin/gcloud`.

## Gmail OAuth Reality Check

`gcloud auth login` is not enough to let `gog` read Gmail.

`gog` needs its own OAuth client credentials and refresh token:

```sh
gog auth credentials set /path/to/credentials.json
gog auth add you@gmail.com --services gmail --gmail-scope full
```

If those steps are missing, the helper will return `oauth_credentials_missing` with the expected credential path.

## Required Environment

`make gmail-config` seeds `.env.local` with these keys if missing:

```sh
OPENCLAW_HOOK_TOKEN=
GMAIL_PUSH_TOKEN=
GMAIL_ACCOUNT=
GMAIL_LABEL=INBOX
GMAIL_PUBSUB_TOPIC=projects/REPLACE_ME/topics/gog-gmail-watch
GMAIL_PUBSUB_SUBSCRIPTION=gog-gmail-watch-push
```

You must still fill in:

- `GMAIL_ACCOUNT`
- `GMAIL_PUBSUB_TOPIC`
- optionally `GMAIL_PUBSUB_SUBSCRIPTION`

## Practical Next Steps

1. Ensure `gcloud` and `gog` are available
2. Run `make gmail-config`
3. Fill `GMAIL_ACCOUNT` and Pub/Sub values in `.env.local`
4. Start the local gateway with `make gui-gateway`
5. Start the Gmail watcher with `make gmail-run`

## Model Strategy

For Gmail hook runs, the repo defaults to:

- model: `qwen/qwen3.5-flash`
- thinking: `off`

This is deliberate:

- routine inbox triage is latency-sensitive and repetitive
- deep reasoning is usually unnecessary
- cost stays low for automatic mail summaries

If you later want more nuanced drafting or thread interpretation, move Gmail to:

- `qwen/qwen3.5-plus`

or for heavy reasoning:

- `qwen/qwen3-max-2026-01-23`
