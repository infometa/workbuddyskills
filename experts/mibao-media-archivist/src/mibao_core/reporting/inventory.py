"""Render one audited SQLite snapshot into an immutable inventory generation."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import shutil
import sqlite3
import unicodedata
import uuid
from collections.abc import Callable, Iterator
from contextlib import ExitStack, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, BinaryIO, ClassVar, Final

from mibao_core.errors import MibaoError
from mibao_core.filesystem.paths import PathPolicy, authorize_existing_path
from mibao_core.filesystem.scanner import compute_scan_completeness_snapshot
from mibao_core.hashing import HashAssuranceToken
from mibao_core.hashing.pipeline import (
    compute_hash_assurance_snapshot,
    consume_issued_hash_assurance_token,
)
from mibao_core.project import ProjectLock, open_project
from mibao_core.project.migrations import audit_schema

_REPORT_SCHEMA_VERSION: Final = "2.0"
_REPORT_POLICY_VERSION: Final = "mibao-inventory-report-policy-v2"
_GENERATOR_VERSION: Final = "mibao-inventory-report-v2"
_REPORT_ROOT = Path("reports") / "inventory"
_HTML_NAME: Final = "index.html"
_ASSET_CSV_NAME: Final = "assets.csv"
_FILE_CSV_NAME: Final = "files.csv"
_FORMAT_CSV_NAME: Final = "formats.csv"
_DUPLICATE_CSV_NAME: Final = "duplicates.csv"
_ANOMALY_CSV_NAME: Final = "anomalies.csv"
_JSONL_NAME: Final = "inventory.jsonl"
_MANIFEST_NAME: Final = "manifest.json"
_STAGE_SENTINEL: Final = ".mibao-owned-report-stage.json"
_MAX_JSONL_PHYSICAL_LINE_BYTES: Final = 1024 * 1024
_CSP_VALUE: Final = (
    "default-src 'none'; object-src 'none'; base-uri 'none'; "
    "form-action 'none'; style-src 'unsafe-inline'"
)
_REPORT_CSS: Final = (
    "body{font-family:system-ui,sans-serif;margin:2rem;color:#172033}"
    "table{border-collapse:collapse;width:100%;margin:1rem 0}"
    "th,td{border:1px solid #ccd3df;padding:.4rem;text-align:left;vertical-align:top}"
    "th{background:#eef2f8}.muted{color:#5b6474}.warn{color:#9b3a00}"
    "code{white-space:pre-wrap;overflow-wrap:anywhere}"
)
_CANNOT_PROVE: Final = (
    "filesystem state after the assurance token's final revalidation",
    "real SMB, USB, or offline-source behavior",
    "active WorkBuddy invocation, submission, or listing",
)
_TestHook = Callable[[str], None]
_RECORD_DATA_KEYS: Final[dict[str, frozenset[str]]] = {
    "report_header": frozenset({"generator_version", "duplicate_assurance"}),
    "asset": frozenset(
        {
            "asset_id",
            "sha256",
            "media_kind",
            "byte_size",
            "capture_time_ms",
            "state",
            "created_at",
            "updated_at",
            "format_id",
            "format_mime",
            "format_media_kind",
            "format_assurance",
            "file_instance_count",
            "present_instance_count",
            "missing_instance_count",
            "changed_instance_count",
            "anomaly_codes",
        }
    ),
    "file_instance": frozenset(
        {
            "operation_id",
            "operation_status",
            "file_instance_id",
            "asset_id",
            "source_root_id",
            "relative_path",
            "file_size",
            "modified_time_ms",
            "file_state",
            "asset_sha256",
            "asset_media_kind",
            "asset_state",
            "source_state",
            "observed_format_id",
            "probe_status",
            "observation_state",
            "metadata_surface",
            "metadata_production_verified",
            "hash_validation_mode",
            "anomaly_codes",
        }
    ),
    "format_summary": frozenset(
        {
            "format_assurance",
            "format_id",
            "mime_type",
            "media_kind",
            "asset_count",
            "active_asset_count",
            "present_file_instance_count",
            "physical_present_bytes",
            "unique_asset_bytes",
        }
    ),
    "duplicate_group": frozenset(
        {
            "duplicate_scope",
            "duplicate_assurance",
            "asset_id",
            "sha256",
            "member_count",
            "extra_copy_count",
            "potential_reclaimable_bytes",
        }
    ),
    "duplicate_member": frozenset(
        {
            "asset_id",
            "file_instance_id",
            "source_root_id",
            "relative_path",
            "file_size",
            "modified_time_ms",
        }
    ),
    "anomaly": frozenset(
        {
            "anomaly_id",
            "code",
            "severity",
            "subject_type",
            "subject_id",
            "source_root_id",
            "relative_path",
            "summary_zh",
            "action_zh",
        }
    ),
    "report_summary": frozenset({"counts", "reconciliation", "duplicate_assurance"}),
}
_MANIFEST_KEYS: Final = frozenset(
    {
        "schemaVersion",
        "reportId",
        "projectId",
        "generatorVersion",
        "policyVersion",
        "generatedAt",
        "snapshotSha256",
        "hashAssuranceSnapshotSha256",
        "duplicateAssurance",
        "assuranceToken",
        "sqlite",
        "sourceStates",
        "scanCompleteness",
        "sqlProvenance",
        "counts",
        "reconciliation",
        "files",
        "claims",
        "cannotProve",
    }
)
_MANIFEST_COUNT_KEYS: Final = frozenset(
    {
        "assetCount",
        "fileInstanceCount",
        "currentExactDuplicateGroupCount",
        "strictAsOfExactDuplicateGroupCount",
        "historicalExactDuplicateGroupCount",
        "historicalDuplicateMemberCount",
        "anomalyCount",
    }
)
_RECONCILIATION_KEYS: Final = frozenset(
    {
        "databaseAssetCount",
        "databaseFileInstanceCount",
        "assetCsvDataRows",
        "fileInstanceCsvDataRows",
        "formatCsvDataRows",
        "duplicateCsvDataRows",
        "anomalyCsvDataRows",
        "jsonlAssetRecords",
        "jsonlFileInstanceRecords",
        "jsonlFormatSummaryRecords",
        "jsonlDuplicateGroupRecords",
        "jsonlDuplicateMemberRecords",
        "jsonlAnomalyRecords",
        "jsonlRecordCount",
        "jsonlExpectedRecordCount",
        "assetResidual",
        "fileInstanceResidual",
        "formatAssetResidual",
        "formatPresentFileResidual",
        "formatPhysicalBytesResidual",
        "formatSummaryResidual",
        "duplicateGroupResidual",
        "duplicateMemberResidual",
        "anomalyResidual",
        "jsonlRecordResidual",
        "passed",
    }
)
_CLAIM_KEYS: Final = frozenset(
    {
        "sourceBytesModified",
        "databaseModified",
        "activeHostModified",
        "submitReady",
        "officiallyListed",
    }
)

_ASSET_SQL: Final = """
WITH file_counts AS (
  SELECT asset_id,
         count(*) AS file_count,
         sum(CASE WHEN state='present' THEN 1 ELSE 0 END) AS present_count,
         sum(CASE WHEN state='missing' THEN 1 ELSE 0 END) AS missing_count,
         sum(CASE WHEN state='changed' THEN 1 ELSE 0 END) AS changed_count
  FROM file_instances
  WHERE project_id=?
  GROUP BY asset_id
)
SELECT asset.asset_id, asset.sha256, asset.media_kind, asset.byte_size,
       asset.capture_time_ms, asset.technical_json, asset.state,
       asset.created_at, asset.updated_at,
       coalesce(file_counts.file_count, 0), coalesce(file_counts.present_count, 0),
       coalesce(file_counts.missing_count, 0), coalesce(file_counts.changed_count, 0)
FROM assets AS asset
LEFT JOIN file_counts ON file_counts.asset_id=asset.asset_id
WHERE asset.project_id=?
ORDER BY asset.asset_id
""".strip()

_FILE_SQL: Final = """
SELECT operation.operation_id, operation.status, operation.request_json, operation.result_json,
       file.file_instance_id, file.asset_id, file.source_root_id, file.relative_path,
       file.file_size, file.modified_time_ms, file.identity_json, file.state,
       asset.sha256, asset.media_kind, asset.state, source.state
FROM operations AS operation
JOIN file_instances AS file
  ON file.project_id=operation.project_id
 AND file.source_root_id=json_extract(operation.request_json, '$.source_root_id')
 AND file.relative_path=json_extract(operation.request_json, '$.relative_path')
JOIN assets AS asset
  ON asset.project_id=file.project_id AND asset.asset_id=file.asset_id
JOIN source_roots AS source
  ON source.project_id=file.project_id AND source.source_root_id=file.source_root_id
WHERE operation.project_id=? AND operation.operation_type='scan_candidate'
ORDER BY file.file_instance_id
""".strip()

_DUPLICATE_SQL: Final = """
WITH duplicate_members AS (
  SELECT asset.asset_id, asset.sha256, asset.byte_size,
         count(*) OVER (PARTITION BY file.asset_id) AS member_count,
         file.file_instance_id, file.source_root_id, file.relative_path,
         file.file_size, file.modified_time_ms
  FROM file_instances AS file
  JOIN assets AS asset
    ON asset.project_id=file.project_id AND asset.asset_id=file.asset_id
  WHERE file.project_id=? AND file.state='present'
)
SELECT asset_id, sha256, byte_size, member_count, file_instance_id,
       source_root_id, relative_path, file_size, modified_time_ms
FROM duplicate_members
WHERE member_count > 1
ORDER BY asset_id, source_root_id, relative_path
""".strip()

_SUMMARY_SQL: Final = """
SELECT
  (SELECT count(*) FROM assets WHERE project_id=?),
  (SELECT count(*) FROM assets WHERE project_id=? AND state='active'),
  (SELECT count(*) FROM assets WHERE project_id=? AND state='missing'),
  (SELECT count(*) FROM assets WHERE project_id=? AND state='quarantined'),
  (SELECT count(*) FROM file_instances WHERE project_id=?),
  (SELECT count(*) FROM file_instances WHERE project_id=? AND state='present'),
  (SELECT count(*) FROM file_instances WHERE project_id=? AND state='missing'),
  (SELECT count(*) FROM file_instances WHERE project_id=? AND state='changed'),
  (SELECT coalesce(sum(byte_size), 0) FROM assets WHERE project_id=?),
  (SELECT coalesce(sum(file_size), 0) FROM file_instances
     WHERE project_id=? AND state='present'),
  (SELECT count(*) FROM duplicate_relations
     WHERE project_id=? AND relation_kind='exact')
