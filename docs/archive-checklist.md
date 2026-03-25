# Archive Checklist

This document defines what belongs in git for the current OpenClaw local stack, what must remain local-only, and what must be recreated on a new machine.

## Commit To Git

Commit these categories:

- source code under [services/](/Volumes/ExtendStorage/workspace/ai/openclaw/services)
- reusable scripts under [scripts/](/Volumes/ExtendStorage/workspace/ai/openclaw/scripts) and [src/tools/](/Volumes/ExtendStorage/workspace/ai/openclaw/src/tools)
- skills under [skills/](/Volumes/ExtendStorage/workspace/ai/openclaw/skills)
- workspace templates under [assets/openclaw-workspace](/Volumes/ExtendStorage/workspace/ai/openclaw/assets/openclaw-workspace) and [assets/openclaw-workspace-wife-english](/Volumes/ExtendStorage/workspace/ai/openclaw/assets/openclaw-workspace-wife-english)
- documentation under [docs/](/Volumes/ExtendStorage/workspace/ai/openclaw/docs)
- safe example configuration such as [.env.example](/Volumes/ExtendStorage/workspace/ai/openclaw/.env.example) and [config.yaml.example](/Volumes/ExtendStorage/workspace/ai/openclaw/config/config.yaml.example)
- automated tests under [tests/](/Volumes/ExtendStorage/workspace/ai/openclaw/tests)
- top-level entrypoints such as [README.md](/Volumes/ExtendStorage/workspace/ai/openclaw/README.md) and [Makefile](/Volumes/ExtendStorage/workspace/ai/openclaw/Makefile)

## Do Not Commit

Keep these local-only:

- [`.env.local`](/Volumes/ExtendStorage/workspace/ai/openclaw/.env.local)
- [`.openclaw-dev/`](/Volumes/ExtendStorage/workspace/ai/openclaw/.openclaw-dev)
- deployment runtime under `/Volumes/ExtendStorage/openclaw`
- logs, caches, temp files, audio outputs, virtualenvs, model files
- Gmail OAuth client secrets and gog auth state
- Telegram bot token values
- Qwen OAuth credentials and refresh tokens
- Weixin session/account state

These are runtime state, secrets, or machine-specific artifacts and must not enter git.

## Local Runtime Only

These items affect the current machine but are not fully represented as source files:

- repo-local OpenClaw config in `.openclaw-dev/config.json`
- repo-local sessions, pairings, media, and workspace mirrors in `.openclaw-dev/state-live/`
- local channel login state for Telegram and Weixin
- host-installed OpenClaw runtime files under the global npm/nvm installation

For host-installed OpenClaw runtime patching, keep the script in git:

- [patch-openclaw-runtime.sh](/Volumes/ExtendStorage/workspace/ai/openclaw/scripts/patch-openclaw-runtime.sh)

But do not treat the patched installed files themselves as versioned project files.

## Rebuild On A New Machine

These steps recreate the working environment after cloning:

1. Create `.env.local` from [.env.example](/Volumes/ExtendStorage/workspace/ai/openclaw/.env.example)
2. Run the repo-local seed/config sync:
   `node src/tools/openclaw_seed_config.mjs .openclaw-dev/config.json .openclaw-dev`
3. Start the local gateway:
   `make gui-gateway`
4. Re-login channel providers and model auth as needed:
   - Telegram bot token in `.env.local`
   - Weixin login via `openclaw channels login --channel openclaw-weixin`
   - Qwen OAuth via `openclaw models auth login --provider qwen-portal`
5. Recreate local TTS deployment:
   `PYTHON_BIN=/opt/homebrew/bin/python3.12 bash scripts/setup.sh`
6. Reapply any host OpenClaw runtime compatibility patch if needed:
   `make gui-runtime-patch`

## Current Feature Set That Should Be In Git

The current project baseline should include:

- local TTS gateway, Melo integration, and OpenClaw local-tts skill
- Gmail organizer skill and Gmail config helper
- browser-research-sandbox skill
- native_english_rewriter_v2 skill
- repo-local model profile helper
- wife-specific English-learning workspace templates and Weixin binding helper
- updated runbooks and learning docs that reflect the local-first architecture

## Verification Before Commit

Recommended checks for this repository state:

- `python3 -m unittest tests.test_browser_research`
- `python3 -m unittest tests.test_gmail_invoke`
- `python3 -m unittest tests.test_local_tts_invoke`
- `python3 -m unittest tests.test_tts_preprocess tests.test_tts_security tests.test_tts_config tests.test_tts_melo_patch tests.test_tts_service`
