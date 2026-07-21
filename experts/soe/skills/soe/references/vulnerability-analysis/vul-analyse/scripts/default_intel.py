#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
default_intel.py —— vul-analyse 默认威胁情报工具

集成三个完全公开（无需任何 token）的权威威胁情报源：

  ┌──────────┬──────────────────────────────────────────────┬────────────────────────┐
  │  数据源  │  端点                                        │  维度                  │
  ├──────────┼──────────────────────────────────────────────┼────────────────────────┤
  │  NVD     │  https://services.nvd.nist.gov/rest/json/... │  CVE → CVSS/CWE/参考   │
  │  EPSS    │  https://api.first.org/data/v1/epss          │  CVE → 利用概率/百分位 │
  │  OSV     │  https://api.osv.dev/v1/query                │  package+version → 漏洞│
  └──────────┴──────────────────────────────────────────────┴────────────────────────┘

设计原则：
  1. 零凭据：三个源都是公开 API，无需任何 token 即可使用
     可选：环境变量 NVD_API_KEY 提升 NVD 限速 5→50 req/30s
  2. 限速控制：内置 token bucket 限速，避免触发 NVD 429
  3. 失败重试：网络抖动时指数退避，3 次失败后该 CVE 加入 query_errors
  4. 兼容 schema：输出与 references/mcp_guide.md 中 xti_results.json 兼容
                  扩展字段 epss_score / epss_percentile（EPSS 提供）
                  扩展字段 osv_advisories（仅 OSV 命中时提供）
  5. 与 intel_provider 叠加：用户配置 intel_provider 时不冲突，二者结果合并

调用方式：
  # 命令行：从 unique_cves.json 批量查询，输出 xti_results.json
  python3 default_intel.py query \\
      --from-unique-cves "$TASK_DIR/unique_cves.json" \\
      --output "$TASK_DIR/xti_results.json"

  # 命令行：直接传入 CVE 列表
  python3 default_intel.py query \\
      --cves CVE-2024-1234,CVE-2025-8194 \\
      --output xti_results.json

  # 健康检查：测试三个源连通性
  python3 default_intel.py validate

参数：
  --include-osv        启用 OSV 查询（需要 unique_cves.json 含 packages 字段）
  --nvd-api-key KEY    NVD API Key（也可通过 NVD_API_KEY 环境变量传入）
  --rate-limit-ms MS   覆盖默认限速间隔
  --timeout SEC        单次请求超时（默认 30s）

退出码：
  0  全部成功
  1  全部 CVE 查询失败（网络全不可达 / API 全部 5xx）
  2  参数错误 / 输入文件不存在
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

# ────────────────── API 端点常量 ──────────────────

NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
EPSS_API_BASE = "https://api.first.org/data/v1/epss"
OSV_API_BASE = "https://api.osv.dev/v1/query"

# ─── 内置默认 API Key（在线调用时 .env 无法加载，直接硬编码） ───
# NVD API Key：免费申请 https://nvd.nist.gov/developers/request-an-api-key
# 有 key 时限速从 5 req/30s 提升到 50 req/30s
DEFAULT_NVD_API_KEY = "31c0371a-c8bb-4efe-b8b8-ad6481740966"

# 默认限速（毫秒）：
#  - NVD 无 token：5 req/30s = 6000ms 间隔（保留 0.5s 缓冲）
#  - NVD 有 token：50 req/30s = 600ms 间隔
#  - EPSS / OSV：服务无明确限速，默认 100ms 友好间隔
NVD_INTERVAL_NO_KEY_MS = 6500
NVD_INTERVAL_WITH_KEY_MS = 700
EPSS_INTERVAL_MS = 100
OSV_INTERVAL_MS = 100

# 默认超时与重试
DEFAULT_TIMEOUT_SEC = 30
MAX_RETRIES = 3
BACKOFF_BASE_SEC = 2  # 指数退避基数：2s, 4s, 8s

# CVSS v3 严重度切分（与 NVD 标准一致）
CVSS_SEVERITY_BANDS = [
    (9.0, "critical"),
    (7.0, "high"),
    (4.0, "medium"),
    (0.1, "low"),
    (0.0, "none"),
]


def cvss_to_severity(score: Optional[float]) -> str:
    """CVSS v3 数值 → 标准严重度标签"""
    if score is None:
        return "unknown"
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "unknown"
    for threshold, label in CVSS_SEVERITY_BANDS:
        if s >= threshold:
            return label
    return "none"


# ────────────────── 简易 Token Bucket 限速器 ──────────────────


