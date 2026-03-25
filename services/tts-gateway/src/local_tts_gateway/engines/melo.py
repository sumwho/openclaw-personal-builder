from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from .base import BaseTTSEngine, EngineError, SynthesisRequest


LOGGER = logging.getLogger(__name__)


class MeloEngine(BaseTTSEngine):
    engine_name = "melo"

    def __init__(self, *, python_bin: str | None, sample_rate: int) -> None:
        self.python_bin = python_bin or sys.executable
        self.sample_rate = sample_rate

    def synthesize_chunk(self, request: SynthesisRequest) -> Path:
        if not request.lang_code:
            raise EngineError("melo lang_code is not configured for the selected voice")
        if not request.speaker:
            raise EngineError("melo speaker is not configured for the selected voice")

        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            self.python_bin,
            "-m",
            "local_tts_gateway.engines.melo_runner",
            "--text",
            request.text,
            "--lang-code",
            request.lang_code,
            "--speaker",
            request.speaker,
            "--output-path",
            str(request.output_path),
            "--speed",
            str(request.speed),
        ]
        if request.model_path:
            command.extend(["--model-path", request.model_path])
        if request.config_path:
            command.extend(["--config-path", request.config_path])

        LOGGER.info("Synthesizing with Melo lang=%s speaker=%s output=%s", request.lang_code, request.speaker, request.output_path)
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise EngineError(completed.stderr.strip() or completed.stdout.strip() or "melo synthesis failed")
        if not request.output_path.exists():
            raise EngineError(f"melo did not create output file: {request.output_path}")
        return request.output_path
