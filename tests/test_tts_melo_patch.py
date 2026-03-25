from pathlib import Path
import tempfile
import unittest

from local_tts_gateway.engines.patch_melo_install import patch_melo_install


ORIGINAL_CLEANER = """from . import chinese, japanese, english, chinese_mix, korean, french, spanish
from . import cleaned_text_to_sequence
import copy

language_module_map = {"ZH": chinese, "JP": japanese, "EN": english, 'ZH_MIX_EN': chinese_mix, 'KR': korean,
                    'FR': french, 'SP': spanish, 'ES': spanish}


def clean_text(text, language):
    language_module = language_module_map[language]
    norm_text = language_module.text_normalize(text)
    phones, tones, word2ph = language_module.g2p(norm_text)
    return norm_text, phones, tones, word2ph
"""

ORIGINAL_ENGLISH = """import pickle
import os
import re
from g2p_en import G2p

from . import symbols

from .english_utils.abbreviations import expand_abbreviations
from .english_utils.time_norm import expand_time_english
from .english_utils.number_norm import normalize_numbers
from .japanese import distribute_phone

from transformers import AutoTokenizer

current_file_path = os.path.dirname(__file__)
CMU_DICT_PATH = os.path.join(current_file_path, "cmudict.rep")
CACHE_PATH = os.path.join(current_file_path, "cmudict_cache.pickle")
_g2p = G2p()
arpa = {
}


def g2p(text, pad_start_end=True, tokenized=None):
    phone_list = list(filter(lambda p: p != " ", _g2p(w)))
    phone_list = list(filter(lambda p: p != " ", _g2p(w)))
    return [], [], []
"""


class MeloPatchTests(unittest.TestCase):
    def test_patch_melo_install_rewrites_cleaner_and_english(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            site_packages = Path(tmp_dir)
            text_dir = site_packages / "melo" / "text"
            text_dir.mkdir(parents=True, exist_ok=True)
            (text_dir / "cleaner.py").write_text(ORIGINAL_CLEANER, encoding="utf-8")
            (text_dir / "english.py").write_text(ORIGINAL_ENGLISH, encoding="utf-8")

            changed = patch_melo_install(site_packages)

            self.assertEqual(
                sorted(path.name for path in changed),
                ["cleaner.py", "english.py"],
            )
            cleaner = (text_dir / "cleaner.py").read_text(encoding="utf-8")
            english = (text_dir / "english.py").read_text(encoding="utf-8")
            self.assertIn("module = import_module", cleaner)
            self.assertIn("get_language_module(language)", cleaner)
            self.assertIn("def _get_g2p()", english)
            self.assertIn("def _fallback_word_pronunciation(word)", english)
            self.assertIn("_get_g2p()(w)", english)
            self.assertNotIn("from .japanese import distribute_phone", english)
            self.assertNotIn("\n_g2p = G2p()\n", english)


if __name__ == "__main__":
    unittest.main()
