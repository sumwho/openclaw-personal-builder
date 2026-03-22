from __future__ import annotations

import re


SENTENCE_BREAK_RE = re.compile(r"(?<=[。！？!?；;…])|(?<=[.])\s+(?=[A-Z0-9])")
WHITESPACE_RE = re.compile(r"\s+")
DATE_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
SLASH_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
NUMBER_RE = re.compile(r"\b\d{1,4}(?:,\d{3})*(?:\.\d+)?\b")


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