class RateLimiter:
    """单线程 token bucket 限速器，基于 monotonic 时钟。

    每个数据源用独立实例，避免相互阻塞。
    """

    def __init__(self, interval_ms: int):
        self.interval_sec = max(0.0, interval_ms / 1000.0)
        self._last_call = 0.0

    def wait(self) -> None:
        if self.interval_sec <= 0:
            return
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self.interval_sec:
            time.sleep(self.interval_sec - elapsed)
        self._last_call = time.monotonic()


# ────────────────── HTTP 客户端封装 ──────────────────


def _get_httpx():
    """延迟导入 httpx，便于在缺失依赖时给清晰错误。"""
    try:
        import httpx  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "未安装 httpx，请先 pip install httpx>=0.27"
        ) from e
    return httpx


def _request_with_retry(
    client: Any,
    method: str,
    url: str,
    *,
    params: Optional[dict] = None,
    json_body: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    max_retries: int = MAX_RETRIES,
) -> Optional[dict]:
    """带指数退避的 HTTP 请求。

    返回 JSON 解析后的 dict；非 2xx / 网络错误时返回 None。
    429 / 5xx 触发指数退避重试，4xx（除 429）直接放弃不重试。
    """
    httpx = _get_httpx()
    last_error = None
    for attempt in range(max_retries):
        try:
            resp = client.request(
                method,
                url,
                params=params,
                json=json_body,
                headers=headers,
                timeout=timeout,
            )
            if 200 <= resp.status_code < 300:
                return resp.json()
            # 429 与 5xx 触发退避重试
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                last_error = f"HTTP {resp.status_code}"
                if attempt < max_retries - 1:
                    sleep_sec = BACKOFF_BASE_SEC * (2**attempt)
                    # 优先使用 Retry-After 响应头
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            sleep_sec = max(sleep_sec, float(retry_after))
                        except ValueError:
                            pass
                    time.sleep(sleep_sec)
                    continue
                return None
            # 其他 4xx：客户端错误，重试无意义
            last_error = f"HTTP {resp.status_code}"
            return None
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            last_error = f"{type(e).__name__}: {e}"
            if attempt < max_retries - 1:
                time.sleep(BACKOFF_BASE_SEC * (2**attempt))
                continue
            return None
        except Exception as e:
            # 其他异常（解析错误等）不重试
            last_error = f"{type(e).__name__}: {e}"
            return None
    _ = last_error  # 保留供调试，但不抛出（调用方根据 None 判断失败）
    return None


# ────────────────── 数据源 1：NVD ──────────────────


def fetch_nvd(
    cve_id: str,
    client: Any,
    rate_limiter: RateLimiter,
    api_key: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT_SEC,
) -> Optional[dict]:
    """查询 NVD，返回标准化的 CVE 详情 dict。

    返回字段：
      - cvss_score:    CVSS v3 baseScore（float 或 None）
      - threat_level:  严重度标签（critical/high/medium/low/none/unknown）
      - cwe_ids:       关联的 CWE 编号列表
      - description:   英文描述
      - references:    参考链接列表
      - published:     发布时间（ISO 8601）

    查询失败返回 None。
    """
    rate_limiter.wait()
    headers = {}
    if api_key:
        headers["apiKey"] = api_key
    raw = _request_with_retry(
        client,
        "GET",
        NVD_API_BASE,
        params={"cveId": cve_id},
        headers=headers,
        timeout=timeout,
    )
    if not raw or not isinstance(raw, dict):
        return None
    vulns = raw.get("vulnerabilities") or []
    if not vulns:
        return None  # CVE 在 NVD 中不存在

    cve_obj = (vulns[0] or {}).get("cve") or {}
    metrics = cve_obj.get("metrics") or {}

    # 优先 CVSS v3.1，其次 v3.0，最后 v2
    cvss_score = None
    threat_level = None
    for key in ("cvssMetricV31", "cvssMetricV30"):
        items = metrics.get(key) or []
        if items:
            data = (items[0] or {}).get("cvssData") or {}
            cvss_score = data.get("baseScore")
            threat_level = (data.get("baseSeverity") or "").lower() or None
            break
    if cvss_score is None:
        v2 = metrics.get("cvssMetricV2") or []
        if v2:
            data = (v2[0] or {}).get("cvssData") or {}
            cvss_score = data.get("baseScore")
    if not threat_level:
        threat_level = cvss_to_severity(cvss_score)

    # CWE 列表
    cwe_ids = []
    for w in cve_obj.get("weaknesses") or []:
        for d in w.get("description") or []:
            val = (d.get("value") or "").strip()
            if val.startswith("CWE-"):
                cwe_ids.append(val)

    # 英文描述
    description = ""
    for d in cve_obj.get("descriptions") or []:
        if d.get("lang") == "en":
            description = (d.get("value") or "").strip()
            break

    # 参考链接
    references = [
        (r.get("url") or "").strip()
        for r in (cve_obj.get("references") or [])
        if r.get("url")
    ]

    return {
        "cvss_score": cvss_score,
        "threat_level": threat_level,
        "cwe_ids": cwe_ids,
        "description": description,
        "references": references[:10],  # 最多保留 10 条避免膨胀
        "published": cve_obj.get("published") or "",
    }


