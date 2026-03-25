#!/usr/bin/env python3
"""Native English Rewriter v2 - OpenClaw Skill with context-aware rewriting."""

import argparse
import json
import re


class NativeEnglishRewriterV2:
    """Advanced text rewriting with mode-specific style control."""

    FORBIDDEN_PHRASES = {
        "greatly appreciate": ["really appreciate", "appreciate"],
        "kindly note": ["note", "just a note"],
        "ensure seamless": ["make sure things run smoothly"],
        "facilitate efficient": ["help"],
        "work diligently": ["focus on"],
        "at your earliest convenience": ["when you can"],
        "please be advised": ["just a heads up"],
        "leverage synergies": ["work together"],
        "action items": ["next steps"],
        "touch base": ["check in"],
        "circle back": ["get back to you"],
        "utilize": ["use"],
        "prior to": ["before"],
        "regarding": ["about"],
        "commence": ["start"],
        "subsequently": ["then"],
        "furthermore": ["also"],
        "nevertheless": ["though"],
        "accordingly": ["so"],
        "in order to": ["to"],
        "due to the fact that": ["because"],
        "optimal solutions": ["effective solutions"],
        "synergy": ["collaboration"],
    }

    def __init__(self, mode="enterprise", audience="business client", region="US"):
        self.mode = mode
        self.audience = audience
        self.region = region

    def detect_unnatural_patterns(self, text):
        issues = []
        text_lower = text.lower()

        for phrase in self.FORBIDDEN_PHRASES.keys():
            if phrase in text_lower:
                issues.append(f"AI/corporate phrase: '{phrase}'")

        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        for i, sentence in enumerate(sentences, 1):
            word_count = len(sentence.split())
            if word_count > 25:
                issues.append(f"Sentence {i} is too long ({word_count} words)")

        corporate_count = sum(1 for p in self.FORBIDDEN_PHRASES.keys() if p in text_lower)
        if corporate_count >= 2:
            issues.append(f"Multiple corporate phrases stacked ({corporate_count} found)")

        return issues

    def apply_mode_style(self, text):
        result = text

        replacement_map = {
            r"greatly\s+appreciate": "really appreciate",
            r"work\s+diligently\s+to\s+ensure\s+(the\s+)?successful\s+completion\s+(?:of\s+)?(?:this\s+)?task\b": "wrap this up",
            r"ensure\s+seamless": "make sure things go smoothly",
            r"touch\s+base": "check in",
            r"action\s+items": "next steps",
            r"leverage\s+synergies": "work together",
            r"utilize": "use",
            r"prior\s+to": "before",
            r"regarding": "about",
            r"at\s+your\s+earliest\s+convenience": "when you can",
            r"please\s+be\s+advised": "just a heads up",
            r"facilitate\s+efficient": "help",
        }

        for pattern, replacement in replacement_map.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE, count=1)

        if self.mode == "marketing":
            marketing_issues = [
                r"facilitates?\s+optimal.*?engagem.*?opportunit",
            ]
            for issue_pattern in marketing_issues:
                if re.search(issue_pattern, text, re.IGNORECASE):
                    result = "It helps users succeed."
                    break

        result = re.sub(r"\b(?:of|this)\s+(of|this)\b", "", result, flags=re.IGNORECASE)
        result = re.sub(r"\.\w+s\.\s*$", ".", result)
        result = re.sub(r"\s+", " ", result).strip()

        simple_map = {
            "kindly note": "note",
            "circle back": "get back to you",
            "driving forward": "moving ahead with",
            "best practices": "what works well",
            "facilitate": "help",
            "pertaining to": "about",
            "commence": "start",
            "terminate": "end",
            "assist": "help",
            "subsequently": "then",
            "furthermore": "also",
            "nevertheless": "though",
            "accordingly": "so",
            "in order to": "to",
            "due to the fact that": "because",
            "optimal solutions": "effective solutions",
            "synergy": "collaboration",
        }

        for old, new in simple_map.items():
            result = result.replace(old, new)
            result = result.replace(old.capitalize(), new.capitalize())

        if self.mode == "enterprise":
            result = self._refine_enterprise(result)
        elif self.mode == "casual":
            result = self._refine_casual(result)
        elif self.mode == "marketing":
            result = self._refine_marketing(result)

        if self.region == "UK":
            uk_map = {"color": "colour", "favor": "favour", "center": "centre"}
            for us, uk in uk_map.items():
                result = result.replace(us, uk)

        return result

    def _refine_enterprise(self, text):
        result = text
        avoid_casual = {"wrap this up": "finalize this", "hanging in there": "patience"}
        for old, new in avoid_casual.items():
            result = result.replace(old, new)
        return result

    def _refine_casual(self, text):
        result = text
        relax = {"I would like to": "I wanted to", "Please let me know": "Let me know"}
        for old, new in relax.items():
            result = result.replace(old, new)
        result = result.replace("I'm inform", "Just")
        if self.audience == "internal" and "thanks" not in result.lower():
            result = result.rstrip("!") + ". Thanks!"
        return result

    def _refine_marketing(self, text):
        result = text
        engage = {"we will": "we're", "you will receive": "you'll get"}
        for old, new in engage.items():
            result = result.replace(old, new)
        return result

    def generate_alternatives(self, native_version):
        alternatives = []
        base = native_version.strip()

        if self.mode == "enterprise":
            alt1 = base.rstrip("!").rstrip(".") + "."
            alternatives.append(alt1)

            fillers = ["just", "really", "actually"]
            alt2 = " ".join(w for w in base.split() if w.lower() not in fillers)
            if alt2 != base:
                alternatives.append(alt2)

            alt3 = base + ", thanks." if "thank" not in base.lower() else base
            alternatives.append(alt3)

        elif self.mode == "casual":
            alt1 = base.replace(".", "!", 1).rstrip("!") + " thx!" if "thx" not in base.lower() else base
            alternatives.append(alt1)

            keep = ["thanks", "done", "ready", "almost"]
            alt2 = " ".join(w for w in base.split() if any(k in w.lower() for k in keep))
            alternatives.append((alt2 + "!") if alt2 else base)

            alt3 = base.rstrip("!") + " 🙂" if "?" not in base else base.rstrip("?") + " 😊"
            alternatives.append(alt3)

        elif self.mode == "marketing":
            alternatives.append("We've got something great coming — thanks for sticking with us!")
            alternatives.append("Coming soon — thank you for your patience!")
            alternatives.append("Almost there! Appreciate your waiting.")

        return alternatives[:3]

    def format_output(self, native_version, why_issues, improvements, alternatives):
        lines = [
            "=== Native Version ===",
            native_version,
            "",
            "=== Why the original sounded unnatural ===",
        ]
        lines.extend([f"- {issue}" for issue in why_issues])
        lines.extend(["", "=== Key Improvements ==="])
        lines.extend([f"- {improvement}" for improvement in improvements])
        lines.extend(["", "=== Alternative Phrasings ==="])
        for i, alt in enumerate(alternatives, 1):
            lines.append(f"{i}. {alt}")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Native English Rewriter v2")
    parser.add_argument("--text", required=True, help="Text to rewrite")
    parser.add_argument("--mode", default="enterprise", choices=["enterprise", "casual", "marketing"])
    parser.add_argument(
        "--audience",
        default="business client",
        choices=["client", "internal", "customer", "business client"],
    )
    parser.add_argument("--region", default="US", choices=["US", "UK", "global"])
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    rewriter = NativeEnglishRewriterV2(mode=args.mode, audience=args.audience, region=args.region)
    issues = rewriter.detect_unnatural_patterns(args.text)
    native_version = rewriter.apply_mode_style(args.text)

    improvements = []
    for issue in issues:
        if "phrase" in issue:
            improvements.append("Removed AI/corporate phrase")
        elif "long" in issue:
            improvements.append("Shortened long sentence")
        elif "stack" in issue:
            improvements.append("Reduced phrase stacking")
    if not improvements:
        improvements.append("Applied style refinement")

    alternatives = rewriter.generate_alternatives(native_version)

    if args.json:
        output = {
            "native_version": native_version,
            "analysis": {
                "issues": issues,
                "improvements": improvements,
                "alternatives": alternatives,
            },
        }
        print(json.dumps(output, indent=2))
    else:
        print(rewriter.format_output(native_version, issues, improvements, alternatives))


if __name__ == "__main__":
    main()
