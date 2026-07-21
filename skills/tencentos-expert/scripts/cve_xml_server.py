#!/usr/bin/env python3
"""TencentOS CVE XML 查询 MCP Server（自包含精简版）.

仅从 https://mirrors.tencent.com/tlinux/errata/cve.xml 查询 CVE 修复状态。
无 MySQL/TManager/Custom 依赖，一个文件即可运行。

注册 6 个 MCP 工具：
  - query_cve_from_xml_source     单个 CVE 查询
  - query_cve_batch_from_xml_source  批量 CVE 查询
  - clear_cve_xml_cache           清除 XML 缓存
  - get_cve_data_source_status    获取数据源状态
  - extract_cve_from_text         从文本提取 CVE 编号
  - validate_cve_format           验证 CVE 编号格式

用法：
  # SSE 模式（网络访问）
  python cve_xml_server.py --transport sse --host 0.0.0.0 --port 8080

  # stdio 模式（IDE 集成）
  python cve_xml_server.py --transport stdio
"""

import asyncio
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Annotated, Any, Optional

import httpx
from loguru import logger
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field


# ===========================================================================
# 配置
# ===========================================================================

CVE_XML_URL = os.getenv(
    "CVE_XML_URL",
    "https://mirrors.tencent.com/tlinux/errata/cve.xml",
)
CVE_XML_CACHE_DURATION = int(os.getenv("CVE_XML_CACHE_DURATION", "3600"))
TSSA_URL_TEMPLATE = os.getenv(
    "TSSA_URL_TEMPLATE",
    "https://mirrors.tencent.com/tlinux/errata/{tssa_id}.xml",
)


# ===========================================================================
# 错误处理
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
# TSSA URL 构建
# ===========================================================================


def build_tssa_url(tssa_id: str) -> str:
    formatted = tssa_id.lower().replace(":", "")
    return TSSA_URL_TEMPLATE.format(tssa_id=formatted)


# ===========================================================================
# 数据模型
# ===========================================================================


class TSSABlock(BaseModel):
    tssa_id: str = ""
    title: str = ""
    severity: str = ""
    advisory_type: str = ""
    issued_date: str = ""
    updated_date: str = ""
    description: str = ""
    cve_list: list[str] = Field(default_factory=list)
    packages: list[str] = Field(default_factory=list)
    product_series: str = ""


class CVEXMLCache(BaseModel):
    tssa_blocks: list[TSSABlock]
    cached_at: datetime

    def is_expired(self) -> bool:
        return datetime.now() - self.cached_at > timedelta(seconds=CVE_XML_CACHE_DURATION)


# ===========================================================================
# XML 获取与解析（带缓存）
# ===========================================================================


class _CacheManager:
    """CVE XML 缓存管理器"""

    def __init__(self):
        self.cache: Optional[CVEXMLCache] = None
        self.lock = asyncio.Lock()

    def clear(self) -> None:
        """清除缓存"""
        self.cache = None

    def get_status(self) -> dict:
        """获取缓存状态"""
        if self.cache:
            return {
                "cached": True,
                "cached_at": self.cache.cached_at.isoformat(),
                "tssa_count": len(self.cache.tssa_blocks),
                "is_expired": self.cache.is_expired(),
            }
        return {"cached": False}


_cache_manager = _CacheManager()


def _get_text(elem: ET.Element, tag: str) -> str:
    child = elem.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return ""


def _extract_product_series(title: str, desc: str) -> str:
    text = f"{title} {desc}"
    for pat in [r"TencentOS\s+Server\s+(\d+)", r"\bTS(\d+)\b"]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return f"TS{m.group(1)}"
    return ""


