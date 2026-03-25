from __future__ import annotations

import logging
from pathlib import Path

from local_tts_gateway.config import AppConfig, VoiceConfig

from .base import BaseTTSEngine, EngineError, SynthesisRequest
from .kokoro_mlx import KokoroMLXEngine
from .melo import MeloEngine
from .piper import PiperEngine


LOGGER = logging.getLogger(__name__)


class EngineRegistry:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.engines: dict[str, BaseTTSEngine] = {
            "melo": MeloEngine(
                python_bin=config.melo.python_bin,
                sample_rate=config.melo.sample_rate,
            ),
            "kokoro": KokoroMLXEngine(
                python_bin=config.kokoro.python_bin,
                model_ref=config.kokoro.model_ref,
                sample_rate=config.kokoro.sample_rate,
            ),
            "piper": PiperEngine(
                executable=config.piper.executable,
                sample_rate=config.piper.sample_rate,
            ),
        }

    def available_engines_for_voice(self, voice: VoiceConfig) -> list[str]:
        engines: list[str] = []
        if voice.melo.speaker and voice.melo.lang_code:
            engines.append("melo")
        if voice.kokoro.voice:
            engines.append("kokoro")
        if voice.piper.model:
            engines.append("piper")
        return engines

    def build_request(
        self,
        engine_name: str,
        voice: VoiceConfig,
        text: str,
        speed: float,
        output_path: Path,
    ) -> SynthesisRequest:
        if engine_name == "melo":
            return SynthesisRequest(
                text=text,
                lang=voice.lang,
                voice=voice.melo.voice or voice.name,
                speed=speed,
                output_path=output_path,
                model_path=voice.melo.model,
                config_path=voice.melo.config,
                speaker=voice.melo.speaker,
                lang_code=voice.melo.lang_code,
            )
        if engine_name == "kokoro":
            return SynthesisRequest(
                text=text,
                lang=voice.lang,
                voice=voice.kokoro.voice or voice.name,
                speed=speed,
                output_path=output_path,
                lang_code=voice.kokoro.lang_code,
            )
        if engine_name == "piper":
            return SynthesisRequest(
                text=text,
                lang=voice.lang,
                voice=voice.name,
                speed=speed,
                output_path=output_path,
                model_path=voice.piper.model,
                config_path=voice.piper.config,
                speaker=voice.piper.speaker,
            )
        raise EngineError(f"unsupported engine: {engine_name}")

    def synthesize_chunk(
        self,
        engine_name: str,
        voice: VoiceConfig,
        text: str,
        speed: float,
        output_path: Path,
    ) -> Path:
        if engine_name not in self.available_engines_for_voice(voice):
            raise EngineError(f"{engine_name}: voice not configured")
        request = self.build_request(engine_name, voice, text, speed, output_path)
        return self.engines[engine_name].synthesize_chunk(request)
