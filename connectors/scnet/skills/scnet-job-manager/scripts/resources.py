#!/usr/bin/env python3
"""SCNet resource recommendation helpers."""

from typing import Any
from urllib.parse import urlencode

import requests
from constant import SCNET_BASE_URL

RESOURCE_SEARCH_PATH = "/acx/search/quantumCompute/full-text"
RESOURCE_SUGGEST_PATH = "/acx/search/quantumCompute/suggest"
RESOURCE_DETAIL_PATH = "/ui/mall/detail/goods"
RESOURCE_MORE_PATH = "/ui/mall/search/resource"
CPU_RESOURCE_SPEC = (
    "COMMON_RESOURCE_SPEC_CPU-国产X86,"
    "COMMON_RESOURCE_SPEC_CPU-Intel,"
    "COMMON_RESOURCE_SPEC_CPU-AMD"
)


def _filter_cpu_resources(
    records: Any,
    region: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Keep CPU records that match at least one requested region."""
    if not isinstance(records, list):
        return []

    requested_regions = set(region or [])
    filtered_records = []
    for record in records:
        if not isinstance(record, dict):
            continue

        extra = record.get("extra")
        if not isinstance(extra, dict) or extra.get("goodsResourceType") != "CPU":
            continue

        record_regions = record.get("region")
        if requested_regions and (
            not isinstance(record_regions, list) or requested_regions.isdisjoint(record_regions)
        ):
            continue

        filtered_records.append(record)

    return filtered_records


def _format_resource(record: dict[str, Any]) -> dict[str, Any]:
    """Select recommendation fields and build the SCNet goods detail URL."""
    extra = record.get("extra")
    if not isinstance(extra, dict):
        extra = {}

    goods_name = extra.get("goodsName") or record.get("nameCn")
    base_price = record.get("basePrice")
    try:
        is_free_trial = base_price is not None and float(base_price) == 0
    except (TypeError, ValueError):
        is_free_trial = False

    price = "免费试用" if is_free_trial else None
    if base_price is not None and not is_free_trial:
        price = f"{base_price}{record.get('priceUnit') or ''}"

    query_values = [
        ("type", "base"),
        ("common1", record.get("resource") or "RESOURCE"),
        ("id", record.get("id")),
        ("resource", record.get("resource") or "RESOURCE"),
        ("goodsId", extra.get("goodsId")),
        ("goodsName", goods_name),
        ("purchasingOption", extra.get("purchasingOption")),
        ("goodsType", extra.get("goodsType")),
        ("goodsResourceType", extra.get("goodsResourceType")),
        ("resourceType", extra.get("resourceType")),
        ("goodsResourceId", extra.get("goodsResourceId")),
    ]
    query = urlencode([(key, value) for key, value in query_values if value is not None])

    return {
        "goodsName": goods_name,
        "goodsId": extra.get("goodsId"),
        "description": record.get("desc"),
        "specifications": {
            "processor": extra.get("processor"),
            "memory": extra.get("memory"),
            "network": extra.get("network"),
            "price": price,
        },
        "resourceUrl": f"{SCNET_BASE_URL.rstrip('/')}{RESOURCE_DETAIL_PATH}?{query}",
    }


def _format_resources(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_format_resource(record) for record in records]


def _build_search_url(region: list[str] | None) -> str:
    query_values = [
        ("spec2", CPU_RESOURCE_SPEC),
        ("resource1", "COMMON_RESOURCE_TYPE-HPC"),
    ]
    if region:
        query_values.append(("region", ",".join(region)))

    query = urlencode(query_values, safe=",")
    return f"{SCNET_BASE_URL.rstrip('/')}{RESOURCE_MORE_PATH}?{query}"


def _build_result(
    records: list[dict[str, Any]],
    region: list[str] | None,
) -> dict[str, Any]:
    return {
        "records": _format_resources(records),
        "searchUrl": _build_search_url(region),
    }


def recommend_resources(
    keyWords: str = "",
    region: list[str] | None = None,
) -> dict[str, Any]:
    """Search SCNet resources and return CPU resource records only.

    Args:
        keyWords: Search keywords accepted by the SCNet full-text endpoint.
        region: Optional SCNet cluster/region ID list. An empty list searches
            without a region restriction.
    """
    payload = {
        "query": {
            "keyWords": keyWords,
            "pageNum": 1,
            "pageSize": 20,
        },
        "classify": {
            "resource": "RESOURCE",
            "region": list(region) if region is not None else [],
        },
        "sort": {},
    }
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "User-Agent": "PostmanRuntime-ApipostRuntime/1.1.0",
    }

    response = requests.post(
        f"{SCNET_BASE_URL.rstrip('/')}{RESOURCE_SEARCH_PATH}",
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    data = result.get("data", {}) if isinstance(result, dict) else {}
    records = data.get("records", []) if isinstance(data, dict) else []
    cpu_records = _filter_cpu_resources(records)
    if cpu_records:
        return _build_result(cpu_records, region)

    suggest_response = requests.post(
        f"{SCNET_BASE_URL.rstrip('/')}{RESOURCE_SUGGEST_PATH}",
        headers=headers,
        json={
            "resource": "RESOURCE",
            "pageNum": 1,
            "pageSize": 20,
            "keyWords": "CPU",
        },
        timeout=30,
    )
    suggest_response.raise_for_status()
    suggest_result = suggest_response.json()
    suggest_records = suggest_result.get("data", []) if isinstance(suggest_result, dict) else []
    return _build_result(_filter_cpu_resources(suggest_records, region), region)
