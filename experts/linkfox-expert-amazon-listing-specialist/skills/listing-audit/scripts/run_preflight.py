#!/usr/bin/env python3
"""Package deterministic Audit preparation into one local invocation.

This command performs no semantic evaluation and no external request. It turns a
Product Detail/user-listing source into the exact normalized, compliance and field
QA artifacts consumed by listing-audit and the canonical scorer.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = SKILL_DIR.parent
CORE_SCRIPTS = SKILLS_DIR / "listing-core" / "scripts"
SCORER_SCRIPTS = SKILLS_DIR / "listing-quality-scorer" / "scripts"
COMPLIANCE_SCRIPT = SKILLS_DIR / "listing-compliance-scan" / "scripts" / "save_compliance_output.py"
sys.path.insert(0, str(CORE_SCRIPTS))
sys.path.insert(0, str(SCORER_SCRIPTS))

from build_spec import assemble_spec  # noqa: E402
from normalize_listing_input import NormalizationError, normalize  # noqa: E402
from validate_fields import check_fields  # noqa: E402


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(os.path.abspath(args.out_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    timings: dict[str, int] = {}

    started = time.perf_counter()
    source = _load_json(args.source)
    normalized = normalize(
        source, args.source_kind, args.asin, args.marketplace, spec=None,
    )
    normalized_path = out_dir / "listing-normalized.json"
    _write_json(normalized_path, normalized)
    timings["normalize_ms"] = _elapsed_ms(started)

    listing_path = out_dir / "listing-for-compliance.json"
    _write_json(listing_path, normalized["listing"])
    compliance_path = out_dir / "compliance-report.json"
    compliance_cmd = [
        sys.executable, str(COMPLIANCE_SCRIPT),
        "--listing", str(listing_path), "--out", str(compliance_path),
    ]
    if args.asin:
        compliance_cmd += ["--asin", args.asin]
    if args.marketplace:
        compliance_cmd += ["--site", args.marketplace]
    for brand in args.own_brand:
        compliance_cmd += ["--own-brand", brand]
    for key in args.skip_compliance:
        compliance_cmd += ["--skip", key]
    started = time.perf_counter()
    compliance = subprocess.run(compliance_cmd, capture_output=True, text=True)
    timings["compliance_ms"] = _elapsed_ms(started)
    if compliance.returncode != 0:
        raise RuntimeError(compliance.stderr or compliance.stdout or "compliance scan failed")

    started = time.perf_counter()
    spec = assemble_spec(
        mode="rewrite",
        brands_owned=args.own_brand,
        brands_competitor=args.competitor_brand,
        keywords={},
        category_flags=[],
        marketplace=args.marketplace or "US",
        evidence_mode="facts_only",
    )
    facts_text = args.facts.read_text(encoding="utf-8") if args.facts else ""
    check_report = check_fields(normalized["listing"], spec, facts_text=facts_text)
    check_report_path = out_dir / "check-report-before.json"
    _write_json(check_report_path, check_report)
    timings["validate_ms"] = _elapsed_ms(started)

    summary_path = out_dir / "audit-preflight.json"
    summary = {
        "kind": "listingAuditPreflight",
        "schema_version": 1,
        "target": {"asin": args.asin, "marketplace": args.marketplace},
        "paths": {
            "normalized": str(normalized_path),
            "compliance": str(compliance_path),
            "check_report": str(check_report_path),
        },
        "field_metrics": normalized["field_metrics"],
        "field_provenance": normalized["field_provenance"],
        "timings": timings,
    }
    _write_json(summary_path, summary)
    return {"summary": summary_path, **summary["paths"], "timings": timings}


def main() -> int:
    parser = argparse.ArgumentParser(description="listing-audit deterministic preflight")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument(
        "--source-kind", default="auto",
        choices=("auto", "amazon_product_detail", "user_listing", "listing_core"),
    )
    parser.add_argument("--asin", default=None)
    parser.add_argument("--marketplace", default="US")
    parser.add_argument("--facts", type=Path, default=None)
    parser.add_argument("--own-brand", action="append", default=[])
    parser.add_argument("--competitor-brand", action="append", default=[])
    parser.add_argument(
        "--skip-compliance", action="append", default=[],
        choices=("restricted", "claims", "claims_zh", "brand"),
        help="debug/tests only; production audit must not skip libraries",
    )
    args = parser.parse_args()
    try:
        result = run(args)
    except (OSError, ValueError, NormalizationError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"audit preflight failed: {exc}", file=sys.stderr)
        return 2

    print(f"Saved full response: {result['summary']}")
    print(f"JSON artifact: {result['normalized']}")
    print(f"JSON artifact: {result['compliance']}")
    print(f"JSON artifact: {result['check_report']}")
    print("Timings: " + " ".join(f"{key}={value}ms" for key, value in result["timings"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
