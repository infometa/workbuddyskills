#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WAF Attack Log Analyzer (Tencent Cloud WAF, Chinese export format).

Inputs:  single CSV file or directory containing CSVs
Outputs: report.md (concise) + report.html (detailed, with SVG charts)

Pure Python stdlib only (csv, json, urllib, ipaddress, datetime, html, etc.).
Threat-intel enrichment uses ip-api.com (free, read-only) for public IPs.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import ipaddress
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# --- Constants -------------------------------------------------------------

EXPECTED_HEADER = [
    "攻击IP", "被攻击域名", "URI", "方法", "攻击类型",
    "攻击内容", "UserAgent", "APPID", "uuid", "动作",
    "风险等级", "攻击时间",
]

CLI_UA_PATTERNS = re.compile(
    r"^(curl|wget|python-requests|httpie|postman|Go-http-client|Java/|Apache-HttpClient)",
    re.I,
)

TEST_DOMAIN_KEYWORDS = ("test", "demo", "dev", "staging", "ngwaftest", "uat", "qa")

SIMPLE_PAYLOADS = {
    "alert(1)", "alert(1", "1 union select", "id=1 and 1=1",
    "id=1 AND 1=1", "1=1", "or 1=1", "<script>", "../../",
}

OBFUSCATION_HINTS = re.compile(
    r"(%[0-9a-fA-F]{2}.*%[0-9a-fA-F]{2}|/\*!|"
    r"&#x?\d+;|\\u00[0-9a-f]{2}|"
    r"char\s*\(|0x[0-9a-fA-F]{4,}|base64,|"
    r"concat\s*\(|substring\s*\(|"
    r"%[uU][0-9a-fA-F]{4})",
)


# --- Parsing ---------------------------------------------------------------

SUPPORTED_EXTS = (".csv", ".xlsx")


def collect_input_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() not in SUPPORTED_EXTS:
            sys.exit(f"[ERROR] unsupported file type: {input_path} (need .csv or .xlsx)")
        return [input_path]
    if input_path.is_dir():
        files = sorted(
            p for p in input_path.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
        )
        if not files:
            sys.exit(f"[ERROR] no .csv/.xlsx under directory: {input_path}")
        return files
    sys.exit(f"[ERROR] path does not exist: {input_path}")


# Backward-compat alias
collect_csv_files = collect_input_files


def _validate_header(header: list[str], path: Path) -> None:
    header = [h.strip() for h in header]
    if header != EXPECTED_HEADER:
        sys.exit(
            f"[ERROR] unexpected header in {path}\n"
            f"  expected: {EXPECTED_HEADER}\n"
            f"  got:      {header}\n"
            f"  This skill only supports Tencent Cloud WAF Chinese export format."
        )


def _normalize_row(header: list[str], values: list[str]) -> dict[str, str]:
    values = (values + [""] * len(header))[: len(header)]
    row = {k: (v or "").strip() for k, v in zip(header, values)}
    # Strip trailing tab artifacts seen in WAF exports
    row["APPID"] = row["APPID"].rstrip("\t").strip()
    row["攻击时间"] = row["攻击时间"].rstrip("\t").strip()
    return row


def read_csv(path: Path) -> list[dict[str, str]]:
    # Tencent Cloud WAF CSVs are UTF-8 with BOM
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return []
        _validate_header(header, path)
        rows: list[dict[str, str]] = []
        for line in reader:
            if not line or all(not c.strip() for c in line):
                continue
            rows.append(_normalize_row(EXPECTED_HEADER, line))
        return rows


def read_xlsx(path: Path) -> list[dict[str, str]]:
    """Parse Tencent Cloud WAF .xlsx export using stdlib only (zipfile + ElementTree)."""
    import zipfile
    import xml.etree.ElementTree as ET

    NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

    def col_index(ref: str) -> int:
        # e.g. "A1" -> 0, "AA12" -> 26
        letters = ""
        for ch in ref:
            if ch.isalpha():
                letters += ch
            else:
                break
        idx = 0
        for ch in letters:
            idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
        return idx - 1

    with zipfile.ZipFile(path) as z:
        # Shared strings
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            with z.open("xl/sharedStrings.xml") as f:
                tree = ET.parse(f)
            for si in tree.getroot().findall(f"{NS}si"):
                shared.append("".join((t.text or "") for t in si.iter(f"{NS}t")))

        # Pick first worksheet relationship target
        sheet_path = "xl/worksheets/sheet1.xml"
        if sheet_path not in z.namelist():
            # find any worksheet xml
            for n in z.namelist():
                if n.startswith("xl/worksheets/") and n.endswith(".xml"):
                    sheet_path = n
                    break

        rows_raw: list[list[str]] = []
        with z.open(sheet_path) as f:
            tree = ET.parse(f)
        for r in tree.getroot().findall(f".//{NS}sheetData/{NS}row"):
            cells: list[str] = []
            max_col = -1
            buf: dict[int, str] = {}
            for c in r.findall(f"{NS}c"):
                ref = c.get("r", "")
                ci = col_index(ref) if ref else len(buf)
                t = c.get("t", "n")
                v = c.find(f"{NS}v")
                inline = c.find(f"{NS}is")
                if t == "s" and v is not None:
                    try:
                        text = shared[int(v.text)] if v.text is not None else ""
                    except (IndexError, ValueError):
                        text = ""
                elif t == "inlineStr" or inline is not None:
                    text = "".join((x.text or "") for x in (inline.iter(f"{NS}t") if inline is not None else []))
                elif v is not None:
                    text = v.text or ""
                else:
                    text = ""
                buf[ci] = text
                if ci > max_col:
                    max_col = ci
            cells = [buf.get(i, "") for i in range(max_col + 1)]
            rows_raw.append(cells)

    if not rows_raw:
        return []
    header = [h.strip() for h in rows_raw[0]]
    _validate_header(header, path)
    out: list[dict[str, str]] = []
    for line in rows_raw[1:]:
        if not line or all(not (c or "").strip() for c in line):
            continue
        out.append(_normalize_row(EXPECTED_HEADER, line))
    return out


def read_any(path: Path) -> list[dict[str, str]]:
    ext = path.suffix.lower()
    if ext == ".csv":
        return read_csv(path)
    if ext == ".xlsx":
        return read_xlsx(path)
    sys.exit(f"[ERROR] unsupported file type: {path}")


def parse_ts(raw: str) -> dt.datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    # millisecond epoch
    if raw.isdigit():
        try:
            v = int(raw)
            if v > 10**12:
                v //= 1000
            return dt.datetime.fromtimestamp(v)
        except (ValueError, OSError, OverflowError):
            return None
    return None


# --- Classification helpers ------------------------------------------------

def is_private_ip(ip: str) -> bool:
    try:
        obj = ipaddress.ip_address(ip)
        return (
            obj.is_private or obj.is_loopback
            or obj.is_link_local or obj.is_reserved
            or obj.is_multicast
        )
    except ValueError:
        return True  # treat unparsable as non-public; skip enrichment


