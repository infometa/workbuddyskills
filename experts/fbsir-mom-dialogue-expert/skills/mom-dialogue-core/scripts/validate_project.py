#!/usr/bin/env python3
"""Schema-driven project, identifier, foreign-key, and receipt validation."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from artifact_metadata import parse_frontmatter
from common import (
    assert_project_root,
    file_sha256,
    is_reparse_point,
    load_schema,
    parse_json_array,
    read_csv,
    safe_project_path,
    schema_path,
    unwrap_csv_value,
    write_json_atomic,
    write_text_atomic,
)
from schema_validation import csv_row_to_instance, validate_instance
from source_registry import read_registry
from source_transaction import load_scan_bundle, source_key


def load_catalog() -> dict:
    path = schema_path("schema-catalog.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != "2.0":
        raise SystemExit(f"unsupported schema catalog: {path}")
    return data


def validate_csv_ledger(
    project: Path,
    entry: dict,
    errors: list[str],
) -> list[dict[str, str]]:
    path = safe_project_path(project, entry["path"])
    if not path.exists():
        if entry.get("required"):
            errors.append(f"missing required ledger: {entry['path']}")
        return []
    schema = load_schema(schema_path(entry["schema"]))
    if schema.get("x-schema-version") != "2.0":
        errors.append(f"{entry['schema']}: unsupported schema version")
    expected_header = list(schema["properties"])
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            header = reader.fieldnames or []
            rows = [{key: unwrap_csv_value(value or "") for key, value in row.items()} for row in reader]
    except Exception as exc:
        errors.append(f"{entry['path']}: unreadable CSV: {exc}")
        return []
    if header != expected_header:
        errors.append(f"{entry['path']}: header mismatch")
    id_field = entry.get("idField")
    seen: set[str] = set()
    required = schema.get("required", [])
    for index, row in enumerate(rows, 2):
        for field in required:
            if not row.get(field, "").strip():
                errors.append(f"{entry['path']}:{index}: missing required {field}")
        instance, parse_errors = csv_row_to_instance(row, schema, f"{entry['path']}:{index}")
        errors.extend(parse_errors)
        errors.extend(validate_instance(instance, schema, f"{entry['path']}:{index}"))
        if id_field:
            value = row.get(id_field, "")
            if value and value in seen:
                errors.append(f"{entry['path']}:{index}: duplicate {id_field} {value}")
            seen.add(value)
    return rows


def array_values(row: dict[str, str], field: str, label: str, errors: list[str]) -> list[str]:
    try:
        return parse_json_array(row.get(field, ""), label)
    except SystemExit:
        errors.append(f"{label}: invalid JSON array")
        return []


def require_members(values: list[str], allowed: set[str], label: str, errors: list[str]) -> None:
    for value in values:
        if value not in allowed:
            errors.append(f"{label}: unknown reference {value}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--allow-empty", action="store_true", help="Allow a newly initialized project with no committed sources")
    parser.add_argument("--fail-on-warnings", action="store_true")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()
    project = assert_project_root(args.project_dir)
    errors: list[str] = []
    warnings: list[str] = []

    marker_path = safe_project_path(project, ".mom-dialogue-project.json", must_exist=True)
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    errors.extend(validate_instance(marker, load_schema(schema_path("project.schema.json")), "project"))

    registry = read_registry(project)
    root_schema = load_schema(schema_path("source-root.schema.json"))
    root_ids: set[str] = set()
    for index, root_record in enumerate(registry.get("roots", [])):
        errors.extend(validate_instance(root_record, root_schema, f"source-roots[{index}]"))
        root_ids.add(root_record.get("root_id", ""))
    if set(marker.get("source_roots_registered", [])) != root_ids:
        errors.append("project marker and source-roots.json root sets differ")

    catalog = load_catalog()
    ledgers = {entry["path"]: validate_csv_ledger(project, entry, errors) for entry in catalog["ledgers"]}
    sources = ledgers.get("02_素材账/source-ledger.csv", [])
    if not sources and not args.allow_empty:
        errors.append("canonical source ledger is empty")

    source_ids = {row.get("source_id", "") for row in sources if row.get("source_id")}
    person_rows = ledgers.get("03_人物与关系/person-ledger.csv", [])
    person_ids = {row.get("person_id", "") for row in person_rows if row.get("person_id")}
    role_ids = {row.get("role_id", "") for row in ledgers.get("03_人物与关系/role-ledger.csv", []) if row.get("role_id")}
    segment_rows = ledgers.get("05_媒体索引/media-index.csv", [])
    segment_ids = {row.get("segment_id", "") for row in segment_rows if row.get("segment_id")}
    event_ids = {row.get("event_id", "") for row in ledgers.get("06_事件与生活轨迹/event-ledger.csv", []) if row.get("event_id")}
    question_rows = ledgers.get("07_问题与回答/question-ledger.csv", [])
    question_ids = {row.get("question_id", "") for row in question_rows if row.get("question_id")}
    answer_rows = ledgers.get("07_问题与回答/answer-ledger.csv", [])
    answer_ids = {row.get("answer_id", "") for row in answer_rows if row.get("answer_id")}
    action_rows = ledgers.get("09_心愿与家庭行动/action-ledger.csv", [])
    action_ids = {row.get("action_id", "") for row in action_rows if row.get("action_id")}
    chapter_rows = ledgers.get("10_大纲与章节/chapter-ledger.csv", [])
    chapter_ids = {row.get("chapter_id", "") for row in chapter_rows if row.get("chapter_id")}

    scan_ids: set[str] = set()
    scan_root = safe_project_path(project, "02_素材账/scan-runs")
    if scan_root.exists():
        for child in sorted(scan_root.iterdir()):
            if not child.is_dir() or not (child / "receipt.json").is_file():
                continue
            try:
                receipt, _, _ = load_scan_bundle(project, child.name)
                scan_ids.add(receipt["scan_id"])
            except SystemExit:
                errors.append(f"invalid scan bundle: {child.name}")
            prepares = {path.stem.removeprefix("prepare-") for path in child.glob("prepare-*.json")}
            terminals = {path.stem.removeprefix("commit-") for path in child.glob("commit-*.json")}
            terminals |= {path.stem.removeprefix("abort-") for path in child.glob("abort-*.json")}
            unresolved = sorted(prepares - terminals)
            if unresolved:
                errors.append(f"scan {child.name}: unresolved prepared commits {unresolved}")

    seen_source_keys: set[str] = set()
    for row in sources:
        if row.get("root_id") not in root_ids:
            errors.append(f"source {row.get('source_id')}: unknown root_id")
        if row.get("scan_id") not in scan_ids:
            errors.append(f"source {row.get('source_id')}: unknown scan_id")
        expected_key = source_key(row.get("root_id", ""), row.get("relative_path", ""))
        if row.get("source_key") != expected_key:
            errors.append(f"source {row.get('source_id')}: source_key mismatch")
        if row.get("source_key") in seen_source_keys:
            errors.append(f"duplicate source_key: {row.get('source_key')}")
        seen_source_keys.add(row.get("source_key", ""))
        array_values(row, "path_history", f"source {row.get('source_id')} path_history", errors)
        if row.get("status") not in {"unreadable", "missing"} and not row.get("sha256"):
            errors.append(f"source {row.get('source_id')}: active source has no sha256")

    for row in person_rows:
        require_members(array_values(row, "source_ids", f"person {row.get('person_id')} source_ids", errors), source_ids, f"person {row.get('person_id')}", errors)
    for row in ledgers.get("03_人物与关系/relationship-ledger.csv", []):
        if row.get("person_a") not in person_ids or row.get("person_b") not in person_ids:
            errors.append(f"relationship {row.get('relationship_id')}: unknown person")
        if row.get("person_a") == row.get("person_b"):
            errors.append(f"relationship {row.get('relationship_id')}: self relationship")
        require_members(array_values(row, "source_ids", f"relationship {row.get('relationship_id')} source_ids", errors), source_ids, f"relationship {row.get('relationship_id')}", errors)
    for row in ledgers.get("03_人物与关系/role-ledger.csv", []):
        if row.get("person_id") not in person_ids:
            errors.append(f"role {row.get('role_id')}: unknown person")
        require_members(array_values(row, "source_ids", f"role {row.get('role_id')} source_ids", errors), source_ids, f"role {row.get('role_id')}", errors)

    for row in segment_rows:
        if row.get("source_id") not in source_ids:
            errors.append(f"segment {row.get('segment_id')}: unknown source")
        require_members(array_values(row, "person_ids", f"segment {row.get('segment_id')} person_ids", errors), person_ids, f"segment {row.get('segment_id')}", errors)
        if row.get("media_type") in {"video", "audio"} and row.get("track") != "file" and row.get("coverage_status") not in {"blocked", "not_applicable"}:
            if not row.get("start_time") or not row.get("end_time"):
                errors.append(f"segment {row.get('segment_id')}: timed media segment lacks timecodes")

    for row in ledgers.get("06_事件与生活轨迹/event-ledger.csv", []):
        require_members(array_values(row, "person_ids", f"event {row.get('event_id')} person_ids", errors), person_ids, f"event {row.get('event_id')}", errors)
        require_members(array_values(row, "source_ids", f"event {row.get('event_id')} source_ids", errors), source_ids, f"event {row.get('event_id')}", errors)

    story_ids: set[str] = set()
    story_dir = safe_project_path(project, "08_故事卡")
    story_schema = load_schema(schema_path("story-card.schema.json"))
    if story_dir.exists():
        for path in sorted(story_dir.glob("*.md")):
            if is_reparse_point(path):
                errors.append(f"unsafe story card path: {path.name}")
                continue
            try:
                metadata, _ = parse_frontmatter(path)
            except Exception as exc:
                errors.append(f"{path.name}: invalid story metadata: {exc}")
                continue
            errors.extend(validate_instance(metadata, story_schema, path.name))
            story_id = str(metadata.get("story_id", ""))
            if story_id in story_ids:
                errors.append(f"duplicate story_id: {story_id}")
            story_ids.add(story_id)
            if path.stem != story_id:
                errors.append(f"{path.name}: filename must equal story_id")
            require_members(list(metadata.get("source_ids", [])), source_ids, story_id, errors)
            require_members(list(metadata.get("segment_ids", [])), segment_ids, story_id, errors)
            require_members(list(metadata.get("person_ids", [])), person_ids, story_id, errors)
            if metadata.get("status") == "confirmed" and metadata.get("source_status") in {"inferred", "unknown", "pending"}:
                errors.append(f"{story_id}: confirmed story has unconfirmed source status")
    if sources and not story_ids:
        warnings.append("no story cards exist yet; first-value host validation remains pending")

    for row in question_rows:
        if row.get("target_person_id") and row.get("target_person_id") not in person_ids:
            errors.append(f"question {row.get('question_id')}: unknown target person")
        require_members(array_values(row, "source_ids", f"question {row.get('question_id')} source_ids", errors), source_ids, f"question {row.get('question_id')}", errors)
    for row in answer_rows:
        if row.get("question_id") not in question_ids:
            errors.append(f"answer {row.get('answer_id')}: unknown question")
        if row.get("narrator_person_id") and row.get("narrator_person_id") not in person_ids:
            errors.append(f"answer {row.get('answer_id')}: unknown narrator")
        require_members(array_values(row, "source_ids", f"answer {row.get('answer_id')} source_ids", errors), source_ids, f"answer {row.get('answer_id')}", errors)
    for row in action_rows:
        require_members(array_values(row, "source_ids", f"action {row.get('action_id')} source_ids", errors), source_ids, f"action {row.get('action_id')}", errors)
        require_members(array_values(row, "story_ids", f"action {row.get('action_id')} story_ids", errors), story_ids, f"action {row.get('action_id')}", errors)
        require_members(array_values(row, "owner_person_ids", f"action {row.get('action_id')} owner_person_ids", errors), person_ids, f"action {row.get('action_id')}", errors)
    for row in chapter_rows:
        require_members(array_values(row, "story_ids", f"chapter {row.get('chapter_id')} story_ids", errors), story_ids, f"chapter {row.get('chapter_id')}", errors)
        require_members(array_values(row, "source_ids", f"chapter {row.get('chapter_id')} source_ids", errors), source_ids, f"chapter {row.get('chapter_id')}", errors)
        try:
            chapter_path = safe_project_path(project, row.get("file_path", ""), must_exist=True)
            if not chapter_path.is_file():
                errors.append(f"chapter {row.get('chapter_id')}: file_path is not a file")
        except SystemExit:
            errors.append(f"chapter {row.get('chapter_id')}: unsafe or missing file_path")
        if row.get("status") == "locked" and row.get("permission_status") != "approved":
            errors.append(f"chapter {row.get('chapter_id')}: locked without approved permissions")

    object_sets = {
        "source": source_ids,
        "story": story_ids,
        "answer": answer_ids,
        "person": person_ids,
        "segment": segment_ids,
        "chapter": chapter_ids,
    }
    for row in ledgers.get("11_隐私与授权/consent-ledger.csv", []):
        if row.get("object_id") not in object_sets.get(row.get("object_type", ""), set()):
            errors.append(f"consent {row.get('consent_id')}: unknown object")
        if row.get("grantor_person_id") and row.get("grantor_person_id") not in person_ids:
            errors.append(f"consent {row.get('consent_id')}: unknown grantor")
        require_members(array_values(row, "evidence_source_ids", f"consent {row.get('consent_id')} evidence", errors), source_ids, f"consent {row.get('consent_id')}", errors)

    version_object_sets = {"story": story_ids, "answer": answer_ids, "chapter": chapter_ids}
    for row in ledgers.get("12_版本与检查点/version-ledger.csv", []):
        if row.get("object_type") in version_object_sets and row.get("object_id") not in version_object_sets[row["object_type"]]:
            errors.append(f"version {row.get('version_id')}: unknown object")
        try:
            version_path = safe_project_path(project, row.get("file_path", ""), must_exist=True)
            if file_sha256(version_path) != row.get("sha256"):
                errors.append(f"version {row.get('version_id')}: file hash mismatch")
        except SystemExit:
            errors.append(f"version {row.get('version_id')}: unsafe or missing file")

    checkpoint_dir = safe_project_path(project, "12_版本与检查点")
    checkpoint_schema = load_schema(schema_path("checkpoint.schema.json"))
    if checkpoint_dir.exists():
        for path in sorted(checkpoint_dir.glob("CPK-*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                errors.extend(validate_instance(data, checkpoint_schema, path.name))
                require_members(list(data.get("processed_source_ids", [])), source_ids, path.name, errors)
                require_members(list(data.get("locked_chapters", [])), chapter_ids, path.name, errors)
                for output in data.get("outputs", []):
                    candidate = safe_project_path(project, output, must_exist=True)
                    if not candidate.is_file():
                        errors.append(f"{path.name}: output is not a file {output}")
            except (Exception, SystemExit) as exc:
                errors.append(f"{path.name}: invalid checkpoint: {exc}")

    valid = not errors and not (args.fail_on_warnings and warnings)
    result = {
        "schemaVersion": "2.0",
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "roots": len(root_ids),
            "scans": len(scan_ids),
            "sources": len(source_ids),
            "people": len(person_ids),
            "roles": len(role_ids),
            "segments": len(segment_ids),
            "events": len(event_ids),
            "stories": len(story_ids),
            "questions": len(question_ids),
            "answers": len(answer_ids),
            "actions": len(action_ids),
            "chapters": len(chapter_ids),
        },
    }
    if not args.no_report:
        report_json = safe_project_path(project, "13_导出成果/project-validation.json")
        report_md = safe_project_path(project, "13_导出成果/project-validation.md")
        write_json_atomic(report_json, result, project_root=project)
        markdown = (
            "# 项目校验报告\n\n"
            + f"结论：{'通过' if valid else '未通过'}\n\n"
            + f"统计：{json.dumps(result['counts'], ensure_ascii=False)}\n\n"
            + "## 错误\n"
            + ("\n".join(f"- {item}" for item in errors) or "- 无")
            + "\n\n## 警告\n"
            + ("\n".join(f"- {item}" for item in warnings) or "- 无")
            + "\n"
        )
        write_text_atomic(report_md, markdown, project_root=project)
        print(f"project validation: {'PASS' if valid else 'FAIL'} -> {report_md}")
    else:
        print(f"project validation: {'PASS' if valid else 'FAIL'}")
    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
