"""Canonical path authorization with Windows-specific fail-closed guards."""

from __future__ import annotations

import os
import stat
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any, Final, Literal

from mibao_core.errors import MibaoError

PathKind = Literal["file", "directory"]

_RESERVED_WINDOWS_NAMES: Final[frozenset[str]] = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{value}" for value in (*range(1, 10), "¹", "²", "³")),
        *(f"LPT{value}" for value in (*range(1, 10), "¹", "²", "³")),
    }
)
_INVALID_WINDOWS_CHARS: Final[frozenset[str]] = frozenset('<>"|?*')


@dataclass(frozen=True, slots=True)
class PathPolicy:
    """Explicit path policy; every non-default relaxation is visible."""

    allow_unc: bool = False
    reject_reparse: bool = True
    max_component_chars: int = 255
    max_path_chars: int = 32760

    def __post_init__(self) -> None:
        if self.reject_reparse is not True:
            raise MibaoError("MB-FS-0001", "Reparse rejection cannot be disabled")
        if not 1 <= self.max_component_chars <= 255:
            raise MibaoError("MB-FS-0001", "Component limit must be between 1 and 255")
        if not 260 <= self.max_path_chars <= 32760:
            raise MibaoError("MB-FS-0001", "Path limit must be between 260 and 32760")


@dataclass(frozen=True, slots=True)
class FileIdentity:
    device: int
    inode: int
    mode: int
    size: int | None
    modified_ns: int | None


@dataclass(frozen=True, slots=True)
class AuthorizedPath:
    """A canonical path decision bound to its current physical identity."""

    root: Path
    path: Path
    relative: Path
    exists: bool
    kind: str
    identity: FileIdentity | None
    policy: PathPolicy

    def as_dict(self) -> dict[str, Any]:
        return {
            "relative": self.relative.as_posix(),
            "exists": self.exists,
            "kind": self.kind,
            "identity": (
                {
                    "device": self.identity.device,
                    "inode": self.identity.inode,
                    "mode": self.identity.mode,
                    "size": self.identity.size,
                    "modified_ns": self.identity.modified_ns,
                }
                if self.identity is not None
                else None
            ),
        }

    def revalidate(self) -> AuthorizedPath:
        """Re-authorize and compare physical identity immediately before use."""

        if not self.exists or self.identity is None:
            raise MibaoError("MB-FS-0006", "Missing output path has no physical identity")
        expected_kind: PathKind = "directory" if self.kind == "directory" else "file"
        current = authorize_existing_path(
            self.root,
            self.path,
            expected_kind=expected_kind,
            policy=self.policy,
        )
        if current.identity != self.identity:
            raise MibaoError("MB-FS-0006", "Authorized path identity changed before use")
        return current


def is_unc_path(value: str | os.PathLike[str]) -> bool:
    text = os.fspath(value).replace("/", "\\")
    return text.startswith("\\\\")


