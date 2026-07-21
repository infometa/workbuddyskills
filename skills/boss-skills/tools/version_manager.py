#!/usr/bin/env python3
"""
Version manager for boss.skill.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


MAX_VERSIONS = 10
ARCHIVE_FILES = (
    "SKILL.md",
    "judgment.md",
    "management.md",
    "persona.md",
    "judgment_skill.md",
    "management_skill.md",
    "persona_skill.md",
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def list_versions(skill_dir: Path) -> list[dict]:
    versions_dir = skill_dir / "versions"
    if not versions_dir.exists():
        return []
    versions = []
    for version_dir in sorted(versions_dir.iterdir()):
        if not version_dir.is_dir():
            continue
        archived_at = datetime.fromtimestamp(version_dir.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        files = [file.name for file in version_dir.iterdir() if file.is_file()]
        versions.append({"version": version_dir.name, "archived_at": archived_at, "files": files})
    return versions


def rollback(skill_dir: Path, target_version: str) -> bool:
    version_dir = skill_dir / "versions" / target_version
    if not version_dir.exists():
        print(f"错误：版本 {target_version} 不存在", file=sys.stderr)
        return False

    meta_path = skill_dir / "meta.json"
    meta = read_json(meta_path)
    current_version = meta.get("version", "v?")
    backup_dir = skill_dir / "versions" / f"{current_version}_before_rollback"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for fname in ARCHIVE_FILES:
        current = skill_dir / fname
        if current.exists():
            shutil.copy2(current, backup_dir / fname)

    restored = []
    for fname in ARCHIVE_FILES:
        src = version_dir / fname
        if src.exists():
            shutil.copy2(src, skill_dir / fname)
            restored.append(fname)

    meta["version"] = target_version + "_restored"
    meta["updated_at"] = datetime.now(timezone.utc).isoformat()
    meta["rollback_from"] = current_version
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已回滚到 {target_version}，恢复文件：{', '.join(restored)}")
    return True


def cleanup_old_versions(skill_dir: Path, max_versions: int = MAX_VERSIONS) -> None:
    versions_dir = skill_dir / "versions"
    if not versions_dir.exists():
        return
    version_dirs = sorted([path for path in versions_dir.iterdir() if path.is_dir()], key=lambda path: path.stat().st_mtime)
    old_dirs = version_dirs[:-max_versions] if len(version_dirs) > max_versions else []
    for old_dir in old_dirs:
        shutil.rmtree(old_dir)
        print(f"已清理旧版本：{old_dir.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="boss.skill version manager")
    parser.add_argument("--action", required=True, choices=["list", "rollback", "cleanup"])
    parser.add_argument("--slug", required=True)
    parser.add_argument("--version")
    parser.add_argument("--base-dir", default="./bosses")
    args = parser.parse_args()

    skill_dir = Path(args.base_dir).expanduser() / args.slug
    if not skill_dir.exists():
        print(f"错误：找不到 Skill 目录 {skill_dir}", file=sys.stderr)
        sys.exit(1)

    if args.action == "list":
        versions = list_versions(skill_dir)
        if not versions:
            print(f"{args.slug} 暂无历史版本")
        else:
            print(f"{args.slug} 的历史版本：\n")
            for item in versions:
                print(f"  {item['version']}  存档时间: {item['archived_at']}  文件: {', '.join(item['files'])}")
        return

    if args.action == "rollback":
        if not args.version:
            print("错误：rollback 操作需要 --version", file=sys.stderr)
            sys.exit(1)
        rollback(skill_dir, args.version)
        return

    cleanup_old_versions(skill_dir)
    print("清理完成")


if __name__ == "__main__":
    main()
