from pathlib import Path
import unittest

from local_tts_gateway.security import SecurityError, ensure_within_base, sanitize_text


class TTSSecurityTests(unittest.TestCase):
    def test_sanitize_text_rejects_oversized_input(self) -> None:
        with self.assertRaises(SecurityError):
            sanitize_text("x" * 12, max_length=10)

    def test_ensure_within_base_rejects_escape(self) -> None:
        base_dir = Path("/Volumes/ExtendStorage/openclaw")
        with self.assertRaises(SecurityError):
            ensure_within_base(base_dir / "../outside.txt", base_dir)


if __name__ == "__main__":
    unittest.main()
