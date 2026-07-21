#!/usr/bin/env python3
"""OpenCloudOS 安全数据 API MCP Server.

通过 OpenCloudOS 安全中心公开 API 查询安全公告和 CVE 漏洞信息。
API 基础地址：https://security.opencloudos.tech/api/v1/vms/public-info

注册 4 个 MCP 工具：
  - query_opencloudos_cve          查询单个 CVE 漏洞详情
  - query_opencloudos_cve_batch    批量查询 CVE 漏洞详情
  - query_opencloudos_advisories   查询安全公告列表
  - query_opencloudos_advisory     查询安全公告详情（CSAF v2）

用法：
  # SSE 模式（网络访问）
  python opencloudos_api_server.py --transport sse --host 0.0.0.0 --port 8081

  # stdio 模式（IDE 集成）
  python opencloudos_api_server.py --transport stdio
"""

import asyncio
import json
import os
import re
import sys
from typing import Annotated, Any

import httpx
from loguru import logger
from mcp.server.fastmcp import FastMCP
from pydantic import Field


# ===========================================================================
# 配置
# ===========================================================================

OPENCLOUDOS_API_BASE = os.getenv(
    "OPENCLOUDOS_API_BASE",
    "https://security.opencloudos.tech/api/v1/vms/public-info",
)
OPENCLOUDOS_API_TIMEOUT = int(os.getenv("OPENCLOUDOS_API_TIMEOUT", "30"))

# ===========================================================================
# CVE ID 工具函数
# ===========================================================================

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)


def validate_cve_id(cve_id: str) -> bool:
    if not cve_id:
        return False
    return bool(CVE_PATTERN.fullmatch(cve_id.upper()))


