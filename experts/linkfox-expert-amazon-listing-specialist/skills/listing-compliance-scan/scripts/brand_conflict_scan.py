#!/usr/bin/env python3
"""Scan Amazon listing text against the hashed brand-conflict lexicon.

Usage:
  python3 brand_conflict_scan.py --listing listing.json [--json] [--fail-on review] \
      [--own-brand Velmoriq] [--lexicon /path/to/brand-lexicon-2026.08.11.bin]

Deliberately the same shape as listing-core/scripts/restricted_content_scan.py —
same --listing/--json/--fail-on flags, same hit keys — so both scanners' output can
be merged into one compliance report without a second rendering contract.

The lexicon is a set of opaque digests (see lexicon_hash.py), so a hit tells us the
matched span is a known infringing brand term but never reveals terms the listing
does not already contain. `term` is therefore quoted from the seller's own text.

Severity follows the product decision "uppercase blocks, lowercase reviews": the
lexicon is full of ordinary English words registered as marks (Brother, Weber,
Bounce, Cure), so casing in the source text is the only local signal for whether the
seller meant the brand or the word. Two guards keep that from over-blocking —
a match in lead position, and a match inside a run of shouty caps, both carry no
casing signal and fall back to review.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lexicon_hash import DIGEST_BYTES, compact_digest, digest  # noqa: E402
from private_assets import private_assets_dir  # noqa: E402

DATA_DIR = private_assets_dir()
FIELDS = ("title", "item_highlights", "bullets", "description", "search_terms", "subject_matter")
RAW_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
LEAD_CHARS = set(".!?\n|—–-:;•*")
# Backend fields are lowercase by convention, so casing carries no brand signal there.
# A competitor brand parked in Search Terms is the textbook TRO exposure, and
# CLAUDE.md's Layer A is explicit that competitor brands are zero-tolerance — so
# these fields block on any hit rather than falling through to review.
CASE_BLIND_FIELDS = frozenset({"search_terms", "subject_matter"})
# The upstream litigation lexicon intentionally has very broad recall and includes
# ordinary category language. These demonstrated generic terms stay visible as
# review hits in backend fields, but must not block an otherwise valid listing.
# Keep this list narrow: add only terms reproduced against the shipped lexicon.
BACKEND_GENERIC_REVIEW_TERMS = frozenset({
    "discovery",
    "stimulation",
    "tummy time",
})
# Amazon titles are written in Title Case, where every significant word is capitalised.
# A capital there says nothing about brand intent, so above this share of capitalised
# words the whole field falls back to review rather than blocking "Velvet Pouch".
TITLE_CASE_RATIO = 0.6
TITLE_CASE_MIN_TOKENS = 4

BLOCK_REASON = "命中已知侵权品牌词，且在原文中以品牌形态（首字母大写／全大写）出现"
BLOCK_REASON_BACKEND = "后台字段命中已知侵权品牌词——后台词天然小写，大小写不构成豁免理由"
REVIEW_REASON_BACKEND_GENERIC = "后台字段命中广覆盖品牌词库，但该词属于已验证的通用类目表达，仅保留人工复核提示"
REVIEW_REASON = "命中已知侵权品牌词，但原文大小写不构成品牌证据（小写／句首／整段大写／标题式大写），需人工确认"
BLOCK_FIX = "删除该词或替换为不指向任何品牌的通用描述词"
REVIEW_FIX = "确认为普通描述用词可保留；若指代该品牌则删除或改为通用说法"
COMPACT_REASON = "拆写形态疑似指向已知侵权品牌词（如 Go-Pro / go pro 之于 GoPro），属启发式匹配"
COMPACT_FIX = "若确为该品牌的拆写，删除或改为通用说法；若是两个独立普通词，可保留"

def latest_lexicon() -> Path:
    # `.compact.bin` is the sidecar index, never the primary lexicon.
    found = sorted(p for p in DATA_DIR.glob("brand-lexicon-*.bin")
                   if not p.name.endswith(".compact.bin"))
    if not found:
        raise SystemExit(f"no brand lexicon found under {DATA_DIR}")
    return found[-1]

def load_lexicon(path: Path) -> set:
    if not path.exists():
        return set()
    blob = path.read_bytes()
    if len(blob) % DIGEST_BYTES:
        raise SystemExit(f"corrupt lexicon: {path} is not a multiple of {DIGEST_BYTES} bytes")
    return {blob[i:i + DIGEST_BYTES] for i in range(0, len(blob), DIGEST_BYTES)}

def load_meta(bin_path: Path) -> dict:
    sidecar = bin_path.with_suffix(".json")
    if not sidecar.exists():
        return {"version": bin_path.stem.replace("brand-lexicon-", ""), "max_tokens": 8}
    return json.loads(sidecar.read_text(encoding="utf-8"))

def values_by_field(listing: dict) -> dict:
    """Flatten each field to one string; lists join with newlines to keep bullets apart."""
    fields = {}
    for field in FIELDS:
        value = listing.get(field, "")
        fields[field] = "\n".join(str(x) for x in value) if isinstance(value, list) else str(value)
    return fields

def in_lead_position(text: str, start: int) -> bool:
    """True when nothing but whitespace or a separator precedes the match.

    Grammar capitalises the first word of every sentence and every bullet lead-in,
    so a capital there says nothing about brand intent.
    """
    cursor = start - 1
    while cursor >= 0 and text[cursor].isspace():
        cursor -= 1
    return cursor < 0 or text[cursor] in LEAD_CHARS

def is_title_cased(tokens: list) -> bool:
    """True when the field capitalises most of its words, voiding the casing signal."""
    words = [t[2] for t in tokens if len(t[2]) > 1 and t[2][0].isalpha()]
    if len(words) < TITLE_CASE_MIN_TOKENS:
        return False
    return sum(w[0].isupper() for w in words) / len(words) >= TITLE_CASE_RATIO

def in_caps_run(tokens: list, index: int, span_len: int) -> bool:
    """True when a neighbouring token is also SHOUTING, which voids the casing signal."""
    def shouty(i):
        return 0 <= i < len(tokens) and len(tokens[i][2]) > 1 and tokens[i][2].isupper()
    return shouty(index - 1) or shouty(index + span_len)

def classify(field: str, text: str, tokens: list, index: int, span_len: int,
             title_cased: bool) -> str:
    if field in CASE_BLIND_FIELDS:
        phrase = " ".join(t[2].casefold() for t in tokens[index:index + span_len])
        if phrase in BACKEND_GENERIC_REVIEW_TERMS:
            return "review"
        return "block"
    # Multi-token entries get the same casing test as single words. The lexicon holds
    # ordinary descriptive phrases registered as marks ("bpa free", "food grade"), so
    # "phrase therefore brand" would block routine material claims.
    raw = " ".join(t[2] for t in tokens[index:index + span_len])
    if raw.islower():
        return "review"
    if title_cased or in_lead_position(text, tokens[index][0]) \
            or in_caps_run(tokens, index, span_len):
        return "review"
    return "block"

def scan_field(field: str, text: str, lexicon: set, max_tokens: int, own: set,
               compacts: set = frozenset()) -> list:
    tokens = [(m.start(), m.end(), m.group(0)) for m in RAW_TOKEN_RE.finditer(text)]
    lowered = [t[2].casefold() for t in tokens]
    title_cased = is_title_cased(tokens)
    hits = []
    i = 0
    while i < len(tokens):
        # Longest match wins, then jump past it so "GoPro Hero" is one hit, not two.
        for span in range(min(max_tokens, len(tokens) - i), 0, -1):
            phrase = lowered[i:i + span]
            heuristic = False
            if digest(phrase) not in lexicon:
                # A hyphenated or space-split spelling of a one-word mark still has to
                # be caught, but a compact join is a guess, so it can only ever review.
                if span < 2 or compact_digest(phrase) not in compacts:
                    continue
                heuristic = True
            if " ".join(phrase) in own or "".join(phrase) in own:
                break
            start, end = tokens[i][0], tokens[i + span - 1][1]
            severity = "review" if heuristic else classify(field, text, tokens, i, span, title_cased)
            normalized_phrase = " ".join(phrase)
            backend_generic_review = (
                field in CASE_BLIND_FIELDS
                and normalized_phrase in BACKEND_GENERIC_REVIEW_TERMS
                and severity == "review"
            )
            hits.append({
                "field": field,
                "severity": severity,
                "category": "brand_conflict",
                "term": text[start:end],
                "offset": start,
                "reason": (
                    COMPACT_REASON if heuristic
                    else REVIEW_REASON_BACKEND_GENERIC if backend_generic_review
                    else (BLOCK_REASON_BACKEND if field in CASE_BLIND_FIELDS else BLOCK_REASON)
                    if severity == "block" else REVIEW_REASON
                ),
                "replacement": (
                    COMPACT_FIX if heuristic
                    else BLOCK_FIX if severity == "block" else REVIEW_FIX
                ),
            })
            i += span - 1
            break
        i += 1
    return hits

def scan(listing: dict, lexicon: set, max_tokens: int, own: set,
         compacts: set = frozenset()) -> list:
    hits = []
    for field, text in values_by_field(listing).items():
        hits.extend(scan_field(field, text, lexicon, max_tokens, own, compacts))
    return hits

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listing", required=True, type=Path)
    parser.add_argument("--lexicon", type=Path, default=None)
    parser.add_argument("--own-brand", action="append", default=[],
                        help="seller's own brand; repeatable, never reported as a conflict")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", choices=("block", "review"), default="block")
    args = parser.parse_args()

    bin_path = args.lexicon or latest_lexicon()
    meta = load_meta(bin_path)
    lexicon = load_lexicon(bin_path)
    compacts = load_lexicon(bin_path.with_suffix(".compact.bin"))
    listing = json.loads(args.listing.read_text(encoding="utf-8"))
    own = {" ".join(re.findall(r"[a-z0-9]+", b.casefold())) for b in args.own_brand}
    hits = scan(listing, lexicon, int(meta.get("max_tokens", 8)), own, compacts)

    result = {
        "library": "brand-lexicon",
        "library_version": meta.get("version"),
        "hits": hits,
        "block_count": sum(h["severity"] == "block" for h in hits),
        "review_count": sum(h["severity"] == "review" for h in hits),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"brand-lexicon {result['library_version']}: "
              f"{result['block_count']} block / {result['review_count']} review")
        for hit in hits:
            print(f"  [{hit['severity']}] {hit['field']}@{hit['offset']}: {hit['term']}")
    if result["block_count"] or (args.fail_on == "review" and result["review_count"]):
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
