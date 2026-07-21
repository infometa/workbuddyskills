"""Cross-OS path prefix mapper for WorkBuddy asset migration.

Used to rewrite source-machine absolute paths to target-machine paths in:
  - DB columns (sessions.cwd, workspaces.path, automations.cwds, automation_runs.source_cwd)
  - meta.json / settings.json / mcp.json fields
  - projects/<projectId>/ directory names (via compressWorkspacePath)
"""
from __future__ import annotations

import ntpath
import posixpath
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


# --- compressWorkspacePath: replicates WorkBuddy's algorithm ---

# session-team-runtime-loader.ts:
#   compressWorkspacePath = path.replace(/[/\\:]/g, '-').collapse('-')
# We replicate it in Python.

_COMPRESS_RE = re.compile(r"[/\\:]+")


def compress_workspace_path(p: str) -> str:
    """Convert an absolute path to a projectId-safe folder name.

    Examples:
      '/Users/foo/proj'      -> 'Users-foo-proj'
      'C:\\Users\\foo\\proj' -> 'C-Users-foo-proj'
      '/Users//foo/./proj/'  -> 'Users-foo-proj'
    """
    # Normalize separators and collapse runs to single '-', then strip
    s = _COMPRESS_RE.sub("-", p)
    # Collapse multiple '-' (in case input already had them)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


# --- OS-aware path helpers ---

def _mod_for_os(os_name: str):
    if os_name in ("win32", "windows", "win"):
        return ntpath
    return posixpath


def _is_case_sensitive(os_name: str) -> bool:
    # mac (darwin) is *technically* case-insensitive by default on HFS+/APFS but
    # behaves case-preserving; treating it as sensitive matches user mental model
    # (paths like /Users/foo and /users/foo are typically the same data).
    # For our purposes: only Windows is truly case-insensitive in path comparisons.
    return os_name not in ("win32", "windows", "win")


def _normalize_for_compare(path: str, os_name: str) -> str:
    """Normalize a path for prefix comparison: collapse slashes, optionally lowercase."""
    mod = _mod_for_os(os_name)
    n = mod.normpath(path)
    # Normalize separators to the OS native form for comparison
    if mod is ntpath:
        n = n.replace("/", "\\")
    else:
        n = n.replace("\\", "/")
    if not _is_case_sensitive(os_name):
        n = n.lower()
    return n


# --- The mapper ---


@dataclass
class MapResult:
    new_path: str
    rule_index: int   # which rule matched
    matched: bool


class PathMapper:
    """Prefix-based path rewriter.

    rules: list of (src_prefix, dst_prefix). Longest source prefix wins.
    src_os / dst_os: 'darwin' | 'linux' | 'win32' | 'windows'.
    """

    def __init__(
        self,
        rules: List[Tuple[str, str]],
        src_os: str,
        dst_os: str,
    ) -> None:
        self.src_os = src_os
        self.dst_os = dst_os
        self._src_mod = _mod_for_os(src_os)
        self._dst_mod = _mod_for_os(dst_os)
        self._dst_sep = "\\" if self._dst_mod is ntpath else "/"
        # Sort rules by normalized src length, longest first (longest-prefix-wins)
        prepared = []
        for src, dst in rules:
            src_n = _normalize_for_compare(src, src_os)
            prepared.append((src_n, src, dst))
        prepared.sort(key=lambda r: -len(r[0]))
        self._rules = prepared  # list[(normalized_src, raw_src, raw_dst)]

    @property
    def rules(self) -> List[Tuple[str, str]]:
        return [(raw_src, raw_dst) for _, raw_src, raw_dst in self._rules]

    def rewrite(self, path: str) -> Optional[MapResult]:
        """Try to rewrite a single path. Returns None if no rule matches."""
        if not path:
            return None
        # Empty string passthrough
        p_norm = _normalize_for_compare(path, self.src_os)
        for idx, (src_n, raw_src, raw_dst) in enumerate(self._rules):
            if not src_n:
                continue
            # Match either exact or prefix-with-separator
            sep = self._src_sep_in(src_n)
            if p_norm == src_n:
                remainder = ""
                matched = True
            elif p_norm.startswith(src_n + sep):
                remainder = p_norm[len(src_n) + 1:]
                matched = True
            else:
                matched = False
            if not matched:
                continue
            # Compose new path: dst_prefix + sep + remainder (translated)
            dst_prefix = self._dst_mod.normpath(raw_dst)
            if not remainder:
                new_path = dst_prefix
            else:
                # Convert remainder separators to dst os
                if self._dst_mod is ntpath:
                    remainder = remainder.replace("/", "\\")
                else:
                    remainder = remainder.replace("\\", "/")
                # Manually join with dst separator (ntpath.join can be quirky
                # when prefix ends with drive letter colon)
                if dst_prefix.endswith(self._dst_sep):
                    new_path = dst_prefix + remainder
                else:
                    new_path = dst_prefix + self._dst_sep + remainder
            new_path = self._dst_mod.normpath(new_path)
            # Re-ensure native separators after normpath (ntpath.normpath
            # converts / to \, posixpath keeps /, so this is usually fine)
            if self._dst_mod is ntpath:
                new_path = new_path.replace("/", "\\")
            return MapResult(new_path=new_path, rule_index=idx, matched=True)
        return None

    def rewrite_or_keep(self, path: str) -> str:
        r = self.rewrite(path)
        return r.new_path if r else path

    def _src_sep_in(self, normalized_src: str) -> str:
        # The normalized form uses os native separator
        return "\\" if self._src_mod is ntpath else "/"

    # --- project id helpers ---

    def project_id_for(self, path: str) -> str:
        """Compute the projects/ subdirectory name for a given cwd."""
        return compress_workspace_path(path)


# --- Case conflict detection ---

def detect_case_conflicts(paths: List[str], target_os: str) -> List[Tuple[str, str]]:
    """If target is case-insensitive, find pairs of source paths that would
    collapse to the same target path.

    Returns list of (path_a, path_b) pairs that conflict.
    """
    if _is_case_sensitive(target_os):
        return []
    seen: dict = {}
    conflicts = []
    for p in paths:
        key = p.lower()
        if key in seen and seen[key] != p:
            conflicts.append((seen[key], p))
        else:
            seen[key] = p
    return conflicts


# --- Auto-propose mapping rules ---

def propose_rules(
    source_paths: List[str],
    source_os: str,
    source_home: Optional[str],
    target_home: Optional[str],
    target_os: str,
) -> List[Tuple[str, str]]:
    """Best-effort: if we know source_home and target_home, propose a single
    home-prefix rule. Caller may refine.
    """
    rules: List[Tuple[str, str]] = []
    if source_home and target_home:
        rules.append((source_home, target_home))
    return rules
