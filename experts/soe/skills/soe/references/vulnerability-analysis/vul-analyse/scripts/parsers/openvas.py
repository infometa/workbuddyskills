"""
Greenbone OpenVAS / GVM 报告解析器（XML 格式）

参考：
  - GVM 报告 XML：根节点 <report> 内含 <results>，每个 <result> 表示一个发现
  - 字段：name / host / port / threat / severity / description / nvt / refs
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from parser_registry import register_parser

try:
    from ._common import cvss_to_severity, extract_cve, make_record, normalize_severity, sniff_head
except ImportError:
    from _common import cvss_to_severity, extract_cve, make_record, normalize_severity, sniff_head  # type: ignore


def _detect(file_path: str) -> bool:
    head = sniff_head(file_path, 8192).decode("utf-8", errors="ignore")
    # OpenVAS 报告通常包含 <get_reports_response> 或 <report id="..."> 且有 GVM/OpenVAS 标识
    if "get_reports_response" in head:
        return True
    if "<report" in head and ("openvas" in head.lower() or "greenbone" in head.lower() or "gvm" in head.lower()):
        return True
    return False


# OpenVAS threat 字段 → 中文
THREAT_MAP = {
    "Critical": "紧急",
    "High": "高危",
    "Medium": "中危",
    "Low": "低危",
    "Log": "信息",
    "Debug": "信息",
    "False Positive": "信息",
}


@register_parser(
    name="openvas_xml",
    vendor="Greenbone OpenVAS / GVM",
    file_extensions=(".xml",),
    detect=_detect,
    description="解析 Greenbone OpenVAS / GVM 漏洞扫描报告 XML",
    priority=70,
)
def parse(file_path: str) -> list[dict]:
    tree = ET.parse(file_path)
    root = tree.getroot()
    results: list[dict] = []

    # 兼容两种根：<get_reports_response><report>... 或直接 <report>...
    report_nodes = list(root.iter("report"))
    if not report_nodes and root.tag == "report":
        report_nodes = [root]

    for report in report_nodes:
        for result in report.iter("result"):
            def _txt(path: str) -> str:
                el = result.find(path)
                return (el.text or "").strip() if el is not None and el.text else ""

            name = _txt("name") or _txt("./nvt/name") or "OpenVAS Finding"
            host = _txt("host")
            port_field = _txt("port")
            # port 形如 "443/tcp"
            port = port_field.split("/")[0] if "/" in port_field else port_field

            threat = _txt("threat")
            severity_num = _txt("severity")  # CVSS 数值字符串
            description = _txt("description")
            nvt_oid = result.find("nvt").attrib.get("oid", "") if result.find("nvt") is not None else ""

            # cve 在 refs 下
            cve = ""
            refs_node = result.find("./nvt/refs")
            if refs_node is not None:
                for ref in refs_node.iter("ref"):
                    ref_type = ref.attrib.get("type", "").lower()
                    if ref_type == "cve":
                        cve = ref.attrib.get("id", "").upper()
                        if cve:
                            break
            if not cve:
                cve = extract_cve(description)

            tags = _txt("./nvt/tags")
            solution = ""
            if "solution=" in tags:
                # tags 形如 "summary=...|solution=...|insight=..."
                for kv in tags.split("|"):
                    if kv.startswith("solution="):
                        solution = kv[len("solution="):].strip()
                        break

            # 严重度优先 threat，再 CVSS
            if threat in THREAT_MAP:
                sev = THREAT_MAP[threat]
            else:
                sev = cvss_to_severity(severity_num)

            results.append(make_record(
                name=name,
                cve=cve,
                cvss=severity_num,
                severity=sev,
                desc=description,
                fix=solution,
                asset=host,
                ip=host,
                port=port,
                scanner="Greenbone OpenVAS",
                vuln_id=nvt_oid,
                vuln_type="远程漏洞扫描",
            ))

    return results
