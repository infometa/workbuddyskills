#!/usr/bin/env python3
"""
审计报告生成脚本
根据代码审计结果生成 HTML / JSON 报告
"""
import json
import argparse
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from html import escape

from _common import (
    Colors, print_colored, format_beijing_time,
    get_git_branch, get_git_project_name,
    normalize_finding, to_report_format,
    load_json_file,
    load_scan_session, is_output_fresh,
    get_scan_output_dirs,
)


DEFAULT_HTML_REPORT_NAME = "security-scan-report.html"
DEFAULT_JSON_REPORT_NAME = "security-scan-report.json"
PRODUCT_SHAPE_CLIENT = "客户端"
PRODUCT_SHAPE_AI_AGENT = "AI agent"
PRODUCT_SHAPE_WEB = "web"
PRODUCT_SHAPE_DATABASE = "数据库"
PRODUCT_SHAPE_UNKNOWN = "未知"
PRODUCT_SHAPE_CODES = {
    PRODUCT_SHAPE_CLIENT: "client",
    PRODUCT_SHAPE_AI_AGENT: "ai_agent",
    PRODUCT_SHAPE_WEB: "web",
    PRODUCT_SHAPE_DATABASE: "database",
    PRODUCT_SHAPE_UNKNOWN: "unknown",
}


def _normalize_project_type(value):
    """归一化报告全局产品形态字段，限定为五类：客户端 / AI agent / web / 数据库 / 未知。"""
    raw = str(value or "").strip()
    if not raw:
        return PRODUCT_SHAPE_UNKNOWN
    lowered = raw.lower().replace("_", "-").replace(" ", "")
    if raw in PRODUCT_SHAPE_CODES:
        return raw
    if lowered in {"ai-agent", "aiagent", "agent"} or "agent" in lowered:
        return PRODUCT_SHAPE_AI_AGENT
    if lowered in {"web", "frontend", "front-end", "backend", "backend-api", "rpc", "server"} or "web" in lowered or "后端" in raw:
        return PRODUCT_SHAPE_WEB
    if lowered in {"client", "mobile", "desktop", "mini-program", "browser-extension"} or any(key in raw for key in ("客户端", "移动", "桌面", "小程序", "浏览器插件")):
        return PRODUCT_SHAPE_CLIENT
    if lowered in {"database", "db", "storage-engine", "sql-engine"} or any(key in raw for key in ("数据库", "存储引擎", "SQL 引擎", "SQL解析", "SQL 解析")):
        return PRODUCT_SHAPE_DATABASE
    if raw in {"通用代码类项目", "未知类目"} or lowered in {"unknown", "generic", "general"}:
        return PRODUCT_SHAPE_UNKNOWN
    return PRODUCT_SHAPE_UNKNOWN


def _project_type_code(value):
    return PRODUCT_SHAPE_CODES.get(_normalize_project_type(value), "unknown")


def _load_project_type_info(batch_dir):
    """从 project-type.json / batch-plan.json 读取 Agent 分析生成的产品形态结果。"""
    if not batch_dir:
        return {}
    batch_dir = Path(batch_dir)
    candidates = [batch_dir / "project-type.json", batch_dir / "batch-plan.json"]
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            with candidate.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        project_type = data.get("project_type") or data.get("projectType") or data.get("product_shape") or data.get("productShape")
        if project_type:
            agent_profile = data.get("agent_profile") or data.get("agentProfile") or {}
            product_shape = data.get("product_shape") or data.get("productShape") or project_type
            normalized_shape = _normalize_project_type(product_shape)
            raw_code = data.get("project_type_code") or data.get("projectType") or ""
            normalized_code = raw_code if raw_code in set(PRODUCT_SHAPE_CODES.values()) else _project_type_code(normalized_shape)
            result = {
                "project_type": normalized_shape,
                "project_type_code": normalized_code,
                "product_category": _normalize_project_type(data.get("product_category") or normalized_shape),
                "product_subtype": data.get("product_subtype") or "",
                "product_shape": normalized_shape,
                "product_shape_decision": data.get("product_shape_decision") or data.get("productShapeDecision"),
                "product_shape_evidence_chain": data.get("product_shape_evidence_chain") or data.get("productShapeEvidenceChain"),
            }
            if agent_profile:
                result["agent_profile"] = agent_profile
                result["product_shape_decision"] = result["product_shape_decision"] or agent_profile.get("product_shape_decision")
                result["product_shape_evidence_chain"] = result["product_shape_evidence_chain"] or agent_profile.get("product_shape_evidence_chain")
            return result
    return {}


# ---------- 语言校验（确保 findings 文本字段以简体中文为主） ----------

_CJK_RE = re.compile(r'[\u4e00-\u9fff]')

# 统一 camelCase 字段（迁移前曾包含 PascalCase 别名 RiskType/RiskDetail/Suggestions，
# 已随插件级 schema 统一移除）。title/attackScenario 当前不渲染但仍约束。
_LANG_CHECK_FIELDS = (
    'riskType', 'description', 'recommendation',
    'title', 'attackScenario',
)


def _collect_language_text(item):
    """从单个 risk_item 或 finding 中拼接所有待校验文本字段的内容。"""
    parts = []
    for key in _LANG_CHECK_FIELDS:
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val)
    return ' '.join(parts).strip()


def _compute_cjk_ratio(text):
    """计算文本中 CJK 汉字字符占比（以非空白字符数为分母）。"""
    if not text:
        return 1.0  # 空文本不算违规
    stripped = re.sub(r'\s+', '', text)
    if not stripped:
        return 1.0
    cjk = len(_CJK_RE.findall(stripped))
    return cjk / len(stripped)


