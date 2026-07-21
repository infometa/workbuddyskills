#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SEMVER_RE = re.compile(r"^[0-9]+[.][0-9]+[.][0-9]+(?:[-.][0-9A-Za-z.-]+)?$")
JSON_MANIFESTS = [
    Path(".codebuddy-plugin/plugin.json"),
    Path("connectors/tongzhou-fin-research/connector-meta.json"),
    Path("codex/plugins/tongzhou-fin-research-expert/.codex-plugin/plugin.json"),
    Path("npm/package.json"),
]


def _read_version(root: Path, explicit: str | None) -> str:
    version = explicit or (root / "VERSION").read_text(encoding="utf-8").strip()
    if not SEMVER_RE.fullmatch(version):
        raise SystemExit(f"invalid version: {version}")
    return version


def _write_json_version(path: Path, version: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = version
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_version(root: Path, version: str) -> None:
    for rel_path in JSON_MANIFESTS:
        _write_json_version(root / rel_path, version)


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize WorkBuddy expert package version files.")
    parser.add_argument("--source", default=".", help="Repository root.")
    parser.add_argument("--version", help="Version to write. Defaults to VERSION file.")
    args = parser.parse_args()

    root = Path(args.source).resolve()
    version = _read_version(root, args.version)
    sync_version(root, version)
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