def _parse_tssa_update(update: ET.Element) -> Optional[TSSABlock]:
    block = TSSABlock()
    block.tssa_id = _get_text(update, "id")
    if not block.tssa_id:
        return None
    block.title = _get_text(update, "title")
    block.severity = _get_text(update, "severity")
    block.advisory_type = update.get("type", "")
    issued = update.find("issued")
    if issued is not None:
        block.issued_date = issued.get("date", "")
    updated = update.find("updated")
    if updated is not None:
        block.updated_date = updated.get("date", "")
    block.description = _get_text(update, "description")
    block.product_series = _extract_product_series(block.title, block.description)
    refs = update.find("references")
    if refs is not None:
        for ref in refs.findall("reference"):
            if ref.get("type") == "cve":
                cve_id = ref.get("id", "")
                if cve_id and cve_id not in block.cve_list:
                    block.cve_list.append(cve_id)
    pkglist = update.find("pkglist")
    if pkglist is not None:
        for coll in pkglist.findall("collection"):
            for pkg in coll.findall("package"):
                if pkg.get("arch") == "src":
                    fn = pkg.find("filename")
                    if fn is not None and fn.text:
                        src = fn.text.strip()
                        if src.endswith(".src.rpm"):
                            v = src[:-8]
                            if v not in block.packages:
                                block.packages.append(v)
    return block


def parse_cve_xml(xml_content: str) -> list[TSSABlock]:
    root = ET.fromstring(xml_content)
    blocks: list[TSSABlock] = []
    for update in root.findall(".//update"):
        try:
            b = _parse_tssa_update(update)
            if b and b.cve_list:
                blocks.append(b)
        except (ET.ParseError, ValueError, KeyError, AttributeError) as e:
            logger.warning("解析 TSSA 块失败: {}", e)
    logger.info("XML 解析完成: {} 个 TSSA 数据块", len(blocks))
    return blocks


async def fetch_cve_xml() -> list[TSSABlock]:
    cache = _cache_manager.cache
    if cache and not cache.is_expired():
        return cache.tssa_blocks
    async with _cache_manager.lock:
        cache = _cache_manager.cache
        if cache and not cache.is_expired():
            return cache.tssa_blocks
        logger.info("获取并解析 CVE XML: {}", CVE_XML_URL)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(CVE_XML_URL)
            resp.raise_for_status()
        blocks = parse_cve_xml(resp.text)
        _cache_manager.cache = CVEXMLCache(tssa_blocks=blocks, cached_at=datetime.now())
        logger.info("缓存成功 ({} 个 TSSA)", len(blocks))
        return blocks


def clear_xml_cache() -> None:
    _cache_manager.clear()


def get_cache_status() -> dict:
    return _cache_manager.get_status()


# ===========================================================================
# CVE 查询逻辑
# ===========================================================================


def _group_latest_by_version(blocks: list[TSSABlock]) -> dict[str, TSSABlock]:
    groups: dict[str, list[TSSABlock]] = defaultdict(list)
    for b in blocks:
        ver = b.product_series or _extract_product_series(b.title, b.description)
        if ver:
            groups[ver].append(b)
    result = {}
    for ver, vblocks in groups.items():
        result[ver] = sorted(vblocks, key=lambda x: x.updated_date or x.issued_date or "", reverse=True)[0]
    return result


def _build_cve_result(cve_id: str, version_blocks: dict[str, TSSABlock]) -> dict:
    if not version_blocks:
        return None
    sorted_items = sorted(
        version_blocks.items(),
        key=lambda x: x[1].updated_date or x[1].issued_date or "",
        reverse=True,
    )
    _, base = sorted_items[0]
    products = []
    for ver in sorted(version_blocks.keys()):
        b = version_blocks[ver]
        fix_ver = ", ".join(b.packages) if b.packages else ""
        p: dict[str, Any] = {
            "product_id": f"TencentOS-{ver}",
            "product_series": ver,
            "package_name": ", ".join(b.packages[:5]) if b.packages else "",
            "fix_version": fix_ver,
            "status": "fixed" if b.packages else "investigating",
            "conclusion": f"Fixed in {b.tssa_id}" if b.packages else "Under investigation",
        }
        if b.tssa_id:
            p["security_advisory"] = {
                "id": b.tssa_id,
                "url": build_tssa_url(b.tssa_id),
                "publish_date": b.issued_date,
            }
        if b.title:
            p["comments"] = f"{ver}: {b.title}"
        products.append(p)
    return {
        "cve_id": cve_id,
        "severity": base.severity.lower() if base.severity else "unknown",
        "status": "fixed" if any(b.packages for b in version_blocks.values()) else "investigating",
        "description": base.description,
        "source": "cve.xml",
        "dates": {"publish_date": base.issued_date, "update_date": base.updated_date},
        "affected_products": products,
    }


