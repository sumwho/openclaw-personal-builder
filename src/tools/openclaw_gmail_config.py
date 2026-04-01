#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path


DEFAULT_CONFIG_PATH = Path(".openclaw-dev/config.json")
DEFAULT_ENV_PATH = Path(".env.local")
DEFAULT_GMAIL_LABEL = "INBOX"
DEFAULT_GMAIL_TOPIC = "projects/REPLACE_ME/topics/gog-gmail-watch"
DEFAULT_GMAIL_SUBSCRIPTION = "gog-gmail-watch-push"
DEFAULT_GMAIL_MODEL = "dashscope/qwen3.5-flash"
DEFAULT_HOOK_TOKEN_REF = "${OPENCLAW_HOOK_TOKEN}"
DEFAULT_PUSH_TOKEN_REF = "${GMAIL_PUSH_TOKEN}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed repo-local Gmail hook config for OpenClaw.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_PATH))
    parser.add_argument("--gateway-port", type=int, default=18789)
    parser.add_argument("--account", default=None)
    parser.add_argument("--label", default=DEFAULT_GMAIL_LABEL)
    parser.add_argument("--topic", default=DEFAULT_GMAIL_TOPIC)
    parser.add_argument("--subscription", default=DEFAULT_GMAIL_SUBSCRIPTION)
    parser.add_argument("--deliver", choices=["last", "none"], default="last")
    parser.add_argument("--model", default=DEFAULT_GMAIL_MODEL)
    parser.add_argument("--thinking", choices=["off", "minimal", "low", "medium", "high"], default="off")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value
    return values


def write_env_file(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={values[key]}" for key in sorted(values)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_secret(values: dict[str, str], key: str) -> None:
    if values.get(key):
        return
    values[key] = secrets.token_urlsafe(24)


def upsert_mapping(mappings: list[dict], mapping: dict) -> list[dict]:
    next_mappings: list[dict] = []
    replaced = False
    for existing in mappings:
        if not isinstance(existing, dict):
            next_mappings.append(existing)
            continue
        match = existing.get("match")
        path_value = match.get("path") if isinstance(match, dict) else None
        if path_value == "gmail":
            next_mappings.append({**existing, **mapping, "match": {"path": "gmail"}})
            replaced = True
        else:
            next_mappings.append(existing)
    if not replaced:
        next_mappings.append(mapping)
    return next_mappings


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    env_path = Path(args.env_file).resolve()

    config = load_json(config_path)
    env_values = parse_env_file(env_path)

    ensure_secret(env_values, "OPENCLAW_HOOK_TOKEN")
    ensure_secret(env_values, "GMAIL_PUSH_TOKEN")
    env_values.setdefault("GMAIL_ACCOUNT", args.account or "")
    env_values.setdefault("GMAIL_LABEL", args.label)
    env_values.setdefault("GMAIL_PUBSUB_TOPIC", args.topic)
    env_values.setdefault("GMAIL_PUBSUB_SUBSCRIPTION", args.subscription)

    hooks = config.get("hooks") if isinstance(config.get("hooks"), dict) else {}
    presets = hooks.get("presets") if isinstance(hooks.get("presets"), list) else []
    mappings = hooks.get("mappings") if isinstance(hooks.get("mappings"), list) else []

    mapping = {
        "match": {"path": "gmail"},
        "action": "agent",
        "wakeMode": "now",
        "name": "Gmail Organizer",
        "sessionKey": "hook:gmail:{{messages[0].id}}",
        "messageTemplate": "New email from {{messages[0].from}}\nSubject: {{messages[0].subject}}\n{{messages[0].snippet}}\n{{messages[0].body}}",
        "model": args.model,
        "thinking": args.thinking,
        "deliver": args.deliver != "none",
    }
    if args.deliver != "none":
        mapping["channel"] = "last"

    gmail_cfg = hooks.get("gmail") if isinstance(hooks.get("gmail"), dict) else {}
    next_gmail_cfg = {
        **gmail_cfg,
        "label": env_values["GMAIL_LABEL"],
        "topic": env_values["GMAIL_PUBSUB_TOPIC"],
        "subscription": env_values["GMAIL_PUBSUB_SUBSCRIPTION"],
        "pushToken": DEFAULT_PUSH_TOKEN_REF,
        "hookUrl": f"http://127.0.0.1:{args.gateway_port}/hooks/gmail",
        "includeBody": True,
        "maxBytes": 20000,
        "renewEveryMinutes": 720,
        "serve": {
            "bind": "127.0.0.1",
            "port": 8788,
            "path": "/gmail-pubsub",
        },
        "tailscale": {
            "mode": "off",
        },
        "model": args.model,
        "thinking": args.thinking,
    }
    if env_values["GMAIL_ACCOUNT"]:
        next_gmail_cfg["account"] = env_values["GMAIL_ACCOUNT"]

    config["hooks"] = {
        **hooks,
        "enabled": True,
        "path": hooks.get("path") or "/hooks",
        "token": DEFAULT_HOOK_TOKEN_REF,
        "presets": sorted({*(value for value in presets if isinstance(value, str)), "gmail"}),
        "mappings": upsert_mapping(mappings, mapping),
        "gmail": next_gmail_cfg,
    }

    dump_json(config_path, config)
    write_env_file(env_path, env_values)

    print(
        json.dumps(
            {
                "config_path": str(config_path),
                "env_file": str(env_path),
                "gmail_account": env_values["GMAIL_ACCOUNT"] or None,
                "gmail_label": env_values["GMAIL_LABEL"],
                "gmail_topic": env_values["GMAIL_PUBSUB_TOPIC"],
                "gmail_subscription": env_values["GMAIL_PUBSUB_SUBSCRIPTION"],
                "model": args.model,
                "deliver": args.deliver,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
