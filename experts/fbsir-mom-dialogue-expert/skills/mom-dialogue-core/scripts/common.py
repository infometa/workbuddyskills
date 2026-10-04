#!/usr/bin/env python3
"""Shared filesystem, atomic-write, CSV, schema, and locking helpers.

The package treats source roots as read-only and project files as untrusted
inputs. Every project read/write therefore rechecks lexical containment and
rejects symbolic links, junctions, and other Windows reparse points.
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import os
import re
import stat
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Iterator, NoReturn

MARKER_NAME = ".mom-dialogue-project.json"
REGISTRY_NAME = "source-roots.json"
EXCLUDED_PARTS = {
    ".workbuddy-ai",
    ".git",
    "node_modules",
    "__pycache__",
    "$RECYCLE.BIN",
    "System Volume Information",
}
EXCLUDED_NAMES = {".DS_Store", "Thumbs.db"}
EXCLUDED_SUFFIXES = {".pyc", ".tmp", ".part", ".swp"}
FORMULA_PREFIXES = ("=", "+", "-", "@")
ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*-[A-Z0-9]{12,64}$")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def fail(message: str, code: int = 2) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def validate_id(value: str, prefix: str) -> str:
    if not value.startswith(prefix + "-") or not ID_PATTERN.fullmatch(value):
        fail(f"invalid {prefix} identifier: {value}")
    return value


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def lexical_path(value: str | Path) -> Path:
    """Return an absolute normalized path without resolving links."""
    return Path(os.path.abspath(os.path.expanduser(str(value))))


def path_lexists(path: Path) -> bool:
    return os.path.lexists(str(path))


def is_reparse_point(path: Path) -> bool:
    if not path_lexists(path):
        return False
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        if callable(is_junction) and is_junction():
            return True
        if os.name == "nt":
            attributes = getattr(os.stat(path, follow_symlinks=False), "st_file_attributes", 0)
            return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
        return False
    except (OSError, ValueError) as exc:
        fail(f"cannot inspect filesystem safety metadata for {path}: {exc}")


def check_existing_components(path: str | Path, stop_at: str | Path | None = None) -> None:
    target = lexical_path(path)
    stop = lexical_path(stop_at) if stop_at is not None else None
    if stop is not None:
        try:
            relative = target.relative_to(stop)
        except ValueError:
            fail(f"path is not below safety boundary: {target}")
        current = stop
        parts = relative.parts
    else:
        current = Path(target.anchor)
        parts = target.parts[1:]
    if path_lexists(current) and is_reparse_point(current):
        fail(f"reparse point is not allowed: {current}")
    for part in parts:
        current = current / part
        if path_lexists(current) and is_reparse_point(current):
            fail(f"symlink/junction/reparse path component is not allowed: {current}")


def safe_new_project_root(path: str | Path) -> Path:
    root = lexical_path(path)
    check_existing_components(root)
    if path_lexists(root) and not root.is_dir():
        fail(f"project path is not a directory: {root}")
    return root


def project_marker(root: Path) -> Path:
    return lexical_path(root) / MARKER_NAME


def is_within(path: str | Path, root: str | Path) -> bool:
    candidate = lexical_path(path)
    boundary = lexical_path(root)
    try:
        return os.path.commonpath([str(candidate), str(boundary)]) == str(boundary)
    except ValueError:
        return False


def safe_project_path(project_root: str | Path, target: str | Path, must_exist: bool = False) -> Path:
    project = lexical_path(project_root)
    raw_target = Path(target)
    candidate = lexical_path(raw_target if raw_target.is_absolute() else project / raw_target)
    if not is_within(candidate, project):
        fail(f"path escapes project directory: {candidate}")
    check_existing_components(project)
    check_existing_components(candidate, stop_at=project)
    if must_exist and not path_lexists(candidate):
        fail(f"project path does not exist: {candidate}")
    if path_lexists(candidate) and is_reparse_point(candidate):
        fail(f"project path cannot be a symlink/junction/reparse point: {candidate}")
    return candidate


def safe_project_dir(project_root: str | Path, relative: str | Path) -> Path:
    project = lexical_path(project_root)
    target = safe_project_path(project, relative)
    current = project
    for part in target.relative_to(project).parts:
        current = current / part
        if path_lexists(current):
            if is_reparse_point(current) or not current.is_dir():
                fail(f"unsafe project directory component: {current}")
        else:
            current.mkdir()
            if is_reparse_point(current):
                fail(f"new project directory became a reparse point: {current}")
    return target


def assert_project_root(path: str | Path) -> Path:
    root = lexical_path(path)
    if not root.is_dir():
        fail(f"project directory does not exist: {root}")
    check_existing_components(root)
    marker = safe_project_path(root, MARKER_NAME, must_exist=True)
    if not marker.is_file():
        fail(f"not a marked mom-dialogue project: {root}")
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid project marker: {marker}: {exc}")
    if data.get("project_type") != "fbsir-mom-dialogue":
        fail(f"unsupported project marker: {marker}")
    if data.get("write_scope") != "project-directory-only" or data.get("source_files_read_only") is not True:
        fail(f"project marker safety policy is missing or changed: {marker}")
    return root


def initialize_marker(root: Path) -> Path:
    root = safe_new_project_root(root)
    if not root.exists():
        root.mkdir(parents=True)
    marker = safe_project_path(root, MARKER_NAME)
    if not marker.exists():
        write_json_atomic(
            marker,
            {
                "project_type": "fbsir-mom-dialogue",
                "schema_version": "2.0",
                "created_at": iso_now(),
                "source_files_read_only": True,
                "write_scope": "project-directory-only",
                "source_roots_registered": [],
            },
            project_root=root,
        )
    return marker


def assert_project_output(output: str | Path, project_root: Path, source_root: Path | None = None) -> Path:
    del source_root
    return safe_project_path(project_root, output)


def assert_project_input(
    project_root: Path,
    input_path: str | Path,
    allowed_relative_dirs: Iterable[str] | None = None,
) -> Path:
    path = safe_project_path(project_root, input_path, must_exist=True)
    if not path.is_file():
        fail(f"project input is not a file: {path}")
    if allowed_relative_dirs:
        allowed = [safe_project_path(project_root, item) for item in allowed_relative_dirs]
        if not any(is_within(path, directory) for directory in allowed):
            fail(f"project input is outside allowed project directories: {path}")
    return path


def safe_source_scope(source_root: str | Path, scope: str | Path = "") -> Path:
    root = lexical_path(source_root)
    scope_path = Path(scope)
    if scope_path.drive or scope_path.root or scope_path.is_absolute():
        fail(f"source scope must be relative: {scope}")
    if any(part in {"..", ""} for part in scope_path.parts):
        fail(f"source scope contains an unsafe component: {scope}")
    candidate = lexical_path(root / scope_path)
    if not is_within(candidate, root):
        fail(f"source scope escapes registered root: {candidate}")
    if path_lexists(root):
        check_existing_components(root)
        check_existing_components(candidate, stop_at=root)
    return candidate


def iter_safe_files(
    root: Path,
    include_hidden: bool = False,
    exclude_roots: Iterable[Path] = (),
    on_skip: Callable[[Path, str], None] | None = None,
) -> Iterator[Path]:
    root = lexical_path(root)
    if not root.is_dir():
        fail(f"scan root is not a directory: {root}")
    check_existing_components(root)
    excluded = [lexical_path(item) for item in exclude_roots]
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = lexical_path(current)
        safe_dirs = []
        for name in sorted(dirs):
            path = current_path / name
            if name in EXCLUDED_PARTS or (not include_hidden and name.startswith(".")):
                if on_skip:
                    on_skip(path, "excluded_directory")
                continue
            if is_reparse_point(path):
                if on_skip:
                    on_skip(path, "reparse_directory")
                continue
            if any(is_within(path, item) for item in excluded):
                if on_skip:
                    on_skip(path, "excluded_output_root")
                continue
            safe_dirs.append(name)
        dirs[:] = safe_dirs
        for name in sorted(files):
            path = current_path / name
            if is_reparse_point(path):
                if on_skip:
                    on_skip(path, "reparse_file")
                continue
            if not path.is_file():
                if on_skip:
                    on_skip(path, "not_regular_file")
                continue
            if name in EXCLUDED_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES:
                if on_skip:
                    on_skip(path, "excluded_file")
                continue
            if not include_hidden and name.startswith("."):
                if on_skip:
                    on_skip(path, "hidden_file")
                continue
            if any(is_within(path, item) for item in excluded):
                if on_skip:
                    on_skip(path, "excluded_output_root")
                continue
            yield path


def relative_posix(path: Path, root: Path) -> str:
    candidate = lexical_path(path)
    boundary = lexical_path(root)
    if not is_within(candidate, boundary):
        fail(f"cannot make source-relative path outside root: {candidate}")
    return candidate.relative_to(boundary).as_posix()


def safe_csv_value(value: object) -> str:
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(FORMULA_PREFIXES) else text


def unwrap_csv_value(value: str) -> str:
    if len(value) > 1 and value.startswith("'") and value[1] in FORMULA_PREFIXES:
        return value[1:]
    return value


def fsync_directory(path: Path) -> None:
    try:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        descriptor = os.open(str(path), flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_bytes(path: str | Path, data: bytes, project_root: Path | None = None) -> Path:
    target = safe_project_path(project_root, path) if project_root is not None else lexical_path(path)
    if path_lexists(target) and is_reparse_point(target):
        fail(f"refuse to overwrite symlink/junction/reparse target: {target}")
    if not target.parent.exists():
        if project_root is None:
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            safe_project_dir(project_root, target.parent.relative_to(lexical_path(project_root)))
    check_existing_components(target.parent)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        check_existing_components(target.parent)
        if path_lexists(target) and is_reparse_point(target):
            fail(f"target became unsafe before commit: {target}")
        os.replace(temporary_name, target)
        fsync_directory(target.parent)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return target


def create_bytes_exclusive(path: str | Path, data: bytes, project_root: Path) -> Path:
    target = safe_project_path(project_root, path)
    if not target.parent.exists():
        safe_project_dir(project_root, target.parent.relative_to(lexical_path(project_root)))
    descriptor = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        fsync_directory(target.parent)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(target)
        raise
    return target


def write_text_atomic(path: str | Path, text: str, project_root: Path | None = None) -> Path:
    return atomic_write_bytes(path, text.encode("utf-8"), project_root)


def write_json_atomic(path: str | Path, value: object, project_root: Path | None = None) -> Path:
    return write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n", project_root)


def create_json_exclusive(path: str | Path, value: object, project_root: Path) -> Path:
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return create_bytes_exclusive(path, payload, project_root)


def csv_bytes(fieldnames: list[str], rows: Iterable[dict[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: safe_csv_value(row.get(key, "")) for key in fieldnames})
    return buffer.getvalue().encode("utf-8")


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: Iterable[dict[str, object]],
    project_root: Path | None = None,
) -> None:
    atomic_write_bytes(path, csv_bytes(fieldnames, rows), project_root)


def read_csv(path: Path, required: bool = False) -> list[dict[str, str]]:
    if not path_lexists(path):
        if required:
            fail(f"required CSV does not exist: {path}")
        return []
    if is_reparse_point(path) or not path.is_file():
        fail(f"unsafe or invalid CSV input: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: unwrap_csv_value(value or "") for key, value in row.items()} for row in csv.DictReader(handle)]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_digest(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def append_quality_issue(project_root: Path, relative_path: str, issue: str, detail: str = "") -> None:
    path = safe_project_path(project_root, "02_素材账/质量问题.csv")
    rows = read_csv(path)
    fields = schema_fields(schema_path("quality-issue.schema.json"))
    rows.append({"relative_path": relative_path, "issue": issue, "detail": detail, "status": "observed", "recorded_at": iso_now()})
    write_csv(path, fields, rows, project_root=project_root)


def load_schema(schema_file: Path) -> dict:
    data = json.loads(schema_file.read_text(encoding="utf-8"))
    if data.get("type") != "object" or not isinstance(data.get("properties"), dict):
        fail(f"invalid object schema: {schema_file}")
    return data


def schema_fields(schema_file: Path) -> list[str]:
    return list(load_schema(schema_file)["properties"].keys())


def schema_path(name: str) -> Path:
    schema_root = Path(__file__).resolve().parents[1] / "schemas"
    candidate = schema_root / name
    if candidate.parent != schema_root:
        fail(f"invalid schema name: {name}")
    return candidate


def ensure_csv_schema(
    project_root: Path,
    relative_csv: str,
    schema_filename: str,
    repair: bool = False,
) -> tuple[Path, list[str], bool]:
    path = safe_project_path(project_root, relative_csv)
    fields = schema_fields(schema_path(schema_filename))
    if not path.exists():
        if repair:
            write_csv(path, fields, [], project_root=project_root)
        return path, fields, True
    if is_reparse_point(path):
        fail(f"unsafe ledger: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        header = next(csv.reader(handle), [])
    if header == fields:
        return path, fields, False
    if not repair:
        return path, fields, True
    backup = path.with_name(f"{path.stem}.migration-{utc_stamp()}{path.suffix}")
    atomic_write_bytes(backup, path.read_bytes(), project_root=project_root)
    write_csv(path, fields, read_csv(path), project_root=project_root)
    return path, fields, True


def parse_json_array(value: str | None, label: str = "value") -> list[str]:
    if not value or not value.strip():
        return []
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        fail(f"{label} must be a JSON array string: {exc}")
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        fail(f"{label} must be a JSON array of strings")
    return data


def json_arg(value: str, default: object) -> object:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON argument: {exc}")


@contextlib.contextmanager
def project_file_lock(project_root: Path, name: str) -> Iterator[None]:
    """Acquire one crash-released OS file lock for a project transaction."""
    if not re.fullmatch(r"[a-z0-9-]+", name):
        fail(f"invalid lock name: {name}")
    lock_dir = safe_project_dir(project_root, "12_版本与检查点/locks")
    lock_path = safe_project_path(project_root, lock_dir / f"{name}.lock")
    handle = lock_path.open("a+b")
    acquired = False
    try:
        if lock_path.stat().st_size == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError:
            fail(f"project transaction is already running: {name}")
        yield
    finally:
        try:
            if acquired:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()
