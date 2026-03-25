#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()


def discover_repo_root() -> Path:
    for candidate in [Path.cwd(), *SCRIPT_PATH.parents]:
        if (candidate / ".env.local").exists():
            return candidate
        if (candidate / ".openclaw-dev").exists() and (candidate / "skills").exists():
            return candidate
    return SCRIPT_PATH.parents[3]


REPO_ROOT = discover_repo_root()


def load_env_local(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


ENV_LOCAL = load_env_local(REPO_ROOT / ".env.local")


def env_get(key: str, default: str = "") -> str:
    value = os.environ.get(key)
    if value is not None and value != "":
        return value
    return ENV_LOCAL.get(key, default)


def default_account() -> str:
    return env_get("GMAIL_ACCOUNT")


def gog_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base) / "gogcli"
    return Path.home() / "Library" / "Application Support" / "gogcli"


def credentials_path() -> Path:
    return gog_config_dir() / "credentials.json"


def run_command(args: list[str], *, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=os.environ.copy(),
    )
    if completed.returncode != 0 and not allow_failure:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "command failed")
    return completed


def gog_available() -> bool:
    return shutil.which("gog") is not None


def result_ok(**payload: Any) -> dict[str, Any]:
    payload["ok"] = True
    return payload


def result_error(code: str, message: str, **payload: Any) -> dict[str, Any]:
    data = {"ok": False, "error_code": code, "error": message}
    data.update(payload)
    return data


def auth_fix_instructions(account: str) -> list[str]:
    instructions = [
        "Download a Google OAuth Desktop App JSON from Google Cloud Console.",
        f"Store it with: gog auth credentials set /path/to/credentials.json",
        f"Authorize Gmail with: gog auth add {account or 'you@gmail.com'} --services gmail --gmail-scope full",
    ]
    return instructions


def parse_json_output(completed: subprocess.CompletedProcess[str]) -> Any:
    text = (completed.stdout or "").strip()
    if not text:
        return None
    return json.loads(text)


def recursive_find_messages(node: Any) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if isinstance(node, list):
        for item in node:
            messages.extend(recursive_find_messages(item))
        if node and all(isinstance(item, dict) for item in node):
            if all(("id" in item or "messageId" in item) for item in node):
                return [item for item in node if isinstance(item, dict)]
        return messages
    if isinstance(node, dict):
        if "id" in node or "messageId" in node:
            messages.append(node)
        for key in ("messages", "items", "threads", "results", "data"):
            if key in node:
                messages.extend(recursive_find_messages(node[key]))
        return messages
    return messages


def extract_headers(message: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {}
    candidates = []
    payload = message.get("payload")
    if isinstance(payload, dict):
        candidates.append(payload.get("headers"))
    candidates.append(message.get("headers"))
    for candidate in candidates:
        if isinstance(candidate, list):
            for item in candidate:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).lower()
                value = str(item.get("value", ""))
                if name:
                    headers[name] = value
        elif isinstance(candidate, dict):
            for key, value in candidate.items():
                headers[str(key).lower()] = str(value)
    return headers


