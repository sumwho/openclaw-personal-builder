from __future__ import annotations

import asyncio
import logging
import os

from fastapi import FastAPI, HTTPException

from local_tts_gateway.config import load_config
from local_tts_gateway.logging_utils import configure_logging
from local_tts_gateway.models import HealthResponse, SpeechRequest, SpeechResponse, VoiceInfo
from local_tts_gateway.security import SecurityError
from local_tts_gateway.service import TTSService, apply_runtime_env


CONFIG_PATH = os.environ.get("OPENCLAW_TTS_CONFIG")
CONFIG = load_config(CONFIG_PATH)
apply_runtime_env(CONFIG)
configure_logging(CONFIG.log_dir)
LOGGER = logging.getLogger(__name__)
SERVICE = TTSService(CONFIG)

app = FastAPI(title="OpenClaw Local TTS Gateway", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        default_engine=CONFIG.default_engine,
        ffmpeg_available=SERVICE.ffmpeg_available(),
    )


@app.get("/voices", response_model=list[VoiceInfo])
async def voices() -> list[VoiceInfo]:
    return [VoiceInfo(**item) for item in SERVICE.list_voices()]


@app.post("/v1/audio/speech", response_model=SpeechResponse)
async def audio_speech(request: SpeechRequest) -> SpeechResponse:
    try:
        result = await asyncio.to_thread(
            SERVICE.generate,
            text=request.text,
            voice_name=request.voice,
            lang=request.lang,
            fmt=request.format,
            speed=request.speed,
            engine=request.engine,
        )
        return SpeechResponse(**result)
    except SecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        LOGGER.exception("speech generation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
