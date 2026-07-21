#!/usr/bin/env python3
"""会话归档模式管理。

企业微信会话存档有两种接入模式：
- key（密钥模式）：企业自持私钥解密，可获取完整消息原文，使用 /openapi/chat/message/list
- zone（专区模式）：消息存储在智能专区，只能获取会话记录元数据，使用 /openapi/chatdata/list

模式由企业与服务商约定，不会频繁变更，因此本模块将其持久化到本地缓存，
避免每次调用时重复询问。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
CHAT_MODE_FILE = CACHE_DIR / "chat_mode.json"

CHAT_MODE_KEY = "key"    # 密钥模式
CHAT_MODE_ZONE = "zone"  # 专区模式
VALID_MODES = {CHAT_MODE_KEY, CHAT_MODE_ZONE}


def load_chat_mode() -> Optional[str]:
    """从缓存读取会话模式，未设置返回 None。"""
    if not CHAT_MODE_FILE.exists():
        return None
    try:
        with open(CHAT_MODE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        mode = data.get("mode")
        return mode if mode in VALID_MODES else None
    except (OSError, json.JSONDecodeError):
        return None


def save_chat_mode(mode: str) -> None:
    """持久化会话模式到缓存文件。"""
    if mode not in VALID_MODES:
        raise ValueError(f"无效的会话模式 '{mode}'，只允许 key 或 zone")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CHAT_MODE_FILE, "w", encoding="utf-8") as f:
            json.dump({"mode": mode}, f, indent=2)
    except OSError:
        pass  # 写入失败时降级，下次重新提示


def require_chat_mode(expected: str) -> None:
    """校验当前模式是否与预期一致，不匹配时抛出 ValueError 并给出提示。"""
    current = load_chat_mode()
    if current is None:
        raise ValueError(
            "尚未配置会话归档模式，请先执行：\n"
            "  scrm set-chat-mode --mode key   # 密钥模式\n"
            "  scrm set-chat-mode --mode zone  # 专区模式"
        )
    if current != expected:
        label = "密钥模式" if expected == CHAT_MODE_KEY else "专区模式"
        current_label = "密钥模式" if current == CHAT_MODE_KEY else "专区模式"
        raise ValueError(
            f"当前配置的会话模式为【{current_label}】，"
            f"该命令仅适用于【{label}】。\n"
            f"如需切换，请执行：scrm set-chat-mode --mode {expected}"
        )
