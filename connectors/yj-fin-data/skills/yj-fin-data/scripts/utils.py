#!/usr/bin/env python3
"""yj-fin-data 公共路径与落盘安全：统一到「用户工作目录」约定。

与同仓库其他技能是**同一约定**（`SKILL_WORK_DIR` 优先，否则向上找 `workspace`
挂载点，再退回 `skills` 的上级、最后 cwd）；本技能自带一份轻量实现，
不跨技能包 `import`（技能包独立分发时，跨包路径不可靠）。
"""
from __future__ import annotations

import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 用户工作目录的环境变量名。未设置时回退到向上探测到的目录，
# 各类产物（落盘的 CSV / JSON）都写在该目录下的技能子目录里。
WORK_DIR_ENV = "SKILL_WORK_DIR"

# 文件名里不得出现的字符（跨平台非法名 + 易被 shell / URL 误读的字符）。
_ILLEGAL_CHARS = '\\:*?"<>|=&'


def _find_workspace_root() -> str:
    """向上遍历：工作目录挂载点 → skills 的上级 → cwd。"""
    path = os.path.abspath(SCRIPT_DIR)
    while path != os.path.dirname(path):
        if os.path.basename(path) == "workspace":
            return path
        path = os.path.dirname(path)

    path = os.path.abspath(SCRIPT_DIR)
    while path != os.path.dirname(path):
        if os.path.basename(path) == "skills":
            return os.path.dirname(path)
        path = os.path.dirname(path)

    return os.path.abspath(os.getcwd())


def resolve_workspace_path() -> str:
    """本技能统一工作目录约定。

    - `SKILL_WORK_DIR` 已设：直接作为本技能工作目录
    - 否则：向上找 `workspace` 挂载点，找不到则退回 skills 上级 / 当前工作目录
    """
    work = os.getenv(WORK_DIR_ENV)
    if work:
        path = os.path.abspath(work)
    else:
        path = _find_workspace_root()
    os.makedirs(path, exist_ok=True)
    return path


def default_skill_output_dir(subdir: str = "yj_fin_data") -> str:
    """默认落盘目录：{workspace_path}/{subdir}（不存在则创建）。"""
    path = os.path.join(resolve_workspace_path(), subdir)
    os.makedirs(path, exist_ok=True)
    return path


# ----------------------------------------------------------------- 文件名处理 ----

def sanitize_filename(name: str) -> str:
    """净化文件名：去目录成分、去非法字符、拒绝路径穿越。

    返回净化后的文件名；无法得到合法名字时返回空串（由调用方兜底）。
    """
    name = (name or "").strip().replace("\\", "/")
    name = name.split("/")[-1]  # 只取最后一段：干掉 ../ 与绝对路径
    name = "".join(
        c for c in name
        if c.isprintable() and c not in _ILLEGAL_CHARS and c != "\0"
    )
    name = name.strip(" .")
    if name in ("", ".", ".."):
        return ""
    return name


def ensure_inside(directory: str, path: str) -> str:
    """兜底边界：净化后仍越出落盘目录则拒绝（防路径穿越的第二道闸）。

    返回目标的绝对路径。
    """
    base = os.path.abspath(directory)
    target = os.path.abspath(path)
    if target != base and not target.startswith(base + os.sep):
        raise ValueError("文件名净化后仍越出落盘目录，已拒绝写入")
    return target


def unique_path(directory: str, filename: str) -> str:
    """同名不覆盖：已存在则追加 (1) / (2) …，返回不冲突的绝对路径。"""
    root, ext = os.path.splitext(filename)
    i = 1
    candidate = os.path.join(directory, f"{root}({i}){ext}")
    while os.path.exists(candidate):
        i += 1
        candidate = os.path.join(directory, f"{root}({i}){ext}")
    return os.path.abspath(candidate)
