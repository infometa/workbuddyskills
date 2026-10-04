"""Closed one-shot execution surface for the no-MCP WorkBuddy expert."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from mibao_core.errors import MibaoError
from mibao_core.filesystem.paths import (
    PathPolicy,
    authorize_existing_path,
    authorize_output_path,
    validate_root_pair,
    validate_windows_path_syntax,
)
from mibao_core.filesystem.scanner import ScanPolicy, scan_project
from mibao_core.hashing import HashPolicy, promote_scan_candidates
from mibao_core.media_probe import MediaProbePolicy, classify_scan_candidates
from mibao_core.project import create_project, open_project_reader, open_project_writer
from mibao_core.reporting import InventoryReportPolicy, generate_inventory_report
from mibao_core.search import SearchDocument, search_documents, upsert_search_documents
from mibao_core.search.fts import SearchValidationError


class ExpertRuntimeError(ValueError):
    """Raised when the expert one-shot request cannot run safely."""


class ExpertPrivacyModeError(ExpertRuntimeError):
    """Raised when a legacy project must migrate before expert search."""


class ExpertRequestCleanupError(ExpertRuntimeError):
    """Raised when a claimed request may still remain on disk."""


class ExpertConsumedRequestError(ExpertRuntimeError):
    """Wrap an execution failure that happened after request consumption."""


class ExpertClaimedRequestError(ExpertRuntimeError):
    """Raised when a raced request was consumed without executing it."""


_MAX_REQUEST_BYTES: Final = 64 * 1024
_MAX_PATH_CHARS: Final = 32760
_MAX_DISPLAY_NAME_CHARS: Final = 128
_MAX_QUERY_CHARS: Final = 256
_REQUEST_VERSION: Final = "1.0"
_REQUEST_SCOPES: Final[frozenset[str]] = frozenset({"plugin-data", "session-workspace"})
_INVENTORY_DOCUMENT_PREFIX: Final = "EXPERT-ASSET-"
_PROJECT_MANIFEST_RELATIVE: Final = Path("project.json")
_PROJECT_DATABASE_RELATIVE: Final = Path("database/mibao.sqlite")
_REPARSE_FLAG: Final = 0x400


@dataclass(frozen=True, slots=True)
class InventoryBuildRequest:
    source_root: Path
    project_root: Path
    display_name: str
    scan_batch_size: int
    hash_batch_size: int
    max_entries: int
    max_depth: int
    html_preview_rows: int


@dataclass(frozen=True, slots=True)
class InventorySearchRequest:
    project_root: Path
    query: str
    limit: int


ExpertRequest = InventoryBuildRequest | InventorySearchRequest


@dataclass(frozen=True, slots=True)
class RequestFileFact:
    """Handle-bound content fact for the host-written one-shot request."""

    bytes_count: int
    sha256: str
    identity: tuple[int, int, int, int, int]


def _exact(value: object, keys: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ExpertRuntimeError(f"{name} shape is invalid")
    return value


def _text(value: object, name: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ExpertRuntimeError(f"{name} is invalid")
    if any(ord(character) < 32 for character in value):
        raise ExpertRuntimeError(f"{name} contains control characters")
    return value.strip()


def _integer(value: object, name: str, *, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ExpertRuntimeError(f"{name} is outside its bounded range")
    return value


def _absolute_path(value: object, name: str) -> Path:
    text = _text(value, name, maximum=_MAX_PATH_CHARS)
    path = Path(text)
    if not path.is_absolute() or ".." in path.parts:
        raise ExpertRuntimeError(f"{name} must be an absolute path without traversal")
    return path.absolute()


def parse_expert_request(payload: object) -> ExpertRequest:
    """Parse one closed inventory-build or inventory-search request."""

    document = _exact(payload, {"schemaVersion", "operation", "input"}, "expert request")
    operation = document["operation"]
    if operation == "inventory_build":
        if document["schemaVersion"] != _REQUEST_VERSION:
            raise ExpertRuntimeError("expert request schema version is unsupported")
        data = _exact(
            document["input"],
            {
                "sourceRoot",
                "projectRoot",
                "displayName",
                "scanBatchSize",
                "hashBatchSize",
                "maxEntries",
                "maxDepth",
                "htmlPreviewRows",
            },
            "inventory build input",
        )
        return InventoryBuildRequest(
            source_root=_absolute_path(data["sourceRoot"], "source root"),
            project_root=_absolute_path(data["projectRoot"], "project root"),
            display_name=_text(
                data["displayName"], "display name", maximum=_MAX_DISPLAY_NAME_CHARS
            ),
            scan_batch_size=_integer(
                data["scanBatchSize"], "scan batch size", minimum=1, maximum=512
            ),
            hash_batch_size=_integer(
                data["hashBatchSize"], "hash batch size", minimum=1, maximum=256
            ),
            max_entries=_integer(data["maxEntries"], "entry limit", minimum=1, maximum=100_000),
            max_depth=_integer(data["maxDepth"], "depth limit", minimum=1, maximum=64),
            html_preview_rows=_integer(
                data["htmlPreviewRows"], "HTML preview rows", minimum=1, maximum=2000
            ),
        )
    if operation == "inventory_search":
        if document["schemaVersion"] != _REQUEST_VERSION:
            raise ExpertRuntimeError("expert request schema version is unsupported")
        data = _exact(
            document["input"],
            {"projectRoot", "query", "limit"},
            "inventory search input",
        )
        return InventorySearchRequest(
            project_root=_absolute_path(data["projectRoot"], "project root"),
            query=_text(data["query"], "query", maximum=_MAX_QUERY_CHARS),
            limit=_integer(data["limit"], "result limit", minimum=1, maximum=100),
        )
    raise ExpertRuntimeError("expert operation is unsupported")


def _contains(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _request_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_nlink, value.st_size, value.st_mtime_ns)


def _assert_request_no_reparse_chain(path: Path) -> None:
    current = path.absolute()
    while True:
        try:
            observed = current.lstat()
        except OSError as exc:
            raise ExpertRuntimeError("expert request path is unavailable") from exc
        if current.is_symlink() or getattr(observed, "st_file_attributes", 0) & _REPARSE_FLAG:
            raise ExpertRuntimeError("expert request path contains a link or reparse point")
        parent = current.parent
        if parent == current:
            break
        current = parent


def _hash_stable_request_file(path: Path) -> RequestFileFact:
    _assert_request_no_reparse_chain(path)
    try:
        with path.open("rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size < 1:
                raise ExpertRuntimeError("expert request is not a nonempty regular file")
            if before.st_nlink != 1:
                raise ExpertRuntimeError("expert request must have exactly one physical link")
            digest = hashlib.sha256()
            bytes_count = 0
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
                bytes_count += len(block)
            after = os.fstat(handle.fileno())
        current = path.lstat()
    except OSError as exc:
        raise ExpertRuntimeError("expert request became unavailable") from exc
    if (
        bytes_count != before.st_size
        or _request_identity(before) != _request_identity(after)
        or _request_identity(after) != _request_identity(current)
    ):
        raise ExpertRuntimeError("expert request changed during hashing")
    return RequestFileFact(
        bytes_count=bytes_count,
        sha256=digest.hexdigest(),
        identity=_request_identity(current),
    )


def _authorize_build_roots(request: InventoryBuildRequest) -> None:
    policy = PathPolicy(allow_unc=False)
    source = authorize_existing_path(
        request.source_root,
        request.source_root,
        expected_kind="directory",
        policy=policy,
    )
    if request.project_root.exists():
        _, project = validate_root_pair(
            request.source_root,
            request.project_root,
            policy=policy,
        )
        manifest = project.path / _PROJECT_MANIFEST_RELATIVE
        database = project.path / _PROJECT_DATABASE_RELATIVE
        if manifest.exists() or manifest.is_symlink() or database.exists() or database.is_symlink():
            _authorize_project_root(project.path)
        return
    parent = request.project_root.parent
    output = authorize_output_path(parent, request.project_root, policy=policy)
    if _contains(source.path, output.path) or _contains(output.path, source.path):
        raise MibaoError("MB-FS-0005", "Source and project roots must not overlap")


def _authorize_project_root(project_root: Path) -> Path:
    policy = PathPolicy(allow_unc=False)
    root = authorize_existing_path(
        project_root,
        project_root,
        expected_kind="directory",
        policy=policy,
    ).path
    for relative in (_PROJECT_MANIFEST_RELATIVE, _PROJECT_DATABASE_RELATIVE):
        authorize_existing_path(
            root,
            root / relative,
            expected_kind="file",
            policy=policy,
        )
    return root


def _index_inventory(project_root: Path) -> tuple[int, int]:
    indexed = 0
    removed = 0
    with open_project_writer(project_root) as (project, connection):
        cursor = connection.execute(
            "SELECT f.file_instance_id, f.asset_id, f.relative_path, a.media_kind "
            "FROM file_instances AS f JOIN assets AS a "
            "ON a.project_id=f.project_id AND a.asset_id=f.asset_id "
            "WHERE f.project_id=? AND f.state='present' AND f.asset_id IS NOT NULL "
            "ORDER BY f.file_instance_id",
            (project.project_id,),
        )
        while rows := cursor.fetchmany(500):
            documents = []
            for file_instance_id, asset_id, relative_path, media_kind in rows:
                relative = str(relative_path)
                title = relative[-512:]
                body = f"{media_kind!s} {relative.replace('/', ' ')}"[-20_000:]
                documents.append(
                    SearchDocument(
                        document_id=_INVENTORY_DOCUMENT_PREFIX
                        + hashlib.sha256(str(file_instance_id).encode("utf-8")).hexdigest(),
                        project_id=project.project_id,
                        document_kind="asset",
                        title=title,
                        body=body,
                        source_ref=str(file_instance_id),
                        asset_id=str(asset_id),
                        evidence_refs=(str(file_instance_id),),
                        state="verified",
                    )
                )
            indexed += upsert_search_documents(connection, documents)
        connection.execute("BEGIN IMMEDIATE")
        try:
            cursor = connection.execute(
                "DELETE FROM search_documents "
                "WHERE project_id=? AND document_kind='asset' "
                "AND substr(document_id, 1, ?)=? "
                "AND NOT EXISTS ("
                "SELECT 1 FROM file_instances AS f "
                "WHERE f.project_id=search_documents.project_id "
                "AND f.file_instance_id=search_documents.source_ref "
                "AND f.state='present' AND f.asset_id IS NOT NULL)",
                (
                    project.project_id,
                    len(_INVENTORY_DOCUMENT_PREFIX),
                    _INVENTORY_DOCUMENT_PREFIX,
                ),
            )
            removed = cursor.rowcount
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
    return indexed, removed


def _inventory_build(request: InventoryBuildRequest) -> dict[str, object]:
    _authorize_build_roots(request)
    project = create_project(
        request.project_root,
        display_name=request.display_name,
        privacy_mode="local-private",
    )
    _authorize_project_root(project.root)
    validate_root_pair(request.source_root, project.root, policy=PathPolicy(allow_unc=False))
    scan = scan_project(
        project.root,
        request.source_root,
        policy=ScanPolicy(
            batch_size=request.scan_batch_size,
            max_entries=request.max_entries,
            max_depth=request.max_depth,
            allow_unc=False,
        ),
    )
    if scan.status != "completed":
        raise ExpertRuntimeError("inventory scan did not complete")
    classification = classify_scan_candidates(
        project.root,
        request.source_root,
        policy=MediaProbePolicy(
            classification_batch_size=request.scan_batch_size,
            max_candidates=request.max_entries,
        ),
        path_policy=PathPolicy(allow_unc=False),
    )
    if classification.failed_candidates or classification.stale_candidates:
        raise ExpertRuntimeError("media classification did not close every candidate")
    promotion = promote_scan_candidates(
        project.root,
        request.source_root,
        policy=HashPolicy(
            promotion_batch_size=request.hash_batch_size,
            max_candidates=request.max_entries,
            strict_rehash=True,
            allow_unc=False,
        ),
    )
    if (
        promotion.failed_candidates
        or promotion.stale_candidates
        or promotion.assurance_token is None
    ):
        raise ExpertRuntimeError("strict content promotion did not close every candidate")
    indexed, removed = _index_inventory(project.root)
    report = generate_inventory_report(
        project.root,
        assurance_token=promotion.assurance_token,
        policy=InventoryReportPolicy(
            batch_size=min(512, request.hash_batch_size * 4),
            max_rows=request.max_entries,
            html_preview_rows=request.html_preview_rows,
        ),
    )
    return {
        "schemaVersion": "1.0",
        "operation": "inventory_build",
        "ok": True,
        "status": "partial" if scan.issues else "completed",
        "project": project.as_dict(),
        "scan": {
            "sourceRootId": scan.source_root_id,
            "discoveredFiles": scan.discovered_files,
            "newCandidates": scan.inserted_candidates,
            "changedCandidates": scan.changed_candidates,
            "unchangedCandidates": scan.unchanged_candidates,
            "rejectedUnsafeEntries": scan.rejected_unsafe_entries,
            "rejectedReparseEntries": scan.rejected_reparse_entries,
            "unreadableEntries": scan.unreadable_entries,
            "issueCount": len(scan.issues),
            "issues": [
                {
                    "code": issue.code,
                    "relativePath": issue.relative_path,
                    "message": issue.message,
                }
                for issue in scan.issues
            ],
        },
        "classification": classification.as_dict(),
        "content": {
            "assetCount": promotion.asset_count,
            "fileInstanceCount": promotion.file_instance_count,
            "exactDuplicateGroupCount": promotion.exact_duplicate_group_count,
            "duplicateMemberCount": promotion.duplicate_member_count,
            "bytesHashed": promotion.bytes_hashed,
            "strictRehashes": promotion.strict_rehashes,
        },
        "searchIndexedDocumentCount": indexed,
        "searchRemovedDocumentCount": removed,
        "report": report.as_dict(project.root),
        "boundaries": {
            "sourceMutationRequested": False,
            "networkCallCount": 0,
            "externalDisclosureCreated": False,
            "mcpServiceInstalled": False,
            "persistentProcessCreated": False,
            "productionVerified": False,
        },
    }


def _inventory_search(request: InventorySearchRequest) -> dict[str, object]:
    with open_project_reader(_authorize_project_root(request.project_root)) as (
        project,
        connection,
    ):
        if project.privacy_mode != "local-private":
            raise ExpertPrivacyModeError("inventory search requires a local-private project")
        matches = search_documents(
            connection,
            project.project_id,
            request.query,
            limit=request.limit,
            document_kind="asset",
            document_id_prefix=_INVENTORY_DOCUMENT_PREFIX,
        )
        results: list[dict[str, object]] = []
        for match in matches:
            row = connection.execute(
                "SELECT relative_path, asset_id, source_root_id FROM file_instances "
                "WHERE project_id=? AND file_instance_id=? AND state='present'",
                (project.project_id, match.source_ref),
            ).fetchone()
            if row is None:
                raise ExpertRuntimeError("search result source binding is missing")
            results.append(
                {
                    "documentId": match.document_id,
                    "fileInstanceId": match.source_ref,
                    "assetId": str(row[1]),
                    "sourceRootId": str(row[2]),
                    "relativePath": str(row[0]),
                    "state": match.state,
                    "snippet": match.snippet,
                    "evidenceRefs": list(match.evidence_refs),
                }
            )
    return {
        "schemaVersion": "1.0",
        "operation": "inventory_search",
        "ok": True,
        "status": "completed",
        "projectId": project.project_id,
        "privacyMode": project.privacy_mode,
        "query": request.query,
        "resultCount": len(results),
        "results": results,
        "boundaries": {
            "databaseModified": False,
            "mediaRead": False,
            "networkCallCount": 0,
            "externalDisclosureCreated": False,
            "mcpServiceInstalled": False,
        },
    }


def execute_expert_request(payload: object) -> dict[str, object]:
    """Execute one already-decoded request and return a path-minimized result."""

    request = parse_expert_request(payload)
    return _execute_parsed_request(request)


def _execute_parsed_request(request: ExpertRequest) -> dict[str, object]:
    if isinstance(request, InventoryBuildRequest):
        return _inventory_build(request)
    return _inventory_search(request)


def _load_expert_request_with_fact(path: Path) -> tuple[object, RequestFileFact]:
    """Read a bounded request twice and return its stable physical fact."""

    try:
        observed_size = path.lstat().st_size
    except OSError as exc:
        raise ExpertRuntimeError("expert request is unavailable") from exc
    if not 1 <= observed_size <= _MAX_REQUEST_BYTES:
        raise ExpertRuntimeError("expert request exceeds the byte budget")
    fact = _hash_stable_request_file(path)
    if fact.bytes_count > _MAX_REQUEST_BYTES:
        raise ExpertRuntimeError("expert request exceeds the byte budget")
    content = path.read_bytes()
    after = _hash_stable_request_file(path)
    if after != fact or hashlib.sha256(content).hexdigest() != fact.sha256:
        raise ExpertRuntimeError("expert request changed during read")

    def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        keys = [item[0] for item in pairs]
        if len(keys) != len(set(keys)):
            raise ExpertRuntimeError("expert request contains duplicate keys")
        return dict(pairs)

    try:
        payload = json.loads(
            content.decode("utf-8", errors="strict"), object_pairs_hook=strict_object
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ExpertRuntimeError("expert request is not strict UTF-8 JSON") from exc
    return payload, fact


def load_expert_request(path: Path) -> object:
    """Read a bounded request twice with a stable physical identity."""

    payload, _ = _load_expert_request_with_fact(path)
    return payload


def _authorize_request_path(path: Path, request_root: Path, request_scope: str) -> Path:
    if request_scope not in _REQUEST_SCOPES:
        raise ExpertRuntimeError("expert request scope is unsupported")
    if not path.is_absolute() or not request_root.is_absolute():
        raise ExpertRuntimeError("expert request path and root must be absolute")
    policy = PathPolicy(allow_unc=False)
    try:
        validate_windows_path_syntax(path, allow_unc=False, policy=policy)
        validate_windows_path_syntax(request_root, allow_unc=False, policy=policy)
    except MibaoError as exc:
        raise ExpertRuntimeError("expert request path or root violates local path policy") from exc
    resolved = path.absolute()
    root = request_root.absolute()
    if request_scope == "session-workspace" and root.name != ".workbuddy":
        raise ExpertRuntimeError("session request root must be the workspace .workbuddy directory")
    expected = root / "mibao" / "expert-request.json"
    if resolved != expected:
        raise ExpertRuntimeError("expert request path is outside its contract root")
    if not root.is_dir():
        raise ExpertRuntimeError("expert request root is unavailable")
    _assert_request_no_reparse_chain(root)
    _assert_request_no_reparse_chain(resolved)
    return resolved


def _delete_claimed_request(claimed: Path) -> None:
    """Delete only the atomically claimed path and fail closed on possible residue."""

    try:
        claimed.unlink()
    except OSError as exc:
        raise ExpertRequestCleanupError("claimed expert request may remain on disk") from exc
    try:
        claimed.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise ExpertRequestCleanupError("claimed expert request absence is unknown") from exc
    raise ExpertRequestCleanupError("claimed expert request may remain on disk")


def _consume_request(path: Path, fact: RequestFileFact) -> None:
    """Atomically claim, revalidate, and delete the exact parsed request bytes."""

    claimed = path.with_name(f".expert-request.{secrets.token_hex(16)}.consuming")
    try:
        path.rename(claimed)
    except OSError as exc:
        raise ExpertRuntimeError("expert request could not be atomically claimed") from exc
    try:
        claimed_fact = _hash_stable_request_file(claimed)
    except BaseException as exc:
        _delete_claimed_request(claimed)
        raise ExpertClaimedRequestError(
            "claimed expert request failed final identity validation"
        ) from exc
    if claimed_fact != fact:
        _delete_claimed_request(claimed)
        raise ExpertClaimedRequestError("expert request changed before consumption")
    _delete_claimed_request(claimed)


def execute_expert_request_file(
    path: Path,
    *,
    request_root: Path,
    request_scope: str,
) -> dict[str, object]:
    """Load, validate, consume, and execute one host-contract request file."""

    resolved = _authorize_request_path(path, request_root, request_scope)
    payload, fact = _load_expert_request_with_fact(resolved)
    request = parse_expert_request(payload)
    _consume_request(resolved, fact)
    try:
        return _execute_parsed_request(request)
    except BaseException as exc:
        raise ExpertConsumedRequestError(
            "expert request execution failed after consumption"
        ) from exc


def safe_error_payload(exc: BaseException) -> dict[str, object]:
    """Return a bounded error without echoing private paths or request data."""

    cause = exc.__cause__ if isinstance(exc, ExpertConsumedRequestError) else exc
    if isinstance(exc, ExpertRequestCleanupError):
        code = "MB-EXPERT-0002"
        request_disposition = "cleanup_failed_possible_residue"
        recovery = "manual_request_cleanup_required"
    elif isinstance(exc, ExpertClaimedRequestError):
        code = "MB-EXPERT-0003"
        request_disposition = "consumed_without_execution"
        recovery = "rewrite_request_before_retry"
    elif isinstance(exc, ExpertConsumedRequestError) and isinstance(cause, ExpertPrivacyModeError):
        code = "MB-EXPERT-0004"
        request_disposition = "consumed_before_execution"
        recovery = "create_or_rebuild_local_private_project_then_rewrite_request"
    elif isinstance(exc, ExpertConsumedRequestError):
        if isinstance(cause, MibaoError):
            code = cause.code
        elif isinstance(cause, SearchValidationError):
            code = "MB-SEARCH-0001"
        else:
            code = "MB-EXPERT-0003"
        request_disposition = "consumed_before_execution"
        recovery = "rewrite_request_before_retry"
    elif isinstance(exc, MibaoError):
        code = exc.code
        request_disposition = "not_consumed"
        recovery = "correct_or_replace_request"
    elif isinstance(exc, SearchValidationError):
        code = "MB-SEARCH-0001"
        request_disposition = "not_consumed"
        recovery = "correct_or_replace_request"
    else:
        code = "MB-EXPERT-0001"
        request_disposition = "not_consumed"
        recovery = "correct_or_replace_request"
    return {
        "schemaVersion": "1.0",
        "ok": False,
        "status": "blocked",
        "code": code,
        "error": "The one-shot expert request failed a bounded safety or integrity gate.",
        "requestDisposition": request_disposition,
        "recovery": recovery,
        "mcpServiceInstalled": False,
        "externalDisclosureCreated": False,
    }
