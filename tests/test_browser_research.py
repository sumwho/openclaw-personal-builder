import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "browser-research-sandbox"
    / "scripts"
    / "browser_research.py"
)
SPEC = importlib.util.spec_from_file_location("browser_research", MODULE_PATH)
browser_research = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(browser_research)


class BrowserResearchTests(unittest.TestCase):
    def test_blocks_local_targets(self):
        with self.assertRaises(ValueError):
            browser_research.validate_public_url("http://127.0.0.1:8000")
        with self.assertRaises(ValueError):
            browser_research.validate_public_url("http://localhost/admin")
        with self.assertRaises(ValueError):
            browser_research.validate_public_url("file:///etc/passwd")

    def test_allows_public_https_url(self):
        self.assertEqual(
            browser_research.validate_public_url("https://example.com/docs?q=1"),
            "https://example.com/docs?q=1",
        )

    def test_extract_text(self):
        title, text = browser_research.extract_text(
            "<html><head><title>Hello</title><style>.x{}</style></head>"
            "<body><h1>Headline</h1><p>Body text</p><script>alert(1)</script></body></html>"
        )
        self.assertEqual(title, "Hello")
        self.assertIn("Headline", text)
        self.assertIn("Body text", text)
        self.assertNotIn("alert(1)", text)
