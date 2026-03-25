#!/bin/bash
set -euo pipefail

OPENCLAW_NPM_ROOT="${OPENCLAW_NPM_ROOT:-/Users/gavin/.nvm/versions/node/v22.22.1/lib/node_modules/openclaw}"

if [ ! -d "${OPENCLAW_NPM_ROOT}" ]; then
  echo "OpenClaw install root not found: ${OPENCLAW_NPM_ROOT}" >&2
  exit 1
fi

python3 - "${OPENCLAW_NPM_ROOT}" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(sys.argv[1])
TARGETS = [
    ROOT / "dist" / "model-selection-CU2b7bN6.js",
    ROOT / "dist" / "auth-profiles-DDVivXkv.js",
]


REPLACEMENTS = [
    (
        'typeof record.new_string === "string" ? record.new_string : void 0;',
        'typeof record.new_string === "string" ? record.new_string : typeof record.new_text === "string" ? record.new_text : void 0;',
    ),
    (
        'typeof record.old_string === "string" ? record.old_string : void 0;',
        'typeof record.old_string === "string" ? record.old_string : record && typeof record.old_text === "string" ? record.old_text : void 0;',
    ),
    (
        'keys: ["oldText", "old_string"],',
        'keys: ["oldText", "old_string", "old_text"],',
    ),
    (
        'label: "oldText (oldText or old_string)"',
        'label: "oldText (oldText, old_string, or old_text)"',
    ),
    (
        'keys: ["newText", "new_string"],',
        'keys: ["newText", "new_string", "new_text"],',
    ),
    (
        'label: "newText (newText or new_string)",',
        'label: "newText (newText, new_string, or new_text)",',
    ),
    (
        'if ("old_string" in normalized && !("oldText" in normalized)) {\n\t\tnormalized.oldText = normalized.old_string;\n\t\tdelete normalized.old_string;\n\t}',
        'if ("old_string" in normalized && !("oldText" in normalized)) {\n\t\tnormalized.oldText = normalized.old_string;\n\t\tdelete normalized.old_string;\n\t}\n\tif ("old_text" in normalized && !("oldText" in normalized)) {\n\t\tnormalized.oldText = normalized.old_text;\n\t\tdelete normalized.old_text;\n\t}',
    ),
    (
        'if ("new_string" in normalized && !("newText" in normalized)) {\n\t\tnormalized.newText = normalized.new_string;\n\t\tdelete normalized.new_string;\n\t}',
        'if ("new_string" in normalized && !("newText" in normalized)) {\n\t\tnormalized.newText = normalized.new_string;\n\t\tdelete normalized.new_string;\n\t}\n\tif ("new_text" in normalized && !("newText" in normalized)) {\n\t\tnormalized.newText = normalized.new_text;\n\t\tdelete normalized.new_text;\n\t}',
    ),
    (
        '{\n\t\t\toriginal: "oldText",\n\t\t\talias: "old_string"\n\t\t},\n\t\t{\n\t\t\toriginal: "newText",\n\t\t\talias: "new_string"\n\t\t}',
        '{\n\t\t\toriginal: "oldText",\n\t\t\talias: "old_string"\n\t\t},\n\t\t{\n\t\t\toriginal: "oldText",\n\t\t\talias: "old_text"\n\t\t},\n\t\t{\n\t\t\toriginal: "newText",\n\t\t\talias: "new_string"\n\t\t},\n\t\t{\n\t\t\toriginal: "newText",\n\t\t\talias: "new_text"\n\t\t}',
    ),
]


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in REPLACEMENTS:
        if new in text:
            continue
        if old not in text:
            continue
        text = text.replace(old, new)
    if text == original:
        return False
    path.write_text(text, encoding="utf-8")
    return True


changed = []
for target in TARGETS:
    if not target.exists():
        print(f"missing: {target}", file=sys.stderr)
        sys.exit(1)
    if patch_file(target):
        changed.append(str(target))

if changed:
    print("patched:")
    for item in changed:
        print(item)
else:
    print("already patched")
PY
