#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from statistics import mean

SENTENCE_SPLIT = re.compile(r"[。！？!?]+")
WORD_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9_]+")
SECOND_PERSON_RE = re.compile(r"\b你\b|\b你们\b|\byou\b", re.IGNORECASE)
FIRST_PERSON_PLURAL_RE = re.compile(r"\b我们\b|\bwe\b", re.IGNORECASE)
QUESTION_RE = re.compile(r"[？?]")
EM_DASH_RE = re.compile(r"[—–]")

BANNED_PHRASES = [
    "in today's",
    "it's important to note that",
    "it's worth noting",
    "delve",
    "dive into",
    "unpack",
    "harness",
    "leverage",
    "utilize",
    "landscape",
    "realm",
    "robust",
    "game-changer",
    "cutting-edge",
    "straightforward",
    "i'd be happy to help",
    "in order to",
    "furthermore",
    "additionally",
    "moreover",
    "moving forward",
    "at the end of the day",
    "to put this in perspective",
    "what makes this particularly interesting is",
    "the implications here are",
    "in other words",
    "it goes without saying",
    "let that sink in",
    "read that again",
    "full stop",
    "this changes everything",
    "are you paying attention",
    "you're not ready for this",
    "supercharge",
    "unlock",
    "future-proof",
    "10x your productivity",
    "the ai revolution",
    "in the age of ai",
    "here's the part nobody's talking about",
    "what nobody tells you",
]

FATAL_PATTERNS = [
    re.compile(r"\bthis isn['’]t\b.*\bthis is\b", re.IGNORECASE),
    re.compile(r"\bnot\b[^.?!\n]{1,80},[^.?!\n]{1,80}", re.IGNORECASE),
    re.compile(r"\bforget\b.*\bthis is\b", re.IGNORECASE),
    re.compile(r"\bless\b[^.?!\n]{1,80},\s*more\b", re.IGNORECASE),
]


def read_text_files(input_dir: Path) -> list[str]:
    files = sorted(
        [p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".txt", ".md"}]
    )
    return [p.read_text(encoding="utf-8", errors="ignore") for p in files]


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]


def tokenize(text: str) -> list[str]:
    return WORD_RE.findall(text)


def top_terms(texts: list[str], limit: int = 30) -> list[dict]:
    stop = {
        "的", "了", "是", "我", "你", "我们", "在", "和", "也", "就", "都", "与", "把", "被",
        "to", "the", "a", "an", "is", "are", "and", "or", "of", "in", "for", "on", "with",
    }
    freq = {}
    for t in texts:
        for w in tokenize(t):
            lw = w.lower()
            if lw in stop or len(lw) <= 1:
                continue
            freq[lw] = freq.get(lw, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [{"term": k, "count": v} for k, v in ranked]


def sentence_counts_in_paragraphs(text: str) -> list[int]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    counts = []
    for p in parts:
        c = len(split_sentences(p))
        counts.append(max(c, 1))
    return counts


def banned_phrase_audit(text: str) -> dict:
    lowered = text.lower()
    hits = []
    for phrase in BANNED_PHRASES:
        cnt = lowered.count(phrase.lower())
        if cnt:
            hits.append({"phrase": phrase, "count": cnt})
    fatal_hits = 0
    for pat in FATAL_PATTERNS:
        fatal_hits += len(pat.findall(text))
    return {
        "total_hits": sum(h["count"] for h in hits),
        "fatal_pattern_hits": fatal_hits,
        "hits": sorted(hits, key=lambda x: x["count"], reverse=True),
    }


def build_profile(texts: list[str]) -> dict:
    joined = "\n".join(texts)
    sentences = split_sentences(joined)
    sent_lengths = [len(tokenize(s)) for s in sentences if tokenize(s)]
    paragraph_lengths = [len(tokenize(p)) for p in re.split(r"\n\s*\n", joined) if p.strip()]
    paragraph_sentence_counts = sentence_counts_in_paragraphs(joined)

    question_count = len(QUESTION_RE.findall(joined))
    second_person_count = len(SECOND_PERSON_RE.findall(joined))
    first_plural_count = len(FIRST_PERSON_PLURAL_RE.findall(joined))
    em_dash_count = len(EM_DASH_RE.findall(joined))
    avg_para_sentences = round(mean(paragraph_sentence_counts), 2) if paragraph_sentence_counts else 0
    para_over_3 = len([c for c in paragraph_sentence_counts if c > 3])
    ban_audit = banned_phrase_audit(joined)

    profile = {
        "corpus": {
            "documents": len(texts),
            "characters": len(joined),
            "sentences": len(sentences),
            "paragraphs": len(paragraph_lengths),
        },
        "rhythm": {
            "avg_sentence_tokens": round(mean(sent_lengths), 2) if sent_lengths else 0,
            "avg_paragraph_tokens": round(mean(paragraph_lengths), 2) if paragraph_lengths else 0,
            "question_density_per_100_sentences": round((question_count / max(len(sentences), 1)) * 100, 2),
        },
        "voice": {
            "second_person_mentions": second_person_count,
            "first_person_plural_mentions": first_plural_count,
        },
        "formatting": {
            "avg_sentences_per_paragraph": avg_para_sentences,
            "paragraphs_over_3_sentences": para_over_3,
            "em_dash_count": em_dash_count,
        },
        "lexicon": {
            "top_terms": top_terms(texts),
        },
        "banned_phrase_audit": ban_audit,
        "dna": {
            "voice_gene": {
                "direct_address_ratio": round(second_person_count / max(len(sentences), 1), 4),
                "collective_voice_ratio": round(first_plural_count / max(len(sentences), 1), 4),
            },
            "rhythm_gene": {
                "avg_sentence_tokens": round(mean(sent_lengths), 2) if sent_lengths else 0,
                "question_density_per_100_sentences": round((question_count / max(len(sentences), 1)) * 100, 2),
            },
            "formatting_gene": {
                "short_paragraph_compliance": round(
                    1 - (para_over_3 / max(len(paragraph_sentence_counts), 1)), 4
                ),
                "avoid_em_dash_compliance": 1 if em_dash_count == 0 else 0,
            },
            "safety_gene": {
                "banned_phrase_compliance": 1 if ban_audit["total_hits"] == 0 else 0,
                "fatal_pattern_compliance": 1 if ban_audit["fatal_pattern_hits"] == 0 else 0,
            },
        },
    }
    return profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Build writing style profile from text/markdown files.")
    parser.add_argument("--input-dir", required=True, help="Directory containing .txt/.md writing samples")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit("--input-dir must be an existing directory")

    texts = read_text_files(input_dir)
    if len(texts) < 3:
        raise SystemExit("Need at least 3 sample files (.txt/.md) to build a stable profile")

    profile = build_profile(texts)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote style profile: {output}")


if __name__ == "__main__":
    main()
