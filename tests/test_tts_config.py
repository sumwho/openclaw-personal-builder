from pathlib import Path
import tempfile
import unittest

from local_tts_gateway.config import load_config
from local_tts_gateway.service import build_runtime_env


class TTSConfigTests(unittest.TestCase):
    def test_load_config_accepts_melo_default_engine(self) -> None:
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
                        "melo:",
                        "  sample_rate: 44100",
                    ],
                ),
                encoding="utf-8",
            )
            config = load_config(config_path)
            self.assertEqual(config.default_engine, "melo")
            self.assertEqual(config.voices["default_zh"].melo.speaker, "ZH")

    def test_runtime_env_redirects_home_under_cache_dir(self) -> None:
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
                        "melo:",
                        "  sample_rate: 44100",
                        "  mecabrc: /opt/homebrew/etc/mecabrc",
                    ],
                ),
                encoding="utf-8",
            )
            config = load_config(config_path)
            runtime_env = build_runtime_env(config)
            self.assertTrue(runtime_env["HOME"].endswith("runtime/cache/home"))
            self.assertTrue(runtime_env["NLTK_DATA"].endswith("runtime/cache/nltk_data"))
            self.assertEqual(runtime_env["MECABRC"], "/opt/homebrew/etc/mecabrc")


if __name__ == "__main__":
    unittest.main()
