#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SANDBOX_ROOT = REPO_ROOT / ".openclaw-dev" / "browser-research-sandbox"
INNER_ENV_FLAG = "OPENCLAW_BROWSER_RESEARCH_INNER"
ISOLATED_ENV_FLAG = "OPENCLAW_BROWSER_RESEARCH_ISOLATED"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
)
BLOCKED_HOSTS = {"localhost", "localhost.localdomain"}
BLOCKED_SCHEMES = {"file", "javascript", "data", "chrome", "about"}
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        elif tag in {"p", "br", "div", "section", "article", "li", "h1", "h2", "h3", "h4"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        elif tag in {"p", "br", "div", "section", "article", "li", "h1", "h2", "h3", "h4"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._chunks.append(data)

    def text(self) -> str:
        joined = html.unescape(" ".join(self._chunks))
        joined = re.sub(r"\s+", " ", joined)
        joined = re.sub(r"( ?\n ?)+", "\n", joined)
        return joined.strip()


def extract_text(raw_html: str) -> tuple[str | None, str]:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
    title = None
    if title_match:
        title = html.unescape(re.sub(r"\s+", " ", title_match.group(1))).strip()
    parser = TextExtractor()
    parser.feed(raw_html)
    return title, parser.text()


def is_blocked_host(hostname: str) -> bool:
    lowered = hostname.strip().strip(".").lower()
    if not lowered:
        return True
    if lowered in BLOCKED_HOSTS or lowered.endswith(".local") or lowered.endswith(".localdomain") or lowered.endswith(".internal"):
        return True
    try:
        addr = ipaddress.ip_address(lowered)
        return (
            addr.is_loopback
            or addr.is_private
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
            or addr.is_unspecified
        )
    except ValueError:
        return False


def validate_public_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    scheme = parsed.scheme.lower()
    if scheme in BLOCKED_SCHEMES:
        raise ValueError(f"unsupported scheme: {scheme}")
    if scheme not in {"http", "https"}:
        raise ValueError("only http and https URLs are allowed")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("credential-bearing URLs are not allowed")
    if is_blocked_host(parsed.hostname):
        raise ValueError(f"blocked host: {parsed.hostname}")
    return urllib.parse.urlunparse(parsed)


def http_get(url: str, *, timeout: int = 20) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.5",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text" not in content_type and "html" not in content_type and "xml" not in content_type:
            raise ValueError(f"unsupported content type: {content_type}")
        body = response.read()
    return body.decode("utf-8", errors="replace")


def find_chrome() -> str | None:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")


def chrome_get(url: str, *, timeout: int = 25) -> str:
    chrome = find_chrome()
    if not chrome:
        raise FileNotFoundError("Chrome/Chromium not found")

    command = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-sync",
        "--disable-background-networking",
        "--disable-default-apps",
        "--disable-component-update",
        "--no-first-run",
        "--no-default-browser-check",
        "--use-mock-keychain",
        f"--user-agent={USER_AGENT}",
        "--dump-dom",
        url,
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={
            "HOME": os.environ.get("HOME", "/tmp"),
            "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
            "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"),
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
            "LC_ALL": os.environ.get("LC_ALL", "en_US.UTF-8"),
        },
    )
    output = completed.stdout.strip()
    if not output:
        raise RuntimeError("headless browser returned empty DOM")
    return output


