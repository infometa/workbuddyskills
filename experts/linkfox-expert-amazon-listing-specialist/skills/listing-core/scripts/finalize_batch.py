#!/usr/bin/env python3
"""Validate settled listing-core runs and export one portable batch JSON."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

SETTLED = {"complete", "failed", "needs_review"}
REQUIRED_STAGES = {"facts", "insight", "write"}


def _load(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _completed_bundle(manifest_path: str) -> tuple[dict[str, Any], str]:
    manifest_abs = os.path.abspath(manifest_path)
    manifest = _load(manifest_abs)
    if manifest.get("kind") != "listingRunManifest":
        raise ValueError(f"not a listing-core manifest: {manifest_abs}")

    stages = {
        str(stage.get("id")): stage.get("status")
        for stage in manifest.get("stages", [])
        if isinstance(stage, dict)
    }
    incomplete = sorted(stage for stage in REQUIRED_STAGES if stages.get(stage) != "complete")
    if incomplete:
        raise ValueError(f"core stages not complete ({', '.join(incomplete)}): {manifest_abs}")

    listing_json = str(manifest.get("final", {}).get("listing_json") or "")
    if not listing_json or not os.path.isfile(listing_json):
        raise ValueError(f"missing final.listing_json: {manifest_abs}")
    return _load(listing_json), os.path.abspath(listing_json)


def finalize_batch(
    items_path: str,
    out_dir: str,
) -> dict[str, str]:
    source = _load(items_path)
    items = source.get("items") if isinstance(source, dict) else None
    if not isinstance(items, list) or not items:
        raise ValueError("batch items must be a non-empty object.items array")

    products: list[dict[str, Any]] = []
    settled: list[dict[str, Any]] = []
    counts = {"complete": 0, "failed": 0, "needs_review": 0}
    row_ids: set[str] = set()

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"item {index} must be an object")
        row_id = str(item.get("row_id") or "").strip()
        status = str(item.get("status") or "").strip()
        if not row_id or row_id in row_ids:
            raise ValueError(f"row_id must be non-empty and unique: {row_id!r}")
        if status not in SETTLED:
            raise ValueError(f"row {row_id} is not settled: {status!r}")
        row_ids.add(row_id)
        counts[status] += 1

        record = {"row_id": row_id, "status": status}
        if status == "complete":
            manifest_path = str(item.get("manifest") or "")
            if not manifest_path:
                raise ValueError(f"row {row_id} complete without manifest")
            bundle, listing_json = _completed_bundle(manifest_path)
            products.append(bundle)
            record.update({"manifest": os.path.abspath(manifest_path), "listing_json": listing_json})
        else:
            reason = str(item.get("reason") or "").strip()
            if not reason:
                raise ValueError(f"row {row_id} {status} without reason")
            record["reason"] = reason
        settled.append(record)

    output_dir = Path(out_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_json = output_dir / "listing-batch-final.json"
    payload = {
        "kind": "listingBatchFinal",
        "type": "productList",
        "schema_version": 1,
        "batch_stats": {"total": len(items), **counts},
        "items": settled,
        "products": products,
    }
    batch_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"batch_json": str(batch_json)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    paths = finalize_batch(
        args.items,
        args.out_dir,
    )
    print(f"Saved full response: {paths['batch_json']}")


if __name__ == "__main__":
    main()
