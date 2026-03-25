# Native English Rewriter v2

## Description

Advanced text rewriting skill that transforms AI-generated or non-native English into natural, native-level communication. Features context-aware rewriting with three mode-specific styles: **enterprise**, **casual**, and **marketing**.

## When To Use

Use this skill when the user asks to:
- make English sound more native
- remove AI tone or corporate tone
- rewrite awkward English
- polish English for chat, email, product copy, or social posts
- rewrite Chinese-to-English output into more natural English

## Input Schema

```json
{
  "text": "string",
  "mode": "enterprise|casual|marketing",
  "audience": "client|internal|customer|business client",
  "region": "US|UK|global"
}
```

Defaults:
- `mode=enterprise`
- `audience=business client`
- `region=US`

## Command

```bash
python3 skills/native_english_rewriter_v2/scripts/invoke_natively_v2.py \
  --text "<payload>" \
  --mode enterprise \
  --audience "business client" \
  --region US
```

Use `--json` when another tool or wrapper needs structured output.

## Style Rules

The skill removes or rewrites common unnatural patterns such as:
- AI/corporate phrasing
- translation-style English
- awkward collocations
- stacked formal phrases
- long unreadable sentences

It prefers:
- simple vocabulary
- natural collocations
- shorter sentences
- native-sounding rhythm

## Practical Guidance

- Use `enterprise` for client emails and business writing.
- Use `casual` for chat, short updates, and relaxed messages.
- Use `marketing` for punchier copy.
- If the user asks for “more native”, “less AI”, “less corporate”, or “rewrite like a real American/British person”, this skill is a good default.
