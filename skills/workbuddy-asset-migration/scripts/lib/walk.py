"""Workspace directory scanning, exclusion matching, du/size estimation, zip packing.

The unit of work here is a single workspace (one root path). Used by export
to enumerate what goes into the workspace bundle.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Tuple


# --- Load default excludes from references/workspace_excludes.md ---

_MACHINE_BLOCK_RE = re.compile(
    r"<!--\s*machine:default_excludes\s*\n(.*?)\n-->",
    re.DOTALL,
)


def load_default_excludes(md_path: Path) -> List[str]:
    if not md_path.is_file():
        return []
    text = md_path.read_text(encoding="utf-8")
    m = _MACHINE_BLOCK_RE.search(text)
    if not m:
        return []
    return json.loads(m.group(1))


def _is_dir_pattern(pat: str) -> bool:
    return pat.endswith("/")


def _split_patterns(patterns: List[str]) -> Tuple[List[str], List[str]]:
    """Return (dir_patterns_without_slash, file_or_any_patterns)."""
    dir_pats, file_pats = [], []
    for p in patterns:
        if _is_dir_pattern(p):
            dir_pats.append(p[:-1])  # drop trailing slash
        else:
            file_pats.append(p)
    return dir_pats, file_pats


# --- Match a relative path against the patterns ---

def matches_any(name: str, patterns: List[str]) -> bool:
    """fnmatch-style check. 'name' is just a basename, not a full relpath."""
    for p in patterns:
        if fnmatch.fnmatch(name, p):
            return True
    return False


def matches_path_segment(rel_parts: Tuple[str, ...], dir_patterns: List[str]) -> bool:
    """Check if any segment of the relative path matches any dir pattern."""
    for seg in rel_parts:
        if matches_any(seg, dir_patterns):
            return True
    return False


# --- Scan a workspace and compute stats / file list ---


@dataclass
class WorkspaceScan:
    root: Path
    files_kept: List[Tuple[Path, int]] = field(default_factory=list)  # (path, size)
    files_kept_bytes: int = 0
    files_excluded_count: int = 0
    excluded_by_pattern: Dict[str, int] = field(default_factory=dict)
    excluded_paths_sample: List[str] = field(default_factory=list)  # first 20
    source_du_bytes: int = 0
    symlinks_skipped: List[str] = field(default_factory=list)
    large_subdirs: List[Tuple[str, int]] = field(default_factory=list)  # (relpath, size)
    file_count_total: int = 0


def scan_workspace(
    root: Path,
    excludes: List[str],
    *,
    follow_symlinks: bool = False,
    large_subdir_threshold_bytes: int = 1024 * 1024 * 1024,
) -> WorkspaceScan:
    """Walk `root` once, record kept files and exclusion stats.

    `excludes` is a flat list of glob patterns (loaded from markdown).
    Directory patterns end with `/`; we match them against any path segment.
    """
    scan = WorkspaceScan(root=root)
    if not root.is_dir():
        return scan

    dir_pats, file_pats = _split_patterns(excludes)

    # Track per-direct-subdir size so we can flag large_subdirs after walking.
    subdir_sizes: Dict[str, int] = {}

    for dirpath_str, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        dirpath = Path(dirpath_str)
        try:
            rel_dir = dirpath.relative_to(root)
        except ValueError:
            continue
        rel_parts = rel_dir.parts

        # Prune dirnames in-place: remove any matching a dir pattern
        pruned = []
        for d in list(dirnames):
            if matches_any(d, dir_pats):
                pruned.append(d)
                # Count what we pruned (approx, by walking it once for size)
                pruned_path = dirpath / d
                size, count = _du(pruned_path, follow_symlinks=follow_symlinks)
                scan.files_excluded_count += count
                # Find which dir pattern caused it
                matched_pat = next((p for p in dir_pats if fnmatch.fnmatch(d, p)), d)
                scan.excluded_by_pattern[matched_pat + "/"] = (
                    scan.excluded_by_pattern.get(matched_pat + "/", 0) + count
                )
                if len(scan.excluded_paths_sample) < 20:
                    scan.excluded_paths_sample.append(str(pruned_path.relative_to(root)))
                scan.source_du_bytes += size
        for d in pruned:
            dirnames.remove(d)

        # Walk files in this directory
        for fname in filenames:
            fpath = dirpath / fname
            scan.file_count_total += 1
            try:
                if fpath.is_symlink() and not follow_symlinks:
                    scan.symlinks_skipped.append(str(fpath.relative_to(root)))
                    continue
                st = fpath.lstat()
                size = st.st_size
            except OSError:
                continue
            scan.source_du_bytes += size

            # Filename-level exclusion
            if matches_any(fname, file_pats):
                scan.files_excluded_count += 1
                matched_pat = next(
                    (p for p in file_pats if fnmatch.fnmatch(fname, p)), fname
                )
                scan.excluded_by_pattern[matched_pat] = (
                    scan.excluded_by_pattern.get(matched_pat, 0) + 1
                )
                if len(scan.excluded_paths_sample) < 20:
                    scan.excluded_paths_sample.append(str(fpath.relative_to(root)))
                continue
            # Path-segment level (in case a dir pattern wasn't pruned, e.g. case)
            if rel_parts and matches_path_segment(rel_parts, dir_pats):
                scan.files_excluded_count += 1
                continue

            scan.files_kept.append((fpath, size))
            scan.files_kept_bytes += size

            # Track top-level subdir size
            if rel_parts:
                top = rel_parts[0]
                subdir_sizes[top] = subdir_sizes.get(top, 0) + size

    # Find subdirs over threshold
    for name, sz in subdir_sizes.items():
        if sz >= large_subdir_threshold_bytes:
            scan.large_subdirs.append((name, sz))
    scan.large_subdirs.sort(key=lambda x: -x[1])

    return scan


def _du(path: Path, *, follow_symlinks: bool) -> Tuple[int, int]:
    """Disk-usage (size_bytes, file_count) of a directory subtree."""
    total = 0
    count = 0
    if path.is_file():
        try:
            return path.stat().st_size, 1
        except OSError:
            return 0, 0
    for dirpath, _, filenames in os.walk(path, followlinks=follow_symlinks):
        for fname in filenames:
            fp = Path(dirpath) / fname
            try:
                if fp.is_symlink() and not follow_symlinks:
                    continue
                total += fp.lstat().st_size
                count += 1
            except OSError:
                pass
    return total, count


# --- Detect "interesting" files for caveats (not excluded by default) ---

# These are NOT excluded by default — they're user personal assets and likely
# wanted (especially .env files, which contain real working config). But we
# surface them so the agent / user can decide if they want to drop them before
# packaging, e.g. via --workspace-exclude-pattern '*.env'.
CAVEAT_PATTERNS = {
    "env_files": ["*.env", "*.envrc", ".env.*", "*.env.local"],
    "private_keys": ["*.pem", "*.key", "id_rsa", "id_ed25519", "*.p12", "*.pfx"],
    "db_dumps": ["*.dump", "*.bak.sql", "*.sql.gz"],
    "secrets": ["secrets.*", "*credentials*", "config.local.*"],
}


def detect_caveats(scan: WorkspaceScan) -> List[Dict[str, object]]:
    """Surface sensitive-looking files so the caller (agent/user) can decide.

    These are informational only — the files ARE included by default. To
    exclude, the user can pass --workspace-exclude-pattern.
    """
    out: List[Dict[str, object]] = []
    for category, patterns in CAVEAT_PATTERNS.items():
        matches: List[str] = []
        for fpath, _size in scan.files_kept:
            name = fpath.name.lower()
            for pat in patterns:
                if fnmatch.fnmatch(name, pat.lower()):
                    matches.append(str(fpath.relative_to(scan.root)))
                    break
        if matches:
            out.append({
                "category": category,
                "patterns": patterns,
                "count": len(matches),
                "sample": matches[:5],
                "note": "Included by default. Exclude via --workspace-exclude-pattern if not wanted.",
            })
    if scan.large_subdirs:
        out.append({
            "category": "large_subdirs",
            "threshold_bytes": 1024 * 1024 * 1024,
            "items": [{"name": n, "size_bytes": s} for n, s in scan.large_subdirs[:5]],
            "note": "Large subdirectories — verify they aren't a mounted volume or data dir.",
        })
    if scan.symlinks_skipped:
        out.append({
            "category": "symlinks_skipped",
            "count": len(scan.symlinks_skipped),
            "sample": scan.symlinks_skipped[:5],
            "note": "Symlinks aren't followed; the targets weren't copied.",
        })
    return out


# --- Pack a scanned workspace into a zip subtree ---

def pack_workspace_files(
    scan: WorkspaceScan,
    zf: zipfile.ZipFile,
    arc_prefix: str,
) -> int:
    """Write files into the open zip under arc_prefix (POSIX-style).

    Returns total bytes written (sum of file sizes, pre-compression).
    """
    total = 0
    root = scan.root
    for fpath, size in scan.files_kept:
        try:
            rel = fpath.relative_to(root)
        except ValueError:
            continue
        # Force POSIX-style arcname (zipfile spec)
        arcname = str(PurePosixPath(arc_prefix) / PurePosixPath(*rel.parts))
        try:
            zf.write(fpath, arcname=arcname)
            total += size
        except (OSError, ValueError):
            continue
    return total


# --- Estimate compressed size (heuristic) ---

def estimate_zip_bytes(kept_bytes: int) -> int:
    """Cheap heuristic: assume 0.4 compression ratio for typical source code."""
    return int(kept_bytes * 0.4)
