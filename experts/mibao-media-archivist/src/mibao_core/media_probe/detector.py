"""Conservative extension, MIME, and magic-byte media identification."""

from __future__ import annotations

import json
import os
import sqlite3
import stat
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Final

from mibao_core.errors import MibaoError
from mibao_core.filesystem.paths import (
    AuthorizedPath,
    FileIdentity,
    PathPolicy,
    authorize_existing_path,
    to_filesystem_api_path,
    validate_root_pair,
)
from mibao_core.filesystem.scanner import stat_change_token
from mibao_core.project import ProjectLock, open_project
from mibao_core.project.migrations import audit_schema


@dataclass(frozen=True, slots=True)
class _FormatSpec:
    format_id: str
    media_kind: str
    mime_type: str
    extensions: tuple[str, ...]
    mime_aliases: tuple[str, ...] = ()
    min_magic_bytes: int = 4


def _spec(
    format_id: str,
    media_kind: str,
    mime_type: str,
    extensions: tuple[str, ...],
    *,
    aliases: tuple[str, ...] = (),
    minimum: int = 4,
) -> _FormatSpec:
    return _FormatSpec(format_id, media_kind, mime_type, extensions, aliases, minimum)


_FORMATS: Final[dict[str, _FormatSpec]] = {
    item.format_id: item
    for item in (
        _spec(
            "jpeg",
            "image",
            "image/jpeg",
            (".jpg", ".jpeg", ".jpe"),
            aliases=("image/jpg",),
            minimum=3,
        ),
        _spec("png", "image", "image/png", (".png",), minimum=8),
        _spec("gif", "image", "image/gif", (".gif",), minimum=6),
        _spec("tiff", "image", "image/tiff", (".tif", ".tiff", ".dng", ".nef"), minimum=4),
        _spec("cr2", "image", "image/x-canon-cr2", (".cr2",), minimum=12),
        _spec("webp", "image", "image/webp", (".webp",), minimum=12),
        _spec("bmp", "image", "image/bmp", (".bmp",), minimum=2),
        _spec("jpeg2000", "image", "image/jp2", (".jp2", ".j2k"), minimum=12),
        _spec("psd", "image", "image/vnd.adobe.photoshop", (".psd",), minimum=4),
        _spec("ico", "image", "image/x-icon", (".ico",), minimum=4),
        _spec("avif", "image", "image/avif", (".avif",), minimum=12),
        _spec("heic", "image", "image/heic", (".heic",), minimum=12),
        _spec("heif", "image", "image/heif", (".heif",), minimum=12),
        _spec("mp4", "video", "video/mp4", (".mp4", ".m4v"), minimum=12),
        _spec("mov", "video", "video/quicktime", (".mov", ".qt"), minimum=12),
        _spec("m4a", "audio", "audio/mp4", (".m4a", ".m4b"), minimum=12),
        _spec("three_gpp", "video", "video/3gpp", (".3gp", ".3g2"), minimum=12),
        _spec("iso_bmff", "other", "application/octet-stream", (), minimum=12),
        _spec("avi", "video", "video/x-msvideo", (".avi",), minimum=12),
        _spec("wav", "audio", "audio/wav", (".wav",), aliases=("audio/x-wav",), minimum=12),
        _spec("webm", "video", "video/webm", (".webm",), minimum=4),
        _spec("matroska", "video", "video/x-matroska", (".mkv",), minimum=4),
        _spec("mpeg_ts", "video", "video/mp2t", (".ts", ".mts"), minimum=377),
        _spec("m2ts", "video", "video/mp2t", (".m2ts",), minimum=389),
        _spec("mpeg_ps", "video", "video/mpeg", (".mpg", ".mpeg", ".vob"), minimum=4),
        _spec("asf", "video", "video/x-ms-asf", (".asf",), minimum=16),
        _spec("wmv", "video", "video/x-ms-wmv", (".wmv",), minimum=16),
        _spec("wma", "audio", "audio/x-ms-wma", (".wma",), minimum=16),
        _spec("flv", "video", "video/x-flv", (".flv",), minimum=4),
        _spec("dv", "video", "video/dv", (".dv", ".dif"), minimum=3),
        _spec("flac", "audio", "audio/flac", (".flac",), minimum=4),
        _spec("mp3", "audio", "audio/mpeg", (".mp3",), minimum=2),
        _spec("aac", "audio", "audio/aac", (".aac",), minimum=2),
        _spec("ogg", "audio", "audio/ogg", (".ogg", ".oga"), minimum=4),
        _spec("ogv", "video", "video/ogg", (".ogv",), minimum=4),
        _spec("aiff", "audio", "audio/aiff", (".aif", ".aiff", ".aifc"), minimum=12),
        _spec("midi", "audio", "audio/midi", (".mid", ".midi"), minimum=4),
        _spec("amr", "audio", "audio/amr", (".amr",), minimum=6),
        _spec("caf", "audio", "audio/x-caf", (".caf",), minimum=4),
        _spec("pdf", "document", "application/pdf", (".pdf",), minimum=5),
    )
}

