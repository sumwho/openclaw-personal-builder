from __future__ import annotations

import logging
import os
import shutil
import threading
import uuid
from pathlib import Path

from local_tts_gateway.audio import AudioProcessingError, concat_audio_files
from local_tts_gateway.config import AppConfig
from local_tts_gateway.engines.base import EngineError
from local_tts_gateway.engines.factory import EngineRegistry
from local_tts_gateway.preprocess import preprocess_text
from local_tts_gateway.security import SecurityError, ensure_within_base, sanitize_text


LOGGER = logging.getLogger(__name__)


class TTSService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.registry = EngineRegistry(config)
        self.semaphore = threading.Semaphore(config.concurrency_limit)

    def list_voices(self) -> list[dict[str, object]]:
        return [
            {
                "name": voice.name,
                "lang": voice.lang,
                "engines": self.registry.available_engines_for_voice(voice),
            }
            for voice in self.config.voices.values()
        ]

    def ffmpeg_available(self) -> bool:
        ffmpeg_path = self.config.ffmpeg_path
        if Path(ffmpeg_path).is_absolute():
            return Path(ffmpeg_path).exists()
        return shutil.which(ffmpeg_path) is not None

    def generate(self, *, text: str, voice_name: str | None, lang: str | None, fmt: str, speed: float, engine: str | None) -> dict[str, object]:
        with self.semaphore:
            return self._generate(text=text, voice_name=voice_name, lang=lang, fmt=fmt, speed=speed, engine=engine)

    def _generate(self, *, text: str, voice_name: str | None, lang: str | None, fmt: str, speed: float, engine: str | None) -> dict[str, object]:
        cleaned_text = sanitize_text(text, self.config.max_input_length)
        selected_voice_name = voice_name or self.config.default_voice
        if selected_voice_name not in self.config.voices:
            raise SecurityError(f"unknown voice: {selected_voice_name}")

        selected_voice = self.config.voices[selected_voice_name]
        if lang and lang != selected_voice.lang:
            raise SecurityError(f"voice '{selected_voice_name}' only supports lang='{selected_voice.lang}'")

        preferred_engine = engine or self.config.default_engine
        chunk_texts = preprocess_text(cleaned_text, selected_voice.lang, self.config.chunk_soft_limit)
        if not chunk_texts:
            raise SecurityError("text preprocessing produced no synthesizeable chunks")

        request_id = uuid.uuid4().hex
        temp_root = ensure_within_base(self.config.temp_dir / request_id, self.config.base_dir)
        temp_root.mkdir(parents=True, exist_ok=True)

        output_name = f"{request_id}.{fmt}"
        output_path = ensure_within_base(self.config.output_dir / output_name, self.config.base_dir)
        engine_order = [preferred_engine]
        if preferred_engine == "kokoro":
            engine_order.append("piper")

        chunk_paths: list[Path] = []
        engine_used: str | None = None
        failures: list[str] = []

        try:
            for engine_name in engine_order:
                chunk_paths.clear()
                self._cleanup_temp_files(temp_root)
                try:
                    for index, chunk_text in enumerate(chunk_texts):
                        chunk_path = temp_root / f"{engine_name}-chunk-{index:03d}.wav"
                        generated_path = self.registry.synthesize_chunk(
                            engine_name=engine_name,
                            voice=selected_voice,
                            text=chunk_text,
                            speed=speed,
                            output_path=chunk_path,
                        )
                        chunk_paths.append(generated_path)

                    concat_audio_files(
                        ffmpeg_path=self.config.ffmpeg_path,
                        parts=chunk_paths,
                        output_path=output_path,
                        normalize_audio=self.config.normalize_audio,
                    )
                    engine_used = engine_name
                    break
                except (EngineError, AudioProcessingError) as exc:
                    LOGGER.warning("TTS request failed on engine %s: %s", engine_name, exc)
                    failures.append(f"{engine_name}: {exc}")
                    if engine_name != engine_order[-1]:
                        continue
                    raise RuntimeError("all engines failed: " + "; ".join(failures)) from exc
        finally:
            self._cleanup_temp_dir(temp_root)

        if engine_used is None:
            raise RuntimeError("speech generation did not produce an engine selection")

        return {
            "audio_path": str(output_path),
            "engine_used": engine_used,
            "chunks": len(chunk_texts),
            "duration_hint": self._duration_hint(cleaned_text),
        }

    def _cleanup_temp_dir(self, temp_root: Path) -> None:
        if not temp_root.exists():
            return
        for path in sorted(temp_root.glob("**/*"), key=lambda item: len(item.parts), reverse=True):
            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                path.rmdir()
        temp_root.rmdir()

    def _cleanup_temp_files(self, temp_root: Path) -> None:
        for path in temp_root.glob("*"):
            if path.is_file():
                path.unlink(missing_ok=True)

    @staticmethod
    def _duration_hint(text: str) -> str:
        words = len(text.split())
        if words < 40:
            return "short"
        if words < 140:
            return "medium"
        return "long"


def build_runtime_env(config: AppConfig) -> dict[str, str]:
    return {
        "HF_HOME": str(config.cache_dir / "huggingface"),
        "XDG_CACHE_HOME": str(config.cache_dir / "xdg"),
        "PIP_CACHE_DIR": str(config.cache_dir / "pip"),
        "TMPDIR": str(config.temp_dir),
        "TEMP": str(config.temp_dir),
        "TMP": str(config.temp_dir),
    }


def apply_runtime_env(config: AppConfig) -> None:
    for key, value in build_runtime_env(config).items():
        os.environ.setdefault(key, value)
