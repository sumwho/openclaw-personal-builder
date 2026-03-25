from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import tempfile
from unittest import mock
import unittest


MODULE_PATH = Path(__file__).resolve().parent.parent / "skills" / "local-tts" / "scripts" / "invoke_tts.py"
SPEC = spec_from_file_location("invoke_tts", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load invoke_tts module from {MODULE_PATH}")
invoke_tts = module_from_spec(SPEC)
SPEC.loader.exec_module(invoke_tts)


class LocalTTSInvokeTests(unittest.TestCase):
    def test_extract_payload_prefers_longest_quoted_span(self) -> None:
        text = 'Convert this paragraph to speech "short" and then "good afternoon， 今天下雨了"'
        self.assertEqual(
            invoke_tts.extract_payload_text(text),
            "good afternoon， 今天下雨了",
        )

    def test_mixed_text_defaults_to_zh_mix_en_voice(self) -> None:
        lang, voice = invoke_tts.infer_lang_and_voice("good afternoon，今天下雨了", None, None)
        self.assertEqual(lang, "zh")
        self.assertEqual(voice, "zh_mix_en")

    def test_pure_chinese_defaults_to_default_zh(self) -> None:
        lang, voice = invoke_tts.infer_lang_and_voice("今天下雨了", None, None)
        self.assertEqual(lang, "zh")
        self.assertEqual(voice, "default_zh")

    def test_default_engine_is_melo(self) -> None:
        self.assertEqual(invoke_tts.infer_engine(None), "melo")
        self.assertEqual(invoke_tts.infer_engine("piper"), "piper")

    def test_health_url_matches_gateway(self) -> None:
        self.assertEqual(
            invoke_tts.health_url_for_request("http://127.0.0.1:28641/v1/audio/speech"),
            "http://127.0.0.1:28641/health",
        )

    def test_infer_delivery_message_defaults_by_language(self) -> None:
        self.assertEqual(invoke_tts.infer_delivery_message("zh"), "已生成语音，请查收。")
        self.assertEqual(invoke_tts.infer_delivery_message("en"), "Audio generated. See attached file.")

    def test_ensure_gateway_reports_missing_start_script(self) -> None:
        with mock.patch.object(invoke_tts, "endpoint_available", return_value=False):
            with mock.patch.dict(invoke_tts.os.environ, {"OPENCLAW_TTS_BASE_DIR": "/missing/base"}, clear=False):
                ok, error = invoke_tts.ensure_gateway(invoke_tts.DEFAULT_URL)
        self.assertFalse(ok)
        self.assertIn("start script was not found", error)

    def test_stage_audio_for_delivery_uses_openclaw_state_media_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state_dir = root / ".openclaw-dev" / "state-live"
            workspace_dir = root / ".openclaw-dev" / "workspace"
            state_dir.mkdir(parents=True)
            workspace_dir.mkdir(parents=True)

            source_path = root / "sample.mp3"
            source_path.write_bytes(b"audio")

            with mock.patch.dict(invoke_tts.os.environ, {}, clear=True):
                with mock.patch.object(invoke_tts.Path, "cwd", return_value=workspace_dir):
                    staged = invoke_tts.stage_audio_for_delivery(str(source_path))

            self.assertIsNotNone(staged)
            staged_path = Path(staged)
            self.assertEqual(staged_path.read_bytes(), b"audio")
            self.assertTrue(
                str(staged_path.resolve()).startswith(str((state_dir / "media" / "local-tts").resolve()))
            )


if __name__ == "__main__":
    unittest.main()