def is_simple_payload(content: str) -> bool:
    c = (content or "").strip().lower()
    if not c:
        return True
    for s in SIMPLE_PAYLOADS:
        if s.lower() in c:
            return True
    # Treat IP-only or path-only custom-policy hits as simple
    if re.fullmatch(r"[\d./:]+", c):
        return True
    if re.fullmatch(r"/[a-z0-9_/.-]*", c):
        return True
    # WAF system / policy match signatures (not real attacker payload)
    if "ip penalty" in c or "ip-match-" in c or "ip-127" in c \
            or "session-" in c or c.startswith("ip-"):
        return True
    return False


def has_obfuscation(content: str) -> bool:
    if not content:
        return False
    return bool(OBFUSCATION_HINTS.search(content))


# --- Verdict (heuristic authenticity assessment) ---------------------------

def verdict(rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return {"label": "无数据", "score_test": 0, "score_real": 0,
                "test_signals": [], "real_signals": []}

    ips = [r["攻击IP"] for r in rows if r["攻击IP"]]
    uas = [r["UserAgent"] for r in rows if r["UserAgent"]]
    domains = [r["被攻击域名"] for r in rows if r["被攻击域名"]]
    types = [r["攻击类型"] for r in rows if r["攻击类型"]]
    actions = [r["动作"] for r in rows if r["动作"]]
    contents = [r["攻击内容"] for r in rows]

    test_signals: list[str] = []
    real_signals: list[str] = []

    # === test signals ===
    if ips and all(is_private_ip(ip) for ip in ips):
        test_signals.append("全部源 IP 为内网/回环/保留地址")

    ua_set = set(uas)
    if len(ua_set) == 1 and CLI_UA_PATTERNS.match(next(iter(ua_set), "")):
        test_signals.append(f"UA 单一且为命令行工具：{next(iter(ua_set))}")

    if contents:
        simple_ratio = sum(1 for c in contents if is_simple_payload(c)) / len(contents)
        if simple_ratio >= 0.9:
            test_signals.append(f"Payload 中 {simple_ratio:.0%} 为最简/教科书形态")

    if any(any(k in d.lower() for k in TEST_DOMAIN_KEYWORDS) for d in domains):
        test_signals.append("域名包含 test/demo/dev/staging/ngwaftest 等测试关键词")

    type_counter = Counter(types)
    if len(type_counter) >= 4:
        top_share = type_counter.most_common(1)[0][1] / max(len(types), 1)
        if top_share <= 0.45:
            test_signals.append("攻击类型分布过于均衡（疑似逐规则验证）")

    custom_policy = sum(1 for t in types if "自定义" in t)
    if types and custom_policy / len(types) > 0.30:
        test_signals.append(
            f"自定义策略命中占比 {custom_policy/len(types):.0%}（>30% 通常为自测）"
        )

    # === real-attack signals ===
    public_ips = [ip for ip in set(ips) if not is_private_ip(ip)]
    if public_ips:
        real_signals.append(f"存在公网攻击源 IP（{len(public_ips)} 个）")

    if len(ua_set) >= 5:
        real_signals.append(f"UA 多样化（共 {len(ua_set)} 种），存在伪装迹象")

    if any(has_obfuscation(c) for c in contents):
        real_signals.append("Payload 中检出混淆/编码特征")

    # one IP touching many attack types
    ip_to_types: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        ip_to_types[r["攻击IP"]].add(r["攻击类型"])
    diverse_ips = [ip for ip, ts in ip_to_types.items() if len(ts) >= 4]
    if diverse_ips:
        real_signals.append(
            f"{len(diverse_ips)} 个 IP 单独覆盖 ≥4 类攻击（疑似侦察→利用模式）"
        )

    bypass = [r for r in rows
              if r["动作"] not in ("拦截",) and r["风险等级"] == "高危"]
    # exclude rows from domains that are entirely observe-only (config anomaly,
    # not a regex bypass) — but still surface count separately downstream
    domain_block_rate: dict[str, float] = {}
    domain_total: dict[str, int] = defaultdict(int)
    domain_blocked: dict[str, int] = defaultdict(int)
    for r in rows:
        domain_total[r["被攻击域名"]] += 1
        if r["动作"] == "拦截":
            domain_blocked[r["被攻击域名"]] += 1
    for d, t in domain_total.items():
        domain_block_rate[d] = (domain_blocked[d] / t) if t else 0
    real_bypass = [r for r in bypass
                   if domain_total[r["被攻击域名"]] < 50
                   or domain_block_rate[r["被攻击域名"]] >= 0.05]
    if real_bypass:
        real_signals.append(f"存在 {len(real_bypass)} 条 高危但未拦截 记录（疑似绕过/观察模式）")

    # automation rhythm: many sub-second intervals from one IP
    fast_burst_ips = 0
    by_ip = defaultdict(list)
    for r in rows:
        ts = parse_ts(r["攻击时间"])
        if ts:
            by_ip[r["攻击IP"]].append(ts)
    for ip, ts_list in by_ip.items():
        ts_list.sort()
        sub_sec = sum(
            1 for a, b in zip(ts_list, ts_list[1:])
            if (b - a).total_seconds() < 1.5
        )
        if sub_sec >= 5:
            fast_burst_ips += 1
    if fast_burst_ips >= 1:
        real_signals.append(f"{fast_burst_ips} 个 IP 出现亚秒级高频请求（自动化节奏）")

    # === decide label ===
    # Strong-override: if UA is uniformly a CLI tool AND domain looks like a
    # test environment, this is almost certainly self-testing — even if other
    # noisy signals (geo-block test IPs, sub-second curl loops, observe-mode
    # custom rules) push the "real attack" counter up.
    cli_only_ua = (len(ua_set) == 1 and CLI_UA_PATTERNS.match(next(iter(ua_set), "")))
    test_domain_hit = any(
        any(k in d.lower() for k in TEST_DOMAIN_KEYWORDS) for d in domains
    )
    if cli_only_ua and test_domain_hit:
        label = "测试流量"
    elif len(test_signals) >= 3 and len(real_signals) <= 1:
        label = "测试流量"
    elif len(real_signals) >= 2:
        label = "真实定向攻击（建议人工复核）"
    else:
        label = "自动化扫描器流量"

    return {
        "label": label,
        "test_signals": test_signals,
        "real_signals": real_signals,
        "score_test": len(test_signals),
        "score_real": len(real_signals),
    }


# --- Threat intel enrichment ----------------------------------------------

def enrich_ips(ips: list[str], enabled: bool = True) -> dict[str, dict[str, str]]:
    """Look up ASN / country / org for public IPs via ip-api.com (free)."""
    info: dict[str, dict[str, str]] = {}
    if not enabled:
        return info
    for ip in ips:
        if is_private_ip(ip):
            info[ip] = {"country": "-", "org": "内网/保留地址", "asn": "-", "isp": "-"}
            continue
        try:
            url = (
                f"http://ip-api.com/json/{urllib.parse.quote(ip)}"
                "?fields=status,country,org,as,isp&lang=zh-CN"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "waf-log-analyzer/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                info[ip] = {
                    "country": data.get("country", "-") or "-",
                    "org": data.get("org", "-") or "-",
                    "asn": data.get("as", "-") or "-",
                    "isp": data.get("isp", "-") or "-",
                }
            else:
                info[ip] = {"country": "-", "org": "-", "asn": "-", "isp": "-"}
        except Exception:
            info[ip] = {"country": "-", "org": "查询失败", "asn": "-", "isp": "-"}
        # ip-api.com free tier: max 45/min
        time.sleep(1.5)
    return info


# --- Aggregations ----------------------------------------------------------

def aggregate(rows: list[dict[str, str]]) -> dict[str, Any]:
    if not rows:
        return {}

    type_counter = Counter(r["攻击类型"] for r in rows if r["攻击类型"])
    ip_counter = Counter(r["攻击IP"] for r in rows if r["攻击IP"])
    uri_counter = Counter(r["URI"] for r in rows if r["URI"])
    domain_counter = Counter(r["被攻击域名"] for r in rows if r["被攻击域名"])
    appid_counter = Counter(r["APPID"] for r in rows if r["APPID"])
    action_counter = Counter(r["动作"] for r in rows if r["动作"])
    ua_counter = Counter(r["UserAgent"] for r in rows if r["UserAgent"])

    times = [parse_ts(r["攻击时间"]) for r in rows]
    times = [t for t in times if t]
    time_min = min(times) if times else None
    time_max = max(times) if times else None

    # hourly distribution
    hourly: dict[str, int] = defaultdict(int)
    for t in times:
        hourly[t.strftime("%Y-%m-%d %H:00")] += 1

    # per-IP profile (only top-15 to keep big files fast)
    ip_profile: dict[str, dict[str, Any]] = {}
    rows_by_ip: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        rows_by_ip[r["攻击IP"]].append(r)
    for ip, _ in ip_counter.most_common(15):
        ip_rows = rows_by_ip[ip]
        ip_times = sorted(t for t in (parse_ts(r["攻击时间"]) for r in ip_rows) if t)
        first = ip_times[0] if ip_times else None
        last = ip_times[-1] if ip_times else None
        intervals = [(b - a).total_seconds() for a, b in zip(ip_times, ip_times[1:])]
        avg_iv = sum(intervals) / len(intervals) if intervals else 0
        ip_profile[ip] = {
            "count": len(ip_rows),
            "types": Counter(r["攻击类型"] for r in ip_rows),
            "domains": Counter(r["被攻击域名"] for r in ip_rows),
            "uas": Counter(r["UserAgent"] for r in ip_rows),
            "uris": Counter(r["URI"] for r in ip_rows),
            "actions": Counter(r["动作"] for r in ip_rows),
            "first": first,
            "last": last,
            "avg_interval_sec": round(avg_iv, 2),
        }

    # suspected bypass events: action != 拦截 OR same IP with many types
    bypass_rows = [
        r for r in rows
        if r["动作"] not in ("拦截",) and r["风险等级"] == "高危"
    ]

    # business impact: per domain & per APPID — group once for O(N)
    rows_by_domain: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        rows_by_domain[r["被攻击域名"]].append(r)
    domain_impact = []
    observe_only_domains: list[dict[str, Any]] = []
    for d, c in domain_counter.most_common():
        d_rows = rows_by_domain[d]
        blocked = sum(1 for r in d_rows if r["动作"] == "拦截")
        block_rate = (blocked / c) if c else 0
        high = sum(1 for r in d_rows if r["风险等级"] == "高危")
        item = {
            "domain": d,
            "count": c,
            "blocked": blocked,
            "block_rate": block_rate,
            "high": high,
            "appids": list({r["APPID"] for r in d_rows if r["APPID"]}),
        }
        domain_impact.append(item)
        # Observe-only configuration anomaly: a whole domain with 0% block-rate
        # AND ≥ 50 high-risk records is almost certainly a misconfigured rule
        # group running in observe mode in production.
        if c >= 50 and block_rate < 0.05 and high >= 50:
            observe_only_domains.append(item)

    # Scanner fingerprint detection
    SCANNER_URI_PATTERNS = [
        ("/HNAP1", "D-Link/Realtek HNAP 路由器漏洞探测"),
        ("/sdk", "VMware vCenter / 路由器 SDK 探测"),
        ("/evox/about", "Niagara/Tridium 工控 SDK 探测"),
        ("eval-stdin.php", "PHPUnit RCE (CVE-2017-9841) 探测"),
        ("/.git/", "Git 源码泄露探测"),
        ("/.env", ".env 配置泄露探测"),
        ("/actuator", "Spring Boot Actuator 信息泄露探测"),
        ("/druid/", "Druid 监控页面探测"),
        ("/wp-admin", "WordPress 后台探测"),
        ("/wp-login.php", "WordPress 后台探测"),
        ("/phpmyadmin", "phpMyAdmin 探测"),
        ("/solr/", "Apache Solr 漏洞探测"),
        ("/console", "管理后台探测"),
        ("/swagger", "Swagger API 文档泄露探测"),
        ("/.well-known", ".well-known 路径扫描"),
        ("/jenkins", "Jenkins 探测"),
    ]
    SCANNER_UA_PATTERNS = [
        ("nmap", "Nmap"),
        ("masscan", "masscan"),
        ("zgrab", "zgrab"),
        ("nuclei", "Nuclei"),
        ("sqlmap", "sqlmap"),
        ("nikto", "Nikto"),
        ("acunetix", "Acunetix"),
        ("nessus", "Nessus"),
        ("burpsuite", "Burp Suite"),
        ("xray", "xray"),
        ("censys", "Censys"),
        ("shodan", "Shodan"),
        ("paloaltonetworks.com", "Palo Alto Expanse 扫描器"),
        ("internet-measurement.com", "互联网测绘扫描器"),
    ]
    scanner_hits: dict[str, dict[str, Any]] = {}
    for r in rows:
        uri = (r.get("URI") or "").lower()
        ua = (r.get("UserAgent") or "").lower()
        ip = r.get("攻击IP", "")
        for pat, label in SCANNER_URI_PATTERNS:
            if pat.lower() in uri:
                k = f"URI:{label}"
                d = scanner_hits.setdefault(k, {"label": label, "kind": "URI",
                                                "pattern": pat, "count": 0, "ips": set()})
                d["count"] += 1
                d["ips"].add(ip)
        for pat, label in SCANNER_UA_PATTERNS:
            if pat in ua:
                k = f"UA:{label}"
                d = scanner_hits.setdefault(k, {"label": label, "kind": "UA",
                                                "pattern": pat, "count": 0, "ips": set()})
                d["count"] += 1
                d["ips"].add(ip)
    scanner_list = sorted(
        ({"label": v["label"], "kind": v["kind"], "pattern": v["pattern"],
          "count": v["count"], "ip_count": len(v["ips"])}
         for v in scanner_hits.values()),
        key=lambda x: x["count"], reverse=True,
    )

    # Risk grade distribution
    risk_counter = Counter(r["风险等级"] for r in rows if r["风险等级"])

    return {
        "total": len(rows),
        "time_min": time_min,
        "time_max": time_max,
        "type_counter": type_counter,
        "ip_counter": ip_counter,
        "uri_counter": uri_counter,
        "domain_counter": domain_counter,
        "appid_counter": appid_counter,
        "action_counter": action_counter,
        "ua_counter": ua_counter,
        "risk_counter": risk_counter,
        "hourly": dict(sorted(hourly.items())),
        "ip_profile": ip_profile,
        "bypass_rows": bypass_rows,
        "domain_impact": domain_impact,
        "observe_only_domains": observe_only_domains,
        "scanner_list": scanner_list,
    }


# --- Generic remediation knowledge base ------------------------------------

GENERIC_REMEDIATION: dict[str, list[str]] = {
    "SQL注入攻击": [
        "在应用层使用参数化查询/预编译语句（PreparedStatement / 占位符），杜绝字符串拼接 SQL。",
        "所有用户输入做白名单类型校验（数字、UUID、枚举），禁止把任意字符串带进 SQL。",
        "数据库账号最小权限，禁用 FILE/EXECUTE/管理类权限；分离读写账号。",
        "WAF 侧保留 SQL 注入规则的拦截动作，并定期复盘观察模式记录。",
    ],
    "XSS攻击": [
        "输出到 HTML 上下文统一做 HTML 转义；JS/属性/URL 上下文使用对应转义函数。",
        "前端启用 CSP（default-src 'self'，禁止 inline script/eval），并设置 X-Content-Type-Options: nosniff。",
        "Cookie 全部加 HttpOnly + Secure + SameSite=Lax/Strict，避免 Session 被脚本读取。",
        "对富文本输入使用成熟过滤库（如 DOMPurify）做白名单清洗，禁止自写正则黑名单。",
    ],
    "SQL注入攻击(扩展)": [
        "同 SQL 注入：参数化 + 输入校验 + 数据库最小权限。",
        "对 ORDER BY / LIMIT 等无法参数化的位置，使用整型校验或字段名白名单映射。",
    ],
    "自定义策略": [
        "复盘自定义规则触发频次，命中量极低或长期无业务流量的规则建议清理。",
        "敏感路径（/admin、/console、/actuator 等）应叠加：IP 白名单 + 强认证 + 审计日志。",
        "自定义规则尽量使用白名单匹配；黑名单只用于已知恶意特征。",
    ],
    "IP黑名单": [
        "持续维护威胁情报源（自有 + 第三方）刷新黑名单。",
        "对命中黑名单的 IP 自动联动其他防护：账号风控、API 网关阻断、CDN 拉黑。",
    ],
    "地域封禁拦截": [
        "确认业务白名单地域，关闭非必要地区的访问入口。",
        "对仍需开放但高风险地区做强校验：人机验证、二次认证、降级策略。",
    ],
    "CC策略拦截": [
        "区分 API 与页面分别配置 CC 阈值；登录、下单、找回密码等关键接口阈值更严。",
        "结合人机识别 + Token 限流，避免单纯按 IP 限速被代理池绕过。",
    ],
    "IP惩罚": [
        "保留 IP 惩罚机制；命中后自动联动 CDN/SLB 同步封禁，缩短惩罚生效路径。",
    ],
    "人机识别": [
        "对登录、注册、下单、抽奖等接口默认开启人机识别。",
        "前端埋点采集行为指纹，后端结合设备指纹 + 风控模型综合判断。",
    ],
    "恶意机器人检测": [
        "确认 robots.txt 与人机识别策略覆盖到所有公开接口；登录/下单/搜索等高价值接口加签名校验。",
        "针对 Nmap / masscan / zgrab / nuclei 等扫描器 UA 维持拦截，并把命中 IP 联动加入风控黑名单。",
        "重要接口启用频次阈值 + 设备指纹双层风控，避免仅靠 UA 判定被伪装绕过。",
    ],
    "AI引擎检出": [
        "AI 引擎规则建议先在 observe 模式跑一轮误报评估，确认无业务影响后再切换到拦截。",
        "若长期保持 observe，必须配套：① 高危记录告警 ② 周期性人工复核 ③ 误报样本回流模型，否则形同虚设。",
        "发现误拦记录时优先调整白名单，不要降级整条 AI 规则。",
    ],
    "已知弱点": [
        "立即排查暴露在公网的 PHP / phpunit / Spring Actuator / .git / .env / Druid 等敏感路径，能下线的全部下线。",
        "脚手架/示例代码（vendor/phpunit/eval-stdin.php、.well-known、debug 路由）禁止打入生产镜像。",
        "在反向代理或 WAF 自定义规则中默认 deny 这类已知弱点路径，按需走白名单放行。",
    ],
    "一般攻击": [
        "保留拦截动作；攻击 IP 自动联动账号风控/网关阻断。",
        "对单 IP 高频高危、跨域跨接口攻击建立告警，便于人工跟进。",
        "应用层补齐输入校验/输出编码/最小权限，不依赖 WAF 单点防御。",
    ],
    "信息泄露": [
        "下线生产暴露的 .git / .svn / .env / phpinfo / debug / actuator / heapdump / swagger 等敏感端点。",
        "错误页统一封装，禁止把堆栈、SQL、文件路径、内网 IP 透出给用户。",
    ],
    "命令注入": [
        "禁止把用户输入拼接进 shell/exec；必须使用参数化数组形式调用，且对参数做白名单校验。",
        "服务进程降权运行，限制可访问的二进制与目录。",
    ],
    "WebShell": [
        "立即隔离主机，导出可疑文件做哈希比对，结合 HIDS 全量扫描确认是否落地。",
        "审计上传接口：限制扩展名白名单 + 文件内容校验 + 上传目录禁止执行权限。",
    ],
    "文件包含攻击": [
        "include/require 等函数禁止使用用户输入；模板路径必须用枚举映射。",
        "PHP 关闭 allow_url_include，统一升级到不再支持远程包含的运行时。",
    ],
    "路径穿越": [
        "服务端使用规范化函数（realpath/Path.normalize）+ 白名单根目录前缀校验。",
        "禁止把用户输入直接拼到 fs 路径中。",
    ],
    "XXE": [
        "XML 解析器关闭外部实体（disable DOCTYPE / external-general-entities / external-parameter-entities）。",
        "优先使用 JSON；保留 XML 的接口必须显式声明安全配置。",
    ],
}

DEFAULT_REMEDIATION = [
    "保留拦截动作；定期复盘观察模式（observe-only）记录，确认是否需要升级为拦截。",
    "在应用层做纵深防御：输入校验、输出编码、最小权限、审计日志，不要只依赖 WAF。",
    "建立攻击日志告警：单 IP 高频高危、动作=观察的高危记录、新出现的攻击类型。",
]


def remediation_for(types: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for t in types:
        for k, v in GENERIC_REMEDIATION.items():
            if k in t or t in k:
                out[t] = v
                break
        else:
            out[t] = DEFAULT_REMEDIATION
    return out


# --- Markdown report -------------------------------------------------------

def fmt_dt(t: dt.datetime | None) -> str:
    return t.strftime("%Y-%m-%d %H:%M:%S") if t else "-"


def render_markdown(agg: dict[str, Any], v: dict[str, Any],
                    enrich: dict[str, dict[str, str]],
                    sources: list[Path]) -> str:
    lines: list[str] = []
    p = lines.append

    p("# WAF 攻击日志分析报告（简版）\n")
    p(f"- 生成时间：{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    p(f"- 分析数据源：{len(sources)} 个文件")
    for s in sources:
        p(f"  - `{s}`")
    p("")

    # Overview
    total = agg["total"]
    blocked = agg["action_counter"].get("拦截", 0)
    block_rate = (blocked / total) if total else 0
    p("## 1. 数据概览\n")
    p(f"| 指标 | 值 |")
    p(f"|---|---|")
    p(f"| 总记录数 | {total} |")
    p(f"| 时间范围 | {fmt_dt(agg['time_min'])} ~ {fmt_dt(agg['time_max'])} |")
    p(f"| 涉及域名数 | {len(agg['domain_counter'])} |")
    p(f"| 独立攻击 IP 数 | {len(agg['ip_counter'])} |")
    p(f"| 独立 APPID 数 | {len(agg['appid_counter'])} |")
    p(f"| 拦截率 | {block_rate:.1%}（拦截 {blocked} / 总 {total}）|")
    p(f"| 动作分布 | " + ", ".join(f"{k}:{v}" for k, v in agg["action_counter"].most_common()) + " |")
    risk_str = ", ".join(f"{k}:{v}" for k, v in agg["risk_counter"].most_common())
    p(f"| 风险等级分布 | {risk_str or '-'} |")
    p("")

    # Verdict
    p("## 2. 真实性研判\n")
    p(f"**判定结论**：{v['label']}")
    p(f"（测试信号 {v['score_test']} 项 / 真实攻击信号 {v['score_real']} 项）\n")
    if v["test_signals"]:
        p("**测试流量信号**：")
        for s in v["test_signals"]:
            p(f"- {s}")
        p("")
    if v["real_signals"]:
        p("**真实攻击信号**：")
        for s in v["real_signals"]:
            p(f"- ⚠️ {s}")
        p("")

    # Top types
    p("## 3. 攻击类型 Top10\n")
    p("| # | 攻击类型 | 次数 | 占比 |")
    p("|---|---|---:|---:|")
    for i, (t, c) in enumerate(agg["type_counter"].most_common(10), 1):
        p(f"| {i} | {t} | {c} | {c/total:.1%} |")
    p("")

    # Top IPs
    p("## 4. 源 IP Top10\n")
    p("| # | 攻击 IP | 次数 | 归属/组织 |")
    p("|---|---|---:|---|")
    for i, (ip, c) in enumerate(agg["ip_counter"].most_common(10), 1):
        meta = enrich.get(ip, {})
        loc = meta.get("country", "-")
        org = meta.get("org") or meta.get("isp") or "-"
        p(f"| {i} | `{ip}` | {c} | {loc} / {org} |")
    p("")

    # Top URIs
    p("## 5. 被攻击 URI Top10\n")
    p("| # | URI | 次数 |")
    p("|---|---|---:|")
    for i, (u, c) in enumerate(agg["uri_counter"].most_common(10), 1):
        p(f"| {i} | `{html.escape(u)}` | {c} |")
    p("")

    # Bypass — split observe-only-domain noise from genuine bypass concerns
    obs_only_domains = {d["domain"] for d in agg.get("observe_only_domains", [])}
    config_anomaly_rows = [r for r in agg["bypass_rows"] if r["被攻击域名"] in obs_only_domains]
    real_bypass_rows = [r for r in agg["bypass_rows"] if r["被攻击域名"] not in obs_only_domains]

    # Configuration anomaly section
    p("## 6. 配置异常告警\n")
    if agg.get("observe_only_domains"):
        p("⚠️ 检测到以下域名整体处于 **observe-only**（高危但全部未拦截），疑似规则配置错误：\n")
        p("| 域名 | 攻击数 | 高危数 | 拦截率 |")
        p("|---|---:|---:|---:|")
        for d in agg["observe_only_domains"]:
            p(f"| {d['domain']} | {d['count']} | {d['high']} | {d['block_rate']:.1%} |")
        p("\n**建议**：核实是否为业务方主动配置（误报评估期），若否，立即在 WAF 控制台将对应规则从「观察」切到「拦截」。")
    else:
        p("✅ 未发现整域 observe-only 配置异常。")
    p("")

    # Scanner fingerprints section
    p("## 7. 扫描器/已知漏洞探测指纹\n")
    if agg.get("scanner_list"):
        p("| 类型 | 指纹 | 命中次数 | 涉及 IP 数 |")
        p("|---|---|---:|---:|")
        for s in agg["scanner_list"][:20]:
            p(f"| {s['kind']} | {html.escape(s['label'])} | {s['count']} | {s['ip_count']} |")
        p("\n**建议**：这些指纹为已知扫描器/漏扫工具特征，对应攻击者意图明确为漏洞探测。"
          "保持 WAF 拦截动作，并把高频扫描源 IP 联动到 CDN/SLB/账号风控全局封禁。")
    else:
        p("未识别到已知扫描器指纹。")
    p("")

    # Suspected bypass (excluding observe-only-domain noise)
    p("## 8. 可疑绕过 / 观察模式记录\n")
    if real_bypass_rows:
        p(f"共 {len(real_bypass_rows)} 条 高危但未拦截 记录（已排除整域 observe-only 噪声 {len(config_anomaly_rows)} 条），需关注：\n")
        p("| 攻击 IP | 域名 | URI | 攻击类型 | 动作 | 时间 |")
        p("|---|---|---|---|---|---|")
        for r in real_bypass_rows[:15]:
            ts = fmt_dt(parse_ts(r["攻击时间"]))
            p(f"| `{r['攻击IP']}` | {r['被攻击域名']} | `{html.escape(r['URI'])}` | {r['攻击类型']} | {r['动作']} | {ts} |")
        if len(real_bypass_rows) > 15:
            p(f"\n_（仅展示前 15 条，共 {len(real_bypass_rows)} 条）_")
    elif config_anomaly_rows:
        p(f"✅ 真正的绕过/观察模式记录：0 条（{len(config_anomaly_rows)} 条已归入「配置异常」类）")
    else:
        p("✅ 无高危未拦截记录")
    p("")

    # Domain impact
    p("## 9. 业务影响（按域名）\n")
    p("| 域名 | 攻击数 | 拦截率 | 高危数 | APPID |")
    p("|---|---:|---:|---:|---|")
    for d in agg["domain_impact"][:10]:
        p(f"| {d['domain']} | {d['count']} | {d['block_rate']:.1%} | {d['high']} | {', '.join(d['appids']) or '-'} |")
    p("")

    # Remediation
    p("## 10. 通用处置建议\n")
    top_types = [t for t, _ in agg["type_counter"].most_common(5)]
    rem = remediation_for(top_types)
    for t in top_types:
        p(f"### {t}")
        for item in rem[t]:
            p(f"- {item}")
        p("")
    p("### 通用建议（适用于全量攻击）")
    for item in DEFAULT_REMEDIATION:
        p(f"- {item}")
    p("")

    p("---")
    p("> ⚠️ 本报告基于启发式规则生成，最终研判建议结合业务流量特征人工复核。")
    return "\n".join(lines)


# --- HTML report -----------------------------------------------------------

def svg_pie(data: list[tuple[str, int]], size: int = 320) -> str:
    """Render a pie chart as inline SVG."""
    total = sum(c for _, c in data) or 1
    cx = cy = size // 2
    r = size // 2 - 10
    colors = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6",
              "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16"]
    parts: list[str] = []
    legend: list[str] = []
    angle = -90.0
    for i, (label, count) in enumerate(data[:10]):
        sweep = 360 * count / total
        if sweep < 0.001:
            continue
        a1 = angle * 3.14159265 / 180
        a2 = (angle + sweep) * 3.14159265 / 180
        x1 = cx + r * __import__("math").cos(a1)
        y1 = cy + r * __import__("math").sin(a1)
        x2 = cx + r * __import__("math").cos(a2)
        y2 = cy + r * __import__("math").sin(a2)
        large = 1 if sweep > 180 else 0
        color = colors[i % len(colors)]
        parts.append(
            f'<path d="M{cx},{cy} L{x1:.2f},{y1:.2f} '
            f'A{r},{r} 0 {large} 1 {x2:.2f},{y2:.2f} Z" '
            f'fill="{color}" stroke="#fff" stroke-width="1"/>'
        )
        legend.append(
            f'<div class="lg-item"><span class="sw" style="background:{color}"></span>'
            f'{html.escape(label)} <b>{count}</b> ({count/total:.0%})</div>'
        )
        angle += sweep
    svg = f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}">{"".join(parts)}</svg>'
    return f'<div class="pie-wrap">{svg}<div class="legend">{"".join(legend)}</div></div>'


def svg_line(hourly: dict[str, int], width: int = 720, height: int = 220) -> str:
    if not hourly:
        return "<p>无时间数据</p>"
    items = list(hourly.items())
    n = len(items)
    max_v = max(hourly.values()) or 1
    pad_l, pad_r, pad_t, pad_b = 40, 16, 16, 40
    chart_w = width - pad_l - pad_r
    chart_h = height - pad_t - pad_b
    if n == 1:
        x_step = chart_w
    else:
        x_step = chart_w / (n - 1)
    pts: list[str] = []
    circles: list[str] = []
    for i, (label, v) in enumerate(items):
        x = pad_l + i * x_step
        y = pad_t + chart_h - (v / max_v) * chart_h
        pts.append(f"{x:.1f},{y:.1f}")
        circles.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#3b82f6">'
            f'<title>{html.escape(label)}: {v}</title></circle>'
        )
    # Y-axis ticks
    y_ticks: list[str] = []
    for k in range(5):
        val = round(max_v * k / 4)
        y = pad_t + chart_h - (k / 4) * chart_h
        y_ticks.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width-pad_r}" y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1"/>'
            f'<text x="{pad_l-6}" y="{y+4:.1f}" font-size="10" fill="#6b7280" text-anchor="end">{val}</text>'
        )
    # X-axis labels: show ~6 evenly spaced
    x_labels: list[str] = []
    step = max(1, n // 6)
    for i in range(0, n, step):
        x = pad_l + i * x_step
        x_labels.append(
            f'<text x="{x:.1f}" y="{height-pad_b+16}" font-size="10" fill="#6b7280" '
            f'text-anchor="middle" transform="rotate(-30 {x:.1f},{height-pad_b+16})">'
            f'{html.escape(items[i][0])}</text>'
        )
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}">'
        f'{"".join(y_ticks)}'
        f'<polyline fill="none" stroke="#3b82f6" stroke-width="2" points="{" ".join(pts)}"/>'
        f'{"".join(circles)}'
        f'{"".join(x_labels)}'
        f'</svg>'
    )


