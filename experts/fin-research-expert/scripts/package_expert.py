#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".gitea",
    ".mypy_cache",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "codex",
    "connectors",
    "inspirations",
    "npm",
    "node_modules",
    "playbooks",
    "dist",
    "reference-materials",
    "tests",
    "workbuddy-expert-audit",
}
EXCLUDED_FILES = {
    ".DS_Store",
    ".gitignore",
    ".npm_acc",
    ".sms_key",
    ".mcp.json",
    "export_playbook_cases.py",
    "package_codex_plugin.py",
    "package_layer1_skills.py",
    "package_workbuddy_connector.py",
}
EXCLUDED_DOC_ASSET_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".psd", ".sketch", ".webp"}


def _include(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDED_DIRS:
        return False
    if path.name in EXCLUDED_FILES:
        return False
    if path.name.startswith(".env"):
        return False
    if path.parts[:1] == ("docs",) and path.suffix.lower() in EXCLUDED_DOC_ASSET_SUFFIXES:
        return False
    if path.suffix.lower() in {".pyc", ".pyo", ".zip"}:
        return False
    return True


def package_expert(source: Path, output_dir: Path) -> Path:
    source = source.resolve()
    plugin = json.loads((source / ".codebuddy-plugin" / "plugin.json").read_text(encoding="utf-8"))
    version = plugin["version"]
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{plugin['name']}-{version}.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if not path.is_file() or not _include(path.relative_to(source)):
                continue
            archive.write(path, path.relative_to(source).as_posix())
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a release zip for Fin Research Expert.")
    parser.add_argument("--source", default=".", help="Source expert directory.")
    parser.add_argument("--output-dir", default="dist", help="Output directory.")
    args = parser.parse_args()
    target = package_expert(Path(args.source), Path(args.output_dir))
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