def _utf16_units(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def validate_windows_path_syntax(
    value: str | os.PathLike[str],
    *,
    allow_unc: bool,
    policy: PathPolicy | None = None,
) -> None:
    """Reject namespace bypasses, ADS, reserved devices, and ambiguous components."""

    active_policy = policy or PathPolicy(allow_unc=allow_unc)
    text = os.fspath(value)
    normalized = text.replace("/", "\\")
    if not text or "\0" in text or any(ord(character) < 32 for character in text):
        raise MibaoError("MB-FS-0001", "Path contains an empty or control character")
    if _utf16_units(text) > active_policy.max_path_chars:
        raise MibaoError("MB-FS-0001", "Path exceeds the configured character limit")
    lower = normalized.lower()
    if lower.startswith(("\\\\?\\", "\\\\.\\")):
        raise MibaoError("MB-FS-0001", "Windows namespace prefixes are not accepted")
    if is_unc_path(text) and not allow_unc:
        raise MibaoError("MB-FS-0004", "UNC path requires an explicit allow_unc policy")
    if (
        len(normalized) >= 2
        and normalized[1] == ":"
        and not (len(normalized) >= 3 and normalized[2] == "\\")
    ):
        raise MibaoError("MB-FS-0001", "Drive-relative Windows paths are not accepted")

    pure = PureWindowsPath(normalized)
    anchor = pure.anchor.rstrip("\\")
    for component in pure.parts:
        if component.rstrip("\\") == anchor or component in {"\\", "."}:
            continue
        if component == "..":
            raise MibaoError("MB-FS-0001", "Parent path components are not accepted")
        if component != unicodedata.normalize("NFC", component):
            raise MibaoError("MB-FS-0001", "Path components must use NFC Unicode")
        if component.endswith((" ", ".")):
            raise MibaoError("MB-FS-0001", "Windows path component ends with space or period")
        if any(character in _INVALID_WINDOWS_CHARS for character in component) or ":" in component:
            raise MibaoError("MB-FS-0001", "Windows path component contains a reserved character")
        base = component.split(".", 1)[0].upper()
        if base in _RESERVED_WINDOWS_NAMES:
            raise MibaoError("MB-FS-0001", f"Windows reserved device name is not allowed: {base}")
        if _utf16_units(component) > active_policy.max_component_chars:
            raise MibaoError("MB-FS-0001", "Path component exceeds the configured character limit")


def _absolute_lexical(value: Path) -> Path:
    expanded = value.expanduser()
    if not expanded.is_absolute():
        raise MibaoError("MB-FS-0001", "Authorized paths must be absolute")
    return Path(os.path.abspath(expanded))


def to_filesystem_api_path(
    value: Path,
    *,
    policy: PathPolicy | None = None,
) -> Path:
    """Create an internal extended-length path only after normal syntax validation."""

    active_policy = policy or PathPolicy()
    lexical = _absolute_lexical(value)
    validate_windows_path_syntax(lexical, allow_unc=active_policy.allow_unc, policy=active_policy)
    if os.name != "nt":
        return lexical
    text = str(lexical)
    if text.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + text[2:])
    return Path("\\\\?\\" + text)


def _strip_extended_prefix(value: Path) -> Path:
    text = str(value)
    lower = text.lower()
    if lower.startswith("\\\\?\\unc\\"):
        return Path("\\\\" + text[8:])
    if lower.startswith("\\\\?\\"):
        return Path(text[4:])
    return value


def _is_reparse(path: Path) -> bool:
    native = to_filesystem_api_path(path, policy=PathPolicy(allow_unc=is_unc_path(path)))
    if native.is_symlink():
        return True
    is_junction = getattr(os.path, "isjunction", None)
    if callable(is_junction) and bool(is_junction(native)):
        return True
    try:
        metadata = os.lstat(native)
    except OSError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_attribute)


def _existing_chain(path: Path) -> list[Path]:
    items: list[Path] = []
    current = path
    while True:
        items.append(current)
        if current.parent == current:
            break
        current = current.parent
    return list(reversed(items))


def _reject_reparse_chain(path: Path, policy: PathPolicy) -> None:
    if not policy.reject_reparse:
        return
    for component in _existing_chain(path):
        native = to_filesystem_api_path(component, policy=policy)
        if (native.exists() or native.is_symlink()) and _is_reparse(component):
            raise MibaoError("MB-FS-0003", f"Reparse path component is not allowed: {component}")


def _resolve_existing(value: Path, policy: PathPolicy) -> Path:
    lexical = _absolute_lexical(value)
    validate_windows_path_syntax(lexical, allow_unc=policy.allow_unc, policy=policy)
    _reject_reparse_chain(lexical, policy)
    try:
        return _strip_extended_prefix(
            to_filesystem_api_path(lexical, policy=policy).resolve(strict=True)
        )
    except OSError as exc:
        code = "MB-FS-0004" if is_unc_path(lexical) else "MB-FS-0001"
        message = "UNC path is unavailable" if code == "MB-FS-0004" else "Path does not exist"
        raise MibaoError(code, message) from exc