""".strip()


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _json_text(payload: object) -> str:
    text = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return text.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _strict_json_loads(payload: str) -> object:
    return json.loads(
        payload,
        object_pairs_hook=_reject_duplicate_json_keys,
        parse_constant=_reject_json_constant,
    )


class _SchemaValidationError(ValueError):
    pass


def _json_value_key(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True
    )


def _json_values_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _json_values_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(
            _json_values_equal(left[key], right[key]) for key in left
        )
    return left == right


def _schema_type_matches(value: object, declared: str) -> bool:
    if declared == "object":
        return isinstance(value, dict)
    if declared == "array":
        return isinstance(value, list)
    if declared == "string":
        return isinstance(value, str)
    if declared == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if declared == "boolean":
        return isinstance(value, bool)
    if declared == "null":
        return value is None
    return False


def _resolve_local_schema_ref(root: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise _SchemaValidationError(f"unsupported schema reference: {reference}")
    current: object = root
    for raw_token in reference[2:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise _SchemaValidationError(f"unresolved schema reference: {reference}")
        current = current[token]
    if not isinstance(current, dict):
        raise _SchemaValidationError(f"schema reference is not an object: {reference}")
    return current


def _validate_schema_subset(
    value: object,
    schema: dict[str, Any],
    root: dict[str, Any],
    *,
    path: str = "$",
) -> None:
    reference = schema.get("$ref")
    if reference is not None:
        if not isinstance(reference, str):
            raise _SchemaValidationError(f"{path}: invalid schema reference")
        _validate_schema_subset(value, _resolve_local_schema_ref(root, reference), root, path=path)

    alternatives = schema.get("oneOf")
    if alternatives is not None:
        if not isinstance(alternatives, list):
            raise _SchemaValidationError(f"{path}: invalid oneOf")
        matches = 0
        for alternative in alternatives:
            if not isinstance(alternative, dict):
                raise _SchemaValidationError(f"{path}: invalid oneOf member")
            try:
                _validate_schema_subset(value, alternative, root, path=path)
            except _SchemaValidationError:
                continue
            matches += 1
        if matches != 1:
            raise _SchemaValidationError(f"{path}: expected exactly one matching schema")

    all_of = schema.get("allOf")
    if all_of is not None:
        if not isinstance(all_of, list):
            raise _SchemaValidationError(f"{path}: invalid allOf")
        for item in all_of:
            if not isinstance(item, dict):
                raise _SchemaValidationError(f"{path}: invalid allOf member")
            condition = item.get("if")
            if condition is None:
                _validate_schema_subset(value, item, root, path=path)
                continue
            if not isinstance(condition, dict):
                raise _SchemaValidationError(f"{path}: invalid if schema")
            try:
                _validate_schema_subset(value, condition, root, path=path)
            except _SchemaValidationError:
                continue
            then_schema = item.get("then")
            if isinstance(then_schema, dict):
                _validate_schema_subset(value, then_schema, root, path=path)

    declared_type = schema.get("type")
    if declared_type is not None:
        declared_types = [declared_type] if isinstance(declared_type, str) else declared_type
        if not isinstance(declared_types, list) or not all(
            isinstance(item, str) for item in declared_types
        ):
            raise _SchemaValidationError(f"{path}: invalid type declaration")
        if not any(_schema_type_matches(value, item) for item in declared_types):
            raise _SchemaValidationError(f"{path}: value has the wrong JSON type")

    if "const" in schema and not _json_values_equal(value, schema["const"]):
        raise _SchemaValidationError(f"{path}: const mismatch")
    enumeration = schema.get("enum")
    if enumeration is not None and (
        not isinstance(enumeration, list)
        or not any(_json_values_equal(value, item) for item in enumeration)
    ):
        raise _SchemaValidationError(f"{path}: enum mismatch")

    if isinstance(value, dict):
        required = schema.get("required", [])
        if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
            raise _SchemaValidationError(f"{path}: invalid required declaration")
        missing = set(required) - set(value)
        if missing:
            raise _SchemaValidationError(f"{path}: required keys are missing")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise _SchemaValidationError(f"{path}: invalid properties declaration")
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            raise _SchemaValidationError(f"{path}: additional properties are forbidden")
        for key, item in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                _validate_schema_subset(item, child_schema, root, path=f"{path}.{key}")

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            raise _SchemaValidationError(f"{path}: array has too few items")
        max_items = schema.get("maxItems")
        if isinstance(max_items, int) and len(value) > max_items:
            raise _SchemaValidationError(f"{path}: array has too many items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema_subset(item, item_schema, root, path=f"{path}[{index}]")
        if schema.get("uniqueItems") is True:
            keys = [_json_value_key(item) for item in value]
            if len(keys) != len(set(keys)):
                raise _SchemaValidationError(f"{path}: array items are not unique")

    if isinstance(value, str):
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            raise _SchemaValidationError(f"{path}: string pattern mismatch")
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            raise _SchemaValidationError(f"{path}: string is too short")
        if schema.get("format") == "date-time":
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise _SchemaValidationError(f"{path}: invalid date-time") from exc
            if parsed.tzinfo is None:
                raise _SchemaValidationError(f"{path}: date-time lacks a timezone")

    minimum = schema.get("minimum")
    if (
        minimum is not None
        and isinstance(value, int)
        and not isinstance(value, bool)
        and value < minimum
    ):
        raise _SchemaValidationError(f"{path}: integer is below minimum")


@lru_cache(maxsize=2)
def _load_public_schema(filename: str) -> dict[str, Any]:
    schema_path = Path(__file__).resolve().parents[3] / "schemas" / filename
    try:
        schema = _strict_json_loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise MibaoError("MB-RPT-0005", f"Public report schema is unavailable: {filename}") from exc
    if not isinstance(schema, dict):
        raise MibaoError("MB-RPT-0005", f"Public report schema is invalid: {filename}")
    return schema


def _validate_public_schema(value: object, filename: str) -> None:
    schema = _load_public_schema(filename)
    try:
        _validate_schema_subset(value, schema, schema)
    except _SchemaValidationError as exc:
        raise MibaoError(
            "MB-RPT-0005", f"Public report schema validation failed: {filename}"
        ) from exc


def _validate_public_record(record: dict[str, Any]) -> None:
    schema = _load_public_schema("inventory-report-record.schema.json")
    properties = schema.get("properties")
    definitions = schema.get("$defs")
    if not isinstance(properties, dict) or not isinstance(definitions, dict):
        raise MibaoError("MB-RPT-0005", "Public report record schema is incomplete")
    try:
        for key in (
            "schema_version",
            "report_id",
            "project_id",
            "snapshot_sha256",
            "sequence",
            "record_type",
        ):
            property_schema = properties.get(key)
            if not isinstance(property_schema, dict):
                raise _SchemaValidationError(f"$.{key}: property schema is missing")
            _validate_schema_subset(record[key], property_schema, schema, path=f"$.{key}")
        record_type = record["record_type"]
        data_schema = definitions.get(record_type) if isinstance(record_type, str) else None
        if not isinstance(data_schema, dict):
            raise _SchemaValidationError("$.record_type: data schema is missing")
        _validate_schema_subset(record["data"], data_schema, schema, path="$.data")
    except _SchemaValidationError as exc:
        raise MibaoError("MB-RPT-0005", "Public report record schema validation failed") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _visible_text(value: object, *, single_line: bool = False) -> str:
    text = str(value)
    rendered: list[str] = []
    for character in text:
        category = unicodedata.category(character)
        invisible = category in {"Cc", "Cf", "Zl", "Zp"}
        if invisible or (single_line and character in {"\r", "\n", "\t"}):
            rendered.append(f"\\u{ord(character):04X}")
        else:
            rendered.append(character)
    return "".join(rendered)


def escape_html_text(value: object) -> str:
    """Make untrusted text visible and safe for an HTML text node."""

    return html.escape(_visible_text(value), quote=True)


def _first_formula_character(value: str) -> str | None:
    normalized = unicodedata.normalize("NFKC", value)
    for character in normalized:
        category = unicodedata.category(character)
        if character.isspace() or category in {"Cc", "Cf", "Zs", "Zl", "Zp"}:
            continue
        return character
    return None


def sanitize_csv_cell(value: object) -> str:
    """Create spreadsheet-safe presentation text; JSONL retains the exact raw value."""

    raw = str(value)
    visible = _visible_text(raw, single_line=True)
    first = _first_formula_character(raw)
    return "'" + visible if first in {"=", "+", "-", "@"} else visible


@dataclass(frozen=True, slots=True)
class InventoryReportPolicy:
    batch_size: int = 512
    max_rows: int = 1_000_000
    max_distinct_formats: int = 1024
    max_cell_chars: int = 32760
    html_preview_rows: int = 1000
    max_total_output_bytes: int = 2 * 1024 * 1024 * 1024
    max_assurance_age_seconds: int = 60

    def __post_init__(self) -> None:
        if not 1 <= self.batch_size <= 5000:
            raise MibaoError("MB-RPT-0001", "Report batch size must be between 1 and 5000")
        if not 1 <= self.max_rows <= 10_000_000:
            raise MibaoError("MB-RPT-0001", "Report row limit must be finite and positive")
        if not 1 <= self.max_distinct_formats <= 10_000:
            raise MibaoError("MB-RPT-0001", "Report format-bucket limit is invalid")
        if not 256 <= self.max_cell_chars <= 32760:
            raise MibaoError("MB-RPT-0001", "Report cell limit must be between 256 and 32760")
        if not 0 <= self.html_preview_rows <= 100_000:
            raise MibaoError("MB-RPT-0001", "HTML preview row limit is invalid")
        if not 1024 * 1024 <= self.max_total_output_bytes <= 8 * 1024 * 1024 * 1024:
            raise MibaoError("MB-RPT-0001", "Report output-byte limit is invalid")
        if not 1 <= self.max_assurance_age_seconds <= 300:
            raise MibaoError("MB-RPT-0001", "Report assurance age limit is invalid")


@dataclass(frozen=True, slots=True)
class InventoryReportResult:
    project_id: str
    report_id: str
    bundle_dir: Path
    html_path: Path
    asset_csv_path: Path
    file_csv_path: Path
    format_csv_path: Path
    duplicate_csv_path: Path
    anomaly_csv_path: Path
    jsonl_path: Path
    receipt_path: Path
    asset_count: int
    file_instance_count: int
    current_exact_duplicate_group_count: int
    strict_as_of_exact_duplicate_group_count: int
    historical_exact_duplicate_group_count: int
    anomaly_count: int
    duplicate_assurance: str
    reused_existing: bool

    def as_dict(self, project_root: Path) -> dict[str, Any]:
        def relative(path: Path) -> str:
            return path.relative_to(project_root).as_posix()

        return {
            "project_id": self.project_id,
            "report_id": self.report_id,
            "bundle_dir": relative(self.bundle_dir),
            "html": relative(self.html_path),
            "assets_csv": relative(self.asset_csv_path),
            "files_csv": relative(self.file_csv_path),
            "formats_csv": relative(self.format_csv_path),
            "duplicates_csv": relative(self.duplicate_csv_path),
            "anomalies_csv": relative(self.anomaly_csv_path),
            "jsonl": relative(self.jsonl_path),
            "manifest": relative(self.receipt_path),
            "asset_count": self.asset_count,
            "file_instance_count": self.file_instance_count,
            "current_exact_duplicate_group_count": self.current_exact_duplicate_group_count,
            "strict_as_of_exact_duplicate_group_count": (
                self.strict_as_of_exact_duplicate_group_count
            ),
            "historical_exact_duplicate_group_count": (self.historical_exact_duplicate_group_count),
            "anomaly_count": self.anomaly_count,
            "duplicate_assurance": self.duplicate_assurance,
            "reused_existing": self.reused_existing,
        }


@dataclass(slots=True)
class _OutputBudget:
    limit: int
    used: int = 0

    def consume(self, size: int) -> None:
        self.used += size
        if self.used > self.limit:
            raise MibaoError("MB-RPT-0004", "Report output-byte limit exceeded")


class _TextSink:
    def __init__(self, path: Path, budget: _OutputBudget, *, bom: bool = False) -> None:
        self.path = path
        self.budget = budget
        self.handle: BinaryIO | None = None
        self.bom = bom

    def __enter__(self) -> _TextSink:
        self.handle = self.path.open("xb")
        if self.bom:
            self._write_bytes(b"\xef\xbb\xbf")
        return self

    def _write_bytes(self, payload: bytes) -> None:
        if self.handle is None:
            raise RuntimeError("report sink is not open")
        self.budget.consume(len(payload))
        self.handle.write(payload)

    def write(self, value: str) -> int:
        payload = value.encode("utf-8")
        self._write_bytes(payload)
        return len(value)

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.handle is None:
            return
        try:
            self.handle.flush()
            os.fsync(self.handle.fileno())
        finally:
            self.handle.close()
            self.handle = None


@dataclass(frozen=True, slots=True)
class _AssetRow:
    asset_id: str
    sha256: str
    media_kind: str
    byte_size: int
    capture_time_ms: int | None
    state: str
    created_at: str
    updated_at: str
    format_id: str | None
    format_mime: str | None
    format_media_kind: str | None
    format_assurance: str
    file_instance_count: int
    present_instance_count: int
    missing_instance_count: int
    changed_instance_count: int
    anomalies: tuple[str, ...]

    def data(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "sha256": self.sha256,
            "media_kind": self.media_kind,
            "byte_size": self.byte_size,
            "capture_time_ms": self.capture_time_ms,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "format_id": self.format_id,
            "format_mime": self.format_mime,
            "format_media_kind": self.format_media_kind,
            "format_assurance": self.format_assurance,
            "file_instance_count": self.file_instance_count,
            "present_instance_count": self.present_instance_count,
            "missing_instance_count": self.missing_instance_count,
            "changed_instance_count": self.changed_instance_count,
            "anomaly_codes": list(self.anomalies),
        }


@dataclass(frozen=True, slots=True)
class _FileRow:
    operation_id: str
    operation_status: str
    file_instance_id: str
    asset_id: str
    source_root_id: str
    relative_path: str
    file_size: int
    modified_time_ms: int
    file_state: str
    asset_sha256: str
    asset_media_kind: str
    asset_state: str
    source_state: str
    observed_format_id: str | None
    probe_status: str | None
    observation_state: str | None
    metadata_surface: str | None
    metadata_production_verified: bool
    hash_validation_mode: str | None
    anomalies: tuple[str, ...]

    def data(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "operation_status": self.operation_status,
            "file_instance_id": self.file_instance_id,
            "asset_id": self.asset_id,
            "source_root_id": self.source_root_id,
            "relative_path": self.relative_path,
            "file_size": self.file_size,
            "modified_time_ms": self.modified_time_ms,
            "file_state": self.file_state,
            "asset_sha256": self.asset_sha256,
            "asset_media_kind": self.asset_media_kind,
            "asset_state": self.asset_state,
            "source_state": self.source_state,
            "observed_format_id": self.observed_format_id,
            "probe_status": self.probe_status,
            "observation_state": self.observation_state,
            "metadata_surface": self.metadata_surface,
            "metadata_production_verified": self.metadata_production_verified,
            "hash_validation_mode": self.hash_validation_mode,
            "anomaly_codes": list(self.anomalies),
        }


def _asset_from_row(row: tuple[Any, ...]) -> _AssetRow:
    technical = json.loads(str(row[5]))
    observations = technical.get("candidate_observations")
    media_probe = technical.get("media_probe")
    content_bound = isinstance(observations, dict) and observations.get("content_bound") is True
    if content_bound and isinstance(media_probe, dict):
        format_id = media_probe.get("format_id")
        format_mime = media_probe.get("mime_type")
        format_media_kind = media_probe.get("media_kind")
        assurance = "content_bound_header_probe"
    else:
        format_id = format_mime = format_media_kind = None
        assurance = "unknown_or_unbound"
    file_count = int(row[9])
    anomalies: list[str] = []
    if str(row[6]) != "active":
        anomalies.append(f"asset_{row[6]}")
    if file_count == 0:
        anomalies.append("asset_unreferenced")
    return _AssetRow(
        asset_id=str(row[0]),
        sha256=str(row[1]),
        media_kind=str(row[2]),
        byte_size=int(row[3]),
        capture_time_ms=int(row[4]) if row[4] is not None else None,
        state=str(row[6]),
        created_at=str(row[7]),
        updated_at=str(row[8]),
        format_id=str(format_id) if format_id is not None else None,
        format_mime=str(format_mime) if format_mime is not None else None,
        format_media_kind=str(format_media_kind) if format_media_kind is not None else None,
        format_assurance=assurance,
        file_instance_count=file_count,
        present_instance_count=int(row[10]),
        missing_instance_count=int(row[11]),
        changed_instance_count=int(row[12]),
        anomalies=tuple(anomalies),
    )


def _file_from_row(row: tuple[Any, ...]) -> _FileRow:
    result = json.loads(str(row[3]))
    probe = result.get("media_probe")
    metadata = result.get("metadata")
    content_hash = result.get("content_hash")
    probe_status = str(probe.get("status")) if isinstance(probe, dict) else None
    anomalies: list[str] = []
    if str(row[11]) != "present":
        anomalies.append(f"file_{row[11]}")
    if str(row[1]) != "succeeded":
        anomalies.append(f"operation_{row[1]}")
    if probe_status in {"mismatch", "empty", "truncated", "unknown"}:
        anomalies.append(f"media_{probe_status}")
    classification = result.get("classification")
    if classification in {"media_probe_failed", "scan_candidate_stale"}:
        anomalies.append(str(classification))
    if result.get("content_observation_state") == "unbound_or_stale_content":
        anomalies.append("unbound_content_observation")
    if not isinstance(content_hash, dict):
        anomalies.append("content_hash_missing")
    metadata_surface = metadata.get("evidence_surface") if isinstance(metadata, dict) else None
    return _FileRow(
        operation_id=str(row[0]),
        operation_status=str(row[1]),
        file_instance_id=str(row[4]),
        asset_id=str(row[5]),
        source_root_id=str(row[6]),
        relative_path=str(row[7]),
        file_size=int(row[8]),
        modified_time_ms=int(row[9]),
        file_state=str(row[11]),
        asset_sha256=str(row[12]),
        asset_media_kind=str(row[13]),
        asset_state=str(row[14]),
        source_state=str(row[15]),
        observed_format_id=(
            str(probe.get("format_id"))
            if isinstance(probe, dict) and probe.get("format_id") is not None
            else None
        ),
        probe_status=probe_status,
        observation_state=(
            str(result.get("content_observation_state"))
            if result.get("content_observation_state") is not None
            else None
        ),
        metadata_surface=str(metadata_surface) if metadata_surface is not None else None,
        metadata_production_verified=(
            metadata.get("production_verified") is True if isinstance(metadata, dict) else False
        ),
        hash_validation_mode=(
            str(content_hash.get("validation_mode"))
            if isinstance(content_hash, dict) and content_hash.get("validation_mode") is not None
            else None
        ),
        anomalies=tuple(sorted(set(anomalies))),
    )


def _iter_rows(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[object, ...],
    batch_size: int,
) -> Iterator[tuple[Any, ...]]:
    cursor = connection.execute(sql, parameters)
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            return
        yield from rows


def _connect_readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(
        path.resolve().as_uri() + "?mode=ro",
        uri=True,
        timeout=5.0,
        isolation_level=None,
    )
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA trusted_schema = OFF")
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _summary(connection: sqlite3.Connection, project_id: str) -> dict[str, int]:
    row = connection.execute(_SUMMARY_SQL, (project_id,) * 11).fetchone()
    if row is None:
        raise MibaoError("MB-RPT-0002", "Inventory summary query returned no row")
    keys = (
        "asset_total",
        "asset_active",
        "asset_missing",
        "asset_quarantined",
        "file_total",
        "file_present",
        "file_missing",
        "file_changed",
        "unique_asset_bytes",
        "physical_present_bytes",
        "exact_relation_rows",
    )
    return {key: int(value) for key, value in zip(keys, row, strict=True)}


def _validate_summary(summary: dict[str, int]) -> None:
    if summary["asset_total"] != (
        summary["asset_active"] + summary["asset_missing"] + summary["asset_quarantined"]
    ):
        raise MibaoError("MB-RPT-0003", "Asset state counts do not reconcile")
    if summary["file_total"] != (
        summary["file_present"] + summary["file_missing"] + summary["file_changed"]
    ):
        raise MibaoError("MB-RPT-0003", "FileInstance state counts do not reconcile")
    if summary["exact_relation_rows"] != 0:
        raise MibaoError("MB-RPT-0003", "Exact duplicate_relations rows violate the Asset model")


def _expected_reconciliation(
    summary: dict[str, int],
    *,
    format_record_count: int,
    duplicate_group_count: int,
    duplicate_member_count: int,
    anomaly_count: int,
) -> dict[str, int | bool]:
    jsonl_record_count = (
        2
        + summary["asset_total"]
        + summary["file_total"]
        + format_record_count
        + duplicate_group_count
        + duplicate_member_count
        + anomaly_count
    )
    return {
        "databaseAssetCount": summary["asset_total"],
        "databaseFileInstanceCount": summary["file_total"],
        "assetCsvDataRows": summary["asset_total"],
        "fileInstanceCsvDataRows": summary["file_total"],
        "formatCsvDataRows": format_record_count,
        "duplicateCsvDataRows": duplicate_member_count,
        "anomalyCsvDataRows": anomaly_count,
        "jsonlAssetRecords": summary["asset_total"],
        "jsonlFileInstanceRecords": summary["file_total"],
        "jsonlFormatSummaryRecords": format_record_count,
        "jsonlDuplicateGroupRecords": duplicate_group_count,
        "jsonlDuplicateMemberRecords": duplicate_member_count,
        "jsonlAnomalyRecords": anomaly_count,
        "jsonlRecordCount": jsonl_record_count,
        "jsonlExpectedRecordCount": jsonl_record_count,
        "assetResidual": 0,
        "fileInstanceResidual": 0,
        "formatAssetResidual": 0,
        "formatPresentFileResidual": 0,
        "formatPhysicalBytesResidual": 0,
        "formatSummaryResidual": 0,
        "duplicateGroupResidual": 0,
        "duplicateMemberResidual": 0,
        "anomalyResidual": 0,
        "jsonlRecordResidual": 0,
        "passed": True,
    }


def _query_provenance() -> dict[str, dict[str, str]]:
    return {
        name: {"sql": sql, "sha256": hashlib.sha256(sql.encode()).hexdigest()}
        for name, sql in {
            "project_summary": _SUMMARY_SQL,
            "asset_rows": _ASSET_SQL,
            "file_instance_rows": _FILE_SQL,
            "duplicate_members": _DUPLICATE_SQL,
        }.items()
    }


def _ensure_owned_directory(project_root: Path, relative: Path) -> Path:
    current = project_root
    for component in relative.parts:
        candidate = current / component
        if not candidate.exists() and not candidate.is_symlink():
            with suppress(FileExistsError):
                candidate.mkdir()
        authorized = authorize_existing_path(
            project_root,
            candidate,
            expected_kind="directory",
            policy=PathPolicy(),
        )
        current = authorized.path
    return current


def _validate_plugin_isolation(project_root: Path) -> None:
    configured = os.environ.get("CODEBUDDY_PLUGIN_ROOT")
    if not configured:
        return
    try:
        plugin_root = Path(configured).expanduser().resolve(strict=False)
        project = project_root.resolve()
        overlaps = project.is_relative_to(plugin_root) or plugin_root.is_relative_to(project)
    except (OSError, ValueError) as exc:
        raise MibaoError("MB-RPT-0004", "Plugin/report root isolation cannot be resolved") from exc
    if overlaps:
        raise MibaoError("MB-RPT-0004", "Inventory reports must not overlap the plugin root")


def _truncate(value: object, limit: int) -> str:
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _csv_row(values: list[object], limit: int) -> list[object]:
    return [
        value
        if isinstance(value, int) and not isinstance(value, bool)
        else sanitize_csv_cell(_truncate(value, limit))
        for value in values
    ]


def _json_record(
    sink: _TextSink,
    *,
    report_id: str,
    project_id: str,
    snapshot_sha256: str,
    sequence: int,
    record_type: str,
    data: dict[str, Any],
) -> None:
    sink.write(
        _json_text(
            {
                "schema_version": _REPORT_SCHEMA_VERSION,
                "report_id": report_id,
                "project_id": project_id,
                "snapshot_sha256": snapshot_sha256,
                "sequence": sequence,
                "record_type": record_type,
                "data": data,
            }
        )
        + "\n"
    )


def _html_header(sink: _TextSink, *, title: str, summary: dict[str, int]) -> None:
    sink.write(
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" '
        f'content="{html.escape(_CSP_VALUE, quote=True)}">'
        f"<title>{escape_html_text(title)}</title>"
        f"<style>{_REPORT_CSS}</style></head><body>"
        f"<h1>{escape_html_text(title)}</h1>"
        '<p class="muted">静态本地报告; 无脚本、无外部资源、无源文件链接。</p>'
        "<h2>总览</h2><table><tbody>"
        f"<tr><th>唯一 Asset</th><td>{summary['asset_total']}</td></tr>"
        f"<tr><th>FileInstance</th><td>{summary['file_total']}</td></tr>"
        f"<tr><th>SQLite snapshot present 路径</th><td>{summary['file_present']}</td></tr>"
        f"<tr><th>唯一资产字节</th><td>{summary['unique_asset_bytes']}</td></tr>"
        "<tr><th>SQLite snapshot present 物理字节</th>"
        f"<td>{summary['physical_present_bytes']}</td></tr>"
        f"<tr><th>异常项</th><td>{summary.get('anomaly_count', 0)}</td></tr>"
        "</tbody></table>"
    )


def _file_facts(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": _sha256(path)}


class _ReportHtmlValidator(HTMLParser):
    _ALLOWED_TAGS: ClassVar[set[str]] = {
        "html",
        "head",
        "meta",
        "title",
        "style",
        "body",
        "h1",
        "h2",
        "p",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "code",
    }
    _PARENTS: ClassVar[dict[str, set[str | None]]] = {
        "html": {None},
        "head": {"html"},
        "meta": {"head"},
        "title": {"head"},
        "style": {"head"},
        "body": {"html"},
        "h1": {"body"},
        "h2": {"body"},
        "p": {"body"},
        "table": {"body"},
        "thead": {"table"},
        "tbody": {"table"},
        "tr": {"thead", "tbody"},
        "th": {"tr"},
        "td": {"tr"},
        "code": {"p", "td"},
    }
    _HEAD_PREFIX: ClassVar[list[str]] = [
        "doctype",
        "start:html",
        "start:head",
        "meta:charset",
        "meta:csp",
        "start:title",
        "end:title",
        "start:style",
        "end:style",
        "end:head",
        "start:body",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.issues: list[str] = []
        self.events: list[str] = []
        self.stack: list[str] = []
        self.tag_counts: dict[str, int] = {}
        self.style_chunks: list[str] = []
        self.doctype_count = 0
        self.charset_count = 0
        self.csp_count = 0

    def handle_decl(self, declaration: str) -> None:
        if declaration.strip().lower() == "doctype html":
            self.doctype_count += 1
            self.events.append("doctype")
        else:
            self.issues.append("forbidden_declaration")

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag not in self._ALLOWED_TAGS:
            self.issues.append(f"forbidden_tag:{tag}")
            return
        parent = self.stack[-1] if self.stack else None
        if parent not in self._PARENTS[tag]:
            self.issues.append(f"invalid_parent:{parent}:{tag}")
        lowered_attrs = [(name.lower(), value) for name, value in attrs]
        if len({name for name, _value in lowered_attrs}) != len(lowered_attrs):
            self.issues.append(f"duplicate_attribute:{tag}")
            return
        observed = dict(lowered_attrs)
        if tag == "html":
            if observed != {"lang": "zh-CN"}:
                self.issues.append("html_attributes_invalid")
        elif tag == "meta":
            if observed == {"charset": "utf-8"}:
                self.charset_count += 1
                self.events.append("meta:charset")
            elif observed == {
                "http-equiv": "Content-Security-Policy",
                "content": _CSP_VALUE,
            }:
                self.csp_count += 1
                self.events.append("meta:csp")
            else:
                self.issues.append("meta_attributes_invalid")
            return
        elif tag in {"p", "td"}:
            if observed not in ({}, {"class": "muted"}, {"class": "warn"}):
                self.issues.append(f"class_attribute_invalid:{tag}")
        elif observed:
            self.issues.append(f"attributes_not_allowed:{tag}")
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        self.events.append(f"start:{tag}")
        self.stack.append(tag)

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.issues.append(f"self_closing_tag_forbidden:{tag}")

    def handle_endtag(self, tag: str) -> None:
        if tag == "meta" or tag not in self._ALLOWED_TAGS:
            self.issues.append(f"forbidden_end_tag:{tag}")
            return
        if not self.stack or self.stack[-1] != tag:
            self.issues.append(f"unbalanced_end_tag:{tag}")
            return
        self.stack.pop()
        self.events.append(f"end:{tag}")

    def handle_data(self, data: str) -> None:
        if self.stack and self.stack[-1] == "style":
            self.style_chunks.append(data)
        elif not self.stack and data.strip():
            self.issues.append("text_outside_document")

    def handle_comment(self, data: str) -> None:
        self.issues.append("comments_forbidden")

    def handle_pi(self, data: str) -> None:
        self.issues.append("processing_instruction_forbidden")

    def unknown_decl(self, data: str) -> None:
        self.issues.append("unknown_declaration_forbidden")


def _verify_csv(path: Path, expected_rows: int) -> None:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader)
            rows = 0
            for row in reader:
                if len(row) != len(header):
                    raise MibaoError("MB-RPT-0005", f"CSV column count drifted: {path.name}")
                for cell in row:
                    if not cell.startswith("'") and _first_formula_character(cell) in {
                        "=",
                        "+",
                        "-",
                        "@",
                    }:
                        raise MibaoError(
                            "MB-RPT-0005",
                            f"CSV contains an unsafe formula-like cell: {path.name}",
                        )
                rows += 1
    except (OSError, UnicodeError, csv.Error, StopIteration) as exc:
        raise MibaoError("MB-RPT-0005", f"CSV cannot be reopened: {path.name}") from exc
    if rows != expected_rows:
        raise MibaoError("MB-RPT-0005", f"CSV row count does not reconcile: {path.name}")


def _verify_jsonl(
    path: Path,
    expected: dict[str, int],
    *,
    expected_report_id: str | None = None,
    expected_project_id: str | None = None,
    expected_snapshot_sha256: str | None = None,
    expected_duplicate_assurance: str | None = None,
) -> None:
    counts: dict[str, int] = {}
    first_type = last_type = None
    observed_identity: tuple[str, str, str] | None = None
    sequence = 0
    try:
        with path.open("rb") as handle:
            while True:
                physical_line = handle.readline(_MAX_JSONL_PHYSICAL_LINE_BYTES + 1)
                if not physical_line:
                    break
                if len(physical_line) > _MAX_JSONL_PHYSICAL_LINE_BYTES:
                    raise MibaoError("MB-RPT-0005", "JSONL physical line exceeds the safety cap")
                if sequence == 0 and physical_line.startswith(b"\xef\xbb\xbf"):
                    raise MibaoError("MB-RPT-0005", "JSONL must not contain a BOM")
                if not physical_line.endswith(b"\n") or b"\r" in physical_line:
                    raise MibaoError("MB-RPT-0005", "JSONL must use strict LF framing")
                framed = physical_line[:-1]
                if not framed:
                    raise MibaoError("MB-RPT-0005", "JSONL contains a blank physical line")
                record = _strict_json_loads(framed.decode("utf-8"))
                required = {
                    "schema_version",
                    "report_id",
                    "project_id",
                    "snapshot_sha256",
                    "sequence",
                    "record_type",
                    "data",
                }
                if not isinstance(record, dict) or set(record) != required:
                    raise MibaoError("MB-RPT-0005", "JSONL record shape is invalid")
                _validate_public_record(record)
                identity = (
                    str(record["report_id"]),
                    str(record["project_id"]),
                    str(record["snapshot_sha256"]),
                )
                observed_identity = observed_identity or identity
                if identity != observed_identity:
                    raise MibaoError("MB-RPT-0005", "JSONL record identity drifted")
                if (
                    (expected_report_id is not None and identity[0] != expected_report_id)
                    or (expected_project_id is not None and identity[1] != expected_project_id)
                    or (
                        expected_snapshot_sha256 is not None
                        and identity[2] != expected_snapshot_sha256
                    )
                ):
                    raise MibaoError("MB-RPT-0005", "JSONL identity does not match the snapshot")
                sequence += 1
                if record.get("sequence") != sequence:
                    raise MibaoError("MB-RPT-0005", "JSONL sequence is not contiguous")
                record_type = str(record.get("record_type"))
                data = record.get("data")
                if (
                    record_type not in _RECORD_DATA_KEYS
                    or record_type not in expected
                    or not isinstance(data, dict)
                    or set(data) != _RECORD_DATA_KEYS[record_type]
                ):
                    raise MibaoError("MB-RPT-0005", "JSONL record data contract is invalid")
                if expected_duplicate_assurance is not None:
                    if record_type in {"report_header", "report_summary", "duplicate_group"} and (
                        data.get("duplicate_assurance") != expected_duplicate_assurance
                    ):
                        raise MibaoError("MB-RPT-0005", "JSONL duplicate assurance drifted")
                    if record_type == "duplicate_group":
                        expected_scope = (
                            "strict_as_of_token"
                            if expected_duplicate_assurance == "strict_full_verified_as_of_token"
                            else "historical_candidate"
                        )
                        if data.get("duplicate_scope") != expected_scope:
                            raise MibaoError("MB-RPT-0005", "JSONL duplicate scope drifted")
                counts[record_type] = counts.get(record_type, 0) + 1
                first_type = first_type or record_type
                last_type = record_type
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise MibaoError("MB-RPT-0005", "JSONL cannot be reopened") from exc
    if sequence == 0:
        raise MibaoError("MB-RPT-0005", "JSONL is empty")
    if first_type != "report_header" or last_type != "report_summary":
        raise MibaoError("MB-RPT-0005", "JSONL header/summary ordering is invalid")
    for record_type, expected_count in expected.items():
        if counts.get(record_type, 0) != expected_count:
            raise MibaoError(
                "MB-RPT-0005",
                f"JSONL record count does not reconcile: {record_type}",
            )


def _verify_html(path: Path) -> None:
    try:
        payload = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise MibaoError("MB-RPT-0005", "HTML report cannot be reopened") from exc
    parser = _ReportHtmlValidator()
    parser.feed(payload)
    parser.close()
    singleton_tags = {"html", "head", "title", "style", "body"}
    if (
        parser.issues
        or parser.stack
        or parser.doctype_count != 1
        or parser.charset_count != 1
        or parser.csp_count != 1
        or any(parser.tag_counts.get(tag) != 1 for tag in singleton_tags)
        or parser.events[: len(parser._HEAD_PREFIX)] != parser._HEAD_PREFIX
        or parser.events[-2:] != ["end:body", "end:html"]
        or "".join(parser.style_chunks) != _REPORT_CSS
        or "<script" in payload.lower()
    ):
        raise MibaoError("MB-RPT-0005", "HTML report contains a forbidden active surface")


def _safe_cleanup_stage(stage: Path, parent: Path, owner_nonce: str) -> None:
    try:
        resolved = stage.resolve(strict=False)
        if resolved.parent != parent.resolve() or not stage.name.startswith(".partial-"):
            return
        sentinel = stage / _STAGE_SENTINEL
        if sentinel.is_file():
            payload = json.loads(sentinel.read_text(encoding="utf-8"))
            if payload.get("owner_nonce") != owner_nonce:
                return
        elif not stage.name.endswith("-" + owner_nonce):
            return
        shutil.rmtree(stage)
    except (OSError, json.JSONDecodeError):
        return


def _result_from_manifest(
    project_root: Path,
    bundle: Path,
    *,
    reused: bool,
    expected_report_id: str | None = None,
    expected_semantics: dict[str, object] | None = None,
    expected_physical_facts: dict[str, dict[str, Any]] | None = None,
    deep_validate_artifacts: bool = True,
) -> InventoryReportResult:
    manifest_authorized = authorize_existing_path(
        bundle,
        bundle / _MANIFEST_NAME,
        expected_kind="file",
        policy=PathPolicy(),
    )
    manifest_path = manifest_authorized.path
    if expected_physical_facts is not None and (
        set(expected_physical_facts)
        != {
            _HTML_NAME,
            _ASSET_CSV_NAME,
            _FILE_CSV_NAME,
            _FORMAT_CSV_NAME,
            _DUPLICATE_CSV_NAME,
            _ANOMALY_CSV_NAME,
            _JSONL_NAME,
            _MANIFEST_NAME,
        }
        or _file_facts(manifest_path) != expected_physical_facts[_MANIFEST_NAME]
    ):
        raise MibaoError("MB-RPT-0005", "Published report manifest bytes changed after validation")
    try:
        manifest = _strict_json_loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise MibaoError("MB-RPT-0005", "Existing report manifest is invalid") from exc
    if not isinstance(manifest, dict) or set(manifest) != _MANIFEST_KEYS:
        raise MibaoError("MB-RPT-0005", "Existing report manifest shape is invalid")
    _validate_public_schema(manifest, "inventory-report-receipt.schema.json")
    expected_identity = expected_report_id or bundle.name
    if manifest.get("schemaVersion") != 2 or manifest.get("reportId") != expected_identity:
        raise MibaoError("MB-RPT-0005", "Existing report identity is inconsistent")
    if expected_semantics is not None and any(
        manifest.get(key) != value for key, value in expected_semantics.items()
    ):
        raise MibaoError("MB-RPT-0005", "Existing report semantics do not match the snapshot")
    files = manifest.get("files")
    expected_files = {
        _HTML_NAME,
        _ASSET_CSV_NAME,
        _FILE_CSV_NAME,
        _FORMAT_CSV_NAME,
        _DUPLICATE_CSV_NAME,
        _ANOMALY_CSV_NAME,
        _JSONL_NAME,
    }
    if not isinstance(files, dict) or set(files) != expected_files:
        raise MibaoError("MB-RPT-0005", "Existing report file facts are missing")
    for name, expected in files.items():
        authorized = authorize_existing_path(
            bundle,
            bundle / str(name),
            expected_kind="file",
            policy=PathPolicy(),
        )
        actual_fact = _file_facts(authorized.path)
        if (
            not isinstance(expected, dict)
            or set(expected) != {"bytes", "sha256"}
            or actual_fact != expected
            or (
                expected_physical_facts is not None
                and actual_fact != expected_physical_facts[str(name)]
            )
        ):
            raise MibaoError("MB-RPT-0005", "Existing report artifact hash is inconsistent")
    counts = manifest.get("counts")
    assurance = manifest.get("duplicateAssurance")
    reconciliation = manifest.get("reconciliation")
    claims = manifest.get("claims")
    assurance_token = manifest.get("assuranceToken")
    scan_completeness = manifest.get("scanCompleteness")
    if (
        not isinstance(counts, dict)
        or set(counts) != _MANIFEST_COUNT_KEYS
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in counts.values()
        )
        or counts.get("currentExactDuplicateGroupCount") != 0
        or assurance
        not in {"strict_full_verified_as_of_token", "historical_last_full_verified_only"}
        or not isinstance(reconciliation, dict)
        or set(reconciliation) != _RECONCILIATION_KEYS
        or reconciliation.get("passed") is not True
        or any(
            isinstance(value, bool) or not isinstance(value, int)
            for key, value in reconciliation.items()
            if key != "passed"
        )
        or any(value != 0 for key, value in reconciliation.items() if key.endswith("Residual"))
        or reconciliation.get("jsonlRecordCount") != reconciliation.get("jsonlExpectedRecordCount")
        or not isinstance(claims, dict)
        or set(claims) != _CLAIM_KEYS
        or any(value is not False for value in claims.values())
    ):
        raise MibaoError("MB-RPT-0005", "Existing report counts are invalid")
    if assurance == "strict_full_verified_as_of_token":
        if (
            not isinstance(assurance_token, dict)
            or not isinstance(scan_completeness, dict)
            or scan_completeness.get("complete") is not True
            or scan_completeness.get("pending_reasons") != []
            or assurance_token.get("project_id") != manifest.get("projectId")
            or assurance_token.get("snapshot_sha256") != manifest.get("hashAssuranceSnapshotSha256")
            or assurance_token.get("scan_state_sha256") != scan_completeness.get("sha256")
            or assurance_token.get("exact_duplicate_group_count")
            != counts.get("strictAsOfExactDuplicateGroupCount")
            or counts.get("strictAsOfExactDuplicateGroupCount")
            != counts.get("historicalExactDuplicateGroupCount")
        ):
            raise MibaoError("MB-RPT-0005", "Existing report assurance facts are inconsistent")
    elif assurance_token is not None or counts.get("strictAsOfExactDuplicateGroupCount") != 0:
        raise MibaoError("MB-RPT-0005", "Historical report contains strict assurance facts")
    if deep_validate_artifacts:
        _verify_csv(bundle / _ASSET_CSV_NAME, int(reconciliation["assetCsvDataRows"]))
        _verify_csv(bundle / _FILE_CSV_NAME, int(reconciliation["fileInstanceCsvDataRows"]))
        _verify_csv(bundle / _FORMAT_CSV_NAME, int(reconciliation["formatCsvDataRows"]))
        _verify_csv(bundle / _DUPLICATE_CSV_NAME, int(reconciliation["duplicateCsvDataRows"]))
        _verify_csv(bundle / _ANOMALY_CSV_NAME, int(reconciliation["anomalyCsvDataRows"]))
        _verify_jsonl(
            bundle / _JSONL_NAME,
            {
                "report_header": 1,
                "asset": int(reconciliation["jsonlAssetRecords"]),
                "file_instance": int(reconciliation["jsonlFileInstanceRecords"]),
                "format_summary": int(reconciliation["jsonlFormatSummaryRecords"]),
                "duplicate_group": int(reconciliation["jsonlDuplicateGroupRecords"]),
                "duplicate_member": int(reconciliation["jsonlDuplicateMemberRecords"]),
                "anomaly": int(reconciliation["jsonlAnomalyRecords"]),
                "report_summary": 1,
            },
            expected_report_id=str(manifest["reportId"]),
            expected_project_id=str(manifest["projectId"]),
            expected_snapshot_sha256=str(manifest["snapshotSha256"]),
            expected_duplicate_assurance=str(manifest["duplicateAssurance"]),
        )
        _verify_html(bundle / _HTML_NAME)
    return InventoryReportResult(
        project_id=str(manifest["projectId"]),
        report_id=str(manifest["reportId"]),
        bundle_dir=bundle,
        html_path=bundle / _HTML_NAME,
        asset_csv_path=bundle / _ASSET_CSV_NAME,
        file_csv_path=bundle / _FILE_CSV_NAME,
        format_csv_path=bundle / _FORMAT_CSV_NAME,
        duplicate_csv_path=bundle / _DUPLICATE_CSV_NAME,
        anomaly_csv_path=bundle / _ANOMALY_CSV_NAME,
        jsonl_path=bundle / _JSONL_NAME,
        receipt_path=manifest_path,
        asset_count=int(counts["assetCount"]),
        file_instance_count=int(counts["fileInstanceCount"]),
        current_exact_duplicate_group_count=int(counts["currentExactDuplicateGroupCount"]),
        strict_as_of_exact_duplicate_group_count=int(counts["strictAsOfExactDuplicateGroupCount"]),
        historical_exact_duplicate_group_count=int(counts["historicalExactDuplicateGroupCount"]),
        anomaly_count=int(counts["anomalyCount"]),
        duplicate_assurance=assurance,
        reused_existing=reused,
    )


def generate_inventory_report(
    project_root: Path,
    *,
    assurance_token: HashAssuranceToken | None = None,
    policy: InventoryReportPolicy | None = None,
    _test_hook: _TestHook | None = None,
) -> InventoryReportResult:
    """Generate one immutable, reconciled report generation from a query-only snapshot."""

    active_policy = policy or InventoryReportPolicy()
    project = open_project(project_root)
    _validate_plugin_isolation(project.root)
    owner_nonce = uuid.uuid4().hex
    stage: Path | None = None
    inventory_root: Path | None = None
    with ProjectLock(project.root):
        connection = _connect_readonly(project.database_path)
        connection_closed = False
        try:
            if connection.execute("PRAGMA query_only").fetchone() != (1,):
                raise MibaoError("MB-RPT-0002", "SQLite query_only mode is not active")
            try:
                connection.execute("CREATE TEMP TABLE mibao_report_write_probe(value INTEGER)")
            except sqlite3.OperationalError:
                pass
            else:
                raise MibaoError("MB-RPT-0002", "SQLite query_only write probe unexpectedly passed")
            audit_schema(
                connection,
                expected_project_id=project.project_id,
                expected_privacy_mode=project.privacy_mode,
            )
            connection.execute("BEGIN")
            summary = _summary(connection, project.project_id)
            _validate_summary(summary)
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            if integrity != ("ok",) or foreign_keys:
                raise MibaoError("MB-RPT-0002", "SQLite snapshot integrity check failed")
            if _test_hook is not None:
                _test_hook("snapshot_opened")
            scan_state = compute_scan_completeness_snapshot(connection, project.project_id)
            hash_snapshot = compute_hash_assurance_snapshot(connection, project.project_id)
            if assurance_token is None:
                duplicate_assurance = "historical_last_full_verified_only"
                current_duplicate_groups = 0
                strict_as_of_duplicate_groups = 0
            else:
                try:
                    issued_at = datetime.fromisoformat(
                        assurance_token.issued_at.replace("Z", "+00:00")
                    )
                except ValueError as exc:
                    raise MibaoError("MB-RPT-0006", "Assurance token timestamp is invalid") from exc
                token_age_seconds = (datetime.now(UTC) - issued_at).total_seconds()
                if (
                    not consume_issued_hash_assurance_token(assurance_token)
                    or not scan_state.complete
                    or not 0 <= token_age_seconds <= active_policy.max_assurance_age_seconds
                    or assurance_token.project_id != project.project_id
                    or assurance_token.source_root_ids != hash_snapshot.source_root_ids
                    or assurance_token.present_scan_candidate_count
                    != hash_snapshot.present_scan_candidate_count
                    or assurance_token.present_file_instance_count
                    != hash_snapshot.present_file_instance_count
                    or assurance_token.current_full_verified_count
                    != hash_snapshot.present_file_instance_count
                    or assurance_token.exact_duplicate_group_count
                    != hash_snapshot.exact_duplicate_group_count
                    or assurance_token.duplicate_member_count
                    != hash_snapshot.duplicate_member_count
                    or assurance_token.duplicate_extra_copy_count
                    != hash_snapshot.duplicate_extra_copy_count
                    or assurance_token.scan_state_sha256 != scan_state.sha256
                    or hash_snapshot.scan_state_sha256 != scan_state.sha256
                    or assurance_token.snapshot_sha256 != hash_snapshot.sha256
                ):
                    raise MibaoError(
                        "MB-RPT-0006",
                        "Current duplicate assurance token does not match the report snapshot",
                    )
                duplicate_assurance = "strict_full_verified_as_of_token"
                current_duplicate_groups = 0
                strict_as_of_duplicate_groups = hash_snapshot.exact_duplicate_group_count
            if _test_hook is not None:
                _test_hook("assurance_validated")

            migration_receipts = [
                {
                    "version": int(row[0]),
                    "migration_id": str(row[1]),
                    "checksum": str(row[2]),
                }
                for row in connection.execute(
                    "SELECT version, migration_id, checksum FROM schema_migrations ORDER BY version"
                )
            ]
            source_states = [
                {"source_root_id": str(row[0]), "state": str(row[1])}
                for row in connection.execute(
                    "SELECT source_root_id, state FROM source_roots WHERE project_id=? "
                    "ORDER BY source_root_id",
                    (project.project_id,),
                )
            ]
            generated_at = _timestamp()
            snapshot_digest = hashlib.sha256()
            snapshot_digest.update(
                _json_text(
                    {
                        "generator": _GENERATOR_VERSION,
                        "policy": _REPORT_POLICY_VERSION,
                        "project_id": project.project_id,
                        "display_name": project.display_name,
                        "privacy_mode": project.privacy_mode,
                        "generated_at": generated_at,
                        "summary": summary,
                        "source_states": source_states,
                        "scan_completeness": scan_state.as_dict(),
                        "migration_receipts": migration_receipts,
                        "duplicate_assurance": duplicate_assurance,
                        "assurance_token": assurance_token.as_dict()
                        if assurance_token is not None
                        else None,
                        "hash_snapshot_sha256": hash_snapshot.sha256,
                    }
                ).encode()
            )
            format_buckets: dict[tuple[str, str, str, str], dict[str, int]] = {}
            anomaly_count = sum(item["state"] != "active" for item in source_states) + len(
                scan_state.pending_reasons
            )
            asset_rows = 0
            for raw in _iter_rows(
                connection,
                _ASSET_SQL,
                (project.project_id, project.project_id),
                active_policy.batch_size,
            ):
                asset = _asset_from_row(raw)
                asset_rows += 1
                anomaly_count += len(asset.anomalies)
                if asset_rows > active_policy.max_rows:
                    raise MibaoError("MB-RPT-0001", "Asset report row limit exceeded")
                snapshot_digest.update(_json_text(asset.data()).encode())
                key = (
                    asset.format_assurance,
                    asset.format_id or "<unverified>",
                    asset.format_mime or "",
                    asset.format_media_kind or asset.media_kind,
                )
                bucket = format_buckets.setdefault(
                    key,
                    {
                        "asset_count": 0,
                        "active_asset_count": 0,
                        "present_file_instance_count": 0,
                        "unique_asset_bytes": 0,
                        "physical_present_bytes": 0,
                    },
                )
                bucket["asset_count"] += 1
                bucket["active_asset_count"] += asset.state == "active"
                bucket["present_file_instance_count"] += asset.present_instance_count
                bucket["unique_asset_bytes"] += asset.byte_size
                bucket["physical_present_bytes"] += asset.byte_size * asset.present_instance_count
                if len(format_buckets) > active_policy.max_distinct_formats:
                    raise MibaoError("MB-RPT-0001", "Distinct format-bucket limit exceeded")
            if _test_hook is not None:
                _test_hook("asset_prepass_completed")
            file_rows = 0
            for raw in _iter_rows(
                connection,
                _FILE_SQL,
                (project.project_id,),
                active_policy.batch_size,
            ):
                file = _file_from_row(raw)
                file_rows += 1
                anomaly_count += len(file.anomalies)
                if file_rows > active_policy.max_rows:
                    raise MibaoError("MB-RPT-0001", "FileInstance report row limit exceeded")
                snapshot_digest.update(_json_text(file.data()).encode())
            if _test_hook is not None:
                _test_hook("file_prepass_completed")
            summary["anomaly_count"] = anomaly_count
            snapshot_digest.update(_json_text({"anomaly_count": anomaly_count}).encode())
            duplicate_rows = duplicate_group_rows = 0
            last_duplicate_asset = ""
            for raw in _iter_rows(
                connection,
                _DUPLICATE_SQL,
                (project.project_id,),
                active_policy.batch_size,
            ):
                duplicate_rows += 1
                asset_id = str(raw[0])
                if asset_id != last_duplicate_asset:
                    duplicate_group_rows += 1
                    last_duplicate_asset = asset_id
                snapshot_digest.update(_json_text(list(raw)).encode())
            if _test_hook is not None:
                _test_hook("duplicate_prepass_completed")
            if asset_rows != summary["asset_total"] or file_rows != summary["file_total"]:
                raise MibaoError("MB-RPT-0003", "Snapshot row counts do not reconcile")
            if sum(item["asset_count"] for item in format_buckets.values()) != asset_rows:
                raise MibaoError("MB-RPT-0003", "Format buckets do not cover all Assets")
            if (
                sum(item["present_file_instance_count"] for item in format_buckets.values())
                != summary["file_present"]
                or sum(item["physical_present_bytes"] for item in format_buckets.values())
                != summary["physical_present_bytes"]
                or sum(item["unique_asset_bytes"] for item in format_buckets.values())
                != summary["unique_asset_bytes"]
            ):
                raise MibaoError("MB-RPT-0003", "Format byte/path denominators do not reconcile")
            if duplicate_rows != hash_snapshot.duplicate_member_count:
                raise MibaoError("MB-RPT-0003", "Duplicate member rows do not reconcile")
            if duplicate_group_rows != hash_snapshot.exact_duplicate_group_count:
                raise MibaoError("MB-RPT-0003", "Duplicate group rows do not reconcile")
            snapshot_digest.update(last_duplicate_asset.encode())
            snapshot_sha256 = snapshot_digest.hexdigest()
            report_id = "RPT-" + snapshot_sha256[:32]
            expected_reconciliation = _expected_reconciliation(
                summary,
                format_record_count=len(format_buckets),
                duplicate_group_count=hash_snapshot.exact_duplicate_group_count,
                duplicate_member_count=hash_snapshot.duplicate_member_count,
                anomaly_count=anomaly_count,
            )
            expected_semantics: dict[str, object] = {
                "schemaVersion": 2,
                "reportId": report_id,
                "projectId": project.project_id,
                "generatorVersion": _GENERATOR_VERSION,
                "policyVersion": _REPORT_POLICY_VERSION,
                "generatedAt": generated_at,
                "snapshotSha256": snapshot_sha256,
                "hashAssuranceSnapshotSha256": hash_snapshot.sha256,
                "duplicateAssurance": duplicate_assurance,
                "assuranceToken": assurance_token.as_dict()
                if assurance_token is not None
                else None,
                "sqlite": {
                    "queryOnly": True,
                    "integrityCheck": "ok",
                    "foreignKeyViolationCount": 0,
                    "userVersion": project.schema_version,
                    "sqliteVersion": sqlite3.sqlite_version,
                    "migrationReceipts": migration_receipts,
                },
                "sourceStates": source_states,
                "scanCompleteness": scan_state.as_dict(),
                "sqlProvenance": _query_provenance(),
                "counts": {
                    "assetCount": summary["asset_total"],
                    "fileInstanceCount": summary["file_total"],
                    "currentExactDuplicateGroupCount": current_duplicate_groups,
                    "strictAsOfExactDuplicateGroupCount": strict_as_of_duplicate_groups,
                    "historicalExactDuplicateGroupCount": hash_snapshot.exact_duplicate_group_count,
                    "historicalDuplicateMemberCount": hash_snapshot.duplicate_member_count,
                    "anomalyCount": anomaly_count,
                },
                "reconciliation": expected_reconciliation,
                "claims": {
                    "sourceBytesModified": False,
                    "databaseModified": False,
                    "activeHostModified": False,
                    "submitReady": False,
                    "officiallyListed": False,
                },
                "cannotProve": list(_CANNOT_PROVE),
            }

            inventory_root = _ensure_owned_directory(project.root, _REPORT_ROOT)
            final = inventory_root / report_id
            if final.exists() or final.is_symlink():
                raise MibaoError(
                    "MB-RPT-0005",
                    "Inventory generation identity already exists; refusing reuse or overwrite",
                )
            stage = inventory_root / f".partial-{os.getpid()}-{owner_nonce}"
            stage.mkdir()
            (stage / _STAGE_SENTINEL).write_text(
                _json_text({"owner_nonce": owner_nonce}) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            budget = _OutputBudget(active_policy.max_total_output_bytes)
            if _test_hook is not None:
                _test_hook("stage_created")
            paths = {
                _HTML_NAME: stage / _HTML_NAME,
                _ASSET_CSV_NAME: stage / _ASSET_CSV_NAME,
                _FILE_CSV_NAME: stage / _FILE_CSV_NAME,
                _FORMAT_CSV_NAME: stage / _FORMAT_CSV_NAME,
                _DUPLICATE_CSV_NAME: stage / _DUPLICATE_CSV_NAME,
                _ANOMALY_CSV_NAME: stage / _ANOMALY_CSV_NAME,
                _JSONL_NAME: stage / _JSONL_NAME,
            }
            with ExitStack() as stack:
                html_sink = stack.enter_context(_TextSink(paths[_HTML_NAME], budget))
                asset_sink = stack.enter_context(
                    _TextSink(paths[_ASSET_CSV_NAME], budget, bom=True)
                )
                file_sink = stack.enter_context(_TextSink(paths[_FILE_CSV_NAME], budget, bom=True))
                format_sink = stack.enter_context(
                    _TextSink(paths[_FORMAT_CSV_NAME], budget, bom=True)
                )
                duplicate_sink = stack.enter_context(
                    _TextSink(paths[_DUPLICATE_CSV_NAME], budget, bom=True)
                )
                anomaly_sink = stack.enter_context(
                    _TextSink(paths[_ANOMALY_CSV_NAME], budget, bom=True)
                )
                jsonl_sink = stack.enter_context(_TextSink(paths[_JSONL_NAME], budget))
                asset_writer = csv.writer(asset_sink, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
                file_writer = csv.writer(file_sink, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
                format_writer = csv.writer(
                    format_sink, quoting=csv.QUOTE_ALL, lineterminator="\r\n"
                )
                duplicate_writer = csv.writer(
                    duplicate_sink, quoting=csv.QUOTE_ALL, lineterminator="\r\n"
                )
                anomaly_writer = csv.writer(
                    anomaly_sink, quoting=csv.QUOTE_ALL, lineterminator="\r\n"
                )
                asset_header = [
                    "asset_id",
                    "sha256",
                    "media_kind",
                    "byte_size",
                    "capture_time_ms",
                    "state",
                    "format_id",
                    "format_mime",
                    "format_media_kind",
                    "format_assurance",
                    "file_instance_count",
                    "present_instance_count",
                    "missing_instance_count",
                    "changed_instance_count",
                    "anomaly_codes",
                    "created_at",
                    "updated_at",
                ]
                file_header = [
                    "file_instance_id",
                    "asset_id",
                    "source_root_id",
                    "relative_path",
                    "file_size",
                    "modified_time_ms",
                    "file_state",
                    "asset_state",
                    "source_state",
                    "observed_format_id",
                    "probe_status",
                    "observation_state",
                    "metadata_surface",
                    "metadata_production_verified",
                    "hash_validation_mode",
                    "anomaly_codes",
                ]
                format_header = [
                    "format_assurance",
                    "format_id",
                    "mime_type",
                    "media_kind",
                    "asset_count",
                    "active_asset_count",
                    "present_file_instance_count",
                    "unique_asset_bytes",
                    "physical_present_bytes",
                ]
                duplicate_header = [
                    "duplicate_scope",
                    "duplicate_assurance",
                    "asset_id",
                    "sha256",
                    "member_count",
                    "extra_copy_count",
                    "potential_reclaimable_bytes",
                    "file_instance_id",
                    "source_root_id",
                    "relative_path",
                    "file_size",
                    "modified_time_ms",
                ]
                anomaly_header = [
                    "anomaly_id",
                    "code",
                    "severity",
                    "subject_type",
                    "subject_id",
                    "source_root_id",
                    "relative_path",
                    "summary_zh",
                    "action_zh",
                ]
                for writer, header in (
                    (asset_writer, asset_header),
                    (file_writer, file_header),
                    (format_writer, format_header),
                    (duplicate_writer, duplicate_header),
                    (anomaly_writer, anomaly_header),
                ):
                    writer.writerow(header)
                title = f"秘宝盘点报告 | {project.display_name}"
                _html_header(html_sink, title=title, summary=summary)
                sequence = 1
                _json_record(
                    jsonl_sink,
                    report_id=report_id,
                    project_id=project.project_id,
                    snapshot_sha256=snapshot_sha256,
                    sequence=sequence,
                    record_type="report_header",
                    data={
                        "generator_version": _GENERATOR_VERSION,
                        "duplicate_assurance": duplicate_assurance,
                    },
                )
                sequence += 1
                html_sink.write(
                    "<h2>格式统计</h2><table><thead><tr><th>保证</th><th>格式</th><th>Asset</th><th>字节</th></tr></thead><tbody>"
                )
                format_csv_rows = jsonl_format_records = 0
                for key in sorted(format_buckets):
                    assurance, format_id, mime_type, media_kind = key
                    bucket = format_buckets[key]
                    data = {
                        "format_assurance": assurance,
                        "format_id": format_id,
                        "mime_type": mime_type,
                        "media_kind": media_kind,
                        **bucket,
                    }
                    format_writer.writerow(
                        _csv_row(
                            [
                                assurance,
                                format_id,
                                mime_type,
                                media_kind,
                                bucket["asset_count"],
                                bucket["active_asset_count"],
                                bucket["present_file_instance_count"],
                                bucket["unique_asset_bytes"],
                                bucket["physical_present_bytes"],
                            ],
                            active_policy.max_cell_chars,
                        )
                    )
                    format_csv_rows += 1
                    _json_record(
                        jsonl_sink,
                        report_id=report_id,
                        project_id=project.project_id,
                        snapshot_sha256=snapshot_sha256,
                        sequence=sequence,
                        record_type="format_summary",
                        data=data,
                    )
                    jsonl_format_records += 1
                    sequence += 1
                    html_sink.write(
                        f"<tr><td>{escape_html_text(assurance)}</td><td>{escape_html_text(format_id)}</td>"
                        f"<td>{bucket['asset_count']}</td><td>{bucket['unique_asset_bytes']}</td></tr>"
                    )
                html_sink.write(
                    "</tbody></table><h2>重复候选</h2><table><thead><tr><th>范围</th><th>SHA-256</th><th>成员</th><th>路径</th></tr></thead><tbody>"
                )
                duplicate_csv_rows = duplicate_group_records = duplicate_member_records = 0
                seen_group = ""
                duplicate_scope = (
                    "strict_as_of_token"
                    if duplicate_assurance == "strict_full_verified_as_of_token"
                    else "historical_candidate"
                )
                for raw in _iter_rows(
                    connection,
                    _DUPLICATE_SQL,
                    (project.project_id,),
                    active_policy.batch_size,
                ):
                    (
                        asset_id,
                        sha256,
                        _byte_size,
                        member_count,
                        file_id,
                        source_id,
                        relative_path,
                        file_size,
                        modified_ms,
                    ) = raw
                    extra_count = int(member_count) - 1
                    reclaimable = 0
                    duplicate_writer.writerow(
                        _csv_row(
                            [
                                duplicate_scope,
                                duplicate_assurance,
                                asset_id,
                                sha256,
                                int(member_count),
                                extra_count,
                                reclaimable,
                                file_id,
                                source_id,
                                relative_path,
                                int(file_size),
                                int(modified_ms),
                            ],
                            active_policy.max_cell_chars,
                        )
                    )
                    duplicate_csv_rows += 1
                    if str(asset_id) != seen_group:
                        _json_record(
                            jsonl_sink,
                            report_id=report_id,
                            project_id=project.project_id,
                            snapshot_sha256=snapshot_sha256,
                            sequence=sequence,
                            record_type="duplicate_group",
                            data={
                                "duplicate_scope": duplicate_scope,
                                "duplicate_assurance": duplicate_assurance,
                                "asset_id": str(asset_id),
                                "sha256": str(sha256),
                                "member_count": int(member_count),
                                "extra_copy_count": extra_count,
                                "potential_reclaimable_bytes": reclaimable,
                            },
                        )
                        sequence += 1
                        duplicate_group_records += 1
                        seen_group = str(asset_id)
                    _json_record(
                        jsonl_sink,
                        report_id=report_id,
                        project_id=project.project_id,
                        snapshot_sha256=snapshot_sha256,
                        sequence=sequence,
                        record_type="duplicate_member",
                        data={
                            "asset_id": str(asset_id),
                            "file_instance_id": str(file_id),
                            "source_root_id": str(source_id),
                            "relative_path": str(relative_path),
                            "file_size": int(file_size),
                            "modified_time_ms": int(modified_ms),
                        },
                    )
                    sequence += 1
                    duplicate_member_records += 1
                    if duplicate_csv_rows <= active_policy.html_preview_rows:
                        html_sink.write(
                            f"<tr><td>{escape_html_text(duplicate_scope)}</td>"
                            f"<td><code>{escape_html_text(sha256)}</code></td>"
                            f"<td>{int(member_count)}</td>"
                            f"<td>{escape_html_text(relative_path)}</td></tr>"
                        )
                html_sink.write(
                    "</tbody></table><h2>唯一 Asset 预览</h2><table><thead><tr>"
                    "<th>Asset</th><th>SHA-256</th><th>状态</th>"
                    "<th>格式保证</th></tr></thead><tbody>"
                )
                asset_csv_rows = jsonl_asset_records = 0
                for raw in _iter_rows(
                    connection,
                    _ASSET_SQL,
                    (project.project_id, project.project_id),
                    active_policy.batch_size,
                ):
                    asset = _asset_from_row(raw)
                    data = asset.data()
                    asset_writer.writerow(
                        _csv_row(
                            [data[key] if data[key] is not None else "" for key in asset_header],
                            active_policy.max_cell_chars,
                        )
                    )
                    asset_csv_rows += 1
                    _json_record(
                        jsonl_sink,
                        report_id=report_id,
                        project_id=project.project_id,
                        snapshot_sha256=snapshot_sha256,
                        sequence=sequence,
                        record_type="asset",
                        data=data,
                    )
                    sequence += 1
                    jsonl_asset_records += 1
                    if asset_csv_rows <= active_policy.html_preview_rows:
                        html_sink.write(
                            f"<tr><td><code>{escape_html_text(asset.asset_id)}</code></td><td><code>{escape_html_text(asset.sha256)}</code></td><td>{escape_html_text(asset.state)}</td><td>{escape_html_text(asset.format_assurance)}</td></tr>"
                        )
                html_sink.write(
                    "</tbody></table><h2>文件路径预览</h2><table><thead><tr><th>相对路径</th><th>状态</th><th>观察格式</th><th>异常</th></tr></thead><tbody>"
                )
                file_csv_rows = jsonl_file_records = 0
                anomaly_csv_rows = jsonl_anomaly_records = 0
                for reason in scan_state.pending_reasons:
                    reason_subject, _separator, _detail = reason.partition(":")
                    source_id = reason_subject if reason_subject.startswith("SRC-") else ""
                    subject_id = source_id or "project-scan-state"
                    code = "scan_recovery_pending"
                    anomaly_id = (
                        "ANOM-"
                        + hashlib.sha256(f"{subject_id}\0{code}\0{reason}".encode()).hexdigest()[
                            :32
                        ]
                    )
                    anomaly_data = {
                        "anomaly_id": anomaly_id,
                        "code": code,
                        "severity": "warning",
                        "subject_type": "source_root",
                        "subject_id": subject_id,
                        "source_root_id": source_id,
                        "relative_path": "",
                        "summary_zh": f"扫描恢复尚未闭合: {reason}",
                        "action_zh": "先恢复并完整扫描源盘; 当前报告只可作为历史/部分视图。",
                    }
                    anomaly_writer.writerow(
                        _csv_row(
                            [anomaly_data[key] for key in anomaly_header],
                            active_policy.max_cell_chars,
                        )
                    )
                    anomaly_csv_rows += 1
                    _json_record(
                        jsonl_sink,
                        report_id=report_id,
                        project_id=project.project_id,
                        snapshot_sha256=snapshot_sha256,
                        sequence=sequence,
                        record_type="anomaly",
                        data=anomaly_data,
                    )
                    sequence += 1
                    jsonl_anomaly_records += 1
                for source_state in source_states:
                    if source_state["state"] == "active":
                        continue
                    source_id = source_state["source_root_id"]
                    code = f"source_{source_state['state']}"
                    anomaly_id = (
                        "ANOM-" + hashlib.sha256(f"{source_id}\0{code}".encode()).hexdigest()[:32]
                    )
                    anomaly_data = {
                        "anomaly_id": anomaly_id,
                        "code": code,
                        "severity": "warning",
                        "subject_type": "source_root",
                        "subject_id": source_id,
                        "source_root_id": source_id,
                        "relative_path": "",
                        "summary_zh": f"源盘状态异常: {code}",
                        "action_zh": "恢复或复核源盘后重新扫描; 不要把离线误报为删除。",
                    }
                    anomaly_writer.writerow(
                        _csv_row(
                            [anomaly_data[key] for key in anomaly_header],
                            active_policy.max_cell_chars,
                        )
                    )
                    anomaly_csv_rows += 1
                    _json_record(
                        jsonl_sink,
                        report_id=report_id,
                        project_id=project.project_id,
                        snapshot_sha256=snapshot_sha256,
                        sequence=sequence,
                        record_type="anomaly",
                        data=anomaly_data,
                    )
                    sequence += 1
                    jsonl_anomaly_records += 1
                for raw in _iter_rows(
                    connection,
                    _ASSET_SQL,
                    (project.project_id, project.project_id),
                    active_policy.batch_size,
                ):
                    asset = _asset_from_row(raw)
                    for code in asset.anomalies:
                        anomaly_id = (
                            "ANOM-"
                            + hashlib.sha256(f"{asset.asset_id}\0{code}".encode()).hexdigest()[:32]
                        )
                        anomaly_data = {
                            "anomaly_id": anomaly_id,
                            "code": code,
                            "severity": "warning",
                            "subject_type": "asset",
                            "subject_id": asset.asset_id,
                            "source_root_id": "",
                            "relative_path": "",
                            "summary_zh": f"资产盘点异常: {code}",
                            "action_zh": "复核路径与证据后再处理; 不要自动删除资产。",
                        }
                        anomaly_writer.writerow(
                            _csv_row(
                                [anomaly_data[key] for key in anomaly_header],
                                active_policy.max_cell_chars,
                            )
                        )
                        anomaly_csv_rows += 1
                        _json_record(
                            jsonl_sink,
                            report_id=report_id,
                            project_id=project.project_id,
                            snapshot_sha256=snapshot_sha256,
                            sequence=sequence,
                            record_type="anomaly",
                            data=anomaly_data,
                        )
                        sequence += 1
                        jsonl_anomaly_records += 1
                for raw in _iter_rows(
                    connection, _FILE_SQL, (project.project_id,), active_policy.batch_size
                ):
                    file = _file_from_row(raw)
                    data = file.data()
                    file_writer.writerow(
                        _csv_row(
                            [data[key] if data[key] is not None else "" for key in file_header],
                            active_policy.max_cell_chars,
                        )
                    )
                    file_csv_rows += 1
                    _json_record(
                        jsonl_sink,
                        report_id=report_id,
                        project_id=project.project_id,
                        snapshot_sha256=snapshot_sha256,
                        sequence=sequence,
                        record_type="file_instance",
                        data=data,
                    )
                    sequence += 1
                    jsonl_file_records += 1
                    for code in file.anomalies:
                        anomaly_id = (
                            "ANOM-"
                            + hashlib.sha256(
                                f"{file.file_instance_id}\0{code}".encode()
                            ).hexdigest()[:32]
                        )
                        anomaly_data = {
                            "anomaly_id": anomaly_id,
                            "code": code,
                            "severity": "warning",
                            "subject_type": "file_instance",
                            "subject_id": file.file_instance_id,
                            "source_root_id": file.source_root_id,
                            "relative_path": file.relative_path,
                            "summary_zh": f"文件盘点异常: {code}",
                            "action_zh": "复核源状态与对应证据后再处理; 不要自动删除原件。",
                        }
                        anomaly_writer.writerow(
                            _csv_row(
                                [anomaly_data[key] for key in anomaly_header],
                                active_policy.max_cell_chars,
                            )
                        )
                        anomaly_csv_rows += 1
                        _json_record(
                            jsonl_sink,
                            report_id=report_id,
                            project_id=project.project_id,
                            snapshot_sha256=snapshot_sha256,
                            sequence=sequence,
                            record_type="anomaly",
                            data=anomaly_data,
                        )
                        sequence += 1
                        jsonl_anomaly_records += 1
                    if file_csv_rows <= active_policy.html_preview_rows:
                        observed_format = escape_html_text(
                            file.observed_format_id or "<unverified>"
                        )
                        html_sink.write(
                            f"<tr><td>{escape_html_text(file.relative_path)}</td>"
                            f"<td>{escape_html_text(file.file_state)}</td>"
                            f"<td>{observed_format}</td>"
                            f'<td class="warn">{escape_html_text(",".join(file.anomalies))}'
                            "</td></tr>"
                        )
                html_sink.write(
                    '</tbody></table><p class="muted">完整记录见同目录 CSV 与 JSONL; '
                    "CSV 为 spreadsheet-safe 展示, JSONL 保留原始相对路径。"
                    "</p></body></html>"
                )
                reconciliation = {
                    "databaseAssetCount": summary["asset_total"],
                    "databaseFileInstanceCount": summary["file_total"],
                    "assetCsvDataRows": asset_csv_rows,
                    "fileInstanceCsvDataRows": file_csv_rows,
                    "formatCsvDataRows": format_csv_rows,
                    "duplicateCsvDataRows": duplicate_csv_rows,
                    "anomalyCsvDataRows": anomaly_csv_rows,
                    "jsonlAssetRecords": jsonl_asset_records,
                    "jsonlFileInstanceRecords": jsonl_file_records,
                    "jsonlFormatSummaryRecords": jsonl_format_records,
                    "jsonlDuplicateGroupRecords": duplicate_group_records,
                    "jsonlDuplicateMemberRecords": duplicate_member_records,
                    "jsonlAnomalyRecords": jsonl_anomaly_records,
                    "jsonlRecordCount": sequence,
                    "jsonlExpectedRecordCount": 2
                    + jsonl_asset_records
                    + jsonl_file_records
                    + jsonl_format_records
                    + duplicate_group_records
                    + duplicate_member_records
                    + jsonl_anomaly_records,
                    "assetResidual": summary["asset_total"] - asset_csv_rows,
                    "fileInstanceResidual": summary["file_total"] - file_csv_rows,
                    "formatAssetResidual": summary["asset_total"]
                    - sum(item["asset_count"] for item in format_buckets.values()),
                    "formatPresentFileResidual": summary["file_present"]
                    - sum(item["present_file_instance_count"] for item in format_buckets.values()),
                    "formatPhysicalBytesResidual": summary["physical_present_bytes"]
                    - sum(item["physical_present_bytes"] for item in format_buckets.values()),
                    "formatSummaryResidual": format_csv_rows - jsonl_format_records,
                    "duplicateGroupResidual": hash_snapshot.exact_duplicate_group_count
                    - duplicate_group_records,
                    "duplicateMemberResidual": hash_snapshot.duplicate_member_count
                    - duplicate_csv_rows,
                    "anomalyResidual": anomaly_count - anomaly_csv_rows,
                }
                reconciliation["jsonlRecordResidual"] = (
                    reconciliation["jsonlRecordCount"] - reconciliation["jsonlExpectedRecordCount"]
                )
                reconciliation["passed"] = all(
                    value == 0 for key, value in reconciliation.items() if key.endswith("Residual")
                )
                if (
                    reconciliation["passed"] is not True
                    or reconciliation != expected_reconciliation
                ):
                    raise MibaoError("MB-RPT-0003", "Rendered artifact counts do not reconcile")
                _json_record(
                    jsonl_sink,
                    report_id=report_id,
                    project_id=project.project_id,
                    snapshot_sha256=snapshot_sha256,
                    sequence=sequence,
                    record_type="report_summary",
                    data={
                        "counts": summary,
                        "reconciliation": reconciliation,
                        "duplicate_assurance": duplicate_assurance,
                    },
                )
            if _test_hook is not None:
                _test_hook("after_render")
            connection.rollback()
            connection.close()
            connection_closed = True
            files = {name: _file_facts(path) for name, path in paths.items()}
            manifest = {
                **expected_semantics,
                "files": files,
            }
            manifest_path = stage / _MANIFEST_NAME
            with _TextSink(manifest_path, budget) as manifest_sink:
                manifest_sink.write(_json_text(manifest) + "\n")
            manifest_fact = _file_facts(manifest_path)
            physical_facts = {**files, _MANIFEST_NAME: manifest_fact}
            _result_from_manifest(
                project.root,
                stage,
                reused=False,
                expected_report_id=report_id,
                expected_semantics=expected_semantics,
            )
            if _test_hook is not None:
                _test_hook("before_publish")
            (stage / _STAGE_SENTINEL).unlink()
            os.replace(stage, final)
            stage = None
            if _test_hook is not None:
                _test_hook("after_publish")
            return _result_from_manifest(
                project.root,
                final,
                reused=False,
                expected_report_id=report_id,
                expected_semantics=expected_semantics,
                expected_physical_facts=physical_facts,
                deep_validate_artifacts=False,
            )
        except BaseException:
            if not connection_closed:
                if connection.in_transaction:
                    connection.rollback()
                connection.close()
            if stage is not None and inventory_root is not None:
                _safe_cleanup_stage(stage, inventory_root, owner_nonce)
            raise
