"""
Tenable Nessus 报告解析器（.nessus / NessusClientData_v2 XML 格式）

参考：
  - https://docs.tenable.com/nessus/Content/NessusFileFormats.htm
  - 根节点 <NessusClientData_v2>，每个主机 <ReportHost>，每个发现 <ReportItem>
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from parser_registry import register_parser

try:
    from ._common import cvss_to_severity, extract_cve, make_record, normalize_severity, sniff_head
except ImportError:
    # 当作为脚本独立加载时（discover_plugins 走的是 spec_from_file_location，
    # 不会按包导入），降级为绝对导入
    from _common import cvss_to_severity, extract_cve, make_record, normalize_severity, sniff_head  # type: ignore


def _detect(file_path: str) -> bool:
    head = sniff_head(file_path, 8192)
    return b"NessusClientData_v2" in head or b"NessusClientData" in head


# Nessus 风险因子 → 中文
RISK_FACTOR = {
    "Critical": "紧急",
    "High": "高危",
    "Medium": "中危",
    "Low": "低危",
    "None": "信息",
    "Info": "信息",
}


@register_parser(
    name="nessus_xml",
    vendor="Tenable Nessus",
    file_extensions=(".nessus", ".xml"),
    detect=_detect,
    description="解析 Nessus 漏洞扫描报告（NessusClientData_v2 XML 格式）",
    priority=80,
)
def parse(file_path: str) -> list[dict]:
    """
    Nessus 报告结构：
        NessusClientData_v2
        └── Report
            └── ReportHost name="<ip>"
                ├── HostProperties
                │   └── tag name="host-fqdn">...</tag>
                └── ReportItem port=".." pluginID=".." severity="..">
                    ├── pluginName / risk_factor / cvss3_base_score / cve / ...
                    └── description / solution / synopsis
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    results: list[dict] = []

    for host in root.iter("ReportHost"):
        host_ip = host.attrib.get("name", "")
        host_fqdn = ""
        for tag in host.findall("./HostProperties/tag"):
            if tag.attrib.get("name") == "host-fqdn":
                host_fqdn = (tag.text or "").strip()
                break
        target = host_fqdn or host_ip

        for item in host.findall("./ReportItem"):
            port = item.attrib.get("port", "") or "0"
            severity_num = item.attrib.get("severity", "0")
            plugin_name = item.attrib.get("pluginName", "") or "Nessus Finding"
            plugin_id = item.attrib.get("pluginID", "")

            def _txt(tag: str) -> str:
                el = item.find(tag)
                return (el.text or "").strip() if el is not None and el.text else ""

            risk_factor = _txt("risk_factor")
            description = _txt("description") or _txt("synopsis")
            solution = _txt("solution")
            cvss3 = _txt("cvss3_base_score") or _txt("cvss_base_score")
            cve_text = _txt("cve")
            vuln_type = _txt("plugin_type") or _txt("plugin_family")

            # 严重度归一：优先 risk_factor，其次 CVSS，再次 severity 数字
            if risk_factor in RISK_FACTOR:
                sev = RISK_FACTOR[risk_factor]
            elif cvss3:
                sev = cvss_to_severity(cvss3)
            else:
                sev_map_num = {"4": "紧急", "3": "高危", "2": "中危", "1": "低危", "0": "信息"}
                sev = sev_map_num.get(severity_num, "信息")

            results.append(make_record(
                name=plugin_name,
                cve=extract_cve(cve_text) if cve_text else "",
                cvss=cvss3,
                severity=sev,
                desc=description,
                fix=solution,
                asset=target,
                ip=host_ip,
                port=port if port != "0" else "",
                scanner="Tenable Nessus",
                vuln_id=plugin_id,
                vuln_type=vuln_type,
            ))

    return results
