"""Versioned SQLite project migrations and completed-state audit."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from typing import Final

from mibao_core.errors import MibaoError

SCHEMA_VERSION: Final = 3

_SCHEMA_MIGRATIONS_SQL: Final = """
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version > 0),
    migration_id TEXT NOT NULL UNIQUE,
    checksum TEXT NOT NULL CHECK (length(checksum) = 64),
    applied_at TEXT NOT NULL
) STRICT
""".strip()

_PROJECT_METADATA_SQL: Final = """
CREATE TABLE project_metadata (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    project_id TEXT NOT NULL UNIQUE,
    schema_version INTEGER NOT NULL CHECK (schema_version > 0),
    privacy_mode TEXT NOT NULL
        CHECK (privacy_mode IN ('local-private', 'hybrid', 'deep-understanding')),
    state TEXT NOT NULL CHECK (state IN ('active', 'archived')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
) STRICT
""".strip()

_V1_TABLES: Final[dict[str, str]] = {
    "schema_migrations": _SCHEMA_MIGRATIONS_SQL,
    "project_metadata": _PROJECT_METADATA_SQL,
}

_V2_TABLES: Final[dict[str, str]] = {
    "source_roots": """
CREATE TABLE source_roots (
    source_root_id TEXT PRIMARY KEY CHECK (length(source_root_id) > 0),
    project_id TEXT NOT NULL,
    canonical_path TEXT NOT NULL CHECK (length(canonical_path) > 0),
    path_identity_json TEXT NOT NULL CHECK (json_valid(path_identity_json)),
    state TEXT NOT NULL CHECK (state IN ('active', 'offline', 'removed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (project_id, source_root_id),
    UNIQUE (project_id, canonical_path),
    FOREIGN KEY (project_id) REFERENCES project_metadata(project_id) ON DELETE CASCADE
) STRICT
""".strip(),
    "assets": """
CREATE TABLE assets (
    asset_id TEXT PRIMARY KEY CHECK (length(asset_id) > 0),
    project_id TEXT NOT NULL,
    sha256 TEXT NOT NULL
        CHECK (length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9a-f]*'),
    media_kind TEXT NOT NULL
        CHECK (media_kind IN ('video', 'audio', 'image', 'document', 'other')),
    byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
    capture_time_ms INTEGER CHECK (capture_time_ms IS NULL OR capture_time_ms >= 0),
    technical_json TEXT NOT NULL CHECK (json_valid(technical_json)),
    state TEXT NOT NULL CHECK (state IN ('active', 'missing', 'quarantined')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (project_id, asset_id),
    UNIQUE (project_id, sha256),
    FOREIGN KEY (project_id) REFERENCES project_metadata(project_id) ON DELETE CASCADE
) STRICT
""".strip(),
    "file_instances": """
CREATE TABLE file_instances (
    file_instance_id TEXT PRIMARY KEY CHECK (length(file_instance_id) > 0),
    project_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    source_root_id TEXT NOT NULL,
    relative_path TEXT NOT NULL CHECK (length(relative_path) > 0),
    file_size INTEGER NOT NULL CHECK (file_size >= 0),
    modified_time_ms INTEGER NOT NULL CHECK (modified_time_ms >= 0),
    identity_json TEXT NOT NULL CHECK (json_valid(identity_json)),
    state TEXT NOT NULL CHECK (state IN ('present', 'missing', 'changed')),
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    UNIQUE (project_id, source_root_id, relative_path),
    FOREIGN KEY (project_id, asset_id)
        REFERENCES assets(project_id, asset_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, source_root_id)
        REFERENCES source_roots(project_id, source_root_id) ON DELETE RESTRICT
) STRICT
""".strip(),
    "representations": """
CREATE TABLE representations (
    representation_id TEXT PRIMARY KEY CHECK (length(representation_id) > 0),
    project_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    representation_kind TEXT NOT NULL CHECK (
        representation_kind IN (
            'original', 'universal', 'proxy', 'thumbnail', 'contact_sheet', 'subtitle'
        )
    ),
    relative_path TEXT NOT NULL CHECK (length(relative_path) > 0),
    profile_id TEXT,
    content_sha256 TEXT CHECK (
        content_sha256 IS NULL OR (
            length(content_sha256) = 64 AND content_sha256 NOT GLOB '*[^0-9a-f]*'
        )
    ),
    media_json TEXT NOT NULL CHECK (json_valid(media_json)),
    state TEXT NOT NULL CHECK (state IN ('planned', 'ready', 'failed', 'stale')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (project_id, asset_id, representation_id),
    UNIQUE (project_id, asset_id, representation_kind, relative_path),
    FOREIGN KEY (project_id, asset_id)
        REFERENCES assets(project_id, asset_id) ON DELETE CASCADE
) STRICT
""".strip(),
    "segments": """
CREATE TABLE segments (
    segment_id TEXT PRIMARY KEY CHECK (length(segment_id) > 0),
    project_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    representation_id TEXT,
    segment_kind TEXT NOT NULL
        CHECK (segment_kind IN ('shot', 'chapter', 'transcript', 'clip', 'event')),
    start_ms INTEGER NOT NULL CHECK (start_ms >= 0),
    end_ms INTEGER NOT NULL CHECK (end_ms > start_ms),
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
    created_at TEXT NOT NULL,
    UNIQUE (project_id, asset_id, segment_id),
    FOREIGN KEY (project_id, asset_id)
        REFERENCES assets(project_id, asset_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, asset_id, representation_id)
        REFERENCES representations(project_id, asset_id, representation_id) ON DELETE CASCADE
) STRICT
""".strip(),
    "evidence": """
CREATE TABLE evidence (
    evidence_id TEXT PRIMARY KEY CHECK (length(evidence_id) > 0),
    project_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    segment_id TEXT,
    evidence_type TEXT NOT NULL CHECK (
        evidence_type IN (
            'frame', 'timecode', 'text', 'metadata', 'human_confirmation', 'ocr', 'asr',
            'audio'
        )
    ),
    locator_json TEXT NOT NULL CHECK (json_valid(locator_json)),
    content_json TEXT NOT NULL CHECK (json_valid(content_json)),
    producer_kind TEXT NOT NULL CHECK (producer_kind IN ('tool', 'model', 'human')),
    producer_name TEXT NOT NULL CHECK (length(producer_name) > 0),
    producer_version TEXT NOT NULL CHECK (length(producer_version) > 0),
    prompt_version TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (project_id, asset_id, evidence_id),
    FOREIGN KEY (project_id, asset_id)
        REFERENCES assets(project_id, asset_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, asset_id, segment_id)
        REFERENCES segments(project_id, asset_id, segment_id) ON DELETE CASCADE
) STRICT
""".strip(),
    "annotations": """
CREATE TABLE annotations (
    annotation_id TEXT PRIMARY KEY CHECK (length(annotation_id) > 0),
    project_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    segment_id TEXT,
    annotation_type TEXT NOT NULL
        CHECK (annotation_type IN ('event', 'person', 'place', 'ocr', 'asr', 'scene', 'technical')),
    value_json TEXT NOT NULL CHECK (json_valid(value_json)),
    evidence_level TEXT NOT NULL CHECK (evidence_level IN ('A', 'B', 'C', 'D')),
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    status TEXT NOT NULL
        CHECK (status IN ('verified', 'candidate', 'needs_review', 'rejected')),
    producer_kind TEXT NOT NULL CHECK (producer_kind IN ('tool', 'model', 'human')),
    producer_name TEXT NOT NULL CHECK (length(producer_name) > 0),
    producer_version TEXT,
    prompt_version TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (project_id, asset_id, annotation_id),
    CHECK (
        evidence_level NOT IN ('C', 'D') OR (
            producer_version IS NOT NULL AND length(producer_version) > 0
            AND prompt_version IS NOT NULL AND length(prompt_version) > 0
        )
    ),
    FOREIGN KEY (project_id, asset_id)
        REFERENCES assets(project_id, asset_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, asset_id, segment_id)
        REFERENCES segments(project_id, asset_id, segment_id) ON DELETE CASCADE
) STRICT
""".strip(),
    "annotation_evidence": """
CREATE TABLE annotation_evidence (
    annotation_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (annotation_id, evidence_id),
    FOREIGN KEY (project_id, asset_id, annotation_id)
        REFERENCES annotations(project_id, asset_id, annotation_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, asset_id, evidence_id)
        REFERENCES evidence(project_id, asset_id, evidence_id) ON DELETE CASCADE
) STRICT
""".strip(),
    "duplicate_relations": """
CREATE TABLE duplicate_relations (
    project_id TEXT NOT NULL,
    left_asset_id TEXT NOT NULL,
    right_asset_id TEXT NOT NULL,
    relation_kind TEXT NOT NULL CHECK (relation_kind IN ('exact', 'near', 'derivative')),
    score REAL NOT NULL CHECK (score >= 0.0 AND score <= 1.0),
    evidence_json TEXT NOT NULL CHECK (json_valid(evidence_json)),
    created_at TEXT NOT NULL,
    PRIMARY KEY (project_id, left_asset_id, right_asset_id, relation_kind),
    CHECK (left_asset_id < right_asset_id),
    FOREIGN KEY (project_id, left_asset_id)
        REFERENCES assets(project_id, asset_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, right_asset_id)
        REFERENCES assets(project_id, asset_id) ON DELETE CASCADE
) STRICT
""".strip(),
    "jobs": """
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY CHECK (length(job_id) > 0),
    project_id TEXT NOT NULL,
    goal TEXT NOT NULL CHECK (length(goal) > 0),
    spec_json TEXT NOT NULL CHECK (json_valid(spec_json)),
    status TEXT NOT NULL CHECK (
        status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled', 'interrupted')
    ),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (project_id, job_id),
    FOREIGN KEY (project_id) REFERENCES project_metadata(project_id) ON DELETE CASCADE
) STRICT
""".strip(),
    "operations": """
CREATE TABLE operations (
    operation_id TEXT PRIMARY KEY CHECK (length(operation_id) > 0),
    project_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    asset_id TEXT,
    operation_type TEXT NOT NULL CHECK (length(operation_type) > 0),
    request_json TEXT NOT NULL CHECK (json_valid(request_json)),
    result_json TEXT CHECK (result_json IS NULL OR json_valid(result_json)),
    status TEXT NOT NULL CHECK (
        status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled', 'interrupted')
    ),
    duration_ms INTEGER CHECK (duration_ms IS NULL OR duration_ms >= 0),
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (project_id, operation_id),
    FOREIGN KEY (project_id, job_id)
        REFERENCES jobs(project_id, job_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, asset_id)
        REFERENCES assets(project_id, asset_id) ON DELETE RESTRICT
) STRICT
""".strip(),
    "qa_results": """
CREATE TABLE qa_results (
    qa_result_id TEXT PRIMARY KEY CHECK (length(qa_result_id) > 0),
    project_id TEXT NOT NULL,
    operation_id TEXT NOT NULL,
    asset_id TEXT,
    check_kind TEXT NOT NULL CHECK (check_kind IN ('technical', 'visual', 'evidence', 'security')),
    status TEXT NOT NULL CHECK (status IN ('pass', 'fail', 'warning', 'not_run')),
    metrics_json TEXT NOT NULL CHECK (json_valid(metrics_json)),
    evidence_json TEXT NOT NULL CHECK (json_valid(evidence_json)),
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id, operation_id)
        REFERENCES operations(project_id, operation_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, asset_id)
        REFERENCES assets(project_id, asset_id) ON DELETE RESTRICT
) STRICT
""".strip(),
    "external_disclosures": """
CREATE TABLE external_disclosures (
    disclosure_id TEXT PRIMARY KEY CHECK (length(disclosure_id) > 0),
    project_id TEXT NOT NULL,
    job_id TEXT,
    asset_id TEXT,
    provider TEXT NOT NULL CHECK (length(provider) > 0),
    purpose TEXT NOT NULL CHECK (length(purpose) > 0),
    privacy_mode TEXT NOT NULL
        CHECK (privacy_mode IN ('local-private', 'hybrid', 'deep-understanding')),
    payload_manifest_json TEXT NOT NULL CHECK (json_valid(payload_manifest_json)),
    consent_ref TEXT,
    status TEXT NOT NULL CHECK (status IN ('planned', 'sent', 'blocked', 'cancelled')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES project_metadata(project_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, job_id)
        REFERENCES jobs(project_id, job_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, asset_id)
        REFERENCES assets(project_id, asset_id) ON DELETE RESTRICT
) STRICT
""".strip(),
}

_V2_INDEXES: Final[dict[str, str]] = {
    "idx_source_roots_project_state": (
        "CREATE INDEX idx_source_roots_project_state ON source_roots(project_id, state)"
    ),
    "idx_assets_project_kind_state": (
        "CREATE INDEX idx_assets_project_kind_state ON assets(project_id, media_kind, state)"
    ),
    "idx_file_instances_asset_state": (
        "CREATE INDEX idx_file_instances_asset_state ON file_instances(project_id, asset_id, state)"
    ),
    "idx_representations_asset_kind_state": (
        "CREATE INDEX idx_representations_asset_kind_state "
        "ON representations(project_id, asset_id, representation_kind, state)"
    ),
    "idx_segments_asset_time": (
        "CREATE INDEX idx_segments_asset_time ON segments(project_id, asset_id, start_ms, end_ms)"
    ),
    "idx_evidence_asset_segment": (
        "CREATE INDEX idx_evidence_asset_segment ON evidence(project_id, asset_id, segment_id)"
    ),
    "idx_annotations_asset_status_level": (
        "CREATE INDEX idx_annotations_asset_status_level "
        "ON annotations(project_id, asset_id, status, evidence_level)"
    ),
    "idx_annotation_evidence_evidence": (
        "CREATE INDEX idx_annotation_evidence_evidence "
        "ON annotation_evidence(evidence_id, annotation_id)"
    ),
    "idx_duplicate_relations_right": (
        "CREATE INDEX idx_duplicate_relations_right "
        "ON duplicate_relations(project_id, right_asset_id, relation_kind)"
    ),
    "idx_jobs_project_status": (
        "CREATE INDEX idx_jobs_project_status ON jobs(project_id, status, updated_at)"
    ),
    "idx_operations_job_status": (
        "CREATE INDEX idx_operations_job_status ON operations(project_id, job_id, status)"
    ),
    "idx_qa_results_operation_status": (
        "CREATE INDEX idx_qa_results_operation_status "
        "ON qa_results(project_id, operation_id, status)"
    ),
    "idx_external_disclosures_project_status": (
        "CREATE INDEX idx_external_disclosures_project_status "
        "ON external_disclosures(project_id, status, created_at)"
    ),
}

_V2_TRIGGERS: Final[dict[str, str]] = {
    "trg_annotations_verified_insert_guard": """
CREATE TRIGGER trg_annotations_verified_insert_guard
BEFORE INSERT ON annotations
WHEN NEW.status = 'verified' AND NEW.evidence_level IN ('C', 'D')
BEGIN
    SELECT CASE
        WHEN NEW.evidence_level = 'D' AND NEW.producer_kind <> 'human'
        THEN RAISE(ABORT, 'MB-DATA-0007 D verified annotation requires human producer')
    END;
    SELECT RAISE(ABORT, 'MB-DATA-0006 verified C/D annotation requires linked evidence');
END
""".strip(),
    "trg_annotations_verified_update_guard": """
CREATE TRIGGER trg_annotations_verified_update_guard
BEFORE UPDATE ON annotations
WHEN NEW.status = 'verified' AND NEW.evidence_level IN ('C', 'D')
BEGIN
    SELECT CASE
        WHEN NEW.evidence_level = 'D' AND NEW.producer_kind <> 'human'
        THEN RAISE(ABORT, 'MB-DATA-0007 D verified annotation requires human producer')
    END;
    SELECT CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM annotation_evidence
            WHERE annotation_id = NEW.annotation_id
        )
        THEN RAISE(ABORT, 'MB-DATA-0006 verified C/D annotation requires linked evidence')
    END;
END
""".strip(),
    "trg_annotation_evidence_delete_guard": """
CREATE TRIGGER trg_annotation_evidence_delete_guard
BEFORE DELETE ON annotation_evidence
WHEN EXISTS (
    SELECT 1 FROM annotations
    WHERE annotation_id = OLD.annotation_id
      AND status = 'verified'
      AND evidence_level IN ('C', 'D')
)
AND (
    SELECT count(*) FROM annotation_evidence
    WHERE annotation_id = OLD.annotation_id
) <= 1
BEGIN
    SELECT RAISE(ABORT, 'MB-DATA-0008 cannot remove last evidence from verified C/D annotation');
END
""".strip(),
    "trg_annotation_evidence_update_guard": """
CREATE TRIGGER trg_annotation_evidence_update_guard
BEFORE UPDATE ON annotation_evidence
BEGIN
    SELECT RAISE(ABORT, 'MB-DATA-0009 annotation evidence links are immutable');
END
""".strip(),
    "trg_evidence_delete_guard": """
CREATE TRIGGER trg_evidence_delete_guard
BEFORE DELETE ON evidence
WHEN EXISTS (
    SELECT 1
    FROM annotation_evidence AS link
    JOIN annotations AS annotation
      ON annotation.annotation_id = link.annotation_id
    WHERE link.evidence_id = OLD.evidence_id
      AND annotation.status = 'verified'
      AND annotation.evidence_level IN ('C', 'D')
      AND (
          SELECT count(*) FROM annotation_evidence AS remaining
          WHERE remaining.annotation_id = annotation.annotation_id
      ) <= 1
)
BEGIN
    SELECT RAISE(ABORT, 'MB-DATA-0008 cannot remove last evidence from verified C/D annotation');
END
""".strip(),
}

_V3_TABLES: Final[dict[str, str]] = {
    "search_documents": """
CREATE TABLE search_documents (
    document_id TEXT PRIMARY KEY CHECK (length(document_id) > 0),
    project_id TEXT NOT NULL,
    asset_id TEXT,
    segment_id TEXT,
    document_kind TEXT NOT NULL CHECK (
        document_kind IN ('asset', 'segment', 'evidence', 'annotation', 'representation')
    ),
    title TEXT NOT NULL CHECK (length(title) <= 512),
    body TEXT NOT NULL CHECK (length(body) <= 20000),
    source_ref TEXT NOT NULL CHECK (length(source_ref) > 0 AND length(source_ref) <= 512),
    start_ms INTEGER CHECK (start_ms IS NULL OR start_ms >= 0),
    end_ms INTEGER CHECK (end_ms IS NULL OR end_ms > COALESCE(start_ms, -1)),
    evidence_refs_json TEXT NOT NULL CHECK (json_valid(evidence_refs_json)),
    state TEXT NOT NULL CHECK (state IN ('candidate', 'verified', 'rejected', 'unknown')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (project_id, document_id),
    FOREIGN KEY (project_id) REFERENCES project_metadata(project_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, asset_id)
        REFERENCES assets(project_id, asset_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id, asset_id, segment_id)
        REFERENCES segments(project_id, asset_id, segment_id) ON DELETE CASCADE
) STRICT
""".strip(),
    "search_fts": (
        "CREATE VIRTUAL TABLE search_fts USING fts5("
        "document_id UNINDEXED, project_id UNINDEXED, title, body)"
    ),
}

_V3_INDEXES: Final[dict[str, str]] = {
    "idx_search_documents_project_kind": (
        "CREATE INDEX idx_search_documents_project_kind "
        "ON search_documents(project_id, document_kind, state)"
    ),
}

_V3_TRIGGERS: Final[dict[str, str]] = {
    "trg_search_documents_insert": """
CREATE TRIGGER trg_search_documents_insert
AFTER INSERT ON search_documents
BEGIN
    INSERT INTO search_fts(rowid, document_id, project_id, title, body)
    VALUES (NEW.rowid, NEW.document_id, NEW.project_id, NEW.title, NEW.body);
END
""".strip(),
    "trg_search_documents_update": """
CREATE TRIGGER trg_search_documents_update
AFTER UPDATE ON search_documents
BEGIN
    DELETE FROM search_fts WHERE rowid = OLD.rowid;
    INSERT INTO search_fts(rowid, document_id, project_id, title, body)
    VALUES (NEW.rowid, NEW.document_id, NEW.project_id, NEW.title, NEW.body);
END
""".strip(),
    "trg_search_documents_delete": """
CREATE TRIGGER trg_search_documents_delete
AFTER DELETE ON search_documents
BEGIN
    DELETE FROM search_fts WHERE rowid = OLD.rowid;
END
""".strip(),
}

EXPECTED_TABLE_SQL: Final[dict[str, str]] = {**_V1_TABLES, **_V2_TABLES, **_V3_TABLES}
EXPECTED_INDEX_SQL: Final[dict[str, str]] = {**_V2_INDEXES, **_V3_INDEXES}
EXPECTED_TRIGGER_SQL: Final[dict[str, str]] = {**_V2_TRIGGERS, **_V3_TRIGGERS}
_EXPECTED_V2_TABLE_SQL: Final[dict[str, str]] = {**_V1_TABLES, **_V2_TABLES}
_EXPECTED_V2_INDEX_SQL: Final[dict[str, str]] = dict(_V2_INDEXES)
_EXPECTED_V2_TRIGGER_SQL: Final[dict[str, str]] = dict(_V2_TRIGGERS)


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    migration_id: str
    statements: tuple[str, ...]

    @property
    def checksum(self) -> str:
        content = "\n-- statement --\n".join(self.statements).encode("utf-8")
        return hashlib.sha256(content).hexdigest()


MIGRATIONS: Final[tuple[Migration, ...]] = (
    Migration(1, "001-project-foundation", tuple(_V1_TABLES.values())),
    Migration(
        2,
        "002-asset-evidence-model",
        (
            *tuple(_V2_TABLES.values()),
            *tuple(_V2_INDEXES.values()),
            *tuple(_V2_TRIGGERS.values()),
        ),
    ),
    Migration(
        3,
        "003-search-fts5",
        (
            *tuple(_V3_TABLES.values()),
            *tuple(_V3_INDEXES.values()),
            *tuple(_V3_TRIGGERS.values()),
        ),
    ),
)


def _normalize_sql(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).replace(" (", "(")


def _selected_migrations(
    migrations: tuple[Migration, ...], target_version: int
) -> tuple[Migration, ...]:
    selected = tuple(item for item in migrations if item.version <= target_version)
    versions = tuple(item.version for item in selected)
    if versions != tuple(range(1, target_version + 1)):
        raise MibaoError("MB-PROJ-0005", "SQLite migrations are not contiguous")
    identifiers = tuple(item.migration_id for item in selected)
    if len(set(identifiers)) != len(identifiers):
        raise MibaoError("MB-PROJ-0005", "SQLite migration identifiers are not unique")
    return selected


def _expected_objects(version: int) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    if version == 1:
        return dict(_V1_TABLES), {}, {}
    if version == 2:
        return (
            dict(_EXPECTED_V2_TABLE_SQL),
            dict(_EXPECTED_V2_INDEX_SQL),
            dict(_EXPECTED_V2_TRIGGER_SQL),
        )
    if version == 3:
        return dict(EXPECTED_TABLE_SQL), dict(EXPECTED_INDEX_SQL), dict(EXPECTED_TRIGGER_SQL)
    raise MibaoError("MB-PROJ-0005", f"Unsupported SQLite schema version: {version}")


def _execute_migration(connection: sqlite3.Connection, migration: Migration) -> None:
    for statement in migration.statements:
        connection.execute(statement)


def apply_initial_schema(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    privacy_mode: str,
    timestamp: str,
    target_version: int = SCHEMA_VERSION,
) -> None:
    """Create a fresh database through the target version in one transaction."""

    selected = _selected_migrations(MIGRATIONS, target_version)
    connection.execute("BEGIN IMMEDIATE")
    try:
        foundation = selected[0]
        _execute_migration(connection, foundation)
        connection.execute(
            "INSERT INTO schema_migrations(version, migration_id, checksum, applied_at) "
            "VALUES (?, ?, ?, ?)",
            (foundation.version, foundation.migration_id, foundation.checksum, timestamp),
        )
        connection.execute(
            "INSERT INTO project_metadata("
            "singleton_id, project_id, schema_version, privacy_mode, state, created_at, updated_at"
            ") VALUES (1, ?, 1, ?, 'active', ?, ?)",
            (project_id, privacy_mode, timestamp, timestamp),
        )
        connection.execute("PRAGMA user_version = 1")
        for migration in selected[1:]:
            _execute_migration(connection, migration)
            connection.execute(
                "INSERT INTO schema_migrations(version, migration_id, checksum, applied_at) "
                "VALUES (?, ?, ?, ?)",
                (migration.version, migration.migration_id, migration.checksum, timestamp),
            )
            connection.execute(
                "UPDATE project_metadata SET schema_version=? WHERE singleton_id=1",
                (migration.version,),
            )
            connection.execute(f"PRAGMA user_version = {migration.version}")
        audit_schema(
            connection,
            expected_project_id=project_id,
            expected_privacy_mode=privacy_mode,
            expected_version=target_version,
            migrations=selected,
        )
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


def apply_pending_migrations(
    connection: sqlite3.Connection,
    *,
    project_id: str,
    privacy_mode: str,
    timestamp: str,
    target_version: int = SCHEMA_VERSION,
    migrations: tuple[Migration, ...] = MIGRATIONS,
) -> bool:
    """Audit an existing database and apply all pending migrations transactionally."""

    selected = _selected_migrations(migrations, target_version)
    row = connection.execute("PRAGMA user_version").fetchone()
    current_version = int(row[0]) if row is not None else 0
    if current_version < 1 or current_version > target_version:
        raise MibaoError("MB-PROJ-0005", "SQLite user_version cannot be migrated")
    audit_schema(
        connection,
        expected_project_id=project_id,
        expected_privacy_mode=privacy_mode,
        expected_version=current_version,
        migrations=selected,
    )
    if current_version == target_version:
        return False

    pending = tuple(item for item in selected if item.version > current_version)
    connection.execute("BEGIN IMMEDIATE")
    try:
        for migration in pending:
            _execute_migration(connection, migration)
            connection.execute(
                "INSERT INTO schema_migrations(version, migration_id, checksum, applied_at) "
                "VALUES (?, ?, ?, ?)",
                (migration.version, migration.migration_id, migration.checksum, timestamp),
            )
            connection.execute(
                "UPDATE project_metadata SET schema_version=? WHERE singleton_id=1",
                (migration.version,),
            )
            connection.execute(f"PRAGMA user_version = {migration.version}")
        audit_schema(
            connection,
            expected_project_id=project_id,
            expected_privacy_mode=privacy_mode,
            expected_version=target_version,
            migrations=selected,
        )
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    return True


def audit_schema(
    connection: sqlite3.Connection,
    *,
    expected_project_id: str,
    expected_privacy_mode: str,
    expected_version: int = SCHEMA_VERSION,
    migrations: tuple[Migration, ...] = MIGRATIONS,
) -> None:
    """Compare the complete durable schema, receipts, metadata, and foreign keys."""

    foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()
    if foreign_keys_enabled != (1,):
        raise MibaoError("MB-PROJ-0005", "SQLite foreign-key enforcement is disabled")
    expected_tables, expected_indexes, expected_triggers = _expected_objects(expected_version)
    selected = _selected_migrations(migrations, expected_version)
    user_version = connection.execute("PRAGMA user_version").fetchone()
    if user_version is None or user_version[0] != expected_version:
        raise MibaoError("MB-PROJ-0005", "SQLite user_version does not match project schema")

    observed_tables = {
        str(name): str(sql)
        for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    }
    observed_indexes = {
        str(name): str(sql)
        for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master "
            "WHERE type='index' AND sql IS NOT NULL ORDER BY name"
        )
    }
    observed_triggers = {
        str(name): str(sql)
        for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='trigger' ORDER BY name"
        )
    }
    # FTS5 owns implementation tables whose exact SQL is SQLite-version-specific.
    # Keep the durable contract strict for the virtual table itself while requiring
    # the complete known shadow-table set and rejecting any unexpected FTS objects.
    if expected_version >= 3:
        fts_shadows = {
            "search_fts_config",
            "search_fts_content",
            "search_fts_data",
            "search_fts_docsize",
            "search_fts_idx",
        }
        observed_shadow_names = {name for name in observed_tables if name.startswith("search_fts_")}
        if observed_shadow_names != fts_shadows:
            raise MibaoError("MB-PROJ-0005", "SQLite FTS5 shadow-table set does not match schema")
        observed_tables = {
            name: sql for name, sql in observed_tables.items() if name not in fts_shadows
        }
    for kind, observed, expected in (
        ("table", observed_tables, expected_tables),
        ("index", observed_indexes, expected_indexes),
        ("trigger", observed_triggers, expected_triggers),
    ):
        if set(observed) != set(expected):
            raise MibaoError("MB-PROJ-0005", f"SQLite {kind} set does not match schema")
        for name, expected_sql in expected.items():
            if _normalize_sql(observed[name]) != _normalize_sql(expected_sql):
                raise MibaoError("MB-PROJ-0005", f"SQLite {kind} definition drifted: {name}")

    receipts = connection.execute(
        "SELECT version, migration_id, checksum FROM schema_migrations ORDER BY version"
    ).fetchall()
    expected_receipts = [
        (migration.version, migration.migration_id, migration.checksum) for migration in selected
    ]
    if receipts != expected_receipts:
        raise MibaoError("MB-PROJ-0005", "SQLite migration receipts or checksums drifted")

    metadata = connection.execute(
        "SELECT project_id, schema_version, privacy_mode, state "
        "FROM project_metadata WHERE singleton_id=1"
    ).fetchone()
    expected_metadata = (
        expected_project_id,
        expected_version,
        expected_privacy_mode,
        "active",
    )
    if metadata != expected_metadata:
        raise MibaoError("MB-PROJ-0004", "Project manifest and SQLite metadata do not match")
    foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_errors:
        raise MibaoError("MB-PROJ-0005", "SQLite foreign-key state is inconsistent")
