from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SynthesisRequest:
    text: str
    lang: str
    voice: str
    speed: float
    output_path: Path
    model_path: str | None = None
    config_path: str | None = None
    speaker: str | None = None
    lang_code: str | None = None


class EngineError(RuntimeError):
    pass


class BaseTTSEngine:
    engine_name = "base"

    def synthesize_chunk(self, request: SynthesisRequest) -> Path:
        raise NotImplementedError
