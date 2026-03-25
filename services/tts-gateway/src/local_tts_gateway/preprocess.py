from __future__ import annotations

import re
from dataclasses import dataclass


SENTENCE_BREAK_RE = re.compile(r"(?<=[。！？!?；;…])|(?<=[.])\s+(?=[A-Z0-9])")
WHITESPACE_RE = re.compile(r"\s+")
DATE_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
SLASH_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
NUMBER_RE = re.compile(r"\b\d{1,4}(?:,\d{3})*(?:\.\d+)?\b")
HAN_RE = re.compile(r"[\u3400-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z0-9]")


@dataclass(frozen=True)
class TextSegment:
    text: str
    lang: str


def normalize_text(text: str, lang: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = DATE_RE.sub(_normalize_iso_date(lang), normalized)
    normalized = SLASH_DATE_RE.sub(_normalize_slash_date(lang), normalized)
    normalized = NUMBER_RE.sub(_normalize_number(lang), normalized)
    normalized = WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip()


def _normalize_number(lang: str):
    def replacer(match: re.Match[str]) -> str:
        raw = match.group(0).replace(",", "")
        if lang == "zh":
            return raw
        return raw

    return replacer


def _normalize_iso_date(lang: str):
    def replacer(match: re.Match[str]) -> str:
        year = match.group(1)
        month = str(int(match.group(2)))
        day = str(int(match.group(3)))
        if lang == "en":
            return f"{year} year {month} month {day} day"
        return f"{year}年{month}月{day}日"

    return replacer


def _normalize_slash_date(lang: str):
    def replacer(match: re.Match[str]) -> str:
        month = str(int(match.group(1)))
        day = str(int(match.group(2)))
        year = match.group(3)
        if lang == "en":
            return f"{year} year {month} month {day} day"
        return f"{year}年{month}月{day}日"

    return replacer


def split_sentences(text: str) -> list[str]:
    pieces = [chunk.strip() for chunk in SENTENCE_BREAK_RE.split(text) if chunk and chunk.strip()]
    if pieces:
        return pieces
    return [text.strip()]


def chunk_sentences(sentences: list[str], soft_limit: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)
        if current and current_length + 1 + sentence_length > soft_limit:
            chunks.append(" ".join(current).strip())
            current = [sentence]
            current_length = sentence_length
            continue

        current.append(sentence)
        current_length += sentence_length + 1

    if current:
        chunks.append(" ".join(current).strip())

    return [chunk for chunk in chunks if chunk]


def preprocess_text(text: str, lang: str, soft_limit: int) -> list[str]:
    normalized = normalize_text(text, lang)
    sentences = split_sentences(normalized)
    return chunk_sentences(sentences, soft_limit)


def split_mixed_script_text(text: str, default_lang: str) -> list[TextSegment]:
    normalized = normalize_text(text, default_lang)
    if not normalized:
        return []

    segments: list[TextSegment] = []
    buffer: list[str] = []
    current_lang: str | None = None

    def flush() -> None:
        nonlocal buffer, current_lang
        chunk = "".join(buffer).strip()
        if chunk:
            segments.append(TextSegment(text=chunk, lang=current_lang or default_lang))
        buffer = []
        current_lang = None

    for char in normalized:
        char_lang = _classify_char_lang(char, default_lang)
        if current_lang is None:
            current_lang = char_lang
            buffer.append(char)
            continue

        if char_lang == current_lang or char_lang == "neutral":
            buffer.append(char)
            continue

        flush()
        current_lang = char_lang
        buffer.append(char)

    flush()
    return segments or [TextSegment(text=normalized, lang=default_lang)]


def _classify_char_lang(char: str, default_lang: str) -> str:
    if HAN_RE.search(char):
        return "zh"
    if LATIN_RE.search(char):
        return "en"
    return "neutral"
