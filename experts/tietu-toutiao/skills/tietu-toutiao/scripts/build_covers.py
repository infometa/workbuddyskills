#!/usr/bin/env python3
"""One-shot pipeline: validate content-state (v1/v2) and render all cover templates.

Replaces the error-prone sequence of running validate_content_state.py,
layout_engine.py (xN) and render_cover.py (xN) by hand. Exits non-zero unless
every requested template rendered successfully -- no pseudo-success.

v2 hard gate: a content-state.v2 with an empty or failed editorial_log.review
is refused -- the self-review phase must pass before anything is rendered.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from validate_content_state import check_image_bounds, validate_state
    from layout_engine import ALLOWED_TYPES, build_layout
    from render_cover import render_cover
except ImportError:
    from scripts.validate_content_state import check_image_bounds, validate_state
    from scripts.layout_engine import ALLOWED_TYPES, build_layout
    from scripts.render_cover import render_cover

DEFAULT_TYPES = ("authoritative", "visual", "digest", "synthesis")


def _review_blocker(state: dict) -> str | None:
    """Return an error message when a v2 state has not passed self-review."""
    if state.get("schema_version") != "content-state.v2":
        return None
    log = state.get("editorial_log")
    if not isinstance(log, dict):
        return "editorial_log missing; content-state.v2 requires editorial_log.review before rendering"
    review = log.get("review")
    if not isinstance(review, dict) or review.get("passed") is not True:
        return "editorial_log.review missing or not passed; the self-review phase must approve rendering"
    return None


def _archive_editorial_log(state: dict, out_dir: Path, template_types: tuple[str, ...]) -> Path:
    """Append one audit line per successful build to editorial_log.jsonl (W8).

    Local-first: plain JSONL in the output directory, no connector involved.
    """
    log = state.get("editorial_log") if isinstance(state.get("editorial_log"), dict) else {}
    record = {
        "archived_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "revision_id": state.get("revision_id"),
        "schema_version": state.get("schema_version"),
        "templates": list(template_types),
        "narrative": log.get("narrative"),
        "model": log.get("model"),
        "excluded": log.get("excluded"),
        "review_passed": isinstance(log.get("review"), dict) and log["review"].get("passed") is True,
    }
    path = out_dir / "editorial_log.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def build_all(
    state_path: Path,
    out_dir: Path,
    types: tuple[str, ...] = DEFAULT_TYPES,
    font_path: str | None = None,
) -> tuple[list[Path], list[str]]:
    """Validate state, then build layout + render cover for each template type.

    Returns (rendered_cover_paths, errors). Writes layout_<type>.json and
    cover_<type>_<revision_id>.png into out_dir, plus editorial_log.jsonl.
    """
    state_path = state_path.resolve()
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [], [f"state file not found: {state_path}"]
    except json.JSONDecodeError as exc:
        return [], [f"invalid state JSON: {exc}"]

    errors = validate_state(state, state_path.parent, check_files=True)
    if not errors:
        errors = check_image_bounds(state, state_path.parent)
    if not errors:
        blocker = _review_blocker(state)
        if blocker:
            errors.append(blocker)
    if errors:
        return [], ["content-state invalid: " + "; ".join(errors)]

    revision_id = state["revision_id"]
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    rendered: list[Path] = []
    for template_type in types:
        if template_type not in ALLOWED_TYPES:
            errors.append(f"unknown template type: {template_type}")
            continue
        layout_path = out_dir / f"layout_{template_type}.json"
        cover_path = out_dir / f"cover_{template_type}_{revision_id}.png"
        try:
            layout = build_layout(state, state_path, template_type)
            layout_path.write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8")
            render_cover(layout_path, cover_path, font_path)
        except (OSError, RuntimeError, ValueError) as exc:
            errors.append(f"{template_type}: {exc}")
            continue
        rendered.append(cover_path)
    if not errors:
        try:
            _archive_editorial_log(state, out_dir, types)
        except OSError as exc:
            errors.append(f"editorial log archive failed: {exc}")
    return rendered, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate state and render all Tietu Toutiao covers")
    parser.add_argument("--state", required=True, help="content-state JSON path (v1 or v2)")
    parser.add_argument("--out-dir", help="output directory (default: state file directory)")
    parser.add_argument("--types", help="comma-separated template subset (default: all four)")
    parser.add_argument("--font-path", help="explicit CJK font file path")
    args = parser.parse_args()

    state_path = Path(args.state)
    out_dir = Path(args.out_dir) if args.out_dir else state_path.resolve().parent
    types = tuple(t.strip() for t in args.types.split(",") if t.strip()) if args.types else DEFAULT_TYPES

    rendered, errors = build_all(state_path, out_dir, types, args.font_path)
    for cover in rendered:
        print(f"[OK] cover generated: {cover}")
    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        print(f"[FAIL] {len(rendered)}/{len(types)} cover(s) rendered; refusing to claim success")
        return 1
    print(f"[OK] all {len(rendered)} cover(s) rendered from one validated state")
    return 0


if __name__ == "__main__":
    sys.exit(main())
