from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable


class AudioProcessingError(RuntimeError):
    pass


def _run_ffmpeg(ffmpeg_path: str, args: list[str]) -> None:
    command = [ffmpeg_path, "-hide_banner", "-loglevel", "error", *args]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise AudioProcessingError(completed.stderr.strip() or "ffmpeg command failed")


def concat_audio_files(ffmpeg_path: str, parts: Iterable[Path], output_path: Path, normalize_audio: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    concat_file = output_path.parent / f"{output_path.stem}.concat.txt"
    lines = [f"file '{part.as_posix()}'" for part in parts]
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    audio_filter = "loudnorm=I=-16:LRA=11:TP=-1.5" if normalize_audio else "anull"
    codec_args = ["-c:a", "libmp3lame", "-q:a", "2"] if output_path.suffix == ".mp3" else ["-c:a", "pcm_s16le"]
    _run_ffmpeg(
        ffmpeg_path,
        [
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-af",
            audio_filter,
            *codec_args,
            str(output_path),
        ],
    )
    concat_file.unlink(missing_ok=True)
