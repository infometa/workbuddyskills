#!/usr/bin/env python3
"""
Content Quality Gate — CI/CD-style gate for content publishing.

Filters drafts through quality scorer before they publish.
Nothing goes live without passing automated quality scoring.

Usage:
    python content-quality-gate.py --input drafts.json
    python content-quality-gate.py --input drafts.json --conservative
    python content-quality-gate.py --input drafts.json --threshold 75
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
import subprocess

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = Path(os.environ.get("CONTENT_OPS_DATA_DIR", PROJECT_DIR / "data"))

DRAFTS_INPUT_FILE = DATA_DIR / "content-drafts-latest.json"
DRAFTS_OUTPUT_FILE = DATA_DIR / "content-drafts-filtered.json"
QUALITY_SCORES_FILE = DATA_DIR / "quality-scores-latest.json"


def run_quality_scorer(input_file, verbose=False):
    """Run the quality scorer on the drafts file."""
    scorer_script = SCRIPT_DIR / "content-quality-scorer.py"
    cmd = [
        sys.executable,
        str(scorer_script),
        "--input", str(input_file)
    ]

    if verbose:
        cmd.append("--verbose")

    print(f"🔍 Running quality scorer...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Quality scorer failed:")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False

    if verbose:
        print(result.stdout)

    return True


def load_quality_scores():
    """Load the latest quality scoring results."""
    if not QUALITY_SCORES_FILE.exists():
        print(f"❌ Quality scores file not found: {QUALITY_SCORES_FILE}")
        return None

    try:
        with open(QUALITY_SCORES_FILE) as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading quality scores: {e}")
        return None


def filter_drafts_by_quality(drafts, quality_results, conservative_mode=False):
    """Filter drafts based on quality scores."""
    if not quality_results or "results" not in quality_results:
        print("❌ No quality results available for filtering")
        return drafts, []

    passed_ids = set()
    failed_drafts = []
    quality_by_id = {}

    for result in quality_results["results"]:
        draft_id = result.get("draft_id")
        quality_by_id[draft_id] = result

        if result.get("passed", False):
            passed_ids.add(draft_id)
        else:
            failed_drafts.append({
                "draft_id": draft_id,
                "platform": result.get("platform"),
                "score": result.get("total_score"),
                "reasons": result.get("failure_reasons", [])
            })

    filtered_drafts = []

    for draft in drafts:
        draft_id = draft.get("id")

        if draft_id in quality_by_id:
            quality_info = quality_by_id[draft_id]
            draft["quality_score"] = quality_info.get("total_score")
            draft["quality_passed"] = quality_info.get("passed")
            draft["quality_reasons"] = quality_info.get("failure_reasons", [])
            draft["quality_scored_at"] = quality_info.get("scored_at")

        if conservative_mode:
            filtered_drafts.append(draft)
        elif draft_id in passed_ids:
            filtered_drafts.append(draft)

    return filtered_drafts, failed_drafts


def save_filtered_drafts(original_data, filtered_drafts, quality_results):
    """Save filtered drafts with quality metadata."""
    filtered_data = original_data.copy()
    filtered_data["drafts"] = filtered_drafts
    filtered_data["filtered_at"] = datetime.now(timezone.utc).isoformat()
    filtered_data["quality_gate_applied"] = True
    filtered_data["original_draft_count"] = original_data.get("draft_count", len(original_data.get("drafts", [])))
    filtered_data["filtered_draft_count"] = len(filtered_drafts)
    filtered_data["quality_threshold"] = quality_results.get("threshold")
    filtered_data["quality_pass_rate"] = quality_results.get("pass_rate")
    filtered_data["quality_average_score"] = quality_results.get("average_score")
    filtered_data["draft_count"] = len(filtered_drafts)

    DRAFTS_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DRAFTS_OUTPUT_FILE, 'w') as f:
        json.dump(filtered_data, f, indent=2)

    return filtered_data


def run_quality_gate(input_file=None, conservative_mode=False, verbose=False):
    """Run the complete quality gate process."""
    input_path = Path(input_file) if input_file else DRAFTS_INPUT_FILE

    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return None

    try:
        with open(input_path) as f:
            original_data = json.load(f)
        drafts = original_data.get("drafts", [])
        print(f"📊 Loaded {len(drafts)} drafts from {input_path}")
    except Exception as e:
        print(f"❌ Error loading drafts: {e}")
        return None

    if not drafts:
        print("❌ No drafts found in input file")
        return None

    if not run_quality_scorer(input_path, verbose):
        return None

    quality_results = load_quality_scores()
    if not quality_results:
        return None

    filtered_drafts, failed_drafts = filter_drafts_by_quality(drafts, quality_results, conservative_mode)
    filtered_data = save_filtered_drafts(original_data, filtered_drafts, quality_results)

    original_count = len(drafts)
    filtered_count = len(filtered_drafts)
    filtered_out = original_count - filtered_count

    print(f"\n{'='*60}")
    print(f"QUALITY GATE RESULTS")
    print(f"{'='*60}")
    print(f"Original drafts: {original_count}")
    print(f"Passed quality gate: {filtered_count}")
    print(f"Filtered out: {filtered_out}")
    print(f"Pass rate: {quality_results.get('pass_rate', 0):.1f}%")
    print(f"Average score: {quality_results.get('average_score', 0):.1f}/100")
    print(f"Threshold: {quality_results.get('threshold', 60)}/100")

    if conservative_mode:
        print(f"\n⚠️  CONSERVATIVE MODE: All drafts passed through with quality flags")

    platform_stats = {}
    for draft in filtered_drafts:
        platform = draft.get("platform", "unknown")
        platform_stats[platform] = platform_stats.get(platform, 0) + 1

    if platform_stats:
        print(f"\n📱 Filtered Drafts by Platform:")
        for platform, count in sorted(platform_stats.items()):
            print(f"  {platform}: {count}")

    if failed_drafts:
        failure_reasons = {}
        for failed in failed_drafts:
            for reason in failed["reasons"]:
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

        if failure_reasons:
            print(f"\n❌ Top Failure Reasons:")
            for reason, count in sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"  {reason}: {count} drafts")

    print(f"\n💾 Filtered drafts saved to: {DRAFTS_OUTPUT_FILE}")

    if filtered_count == 0:
        print("\n⚠️  WARNING: No drafts passed quality gate!")
        print("Consider lowering threshold or improving content quality.")
        return None

    return filtered_data


def main():
    parser = argparse.ArgumentParser(description="Filter content drafts through quality gate")
    parser.add_argument("--input", type=str, help="Input drafts JSON file")
    parser.add_argument("--conservative", action="store_true", help="Pass all drafts but add quality flags")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--threshold", type=float, help="Override quality threshold")
    args = parser.parse_args()

    if args.threshold:
        weights_file = DATA_DIR / "quality-scorer-weights.json"
        if weights_file.exists():
            try:
                with open(weights_file) as f:
                    weights_data = json.load(f)
                weights_data["threshold"] = args.threshold
                with open(weights_file, 'w') as f:
                    json.dump(weights_data, f, indent=2)
                print(f"🎯 Set threshold to {args.threshold}")
            except Exception as e:
                print(f"⚠ Could not update threshold: {e}")

    filtered_data = run_quality_gate(
        input_file=args.input,
        conservative_mode=args.conservative,
        verbose=args.verbose
    )

    if filtered_data:
        filtered_count = filtered_data.get("filtered_draft_count", 0)
        if filtered_count > 0:
            print(f"\n📤 Next: Pass filtered drafts to your publishing pipeline")
        else:
            print(f"\n⚠️  No drafts to publish. Consider:")
            print(f"  • Lowering threshold: --threshold 50")
            print(f"  • Conservative mode: --conservative")
            print(f"  • Improving content quality in transform step")


if __name__ == "__main__":
    main()
