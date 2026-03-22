from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path

from .base import BaseTTSEngine, EngineError, SynthesisRequest


LOGGER = logging.getLogger(__name__)


class KokoroMLXEngine(BaseTTSEngine):
    engine_name = "kokoro"

    def __init__(self, python_bin: str | None, model_ref: str | None, sample_rate: int) -> None:
        self.python_bin = python_bin or sys.executable
        self.model_ref = model_ref or "mlx-community/Kokoro-82M-bf16"
        self.sample_rate = sample_rate

    def synthesize_chunk(self, request: SynthesisRequest) -> Path:
        request.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Assumption: mlx-audio exposes the documented CLI entrypoint via `python -m mlx_audio.tts.generate`.
        # This call surface is intentionally isolated here so a future package/API change only touches this adapter.
        command = [
            self.python_bin,
            "-m",
            "mlx_audio.tts.generate",
            "--model",
            self.model_ref,
            "--text",
            request.text,
            "--output_path",
            str(request.output_path),
            "--speed",
            str(request.speed),
            "--voice",
            request.voice,
        ]
        if request.lang_code:
            command.extend(["--lang_code", request.lang_code])

        LOGGER.info("Synthesizing with Kokoro MLX voice=%s output=%s", request.voice, request.output_path)
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise EngineError(completed.stderr.strip() or completed.stdout.strip() or "kokoro synthesis failed")
        resolved_output = self._resolve_output_path(request.output_path)
        if resolved_output is None:
            raise EngineError(f"kokoro did not create output file: {request.output_path}")
        if resolved_output != request.output_path:
            temp_output = request.output_path.parent / f"{request.output_path.stem}.kokoro.tmp.wav"
            shutil.move(str(resolved_output), str(temp_output))
            shutil.rmtree(request.output_path, ignore_errors=True)
            shutil.move(str(temp_output), str(request.output_path))
        return request.output_path

    @staticmethod
    def _resolve_output_path(output_path: Path) -> Path | None:
        if output_path.is_file():
            return output_path
        if output_path.is_dir():
            candidates = sorted(output_path.glob("audio_*.wav"))
            if candidates:
                return candidates[0]
        return None
