#!/usr/bin/env python3
"""Save and restore complete Tietu Toutiao revision state safely."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSIONS_DIR_NAME = ".tietu_versions"
VERSIONS_FILE = "versions.json"
DB_FILE = "versions.db"
SAFE_NAME = re.compile(r"^[^/\\\x00]+$")

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  timestamp TEXT NOT NULL,
  revision_id TEXT,
  dir TEXT NOT NULL,
  sha256_state TEXT,
  sha256_layout TEXT,
  sha256_cover TEXT,
  source TEXT NOT NULL DEFAULT 'manual'
);
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  revision_id TEXT,
  narrative TEXT,
  model TEXT,
  excluded TEXT,
  review TEXT,
  confirmed_by TEXT,
  channel TEXT NOT NULL DEFAULT 'local',
  recorded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  revision_id TEXT,
  origin TEXT NOT NULL,
  text TEXT NOT NULL,
  recorded_at TEXT NOT NULL
);
"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_version_name(name: str) -> str:
    name = name.strip()
    if not name or name in {".", ".."} or not SAFE_NAME.fullmatch(name) or name.startswith("."):
        raise ValueError("version name must be non-empty, path-safe, and must not contain / or \\")
    return name


def _within(root: Path, candidate: Path) -> Path:
    root = root.resolve()
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes workspace: {candidate}") from exc
    return candidate


def _versions_path(workspace: Path, create: bool) -> tuple[Path, Path]:
    workspace = workspace.resolve()
    if create:
        workspace.mkdir(parents=True, exist_ok=True)
    versions_dir = _within(workspace, workspace / VERSIONS_DIR_NAME)
    if create:
        versions_dir.mkdir(parents=True, exist_ok=True)
    return workspace, versions_dir / VERSIONS_FILE


def _read_versions(workspace: Path) -> list[dict[str, Any]]:
    _, path = _versions_path(workspace, create=False)
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid versions file: {path}: {exc}") from exc
    if not isinstance(value, list):
        raise ValueError("versions file must contain an array")
    return value


def _write_versions(workspace: Path, versions: list[dict[str, Any]]) -> None:
    _, path = _versions_path(workspace, create=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(versions, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _copy_inside(source: Path, destination: Path, workspace: Path) -> None:
    source = source.resolve()
    destination = _within(workspace, destination)
    if not source.is_file():
        raise ValueError(f"source file not found: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _db_connect(workspace: Path, read_only: bool = False) -> sqlite3.Connection:
    """Open versions.db with the schema ensured (or read-only for audit queries)."""
    versions_dir = _within(workspace, workspace / VERSIONS_DIR_NAME)
    db_path = versions_dir / DB_FILE
    if read_only:
        if not db_path.is_file():
            raise LookupError(f"versions.db not found: {db_path}")
        connection = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    else:
        connection = sqlite3.connect(str(db_path))
    connection.executescript(DB_SCHEMA)
    return connection


def _sync_db_version(workspace: Path, record: dict[str, Any], state: dict[str, Any], source: str) -> None:
    """Dual-write every saved version into versions.db (JSON stays the restore source)."""
    connection = _db_connect(workspace)
    try:
        connection.execute(
            "INSERT OR REPLACE INTO versions (name, timestamp, revision_id, dir, sha256_state, sha256_layout, sha256_cover, source)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record["name"], record["timestamp"], record.get("revision_id"), record["dir"],
                record["sha256"]["state"], record["sha256"]["layout"], record["sha256"]["cover"], source,
            ),
        )
        log = state.get("editorial_log")
        if isinstance(log, dict):
            review = log.get("review")
            connection.execute(
                "INSERT INTO decisions (revision_id, narrative, model, excluded, review, confirmed_by, channel, recorded_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    state.get("revision_id"), log.get("narrative"), log.get("model"),
                    json.dumps(log.get("excluded"), ensure_ascii=False),
                    json.dumps(review, ensure_ascii=False) if review is not None else None,
                    None, source, datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ),
            )
        connection.commit()
    finally:
        connection.close()


def record_feedback(workspace: Path, revision_id: str, origin: str, text: str) -> None:
    if not revision_id.strip() or not origin.strip() or not text.strip():
        raise ValueError("feedback requires non-empty revision_id, origin, and text")
    connection = _db_connect(workspace)
    try:
        connection.execute(
            "INSERT INTO feedback (revision_id, origin, text, recorded_at) VALUES (?, ?, ?, ?)",
            (revision_id, origin, text, datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        connection.commit()
    finally:
        connection.close()


def migrate_json_to_db(workspace: Path) -> int:
    """Import versions.json records into versions.db; idempotent by version name."""
    migrated = 0
    connection = _db_connect(workspace)
    try:
        existing = {row[0] for row in connection.execute("SELECT name FROM versions")}
        for record in _read_versions(workspace):
            if record.get("name") in existing:
                continue
            state_path = workspace / record["state"]
            state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
            connection.execute(
                "INSERT OR REPLACE INTO versions (name, timestamp, revision_id, dir, sha256_state, sha256_layout, sha256_cover, source)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record["name"], record.get("timestamp", ""), record.get("revision_id"), record.get("dir", ""),
                    record.get("sha256", {}).get("state"), record.get("sha256", {}).get("layout"),
                    record.get("sha256", {}).get("cover"), "migrated",
                ),
            )
            migrated += 1
        connection.commit()
    finally:
        connection.close()
    return migrated


def db_query(workspace: Path, sql: str) -> list[tuple]:
    """Run a read-only audit query; anything that is not a SELECT is refused."""
    if not sql.lstrip().lower().startswith("select"):
        raise ValueError("only SELECT statements are allowed for audit queries")
    connection = _db_connect(workspace, read_only=True)
    try:
        return connection.execute(sql).fetchall()
    finally:
        connection.close()


def save_version(workspace: Path, name: str, state: Path, layout: Path, cover: Path, source: str = "manual") -> None:
    workspace, _ = _versions_path(workspace, create=True)
    safe_name = _safe_version_name(name)
    state = state.resolve()
    layout = layout.resolve()
    cover = cover.resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    version_dir = _within(workspace, workspace / VERSIONS_DIR_NAME / f"{timestamp}_{safe_name}")
    version_dir.mkdir(parents=True, exist_ok=False)
    _copy_inside(state, version_dir / "state.json", workspace)
    _copy_inside(layout, version_dir / "layout.json", workspace)
    _copy_inside(cover, version_dir / "cover.png", workspace)

    relative_dir = version_dir.relative_to(workspace).as_posix()
    record = {
        "name": safe_name,
        "timestamp": timestamp,
        "revision_id": json.loads((version_dir / "state.json").read_text(encoding="utf-8")).get("revision_id"),
        "dir": relative_dir,
        "state": f"{relative_dir}/state.json",
        "layout": f"{relative_dir}/layout.json",
        "cover": f"{relative_dir}/cover.png",
        "sha256": {
            "state": _sha256(version_dir / "state.json"),
            "layout": _sha256(version_dir / "layout.json"),
            "cover": _sha256(version_dir / "cover.png"),
        },
    }
    versions = _read_versions(workspace)
    versions.append(record)
    _write_versions(workspace, versions)
    _sync_db_version(workspace, record, json.loads((version_dir / "state.json").read_text(encoding="utf-8")), source)
    print(f"[OK] version saved: {safe_name} ({timestamp})")


def list_versions(workspace: Path) -> None:
    versions = _read_versions(workspace)
    if not versions:
        print("[INFO] no versions")
        return
    print(f"{len(versions)} version(s):")
    for index, version in enumerate(versions, 1):
        print(f"  {index}. {version['name']} ({version['timestamp']}) revision={version.get('revision_id')}")


def revert_version(workspace: Path, name: str, output_state: Path, output_layout: Path, output_cover: Path) -> None:
    workspace = workspace.resolve()
    safe_name = _safe_version_name(name)
    versions = _read_versions(workspace)
    target = next((version for version in reversed(versions) if version.get("name") == safe_name), None)
    if target is None:
        raise LookupError(f"version not found: {safe_name}")

    for key, output in (("state", output_state), ("layout", output_layout), ("cover", output_cover)):
        source = _within(workspace, workspace / target[key])
        destination = _within(workspace, output)
        _copy_inside(source, destination, workspace)
    print(f"[OK] version restored: {safe_name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Tietu Toutiao revision manager")
    sub = parser.add_subparsers(dest="command")

    save = sub.add_parser("save")
    save.add_argument("--workspace", required=True)
    save.add_argument("--name", required=True)
    save.add_argument("--state", required=True)
    save.add_argument("--layout", required=True)
    save.add_argument("--cover", required=True)

    listing = sub.add_parser("list")
    listing.add_argument("--workspace", required=True)

    revert = sub.add_parser("revert")
    revert.add_argument("--workspace", required=True)
    revert.add_argument("--name", required=True)
    revert.add_argument("--output-state", required=True)
    revert.add_argument("--output-layout", required=True)
    revert.add_argument("--output-cover", required=True)

    feedback = sub.add_parser("feedback")
    feedback.add_argument("--workspace", required=True)
    feedback.add_argument("--revision-id", required=True)
    feedback.add_argument("--origin", required=True, help="e.g. review-page, session, wecom")
    feedback.add_argument("--text", required=True)

    migrate = sub.add_parser("migrate")
    migrate.add_argument("--workspace", required=True)

    query = sub.add_parser("db-query")
    query.add_argument("--workspace", required=True)
    query.add_argument("--sql", required=True, help="read-only SELECT audit query")

    args = parser.parse_args()
    try:
        if args.command == "save":
            save_version(Path(args.workspace), args.name, Path(args.state), Path(args.layout), Path(args.cover))
        elif args.command == "list":
            list_versions(Path(args.workspace))
        elif args.command == "revert":
            revert_version(Path(args.workspace), args.name, Path(args.output_state), Path(args.output_layout), Path(args.output_cover))
        elif args.command == "feedback":
            record_feedback(Path(args.workspace), args.revision_id, args.origin, args.text)
            print(f"[OK] feedback recorded for {args.revision_id}")
        elif args.command == "migrate":
            count = migrate_json_to_db(Path(args.workspace))
            print(f"[OK] migrated {count} version record(s) into versions.db")
        elif args.command == "db-query":
            rows = db_query(Path(args.workspace), args.sql)
            for row in rows:
                print(row)
            print(f"[OK] {len(rows)} row(s)")
        else:
            parser.print_help()
            return 2
    except (OSError, ValueError, LookupError, json.JSONDecodeError) as exc:
        print(f"[ERROR] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
