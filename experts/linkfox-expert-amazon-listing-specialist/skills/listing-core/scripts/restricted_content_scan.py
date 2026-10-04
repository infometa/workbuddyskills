#!/usr/bin/env python3
"""Scan Amazon listing text against a versioned term library.

Usage:
  python3 restricted_content_scan.py --listing listing.json [--json] [--fail-on review]
  python3 restricted_content_scan.py --listing listing.json \
      --library /path/to/skills/_listing-private-assets/data/superlative-claims-v1.json

The input may contain title, bullets, description, search_terms, item_highlights,
and subject_matter. A `block` hit exits 2; --fail-on review also exits 2 for review hits.

Defaults to the restricted-content library next to this script. `--library` points it
at any file with the same shape — currently the superlative / unsubstantiated-claim
library, which is a separate concern (绝对化用语与无证据宣称) from restricted categories
(受限品类) and is kept in its own file so each can be versioned and updated on its own.
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_LIBRARY = Path(__file__).resolve().parent / "restricted-content-v1.json"
FIELDS = ("title", "item_highlights", "bullets", "description", "search_terms", "subject_matter")

def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())

def values_by_field(listing: dict) -> dict:
    fields = {}
    for field in FIELDS:
        value = listing.get(field, "")
        fields[field] = " ".join(str(x) for x in value) if isinstance(value, list) else str(value)
    return fields

def find_spans(text: str, term: str) -> list:
    """Every (start, end) where `term` occurs as whole words, offsets into `text`."""
    lowered = text.casefold()
    spans = [m.span() for m in re.finditer(
        r"(?<![a-z0-9])" + re.escape(term.casefold()) + r"(?![a-z0-9])", lowered)]
    # Detect fully separated obfuscation (c-u-r-e / c u r e) without treating
    # an ordinary larger word such as "secure" as a hit for "cure".
    compact = normalized(term)
    if len(compact) < 4 or normalized(term) != term.casefold():
        return spans
    obfuscated = r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(map(re.escape, compact)) + r"(?![a-z0-9])"
    spans.extend(m.span() for m in re.finditer(obfuscated, lowered))
    return spans

def drop_contained(hits: list) -> list:
    """Keep the longest term at each position: "best seller" wins over "best"."""
    kept = []
    for hit in sorted(hits, key=lambda h: (h["offset"], -h["length"])):
        if any(k["offset"] <= hit["offset"]
               and hit["offset"] + hit["length"] <= k["offset"] + k["length"]
               for k in kept):
            continue
        kept.append(hit)
    return kept

def scan(listing: dict, library: dict) -> list:
    hits = []
    for field, text in values_by_field(listing).items():
        found = []
        for level in ("block", "review"):
            for rule in library["profiles"][level]:
                # Amazon polices subjective claims harder in the title than in body
                # copy, so a rule may name the fields where review escalates to block.
                severity = "block" if field in rule.get("escalate_in", ()) else level
                for term in rule["terms"]:
                    for start, end in find_spans(text, term):
                        found.append({"field": field, "severity": severity, "category": rule["category"], "term": text[start:end], "offset": start, "length": end - start, "reason": rule["reason"], "replacement": rule["replacement"]})
        hits.extend(drop_contained(found))
    for hit in hits:
        hit.pop("length")
    return hits

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listing", required=True, type=Path)
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY,
                        help="term library to scan against; defaults to restricted-content")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", choices=("block", "review"), default="block")
    args = parser.parse_args()
    listing = json.loads(args.listing.read_text(encoding="utf-8"))
    library = json.loads(args.library.read_text(encoding="utf-8"))
    hits = scan(listing, library)
    result = {"library": library.get("library", args.library.stem),
              "library_version": library["version"], "hits": hits, "block_count": sum(h["severity"] == "block" for h in hits), "review_count": sum(h["severity"] == "review" for h in hits)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for hit in hits:
            print(f"{hit['severity'].upper()} {hit['field']}@{hit['offset']}: {hit['term']} ({hit['category']})")
        if not hits:
            print("PASS: no restricted-content hits")
    return 2 if result["block_count"] or (args.fail_on == "review" and result["review_count"]) else 0

if __name__ == "__main__":
    raise SystemExit(main())
