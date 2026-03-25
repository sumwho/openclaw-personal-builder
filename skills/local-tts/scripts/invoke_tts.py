#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_URL = "http://127.0.0.1:28641/v1/audio/speech"
DEFAULT_BASE_DIR = "/Volumes/ExtendStorage/openclaw"
DEFAULT_HEALTH_PATH = "http://127.0.0.1:28641/health"
HAN_RE = re.compile(r"[\u3400-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z]")
QUOTE_PATTERNS = [
    re.compile(r"“([^”]+)”"),
    re.compile(r'"([^"]+)"'),
    re.compile(r"'([^']+)'"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Invoke the local OpenClaw TTS gateway.")
    parser.add_argument("--text", required=True)
    parser.add_argument("--voice", default=None)
    parser.add_argument("--lang", choices=["zh", "en"], default=None)
    parser.add_argument("--format", choices=["mp3", "wav"], default="mp3")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--engine", choices=["melo", "kokoro", "piper"], default=None)
    parser.add_argument("--url", default=DEFAULT_URL)
    return parser.parse_args()


def extract_payload_text(text: str) -> str:
    stripped = text.strip()
    for pattern in QUOTE_PATTERNS:
        matches = [match.group(1).strip() for match in pattern.finditer(stripped) if match.group(1).strip()]
        if matches:
            # Prefer the longest quoted span to avoid reading the wrapper instruction.
            return max(matches, key=len)
    return stripped


def infer_lang_and_voice(text: str, lang: str | None, voice: str | None) -> tuple[str | None, str | None]:
    if lang is not None and voice is not None:
        return lang, voice

    has_han = HAN_RE.search(text) is not None
    has_latin = LATIN_RE.search(text) is not None

    if has_han and has_latin:
        return lang or "zh", voice or "zh_mix_en"

    if has_han:
        return lang or "zh", voice or "default_zh"

    return lang or "en", voice or "default_en"


def infer_engine(engine: str | None) -> str:
    return engine or "melo"


def infer_delivery_message(lang: str | None) -> str:
    if lang == "zh":
        return "已生成语音，请查收。"
    return "Audio generated. See attached file."


def emit_result(payload: dict[str, object]) -> int:
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def health_url_for_request(url: str) -> str:
    if url.endswith("/v1/audio/speech"):
        return url[: -len("/v1/audio/speech")] + "/health"
    return DEFAULT_HEALTH_PATH


def endpoint_available(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 300
    except urllib.error.URLError:
        return False


def ensure_gateway(url: str) -> tuple[bool, str | None]:
    health_url = health_url_for_request(url)
    if endpoint_available(health_url):
        return True, None

    base_dir = os.environ.get("OPENCLAW_TTS_BASE_DIR", DEFAULT_BASE_DIR)
    start_script = os.path.join(base_dir, "scripts", "start.sh")
    if not os.path.exists(start_script):
        return False, f"TTS gateway is unavailable and start script was not found: {start_script}"

    env = os.environ.copy()
    env.setdefault("OPENCLAW_TTS_BASE_DIR", base_dir)

    try:
        result = subprocess.run(
            ["bash", start_script],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return False, f"failed to execute start script: {exc}"

    if result.returncode not in (0,):
        detail = (result.stderr or result.stdout or "").strip()
        if not detail:
            detail = f"start script exited with code {result.returncode}"
        return False, f"failed to start local TTS gateway: {detail}"

    deadline = time.time() + 20.0
    while time.time() < deadline:
        if endpoint_available(health_url):
            return True, None
        time.sleep(0.5)

    detail = (result.stdout or result.stderr or "").strip()
    return False, f"TTS gateway did not become ready after startup attempt: {detail}"


def discover_openclaw_state_dir() -> Path | None:
    env_state_dir = os.environ.get("OPENCLAW_STATE_DIR")
    candidates: list[Path] = []
    if env_state_dir:
        candidates.append(Path(env_state_dir).expanduser())

    script_path = Path(__file__).resolve()
    cwd_path = Path.cwd().resolve()

    for anchor in [cwd_path, script_path.parent]:
        candidates.append(anchor)
        candidates.extend(anchor.parents)

    seen: set[Path] = set()
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except OSError:
            continue
        if candidate in seen:
            continue
        seen.add(candidate)

        if (candidate / "agents").is_dir() and (candidate / "workspace-main").is_dir():
            return candidate

        nested_state_dir = candidate / ".openclaw-dev" / "state-live"
        if nested_state_dir.is_dir():
            return nested_state_dir.resolve()

    return None


def stage_audio_for_delivery(audio_path: str | None) -> str | None:
    if not audio_path:
        return None

    source_path = Path(audio_path).expanduser()
    if not source_path.is_file():
        return None

    state_dir = discover_openclaw_state_dir()
    if state_dir is None:
        return None

    target_dir = state_dir / "media" / "local-tts"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / source_path.name
    shutil.copy2(source_path, target_path)
    return str(target_path)


def main() -> int:
    args = parse_args()
    payload_text = extract_payload_text(args.text)
    lang, voice = infer_lang_and_voice(payload_text, args.lang, args.voice)
    engine = infer_engine(args.engine)
    gateway_ok, gateway_error = ensure_gateway(args.url)
    if not gateway_ok:
        return emit_result(
            {
                "ok": False,
                "error": gateway_error,
                "audio_path": None,
                "delivery_audio_path": None,
                "delivery_message": infer_delivery_message(lang),
                "engine_used": None,
            }
        )

    payload = {
        "text": payload_text,
        "voice": voice,
        "lang": lang,
        "format": args.format,
        "speed": args.speed,
        "engine": engine,
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
        return emit_result(
            {
                "ok": False,
                "error": error_body or str(exc),
                "audio_path": None,
                "delivery_audio_path": None,
                "delivery_message": infer_delivery_message(lang),
                "engine_used": None,
            }
        )
    except urllib.error.URLError as exc:
        return emit_result(
            {
                "ok": False,
                "error": str(exc),
                "audio_path": None,
                "delivery_audio_path": None,
                "delivery_message": infer_delivery_message(lang),
                "engine_used": None,
            }
        )

    body["delivery_audio_path"] = stage_audio_for_delivery(body.get("audio_path"))
    body["delivery_message"] = infer_delivery_message(lang)
    body["ok"] = True
    return emit_result(body)


if __name__ == "__main__":
    raise SystemExit(main())
