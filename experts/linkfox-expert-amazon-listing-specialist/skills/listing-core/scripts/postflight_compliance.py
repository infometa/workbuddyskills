#!/usr/bin/env python3
"""Run the complete local compliance suite over the final front/back listing fields."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


BACKEND_FIELDS = frozenset({"search_terms", "subject_matter"})


def scanner_script() -> Path:
    script = (
        Path(__file__).resolve().parents[2]
        / "listing-compliance-scan" / "scripts" / "save_compliance_output.py"
    )
    if not script.is_file():
        raise RuntimeError(f"complete compliance scanner not found: {script}")
    return script


def _blocking_hits(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Use the global lexicon strictly for backend fields, where terms are intentional.

    Frontend brand-lexicon matches contain many ordinary Title Case phrases.  Explicit
    competitor brands are already fail-closed in validate_fields; opaque global marks on
    frontend copy remain human-review signals.  Restricted/claims block hits remain
    blockers in every field.
    """
    blocking: list[dict[str, Any]] = []
    for hit in report.get("hits") or []:
        if not isinstance(hit, dict) or hit.get("severity") != "block":
            continue
        if hit.get("library") == "brand-lexicon" and hit.get("field") not in BACKEND_FIELDS:
            continue
        blocking.append(hit)
    return blocking


def run_postflight(
    listing_path: str | Path,
    output_path: str | Path,
    spec: dict[str, Any],
    *,
    asin: str | None = None,
) -> dict[str, Any]:
    listing = Path(listing_path).resolve()
    output = Path(output_path).resolve()
    if not listing.is_file():
        raise RuntimeError(f"listing draft not found: {listing}")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(scanner_script()),
        "--listing", str(listing),
        "--out", str(output),
        "--site", str(spec.get("marketplace") or "US"),
    ]
    if asin:
        command += ["--asin", asin]
    brands = spec.get("brands") or {}
    for brand in brands.get("owned") or []:
        if isinstance(brand, str) and brand.strip():
            command += ["--own-brand", brand.strip()]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"complete compliance scanner failed: {detail}")
    try:
        report = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid compliance report: {exc}") from exc

    failed_libraries = [
        item for item in report.get("libraries") or []
        if isinstance(item, dict) and item.get("status") not in {"ok", "not_applicable"}
    ]
    blocking = _blocking_hits(report)
    frontend_brand_reviews = [
        hit for hit in report.get("hits") or []
        if isinstance(hit, dict)
        and hit.get("library") == "brand-lexicon"
        and hit.get("field") not in BACKEND_FIELDS
    ]
    status = "blocked" if (blocking or failed_libraries) else (
        "review" if (report.get("hits") or frontend_brand_reviews) else "passed"
    )
    report["postflight_gate"] = {
        "status": status,
        "blocking_hits": blocking,
        "failed_libraries": failed_libraries,
        "frontend_brand_reviews": frontend_brand_reviews,
        "policy": (
            "restricted/claims block in all fields; global brand lexicon blocks backend fields; "
            "frontend global-brand matches require review unless explicit competitor validation blocks them"
        ),
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report