def enforce_language_zh(results, min_ratio=0.30, quiet=False,
                         violations_out=None):
    """校验 findings 文本字段中文占比。

    Args:
        results: load_audit_results 返回的 list，其元素为
                 {'findings': [finding, ...]} 或直接 finding。
        min_ratio: 中文字符占比下限（对非空白字符数而言）。
        quiet: 静默模式不打印校验结果。
        violations_out: 若提供 Path，把违规明细写入 language-violations.json。

    Returns:
        违规 finding 列表，形如 [{'id':..., 'ratio':..., 'fields':[...]}]。
    """
    violations = []

    def _check_item(item, parent_idx=None, inner_idx=None):
        text = _collect_language_text(item)
        if not text:
            return
        ratio = _compute_cjk_ratio(text)
        if ratio >= min_ratio:
            return
        fid = item.get('findingId') or item.get('id') or ''
        if not fid:
            fid = f'#result[{parent_idx}].findings[{inner_idx}]'
        non_cn_fields = []
        for key in _LANG_CHECK_FIELDS:
            val = item.get(key)
            if isinstance(val, str) and val.strip():
                if _compute_cjk_ratio(val) < min_ratio:
                    non_cn_fields.append(key)
        violations.append({
            'id': fid,
            'filePath': item.get('filePath') or '',
            'lineNumber': item.get('lineNumber') or 0,
            'ratio': round(ratio, 3),
            'fields': non_cn_fields,
        })

    # 遍历 results：优先展开 findings；否则把 item 本身当作 finding
    for p_idx, entry in enumerate(results):
        if isinstance(entry, dict) and isinstance(entry.get('findings'), list):
            for i_idx, item in enumerate(entry['findings']):
                if isinstance(item, dict):
                    _check_item(item, p_idx, i_idx)
        elif isinstance(entry, dict):
            _check_item(entry, p_idx, 0)

    if violations and not quiet:
        print_colored(
            f"[FAIL] 语言校验失败：{len(violations)} 个 findings 文本字段"
            f"中文占比 < {int(min_ratio * 100)}%",
            Colors.FAIL)
        for v in violations[:20]:
            fields_s = ','.join(v['fields']) or '(未定位)'
            print_colored(
                f"  - {v['id']} @ {v['filePath']}:{v['lineNumber']} "
                f"中文占比 {v['ratio']*100:.1f}%  字段=[{fields_s}]",
                Colors.FAIL)
        if len(violations) > 20:
            print_colored(f"  ... 另有 {len(violations) - 20} 条未列出",
                          Colors.FAIL)
        print_colored(
            "  处理方式：将 findings JSON（agents/<agent>.json）中上述字段改写"
            "为简体中文，重跑 merge_findings.py merge-scan + merge-verify 后"
            "再调用 generate_report.py。",
            Colors.WARNING)

    if violations_out is not None:
        try:
            violations_out.parent.mkdir(parents=True, exist_ok=True)
            with open(violations_out, 'w', encoding='utf-8') as f:
                json.dump({
                    'violations': violations,
                    'minRatio': min_ratio,
                    'checkedFields': list(_LANG_CHECK_FIELDS),
                    'generatedAt': datetime.now(timezone.utc).isoformat(),
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if not quiet:
                print_colored(
                    f"[WARN] 写出 language-violations.json 失败: {e}",
                    Colors.WARNING)

    return violations


# ---------------------------------------------------------------------------
# 输入 schema 归一化（保证字段唯一）
# ---------------------------------------------------------------------------
# 设计原则：
#   - 单文件 --input 可能是任意上下游产物（finding-*.json / merged-*.json /
#     security-scan-report.json / report-payload.json / agent 输出 / 内部 report）
#   - 经过 _normalize_input_data_schema 处理后，返回 dict 中同一语义只保留一个规范字段，
#     所有已识别的别名键会被 pop 删除，避免下游 generate_json_report 同时遇到
#     "findings" 和 "risk_list" 这种二义性
#   - 规范字段：findings(list) / summary(dict) / metadata(dict).auditBatchId
# ---------------------------------------------------------------------------

# payload 风险项（report-payload.json:risk_list[i]）字段映射：snake_case → camelCase。
# 每个规范字段仅被写入一次，确保归一化后 finding dict 不留 snake_case 残余。
_PAYLOAD_RISK_FIELD_MAP = {
    "file_path": "filePath",
    "line_number": "lineNumber",
    "risk_confidence": "confidence",
    "code_snippet": "riskCode",
    "fixed_code": "fixedCode",
    "rule_name": "riskType",
    "rule_id": "ruleId",  # 单独保留，不与 riskType 冲突
    "severity": "severity",
    "description": "description",
    "recommendation": "recommendation",
}

# 顶层 summary 别名 → 规范字段。覆盖 payload schema 与 merged 输出 schema。
_SUMMARY_COUNT_ALIASES = {
    "totalIssues": ("total_risks", "totalFindings"),
    "criticalRisk": ("critical_risks",),
    "highRisk": ("high_risks",),
    "mediumRisk": ("medium_risks",),
    "lowRisk": ("low_risks",),
}

# 归一化结束后必须从顶层 dict 删除的别名键集合。
_INPUT_ALIAS_KEYS_TO_REMOVE = (
    "risk_list", "allIssues", "issues", "auto_fixed_list",
    "total_risks", "critical_risks", "high_risks", "medium_risks", "low_risks",
    "totalFindings", "riskStatistics", "totalRisk", "bySeverity",
    "batch_id", "batchId", "auditBatchId",
)


def _payload_risk_to_finding(item):
    """report-payload.json:risk_list[i] (snake_case) → finding (camelCase)。

    规则：
    - 每条规范字段最多写入一次（dict key 天然唯一）；
    - 未识别字段（如 extra_info）整体丢弃，保持输出 schema 干净；
    - 若 rule_name 缺失但 rule_id 存在，用 rule_id 兜底 riskType。
    """
    if not isinstance(item, dict):
        return {}
    out = {}
    for snake_key, camel_key in _PAYLOAD_RISK_FIELD_MAP.items():
        if snake_key in item and camel_key not in out:
            out[camel_key] = item[snake_key]
    if "riskType" not in out and "ruleId" in out:
        out["riskType"] = out["ruleId"]
    return out


def _coalesce_summary_counts(data):
    """从 data 顶层、data['summary']、data['riskStatistics'] 中收集计数。

    返回 (counts_dict, batch_id_or_none)。counts_dict 只含规范字段
    (totalIssues / criticalRisk / highRisk / mediumRisk / lowRisk)，
    不含任何别名键。
    """
    counts = {}

    def _absorb(src):
        if not isinstance(src, dict):
            return
        # 规范字段直接命名最高优先
        for canonical in _SUMMARY_COUNT_ALIASES:
            if canonical in src and canonical not in counts:
                counts[canonical] = src[canonical]
        # 别名兜底
        for canonical, aliases in _SUMMARY_COUNT_ALIASES.items():
            if canonical in counts:
                continue
            for alias in aliases:
                if alias in src:
                    counts[canonical] = src[alias]
                    break
        # companion JSON 的 totalRisk 等价于 totalIssues
        if "totalIssues" not in counts and "totalRisk" in src:
            counts["totalIssues"] = src["totalRisk"]

    if isinstance(data, dict):
        _absorb(data.get("summary"))
        _absorb(data.get("riskStatistics"))
        # bySeverity（merged-scan.json）= {critical, high, medium, low}
        by_severity = data.get("bySeverity")
        if isinstance(by_severity, dict):
            sev_to_canonical = {
                "critical": "criticalRisk",
                "high": "highRisk",
                "medium": "mediumRisk",
                "low": "lowRisk",
            }
            for sev_key, canonical in sev_to_canonical.items():
                if canonical not in counts and sev_key in by_severity:
                    counts[canonical] = by_severity[sev_key]
        _absorb(data)

    batch_id = None
    if isinstance(data, dict):
        meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        batch_id = (
            meta.get("auditBatchId")
            or data.get("auditBatchId")
            or data.get("batchId")
            or data.get("batch_id")
        )

    return counts, batch_id


def _normalize_input_data_schema(data):
    """归一化单文件 --input 的 data 结构，保证字段唯一性。

    支持以下输入形态：
    - 标准 finding-*.json / agent 输出（findings + 可选 summary）
    - merged-scan.json / merged-verified.json（findings + totalFindings + bySeverity）
    - security-scan-report.json 伴生 JSON（findings + riskStatistics）
    - report-payload.json 上报 payload（risk_list + total_risks/...）
    - 内部 report 结构（allIssues 或 issues:{critical:[], high:[], ...}）

    返回归一化后的新 dict：保留 findings/summary/metadata 三个规范容器，
    删除所有已识别别名键，确保 results[i] 中每个语义只有一个字段名承载。
    """
    if not isinstance(data, dict):
        return data

    out = dict(data)  # 浅拷贝，避免污染调用方

    # ---- findings 来源解析（多别名 → 单一 findings 字段）----
    findings = None
    if isinstance(out.get("findings"), list):
        findings = out["findings"]
    elif isinstance(out.get("risk_list"), list):
        findings = [_payload_risk_to_finding(item) for item in out["risk_list"] if isinstance(item, dict)]
    elif isinstance(out.get("allIssues"), list):
        findings = list(out["allIssues"])
    elif isinstance(out.get("issues"), dict):
        # 内部 report 结构：{"issues": {"critical": [...], "high": [...], ...}}
        flattened = []
        for level_key in ("critical", "high", "medium", "low"):
            level_list = out["issues"].get(level_key)
            if isinstance(level_list, list):
                flattened.extend(level_list)
        findings = flattened

    if findings is not None:
        out["findings"] = findings

    # ---- summary 计数归一（多别名 → 单一 summary dict）----
    canonical_counts, batch_id = _coalesce_summary_counts(data)
    existing_summary = out.get("summary") if isinstance(out.get("summary"), dict) else {}
    merged_summary = dict(existing_summary)
    for k, v in canonical_counts.items():
        if k not in merged_summary or not merged_summary.get(k):
            merged_summary[k] = v
    if merged_summary:
        out["summary"] = merged_summary

    # ---- metadata.auditBatchId 归一 ----
    if batch_id:
        meta = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
        meta = dict(meta)
        if not meta.get("auditBatchId"):
            meta["auditBatchId"] = batch_id
        out["metadata"] = meta

    # ---- 强制删除所有已识别别名键，保证字段唯一 ----
    for alias_key in _INPUT_ALIAS_KEYS_TO_REMOVE:
        out.pop(alias_key, None)

    return out


def convert_remediation_to_findings(data):
    """将 remediation agent 输出格式转换为统一 camelCase findings 格式。

    历史上此函数返回 {'RiskList': [...]}（PascalCase 报告契约），
    迁移到统一 schema 后改为 {'findings': [...]} 单一规范。
    """
    remediations = data.get('remediations', [])
    if not remediations:
        return None

    findings = []
    for r in remediations:
        # 使用集中式归一化函数统一字段
        normalized = normalize_finding(r)
        entry = to_report_format(normalized)
        # 保留 0-day / AI 推理标记
        merged_id = r.get('mergedId', r.get('findingId', ''))
        if merged_id:
            entry['mergedId'] = merged_id
        audited_by = r.get('auditedBy', [])
        if audited_by:
            entry['auditedBy'] = audited_by
        # 标记发现来源（用于 0-day 判断）
        discovery_method = r.get('discoveryMethod', '')
        if discovery_method:
            entry['discoveryMethod'] = discovery_method
        findings.append(entry)

    # 构造 summary
    critical = 0
    high = 0
    medium = 0
    low = 0
    for entry in findings:
        level = get_risk_level_normalized(entry.get('severity', 'low'))
        if level == 'critical':
            critical += 1
        elif level == 'high':
            high += 1
        elif level == 'medium':
            medium += 1
        else:
            low += 1

    # 收集涉及的文件
    file_set = {}
    for entry in findings:
        fp = entry.get('filePath', '')
        if fp:
            if fp not in file_set:
                file_set[fp] = {'fileName': os.path.basename(fp), 'filePath': fp, 'issues': 0}
            file_set[fp]['issues'] += 1

    normalized = {
        'metadata': data.get('metadata', {}),
        'summary': {
            'totalIssues': len(findings),
            'criticalRisk': critical,
            'highRisk': high,
            'mediumRisk': medium,
            'lowRisk': low,
        },
        'findings': findings,
        '_files': list(file_set.values()),
    }

    # 保留攻击链信息（统一 schema 使用单数 attackChain）
    attack_chain = data.get('attackChain', data.get('chainVerification', []))
    if attack_chain:
        normalized['attackChain'] = attack_chain

    return normalized


def load_audit_results(input_path, audit_batch_id=None):
    """加载审计结果"""
    results = []
    summary = None
    # 走 is_dir 分支时会被填充早于会话锁的产物名；其他分支保持空列表
    stale_files = []

    # 确定输入路径
    if audit_batch_id and not input_path:
        for scan_dir in get_scan_output_dirs(os.getcwd()):
            path = scan_dir / audit_batch_id
            if path.exists():
                input_path = str(path)
                break

    if not input_path:
        raise ValueError("未指定输入路径，请使用 --input 或 --audit-batch-id")

    input_path = Path(input_path)

    if input_path.is_file():
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # 如果是 remediation agent 格式，先转换
            if 'remediations' in data and 'findings' not in data:
                normalized = convert_remediation_to_findings(data)
                if normalized:
                    data = normalized

            # 归一化多种单文件 schema（payload / merged / companion / 内部 report 等）
            # 保证 data 含 findings + summary + metadata.auditBatchId 规范字段，
            # 别名键（risk_list / total_risks / allIssues / issues / batchId 等）被删除。
            data = _normalize_input_data_schema(data)

            results.append(data)
            if 'summary' in data:
                summary = {
                    'auditBatchId': data.get('metadata', {}).get('auditBatchId', audit_batch_id or 'unknown'),
                    'riskFiles': sum(1 for f in (data.get('_files', []) or []) if f.get('issues', 0) > 0) or (1 if data['summary'].get('totalIssues', 0) > 0 else 0),
                    'totalIssues': data['summary'].get('totalIssues', 0),
                    'criticalRisk': data['summary'].get('criticalRisk', 0),
                    'highRisk': data['summary'].get('highRisk', 0),
                    'mediumRisk': data['summary'].get('mediumRisk', 0),
                    'lowRisk': data['summary'].get('lowRisk', 0),
                    'files': data.get('_files', []) or [{
                        'fileName': data.get('metadata', {}).get('fileName', 'unknown'),
                        'filePath': data.get('metadata', {}).get('filePath', ''),
                        'issues': data['summary'].get('totalIssues', 0)
                    }]
                }

    elif input_path.is_dir():
        # 加载会话锁 — 用于检测 summary/finding 是否为本次扫描的产物
        # 报告生成不像 gate / upload 那样 fail-fast，但需要把陈旧情况标注给用户
        scan_session = load_scan_session(input_path)
        stale_files = []

        summary_file = input_path / "summary.json"
        if summary_file.exists():
            if scan_session is not None and not is_output_fresh(summary_file, scan_session):
                stale_files.append(summary_file.name)
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
            # 兼容 summary.json 中的不同字段名
            if isinstance(summary, dict):
                # batchId → auditBatchId
                if 'batchId' in summary and 'auditBatchId' not in summary:
                    summary['auditBatchId'] = summary['batchId']
                # totalFindings → totalIssues
                if 'totalFindings' in summary and 'totalIssues' not in summary:
                    summary['totalIssues'] = summary['totalFindings']
            summary_id = summary.get('auditBatchId') if isinstance(summary, dict) else None
            if audit_batch_id and (not summary_id or summary_id == 'unknown'):
                summary['auditBatchId'] = audit_batch_id
            elif not summary_id or summary_id == 'unknown':
                summary['auditBatchId'] = input_path.name

        # 从 batch-plan.json 补充 scanFiles（扫描文件总数）与扫描时间
        batch_plan_file = input_path / "batch-plan.json"
        if batch_plan_file.exists():
            with open(batch_plan_file, 'r', encoding='utf-8') as f:
                batch_plan = json.load(f)
            total_files_from_plan = batch_plan.get('total_files', 0)
            if summary is None:
                summary = {}
            if total_files_from_plan > 0:
                if not summary.get('totalFiles') and not summary.get('scanFiles'):
                    summary['totalFiles'] = total_files_from_plan
            if batch_plan.get('scan_timestamp') and not summary.get('scanTime'):
                summary['scanTime'] = batch_plan.get('scan_timestamp')
            if batch_plan.get('scan_mode') and not summary.get('scanMode'):
                summary['scanMode'] = batch_plan.get('scan_mode')
        elif scan_session is not None:
            if summary is None:
                summary = {}
            if scan_session.get('startedAtIso') and not summary.get('scanTime'):
                summary['scanTime'] = scan_session.get('startedAtIso')

        for file_path in sorted(input_path.glob("finding-*.json")):
            if scan_session is not None and not is_output_fresh(file_path, scan_session):
                stale_files.append(file_path.name)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'remediations' in data and 'findings' not in data:
                    normalized = convert_remediation_to_findings(data)
                    if normalized:
                        data = normalized
                results.append(data)

        # 如果没有 finding-*.json，尝试加载最终合并产物。
        # 优先使用 merged-verified.json；存在且 findings=[] 时代表后置验证/过滤已清空风险，
        # 不允许再回退 merged-scan.json。
        if not results:
            for merged_name in ("merged-verified.json", "merged-scan.json"):
                merged_scan_file = input_path / merged_name
                if not merged_scan_file.exists():
                    continue
                # 与 summary/finding-*.json 同样的 session 校验，
                # 防止 finding-*.json 缺失时回退读到上次扫描遗留的合并产物。
                if scan_session is not None and not is_output_fresh(merged_scan_file, scan_session):
                    stale_files.append(merged_scan_file.name)
                    print_colored(
                        f"[generate_report] [WARN] {merged_name} 早于本次会话，跳过兜底加载",
                        Colors.WARNING,
                    )
                    continue
                with open(merged_scan_file, 'r', encoding='utf-8') as f:
                    merged_data = json.load(f)
                if 'findings' in merged_data and isinstance(merged_data['findings'], list):
                    # 空 findings 场景（早退 / 无漏洞）：构造最小 result entry 使 results 非空
                    if not merged_data['findings']:
                        results.append({
                            'metadata': {
                                'fileName': merged_name,
                                'filePath': str(merged_scan_file),
                            },
                            'summary': {
                                'totalIssues': 0, 'criticalRisk': 0,
                                'highRisk': 0, 'mediumRisk': 0, 'lowRisk': 0,
                            },
                            'findings': [],
                        })
                        # 从合并产物构建空 summary，并透传 early_exit 信息
                        merged_meta = merged_data.get('metadata', {})
                        merged_summary = {
                            'auditBatchId': audit_batch_id or input_path.name or 'unknown',
                            'riskFiles': 0,
                            'totalIssues': 0,
                            'criticalRisk': 0, 'highRisk': 0,
                            'mediumRisk': 0, 'lowRisk': 0,
                            'files': [],
                        }
                        if merged_meta.get('early_exit_reason'):
                            merged_summary['early_exit_reason'] = merged_meta['early_exit_reason']
                            merged_summary['skip_detail'] = merged_meta.get('skip_detail', '')
                        if summary and isinstance(summary, dict):
                            for k in ('riskFiles', 'totalIssues', 'criticalRisk', 'highRisk', 'mediumRisk', 'lowRisk', 'files'):
                                summary[k] = merged_summary[k]
                            if not summary.get('auditBatchId') or summary.get('auditBatchId') == 'unknown':
                                summary['auditBatchId'] = merged_summary['auditBatchId']
                            if merged_summary.get('early_exit_reason'):
                                summary['early_exit_reason'] = merged_summary['early_exit_reason']
                                summary['skip_detail'] = merged_summary.get('skip_detail', '')
                        else:
                            summary = merged_summary
                    else:
                        # 按 riskType 分组转换为 finding-*.json 等价结构
                        by_risk_type = {}
                        for finding in merged_data['findings']:
                            rt = finding.get('riskType', 'unknown')
                            slug = rt.lower().replace(' ', '-').replace('_', '-')
                            by_risk_type.setdefault(slug, []).append(finding)

                        for slug, group_findings in by_risk_type.items():
                            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                            grouped = []
                            for gf in group_findings:
                                # 归一化后转为报告格式
                                nf = normalize_finding(gf)
                                entry = to_report_format(nf)
                                sev = (nf.get('severity') or 'medium').lower()
                                if sev in sev_counts:
                                    sev_counts[sev] += 1
                                # 携带攻击向量/调用链数据
                                attack_vector = gf.get('attackVector', '')
                                attack_chain = gf.get('attackChain')
                                if attack_chain and isinstance(attack_chain, dict):
                                    entry['attackChain'] = attack_chain
                                elif attack_chain and isinstance(attack_chain, str):
                                    entry['attackChain'] = attack_chain
                                elif attack_vector:
                                    source_file = nf.get('filePath', '')
                                    source_line = nf.get('lineNumber', 0)
                                    sink_snippet = nf.get('riskCode', '')
                                    entry['attackChain'] = {
                                        'source': attack_vector,
                                        'sink': {'file': source_file, 'line': source_line, 'description': sink_snippet} if source_file else sink_snippet,
                                    }
                                grouped.append(entry)
                            results.append({
                                'metadata': {
                                    'fileName': f'finding-{slug}.json',
                                    'filePath': str(merged_scan_file),
                                    'riskType': slug,
                                },
                                'summary': {
                                    'totalIssues': len(group_findings),
                                    'criticalRisk': sev_counts['critical'],
                                    'highRisk': sev_counts['high'],
                                    'mediumRisk': sev_counts['medium'],
                                    'lowRisk': sev_counts['low'],
                                },
                                'findings': grouped,
                            })

                        # 从合并产物构建 summary
                        if results:
                            merged_summary = {
                                'auditBatchId': audit_batch_id or input_path.name or 'unknown',
                                'riskFiles': len(by_risk_type),
                                'totalIssues': merged_data.get('totalFindings', len(merged_data['findings'])),
                                'criticalRisk': merged_data.get('bySeverity', {}).get('critical', 0),
                                'highRisk': merged_data.get('bySeverity', {}).get('high', 0),
                                'mediumRisk': merged_data.get('bySeverity', {}).get('medium', 0),
                                'lowRisk': merged_data.get('bySeverity', {}).get('low', 0),
                                'files': [
                                    {'fileName': f'finding-{slug}.json', 'filePath': '', 'issues': len(gf_list)}
                                    for slug, gf_list in by_risk_type.items()
                                ]
                            }
                            if summary and isinstance(summary, dict):
                                for k in ('riskFiles', 'totalIssues', 'criticalRisk', 'highRisk', 'mediumRisk', 'lowRisk', 'files'):
                                    summary[k] = merged_summary[k]
                                if not summary.get('auditBatchId') or summary.get('auditBatchId') == 'unknown':
                                    summary['auditBatchId'] = merged_summary['auditBatchId']
                            else:
                                summary = merged_summary
                    break

        # 如果仍无结果，尝试加载 agents 子目录中的 remediation.json 或 verifier.json
        if not results:
            agents_dir = input_path / "agents"
            if agents_dir.is_dir():
                for candidate in ["remediation.json", "verifier.json"]:
                    candidate_path = agents_dir / candidate
                    if candidate_path.exists():
                        with open(candidate_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if 'remediations' in data or 'verifiedFindings' in data:
                            if 'remediations' in data:
                                normalized = convert_remediation_to_findings(data)
                            elif 'verifiedFindings' in data:
                                # verifier 格式也做简单转换
                                vdata = dict(data)
                                vdata['remediations'] = vdata.pop('verifiedFindings', [])
                                normalized = convert_remediation_to_findings(vdata)
                            if normalized:
                                results.append(normalized)
                                break

        if not summary and results:
            total_issues = 0
            critical_risk = 0
            high_risk = 0
            medium_risk = 0
            low_risk = 0
            files = []

            for r in results:
                s = r.get('summary', {})
                total_issues += s.get('totalIssues', 0)
                critical_risk += s.get('criticalRisk', 0)
                high_risk += s.get('highRisk', 0)
                medium_risk += s.get('mediumRisk', 0)
                low_risk += s.get('lowRisk', 0)
                files.append({
                    'fileName': r.get('metadata', {}).get('fileName', 'unknown'),
                    'filePath': r.get('metadata', {}).get('filePath', ''),
                    'issues': s.get('totalIssues', 0)
                })

            summary = {
                'auditBatchId': audit_batch_id or input_path.name or 'unknown',
                'riskFiles': sum(1 for r in results if r.get('summary', {}).get('totalIssues', 0) > 0),
                'totalIssues': total_issues,
                'criticalRisk': critical_risk,
                'highRisk': high_risk,
                'mediumRisk': medium_risk,
                'lowRisk': low_risk,
                'files': files
            }
    else:
        raise ValueError(f"输入路径不存在: {input_path}")

    if summary and isinstance(summary, dict):
        summary_id = summary.get('auditBatchId')
        if audit_batch_id and (not summary_id or summary_id == 'unknown'):
            summary['auditBatchId'] = audit_batch_id
        elif not summary_id or summary_id == 'unknown':
            if input_path.is_dir():
                summary['auditBatchId'] = input_path.name
            elif input_path.is_file():
                parent_name = input_path.parent.name
                if parent_name.startswith("audit-"):
                    summary['auditBatchId'] = parent_name

    # 兼容 summary 中的不同字段名（覆盖所有输入路径）
    if summary and isinstance(summary, dict):
        if 'batchId' in summary and 'auditBatchId' not in summary:
            summary['auditBatchId'] = summary['batchId']
        if 'totalFindings' in summary and 'totalIssues' not in summary:
            summary['totalIssues'] = summary['totalFindings']

    if summary is None:
        summary = {}
    if input_path.is_dir():
        project_type_info = _load_project_type_info(input_path)
    elif input_path.is_file():
        project_type_info = _load_project_type_info(input_path.parent)
    else:
        project_type_info = {}
    if project_type_info:
        summary['project_type'] = project_type_info.get('project_type', PRODUCT_SHAPE_UNKNOWN)
        if project_type_info.get('project_type_code'):
            summary['project_type_code'] = project_type_info['project_type_code']
        if project_type_info.get('product_category'):
            summary['product_category'] = project_type_info['product_category']
        if project_type_info.get('product_subtype'):
            summary['product_subtype'] = project_type_info['product_subtype']
        if project_type_info.get('product_shape'):
            summary['product_shape'] = project_type_info['product_shape']
        if project_type_info.get('product_shape_decision'):
            summary['product_shape_decision'] = project_type_info['product_shape_decision']
        if project_type_info.get('product_shape_evidence_chain'):
            summary['product_shape_evidence_chain'] = project_type_info['product_shape_evidence_chain']
        if project_type_info.get('agent_profile'):
            summary['agent_profile'] = project_type_info['agent_profile']
    elif not summary.get('project_type'):
        summary['project_type'] = PRODUCT_SHAPE_UNKNOWN

    # 注入陈旧文件警告（仅目录输入路径会设置 stale_files）
    # 报告生成器不像 gate / upload 那样 fail-fast，因此把陈旧情况附在 summary 里
    # 让 stderr 与上层 CLI 调用方都能感知，避免静默生成历史报告
    if stale_files:
        if summary is None:
            summary = {}
        summary['_staleFiles'] = stale_files
        print_colored(
            f"[generate_report] [WARN] 检测到 {len(stale_files)} 个早于本次扫描会话的产物：{stale_files}。"
            "报告将基于这些文件生成，但可能反映上次扫描的结果。",
            Colors.WARNING,
        )

    return results, summary



def resolve_git_base(input_path):
    if not input_path:
        return Path.cwd()
    try:
        path = Path(input_path)
        if path.is_file():
            return path.parent
        return path
    except Exception:
        return Path.cwd()


def _format_file_entries(files):
    formatted = []
    for item in files or []:
        if isinstance(item, dict):
            entry = dict(item)
            if "timestamp" in entry:
                entry["timestamp"] = format_beijing_time(entry.get("timestamp"))
            formatted.append(entry)
        else:
            formatted.append(item)
    return formatted


def _resolve_issue_file_path(issue_path, fallback_path, file_name):
    issue_path = issue_path or ""
    fallback_path = fallback_path or ""
    if fallback_path:
        normalized = issue_path.replace("\\", "/")
        if not issue_path or normalized.startswith("task/") or issue_path == file_name:
            return fallback_path
    return issue_path or fallback_path


def get_risk_level_normalized(level):
    """标准化风险等级（支持4级：critical/high/medium/low）"""
    level_lower = str(level).lower()
    if level_lower in ['critical', '严重']:
        return 'critical'
    elif level_lower in ['high', '高']:
        return 'high'
    elif level_lower in ['medium', '中', 'moderate', '中等']:
        return 'medium'
    else:
        return 'low'


def _build_fallback_attack_chain(issue, raw_issue):
    """Auto-construct attackChain from available finding fields when explicit chain is missing.

    Uses attackVector/description for source, filePath+lineNumber+riskCode for sink.
    Returns a dict {source, sink, traceMethod} or None if insufficient data.
    """
    attack_vector = raw_issue.get('attackVector', '')
    description = issue.get('description', '')

    file_path = issue.get('filePath', '')
    line_number = issue.get('lineNumber')
    code_snippet = issue.get('riskCode', '')
    trace_method = raw_issue.get('traceMethod', '')

    if not file_path and not code_snippet:
        return None

    source = attack_vector or ''
    if not source and description:
        source = description.split('\u3002')[0].split('\uff0c')[0][:120]
    if not source:
        return None

    sink = {}
    if file_path:
        sink['file'] = file_path
    if line_number:
        sink['line'] = line_number
    if code_snippet:
        sink['description'] = code_snippet

    chain = {
        'source': source,
        'propagation': [],
        'sink': sink if isinstance(sink, dict) and sink else code_snippet,
    }
    if trace_method:
        chain['traceMethod'] = trace_method

    return chain


_SCAN_MODE_LABELS = {
    'deep': '深度扫描',
    'light': '快速扫描',
    'fast': '极速扫描',
}


def _extract_scan_mode(scan_mode_arg, summary_scan_mode, batch_id):
    """Extract scan mode from explicit argument, summary.json field, or batch_id.

    Priority: CLI arg > summary.json scanMode > batch_id parsing.
    """
    if scan_mode_arg:
        return _SCAN_MODE_LABELS.get(scan_mode_arg, scan_mode_arg)
    if summary_scan_mode:
        return _SCAN_MODE_LABELS.get(summary_scan_mode, summary_scan_mode)
    if not batch_id or batch_id == 'unknown':
        return '未知'
    parts = batch_id.split('-')
    known_modes = {'deep', 'light', 'fast'}
    if len(parts) >= 2 and parts[1] in known_modes:
        return _SCAN_MODE_LABELS.get(parts[1], parts[1])
    if len(parts) >= 1 and parts[0] in known_modes:
        return _SCAN_MODE_LABELS.get(parts[0], parts[0])
    return '未知'


# security-scan-report.json 对外风险项固定字段（统一 camelCase canonical schema）。
# 字段集合与 merged-verified.json > findings、merge_findings.py 输出保持一致；
# 即 merged-verified.json 缺失，也按这组字段从 finding-*.json / merged-scan.json 兜底转换。
_EXTERNAL_RISK_LIST_FIELDS = (
    'findingId', 'riskType', 'severity', 'filePath', 'lineNumber', 'confidence',
    'title', 'description', 'attackScenario', 'recommendation', 'riskCode', 'fixedCode',
    'sourceAgent', 'auditedBy', 'discoveryMethod', 'verificationStatus', 'challengeVerdict',
    'traceMethod', 'confidenceBreakdown', 'confidenceCeiling', 'confidenceCeilingReason',
    'defenses', 'attackPayload', 'attackChain', 'callChain', 'component', 'currentVersion',
    'fixedVersion', 'cve', 'cwe', 'source', 'reasoning', 'dependencyFile', 'manifestFile',
    'mergedId', 'isZeroDay', 'humanReviewRequired', 'originalSeverity',
)


def _load_plugin_metadata():
    """读取当前插件的名称和版本，失败时返回保守默认值。"""
    plugin_file = Path(__file__).resolve().parent.parent / ".codebuddy-plugin" / "plugin.json"
    metadata = {"name": "security-scan", "version": "unknown"}
    try:
        with plugin_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            metadata["name"] = str(data.get("name") or metadata["name"])
            metadata["version"] = str(data.get("version") or metadata["version"])
    except Exception:
        pass
    return metadata


def _to_int_or_default(value, default=0):
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool_or_default(value, default=False):
    if isinstance(value, bool):
        return value
    if value in (None, ''):
        return default
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'y', '是'}
    return bool(value)


def _format_external_risk_item(raw_issue, issue_entry=None):
    """生成 security-scan-report.json 对外固定字段风险项（统一 camelCase）。

    迁移说明：之前曾经从 PascalCase（FilePath/RiskLevel/RiskCode/...）以及内部
    intermediate dict 多源回退取值。现在严格按 unified schema 只读 camelCase 规范字段，
    issue_entry（来自 generate_json_report 内部 dict）也已经是 camelCase。
    """
    raw = raw_issue if isinstance(raw_issue, dict) else {}
    issue = issue_entry if isinstance(issue_entry, dict) else {}

    def _pick(key, default=''):
        value = raw.get(key)
        if value is None or value == '':
            value = issue.get(key, default)
        if value is None or value == '':
            return default
        return value

    severity = get_risk_level_normalized(_pick('severity', 'low'))
    line_number = _to_int_or_default(_pick('lineNumber', 0))
    confidence = _to_int_or_default(_pick('confidence', 0))

    trace_method = raw.get('traceMethod') or issue.get('traceMethod') or ''
    if not trace_method and isinstance(raw.get('attackChain'), dict):
        trace_method = raw['attackChain'].get('traceMethod') or ''

    item = {
        'findingId': str(_pick('findingId') or raw.get('id') or ''),
        'riskType': _pick('riskType', '未知风险'),
        'severity': severity,
        'filePath': _pick('filePath'),
        'lineNumber': line_number,
        'confidence': confidence,
        'title': _pick('title') or _pick('riskType'),
        'description': _pick('description'),
        'attackScenario': _pick('attackScenario'),
        'recommendation': _pick('recommendation'),
        'riskCode': _pick('riskCode'),
        'fixedCode': _pick('fixedCode'),
        'sourceAgent': _pick('sourceAgent'),
        'auditedBy': raw.get('auditedBy') if isinstance(raw.get('auditedBy'), list) else issue.get('auditedBy', []),
        'discoveryMethod': _pick('discoveryMethod'),
        'verificationStatus': _pick('verificationStatus'),
        'challengeVerdict': _pick('challengeVerdict'),
        'traceMethod': trace_method,
        'confidenceBreakdown': raw.get('confidenceBreakdown') if isinstance(raw.get('confidenceBreakdown'), dict) else issue.get('confidenceBreakdown', {}),
        'confidenceCeiling': _pick('confidenceCeiling'),
        'confidenceCeilingReason': _pick('confidenceCeilingReason'),
        'defenses': raw.get('defenses', issue.get('defenses', [])),
        'attackPayload': _pick('attackPayload'),
        'attackChain': raw.get('attackChain', issue.get('attackChain', {})),
        'callChain': raw.get('callChain', issue.get('callChain', [])),
        'component': _pick('component'),
        'currentVersion': _pick('currentVersion'),
        'fixedVersion': _pick('fixedVersion'),
        'cve': _pick('cve'),
        'cwe': _pick('cwe'),
        'source': _pick('source'),
        'reasoning': _pick('reasoning'),
        'dependencyFile': _pick('dependencyFile'),
        'manifestFile': _pick('manifestFile'),
        'mergedId': _pick('mergedId'),
        'isZeroDay': _to_bool_or_default(_pick('isZeroDay'), False),
        'humanReviewRequired': _to_bool_or_default(_pick('humanReviewRequired'), False),
        'originalSeverity': _pick('originalSeverity'),
    }
    return {key: item.get(key) for key in _EXTERNAL_RISK_LIST_FIELDS}


def _load_merged_findings_for_report(audit_dir):
    """优先读取 merged-verified.json 的 findings，作为 security-scan-report.json 的 findings。"""
    if not audit_dir:
        return None, ""
    audit_path = Path(audit_dir)
    if audit_path.is_file():
        audit_path = audit_path.parent
    for file_name in ("merged-verified.json", "merged-scan.json"):
        candidate = audit_path / file_name
        if not candidate.exists():
            continue
        try:
            with candidate.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        findings = data.get("findings") if isinstance(data, dict) else None
        if isinstance(findings, list):
            return [_format_external_risk_item(item) for item in findings if isinstance(item, dict)], file_name
    return None, ""


def align_report_findings_with_merged_findings(report, audit_dir):
    """固化 security-scan-report.json 的 findings 字段；优先用 merged-verified，缺失时兜底转换。

    迁移说明：之前此函数填充 report["RiskList"]，统一 schema 后改写到 report["findings"]。
    """
    findings, source = _load_merged_findings_for_report(audit_dir)
    if findings is not None:
        report["findings"] = findings
        report.setdefault("metadata", {})["riskListSource"] = source
        return report

    fallback = report.get("findings")
    if not isinstance(fallback, list):
        fallback = report.get("allIssues", [])
    report["findings"] = [
        _format_external_risk_item(item)
        for item in fallback
        if isinstance(item, dict)
    ]
    report.setdefault("metadata", {})["riskListSource"] = "generated"
    return report


def generate_json_report(results, summary, code_branch=None, project_name=None, scan_mode=None):
    """生成 JSON 格式报告"""
    audit_batch_id = summary.get('auditBatchId') or 'unknown'
    timestamp = format_beijing_time(datetime.now(timezone.utc))
    scan_time = format_beijing_time(
        summary.get('scanTime') or summary.get('scan_timestamp') or timestamp
    )
    code_branch_value = code_branch or "未知"
    project_type = _normalize_project_type(summary.get('project_type') or summary.get('projectType'))
    total_issues = summary.get('totalIssues', 0)
    critical_count = summary.get('criticalRisk', 0)
    high_count = summary.get('highRisk', 0)
    medium_count = summary.get('mediumRisk', 0)
    low_count = summary.get('lowRisk', 0)
    

    # 收集所有风险并分类
    all_issues = []
    findings_list = []
    critical_issues = []
    high_issues = []
    medium_issues = []
    low_issues = []

    all_attack_chains = []

    for result in results:
        file_name = result.get('metadata', {}).get('fileName', '')
        file_path_meta = result.get('metadata', {}).get('filePath', '')

        # 收集攻击链（统一 schema 使用 attackChain 单数；wrapper 层可能是 list 或单值）
        result_chain = result.get('attackChain', result.get('chainVerification', []))
        if result_chain:
            if isinstance(result_chain, list):
                all_attack_chains.extend(result_chain)
            else:
                all_attack_chains.append(result_chain)

        issues = result.get('findings', [])

        for issue in issues:
            level_normalized = get_risk_level_normalized(issue.get('severity', ''))
            raw_file_path = issue.get('filePath', '')
            file_path = _resolve_issue_file_path(raw_file_path, file_path_meta, file_name)
            file_name_value = file_name or os.path.basename(file_path) or "unknown"

            # 判断是否为 0-day / AI 推理发现的漏洞
            discovery_method = issue.get('discoveryMethod', '')
            audited_by = issue.get('auditedBy', [])
            is_zero_day = (
                discovery_method == '0-day'
                or (isinstance(audited_by, list) and any(a in audited_by for a in ('vuln-scan', 'logic-scan', 'red-team')))
            )

            issue_entry = {
                "issueId": len(all_issues),
                "fileName": file_name_value,
                "filePath": file_path,
                "riskType": issue.get('riskType', '未知风险'),
                "severity": level_normalized,
                "lineNumber": issue.get('lineNumber'),
                "riskCode": issue.get('riskCode', ''),
                "confidence": issue.get('confidence', ''),
                "description": issue.get('description', ''),
                "recommendation": issue.get('recommendation', ''),
                "fixedCode": issue.get('fixedCode', ''),
                "isZeroDay": is_zero_day,
                "findingId": issue.get('findingId', ''),
            }
            if issue.get('mergedId'):
                issue_entry["mergedId"] = issue['mergedId']
            # 保留调用链数据（单漏洞 source→propagation→sink 路径）
            attack_chain = issue.get('attackChain')
            if attack_chain and isinstance(attack_chain, (dict, str)):
                issue_entry["attackChain"] = attack_chain
            else:
                # Auto-construct attackChain from available fields
                fallback_chain = _build_fallback_attack_chain(issue_entry, issue)
                if fallback_chain:
                    issue_entry["attackChain"] = fallback_chain

            all_issues.append(issue_entry)
            findings_list.append(_format_external_risk_item(issue, issue_entry))

            if level_normalized == 'critical':
                critical_issues.append(issue_entry)
            elif level_normalized == 'high':
                high_issues.append(issue_entry)
            elif level_normalized == 'medium':
                medium_issues.append(issue_entry)
            else:
                low_issues.append(issue_entry)

    # 如果 summary 中的计数为 0 但实际有 issues，用实际数据覆盖
    actual_total = len(all_issues)
    actual_critical = len(critical_issues)
    actual_high = len(high_issues)
    actual_medium = len(medium_issues)
    actual_low = len(low_issues)
    if actual_total > 0:
        total_issues = actual_total
        critical_count = actual_critical
        high_count = actual_high
        medium_count = actual_medium
        low_count = actual_low

    # 如果 files 列表为空但可以从 _files 或 issues 推导
    files_list = summary.get('files', [])
    if not files_list:
        for result in results:
            files_list.extend(result.get('_files', []))
    if not files_list and all_issues:
        file_map = {}
        for iss in all_issues:
            fp = iss.get('filePath', '')
            if fp and fp not in file_map:
                file_map[fp] = {'fileName': iss.get('fileName', ''), 'filePath': fp, 'issues': 0}
            if fp:
                file_map[fp]['issues'] += 1
        files_list = list(file_map.values())
    risk_files_count = sum(1 for f in files_list if f.get('issues', 0) > 0)

    files = _format_file_entries(files_list)
    # Early exit 信息透传到报告 metadata（仅在有值时写入，避免污染正常报告）
    early_exit_reason = summary.get('early_exit_reason', '') or ''
    skip_detail_val = summary.get('skip_detail', '') or ''
    early_exit_meta = {}
    if early_exit_reason:
        early_exit_meta = {
            "earlyExitReason": early_exit_reason,
            "skipDetail": skip_detail_val,
        }
    plugin_meta = _load_plugin_metadata()
    high_confidence_count = sum(
        1 for issue in all_issues
        if _is_high_confidence(issue.get("confidence"))
    )
    report = {
        "success": True,
        "project_type": project_type,
        "productShape": _normalize_project_type(summary.get('product_shape') or project_type),
        "productShapeDecision": summary.get('product_shape_decision', ''),
        "productShapeEvidenceChain": summary.get('product_shape_evidence_chain', {}),
        "metadata": {
            "pluginName": plugin_meta["name"],
            "pluginVersion": plugin_meta["version"],
            "auditBatchId": audit_batch_id,
            "generatedAt": timestamp,
            "scanTime": scan_time,
            "codeBranch": code_branch_value,
            "scanMode": scan_mode or "未知",
            "projectName": project_name or "",
            "project_type": project_type,
            "productCategory": summary.get('product_category', ''),
            "productSubtype": summary.get('product_subtype', ''),
            "productShape": _normalize_project_type(summary.get('product_shape') or project_type),
            "productShapeDecision": summary.get('product_shape_decision', ''),
            "productShapeEvidenceChain": summary.get('product_shape_evidence_chain', {}),
            **early_exit_meta,
        },
        "summary": {
            "scanFiles": summary.get('scanFiles', 0) or summary.get('totalFiles', 0),
            "riskFiles": risk_files_count,
            "highConfidenceRisk": high_confidence_count,
            "totalIssues": total_issues,
            "criticalRisk": critical_count,
            "highRisk": high_count,
            "mediumRisk": medium_count,
            "lowRisk": low_count
        },
        "files": files,
        "issues": {
            "critical": critical_issues,
            "high": high_issues,
            "medium": medium_issues,
            "low": low_issues
        },
        "allIssues": all_issues,
        "findings": findings_list,
    }

    if all_attack_chains:
        # 统一 schema：使用单数 attackChain；多条目以列表传递
        report["attackChain"] = all_attack_chains

    return report


def resolve_input_path(input_path, audit_batch_id=None):
    """解析输入路径（用于写回 summary.json）"""
    if input_path:
        return Path(input_path)
    if audit_batch_id:
        for scan_dir in get_scan_output_dirs(os.getcwd()):
            path = scan_dir / audit_batch_id
            if path.exists():
                return Path(path)
    return None


def ensure_summary_file(input_path, summary):
    """确保目录输入生成 summary.json"""
    if not input_path or not input_path.is_dir():
        return
    summary_path = input_path / "summary.json"
    if summary_path.exists() or not isinstance(summary, dict):
        return
    try:
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    except Exception:
        return


def resolve_default_output_path(output_format, resolved_input, summary):
    """推导默认输出路径。

    - HTML：优先写回审计目录中的固定文件名 `security-scan-report.html`
      （若无法定位审计目录，则回退到当前目录 + batchId 命名）
    - JSON：默认输出到 stdout，因此返回 None
    """
    if output_format != "html":
        return None

    if resolved_input and resolved_input.is_dir():
        return resolved_input / DEFAULT_HTML_REPORT_NAME

    batch_id = (summary or {}).get('auditBatchId', 'unknown')
    return Path.cwd() / f"security-scan-report-{batch_id}.html"


def ensure_output_parent(output_path):
    """确保输出文件的父目录存在，并返回绝对路径字符串。"""
    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path.resolve())


def _risk_label(level):
    if level == "critical":
        return "严重"
    if level == "high":
        return "高"
    if level == "medium":
        return "中"
    return "低"


# 风险类型英文→中文映射
_RISK_TYPE_CN_MAP = {
    "CODE_EXECUTION": "代码执行",
    "COMMAND_INJECTION": "命令注入",
    "EXPRESSION_INJECTION": "表达式注入",
    "HARDCODED_SECRET": "硬编码密钥",
    "IDOR": "越权访问",
    "INSECURE_CONFIGURATION": "不安全配置",
    "INSECURE_COOKIE": "不安全Cookie",
    "INSECURE_DESERIALIZATION": "不安全反序列化",
    "OPEN_REDIRECT": "开放重定向",
    "PATH_TRAVERSAL": "路径遍历",
    "PROTOTYPE_POLLUTION": "原型链污染",
    "SQL_INJECTION": "SQL注入",
    "SSRF": "服务端请求伪造",
    "SSTI": "模板注入",
    "UNRESTRICTED_FILE_UPLOAD": "任意文件上传",
    "WEAK_CRYPTOGRAPHY": "弱加密",
    "XSS": "跨站脚本",
    "XXE": "XML外部实体注入",
    "CSRF": "跨站请求伪造",
    "LDAP_INJECTION": "LDAP注入",
    "LOG_INJECTION": "日志注入",
    "RACE_CONDITION": "竞态条件",
    "BUFFER_OVERFLOW": "缓冲区溢出",
    "INFORMATION_DISCLOSURE": "信息泄露",
    "AUTHENTICATION_BYPASS": "认证绕过",
    "PRIVILEGE_ESCALATION": "权限提升",
    # 分类代码映射
    "C1.1": "SQL注入",
    "C1.2": "命令注入",
    "C1.3": "服务端请求伪造(SSRF)",
    "C1.4": "LDAP注入",
    "C1.5": "XPath注入",
    "C2.1": "硬编码密钥",
    "C2.2": "弱加密算法",
    "C2.3": "不安全的密钥管理",
    "C2.4": "不安全随机数",
    "C3.1": "认证绕过",
    "C3.2": "授权绕过",
    "C3.3": "会话管理缺陷",
    "C4.1": "路径遍历",
    "C4.2": "任意文件上传",
    "C4.3": "任意文件读取",
    "C5.1": "敏感信息泄露",
    "C5.2": "日志注入",
    "C5.3": "错误信息泄露",
    "C6.1": "SSRF",
    "C6.2": "XXE",
    "C7.1": "业务逻辑缺陷",
    "C7.2": "竞态条件",
    "C7.3": "越权访问",
    "D2.1": "不安全的HTTP头",
    "D2.2": "不安全的Cookie配置",
    "D2.3": "缺少安全头",
    "D2.4": "不安全的安全配置",
}


def _risk_type_chinese(risk_type):
    """将风险类型英文标识转为中文名称"""
    return _RISK_TYPE_CN_MAP.get(risk_type, risk_type)


# ---------- 早退原因中文标签（early_exit_reason → 显示名） ----------

_EARLY_EXIT_REASON_LABELS = {
    'no_sinks': '未检测到可利用的 Sink 点',
    'no_sinks_in_diff': '变更代码中未检测到 Sink 点',
    'no_findings': '扫描后未发现有效风险',
    'no_scannable_files': '变更文件无可扫描的代码 / 配置 / 依赖',
}


def _confidence_chinese(value):
    """将置信度文本值转为中文显示"""
    if value is None or value == '':
        return '无'
    str_val = str(value).strip().lower()
    mapping = {'high': '高', 'medium': '中', 'low': '低', 'very high': '极高', 'very low': '极低'}
    return mapping.get(str_val, str(value))


def _is_high_confidence(raw_conf):
    """判断置信度是否为高置信度"""
    if not raw_conf:
        return False
    if isinstance(raw_conf, str) and raw_conf.strip().lower() in ('high', '高', 'very high', '极高'):
        return True
    try:
        conf_value = float(str(raw_conf).strip())
        return conf_value >= 90
    except (ValueError, TypeError):
        return False


def resolve_companion_json_output_path(html_output_path):
    """根据 HTML 输出路径推导同步 JSON 报告路径。"""
    path = Path(html_output_path).expanduser()
    if path.suffix:
        return path.with_suffix('.json')
    return Path(f"{path}.json")


def generate_companion_json_report(report):
    """生成 HTML 伴生 JSON 报告，作为 HTML 渲染的唯一数据源。

    输出字段保持唯一（不存别名），覆盖 HTML 渲染所需的所有内容：
      - 元数据：pluginName/pluginVersion/project_type/productCategory/productSubtype/
        productShape/productShapeDecision/productShapeEvidenceChain/scanMode/
        auditBatchId/scanTime/generatedAt/codeBranch/projectName
      - 状态：success/earlyExitReason/skipDetail
      - 统计：riskStatistics（含 scanFiles/riskFiles）
      - 数据：findings（统一 camelCase）/files（受影响文件精简列表）
    """
    metadata = report.get("metadata", {})
    summary = report.get("summary", {})
    findings = report.get("findings")
    if not isinstance(findings, list):
        findings = report.get("allIssues", [])
    findings = [
        _format_external_risk_item(issue)
        for issue in findings
        if isinstance(issue, dict)
    ]
    high_confidence_count = summary.get("highConfidenceRisk")
    if high_confidence_count is None:
        high_confidence_count = sum(
            1 for issue in report.get("allIssues", [])
            if _is_high_confidence(issue.get("confidence"))
        )
    plugin_name = metadata.get("pluginName") or "security-scan"
    plugin_version = metadata.get("pluginVersion") or "unknown"
    project_type = _normalize_project_type(report.get("project_type") or metadata.get("project_type"))

    # 精简 files 列表：HTML 只用到 path/issues/severity 等基础字段
    files_compact = []
    for f in report.get("files", []) or []:
        if not isinstance(f, dict):
            continue
        entry = {
            "path": f.get("path") or f.get("filePath") or "",
            "issues": f.get("issues", 0),
            "severity": f.get("severity", ""),
            "timestamp": f.get("timestamp", ""),
        }
        # 去掉空值，保持紧凑
        files_compact.append({k: v for k, v in entry.items() if v not in ("", None)})

    return {
        "pluginName": plugin_name,
        "pluginVersion": plugin_version,
        "project_type": project_type,
        "productCategory": metadata.get("productCategory", ""),
        "productSubtype": metadata.get("productSubtype", ""),
        "productShape": metadata.get("productShape", report.get("productShape", "")),
        "productShapeDecision": metadata.get("productShapeDecision", report.get("productShapeDecision", "")),
        "productShapeEvidenceChain": metadata.get("productShapeEvidenceChain", report.get("productShapeEvidenceChain", {})),
        "scanMode": metadata.get("scanMode", "未知"),
        "auditBatchId": metadata.get("auditBatchId", "unknown"),
        "scanTime": metadata.get("scanTime") or metadata.get("generatedAt", ""),
        "generatedAt": metadata.get("generatedAt", ""),
        "codeBranch": metadata.get("codeBranch", ""),
        "projectName": metadata.get("projectName", ""),
        "success": bool(report.get("success", False)),
        "earlyExitReason": metadata.get("earlyExitReason", ""),
        "skipDetail": metadata.get("skipDetail", ""),
        "riskStatistics": {
            "highConfidenceRisk": high_confidence_count,
            "totalRisk": summary.get("totalIssues", 0),
            "criticalRisk": summary.get("criticalRisk", 0),
            "highRisk": summary.get("highRisk", 0),
            "mediumRisk": summary.get("mediumRisk", 0),
            "lowRisk": summary.get("lowRisk", 0),
            "scanFiles": summary.get("scanFiles", 0) or summary.get("totalFiles", 0),
            "riskFiles": summary.get("riskFiles", 0),
        },
        "findings": findings,
        "files": files_compact,
    }


def _report_status(success, critical_count, high_count, medium_count, low_count):
    if not success:
        return "failed", "生成失败", "审计结果可能不完整"
    if critical_count:
        return "critical", "需立即处理", "存在严重风险"
    if high_count:
        return "high", "需立即处理", "存在高危风险"
    if medium_count:
        return "medium", "需要关注", "存在中危风险"
    if low_count:
        return "low", "低危风险", "存在低危风险"
    return "clean", "通过", "未发现风险"


_CODE_FENCE_PATTERN = re.compile(r"```([A-Za-z0-9_-]*)\n?([\s\S]*?)```")

# 匹配中文方括号段落标签：【概述】/【影响】/【证据】/【攻击链】等
_SECTION_LABEL_PATTERN = re.compile(r"(?<!^)\s*(?=【[^】]{1,20}】)")


def _format_description_html(description):
    """将 description 文本格式化为带段落分隔的 HTML。

    处理规则：
    1. 保留已有换行（\n -> <br>）
    2. 将【xxx】段落标签前（除开头外）强制插入段落分隔，避免所有内容挤在一行
    3. HTML 特殊字符转义
    """
    if not description:
        return "无描述"
    text = str(description).strip()
    if not text:
        return "无描述"

    # 先在每个【xxx】段落标签前切分（第一个标签除外）
    segments = _SECTION_LABEL_PATTERN.split(text)
    parts = []
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        escaped = escape(seg).replace("\n", "<br>")
        # 如果是【xxx】开头的段落，把标签加粗突出
        m = re.match(r"^【([^】]{1,20})】(.*)$", seg, re.DOTALL)
        if m:
            label = escape(m.group(1))
            body = escape(m.group(2).lstrip()).replace("\n", "<br>")
            parts.append(f'<p class="issue-desc-section"><strong>【{label}】</strong>{body}</p>')
        else:
            parts.append(f'<p class="issue-desc-section">{escaped}</p>')
    if not parts:
        return "无描述"
    return "\n".join(parts)


def _format_recommendation_html(recommendation):
    if not recommendation:
        return ""

    sections = []
    last_index = 0
    for match in _CODE_FENCE_PATTERN.finditer(recommendation):
        if match.start() > last_index:
            sections.append(("text", recommendation[last_index:match.start()]))
        sections.append(("code", (match.group(1).strip(), match.group(2))))
        last_index = match.end()
    if last_index < len(recommendation):
        sections.append(("text", recommendation[last_index:]))

    html_parts = []
    for kind, value in sections:
        if kind == "text":
            text = value.strip()
            if not text:
                continue
            escaped = escape(text).replace("\n", "<br>")
            html_parts.append(f"<p>{escaped}</p>")
            continue

        lang, code = value
        if code is None:
            continue
        code = code.rstrip("\n")
        if code.startswith("\n"):
            code = code[1:]
        elif code.startswith(" "):
            code = code[1:]
        if not code.strip():
            continue
        summary = "修复建议代码"
        if lang:
            summary = f"{summary} ({escape(lang)})"
        html_parts.append(
            f"""
                <details class="code-block" open>
                    <summary>{summary}</summary>
                    <pre><code>{escape(code)}</code></pre>
                </details>
            """
        )

    if not html_parts:
        escaped = escape(str(recommendation)).replace("\n", "<br>")
        return f"<p>{escaped}</p>"
    return "\n".join(html_parts)


def _stringify_chain_node(node):
    """将 attackChain 的 source/sink/propagation 节点统一转为字符串。
    兼容 str 和 dict（如 {"file": "...", "line": 55, "description": "..."}）两种格式。"""
    if isinstance(node, str):
        return node.strip()
    if isinstance(node, dict):
        parts = []
        if node.get('file'):
            loc = str(node['file'])
            if node.get('line'):
                loc += f":{node['line']}"
            parts.append(loc)
        if node.get('description'):
            parts.append(str(node['description']))
        return ' — '.join(parts) if parts else str(node)
    if node is None:
        return ''
    return str(node).strip()


def _format_attack_chain_html(attack_chain):
    """将单个漏洞的 attackChain 渲染为调用链流程图（支持 dict 和 str 两种格式）"""
    if not attack_chain:
        return ""
    # 字符串格式：按 → 分割渲染为简化链路
    if isinstance(attack_chain, str):
        steps = [s.strip() for s in attack_chain.replace('->', '→').split('→') if s.strip()]
        if not steps:
            return ""
        nodes_html = ""
        for i, step in enumerate(steps):
            node_type = 'source' if i == 0 else ('sink' if i == len(steps) - 1 else 'prop')
            node_label = '入口' if i == 0 else ('危险点' if i == len(steps) - 1 else '传播')
            nodes_html += f"""
            <div class="chain-node chain-node-{node_type}">
                <span class="chain-node-label">{node_label}</span>
                <span class="chain-node-text">{escape(step)}</span>
            </div>
            """
            if i < len(steps) - 1:
                nodes_html += '<div class="chain-arrow">↓</div>'
        return f"""
        <div class="issue-section">
            <div class="issue-section-title">调用链路:</div>
            <div class="attack-call-chain">{nodes_html}</div>
        </div>
        """
    if not isinstance(attack_chain, dict):
        return ""
    source = _stringify_chain_node(attack_chain.get('source', ''))
    propagation = attack_chain.get('propagation', [])
    sink = _stringify_chain_node(attack_chain.get('sink', ''))
    raw_trace = attack_chain.get('traceMethod', '')
    trace_method = raw_trace.strip() if isinstance(raw_trace, str) else str(raw_trace or '').strip()
    if not source and not sink:
        return ""

    trace_labels = {
        'LSP': 'LSP 语义追踪',
        'Grep+Read': 'Grep 模式匹配',
        'unknown': '未知',
    }
    trace_badge = ""
    if trace_method:
        label = trace_labels.get(trace_method, escape(trace_method))
        trace_badge = f'<span class="chain-trace-badge">{label}</span>'

    nodes_html = ""
    if source:
        nodes_html += f"""
            <div class="chain-node chain-node-source">
                <span class="chain-node-label">入口</span>
                <span class="chain-node-text">{escape(source)}</span>
            </div>
            <div class="chain-arrow">↓</div>
        """
    for step in (propagation or []):
        step_text = _stringify_chain_node(step)
        if step_text:
            nodes_html += f"""
            <div class="chain-node chain-node-prop">
                <span class="chain-node-label">传播</span>
                <span class="chain-node-text">{escape(step_text)}</span>
            </div>
            <div class="chain-arrow">↓</div>
        """
    if sink:
        nodes_html += f"""
            <div class="chain-node chain-node-sink">
                <span class="chain-node-label">危险点</span>
                <span class="chain-node-text">{escape(sink)}</span>
            </div>
        """

    return f"""
        <div class="issue-section">
            <div class="issue-section-title">调用链路:{trace_badge}</div>
            <div class="attack-call-chain">{nodes_html}</div>
        </div>
    """


def _format_poc_html(poc):
    """渲染攻击请求（PoC）可得性块。"""
    if not poc or not isinstance(poc, dict):
        return ""
    available = (poc.get("available") or "").strip().lower()
    if not available:
        return ""

    avail_labels = {
        "yes": ("可构造攻击请求", "poc-yes"),
        "conditional": ("有条件构造攻击请求", "poc-conditional"),
        "no": ("无法构造攻击请求", "poc-no"),
    }
    reach_labels = {
        "remote-direct": "可直接远程（无前置直达）",
        "remote-conditional": "需前置条件方可远程触发",
        "local-only": "仅本地 / 间接可控",
        "none": "无可达入口",
    }
    label, cls = avail_labels.get(available, (escape(available), "poc-conditional"))
    reach = poc.get("reachability") or ""
    reach_text = reach_labels.get(reach, escape(str(reach))) if reach else ""

    rows = [f'<div class="poc-badge {cls}">{label}</div>']
    if reach_text:
        rows.append(f'<div class="poc-meta">可达性：{reach_text}</div>')
    entry_type = poc.get("entryType")
    if entry_type and entry_type != "none":
        rows.append(f'<div class="poc-meta">入口类型：{escape(str(entry_type))}</div>')

    request = poc.get("request")
    if request:
        rows.append(
            f'<div class="poc-meta">攻击请求 / 触发工件：</div>'
            f'<pre class="issue-code"><code>{escape(str(request))}</code></pre>'
        )

    preconditions = poc.get("preconditions")
    if isinstance(preconditions, list) and preconditions:
        items = "".join(f"<li>{escape(str(p))}</li>" for p in preconditions)
        rows.append(f'<div class="poc-meta">前置条件：</div><ul class="poc-pre">{items}</ul>')

    if available == "no":
        reason = poc.get("notObtainableReason") or "未说明"
        rows.append(
            f'<div class="poc-meta poc-no-reason">无法构造原因（已封顶中危并标记人工复核）：'
            f'{escape(str(reason))}</div>'
        )

    return f"""
        <div class="issue-section poc-section">
            <div class="issue-section-title">攻击请求（PoC）可得性:</div>
            <div class="poc-content">{''.join(rows)}</div>
        </div>
    """


def _format_issue_html(issue, issue_id=None):
    file_name = escape(str(issue.get("fileName", ""))) or "未知文件"
    file_path = escape(str(issue.get("filePath", "")))
    risk_type_raw = escape(str(issue.get("riskType", ""))) or "未知风险"
    risk_type_cn = _risk_type_chinese(risk_type_raw)
    # 如果有中文翻译，显示"中文名称 (分类代码)"，否则只显示分类代码
    risk_type = f"{risk_type_cn} ({risk_type_raw})" if risk_type_cn != risk_type_raw else risk_type_raw
    severity = escape(str(issue.get("severity", ""))).lower() or "low"
    line_number = issue.get("lineNumber")
    description = _format_description_html(issue.get("description", ""))
    recommendation = str(issue.get("recommendation", ""))
    risk_code = escape(str(issue.get("riskCode", "")))
    confidence = _confidence_chinese(issue.get("confidence", ""))
    fixed_code = escape(str(issue.get("fixedCode", "")))
    is_zero_day = issue.get("isZeroDay", False)
    
    # Generate unique ID for the issue card
    id_attr = f' id="issue-{issue_id}"' if issue_id is not None else ""

    line_display = f": {line_number}" if line_number else ""
    location = f"{file_name}{line_display}"
    risk_label = _risk_label(severity)
    if file_path and file_path != file_name:
        location = f"{file_path}{line_display}"

    # 0-day tag
    zero_day_tag = ""
    if is_zero_day:
        zero_day_tag = '<span class="zero-day-tag">0-day线索</span>'

    confidence_html = ""
    if confidence and confidence != "无":
        confidence_html = f'<div class="issue-info-item"><span class="issue-info-label">置信度:</span><span class="mono">{escape(str(confidence))}</span></div>'

    # Build risk code block
    risk_code_block = ""
    if risk_code:
        risk_code_block = f"""
            <div class="issue-section">
                <div class="issue-section-title">风险代码:</div>
                <pre class="issue-code"><code>{risk_code}</code></pre>
            </div>
        """

    # Build recommendation block
    recommendation_block = ""
    recommendation_html = _format_recommendation_html(recommendation)
    if recommendation_html:
        recommendation_block = f"""
            <div class="issue-section">
                <div class="issue-section-title">修复建议:</div>
                <div class="issue-recommendation">{recommendation_html}</div>
            </div>
        """

    # Build fixed code block
    fixed_code_block = ""
    if fixed_code:
        fixed_code_block = f"""
            <div class="issue-section">
                <div class="issue-section-title">修复后代码:</div>
                <pre class="issue-code issue-code-fixed"><code>{fixed_code}</code></pre>
            </div>
        """

    # Build attack call chain block
    attack_chain_block = _format_attack_chain_html(issue.get("attackChain"))

    # Build PoC (attack request) availability block
    poc_block = _format_poc_html(issue.get("poc"))

    # Build verification guide block - 根据漏洞类型生成验证指引
    verification_guide_block = ""
    risk_type_raw_for_guide = issue.get("riskType", "") or issue.get("category", "")

    # 生成有意义的 finding ID：优先使用 findingId/id，否则根据文件+行号生成
    finding_id = issue.get("findingId") or issue.get("id", "")
    if not finding_id:
        # 生成格式如 "src/routes.js:39" 的标识符
        finding_id = f"{file_path}:{line_number}" if file_path and line_number else "unknown"

    # 获取验证指引（返回步骤列表）
    verification_steps = _generate_verification_guide(
        risk_type_raw_for_guide, finding_id, file_path, line_number,
        issue=issue,
    )

    # 渲染步骤列表 HTML
    steps_html_parts = []
    for idx, step in enumerate(verification_steps, 1):
        step_desc = escape(step.get("desc", ""))
        step_cmd = step.get("cmd")
        if step_cmd:
            steps_html_parts.append(f"""
                <div class="verification-step">
                    <div class="verification-step-header">
                        <span class="verification-step-number">步骤 {idx}</span>
                        <span class="verification-step-desc">{step_desc}</span>
                    </div>
                    <pre class="verification-command"><code>{escape(step_cmd)}</code></pre>
                </div>
            """)
        else:
            steps_html_parts.append(f"""
                <div class="verification-step">
                    <div class="verification-step-header">
                        <span class="verification-step-number">步骤 {idx}</span>
                        <span class="verification-step-desc">{step_desc}</span>
                    </div>
                </div>
            """)
    steps_html = "\n".join(steps_html_parts)

    note_text = "请在授权的安全测试环境中执行验证。"

    verification_guide_block = f"""
        <div class="issue-section verification-guide-section">
            <div class="issue-section-title">漏洞验证指引:</div>
            <div class="verification-guide-content">
                <div class="verification-steps-list">
                    {steps_html}
                </div>
                <p class="verification-note">{note_text}</p>
            </div>
        </div>
    """

    return f"""
        <article class="issue-card issue-{severity}"{id_attr}>
            <header class="issue-head">
                <div class="issue-type" title="{risk_type_raw}"><span class="issue-id mono">{escape(str(finding_id))}</span>{risk_type}{zero_day_tag}</div>
                <span class="severity-pill severity-{severity}">{risk_label}</span>
            </header>
            <div class="issue-body">
                <div class="issue-info">
                    <div class="issue-info-item"><span class="issue-info-label">位置:</span><span class="mono">{location}</span></div>
                    {confidence_html}
                </div>
                <div class="issue-section">
                    <div class="issue-section-title">风险描述:</div>
                    <div class="issue-desc">{description}</div>
                </div>
                {attack_chain_block}
                {poc_block}
                {verification_guide_block}
                {risk_code_block}
                {recommendation_block}
                {fixed_code_block}
            </div>
        </article>
    """


def _generate_verification_guide(risk_type, finding_id, file_path, line_number, issue=None):
    """根据风险类型生成具体可落地的验证指引

    返回: steps_list — list of dicts，每步 {"desc": "...", "cmd": "..."} 或 {"desc": "...", "cmd": None}
    """

    # 标准化风险类型
    risk_type_lower = (risk_type or "").lower().strip().replace(' ', '-').replace('_', '-')
    risk_type_code = (risk_type or "").lower().replace(".", "")
    fp = file_path or "<file>"
    ln = line_number or 0

    # ── 分类一：适合动态验证的漏洞类型 ──
    # 这些漏洞可通过 HTTP 请求实际验证（发请求、观察响应差异）
    _dynamic_types = {
        # 注入类 — 发送恶意 payload 观察响应
        "sql-injection", "xss", "command-injection", "ssrf", "path-traversal",
        "idor", "open-redirect", "xxe", "csrf",
        # 代码执行
        "code-execution", "code-injection",
        # 认证授权 — 匿名/伪造凭证请求验证
        "access-control", "auth-bypass", "missing-auth", "missing-authentication",
        "endpoint-exposure",
        # 竞态条件 — 并发请求验证
        "race-condition",
        # 不安全配置 — curl 检查安全头
        "insecure-configuration",
        # 分类代码
        "c11", "c12", "c13", "c14", "c15", "c41", "c42",
        "c61", "c62", "c72", "c73",
    }

    # ── 分类二：仅适合静态验证的漏洞类型 ──
    # 这些是代码层面的问题，无法通过 HTTP 请求动态验证，给出静态代码审查指引
    _static_only_types = {
        # 弱加密/弱随机数 — 代码使用了不安全算法，发请求测不出来
        "weak-cryptography", "weak-crypto", "weak-random",
        "insecure-random", "weak-password-hash", "plaintext-password",
        # 硬编码凭证 — 需要看源码才能发现
        "hardcoded-secret", "hardcoded-credential",
        # 信息泄露/日志泄露 — 代码审查问题
        "information-leak", "information-disclosure", "sensitive-data-logging",
        # 不安全 Cookie — 代码审查 + 简单 curl 即可
        "insecure-cookie",
        # 依赖安全 — 需要 SCA 工具
        "vulnerable-dependency",
        # 业务逻辑 — 需要人工审查流程
        "business-logic", "state-machine-violation", "payment-logic",
        # 密码/会话
        "jwt-weak-key", "jwt-algorithm-confusion", "session-fixation",
        "brute-force-unprotected", "credential-enumeration",
    }

    # ── 分类三：高层分类码需推断 ──
    # C3(认证授权) 多数适合动态验证，但 subcategory=weak-crypto 可能仅适合静态验证
    # C7(业务逻辑) 部分适合动态验证（如 RCE、竞态），部分仅适合静态验证（弱加密）
    if risk_type_code in ("c3", "c7") and issue:
        # 从 subcategory/description 推断是否适合动态验证
        subcat = (issue.get("subcategory", "") or "").lower()
        title = (issue.get("title", "") or "").lower()
        risk_detail = (issue.get("description", "") or "").lower()
        risk_code = (issue.get("riskCode", "") or "").lower()
        combined = f"{subcat} {title} {risk_detail} {risk_code}"
        # 弱加密类 → 静态验证
        if any(kw in combined for kw in ["weak-crypto", "sha-1", "sha1", "md5", "弱加密", "弱随机", "弱密码",
                                          "nonce", "hashlib", "random.rand", "getpass", "密码生成",
                                          "insecure-random", "plaintext-password"]):
            is_dynamic_type = False
        # 可动态验证的
        elif any(kw in combined for kw in ["eval", "rce", "exec(", "race-condition", "竞态",
                                           "auth-bypass", "idor", "越权", "认证绕过", "无认证",
                                           "匿名", "check_lock", "toctou", "权限",
                                           "permission_classes", "loginrequired", "allowany"]):
            is_dynamic_type = True
        else:
            is_dynamic_type = False  # 默认不归为动态验证类型
    else:
        is_dynamic_type = risk_type_lower in _dynamic_types or risk_type_code in _dynamic_types

    is_static_only = risk_type_lower in _static_only_types

    if is_dynamic_type:
        return _build_manual_verification_steps(risk_type_lower, risk_type_code, fp, ln, issue=issue)

    if is_static_only or (risk_type_code in ("c3", "c7") and not is_dynamic_type):
        return _build_static_verification_steps(risk_type_lower, risk_type_code, fp, ln, issue=issue)

    # 其他类型：给出简短的静态验证指引
    return _build_static_verification_steps(risk_type_lower, risk_type_code, fp, ln, issue=issue)


def _build_manual_verification_steps(risk_type_lower, risk_type_code, fp, ln, issue=None):
    """为漏洞构建可执行的动态验证步骤

    优先使用 curl 等动态验证手段，仅将代码查看作为辅助参考。
    """

    # 提取可能的端点路径用于动态验证
    ep_path = ""
    if issue:
        chain = issue.get("attackChain")
        if isinstance(chain, dict):
            source = str(chain.get("source", ""))
            import re as _re
            m = _re.search(r'"(/[/\w\-]+)"', source)
            if m:
                ep_path = m.group(1)

    steps = []

    # Step 1: 动态验证 — 用 curl 对目标端点进行实际请求测试
    if risk_type_lower in ("access-control", "auth-bypass", "missing-auth", "endpoint-exposure") or risk_type_code in ("c3", "c31", "c32", "c33"):
        # 认证/授权缺陷 — 动态验证
        if ep_path:
            steps.append({
                "desc": "不携带任何认证信息直接请求接口（预期应返回 401/403，若返回 200 则漏洞存在）",
                "cmd": f"curl -sv http://<目标地址:端口>{ep_path} 2>&1 | grep -E '(HTTP/|< )'"
            })
            steps.append({
                "desc": "使用伪造的 Authorization 头请求接口（验证是否校验 token 有效性）",
                "cmd": f"curl -sv http://<目标地址:端口>{ep_path} -H 'Authorization: Bearer invalid_token_xxx' 2>&1 | grep -E '(HTTP/|< )'"
            })
        else:
            steps.append({
                "desc": "不携带任何认证信息直接请求接口（将 <接口路径> 替换为实际端点，预期应返回 401/403）",
                "cmd": "curl -sv http://<目标地址:端口>/<接口路径> 2>&1 | grep -E '(HTTP/|< )'"
            })
        steps.append({
            "desc": "检查代码中是否有权限装饰器/注解（辅助确认）",
            "cmd": f"sed -n '{max(1, ln - 20)},{ln}p' {fp} | grep -iE '(auth|permission|login_required|@requires|@Secured|@PreAuthorize|middleware)'"
        })

    elif risk_type_lower in ("hardcoded-secret", "hardcoded-credential") or risk_type_code in ("c21", "c51"):
        # 硬编码密钥/凭证
        steps.append({
            "desc": "提取第 {ln} 行的密钥值并搜索全项目引用".format(ln=ln),
            "cmd": f"grep -rn \"$(sed -n '{ln}p' {fp} | grep -oE '[A-Za-z0-9+/=]{{16,}}' | head -1)\" "
                   f"--include='*.py' --include='*.js' --include='*.java' --include='*.yaml' --include='*.env' ."
        })
        steps.append({
            "desc": "若密钥有效，需立即轮换并迁移到环境变量或密钥管理服务",
            "cmd": None
        })

    elif risk_type_lower in ("weak-crypto", "weak-password-hash", "weak-cryptography", "weak-random") or risk_type_code in ("c22",):
        # 弱加密算法 — 动态验证
        if ep_path:
            steps.append({
                "desc": "发送相同请求两次，验证服务端是否接受重放（缺少 nonce/anti-replay 保护）",
                "cmd": f"curl -s http://<目标地址:端口>{ep_path} -o /dev/null -w '%{{http_code}}' && echo '' && curl -s http://<目标地址:端口>{ep_path} -o /dev/null -w '%{{http_code}}' && echo ''"
            })
        steps.append({
            "desc": "检查响应签名头是否使用弱算法（SHA-1/MD5）",
            "cmd": "curl -sI http://<目标地址:端口>/ | grep -iE '(signature|x-sign|authorization)' || echo '未发现自定义签名头'"
        })
        steps.append({
            "desc": "搜索全项目中的弱加密算法使用（辅助确认）",
            "cmd": "grep -rn --include='*.py' --include='*.js' --include='*.java' --include='*.go' "
                   "-iE '(md5|sha1|\\bdes\\b|\\becb\\b|\\brc4\\b)' . | grep -v node_modules | grep -v __pycache__ | head -20"
        })

    elif risk_type_lower in ("insecure-config", "insecure-configuration", "missing-security-headers") or risk_type_code in ("d21", "d24"):
        # 不安全配置 — 动态验证
        steps.append({
            "desc": "检测 HTTP 响应安全头（将 URL 替换为实际目标地址）",
            "cmd": "curl -sI http://<目标地址:端口>/ | grep -iE '(X-Frame-Options|Content-Security-Policy|X-Content-Type-Options|Strict-Transport-Security|X-XSS-Protection)' || echo '未检测到安全响应头'"
        })
        steps.append({
            "desc": "检查当前配置值（辅助确认）",
            "cmd": f"sed -n '{ln}p' {fp}"
        })

    elif risk_type_lower in ("information-leak", "sensitive-data-logging") or risk_type_code in ("c52", "c53"):
        # 信息泄露/日志泄露 — 动态验证
        if ep_path:
            steps.append({
                "desc": "发送异常输入请求，检查错误响应是否泄露堆栈/调试信息",
                "cmd": f"curl -s http://<目标地址:端口>{ep_path}?id=' 2>&1 | grep -iE '(traceback|exception|stack|debug|error detail)' && echo '发现信息泄露' || echo '未发现明显泄露'"
            })
        steps.append({
            "desc": "搜索可能泄露敏感信息的日志语句（辅助确认）",
            "cmd": "grep -rn --include='*.py' --include='*.js' --include='*.java' "
                   "-iE '(log\\.|logger\\.|console\\.log|print\\().*(?i)(password|token|secret|key|credential|session)' . | head -20"
        })

    elif risk_type_lower in ("insecure-cookie",) or risk_type_code in ("d22",):
        # 不安全 Cookie — 动态验证
        steps.append({
            "desc": "检测 HTTP 响应中 Cookie 的安全属性（将 URL 替换为实际地址）",
            "cmd": "curl -sI http://<目标地址:端口>/login | grep -i 'Set-Cookie'"
        })

    elif risk_type_lower in ("race-condition",) or risk_type_code in ("c72",):
        # 竞态条件 — 动态验证
        if ep_path:
            steps.append({
                "desc": "并发请求测试（同时发送多个请求，检查是否全部成功）",
                "cmd": f"for i in $(seq 1 10); do curl -s http://<目标地址:端口>{ep_path} -X POST -d 'test=race_test_$i' & done; wait; echo '并发请求已完成，检查服务端数据是否一致'"
            })
        else:
            steps.append({
                "desc": "并发请求测试（将 URL 和参数替换为实际值）",
                "cmd": "for i in $(seq 1 10); do curl -s http://<目标地址:端口>/<接口路径> -X POST -d '<参数>' & done; wait; echo '并发请求已完成，检查服务端数据是否一致'"
            })
        steps.append({
            "desc": "检查代码中是否有锁/事务保护（辅助确认）",
            "cmd": f"grep -n -iE '(lock|Lock|synchronized|@Transactional|BEGIN|COMMIT|atomic|mutex|with_lock)' {fp} | head -10"
        })

    elif risk_type_lower in ("business-logic", "state-machine-violation", "payment-logic") or risk_type_code in ("c71",):
        # 业务逻辑 — 动态验证
        if ep_path:
            steps.append({
                "desc": "使用边界值/异常值测试业务逻辑（如负数金额、空值、非法状态转换）",
                "cmd": f"curl -sv http://<目标地址:端口>{ep_path} -X POST -H 'Content-Type: application/json' -d '{{\"amount\": -1}}' 2>&1 | grep -E '(HTTP/|< )'"
            })
        steps.append({
            "desc": "查看完整业务流程上下文（辅助分析）",
            "cmd": f"sed -n '{max(1, ln - 30)},{ln + 30}p' {fp}"
        })

    else:
        # 通用 fallback — 优先动态验证
        if ep_path:
            steps.append({
                "desc": "对目标端点发送请求，检查响应状态和内容",
                "cmd": f"curl -sv http://<目标地址:端口>{ep_path} 2>&1 | grep -E '(HTTP/|< )'"
            })
        else:
            steps.append({
                "desc": "对目标端点发送请求（将 URL 替换为实际路径）",
                "cmd": "curl -sv http://<目标地址:端口>/<接口路径> 2>&1 | grep -E '(HTTP/|< )'"
            })
        steps.append({
            "desc": "搜索相关函数在项目中的调用（辅助分析）",
            "cmd": f"grep -rn --include='*.py' --include='*.js' --include='*.java' --include='*.go' "
                   f"\"$(sed -n '{ln}p' {fp} | grep -oE '\\w+\\(' | head -1 | tr -d '(')\" . | head -10"
        })

    return steps


def _build_static_verification_steps(risk_type_lower, risk_type_code, fp, ln, issue=None):
    """为仅适合静态验证的漏洞类型构建代码审查指引

    这类漏洞（弱加密、硬编码密钥等）无法通过 HTTP 请求动态验证，
    给出精简的代码定位和确认指引。
    """

    steps = []

    if risk_type_lower in ("weak-cryptography", "weak-crypto", "weak-random",
                           "insecure-random", "weak-password-hash", "plaintext-password") or risk_type_code in ("c22",):
        steps.append({
            "desc": "查看风险代码位置，确认使用了不安全的加密算法或随机数生成器",
            "cmd": f"sed -n '{max(1, ln - 10)},{ln + 10}p' {fp}"
        })
        steps.append({
            "desc": "确认是否用于安全敏感场景（密码哈希/签名/加密存储/Token 生成），若非安全场景可降级处理",
            "cmd": None
        })

    elif risk_type_lower in ("hardcoded-secret", "hardcoded-credential") or risk_type_code in ("c21", "c51"):
        steps.append({
            "desc": "查看硬编码凭证的具体位置",
            "cmd": f"sed -n '{max(1, ln - 3)},{ln + 3}p' {fp}"
        })
        steps.append({
            "desc": "若凭证有效，需立即轮换并迁移到环境变量或密钥管理服务",
            "cmd": None
        })

    elif risk_type_lower in ("information-leak", "information-disclosure", "sensitive-data-logging") or risk_type_code in ("c52", "c53"):
        steps.append({
            "desc": "查看日志/输出中是否包含敏感数据",
            "cmd": f"sed -n '{max(1, ln - 5)},{ln + 5}p' {fp}"
        })

    elif risk_type_lower in ("insecure-cookie",) or risk_type_code in ("d22",):
        steps.append({
            "desc": "检查 Cookie 设置是否缺少 Secure/HttpOnly/SameSite 属性",
            "cmd": f"sed -n '{max(1, ln - 5)},{ln + 5}p' {fp}"
        })

    elif risk_type_lower in ("vulnerable-dependency",):
        steps.append({
            "desc": "检查依赖版本是否存在已知 CVE 漏洞",
            "cmd": None
        })

    elif risk_type_lower in ("business-logic", "state-machine-violation", "payment-logic") or risk_type_code in ("c71",):
        steps.append({
            "desc": "查看完整业务流程上下文，分析是否存在流程绕过或非法状态转换",
            "cmd": f"sed -n '{max(1, ln - 20)},{ln + 20}p' {fp}"
        })

    else:
        # 通用静态验证 — 仅定位代码
        steps.append({
            "desc": "查看风险代码位置",
            "cmd": f"sed -n '{max(1, ln - 5)},{ln + 5}p' {fp}"
        })

    return steps


def _format_product_shape_evidence_html(metadata, report):
    """格式化产品形态证据链卡片：结论 + 实际文件证据。"""
    chain = metadata.get("productShapeEvidenceChain") or report.get("productShapeEvidenceChain") or {}
    product_shape = metadata.get("productShape") or report.get("productShape") or ""
    if not isinstance(chain, dict):
        chain = {}
    conclusion = _normalize_project_type(chain.get("conclusion") or product_shape)
    if not conclusion:
        return ""

    evidence = chain.get("evidence") if isinstance(chain.get("evidence"), list) else []
    rows = [f'<p><strong>结论：</strong>{escape(str(conclusion))}</p>']
    decision = chain.get("decision") or metadata.get("productShapeDecision") or report.get("productShapeDecision") or ""
    if decision:
        rows.append(f'<p><strong>判断说明：</strong>{escape(str(decision))}</p>')

    evidence_rows = []
    for item in evidence[:5]:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "")
        line = item.get("line") or item.get("lineNumber") or item.get("lines") or ""
        snippet = str(item.get("snippet") or item.get("code") or item.get("signal") or "")
        reason = str(item.get("reason") or item.get("category") or item.get("source") or "")
        if not (path or snippet or reason):
            continue
        location = escape(path)
        if line:
            location = f"{location}:{escape(str(line))}" if location else escape(str(line))
        snippet_html = f'<div><strong>片段：</strong><span class="mono">{escape(snippet[:240])}</span></div>' if snippet else ""
        reason_html = f'<div><strong>依据：</strong>{escape(reason)}</div>' if reason else ""
        evidence_rows.append(
            "<li>"
            f'<div><strong>位置：</strong><span class="mono">{location or "未标注"}</span></div>'
            f"{snippet_html}"
            f"{reason_html}"
            "</li>"
        )
    if evidence_rows:
        rows.append(f'<div><strong>实际举证：</strong><ul>{"".join(evidence_rows)}</ul></div>')
    else:
        rows.append('<p><strong>实际举证：</strong>未提供有效文件证据，产品形态应视为未知或需人工复核。</p>')

    body = "\n            ".join(rows)
    return f"""
        <section class="card product-shape-card">
            <div class="card-header">产品形态证据链</div>
            {body}
        </section>
    """


