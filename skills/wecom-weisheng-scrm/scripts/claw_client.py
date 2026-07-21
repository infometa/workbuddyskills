#!/usr/bin/env python3
"""Claw 客户端模块。

封装 claw 模块接口调用：
- /claw/api/page：获取可用接口列表（含 api_path 文档路径）
- /claw/proxy/forward：通用代理调用下游业务接口

结果缓存到 .cache/api_list.json，避免重复请求。
缓存有效期 2 小时（CACHE_TTL）。

@author jzc
@date 2026-04-02 17:11
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Optional

from utils import ensure_dir, LOGGER, normalize_datetimes

SKILL_ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = SKILL_ROOT / ".cache" / "api_list.json"


class ClawClient:
    """封装 Claw 模块接口，提供 API 列表查询和代理转发能力。"""

    # 缓存有效期：2小时
    CACHE_TTL = 7200
    # 全量拉取时每页条数
    FETCH_PAGE_SIZE = 100

    def __init__(self, client) -> None:
        """初始化 Claw 客户端。

        Args:
            client: SCRMClient 实例，用于调用开放平台接口。
        """
        self.client = client

    def _ensure_cache(self) -> list[dict[str, Any]]:
        """确保缓存中有全量 API 列表，无缓存或过期时自动全量拉取。

        Returns:
            全量 API 记录列表。
        """
        cached = self._load_cache()
        if cached is not None:
            return cached.get("records", [])

        resp_data = self._fetch_all_from_remote()
        return resp_data.get("records", [])

    def _fetch_all_from_remote(self) -> dict[str, Any]:
        """从远程全量拉取 API 列表并缓存。

        Returns:
            {"total": int, "records": [{...}]}
        """
        LOGGER.info("ClawClient_fetch_all_from_remote_开始执行")

        page_size = self.FETCH_PAGE_SIZE
        body: dict[str, Any] = {
            "current_index": 1,
            "page_size": page_size,
        }

        resp = self.client.post_json("/openapi/claw/api/page", body)
        resp_data = resp.get("data", resp)

        all_records = list(resp_data.get("records", []))
        total = resp_data.get("total", 0)
        page_index = 1

        max_pages = 100
        while len(all_records) < total and page_index < max_pages:
            page_index += 1
            body["current_index"] = page_index
            next_resp = self.client.post_json("/openapi/claw/api/page", body)
            next_data = next_resp.get("data", next_resp)
            next_records = next_data.get("records", [])
            if not next_records:
                break
            all_records.extend(next_records)

        # 按 id 去重，防止分页边界或服务端重复数据导致重复记录
        seen_ids = set()
        unique_records = []
        for record in all_records:
            record_id = record.get("id")
            if record_id not in seen_ids:
                seen_ids.add(record_id)
                unique_records.append(record)

        full_data = {"total": len(unique_records), "records": unique_records}
        self._save_cache(full_data)
        LOGGER.info("ClawClient_fetch_all_from_remote_全量缓存完成，total=%d", len(unique_records))
        return full_data

    @staticmethod
    def _fuzzy_match(
        records: list[dict[str, Any]],
        *,
        keyword: str,
    ) -> list[dict[str, Any]]:
        """对记录列表进行多关键词模糊匹配。

        keyword 支持逗号分隔的多个关键词，任一关键词匹配 api_name 即命中，
        取并集。匹配不区分大小写。

        Args:
            records: 全量记录列表。
            keyword: 逗号分隔的关键词，如 "客户列表,分页查询"。

        Returns:
            匹配的记录列表。
        """
        keywords = [kw.strip().lower() for kw in keyword.split(",") if kw.strip()]

        matched = []
        for record in records:
            rec_name = (record.get("api_name") or "").lower()
            if any(kw in rec_name for kw in keywords):
                matched.append(record)
        return matched

    def get_api_list(
        self,
        *,
        keyword: str,
    ) -> dict[str, Any]:
        """通过关键词从接口仓库匹配调用规则。

        使用逗号分隔的多个关键词模糊匹配 api_name，返回最匹配的结果。
        返回字段精简为 api_name、description、api_path、doc_url。

        Args:
            keyword: 逗号分隔的关键词，如 "客户列表,分页查询"。

        Returns:
            {"total": int, "records": [{api_name, description, api_path, doc_url}]}
        """
        LOGGER.info(
            "ClawClient_get_api_list_开始执行，keyword=%s",
            keyword,
        )

        all_records = self._ensure_cache()
        matched = self._fuzzy_match(all_records, keyword=keyword)

        # 精简返回字段
        stripped = []
        for record in matched:
            stripped.append({
                "api_name": record.get("api_name", ""),
                "description": record.get("description", ""),
                "api_path": record.get("api_path", ""),
                "service_name": record.get("category", ""),
                "doc_url": record.get("doc_url", ""),
            })

        LOGGER.info("ClawClient_get_api_list_执行成功，total=%d", len(stripped))
        return {"total": len(stripped), "records": stripped}

    def get_cached_api_list(self) -> list[dict[str, Any]]:
        """从缓存读取 API 列表，缓存不存在或过期则全量拉取。

        Returns:
            API 记录列表。
        """
        return self._ensure_cache()

    # 用于匹配 uri 中路径参数的正则，如 /detail/{chatId} → /detail/[^/]+
    _PATH_PARAM_RE = re.compile(r"\{[^}]+\}")

    # 写操作关键词，api_name 中包含这些关键词时标记为写操作
    _WRITE_KEYWORDS = ("新增", "创建", "添加", "编辑", "修改", "更新", "删除", "移除", "发送", "打标签", "批量操作", "跟进记录添加")

    def _is_write_operation(self, uri: str) -> bool:
        """根据 api_name 判断当前接口是否为写操作。

        Args:
            uri: 请求 URI。

        Returns:
            写操作返回 True，读操作返回 False。
        """
        all_records = self._ensure_cache()
        for record in all_records:
            api_path = record.get("api_path", "")
            if api_path == uri:
                api_name = (record.get("api_name") or "").lower()
                return any(kw in api_name for kw in self._WRITE_KEYWORDS)
            # 路径参数匹配
            if "{" in api_path:
                pattern = self._PATH_PARAM_RE.sub("[^/]+", api_path)
                if re.fullmatch(pattern, uri):
                    api_name = (record.get("api_name") or "").lower()
                    return any(kw in api_name for kw in self._WRITE_KEYWORDS)
        return False

    def forward(
        self,
        service_name: str,
        uri: str,
        method: str = "POST",
        biz_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """调用 POST /claw/proxy/forward 代理转发。

        接口可用性校验由后台完成，Skill 层不再重复验证。
        返回数据中会标记 write_operation，用于区分读写操作。

        Args:
            service_name: 下游服务名，如 "wshoto-basebiz-service"。
            uri: 下游接口 URI，如 "/bff/bizCustomer/private/h5/customer/pageQuery"。
            method: HTTP 方法，默认 "POST"。
            biz_params: 业务参数，透传到下游。

        Returns:
            代理转发的响应数据，包含 write_operation 标记。
        """
        write_op = self._is_write_operation(uri)

        LOGGER.info(
            "ClawClient_forward_开始执行，service_name=%s, uri=%s, write_operation=%s",
            service_name, uri, write_op,
        )

        body: dict[str, Any] = {
            "service_name": service_name,
            "uri": uri,
            "method": method,
        }
        if biz_params:
            body["biz_params"] = biz_params

        resp = self.client.post_json("/openapi/claw/proxy/forward", body)
        resp_data = resp.get("data", resp)
        resp_data = normalize_datetimes(resp_data)

        LOGGER.info("ClawClient_forward_执行成功，service_name=%s", service_name)
        return {"write_operation": write_op, "response": resp_data}

    def find_api_by_name(self, api_name: str) -> Optional[dict[str, Any]]:
        """从缓存中按 api_name 查找接口记录。

        Args:
            api_name: 接口名称。

        Returns:
            匹配的接口记录，未找到返回 None。
        """
        records = self.get_cached_api_list()
        for record in records:
            if record.get("api_name") == api_name:
                return record
        return None

    def find_apis_by_category(self, category: str) -> list[dict[str, Any]]:
        """从缓存中按 category 查找接口列表。

        Args:
            category: 分类名称。

        Returns:
            匹配分类的接口记录列表。
        """
        records = self.get_cached_api_list()
        return [r for r in records if r.get("category") == category]

    def _load_cache(self) -> Optional[dict[str, Any]]:
        """从缓存文件加载 API 列表。

        Returns:
            缓存的 API 列表数据，缓存不存在或过期时返回 None。
        """
        if not CACHE_FILE.exists():
            return None
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 校验缓存是否过期（2小时有效期）
            update_at = data.get("update_at", 0)
            if time.time() - update_at > self.CACHE_TTL:
                return None

            return data
        except (OSError, json.JSONDecodeError):
            return None

    def _save_cache(self, data: dict[str, Any]) -> None:
        """保存 API 列表到缓存文件。

        Args:
            data: 要缓存的 API 列表数据。
        """
        ensure_dir(CACHE_FILE.parent)

        cache_data = {
            "update_at": int(time.time()),
            "records": data.get("records", []),
            "total": data.get("total", 0),
        }

        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except OSError:
            pass  # 写入失败时降级，下次重新请求
