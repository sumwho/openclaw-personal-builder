import unittest

from local_tts_gateway.preprocess import preprocess_text, split_mixed_script_text


class TTSPreprocessTests(unittest.TestCase):
    def test_preprocess_splits_long_text(self) -> None:
        text = "第一句。第二句。Third sentence. Fourth sentence."
        chunks = preprocess_text(text, "zh", soft_limit=12)
        self.assertGreaterEqual(len(chunks), 2)

    def test_preprocess_normalizes_dates(self) -> None:
        chunks = preprocess_text("日期是 2026-03-19。", "zh", soft_limit=100)
        self.assertIn("2026年3月19日", chunks[0])

    def test_split_mixed_script_text_preserves_both_languages(self) -> None:
        segments = split_mixed_script_text("good afternoon， 今天下雨了， 天气有些阴", "zh")
        self.assertEqual(
            [(segment.lang, segment.text) for segment in segments],
            [
                ("en", "good afternoon，"),
                ("zh", "今天下雨了， 天气有些阴"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
