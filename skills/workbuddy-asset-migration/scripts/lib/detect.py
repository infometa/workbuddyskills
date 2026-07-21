"""Detect WorkBuddy root directory, variant (cn/intl), and active user_id."""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class RootInfo:
    path: Path
    variant: str  # "cn" | "intl" | "unknown"
    exists: bool

    @property
    def db_path(self) -> Path:
        return self.path / "workbuddy.db"


CN_PATH = Path.home() / ".workbuddy"
INTL_PATH = Path.home() / ".workbuddy-ai"


def _classify(path: Path) -> str:
    """Decide cn / intl based on product.json or path name suffix."""
    product = path / "product.json"
    if product.is_file():
        try:
            data = json.loads(product.read_text(encoding="utf-8"))
            # Heuristic: look for known fields
            name = (data.get("productName") or "").lower()
            folder = (data.get("dataFolderName") or "").lower()
            if "ai" in folder or "intl" in name or "international" in name:
                return "intl"
            if "workbuddy" in folder or "workbuddy" in name:
                return "cn"
        except (json.JSONDecodeError, OSError):
            pass
    name = path.name.lower()
    if name.endswith("workbuddy-ai") or name.endswith(".workbuddy-ai"):
        return "intl"
    if name.endswith("workbuddy") or name.endswith(".workbuddy"):
        return "cn"
    return "unknown"


def _looks_like_root(path: Path) -> bool:
    """Heuristic: directory contains workbuddy.db or settings.json or skills/."""
    if not path.is_dir():
        return False
    return any(
        (path / marker).exists()
        for marker in ("workbuddy.db", "settings.json", "skills", "memory")
    )


def candidate_roots() -> List[RootInfo]:
    """Return all plausible roots in priority order, existing first."""
    candidates: List[Path] = []
    env = os.environ.get("WORKBUDDY_CONFIG_DIR")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.extend([CN_PATH, INTL_PATH])
    seen = set()
    out: List[RootInfo] = []
    for p in candidates:
        rp = p.resolve() if p.exists() else p
        if rp in seen:
            continue
        seen.add(rp)
        if _looks_like_root(p):
            out.append(RootInfo(path=p, variant=_classify(p), exists=True))
    return out


def resolve_root(arg: str, *, must_exist: bool = True, interactive: bool = True) -> RootInfo:
    """Resolve --source / --target argument.

    arg == "auto" → pick from candidate_roots; interactive choice if >1.
    Otherwise treat as a literal path.
    """
    if arg != "auto":
        path = Path(arg).expanduser()
        if must_exist and not path.is_dir():
            raise FileNotFoundError(f"Root does not exist: {path}")
        return RootInfo(path=path, variant=_classify(path), exists=path.exists())

    roots = candidate_roots()
    if not roots:
        if must_exist:
            raise FileNotFoundError(
                "auto detect failed: no WorkBuddy root found at "
                f"{CN_PATH}, {INTL_PATH}, or $WORKBUDDY_CONFIG_DIR"
            )
        # Allow non-existent for import --target auto fresh case: pick cn
        return RootInfo(path=CN_PATH, variant="cn", exists=False)

    if len(roots) == 1:
        return roots[0]

    if not interactive:
        return roots[0]

    print("Multiple WorkBuddy roots detected:")
    for i, r in enumerate(roots, 1):
        print(f"  [{i}] {r.path} ({r.variant})")
    while True:
        choice = input(f"Pick one [1-{len(roots)}]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(roots):
            return roots[int(choice) - 1]
        print("Invalid choice.")


def extract_user_ids(db_path: Path) -> List[tuple]:
    """Return list of (user_id, session_count) sorted by count desc.

    Returns empty list if DB missing / no sessions table / empty.
    """
    if not db_path.is_file():
        return []
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            cur = conn.execute(
                """SELECT user_id, COUNT(*) c
                   FROM sessions
                   WHERE deleted_at IS NULL AND user_id IS NOT NULL AND user_id != ''
                   GROUP BY user_id
                   ORDER BY c DESC"""
            )
            return [(row[0], row[1]) for row in cur.fetchall()]
        finally:
            conn.close()
    except sqlite3.Error:
        return []
