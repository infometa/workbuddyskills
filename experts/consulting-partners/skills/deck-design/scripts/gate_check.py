#!/usr/bin/env python3
"""S4 machine-readable QA gate for generated PPTX files."""
import json
import os
import re
import sys
from pathlib import Path

ENGINE_BUG_WHITELIST = {
    "peer_font_inconsistency",
}
PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\[\s*Insert\b", re.IGNORECASE),
    re.compile(r"\blorem\b", re.IGNORECASE),
    re.compile(r"source\s*=\s*xx", re.IGNORECASE),
]


def _failure(message):
    detail = {
        "slide": None,
        "category": "gate_exception",
        "message": str(message)[:240],
        "shape": "",
    }
    return {
        "passed": False,
        "overall_score": 0,
        "error": str(message),
        "checklist": {
            "user_code_errors": 1,
            "engine_bug_errors": 0,
            "warnings": 0,
        },
        "verdict": "FAIL - QA gate could not complete",
        "user_code_error_detail": [detail],
        "engine_bug_detail": [],
        "warnings_detail": [],
    }


def _placeholder_errors(prs):
    errors = []
    for slide_num, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if not getattr(shape, "has_text_frame", False):
                continue
            text = shape.text_frame.text or ""
            stripped = text.strip()
            matched = any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS)
            matched = matched or stripped.lower() in {"xx", "xxx", "placeholder"}
            if matched:
                errors.append({
                    "slide": slide_num,
                    "category": "placeholder",
                    "message": f"Visible placeholder text: {stripped[:100]}",
                    "shape": getattr(shape, "name", ""),
                })
    return errors


def run_gate_check(pptx_path, project_dir):
    del project_dir
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if skill_dir not in sys.path:
        sys.path.insert(0, skill_dir)
    try:
        from mck_ppt.qa import PptQA
    except ImportError as exc:
        return _failure(f"Cannot import mck_ppt.qa: {exc}")
    if not os.path.exists(pptx_path):
        return _failure(f"File does not exist: {pptx_path}")

    try:
        qa = PptQA(pptx_path)
        report = qa.run()
    except Exception as exc:
        return _failure(f"PPT QA failed: {exc}")

    user_code_errors = []
    engine_bug_errors = []
    for item in report.errors:
        entry = {
            "slide": item.slide_num,
            "category": item.category,
            "message": item.message[:120],
            "shape": getattr(item, "shape_name", ""),
        }
        if item.category in ENGINE_BUG_WHITELIST:
            entry["whitelist_reason"] = "Known engine typography behavior"
            engine_bug_errors.append(entry)
        else:
            user_code_errors.append(entry)

    user_code_errors.extend(_placeholder_errors(qa.prs))
    warnings = [
        {
            "slide": item.slide_num,
            "category": item.category,
            "message": item.message[:100],
        }
        for item in report.warnings
    ]
    passed = not user_code_errors
    return {
        "passed": passed,
        "overall_score": report.overall_score,
        "pptx_path": str(pptx_path),
        "checklist": {
            "user_code_errors": len(user_code_errors),
            "engine_bug_errors": len(engine_bug_errors),
            "warnings": len(warnings),
        },
        "verdict": "PASS - ready for visual QC" if passed else f"FAIL - fix {len(user_code_errors)} user code error(s)",
        "user_code_error_detail": user_code_errors,
        "engine_bug_detail": engine_bug_errors,
        "warnings_detail": warnings,
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python gate_check.py <pptx_path> <project_dir>")
        sys.exit(1)
    pptx_path = sys.argv[1]
    project_dir = sys.argv[2]
    Path(project_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(project_dir, "gate_result.json")
    result = run_gate_check(pptx_path, project_dir)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)

    checklist = result["checklist"]
    print(f"[gate_check] Score: {result.get('overall_score', 'N/A')}")
    print(f"[gate_check] User code errors: {checklist['user_code_errors']}")
    print(f"[gate_check] Engine bug errors: {checklist['engine_bug_errors']}")
    print(f"[gate_check] Warnings: {checklist['warnings']}")
    print(f"[gate_check] Verdict: {result['verdict']}")
    print(f"[gate_check] Result: {output_path}")
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
