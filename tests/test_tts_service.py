from pathlib import Path
import tempfile
import unittest

from local_tts_gateway.config import load_config
from local_tts_gateway.service import TTSService


class TTSServiceTests(unittest.TestCase):
    def test_zh_mix_en_uses_single_pass_for_melo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            config_path = base_dir / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        f"base_dir: {base_dir}",
                        "models_dir: models",
                        "output_dir: runtime/audio",
                        "temp_dir: runtime/temp",
                        "cache_dir: runtime/cache",
                        "log_dir: runtime/logs",
                        "default_engine: melo",
                        "default_voice: zh_mix_en",
                        "voice_map:",
                        "  zh_mix_en:",
                        "    lang: zh",
                        "    melo:",
                        "      speaker: ZH",
                        "      lang_code: ZH",
                        "  default_en:",
                        "    lang: en",
                        "    melo:",
                        "      speaker: EN-Default",
                        "      lang_code: EN",
                        "melo:",
                        "  sample_rate: 44100",
                    ],
                ),
                encoding="utf-8",
            )
            config = load_config(config_path)
            service = TTSService(config)
            voice = config.voices["zh_mix_en"]

            plan = service._build_synthesis_plan("今天我们讨论一下 AI system architecture", voice, "melo")

            self.assertEqual(len(plan), 1)
            self.assertEqual(plan[0][0].name, "zh_mix_en")
            self.assertIn("AI system architecture", plan[0][1])

    def test_default_zh_still_splits_mixed_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            config_path = base_dir / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        f"base_dir: {base_dir}",
                        "models_dir: models",
                        "output_dir: runtime/audio",
                        "temp_dir: runtime/temp",
                        "cache_dir: runtime/cache",
                        "log_dir: runtime/logs",
                        "default_engine: melo",
                        "default_voice: default_zh",
                        "voice_map:",
                        "  default_zh:",
                        "    lang: zh",
                        "    melo:",
                        "      speaker: ZH",
                        "      lang_code: ZH",
                        "  default_en:",
                        "    lang: en",
                        "    melo:",
                        "      speaker: EN-Default",
                        "      lang_code: EN",
                        "melo:",
                        "  sample_rate: 44100",
                    ],
                ),
                encoding="utf-8",
            )
            config = load_config(config_path)
            service = TTSService(config)
            voice = config.voices["default_zh"]

            plan = service._build_synthesis_plan("今天我们讨论一下 AI system architecture", voice, "melo")

            self.assertGreaterEqual(len(plan), 2)
            self.assertEqual(plan[0][0].name, "default_zh")


if __name__ == "__main__":
    unittest.main()
