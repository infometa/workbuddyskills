"""
Aqua Trivy 报告解析器（JSON 格式）

参考：
  - https://aquasecurity.github.io/trivy/latest/docs/configuration/reporting/#json
  - 顶层有 SchemaVersion + ArtifactName + Results[]
  - Results[].Vulnerabilities[] 每条含 VulnerabilityID / PkgName / Severity / Description / FixedVersion 等
"""
from __future__ import annotations

import json
from typing import Any

from parser_registry import register_parser

try:
    from ._common import cvss_to_severity, make_record, normalize_severity, sniff_head
except ImportError:
    from _common import cvss_to_severity, make_record, normalize_severity, sniff_head  # type: ignore


def _detect(file_path: str) -> bool:
    head = sniff_head(file_path, 4096).decode("utf-8", errors="ignore")
    return ('"SchemaVersion"' in head and '"Results"' in head) or '"ArtifactName"' in head


def _extract_cvss(vuln: dict) -> str:
    cvss = vuln.get("CVSS") or {}
    if not isinstance(cvss, dict):
        return ""
    # 优先 NVD v3，再 RedHat v3，再 vendor v3
    for source in ("nvd", "redhat", "ghsa"):
        block = cvss.get(source) or {}
        if isinstance(block, dict):
            v = block.get("V3Score") or block.get("V2Score")
            if v:
                return str(v)
    # 兜底：取任意一个 V3Score
    for block in cvss.values():
        if isinstance(block, dict):
            v = block.get("V3Score")
            if v:
                return str(v)
    return ""


@register_parser(
    name="trivy_json",
    vendor="Aqua Trivy",
    file_extensions=(".json",),
    detect=_detect,
    description="解析 Aqua Trivy 容器/IaC 扫描 JSON 报告",
    priority=75,
)
def parse(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return []

    artifact = data.get("ArtifactName", "") or data.get("artifactName", "")
    artifact_type = data.get("ArtifactType", "") or "container"
    results: list[dict] = []

    targets = data.get("Results") or data.get("results") or []
    if not isinstance(targets, list):
        return []

    for target in targets:
        if not isinstance(target, dict):
            continue
        target_name = target.get("Target", "") or target.get("Class", "") or artifact
        # 漏洞列表
        for vuln in target.get("Vulnerabilities") or []:
            if not isinstance(vuln, dict):
                continue
            cve = vuln.get("VulnerabilityID", "") or ""
            pkg = vuln.get("PkgName", "")
            installed = vuln.get("InstalledVersion", "")
            fixed = vuln.get("FixedVersion", "")
            title = vuln.get("Title", "") or vuln.get("Description", "")[:80] or cve
            severity = vuln.get("Severity", "")
            description = vuln.get("Description", "")
            refs = vuln.get("References") or []
            cvss_score = _extract_cvss(vuln)

            asset = f"{pkg}@{installed}" if pkg else target_name
            fix = ""
            if fixed:
                fix = f"升级 {pkg} 到 {fixed}"
            elif refs:
                fix = "参考链接：\n" + "\n".join(refs[:3])

            results.append(make_record(
                name=title,
                cve=cve if cve.upper().startswith("CVE-") else "",
                cvss=cvss_score,
                severity=severity,
                desc=description,
                fix=fix,
                asset=asset,
                ip=target_name,
                scanner="Aqua Trivy",
                vuln_id=cve,
                vuln_type=artifact_type,
            ))

        # Misconfigurations（IaC 配置缺陷）
        for misc in target.get("Misconfigurations") or []:
            if not isinstance(misc, dict):
                continue
            results.append(make_record(
                name=misc.get("Title", "") or misc.get("ID", "Misconfiguration"),
                severity=misc.get("Severity", ""),
                desc=misc.get("Description", ""),
                fix=misc.get("Resolution", ""),
                asset=target_name,
                ip=target_name,
                scanner="Aqua Trivy",
                vuln_id=misc.get("ID", ""),
                vuln_type="Misconfiguration",
            ))

        # Secrets
        for secret in target.get("Secrets") or []:
            if not isinstance(secret, dict):
                continue
            results.append(make_record(
                name=f"硬编码密钥: {secret.get('Title', secret.get('RuleID', ''))}",
                severity=secret.get("Severity", "HIGH"),
                desc=secret.get("Match", ""),
                asset=f"{target_name}:{secret.get('StartLine', '')}",
                ip=target_name,
                scanner="Aqua Trivy",
                vuln_id=secret.get("RuleID", ""),
                vuln_type="Secret",
            ))

    return results
