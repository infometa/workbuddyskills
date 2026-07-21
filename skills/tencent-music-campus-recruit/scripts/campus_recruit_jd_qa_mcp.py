#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯校招岗位JD 问答检索 MCP 服务（只读）
----------------------------------------------------------------
对接 trag collection: col-928fec14（col-campus-jd-2026）
共 595 条在招岗位，字段：
  position / recruit_type / direction / category / location /
  description / requirements / bonus / apply_url

工具：
  - search_jds                : 语义搜岗位（最常用）
  - search_jds_by_direction   : 按方向过滤 + 语义搜（技术/设计/产品/职能/市场）
  - search_jds_by_recruit_type: 按招聘类型过滤 + 语义搜（应届毕业生/应届实习/日常实习/青云计划-应届生/青云计划-实习生/Pre留学生实习）
  - search_jds_by_location    : 按工作地模糊过滤（北京/深圳/上海/广州/成都/杭州）
  - get_jd_detail             : 取某岗位完整 JD（描述+要求+加分项+投递链接）
  - batch_search_jds          : 批量搜多个岗位
  - get_jd_stats              : 查看知识库统计信息
"""

import os
import sys
import json
import asyncio
from typing import Dict, List, Any, Optional


def configure_output_encoding() -> None:
    """Avoid UnicodeEncodeError on Windows terminals with legacy encodings."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


configure_output_encoding()

from trag import TRAG

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ======== 配置（环境变量注入，不内置凭据） ========
API_KEY = os.getenv("TRAG_API_KEY")
NAMESPACE_CODE = os.getenv("TRAG_NAMESPACE", "ns-f5e64417")
JD_COLLECTION_CODE = os.getenv("TRAG_JD_COLLECTION", "col-928fec14")
# =================================================


# ============ 枚举字典（用于参数校验与提示） ============
VALID_DIRECTIONS = {"技术", "设计", "产品", "职能", "市场"}
VALID_RECRUIT_TYPES = {
    "应届毕业生", "应届实习", "日常实习",
    "青云计划-应届生", "青云计划-实习生", "Pre留学生实习",
}


def _kv_get(kv: Dict[str, Any], *keys) -> str:
    """按顺序尝试多个键取值，返回第一个非空字符串"""
    for k in keys:
        v = kv.get(k)
        if v:
            return str(v)
    return ""


def _normalize_top_k(value: Any, default: int, minimum: int, maximum: int) -> int:
    """将 top_k 规范到安全范围，避免异常值导致工具报错或过量查询。"""
    try:
        top_k = int(value)
    except (TypeError, ValueError):
        top_k = default
    return max(minimum, min(maximum, top_k))


def _normalize_text(value: Any, max_len: int = 500) -> str:
    """清理文本参数并限制长度。"""
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]


def _format_jd_hit(r, rank: int, brief: bool = True) -> Dict[str, Any]:
    """把一条检索结果格式化成前端可读的 dict"""
    kv = getattr(r, "doc_key_value", {}) or {}
    item = {
        "rank": rank,
        "position":     _kv_get(kv, "position"),
        "recruit_type": _kv_get(kv, "recruit_type_view", "recruit_type"),
        "direction":    _kv_get(kv, "direction_view", "direction"),
        "category":     _kv_get(kv, "category"),
        "location":     _kv_get(kv, "location"),
        "apply_url":    _kv_get(kv, "apply_url"),
        "doc_id":       getattr(r, "id", "") or "",
    }
    if not brief:
        item["description"]  = _kv_get(kv, "description")
        item["requirements"] = _kv_get(kv, "requirements")
        item["bonus"]        = _kv_get(kv, "bonus")
    return item