# ────────────────── 数据源 2：EPSS ──────────────────


def fetch_epss(
    cve_ids: list,
    client: Any,
    rate_limiter: RateLimiter,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    batch_size: int = 100,
) -> dict:
    """批量查询 EPSS，返回 {cve_id: {epss_score, epss_percentile}} 映射。

    EPSS API 支持单次最多 100 个 CVE 批量查询（用逗号分隔），效率远高于单查。
    未收录的 CVE 在返回 dict 中不出现，调用方需用 .get() 容错。
    """
    if not cve_ids:
        return {}
    out: dict[str, dict] = {}
    for i in range(0, len(cve_ids), batch_size):
        batch = cve_ids[i : i + batch_size]
        rate_limiter.wait()
        raw = _request_with_retry(
            client,
            "GET",
            EPSS_API_BASE,
            params={"cve": ",".join(batch)},
            timeout=timeout,
        )
        if not raw or not isinstance(raw, dict):
            continue
        for item in raw.get("data") or []:
            cve_id = item.get("cve")
            if not cve_id:
                continue
            try:
                score = float(item.get("epss") or 0)
                percentile = float(item.get("percentile") or 0)
            except (TypeError, ValueError):
                continue
            out[cve_id] = {
                "epss_score": round(score, 4),
                "epss_percentile": round(percentile, 4),
            }
    return out


# ────────────────── 数据源 3：OSV ──────────────────


# 简易 ecosystem 推断（按文件后缀/包名特征）
_ECOSYSTEM_HINTS = [
    (".jar", "Maven"),
    (".war", "Maven"),
    (".whl", "PyPI"),
    (".egg", "PyPI"),
    (".gem", "RubyGems"),
    (".crate", "crates.io"),
]


def infer_ecosystem(package_name: str) -> Optional[str]:
    """按包名后缀启发式推断 ecosystem。无法推断时返回 None。"""
    name_lower = (package_name or "").lower()
    for suffix, eco in _ECOSYSTEM_HINTS:
        if name_lower.endswith(suffix):
            return eco
    return None


