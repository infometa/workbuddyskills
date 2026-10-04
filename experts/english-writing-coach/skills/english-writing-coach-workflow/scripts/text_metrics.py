#!/usr/bin/env python3
"""Compute deterministic metrics for English writing and reading inputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

WORD_RE = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
LETTER_RE = re.compile(r"[A-Za-z]")
COMMON_ABBREVIATIONS = (
    "Mr", "Mrs", "Ms", "Dr", "Prof", "Sr", "Jr", "St", "Mt",
    "e.g", "i.e", "etc", "vs", "Fig", "No", "Inc", "Ltd", "Co",
)
DOT_SENTINEL = "\uE000"


def read_text_file(file_path: str) -> str:
    path = Path(file_path)
    if not path.is_file():
        raise ValueError(f"Input file not found: {path}")
    return path.read_text(encoding="utf-8")


def read_input(text: str | None, file_path: str | None) -> str:
    if (text is None) == (file_path is None):
        raise ValueError("Provide exactly one of --text or --file")
    return read_text_file(file_path) if file_path is not None else (text or "")


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def protect_nonterminal_periods(text: str) -> str:
    protected = text
    for abbreviation in COMMON_ABBREVIATIONS:
        pattern = re.compile(rf"\b{re.escape(abbreviation)}\.", re.IGNORECASE)
        protected = pattern.sub(lambda match: match.group(0)[:-1] + DOT_SENTINEL, protected)
    protected = re.sub(
        r"\b(?:[A-Z]\.){2,}",
        lambda match: match.group(0).replace(".", DOT_SENTINEL),
        protected,
    )
    protected = re.sub(
        r"\b([A-Z])\.(?=\s*[A-Z][a-z])",
        rf"\1{DOT_SENTINEL}",
        protected,
    )
    protected = re.sub(r"(?<=\d)\.(?=\d)", DOT_SENTINEL, protected)
    return protected


def count_sentences(text: str) -> int:
    if not text.strip():
        return 0
    protected = protect_nonterminal_periods(text)
    chunks = re.split(r"[.!?]+(?:[\"'”’)]*)\s+", protected)
    return len([chunk for chunk in chunks if chunk.strip()])


def count_paragraphs(text: str, mode: str) -> int:
    if not text.strip():
        return 0
    if mode == "auto":
        mode = "blank-line" if re.search(r"\n\s*\n", text) else "line"
    if mode == "line":
        return len([line for line in text.split("\n") if line.strip()])
    return len([part for part in re.split(r"\n\s*\n", text) if part.strip()])


def apply_exclusions(text: str, exclusions: list[str]) -> tuple[str, list[dict[str, object]]]:
    effective_text = text
    details: list[dict[str, object]] = []
    for raw_exclusion in exclusions:
        exclusion = normalize(raw_exclusion)
        if not exclusion:
            continue
        occurrence_count = effective_text.count(exclusion)
        excluded_word_count = len(WORD_RE.findall(exclusion)) * occurrence_count
        if occurrence_count:
            effective_text = effective_text.replace(exclusion, " ")
        details.append({
            "text": exclusion,
            "occurrence_count": occurrence_count,
            "excluded_word_count": excluded_word_count,
            "matched": occurrence_count > 0,
        })
    return effective_text, details


def analyze(text: str, exclusions: list[str] | None = None, paragraph_mode: str = "auto") -> dict[str, object]:
    normalized = normalize(text)
    exclusions = exclusions or []
    effective_text, exclusion_details = apply_exclusions(normalized, exclusions)
    total_words = WORD_RE.findall(normalized)
    effective_words = WORD_RE.findall(effective_text)
    sentence_count = count_sentences(normalized)
    paragraph_count = count_paragraphs(normalized, paragraph_mode)
    visible_chars = [char for char in normalized if not char.isspace()]
    letter_count = len(LETTER_RE.findall(normalized))
    latin_ratio = round(letter_count / len(visible_chars), 4) if visible_chars else 0.0
    average_sentence_words = round(len(total_words) / sentence_count, 2) if sentence_count else 0.0
    unmatched_exclusions = [item["text"] for item in exclusion_details if not item["matched"]]
    return {
        "total_word_count": len(total_words),
        "excluded_word_count": len(total_words) - len(effective_words),
        "effective_word_count": len(effective_words),
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "paragraph_mode_used": (
            "blank-line" if paragraph_mode == "auto" and re.search(r"\n\s*\n", normalized)
            else "line" if paragraph_mode == "auto"
            else paragraph_mode
        ),
        "visible_character_count": len(visible_chars),
        "latin_letter_ratio": latin_ratio,
        "average_words_per_sentence": average_sentence_words,
        "over_3000_words": len(total_words) > 3000,
        "recommended_granularity": "paragraph" if sentence_count > 20 else "sentence",
        "exclusions": exclusion_details,
        "warnings": [f"Exclusion text not found: {item}" for item in unmatched_exclusions],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute English text metrics as JSON")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="Text to analyze")
    group.add_argument("--file", help="UTF-8 text file to analyze")
    parser.add_argument("--exclude-text", action="append", default=[], help="Exact text to exclude from effective word count")
    parser.add_argument("--exclude-file", action="append", default=[], help="UTF-8 file containing exact text to exclude")
    parser.add_argument(
        "--paragraph-mode",
        choices=("auto", "blank-line", "line"),
        default="auto",
        help="Paragraph boundary rule; auto uses blank lines when present, otherwise non-empty lines",
    )
    parser.add_argument("--output", help="Optional new JSON output file")
    args = parser.parse_args()

    try:
        exclusions = list(args.exclude_text)
        exclusions.extend(read_text_file(path) for path in args.exclude_file)
        result = analyze(
            read_input(args.text, args.file),
            exclusions=exclusions,
            paragraph_mode=args.paragraph_mode,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with output.open("x", encoding="utf-8") as handle:
                handle.write(payload + "\n")
        except FileExistsError:
            parser.error(f"Output file already exists: {output}")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
