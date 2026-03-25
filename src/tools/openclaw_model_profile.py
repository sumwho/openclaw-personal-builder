#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path
import sys


PROFILES = {
    "cheap": "qwen/qwen3.5-flash",
    "balanced": "qwen/qwen3.5-plus",
    "reasoning": "qwen/qwen3-max-2026-01-23",
    "analysis": "qwen/tongyi-xiaomi-analysis-pro",
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in PROFILES:
        valid = ", ".join(sorted(PROFILES))
        print(f"usage: {Path(sys.argv[0]).name} <{valid}>", file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / ".openclaw-dev" / "config.json"
    data = json.loads(config_path.read_text())

    data.setdefault("meta", {})
    data["meta"]["lastTouchedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    data["agents"]["defaults"]["model"]["primary"] = PROFILES[sys.argv[1]]

    config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(PROFILES[sys.argv[1]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
