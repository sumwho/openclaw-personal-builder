from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


AudioFormat = Literal["mp3", "wav"]
LanguageCode = Literal["zh", "en"]
EngineName = Literal["melo", "kokoro", "piper"]


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    voice: str | None = None
    lang: LanguageCode | None = None
    format: AudioFormat = "mp3"
    speed: float = Field(default=1.0, ge=0.5, le=1.8)
    engine: EngineName | None = None

    @field_validator("text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("text cannot be empty")
        return cleaned


class SpeechResponse(BaseModel):
    audio_path: str
    engine_used: EngineName
    chunks: int
    duration_hint: str


class HealthResponse(BaseModel):
    status: str
    default_engine: str
    ffmpeg_available: bool


class VoiceInfo(BaseModel):
    name: str
    lang: str
    engines: list[str]
