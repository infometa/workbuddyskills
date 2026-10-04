"""Filesystem safety primitives."""

from __future__ import annotations

from mibao_core.filesystem.paths import (
    AuthorizedPath,
    PathPolicy,
    authorize_existing_path,
    authorize_output_path,
    is_unc_path,
    to_filesystem_api_path,
    validate_root_pair,
    validate_windows_path_syntax,
)
from mibao_core.filesystem.scanner import (
    ScanCompletenessSnapshot,
    ScanPolicy,
    ScanRecoveryReceipt,
    ScanResult,
    compute_scan_completeness_snapshot,
    scan_project,
    stat_change_token,
)

__all__ = [
    "AuthorizedPath",
    "PathPolicy",
    "ScanCompletenessSnapshot",
    "ScanPolicy",
    "ScanRecoveryReceipt",
    "ScanResult",
    "authorize_existing_path",
    "authorize_output_path",
    "compute_scan_completeness_snapshot",
    "is_unc_path",
    "scan_project",
    "stat_change_token",
    "to_filesystem_api_path",
    "validate_root_pair",
    "validate_windows_path_syntax",
]
