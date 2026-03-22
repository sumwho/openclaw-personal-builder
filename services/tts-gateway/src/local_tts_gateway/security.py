from __future__ import annotations

import re
from pathlib import Path


SAFE_TEXT_PATTERN = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


class SecurityError(ValueError):
    pass


def sanitize_text(text: str, max_length: int) -> str:
    cleaned = SAFE_TEXT_PATTERN.sub(" ", text).strip()
    if len(cleaned) > max_length:
        raise SecurityError(f"text length exceeds max_input_length={max_length}")
    return cleaned


def ensure_within_base(path: Path, base_dir: Path) -> Path:
    resolved = path.resolve()
    base_resolved = base_dir.resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise SecurityError(f"path escapes configured base_dir: {resolved}") from exc
    return resolved
