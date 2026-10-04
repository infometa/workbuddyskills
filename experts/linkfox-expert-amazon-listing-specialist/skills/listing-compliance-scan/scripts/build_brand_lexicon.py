#!/usr/bin/env python3
"""Build the hashed brand-conflict lexicon from a nz_common_tort_lexicon export.

Usage:
  python3 build_brand_lexicon.py --csv nz_common_tort_lexicon_detail_YYYYMMDDHHMM.csv \
      [--platform AMAZON] [--out-dir /path/to/skills/_listing-private-assets/data]

Rebuilt by hand after each upstream export — there is no incremental feed.
Writes `brand-lexicon-<version>.bin` (concatenated 8-byte digests, sorted) plus a
`.json` sidecar. The source phrases are deliberately NOT written: shipping digests
keeps the word list out of any skill package a user downloads, while still
answering "does this listing contain a known infringing brand term?".

The export carries platform_code / site_code / risk_level columns. They are dropped
on purpose: in the 2026-08-11 export 124,685 of 125,297 words appear under AMAZON,
124,367 words share one identical 20-site set, and 1,761,595 of 1,761,641 rows are
risk_level=3. Those columns are cartesian padding, not signal.
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lexicon_hash import compact_digest, digest, tokenize  # noqa: E402
from private_assets import private_assets_dir  # noqa: E402

def version_from_filename(path: Path) -> str:
    """`..._202608111418.csv` -> `2026.08.11`; falls back to today."""
    stem = path.stem
    for chunk in reversed(stem.split("_")):
        if chunk.isdigit() and len(chunk) >= 8:
            return f"{chunk[0:4]}.{chunk[4:6]}.{chunk[6:8]}"
    return datetime.now(timezone.utc).strftime("%Y.%m.%d")

def collect(csv_path: Path, platform: str) -> tuple:
    """Return (digests, compact_digests, max_tokens) for one platform slice."""
    csv.field_size_limit(10 ** 7)
    digests = set()
    compacts = set()
    max_tokens = 0
    with csv_path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            if platform and row.get("platform_code") != platform:
                continue
            tokens = tokenize(row.get("infringe_word") or "")
            if not tokens:
                continue
            digests.add(digest(tokens))
            if len(tokens) == 1:
                compact = compact_digest(tokens)
                if compact:
                    compacts.add(compact)
            max_tokens = max(max_tokens, len(tokens))
    return digests, compacts, max_tokens

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--platform", default="AMAZON",
                        help="platform_code to keep; empty string keeps every platform")
    parser.add_argument("--out-dir", type=Path,
                        default=private_assets_dir())
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"csv not found: {args.csv}", file=sys.stderr)
        return 1

    version = version_from_filename(args.csv)
    digests, compacts, max_tokens = collect(args.csv, args.platform)
    if not digests:
        print("no rows matched — check --platform", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    blob = b"".join(sorted(digests))
    bin_path = args.out_dir / f"brand-lexicon-{version}.bin"
    bin_path.write_bytes(blob)
    compact_blob = b"".join(sorted(compacts))
    (args.out_dir / f"brand-lexicon-{version}.compact.bin").write_bytes(compact_blob)
    meta = {
        "version": version,
        "algo": "sha256-first-8-bytes-of-space-joined-lowercase-tokens",
        "platform": args.platform or "ALL",
        "entry_count": len(digests),
        "compact_entry_count": len(compacts),
        "max_tokens": max_tokens,
        "source_export": args.csv.name,
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (args.out_dir / f"brand-lexicon-{version}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**meta, "bytes": len(blob) + len(compact_blob)},
                     ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