_EXTENSIONS: Final[dict[str, str]] = {
    extension: spec.format_id for spec in _FORMATS.values() for extension in spec.extensions
}
_COMPATIBLE: Final[tuple[frozenset[str], ...]] = (
    frozenset({"heic", "heif"}),
    frozenset({"mpeg_ts", "m2ts"}),
    frozenset({"asf", "wmv", "wma"}),
    frozenset({"ogg", "ogv"}),
)
_ASF_GUID: Final = bytes.fromhex("3026b2758e66cf11a6d900aa0062ce6c")


@dataclass(frozen=True, slots=True)
class MediaProbePolicy:
    max_header_bytes: int = 4096
    classification_batch_size: int = 256
    max_candidates: int = 1_000_000

    def __post_init__(self) -> None:
        if not 32 <= self.max_header_bytes <= 65_536:
            raise MibaoError("MB-MEDIA-0001", "Header read limit must be between 32 and 65536")
        if not 1 <= self.classification_batch_size <= 1000:
            raise MibaoError("MB-MEDIA-0001", "Classification batch must be between 1 and 1000")
        if not 1 <= self.max_candidates <= 10_000_000:
            raise MibaoError("MB-MEDIA-0001", "Classification candidate limit must be finite")


@dataclass(frozen=True, slots=True)
class MediaProbeResult:
    status: str
    format_id: str | None
    media_kind: str | None
    mime_type: str | None
    extension: str
    expected_format_id: str | None
    expected_mime_type: str | None
    declared_mime: str | None
    magic_evidence: str | None
    bytes_read: int
    mismatch_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "status": self.status,
            "format_id": self.format_id,
            "media_kind": self.media_kind,
            "mime_type": self.mime_type,
            "extension": self.extension,
            "expected_format_id": self.expected_format_id,
            "expected_mime_type": self.expected_mime_type,
            "declared_mime": self.declared_mime,
            "magic_evidence": self.magic_evidence,
            "bytes_read": self.bytes_read,
            "mismatch_reasons": list(self.mismatch_reasons),
        }


@dataclass(frozen=True, slots=True)
class CandidateClassificationResult:
    project_id: str
    source_root_id: str
    classified_candidates: int
    unchanged_candidates: int
    recognized_candidates: int
    mismatched_candidates: int
    unknown_candidates: int
    truncated_candidates: int
    empty_candidates: int
    stale_candidates: int
    failed_candidates: int
    committed_batches: int
    max_batch_entries: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "source_root_id": self.source_root_id,
            "classified_candidates": self.classified_candidates,
            "unchanged_candidates": self.unchanged_candidates,
            "recognized_candidates": self.recognized_candidates,
            "mismatched_candidates": self.mismatched_candidates,
            "unknown_candidates": self.unknown_candidates,
            "truncated_candidates": self.truncated_candidates,
            "empty_candidates": self.empty_candidates,
            "stale_candidates": self.stale_candidates,
            "failed_candidates": self.failed_candidates,
            "committed_batches": self.committed_batches,
            "max_batch_entries": self.max_batch_entries,
        }