def _relative_to_root(root: Path, candidate: Path) -> Path:
    try:
        return candidate.relative_to(root)
    except ValueError as exc:
        raise MibaoError("MB-FS-0002", "Path escapes the authorized root") from exc


def _identity(path: Path, kind: PathKind) -> FileIdentity:
    metadata = os.stat(
        to_filesystem_api_path(path, policy=PathPolicy(allow_unc=is_unc_path(path))),
        follow_symlinks=False,
    )
    return FileIdentity(
        device=metadata.st_dev,
        inode=metadata.st_ino,
        mode=metadata.st_mode,
        size=metadata.st_size if kind == "file" else None,
        modified_ns=metadata.st_mtime_ns if kind == "file" else None,
    )


def authorize_existing_path(
    root: Path,
    candidate: Path,
    *,
    expected_kind: PathKind,
    policy: PathPolicy | None = None,
) -> AuthorizedPath:
    """Authorize an existing file/directory after physical containment and reparse checks."""

    active_policy = policy or PathPolicy()
    resolved_root = _resolve_existing(root, active_policy)
    if not to_filesystem_api_path(resolved_root, policy=active_policy).is_dir():
        raise MibaoError("MB-FS-0001", "Authorized root must be a directory")
    resolved_candidate = _resolve_existing(candidate, active_policy)
    relative = _relative_to_root(resolved_root, resolved_candidate)
    native_candidate = to_filesystem_api_path(resolved_candidate, policy=active_policy)
    if expected_kind == "file" and not native_candidate.is_file():
        raise MibaoError("MB-FS-0001", "Authorized path is not a file")
    if expected_kind == "directory" and not native_candidate.is_dir():
        raise MibaoError("MB-FS-0001", "Authorized path is not a directory")
    return AuthorizedPath(
        root=resolved_root,
        path=resolved_candidate,
        relative=relative,
        exists=True,
        kind=expected_kind,
        identity=_identity(resolved_candidate, expected_kind),
        policy=active_policy,
    )


def authorize_output_path(
    root: Path,
    candidate: Path,
    *,
    policy: PathPolicy | None = None,
) -> AuthorizedPath:
    """Authorize exactly one missing leaf beneath an existing safe parent."""

    active_policy = policy or PathPolicy()
    lexical = _absolute_lexical(candidate)
    validate_windows_path_syntax(lexical, allow_unc=active_policy.allow_unc, policy=active_policy)
    native = to_filesystem_api_path(lexical, policy=active_policy)
    if native.exists() or native.is_symlink():
        raise MibaoError("MB-FS-0007", "Output path already exists; overwrite is forbidden")
    parent = authorize_existing_path(
        root,
        lexical.parent,
        expected_kind="directory",
        policy=active_policy,
    )
    resolved_candidate = parent.path / lexical.name
    relative = _relative_to_root(parent.root, resolved_candidate)
    return AuthorizedPath(
        root=parent.root,
        path=resolved_candidate,
        relative=relative,
        exists=False,
        kind="missing-output",
        identity=None,
        policy=active_policy,
    )


def _contains(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def validate_root_pair(
    source_root: Path,
    output_root: Path,
    *,
    policy: PathPolicy | None = None,
) -> tuple[AuthorizedPath, AuthorizedPath]:
    """Authorize two existing roots and reject same/nested physical paths."""

    active_policy = policy or PathPolicy()
    source = authorize_existing_path(
        source_root,
        source_root,
        expected_kind="directory",
        policy=active_policy,
    )
    output = authorize_existing_path(
        output_root,
        output_root,
        expected_kind="directory",
        policy=active_policy,
    )
    if _contains(source.path, output.path) or _contains(output.path, source.path):
        raise MibaoError("MB-FS-0005", "Source and output roots must not overlap")
    return source, output
