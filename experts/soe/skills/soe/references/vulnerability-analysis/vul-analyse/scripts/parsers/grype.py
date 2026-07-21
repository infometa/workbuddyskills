"""
Anchore Grype 报告解析器（JSON 格式）

参考：
  - https://github.com/anchore/grype#json-output
  - 顶层有 descriptor.name="grype" + matches[]
  - matches[].vulnerability 含 id / severity / description / fix / urls
  - matches[].artifact 含 name / version / type / locations
"""
from __future__ import annotations

import json

from parser_registry import register_parser

try:
    from ._common import cvss_to_severity, extract_cve, make_record, normalize_severity, sniff_head
except ImportError:
    from _common import cvss_to_severity, extract_cve, make_record, normalize_severity, sniff_head  # type: ignore


def _detect(file_path: str) -> bool:
    head = sniff_head(file_path, 4096).decode("utf-8", errors="ignore")
    return '"descriptor"' in head and '"grype"' in head.lower() and '"matches"' in head


def _get_cvss(vuln: dict) -> str:
    """从 Grype 的 cvss[] 数组中提取最高 CVSS v3 评分。"""
    cvss_list = vuln.get("cvss") or []
    best = 0.0
    for entry in cvss_list:
        if not isinstance(entry, dict):
            continue
        # Grype 格式：{"version": "3.1", "metrics": {"baseScore": 9.8, ...}}
        metrics = entry.get("metrics") or {}
        score = metrics.get("baseScore") or 0
        try:
            score = float(score)
        except (TypeError, ValueError):
            continue
        if score > best:
            best = score
    return str(best) if best > 0 else ""


@register_parser(
    name="grype_json",
    vendor="Anchore Grype",
    file_extensions=(".json",),
    detect=_detect,
    description="解析 Anchore Grype SBOM 漏洞扫描 JSON 报告",
    priority=74,
)
def parse(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return []

    matches = data.get("matches") or []
    if not isinstance(matches, list):
        return []

    # 从 source 中提取扫描目标
    source = data.get("source") or {}
    source_target = ""
    if isinstance(source, dict):
        target = source.get("target") or {}
        if isinstance(target, dict):
            source_target = target.get("userInput", "") or target.get("imageID", "")
        elif isinstance(target, str):
            source_target = target

    results: list[dict] = []

    for match in matches:
        if not isinstance(match, dict):
            continue

        vuln = match.get("vulnerability") or {}
        artifact = match.get("artifact") or {}

        vuln_id = vuln.get("id", "")
        severity = vuln.get("severity", "")
        description = vuln.get("description", "")
        urls = vuln.get("urls") or []

        # 修复信息
        fix_info = vuln.get("fix") or {}
        fix_versions = fix_info.get("versions") or []
        fix_state = fix_info.get("state", "")

        # 制品信息
        pkg_name = artifact.get("name", "")
        pkg_version = artifact.get("version", "")
        pkg_type = artifact.get("type", "")
        locations = artifact.get("locations") or []
        location_str = ""
        if locations and isinstance(locations[0], dict):
            location_str = locations[0].get("path", "")

        # CVE 编号
        cve = vuln_id if vuln_id.upper().startswith("CVE-") else extract_cve(description)

        # CVSS 评分
        cvss_score = _get_cvss(vuln)
        # 也检查 relatedVulnerabilities 中的 CVSS
        if not cvss_score:
            for rv in match.get("relatedVulnerabilities") or []:
                if isinstance(rv, dict):
                    s = _get_cvss(rv)
                    if s:
                        cvss_score = s
                        break

        # 修复建议
        fix_text = ""
        if fix_versions:
            fix_text = f"升级 {pkg_name} 到 {', '.join(fix_versions)}"
        elif fix_state == "wont-fix":
            fix_text = "上游标记为 wont-fix，建议评估替代方案"
        elif fix_state == "not-fixed":
            fix_text = "暂无修复版本，建议持续关注"
        if urls:
            fix_text += "\n参考：" + " ".join(urls[:3])

        asset = f"{pkg_name}@{pkg_version}" if pkg_name else source_target

        results.append(make_record(
            name=f"{vuln_id}: {pkg_name}" if pkg_name else vuln_id,
            cve=cve,
            cvss=cvss_score,
            severity=severity,
            desc=description,
            fix=fix_text,
            asset=asset,
            ip=location_str or source_target,
            scanner="Anchore Grype",
            vuln_id=vuln_id,
            vuln_type=pkg_type or "SCA",
        ))

    return results
