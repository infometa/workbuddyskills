#!/usr/bin/env python3
"""
segment_sentences.py — english-intensive-reader
Split article text into sentences and assign sentence IDs.

Usage:
    python segment_sentences.py --text "article text here"
    python segment_sentences.py --file article.txt [--json]
"""

import re
import sys
import json
import argparse
from typing import List, Dict


# ---------------------------------------------------------------------------
# Sentence segmentation
# ---------------------------------------------------------------------------

# Abbreviations that should NOT trigger sentence splits
ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "vs", "etc", "e.g", "i.e",
    "fig", "vol", "no", "pp", "ed", "eds", "rev", "est", "dept", "approx",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "u.s", "u.k", "u.n", "e.u", "u.s.a",
}


def _is_abbreviation(text: str, pos: int) -> bool:
    """Check if the period at pos is part of an abbreviation."""
    # Find the word before the period
    start = pos - 1
    while start >= 0 and text[start].isalpha():
        start -= 1
    word = text[start + 1:pos].lower()
    return word in ABBREVIATIONS or len(word) <= 2


def segment_sentences_rule_based(text: str) -> List[str]:
    """
    Rule-based sentence segmentation for English text.
    Handles common abbreviations and edge cases.
    """
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    sentences = []
    current = []
    i = 0

    while i < len(text):
        char = text[i]
        current.append(char)

        # Check for sentence-ending punctuation
        if char in ".!?":
            # Skip if abbreviation
            if char == "." and _is_abbreviation(text, i):
                i += 1
                continue

            # Skip if followed by lowercase (likely mid-sentence)
            next_non_space = i + 1
            while next_non_space < len(text) and text[next_non_space] == " ":
                next_non_space += 1

            if next_non_space < len(text):
                next_char = text[next_non_space]
                # If next char is uppercase or end of text → sentence boundary
                if next_char.isupper() or next_char in '"\'':
                    sentence = "".join(current).strip()
                    if sentence:
                        sentences.append(sentence)
                    current = []
            else:
                # End of text
                sentence = "".join(current).strip()
                if sentence:
                    sentences.append(sentence)
                current = []

        i += 1

    # Remaining text
    remaining = "".join(current).strip()
    if remaining:
        sentences.append(remaining)

    return [s for s in sentences if len(s.split()) >= 3]  # Filter very short fragments


def segment_sentences_spacy(text: str) -> List[str]:
    """
    spaCy-based sentence segmentation (preferred if available).
    """
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Model not installed, fall back to rule-based
            return segment_sentences_rule_based(text)

        doc = nlp(text)
        return [sent.text.strip() for sent in doc.sents if len(sent.text.split()) >= 3]
    except ImportError:
        return segment_sentences_rule_based(text)


def segment_sentences(text: str, use_spacy: bool = True) -> List[str]:
    """
    Main segmentation function. Tries spaCy first, falls back to rule-based.
    """
    if use_spacy:
        sentences = segment_sentences_spacy(text)
    else:
        sentences = segment_sentences_rule_based(text)

    # Post-process: merge very short sentences (< 5 words) with previous
    merged = []
    for sent in sentences:
        if merged and len(sent.split()) < 5:
            merged[-1] = merged[-1] + " " + sent
        else:
            merged.append(sent)

    return merged


# ---------------------------------------------------------------------------
# Sentence unit assembly
# ---------------------------------------------------------------------------

def build_sentence_units(sentences: List[str]) -> List[Dict]:
    """
    Build sentence_unit list from segmented sentences.
    Assigns IDs and detects complex sentences.
    """
    units = []
    for i, sent in enumerate(sentences):
        sid = f"s{i + 1:02d}"
        word_count = len(sent.split())

        # Detect complex sentence heuristics
        # Complex if: > 25 words OR contains subordinating conjunctions + comma
        complex_indicators = [
            "although", "though", "even though", "even if",
            "because", "since", "as", "while", "whereas",
            "which", "who", "whom", "whose", "that",
            "if", "unless", "provided", "whether",
            "not only", "not just", "neither", "either",
        ]
        has_complex_indicator = any(
            indicator in sent.lower() for indicator in complex_indicators
        )
        is_complex = word_count > 25 or (has_complex_indicator and "," in sent)

        units.append({
            "id": sid,
            "raw": sent,
            "word_count": word_count,
            "is_complex": is_complex,
            "highlights": {
                "new_words": [],          # To be filled by AI analysis
                "complex_clause_spans": [],  # To be filled by AI analysis
            },
            "sentence_analysis": None,    # To be filled by AI analysis
            "vocab_notes": [],            # To be filled by AI analysis
        })

    return units


def count_words(text: str) -> int:
    """Count English words."""
    return len(re.findall(r"\b[a-zA-Z]+\b", text))


def check_word_limit(text: str, limit: int = 3000) -> Dict:
    """Check if text exceeds word limit."""
    wc = count_words(text)
    return {
        "word_count": wc,
        "exceeded": wc > limit,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Segment English article into sentences for english-intensive-reader"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="Article text (inline)")
    group.add_argument("--file", help="Path to text file")
    parser.add_argument("--no-spacy", action="store_true", help="Disable spaCy, use rule-based only")
    parser.add_argument("--word-limit", type=int, default=3000)
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Read text
    if args.text:
        text = args.text
    else:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()

    # Check word limit
    limit_check = check_word_limit(text, args.word_limit)
    if limit_check["exceeded"]:
        msg = (
            f"⚠️ 文章共 {limit_check['word_count']} 词，超过单次处理上限（{args.word_limit} 词）。\n"
            "请分段精读，每次处理约 3000 词。"
        )
        print(msg, file=sys.stderr)

    # Segment
    sentences = segment_sentences(text, use_spacy=not args.no_spacy)
    units = build_sentence_units(sentences)

    result = {
        "word_count": limit_check["word_count"],
        "sentence_count": len(units),
        "complex_count": sum(1 for u in units if u["is_complex"]),
        "word_limit_exceeded": limit_check["exceeded"],
        "sentence_units": units,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for unit in units:
            flag = "🔴" if unit["is_complex"] else "⚪"
            print(f"[{unit['id']}] {flag} ({unit['word_count']}w) {unit['raw']}")
        print(f"\n共 {len(units)} 句，其中长难句 {result['complex_count']} 句")


if __name__ == "__main__":
    main()