def _normalized_mime(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.split(";", 1)[0].strip().lower()
    if not normalized or "/" not in normalized:
        raise MibaoError("MB-MEDIA-0001", "Declared MIME type is invalid")
    return normalized


def _compatible(expected: str, observed: str) -> bool:
    if expected == observed:
        return True
    return any(expected in group and observed in group for group in _COMPATIBLE)


def _detect_iso_bmff(header: bytes) -> tuple[str, str] | None:
    if len(header) < 12 or header[4:8] != b"ftyp":
        return None
    size = int.from_bytes(header[:4], "big")
    if size != 0 and size < 12:
        return None
    box_end = min(len(header), size if size >= 12 else len(header))
    brands = {header[8:12]}
    for offset in range(16, box_end - 3, 4):
        brands.add(header[offset : offset + 4])
    lowered = {brand.lower() for brand in brands}
    if b"avif" in lowered or b"avis" in lowered:
        return "avif", "iso_bmff_ftyp_avif"
    if any(brand in lowered for brand in {b"heic", b"heix", b"hevc", b"hevx"}):
        return "heic", "iso_bmff_ftyp_heic"
    if b"mif1" in lowered or b"msf1" in lowered:
        return "heif", "iso_bmff_ftyp_heif"
    if b"qt  " in lowered:
        return "mov", "iso_bmff_ftyp_quicktime"
    if any(brand.startswith(b"3gp") or brand.startswith(b"3g2") for brand in lowered):
        return "three_gpp", "iso_bmff_ftyp_3gpp"
    if b"m4a " in lowered or b"m4b " in lowered:
        return "m4a", "iso_bmff_ftyp_m4a"
    if any(
        brand in lowered
        for brand in {b"isom", b"iso2", b"avc1", b"mp41", b"mp42", b"m4v ", b"dash"}
    ):
        return "mp4", "iso_bmff_ftyp_mp4"
    return "iso_bmff", "iso_bmff_ftyp_unknown_brand"


def _detect_magic(header: bytes, extension: str) -> tuple[str, str] | None:
    if header.startswith(b"II*\0\x10\0\0\0CR\x02\0"):
        return "cr2", "canon_cr2_tiff_header"
    fixed = (
        (b"\xff\xd8\xff", "jpeg", "jpeg_soi"),
        (b"\x89PNG\r\n\x1a\n", "png", "png_signature"),
        (b"GIF87a", "gif", "gif87a_signature"),
        (b"GIF89a", "gif", "gif89a_signature"),
        (b"II*\0", "tiff", "tiff_little_endian"),
        (b"MM\0*", "tiff", "tiff_big_endian"),
        (b"BM", "bmp", "bmp_signature"),
        (b"\0\0\0\x0cjP  \r\n\x87\n", "jpeg2000", "jpeg2000_signature"),
        (b"8BPS", "psd", "photoshop_signature"),
        (b"\0\0\x01\0", "ico", "ico_signature"),
        (b"\x1aE\xdf\xa3", "webm" if b"webm" in header.lower() else "matroska", "ebml_signature"),
        (
            _ASF_GUID,
            "wma" if extension == ".wma" else "wmv" if extension == ".wmv" else "asf",
            "asf_guid",
        ),
        (b"FLV\x01", "flv", "flv_signature"),
        (b"\0\0\x01\xba", "mpeg_ps", "mpeg_program_stream_pack"),
        (b"\0\0\x01\xb3", "mpeg_ps", "mpeg_video_sequence"),
        (b"\x1f\x07\0", "dv", "dv_dif_header"),
        (b"fLaC", "flac", "flac_signature"),
        (b"ID3", "mp3", "id3_signature"),
        (b"OggS", "ogv" if extension == ".ogv" else "ogg", "ogg_capture_pattern"),
        (b"MThd", "midi", "midi_header"),
        (b"#!AMR\n", "amr", "amr_signature"),
        (b"caff", "caf", "caf_signature"),
        (b"%PDF-", "pdf", "pdf_header"),
    )
    for signature, format_id, evidence in fixed:
        if header.startswith(signature):
            return format_id, evidence
    if len(header) >= 12 and header[:4] == b"RIFF":
        form = header[8:12]
        if form == b"WEBP":
            return "webp", "riff_webp"
        if form == b"AVI ":
            return "avi", "riff_avi"
        if form == b"WAVE":
            return "wav", "riff_wave"
    if len(header) >= 12 and header[:4] == b"FORM" and header[8:12] in {b"AIFF", b"AIFC"}:
        return "aiff", "iff_aiff"
    bmff = _detect_iso_bmff(header)
    if bmff is not None:
        return bmff
    if len(header) >= 389 and all(header[offset] == 0x47 for offset in (4, 196, 388)):
        return "m2ts", "mpeg_ts_sync_192"
    if len(header) >= 377 and all(header[offset] == 0x47 for offset in (0, 188, 376)):
        return "mpeg_ts", "mpeg_ts_sync_188"
    if len(header) >= 2 and header[0] == 0xFF:
        second = header[1]
        if second & 0xF6 == 0xF0:
            return "aac", "aac_adts_sync"
        if second & 0xE0 == 0xE0 and second & 0x18 != 0x08 and second & 0x06 != 0:
            return "mp3", "mpeg_audio_frame_sync"
    return None


def probe_header(
    header: bytes,
    *,
    filename: str,
    declared_mime: str | None = None,
) -> MediaProbeResult:
    """Classify bounded header bytes; this does not decode media or infer codecs."""

    extension = Path(filename).suffix.lower()
    expected_id = _EXTENSIONS.get(extension)
    expected = _FORMATS.get(expected_id) if expected_id else None
    normalized_mime = _normalized_mime(declared_mime)
    if not header:
        status = "empty"
        detected = None
    else:
        detected = _detect_magic(header, extension)
        if detected is None and expected is not None and len(header) < expected.min_magic_bytes:
            status = "truncated"
        elif detected is None:
            status = "unknown"
        else:
            status = "recognized"

    format_id = detected[0] if detected else None
    magic_evidence = detected[1] if detected else None
    observed = _FORMATS.get(format_id) if format_id else None
    mismatches: list[str] = []
    if (
        observed is not None
        and expected is not None
        and not _compatible(expected.format_id, observed.format_id)
    ):
        mismatches.append("extension")
    if observed is not None and normalized_mime is not None:
        allowed_mimes = {observed.mime_type, *observed.mime_aliases}
        if normalized_mime not in allowed_mimes:
            mismatches.append("declared_mime")
    if observed is not None and mismatches:
        status = "mismatch"
    return MediaProbeResult(
        status=status,
        format_id=observed.format_id if observed else None,
        media_kind=observed.media_kind if observed else None,
        mime_type=observed.mime_type if observed else None,
        extension=extension,
        expected_format_id=expected.format_id if expected else None,
        expected_mime_type=expected.mime_type if expected else None,
        declared_mime=normalized_mime,
        magic_evidence=magic_evidence,
        bytes_read=len(header),
        mismatch_reasons=tuple(mismatches),
    )


def _same_file_identity(expected: FileIdentity, observed: os.stat_result) -> bool:
    # Compare file-type bits only (stat.S_IFMT). On Windows, os.stat() synthesizes
    # execute bits from the file extension (.exe/.bat/.cmd/.com) while os.fstat()
    # cannot (a bare handle has no path), so raw st_mode would report a false
    # identity change for every executable file. The hashing pipeline's
    # _same_open_identity already uses the same S_IFMT normalization.
    return (
        expected.device,
        expected.inode,
        stat.S_IFMT(expected.mode),
        expected.size,
        expected.modified_ns,
    ) == (
        observed.st_dev,
        observed.st_ino,
        stat.S_IFMT(observed.st_mode),
        observed.st_size,
        observed.st_mtime_ns,
    )


def _probe_authorized(
    authorized: AuthorizedPath,
    *,
    declared_mime: str | None,
    policy: MediaProbePolicy,
) -> MediaProbeResult:
    checked = authorized.revalidate()
    if checked.identity is None:
        raise MibaoError("MB-MEDIA-0002", "Media path has no physical identity")
    native = to_filesystem_api_path(checked.path, policy=checked.policy)
    try:
        with native.open("rb", buffering=0) as handle:
            header = handle.read(policy.max_header_bytes)
            physical = os.fstat(handle.fileno())
    except OSError as exc:
        raise MibaoError("MB-MEDIA-0002", f"Media header cannot be read: {exc}") from exc
    if not _same_file_identity(checked.identity, physical):
        raise MibaoError("MB-FS-0006", "Media identity changed between authorization and read")
    checked.revalidate()
    return probe_header(header, filename=checked.relative.name, declared_mime=declared_mime)


def probe_file(
    root: Path,
    candidate: Path,
    *,
    declared_mime: str | None = None,
    policy: MediaProbePolicy | None = None,
    path_policy: PathPolicy | None = None,
) -> MediaProbeResult:
    """Authorize one file, read at most the header budget, and bind bytes to file identity."""

    active_policy = policy or MediaProbePolicy()
    authorized = authorize_existing_path(
        root,
        candidate,
        expected_kind="file",
        policy=path_policy or PathPolicy(),
    )
    return _probe_authorized(
        authorized,
        declared_mime=declared_mime,
        policy=active_policy,
    )


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA synchronous = FULL")
    connection.execute("PRAGMA journal_mode = DELETE")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _validate_candidate_request(payload: object, source_root_id: str) -> dict[str, Any]:
    required = {
        "schema_version",
        "source_root_id",
        "relative_path",
        "size_bytes",
        "modified_time_ms",
        "identity",
        "change_token",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise MibaoError("MB-MEDIA-0004", "Scan candidate request schema is invalid")
    if payload.get("schema_version") != "1.0" or payload.get("source_root_id") != source_root_id:
        raise MibaoError("MB-MEDIA-0004", "Scan candidate source identity is invalid")
    relative = payload.get("relative_path")
    if not isinstance(relative, str):
        raise MibaoError("MB-MEDIA-0004", "Scan candidate relative path is invalid")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise MibaoError("MB-MEDIA-0004", "Scan candidate relative path is unsafe")
    token = payload.get("change_token")
    if not isinstance(token, str) or len(token) != 64:
        raise MibaoError("MB-MEDIA-0004", "Scan candidate change token is invalid")
    return payload


def _write_classification_batch(
    connection: sqlite3.Connection,
    rows: list[tuple[str, str, str]],
) -> None:
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.executemany(
            "UPDATE operations SET result_json=?, status=?, updated_at=? WHERE operation_id=?",
            [(result, status, _timestamp(), operation_id) for operation_id, result, status in rows],
        )
        connection.commit()
    except sqlite3.Error as exc:
        connection.rollback()
        raise MibaoError("MB-MEDIA-0005", f"Media classifications were rolled back: {exc}") from exc


def classify_scan_candidates(
    project_root: Path,
    source_root: Path,
    *,
    policy: MediaProbePolicy | None = None,
    path_policy: PathPolicy | None = None,
) -> CandidateClassificationResult:
    """Probe present scan candidates in finite batches without creating content Assets."""

    active_policy = policy or MediaProbePolicy()
    active_path_policy = path_policy or PathPolicy()
    project = open_project(project_root)
    source, _ = validate_root_pair(source_root, project.root, policy=active_path_policy)
    if source.identity is None:
        raise MibaoError("MB-MEDIA-0003", "Source root has no physical identity")
    classified = unchanged = recognized = mismatched = unknown = 0
    truncated = empty = stale = failed = committed = max_batch = 0
    source_root_id = ""

    with ProjectLock(project.root):
        connection = _connect(project.database_path)
        try:
            audit_schema(
                connection,
                expected_project_id=project.project_id,
                expected_privacy_mode=project.privacy_mode,
            )
            source_row = connection.execute(
                "SELECT source_root_id, path_identity_json FROM source_roots "
                "WHERE project_id=? AND canonical_path=? AND state='active'",
                (project.project_id, str(source.path)),
            ).fetchone()
            expected_identity = _json(
                {
                    "device": source.identity.device,
                    "inode": source.identity.inode,
                    "mode": source.identity.mode,
                }
            )
            if source_row is None or source_row[1] != expected_identity:
                raise MibaoError("MB-MEDIA-0003", "Source root is unregistered or changed")
            source_root_id = str(source_row[0])
            cursor = ""
            processed = 0
            while True:
                records = connection.execute(
                    "SELECT operation_id, request_json, result_json FROM operations "
                    "WHERE project_id=? AND operation_type='scan_candidate' "
                    "AND operation_id>? AND json_extract(result_json, '$.present')=1 "
                    "AND json_extract(request_json, '$.source_root_id')=? "
                    "ORDER BY operation_id LIMIT ?",
                    (
                        project.project_id,
                        cursor,
                        source_root_id,
                        active_policy.classification_batch_size,
                    ),
                ).fetchall()
                if not records:
                    break
                max_batch = max(max_batch, len(records))
                updates: list[tuple[str, str, str]] = []
                for operation_id, request_text, result_text in records:
                    cursor = str(operation_id)
                    processed += 1
                    if processed > active_policy.max_candidates:
                        raise MibaoError("MB-MEDIA-0005", "Media candidate limit exceeded")
                    prior: Any = {}
                    try:
                        loaded_prior = json.loads(str(result_text))
                        if not isinstance(loaded_prior, dict):
                            raise MibaoError(
                                "MB-MEDIA-0004", "Scan candidate result schema is invalid"
                            )
                        prior = loaded_prior
                        request = _validate_candidate_request(
                            json.loads(str(request_text)), source_root_id
                        )
                    except (json.JSONDecodeError, MibaoError) as exc:
                        code = exc.code if isinstance(exc, MibaoError) else "MB-MEDIA-0004"
                        updates.append(
                            (
                                str(operation_id),
                                _json(
                                    {
                                        "classification": "media_probe_failed",
                                        "error_code": code,
                                        "present": True,
                                        "scan_attempt_id": prior.get("scan_attempt_id"),
                                        "schema_version": "1.0",
                                    }
                                ),
                                "failed",
                            )
                        )
                        failed += 1
                        continue
                    token = str(request["change_token"])
                    if (
                        isinstance(prior, dict)
                        and prior.get("classification")
                        in {"media_probe_completed", "metadata_completed", "metadata_partial"}
                        and prior.get("probed_change_token") == token
                        and isinstance(prior.get("media_probe"), dict)
                    ):
                        unchanged += 1
                        continue
                    candidate = source.path / Path(
                        *PurePosixPath(str(request["relative_path"])).parts
                    )
                    try:
                        authorized = authorize_existing_path(
                            source.path,
                            candidate,
                            expected_kind="file",
                            policy=active_path_policy,
                        )
                        identity = authorized.identity
                        if identity is None or stat_change_token(identity) != token:
                            raise MibaoError("MB-MEDIA-0004", "Scan candidate is stale")
                        probe = _probe_authorized(
                            authorized,
                            declared_mime=None,
                            policy=active_policy,
                        )
                    except MibaoError as exc:
                        classification = (
                            "scan_candidate_stale"
                            if exc.code in {"MB-MEDIA-0004", "MB-FS-0006"}
                            else "media_probe_failed"
                        )
                        updates.append(
                            (
                                str(operation_id),
                                _json(
                                    {
                                        "classification": classification,
                                        "error_code": exc.code,
                                        "present": True,
                                        "scan_attempt_id": prior.get("scan_attempt_id"),
                                        "schema_version": "1.0",
                                    }
                                ),
                                "failed",
                            )
                        )
                        if classification == "scan_candidate_stale":
                            stale += 1
                        else:
                            failed += 1
                        continue
                    result_payload = {
                        "classification": "media_probe_completed",
                        "media_probe": probe.as_dict(),
                        "present": True,
                        "probed_change_token": token,
                        "scan_attempt_id": prior.get("scan_attempt_id"),
                        "schema_version": "1.0",
                    }
                    updates.append((str(operation_id), _json(result_payload), "succeeded"))
                    classified += 1
                    if probe.status == "recognized":
                        recognized += 1
                    elif probe.status == "mismatch":
                        mismatched += 1
                    elif probe.status == "unknown":
                        unknown += 1
                    elif probe.status == "truncated":
                        truncated += 1
                    elif probe.status == "empty":
                        empty += 1
                if updates:
                    _write_classification_batch(connection, updates)
                    committed += 1
        finally:
            connection.close()

    return CandidateClassificationResult(
        project_id=project.project_id,
        source_root_id=source_root_id,
        classified_candidates=classified,
        unchanged_candidates=unchanged,
        recognized_candidates=recognized,
        mismatched_candidates=mismatched,
        unknown_candidates=unknown,
        truncated_candidates=truncated,
        empty_candidates=empty,
        stale_candidates=stale,
        failed_candidates=failed,
        committed_batches=committed,
        max_batch_entries=max_batch,
    )


def expected_media_type_policy() -> dict[str, Any]:
    return {
        "schemaVersion": "1.0",
        "maxHeaderBytes": 4096,
        "formats": [
            {
                "formatId": spec.format_id,
                "mediaKind": spec.media_kind,
                "mimeType": spec.mime_type,
                "extensions": list(spec.extensions),
                "mimeAliases": list(spec.mime_aliases),
                "minMagicBytes": spec.min_magic_bytes,
            }
            for spec in _FORMATS.values()
        ],
    }


def validate_media_type_policy(path: Path) -> list[str]:
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"policy_unreadable:{exc}"]
    return [] if payload == expected_media_type_policy() else ["policy_does_not_match_runtime"]
