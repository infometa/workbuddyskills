"""Create and open durable, byte-stable MIBAO project roots."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from mibao_core.errors import MibaoError
from mibao_core.project.lock import ProjectLock
from mibao_core.project.migrations import (
    SCHEMA_VERSION,
    apply_initial_schema,
    apply_pending_migrations,
    audit_schema,
)

MANIFEST_SCHEMA_VERSION: Final = "1.0"
MANIFEST_NAME: Final = "project.json"
DATABASE_RELATIVE: Final = "database/mibao.sqlite"
PRIVACY_MODES: Final[frozenset[str]] = frozenset({"local-private", "hybrid", "deep-understanding"})
_PROJECT_ID = re.compile(r"^MB-[0-9a-f]{32}$")
_MANIFEST_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "project_id",
        "display_name",
        "privacy_mode",
        "state",
        "created_at",
        "updated_at",
        "project_root",
        "database",
    }
)


@dataclass(frozen=True, slots=True)
class Project:
    root: Path
    project_id: str
    display_name: str
    privacy_mode: str
    state: str
    created_at: str
    updated_at: str
    migration_applied: bool = False

    @property
    def schema_version(self) -> int:
        return SCHEMA_VERSION

    @property
    def manifest_path(self) -> Path:
        return self.root / MANIFEST_NAME

    @property
    def database_path(self) -> Path:
        return self.root / Path(*DATABASE_RELATIVE.split("/"))

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "display_name": self.display_name,
            "privacy_mode": self.privacy_mode,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "schema_version": self.schema_version,
            "database_relative": DATABASE_RELATIVE,
        }


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _resolve_project_root(value: Path) -> Path:
    if value.exists() and value.is_symlink():
        raise MibaoError("MB-PROJ-0001", "Project root must not be a symlink")
    try:
        root = value.expanduser().resolve(strict=False)
    except OSError as exc:
        raise MibaoError("MB-PROJ-0001", f"Project root cannot be resolved: {exc}") from exc
    if root == Path(root.anchor):
        raise MibaoError("MB-PROJ-0001", "Filesystem root cannot be a MIBAO project")
    if root.exists() and not root.is_dir():
        raise MibaoError("MB-PROJ-0001", "Project root is not a directory")
    return root


def _manifest_payload(
    *,
    project_id: str,
    display_name: str,
    privacy_mode: str,
    timestamp: str,
) -> dict[str, Any]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "project_id": project_id,
        "display_name": display_name,
        "privacy_mode": privacy_mode,
        "state": "active",
        "created_at": timestamp,
        "updated_at": timestamp,
        "project_root": ".",
        "database": DATABASE_RELATIVE,
    }


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MibaoError("MB-PROJ-0004", f"Project manifest is invalid: {exc}") from exc
    if not isinstance(payload, dict) or set(payload) != _MANIFEST_KEYS:
        raise MibaoError("MB-PROJ-0004", "Project manifest fields do not match schema 1.0")
    if payload.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise MibaoError("MB-PROJ-0004", "Project manifest schema version is unsupported")
    project_id = payload.get("project_id")
    if not isinstance(project_id, str) or not _PROJECT_ID.fullmatch(project_id):
        raise MibaoError("MB-PROJ-0004", "Project id is invalid")
    display_name = payload.get("display_name")
    if not isinstance(display_name, str) or not display_name.strip():
        raise MibaoError("MB-PROJ-0004", "Project display name is invalid")
    if payload.get("privacy_mode") not in PRIVACY_MODES:
        raise MibaoError("MB-PROJ-0004", "Project privacy mode is invalid")
    if payload.get("state") != "active":
        raise MibaoError("MB-PROJ-0004", "Project state is unsupported")
    if payload.get("project_root") != "." or payload.get("database") != DATABASE_RELATIVE:
        raise MibaoError("MB-PROJ-0004", "Project storage paths are not canonical relative paths")
    for field in ("created_at", "updated_at"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.endswith("Z"):
            raise MibaoError("MB-PROJ-0004", f"Project {field} is invalid")
    return payload


def _connect_writable(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA synchronous = FULL")
    connection.execute("PRAGMA journal_mode = DELETE")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _connect_readonly(path: Path) -> sqlite3.Connection:
    uri = path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=5.0, isolation_level=None)
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_project(
    root: Path,
    *,
    display_name: str,
    privacy_mode: str = "hybrid",
) -> Project:
    """Create one project without overwriting owner files; reopening is idempotent."""

    if not isinstance(display_name, str) or not display_name.strip():
        raise MibaoError("MB-PROJ-0001", "Project display name is required")
    if privacy_mode not in PRIVACY_MODES:
        raise MibaoError("MB-PROJ-0001", f"Unsupported privacy mode: {privacy_mode}")
    project_root = _resolve_project_root(root)
    project_root.mkdir(parents=True, exist_ok=True)
    with ProjectLock(project_root):
        manifest_path = project_root / MANIFEST_NAME
        if manifest_path.is_file():
            existing = open_project(project_root)
            if (
                existing.display_name != display_name.strip()
                or existing.privacy_mode != privacy_mode
            ):
                raise MibaoError("MB-PROJ-0002", "Existing project configuration does not match")
            return existing
        owner_entries = [entry for entry in project_root.iterdir() if entry.name != ".mibao"]
        if owner_entries:
            raise MibaoError("MB-PROJ-0002", "Project directory is not empty")

        project_id = "MB-" + uuid.uuid4().hex
        timestamp = _timestamp()
        payload = _manifest_payload(
            project_id=project_id,
            display_name=display_name.strip(),
            privacy_mode=privacy_mode,
            timestamp=timestamp,
        )
        database_path = project_root / Path(*DATABASE_RELATIVE.split("/"))
        database_path.parent.mkdir(parents=True)
        database_partial = database_path.with_name(f"{database_path.name}.partial-{os.getpid()}")
        manifest_partial = manifest_path.with_name(f"{MANIFEST_NAME}.partial-{os.getpid()}")
        try:
            connection = _connect_writable(database_partial)
            try:
                apply_initial_schema(
                    connection,
                    project_id=project_id,
                    privacy_mode=privacy_mode,
                    timestamp=timestamp,
                )
                integrity = connection.execute("PRAGMA integrity_check").fetchone()
                if integrity != ("ok",):
                    raise MibaoError("MB-PROJ-0005", "SQLite integrity check failed")
            finally:
                connection.close()
            manifest_encoded = (
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
            with manifest_partial.open("xb") as handle:
                handle.write(manifest_encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(database_partial, database_path)
            os.replace(manifest_partial, manifest_path)
        except BaseException:
            database_partial.unlink(missing_ok=True)
            manifest_partial.unlink(missing_ok=True)
            raise
    return open_project(project_root)


@contextmanager
def open_project_reader(root: Path) -> Iterator[tuple[Project, sqlite3.Connection]]:
    """Keep one audited read-only connection open for the complete read transaction."""

    project_root = _resolve_project_root(root)
    manifest_path = project_root / MANIFEST_NAME
    database_path = project_root / Path(*DATABASE_RELATIVE.split("/"))
    if not manifest_path.is_file() or not database_path.is_file():
        raise MibaoError("MB-PROJ-0004", "Project manifest or database is missing")
    payload = _load_manifest(manifest_path)
    connection = _connect_readonly(database_path)
    try:
        connection.execute("BEGIN")
        audit_schema(
            connection,
            expected_project_id=str(payload["project_id"]),
            expected_privacy_mode=str(payload["privacy_mode"]),
        )
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity != ("ok",):
            raise MibaoError("MB-PROJ-0005", "SQLite integrity check failed")
        project = Project(
            root=project_root,
            project_id=str(payload["project_id"]),
            display_name=str(payload["display_name"]),
            privacy_mode=str(payload["privacy_mode"]),
            state=str(payload["state"]),
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
        )
        yield project, connection
    finally:
        if connection.in_transaction:
            connection.rollback()
        connection.close()


def open_project(root: Path) -> Project:
    """Open and current-read audit a project without mutating its bytes."""

    with open_project_reader(root) as (project, _):
        return project


@contextmanager
def open_project_writer(root: Path) -> Iterator[tuple[Project, sqlite3.Connection]]:
    """Lock and current-read a project through a writable recovery connection.

    Opening the writable connection before any read-only database connection lets SQLite
    recover an abandoned DELETE-mode hot journal after abrupt process termination.
    """

    project_root = _resolve_project_root(root)
    manifest_path = project_root / MANIFEST_NAME
    database_path = project_root / Path(*DATABASE_RELATIVE.split("/"))
    with ProjectLock(project_root):
        if not manifest_path.is_file() or not database_path.is_file():
            raise MibaoError("MB-PROJ-0004", "Project manifest or database is missing")
        payload = _load_manifest(manifest_path)
        connection = _connect_writable(database_path)
        try:
            audit_schema(
                connection,
                expected_project_id=str(payload["project_id"]),
                expected_privacy_mode=str(payload["privacy_mode"]),
            )
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if integrity != ("ok",):
                raise MibaoError("MB-PROJ-0005", "SQLite integrity check failed")
            project = Project(
                root=project_root,
                project_id=str(payload["project_id"]),
                display_name=str(payload["display_name"]),
                privacy_mode=str(payload["privacy_mode"]),
                state=str(payload["state"]),
                created_at=str(payload["created_at"]),
                updated_at=str(payload["updated_at"]),
            )
            yield project, connection
        finally:
            if connection.in_transaction:
                connection.rollback()
            connection.close()


def migrate_project(root: Path) -> Project:
    """Upgrade a valid legacy project transactionally and audit the completed state."""

    project_root = _resolve_project_root(root)
    manifest_path = project_root / MANIFEST_NAME
    database_path = project_root / Path(*DATABASE_RELATIVE.split("/"))
    if not manifest_path.is_file() or not database_path.is_file():
        raise MibaoError("MB-PROJ-0004", "Project manifest or database is missing")
    payload = _load_manifest(manifest_path)
    changed = False
    with ProjectLock(project_root):
        connection = _connect_writable(database_path)
        try:
            try:
                changed = apply_pending_migrations(
                    connection,
                    project_id=str(payload["project_id"]),
                    privacy_mode=str(payload["privacy_mode"]),
                    timestamp=_timestamp(),
                )
            except sqlite3.Error as exc:
                raise MibaoError(
                    "MB-PROJ-0006",
                    f"SQLite migration failed and was rolled back: {exc}",
                ) from exc
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if integrity != ("ok",):
                raise MibaoError("MB-PROJ-0005", "SQLite integrity check failed")
        finally:
            connection.close()
    return replace(open_project(project_root), migration_applied=changed)
