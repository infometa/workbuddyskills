#!/usr/bin/env python3
"""Fail-closed permission gate over one immutable delivery selection."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from artifact_metadata import parse_frontmatter
from common import (
    assert_project_input,
    assert_project_root,
    file_sha256,
    load_schema,
    read_csv,
    safe_project_path,
    schema_path,
    write_json_atomic,
    write_text_atomic,
)
from schema_validation import validate_instance

ID_PATTERNS = {
    "source_ids": re.compile(r"\bSRC-[A-Z0-9]{12,64}\b"),
    "story_ids": re.compile(r"\bSTY-[A-Z0-9][A-Z0-9_-]{2,63}\b"),
    "answer_ids": re.compile(r"\bANS-[A-Z0-9][A-Z0-9_-]{2,63}\b"),
    "person_ids": re.compile(r"\bPER-[A-Z0-9][A-Z0-9_-]{2,63}\b"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--scope", choices=["manuscript", "public"], required=True)
    parser.add_argument("--selection", default="13_导出成果/delivery-selection.json")
    args = parser.parse_args()
    project = assert_project_root(args.project_dir)
    errors: list[str] = []
    selection_path = assert_project_input(project, args.selection, ["13_导出成果"])
    try:
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"invalid delivery selection: {exc}")
    errors.extend(validate_instance(selection, load_schema(schema_path("delivery-selection.schema.json")), "delivery-selection"))
    if selection.get("scope") != args.scope:
        errors.append("delivery selection scope differs from requested gate")
    if not selection.get("outputs"):
        errors.append("delivery selection has no outputs")

    discovered = {field: set() for field in ID_PATTERNS}
    for output in selection.get("outputs", []):
        try:
            path = assert_project_input(project, output.get("path", ""), ["08_故事卡", "10_大纲与章节", "13_导出成果"])
            if file_sha256(path) != output.get("sha256"):
                errors.append(f"selected output changed after selection: {output.get('path')}")
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                text = ""
            for field, pattern in ID_PATTERNS.items():
                discovered[field].update(pattern.findall(text))
        except SystemExit:
            errors.append(f"selected output is unsafe or missing: {output.get('path')}")
    for field in discovered:
        undeclared = sorted(discovered[field] - set(selection.get(field, [])))
        if undeclared:
            errors.append(f"selected outputs contain undeclared {field}: {undeclared}")

    sources = {row.get("source_id", ""): row for row in read_csv(safe_project_path(project, "02_素材账/source-ledger.csv"), required=True)}
    people = {row.get("person_id", ""): row for row in read_csv(safe_project_path(project, "03_人物与关系/person-ledger.csv"), required=True)}
    answers = {row.get("answer_id", ""): row for row in read_csv(safe_project_path(project, "07_问题与回答/answer-ledger.csv"), required=True)}
    story_metadata = {}
    story_dir = safe_project_path(project, "08_故事卡")
    for path in story_dir.glob("*.md") if story_dir.exists() else []:
        try:
            metadata, _ = parse_frontmatter(path)
            story_metadata[str(metadata.get("story_id", ""))] = metadata
        except Exception as exc:
            errors.append(f"invalid story card during permission gate: {path.name}: {exc}")

    selected_objects = {
        **{value: "source" for value in selection.get("source_ids", [])},
        **{value: "story" for value in selection.get("story_ids", [])},
        **{value: "answer" for value in selection.get("answer_ids", [])},
        **{value: "person" for value in selection.get("person_ids", [])},
    }
    known = {"source": sources, "story": story_metadata, "answer": answers, "person": people}
    for object_id, object_type in selected_objects.items():
        if object_id not in known[object_type]:
            errors.append(f"selected {object_type} does not exist: {object_id}")

    consent_rows = read_csv(safe_project_path(project, "11_隐私与授权/consent-ledger.csv"), required=True)
    consents: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in consent_rows:
        consents[row.get("object_id", "")].append(row)
    anonymized = set(selection.get("anonymized_object_ids", []))
    sensitive_reviewed = set(selection.get("sensitive_reviewed_object_ids", []))

    for object_id, object_type in selected_objects.items():
        rows = consents.get(object_id, [])
        if not rows:
            errors.append(f"{object_id}: no explicit consent record")
            continue
        states = {row.get("status", "") for row in rows}
        if states & {"pending", "withdrawn", "disputed"}:
            errors.append(f"{object_id}: restrictive consent state {sorted(states)}")
        if args.scope == "public":
            if any(row.get("public_use") != "yes" or row.get("family_visibility") != "public" for row in rows):
                errors.append(f"{object_id}: every applicable consent must explicitly allow public use")
            if any(row.get("status") not in {"public_allowed", "anonymized"} for row in rows):
                errors.append(f"{object_id}: consent status does not authorize public use")
        else:
            if any(row.get("manuscript_use") != "yes" for row in rows):
                errors.append(f"{object_id}: every applicable consent must explicitly allow manuscript use")
            if any(row.get("status") not in {"manuscript_allowed", "public_allowed", "anonymized"} for row in rows):
                errors.append(f"{object_id}: consent status does not authorize manuscript use")
        if any(row.get("anonymize") == "required" for row in rows) and object_id not in anonymized:
            errors.append(f"{object_id}: anonymization is required but not attested in the selection")
        if any(row.get("sensitive") == "yes" for row in rows) and object_id not in sensitive_reviewed:
            errors.append(f"{object_id}: sensitive-content review is missing")

        if object_type == "source":
            source = sources.get(object_id, {})
            if source.get("status") in {"unreadable", "pending"}:
                errors.append(f"{object_id}: source status blocks delivery")
            if args.scope == "public" and source.get("public_use") != "yes":
                errors.append(f"{object_id}: source ledger does not allow public use")
            if args.scope == "manuscript" and source.get("manuscript_use") != "yes":
                errors.append(f"{object_id}: source ledger does not allow manuscript use")
        elif object_type == "story":
            story = story_metadata.get(object_id, {})
            if story.get("status") in {"withdrawn", "disputed", "candidate"}:
                errors.append(f"{object_id}: story is not confirmed for delivery")
            if args.scope == "public" and story.get("visibility") != "public":
                errors.append(f"{object_id}: story visibility is not public")
            if story.get("manuscript_use") != "yes":
                errors.append(f"{object_id}: story is not approved for manuscript use")
        elif object_type == "answer" and answers.get(object_id, {}).get("status") in {"draft", "withdrawn"}:
            errors.append(f"{object_id}: answer status blocks delivery")

    result = {
        "schemaVersion": "2.0",
        "valid": not errors,
        "scope": args.scope,
        "selectionId": selection.get("selection_id", ""),
        "selectionSha256": file_sha256(selection_path),
        "checkedObjects": len(selected_objects),
        "checkedOutputs": len(selection.get("outputs", [])),
        "errors": errors,
    }
    report_json = safe_project_path(project, "13_导出成果/permission-validation.json")
    report_md = safe_project_path(project, "13_导出成果/permission-validation.md")
    write_json_atomic(report_json, result, project_root=project)
    markdown = (
        "# 权限校验报告\n\n"
        + f"结论：{'通过' if result['valid'] else '未通过'}\n"
        + f"范围：{args.scope}\n"
        + f"选择：{result['selectionId']}\n"
        + f"输出：{result['checkedOutputs']}\n"
        + f"对象：{result['checkedObjects']}\n\n"
        + "## 阻断项\n"
        + ("\n".join(f"- {item}" for item in errors) or "- 无")
        + "\n"
    )
    write_text_atomic(report_md, markdown, project_root=project)
    print(f"permission validation: {'PASS' if result['valid'] else 'FAIL'} -> {report_md}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