def fetch_osv(
    package_name: str,
    version: str,
    ecosystem: str,
    client: Any,
    rate_limiter: RateLimiter,
    timeout: float = DEFAULT_TIMEOUT_SEC,
) -> Optional[list]:
    """查询 OSV，返回该 (package, version) 对应的漏洞 advisory 列表。

    返回 list of {id, summary, severity, references}，未命中返回空列表，
    查询失败返回 None。
    """
    if not package_name or not version or not ecosystem:
        return None
    rate_limiter.wait()
    body = {
        "package": {"name": package_name, "ecosystem": ecosystem},
        "version": version,
    }
    raw = _request_with_retry(
        client,
        "POST",
        OSV_API_BASE,
        json_body=body,
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    if raw is None or not isinstance(raw, dict):
        return None
    advisories = []
    for vuln in raw.get("vulns") or []:
        # 优先取 CVSS_V3 严重度
        sev_score = None
        for s in vuln.get("severity") or []:
            if s.get("type") in ("CVSS_V3", "CVSS_V4"):
                sev_score = s.get("score")
                break
        advisories.append(
            {
                "id": vuln.get("id"),
                "summary": (vuln.get("summary") or "")[:200],
                "severity": sev_score,
                "references": [
                    (r.get("url") or "").strip()
                    for r in (vuln.get("references") or [])
                    if r.get("url")
                ][:5],
            }
        )
    return advisories


# ────────────────── 聚合层：对外统一入口 ──────────────────


def query_intel(
    cve_list: list,
    output_path: Path,
    packages: Optional[list] = None,
    nvd_api_key: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    rate_limit_ms_override: Optional[int] = None,
) -> dict:
    """聚合查询 NVD + EPSS + (可选) OSV，写出 xti_results.json。

    :param cve_list: 待查询的 CVE 编号列表（建议来自 unique_cves.json.cve_list）
    :param output_path: 输出文件路径（与现有 xti_results.json schema 兼容）
    :param packages: 可选的 [{name, version, ecosystem}] 列表，触发 OSV 查询
    :param nvd_api_key: 可选 NVD API Key（参数 > 环境变量 NVD_API_KEY）
    :param timeout: 单次请求超时
    :param rate_limit_ms_override: 覆盖默认 NVD 限速（调试用）
    :return: 写出的结果 dict
    """
    httpx = _get_httpx()

    # 凭据来源优先级：参数 > 环境变量 > 内置默认值
    api_key = nvd_api_key or os.environ.get("NVD_API_KEY") or DEFAULT_NVD_API_KEY
    nvd_interval = (
        rate_limit_ms_override
        if rate_limit_ms_override is not None
        else (NVD_INTERVAL_WITH_KEY_MS if api_key else NVD_INTERVAL_NO_KEY_MS)
    )
    nvd_limiter = RateLimiter(nvd_interval)
    epss_limiter = RateLimiter(EPSS_INTERVAL_MS)
    osv_limiter = RateLimiter(OSV_INTERVAL_MS)

    results = []
    query_errors = []
    hit_count = 0

    with httpx.Client(
        headers={"User-Agent": "vul-analyse-default-intel/1.0"}
    ) as client:
        # 批量预查 EPSS（一次 100 个），减少请求数
        epss_map = fetch_epss(cve_list, client, epss_limiter, timeout=timeout)

        # 逐个查 NVD（限速保护）
        for cve_id in cve_list:
            nvd_data = fetch_nvd(
                cve_id, client, nvd_limiter, api_key=api_key, timeout=timeout
            )
            epss_data = epss_map.get(cve_id, {})

            if nvd_data is None and not epss_data:
                query_errors.append(
                    {"cve_id": cve_id, "reason": "all sources failed"}
                )
                continue

            entry = {
                "cve_id": cve_id,
                "found": nvd_data is not None,
                "source": "nvd+epss",
            }
            if nvd_data:
                entry.update(
                    {
                        "cvss_score": nvd_data["cvss_score"],
                        "threat_level": nvd_data["threat_level"],
                        "cwe_ids": nvd_data["cwe_ids"],
                        "fix_advice": nvd_data["description"],
                        "references": nvd_data["references"],
                        "published": nvd_data["published"],
                    }
                )
            if epss_data:
                entry["epss_score"] = epss_data["epss_score"]
                entry["epss_percentile"] = epss_data["epss_percentile"]
                # 标记是否进入 EPSS 高风险（百分位 > 0.95）
                entry["has_public_exploit"] = (
                    epss_data["epss_percentile"] > 0.95
                )
            results.append(entry)
            if entry["found"]:
                hit_count += 1

        # OSV 仅在 packages 提供时查询
        osv_results = []
        if packages:
            for pkg in packages:
                name = pkg.get("name") or ""
                version = pkg.get("version") or ""
                ecosystem = pkg.get("ecosystem") or infer_ecosystem(name) or ""
                if not (name and version and ecosystem):
                    continue
                advisories = fetch_osv(
                    name, version, ecosystem, client, osv_limiter, timeout=timeout
                )
                if advisories is None:
                    query_errors.append(
                        {
                            "package": f"{name}@{version}",
                            "reason": "osv query failed",
                        }
                    )
                    continue
                osv_results.append(
                    {
                        "package": name,
                        "version": version,
                        "ecosystem": ecosystem,
                        "advisories": advisories,
                    }
                )

    payload = {
        "provider": "default_intel",
        "sources": ["nvd", "epss"] + (["osv"] if packages else []),
        "queried_count": len(cve_list),
        "hit_count": hit_count,
        "hit_rate": (
            round(hit_count / len(cve_list), 4) if cve_list else 0.0
        ),
        "results": results,
        "query_errors": query_errors,
    }
    if osv_results:
        payload["osv_results"] = osv_results

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


# ────────────────── CLI ──────────────────


def _load_cves_from_unique(path: Path) -> tuple:
    """从 unique_cves.json 加载 cve_list 与可选 packages。

    返回 (cve_list, packages_or_none)。
    """
    if not path.exists():
        raise FileNotFoundError(f"unique_cves.json 不存在: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    cve_list = []
    for item in data.get("cve_list") or []:
        if isinstance(item, dict):
            cve_id = item.get("cve_id") or item.get("id")
        else:
            cve_id = item
        if cve_id:
            cve_list.append(cve_id)
    packages = data.get("packages") or None  # 漏扫报告通常没有，OSV 自然跳过
    return cve_list, packages


def _cmd_query(args: argparse.Namespace) -> int:
    if args.from_unique_cves:
        try:
            cve_list, packages = _load_cves_from_unique(
                Path(args.from_unique_cves)
            )
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ 输入文件错误: {e}", file=sys.stderr)
            return 2
    elif args.cves:
        cve_list = [c.strip() for c in args.cves.split(",") if c.strip()]
        packages = None
    else:
        print(
            "❌ 必须指定 --cves 或 --from-unique-cves 之一", file=sys.stderr
        )
        return 2

    if not cve_list:
        print("❌ 输入 CVE 列表为空", file=sys.stderr)
        return 2

    if not args.include_osv:
        packages = None  # 显式禁用 OSV

    output_path = Path(args.output)
    try:
        result = query_intel(
            cve_list=cve_list,
            output_path=output_path,
            packages=packages,
            nvd_api_key=args.nvd_api_key,
            timeout=args.timeout,
            rate_limit_ms_override=args.rate_limit_ms,
        )
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2

    total = result["queried_count"]
    hit = result["hit_count"]
    errors = len(result["query_errors"])
    print(
        f"✅ 查询完成：{hit}/{total} 命中"
        f"（命中率 {result['hit_rate']:.1%}），失败 {errors} 条"
    )
    print(f"   输出文件：{output_path}")
    print(f"   数据源：{', '.join(result['sources'])}")
    return 0 if hit > 0 or total == 0 else 1


def _cmd_validate(args: argparse.Namespace) -> int:
    """连通性自检：分别 ping 三个 API。"""
    httpx = _get_httpx()
    api_key = args.nvd_api_key or os.environ.get("NVD_API_KEY") or DEFAULT_NVD_API_KEY
    print("🔍 默认情报源连通性检查\n")
    results = []
    test_cve = "CVE-2024-1234"
    with httpx.Client(timeout=10) as client:
        # NVD
        nvd_headers = {"apiKey": api_key} if api_key else {}
        r = _request_with_retry(
            client,
            "GET",
            NVD_API_BASE,
            params={"cveId": test_cve},
            headers=nvd_headers,
            timeout=10,
            max_retries=1,
        )
        results.append(("NVD", r is not None, NVD_API_BASE))
        # EPSS
        r = _request_with_retry(
            client,
            "GET",
            EPSS_API_BASE,
            params={"cve": test_cve},
            timeout=10,
            max_retries=1,
        )
        results.append(("EPSS", r is not None, EPSS_API_BASE))
        # OSV
        r = _request_with_retry(
            client,
            "POST",
            OSV_API_BASE,
            json_body={
                "package": {"name": "log4j-core", "ecosystem": "Maven"},
                "version": "2.14.0",
            },
            timeout=10,
            max_retries=1,
        )
        results.append(("OSV", r is not None, OSV_API_BASE))

    all_ok = True
    for name, ok, url in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name:<6} {url}")
        if not ok:
            all_ok = False
    print()
    print(
        f"  NVD API Key: {'已配置（限速 50 req/30s）' if api_key else '未配置（限速 5 req/30s）'}"
    )
    return 0 if all_ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="vul-analyse 默认威胁情报工具（NVD + EPSS + OSV）"
    )
    p.add_argument(
        "--nvd-api-key",
        type=str,
        default=None,
        help="NVD API Key（也可通过 NVD_API_KEY 环境变量传入）",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SEC,
        help=f"单次请求超时秒数（默认 {DEFAULT_TIMEOUT_SEC}）",
    )

    sub = p.add_subparsers(dest="command", required=True)

    # query 子命令
    qp = sub.add_parser("query", help="批量查询威胁情报")
    qp.add_argument(
        "--cves",
        type=str,
        default=None,
        help="逗号分隔的 CVE 列表，如 CVE-2024-1234,CVE-2025-8194",
    )
    qp.add_argument(
        "--from-unique-cves",
        type=str,
        default=None,
        help="从 unique_cves.json 读取 cve_list",
    )
    qp.add_argument(
        "--output",
        type=str,
        required=True,
        help="输出文件路径（xti_results.json 兼容格式）",
    )
    qp.add_argument(
        "--include-osv",
        action="store_true",
        help="启用 OSV 查询（需要 unique_cves.json 含 packages 字段）",
    )
    qp.add_argument(
        "--rate-limit-ms",
        type=int,
        default=None,
        help="覆盖 NVD 限速间隔（毫秒），默认按是否有 API Key 自动选择",
    )

    # validate 子命令
    sub.add_parser("validate", help="检查三个数据源的连通性")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "query":
        return _cmd_query(args)
    if args.command == "validate":
        return _cmd_validate(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