class CampusJDQA:
    """岗位JD问答检索业务封装"""

    def __init__(self):
        if not API_KEY:
            raise RuntimeError("缺少 TRAG_API_KEY 环境变量，请由平台或本机环境安全注入")
        self.rag = TRAG.from_api_key(api_key=API_KEY)
        self.ns = self.rag.namespace(NAMESPACE_CODE)
        self.collection = self.ns.collection(JD_COLLECTION_CODE)
        print(f"[OK] 校招JD知识库已连接: {JD_COLLECTION_CODE}", file=sys.stderr)

    # ---------- 基础搜 ----------
    def search_jds(self, query: str, top_k: int = 5, detail: bool = False) -> Dict[str, Any]:
        try:
            query = _normalize_text(query)
            top_k = _normalize_top_k(top_k, 5, 1, 15)
            if not query:
                return {"success": False, "message": "query 不能为空", "results": []}
            results = self.collection.search_documents(doc=query, limit=top_k)
            if not results:
                return {"success": False, "message": "未找到相关岗位", "results": []}
            formatted = [_format_jd_hit(r, i, brief=not detail) for i, r in enumerate(results, 1)]
            return {
                "success": True,
                "message": f"找到 {len(formatted)} 个相关岗位",
                "results": formatted,
            }
        except Exception as e:
            return {"success": False, "message": f"JD 搜索失败: {str(e)}", "results": []}

    # ---------- 按方向过滤 ----------
    def search_jds_by_direction(self, direction: str, query: str = "", top_k: int = 10) -> Dict[str, Any]:
        direction = _normalize_text(direction, 50)
        query = _normalize_text(query)
        top_k = _normalize_top_k(top_k, 10, 1, 20)
        if direction and direction not in VALID_DIRECTIONS:
            return {
                "success": False,
                "message": f"无效方向: {direction}，可选值：{sorted(VALID_DIRECTIONS)}",
                "results": [],
            }
        try:
            # 用 query+direction 做一次语义搜，然后在内存里按方向精确过滤
            search_text = (query + " " + direction).strip()
            # 多取一些候选，过滤后再截断
            results = self.collection.search_documents(doc=search_text, limit=max(top_k * 3, 20))
            matched = []
            for r in results:
                kv = getattr(r, "doc_key_value", {}) or {}
                dr = _kv_get(kv, "direction_view", "direction")
                if direction and dr != direction:
                    continue
                matched.append(r)
                if len(matched) >= top_k:
                    break
            if not matched:
                return {"success": False, "message": f"未找到方向为 {direction} 的岗位", "results": []}
            formatted = [_format_jd_hit(r, i) for i, r in enumerate(matched, 1)]
            return {
                "success": True,
                "message": f"方向={direction}，找到 {len(formatted)} 个岗位",
                "results": formatted,
            }
        except Exception as e:
            return {"success": False, "message": f"按方向搜索失败: {str(e)}", "results": []}

    # ---------- 按招聘类型过滤 ----------
    def search_jds_by_recruit_type(self, recruit_type: str, query: str = "", top_k: int = 10) -> Dict[str, Any]:
        recruit_type = _normalize_text(recruit_type, 50)
        query = _normalize_text(query)
        top_k = _normalize_top_k(top_k, 10, 1, 20)
        if recruit_type and recruit_type not in VALID_RECRUIT_TYPES:
            return {
                "success": False,
                "message": f"无效招聘类型: {recruit_type}，可选值：{sorted(VALID_RECRUIT_TYPES)}",
                "results": [],
            }
        try:
            search_text = (query + " " + recruit_type).strip()
            results = self.collection.search_documents(doc=search_text, limit=max(top_k * 3, 20))
            matched = []
            for r in results:
                kv = getattr(r, "doc_key_value", {}) or {}
                rt = _kv_get(kv, "recruit_type_view", "recruit_type")
                if recruit_type and rt != recruit_type:
                    continue
                matched.append(r)
                if len(matched) >= top_k:
                    break
            if not matched:
                return {"success": False, "message": f"未找到招聘类型为 {recruit_type} 的岗位", "results": []}
            formatted = [_format_jd_hit(r, i) for i, r in enumerate(matched, 1)]
            return {
                "success": True,
                "message": f"招聘类型={recruit_type}，找到 {len(formatted)} 个岗位",
                "results": formatted,
            }
        except Exception as e:
            return {"success": False, "message": f"按招聘类型搜索失败: {str(e)}", "results": []}

    # ---------- 按工作地过滤（模糊） ----------
    def search_jds_by_location(self, location: str, query: str = "", top_k: int = 10) -> Dict[str, Any]:
        location = _normalize_text(location, 50)
        query = _normalize_text(query)
        top_k = _normalize_top_k(top_k, 10, 1, 20)
        if not location:
            return {"success": False, "message": "location 不能为空", "results": []}
        try:
            search_text = (query + " " + location).strip()
            results = self.collection.search_documents(doc=search_text, limit=max(top_k * 3, 20))
            matched = []
            for r in results:
                kv = getattr(r, "doc_key_value", {}) or {}
                loc = _kv_get(kv, "location")
                if location not in loc:
                    continue
                matched.append(r)
                if len(matched) >= top_k:
                    break
            if not matched:
                return {"success": False, "message": f"未找到工作地含 {location} 的岗位", "results": []}
            formatted = [_format_jd_hit(r, i) for i, r in enumerate(matched, 1)]
            return {
                "success": True,
                "message": f"工作地含 '{location}'，找到 {len(formatted)} 个岗位",
                "results": formatted,
            }
        except Exception as e:
            return {"success": False, "message": f"按工作地搜索失败: {str(e)}", "results": []}

    # ---------- 获取岗位详情 ----------
    def get_jd_detail(self, position: str, recruit_type: str = "") -> Dict[str, Any]:
        try:
            position = _normalize_text(position, 120)
            recruit_type = _normalize_text(recruit_type, 50)
            if not position:
                return {"success": False, "message": "position 不能为空", "jd": {}}
            # 用岗位名+招聘类型拼成查询串，取 top3 再按岗位名精确匹配
            q = (position + " " + recruit_type).strip()
            results = self.collection.search_documents(doc=q, limit=5)
            best = None
            for r in results:
                kv = getattr(r, "doc_key_value", {}) or {}
                if _kv_get(kv, "position") == position:
                    if recruit_type:
                        if _kv_get(kv, "recruit_type_view", "recruit_type") == recruit_type:
                            best = r
                            break
                    else:
                        best = r
                        break
            if best is None and results:
                best = results[0]  # 退化为最相似的一条
            if best is None:
                return {"success": False, "message": f"未找到岗位: {position}", "jd": {}}

            item = _format_jd_hit(best, 1, brief=False)
            return {
                "success": True,
                "message": f"找到岗位: {item.get('position')}",
                "jd": item,
            }
        except Exception as e:
            return {"success": False, "message": f"获取岗位详情失败: {str(e)}", "jd": {}}

    # ---------- 批量搜 ----------
    def batch_search_jds(self, queries: List[str], top_k: int = 3) -> Dict[str, Any]:
        try:
            top_k = _normalize_top_k(top_k, 3, 1, 10)
            out = {}
            for q in (queries or [])[:10]:
                q = _normalize_text(q)
                if not q:
                    continue
                results = self.collection.search_documents(doc=q, limit=top_k)
                if not results:
                    out[q] = {"found": False, "hits": []}
                    continue
                out[q] = {
                    "found": True,
                    "hits": [_format_jd_hit(r, i) for i, r in enumerate(results, 1)],
                }
            return {
                "success": True,
                "message": f"批量搜索完成，共 {len(out)} 个查询",
                "results": out,
            }
        except Exception as e:
            return {"success": False, "message": f"批量搜索失败: {str(e)}", "results": {}}

    # ---------- 统计 ----------
    def get_jd_stats(self) -> Dict[str, Any]:
        try:
            info = self.collection.info
            return {
                "success": True,
                "name": info.name,
                "code": info.code,
                "state": str(info.state),
                "document_count": info.document_count,
                "namespace": NAMESPACE_CODE,
                "description": info.description,
                "valid_directions": sorted(VALID_DIRECTIONS),
                "valid_recruit_types": sorted(VALID_RECRUIT_TYPES),
            }
        except Exception as e:
            return {"success": False, "message": f"获取统计失败: {str(e)}"}


