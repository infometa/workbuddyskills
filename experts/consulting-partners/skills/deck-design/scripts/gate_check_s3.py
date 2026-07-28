#!/usr/bin/env python3
"""S3 gate for the unified DeckSpec contract."""
import json
import os
import re
import sys
from pathlib import Path

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from mck_fusion import FusionDeck

STRUCTURAL_LAYOUTS = {"cover", "cover_slide", "section_divider", "closing", "appendix_title"}
ROLE_VALUES = {"Hero", "Supporting", "Transition"}
RHYTHM_VALUES = {"Peak", "Valley", "Transition"}
DENSITY_VALUES = {"low", "medium", "high"}
ENGINE_ALIASES = {
    "main": "main",
    "mck_ppt": "main",
    "supplemental": "supplemental",
    "mckinsey_pptx": "supplemental",
}
PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\[\s*Insert\b", re.IGNORECASE),
    re.compile(r"\blorem\b", re.IGNORECASE),
    re.compile(r"source\s*=\s*xx", re.IGNORECASE),
]
GENERIC_TITLES = {
    "市场概览",
    "竞争格局",
    "执行摘要",
    "核心发现",
    "主要发现",
    "下一步",
    "建议",
    "结论",
    "overview",
    "market overview",
    "competitive landscape",
    "next steps",
    "recommendation",
}


def issue(idx, layout, check, message):
    return {
        "slide_idx": idx,
        "layout": layout,
        "check": check,
        "message": message,
    }


def payload(slide):
    data = slide.get("data", {})
    return data if isinstance(data, dict) else {}


