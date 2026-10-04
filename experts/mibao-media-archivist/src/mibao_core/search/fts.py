"""SQLite FTS5 indexing for bounded, evidence-linked project documents.

This module deliberately accepts only already-derived text and opaque stable
references. It never reads files, invokes processes, talks to networks, or
promotes candidate annotations to verified facts.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final


class SearchValidationError(ValueError):
    """Raised when an index document or query violates the local contract."""


_KINDS: Final[frozenset[str]] = frozenset(
    {"asset", "segment", "evidence", "annotation", "representation"}
)
_STATES: Final[frozenset[str]] = frozenset({"candidate", "verified", "rejected", "unknown"})
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,511}$")
_QUERY_TOKEN = re.compile(r"^[\w\u3400-\u9fff]+$", re.UNICODE)
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_PATH_MARKERS = ("/", "\\")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _bounded_text(value: str, *, field: str, maximum: int, required: bool = True) -> str:
    if not isinstance(value, str):
        raise SearchValidationError(f"{field} must be text")
    value = unicodedata.normalize("NFC", value).strip()
    if required and not value:
        raise SearchValidationError(f"{field} must not be empty")
    if len(value) > maximum or _CONTROL.search(value):
        raise SearchValidationError(f"{field} exceeds the bounded text contract")
    return value


@dataclass(frozen=True, slots=True)
class SearchDocument:
    document_id: str
    project_id: str
    document_kind: str
    title: str
    body: str
    source_ref: str
    asset_id: str | None = None
    segment_id: str | None = None
    start_ms: int | None = None
    end_ms: int | None = None
    evidence_refs: tuple[str, ...] = ()
    state: str = "unknown"
    created_at: str | None = None
    updated_at: str | None = None

    def validated(self, *, timestamp: str) -> SearchDocument:
        for field, value in (("document_id", self.document_id), ("project_id", self.project_id)):
            if not isinstance(value, str) or not _ID.fullmatch(value):
                raise SearchValidationError(f"{field} is not a stable identifier")
        if self.document_kind not in _KINDS:
            raise SearchValidationError("document_kind is unsupported")
        if self.state not in _STATES:
            raise SearchValidationError("state is unsupported")
        title = _bounded_text(self.title, field="title", maximum=512)
        body = _bounded_text(self.body, field="body", maximum=20_000, required=False)
        source_ref = _bounded_text(self.source_ref, field="source_ref", maximum=512)
        if any(marker in source_ref for marker in _PATH_MARKERS) or ":" in source_ref:
            raise SearchValidationError("source_ref must be an opaque reference, not a path")
        for optional_field, optional_value in (
            ("asset_id", self.asset_id),
            ("segment_id", self.segment_id),
        ):
            if optional_value is not None and (
                not isinstance(optional_value, str) or not _ID.fullmatch(optional_value)
            ):
                raise SearchValidationError(f"{optional_field} is not a stable identifier")
        if self.start_ms is not None and (not isinstance(self.start_ms, int) or self.start_ms < 0):
            raise SearchValidationError("start_ms must be a non-negative integer")
        if self.end_ms is not None and (
            not isinstance(self.end_ms, int)
            or self.end_ms < 0
            or (self.start_ms is not None and self.end_ms <= self.start_ms)
        ):
            raise SearchValidationError("end_ms must be after start_ms")
        refs = tuple(self.evidence_refs)
        if len(refs) > 128 or any(
            not isinstance(ref, str) or not _ID.fullmatch(ref) for ref in refs
        ):
            raise SearchValidationError("evidence_refs must contain stable identifiers")
        return SearchDocument(
            document_id=self.document_id,
            project_id=self.project_id,
            document_kind=self.document_kind,
            title=title,
            body=body,
            source_ref=source_ref,
            asset_id=self.asset_id,
            segment_id=self.segment_id,
            start_ms=self.start_ms,
            end_ms=self.end_ms,
            evidence_refs=refs,
            state=self.state,
            created_at=self.created_at or timestamp,
            updated_at=self.updated_at or timestamp,
        )


@dataclass(frozen=True, slots=True)
class SearchResult:
    document_id: str
    project_id: str
    document_kind: str
    title: str
    source_ref: str
    start_ms: int | None
    end_ms: int | None
    evidence_refs: tuple[str, ...]
    state: str
    rank: float
    snippet: str


def upsert_search_documents(
    connection: sqlite3.Connection,
    documents: Iterable[SearchDocument],
    *,
    timestamp: str | None = None,
) -> int:
    """Atomically upsert bounded documents; all validation occurs before writes."""

    items = tuple(documents)
    if not items:
        return 0
    stamp = timestamp or _now()
    validated = tuple(item.validated(timestamp=stamp) for item in items)
    project_ids = {item.project_id for item in validated}
    if len(project_ids) != 1:
        raise SearchValidationError("one transaction cannot mix projects")
    connection.execute("BEGIN IMMEDIATE")
    try:
        for item in validated:
            connection.execute(
                "INSERT INTO search_documents("
                "document_id, project_id, asset_id, segment_id, document_kind, title, body, "
                "source_ref, start_ms, end_ms, evidence_refs_json, state, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(document_id) DO UPDATE SET project_id=excluded.project_id, "
                "asset_id=excluded.asset_id, segment_id=excluded.segment_id, "
                "document_kind=excluded.document_kind, title=excluded.title, body=excluded.body, "
                "source_ref=excluded.source_ref, start_ms=excluded.start_ms, "
                "end_ms=excluded.end_ms, "
                "evidence_refs_json=excluded.evidence_refs_json, state=excluded.state, "
                "updated_at=excluded.updated_at",
                (
                    item.document_id,
                    item.project_id,
                    item.asset_id,
                    item.segment_id,
                    item.document_kind,
                    item.title,
                    item.body,
                    item.source_ref,
                    item.start_ms,
                    item.end_ms,
                    json.dumps(item.evidence_refs, ensure_ascii=False, separators=(",", ":")),
                    item.state,
                    item.created_at,
                    item.updated_at,
                ),
            )
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    return len(validated)


def _match_query(query: str) -> str:
    value = _bounded_text(query, field="query", maximum=256)
    if any(marker in value for marker in ('"', "'", "*", ":", "(", ")", "-", "/", "\\")):
        raise SearchValidationError("query contains unsupported FTS syntax")
    if value.startswith(".") or value.endswith(".") or ".." in value:
        raise SearchValidationError("query contains unsupported FTS syntax")
    tokens = value.replace(".", " ").split()
    if not tokens or any(not _QUERY_TOKEN.fullmatch(token) for token in tokens):
        raise SearchValidationError("query contains unsupported FTS syntax")
    if any(token.upper() in {"AND", "OR", "NOT", "NEAR"} for token in tokens):
        raise SearchValidationError("FTS operators are not accepted")
    return " AND ".join(f'"{token}"' for token in tokens)


def search_documents(
    connection: sqlite3.Connection,
    project_id: str,
    query: str,
    *,
    limit: int = 20,
    document_kind: str | None = None,
    document_id_prefix: str | None = None,
) -> tuple[SearchResult, ...]:
    """Read-only, project-scoped FTS query with optional exact namespace filters."""

    if not isinstance(project_id, str) or not _ID.fullmatch(project_id):
        raise SearchValidationError("project_id is not a stable identifier")
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise SearchValidationError("limit must be between 1 and 100")
    if document_kind is not None and document_kind not in _KINDS:
        raise SearchValidationError("document_kind filter is unsupported")
    if document_id_prefix is not None and (
        not isinstance(document_id_prefix, str) or not _ID.fullmatch(document_id_prefix)
    ):
        raise SearchValidationError("document_id_prefix filter is invalid")
    match = _match_query(query)
    rows = connection.execute(
        "SELECT d.document_id, d.project_id, d.document_kind, d.title, d.source_ref, "
        "d.start_ms, d.end_ms, d.evidence_refs_json, d.state, bm25(search_fts) AS rank, "
        "snippet(search_fts, 2, '[', ']', '…', 12) AS snippet "
        "FROM search_fts JOIN search_documents AS d ON d.rowid=search_fts.rowid "
        "WHERE search_fts MATCH ? AND d.project_id=? "
        "AND (? IS NULL OR d.document_kind=?) "
        "AND (? IS NULL OR substr(d.document_id, 1, ?)=?) "
        "ORDER BY rank, d.document_id LIMIT ?",
        (
            match,
            project_id,
            document_kind,
            document_kind,
            document_id_prefix,
            len(document_id_prefix or ""),
            document_id_prefix,
            limit,
        ),
    ).fetchall()
    return tuple(
        SearchResult(
            document_id=str(row[0]),
            project_id=str(row[1]),
            document_kind=str(row[2]),
            title=str(row[3]),
            source_ref=str(row[4]),
            start_ms=row[5],
            end_ms=row[6],
            evidence_refs=tuple(json.loads(row[7])),
            state=str(row[8]),
            rank=float(row[9]),
            snippet=str(row[10]),
        )
        for row in rows
    )
