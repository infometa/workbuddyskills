#!/usr/bin/env python3
"""Fail-open Skill update checks backed by the AI-Shifu website manifest."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import requests

SKILL_NAME = "ai-shifu-course-creator"
SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_ROOT / "SKILL.md"
CACHE_FILE = SKILL_ROOT / ".update-check.json"
DEV_CACHE_FILE = SKILL_ROOT / ".update-check.dev.json"
MANIFEST_URL = (
    "https://ai-shifu.cn/skill-manifests/ai-shifu-course-creator.json"
)

SCHEMA_VERSION = 1
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
ALLOWED_MANIFEST_HOSTS = frozenset({"ai-shifu.cn", "www.ai-shifu.cn"})
LOOPBACK_MANIFEST_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
MAX_MANIFEST_BYTES = 64 * 1024
MAX_NOTES_CHARS = 500
VERSION_MANAGEMENT_STANDALONE = "standalone"
VERSION_MANAGEMENT_PLUGIN = "plugin"


class ManifestError(ValueError):
    """The remote or cached manifest is not safe to consume."""


def _validate_manifest_source_url(url: str, *, allow_loopback: bool) -> None:
    """Allow the official HTTPS source, or an explicit loopback-only dev source."""
    parsed = urlparse(url)
    if parsed.username is not None or parsed.password is not None:
        raise ManifestError("manifest URL must not contain credentials")
    if allow_loopback:
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname not in LOOPBACK_MANIFEST_HOSTS
        ):
            raise ManifestError("development manifest URL must use a loopback host")
        return
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_MANIFEST_HOSTS:
        raise ManifestError("manifest URL must use the official HTTPS host")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def parse_semver(value: object) -> tuple[int, int, int] | None:
    """Parse the deliberately small MAJOR.MINOR.PATCH subset used by Skills."""
    if not isinstance(value, str) or not SEMVER_PATTERN.fullmatch(value):
        return None
    try:
        major, minor, patch = (int(part) for part in value.split("."))
    except (TypeError, ValueError):
        return None
    return major, minor, patch


def read_skill_metadata(skill_md: Path = SKILL_MD) -> dict[str, str] | None:
    """Read simple top-level scalar fields from SKILL.md frontmatter."""
    try:
        lines = skill_md.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None

    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return result
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip("\"'")
    return None


def validate_manifest(
    raw: object, expected_skill_name: str = SKILL_NAME
) -> dict[str, Any]:
    """Validate schema and cross-field invariants; return a shallow copy."""
    if not isinstance(raw, dict):
        raise ManifestError("manifest must be an object")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ManifestError("unsupported schema_version")
    if raw.get("skill_name") != expected_skill_name:
        raise ManifestError("skill_name mismatch")

    latest = parse_semver(raw.get("latest"))
    minimum = parse_semver(raw.get("min_supported"))
    if latest is None or minimum is None:
        raise ManifestError("invalid latest or min_supported")
    if minimum > latest:
        raise ManifestError("min_supported exceeds latest")

    notes = raw.get("notes")
    if not isinstance(notes, str) or len(notes) > MAX_NOTES_CHARS:
        raise ManifestError("invalid notes")

    interval = raw.get("check_interval_hours")
    if isinstance(interval, bool) or not isinstance(interval, int):
        raise ManifestError("check_interval_hours must be an integer")
    if not 1 <= interval <= 168:
        raise ManifestError("check_interval_hours outside 1..168")

    if _parse_utc(raw.get("published_at")) is None:
        raise ManifestError("invalid published_at")

    update_url = raw.get("update_url")
    if not isinstance(update_url, str):
        raise ManifestError("invalid update_url")
    parsed_url = urlparse(update_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ManifestError("update_url must use HTTPS")

    return dict(raw)


def determine_update(
    local_version: str,
    manifest: dict[str, Any],
    *,
    source: str,
) -> dict[str, Any]:
    """Pure SemVer decision logic. The manifest must already be validated."""
    local = parse_semver(local_version)
    if local is None:
        raise ManifestError("invalid local version")

    minimum = parse_semver(manifest["min_supported"])
    latest = parse_semver(manifest["latest"])
    if minimum is None or latest is None:
        raise ManifestError("validated manifest contains invalid versions")

    if local < minimum:
        status = "update_required"
    elif local < latest:
        status = "update_recommended"
    else:
        status = "latest"

    return {
        "status": status,
        "skill_name": manifest["skill_name"],
        "local_version": local_version,
        "latest": manifest["latest"],
        "min_supported": manifest["min_supported"],
        "notes": manifest["notes"],
        "update_url": manifest["update_url"],
        "source": source,
    }


def _read_cache(cache_file: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(cache_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    checked_at = _parse_utc(raw.get("checked_at"))
    if checked_at is None:
        return None
    try:
        manifest = validate_manifest(raw.get("manifest"))
    except ManifestError:
        return None
    etag = raw.get("etag", "")
    if not isinstance(etag, str):
        return None
    return {"checked_at": checked_at, "etag": etag, "manifest": manifest}


def _write_cache(
    cache_file: Path,
    *,
    manifest: dict[str, Any],
    etag: str,
    checked_at: datetime,
) -> None:
    payload = {
        "checked_at": _format_utc(checked_at),
        "etag": etag,
        "manifest": manifest,
    }
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = cache_file.with_name(f".{cache_file.name}.{os.getpid()}.tmp")
    try:
        tmp_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp_file, cache_file)
    finally:
        try:
            tmp_file.unlink()
        except FileNotFoundError:
            pass


def _try_write_cache(
    cache_file: Path,
    *,
    manifest: dict[str, Any],
    etag: str,
    checked_at: datetime,
) -> None:
    """Cache persistence is an optimization and must never break a valid check."""
    try:
        _write_cache(
            cache_file,
            manifest=manifest,
            etag=etag,
            checked_at=checked_at,
        )
    except OSError:
        pass


def _cache_is_fresh(cache: dict[str, Any], now: datetime) -> bool:
    interval = cache["manifest"]["check_interval_hours"]
    age_seconds = (now - cache["checked_at"]).total_seconds()
    return 0 <= age_seconds < interval * 3600


def _response_header(response: Any, name: str) -> str:
    headers = getattr(response, "headers", {})
    value = headers.get(name, "") if hasattr(headers, "get") else ""
    return value if isinstance(value, str) else ""


def _read_response_body(response: Any) -> bytes:
    length = _response_header(response, "Content-Length")
    if length:
        try:
            if int(length) > MAX_MANIFEST_BYTES:
                raise ManifestError("manifest response exceeds size limit")
        except ValueError as exc:
            raise ManifestError("invalid Content-Length") from exc

    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_content(chunk_size=8192):
        if not chunk:
            continue
        size += len(chunk)
        if size > MAX_MANIFEST_BYTES:
            raise ManifestError("manifest response exceeds size limit")
        chunks.append(chunk)
    return b"".join(chunks)


def _close_response(response: Any) -> None:
    close = getattr(response, "close", None)
    if callable(close):
        close()


def fetch_manifest(
    *,
    cache_file: Path = CACHE_FILE,
    force: bool = False,
    manifest_url: str = MANIFEST_URL,
    allow_loopback: bool = False,
    http_get: Callable[..., Any] = requests.get,
    now: datetime | None = None,
) -> tuple[dict[str, Any], str]:
    """Return a validated manifest and its source (network/cache/revalidated)."""
    _validate_manifest_source_url(manifest_url, allow_loopback=allow_loopback)
    current_time = (now or _utc_now()).astimezone(timezone.utc)
    cache = _read_cache(cache_file)
    if cache is not None and not force and _cache_is_fresh(cache, current_time):
        return cache["manifest"], "cache"

    headers = {"Accept": "application/json"}
    if cache is not None and cache["etag"]:
        headers["If-None-Match"] = cache["etag"]

    response = http_get(
        manifest_url,
        headers=headers,
        timeout=(3, 5),
        allow_redirects=True,
        stream=True,
    )
    final_url = getattr(response, "url", manifest_url) or manifest_url
    try:
        _validate_manifest_source_url(final_url, allow_loopback=allow_loopback)
    except ManifestError:
        _close_response(response)
        raise

    if response.status_code == 304:
        _close_response(response)
        if cache is None:
            raise ManifestError("received 304 without a valid cache")
        _try_write_cache(
            cache_file,
            manifest=cache["manifest"],
            etag=cache["etag"],
            checked_at=current_time,
        )
        return cache["manifest"], "revalidated"

    if response.status_code != 200:
        _close_response(response)
        raise ManifestError(f"unexpected HTTP status {response.status_code}")

    try:
        body = _read_response_body(response)
    finally:
        _close_response(response)
    try:
        raw = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError("manifest is not valid UTF-8 JSON") from exc
    manifest = validate_manifest(raw)
    etag = _response_header(response, "ETag")
    _try_write_cache(
        cache_file,
        manifest=manifest,
        etag=etag,
        checked_at=current_time,
    )
    return manifest, "network"


def check_for_update(
    *,
    force: bool = False,
    skill_md: Path = SKILL_MD,
    cache_file: Path = CACHE_FILE,
    manifest_url: str = MANIFEST_URL,
    allow_loopback: bool = False,
    http_get: Callable[..., Any] = requests.get,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run the complete fail-open check and always return a public result."""
    try:
        metadata = read_skill_metadata(skill_md)
        if metadata is None:
            raise ManifestError("missing local metadata")
        version_management = metadata.get(
            "version_management", VERSION_MANAGEMENT_STANDALONE
        )
        if version_management == VERSION_MANAGEMENT_PLUGIN:
            return {"status": "check_skipped", "source": "plugin_managed"}
        if version_management != VERSION_MANAGEMENT_STANDALONE:
            return {
                "status": "check_skipped",
                "source": "invalid_version_management",
            }
        local_version = metadata.get("version", "")
        if parse_semver(local_version) is None:
            raise ManifestError("invalid local version")
        manifest, source = fetch_manifest(
            cache_file=cache_file,
            force=force,
            manifest_url=manifest_url,
            allow_loopback=allow_loopback,
            http_get=http_get,
            now=now,
        )
        return determine_update(
            local_version,
            manifest,
            source=source,
        )
    except Exception:
        return {"status": "check_skipped", "source": "none"}
