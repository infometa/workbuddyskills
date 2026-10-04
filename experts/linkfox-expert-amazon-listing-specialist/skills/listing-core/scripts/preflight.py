#!/usr/bin/env python3
"""Fail fast when the deployed listing-core runtime is incomplete."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


REQUIRED_FILES = (
    "run_manifest.py",
    "build_spec.py",
    "run_full.py",
    "validate_fields.py",
    "finalize_listing.py",
    "finalize_batch.py",
    "save_keyword_plan.py",
    "save_buyer_questions.py",
    "project_product_detail.py",
    "evidence_cache.py",
    "response_io.py",
    "linkfox_paths.py",
    "restricted_content_scan.py",
    "listing_spec.py",
    "restricted-content-v1.json",
)

# 只守热路径上容易被文档/部署版本写错的参数；完整帮助仍由各脚本 argparse 维护。
REQUIRED_CLI_FLAGS = {
    "run_manifest.py": {
        "--run-dir", "--mode", "--manifest", "--stage", "--status", "--artifact",
        "--activate", "--listing-json", "--detail-preview",
    },
    "build_spec.py": {
        "--mode", "--out", "--keywords", "--buyer-questions", "--audit-handoff",
        "--brands-owned", "--brands-competitor", "--marketplace", "--output-language",
    },
    "run_full.py": {
        "--run-dir", "--mode", "--keywords", "--audit-handoff", "--draft", "--facts",
        "--deductions", "--scorer",
    },
    "validate_fields.py": {"--draft", "--spec", "--facts", "--out"},
    "finalize_listing.py": {
        "--manifest", "--draft", "--spec", "--check-report", "--score-result",
    },
    "save_keyword_plan.py": {"--out", "--source", "--matrix"},
    "save_buyer_questions.py": {"--out", "--source"},
    "project_product_detail.py": {
        "--source", "--out-dir", "--target-asin", "--own-facts", "--competitor-asin",
        "--reference-asin",
    },
}


def _declared_flags(script: Path) -> set[str]:
    try:
        source = script.read_text(encoding="utf-8")
    except OSError:
        return set()
    return set(re.findall(r"add_argument\(\s*['\"](--[a-z0-9-]+)['\"]", source))


def inspect_runtime(source_file: Path | None = None) -> dict[str, object]:
    scripts_root = (source_file or Path(__file__)).resolve().parent
    missing = [item for item in REQUIRED_FILES if not (scripts_root / item).is_file()]
    incompatible = {
        script: sorted(required - _declared_flags(scripts_root / script))
        for script, required in REQUIRED_CLI_FLAGS.items()
        if script not in missing and required - _declared_flags(scripts_root / script)
    }
    return {
        "ok": not missing and not incompatible,
        "scripts_root": str(scripts_root),
        "missing": missing,
        "incompatible": incompatible,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("fast", "standard"), default="standard")
    args = parser.parse_args()
    result = inspect_runtime()
    result["profile"] = args.profile
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
