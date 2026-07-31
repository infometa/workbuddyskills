"""
handlers/pdb_filter.py — PDB 文件过滤与导出
============================================

纯函数模块，无全局状态，可独立测试。

对外暴露：
  - filter_pdb(source_path, out_path, remove=[], keep_chains=[], keep_altloc=None)
      → {"ok": True, "saved": str, "removed_count": int, "total_lines": int}
  - copy_pdb(source_path, out_path)
      → {"ok": True, "saved": str}
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def filter_pdb(
    source_path: Path,
    out_path: Path,
    remove: Optional[list[str]] = None,
    keep_chains: Optional[list[str]] = None,
    keep_altloc: Optional[str] = None,
) -> dict:
    """
    读取 PDB 文件，按条件过滤后写入新文件。原文件不修改。

    参数：
      source_path  原始 PDB 文件路径
      out_path     输出文件路径（必须是 .pdb/.cif/.mmcif）
      remove       要移除的残基名列表，如 ["HOH", "SO4"]（忽略大小写）
      keep_chains  只保留这些链，其余过滤，如 ["A"]（忽略大小写）
      keep_altloc  替代构象策略："highest" → 只保留空格或 "A"；None → 不过滤

    返回 dict：
      {"ok": True, "saved": str(out_path), "removed_count": int, "total_lines": int}
      或
      {"ok": False, "error": str}
    """
    remove_set = {r.upper() for r in (remove or [])}
    keep_chain_set = {c.upper() for c in (keep_chains or [])}

    try:
        pdb_lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    except OSError as exc:
        return {"ok": False, "error": f"读取源文件失败: {exc}"}

    filtered_lines: list[str] = []
    removed_count = 0

    for line in pdb_lines:
        record = line[:6].strip()
        if record in ("ATOM", "HETATM", "TER", "ANISOU"):
            res_name = line[17:20].strip().upper() if len(line) > 20 else ""
            chain_id = line[21].upper() if len(line) > 21 else ""
            alt_loc  = line[16] if len(line) > 16 else " "

            # 1. 按残基名过滤
            if remove_set and res_name in remove_set:
                removed_count += 1
                continue

            # 2. 按链 ID 过滤（TER 记录始终保留，避免破坏 PDB 格式）
            if keep_chain_set and chain_id not in keep_chain_set and record != "TER":
                removed_count += 1
                continue

            # 3. 替代构象过滤：只保留 altLoc == 空格 或 'A'
            if keep_altloc == "highest" and alt_loc not in (" ", "A"):
                removed_count += 1
                continue

        filtered_lines.append(line)

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("".join(filtered_lines), encoding="utf-8")
    except OSError as exc:
        return {"ok": False, "error": f"写入失败: {exc}"}

    return {
        "ok": True,
        "saved": str(out_path),
        "removed_count": removed_count,
        "total_lines": len(pdb_lines),
    }


def copy_pdb(source_path: Path, out_path: Path) -> dict:
    """简单复制 PDB 文件（用于 export_selection 的占位实现）。"""
    try:
        import shutil
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source_path), str(out_path))
        return {"ok": True, "saved": str(out_path)}
    except OSError as exc:
        return {"ok": False, "error": f"复制失败: {exc}"}
