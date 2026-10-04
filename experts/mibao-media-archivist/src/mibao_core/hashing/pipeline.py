"""Handle-bound SHA-256 and short-transaction Asset/FileInstance promotion."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
import unicodedata
import weakref
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Final

from mibao_core.errors import MibaoError
from mibao_core.filesystem.paths import (
    AuthorizedPath,
    FileIdentity,
    PathPolicy,
    authorize_existing_path,
    to_filesystem_api_path,
    validate_root_pair,
    validate_windows_path_syntax,
)
from mibao_core.filesystem.scanner import compute_scan_completeness_snapshot, stat_change_token
from mibao_core.project import ProjectLock, open_project
from mibao_core.project.migrations import audit_schema

_HASH_POLICY_VERSION: Final = "mibao-hash-policy-v1"
_SAMPLE_SCHEME: Final = "sha256-regions-v1"
_HEX_64: Final = re.compile(r"^[0-9a-f]{64}$")
_CANDIDATE_KEYS: Final = {
    "schema_version",
    "source_root_id",
    "relative_path",
    "size_bytes",
    "modified_time_ms",
    "identity",
    "change_token",
}
_TestHook = Callable[[str, str], None]


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


@dataclass(frozen=True, slots=True)
class HashPolicy:
    """Finite hashing, sampling, and promotion budgets."""

    chunk_size_bytes: int = 1024 * 1024
    sample_window_bytes: int = 64 * 1024
    promotion_batch_size: int = 128
    max_candidates: int = 1_000_000
    strict_rehash: bool = False
    allow_unc: bool = False

    def __post_init__(self) -> None:
        if not 4096 <= self.chunk_size_bytes <= 16 * 1024 * 1024:
            raise MibaoError("MB-HASH-0001", "Hash chunk size must be between 4 KiB and 16 MiB")
        if not 4096 <= self.sample_window_bytes <= 1024 * 1024:
            raise MibaoError("MB-HASH-0001", "Sample window must be between 4 KiB and 1 MiB")
        if not 1 <= self.promotion_batch_size <= 1000:
            raise MibaoError("MB-HASH-0001", "Promotion batch size must be between 1 and 1000")
        if not 1 <= self.max_candidates <= 10_000_000:
            raise MibaoError("MB-HASH-0001", "Hash candidate limit must be finite and positive")
        if not isinstance(self.strict_rehash, bool) or not isinstance(self.allow_unc, bool):
            raise MibaoError("MB-HASH-0001", "Hash policy flags must be booleans")


@dataclass(frozen=True, slots=True)
class _SampleReceipt:
    digest: str
    sampled_bytes: int
    covers_all_bytes: bool
    windows: tuple[tuple[int, int], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "scheme": _SAMPLE_SCHEME,
            "digest": self.digest,
            "sampled_bytes": self.sampled_bytes,
            "covers_all_bytes": self.covers_all_bytes,
            "windows": [{"offset": offset, "length": length} for offset, length in self.windows],
        }


@dataclass(frozen=True, slots=True)
class HashReceipt:
    """A current, completed full-stream observation; never a partial digest."""

    sha256: str
    bytes_hashed: int
    chunk_count: int
    chunk_size_bytes: int
    sample: _SampleReceipt
    pre_handle_identity: FileIdentity
    post_handle_identity: FileIdentity
    post_path_identity: FileIdentity
    validation_mode: str
    full_pass_count: int
    candidate_change_token: str | None
    cache_decision: str
    full_hash_performed: bool = True
    content_assertion: str = "current_full_verified"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "policy_version": _HASH_POLICY_VERSION,
            "content_assertion": self.content_assertion,
            "algorithm": "sha256",
            "validation_mode": self.validation_mode,
            "full_hash_performed": self.full_hash_performed,
            "full_pass_count": self.full_pass_count,
            "sha256": self.sha256,
            "bytes_hashed": self.bytes_hashed,
            "chunk_count": self.chunk_count,
            "chunk_size_bytes": self.chunk_size_bytes,
            "candidate_change_token": self.candidate_change_token,
            "pre_handle_identity": _identity_dict(self.pre_handle_identity),
            "post_handle_identity": _identity_dict(self.post_handle_identity),
            "post_path_identity": _identity_dict(self.post_path_identity),
            "path_revalidated": True,
            "sample": self.sample.as_dict(),
            "cache": {
                "decision": self.cache_decision,
                "authority": "current_full_hash",
            },
        }


@dataclass(frozen=True, slots=True, weakref_slot=True)
class HashAssuranceToken:
    """Ephemeral proof that one hash run covers the exact current DB snapshot."""

    project_id: str
    source_root_ids: tuple[str, ...]
    present_scan_candidate_count: int
    present_file_instance_count: int
    current_full_verified_count: int
    exact_duplicate_group_count: int
    duplicate_member_count: int
    duplicate_extra_copy_count: int
    scan_state_sha256: str
    snapshot_sha256: str
    issued_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "2.0",
            "project_id": self.project_id,
            "source_root_ids": list(self.source_root_ids),
            "present_scan_candidate_count": self.present_scan_candidate_count,
            "present_file_instance_count": self.present_file_instance_count,
            "current_full_verified_count": self.current_full_verified_count,
            "exact_duplicate_group_count": self.exact_duplicate_group_count,
            "duplicate_member_count": self.duplicate_member_count,
            "duplicate_extra_copy_count": self.duplicate_extra_copy_count,
            "scan_state_sha256": self.scan_state_sha256,
            "snapshot_sha256": self.snapshot_sha256,
            "issued_at": self.issued_at,
        }


_ISSUED_ASSURANCE_TOKENS: weakref.WeakValueDictionary[int, HashAssuranceToken] = (
    weakref.WeakValueDictionary()
)


def consume_issued_hash_assurance_token(token: HashAssuranceToken) -> bool:
    """Consume one exact live capability issued by this hashing process."""

    issued = _ISSUED_ASSURANCE_TOKENS.pop(id(token), None)
    return issued is token


@dataclass(frozen=True, slots=True)
class PromotionResult:
    project_id: str
    source_root_id: str
    promoted_candidates: int
    reused_candidates: int
    full_hashes: int
    strict_rehashes: int
    cache_invalidations: int
    stale_candidates: int
    failed_candidates: int
    current_full_verified_candidates: int
    prior_hash_cache_hint_candidates: int
    asset_count: int
    active_asset_count: int
    file_instance_count: int
    present_file_instance_count: int
    exact_duplicate_group_count: int
    duplicate_member_count: int
    duplicate_extra_copy_count: int
    historical_exact_duplicate_group_count: int
    historical_duplicate_member_count: int
    historical_duplicate_extra_copy_count: int
    duplicate_assurance: str
    committed_batches: int
    max_batch_candidates: int
    bytes_hashed: int
    chunk_count: int
    scan_state_sha256: str
    assurance_token: HashAssuranceToken | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "source_root_id": self.source_root_id,
            "promoted_candidates": self.promoted_candidates,
            "reused_candidates": self.reused_candidates,
            "full_hashes": self.full_hashes,
            "strict_rehashes": self.strict_rehashes,
            "cache_invalidations": self.cache_invalidations,
            "stale_candidates": self.stale_candidates,
            "failed_candidates": self.failed_candidates,
            "current_full_verified_candidates": self.current_full_verified_candidates,
            "prior_hash_cache_hint_candidates": self.prior_hash_cache_hint_candidates,
            "asset_count": self.asset_count,
            "active_asset_count": self.active_asset_count,
            "file_instance_count": self.file_instance_count,
            "present_file_instance_count": self.present_file_instance_count,
            "exact_duplicate_group_count": self.exact_duplicate_group_count,
            "duplicate_member_count": self.duplicate_member_count,
            "duplicate_extra_copy_count": self.duplicate_extra_copy_count,
            "historical_exact_duplicate_group_count": (self.historical_exact_duplicate_group_count),
            "historical_duplicate_member_count": self.historical_duplicate_member_count,
            "historical_duplicate_extra_copy_count": (self.historical_duplicate_extra_copy_count),
            "duplicate_assurance": self.duplicate_assurance,
            "committed_batches": self.committed_batches,
            "max_batch_candidates": self.max_batch_candidates,
            "bytes_hashed": self.bytes_hashed,
            "chunk_count": self.chunk_count,
            "scan_state_sha256": self.scan_state_sha256,
            "cache_assurance": "bounded_hint_only",
            "content_identity_algorithm": "sha256",
            "strict_rehash_available": True,
            "assurance_token": (
                self.assurance_token.as_dict() if self.assurance_token is not None else None
            ),
        }


@dataclass(frozen=True, slots=True)
class _CandidateSnapshot:
    operation_id: str
    request_text: str
    result_text: str
    asset_id: str | None
    status: str
    updated_at: str
    request: dict[str, Any]
    result: dict[str, Any]


@dataclass(frozen=True, slots=True)
class _PreparedPromotion:
    snapshot: _CandidateSnapshot
    authorized: AuthorizedPath
    receipt: HashReceipt
    cache_invalidated: bool


@dataclass(slots=True)
class _Counters:
    promoted: int = 0
    reused: int = 0
    full_hashes: int = 0
    strict_rehashes: int = 0
    cache_invalidations: int = 0
    stale: int = 0
    failed: int = 0
    current_full_verified: int = 0
    cache_hints: int = 0
    committed_batches: int = 0
    max_batch: int = 0
    bytes_hashed: int = 0
    chunks: int = 0


class _StaleSnapshot(Exception):
    pass


@dataclass(frozen=True, slots=True)
class _HashAssuranceSnapshot:
    source_root_ids: tuple[str, ...]
    present_scan_candidate_count: int
    present_file_instance_count: int
    exact_duplicate_group_count: int
    duplicate_member_count: int
    duplicate_extra_copy_count: int
    scan_state_sha256: str
    sha256: str


def _identity_from_stat(metadata: os.stat_result) -> FileIdentity:
    return FileIdentity(
        device=int(metadata.st_dev),
        inode=int(metadata.st_ino),
        mode=int(metadata.st_mode),
        size=int(metadata.st_size),
        modified_ns=int(metadata.st_mtime_ns),
    )


def _identity_dict(identity: FileIdentity) -> dict[str, int | None]:
    return {
        "device": identity.device,
        "inode": identity.inode,
        "mode": identity.mode,
        "size_bytes": identity.size,
        "modified_time_ns": identity.modified_ns,
    }


def _sample_windows(size: int, window_size: int) -> tuple[tuple[int, int], ...]:
    if size <= 0:
        return ((0, 0),)
    if size <= window_size * 5:
        return ((0, size),)
    offsets = (0, size // 4, size // 2, (size * 3) // 4, max(0, size - window_size))
    windows: list[tuple[int, int]] = []
    for offset in offsets:
        length = min(window_size, size - offset)
        candidate = (offset, length)
        if candidate not in windows:
            windows.append(candidate)
    return tuple(windows)


def _sample_handle(handle: BinaryIO, size: int, window_size: int) -> _SampleReceipt:
    windows = _sample_windows(size, window_size)
    digest = hashlib.sha256()
    digest.update((_SAMPLE_SCHEME + "\0" + str(size) + "\0").encode("ascii"))
    sampled_bytes = 0
    for offset, length in windows:
        handle.seek(offset)
        payload = handle.read(length)
        if len(payload) != length:
            raise MibaoError("MB-HASH-0003", "File became short while sampling")
        digest.update(f"{offset}\0{length}\0".encode("ascii"))
        digest.update(payload)
        sampled_bytes += length
    return _SampleReceipt(
        digest=digest.hexdigest(),
        sampled_bytes=sampled_bytes,
        covers_all_bytes=windows == ((0, size),),
        windows=windows,
    )


def _same_open_identity(left: FileIdentity, right: FileIdentity) -> bool:
    return (
        left.device,
        left.inode,
        stat.S_IFMT(left.mode),
        left.size,
        left.modified_ns,
    ) == (
        right.device,
        right.inode,
        stat.S_IFMT(right.mode),
        right.size,
        right.modified_ns,
    )


def _validate_expected_token(identity: FileIdentity, expected_change_token: str | None) -> None:
    if expected_change_token is not None and stat_change_token(identity) != expected_change_token:
        raise MibaoError("MB-HASH-0002", "Scan candidate stat token is stale")


def _revalidate_open_path(
    authorized: AuthorizedPath,
    expected_identity: FileIdentity,
) -> FileIdentity:
    """Recheck the leaf after I/O; the registered SourceRoot is checked once per batch."""

    native = to_filesystem_api_path(authorized.path, policy=authorized.policy)
    try:
        metadata = os.stat(native, follow_symlinks=False)
    except OSError as exc:
        raise MibaoError("MB-HASH-0002", "Hash path disappeared after the read") from exc
    attributes = int(getattr(metadata, "st_file_attributes", 0))
    reparse_attribute = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    current = _identity_from_stat(metadata)
    if attributes & reparse_attribute or not _same_open_identity(expected_identity, current):
        raise MibaoError("MB-HASH-0002", "Hash path no longer names the opened file")
    return current


def _hash_authorized(
    authorized: AuthorizedPath,
    *,
    policy: HashPolicy,
    expected_change_token: str | None,
) -> HashReceipt:
    expected_identity = authorized.identity
    if expected_identity is None:
        raise MibaoError("MB-HASH-0002", "Authorized hash input has no file identity")
    _validate_expected_token(expected_identity, expected_change_token)
    native = to_filesystem_api_path(authorized.path, policy=authorized.policy)
    try:
        with native.open("rb", buffering=0) as handle:
            pre_identity = _identity_from_stat(os.fstat(handle.fileno()))
            if not _same_open_identity(expected_identity, pre_identity):
                raise MibaoError("MB-HASH-0002", "Hash input changed before the stream opened")
            pre_sample = _sample_handle(
                handle, int(pre_identity.size or 0), policy.sample_window_bytes
            )
            handle.seek(0)
            digest = hashlib.sha256()
            bytes_hashed = 0
            chunk_count = 0
            while True:
                block = handle.read(policy.chunk_size_bytes)
                if not block:
                    break
                digest.update(block)
                bytes_hashed += len(block)
                chunk_count += 1
            post_sample = _sample_handle(
                handle,
                int(pre_identity.size or 0),
                policy.sample_window_bytes,
            )
            post_identity = _identity_from_stat(os.fstat(handle.fileno()))
    except MibaoError:
        raise
    except OSError as exc:
        raise MibaoError(
            "MB-HASH-0003", f"Hash input could not be read: {type(exc).__name__}"
        ) from exc
    if bytes_hashed != pre_identity.size:
        raise MibaoError("MB-HASH-0002", "Hash stream length changed during the read")
    if not _same_open_identity(pre_identity, post_identity):
        raise MibaoError("MB-HASH-0002", "Hash input identity changed during the read")
    if pre_sample != post_sample:
        raise MibaoError("MB-HASH-0002", "Hash input sample changed during the read")
    current_identity = _revalidate_open_path(authorized, post_identity)
    _validate_expected_token(current_identity, expected_change_token)
    return HashReceipt(
        sha256=digest.hexdigest(),
        bytes_hashed=bytes_hashed,
        chunk_count=chunk_count,
        chunk_size_bytes=policy.chunk_size_bytes,
        sample=post_sample,
        pre_handle_identity=pre_identity,
        post_handle_identity=post_identity,
        post_path_identity=current_identity,
        validation_mode="full_hash",
        full_pass_count=1,
        candidate_change_token=expected_change_token,
        cache_decision="miss",
    )


def hash_file(
    root: Path,
    candidate: Path,
    *,
    policy: HashPolicy | None = None,
    expected_change_token: str | None = None,
) -> HashReceipt:
    """Hash one authorized file with bounded reads and before/after identity checks."""

    active_policy = policy or HashPolicy()
    authorized = authorize_existing_path(
        root,
        candidate,
        expected_kind="file",
        policy=PathPolicy(allow_unc=active_policy.allow_unc),
    )
    first = _hash_authorized(
        authorized,
        policy=active_policy,
        expected_change_token=expected_change_token,
    )
    if not active_policy.strict_rehash:
        return first
    second = _hash_authorized(
        authorized,
        policy=active_policy,
        expected_change_token=expected_change_token,
    )
    if first.sha256 != second.sha256 or first.bytes_hashed != second.bytes_hashed:
        raise MibaoError("MB-HASH-0002", "Strict rehash passes observed different content")
    return replace(
        second,
        validation_mode="strict_rehash",
        full_pass_count=2,
        cache_decision="bypass_strict",
    )


def _sample_authorized(
    authorized: AuthorizedPath,
    *,
    policy: HashPolicy,
    expected_change_token: str,
) -> tuple[_SampleReceipt, FileIdentity]:
    expected_identity = authorized.identity
    if expected_identity is None:
        raise MibaoError("MB-HASH-0002", "Sample input has no file identity")
    _validate_expected_token(expected_identity, expected_change_token)
    native = to_filesystem_api_path(authorized.path, policy=authorized.policy)
    try:
        with native.open("rb", buffering=0) as handle:
            pre_identity = _identity_from_stat(os.fstat(handle.fileno()))
            if not _same_open_identity(expected_identity, pre_identity):
                raise MibaoError("MB-HASH-0002", "Sample input changed before open")
            sample = _sample_handle(handle, int(pre_identity.size or 0), policy.sample_window_bytes)
            post_identity = _identity_from_stat(os.fstat(handle.fileno()))
    except MibaoError:
        raise
    except OSError as exc:
        raise MibaoError(
            "MB-HASH-0003", f"Sample input could not be read: {type(exc).__name__}"
        ) from exc
    if not _same_open_identity(pre_identity, post_identity):
        raise MibaoError("MB-HASH-0002", "Sample input changed during the read")
    current_identity = _revalidate_open_path(authorized, post_identity)
    _validate_expected_token(current_identity, expected_change_token)
    return sample, current_identity


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA synchronous = FULL")
    connection.execute("PRAGMA journal_mode = DELETE")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def compute_hash_assurance_snapshot(
    connection: sqlite3.Connection,
    project_id: str,
    *,
    batch_size: int = 512,
) -> _HashAssuranceSnapshot:
    """Digest the complete present path/Operation binding in one SQLite snapshot."""

    scan_state = compute_scan_completeness_snapshot(connection, project_id)
    source_root_ids = scan_state.source_root_ids
    digest = hashlib.sha256()
    digest.update(b"mibao.hash-assurance-snapshot.v2\0")
    digest.update(
        _json(
            {
                "project_id": project_id,
                "source_root_ids": source_root_ids,
                "scan_state_sha256": scan_state.sha256,
            }
        ).encode()
    )
    present_scan_candidate_count = int(
        connection.execute(
            "SELECT count(*) FROM operations WHERE project_id=? "
            "AND operation_type='scan_candidate' "
            "AND json_extract(result_json, '$.present')=1",
            (project_id,),
        ).fetchone()[0]
    )
    cursor = connection.execute(
        "SELECT operation.operation_id, operation.request_json, operation.result_json, "
        "operation.asset_id, operation.status, operation.updated_at, "
        "file.file_instance_id, file.asset_id, file.source_root_id, file.relative_path, "
        "file.file_size, file.modified_time_ms, file.identity_json, file.state "
        "FROM operations AS operation JOIN file_instances AS file "
        "ON file.project_id=operation.project_id "
        "AND file.source_root_id=json_extract(operation.request_json, '$.source_root_id') "
        "AND file.relative_path=json_extract(operation.request_json, '$.relative_path') "
        "WHERE operation.project_id=? AND operation.operation_type='scan_candidate' "
        "AND json_extract(operation.result_json, '$.present')=1 AND file.state='present' "
        "ORDER BY file.file_instance_id",
        (project_id,),
    )
    present_count = 0
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        for row in rows:
            encoded = _json(list(row)).encode()
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
            present_count += 1
    duplicate_summary = connection.execute(
        "SELECT count(*), coalesce(sum(member_count), 0) FROM ("
        "SELECT count(*) AS member_count FROM file_instances "
        "WHERE project_id=? AND state='present' GROUP BY asset_id HAVING count(*)>1)",
        (project_id,),
    ).fetchone()
    duplicate_groups = int(duplicate_summary[0]) if duplicate_summary else 0
    duplicate_members = int(duplicate_summary[1]) if duplicate_summary else 0
    digest.update(
        _json(
            {
                "present_file_instance_count": present_count,
                "present_scan_candidate_count": present_scan_candidate_count,
                "exact_duplicate_group_count": duplicate_groups,
                "duplicate_member_count": duplicate_members,
            }
        ).encode()
    )
    return _HashAssuranceSnapshot(
        source_root_ids=source_root_ids,
        present_scan_candidate_count=present_scan_candidate_count,
        present_file_instance_count=present_count,
        exact_duplicate_group_count=duplicate_groups,
        duplicate_member_count=duplicate_members,
        duplicate_extra_copy_count=duplicate_members - duplicate_groups,
        scan_state_sha256=scan_state.sha256,
        sha256=digest.hexdigest(),
    )


def _validate_candidate_request(payload: object, source_root_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != _CANDIDATE_KEYS:
        raise MibaoError("MB-HASH-0004", "Scan candidate request schema is invalid")
    if payload.get("schema_version") != "1.0" or payload.get("source_root_id") != source_root_id:
        raise MibaoError("MB-HASH-0004", "Scan candidate source binding is invalid")
    relative = payload.get("relative_path")
    if not isinstance(relative, str) or relative != unicodedata.normalize("NFC", relative):
        raise MibaoError("MB-HASH-0004", "Scan candidate relative path is invalid")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise MibaoError("MB-HASH-0004", "Scan candidate relative path is unsafe")
    for field in ("size_bytes", "modified_time_ms"):
        value = payload.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise MibaoError("MB-HASH-0004", f"Scan candidate {field} is invalid")
    identity = payload.get("identity")
    if not isinstance(identity, dict) or set(identity) != {"device", "inode", "mode"}:
        raise MibaoError("MB-HASH-0004", "Scan candidate identity is invalid")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in identity.values()
    ):
        raise MibaoError("MB-HASH-0004", "Scan candidate identity values are invalid")
    token = payload.get("change_token")
    if not isinstance(token, str) or _HEX_64.fullmatch(token) is None:
        raise MibaoError("MB-HASH-0004", "Scan candidate change token is invalid")
    return payload


def _snapshot(row: tuple[object, ...], source_root_id: str) -> _CandidateSnapshot:
    operation_id, request_text, result_text, asset_id, status, updated_at = row
    try:
        request = _validate_candidate_request(json.loads(str(request_text)), source_root_id)
        result_value: object = json.loads(str(result_text))
    except json.JSONDecodeError as exc:
        raise MibaoError("MB-HASH-0004", "Scan candidate JSON is invalid") from exc
    if not isinstance(result_value, dict) or result_value.get("present") is not True:
        raise MibaoError("MB-HASH-0004", "Scan candidate result is not present")
    return _CandidateSnapshot(
        operation_id=str(operation_id),
        request_text=str(request_text),
        result_text=str(result_text),
        asset_id=str(asset_id) if asset_id is not None else None,
        status=str(status),
        updated_at=str(updated_at),
        request=request,
        result=result_value,
    )


def _path_key(relative_path: str) -> str:
    normalized = unicodedata.normalize("NFC", relative_path)
    return normalized.casefold() if os.name == "nt" else normalized


def _authorize_scanned_candidate(
    source: AuthorizedPath,
    candidate: Path,
    *,
    policy: PathPolicy,
) -> AuthorizedPath:
    """Authorize one persisted relative path beneath an already authorized SourceRoot."""

    try:
        relative = candidate.relative_to(source.path)
    except ValueError as exc:
        raise MibaoError("MB-FS-0002", "Hash candidate escapes the SourceRoot") from exc
    if not relative.parts or ".." in relative.parts:
        raise MibaoError("MB-FS-0002", "Hash candidate relative path is unsafe")
    validate_windows_path_syntax(candidate, allow_unc=policy.allow_unc, policy=policy)
    current = source.path
    metadata: os.stat_result | None = None
    try:
        for component in relative.parts:
            current = current / component
            native_component = to_filesystem_api_path(current, policy=policy)
            metadata = os.lstat(native_component)
            attributes = int(getattr(metadata, "st_file_attributes", 0))
            reparse_attribute = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
            is_junction = getattr(os.path, "isjunction", None)
            if (
                stat.S_ISLNK(metadata.st_mode)
                or attributes & reparse_attribute
                or (callable(is_junction) and bool(is_junction(native_component)))
            ):
                raise MibaoError("MB-FS-0003", "Hash candidate contains a reparse component")
    except MibaoError:
        raise
    except OSError as exc:
        raise MibaoError("MB-HASH-0002", "Hash candidate does not exist") from exc
    if metadata is None or not stat.S_ISREG(metadata.st_mode):
        raise MibaoError("MB-HASH-0002", "Hash candidate is not a regular file")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(source.path)
    except (OSError, ValueError) as exc:
        raise MibaoError("MB-FS-0002", "Hash candidate resolved outside SourceRoot") from exc
    return AuthorizedPath(
        root=source.path,
        path=resolved,
        relative=relative,
        exists=True,
        kind="file",
        identity=_identity_from_stat(metadata),
        policy=policy,
    )


def _asset_id(project_id: str, content_sha256: str) -> str:
    payload = f"mibao.asset.v1\0{project_id}\0{content_sha256}".encode()
    return "AST-" + hashlib.sha256(payload).hexdigest()


def _file_instance_id(project_id: str, source_root_id: str, relative_path: str) -> str:
    payload = (
        f"mibao.file-instance.v1\0{project_id}\0{source_root_id}\0{_path_key(relative_path)}"
    ).encode()
    return "FIL-" + hashlib.sha256(payload).hexdigest()


def _cache_reusable(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    snapshot: _CandidateSnapshot,
    sample: _SampleReceipt,
    identity: FileIdentity,
) -> bool:
    content_hash = snapshot.result.get("content_hash")
    promotion = snapshot.result.get("promotion")
    if not isinstance(content_hash, dict) or not isinstance(promotion, dict):
        return False
    digest = content_hash.get("sha256")
    persisted_bytes = content_hash.get("bytes_hashed")
    persisted_sample = content_hash.get("sample")
    validation_mode = content_hash.get("validation_mode")
    full_pass_count = content_hash.get("full_pass_count")
    cache_receipt = content_hash.get("cache")
    relative = str(snapshot.request["relative_path"])
    source_root_id = str(snapshot.request["source_root_id"])
    expected_file_id = _file_instance_id(project_id, source_root_id, relative)
    if (
        content_hash.get("schema_version") != "1.0"
        or content_hash.get("policy_version") != _HASH_POLICY_VERSION
        or content_hash.get("content_assertion") != "current_full_verified"
        or content_hash.get("algorithm") != "sha256"
        or content_hash.get("full_hash_performed") is not True
        or content_hash.get("path_revalidated") is not True
        or validation_mode not in {"full_hash", "strict_rehash"}
        or full_pass_count != (2 if validation_mode == "strict_rehash" else 1)
        or not isinstance(cache_receipt, dict)
        or cache_receipt.get("authority") != "current_full_hash"
        or cache_receipt.get("decision") not in {"miss", "bypass_strict"}
        or content_hash.get("candidate_change_token") != snapshot.request["change_token"]
        or not isinstance(digest, str)
        or _HEX_64.fullmatch(digest) is None
        or not isinstance(persisted_sample, dict)
        or persisted_sample.get("scheme") != _SAMPLE_SCHEME
        or persisted_sample.get("digest") != sample.digest
        or persisted_sample.get("windows") != sample.as_dict()["windows"]
        or snapshot.asset_id != _asset_id(project_id, digest)
        or promotion.get("asset_id") != snapshot.asset_id
        or promotion.get("file_instance_id") != expected_file_id
        or not isinstance(persisted_bytes, int)
        or isinstance(persisted_bytes, bool)
        or persisted_bytes != identity.size
        or identity.device == 0
        or identity.inode == 0
    ):
        return False
    expected_identity = _identity_dict(identity)
    if any(
        content_hash.get(field) != expected_identity
        for field in ("pre_handle_identity", "post_handle_identity", "post_path_identity")
    ):
        return False
    asset = connection.execute(
        "SELECT asset_id, sha256, byte_size FROM assets WHERE project_id=? AND asset_id=?",
        (project_id, snapshot.asset_id),
    ).fetchone()
    file_instance = connection.execute(
        "SELECT file_instance_id, asset_id, state, identity_json FROM file_instances "
        "WHERE project_id=? AND source_root_id=? AND relative_path=?",
        (project_id, source_root_id, relative),
    ).fetchone()
    if asset != (snapshot.asset_id, digest, identity.size) or file_instance is None:
        return False
    if file_instance[:3] != (expected_file_id, snapshot.asset_id, "present"):
        return False
    try:
        persisted_identity = json.loads(str(file_instance[3]))
    except json.JSONDecodeError:
        return False
    return (
        isinstance(persisted_identity, dict)
        and persisted_identity.get("schema_version") == "1.0"
        and persisted_identity.get("scan_change_token") == snapshot.request["change_token"]
        and persisted_identity.get("sample_scheme") == _SAMPLE_SCHEME
        and persisted_identity.get("sample_digest") == sample.digest
    )


def _content_observations_bound(result: dict[str, Any], content_sha256: str) -> bool:
    binding = result.get("content_binding")
    return (
        isinstance(binding, dict)
        and binding.get("schema_version") == "1.0"
        and binding.get("algorithm") == "sha256"
        and binding.get("sha256") == content_sha256
        and binding.get("content_assertion") == "current_full_verified"
    )


def _technical_payload(result: dict[str, Any], content_sha256: str) -> dict[str, Any]:
    content_bound = _content_observations_bound(result, content_sha256)
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "content_identity": {"algorithm": "sha256", "sha256": content_sha256},
    }
    media_probe = result.get("media_probe")
    metadata = result.get("metadata")
    payload["candidate_observations"] = {
        "content_bound": content_bound,
        "media_probe_present": isinstance(media_probe, dict),
        "metadata_present": isinstance(metadata, dict),
    }
    if content_bound and isinstance(media_probe, dict):
        payload["media_probe"] = media_probe
    if isinstance(metadata, dict):
        evidence_surface = metadata.get("evidence_surface")
        if isinstance(evidence_surface, str):
            payload["metadata_evidence_surface"] = evidence_surface
        if (
            content_bound
            and metadata.get("production_verified") is True
            and isinstance(metadata.get("normalized"), dict)
        ):
            payload["normalized_metadata"] = metadata["normalized"]
    return payload


def _media_kind(result: dict[str, Any], content_sha256: str) -> str:
    if not _content_observations_bound(result, content_sha256):
        return "other"
    media_probe = result.get("media_probe")
    if isinstance(media_probe, dict) and media_probe.get("media_kind") in {
        "video",
        "audio",
        "image",
        "document",
        "other",
    }:
        return str(media_probe["media_kind"])
    return "other"


def _reconcile_asset(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    asset_id: str,
    timestamp: str,
) -> None:
    connection.execute(
        "UPDATE assets SET state=CASE WHEN EXISTS("
        "SELECT 1 FROM file_instances WHERE project_id=? AND asset_id=? AND state='present'"
        ") THEN 'active' ELSE 'missing' END, updated_at=? "
        "WHERE project_id=? AND asset_id=? AND state<>'quarantined'",
        (project_id, asset_id, timestamp, project_id, asset_id),
    )


def _apply_prepared(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    source_root_id: str,
    prepared: _PreparedPromotion,
    timestamp: str,
    test_hook: _TestHook | None,
) -> None:
    snapshot = prepared.snapshot
    receipt = prepared.receipt
    relative = str(snapshot.request["relative_path"])
    asset_id = _asset_id(project_id, receipt.sha256)
    file_instance_id = _file_instance_id(project_id, source_root_id, relative)
    current_snapshot = connection.execute(
        "SELECT request_json, result_json, asset_id, status, updated_at FROM operations "
        "WHERE project_id=? AND operation_id=?",
        (project_id, snapshot.operation_id),
    ).fetchone()
    if current_snapshot != (
        snapshot.request_text,
        snapshot.result_text,
        snapshot.asset_id,
        snapshot.status,
        snapshot.updated_at,
    ):
        raise _StaleSnapshot
    connection.execute(
        "INSERT INTO assets("
        "asset_id, project_id, sha256, media_kind, byte_size, capture_time_ms, "
        "technical_json, state, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, NULL, ?, 'active', ?, ?) "
        "ON CONFLICT(project_id, sha256) DO NOTHING",
        (
            asset_id,
            project_id,
            receipt.sha256,
            _media_kind(snapshot.result, receipt.sha256),
            receipt.bytes_hashed,
            _json(_technical_payload(snapshot.result, receipt.sha256)),
            timestamp,
            timestamp,
        ),
    )
    asset = connection.execute(
        "SELECT asset_id, byte_size FROM assets WHERE project_id=? AND sha256=?",
        (project_id, receipt.sha256),
    ).fetchone()
    if asset != (asset_id, receipt.bytes_hashed):
        raise MibaoError("MB-HASH-0005", "Content-addressed Asset identity is inconsistent")
    if test_hook is not None:
        test_hook("after_asset_upsert", snapshot.operation_id)
    prior_file = connection.execute(
        "SELECT asset_id, first_seen_at FROM file_instances "
        "WHERE project_id=? AND source_root_id=? AND relative_path=?",
        (project_id, source_root_id, relative),
    ).fetchone()
    old_asset_id = str(prior_file[0]) if prior_file is not None else None
    first_seen = str(prior_file[1]) if prior_file is not None else timestamp
    identity_payload = {
        "schema_version": "1.0",
        "path_identity": _identity_dict(receipt.post_path_identity),
        "scan_change_token": snapshot.request["change_token"],
        "sample_scheme": _SAMPLE_SCHEME,
        "sample_digest": receipt.sample.digest,
        "content_assertion_at_write": "current_full_verified",
    }
    connection.execute(
        "INSERT INTO file_instances("
        "file_instance_id, project_id, asset_id, source_root_id, relative_path, file_size, "
        "modified_time_ms, identity_json, state, first_seen_at, last_seen_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'present', ?, ?) "
        "ON CONFLICT(project_id, source_root_id, relative_path) DO UPDATE SET "
        "asset_id=excluded.asset_id, file_size=excluded.file_size, "
        "modified_time_ms=excluded.modified_time_ms, identity_json=excluded.identity_json, "
        "state='present', last_seen_at=excluded.last_seen_at",
        (
            file_instance_id,
            project_id,
            asset_id,
            source_root_id,
            relative,
            receipt.bytes_hashed,
            int(receipt.post_path_identity.modified_ns or 0) // 1_000_000,
            _json(identity_payload),
            first_seen,
            timestamp,
        ),
    )
    if test_hook is not None:
        test_hook("after_file_instance_upsert", snapshot.operation_id)
    result = dict(snapshot.result)
    if isinstance(result.get("media_probe"), dict) or isinstance(result.get("metadata"), dict):
        result["content_observation_state"] = (
            "current_content_bound"
            if _content_observations_bound(result, receipt.sha256)
            else "unbound_or_stale_content"
        )
    result["content_hash"] = receipt.as_dict()
    result["promotion"] = {
        "schema_version": "1.0",
        "asset_id": asset_id,
        "file_instance_id": file_instance_id,
        "content_assertion": "current_full_verified",
        "promoted_at": timestamp,
    }
    cursor = connection.execute(
        "UPDATE operations SET asset_id=?, result_json=?, status='succeeded', updated_at=? "
        "WHERE project_id=? AND operation_id=? AND request_json=? AND result_json=? "
        "AND asset_id IS ? AND status=? AND updated_at=?",
        (
            asset_id,
            _json(result),
            timestamp,
            project_id,
            snapshot.operation_id,
            snapshot.request_text,
            snapshot.result_text,
            snapshot.asset_id,
            snapshot.status,
            snapshot.updated_at,
        ),
    )
    if cursor.rowcount != 1:
        raise _StaleSnapshot
    if test_hook is not None:
        test_hook("after_operation_cas", snapshot.operation_id)
    _reconcile_asset(
        connection,
        project_id=project_id,
        asset_id=asset_id,
        timestamp=timestamp,
    )
    if old_asset_id is not None and old_asset_id != asset_id:
        _reconcile_asset(
            connection,
            project_id=project_id,
            asset_id=old_asset_id,
            timestamp=timestamp,
        )


def _registered_source_id(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    source: AuthorizedPath,
) -> str:
    if source.identity is None:
        raise MibaoError("MB-HASH-0002", "Source root has no physical identity")
    expected_identity = _json(
        {
            "device": source.identity.device,
            "inode": source.identity.inode,
            "mode": source.identity.mode,
        }
    )
    row = connection.execute(
        "SELECT source_root_id, path_identity_json FROM source_roots "
        "WHERE project_id=? AND canonical_path=? AND state='active'",
        (project_id, str(source.path)),
    ).fetchone()
    if row is None or row[1] != expected_identity:
        raise MibaoError("MB-HASH-0002", "Source root is unregistered or changed")
    return str(row[0])


def _prepare_batch(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    source_root_id: str,
    source: AuthorizedPath,
    rows: list[tuple[object, ...]],
    policy: HashPolicy,
    counters: _Counters,
    test_hook: _TestHook | None,
) -> list[_PreparedPromotion]:
    prepared: list[_PreparedPromotion] = []
    single_pass_policy = replace(policy, strict_rehash=False)
    for row in rows:
        try:
            snapshot = _snapshot(row, source_root_id)
            relative = str(snapshot.request["relative_path"])
            candidate = source.path / Path(*PurePosixPath(relative).parts)
            token = str(snapshot.request["change_token"])
            path_policy = PathPolicy(allow_unc=policy.allow_unc)
            authorized = _authorize_scanned_candidate(
                source,
                candidate,
                policy=path_policy,
            )
            if authorized.identity is None:
                raise MibaoError("MB-HASH-0002", "Hash candidate has no current identity")
            _validate_expected_token(authorized.identity, token)
            cache_invalidated = False
            if not policy.strict_rehash and not policy.allow_unc and snapshot.asset_id is not None:
                sample, identity = _sample_authorized(
                    authorized,
                    policy=policy,
                    expected_change_token=token,
                )
                if _cache_reusable(
                    connection,
                    project_id=project_id,
                    snapshot=snapshot,
                    sample=sample,
                    identity=identity,
                ):
                    counters.reused += 1
                    counters.cache_hints += 1
                    continue
                cache_invalidated = isinstance(snapshot.result.get("content_hash"), dict)
            first = _hash_authorized(
                authorized,
                policy=single_pass_policy,
                expected_change_token=token,
            )
            if test_hook is not None:
                test_hook("after_hash", snapshot.operation_id)
            receipt = first
            if policy.strict_rehash:
                second = _hash_authorized(
                    authorized,
                    policy=single_pass_policy,
                    expected_change_token=token,
                )
                if first.sha256 != second.sha256 or first.bytes_hashed != second.bytes_hashed:
                    raise MibaoError(
                        "MB-HASH-0002", "Strict rehash passes observed different content"
                    )
                receipt = replace(
                    second,
                    validation_mode="strict_rehash",
                    full_pass_count=2,
                    cache_decision="bypass_strict",
                )
            prepared.append(
                _PreparedPromotion(
                    snapshot=snapshot,
                    authorized=authorized,
                    receipt=receipt,
                    cache_invalidated=cache_invalidated,
                )
            )
            counters.full_hashes += 1
            counters.bytes_hashed += receipt.bytes_hashed
            counters.chunks += receipt.chunk_count
            if policy.strict_rehash:
                counters.strict_rehashes += 1
        except MibaoError as exc:
            if exc.code in {"MB-HASH-0002", "MB-FS-0001", "MB-FS-0006"}:
                counters.stale += 1
            else:
                counters.failed += 1
    return prepared


def _guard_prepared(
    prepared: list[_PreparedPromotion],
    *,
    policy: HashPolicy,
    counters: _Counters,
) -> list[_PreparedPromotion]:
    guarded: list[_PreparedPromotion] = []
    for item in prepared:
        try:
            sample, _ = _sample_authorized(
                item.authorized,
                policy=policy,
                expected_change_token=str(item.snapshot.request["change_token"]),
            )
            if sample != item.receipt.sample:
                raise MibaoError("MB-HASH-0002", "Candidate changed after full hashing")
            guarded.append(item)
        except MibaoError:
            counters.stale += 1
    return guarded


def _commit_batch(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    source_root_id: str,
    prepared: list[_PreparedPromotion],
    counters: _Counters,
    test_hook: _TestHook | None,
) -> None:
    if not prepared:
        return
    timestamp = _timestamp()
    connection.execute("BEGIN IMMEDIATE")
    try:
        for item in prepared:
            connection.execute("SAVEPOINT mibao_promote_candidate")
            try:
                _apply_prepared(
                    connection,
                    project_id=project_id,
                    source_root_id=source_root_id,
                    prepared=item,
                    timestamp=timestamp,
                    test_hook=test_hook,
                )
                connection.execute("RELEASE SAVEPOINT mibao_promote_candidate")
                counters.promoted += 1
                counters.current_full_verified += 1
                if item.cache_invalidated:
                    counters.cache_invalidations += 1
            except _StaleSnapshot:
                connection.execute("ROLLBACK TO SAVEPOINT mibao_promote_candidate")
                connection.execute("RELEASE SAVEPOINT mibao_promote_candidate")
                counters.stale += 1
        connection.commit()
        counters.committed_batches += 1
    except BaseException:
        connection.rollback()
        raise


def _database_counts(connection: sqlite3.Connection, project_id: str) -> tuple[int, ...]:
    asset_count = int(
        connection.execute(
            "SELECT count(*) FROM assets WHERE project_id=?", (project_id,)
        ).fetchone()[0]
    )
    active_asset_count = int(
        connection.execute(
            "SELECT count(*) FROM assets WHERE project_id=? AND state='active'", (project_id,)
        ).fetchone()[0]
    )
    file_count = int(
        connection.execute(
            "SELECT count(*) FROM file_instances WHERE project_id=?", (project_id,)
        ).fetchone()[0]
    )
    present_count = int(
        connection.execute(
            "SELECT count(*) FROM file_instances WHERE project_id=? AND state='present'",
            (project_id,),
        ).fetchone()[0]
    )
    duplicate_summary = connection.execute(
        "SELECT count(*), coalesce(sum(member_count), 0) FROM ("
        "SELECT count(*) AS member_count FROM file_instances "
        "WHERE project_id=? AND state='present' GROUP BY asset_id HAVING count(*)>1)",
        (project_id,),
    ).fetchone()
    duplicate_groups = int(duplicate_summary[0]) if duplicate_summary else 0
    duplicate_members = int(duplicate_summary[1]) if duplicate_summary else 0
    return (
        asset_count,
        active_asset_count,
        file_count,
        present_count,
        duplicate_groups,
        duplicate_members,
        duplicate_members - duplicate_groups,
    )


def promote_scan_candidates(
    project_root: Path,
    source_root: Path,
    *,
    policy: HashPolicy | None = None,
    _test_hook: _TestHook | None = None,
) -> PromotionResult:
    """Promote present scanner candidates through full SHA-256 into durable Assets."""

    active_policy = policy or HashPolicy()
    project = open_project(project_root)
    path_policy = PathPolicy(allow_unc=active_policy.allow_unc)
    source, _ = validate_root_pair(source_root, project.root, policy=path_policy)
    counters = _Counters()
    source_root_id = ""
    scan_state_sha256 = ""
    all_present_currently_verified = False
    assurance_token: HashAssuranceToken | None = None
    with ProjectLock(project.root):
        connection = _connect(project.database_path)
        try:
            audit_schema(
                connection,
                expected_project_id=project.project_id,
                expected_privacy_mode=project.privacy_mode,
            )
            scan_state = compute_scan_completeness_snapshot(connection, project.project_id)
            if not scan_state.complete:
                raise MibaoError(
                    "MB-HASH-0006",
                    "Hash promotion requires a complete terminal inventory scan: "
                    + ",".join(scan_state.pending_reasons),
                )
            scan_state_sha256 = scan_state.sha256
            source_root_id = _registered_source_id(
                connection,
                project_id=project.project_id,
                source=source,
            )
            cursor = ""
            processed = 0
            while True:
                records = connection.execute(
                    "SELECT operation_id, request_json, result_json, asset_id, status, updated_at "
                    "FROM operations WHERE project_id=? AND operation_type='scan_candidate' "
                    "AND operation_id>? AND json_extract(result_json, '$.present')=1 "
                    "AND json_extract(request_json, '$.source_root_id')=? "
                    "ORDER BY operation_id LIMIT ?",
                    (
                        project.project_id,
                        cursor,
                        source_root_id,
                        active_policy.promotion_batch_size,
                    ),
                ).fetchall()
                if not records:
                    break
                cursor = str(records[-1][0])
                processed += len(records)
                if processed > active_policy.max_candidates:
                    raise MibaoError("MB-HASH-0005", "Hash candidate limit exceeded")
                counters.max_batch = max(counters.max_batch, len(records))
                prepared = _prepare_batch(
                    connection,
                    project_id=project.project_id,
                    source_root_id=source_root_id,
                    source=source,
                    rows=records,
                    policy=active_policy,
                    counters=counters,
                    test_hook=_test_hook,
                )
                source.revalidate()
                guarded = _guard_prepared(
                    prepared,
                    policy=active_policy,
                    counters=counters,
                )
                _commit_batch(
                    connection,
                    project_id=project.project_id,
                    source_root_id=source_root_id,
                    prepared=guarded,
                    counters=counters,
                    test_hook=_test_hook,
                )
            audit_schema(
                connection,
                expected_project_id=project.project_id,
                expected_privacy_mode=project.privacy_mode,
            )
            foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_key_errors:
                raise MibaoError("MB-HASH-0005", "Promotion left inconsistent foreign keys")
            counts = _database_counts(connection, project.project_id)
            snapshot = compute_hash_assurance_snapshot(connection, project.project_id)
            if snapshot.scan_state_sha256 != scan_state_sha256:
                raise MibaoError("MB-HASH-0006", "Inventory scan state changed during hashing")
            all_present_currently_verified = (
                counters.current_full_verified == snapshot.present_scan_candidate_count
                and snapshot.present_scan_candidate_count == counts[3]
                and counters.cache_hints == 0
                and counters.stale == 0
                and counters.failed == 0
            )
            if all_present_currently_verified:
                if (
                    snapshot.present_file_instance_count != counts[3]
                    or snapshot.exact_duplicate_group_count != counts[4]
                    or snapshot.duplicate_member_count != counts[5]
                    or snapshot.duplicate_extra_copy_count != counts[6]
                ):
                    raise MibaoError(
                        "MB-HASH-0005",
                        "Hash assurance snapshot does not reconcile to project counts",
                    )
                assurance_token = HashAssuranceToken(
                    project_id=project.project_id,
                    source_root_ids=snapshot.source_root_ids,
                    present_scan_candidate_count=snapshot.present_scan_candidate_count,
                    present_file_instance_count=snapshot.present_file_instance_count,
                    current_full_verified_count=counters.current_full_verified,
                    exact_duplicate_group_count=snapshot.exact_duplicate_group_count,
                    duplicate_member_count=snapshot.duplicate_member_count,
                    duplicate_extra_copy_count=snapshot.duplicate_extra_copy_count,
                    scan_state_sha256=snapshot.scan_state_sha256,
                    snapshot_sha256=snapshot.sha256,
                    issued_at=_timestamp(),
                )
                _ISSUED_ASSURANCE_TOKENS[id(assurance_token)] = assurance_token
        except sqlite3.Error as exc:
            if connection.in_transaction:
                connection.rollback()
            raise MibaoError("MB-HASH-0005", f"Hash promotion transaction failed: {exc}") from exc
        finally:
            connection.close()
    current_duplicate_counts = counts[4:7] if all_present_currently_verified else (0, 0, 0)
    return PromotionResult(
        project_id=project.project_id,
        source_root_id=source_root_id,
        promoted_candidates=counters.promoted,
        reused_candidates=counters.reused,
        full_hashes=counters.full_hashes,
        strict_rehashes=counters.strict_rehashes,
        cache_invalidations=counters.cache_invalidations,
        stale_candidates=counters.stale,
        failed_candidates=counters.failed,
        current_full_verified_candidates=counters.current_full_verified,
        prior_hash_cache_hint_candidates=counters.cache_hints,
        asset_count=counts[0],
        active_asset_count=counts[1],
        file_instance_count=counts[2],
        present_file_instance_count=counts[3],
        exact_duplicate_group_count=current_duplicate_counts[0],
        duplicate_member_count=current_duplicate_counts[1],
        duplicate_extra_copy_count=current_duplicate_counts[2],
        historical_exact_duplicate_group_count=counts[4],
        historical_duplicate_member_count=counts[5],
        historical_duplicate_extra_copy_count=counts[6],
        duplicate_assurance=(
            "current_full_verified_all_present"
            if all_present_currently_verified
            else "historical_last_full_verified_only"
        ),
        committed_batches=counters.committed_batches,
        max_batch_candidates=counters.max_batch,
        bytes_hashed=counters.bytes_hashed,
        chunk_count=counters.chunks,
        scan_state_sha256=scan_state_sha256,
        assurance_token=assurance_token,
    )
