#!/usr/bin/env python3
"""yj-fin-inv-fin-analysis 公共路径：统一到「用户工作目录」约定。

本技能自带、不依赖其他技能——每个技能的 scripts/utils.py 自包含，
不 import 其它技能目录里的模块（技能包独立分发，跨目录引用会断）。
"""
from __future__ import annotations

import os
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 用户工作目录的环境变量名。未设置时回退到当前工作目录，
# 各类产物（中间 JSON、HTML 报告）都写在该目录下的技能子目录里。
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
    - 否则：向上找 `workspace` 挂载点，找不到则退回当前工作目录
    """
    work = os.getenv(WORK_DIR_ENV)
    if work:
        path = os.path.abspath(work)
    else:
        path = _find_workspace_root()
    os.makedirs(path, exist_ok=True)
    return path


def default_skill_output_dir(subdir: str = "inv_fin_analysis") -> str:
    """默认：{workspace_path}/inv_fin_analysis"""
    path = os.path.join(resolve_workspace_path(), subdir)
    os.makedirs(path, exist_ok=True)
    return path


def data_json_filename(name: Optional[str]) -> str:
    """中间数据 JSON 的**文件名**（不含目录），供正反两个方向复用同一套净化规则。

    净化：去掉非 `字母/数字/-/_/.` 的字符（含路径分隔符，故 `../` 会被消解为 `.._`），
    并截断到 64 字符。name 为空时退回 `inv_fin_analysis_input.json`。
    """
    if not name:
        return "inv_fin_analysis_input.json"
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in str(name).strip())[:64]
    return f"{safe}_inv_fin_analysis_input.json"


def default_data_json_path(name: Optional[str] = None) -> str:
    """默认中间数据 JSON 路径。"""
    return os.path.join(default_skill_output_dir(), data_json_filename(name))
