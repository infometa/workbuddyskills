"""Streaming, checkpointed source inventory without premature content hashing."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import sqlite3
import stat
import unicodedata
import uuid
from collections.abc import Callable, Iterator
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Final

from mibao_core.errors import MibaoError
from mibao_core.filesystem.paths import (
    AuthorizedPath,
    FileIdentity,
    PathPolicy,
    to_filesystem_api_path,
    validate_root_pair,
    validate_windows_path_syntax,
)
from mibao_core.project import Project, open_project_writer

_DEFAULT_IGNORES: Final[tuple[str, ...]] = (
    ".mibao",
    ".mibao/**",
    "_MIBAO_OUTPUT",
    "_MIBAO_OUTPUT/**",
)
_OPERATION_TYPE: Final = "scan_candidate"
_TestHook = Callable[[str, int], None]
_SCAN_SPEC_BASE_KEYS: Final = frozenset(
    {
        "allow_unc",
        "batch_size",
        "ignore_patterns",
        "max_depth",
        "max_entries",
        "max_reported_issues",
        "privacy_mode",
        "schema_version",
        "source_root_id",
    }
)
_LEGACY_SCAN_SPEC_KEYS: Final = _SCAN_SPEC_BASE_KEYS - {"allow_unc", "max_reported_issues"}
_RECOVERY_RECEIPT_KEYS: Final = frozenset(
    {
        "schema_version",
        "attempt_id",
        "attempt_number",
        "fence_epoch",
        "scan_spec_sha256",
        "started_at",
        "prior_job_status",
        "recovery_mode",
        "prior_durable_operation_count",
        "prior_operation_set_sha256",
        "recovered_abandoned_running_state",
        "database_integrity_check",
        "foreign_key_violation_count",
        "journal_mode",
        "synchronous",
        "source_state_at_attempt_start",
    }
)


@dataclass(frozen=True, slots=True)
class ScanPolicy:
    """Finite scanner budgets and explicit relative-path ignore patterns."""

    batch_size: int = 256
    max_entries: int = 1_000_000
    max_depth: int = 64
    max_reported_issues: int = 100
    ignore_patterns: tuple[str, ...] = ()
    allow_unc: bool = False

    def __post_init__(self) -> None:
        if not 1 <= self.batch_size <= 1000:
            raise MibaoError("MB-SCAN-0001", "Scan batch size must be between 1 and 1000")
        if not 1 <= self.max_entries <= 10_000_000:
            raise MibaoError("MB-SCAN-0001", "Scan entry limit must be finite and positive")
        if not 1 <= self.max_depth <= 128:
            raise MibaoError("MB-SCAN-0001", "Scan depth must be between 1 and 128")
        if not 0 <= self.max_reported_issues <= 1000:
            raise MibaoError("MB-SCAN-0001", "Reported issue limit must be between 0 and 1000")
        for pattern in self.ignore_patterns:
            _validate_ignore_pattern(pattern)

    @property
    def effective_ignore_patterns(self) -> tuple[str, ...]:
        return (*_DEFAULT_IGNORES, *self.ignore_patterns)


@dataclass(frozen=True, slots=True)
class ScanIssue:
    code: str
    relative_path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "relative_path": self.relative_path,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class ScanRecoveryReceipt:
    schema_version: str
    attempt_id: str
    attempt_number: int
    fence_epoch: int
    scan_spec_sha256: str
    started_at: str
    prior_job_status: str | None
    recovery_mode: str
    prior_durable_operation_count: int
    prior_operation_set_sha256: str
    recovered_abandoned_running_state: bool
    database_integrity_check: str
    foreign_key_violation_count: int
    journal_mode: str
    synchronous: str
    source_state_at_attempt_start: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "attempt_id": self.attempt_id,
            "attempt_number": self.attempt_number,
            "fence_epoch": self.fence_epoch,
            "scan_spec_sha256": self.scan_spec_sha256,
            "started_at": self.started_at,
            "prior_job_status": self.prior_job_status,
            "recovery_mode": self.recovery_mode,
            "prior_durable_operation_count": self.prior_durable_operation_count,
            "prior_operation_set_sha256": self.prior_operation_set_sha256,
            "recovered_abandoned_running_state": self.recovered_abandoned_running_state,
            "database_integrity_check": self.database_integrity_check,
            "foreign_key_violation_count": self.foreign_key_violation_count,
            "journal_mode": self.journal_mode,
            "synchronous": self.synchronous,
            "source_state_at_attempt_start": self.source_state_at_attempt_start,
        }


@dataclass(frozen=True, slots=True)
class ScanCompletenessSnapshot:
    source_root_ids: tuple[str, ...]
    complete: bool
    pending_reasons: tuple[str, ...]
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "source_root_ids": list(self.source_root_ids),
            "complete": self.complete,
            "pending_reasons": list(self.pending_reasons),
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class ScanResult:
    project_id: str
    source_root_id: str
    job_id: str
    status: str
    discovered_files: int
    inserted_candidates: int
    changed_candidates: int
    unchanged_candidates: int
    missing_candidates: int
    ignored_entries: int
    rejected_reparse_entries: int
    rejected_unsafe_entries: int
    unreadable_entries: int
    committed_batches: int
    max_batch_entries: int
    max_directory_depth: int
    resumed: bool
    source_state: str
    recovery: ScanRecoveryReceipt
    completion: ScanCompletenessSnapshot
    issues: tuple[ScanIssue, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "source_root_id": self.source_root_id,
            "job_id": self.job_id,
            "status": self.status,
            "discovered_files": self.discovered_files,
            "inserted_candidates": self.inserted_candidates,
            "changed_candidates": self.changed_candidates,
            "unchanged_candidates": self.unchanged_candidates,
            "missing_candidates": self.missing_candidates,
            "ignored_entries": self.ignored_entries,
            "rejected_reparse_entries": self.rejected_reparse_entries,
            "rejected_unsafe_entries": self.rejected_unsafe_entries,
            "unreadable_entries": self.unreadable_entries,
            "committed_batches": self.committed_batches,
            "max_batch_entries": self.max_batch_entries,
            "max_directory_depth": self.max_directory_depth,
            "resumed": self.resumed,
            "source_state": self.source_state,
            "recovery": self.recovery.as_dict(),
            "completion": self.completion.as_dict(),
            "issues": [issue.as_dict() for issue in self.issues],
        }


@dataclass(frozen=True, slots=True)
class _Candidate:
    operation_id: str
    request_json: str


@dataclass(slots=True)
class _WalkState:
    discovered_files: int = 0
    ignored_entries: int = 0
    rejected_reparse_entries: int = 0
    rejected_unsafe_entries: int = 0
    unreadable_entries: int = 0
    max_directory_depth: int = 0
    incomplete: bool = False
    source_offline: bool = False
    issues: list[ScanIssue] = field(default_factory=list)


class _ScanInterrupted(Exception):
    pass


class _SourceOffline(Exception):
    pass


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _validate_ignore_pattern(pattern: str) -> None:
    if (
        not isinstance(pattern, str)
        or not pattern
        or len(pattern) > 512
        or "\0" in pattern
        or any(ord(character) < 32 for character in pattern)
    ):
        raise MibaoError("MB-SCAN-0001", "Ignore pattern is empty, oversized, or invalid")
    normalized = pattern.replace("\\", "/")
    pure_posix = PurePosixPath(normalized)
    pure_windows = PureWindowsPath(pattern)
    if pure_posix.is_absolute() or pure_windows.is_absolute() or pure_windows.drive:
        raise MibaoError("MB-SCAN-0001", "Ignore patterns must be project-relative")
    if ".." in pure_posix.parts:
        raise MibaoError("MB-SCAN-0001", "Ignore patterns must not contain parent traversal")


def _pattern_key(value: str) -> str:
    return value.casefold() if os.name == "nt" else value


def _is_ignored(relative_path: str, patterns: tuple[str, ...]) -> bool:
    candidate = _pattern_key(relative_path)
    return any(
        fnmatch.fnmatchcase(candidate, _pattern_key(pattern.replace("\\", "/")))
        for pattern in patterns
    )


def _entry_is_reparse(entry: os.DirEntry[str], metadata: os.stat_result) -> bool:
    if entry.is_symlink():
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_attribute)


def _entry_identity(
    entry: os.DirEntry[str],
    *,
    is_file: bool,
) -> FileIdentity:
    initial = os.stat(entry.path, follow_symlinks=False)
    current = os.stat(entry.path, follow_symlinks=False)
    expected_key = (
        initial.st_dev,
        initial.st_ino,
        initial.st_mode,
        initial.st_size if is_file else None,
        initial.st_mtime_ns if is_file else None,
    )
    current_key = (
        current.st_dev,
        current.st_ino,
        current.st_mode,
        current.st_size if is_file else None,
        current.st_mtime_ns if is_file else None,
    )
    if current_key != expected_key:
        raise MibaoError("MB-FS-0006", "Scan entry identity changed before checkpoint")
    return FileIdentity(
        device=current.st_dev,
        inode=current.st_ino,
        mode=current.st_mode,
        size=current.st_size if is_file else None,
        modified_ns=current.st_mtime_ns if is_file else None,
    )


def _source_key(project_id: str, source_root: Path) -> str:
    text = str(source_root)
    normalized = text.casefold() if os.name == "nt" else text
    digest = hashlib.sha256(f"{project_id}\0{normalized}".encode()).hexdigest()
    return "SRC-" + digest[:32]


def _job_key(project_id: str, source_root_id: str) -> str:
    digest = hashlib.sha256(f"{project_id}\0{source_root_id}".encode()).hexdigest()
    return "JOB-SCAN-" + digest[:32]


def _operation_key(project_id: str, source_root_id: str, relative_path: str) -> str:
    path_key = _pattern_key(relative_path)
    digest = hashlib.sha256(f"{project_id}\0{source_root_id}\0{path_key}".encode()).hexdigest()
    return "OP-SCAN-" + digest[:32]


def stat_change_token(identity: FileIdentity) -> str:
    """Hash stat facts for cache invalidation; this is explicitly not a content hash."""

    if identity.size is None or identity.modified_ns is None:
        raise MibaoError("MB-SCAN-0002", "File stat identity lacks size or modified time")
    return hashlib.sha256(
        (f"{identity.device}\0{identity.inode}\0{identity.size}\0{identity.modified_ns}").encode(
            "ascii"
        )
    ).hexdigest()


def _database_recovery_facts(connection: sqlite3.Connection) -> tuple[str, int, str, str]:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()
    foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
    journal = connection.execute("PRAGMA journal_mode").fetchone()
    synchronous = connection.execute("PRAGMA synchronous").fetchone()
    if integrity != ("ok",) or foreign_keys:
        raise MibaoError("MB-SCAN-0007", "SQLite recovery integrity checks failed")
    journal_mode = str(journal[0]).lower() if journal else ""
    synchronous_mode = {0: "off", 1: "normal", 2: "full", 3: "extra"}.get(
        int(synchronous[0]) if synchronous else -1,
        "unknown",
    )
    if journal_mode != "delete" or synchronous_mode != "full":
        raise MibaoError("MB-SCAN-0007", "SQLite recovery durability policy drifted")
    return "ok", 0, journal_mode, synchronous_mode


def _operation_checkpoint(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    job_id: str,
    attempt_id: str | None = None,
) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    sql = (
        "SELECT operation_id, request_json, "
        "json_extract(result_json, '$.present'), "
        "json_extract(result_json, '$.scan_attempt_id'), created_at "
        "FROM operations WHERE project_id=? AND job_id=? AND operation_type=?"
    )
    parameters: tuple[object, ...] = (project_id, job_id, _OPERATION_TYPE)
    if attempt_id is not None:
        sql += " AND json_extract(result_json, '$.scan_attempt_id')=?"
        parameters = (*parameters, attempt_id)
    sql += " ORDER BY operation_id"
    for row in connection.execute(sql, parameters):
        digest.update(_json(list(row)).encode())
        digest.update(b"\n")
        count += 1
    return count, digest.hexdigest()


def _scan_operation_set(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    job_id: str,
) -> tuple[int, str]:
    return _operation_checkpoint(
        connection,
        project_id=project_id,
        job_id=job_id,
    )


def _scan_contract(
    *,
    policy: ScanPolicy,
    privacy_mode: str,
    source_root_id: str,
) -> dict[str, Any]:
    return {
        "allow_unc": policy.allow_unc,
        "batch_size": policy.batch_size,
        "ignore_patterns": list(policy.effective_ignore_patterns),
        "max_depth": policy.max_depth,
        "max_entries": policy.max_entries,
        "max_reported_issues": policy.max_reported_issues,
        "privacy_mode": privacy_mode,
        "schema_version": "1.0",
        "source_root_id": source_root_id,
    }


def _scan_contract_sha256(contract: dict[str, Any]) -> str:
    if set(contract) != _SCAN_SPEC_BASE_KEYS:
        raise MibaoError("MB-SCAN-0007", "Scan recovery contract keys drifted")
    return hashlib.sha256(_json(contract).encode()).hexdigest()


def _is_lower_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_recovery_semantics(
    recovery: dict[str, Any],
    *,
    contract_sha256: str,
) -> tuple[int, str]:
    attempt = recovery.get("attempt_number")
    fence_epoch = recovery.get("fence_epoch")
    attempt_id = recovery.get("attempt_id")
    prior_status = recovery.get("prior_job_status")
    source_state = recovery.get("source_state_at_attempt_start")
    prior_count = recovery.get("prior_durable_operation_count")
    started_at = recovery.get("started_at")
    foreign_key_count = recovery.get("foreign_key_violation_count")
    valid_source_state = isinstance(source_state, str) and source_state in ("active", "offline")
    valid_prior_status = prior_status is None or (
        isinstance(prior_status, str)
        and prior_status in ("queued", "running", "succeeded", "failed", "cancelled", "interrupted")
    )
    if (
        recovery.get("schema_version") != "1.0"
        or not isinstance(attempt, int)
        or isinstance(attempt, bool)
        or attempt < 1
        or not isinstance(fence_epoch, int)
        or isinstance(fence_epoch, bool)
        or fence_epoch != attempt
        or not isinstance(attempt_id, str)
        or len(attempt_id) != 41
        or not attempt_id.startswith("RUN-SCAN-")
        or any(character not in "0123456789abcdef" for character in attempt_id[9:])
        or recovery.get("scan_spec_sha256") != contract_sha256
        or not _is_lower_sha256(recovery.get("prior_operation_set_sha256"))
        or not isinstance(prior_count, int)
        or isinstance(prior_count, bool)
        or prior_count < 0
        or recovery.get("database_integrity_check") != "ok"
        or not isinstance(foreign_key_count, int)
        or isinstance(foreign_key_count, bool)
        or foreign_key_count != 0
        or recovery.get("journal_mode") != "delete"
        or recovery.get("synchronous") != "full"
        or not valid_source_state
        or not valid_prior_status
        or not isinstance(recovery.get("recovered_abandoned_running_state"), bool)
        or not isinstance(started_at, str)
    ):
        raise MibaoError("MB-SCAN-0007", "Prior recovery receipt semantics drifted")
    try:
        parsed_started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MibaoError("MB-SCAN-0007", "Prior recovery timestamp drifted") from exc
    if parsed_started_at.tzinfo is None:
        raise MibaoError("MB-SCAN-0007", "Prior recovery timestamp lacks a timezone")
    source_offline = source_state == "offline"
    if source_offline and prior_status is None:
        raise MibaoError("MB-SCAN-0007", "Offline recovery lacks a prior job state")
    expected_mode = _recovery_mode(prior_status, source_offline=source_offline)
    expected_recovered = prior_status == "running" and not source_offline
    if (
        recovery.get("recovery_mode") != expected_mode
        or recovery.get("recovered_abandoned_running_state") is not expected_recovered
        or (prior_status is None and (attempt != 1 or prior_count != 0))
        or (prior_status is not None and attempt < 2)
    ):
        raise MibaoError("MB-SCAN-0007", "Prior recovery mode/status pairing drifted")
    return attempt, attempt_id


def _parse_prior_spec(spec_text: object) -> tuple[int, str, str | None, dict[str, Any]]:
    if not isinstance(spec_text, str):
        raise MibaoError("MB-SCAN-0007", "Prior scan recovery spec is missing")
    try:
        payload = json.loads(spec_text)
    except json.JSONDecodeError as exc:
        raise MibaoError("MB-SCAN-0007", "Prior scan recovery spec is invalid JSON") from exc
    if not isinstance(payload, dict) or set(payload) not in {
        _SCAN_SPEC_BASE_KEYS,
        _SCAN_SPEC_BASE_KEYS | {"recovery"},
        _LEGACY_SCAN_SPEC_KEYS,
    }:
        raise MibaoError("MB-SCAN-0007", "Prior scan recovery spec shape drifted")
    if set(payload) == _LEGACY_SCAN_SPEC_KEYS:
        payload = {**payload, "allow_unc": False, "max_reported_issues": 100}
    contract = {key: payload[key] for key in _SCAN_SPEC_BASE_KEYS}
    contract_sha256 = _scan_contract_sha256(contract)
    recovery = payload.get("recovery")
    if recovery is None:
        return 1, contract_sha256, None, contract
    if not isinstance(recovery, dict) or set(recovery) != _RECOVERY_RECEIPT_KEYS:
        raise MibaoError("MB-SCAN-0007", "Prior recovery receipt shape drifted")
    attempt, attempt_id = _validate_recovery_semantics(
        recovery,
        contract_sha256=contract_sha256,
    )
    return attempt, contract_sha256, attempt_id, contract


def _recovery_mode(prior_status: str | None, *, source_offline: bool = False) -> str:
    if source_offline:
        return "source_offline_observation"
    return {
        None: "fresh",
        "queued": "queued_resume",
        "running": "abandoned_running_resume",
        "succeeded": "repeat_completed",
        "failed": "failed_resume",
        "cancelled": "cancelled_resume",
        "interrupted": "controlled_resume",
    }[prior_status]


def _recovery_receipt(
    *,
    attempt_id: str,
    attempt_number: int,
    scan_spec_sha256: str,
    started_at: str,
    prior_job_status: str | None,
    prior_durable_operation_count: int,
    prior_operation_set_sha256: str,
    database_facts: tuple[str, int, str, str],
    source_state_at_attempt_start: str,
    source_offline: bool = False,
) -> ScanRecoveryReceipt:
    integrity, foreign_key_count, journal_mode, synchronous_mode = database_facts
    return ScanRecoveryReceipt(
        schema_version="1.0",
        attempt_id=attempt_id,
        attempt_number=attempt_number,
        fence_epoch=attempt_number,
        scan_spec_sha256=scan_spec_sha256,
        started_at=started_at,
        prior_job_status=prior_job_status,
        recovery_mode=_recovery_mode(prior_job_status, source_offline=source_offline),
        prior_durable_operation_count=prior_durable_operation_count,
        prior_operation_set_sha256=prior_operation_set_sha256,
        recovered_abandoned_running_state=prior_job_status == "running" and not source_offline,
        database_integrity_check=integrity,
        foreign_key_violation_count=foreign_key_count,
        journal_mode=journal_mode,
        synchronous=synchronous_mode,
        source_state_at_attempt_start=source_state_at_attempt_start,
    )


def _scan_spec(
    *,
    policy: ScanPolicy,
    privacy_mode: str,
    source_root_id: str,
    recovery: ScanRecoveryReceipt,
) -> str:
    contract = _scan_contract(
        policy=policy,
        privacy_mode=privacy_mode,
        source_root_id=source_root_id,
    )
    return _scan_spec_from_contract(contract, recovery)


def _scan_spec_from_contract(
    contract: dict[str, Any],
    recovery: ScanRecoveryReceipt,
) -> str:
    _scan_contract_sha256(contract)
    payload = dict(contract)
    payload["recovery"] = recovery.as_dict()
    return _json(payload)


def _assert_attempt_fence(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    job_id: str,
    attempt_id: str,
    attempt_number: int,
    scan_spec_sha256: str,
) -> None:
    row = connection.execute(
        "SELECT status, spec_json FROM jobs WHERE project_id=? AND job_id=?",
        (project_id, job_id),
    ).fetchone()
    if row is None or row[0] != "running":
        raise MibaoError("MB-SCAN-0007", "Scan writer attempt/spec fence is stale")
    parsed_attempt, parsed_spec_sha256, parsed_attempt_id, _contract = _parse_prior_spec(row[1])
    if (
        parsed_attempt_id != attempt_id
        or parsed_attempt != attempt_number
        or parsed_spec_sha256 != scan_spec_sha256
    ):
        raise MibaoError("MB-SCAN-0007", "Scan writer attempt/spec fence is stale")


def compute_scan_completeness_snapshot(
    connection: sqlite3.Connection,
    project_id: str,
) -> ScanCompletenessSnapshot:
    """Current-read all registered inventory jobs and their attempt fences."""

    source_rows = connection.execute(
        "SELECT source_root_id, state FROM source_roots "
        "WHERE project_id=? AND state<>'removed' ORDER BY source_root_id",
        (project_id,),
    ).fetchall()
    digest = hashlib.sha256()
    digest.update(b"mibao.scan-completeness.v1\0")
    pending: list[str] = []
    source_root_ids: list[str] = []
    if not source_rows:
        pending.append("project:no_registered_source")
    for raw_source_id, raw_source_state in source_rows:
        source_root_id = str(raw_source_id)
        source_state = str(raw_source_state)
        source_root_ids.append(source_root_id)
        job_id = _job_key(project_id, source_root_id)
        job = connection.execute(
            "SELECT status, spec_json FROM jobs "
            "WHERE project_id=? AND job_id=? AND goal='inventory'",
            (project_id, job_id),
        ).fetchone()
        job_status = str(job[0]) if job is not None else "missing"
        spec_text = str(job[1]) if job is not None else ""
        attempt_id = ""
        attempt_number = 0
        fence_epoch = 0
        scan_spec_sha256 = ""
        spec_valid = False
        if spec_text:
            try:
                spec_payload = json.loads(spec_text)
                (
                    attempt_number,
                    scan_spec_sha256,
                    _prior_attempt_id,
                    _prior_contract,
                ) = _parse_prior_spec(spec_text)
            except (json.JSONDecodeError, MibaoError):
                spec_payload = None
            recovery = spec_payload.get("recovery") if isinstance(spec_payload, dict) else None
            attempt_id_value = recovery.get("attempt_id") if isinstance(recovery, dict) else None
            fence_value = recovery.get("fence_epoch") if isinstance(recovery, dict) else None
            spec_valid = (
                isinstance(spec_payload, dict)
                and isinstance(recovery, dict)
                and spec_payload.get("schema_version") == "1.0"
                and spec_payload.get("source_root_id") == source_root_id
                and isinstance(attempt_id_value, str)
                and attempt_id_value.startswith("RUN-SCAN-")
                and len(attempt_id_value) == 41
                and isinstance(fence_value, int)
                and not isinstance(fence_value, bool)
                and fence_value == attempt_number
                and recovery.get("scan_spec_sha256") == scan_spec_sha256
                and recovery.get("source_state_at_attempt_start") == source_state
            )
            if spec_valid and isinstance(fence_value, int):
                attempt_id = str(attempt_id_value)
                fence_epoch = fence_value
        nonterminal = int(
            connection.execute(
                "SELECT count(*) FROM operations WHERE project_id=? AND job_id=? "
                "AND operation_type=? AND status IN ('queued', 'running')",
                (project_id, job_id, _OPERATION_TYPE),
            ).fetchone()[0]
        )
        stale_present_fence = int(
            connection.execute(
                "SELECT count(*) FROM operations WHERE project_id=? AND job_id=? "
                "AND operation_type=? AND json_extract(result_json, '$.present')=1 "
                "AND coalesce(json_extract(result_json, '$.scan_attempt_id'), '')<>?",
                (project_id, job_id, _OPERATION_TYPE, attempt_id),
            ).fetchone()[0]
        )
        operation_count, operation_digest = _scan_operation_set(
            connection,
            project_id=project_id,
            job_id=job_id,
        )
        if source_state != "active":
            pending.append(f"{source_root_id}:source_{source_state}")
        if job_status != "succeeded":
            pending.append(f"{source_root_id}:job_{job_status}")
        if not spec_valid:
            pending.append(f"{source_root_id}:recovery_spec_invalid")
        if nonterminal:
            pending.append(f"{source_root_id}:nonterminal_operations_{nonterminal}")
        if stale_present_fence:
            pending.append(f"{source_root_id}:stale_present_fence_{stale_present_fence}")
        digest.update(
            _json(
                {
                    "source_root_id": source_root_id,
                    "source_state": source_state,
                    "job_id": job_id,
                    "job_status": job_status,
                    "attempt_id": attempt_id,
                    "attempt_number": attempt_number,
                    "fence_epoch": fence_epoch,
                    "scan_spec_sha256": scan_spec_sha256,
                    "spec_valid": spec_valid,
                    "operation_count": operation_count,
                    "operation_set_sha256": operation_digest,
                    "nonterminal_operation_count": nonterminal,
                    "stale_present_fence_count": stale_present_fence,
                }
            ).encode()
        )
        digest.update(b"\n")
    return ScanCompletenessSnapshot(
        source_root_ids=tuple(source_root_ids),
        complete=not pending,
        pending_reasons=tuple(pending),
        sha256=digest.hexdigest(),
    )


def _record_issue(
    state: _WalkState,
    policy: ScanPolicy,
    *,
    code: str,
    relative_path: str,
    message: str,
) -> None:
    if len(state.issues) < policy.max_reported_issues:
        state.issues.append(ScanIssue(code, relative_path, message))


def _candidate_from_identity(
    relative_path: str,
    identity: FileIdentity,
    *,
    project_id: str,
    source_root_id: str,
) -> _Candidate:
    if identity.size is None or identity.modified_ns is None:
        raise MibaoError("MB-SCAN-0002", "Authorized scan file has no stable stat identity")
    relative = unicodedata.normalize("NFC", relative_path)
    request = {
        "change_token": stat_change_token(identity),
        "identity": {
            "device": identity.device,
            "inode": identity.inode,
            "mode": identity.mode,
        },
        "modified_time_ms": identity.modified_ns // 1_000_000,
        "relative_path": relative,
        "schema_version": "1.0",
        "size_bytes": identity.size,
        "source_root_id": source_root_id,
    }
    return _Candidate(
        operation_id=_operation_key(project_id, source_root_id, relative),
        request_json=_json(request),
    )


def _walk_candidates(
    source: AuthorizedPath,
    *,
    project_id: str,
    source_root_id: str,
    scan_policy: ScanPolicy,
    path_policy: PathPolicy,
    cancel_check: Callable[[], bool],
    state: _WalkState,
) -> Iterator[_Candidate]:
    patterns = scan_policy.effective_ignore_patterns

    def walk(directory: Path, depth: int) -> Iterator[_Candidate]:
        if cancel_check():
            raise _ScanInterrupted
        state.max_directory_depth = max(state.max_directory_depth, depth)
        try:
            iterator = os.scandir(to_filesystem_api_path(directory, policy=path_policy))
        except OSError as exc:
            relative = directory.relative_to(source.path).as_posix() or "."
            state.unreadable_entries += 1
            state.incomplete = True
            state.source_offline = directory == source.path
            _record_issue(
                state,
                scan_policy,
                code="MB-SCAN-0002",
                relative_path=relative,
                message=f"Directory cannot be enumerated: {type(exc).__name__}",
            )
            return
        with iterator:
            for entry in iterator:
                if cancel_check():
                    raise _ScanInterrupted
                # ``DirEntry.path`` inherits the internal Windows ``\\?\\`` prefix used by
                # scandir; reconstruct the logical path so containment compares like with like.
                entry_path = directory / entry.name
                try:
                    relative = entry_path.relative_to(source.path).as_posix()
                except ValueError:
                    state.unreadable_entries += 1
                    state.incomplete = True
                    _record_issue(
                        state,
                        scan_policy,
                        code="MB-FS-0002",
                        relative_path="<outside-root>",
                        message="Directory entry escaped the authorized source root",
                    )
                    continue
                if _is_ignored(relative, patterns):
                    state.ignored_entries += 1
                    continue
                try:
                    validate_windows_path_syntax(
                        entry_path,
                        allow_unc=path_policy.allow_unc,
                        policy=path_policy,
                    )
                    metadata = entry.stat(follow_symlinks=False)
                    if _entry_is_reparse(entry, metadata):
                        state.rejected_reparse_entries += 1
                        _record_issue(
                            state,
                            scan_policy,
                            code="MB-FS-0003",
                            relative_path=relative,
                            message="Reparse entry was not followed",
                        )
                        continue
                    is_directory = stat.S_ISDIR(metadata.st_mode)
                    is_file = stat.S_ISREG(metadata.st_mode)
                except MibaoError as exc:
                    if exc.code == "MB-FS-0001":
                        state.rejected_unsafe_entries += 1
                        _record_issue(
                            state,
                            scan_policy,
                            code=exc.code,
                            relative_path=relative,
                            message="Entry path was excluded by the closed path policy",
                        )
                        continue
                    state.unreadable_entries += 1
                    state.incomplete = True
                    _record_issue(
                        state,
                        scan_policy,
                        code=exc.code,
                        relative_path=relative,
                        message=f"Entry metadata cannot be read: {exc.message}",
                    )
                    continue
                except OSError as exc:
                    state.unreadable_entries += 1
                    state.incomplete = True
                    _record_issue(
                        state,
                        scan_policy,
                        code="MB-SCAN-0002",
                        relative_path=relative,
                        message=f"Entry metadata cannot be read: {type(exc).__name__}",
                    )
                    continue
                if is_directory:
                    if depth >= scan_policy.max_depth:
                        raise MibaoError(
                            "MB-SCAN-0005",
                            f"Scan depth limit exceeded at relative path: {relative}",
                        )
                    try:
                        _entry_identity(entry, is_file=False)
                    except (MibaoError, OSError) as exc:
                        state.unreadable_entries += 1
                        state.incomplete = True
                        code = exc.code if isinstance(exc, MibaoError) else "MB-SCAN-0002"
                        message = exc.message if isinstance(exc, MibaoError) else type(exc).__name__
                        _record_issue(
                            state,
                            scan_policy,
                            code=code,
                            relative_path=relative,
                            message=message,
                        )
                        continue
                    yield from walk(entry_path, depth + 1)
                    continue
                if not is_file:
                    state.ignored_entries += 1
                    continue
                state.discovered_files += 1
                if state.discovered_files > scan_policy.max_entries:
                    raise MibaoError("MB-SCAN-0005", "Scan entry limit exceeded")
                try:
                    identity = _entry_identity(entry, is_file=True)
                    yield _candidate_from_identity(
                        relative,
                        identity,
                        project_id=project_id,
                        source_root_id=source_root_id,
                    )
                except (MibaoError, OSError) as exc:
                    state.unreadable_entries += 1
                    state.incomplete = True
                    code = exc.code if isinstance(exc, MibaoError) else "MB-SCAN-0002"
                    message = exc.message if isinstance(exc, MibaoError) else type(exc).__name__
                    _record_issue(
                        state,
                        scan_policy,
                        code=code,
                        relative_path=relative,
                        message=message,
                    )

    yield from walk(source.path, 0)


def _begin_scan(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    privacy_mode: str,
    source: AuthorizedPath,
    source_root_id: str,
    job_id: str,
    policy: ScanPolicy,
    timestamp: str,
    attempt_id: str,
    database_facts: tuple[str, int, str, str],
) -> tuple[bool, ScanRecoveryReceipt]:
    identity = source.identity
    if identity is None:
        raise MibaoError("MB-SCAN-0002", "Authorized source root has no identity")
    path_identity = _json(
        {"device": identity.device, "inode": identity.inode, "mode": identity.mode}
    )
    canonical_path = str(source.path)
    current_contract_sha256 = _scan_contract_sha256(
        _scan_contract(
            policy=policy,
            privacy_mode=privacy_mode,
            source_root_id=source_root_id,
        )
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        existing_source = connection.execute(
            "SELECT canonical_path, path_identity_json FROM source_roots "
            "WHERE source_root_id=? AND project_id=?",
            (source_root_id, project_id),
        ).fetchone()
        if existing_source is None:
            connection.execute(
                "INSERT INTO source_roots("
                "source_root_id, project_id, canonical_path, path_identity_json, state, "
                "created_at, updated_at"
                ") VALUES (?, ?, ?, ?, 'active', ?, ?)",
                (source_root_id, project_id, canonical_path, path_identity, timestamp, timestamp),
            )
        elif existing_source != (canonical_path, path_identity):
            raise MibaoError(
                "MB-SCAN-0003",
                "Registered source root path or physical identity changed",
            )
        else:
            connection.execute(
                "UPDATE source_roots SET state='active', updated_at=? "
                "WHERE source_root_id=? AND project_id=?",
                (timestamp, source_root_id, project_id),
            )
        existing_job = connection.execute(
            "SELECT status, spec_json FROM jobs WHERE job_id=? AND project_id=?",
            (job_id, project_id),
        ).fetchone()
        prior_status = str(existing_job[0]) if existing_job is not None else None
        prior_spec = existing_job[1] if existing_job is not None else None
        resumed = prior_status in {
            "queued",
            "running",
            "failed",
            "cancelled",
            "interrupted",
        }
        if existing_job is None:
            attempt_number = 1
            prior_attempt_id = None
        else:
            (
                prior_attempt,
                prior_contract_sha256,
                prior_attempt_id,
                _prior_contract,
            ) = _parse_prior_spec(prior_spec)
            if prior_status in {"queued", "running", "failed", "cancelled", "interrupted"} and (
                prior_contract_sha256 != current_contract_sha256
            ):
                raise MibaoError(
                    "MB-SCAN-0007",
                    "Incomplete scan cannot resume under a different recovery contract",
                )
            attempt_number = prior_attempt + 1
        prior_count, prior_digest = _operation_checkpoint(
            connection,
            project_id=project_id,
            job_id=job_id,
            attempt_id=prior_attempt_id,
        )
        recovery = _recovery_receipt(
            attempt_id=attempt_id,
            attempt_number=attempt_number,
            scan_spec_sha256=current_contract_sha256,
            started_at=timestamp,
            prior_job_status=prior_status,
            prior_durable_operation_count=prior_count,
            prior_operation_set_sha256=prior_digest,
            database_facts=database_facts,
            source_state_at_attempt_start="active",
        )
        spec = _scan_spec(
            policy=policy,
            privacy_mode=privacy_mode,
            source_root_id=source_root_id,
            recovery=recovery,
        )
        if prior_status == "running":
            connection.execute(
                "UPDATE operations SET status='interrupted', finished_at=coalesce(finished_at, ?), "
                "updated_at=? WHERE project_id=? AND job_id=? AND operation_type=? "
                "AND status='running'",
                (timestamp, timestamp, project_id, job_id, _OPERATION_TYPE),
            )
        if existing_job is None:
            connection.execute(
                "INSERT INTO jobs("
                "job_id, project_id, goal, spec_json, status, created_at, updated_at"
                ") "
                "VALUES (?, ?, 'inventory', ?, 'running', ?, ?)",
                (job_id, project_id, spec, timestamp, timestamp),
            )
        else:
            connection.execute(
                "UPDATE jobs SET spec_json=?, status='running', updated_at=? "
                "WHERE job_id=? AND project_id=?",
                (spec, timestamp, job_id, project_id),
            )
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    return resumed, recovery


def _write_batch(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    job_id: str,
    timestamp: str,
    attempt_id: str,
    attempt_number: int,
    scan_spec_sha256: str,
    batch: list[_Candidate],
    test_hook: _TestHook | None,
) -> tuple[int, int, int]:
    identifiers = [candidate.operation_id for candidate in batch]
    placeholders = ",".join("?" for _ in identifiers)
    existing = {
        str(operation_id): (str(request_json), str(result_json), asset_id)
        for operation_id, request_json, result_json, asset_id in connection.execute(
            "SELECT operation_id, request_json, result_json, asset_id FROM operations "
            f"WHERE operation_id IN ({placeholders})",
            identifiers,
        )
    }
    inserted = 0
    changed = 0
    unchanged = 0
    rows: list[tuple[object, ...]] = []
    changed_paths: list[tuple[str, str]] = []
    for candidate in batch:
        prior = existing.get(candidate.operation_id)
        result_payload: dict[str, Any] = {
            "classification": "pending_media_probe",
            "present": True,
            "scan_attempt_id": attempt_id,
            "schema_version": "1.0",
        }
        asset_id: object = None
        if prior is None:
            inserted += 1
        else:
            prior_request, prior_result, prior_asset_id = prior
            try:
                prior_payload = json.loads(prior_result)
            except json.JSONDecodeError:
                prior_payload = None
            if (
                prior_request == candidate.request_json
                and isinstance(prior_payload, dict)
                and prior_payload.get("present") is True
            ):
                unchanged += 1
                result_payload = dict(prior_payload)
                result_payload["scan_attempt_id"] = attempt_id
                asset_id = prior_asset_id
            else:
                changed += 1
                request = json.loads(candidate.request_json)
                changed_paths.append(
                    (str(request["source_root_id"]), str(request["relative_path"]))
                )
        result_json = _json(result_payload)
        rows.append(
            (
                candidate.operation_id,
                project_id,
                job_id,
                asset_id,
                _OPERATION_TYPE,
                candidate.request_json,
                result_json,
                timestamp,
                timestamp,
                timestamp,
                timestamp,
            )
        )
    if test_hook is not None:
        test_hook("before_batch_begin", len(batch))
    connection.execute("BEGIN IMMEDIATE")
    try:
        _assert_attempt_fence(
            connection,
            project_id=project_id,
            job_id=job_id,
            attempt_id=attempt_id,
            attempt_number=attempt_number,
            scan_spec_sha256=scan_spec_sha256,
        )
        connection.executemany(
            "INSERT INTO operations("
            "operation_id, project_id, job_id, asset_id, operation_type, request_json, "
            "result_json, status, duration_ms, started_at, finished_at, created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, 'succeeded', 0, ?, ?, ?, ?) "
            "ON CONFLICT(operation_id) DO UPDATE SET "
            "asset_id=excluded.asset_id, request_json=excluded.request_json, "
            "result_json=excluded.result_json, "
            "status='succeeded', duration_ms=0, started_at=excluded.started_at, "
            "finished_at=excluded.finished_at, updated_at=excluded.updated_at",
            rows,
        )
        affected_assets: set[str] = set()
        for source_root_id, relative_path in changed_paths:
            prior_assets = connection.execute(
                "SELECT asset_id FROM file_instances WHERE project_id=? AND source_root_id=? "
                "AND relative_path=? AND state='present'",
                (project_id, source_root_id, relative_path),
            ).fetchall()
            affected_assets.update(str(row[0]) for row in prior_assets)
            connection.execute(
                "UPDATE file_instances SET state='changed', last_seen_at=? "
                "WHERE project_id=? AND source_root_id=? AND relative_path=?",
                (timestamp, project_id, source_root_id, relative_path),
            )
        for affected_asset_id in sorted(affected_assets):
            connection.execute(
                "UPDATE assets SET state=CASE WHEN EXISTS("
                "SELECT 1 FROM file_instances WHERE project_id=? AND asset_id=? "
                "AND state='present') THEN 'active' ELSE 'missing' END, updated_at=? "
                "WHERE project_id=? AND asset_id=? AND state<>'quarantined'",
                (
                    project_id,
                    affected_asset_id,
                    timestamp,
                    project_id,
                    affected_asset_id,
                ),
            )
        if test_hook is not None:
            test_hook("batch_before_commit", len(batch))
        connection.commit()
    except BaseException as exc:
        connection.rollback()
        if isinstance(exc, sqlite3.Error):
            raise MibaoError("MB-SCAN-0004", f"Scan batch was rolled back: {exc}") from exc
        raise
    return inserted, changed, unchanged


def _finish_scan(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    source_root_id: str,
    job_id: str,
    attempt_id: str,
    attempt_number: int,
    scan_spec_sha256: str,
    timestamp: str,
    status: str,
    source_state: str,
    mark_missing: bool,
    terminal_revalidate: Callable[[], None] | None = None,
) -> int:
    connection.execute("BEGIN IMMEDIATE")
    try:
        _assert_attempt_fence(
            connection,
            project_id=project_id,
            job_id=job_id,
            attempt_id=attempt_id,
            attempt_number=attempt_number,
            scan_spec_sha256=scan_spec_sha256,
        )
        missing = 0
        if mark_missing:
            if terminal_revalidate is None:
                raise MibaoError("MB-SCAN-0007", "Complete scan lacks terminal source revalidation")
            terminal_revalidate()
            connection.execute(
                "CREATE TEMP TABLE IF NOT EXISTS mibao_missing_paths("
                "source_root_id TEXT NOT NULL, relative_path TEXT NOT NULL, "
                "was_present INTEGER NOT NULL CHECK(was_present IN (0, 1)), "
                "PRIMARY KEY(source_root_id, relative_path)) WITHOUT ROWID"
            )
            connection.execute("DELETE FROM temp.mibao_missing_paths")
            connection.execute(
                "INSERT INTO temp.mibao_missing_paths("
                "source_root_id, relative_path, was_present) "
                "SELECT json_extract(request_json, '$.source_root_id'), "
                "json_extract(request_json, '$.relative_path'), "
                "CASE WHEN json_extract(result_json, '$.present')=1 THEN 1 ELSE 0 END "
                "FROM operations WHERE project_id=? AND job_id=? AND operation_type=? "
                "AND coalesce(json_extract(result_json, '$.scan_attempt_id'), '')<>?",
                (project_id, job_id, _OPERATION_TYPE, attempt_id),
            )
            row = connection.execute(
                "SELECT coalesce(sum(was_present), 0) FROM temp.mibao_missing_paths"
            ).fetchone()
            missing = int(row[0]) if row else 0
            connection.execute(
                "UPDATE file_instances AS file SET state='missing', last_seen_at=? "
                "WHERE file.project_id=? AND file.state IN ('present', 'changed') AND EXISTS("
                "SELECT 1 FROM temp.mibao_missing_paths AS missing "
                "WHERE missing.source_root_id=file.source_root_id "
                "AND missing.relative_path=file.relative_path)",
                (timestamp, project_id),
            )
            connection.execute(
                "UPDATE assets AS asset SET state=CASE WHEN EXISTS("
                "SELECT 1 FROM file_instances AS current "
                "WHERE current.project_id=? AND current.asset_id=asset.asset_id "
                "AND current.state='present') THEN 'active' ELSE 'missing' END, updated_at=? "
                "WHERE asset.project_id=? AND asset.state<>'quarantined' AND EXISTS("
                "SELECT 1 FROM file_instances AS file "
                "JOIN temp.mibao_missing_paths AS missing "
                "ON missing.source_root_id=file.source_root_id "
                "AND missing.relative_path=file.relative_path "
                "WHERE file.project_id=? AND file.asset_id=asset.asset_id)",
                (
                    project_id,
                    timestamp,
                    project_id,
                    project_id,
                ),
            )
            connection.execute(
                "UPDATE operations SET "
                "asset_id=NULL, result_json=json_set(result_json, '$.present', json('false')), "
                "updated_at=? "
                "WHERE project_id=? AND job_id=? AND operation_type=? "
                "AND coalesce(json_extract(result_json, '$.scan_attempt_id'), '')<>?",
                (timestamp, project_id, job_id, _OPERATION_TYPE, attempt_id),
            )
            connection.execute(
                "UPDATE operations SET status='interrupted', "
                "finished_at=coalesce(finished_at, ?), updated_at=? "
                "WHERE project_id=? AND job_id=? AND operation_type=? AND status='running'",
                (timestamp, timestamp, project_id, job_id, _OPERATION_TYPE),
            )
        connection.execute(
            "UPDATE source_roots SET state=?, updated_at=? WHERE project_id=? AND source_root_id=?",
            (source_state, timestamp, project_id, source_root_id),
        )
        connection.execute(
            "UPDATE jobs SET status=?, updated_at=? WHERE project_id=? AND job_id=?",
            (status, timestamp, project_id, job_id),
        )
        if (
            status == "succeeded"
            and not compute_scan_completeness_snapshot(connection, project_id).complete
        ):
            raise MibaoError(
                "MB-SCAN-0007",
                "Completed scan contradicts the persisted scan-completeness fence",
            )
        connection.commit()
    except BaseException as exc:
        connection.rollback()
        if isinstance(exc, sqlite3.Error):
            raise MibaoError("MB-SCAN-0004", f"Scan completion was rolled back: {exc}") from exc
        raise
    return missing


def _logical_unavailable_source(source_root: Path, path_policy: PathPolicy) -> Path:
    try:
        candidate = source_root.expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        candidate = candidate.resolve(strict=False)
    except OSError as exc:
        raise MibaoError("MB-SCAN-0006", "Unavailable SourceRoot cannot be resolved") from exc
    validate_windows_path_syntax(
        candidate,
        allow_unc=path_policy.allow_unc,
        policy=path_policy,
    )
    return candidate


def _record_source_offline(
    project: Project,
    connection: sqlite3.Connection,
    source_root: Path,
    *,
    policy: ScanPolicy,
    path_policy: PathPolicy,
    database_facts: tuple[str, int, str, str],
    timestamp: str,
    attempt_id: str,
) -> ScanResult:
    canonical = _logical_unavailable_source(source_root, path_policy)
    source_root_id = _source_key(project.project_id, canonical)
    job_id = _job_key(project.project_id, source_root_id)
    connection.execute("BEGIN IMMEDIATE")
    try:
        source_row = connection.execute(
            "SELECT canonical_path FROM source_roots WHERE project_id=? AND source_root_id=?",
            (project.project_id, source_root_id),
        ).fetchone()
        existing_job = connection.execute(
            "SELECT status, spec_json FROM jobs WHERE project_id=? AND job_id=?",
            (project.project_id, job_id),
        ).fetchone()
        if (
            source_row is None
            or _pattern_key(str(source_row[0])) != _pattern_key(str(canonical))
            or existing_job is None
        ):
            raise MibaoError(
                "MB-SCAN-0006",
                "Unavailable SourceRoot is not an exact previously registered source",
            )
        prior_status = str(existing_job[0])
        (
            prior_attempt,
            prior_contract_sha256,
            prior_attempt_id,
            prior_contract,
        ) = _parse_prior_spec(existing_job[1])
        prior_count, prior_digest = _operation_checkpoint(
            connection,
            project_id=project.project_id,
            job_id=job_id,
            attempt_id=prior_attempt_id,
        )
        recovery = _recovery_receipt(
            attempt_id=attempt_id,
            attempt_number=prior_attempt + 1,
            scan_spec_sha256=prior_contract_sha256,
            started_at=timestamp,
            prior_job_status=prior_status,
            prior_durable_operation_count=prior_count,
            prior_operation_set_sha256=prior_digest,
            database_facts=database_facts,
            source_state_at_attempt_start="offline",
            source_offline=True,
        )
        spec = _scan_spec_from_contract(prior_contract, recovery)
        connection.execute(
            "UPDATE operations SET status='interrupted', finished_at=coalesce(finished_at, ?), "
            "updated_at=? WHERE project_id=? AND job_id=? AND operation_type=? "
            "AND status='running'",
            (timestamp, timestamp, project.project_id, job_id, _OPERATION_TYPE),
        )
        connection.execute(
            "UPDATE source_roots SET state='offline', updated_at=? "
            "WHERE project_id=? AND source_root_id=?",
            (timestamp, project.project_id, source_root_id),
        )
        connection.execute(
            "UPDATE jobs SET spec_json=?, status='interrupted', updated_at=? "
            "WHERE project_id=? AND job_id=?",
            (spec, timestamp, project.project_id, job_id),
        )
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    issue = ScanIssue(
        "MB-SCAN-0006",
        ".",
        "Registered SourceRoot is unavailable; no missing paths were inferred",
    )
    completion = compute_scan_completeness_snapshot(connection, project.project_id)
    return ScanResult(
        project_id=project.project_id,
        source_root_id=source_root_id,
        job_id=job_id,
        status="offline",
        discovered_files=0,
        inserted_candidates=0,
        changed_candidates=0,
        unchanged_candidates=0,
        missing_candidates=0,
        ignored_entries=0,
        rejected_reparse_entries=0,
        rejected_unsafe_entries=0,
        unreadable_entries=1,
        committed_batches=0,
        max_batch_entries=0,
        max_directory_depth=0,
        resumed=prior_status in {"queued", "running", "failed", "cancelled", "interrupted"},
        source_state="offline",
        recovery=recovery,
        completion=completion,
        issues=(issue,),
    )


def scan_project(
    project_root: Path,
    source_root: Path,
    *,
    policy: ScanPolicy | None = None,
    cancel_check: Callable[[], bool] | None = None,
    _test_hook: _TestHook | None = None,
) -> ScanResult:
    """Stream one source tree into stable scan-candidate operations and resume idempotently."""

    scan_policy = policy or ScanPolicy()
    should_cancel = cancel_check or (lambda: False)
    path_policy = PathPolicy(allow_unc=scan_policy.allow_unc)
    run_timestamp = _timestamp()
    attempt_id = "RUN-SCAN-" + uuid.uuid4().hex
    state = _WalkState()
    inserted = 0
    changed = 0
    unchanged = 0
    missing = 0
    committed_batches = 0
    max_batch_entries = 0
    interrupted = False
    source_state = "active"

    with open_project_writer(project_root) as (project, connection):
        database_facts = _database_recovery_facts(connection)
        try:
            source, _ = validate_root_pair(source_root, project.root, policy=path_policy)
        except MibaoError as exc:
            if exc.code not in {"MB-FS-0001", "MB-FS-0004"}:
                raise
            return _record_source_offline(
                project,
                connection,
                source_root,
                policy=scan_policy,
                path_policy=path_policy,
                database_facts=database_facts,
                timestamp=run_timestamp,
                attempt_id=attempt_id,
            )
        source_root_id = _source_key(project.project_id, source.path)
        job_id = _job_key(project.project_id, source_root_id)
        recovery: ScanRecoveryReceipt | None = None

        def require_source() -> None:
            try:
                source.revalidate()
            except (MibaoError, OSError) as exc:
                if not source.path.exists():
                    raise _SourceOffline from exc
                raise

        def terminal_source_revalidate() -> None:
            if _test_hook is not None:
                _test_hook("before_terminal_revalidate", 0)
            require_source()

        try:
            resumed, recovery = _begin_scan(
                connection,
                project_id=project.project_id,
                privacy_mode=project.privacy_mode,
                source=source,
                source_root_id=source_root_id,
                job_id=job_id,
                policy=scan_policy,
                timestamp=run_timestamp,
                attempt_id=attempt_id,
                database_facts=database_facts,
            )
            batch: list[_Candidate] = []

            def flush() -> None:
                nonlocal inserted, changed, unchanged, committed_batches, max_batch_entries
                if not batch:
                    return
                require_source()
                max_batch_entries = max(max_batch_entries, len(batch))
                new, modified, stable = _write_batch(
                    connection,
                    project_id=project.project_id,
                    job_id=job_id,
                    timestamp=run_timestamp,
                    attempt_id=attempt_id,
                    attempt_number=recovery.attempt_number,
                    scan_spec_sha256=recovery.scan_spec_sha256,
                    batch=batch,
                    test_hook=_test_hook,
                )
                inserted += new
                changed += modified
                unchanged += stable
                committed_batches += 1
                batch.clear()

            try:
                for candidate in _walk_candidates(
                    source,
                    project_id=project.project_id,
                    source_root_id=source_root_id,
                    scan_policy=scan_policy,
                    path_policy=path_policy,
                    cancel_check=should_cancel,
                    state=state,
                ):
                    batch.append(candidate)
                    if len(batch) >= scan_policy.batch_size:
                        flush()
            except _ScanInterrupted:
                interrupted = True
            except _SourceOffline:
                state.source_offline = True
                batch.clear()
            if not state.source_offline:
                try:
                    flush()
                except _SourceOffline:
                    state.source_offline = True
                    batch.clear()
            if state.source_offline:
                database_status = "interrupted"
                result_status = "offline"
                source_state = "offline"
            elif interrupted:
                database_status = "interrupted"
                result_status = "interrupted"
            elif state.incomplete:
                database_status = "failed"
                result_status = "partial"
            else:
                database_status = "succeeded"
                result_status = "completed"
            try:
                missing = _finish_scan(
                    connection,
                    project_id=project.project_id,
                    source_root_id=source_root_id,
                    job_id=job_id,
                    attempt_id=attempt_id,
                    attempt_number=recovery.attempt_number,
                    scan_spec_sha256=recovery.scan_spec_sha256,
                    timestamp=run_timestamp,
                    status=database_status,
                    source_state=source_state,
                    mark_missing=result_status == "completed",
                    terminal_revalidate=(
                        terminal_source_revalidate if result_status == "completed" else None
                    ),
                )
            except _SourceOffline:
                state.source_offline = True
                source_state = "offline"
                result_status = "offline"
                missing = _finish_scan(
                    connection,
                    project_id=project.project_id,
                    source_root_id=source_root_id,
                    job_id=job_id,
                    attempt_id=attempt_id,
                    attempt_number=recovery.attempt_number,
                    scan_spec_sha256=recovery.scan_spec_sha256,
                    timestamp=_timestamp(),
                    status="interrupted",
                    source_state="offline",
                    mark_missing=False,
                )
            completion = compute_scan_completeness_snapshot(connection, project.project_id)
            if result_status == "completed" and not completion.complete:
                raise MibaoError(
                    "MB-SCAN-0007",
                    "Completed scan contradicts the persisted scan-completeness fence",
                )
        except BaseException:
            if recovery is not None:
                with suppress(MibaoError, sqlite3.Error):
                    _finish_scan(
                        connection,
                        project_id=project.project_id,
                        source_root_id=source_root_id,
                        job_id=job_id,
                        attempt_id=attempt_id,
                        attempt_number=recovery.attempt_number,
                        scan_spec_sha256=recovery.scan_spec_sha256,
                        timestamp=_timestamp(),
                        status="failed",
                        source_state="active",
                        mark_missing=False,
                    )
            raise

    if recovery is None:
        raise MibaoError("MB-SCAN-0007", "Scan recovery receipt was not initialized")
    return ScanResult(
        project_id=project.project_id,
        source_root_id=source_root_id,
        job_id=job_id,
        status=result_status,
        discovered_files=state.discovered_files,
        inserted_candidates=inserted,
        changed_candidates=changed,
        unchanged_candidates=unchanged,
        missing_candidates=missing,
        ignored_entries=state.ignored_entries,
        rejected_reparse_entries=state.rejected_reparse_entries,
        rejected_unsafe_entries=state.rejected_unsafe_entries,
        unreadable_entries=state.unreadable_entries,
        committed_batches=committed_batches,
        max_batch_entries=max_batch_entries,
        max_directory_depth=state.max_directory_depth,
        resumed=resumed,
        source_state=source_state,
        recovery=recovery,
        completion=completion,
        issues=tuple(state.issues),
    )
