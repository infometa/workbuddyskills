#!/usr/bin/env python3
"""Validate the versioned content-state contract (v1 + v2) used by Tietu Toutiao."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ALLOWED_TEMPLATES = {"authoritative", "visual", "digest", "synthesis"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
CONFIDENCE_FLOOR = 0.85


def _resolve_path(value: str, base_dir: Path | None) -> Path:
    path = Path(value)
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    return path.resolve()


def _check_confidence(value: Any, name: str, errors: list[str]) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
        errors.append(f"{name}.confidence must be a number between 0 and 1")


def _check_text_field(value: Any, name: str, errors: list[str], allow_empty: bool = False) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return
    text_key = "original" if name == "headline" else "text"
    text = value.get(text_key)
    if not isinstance(text, str) or (not allow_empty and not text.strip()):
        errors.append(f"{name}.{text_key} must be a non-empty string")
    _check_confidence(value.get("confidence"), name, errors)
    if not isinstance(value.get("confirmed"), bool):
        errors.append(f"{name}.confirmed must be boolean")


def _check_confirmed_confidence(name: str, value: Any, errors: list[str]) -> None:
    """A low-confidence key field must not be marked confirmed (human-review rule)."""
    if not isinstance(value, dict):
        return
    confidence = value.get("confidence")
    if (
        isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and confidence < CONFIDENCE_FLOOR
        and value.get("confirmed") is True
    ):
        errors.append(
            f"{name}: confidence {confidence} < {CONFIDENCE_FLOOR} must stay confirmed=false "
            f"until a human reviews it"
        )


def _check_rect(value: Any, name: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return
    for key in ("x", "y", "width", "height"):
        number = value.get(key)
        if not isinstance(number, (int, float)) or isinstance(number, bool):
            errors.append(f"{name}.{key} must be numeric")
        elif key in ("x", "y") and number < 0:
            errors.append(f"{name}.{key} must be >= 0")
        elif key in ("width", "height") and number <= 0:
            errors.append(f"{name}.{key} must be > 0")


def _check_point(value: Any, name: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return
    for key in ("x", "y"):
        number = value.get(key)
        if not isinstance(number, (int, float)) or isinstance(number, bool) or not 0 <= number <= 1:
            errors.append(f"{name}.{key} must be numeric between 0 and 1")


def _check_bbox(value: Any, name: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return
    for key in ("x", "y", "width", "height"):
        number = value.get(key)
        if not isinstance(number, (int, float)) or isinstance(number, bool):
            errors.append(f"{name}.{key} must be numeric")
            return
        elif key in ("x", "y") and number < 0:
            errors.append(f"{name}.{key} must be >= 0")
        elif key in ("width", "height") and number <= 0:
            errors.append(f"{name}.{key} must be > 0")


def _check_source_manifest(manifest: Any, errors: list[str]) -> None:
    if not isinstance(manifest, dict):
        errors.append("source_manifest must be an object")
        return
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("source_manifest.sources must be a non-empty array")
        return
    seen: set[str] = set()
    for index, source in enumerate(sources):
        where = f"source_manifest.sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{where} must be an object")
            continue
        file_value = source.get("file")
        if not isinstance(file_value, str) or not file_value.strip():
            errors.append(f"{where}.file must be a non-empty string")
        sha = source.get("sha256")
        if not isinstance(sha, str) or not SHA256_RE.match(sha):
            errors.append(f"{where}.sha256 must be a 64-character hex digest")
        if isinstance(file_value, str) and file_value in seen:
            errors.append(f"{where}.file duplicates an earlier source entry: {file_value}")
        if isinstance(file_value, str):
            seen.add(file_value)
        pages = source.get("pages_used")
        if pages is not None:
            if not isinstance(pages, list) or any(
                isinstance(page, bool) or not isinstance(page, int) or page < 1 for page in pages
            ):
                errors.append(f"{where}.pages_used must be an array of positive integers")
        if "page_label" in source and not isinstance(source.get("page_label"), str):
            errors.append(f"{where}.page_label must be a string")
    if not isinstance(manifest.get("ingested_at"), str) or not manifest["ingested_at"].strip():
        errors.append("source_manifest.ingested_at must be a non-empty string")
    if not isinstance(manifest.get("ingest_method"), str) or not manifest["ingest_method"].strip():
        errors.append("source_manifest.ingest_method must be a non-empty string")


def _check_layout_analysis(analysis: Any, errors: list[str]) -> None:
    if not isinstance(analysis, dict):
        errors.append("layout_analysis must be an object")
        return
    for key in ("masthead_bbox", "date_bbox"):
        if key in analysis:
            _check_bbox(analysis[key], f"layout_analysis.{key}", errors)
    regions = analysis.get("photo_regions")
    if not isinstance(regions, list):
        errors.append("layout_analysis.photo_regions must be an array")
    else:
        for index, region in enumerate(regions):
            where = f"layout_analysis.photo_regions[{index}]"
            if not isinstance(region, dict):
                errors.append(f"{where} must be an object")
                continue
            _check_bbox(region.get("bbox"), f"{where}.bbox", errors)
            if not isinstance(region.get("kind"), str) or not region["kind"].strip():
                errors.append(f"{where}.kind must be a non-empty string")
            if "subject" in region and not isinstance(region.get("subject"), str):
                errors.append(f"{where}.subject must be a string")
            _check_confidence(region.get("confidence"), where, errors)
    text_regions = analysis.get("text_regions")
    if text_regions is not None:
        if not isinstance(text_regions, list):
            errors.append("layout_analysis.text_regions must be an array")
        else:
            for index, region in enumerate(text_regions):
                where = f"layout_analysis.text_regions[{index}]"
                if not isinstance(region, dict):
                    errors.append(f"{where} must be an object")
                    continue
                _check_bbox(region.get("bbox"), f"{where}.bbox", errors)
                if not isinstance(region.get("kind"), str) or not region["kind"].strip():
                    errors.append(f"{where}.kind must be a non-empty string")
                _check_confidence(region.get("confidence"), where, errors)
    if not isinstance(analysis.get("analyzer"), str) or not analysis["analyzer"].strip():
        errors.append("layout_analysis.analyzer must be a non-empty string")
    if not isinstance(analysis.get("confirmed"), bool):
        errors.append("layout_analysis.confirmed must be boolean")


def _check_item(item: Any, index: int, errors: list[str], ids: set[str]) -> None:
    where = f"items[{index}]"
    if not isinstance(item, dict):
        errors.append(f"{where} must be an object")
        return
    item_id = item.get("id")
    if not isinstance(item_id, str) or not item_id.strip() or any(ch in item_id for ch in "/\\"):
        errors.append(f"{where}.id must be a non-empty path-safe string")
    elif item_id in ids:
        errors.append(f"{where}.id duplicates an earlier item: {item_id}")
    else:
        ids.add(item_id)
    if not isinstance(item.get("type"), str) or not item["type"].strip():
        errors.append(f"{where}.type must be a non-empty string")
    if not isinstance(item.get("headline"), str) or not item["headline"].strip():
        errors.append(f"{where}.headline must be a non-empty string")
    summary = item.get("summary")
    if summary is not None and not isinstance(summary, str):
        errors.append(f"{where}.summary must be a string")
    if "source_page" in item and not isinstance(item.get("source_page"), str):
        errors.append(f"{where}.source_page must be a string")
    ref = item.get("photo_region_ref")
    if ref is not None and (isinstance(ref, bool) or not isinstance(ref, int) or ref < 0):
        errors.append(f"{where}.photo_region_ref must be a non-negative integer or null")
    weight = item.get("weight")
    if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not 0 <= weight <= 1:
        errors.append(f"{where}.weight must be a number between 0 and 1")
    scores = item.get("scores")
    if scores is not None:
        if not isinstance(scores, dict):
            errors.append(f"{where}.scores must be an object")
        else:
            for key, value in scores.items():
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    errors.append(f"{where}.scores.{key} must be a number between 0 and 1")
    if not isinstance(item.get("selected"), bool):
        errors.append(f"{where}.selected must be boolean")


def _check_editorial_log(log: Any, errors: list[str]) -> None:
    if not isinstance(log, dict):
        errors.append("editorial_log must be an object")
        return
    if not isinstance(log.get("narrative"), str) or not log["narrative"].strip():
        errors.append("editorial_log.narrative must be a non-empty string")
    excluded = log.get("excluded")
    if not isinstance(excluded, list):
        errors.append("editorial_log.excluded must be an array")
    else:
        for index, entry in enumerate(excluded):
            where = f"editorial_log.excluded[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{where} must be an object")
                continue
            if not isinstance(entry.get("id"), str) or not entry["id"].strip():
                errors.append(f"{where}.id must be a non-empty string")
            if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
                errors.append(f"{where}.reason must be a non-empty string")
    if not isinstance(log.get("model"), str) or not log["model"].strip():
        errors.append("editorial_log.model must be a non-empty string")
    if not isinstance(log.get("generated_at"), str) or not log["generated_at"].strip():
        errors.append("editorial_log.generated_at must be a non-empty string")
    review = log.get("review")
    if review is not None:
        _check_review(review, errors)


def _check_review(review: Any, errors: list[str]) -> None:
    if not isinstance(review, dict):
        errors.append("editorial_log.review must be an object")
        return
    if not isinstance(review.get("passed"), bool):
        errors.append("editorial_log.review.passed must be boolean")
    checks = review.get("checks")
    if not isinstance(checks, list):
        errors.append("editorial_log.review.checks must be an array")
        return
    for index, check in enumerate(checks):
        where = f"editorial_log.review.checks[{index}]"
        if not isinstance(check, dict):
            errors.append(f"{where} must be an object")
            continue
        if not isinstance(check.get("item"), str) or not check["item"].strip():
            errors.append(f"{where}.item must be a non-empty string")
        if not isinstance(check.get("ok"), bool):
            errors.append(f"{where}.ok must be boolean")
        if "note" in check and not isinstance(check.get("note"), str):
            errors.append(f"{where}.note must be a string")


def validate_state(state: Any, base_dir: Path | None = None, check_files: bool = True) -> list[str]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return ["state must be a JSON object"]

    schema_version = state.get("schema_version")
    is_v2 = schema_version == "content-state.v2"
    if schema_version not in ("content-state.v1", "content-state.v2"):
        errors.append("schema_version must equal content-state.v1 or content-state.v2")

    required = [
        "schema_version",
        "source_image",
        "masthead",
        "date",
        "headline",
        "primary_photo",
        "selected_template",
        "locked_fields",
        "rejected_styles",
        "revision_id",
        "parent_revision_id",
    ]
    for key in required:
        if key not in state:
            errors.append(f"missing required field: {key}")

    source_image = state.get("source_image")
    if not isinstance(source_image, str) or not source_image.strip():
        errors.append("source_image must be a non-empty string")
    else:
        source_path = _resolve_path(source_image, base_dir)
        if source_path.suffix.lower() not in IMAGE_EXTENSIONS:
            errors.append("source_image must use JPG, JPEG, or PNG")
        if check_files and not source_path.is_file():
            errors.append(f"source_image does not exist: {source_path}")

    _check_text_field(state.get("masthead"), "masthead", errors)
    _check_text_field(state.get("date"), "date", errors)
    _check_text_field(state.get("headline"), "headline", errors)

    sub_headline = state.get("sub_headline")
    if sub_headline is not None:
        _check_text_field(sub_headline, "sub_headline", errors, allow_empty=True)

    photo = state.get("primary_photo")
    if not isinstance(photo, dict):
        errors.append("primary_photo must be an object")
    else:
        photo_path = photo.get("path")
        if not isinstance(photo_path, str):
            errors.append("primary_photo.path must be a string")
        elif photo_path.strip():
            path = _resolve_path(photo_path, base_dir)
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                errors.append("primary_photo.path must use JPG, JPEG, or PNG")
            if check_files and not path.is_file():
                errors.append(f"primary_photo.path does not exist: {path}")
        _check_rect(photo.get("crop"), "primary_photo.crop", errors)
        _check_point(photo.get("focal_point"), "primary_photo.focal_point", errors)
        _check_confidence(photo.get("confidence"), "primary_photo", errors)
        if not isinstance(photo.get("confirmed"), bool):
            errors.append("primary_photo.confirmed must be boolean")
        if photo_path and not photo.get("confirmed"):
            errors.append("primary_photo with a path must be confirmed before rendering")

    selected = state.get("selected_template")
    if selected is not None and selected not in ALLOWED_TEMPLATES:
        errors.append("selected_template must be authoritative, visual, digest, synthesis, or null")

    for key in ("locked_fields", "rejected_styles"):
        value = state.get(key)
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            errors.append(f"{key} must be an array of non-empty strings")

    revision_id = state.get("revision_id")
    if not isinstance(revision_id, str) or not revision_id.strip() or any(ch in revision_id for ch in "/\\"):
        errors.append("revision_id must be a non-empty path-safe string")
    parent = state.get("parent_revision_id")
    if parent is not None and (not isinstance(parent, str) or not parent.strip()):
        errors.append("parent_revision_id must be a non-empty string or null")

    if is_v2:
        for key in ("source_manifest", "layout_analysis", "items", "editorial_log"):
            if key not in state:
                errors.append(f"missing required field (v2): {key}")
        if "source_manifest" in state:
            _check_source_manifest(state["source_manifest"], errors)
        if "layout_analysis" in state:
            _check_layout_analysis(state["layout_analysis"], errors)
        if "items" in state:
            items = state["items"]
            if not isinstance(items, list):
                errors.append("items must be an array")
            else:
                ids: set[str] = set()
                for index, item in enumerate(items):
                    _check_item(item, index, errors, ids)
        if "editorial_log" in state:
            _check_editorial_log(state["editorial_log"], errors)
        for name in ("masthead", "date", "headline"):
            _check_confirmed_confidence(name, state.get(name), errors)
    elif "source_manifest" in state or "layout_analysis" in state or "items" in state or "editorial_log" in state:
        # v2-only fields on a v1 document are invalid there; move up to v2 instead.
        for key in ("source_manifest", "layout_analysis", "items", "editorial_log"):
            if key in state:
                errors.append(f"{key} requires schema_version content-state.v2")

    return errors


def check_image_bounds(state: Any, base_dir: Path | None = None) -> list[str]:
    """Verify images are readable and primary_photo.crop fits inside the real image.

    Requires Pillow. Never silently skips: if Pillow is missing, that is an error.
    """
    try:
        from PIL import Image
    except ImportError:
        return ["--check-image-bounds requires Pillow (install requirements.txt)"]

    errors: list[str] = []
    if not isinstance(state, dict):
        return ["state must be a JSON object"]

    source_image = state.get("source_image")
    if isinstance(source_image, str) and source_image.strip():
        source_path = _resolve_path(source_image, base_dir)
        try:
            with Image.open(source_path) as image:
                image.verify()
        except Exception as exc:  # noqa: BLE001 - report any unreadable image
            errors.append(f"source_image is not a readable image: {source_path} ({exc})")

    photo = state.get("primary_photo")
    if isinstance(photo, dict):
        photo_path_value = photo.get("path")
        crop = photo.get("crop")
        if isinstance(photo_path_value, str) and photo_path_value.strip() and isinstance(crop, dict):
            path = _resolve_path(photo_path_value, base_dir)
            try:
                with Image.open(path) as image:
                    width, height = image.size
            except Exception as exc:  # noqa: BLE001
                errors.append(f"primary_photo.path is not a readable image: {path} ({exc})")
            else:
                try:
                    right = float(crop.get("x")) + float(crop.get("width"))
                    bottom = float(crop.get("y")) + float(crop.get("height"))
                except (TypeError, ValueError):
                    right = bottom = None
                if right is None or bottom is None:
                    errors.append("primary_photo.crop must contain numeric x, y, width, height")
                elif right > width or bottom > height:
                    errors.append(
                        f"primary_photo.crop exceeds image bounds: crop ends at "
                        f"({right}, {bottom}) but image is {width}x{height}"
                    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Tietu Toutiao content-state (v1/v2)")
    parser.add_argument("--input", required=True, help="content-state JSON path (v1 or v2)")
    parser.add_argument("--allow-missing-files", action="store_true", help="only validate structure")
    parser.add_argument("--check-image-bounds", action="store_true", help="also verify crop fits inside real image dimensions")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    try:
        state = json.loads(input_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[ERROR] state file not found: {input_path}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"[ERROR] invalid JSON: {exc}")
        return 2

    errors = validate_state(state, input_path.parent, check_files=not args.allow_missing_files)
    if args.check_image_bounds and not errors:
        errors = check_image_bounds(state, input_path.parent)
    if errors:
        print(f"[ERROR] {state.get('schema_version', 'content-state')} invalid ({len(errors)} issue(s))")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"[OK] {state.get('schema_version')} valid: {input_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