def extract_cve_ids(text: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for m in CVE_PATTERN.findall(text):
        u = m.upper()
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result


def normalize_cve_id(cve_id: str) -> str:
    cve_id = cve_id.strip().upper()
    if not validate_cve_id(cve_id):
        raise ValueError(f"Invalid CVE ID format: {cve_id}")
    return cve_id


# ===========================================================================
# 响应封装
# ===========================================================================


def _success(data: Any, meta: dict | None = None) -> str:
    resp: dict[str, Any] = {"status": "success", "data": data}
    if meta:
        resp["meta"] = meta
    return json.dumps(resp, ensure_ascii=False, default=str)


def _error(msg: str, meta: dict | None = None) -> str:
    resp: dict[str, Any] = {"status": "error", "error": {"message": msg}, "data": {}}
    if meta:
        resp["meta"] = meta
    return json.dumps(resp, ensure_ascii=False)


# ===========================================================================
# HTTP 客户端
# ===========================================================================


async def _api_get(path: str, params: dict | None = None) -> dict:
    """向 OpenCloudOS API 发起 GET 请求并返回 JSON."""
    url = f"{OPENCLOUDOS_API_BASE}{path}"
    async with httpx.AsyncClient(timeout=OPENCLOUDOS_API_TIMEOUT) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


# ===========================================================================
# API 封装：安全公告
# ===========================================================================


async def fetch_advisories(
    page: int = 1,
    page_size: int = 10,
    keywords: str = "",
    severity: str = "",
    date_start: str = "",
    date_end: str = "",
) -> dict:
    """获取安全公告列表."""
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if keywords:
        params["keywords"] = keywords
    if severity:
        params["severity"] = severity
    if date_start:
        params["date_start"] = date_start
    if date_end:
        params["date_end"] = date_end
    return await _api_get("/advisories", params)


async def fetch_advisory_detail(sa_id: str) -> dict:
    """获取安全公告详情（CSAF v2 格式）."""
    return await _api_get(f"/csaf/{sa_id}")


# ===========================================================================
# API 封装：CVE 漏洞
# ===========================================================================


async def fetch_vulns(
    page: int = 1,
    page_size: int = 10,
    keywords: str = "",
    severity: str = "",
    status: str = "",
    create_date_start: str = "",
    create_date_end: str = "",
    update_date_start: str = "",
    update_date_end: str = "",
    sort: str = "create_date",
    order: str = "desc",
) -> dict:
    """获取漏洞库列表."""
    params: dict[str, Any] = {
        "page": page,
        "page_size": page_size,
        "sort": sort,
        "order": order,
    }
    if keywords:
        params["keywords"] = keywords
    if severity:
        params["severity"] = severity
    if status:
        params["status"] = status
    if create_date_start:
        params["create_date_start"] = create_date_start
    if create_date_end:
        params["create_date_end"] = create_date_end
    if update_date_start:
        params["update_date_start"] = update_date_start
    if update_date_end:
        params["update_date_end"] = update_date_end
    return await _api_get("/vulns", params)


async def fetch_cve_detail(cve_id: str) -> dict:
    """获取 CVE 漏洞详情."""
    return await _api_get(f"/vulns/{cve_id}")


# ===========================================================================
# MCP Server 定义
# ===========================================================================

mcp = FastMCP(
    "opencloudos-cve",
    instructions="OpenCloudOS 安全数据 API Server — 查询 OpenCloudOS 安全公告和 CVE 漏洞信息",
)


@mcp.tool()
async def query_opencloudos_cve(
    cve_id: Annotated[str, Field(description="CVE 编号，格式如 CVE-2024-2961")],
) -> str:
    """查询单个 CVE 在 OpenCloudOS 上的漏洞详情.

    数据源：https://security.opencloudos.tech
    返回漏洞描述、CVSS 评分、严重程度、修复状态、受影响产品列表等。
    """
    meta = {"tool": "query_opencloudos_cve", "cve_id": cve_id}
    try:
        actual = normalize_cve_id(cve_id)
        result = await fetch_cve_detail(actual)
        if result.get("code") != 0:
            return _error(
                f"API returned error: {result.get('message', 'unknown error')}",
                meta,
            )
        data = result.get("data")
        if not data:
            return _error(f"CVE {actual} not found in OpenCloudOS", meta)
        return _success(data, meta)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return _error(f"CVE {cve_id} not found in OpenCloudOS", meta)
        return _error(f"HTTP error: {e.response.status_code}", meta)
    except (ValueError, httpx.HTTPError) as e:
        return _error(str(e), meta)


@mcp.tool()
async def query_opencloudos_cve_batch(
    cve_ids: Annotated[str, Field(description="CVE 编号列表，逗号或空格分隔")],
) -> str:
    """批量查询多个 CVE 在 OpenCloudOS 上的漏洞详情.

    逐个调用 CVE 详情接口，汇总返回所有结果。
    """
    meta = {"tool": "query_opencloudos_cve_batch", "input": cve_ids}
    try:
        ids = extract_cve_ids(cve_ids)
        if not ids:
            return _error("No valid CVE IDs found", meta)

        # 并发查询所有 CVE
        tasks = [fetch_cve_detail(cve_id) for cve_id in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results: dict[str, Any] = {}
        for cve_id, resp in zip(ids, responses):
            if isinstance(resp, httpx.HTTPStatusError) and resp.response.status_code == 404:
                results[cve_id] = None
            elif isinstance(resp, Exception):
                results[cve_id] = {"error": str(resp)}
            elif resp.get("code") == 0 and resp.get("data"):
                results[cve_id] = resp["data"]
            else:
                results[cve_id] = None

        found = sum(1 for v in results.values() if isinstance(v, dict) and "error" not in v)
        not_found = [k for k, v in results.items() if v is None]
        errors = [k for k, v in results.items() if isinstance(v, dict) and "error" in v]
        meta.update({
            "total": len(ids),
            "found": found,
            "not_found_list": not_found,
            "error_list": errors,
        })
        return _success(results, meta)
    except (ValueError, httpx.HTTPError) as e:
        return _error(str(e), meta)


@mcp.tool()
async def query_opencloudos_advisories(
    page: Annotated[int, Field(description="页码，默认 1")] = 1,
    page_size: Annotated[int, Field(description="每页条数，最小 10，默认 10")] = 10,
    keywords: Annotated[str, Field(description="搜索关键词（公告 ID 或标题）")] = "",
    severity: Annotated[str, Field(description="严重程度，可选: critical, important, moderate, low，多选用逗号分隔")] = "",
    date_start: Annotated[str, Field(description="起始日期，格式 YYYY-MM-DD")] = "",
    date_end: Annotated[str, Field(description="结束日期，格式 YYYY-MM-DD")] = "",
) -> str:
    """查询 OpenCloudOS 安全公告列表.

    支持按关键词、严重程度、日期范围筛选，分页返回。
    """
    meta = {
        "tool": "query_opencloudos_advisories",
        "page": page,
        "page_size": page_size,
    }
    try:
        result = await fetch_advisories(
            page=page,
            page_size=page_size,
            keywords=keywords,
            severity=severity,
            date_start=date_start,
            date_end=date_end,
        )
        if result.get("code") != 0:
            return _error(
                f"API returned error: {result.get('message', 'unknown error')}",
                meta,
            )
        data = result.get("data", [])
        meta.update({
            "total": result.get("total", 0),
            "total_page": result.get("total_page", 0),
            "current_page": result.get("current_page", page),
        })
        return _success(data, meta)
    except (ValueError, httpx.HTTPError) as e:
        return _error(str(e), meta)


@mcp.tool()
async def query_opencloudos_advisory(
    sa_id: Annotated[str, Field(description="安全公告 ID，格式如 OCSA-2024:1112")],
) -> str:
    """查询 OpenCloudOS 安全公告详情（CSAF v2 格式）.

    通过公告 ID 获取完整的安全公告信息，包含受影响产品、漏洞详情、修复方案等。
    """
    meta = {"tool": "query_opencloudos_advisory", "sa_id": sa_id}
    try:
        sa_id = sa_id.strip()
        if not sa_id:
            return _error("Advisory ID is required", meta)
        result = await fetch_advisory_detail(sa_id)
        # CSAF 接口直接返回 JSON 对象，不包含 code 字段
        if not result:
            return _error(f"Advisory {sa_id} not found", meta)
        return _success(result, meta)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return _error(f"Advisory {sa_id} not found in OpenCloudOS", meta)
        return _error(f"HTTP error: {e.response.status_code}", meta)
    except (ValueError, httpx.HTTPError) as e:
        return _error(str(e), meta)


# ===========================================================================
# 启动入口
# ===========================================================================


def _cli_query():
    """命令行直接查询模式（Fallback 使用）"""
    import argparse

    parser = argparse.ArgumentParser(
        description="OpenCloudOS CVE/安全公告查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询单个 CVE
  python opencloudos_api_server.py cve CVE-2020-15778

  # 批量查询多个 CVE
  python opencloudos_api_server.py cve CVE-2024-1234 CVE-2024-5678

  # 查询安全公告列表
  python opencloudos_api_server.py advisories --keywords openssh --page 1

  # 查询安全公告详情
  python opencloudos_api_server.py advisory OCSA-2024:1112
""",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # cve 子命令
    cve_parser = subparsers.add_parser("cve", help="查询 CVE 漏洞详情")
    cve_parser.add_argument("cve_ids", nargs="+", help="CVE 编号（支持多个）")

    # advisory 子命令
    advisory_parser = subparsers.add_parser("advisory", help="查询安全公告详情")
    advisory_parser.add_argument("sa_id", help="安全公告 ID，如 OCSA-2024:1112")

    # advisories 子命令
    advisories_parser = subparsers.add_parser("advisories", help="查询安全公告列表")
    advisories_parser.add_argument("--page", type=int, default=1, help="页码")
    advisories_parser.add_argument("--page-size", type=int, default=10, help="每页条数")
    advisories_parser.add_argument("--keywords", default="", help="搜索关键词")
    advisories_parser.add_argument("--severity", default="", help="严重程度: critical,important,moderate,low")
    advisories_parser.add_argument("--date-start", default="", help="起始日期 YYYY-MM-DD")
    advisories_parser.add_argument("--date-end", default="", help="结束日期 YYYY-MM-DD")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 静默日志
    logger.remove()

    if args.command == "cve":
        cve_ids = [cve.upper() for cve in args.cve_ids]
        if len(cve_ids) == 1:
            result = asyncio.run(fetch_cve_detail(cve_ids[0]))
            if result.get("code") == 0 and result.get("data"):
                print(json.dumps(result["data"], ensure_ascii=False, indent=2, default=str))
            else:
                print(json.dumps({"found": False, "cve_id": cve_ids[0]}, ensure_ascii=False))
        else:
            # 批量查询
            async def batch():
                tasks = [fetch_cve_detail(cve_id) for cve_id in cve_ids]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                results = {}
                for cve_id, resp in zip(cve_ids, responses):
                    if isinstance(resp, Exception):
                        results[cve_id] = {"error": str(resp)}
                    elif resp.get("code") == 0 and resp.get("data"):
                        results[cve_id] = resp["data"]
                    else:
                        results[cve_id] = None
                return results
            results = asyncio.run(batch())
            print(json.dumps(results, ensure_ascii=False, indent=2, default=str))

    elif args.command == "advisory":
        result = asyncio.run(fetch_advisory_detail(args.sa_id))
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        else:
            print(json.dumps({"found": False, "sa_id": args.sa_id}, ensure_ascii=False))

    elif args.command == "advisories":
        result = asyncio.run(fetch_advisories(
            page=args.page,
            page_size=args.page_size,
            keywords=args.keywords,
            severity=args.severity,
            date_start=args.date_start,
            date_end=args.date_end,
        ))
        if result.get("code") == 0:
            output = {
                "total": result.get("total", 0),
                "total_page": result.get("total_page", 0),
                "current_page": result.get("current_page", args.page),
                "data": result.get("data", []),
            }
            print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
        else:
            print(json.dumps({"error": result.get("message", "unknown error")}, ensure_ascii=False))


def _mcp_server():
    """MCP Server 模式"""
    import argparse

    parser = argparse.ArgumentParser(description="OpenCloudOS CVE API MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="sse")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

    # 新版 FastMCP 通过 settings 设置 host/port
    mcp.settings.host = args.host
    mcp.settings.port = args.port

    logger.info(f"Starting OpenCloudOS CVE API MCP Server ({args.transport})")
    logger.info(f"API base: {OPENCLOUDOS_API_BASE}")
    logger.info("Registered 4 tools")

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        logger.info(f"SSE endpoint: http://{args.host}:{args.port}/sse")
        mcp.run(transport="sse")


def main():
    # 判断是 CLI 查询模式还是 MCP Server 模式
    # CLI 模式：python opencloudos_api_server.py cve/advisory/advisories ...
    # MCP 模式：python opencloudos_api_server.py --transport stdio/sse ...
    if len(sys.argv) > 1 and sys.argv[1] in ("cve", "advisory", "advisories"):
        _cli_query()
    else:
        _mcp_server()


if __name__ == "__main__":
    main()
