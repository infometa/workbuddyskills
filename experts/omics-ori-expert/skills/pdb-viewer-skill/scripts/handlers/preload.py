"""
handlers/preload.py — PDB 预加载缓存管理
========================================

依赖 state 模块的 preloaded_pdb / preload_lock。

对外暴露：
  - set_preloaded(data: dict) -> None     写入预加载缓存
  - get_preloaded() -> dict | None        读取预加载缓存（线程安全）
  - clear_preloaded() -> None             清空缓存
"""
from __future__ import annotations

import sys, os
_scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import state
from typing import Optional


def set_preloaded(data: dict) -> None:
    """写入预加载缓存（线程安全）。"""
    with state.preload_lock:
        state.preloaded_pdb = data


def get_preloaded() -> Optional[dict]:
    """读取预加载缓存（线程安全）。返回 None 表示无缓存。"""
    with state.preload_lock:
        return state.preloaded_pdb.copy() if state.preloaded_pdb else None


def clear_preloaded() -> None:
    """清空缓存。"""
    with state.preload_lock:
        state.preloaded_pdb = None
