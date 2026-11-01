#!/usr/bin/env python3
"""yj-fin-knowledge 公共路径：统一到「用户工作目录」约定。

与同仓库其他技能是**同一约定**（`SKILL_WORK_DIR` 优先，否则向上找 `workspace`
挂载点，再退回 `skills` 的上级、最后 cwd）；本技能自带一份轻量实现，
不跨技能包 `import`（技能包独立分发时，跨包路径不可靠）。
"""
from __future__ import annotations

import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 用户工作目录的环境变量名。未设置时回退到向上探测到的目录，
# 各类产物（下载落盘的文件）都写在该目录下的技能子目录里。
WORK_DIR_ENV = "SKILL_WORK_DIR"


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


def default_skill_output_dir(subdir: str = "knowledge_documents") -> str:
    """默认落盘目录：{workspace_path}/{subdir}（不存在则创建）。"""
    path = os.path.join(resolve_workspace_path(), subdir)
    os.makedirs(path, exist_ok=True)
    return path