def render_html(agg: dict[str, Any], v: dict[str, Any],
                enrich: dict[str, dict[str, str]],
                sources: list[Path], rows: list[dict[str, str]]) -> str:
    total = agg["total"]
    blocked = agg["action_counter"].get("拦截", 0)
    block_rate = (blocked / total) if total else 0

    verdict_color = {
        "测试流量": "#10b981",
        "自动化扫描器流量": "#f59e0b",
        "真实定向攻击（建议人工复核）": "#ef4444",
        "无数据": "#6b7280",
    }.get(v["label"], "#6b7280")

    css = """
    *{box-sizing:border-box}
    body{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
         background:#f9fafb;color:#111827;margin:0;padding:24px;}
    h1{font-size:24px;margin:0 0 4px}
    h2{font-size:18px;margin:32px 0 12px;border-left:4px solid #3b82f6;padding-left:10px}
    .meta{color:#6b7280;font-size:13px;margin-bottom:24px}
    .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
    .kpi{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:16px}
    .kpi .lbl{font-size:12px;color:#6b7280}
    .kpi .val{font-size:24px;font-weight:600;margin-top:6px;color:#111827}
    .verdict{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin-top:8px}
    .verdict .badge{display:inline-block;padding:4px 12px;border-radius:999px;color:#fff;font-weight:600;font-size:13px}
    .sig-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:14px}
    .sig-box{background:#f9fafb;border-radius:8px;padding:12px;border:1px solid #e5e7eb}
    .sig-box h4{margin:0 0 8px;font-size:13px}
    .sig-box ul{margin:0;padding-left:18px;font-size:13px;color:#374151}
    table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;font-size:13px}
    th,td{padding:8px 12px;border-bottom:1px solid #f3f4f6;text-align:left;vertical-align:top}
    th{background:#f3f4f6;font-weight:600;color:#374151}
    tr:last-child td{border-bottom:none}
    code{background:#f3f4f6;padding:2px 6px;border-radius:4px;font-size:12px}
    .pie-wrap{display:flex;align-items:center;gap:24px;background:#fff;padding:16px;border:1px solid #e5e7eb;border-radius:10px;flex-wrap:wrap}
    .legend{display:flex;flex-direction:column;gap:6px;font-size:13px}
    .lg-item{display:flex;align-items:center;gap:8px}
    .sw{display:inline-block;width:12px;height:12px;border-radius:2px}
    .chart{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:12px}
    .ip-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin-bottom:12px}
    .ip-card .row{display:flex;flex-wrap:wrap;gap:24px;margin-top:8px;font-size:13px;color:#374151}
    .tag{display:inline-block;background:#eff6ff;color:#1d4ed8;padding:2px 8px;border-radius:6px;font-size:12px;margin-right:4px}
    details>summary{cursor:pointer;padding:8px 12px;background:#f3f4f6;border-radius:6px;font-weight:600}
    .footer{margin-top:32px;color:#9ca3af;font-size:12px;text-align:center}
    .warn{color:#b45309;background:#fef3c7;padding:10px 14px;border-radius:8px;border-left:4px solid #f59e0b;font-size:13px;margin:12px 0}
    """

    h: list[str] = []
    a = h.append
    a(f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>")
    a(f"<title>WAF 攻击日志分析报告</title><style>{css}</style></head><body>")
    a("<h1>WAF 攻击日志分析报告</h1>")
    a(f"<div class='meta'>生成时间 {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · "
      f"数据源 {len(sources)} 个 CSV · 总记录 {total} 条</div>")

    # KPI cards
    a("<div class='kpis'>")
    a(f"<div class='kpi'><div class='lbl'>总攻击数</div><div class='val'>{total}</div></div>")
    a(f"<div class='kpi'><div class='lbl'>拦截率</div><div class='val'>{block_rate:.1%}</div></div>")
    a(f"<div class='kpi'><div class='lbl'>独立攻击 IP</div><div class='val'>{len(agg['ip_counter'])}</div></div>")
    a(f"<div class='kpi'><div class='lbl'>涉及域名</div><div class='val'>{len(agg['domain_counter'])}</div></div>")
    high_n = agg["risk_counter"].get("高危", 0)
    a(f"<div class='kpi'><div class='lbl'>高危记录</div><div class='val'>{high_n}</div></div>")
    a(f"<div class='kpi'><div class='lbl'>时间跨度</div><div class='val'>"
      f"{fmt_dt(agg['time_min'])[:10]} → {fmt_dt(agg['time_max'])[:10]}</div></div>")
    a("</div>")

    # Verdict
    a("<h2>🔍 真实性研判</h2>")
    a("<div class='verdict'>")
    a(f"<span class='badge' style='background:{verdict_color}'>{html.escape(v['label'])}</span>")
    a(f"<span style='margin-left:12px;color:#6b7280;font-size:13px'>"
      f"测试信号 {v['score_test']} · 真实攻击信号 {v['score_real']}</span>")
    a("<div class='sig-grid'>")
    a("<div class='sig-box'><h4>📋 测试流量信号</h4><ul>")
    for s in v["test_signals"] or ["（无）"]:
        a(f"<li>{html.escape(s)}</li>")
    a("</ul></div>")
    a("<div class='sig-box'><h4>⚠️ 真实攻击信号</h4><ul>")
    for s in v["real_signals"] or ["（无）"]:
        a(f"<li>{html.escape(s)}</li>")
    a("</ul></div>")
    a("</div></div>")

    # Charts
    a("<h2>📊 攻击类型分布</h2>")
    a(svg_pie(agg["type_counter"].most_common(10)))

    a("<h2>📈 时间分布（按小时）</h2>")
    a(f"<div class='chart'>{svg_line(agg['hourly'])}</div>")

    # Top IPs with profile
    a("<h2>👤 攻击者画像（Top IP）</h2>")
    for ip, c in agg["ip_counter"].most_common(5):
        prof = agg["ip_profile"][ip]
        meta = enrich.get(ip, {})
        loc = html.escape(meta.get("country", "-"))
        org = html.escape(meta.get("org") or meta.get("isp") or "-")
        asn = html.escape(meta.get("asn", "-"))
        types_tags = "".join(f"<span class='tag'>{html.escape(t)}({n})</span>"
                             for t, n in prof["types"].most_common(5))
        ua_tags = "".join(f"<span class='tag'>{html.escape(u)}</span>"
                          for u, _ in prof["uas"].most_common(3))
        a("<div class='ip-card'>")
        a(f"<div><b><code>{html.escape(ip)}</code></b> · "
          f"{c} 次攻击 · {loc} / {org} · ASN {asn}</div>")
        a("<div class='row'>")
        a(f"<div>首次：{fmt_dt(prof['first'])}</div>")
        a(f"<div>末次：{fmt_dt(prof['last'])}</div>")
        a(f"<div>平均间隔：{prof['avg_interval_sec']} 秒</div>")
        a(f"<div>覆盖域名：{len(prof['domains'])}</div>")
        a(f"<div>动作：{', '.join(f'{k}:{n}' for k,n in prof['actions'].most_common())}</div>")
        a("</div>")
        a(f"<div style='margin-top:10px'>攻击类型：{types_tags}</div>")
        a(f"<div style='margin-top:6px'>UA：{ua_tags}</div>")
        a("</div>")

    # Configuration anomaly
    obs_only = agg.get("observe_only_domains", []) or []
    a("<h2>⚙️ 配置异常告警</h2>")
    if obs_only:
        a("<div class='warn'>检测到以下域名整体处于 observe-only（高危但全部未拦截），疑似规则配置错误。"
          "建议核实是否业务方主动配置；若否，立即在 WAF 控制台将对应规则切换为「拦截」。</div>")
        a("<table><thead><tr><th>域名</th><th>攻击数</th><th>高危数</th><th>拦截率</th><th>APPID</th></tr></thead><tbody>")
        for d in obs_only:
            a(f"<tr><td>{html.escape(d['domain'])}</td>"
              f"<td>{d['count']}</td><td>{d['high']}</td>"
              f"<td>{d['block_rate']:.1%}</td>"
              f"<td>{html.escape(', '.join(d['appids']) or '-')}</td></tr>")
        a("</tbody></table>")
    else:
        a("<p style='color:#10b981'>✅ 未发现整域 observe-only 配置异常</p>")

    # Scanner fingerprints
    scanners = agg.get("scanner_list", []) or []
    a("<h2>🛰 扫描器/已知漏洞探测指纹</h2>")
    if scanners:
        a("<p style='color:#374151;font-size:13px'>这些指纹为已知扫描器/漏扫工具特征，"
          "对应攻击者意图明确为漏洞探测。建议把高频扫描源 IP 联动到 CDN/SLB/账号风控全局封禁。</p>")
        a("<table><thead><tr><th>类型</th><th>指纹</th><th>命中次数</th><th>涉及 IP 数</th></tr></thead><tbody>")
        for s in scanners[:30]:
            a(f"<tr><td>{html.escape(s['kind'])}</td>"
              f"<td>{html.escape(s['label'])}</td>"
              f"<td>{s['count']}</td><td>{s['ip_count']}</td></tr>")
        a("</tbody></table>")
    else:
        a("<p>未识别到已知扫描器指纹。</p>")

    # Suspected bypass — exclude observe-only domain noise
    obs_only_domains_set = {d["domain"] for d in obs_only}
    real_bypass = [r for r in agg["bypass_rows"] if r["被攻击域名"] not in obs_only_domains_set]
    config_bypass_count = len(agg["bypass_rows"]) - len(real_bypass)
    a("<h2>🚨 可疑绕过 / 观察模式记录</h2>")
    if real_bypass:
        note = (f"共 {len(real_bypass)} 条 高危但未拦截 记录"
                + (f"（已排除整域 observe-only 噪声 {config_bypass_count} 条）" if config_bypass_count else "")
                + "，需关注是否为故意配置或规则失效。")
        a(f"<div class='warn'>{note}</div>")
        a("<table><thead><tr><th>IP</th><th>域名</th><th>URI</th><th>攻击类型</th><th>动作</th><th>时间</th></tr></thead><tbody>")
        for r in real_bypass[:50]:
            a(f"<tr><td><code>{html.escape(r['攻击IP'])}</code></td>"
              f"<td>{html.escape(r['被攻击域名'])}</td>"
              f"<td><code>{html.escape(r['URI'])}</code></td>"
              f"<td>{html.escape(r['攻击类型'])}</td>"
              f"<td>{html.escape(r['动作'])}</td>"
              f"<td>{fmt_dt(parse_ts(r['攻击时间']))}</td></tr>")
        a("</tbody></table>")
        if len(real_bypass) > 50:
            a(f"<div class='meta'>仅展示前 50 条，共 {len(real_bypass)} 条</div>")
    elif config_bypass_count:
        a(f"<p style='color:#10b981'>✅ 真正的绕过/观察模式记录：0 条（{config_bypass_count} 条已归入「配置异常」）</p>")
    else:
        a("<p style='color:#10b981'>✅ 无高危未拦截记录</p>")

    # Business impact
    a("<h2>🏢 业务影响评估（按域名）</h2>")
    a("<table><thead><tr><th>域名</th><th>攻击数</th><th>拦截率</th><th>高危数</th><th>APPID</th></tr></thead><tbody>")
    for d in agg["domain_impact"]:
        a(f"<tr><td>{html.escape(d['domain'])}</td>"
          f"<td>{d['count']}</td><td>{d['block_rate']:.1%}</td>"
          f"<td>{d['high']}</td>"
          f"<td>{html.escape(', '.join(d['appids']) or '-')}</td></tr>")
    a("</tbody></table>")

    # Threat intel
    a("<h2>🌐 威胁情报富化（Top IP）</h2>")
    a("<table><thead><tr><th>IP</th><th>国家/地区</th><th>组织</th><th>ISP</th><th>ASN</th></tr></thead><tbody>")
    for ip, _ in agg["ip_counter"].most_common(15):
        m = enrich.get(ip, {})
        a(f"<tr><td><code>{html.escape(ip)}</code></td>"
          f"<td>{html.escape(m.get('country','-'))}</td>"
          f"<td>{html.escape(m.get('org','-'))}</td>"
          f"<td>{html.escape(m.get('isp','-'))}</td>"
          f"<td>{html.escape(m.get('asn','-'))}</td></tr>")
    a("</tbody></table>")

    # Generic remediation
    a("<h2>🛡 通用处置建议</h2>")
    top_types = [t for t, _ in agg["type_counter"].most_common(5)]
    rem = remediation_for(top_types)
    for t in top_types:
        a(f"<details open><summary>{html.escape(t)}</summary><ul>")
        for item in rem[t]:
            a(f"<li>{html.escape(item)}</li>")
        a("</ul></details>")
    a("<details><summary>通用建议（适用全量攻击）</summary><ul>")
    for item in DEFAULT_REMEDIATION:
        a(f"<li>{html.escape(item)}</li>")
    a("</ul></details>")

    # Detail rows
    a("<h2>📋 攻击明细（前 200 行）</h2>")
    a("<details><summary>展开/收起</summary>")
    a("<table><thead><tr><th>时间</th><th>IP</th><th>域名</th><th>URI</th>"
      "<th>方法</th><th>攻击类型</th><th>动作</th></tr></thead><tbody>")
    for r in rows[:200]:
        a(f"<tr><td>{fmt_dt(parse_ts(r['攻击时间']))}</td>"
          f"<td><code>{html.escape(r['攻击IP'])}</code></td>"
          f"<td>{html.escape(r['被攻击域名'])}</td>"
          f"<td><code>{html.escape(r['URI'])}</code></td>"
          f"<td>{html.escape(r['方法'])}</td>"
          f"<td>{html.escape(r['攻击类型'])}</td>"
          f"<td>{html.escape(r['动作'])}</td></tr>")
    a("</tbody></table></details>")
    if len(rows) > 200:
        a(f"<div class='meta'>仅展示前 200 行，总 {len(rows)} 行。完整数据请查看原始 CSV。</div>")

    a("<div class='footer'>本报告由 waf-log-analyzer skill 基于启发式规则生成，"
      "最终研判建议结合业务流量特征人工复核。</div>")
    a("</body></html>")
    return "".join(h)


# --- Main ------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Tencent Cloud WAF attack log analyzer")
    ap.add_argument("--input", required=True, help="CSV file path or directory")
    ap.add_argument("--output", default=None, help="Output report directory")
    ap.add_argument("--no-enrich", action="store_true", help="Skip IP threat-intel enrichment")
    args = ap.parse_args()

    in_path = Path(args.input)
    in_files = collect_input_files(in_path)

    rows: list[dict[str, str]] = []
    for f in in_files:
        rows.extend(read_any(f))

    if not rows:
        sys.exit("[ERROR] no rows parsed from input")

    print(f"[INFO] parsed {len(rows)} rows from {len(in_files)} file(s)")

    # Output dir
    if args.output:
        out_dir = Path(args.output)
    else:
        base = in_path.parent if in_path.is_file() else in_path
        out_dir = base / f"waf-report-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Aggregate
    agg = aggregate(rows)

    # Verdict
    v = verdict(rows)
    print(f"[INFO] verdict: {v['label']} (test={v['score_test']}, real={v['score_real']})")

    # Enrichment for top 15 IPs
    top_ips = [ip for ip, _ in agg["ip_counter"].most_common(15)]
    if args.no_enrich:
        print("[INFO] enrichment skipped (--no-enrich)")
        enrich = {ip: {"country": "-", "org": "-", "asn": "-", "isp": "-"} for ip in top_ips}
    else:
        print(f"[INFO] enriching {len(top_ips)} IPs via ip-api.com ...")
        enrich = enrich_ips(top_ips, enabled=True)

    # Render
    md_text = render_markdown(agg, v, enrich, in_files)
    html_text = render_html(agg, v, enrich, in_files, rows)

    md_path = out_dir / "report.md"
    html_path = out_dir / "report.html"
    md_path.write_text(md_text, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")

    print(f"[OK] Markdown report: {md_path}")
    print(f"[OK] HTML report:     {html_path}")
    # Machine-readable summary line for the skill caller
    summary = {
        "ok": True,
        "total": agg["total"],
        "block_rate": round((agg["action_counter"].get("拦截", 0) / agg["total"]) if agg["total"] else 0, 4),
        "unique_ips": len(agg["ip_counter"]),
        "domains": len(agg["domain_counter"]),
        "verdict": v["label"],
        "test_signals": v["test_signals"],
        "real_signals": v["real_signals"],
        "report_md": str(md_path),
        "report_html": str(html_path),
        "output_dir": str(out_dir),
    }
    print("SUMMARY_JSON=" + json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