# ============ MCP 服务器 ============

app = Server("campus-recruit-jd-qa-mcp")
_qa: Optional[CampusJDQA] = None
_init_failure: Optional[str] = None


def _get_qa() -> Optional[CampusJDQA]:
    """懒初始化，初始化失败缓存错误信息，避免工具直接崩溃。"""
    global _qa, _init_failure
    if _qa is not None:
        return _qa
    if _init_failure is not None:
        return None
    try:
        _qa = CampusJDQA()
        return _qa
    except Exception as e:
        _init_failure = f"{type(e).__name__}: {e}"
        print(f"[ERROR] 校招JD知识库初始化失败: {_init_failure}", file=sys.stderr)
        return None


def _service_unavailable_response() -> Dict[str, Any]:
    return {
        "success": False,
        "message": "JD 知识库服务暂时不可用",
        "error_detail": _init_failure or "未知错误",
        "fallback_action": "请改用 scripts/fetch_recruit_jds.py 从 join.qq.com 官网公开接口获取岗位数据",
    }


@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="search_jds",
            description="在腾讯校招JD知识库里搜索相关岗位（语义搜索，通用入口）。返回岗位名、招聘类型、方向、工作地、投递链接等摘要信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词，如 '后端开发'、'强化学习算法'、'游戏策划'"},
                    "top_k": {"type": "integer", "description": "返回条数，默认5", "default": 5, "minimum": 1, "maximum": 15},
                    "detail": {"type": "boolean", "description": "是否返回完整岗位描述/要求/加分项，默认 false 只返回摘要", "default": False},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="search_jds_by_direction",
            description="按方向过滤后再语义搜索。方向可选：技术 / 设计 / 产品 / 职能 / 市场。",
            inputSchema={
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "description": "方向：技术/设计/产品/职能/市场"},
                    "query": {"type": "string", "description": "可选的语义关键词", "default": ""},
                    "top_k": {"type": "integer", "default": 10, "minimum": 1, "maximum": 20},
                },
                "required": ["direction"],
            },
        ),
        Tool(
            name="search_jds_by_recruit_type",
            description="按招聘类型过滤后再语义搜索。类型可选：应届毕业生 / 应届实习 / 日常实习 / 青云计划-应届生 / 青云计划-实习生 / Pre留学生实习。",
            inputSchema={
                "type": "object",
                "properties": {
                    "recruit_type": {"type": "string", "description": "招聘类型"},
                    "query": {"type": "string", "description": "可选的语义关键词", "default": ""},
                    "top_k": {"type": "integer", "default": 10, "minimum": 1, "maximum": 20},
                },
                "required": ["recruit_type"],
            },
        ),
        Tool(
            name="search_jds_by_location",
            description="按工作地模糊过滤后再语义搜索。工作地是字符串模糊匹配（如 '北京' 会命中 '深圳总部、北京'）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "工作地关键词（北京/深圳/上海/广州/成都/杭州/武汉等）"},
                    "query": {"type": "string", "description": "可选的语义关键词", "default": ""},
                    "top_k": {"type": "integer", "default": 10, "minimum": 1, "maximum": 20},
                },
                "required": ["location"],
            },
        ),
        Tool(
            name="get_jd_detail",
            description="根据岗位名称精确获取该岗位的完整JD（描述+要求+加分项+投递链接）。如有多个同名岗位，可附加招聘类型精确定位。",
            inputSchema={
                "type": "object",
                "properties": {
                    "position": {"type": "string", "description": "岗位名称"},
                    "recruit_type": {"type": "string", "description": "可选：招聘类型，用于区分同名岗位", "default": ""},
                },
                "required": ["position"],
            },
        ),
        Tool(
            name="batch_search_jds",
            description="批量搜索多个岗位查询，每个查询返回前 top_k 条相关岗位。",
            inputSchema={
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "查询列表",
                    },
                    "top_k": {"type": "integer", "default": 3, "minimum": 1, "maximum": 10},
                },
                "required": ["queries"],
            },
        ),
        Tool(
            name="get_jd_stats",
            description="查看校招JD知识库的统计信息（岗位数、可选方向、可选招聘类型等）。",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    qa = _get_qa()
    arguments = arguments or {}

    if qa is None:
        result = _service_unavailable_response()
    elif name == "search_jds":
        result = qa.search_jds(
            query=arguments.get("query", ""),
            top_k=arguments.get("top_k", 5),
            detail=bool(arguments.get("detail", False)),
        )
    elif name == "search_jds_by_direction":
        result = qa.search_jds_by_direction(
            direction=arguments.get("direction", ""),
            query=arguments.get("query", ""),
            top_k=arguments.get("top_k", 10),
        )
    elif name == "search_jds_by_recruit_type":
        result = qa.search_jds_by_recruit_type(
            recruit_type=arguments.get("recruit_type", ""),
            query=arguments.get("query", ""),
            top_k=arguments.get("top_k", 10),
        )
    elif name == "search_jds_by_location":
        result = qa.search_jds_by_location(
            location=arguments.get("location", ""),
            query=arguments.get("query", ""),
            top_k=arguments.get("top_k", 10),
        )
    elif name == "get_jd_detail":
        result = qa.get_jd_detail(
            position=arguments.get("position", ""),
            recruit_type=arguments.get("recruit_type", ""),
        )
    elif name == "batch_search_jds":
        result = qa.batch_search_jds(
            queries=arguments.get("queries", []),
            top_k=arguments.get("top_k", 3),
        )
    elif name == "get_jd_stats":
        result = qa.get_jd_stats()
    else:
        result = {"success": False, "message": f"未知工具: {name}"}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())