def walk_strings(value, path="slide"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from walk_strings(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_strings(item, f"{path}[{index}]")


def check_placeholders(slide, idx):
    layout = slide.get("layout", "")
    found = []
    for path, text in walk_strings(slide):
        stripped = text.strip()
        matched = any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS)
        matched = matched or stripped.lower() in {"xx", "xxx", "placeholder"}
        if matched:
            found.append(issue(idx, layout, "placeholder", f"Placeholder found at {path}: {text[:80]}"))
    return found


def check_semantics(slide, idx):
    layout = slide.get("layout", "")
    issues = []
    for field in ("role", "rhythm", "visual_role", "anti_pattern", "objective", "one_message"):
        value = slide.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(issue(idx, layout, "semantic_field", f"Missing non-empty field: {field}"))
    if slide.get("role") not in ROLE_VALUES:
        issues.append(issue(idx, layout, "role", f"role must be one of {sorted(ROLE_VALUES)}"))
    if slide.get("rhythm") not in RHYTHM_VALUES:
        issues.append(issue(idx, layout, "rhythm", f"rhythm must be one of {sorted(RHYTHM_VALUES)}"))
    density = slide.get("density")
    if density is not None and density not in DENSITY_VALUES:
        issues.append(issue(idx, layout, "density", f"density must be one of {sorted(DENSITY_VALUES)}"))
    return issues


def check_action_title(slide, idx):
    layout = slide.get("layout", "")
    title = slide.get("title", "")
    if not isinstance(title, str) or not title.strip():
        return [issue(idx, layout, "title_missing", "title must be a non-empty string")]
    if layout in STRUCTURAL_LAYOUTS:
        return []
    stripped = title.strip()
    compact = re.sub(r"\s+", "", stripped)
    has_cjk = bool(re.search(r"[\u4e00-\u9fff]", stripped))
    too_short = len(compact) < 12 if has_cjk else len(stripped.split()) < 5
    if too_short or stripped.lower() in GENERIC_TITLES or stripped.endswith((":", "：")):
        return [issue(
            idx,
            layout,
            "action_title",
            f"Content slide title must be a complete action title, got: {title}",
        )]
    return []


def check_evidence(slide, idx):
    layout = slide.get("layout", "")
    evidence = slide.get("evidence")
    if evidence is None:
        evidence = []
    if not isinstance(evidence, list):
        return [issue(idx, layout, "evidence", "evidence must be an array")]
    issues = []
    if layout not in STRUCTURAL_LAYOUTS and not evidence:
        issues.append(issue(idx, layout, "evidence_missing", "Content slide must reference at least one claim_id"))
    for pos, item in enumerate(evidence):
        if not isinstance(item, dict):
            issues.append(issue(idx, layout, "evidence", f"evidence[{pos}] must be an object"))
            continue
        claim_id = item.get("claim_id")
        grade = item.get("grade")
        if not isinstance(claim_id, str) or not claim_id.strip():
            issues.append(issue(idx, layout, "evidence", f"evidence[{pos}].claim_id is required"))
        if grade not in {"F", "I", "A", "E", "[F]", "[I]", "[A]", "[E]"}:
            issues.append(issue(idx, layout, "evidence", f"evidence[{pos}].grade must be [F]/[I]/[A]/[E]"))
    return issues


def check_source(slide, idx):
    layout = slide.get("layout", "")
    sources = slide.get("source")
    if sources is None:
        sources = []
    if not isinstance(sources, list):
        return [issue(idx, layout, "source", "source must be a structured array")]
    issues = []
    if layout not in STRUCTURAL_LAYOUTS and not sources:
        issues.append(issue(idx, layout, "source_missing", "Content slide must contain at least one source"))
    for pos, item in enumerate(sources):
        if not isinstance(item, dict):
            issues.append(issue(idx, layout, "source", f"source[{pos}] must be an object"))
            continue
        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            issues.append(issue(idx, layout, "source", f"source[{pos}].label is required"))
    return issues


def check_four_column(slide, idx):
    issues = []
    for pos, item in enumerate(payload(slide).get("items", [])):
        if not isinstance(item, (list, tuple)) or len(item) != 3:
            issues.append(issue(idx, "four_column", "api_format", f"items[{pos}] must be (num, title, desc)"))
    return issues


def check_executive_summary(slide, idx):
    issues = []
    for pos, item in enumerate(payload(slide).get("items", [])):
        if not isinstance(item, (list, tuple)) or len(item) != 3:
            issues.append(issue(idx, "executive_summary", "api_format", f"items[{pos}] must be (num, title, desc)"))
    return issues


def check_matrix_2x2(slide, idx):
    quadrants = payload(slide).get("quadrants", [])
    issues = []
    if len(quadrants) != 4:
        issues.append(issue(idx, "matrix_2x2", "count", f"matrix_2x2 requires 4 quadrants, got {len(quadrants)}"))
    for pos, item in enumerate(quadrants):
        if not isinstance(item, (list, tuple)) or len(item) != 3:
            issues.append(issue(idx, "matrix_2x2", "api_format", f"quadrants[{pos}] must contain 3 values"))
    return issues


def check_process_chevron(slide, idx):
    steps = payload(slide).get("steps", [])
    issues = []
    if len(steps) < 2 or len(steps) > 5:
        issues.append(issue(idx, "process_chevron", "count", f"process_chevron requires 2-5 steps, got {len(steps)}"))
    for pos, step in enumerate(steps):
        if not isinstance(step, (list, tuple)) or len(step) != 3:
            issues.append(issue(idx, "process_chevron", "api_format", f"steps[{pos}] must be (label, title, desc)"))
            continue
        if "\n" in str(step[0]):
            issues.append(issue(idx, "process_chevron", "label_newline", f"steps[{pos}] label cannot contain a newline"))
        if len(str(step[2])) > 50:
            issues.append(issue(idx, "process_chevron", "desc_length", f"steps[{pos}] desc exceeds 50 characters"))
    return issues


def check_donut_pie(slide, idx):
    segments = payload(slide).get("segments", [])
    if len(segments) > 6:
        return [issue(idx, slide.get("layout", ""), "count", f"chart supports at most 6 segments, got {len(segments)}")]
    return []


def check_grouped_bar(slide, idx):
    data = payload(slide)
    issues = []
    if len(data.get("categories", [])) > 6:
        issues.append(issue(idx, "grouped_bar", "count", "grouped_bar supports at most 6 categories"))
    if len(data.get("series", [])) > 3:
        issues.append(issue(idx, "grouped_bar", "count", "grouped_bar supports at most 3 series"))
    return issues


def check_timeline(slide, idx):
    milestones = payload(slide).get("milestones", [])
    if milestones and isinstance(milestones[-1], (list, tuple)) and len(str(milestones[-1][0])) > 6:
        return [issue(idx, "timeline", "last_label_length", "The final timeline label must not exceed 6 characters")]
    return []


LAYOUT_CHECKERS = {
    "four_column": [check_four_column],
    "executive_summary": [check_executive_summary],
    "matrix_2x2": [check_matrix_2x2],
    "process_chevron": [check_process_chevron],
    "donut": [check_donut_pie],
    "pie": [check_donut_pie],
    "grouped_bar": [check_grouped_bar],
    "timeline": [check_timeline],
}


def _load_content(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def run_gate_check_s3(content_json_path, project_dir):
    del project_dir
    if not os.path.exists(content_json_path):
        return {
            "passed": False,
            "total_slides": 0,
            "verdict": "FAIL - DeckSpec file is missing",
            "fail_items": [issue(None, None, "file_missing", f"File not found: {content_json_path}")],
            "pass_items": [],
        }
    try:
        content = _load_content(content_json_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "passed": False,
            "total_slides": 0,
            "verdict": "FAIL - DeckSpec cannot be parsed",
            "fail_items": [issue(None, None, "json_parse", str(exc))],
            "pass_items": [],
        }
    if not isinstance(content, dict):
        return {
            "passed": False,
            "total_slides": 0,
            "verdict": "FAIL - DeckSpec root must be an object",
            "fail_items": [issue(None, None, "root_type", "DeckSpec root must be an object")],
            "pass_items": [],
        }

    slides = content.get("slides")
    all_issues = []
    passed_slides = []
    if not isinstance(slides, list) or not slides:
        all_issues.append(issue(None, None, "slides_empty", "slides must be a non-empty array"))
        slides = []

    meta = content.get("meta")
    if not isinstance(meta, dict):
        all_issues.append(issue(None, None, "meta", "meta must be an object"))
        meta = {}
    declared_total = meta.get("total_slides")
    if declared_total != len(slides):
        all_issues.append(issue(None, None, "total_slides", f"meta.total_slides={declared_total} does not match slides={len(slides)}"))

    primary = set(FusionDeck.available_primary_layouts())
    supplemental = set(FusionDeck.available_fusion_layouts())

    for position, slide in enumerate(slides, 1):
        if not isinstance(slide, dict):
            all_issues.append(issue(position, None, "slide_type", "slide must be an object"))
            continue
        idx = slide.get("idx")
        layout = slide.get("layout", "")
        slide_issues = []
        if idx != position:
            slide_issues.append(issue(idx, layout, "idx_sequence", f"Expected idx {position}, got {idx}"))
        engine = ENGINE_ALIASES.get(slide.get("engine"))
        if engine is None:
            slide_issues.append(issue(idx, layout, "engine", f"Unknown engine: {slide.get('engine')}"))
        elif engine == "main" and layout not in primary:
            slide_issues.append(issue(idx, layout, "layout_unknown", f"Unknown primary layout: {layout}"))
        elif engine == "supplemental" and layout not in supplemental:
            slide_issues.append(issue(idx, layout, "layout_unknown", f"Unknown supplemental layout: {layout}"))
        if not isinstance(slide.get("data"), dict):
            slide_issues.append(issue(idx, layout, "data", "data must be an object"))

        slide_issues.extend(check_semantics(slide, idx))
        slide_issues.extend(check_action_title(slide, idx))
        slide_issues.extend(check_evidence(slide, idx))
        slide_issues.extend(check_source(slide, idx))
        slide_issues.extend(check_placeholders(slide, idx))
        for checker in LAYOUT_CHECKERS.get(layout, []):
            slide_issues.extend(checker(slide, idx))

        if slide_issues:
            all_issues.extend(slide_issues)
        else:
            passed_slides.append({"slide_idx": idx, "layout": layout, "status": "ok"})

    passed = not all_issues
    return {
        "passed": passed,
        "total_slides": len(slides),
        "verdict": "PASS - ready for build" if passed else f"FAIL - fix {len(all_issues)} issue(s)",
        "fail_items": all_issues,
        "pass_items": passed_slides,
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python gate_check_s3.py <deck_spec.json> <project_dir>")
        sys.exit(1)
    spec_path = sys.argv[1]
    project_dir = sys.argv[2]
    Path(project_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(project_dir, "gate_s3.json")
    result = run_gate_check_s3(spec_path, project_dir)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(f"[gate_check_s3] Slides: {result['total_slides']}")
    print(f"[gate_check_s3] Fail items: {len(result['fail_items'])}")
    print(f"[gate_check_s3] Verdict: {result['verdict']}")
    print(f"[gate_check_s3] Result: {output_path}")
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