def generate_html_report(companion_json):
    """生成 HTML 格式报告。

    数据源唯一：完全从 companion_json（即 security-scan-report.json 的内存对象）读取，
    不再回退访问内部 report 的 summary/allIssues/issues 等字段，保证 JSON 与 HTML 严格一致。

    参数：
      companion_json: dict，generate_companion_json_report() 的返回值
    """
    if not isinstance(companion_json, dict):
        companion_json = {}

    # ── 顶部元数据 ──
    audit_batch_id = escape(str(companion_json.get("auditBatchId") or "unknown"))
    generated_at = escape(str(companion_json.get("generatedAt", "")))
    code_branch = escape(str(companion_json.get("codeBranch", ""))) or "未知"
    project_name = escape(str(companion_json.get("projectName", ""))) or "未知项目"
    project_type = escape(str(_normalize_project_type(companion_json.get("project_type"))))
    scan_mode = escape(str(companion_json.get("scanMode", ""))) or "未知"

    # 产品形态证据链卡片：构造一个最小入参满足 _format_product_shape_evidence_html
    _shape_view = {
        "productShape": companion_json.get("productShape", ""),
        "productShapeDecision": companion_json.get("productShapeDecision", ""),
        "productShapeEvidenceChain": companion_json.get("productShapeEvidenceChain", {}),
    }
    product_shape_evidence_html = _format_product_shape_evidence_html(_shape_view, _shape_view)

    success = bool(companion_json.get("success", False))

    # ── 风险统计（唯一来源：companion_json.riskStatistics） ──
    risk_stats = companion_json.get("riskStatistics") or {}
    total_issues = risk_stats.get("totalRisk", 0)
    critical_count = risk_stats.get("criticalRisk", 0)
    high_count = risk_stats.get("highRisk", 0)
    medium_count = risk_stats.get("mediumRisk", 0)
    low_count = risk_stats.get("lowRisk", 0)
    high_confidence_count = risk_stats.get("highConfidenceRisk", 0)
    scan_files = risk_stats.get("scanFiles", 0)
    risk_files = risk_stats.get("riskFiles", 0)
    status_class, _, _ = _report_status(
        success, critical_count, high_count, medium_count, low_count
    )

    # 副标题固定格式：{N} 个扫描文件 · {M} 个风险文件
    scope = f"{scan_files} 个扫描文件 · {risk_files} 个风险文件"

    # ── 早退横幅 ──
    early_exit_reason = companion_json.get("earlyExitReason", "")
    skip_detail = companion_json.get("skipDetail", "")
    early_exit_banner = ""
    if early_exit_reason:
        reason_label = _EARLY_EXIT_REASON_LABELS.get(early_exit_reason, early_exit_reason)
        detail_html = (
            f'<div style="margin-top:6px;font-size:13px;color:#555;">'
            f'{escape(str(skip_detail))}</div>'
        ) if skip_detail else ''
        scan_mode_raw = companion_json.get("scanMode", "")
        mode_note = (
            f'<div style="margin-top:6px;font-size:12px;color:#666;">'
            f'这是 {escape(str(scan_mode_raw))} 模式的预期行为，而非扫描失败。'
            f'门禁已按"无风险"判通过。</div>'
        ) if scan_mode_raw else ''
        early_exit_banner = (
            f'<section class="early-exit-banner" style="margin:16px 0;padding:14px 18px;'
            f'background:#e0f2fe;border:1px solid #7dd3fc;border-radius:10px;">'
            f'<div style="font-weight:600;color:#0369a1;font-size:14px;">'
            f'扫描已早退：{escape(reason_label)}</div>'
            f'{detail_html}{mode_note}'
            f'</section>'
        )

    # ── findings 是唯一的风险数据源，按 severity 分桶 ──
    all_issues = [f for f in (companion_json.get("findings") or []) if isinstance(f, dict)]
    severity_buckets = {"critical": [], "high": [], "medium": [], "low": []}
    for issue in all_issues:
        sev = get_risk_level_normalized(issue.get("severity"))
        if sev not in severity_buckets:
            sev = "low"
        severity_buckets[sev].append(issue)
    critical_issues = severity_buckets["critical"]
    high_issues = severity_buckets["high"]
    medium_issues = severity_buckets["medium"]
    low_issues = severity_buckets["low"]

    # 为每个 issue 派生稳定的 issueId（findingId 优先，否则用序号）
    # 注意：不修改原 findings dict，避免污染 companion_json 内嵌入 HTML 的数据。
    issue_id_map = {}
    for idx, issue in enumerate(all_issues):
        issue_id_map[id(issue)] = issue.get("issueId") or issue.get("findingId") or idx

    def _iid(issue):
        return issue_id_map.get(id(issue))

    critical_html = "\n".join(_format_issue_html(i, _iid(i)) for i in critical_issues) or "<p class=\"empty-state\">暂无严重风险。</p>"
    high_html = "\n".join(_format_issue_html(i, _iid(i)) for i in high_issues) or "<p class=\"empty-state\">暂无高危风险。</p>"
    medium_html = "\n".join(_format_issue_html(i, _iid(i)) for i in medium_issues) or "<p class=\"empty-state\">暂无中危风险。</p>"
    low_html = "\n".join(_format_issue_html(i, _iid(i)) for i in low_issues) or "<p class=\"empty-state\">暂无低危风险。</p>"

    risk_type_stats = {}
    for issue in all_issues:
        risk_type = issue.get("riskType") or "未知风险"
        entry = risk_type_stats.setdefault(risk_type, {"count": 0, "max_level": "low"})
        entry["count"] += 1
        level = (issue.get("severity") or "").lower()
        if level in ("critical", "严重"):
            entry["max_level"] = "critical"
        elif level in ("high", "高") and entry["max_level"] not in ("critical",):
            entry["max_level"] = "high"
        elif level in ("medium", "中") and entry["max_level"] == "low":
            entry["max_level"] = "medium"

    risk_type_rows = ""
    _severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    for risk_type, stats in sorted(risk_type_stats.items(), key=lambda x: (_severity_order.get(x[1]["max_level"], 9), -x[1]["count"])):
        # 添加中文风险类型名称
        risk_type_cn = _risk_type_chinese(risk_type)
        risk_type_display = f"{risk_type_cn} ({risk_type})" if risk_type_cn != risk_type else risk_type
        risk_type_rows += f"""
            <tr>
                <td>{escape(str(risk_type_display))}</td>
                <td>{stats["count"]}</td>
                <td><span class="severity-pill severity-{stats["max_level"]}">{_risk_label(stats["max_level"])}</span></td>
            </tr>
        """
    if not risk_type_rows:
        risk_type_rows = "<tr><td colspan=\"3\" class=\"empty-state\">暂无风险类型统计</td></tr>"

    all_issues_rows = ""
    for idx, issue in enumerate(all_issues):
        issue_id = issue_id_map.get(id(issue), idx)
        risk_no = escape(str(issue.get("findingId") or issue_id))
        file_name = escape(str(issue.get("fileName", ""))) or "未知文件"
        file_path = escape(str(issue.get("filePath", "")))
        risk_type = str(issue.get("riskType", "")) or "未知风险"
        risk_type_cn = _risk_type_chinese(risk_type)
        severity = escape(str(issue.get("severity", ""))).lower() or "low"
        line_number = issue.get("lineNumber") or "无"
        description = escape(str(issue.get("description", ""))) or "无"
        risk_confidence = escape(_confidence_chinese(issue.get("confidence", "")))
        is_zero_day = issue.get("isZeroDay", False)
        zero_day_td = '<span class="zero-day-tag">0-day线索</span>' if is_zero_day else ''

        # 判断置信度等级（用于筛选）
        confidence_level = "high" if _is_high_confidence(issue.get("confidence")) else "all"

        # issue_id 可能是字符串（如 "F-001"）或整数；直接插值进 onclick 会被 JS
        # 当成表达式解析（F-001 → F 减 001 → NaN），导致弹窗找不到对应 article。
        # 用 json.dumps 生成合法 JS 字符串字面量，再 HTML 转义以安全嵌入属性。
        issue_id_js = escape(json.dumps(str(issue_id), ensure_ascii=False))

        all_issues_rows += f"""
            <tr class="issue-row" data-issue-id="{escape(str(issue_id))}" data-confidence="{confidence_level}" data-severity="{severity}" onclick="openIssueModal({issue_id_js})">
                <td><span class="mono">{risk_no}</span></td>
                <td><span class="mono">{file_path or file_name}</span></td>
                <td title="{escape(risk_type)}">{escape(risk_type_cn)}{zero_day_td}</td>
                <td><span class="severity-pill severity-{severity}">{_risk_label(severity)}</span></td>
                <td><span class="mono">{line_number}</span></td>
                <td>{risk_confidence}</td>
                <td>{description}</td>
            </tr>
        """
    if not all_issues_rows:
        all_issues_rows = "<tr><td colspan=\"7\" class=\"empty-state\">暂无风险详情</td></tr>"

    # 内嵌精简 JSON：用户复制 HTML 后仍可解析；同时避免 </script> 闭合突破。
    # type="application/json" 不会被浏览器执行，仅在需要时用 JS 读取。
    _embedded_payload = json.dumps(companion_json, ensure_ascii=False)
    _embedded_payload = _embedded_payload.replace("</", "<\\/")
    embedded_json_script = (
        f'<script id="security-scan-report-data" type="application/json">'
        f'{_embedded_payload}'
        f'</script>'
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码安全审查报告 - {audit_batch_id}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600;700&family=Spectral:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

        :root {{
            --paper: #f7f2e8;
            --paper-2: #fcfaf5;
            --ink: #1b1a17;
            --muted: #6e665c;
            --border: #e1d7c6;
            --accent: #1f3a5f;
            --accent-soft: rgba(31, 58, 95, 0.16);
            --high: #b23a2f;
            --critical: #7b1a1a;
            --medium: #d08a27;
            --low: #2f7e59;
            --shadow: 0 24px 60px rgba(17, 14, 10, 0.18);
            --mono: "JetBrains Mono", "Fira Code", monospace;
            --display: "Chakra Petch", "Trebuchet MS", sans-serif;
            --body: "Spectral", "Noto Serif SC", "Songti SC", serif;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family: var(--body);
            color: var(--ink);
            background-color: #fff;
            padding: 32px;
            line-height: 1.6;
        }}

        .report {{
            max-width: 1280px;
            margin: 0 auto;
            background: var(--paper-2);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 36px;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }}

        .report[data-risk="critical"] {{
            --accent: var(--critical);
            --accent-soft: rgba(123, 26, 26, 0.14);
        }}

        .report[data-risk="high"] {{
            --accent: var(--high);
            --accent-soft: rgba(178, 58, 47, 0.14);
        }}

        .report[data-risk="medium"] {{
            --accent: var(--medium);
            --accent-soft: rgba(208, 138, 39, 0.16);
        }}

        .report[data-risk="low"] {{
            --accent: var(--low);
            --accent-soft: rgba(47, 126, 89, 0.16);
        }}

        .report[data-risk="clean"] {{
            --accent: var(--low);
            --accent-soft: rgba(47, 126, 89, 0.16);
        }}

        .report[data-risk="failed"] {{
            --accent: var(--high);
            --accent-soft: rgba(178, 58, 47, 0.18);
        }}

        .report-header {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 32px;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 24px;
            margin-bottom: 28px;
        }}

        .kicker {{
            font-family: var(--display);
            text-transform: uppercase;
            letter-spacing: 0.2em;
            font-size: 0.72rem;
            color: var(--muted);
            margin-bottom: 12px;
        }}

        h1 {{
            font-family: var(--display);
            font-size: 2.4rem;
            margin: 0 0 8px;
        }}

        .subtitle {{
            margin: 0 0 20px;
            color: var(--muted);
            font-size: 1rem;
        }}

        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px 20px;
            font-size: 0.9rem;
        }}

        .meta-item {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .meta-label {{
            color: var(--muted);
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-family: var(--display);
        }}

        .meta-value {{
            font-weight: 600;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}

        .metric {{
            background: #fff;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 8px 18px rgba(24, 19, 13, 0.08);
        }}

        .metric-value {{
            font-family: var(--display);
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 6px;
        }}

        .metric-label {{
            color: var(--muted);
            font-size: 0.85rem;
        }}

        .metric.high .metric-value {{ color: var(--high); }}
        .metric.critical .metric-value {{ color: var(--critical); }}
        .metric.medium .metric-value {{ color: var(--medium); }}
        .metric.low .metric-value {{ color: var(--low); }}

        .metric.clickable {{
            cursor: pointer;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}

        .metric.clickable:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(24, 19, 13, 0.15);
        }}

        .section-title {{
            font-family: var(--display);
            font-size: 1.5rem;
            margin: 0 0 14px;
            border-left: 4px solid var(--accent);
            padding-left: 12px;
        }}

        .section-title.section-title-lg {{
            font-size: 1.9rem;
            margin-bottom: 18px;
        }}

        .section-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 28px;
        }}

        .card {{
            background: #fff;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 18px;
            box-shadow: 0 10px 24px rgba(24, 19, 13, 0.08);
        }}

        section.card + section.card {{
            margin-top: 28px;
        }}

        .product-shape-card {{
            margin-bottom: 28px;
        }}

        .card-header {{
            font-family: var(--display);
            font-size: 1.1rem;
            margin-bottom: 12px;
            color: var(--ink);
        }}

        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}

        .data-table th,
        .data-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            text-align: left;
            vertical-align: top;
        }}

        .data-table th {{
            font-family: var(--display);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
        }}

        .data-table th.sortable {{
            cursor: pointer;
            user-select: none;
            position: relative;
            padding-right: 24px;
            transition: color 0.2s ease, background-color 0.2s ease;
        }}

        .data-table th.sortable:hover {{
            color: var(--ink);
            background-color: var(--accent-soft);
        }}

        .data-table th.sortable::after {{
            content: '⇅';
            position: absolute;
            right: 8px;
            opacity: 0.4;
            font-size: 0.7rem;
        }}

        .data-table th.sortable.asc::after {{
            content: '↑';
            opacity: 1;
            color: var(--accent);
        }}

        .data-table th.sortable.desc::after {{
            content: '↓';
            opacity: 1;
            color: var(--accent);
        }}

        .data-table tbody tr:nth-child(even) {{
            background: rgba(247, 242, 232, 0.6);
        }}

        .data-table tbody tr.issue-row {{
            cursor: pointer;
            transition: background-color 0.2s ease;
        }}

        .data-table tbody tr.issue-row:hover {{
            background: var(--accent-soft);
        }}

        .issue-card.highlight {{
            animation: highlight-pulse 2s ease-out;
        }}

        @keyframes highlight-pulse {{
            0% {{
                box-shadow: 0 0 0 4px var(--accent);
            }}
            100% {{
                box-shadow: 0 8px 20px rgba(24, 19, 13, 0.08);
            }}
        }}

        /* Modal */
        .modal-overlay {{
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.45);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            padding: 24px;
            backdrop-filter: blur(4px);
        }}

        .modal-overlay.active {{
            display: flex;
        }}

        .modal-box {{
            background: var(--paper-2);
            border-radius: 18px;
            max-width: 780px;
            width: 100%;
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: 0 24px 64px rgba(24, 19, 13, 0.25);
            position: relative;
            animation: modal-in 0.25s ease-out;
        }}

        @keyframes modal-in {{
            from {{ opacity: 0; transform: translateY(16px) scale(0.97); }}
            to   {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}

        .modal-close {{
            position: sticky;
            top: 0;
            display: flex;
            justify-content: flex-end;
            padding: 12px 16px 0;
            z-index: 1;
        }}

        .modal-close-btn {{
            width: 36px;
            height: 36px;
            border: none;
            border-radius: 50%;
            background: var(--border);
            color: var(--ink);
            font-size: 1.2rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }}

        .modal-close-btn:hover {{
            background: var(--muted);
            color: #fff;
        }}

        .modal-body {{
            padding: 4px 24px 24px;
        }}

        .modal-body .issue-card {{
            margin-bottom: 0;
            box-shadow: none;
        }}

        .mono {{
            font-family: var(--mono);
            font-size: 0.82rem;
        }}

        .empty-state {{
            color: var(--muted);
            font-style: italic;
        }}

        .issues-block {{
            margin: 40px 0 32px;
        }}

        .group-title {{
            font-family: var(--display);
            font-size: 1.1rem;
            margin: 20px 0 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .issue-card {{
            border: 1px solid var(--border);
            border-left: 6px solid var(--accent);
            border-radius: 14px;
            padding: 16px 18px;
            background: #fff;
            margin-bottom: 16px;
            box-shadow: 0 8px 20px rgba(24, 19, 13, 0.08);
        }}

        .issue-card.issue-critical {{
            border-left-color: var(--critical);
            background: #fff2f0;
        }}

        .issue-card.issue-high {{
            border-left-color: var(--high);
            background: #fff6f4;
        }}

        .issue-card.issue-medium {{
            border-left-color: var(--medium);
            background: #fff8ea;
        }}

        .issue-card.issue-low {{
            border-left-color: var(--low);
            background: #f4fbf7;
        }}

        .issue-head {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
            margin-bottom: 14px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }}

        .issue-type {{
            font-family: var(--display);
            font-size: 1.15rem;
            font-weight: 700;
        }}

        .issue-id {{
            display: inline-block;
            margin-right: 8px;
            padding: 1px 8px;
            border: 1px solid var(--border);
            border-radius: 4px;
            background: var(--paper);
            color: var(--accent);
            font-size: 0.82rem;
            font-weight: 600;
            vertical-align: middle;
        }}

        .issue-info {{
            display: flex;
            flex-direction: column;
            gap: 14px;
            margin-bottom: 14px;
            font-size: 0.9rem;
        }}

        .issue-info-item {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .issue-info-label {{
            font-family: var(--display);
            color: #1a1a1a;
            font-weight: 600;
            font-size: 0.9rem;
        }}

        .issue-section {{
            margin-bottom: 14px;
        }}

        .issue-section:last-child {{
            margin-bottom: 0;
        }}

        .issue-section-title {{
            font-family: var(--display);
            font-size: 0.9rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 4px;
        }}

        .issue-desc {{
            margin: 0;
            line-height: 1.7;
        }}

        .issue-desc-section {{
            margin: 0 0 8px 0;
            line-height: 1.7;
        }}

        .issue-desc-section:last-child {{
            margin-bottom: 0;
        }}

        .issue-desc-section strong {{
            color: var(--ink);
            margin-right: 4px;
        }}

        .issue-code {{
            margin: 0;
            padding: 14px;
            background: #1f1c18;
            color: #f5efe6;
            border-radius: 10px;
            font-family: var(--mono);
            font-size: 0.82rem;
            overflow-x: auto;
            border: 1px solid var(--border);
        }}

        .issue-code-fixed {{
            background: #1a2e1a;
            border-color: var(--low);
        }}

        .issue-recommendation {{
            background: #e8f5e9;
            border-left: 4px solid var(--low);
            padding: 12px 14px;
            border-radius: 10px;
        }}

        .issue-recommendation p {{
            margin: 0 0 8px;
        }}

        .issue-recommendation p:last-child {{
            margin-bottom: 0;
        }}

        .severity-pill {{
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-family: var(--display);
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #fff;
            background: var(--accent);
        }}

        .severity-critical {{ background: var(--critical); }}
        .severity-high {{ background: var(--high); }}
        .severity-medium {{ background: var(--medium); }}
        .severity-low {{ background: var(--low); }}

        .zero-day-tag {{
            display: inline-flex;
            align-items: center;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.65rem;
            font-family: var(--display);
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #fff;
            background: linear-gradient(135deg, #6b21a8, #9333ea);
            margin-left: 8px;
            vertical-align: middle;
        }}

        /* 单漏洞调用链流程图 */
        .attack-call-chain {{
            display: flex;
            flex-direction: column;
            padding: 10px 12px;
            background: #f9f7f3;
            border: 1px solid var(--border);
            border-radius: 10px;
        }}

        .chain-node {{
            display: flex;
            align-items: flex-start;
            gap: 8px;
            padding: 6px 10px;
            border-radius: 6px;
            font-family: var(--mono);
            font-size: 0.82rem;
            line-height: 1.5;
        }}

        .chain-node-source {{
            background: rgba(31, 58, 95, 0.10);
            border-left: 3px solid var(--accent);
        }}

        .chain-node-prop {{
            background: rgba(0, 0, 0, 0.04);
            border-left: 3px solid var(--border);
            margin-left: 16px;
        }}

        .chain-node-sink {{
            background: rgba(178, 58, 47, 0.10);
            border-left: 3px solid var(--high);
        }}

        .chain-node-label {{
            flex-shrink: 0;
            font-family: var(--display);
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            padding: 1px 6px;
            border-radius: 4px;
            margin-top: 2px;
            white-space: nowrap;
        }}

        .chain-node-source .chain-node-label {{
            background: var(--accent);
            color: #fff;
        }}

        .chain-node-prop .chain-node-label {{
            background: var(--muted);
            color: #fff;
        }}

        .chain-node-sink .chain-node-label {{
            background: var(--high);
            color: #fff;
        }}

        .chain-node-text {{
            word-break: break-all;
            color: var(--ink);
        }}

        .chain-arrow {{
            text-align: left;
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1;
            padding: 3px 0 3px 22px;
            user-select: none;
        }}

        .chain-trace-badge {{
            display: inline-flex;
            align-items: center;
            padding: 1px 8px;
            border-radius: 999px;
            font-size: 0.7rem;
            font-family: var(--display);
            background: var(--accent-soft);
            color: var(--accent);
            margin-left: 6px;
            vertical-align: middle;
            font-weight: 600;
        }}

        .poc-content {{
            padding: 8px 0;
        }}
        .poc-badge {{
            display: inline-flex;
            align-items: center;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            font-family: var(--display);
            margin-bottom: 6px;
        }}
        .poc-badge.poc-yes {{
            background: rgba(220, 38, 38, 0.12);
            color: #dc2626;
        }}
        .poc-badge.poc-conditional {{
            background: rgba(217, 119, 6, 0.12);
            color: #d97706;
        }}
        .poc-badge.poc-no {{
            background: rgba(100, 116, 139, 0.15);
            color: #475569;
        }}
        .poc-meta {{
            font-size: 0.82rem;
            color: var(--muted);
            margin: 4px 0 2px;
        }}
        .poc-no-reason {{
            color: #475569;
            font-style: italic;
        }}
        .poc-pre {{
            margin: 2px 0 6px 18px;
            font-size: 0.82rem;
            color: var(--muted);
        }}

        .advice {{
            background: var(--accent-soft);
            border-left: 4px solid var(--accent);
            padding: 12px 14px;
            border-radius: 10px;
            margin-bottom: 12px;
        }}

        .advice-title {{
            font-family: var(--display);
            font-size: 0.85rem;
            margin-bottom: 6px;
        }}

        .code-stack {{
            display: grid;
            gap: 12px;
        }}

        .code-block {{
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 0;
            overflow: hidden;
            background: #1f1c18;
        }}

        .code-block summary {{
            cursor: pointer;
            padding: 10px 12px;
            font-family: var(--display);
            color: #f5efe6;
            background: rgba(255, 255, 255, 0.08);
        }}

        .code-block pre {{
            margin: 0;
            padding: 14px;
            color: #f5efe6;
            font-family: var(--mono);
            font-size: 0.82rem;
            overflow-x: auto;
        }}

        .inline-details summary {{
            cursor: pointer;
            font-family: var(--display);
            font-size: 0.8rem;
        }}

        .inline-details pre {{
            margin-top: 8px;
            background: #1f1c18;
            color: #f5efe6;
            padding: 12px;
            border-radius: 8px;
            font-family: var(--mono);
            font-size: 0.78rem;
        }}

        .filter-tags {{
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}

        .filter-tag {{
            display: inline-flex;
            align-items: center;
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: #fff;
            color: var(--ink);
            font-family: var(--display);
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
        }}

        .filter-tag:hover {{
            background: var(--accent-soft);
            color: var(--accent);
            border-color: var(--accent);
        }}

        .filter-tag.active {{
            background: var(--accent);
            color: #fff;
            border-color: var(--accent);
        }}

        .filter-tag-label {{
            display: inline-block;
        }}

        .table-scroll {{
            overflow-x: auto;
        }}

        .verification-guide-section {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-top: 8px;
        }}

        .verification-guide-content {{
            margin-top: 8px;
        }}

        .verification-steps-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 12px;
        }}

        .verification-step {{
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 14px;
            transition: border-color 0.2s ease;
        }}

        .verification-step:hover {{
            border-color: #94a3b8;
        }}

        .verification-step-header {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 4px;
        }}

        .verification-step-number {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 56px;
            height: 22px;
            background: linear-gradient(135deg, #0ea5e9, #0284c7);
            color: #fff;
            font-size: 0.72rem;
            font-weight: 700;
            border-radius: 11px;
            letter-spacing: 0.04em;
            flex-shrink: 0;
            margin-top: 1px;
        }}

        .verification-step-desc {{
            color: #334155;
            font-size: 0.88rem;
            line-height: 1.5;
            flex: 1;
        }}

        .verification-command {{
            background: #1e293b;
            color: #22d3ee;
            padding: 10px 14px;
            border-radius: 6px;
            font-family: 'SF Mono', Monaco, 'Courier New', monospace;
            font-size: 12.5px;
            overflow-x: auto;
            margin: 8px 0 0 0;
            white-space: pre-wrap;
            word-break: break-all;
            line-height: 1.6;
        }}

        .verification-note {{
            font-size: 0.82rem;
            color: #64748b;
            margin-top: 12px;
            padding: 8px 12px;
            border-left: 3px solid #0ea5e9;
            background: #f0f9ff;
            border-radius: 0 4px 4px 0;
        }}

        .report-footer {{
            margin-top: 32px;
            padding-top: 18px;
            border-top: 1px solid var(--border);
            text-align: center;
            font-size: 0.9rem;
            color: var(--muted);
        }}

        @media (max-width: 980px) {{
            body {{ padding: 20px; }}
            .report {{ padding: 24px; }}
            .report-header {{
                grid-template-columns: 1fr;
            }}
        }}

        @media (max-width: 720px) {{
            h1 {{ font-size: 2rem; }}
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        @media print {{
            body {{
                background: #fff;
                padding: 0;
            }}
            .report {{
                box-shadow: none;
                border: none;
                padding: 0;
            }}
            .issue-card {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="report" data-risk="{status_class}">
        <header class="report-header">
            <div class="header-main">
                <h1>代码安全审查报告</h1>
                <p class="subtitle">{project_name} · {scope}</p>
                <div class="meta-grid">
                    <div class="meta-item">
                        <span class="meta-label">生成时间</span>
                        <span class="meta-value">{generated_at}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">项目名称</span>
                        <span class="meta-value">{project_name}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">审计批次</span>
                        <span class="meta-value">{audit_batch_id}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">代码分支</span>
                        <span class="meta-value">{code_branch}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">扫描模式</span>
                        <span class="meta-value">{scan_mode}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">项目类型</span>
                        <span class="meta-value">{project_type}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">生成状态</span>
                        <span class="meta-value">{"成功" if success else "失败"}</span>
                    </div>
                </div>
            </div>
        </header>

        {early_exit_banner}

        {product_shape_evidence_html}

        <section class="metrics-grid">
            <div class="metric clickable" onclick="filterRiskTable('high')">
                <div class="metric-value">{high_confidence_count}</div>
                <div class="metric-label">高置信度风险</div>
            </div>
            <div class="metric clickable" onclick="filterRiskTable('all')">
                <div class="metric-value">{total_issues}</div>
                <div class="metric-label">风险总数</div>
            </div>
            <div class="metric critical clickable" onclick="filterRiskTableByLevel('critical')">
                <div class="metric-value">{critical_count}</div>
                <div class="metric-label">严重风险</div>
            </div>
            <div class="metric high clickable" onclick="filterRiskTableByLevel('high')">
                <div class="metric-value">{high_count}</div>
                <div class="metric-label">高危风险</div>
            </div>
            <div class="metric medium clickable" onclick="filterRiskTableByLevel('medium')">
                <div class="metric-value">{medium_count}</div>
                <div class="metric-label">中等风险</div>
            </div>
            <div class="metric low clickable" onclick="filterRiskTableByLevel('low')">
                <div class="metric-value">{low_count}</div>
                <div class="metric-label">低危风险</div>
            </div>
        </section>

        <section class="section-grid">
            <div class="card">
                <div class="card-header">风险类型分布</div>
                <div class="table-scroll">
                    <table class="data-table" id="risk-type-table">
                        <thead>
                            <tr>
                                <th class="sortable" data-sort="string" onclick="sortTable(this, 0)">风险类型</th>
                                <th class="sortable" data-sort="number" onclick="sortTable(this, 1)">数量</th>
                                <th class="sortable" data-sort="severity" onclick="sortTable(this, 2)">严重程度</th>
                            </tr>
                        </thead>
                        <tbody>
                            {risk_type_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <section class="card" id="risk-list-section">
            <div class="card-header">风险列表</div>
            <div class="filter-tags">
                <button class="filter-tag active" data-filter="high" onclick="filterRiskTable('high')">
                    <span class="filter-tag-label">高置信度</span>
                </button>
                <button class="filter-tag" data-filter="all" onclick="filterRiskTable('all')">
                    <span class="filter-tag-label">全部</span>
                </button>
                <button class="filter-tag" data-filter="level-critical" onclick="filterRiskTableByLevel('critical')">
                    <span class="filter-tag-label">严重</span>
                </button>
                <button class="filter-tag" data-filter="level-high" onclick="filterRiskTableByLevel('high')">
                    <span class="filter-tag-label">高危</span>
                </button>
                <button class="filter-tag" data-filter="level-medium" onclick="filterRiskTableByLevel('medium')">
                    <span class="filter-tag-label">中危</span>
                </button>
                <button class="filter-tag" data-filter="level-low" onclick="filterRiskTableByLevel('low')">
                    <span class="filter-tag-label">低危</span>
                </button>
            </div>
            <div class="table-scroll">
                <table class="data-table" id="risk-list-table">
                    <thead>
                        <tr>
                            <th class="sortable" data-sort="string" onclick="sortTable(this, 0)">编号</th>
                            <th class="sortable" data-sort="string" onclick="sortTable(this, 1)">文件</th>
                            <th class="sortable" data-sort="string" onclick="sortTable(this, 2)">风险类型</th>
                            <th class="sortable" data-sort="severity" onclick="sortTable(this, 3)">级别</th>
                            <th class="sortable" data-sort="number" onclick="sortTable(this, 4)">行号</th>
                            <th class="sortable" data-sort="number" onclick="sortTable(this, 5)">置信度</th>
                            <th class="sortable" data-sort="string" onclick="sortTable(this, 6)">描述</th>
                        </tr>
                    </thead>
                    <tbody>
                        {all_issues_rows}
                    </tbody>
                </table>
            </div>
        </section>

        <section class="issues-block">
            <h2 class="section-title section-title-lg">详细风险列表</h2>
            <h3 class="group-title">🔴 严重风险</h3>
            {critical_html}
            <h3 class="group-title">🟠 高危风险</h3>
            {high_html}
            <h3 class="group-title">🟡 中危风险</h3>
            {medium_html}
            <h3 class="group-title">🟢 低危风险</h3>
            {low_html}
        </section>

        <div class="modal-overlay" id="issueModal" onclick="closeIssueModal()">
            <div class="modal-box" onclick="event.stopPropagation()">
                <div class="modal-close"><button class="modal-close-btn" onclick="closeIssueModal()">&times;</button></div>
                <div class="modal-body" id="issueModalBody"></div>
            </div>
        </div>

        <footer class="report-footer">
            <div>内容由 AI 生成，仅供参考</div>
        </footer>
    </div>
    <script>
        function openIssueModal(issueId) {{
            var source = document.getElementById('issue-' + issueId);
            if (!source) return;
            var body = document.getElementById('issueModalBody');
            while (body.firstChild) body.removeChild(body.firstChild);
            var clone = source.cloneNode(true);
            clone.removeAttribute('id');
            body.appendChild(clone);
            document.getElementById('issueModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function closeIssueModal() {{
            document.getElementById('issueModal').classList.remove('active');
            document.body.style.overflow = '';
        }}

        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') closeIssueModal();
        }});

        function sortTable(header, columnIndex) {{
            const table = header.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const sortType = header.dataset.sort || 'string';
            
            // Severity order mapping (critical > high > medium > low)
            const severityOrder = {{
                '严重': 4, 'critical': 4, 'CRITICAL': 4,
                '高': 3, 'high': 3, 'HIGH': 3,
                '中': 2, 'medium': 2, 'MEDIUM': 2,
                '低': 1, 'low': 1, 'LOW': 1
            }};
            
            // Check if already sorted and determine direction
            const isAsc = header.classList.contains('asc');
            const direction = isAsc ? -1 : 1;
            
            // Remove sort classes from all headers in this table
            table.querySelectorAll('th.sortable').forEach(th => {{
                th.classList.remove('asc', 'desc');
            }});
            
            // Add appropriate class to current header
            header.classList.add(isAsc ? 'desc' : 'asc');
            
            // Sort rows
            rows.sort((a, b) => {{
                const aCell = a.cells[columnIndex];
                const bCell = b.cells[columnIndex];
                
                if (!aCell || !bCell) return 0;
                
                let aVal = aCell.textContent.trim();
                let bVal = bCell.textContent.trim();
                
                if (sortType === 'number') {{
                    aVal = parseFloat(aVal) || 0;
                    bVal = parseFloat(bVal) || 0;
                    return (aVal - bVal) * direction;
                }} else if (sortType === 'severity') {{
                    aVal = severityOrder[aVal] || 0;
                    bVal = severityOrder[bVal] || 0;
                    return (aVal - bVal) * direction;
                }} else {{
                    return aVal.localeCompare(bVal, 'zh-CN') * direction;
                }}
            }});
            
            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
        }}

        function filterRiskTable(filterType, scroll) {{
            const table = document.getElementById('risk-list-table');
            const rows = table.querySelectorAll('tbody tr');
            const filterButtons = document.querySelectorAll('.filter-tag');

            // 更新按钮状态（同时清除 level 过滤的 active 状态）
            filterButtons.forEach(btn => {{
                btn.classList.remove('active');
                if (btn.dataset.filter === filterType) {{
                    btn.classList.add('active');
                }}
            }});

            // 过滤行
            rows.forEach(row => {{
                const confidence = row.dataset.confidence;
                if (filterType === 'high') {{
                    row.style.display = confidence === 'high' ? '' : 'none';
                }} else {{
                    row.style.display = '';
                }}
            }});

            // 滚动到风险列表
            if (scroll !== false) {{
                document.getElementById('risk-list-section').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}

        function filterRiskTableByLevel(level) {{
            const table = document.getElementById('risk-list-table');
            const rows = table.querySelectorAll('tbody tr');
            const filterButtons = document.querySelectorAll('.filter-tag');

            // 更新按钮状态（同时清除 confidence 过滤的 active 状态）
            filterButtons.forEach(btn => {{
                btn.classList.remove('active');
                if (btn.dataset.filter === 'level-' + level) {{
                    btn.classList.add('active');
                }}
            }});

            // 按风险级别过滤
            rows.forEach(row => {{
                const severity = row.dataset.severity;
                row.style.display = severity === level ? '' : 'none';
            }});

            // 滚动到风险列表
            document.getElementById('risk-list-section').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
        
        // 页面加载时初始化过滤（默认显示高置信度）
        document.addEventListener('DOMContentLoaded', function() {{
            filterRiskTable('high', false);
        }});
    </script>
    {embedded_json_script}
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(
        description="根据代码审计结果生成 JSON 或 HTML 报告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
输入支持：
  - 审计目录：包含 summary.json + finding-*.json 的批次目录
  - 单个 JSON：单个 finding 文件、summary 文件或 remediation/verifier 结果
  - audit-batch-id：自动在当前工作目录 /tmp 下查找 .codebuddy/security-scan/runs/<batch>

输出行为：
  - JSON：默认输出到 stdout；传 --output 时写入文件
  - HTML：传 --format html 或输出文件以 .html 结尾时生成 HTML，并同步输出同名 JSON 报告
  - HTML 未传 --output 时：优先写入审计目录 `{DEFAULT_HTML_REPORT_NAME}` 与 `{DEFAULT_JSON_REPORT_NAME}`

示例用法:
  # 从审计目录输出 JSON 到 stdout
  %(prog)s --input .codebuddy/security-scan/runs/audit-20250103120000

  # 使用审计批次 ID 自动查找目录
  %(prog)s --audit-batch-id audit-20250103120000

  # 输出 JSON 到文件
  %(prog)s --input .codebuddy/security-scan/runs/audit-20250103120000 \\
    --output .codebuddy/security-scan/runs/audit-20250103120000/report.json

  # 输出 HTML 到固定报告文件
  %(prog)s --input .codebuddy/security-scan/runs/audit-20250103120000 \\
    --format html \\
    --output .codebuddy/security-scan/runs/audit-20250103120000/{DEFAULT_HTML_REPORT_NAME}
        """
    )

    parser.add_argument(
        '--input',
        help='输入路径（审计目录或单个 JSON 文件；与 --audit-batch-id 二选一即可）',
    )
    parser.add_argument('--audit-batch-id', help='审计批次 ID（用于自动定位目录）')
    parser.add_argument(
        '--output',
        help='输出文件路径（JSON 默认 stdout；HTML 默认写入审计目录中的 security-scan-report.html，并同步写出同名 .json）',
    )
    parser.add_argument(
        '--format', choices=['json', 'html'], default='json',
        help='报告输出格式（默认: json；当 --output 以 .html 结尾时会自动切换为 html）',
    )
    parser.add_argument('--quiet', action='store_true', help='静默模式（不输出日志）')
    parser.add_argument(
        '--pretty', action='store_true', default=True,
        help='兼容参数：当前 JSON 默认已格式化输出，可忽略此选项',
    )
    parser.add_argument('--compact', action='store_true',
                       help='紧凑 JSON 输出（单行）')
    parser.add_argument('--scan-mode', default=None,
                       help='扫描模式（deep/light）；未指定时从 batch-id 自动推断')
    parser.add_argument('--scan-files', type=int, default=None,
                       help='扫描的源文件总数（用于报告展示）')
    parser.add_argument(
        '--enforce-language',
        choices=['zh', 'none'], default='zh',
        help='报告语言校验：zh=findings 文本字段须以简体中文为主（默认）；'
             'none=跳过校验'
    )
    parser.add_argument(
        '--language-min-ratio', type=float, default=0.30,
        help='中文字符占比下限，低于该值视为违规（默认 0.30）'
    )

    args = parser.parse_args()

    if args.quiet:
        Colors.HEADER = Colors.BLUE = Colors.CYAN = Colors.GREEN = ''
        Colors.WARNING = Colors.FAIL = Colors.ENDC = Colors.BOLD = ''

    if not args.input and not args.audit_batch_id:
        print_colored("[FAIL] 请指定 --input 或 --audit-batch-id", Colors.FAIL)
        sys.exit(1)

    try:
        # 加载审计结果
        resolved_input = resolve_input_path(args.input, args.audit_batch_id)
        input_for_load = str(resolved_input) if resolved_input else args.input
        results, summary = load_audit_results(input_for_load, args.audit_batch_id)
        ensure_summary_file(resolved_input, summary)

        if not results:
            # 兜底：如果 summary 已加载（早退场景），构造空结果集继续生成报告
            if summary:
                results = [{
                    'metadata': {'fileName': 'empty', 'filePath': ''},
                    'summary': {
                        'totalIssues': 0, 'criticalRisk': 0,
                        'highRisk': 0, 'mediumRisk': 0, 'lowRisk': 0,
                    },
                    'findings': [],
                }]
                if not args.quiet:
                    print_colored("[INFO] 无 findings，生成 clean 报告", Colors.BLUE)
            else:
                raise ValueError("未找到审计结果")

        if not args.quiet:
            print_colored(f"[OK] 加载了 {len(results)} 个审计结果", Colors.GREEN)

        # 语言校验：findings 文本字段必须以简体中文为主
        if args.enforce_language == 'zh':
            violations_path = None
            if resolved_input:
                base_dir = resolved_input if resolved_input.is_dir() else resolved_input.parent
                violations_path = base_dir / "language-violations.json"
            violations = enforce_language_zh(
                results,
                min_ratio=args.language_min_ratio,
                quiet=args.quiet,
                violations_out=violations_path,
            )
            if violations:
                if not args.quiet and violations_path:
                    print_colored(
                        f"[FAIL] 违规明细已写入：{violations_path}",
                        Colors.FAIL)
                # 退出码 2 = 语言校验失败，供工作流识别并触发自动改写重跑
                sys.exit(2)

        # 生成报告
        base_path = resolve_git_base(args.input)
        code_branch = get_git_branch(base_path) or "未知"
        project_name = get_git_project_name(base_path) or "未知项目"
        scan_mode_value = _extract_scan_mode(
            getattr(args, 'scan_mode', None),
            summary.get('scanMode', ''),
            summary.get('auditBatchId', summary.get('batchId', ''))
        )
        if args.scan_files is not None:
            summary['scanFiles'] = args.scan_files
        report = generate_json_report(results, summary, code_branch=code_branch,
                                       project_name=project_name, scan_mode=scan_mode_value)

        if resolved_input:
            align_report_findings_with_merged_findings(report, resolved_input)

        output_format = args.format
        if args.output and args.output.lower().endswith(".html"):
            output_format = "html"

        if output_format == "html":
            # 标准流程：先生成 companion JSON（HTML 渲染的唯一数据源），再渲染 HTML。
            companion_report = generate_companion_json_report(report)
            output_target = args.output or resolve_default_output_path(output_format, resolved_input, summary)
            output_path = ensure_output_parent(output_target)
            companion_output_path = ensure_output_parent(resolve_companion_json_output_path(output_path))

            # 先写 JSON：HTML 渲染失败时 JSON 仍然可用
            with open(companion_output_path, 'w', encoding='utf-8') as f:
                json.dump(companion_report, f, ensure_ascii=False, indent=2)

            html_output = generate_html_report(companion_report)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_output)

            if not args.quiet:
                print_colored(f"[OK] JSON 报告已保存: {companion_output_path}", Colors.GREEN)
                print_colored(f"[OK] HTML 报告已保存: {output_path}", Colors.GREEN)
        else:
            # 输出 JSON
            indent = None if args.compact else 2
            json_output = json.dumps(report, ensure_ascii=False, indent=indent)

            if args.output:
                output_path = ensure_output_parent(args.output)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                if not args.quiet:
                    print_colored(f"[OK] 报告已保存: {output_path}", Colors.GREEN)
            else:
                print(json_output)

    except Exception as e:
        error_report = {"success": False, "error": str(e)}
        print(json.dumps(error_report, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n[WARN] 用户中断操作", Colors.WARNING)
        sys.exit(130)
    except Exception as e:
        print_colored(f"\n[FAIL] 未预期的错误: {e}", Colors.FAIL)
        import traceback
        traceback.print_exc()
        sys.exit(1)
