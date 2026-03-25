# Browser Research Sandbox

This repository includes a constrained web lookup skill at [skills/browser-research-sandbox](/Volumes/ExtendStorage/workspace/ai/openclaw/skills/browser-research-sandbox).

## Goal

Provide a web information query path for OpenClaw without enabling the broad built-in `browser` tool.

The design is intentionally narrow:

- read-only search and page retrieval
- public web targets only
- no login flows
- no uploads
- no local service access
- no reuse of your host browser profile, cookies, or shell environment

## Safety Properties

The helper script [browser_research.py](/Volumes/ExtendStorage/workspace/ai/openclaw/skills/browser-research-sandbox/scripts/browser_research.py):

- re-execs itself into an isolated subprocess
- uses a fresh temporary `HOME`
- clears inherited environment variables
- prefers headless Chrome with a temporary user-data-dir when available
- writes only under `.openclaw-dev/browser-research-sandbox/`
- blocks `file://`, `javascript:`, `data:`, `localhost`, loopback, and private-network targets

Execution modes:

- Preferred: isolated headless Chrome / Chromium with a temporary `HOME`
- Fallback: `sandbox-exec` plus plain HTTP retrieval if Chrome is unavailable

## Important Boundary

This is a practical containment layer, not a formally verified DLP system.

It meaningfully reduces accidental leakage by:

- not giving the subprocess local chat logs or repo paths as input
- not giving it your normal browser profile or cookies
- not allowing local/private URLs

If you need a stronger boundary than this, move the same workflow into a dedicated VM or container with no repository mount.

## Usage

Search:

```sh
python3 skills/browser-research-sandbox/scripts/browser_research.py search \
  --query "OpenClaw Gmail Pub/Sub docs" \
  --limit 5
```

Fetch:

```sh
python3 skills/browser-research-sandbox/scripts/browser_research.py fetch \
  --url "https://docs.openclaw.ai/automation/gmail-pubsub" \
  --max-chars 6000
```

## OpenClaw Policy Recommendation

Use this skill only for external factual lookup. Do not use it for:

- local admin panels
- intranet targets
- credentialed SaaS sessions
- payment or purchase pages
- anything that requires typing local private content into a remote form
