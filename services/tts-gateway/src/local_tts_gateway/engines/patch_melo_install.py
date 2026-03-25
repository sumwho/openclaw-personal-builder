from __future__ import annotations

import importlib.util
from pathlib import Path


ENGLISH_HEADER_PATCH = """import pickle
import os
import re

from . import symbols
from .english_utils.abbreviations import expand_abbreviations
from .english_utils.time_norm import expand_time_english
from .english_utils.number_norm import normalize_numbers


def distribute_phone(n_phone, n_word):
    phones_per_word = [0] * n_word
    for task in range(n_phone):
        min_tasks = min(phones_per_word)
        min_index = phones_per_word.index(min_tasks)
        phones_per_word[min_index] += 1
    return phones_per_word


_g2p = None


def _get_g2p():
    global _g2p
    if _g2p is None:
        from g2p_en import G2p

        _g2p = G2p()
    return _g2p


from transformers import AutoTokenizer

current_file_path = os.path.dirname(__file__)
CMU_DICT_PATH = os.path.join(current_file_path, "cmudict.rep")
CACHE_PATH = os.path.join(current_file_path, "cmudict_cache.pickle")
"""

ENGLISH_FALLBACK_HELPERS = """

def _direct_token_pronunciation(word):
    if word in {",", ".", "!", "?", "'", "-", "…"}:
        return [post_replace_ph(word)], [0]
    return None


def _spell_out_word(word):
    phones = []
    tones = []
    for char in word:
        if not char.isalpha():
            continue
        syllables = eng_dict.get(char.upper())
        if syllables is None:
            return None
        phns, tns = refine_syllables(syllables)
        phones.extend(phns)
        tones.extend(tns)
    if not phones:
        return None
    return phones, tones


def _fallback_word_pronunciation(word):
    direct = _direct_token_pronunciation(word)
    if direct is not None:
        return direct

    spelled = _spell_out_word(word)
    if spelled is not None:
        return spelled

    try:
        phone_list = list(filter(lambda p: p != " ", _get_g2p()(word)))
    except LookupError:
        phone_list = []

    if phone_list:
        phones = []
        tones = []
        for ph in phone_list:
            if ph in arpa:
                ph, tn = refine_ph(ph)
                phones.append(ph)
                tones.append(tn)
            else:
                phones.append(ph)
                tones.append(0)
        return phones, tones

    return ["UNK"], [0]
"""

ENGLISH_UNKNOWN_BLOCK = """        else:
            phone_list = list(filter(lambda p: p != " ", _get_g2p()(w)))
            for ph in phone_list:
                if ph in arpa:
                    ph, tn = refine_ph(ph)
                    phones.append(ph)
                    tones.append(tn)
                else:
                    phones.append(ph)
                    tones.append(0)
                phone_len += 1
"""

ENGLISH_UNKNOWN_BLOCK_ORIGINAL = """        else:
            phone_list = list(filter(lambda p: p != " ", _g2p(w)))
            for ph in phone_list:
                if ph in arpa:
                    ph, tn = refine_ph(ph)
                    phones.append(ph)
                    tones.append(tn)
                else:
                    phones.append(ph)
                    tones.append(0)
                phone_len += 1
"""

ENGLISH_UNKNOWN_BLOCK_PATCH = """        else:
            phns, tns = _fallback_word_pronunciation(w)
            phones += phns
            tones += tns
            phone_len += len(phns)
"""

CLEANER_IMPORT_BLOCK = """from . import chinese, japanese, english, chinese_mix, korean, french, spanish
from . import cleaned_text_to_sequence
import copy

language_module_map = {"ZH": chinese, "JP": japanese, "EN": english, 'ZH_MIX_EN': chinese_mix, 'KR': korean,
                    'FR': french, 'SP': spanish, 'ES': spanish}
"""

CLEANER_PATCH_BLOCK = """from importlib import import_module
from . import cleaned_text_to_sequence
import copy

_LANGUAGE_MODULE_NAMES = {
    "ZH": "chinese",
    "JP": "japanese",
    "EN": "english",
    "ZH_MIX_EN": "chinese_mix",
    "KR": "korean",
    "FR": "french",
    "SP": "spanish",
    "ES": "spanish",
}
_LANGUAGE_MODULE_CACHE = {}


def get_language_module(language):
    module = _LANGUAGE_MODULE_CACHE.get(language)
    if module is None:
        module_name = _LANGUAGE_MODULE_NAMES[language]
        module = import_module(f"{__package__}.{module_name}")
        _LANGUAGE_MODULE_CACHE[language] = module
    return module
"""


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_if_changed(path: Path, content: str) -> bool:
    original = _read(path)
    if original == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def patch_melo_install(site_packages_root: Path | None = None) -> list[Path]:
    if site_packages_root is None:
        spec = importlib.util.find_spec("melo")
        if spec is None or not spec.submodule_search_locations:
            raise RuntimeError("melo is not installed in the current interpreter")
        melo_root = Path(next(iter(spec.submodule_search_locations)))
    else:
        melo_root = site_packages_root / "melo"

    text_root = melo_root / "text"
    cleaner_path = text_root / "cleaner.py"
    english_path = text_root / "english.py"
    changed: list[Path] = []

    cleaner_content = _read(cleaner_path)
    if CLEANER_PATCH_BLOCK not in cleaner_content:
        if CLEANER_IMPORT_BLOCK not in cleaner_content:
            raise RuntimeError(f"unexpected Melo cleaner.py layout: {cleaner_path}")
        cleaner_content = cleaner_content.replace(CLEANER_IMPORT_BLOCK, CLEANER_PATCH_BLOCK, 1)
        cleaner_content = cleaner_content.replace("language_module = language_module_map[language]", "language_module = get_language_module(language)")
        if _write_if_changed(cleaner_path, cleaner_content):
            changed.append(cleaner_path)

    english_content = _read(english_path)
    english_marker = "arpa = {\n"
    english_marker_index = english_content.find(english_marker)
    if english_marker_index == -1:
        raise RuntimeError(f"unexpected Melo english.py marker layout: {english_path}")
    english_content = ENGLISH_HEADER_PATCH + english_content[english_marker_index:]
    english_content = english_content.replace("_g2p(w)", "_get_g2p()(w)")
    if ENGLISH_FALLBACK_HELPERS not in english_content:
        if "def g2p_old(text):" in english_content:
            english_content = english_content.replace("def g2p_old(text):", ENGLISH_FALLBACK_HELPERS + "\n\ndef g2p_old(text):", 1)
        elif "def g2p(text, pad_start_end=True, tokenized=None):" in english_content:
            english_content = english_content.replace(
                "def g2p(text, pad_start_end=True, tokenized=None):",
                ENGLISH_FALLBACK_HELPERS + "\n\ndef g2p(text, pad_start_end=True, tokenized=None):",
                1,
            )
        else:
            raise RuntimeError(f"unexpected Melo english.py function layout: {english_path}")
    english_content = english_content.replace(ENGLISH_UNKNOWN_BLOCK_ORIGINAL, ENGLISH_UNKNOWN_BLOCK_PATCH)
    english_content = english_content.replace(ENGLISH_UNKNOWN_BLOCK, ENGLISH_UNKNOWN_BLOCK_PATCH)
    if _write_if_changed(english_path, english_content):
        changed.append(english_path)

    return changed


def main() -> int:
    changed = patch_melo_install()
    for path in changed:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
