#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bind a Weixin accountId to a specific OpenClaw agent via bindings[].",
    )
    parser.add_argument("--config", default=".openclaw-dev/config.json", help="Path to repo-local config.json")
    parser.add_argument("--account-id", required=True, help="Weixin accountId to bind")
    parser.add_argument("--agent-id", default="wife-english", help="Target agent id")
    parser.add_argument("--channel", default="openclaw-weixin", help="Channel id")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    account_id = args.account_id.strip()
    agent_id = args.agent_id.strip()
    channel = args.channel.strip()

    if not account_id:
        raise SystemExit("account-id must not be empty")
    if not agent_id:
        raise SystemExit("agent-id must not be empty")

    data = json.loads(config_path.read_text(encoding="utf-8"))

    agent_ids = {
        agent.get("id")
        for agent in data.get("agents", {}).get("list", [])
        if isinstance(agent, dict) and isinstance(agent.get("id"), str)
    }
    if agent_id not in agent_ids:
        raise SystemExit(f"unknown agent id: {agent_id}")

    channels = data.setdefault("channels", {})
    channel_cfg = channels.setdefault(channel, {})
    if not isinstance(channel_cfg, dict):
        raise SystemExit(f"channels.{channel} is not an object")
    accounts_cfg = channel_cfg.setdefault("accounts", {})
    if not isinstance(accounts_cfg, dict):
        raise SystemExit(f"channels.{channel}.accounts is not an object")
    accounts_cfg.setdefault(account_id, {})

    bindings = data.setdefault("bindings", [])
    if not isinstance(bindings, list):
        raise SystemExit("bindings is not a list")

    next_bindings = []
    for entry in bindings:
        if not isinstance(entry, dict):
            next_bindings.append(entry)
            continue
        match = entry.get("match")
        if (
            isinstance(match, dict)
            and entry.get("agentId")
            and match.get("channel") == channel
            and match.get("accountId") == account_id
        ):
            continue
        next_bindings.append(entry)

    next_bindings.insert(
        0,
        {
            "agentId": agent_id,
            "match": {
                "channel": channel,
                "accountId": account_id,
            },
        },
    )
    data["bindings"] = next_bindings

    config_path.write_text(f"{json.dumps(data, ensure_ascii=False, indent=2)}\n", encoding="utf-8")

    print(f"Bound {channel}:{account_id} -> {agent_id}")
    print("Restart the gateway to apply the new binding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