async def query_cve_from_xml(cve_id: str) -> Optional[dict]:
    blocks = await fetch_cve_xml()
    matching = [b for b in blocks if cve_id.upper() in [c.upper() for c in b.cve_list]]
    if not matching:
        return None
    vb = _group_latest_by_version(matching)
    return _build_cve_result(cve_id, vb)


async def query_cve_batch_from_xml(cve_ids: list[str]) -> dict[str, Optional[dict]]:
    blocks = await fetch_cve_xml()
    results: dict[str, Optional[dict]] = {}
    for cve_id in cve_ids:
        matching = [b for b in blocks if cve_id.upper() in [c.upper() for c in b.cve_list]]
        if not matching:
            results[cve_id] = None
        else:
            vb = _group_latest_by_version(matching)
            results[cve_id] = _build_cve_result(cve_id, vb)
    return results


# ===========================================================================
# MCP Server 定义
# ===========================================================================

mcp = FastMCP(
    "tencentos-cve-xml",
    instructions="TencentOS CVE XML 查询 Server — 从官方 XML 镜像查询 CVE 修复状态",
)


@mcp.tool()
async def query_cve_from_xml_source(
    cve_id: Annotated[str, Field(description="CVE 编号，格式如 CVE-2024-2961")],
) -> str:
    """从 CVE XML 官方镜像查询单个 CVE 信息.

    数据源：https://mirrors.tencent.com/tlinux/errata/cve.xml
    返回受影响的 TencentOS 产品版本（TS2/TS3/TS4）、修复版本、TSSA 安全公告链接。
    首次约 2s（下载 XML），缓存后秒级响应。
    """
    meta = {"tool": "query_cve_from_xml_source", "cve_id": cve_id}
    try:
        actual = normalize_cve_id(cve_id)
        result = await query_cve_from_xml(actual)
        if result is None:
            return _error(f"CVE {actual} not found in XML source", meta)
        return _success(result, meta)
    except (ValueError, httpx.HTTPError, ET.ParseError) as e:
        return _error(str(e), meta)


@mcp.tool()
async def query_cve_batch_from_xml_source(
    cve_ids: Annotated[str, Field(description="CVE 编号列表，逗号或空格分隔")],
) -> str:
    """批量查询多个 CVE 信息（基于 XML 源）.

    一次性加载 XML，批量解析效率高。返回每个 CVE 的修复状态。
    """
    meta = {"tool": "query_cve_batch_from_xml_source", "input": cve_ids}
    try:
        ids = extract_cve_ids(cve_ids)
        if not ids:
            return _error("No valid CVE IDs found", meta)
        results = await query_cve_batch_from_xml(ids)
        found = sum(1 for v in results.values() if v is not None)
        not_found = [k for k, v in results.items() if v is None]
        meta.update({"total": len(ids), "found": found, "not_found_list": not_found})
        return _success(results, meta)
    except (ValueError, httpx.HTTPError, ET.ParseError) as e:
        return _error(str(e), meta)


@mcp.tool()
async def clear_cve_xml_cache() -> str:
    """清空 CVE XML 缓存，下次查询时重新下载。"""
    clear_xml_cache()
    return _success({"message": "CVE XML cache cleared"}, {"tool": "clear_cve_xml_cache"})


@mcp.tool()
async def get_cve_data_source_status() -> str:
    """获取 CVE XML 数据源状态（缓存信息、数据源 URL）."""
    return _success({
        "xml_source": {
            "url": CVE_XML_URL,
            "cache_duration_seconds": CVE_XML_CACHE_DURATION,
            "cache_status": get_cache_status(),
        },
    }, {"tool": "get_cve_data_source_status"})


