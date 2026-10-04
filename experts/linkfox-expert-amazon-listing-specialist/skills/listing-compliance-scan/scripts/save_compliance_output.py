#!/usr/bin/env python3
"""Run every local compliance library over one listing and persist a complianceReport.

Usage:
  python3 save_compliance_output.py --listing /abs/listing.json \
      [--own-brand Velmoriq] [--skip brand] [--asin B0XXXXXXXX] [--site US]

Runs every applicable local term library in one call — restricted content, superlative /
unsubstantiated claims (English and Chinese), and brand conflict — merges their hits,
and writes it through linkfox_paths so the bridge picks it up:

    Saved full response: /abs/.../linkfox-listing-compliance-report-<ts>.json (N bytes)

One entry point on purpose. The three scanners share a hit shape, so merging here is
cheap, and it removes the chance of the agent running two libraries and reporting as
if it had run three. A library that fails to load is recorded in `libraries[].status`
rather than silently dropped — a missing library must never read as "passed".

The scanners themselves stay usable standalone for debugging; this script is what the
playbook calls.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from linkfox_paths import resolve_data_path  # noqa: E402
from private_assets import private_assets_dir  # noqa: E402

SLUG = "linkfox-listing-compliance-report"
PRIVATE_DATA_DIR = private_assets_dir()
FIELD_ORDER = ("title", "item_highlights", "bullets", "description", "search_terms", "subject_matter")
SEVERITY_ORDER = {"block": 0, "review": 1}
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

def has_chinese(listing: dict) -> bool:
    """Whether any scanned field carries Chinese, which decides if the zh library runs."""
    return any(CJK_RE.search(text) for text in values_by_field(listing).values())

def core_scripts(explicit: Path = None) -> Path:
    """listing-core sits beside this skill on EFS; --core-scripts overrides for tests."""
    return explicit or SKILL_DIR.parent / "listing-core" / "scripts"

def run_scanner(argv: list) -> tuple:
    """Return (payload, error). Exit code 2 means hits were found, not a failure."""
    proc = subprocess.run([sys.executable, *map(str, argv)], capture_output=True, text=True)
    if proc.returncode not in (0, 2):
        return None, (proc.stderr or proc.stdout).strip().splitlines()[-1:] or ["unknown error"]
    try:
        return json.loads(proc.stdout), None
    except json.JSONDecodeError:
        return None, [f"unparseable output: {proc.stdout[:200]}"]

def values_by_field(listing: dict) -> dict:
    fields = {}
    for field in FIELD_ORDER:
        value = listing.get(field, "")
        fields[field] = "\n".join(str(x) for x in value) if isinstance(value, list) else str(value)
    return fields

def scanner_plan(args, listing: dict) -> list:
    """(key, argv) for each library this run should execute.

    The Chinese claims library only runs when the copy actually contains Chinese —
    on an English listing it can never match, and listing it as "ok" would imply a
    check that had nothing to look at. It is reported as not_applicable instead.
    """
    core = core_scripts(args.core_scripts)
    plan = [
        ("restricted", [core / "restricted_content_scan.py",
                        "--listing", args.listing, "--json"]),
        ("claims", [core / "restricted_content_scan.py",
                    "--listing", args.listing, "--json",
                    "--library", PRIVATE_DATA_DIR / "superlative-claims-v1.json"]),
    ]
    brand = [SKILL_DIR / "scripts" / "brand_conflict_scan.py",
             "--listing", args.listing, "--json"]
    for own in args.own_brand:
        brand += ["--own-brand", own]
    plan.append(("brand", brand))
    if has_chinese(listing):
        plan.insert(2, ("claims_zh", [core / "restricted_content_scan.py",
                                      "--listing", args.listing, "--json",
                                      "--library", PRIVATE_DATA_DIR / "superlative-claims-zh-v1.json"]))
    return [(key, argv) for key, argv in plan if key not in args.skip]

def scanned_fields(listing: dict) -> list:
    present = []
    for field in FIELD_ORDER:
        value = listing.get(field)
        if value or value == 0:
            present.append(field)
    return present

def merge_duplicates(hits: list) -> list:
    """Fold hits that flag the same span in the same field into one.

    "bpa free" is both a registered mark and an eco claim, so two libraries land on
    the identical offset. Showing it twice — once block, once review — reads as a
    contradiction. The stricter verdict wins and the other library is named on the hit.
    """
    merged = {}
    for hit in sorted(hits, key=lambda h: SEVERITY_ORDER.get(h["severity"], 9)):
        key = (hit["field"], hit.get("offset"), hit["term"].casefold())
        if key in merged:
            others = merged[key].setdefault("also_flagged_by", [])
            if hit["library"] not in others:
                others.append(hit["library"])
            continue
        merged[key] = dict(hit)
    return list(merged.values())

def sort_key(hit: dict) -> tuple:
    order = FIELD_ORDER.index(hit["field"]) if hit["field"] in FIELD_ORDER else len(FIELD_ORDER)
    return (SEVERITY_ORDER.get(hit["severity"], 9), order, hit.get("offset", 0))

def build_report(args) -> dict:
    listing = json.loads(Path(args.listing).read_text(encoding="utf-8"))
    libraries, hits = [], []
    if not has_chinese(listing) and "claims_zh" not in args.skip:
        libraries.append({"key": "claims_zh", "status": "not_applicable",
                          "reason": "文案中未出现中文，中文极限词库无适用内容"})
    for key, argv in scanner_plan(args, listing):
        payload, error = run_scanner(argv)
        if error:
            libraries.append({"key": key, "status": "failed", "error": error[0]})
            continue
        libraries.append({"key": key, "status": "ok",
                          "library": payload.get("library"),
                          "version": payload.get("library_version")})
        for hit in payload["hits"]:
            hits.append({**hit, "library": payload.get("library")})
    hits = merge_duplicates(hits)
    hits.sort(key=sort_key)

    block = sum(h["severity"] == "block" for h in hits)
    review = sum(h["severity"] == "review" for h in hits)
    # not_applicable 不是降级：它说明这个库没有可检内容，不是"没跑起来"。
    degraded = [lib for lib in libraries if lib["status"] not in ("ok", "not_applicable")]
    return {
        "type": "complianceReport",
        # A failed library means we cannot say "pass" — say so instead of implying safety.
        "verdict": "block" if block else "review" if (review or degraded) else "pass",
        "asin": args.asin,
        "site": args.site,
        "summary": {
            "block_count": block,
            "review_count": review,
            "scanned_fields": scanned_fields(listing),
            "degraded": bool(degraded),
            "note": ("部分词库未能执行，本次结论不完整" if degraded
                     else "本地词库为确定性判定；未命中不等于无风险，品牌词库不是全集"),
        },
        "libraries": libraries,
        "hits": hits,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listing", required=True, type=Path)
    parser.add_argument("--own-brand", action="append", default=[])
    parser.add_argument("--skip", action="append", default=[],
                        choices=("restricted", "claims", "claims_zh", "brand"),
                        help="skip one library; recorded nowhere, so use only for debugging")
    parser.add_argument("--asin", default=None)
    parser.add_argument("--site", default=None)
    parser.add_argument("--core-scripts", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None, help="bypass linkfox_paths (tests)")
    args = parser.parse_args()

    report = build_report(args)
    blob = json.dumps(report, ensure_ascii=False, indent=2)
    out = args.out or Path(resolve_data_path(SLUG, time.time()))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(blob + "\n", encoding="utf-8")
    print(f"Saved full response: {out} ({len(blob.encode('utf-8'))} bytes)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
