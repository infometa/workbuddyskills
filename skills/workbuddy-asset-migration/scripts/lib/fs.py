"""Filesystem-level merge helpers: skills, memory, projects, connectors, simple files."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Set


def backup(path: Path, ts: str) -> Optional[Path]:
    """Rename path → path.bak-<ts>. Returns the backup path, or None if src missing."""
    if not path.exists():
        return None
    bak = path.with_name(path.name + f".bak-{ts}")
    # If running multiple times in same second, keep retrying with suffix
    n = 0
    while bak.exists():
        n += 1
        bak = path.with_name(path.name + f".bak-{ts}-{n}")
    shutil.copy2(path, bak) if path.is_file() else shutil.copytree(path, bak)
    return bak


def make_ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


# --- copy with skip ---

def copy_tree(src: Path, dst: Path, *, overwrite: bool = False) -> str:
    """Copy directory tree. Returns one of: 'created', 'skipped', 'overwritten'."""
    if not src.is_dir():
        return "skipped"
    if dst.exists():
        if not overwrite:
            return "skipped"
        shutil.rmtree(dst)
        shutil.copytree(src, dst)
        return "overwritten"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    return "created"


def copy_file(src: Path, dst: Path, *, overwrite: bool = False) -> str:
    if not src.is_file():
        return "skipped"
    if dst.exists():
        if not overwrite:
            return "skipped"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return "overwritten" if overwrite and dst.exists() else "created"


# --- memory append-with-separator ---

def merge_memory_file(
    src: Path, dst: Path, *, overwrite: bool, source_uid: str, export_time: str
) -> str:
    """Merge a single {uid}_memory.md file. Returns action label."""
    if not src.is_file():
        return "skipped"
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return "created"
    if overwrite:
        shutil.copy2(src, dst)
        return "overwritten"
    # Append with separator, preserving target content first
    sep = (
        f"\n\n--- imported from migration package at {export_time} "
        f"(source uid: {source_uid}) ---\n\n"
    )
    src_text = src.read_text(encoding="utf-8", errors="replace")
    with dst.open("a", encoding="utf-8") as f:
        f.write(sep)
        f.write(src_text)
    return "appended"


# --- identity files: write as .imported.md if target exists ---

def merge_identity_file(src: Path, dst: Path, *, overwrite: bool) -> str:
    if not src.is_file():
        return "skipped"
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return "created"
    if overwrite:
        shutil.copy2(src, dst)
        return "overwritten"
    # Drop ".imported" before final suffix: IDENTITY.md → IDENTITY.imported.md
    imported = dst.with_name(dst.stem + ".imported" + dst.suffix)
    n = 0
    while imported.exists():
        n += 1
        imported = dst.with_name(dst.stem + f".imported.{n}" + dst.suffix)
    shutil.copy2(src, imported)
    return f"imported-as:{imported.name}"


# --- skills directory: skip-if-exists at top level ---

def merge_skills_dir(
    src_skills: Path,
    dst_skills: Path,
    *,
    overwrite: bool,
    skip_indices: List[str],
) -> dict:
    """Merge skills/<name>/ subdirectories one by one. Top-level files in skip_indices are not copied."""
    result = {"created": [], "skipped": [], "overwritten": []}
    if not src_skills.is_dir():
        return result
    dst_skills.mkdir(parents=True, exist_ok=True)
    for entry in sorted(src_skills.iterdir()):
        if entry.name in skip_indices:
            continue
        if entry.is_dir():
            action = copy_tree(entry, dst_skills / entry.name, overwrite=overwrite)
            result[action].append(entry.name)
        # ignore loose files at top of skills/
    return result


# --- projects (conversation jsonl) ---

def list_session_jsonls(projects_dir: Path) -> List[Path]:
    """Return all .jsonl files under projects/<folder>/.../."""
    if not projects_dir.is_dir():
        return []
    return [p for p in projects_dir.rglob("*.jsonl") if p.is_file()]


def filter_jsonls_by_session_ids(
    jsonls: List[Path], session_ids: Set[str], projects_dir: Path
) -> List[Path]:
    """Keep only jsonls whose filename stem (or any path segment) matches a session id."""
    out: List[Path] = []
    for jp in jsonls:
        rel = jp.relative_to(projects_dir)
        segments = [s.strip(".jsonl") for s in rel.parts] + [jp.stem]
        if any(s in session_ids for s in segments):
            out.append(jp)
    return out


def merge_projects_dir(
    src_projects: Path, dst_projects: Path, *, overwrite: bool
) -> dict:
    """Merge projects/ tree. Same-relative-path file: skip unless overwrite."""
    result = {"created": 0, "skipped": 0, "overwritten": 0}
    if not src_projects.is_dir():
        return result
    for src_file in src_projects.rglob("*"):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(src_projects)
        dst_file = dst_projects / rel
        if dst_file.exists():
            if not overwrite:
                result["skipped"] += 1
                continue
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            result["overwritten"] += 1
        else:
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            result["created"] += 1
    return result


# --- connectors ---

def merge_connectors_dir(
    src_connectors: Path,
    dst_connectors: Path,
    *,
    overwrite: bool,
    no_credentials: bool,
    credentials_files: List[str],
    uid_map: dict,
) -> dict:
    """Merge connectors/<uid>/ subdirs. Honor --no-credentials and uid rewrites."""
    result = {"created": [], "skipped": [], "overwritten": [], "merged": [], "credentials_dropped": 0}
    if not src_connectors.is_dir():
        return result
    dst_connectors.mkdir(parents=True, exist_ok=True)

    for entry in sorted(src_connectors.iterdir()):
        if entry.is_file():
            continue  # top-level files handled by caller
        dst_name = uid_map.get(entry.name, entry.name)
        dst_uid_dir = dst_connectors / dst_name
        if not dst_uid_dir.exists():
            shutil.copytree(entry, dst_uid_dir)
            result["created"].append(dst_name)
        elif overwrite:
            shutil.rmtree(dst_uid_dir)
            shutil.copytree(entry, dst_uid_dir)
            result["overwritten"].append(dst_name)
        else:
            # Walk file by file, skip-existing
            for sf in entry.rglob("*"):
                if not sf.is_file():
                    continue
                rel = sf.relative_to(entry)
                df = dst_uid_dir / rel
                if df.exists():
                    continue
                df.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sf, df)
            result["merged"].append(dst_name)

        # Drop credentials if requested (post-copy)
        if no_credentials:
            for fn in credentials_files:
                cf = dst_uid_dir / fn
                if cf.exists():
                    cf.unlink()
                    result["credentials_dropped"] += 1
    return result


# --- project directory rename (cross-machine cwd rewrite) ---

def rename_project_dirs(
    projects_root: Path,
    mapper,  # PathMapper
) -> dict:
    """Walk projects/<oldProjectId>/, look up the original cwd from any
    meta.json inside, compute new projectId based on rewritten cwd, and
    rename the directory + update meta.json files.

    Returns {renamed: [...], cwd_updated: [...], skipped: [...]}.
    """
    import json
    result = {"renamed": [], "cwd_updated": [], "skipped": []}
    if not projects_root.is_dir():
        return result

    for project_dir in sorted(projects_root.iterdir()):
        if not project_dir.is_dir():
            continue
        # Find any meta.json to read original cwd
        meta_files = list(project_dir.glob("*.meta.json"))
        # Also look one level deep (subagents/...)
        meta_files.extend(project_dir.glob("**/*.meta.json"))
        old_cwd = None
        for mf in meta_files:
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "cwd" in data:
                    old_cwd = data["cwd"]
                    break
            except (json.JSONDecodeError, OSError):
                continue
        if not old_cwd:
            # Fall back: decode directory name (lossy, but better than nothing)
            result["skipped"].append({
                "dir": project_dir.name,
                "reason": "no meta.json with cwd field",
            })
            continue

        rewrite_result = mapper.rewrite(old_cwd)
        if not rewrite_result:
            # No rule matched → no rewrite needed
            continue
        new_cwd = rewrite_result.new_path
        new_project_id = mapper.project_id_for(new_cwd)
        if new_project_id == project_dir.name:
            # Same projectId after rewrite (unlikely but possible) — still
            # need to fix meta.json cwd fields
            for mf in meta_files:
                _update_cwd_in_meta(mf, old_cwd, new_cwd)
                result["cwd_updated"].append(str(mf.relative_to(projects_root)))
            continue

        new_dir = projects_root / new_project_id
        if new_dir.exists():
            # Merge: move file by file into new_dir
            for child in project_dir.rglob("*"):
                if not child.is_file():
                    continue
                rel = child.relative_to(project_dir)
                dst = new_dir / rel
                if dst.exists():
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                child.rename(dst)
            # Clean up old dir
            try:
                shutil.rmtree(project_dir)
            except OSError:
                pass
            result["renamed"].append({
                "from": project_dir.name,
                "to": new_project_id,
                "mode": "merged-into-existing",
            })
        else:
            project_dir.rename(new_dir)
            result["renamed"].append({
                "from": project_dir.name,
                "to": new_project_id,
                "mode": "renamed",
            })

        # Now patch meta.json cwd fields inside the (renamed) dir
        for mf in new_dir.glob("**/*.meta.json"):
            _update_cwd_in_meta(mf, old_cwd, new_cwd)
            result["cwd_updated"].append(str(mf.relative_to(projects_root)))

    return result


def _update_cwd_in_meta(meta_path: Path, old_cwd: str, new_cwd: str) -> None:
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if not isinstance(data, dict):
        return
    if data.get("cwd") != old_cwd:
        # Only update if it matches (don't blindly overwrite other cwd values)
        # but tolerate path normalization differences
        import posixpath
        cur = data.get("cwd")
        if isinstance(cur, str) and posixpath.normpath(cur) == posixpath.normpath(old_cwd):
            data["cwd"] = new_cwd
            meta_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return
    data["cwd"] = new_cwd
    meta_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# --- Workspace bundle extract ---

def extract_workspace_bundle(
    bundle_zip: Path,
    destination_root: Path,
    mapper=None,
) -> dict:
    """Extract workspaces/<projectId>/ subtree from bundle zip.

    If mapper is provided (cross-machine), each <projectId> in the bundle is
    re-mapped: we don't know the projectId-to-cwd reverse, so the manifest
    inside the bundle tells us. For each entry the bundle's manifest provides
    `source_path`, which we run through mapper to get destination.

    If mapper is None (same-machine), put files at original path.
    """
    import zipfile
    import json
    result = {"workspaces": [], "errors": []}
    if not bundle_zip.exists():
        return result
    with zipfile.ZipFile(bundle_zip) as zf:
        # Read bundle manifest
        try:
            bm = json.loads(zf.read("manifest.json"))
        except (KeyError, json.JSONDecodeError) as e:
            result["errors"].append(f"bundle manifest unreadable: {e}")
            return result
        for ws in bm.get("workspaces", []):
            project_id = ws["project_id"]
            source_path = ws["source_path"]
            dst_path = source_path
            if mapper is not None:
                r = mapper.rewrite(source_path)
                if r:
                    dst_path = r.new_path
                else:
                    result["errors"].append(
                        f"no path-map rule matched {source_path}; "
                        f"falling back to destination_root/{project_id}"
                    )
                    dst_path = str(destination_root / project_id)
            target_dir = Path(dst_path).expanduser()
            target_dir.mkdir(parents=True, exist_ok=True)
            prefix = f"workspaces/{project_id}/"
            count = 0
            for name in zf.namelist():
                if not name.startswith(prefix) or name.endswith("/"):
                    continue
                rel = name[len(prefix):]
                target_file = target_dir / rel
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(name) as src, target_file.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                count += 1
            result["workspaces"].append({
                "source_path": source_path,
                "destination": str(target_dir),
                "files_written": count,
            })
    return result
