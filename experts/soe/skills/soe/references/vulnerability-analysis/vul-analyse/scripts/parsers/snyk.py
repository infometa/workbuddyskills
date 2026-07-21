"""
Snyk 报告解析器（JSON 格式）

参考：
  - https://docs.snyk.io/snyk-cli/commands/test#json
  - `snyk test --json` 输出：顶层有 vulnerabilities[] + projectName
  - `snyk container test --json` 输出：类似结构
  - `snyk code test --json` 输出：runs[].results[]（SARIF 子集），本解析器也兼容

每条 vulnerability 含：
  id / title / severity / description / CVSSv3 / cvssScore
  packageName / version / fixedIn[] / from[] / exploit
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
    # Snyk JSON 特征：含 "vulnerabilities" + ("projectName" 或 "org" 或 "snyk")
    if '"vulnerabilities"' not in head:
        return False
    return ('"projectName"' in head or '"org"' in head
            or '"snyk"' in head.lower() or '"packageManager"' in head)


def _parse_snyk_test(data: dict) -> list[dict]:
    """解析 `snyk test --json` / `snyk container test --json` 格式。"""
    project = data.get("projectName", "") or data.get("displayTargetFile", "")
    pkg_manager = data.get("packageManager", "")
    results: list[dict] = []

    for vuln in data.get("vulnerabilities") or []:
        if not isinstance(vuln, dict):
            continue

        vuln_id = vuln.get("id", "")
        title = vuln.get("title", "") or vuln.get("name", "")
        severity = vuln.get("severity", "")
        description = vuln.get("description", "")
        cvss_score = vuln.get("cvssScore", "") or ""
        cvss_vector = vuln.get("CVSSv3", "")

        pkg_name = vuln.get("packageName", "") or vuln.get("moduleName", "")
        pkg_version = vuln.get("version", "")
        fixed_in = vuln.get("fixedIn") or []
        exploit = vuln.get("exploit", "")
        from_chain = vuln.get("from") or []

        # 提取 CVE 编号（Snyk 有自己的 SNYK-xxx ID，但也可能带 CVE 引用）
        identifiers = vuln.get("identifiers") or {}
        cve_list = identifiers.get("CVE") or []
        cve = cve_list[0] if cve_list else ""
        if not cve:
            # 从 references 或 title 中尝试提取
            refs = vuln.get("references") or []
            for ref in refs:
                if isinstance(ref, dict):
                    ref_url = ref.get("url", "")
                elif isinstance(ref, str):
                    ref_url = ref
                else:
                    continue
                c = extract_cve(ref_url)
                if c:
                    cve = c
                    break
            if not cve:
                cve = extract_cve(title)

        # 修复建议
        fix_text = ""
        if fixed_in:
            fix_text = f"升级 {pkg_name} 到 {', '.join(str(v) for v in fixed_in)}"
        upgrade_path = vuln.get("upgradePath") or []
        if not fix_text and upgrade_path:
            fix_text = "升级路径：" + " → ".join(str(p) for p in upgrade_path if p)
        if exploit and exploit != "Not Defined":
            fix_text += f"\n⚠️ 已知利用方式: {exploit}"

        # 依赖链
        dep_chain = " → ".join(str(p) for p in from_chain) if from_chain else ""
        asset = f"{pkg_name}@{pkg_version}" if pkg_name else project

        results.append(make_record(
            name=title or vuln_id,
            cve=cve,
            cvss=str(cvss_score) if cvss_score else "",
            severity=severity,
            desc=description[:2000] if description else "",  # Snyk 描述可能很长
            fix=fix_text,
            asset=asset,
            ip=dep_chain or project,
            scanner="Snyk",
            vuln_id=vuln_id,
            vuln_type=pkg_manager or "SCA",
        ))

    return results


def _parse_snyk_code(data: dict) -> list[dict]:
    """解析 `snyk code test --json` 格式（SARIF 子集）。"""
    results: list[dict] = []
    for run in data.get("runs") or []:
        if not isinstance(run, dict):
            continue
        tool_name = "Snyk Code"
        tool_info = run.get("tool") or {}
        driver = tool_info.get("driver") or {}
        rules_map: dict = {}
        for rule in driver.get("rules") or []:
            if isinstance(rule, dict):
                rules_map[rule.get("id", "")] = rule

        for result in run.get("results") or []:
            if not isinstance(result, dict):
                continue
            rule_id = result.get("ruleId", "")
            rule = rules_map.get(rule_id, {})
            message = result.get("message", {})
            msg_text = message.get("text", "") if isinstance(message, dict) else str(message)
            level = result.get("level", "warning")

            # 位置
            locations = result.get("locations") or []
            loc_str = ""
            if locations and isinstance(locations[0], dict):
                phys = locations[0].get("physicalLocation") or {}
                artifact = phys.get("artifactLocation") or {}
                loc_str = artifact.get("uri", "")
                region = phys.get("region") or {}
                line = region.get("startLine", "")
                if line:
                    loc_str += f":{line}"

            # 严重度映射
            level_map = {"error": "高危", "warning": "中危", "note": "低危", "none": "信息"}
            sev = level_map.get(level, "中危")

            # 从 rule 中获取描述
            desc = ""
            help_info = rule.get("help") or {}
            if isinstance(help_info, dict):
                desc = help_info.get("text", "") or help_info.get("markdown", "")
            if not desc:
                short_desc = rule.get("shortDescription") or {}
                desc = short_desc.get("text", "") if isinstance(short_desc, dict) else ""

            results.append(make_record(
                name=rule.get("name", "") or rule_id or msg_text[:60],
                severity=sev,
                desc=msg_text or desc,
                fix=desc if desc != msg_text else "",
                asset=loc_str,
                ip=loc_str,
                scanner=tool_name,
                vuln_id=rule_id,
                vuln_type="SAST",
            ))

    return results


@register_parser(
    name="snyk_json",
    vendor="Snyk",
    file_extensions=(".json",),
    detect=_detect,
    description="解析 Snyk CLI 漏洞扫描 JSON 报告（SCA + Container + Code）",
    priority=73,
)
def parse(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        return []

    # 判断是 snyk test 还是 snyk code test（SARIF 子集）
    if "runs" in data and isinstance(data.get("runs"), list):
        return _parse_snyk_code(data)

    # 标准 snyk test --json
    if "vulnerabilities" in data:
        return _parse_snyk_test(data)

    # 可能是多项目输出（数组包装）—— 不太常见但兼容
    return []
