"""
插件解析器共享工具。

下划线开头，parser_registry.discover_plugins 会跳过它，但其它解析器可以正常 import。
"""
from __future__ import annotations

import re
from typing import Any, Iterable


# ──────────────── 严重度归一 ────────────────


# 国际通用 CVSS Severity → 中文等级
SEVERITY_MAP = {
    # NVD CVSS v3.x
    "critical": "紧急",
    "high": "高危",
    "medium": "中危",
    "low": "低危",
    "negligible": "信息",
    "none": "信息",
    "unknown": "信息",
    # 中文
    "紧急": "紧急", "严重": "紧急",
    "高危": "高危", "高": "高危",
    "中危": "中危", "中": "中危",
    "低危": "低危", "低": "低危",
    "信息": "信息", "提示": "信息",
}


def normalize_severity(raw: Any) -> str:
    """各种来源的等级 → 中文统一标签"""
    if raw is None:
        return "信息"
    s = str(raw).strip().lower()
    return SEVERITY_MAP.get(s, "信息")


def cvss_to_severity(score: Any) -> str:
    """CVSS v3 数值 → 中文等级（NVD 标准切分）"""
    try:
        v = float(score)
    except (TypeError, ValueError):
        return "信息"
    if v >= 9.0:
        return "紧急"
    if v >= 7.0:
        return "高危"
    if v >= 4.0:
        return "中危"
    if v > 0.0:
        return "低危"
    return "信息"


# ──────────────── CVE 提取 ────────────────


_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


def extract_cve(text: Any) -> str:
    """从任意字段中抽取第一个 CVE 编号（大写格式）。无则返回空串。"""
    if text is None:
        return ""
    m = _CVE_RE.search(str(text))
    return m.group(0).upper() if m else ""


def extract_all_cves(items: Iterable[Any]) -> list[str]:
    """从一组字段或字符串中抽取所有 CVE，去重保序。"""
    seen: list[str] = []
    for item in items:
        if item is None:
            continue
        for m in _CVE_RE.finditer(str(item)):
            cve = m.group(0).upper()
            if cve not in seen:
                seen.append(cve)
    return seen


# ──────────────── 标准记录构造 ────────────────


def make_record(
    name: str = "",
    cve: str = "",
    cvss: Any = "",
    severity: str = "",
    desc: str = "",
    fix: str = "",
    asset: str = "",
    ip: str = "",
    port: Any = "",
    discover_time: str = "",
    scanner: str = "",
    vuln_id: str = "",
    vuln_type: str = "",
    cnvd: str = "",
    cnnvd: str = "",
    cncve: str = "",
) -> dict:
    """构造一条符合 STANDARD_FIELDS 的标准漏洞记录。"""
    if severity:
        sev = normalize_severity(severity)
    elif cvss:
        sev = cvss_to_severity(cvss)
    else:
        sev = "信息"

    return {
        "漏洞名称": str(name or "").strip(),
        "漏洞ID": str(vuln_id or "").strip(),
        "漏洞类型": str(vuln_type or "").strip(),
        "漏洞描述": str(desc or "").strip(),
        "修复建议": str(fix or "").strip(),
        "影响资产": str(asset or "").strip(),
        "风险域名/IP": str(ip or "").strip(),
        "风险端口": str(port or "").strip(),
        "发现时间": str(discover_time or "").strip(),
        "扫描工具": str(scanner or "").strip(),
        "CVE编号": str(cve or "").upper().strip(),
        "CNVD编号": str(cnvd or "").strip(),
        "CNNVD编号": str(cnnvd or "").strip(),
        "CNCVE编号": str(cncve or "").strip(),
        "CVSS评分": str(cvss or "").strip(),
        "风险等级": sev,
    }


# ──────────────── 文件嗅探 ────────────────


def sniff_head(file_path: str, n: int = 4096) -> bytes:
    """读取文件头若干字节，用于 detect 函数嗅探格式特征。"""
    try:
        with open(file_path, "rb") as f:
            return f.read(n)
    except Exception:
        return b""
