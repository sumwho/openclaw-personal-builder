from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path("/Volumes/ExtendStorage/openclaw/config/config.yaml")


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class VoiceEngineConfig:
    voice: str | None = None
    model: str | None = None
    config: str | None = None
    speaker: str | None = None
    lang_code: str | None = None


@dataclass(frozen=True)
class VoiceConfig:
    name: str
    lang: str
    kokoro: VoiceEngineConfig
    piper: VoiceEngineConfig


@dataclass(frozen=True)
class EngineConfig:
    name: str
    executable: str | None
    python_bin: str | None
    model_ref: str | None
    sample_rate: int


@dataclass(frozen=True)
class AppConfig:
    config_path: Path
    base_dir: Path
    models_dir: Path
    output_dir: Path
    temp_dir: Path
    cache_dir: Path
    log_dir: Path
    default_engine: str
    max_input_length: int
    chunk_soft_limit: int
    default_voice: str
    ffmpeg_path: str
    concurrency_limit: int
    gateway_host: str
    gateway_port: int
    normalize_audio: bool
    voices: dict[str, VoiceConfig]
    kokoro: EngineConfig
    piper: EngineConfig


def _resolve_path(base_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError("Top-level config must be a mapping.")
    return data


def _read_voice_config(name: str, raw: dict[str, Any]) -> VoiceConfig:
    return VoiceConfig(
        name=name,
        lang=str(raw["lang"]),
        kokoro=VoiceEngineConfig(**(raw.get("kokoro") or {})),
        piper=VoiceEngineConfig(**(raw.get("piper") or {})),
    )


def _read_engine_config(name: str, raw: dict[str, Any]) -> EngineConfig:
    return EngineConfig(
        name=name,
        executable=raw.get("executable"),
        python_bin=raw.get("python_bin"),
        model_ref=raw.get("model_ref"),
        sample_rate=int(raw.get("sample_rate", 24000)),
    )


def ensure_directories(config: AppConfig) -> None:
    required_dirs = (
        config.base_dir,
        config.models_dir,
        config.output_dir,
        config.temp_dir,
        config.cache_dir,
        config.log_dir,
    )
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)


def load_config(config_path: str | Path | None = None) -> AppConfig:
    path = Path(config_path or DEFAULT_CONFIG_PATH).expanduser().resolve()
    data = _read_yaml(path)

    base_dir = _resolve_path(path.parent.parent, str(data["base_dir"]))
    voices = {
        name: _read_voice_config(name, raw)
        for name, raw in (data.get("voice_map") or {}).items()
    }

    config = AppConfig(
        config_path=path,
        base_dir=base_dir,
        models_dir=_resolve_path(base_dir, str(data["models_dir"])),
        output_dir=_resolve_path(base_dir, str(data["output_dir"])),
        temp_dir=_resolve_path(base_dir, str(data["temp_dir"])),
        cache_dir=_resolve_path(base_dir, str(data["cache_dir"])),
        log_dir=_resolve_path(base_dir, str(data["log_dir"])),
        default_engine=str(data.get("default_engine", "kokoro")),
        max_input_length=int(data.get("max_input_length", 5000)),
        chunk_soft_limit=int(data.get("chunk_soft_limit", 280)),
        default_voice=str(data["default_voice"]),
        ffmpeg_path=str(data.get("ffmpeg_path", "ffmpeg")),
        concurrency_limit=max(1, int(data.get("concurrency_limit", 1))),
        gateway_host=str(data.get("gateway_host", "127.0.0.1")),
        gateway_port=int(data.get("gateway_port", 28641)),
        normalize_audio=bool(data.get("normalize_audio", False)),
        voices=voices,
        kokoro=_read_engine_config("kokoro", data.get("kokoro") or {}),
        piper=_read_engine_config("piper", data.get("piper") or {}),
    )

    if config.default_voice not in config.voices:
        raise ConfigError(f"default_voice '{config.default_voice}' is not defined in voice_map")
    if config.default_engine not in {"kokoro", "piper"}:
        raise ConfigError("default_engine must be 'kokoro' or 'piper'")

    ensure_directories(config)
    return config
