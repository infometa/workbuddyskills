#!/usr/bin/env python3
"""Build a complete PPTX from one validated DeckSpec."""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from mck_fusion import FusionDeck
from scripts.gate_check_s3 import run_gate_check_s3


def _write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def _read_spec(path):
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("DeckSpec root must be an object")
    return value


def build_deck(spec_path, output_path, result_path=None):
    project_dir = os.path.dirname(os.path.abspath(spec_path))
    result_path = result_path or os.path.join(project_dir, "build_result.json")
    gate_path = os.path.join(project_dir, "gate_s3.json")
    output_path = os.path.abspath(output_path)
    temp_path = os.path.join(
        os.path.dirname(output_path),
        f".{os.path.basename(output_path)}.{uuid.uuid4().hex}.tmp.pptx",
    )
    result = {
        "passed": False,
        "spec_path": os.path.abspath(spec_path),
        "output_path": output_path,
        "built_slides": 0,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    try:
        spec = _read_spec(spec_path)
        gate = run_gate_check_s3(spec_path, project_dir)
        _write_json(gate_path, gate)
        result["gate_s3_passed"] = gate["passed"]
        if not gate["passed"]:
            raise ValueError(f"S3 gate failed with {len(gate['fail_items'])} issue(s)")

        slides = spec["slides"]
        total = spec["meta"]["total_slides"]
        if total != len(slides):
            raise ValueError(f"Declared total {total} does not match slide count {len(slides)}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        deck = FusionDeck(total_slides=total)
        deck.build_specs(slides)
        deck.save(temp_path)
        if len(deck.prs.slides) != total:
            raise RuntimeError(f"Built slide count {len(deck.prs.slides)} does not match {total}")
        os.replace(temp_path, output_path)
        result.update({
            "passed": True,
            "built_slides": total,
            "actual_slides": len(deck.prs.slides),
            "file_size": os.path.getsize(output_path),
        })
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        if os.path.exists(temp_path):
            os.remove(temp_path)
    finally:
        _write_json(result_path, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Build a PPTX from a strict DeckSpec")
    parser.add_argument("--spec", required=True, help="Path to deck_spec.json")
    parser.add_argument("--output", required=True, help="Final .pptx output path")
    parser.add_argument("--result", help="Optional build_result.json path")
    args = parser.parse_args()

    result = build_deck(args.spec, args.output, args.result)
    if result["passed"]:
        print(f"[build_fusion_deck] Built {result['actual_slides']} slides: {result['output_path']}")
    else:
        print(f"[build_fusion_deck] Failed: {result.get('error', 'unknown error')}", file=sys.stderr)
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
