import unittest

from local_tts_gateway.preprocess import preprocess_text


class TTSPreprocessTests(unittest.TestCase):
    def test_preprocess_splits_long_text(self) -> None:
        text = "第一句。第二句。Third sentence. Fourth sentence."
        chunks = preprocess_text(text, "zh", soft_limit=12)
        self.assertGreaterEqual(len(chunks), 2)

    def test_preprocess_normalizes_dates(self) -> None:
        chunks = preprocess_text("日期是 2026-03-19。", "zh", soft_limit=100)
        self.assertIn("2026年3月19日", chunks[0])


if __name__ == "__main__":
    unittest.main()
