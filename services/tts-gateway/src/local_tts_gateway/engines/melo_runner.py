from __future__ import annotations

import argparse
from pathlib import Path

from .base import EngineError
from .patch_melo_install import patch_melo_install

patch_melo_install()

try:
    from melo.api import TTS as MeloTTS
except ImportError as exc:  # pragma: no cover - exercised in deployed env
    raise SystemExit(f"melo is not installed in the Melo runtime environment: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthesize one chunk with MeloTTS.")
    parser.add_argument("--text", required=True)
    parser.add_argument("--lang-code", required=True)
    parser.add_argument("--speaker", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--speed", required=True, type=float)
    parser.add_argument("--model-path")
    parser.add_argument("--config-path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    kwargs: dict[str, object] = {
        "language": args.lang_code,
        "device": "auto",
        "use_hf": not (args.model_path or args.config_path),
    }
    if args.model_path:
        kwargs["ckpt_path"] = args.model_path
    if args.config_path:
        kwargs["config_path"] = args.config_path

    try:
        model = MeloTTS(**kwargs)
        speaker_ids = getattr(model.hps.data, "spk2id", {})
        if args.speaker not in speaker_ids:
            raise EngineError(f"melo speaker '{args.speaker}' is not available for {args.lang_code}")
        speaker_id = int(speaker_ids[args.speaker])
        model.tts_to_file(
            args.text,
            speaker_id,
            str(output_path),
            speed=args.speed,
            quiet=True,
        )
    except Exception as exc:
        raise SystemExit(str(exc)) from exc

    if not output_path.exists():
        raise SystemExit(f"melo did not create output file: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
