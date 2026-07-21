#!/usr/bin/env python3
"""
Skill file writer for boss-skills.

Supports:
- creating a boss skill from imported content
- updating an existing boss skill
- listing created boss skills
- deleting an existing boss skill
- listing bundled entrepreneur archetypes
- creating a boss skill from a bundled archetype
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


SKILL_MD_TEMPLATE = """\
---
name: {slug}
description: {description}
user-invocable: true
---

# {name}

{identity}

---

## Part A: Boss Judgment

{judgment_content}

---

## Part B: Managing Up

{management_content}

---

## Part C: Persona

{persona_content}

---

## Operating Rules

When evaluating any project, plan, status update, risk, or escalation:

1. Start with Part C to set tone, pressure level, and communication style.
2. Use Part A to evaluate the proposal, timing, risk, ownership, and tradeoffs.
3. Use Part B to give concrete managing-up advice and reporting actions.
4. Respond in the style of this boss without roleplaying fake private facts.
"""


def slugify(name: str) -> str:
    try:
        from pypinyin import lazy_pinyin

        parts = lazy_pinyin(name)
        slug = "-".join(parts)
    except ImportError:
        result = []
        for char in name.lower():
            if char.isascii() and (char.isalnum() or char in ("-", "_")):
                result.append(char)
            elif char.isspace():
                result.append("-")
            elif unicodedata.category(char).startswith("L"):
                continue
        slug = "".join(result)

    slug = re.sub(r"[-_]+", "-", slug).strip("-")
    return slug or "boss"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> dict:
    return json.loads(read_text(path))


def build_identity_string(meta: dict) -> str:
    profile = meta.get("profile", {})
    parts = []
    for key in ("company", "level", "role"):
        value = profile.get(key, "")
        if value:
            parts.append(value)

    identity = " ".join(parts) if parts else "Boss operating model"
    relation = profile.get("relation", "")
    if relation:
        identity += f" | {relation}"

    source = meta.get("source", {})
    if source.get("type") == "archetype":
        identity += f" | Inspired by {source.get('display_name', source.get('archetype', 'an entrepreneur archetype'))}"

    mbti = profile.get("mbti", "")
    if mbti:
        identity += f" | MBTI {mbti}"
    return identity


def build_description(meta: dict, name: str, identity: str) -> str:
    source = meta.get("source", {})
    if source.get("type") == "archetype":
        display = source.get("display_name", name)
        return f"{display}-inspired boss operating model | {identity}"
    return f"{name} boss skill | {identity}"


def write_skill_bundle(
    skill_dir: Path,
    slug: str,
    meta: dict,
    judgment_content: str,
    management_content: str,
    persona_content: str,
) -> None:
    name = meta.get("name", slug)
    identity = build_identity_string(meta)
    description = build_description(meta, name, identity)

    skill_md = SKILL_MD_TEMPLATE.format(
        slug=slug,
        name=name,
        description=description,
        identity=identity,
        judgment_content=judgment_content,
        management_content=management_content,
        persona_content=persona_content,
    )
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (skill_dir / "judgment_skill.md").write_text(
        (
            f"---\n"
            f"name: {slug}-judgment\n"
            f"description: {name} judgment lens\n"
            f"user-invocable: true\n"
            f"---\n\n{judgment_content}\n"
        ),
        encoding="utf-8",
    )
    (skill_dir / "management_skill.md").write_text(
        (
            f"---\n"
            f"name: {slug}-management\n"
            f"description: How to manage up with {name}\n"
            f"user-invocable: true\n"
            f"---\n\n{management_content}\n"
        ),
        encoding="utf-8",
    )
    (skill_dir / "persona_skill.md").write_text(
        (
            f"---\n"
            f"name: {slug}-persona\n"
            f"description: {name} communication persona\n"
            f"user-invocable: true\n"
            f"---\n\n{persona_content}\n"
        ),
        encoding="utf-8",
    )


def create_skill(
    base_dir: Path,
    slug: str,
    meta: dict,
    judgment_content: str,
    management_content: str,
    persona_content: str,
) -> Path:
    skill_dir = base_dir / slug
    skill_dir.mkdir(parents=True, exist_ok=True)

    (skill_dir / "versions").mkdir(exist_ok=True)
    (skill_dir / "knowledge" / "chats").mkdir(parents=True, exist_ok=True)
    (skill_dir / "knowledge" / "docs").mkdir(parents=True, exist_ok=True)
    (skill_dir / "knowledge" / "emails").mkdir(parents=True, exist_ok=True)
    (skill_dir / "knowledge" / "meetings").mkdir(parents=True, exist_ok=True)

    (skill_dir / "judgment.md").write_text(judgment_content, encoding="utf-8")
    (skill_dir / "management.md").write_text(management_content, encoding="utf-8")
    (skill_dir / "persona.md").write_text(persona_content, encoding="utf-8")

    now = datetime.now(timezone.utc).isoformat()
    meta["slug"] = slug
    meta.setdefault("created_at", now)
    meta["updated_at"] = now
    meta["version"] = "v1"
    meta.setdefault("corrections_count", 0)
    meta.setdefault("knowledge_sources", [])

    write_skill_bundle(skill_dir, slug, meta, judgment_content, management_content, persona_content)
    (skill_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return skill_dir


def update_skill(
    skill_dir: Path,
    judgment_patch: Optional[str] = None,
    management_patch: Optional[str] = None,
    persona_patch: Optional[str] = None,
    correction: Optional[dict] = None,
) -> str:
    meta_path = skill_dir / "meta.json"
    meta = read_json(meta_path)
    current_version = meta.get("version", "v1")
    try:
        version_num = int(current_version.lstrip("v").split("_")[0]) + 1
    except ValueError:
        version_num = 2
    new_version = f"v{version_num}"

    version_dir = skill_dir / "versions" / current_version
    version_dir.mkdir(parents=True, exist_ok=True)
    for fname in (
        "SKILL.md",
        "judgment.md",
        "management.md",
        "persona.md",
        "judgment_skill.md",
        "management_skill.md",
        "persona_skill.md",
    ):
        src = skill_dir / fname
        if src.exists():
            shutil.copy2(src, version_dir / fname)

    def append_patch(path: Path, patch: Optional[str]) -> None:
        if not patch:
            return
        current = read_text(path)
        path.write_text(current.rstrip() + "\n\n" + patch.strip() + "\n", encoding="utf-8")

    append_patch(skill_dir / "judgment.md", judgment_patch)
    append_patch(skill_dir / "management.md", management_patch)

    if correction:
        current_persona = read_text(skill_dir / "persona.md")
        correction_line = (
            f"- [{correction.get('scene', 'general')}] "
            f"Do not say: {correction['wrong']} | Prefer: {correction['correct']}"
        )
        target = "## Corrections"
        if target in current_persona:
            new_persona = current_persona.rstrip() + "\n" + correction_line + "\n"
        else:
            new_persona = current_persona.rstrip() + "\n\n## Corrections\n\n" + correction_line + "\n"
        (skill_dir / "persona.md").write_text(new_persona, encoding="utf-8")
        meta["corrections_count"] = meta.get("corrections_count", 0) + 1
    else:
        append_patch(skill_dir / "persona.md", persona_patch)

    slug = skill_dir.name
    judgment_content = read_text(skill_dir / "judgment.md")
    management_content = read_text(skill_dir / "management.md")
    persona_content = read_text(skill_dir / "persona.md")

    write_skill_bundle(skill_dir, slug, meta, judgment_content, management_content, persona_content)

    meta["version"] = new_version
    meta["updated_at"] = datetime.now(timezone.utc).isoformat()
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return new_version


def list_bosses(base_dir: Path) -> list[dict]:
    bosses: list[dict] = []
    if not base_dir.exists():
        return bosses

    for skill_dir in sorted(base_dir.iterdir()):
        meta_path = skill_dir / "meta.json"
        if not skill_dir.is_dir() or not meta_path.exists():
            continue
        try:
            meta = read_json(meta_path)
        except Exception:
            continue
        bosses.append(
            {
                "slug": meta.get("slug", skill_dir.name),
                "name": meta.get("name", skill_dir.name),
                "identity": build_identity_string(meta),
                "version": meta.get("version", "v1"),
                "updated_at": meta.get("updated_at", ""),
                "corrections_count": meta.get("corrections_count", 0),
                "source_type": meta.get("source", {}).get("type", "real"),
            }
        )
    return bosses


def delete_boss(base_dir: Path, slug: str) -> Path:
    skill_dir = base_dir / slug
    if not skill_dir.exists():
        raise FileNotFoundError(f"Boss skill not found: {skill_dir}")
    shutil.rmtree(skill_dir)
    return skill_dir


def load_archetype(archetypes_dir: Path, slug: str) -> tuple[dict, str, str, str]:
    archetype_dir = archetypes_dir / slug
    if not archetype_dir.exists():
        raise FileNotFoundError(f"Archetype not found: {archetype_dir}")

    meta = read_json(archetype_dir / "meta.json")
    judgment = read_text(archetype_dir / "judgment.md")
    management = read_text(archetype_dir / "management.md")
    persona = read_text(archetype_dir / "persona.md")
    return meta, judgment, management, persona


def list_archetypes(archetypes_dir: Path) -> list[dict]:
    items: list[dict] = []
    if not archetypes_dir.exists():
        return items

    for archetype_dir in sorted(archetypes_dir.iterdir()):
        meta_path = archetype_dir / "meta.json"
        if not archetype_dir.is_dir() or not meta_path.exists():
            continue
        try:
            meta = read_json(meta_path)
        except Exception:
            continue
        items.append(meta)
    return items


def create_from_archetype(base_dir: Path, archetypes_dir: Path, archetype_slug: str, output_slug: Optional[str]) -> Path:
    archetype_meta, judgment, management, persona = load_archetype(archetypes_dir, archetype_slug)
    name = archetype_meta.get("name", archetype_slug)
    slug = output_slug or archetype_slug
    meta = {
        "name": name,
        "profile": archetype_meta.get("profile", {}),
        "tags": archetype_meta.get("tags", {}),
        "impression": archetype_meta.get("impression", ""),
        "knowledge_sources": ["bundled archetype"],
        "source": {
            "type": "archetype",
            "archetype": archetype_slug,
            "display_name": archetype_meta.get("display_name", name),
        },
        "archetype_notes": archetype_meta.get("notes", []),
        "safety": {
            "framing": "This skill is inspired by public management patterns, not a claim of private access or exact impersonation."
        },
    }
    return create_skill(base_dir, slug, meta, judgment, management, persona)


def read_optional(path_str: Optional[str]) -> Optional[str]:
    if not path_str:
        return None
    return read_text(Path(path_str))


def print_boss_list(base_dir: Path) -> None:
    bosses = list_bosses(base_dir)
    if not bosses:
        print("No boss skills found.")
        return

    print(f"Found {len(bosses)} boss skills:\n")
    for item in bosses:
        updated = item["updated_at"][:10] if item["updated_at"] else "unknown"
        print(f"[{item['slug']}] {item['name']}")
        print(f"  source: {item['source_type']} | version: {item['version']} | corrections: {item['corrections_count']} | updated: {updated}")
        print(f"  identity: {item['identity']}\n")


def print_archetype_list(archetypes_dir: Path) -> None:
    items = list_archetypes(archetypes_dir)
    if not items:
        print("No archetypes found.")
        return

    print(f"Found {len(items)} archetypes:\n")
    for item in items:
        tags = ", ".join(item.get("tags", {}).get("style", [])[:4])
        print(f"[{item['slug']}] {item.get('display_name', item['name'])}")
        print(f"  company: {item.get('profile', {}).get('company', 'n/a')}")
        print(f"  style: {tags}")
        print(f"  summary: {item.get('summary', '')}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="boss-skills file writer")
    parser.add_argument(
        "--action",
        required=True,
        choices=["create", "update", "list", "delete", "list-archetypes", "create-archetype"],
    )
    parser.add_argument("--slug")
    parser.add_argument("--name")
    parser.add_argument("--meta")
    parser.add_argument("--judgment")
    parser.add_argument("--management")
    parser.add_argument("--persona")
    parser.add_argument("--judgment-patch")
    parser.add_argument("--management-patch")
    parser.add_argument("--persona-patch")
    parser.add_argument("--base-dir", default="./bosses")
    parser.add_argument("--archetypes-dir", default="./archetypes")
    parser.add_argument("--archetype")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).expanduser()
    archetypes_dir = Path(args.archetypes_dir).expanduser()

    if args.action == "list":
        print_boss_list(base_dir)
        return

    if args.action == "delete":
        if not args.slug:
            print("Error: delete requires --slug", file=sys.stderr)
            sys.exit(1)
        deleted_dir = delete_boss(base_dir, args.slug)
        print(f"Deleted boss skill: {deleted_dir}")
        return

    if args.action == "list-archetypes":
        print_archetype_list(archetypes_dir)
        return

    if args.action == "create-archetype":
        if not args.archetype:
            print("Error: create-archetype requires --archetype", file=sys.stderr)
            sys.exit(1)
        skill_dir = create_from_archetype(base_dir, archetypes_dir, args.archetype, args.slug)
        print(f"Created archetype skill: {skill_dir}")
        print(f"Trigger command: /{skill_dir.name}")
        return

    if args.action == "create":
        if not args.slug and not args.name:
            print("Error: create requires --slug or --name", file=sys.stderr)
            sys.exit(1)
        meta = read_json(Path(args.meta)) if args.meta else {}
        if args.name:
            meta["name"] = args.name
        slug = args.slug or slugify(meta.get("name", "boss"))
        skill_dir = create_skill(
            base_dir,
            slug,
            meta,
            read_optional(args.judgment) or "",
            read_optional(args.management) or "",
            read_optional(args.persona) or "",
        )
        print(f"Created skill: {skill_dir}")
        print(f"Trigger command: /{slug}")
        return

    if not args.slug:
        print("Error: update requires --slug", file=sys.stderr)
        sys.exit(1)

    skill_dir = base_dir / args.slug
    if not skill_dir.exists():
        print(f"Error: skill directory not found: {skill_dir}", file=sys.stderr)
        sys.exit(1)

    new_version = update_skill(
        skill_dir,
        read_optional(args.judgment_patch),
        read_optional(args.management_patch),
        read_optional(args.persona_patch),
    )
    print(f"Updated skill to {new_version}: {skill_dir}")


if __name__ == "__main__":
    main()