@mcp.tool()
async def extract_cve_from_text(
    text: Annotated[str, Field(description="包含 CVE 编号的文本")],
) -> str:
    """从文本中提取 CVE 编号（去重、大写）."""
    ids = extract_cve_ids(text)
    return _success({"total": len(ids), "cve_ids": ids}, {"tool": "extract_cve_from_text"})


@mcp.tool()
async def validate_cve_format(
    cve_id: Annotated[str, Field(description="待验证的 CVE 编号")],
) -> str:
    """验证 CVE 编号格式是否正确."""
    valid = validate_cve_id(cve_id)
    return _success({
        "input": cve_id, "is_valid": valid,
        "normalized": cve_id.upper() if valid else None,
        "format_hint": "CVE-YYYY-NNNNN",
    }, {"tool": "validate_cve_format"})


# ===========================================================================
# 启动入口
# ===========================================================================


def _cli_query():
    """命令行直接查询模式（Fallback 使用）"""
    import argparse

    parser = argparse.ArgumentParser(
        description="TencentOS CVE XML 查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询单个 CVE
  python cve_xml_server.py query CVE-2020-15778

  # 批量查询多个 CVE
  python cve_xml_server.py query CVE-2024-1234 CVE-2024-5678

  # 从文本提取 CVE 编号
  python cve_xml_server.py extract "修复了 CVE-2024-1234 和 CVE-2024-5678"

  # 查看数据源状态
  python cve_xml_server.py status
""",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # query 子命令
    query_parser = subparsers.add_parser("query", help="查询 CVE 信息")
    query_parser.add_argument("cve_ids", nargs="+", help="CVE 编号（支持多个）")

    # extract 子命令
    extract_parser = subparsers.add_parser("extract", help="从文本提取 CVE 编号")
    extract_parser.add_argument("text", help="包含 CVE 编号的文本")

    # status 子命令
    subparsers.add_parser("status", help="查看数据源和缓存状态")

    # clear 子命令
    subparsers.add_parser("clear", help="清除 XML 缓存")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 静默日志
    logger.remove()

    if args.command == "query":
        cve_ids = args.cve_ids
        if len(cve_ids) == 1:
            result = asyncio.run(query_cve_from_xml(cve_ids[0].upper()))
            if result:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            else:
                print(json.dumps({"found": False, "cve_id": cve_ids[0]}, ensure_ascii=False))
        else:
            results = asyncio.run(query_cve_batch_from_xml([cve.upper() for cve in cve_ids]))
            print(json.dumps(results, ensure_ascii=False, indent=2, default=str))

    elif args.command == "extract":
        ids = extract_cve_ids(args.text)
        print(json.dumps({"total": len(ids), "cve_ids": ids}, ensure_ascii=False, indent=2))

    elif args.command == "status":
        status = {
            "xml_source": CVE_XML_URL,
            "cache_duration_seconds": CVE_XML_CACHE_DURATION,
            "cache_status": get_cache_status(),
        }
        print(json.dumps(status, ensure_ascii=False, indent=2, default=str))

    elif args.command == "clear":
        clear_xml_cache()
        print(json.dumps({"message": "CVE XML cache cleared"}, ensure_ascii=False))


def _mcp_server():
    """MCP Server 模式"""
    import argparse

    parser = argparse.ArgumentParser(description="TencentOS CVE XML MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="sse")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

    # 新版 FastMCP 通过 settings 设置 host/port
    mcp.settings.host = args.host
    mcp.settings.port = args.port

    logger.info(f"Starting TencentOS CVE XML MCP Server ({args.transport})")
    logger.info(f"XML source: {CVE_XML_URL}")
    logger.info("Registered 6 tools")

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        logger.info(f"SSE endpoint: http://{args.host}:{args.port}/sse")
        mcp.run(transport="sse")


def main():
    # 判断是 CLI 查询模式还是 MCP Server 模式
    # CLI 模式：python cve_xml_server.py query/extract/status/clear ...
    # MCP 模式：python cve_xml_server.py --transport stdio/sse ...
    if len(sys.argv) > 1 and sys.argv[1] in ("query", "extract", "status", "clear"):
        _cli_query()
    else:
        _mcp_server()


if __name__ == "__main__":
    main()
