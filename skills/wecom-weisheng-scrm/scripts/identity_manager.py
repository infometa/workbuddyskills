#!/usr/bin/env python3
"""身份管理模块。

调用 /auth/check_super_user 获取用户身份（超管/分管/员工），
并缓存到 .cache/identity.json，避免重复请求。

@author jzc
@date 2026-04-02 17:11
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from utils import ensure_dir, LOGGER

SKILL_ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = SKILL_ROOT / ".cache" / "identity.json"


class IdentityManager:
    """管理用户身份信息的获取与缓存。"""

    def __init__(self, client, user_id: str) -> None:
        """初始化身份管理器。

        Args:
            client: SCRMClient 实例，用于调用开放平台接口。
            user_id: 从 token 缓存获取的用户 ID。
        """
        self.client = client
        self.user_id = user_id

    def get_identity(self) -> dict[str, Any]:
        """获取身份信息，优先读缓存，缓存无效或不存在则调用 API。

        Returns:
            {"super_user": int, "limit": int, "team_enum": str, "role_description": str, "user_name": str}
        """
        cached = self._load_cache()
        if cached:
            LOGGER.info("IdentityManager_get_identity_读取缓存成功，user_id=%s", self.user_id)
            return cached

        return self._refresh()

    def is_team_role(self) -> bool:
        """是否团队角色（超管或分管）。

        Returns:
            super_user in (1, 2) 时返回 True。
        """
        identity = self.get_identity()
        return identity.get("super_user") in (1, 2)

    def get_team_enum(self) -> str:
        """返回 team_enum 值。

        Returns:
            团队角色返回 "TEAM"，普通员工返回 "MINE"。
        """
        identity = self.get_identity()
        return identity.get("team_enum", "MINE")

    def _load_cache(self) -> Optional[dict[str, Any]]:
        """从缓存文件加载身份信息。

        Returns:
            缓存的身份字典，缓存不存在或无效时返回 None。
        """
        if not CACHE_FILE.exists():
            return None
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 校验缓存是否属于当前 app_key 和 user_id
            if data.get("user_id") != self.user_id:
                return None

            # 检查缓存是否过期
            update_at = data.get("update_at", 0)
            if time.time() - update_at > self.CACHE_TTL:
                return None

            return data
        except (OSError, json.JSONDecodeError):
            return None

    # 缓存有效期：2小时
    CACHE_TTL = 7200

    def _save_cache(self, data: dict[str, Any]) -> None:
        """保存身份信息到缓存文件。

        Args:
            data: 要缓存的身份数据字典。
        """
        ensure_dir(CACHE_FILE.parent)
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError:
            pass  # 写入失败时降级，下次重新请求

    def _refresh(self) -> dict[str, Any]:
        """调用 /auth/check_super_user 刷新身份信息。

        Returns:
            包含 super_user、limit、team_enum、role_description 的字典。
        """
        LOGGER.info("IdentityManager_refresh_开始执行，user_id=%s", self.user_id)

        resp = self.client.post_json("/openapi/auth/check_super_user", {"user_id": self.user_id})
        resp_data = resp.get("data", resp)

        super_user = resp_data.get("superUser", resp_data.get("super_user", 0))
        limit = resp_data.get("limit", 0)
        user_name = resp_data.get("user_name", resp_data.get("userName", ""))

        # 计算角色描述和 team_enum
        if super_user == 1:
            role_description = "超级管理员"
            team_enum = "TEAM"
        elif super_user == 2:
            role_description = "分管管理员"
            team_enum = "TEAM"
        else:
            role_description = "普通员工"
            team_enum = "MINE"

        result = {
            "user_id": self.user_id,
            "user_name": user_name,
            "super_user": super_user,
            "limit": limit,
            "team_enum": team_enum,
            "role_description": role_description,
            "update_at": int(time.time()),
        }

        self._save_cache(result)
        LOGGER.info("IdentityManager_refresh_执行成功，super_user=%s", super_user)
        return result
