#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


DEFAULT_URL = "http://127.0.0.1:28641/v1/audio/speech"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Invoke the local OpenClaw TTS gateway.")
    parser.add_argument("--text", required=True)
    parser.add_argument("--voice", default=None)
    parser.add_argument("--lang", choices=["zh", "en"], default=None)
    parser.add_argument("--format", choices=["mp3", "wav"], default="mp3")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--engine", choices=["kokoro", "piper"], default=None)
    parser.add_argument("--url", default=DEFAULT_URL)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = {
        "text": args.text,
        "voice": args.voice,
        "lang": args.lang,
        "format": args.format,
        "speed": args.speed,
        "engine": args.engine,
    }
    request = urllib.request.Request(
        args.url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(error_body, file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(body, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