def extract_body_text(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    for key in ("bodyText", "snippet", "text", "plainText"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    payload = node.get("payload")
    if isinstance(payload, dict):
        body = payload.get("body")
        if isinstance(body, dict):
            data = body.get("data")
            if isinstance(data, str) and data.strip():
                return data.strip()
        parts = payload.get("parts")
        if isinstance(parts, list):
            for part in parts:
                text = extract_body_text(part)
                if text:
                    return text
    return ""


def normalize_message(message: dict[str, Any]) -> dict[str, Any]:
    headers = extract_headers(message)
    snippet = str(message.get("snippet") or extract_body_text(message) or "").strip()
    return {
        "id": message.get("id") or message.get("messageId"),
        "thread_id": message.get("threadId") or message.get("thread_id"),
        "subject": headers.get("subject") or message.get("subject"),
        "from": headers.get("from") or message.get("from"),
        "to": headers.get("to") or message.get("to"),
        "date": headers.get("date") or message.get("internalDate") or message.get("date"),
        "snippet": snippet,
        "label_ids": message.get("labelIds") or message.get("labels") or [],
        "raw": message,
    }


def search_messages(account: str, query: str, limit: int) -> dict[str, Any]:
    cmd = ["gog", "gmail", "search", query, "-a", account, "--max", str(limit), "-j", "--results-only", "--no-input"]
    completed = run_command(cmd, allow_failure=True)
    stderr = (completed.stderr or "").strip()
    stdout = (completed.stdout or "").strip()
    if completed.returncode != 0:
        if "OAuth client credentials missing" in stderr or "OAuth client credentials missing" in stdout:
            return result_error(
                "oauth_credentials_missing",
                "gog is installed but Google OAuth client credentials are missing.",
                account=account,
                credentials_path=str(credentials_path()),
                next_steps=auth_fix_instructions(account),
            )
        return result_error("gmail_search_failed", stderr or stdout or "gmail search failed", account=account, query=query)
    payload = parse_json_output(completed)
    raw_items = recursive_find_messages(payload)
    normalized = [normalize_message(item) for item in raw_items]
    return result_ok(account=account, query=query, items=normalized, count=len(normalized), raw=payload)


def get_message(account: str, message_id: str) -> dict[str, Any]:
    cmd = ["gog", "gmail", "get", message_id, "-a", account, "--format", "full", "-j", "--results-only", "--no-input"]
    completed = run_command(cmd, allow_failure=True)
    stderr = (completed.stderr or "").strip()
    stdout = (completed.stdout or "").strip()
    if completed.returncode != 0:
        if "OAuth client credentials missing" in stderr or "OAuth client credentials missing" in stdout:
            return result_error(
                "oauth_credentials_missing",
                "gog is installed but Google OAuth client credentials are missing.",
                account=account,
                credentials_path=str(credentials_path()),
                next_steps=auth_fix_instructions(account),
            )
        return result_error("gmail_get_failed", stderr or stdout or "gmail get failed", account=account, message_id=message_id)
    payload = parse_json_output(completed)
    normalized = normalize_message(payload if isinstance(payload, dict) else {"raw": payload})
    normalized["body"] = extract_body_text(payload if isinstance(payload, dict) else {})
    return result_ok(account=account, message=normalized, raw=payload)


def mutate_messages(command: str, account: str, ids: list[str], query: str | None, limit: int) -> dict[str, Any]:
    cmd = ["gog", "gmail", command, "-a", account, "-j", "--results-only", "--no-input"]
    if query:
        cmd.extend(["--query", query, "--max", str(limit)])
    else:
        cmd.extend(ids)
    completed = run_command(cmd, allow_failure=True)
    stderr = (completed.stderr or "").strip()
    stdout = (completed.stdout or "").strip()
    if completed.returncode != 0:
        if "OAuth client credentials missing" in stderr or "OAuth client credentials missing" in stdout:
            return result_error(
                "oauth_credentials_missing",
                "gog is installed but Google OAuth client credentials are missing.",
                account=account,
                credentials_path=str(credentials_path()),
                next_steps=auth_fix_instructions(account),
            )
        return result_error(f"gmail_{command}_failed", stderr or stdout or f"gmail {command} failed", account=account)
    payload = parse_json_output(completed)
    return result_ok(account=account, command=command, ids=ids, query=query, limit=limit, raw=payload)


def status(account: str) -> dict[str, Any]:
    if not gog_available():
        return result_error("gog_missing", "gog is not installed on this machine.")
    auth_status = run_command(["gog", "auth", "status", "--plain", "--no-input"], allow_failure=True)
    creds_list = run_command(["gog", "auth", "credentials", "list", "--plain", "--no-input"], allow_failure=True)
    watch_status = None
    watch_started = False
    if account:
        watch = run_command(["gog", "gmail", "watch", "status", "--account", account], allow_failure=True)
        watch_status = (watch.stdout or watch.stderr or "").strip()
        watch_started = watch.returncode == 0
    return result_ok(
        account=account,
        gog_installed=True,
        gog_auth_status=(auth_status.stdout or auth_status.stderr or "").strip(),
        oauth_credentials_present=credentials_path().exists(),
        oauth_credentials_path=str(credentials_path()),
        watch_started=watch_started,
        watch_status=watch_status,
        next_steps=[] if credentials_path().exists() else auth_fix_instructions(account),
    )


def latest_query(unread_only: bool) -> str:
    base = "label:inbox"
    if unread_only:
        base += " is:unread"
    return f"{base} newer_than:30d"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Gmail helper for OpenClaw via gogcli")
    subparsers = parser.add_subparsers(dest="action", required=True)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--account", default=default_account())

    latest_parser = subparsers.add_parser("latest")
    latest_parser.add_argument("--account", default=default_account())
    latest_parser.add_argument("--limit", type=int, default=5)
    latest_parser.add_argument("--unread-only", action="store_true")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--account", default=default_account())
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--limit", type=int, default=10)

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("--account", default=default_account())
    get_parser.add_argument("--message-id", required=True)

    archive_parser = subparsers.add_parser("archive")
    archive_parser.add_argument("--account", default=default_account())
    archive_parser.add_argument("--ids", nargs="*", default=[])
    archive_parser.add_argument("--query")
    archive_parser.add_argument("--limit", type=int, default=50)

    mark_read_parser = subparsers.add_parser("mark-read")
    mark_read_parser.add_argument("--account", default=default_account())
    mark_read_parser.add_argument("--ids", nargs="*", default=[])
    mark_read_parser.add_argument("--query")
    mark_read_parser.add_argument("--limit", type=int, default=50)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    account = getattr(args, "account", "") or default_account()
    if args.action != "status" and not account:
        print(json.dumps(result_error("missing_account", "GMAIL_ACCOUNT is not set.", next_steps=["Set GMAIL_ACCOUNT in .env.local or pass --account."])))
        return 1

    try:
        if args.action == "status":
            result = status(account)
        elif args.action == "latest":
            result = search_messages(account, latest_query(args.unread_only), args.limit)
        elif args.action == "search":
            result = search_messages(account, args.query, args.limit)
        elif args.action == "get":
            result = get_message(account, args.message_id)
        elif args.action == "archive":
            if not args.ids and not args.query:
                result = result_error("missing_target", "Provide --ids or --query for archive.")
            else:
                result = mutate_messages("archive", account, args.ids, args.query, args.limit)
        elif args.action == "mark-read":
            if not args.ids and not args.query:
                result = result_error("missing_target", "Provide --ids or --query for mark-read.")
            else:
                result = mutate_messages("mark-read", account, args.ids, args.query, args.limit)
        else:
            result = result_error("unknown_action", f"Unsupported action: {args.action}")
    except Exception as exc:  # pragma: no cover - safety net for runtime usage
        print(json.dumps(result_error("unexpected_error", str(exc))))
        return 1

    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
