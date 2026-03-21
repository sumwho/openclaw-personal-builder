from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import numpy
import soundfile as sf

from .base import BaseTTSEngine, EngineError, SynthesisRequest

try:
    from piper import PiperVoice, SynthesisConfig
except ImportError:  # pragma: no cover - exercised in deployed env
    PiperVoice = None
    SynthesisConfig = None


LOGGER = logging.getLogger(__name__)


class PiperEngine(BaseTTSEngine):
    engine_name = "piper"

    def __init__(self, executable: str | None, sample_rate: int) -> None:
        self.executable = executable or "piper"
        self.sample_rate = sample_rate

    def synthesize_chunk(self, request: SynthesisRequest) -> Path:
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        if not request.model_path:
            raise EngineError("piper model path is not configured for the selected voice")

        if PiperVoice is not None and SynthesisConfig is not None:
            return self._synthesize_with_python_api(request)

        return self._synthesize_with_executable(request)

    def _synthesize_with_python_api(self, request: SynthesisRequest) -> Path:
        try:
            voice = PiperVoice.load(
                model_path=request.model_path,
                config_path=request.config_path,
                use_cuda=False,
            )
            syn_config = SynthesisConfig(
                speaker_id=int(request.speaker) if request.speaker is not None else None,
                length_scale=max(0.5, min(2.0, 1.0 / request.speed)),
                normalize_audio=True,
                volume=1.0,
            )
            chunks = list(voice.synthesize(request.text, syn_config=syn_config))
        except Exception as exc:  # pragma: no cover - depends on runtime model files
            raise EngineError(f"piper python api failed: {exc}") from exc

        if not chunks:
            raise EngineError("piper python api produced no audio chunks")

        audio = numpy.concatenate([chunk.audio_float_array for chunk in chunks])
        sample_rate = chunks[0].sample_rate or self.sample_rate
        sf.write(str(request.output_path), audio, samplerate=sample_rate)
        return request.output_path

    def _synthesize_with_executable(self, request: SynthesisRequest) -> Path:
        command = [
            self.executable,
            "--model",
            request.model_path,
            "--output_file",
            str(request.output_path),
            "--length_scale",
            str(max(0.5, min(2.0, 1.0 / request.speed))),
        ]
        if request.config_path:
            command.extend(["--config", request.config_path])
        if request.speaker:
            command.extend(["--speaker", request.speaker])

        LOGGER.info("Synthesizing with Piper model=%s output=%s", request.model_path, request.output_path)
        completed = subprocess.run(
            command,
            input=request.text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if completed.returncode != 0:
            raise EngineError(completed.stderr.strip() or completed.stdout.strip() or "piper synthesis failed")
        if not request.output_path.exists():
            raise EngineError(f"piper did not create output file: {request.output_path}")
        return request.output_path