def search(query: str, limit: int) -> dict:
    search_url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    raw_html = http_get(search_url)
    engine = "http"
    matches = re.findall(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        raw_html,
        re.IGNORECASE | re.DOTALL,
    )
    results = []
    seen = set()
    for href, raw_title in matches:
        if len(results) >= limit:
            break
        parsed_href = html.unescape(href)
        candidate = urllib.parse.urlparse(parsed_href)
        final_url = parsed_href
        if candidate.netloc.endswith("duckduckgo.com") and candidate.path.startswith("/l/"):
            qs = urllib.parse.parse_qs(candidate.query)
            final_url = qs.get("uddg", [parsed_href])[0]
        elif candidate.netloc.endswith("duckduckgo.com"):
            continue
        try:
            final_url = validate_public_url(final_url)
        except ValueError:
            continue
        final_host = urllib.parse.urlparse(final_url).hostname or ""
        if final_host.endswith("duckduckgo.com"):
            continue
        if final_url in seen:
            continue
        seen.add(final_url)
        title = html.unescape(re.sub(r"<[^>]+>", " ", raw_title))
        title = re.sub(r"\s+", " ", title).strip()
        results.append({"title": title, "url": final_url})
    return {"mode": "search", "query": query, "results": results, "engine": engine}


def fetch(url: str, max_chars: int) -> dict:
    safe_url = validate_public_url(url)
    try:
        raw_html = chrome_get(safe_url)
        engine = "chrome"
    except Exception:
        raw_html = http_get(safe_url)
        engine = "http"
    title, text = extract_text(raw_html)
    if max_chars > 0:
        text = text[:max_chars]
    return {"mode": "fetch", "url": safe_url, "title": title, "text": text, "engine": engine}


def make_profile(tmp_root: Path) -> Path:
    profile = tmp_root / "browser_research.sb"
    profile.write_text(
        "\n".join(
            [
                "(version 1)",
                "(deny default)",
                "(allow process-exec)",
                "(allow process-fork)",
                "(allow signal (target self))",
                "(allow sysctl-read)",
                "(allow mach-lookup)",
                "(allow ipc-posix-shm)",
                "(allow network-outbound)",
                "(allow file-read*)",
                f'(allow file-write* (subpath "{tmp_root}"))',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return profile


def reexec_in_sandbox(argv: list[str]) -> int:
    sandbox_exec = shutil.which("sandbox-exec")
    if not sandbox_exec:
        print(json.dumps({"ok": False, "error": "sandbox-exec not found"}))
        return 1

    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
    tmp_root = Path(tempfile.mkdtemp(prefix="run-", dir=str(SANDBOX_ROOT)))
    home_dir = tmp_root / "home"
    tmp_dir = tmp_root / "tmp"
    home_dir.mkdir()
    tmp_dir.mkdir()
    profile = make_profile(tmp_root)

    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "HOME": str(home_dir),
        "TMPDIR": str(tmp_dir),
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
        INNER_ENV_FLAG: "1",
    }
    command = [sandbox_exec, "-f", str(profile), sys.executable, str(Path(__file__).resolve()), *argv]
    completed = subprocess.run(command, env=env, cwd=str(REPO_ROOT))
    return completed.returncode


def reexec_isolated(argv: list[str]) -> int:
    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
    tmp_root = Path(tempfile.mkdtemp(prefix="run-", dir=str(SANDBOX_ROOT)))
    home_dir = tmp_root / "home"
    tmp_dir = tmp_root / "tmp"
    home_dir.mkdir()
    tmp_dir.mkdir()
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "HOME": str(home_dir),
        "TMPDIR": str(tmp_dir),
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
        ISOLATED_ENV_FLAG: "1",
        INNER_ENV_FLAG: "1",
    }
    completed = subprocess.run([sys.executable, str(Path(__file__).resolve()), *argv], env=env, cwd=str(REPO_ROOT))
    return completed.returncode


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sandboxed web research helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--limit", type=int, default=5)

    fetch_parser = subparsers.add_parser("fetch")
    fetch_parser.add_argument("--url", required=True)
    fetch_parser.add_argument("--max-chars", type=int, default=6000)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    if os.environ.get(INNER_ENV_FLAG) != "1":
        if find_chrome():
            return reexec_isolated(argv)
        return reexec_in_sandbox(argv)

    args = parse_args(argv)
    try:
        if args.command == "search":
            payload = search(args.query, args.limit)
        else:
            payload = fetch(args.url, args.max_chars)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1

    payload["ok"] = True
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
