#!/usr/bin/env python3
"""Activate a package template into a validated project location."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import assert_project_root, fail, new_id, read_csv, safe_project_path, write_text_atomic

TEMPLATES = {
    "question-map": ("question-map.md", "07_问题与回答/问题地图.md", ""),
    "video-segment-card": ("video-segment-card.md", "05_媒体索引/{id}.md", "SEG"),
    "video-global-summary": ("video-global-summary.md", "05_媒体索引/视频全片摘要.md", ""),
    "pending-media": ("pending-media.csv", "05_媒体索引/待处理队列.csv", ""),
    "batch-plan": ("batch-plan.csv", "12_版本与检查点/批次计划.csv", ""),
    "memory-conflicts": ("memory-conflicts.csv", "07_问题与回答/记忆冲突.csv", ""),
    "chapter": ("chapter.md", "10_大纲与章节/{id}.md", "CH"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("artifact", choices=["story-card", *sorted(TEMPLATES)])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--title", default="待命名故事")
    parser.add_argument("--mother-relation", choices=["direct_experience", "relationship_story", "family_view", "shared_family_event", "growth_context", "indirect_material", "family_branch"], default="direct_experience")
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--segment-id", action="append", default=[])
    parser.add_argument("--person-id", action="append", default=[])
    args = parser.parse_args()
    project = assert_project_root(args.project_dir)
    template_root = Path(__file__).resolve().parents[1] / "templates"

    if args.artifact == "story-card":
        if not args.source_id:
            fail("story-card requires at least one --source-id")
        known_sources = {row.get("source_id", "") for row in read_csv(safe_project_path(project, "02_素材账/source-ledger.csv"), required=True)}
        known_segments = {row.get("segment_id", "") for row in read_csv(safe_project_path(project, "05_媒体索引/media-index.csv"), required=True)}
        known_people = {row.get("person_id", "") for row in read_csv(safe_project_path(project, "03_人物与关系/person-ledger.csv"), required=True)}
        if set(args.source_id) - known_sources:
            fail(f"unknown source ids: {sorted(set(args.source_id) - known_sources)}")
        if set(args.segment_id) - known_segments:
            fail(f"unknown segment ids: {sorted(set(args.segment_id) - known_segments)}")
        if set(args.person_id) - known_people:
            fail(f"unknown person ids: {sorted(set(args.person_id) - known_people)}")
        identifier = new_id("STY")
        target = safe_project_path(project, f"08_故事卡/{identifier}.md")
        text = (template_root / "story-card.md").read_text(encoding="utf-8")
        replacements = {
            "{{story_id}}": identifier,
            "{{title}}": args.title.replace('"', "'"),
            "{{mother_relation}}": args.mother_relation,
            "{{source_ids_json}}": json.dumps(sorted(set(args.source_id)), ensure_ascii=False),
            "{{segment_ids_json}}": json.dumps(sorted(set(args.segment_id)), ensure_ascii=False),
            "{{person_ids_json}}": json.dumps(sorted(set(args.person_id)), ensure_ascii=False),
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
    else:
        template_name, target_pattern, prefix = TEMPLATES[args.artifact]
        identifier = new_id(prefix) if prefix else ""
        target = safe_project_path(project, target_pattern.format(id=identifier))
        text = (template_root / template_name).read_text(encoding="utf-8")
        if identifier:
            text = text.replace("SEG-001", identifier).replace("CH-001", identifier)
    if target.exists() and not args.force:
        fail(f"artifact exists; explicit --force is required: {target}")
    write_text_atomic(target, text, project_root=project)
    print(f"artifact initialized: {args.artifact} -> {target}")


if __name__ == "__main__":
    main()
