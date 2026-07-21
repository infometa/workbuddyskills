#!/usr/bin/env python3
"""
审计报告与修复结果上报脚本
独立运行，直接从审计结果目录读取数据并上报

支持两种上报类型：
  --type audit  上报审计结果（默认）
  --type fix    上报修复结果（需先生成 fix-report.json）

上报通过 CodeBuddy 代理通道发送（环境变量 CODEBUDDY_SERVICE_PROXY_URL），
由网关注入认证信息。
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _common import (
    Colors, print_colored, BEIJING_TZ, LOCAL_TZ, TIME_FORMAT,
    _parse_datetime, format_beijing_time,
    get_git_branch, get_git_project_name,
    get_risk_level_normalized,
    BATCH_PREFIXES, get_scan_output_dirs,
    load_scan_session, is_output_fresh, session_started_at,
)


UPLOAD_TIMEOUT_SECONDS = 8
UPLOAD_MAX_RETRIES = 2
UPLOAD_RETRY_BACKOFF_SECONDS = 1.0

# 服务端约束：extra_info 序列化后 ≤ 64 KB
MAX_EXTRA_INFO_BYTES = 65536

# 客户端约束：risk_list / auto_fixed_list 合计序列化后 ≤ 512 KB
MAX_RISK_LIST_BYTES = 524288

# extra_info 中可能随数据规模膨胀的字段（按裁剪优先级从高到低）
_EXTRA_INFO_TRUNCATABLE_KEYS = ("fixed_risk_ids",)

# severity 裁剪优先级（值越小越优先保留）
_SEVERITY_PRIORITY = {"critical": 0, "high": 1, "medium": 2, "low": 3}


REPORT_ENDPOINT_PATH = "/api/v1/reports/upload"


def get_report_url():
    """获取上报 URL

    仅通过 CodeBuddy 代理通道上报，由环境变量 CODEBUDDY_SERVICE_PROXY_URL 提供。
    代理通道未注入时返回 None，上报流程将据此判定失败并给出清晰错误。
    """
    proxy_url = os.environ.get("CODEBUDDY_SERVICE_PROXY_URL")
    if not proxy_url:
        return None
    return proxy_url.rstrip("/") + REPORT_ENDPOINT_PATH


def load_audit_results(input_path, audit_batch_id=None):
    """从审计结果目录加载数据"""
    results = []
    summary = None

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
            results.append(data)
            if 'summary' in data:
                summary = {
                    'auditBatchId': data.get('metadata', {}).get('auditBatchId', audit_batch_id or 'unknown'),
                    'riskFiles': 1 if data['summary'].get('totalIssues', 0) > 0 else 0,
                    'totalIssues': data['summary'].get('totalIssues', 0),
                    'criticalRisk': data['summary'].get('criticalRisk', 0),
                    'highRisk': data['summary'].get('highRisk', 0),
                    'mediumRisk': data['summary'].get('mediumRisk', 0),
                    'lowRisk': data['summary'].get('lowRisk', 0),
                }

    elif input_path.is_dir():
        summary_file = input_path / "summary.json"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
            summary_id = summary.get('auditBatchId') if isinstance(summary, dict) else None
            if audit_batch_id and (not summary_id or summary_id == 'unknown'):
                summary['auditBatchId'] = audit_batch_id
            elif not summary_id or summary_id == 'unknown':
                summary['auditBatchId'] = input_path.name

        for file_path in sorted(input_path.glob("result-*.json")):
            with open(file_path, 'r', encoding='utf-8') as f:
                results.append(json.load(f))

        # 统一最终风险源：优先使用 merged-verified.json，缺失时才回退 merged-scan.json。
        # 如果 merged-verified.json 存在且 findings=[]，说明后置验证/过滤已清空风险，
        # 不允许再回退读取 merged-scan.json 把已移除的风险上报。
        if not results:
            for merged_name in ("merged-verified.json", "merged-scan.json"):
                merged_scan_file = input_path / merged_name
                if not merged_scan_file.exists():
                    continue
                with open(merged_scan_file, 'r', encoding='utf-8') as f:
                    merged_data = json.load(f)
                if 'findings' not in merged_data or not isinstance(merged_data['findings'], list):
                    continue
                # 将 findings 转换为 result-*.json 等价结构
                by_risk_type = {}
                for finding in merged_data['findings']:
                    rt = finding.get('riskType', 'unknown')
                    slug = rt.lower().replace(' ', '-').replace('_', '-')
                    by_risk_type.setdefault(slug, []).append(finding)

                for slug, group_findings in by_risk_type.items():
                    issues = []
                    for gf in group_findings:
                        issues.append({
                            'RiskLevel': get_risk_level_normalized(
                                gf.get('severity', 'medium')
                            ),
                            'FilePath': gf.get('filePath', ''),
                            'RiskType': gf.get('riskType', ''),
                            'LineNumber': gf.get('lineNumber', 0),
                            'RiskCode': gf.get('riskCode', ''),
                            'RiskDetail': gf.get('description', ''),
                            'Suggestions': gf.get('recommendation', ''),
                            'FixedCode': gf.get('fixedCode', ''),
                            'RiskConfidence': gf.get('confidence', 0),
                        })
                    results.append({
                        'summary': {
                            'totalIssues': len(group_findings),
                        },
                        'issues': issues,
                    })

                total = merged_data.get('totalFindings', len(merged_data['findings']))
                by_sev = merged_data.get('bySeverity', {})
                merged_summary = {
                    'auditBatchId': audit_batch_id or input_path.name or 'unknown',
                    'riskFiles': len(by_risk_type),
                    'totalIssues': total,
                    'criticalRisk': by_sev.get('critical', 0),
                    'highRisk': by_sev.get('high', 0),
                    'mediumRisk': by_sev.get('medium', 0),
                    'lowRisk': by_sev.get('low', 0),
                }
                if summary and isinstance(summary, dict):
                    # 合并产物是最终风险源；风险计数字段必须覆盖旧 summary 残留。
                    for k in ("riskFiles", "totalIssues", "criticalRisk", "highRisk", "mediumRisk", "lowRisk"):
                        summary[k] = merged_summary[k]
                    if not summary.get("auditBatchId") or summary.get("auditBatchId") == "unknown":
                        summary["auditBatchId"] = merged_summary["auditBatchId"]
                else:
                    summary = merged_summary
                break

        if not summary and results:
            total_issues = 0
            critical_risk = 0
            high_risk = 0
            medium_risk = 0
            low_risk = 0

            for r in results:
                s = r.get('summary', {})
                total_issues += s.get('totalIssues', 0)
                critical_risk += s.get('criticalRisk', 0)
                high_risk += s.get('highRisk', 0)
                medium_risk += s.get('mediumRisk', 0)
                low_risk += s.get('lowRisk', 0)

            summary = {
                'auditBatchId': audit_batch_id or input_path.name or 'unknown',
                'riskFiles': sum(1 for r in results if r.get('summary', {}).get('totalIssues', 0) > 0),
                'totalIssues': total_issues,
                'criticalRisk': critical_risk,
                'highRisk': high_risk,
                'mediumRisk': medium_risk,
                'lowRisk': low_risk,
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

    # 根据 files 列表动态计算 riskFiles（兼容旧数据中无此字段的情况）
    if summary and isinstance(summary, dict) and 'riskFiles' not in summary:
        files_list = summary.get('files', [])
        if files_list:
            summary['riskFiles'] = sum(1 for f in files_list if f.get('issues', 0) > 0)
        else:
            summary['riskFiles'] = len(results)

    return results, summary


def load_fix_report(batch_dir):
    """从批次目录加载修复报告

    Args:
        batch_dir: 批次目录路径 (Path)

    Returns:
        dict: 修复报告数据，如果文件不存在或解析失败返回 None
    """
    fix_report_path = batch_dir / "fix-report.json"
    if not fix_report_path.exists():
        return None
    try:
        with fix_report_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


def _load_gate_result(batch_dir):
    """读取门禁评估结果。

    Args:
        batch_dir: 批次目录路径 (Path)

    Returns:
        dict: gate-result.json 数据，不存在或解析失败返回 None
    """
    if not batch_dir:
        return None
    gate_path = batch_dir / "gate-result.json"
    if not gate_path.exists():
        return None
    try:
        with gate_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "gateStatus" in data:
            return data
    except Exception:
        pass
    return None


def _read_audit_timing(batch_dir):
    """读取审计耗时信息

    从批次目录中读取 .audit_start_time 和 .audit_end_time 文件，
    解析 ISO 8601 时间戳并计算审计耗时。

    Args:
        batch_dir: 批次目录路径 (Path)

    Returns:
        dict: 包含 audit_start_time, audit_end_time, audit_duration_seconds，
              缺失的字段不包含在返回值中。返回空 dict 表示无任何时间信息。
    """
    timing = {}
    start_path = batch_dir / ".audit_start_time"
    end_path = batch_dir / ".audit_end_time"

    start_dt = None
    end_dt = None

    if start_path.exists():
        try:
            raw = start_path.read_text(encoding="utf-8").strip()
            start_dt = _parse_datetime(raw)
            if start_dt:
                timing["audit_start_time"] = start_dt.isoformat()
        except Exception:
            pass

    if end_path.exists():
        try:
            raw = end_path.read_text(encoding="utf-8").strip()
            end_dt = _parse_datetime(raw)
            if end_dt:
                timing["audit_end_time"] = end_dt.isoformat()
        except Exception:
            pass

    if start_dt and end_dt:
        delta = (end_dt - start_dt).total_seconds()
        if delta >= 0:
            # 保留毫秒精度上报：服务端列为 DOUBLE（Float(precision=53)），
            # 设计意图就是保留亚秒精度。round 到 3 位避免浮点尾数噪声。
            timing["audit_duration_seconds"] = round(delta, 3)

    return timing


def _enforce_extra_info_limit(extra_info, max_bytes=MAX_EXTRA_INFO_BYTES):
    """确保 extra_info 序列化后不超过服务端限制（默认 64 KB）。

    超限时按既定优先级裁剪可变长字段（如 fixed_risk_ids），并追加
    `truncated: true` + `original_size_bytes` 供服务端/运维事后识别。

    Args:
        extra_info: 原始 extra_info 字典
        max_bytes: 最大允许字节数（UTF-8 编码后的 JSON 长度）

    Returns:
        dict: 裁剪后的 extra_info（原始对象不会被修改）
    """
    if not isinstance(extra_info, dict):
        return extra_info

    def _size(obj):
        return len(json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    original_size = _size(extra_info)
    if original_size <= max_bytes:
        return extra_info

    trimmed = dict(extra_info)
    trimmed["truncated"] = True
    trimmed["original_size_bytes"] = original_size

    # 1) 先按优先级清空可截断字段
    for key in _EXTRA_INFO_TRUNCATABLE_KEYS:
        if key not in trimmed:
            continue
        value = trimmed[key]
        if isinstance(value, list):
            # 先记录原始数量再尝试逐步截断
            trimmed[f"{key}_truncated_count"] = len(value)
            # 二分式缩减，尽量多保留。
            # 性能优化：预先计算 trimmed 在该 key 暂置为空列表时的"骨架"大小，
            # 以及每个候选 item 单独序列化的大小并构造前缀和，
            # 从而把二分循环内的 O(N) 全量 json.dumps 退化为 O(1) 估算。
            trimmed[key] = []
            skeleton_size = _size(trimmed)
            # 各 item 单独序列化字节数
            item_sizes = [_size(item) for item in value]
            # 前缀和：prefix[i] = item_sizes[0..i-1] 总和
            prefix = [0]
            for s in item_sizes:
                prefix.append(prefix[-1] + s)

            def _estimate(n):
                # 估算把 value[:n] 写回 trimmed[key] 后的总字节数。
                # skeleton_size 已包含 "[]"（2 字节空列表）；
                # 非空时形如 [item1, item2, ...]：增加 sum(item_sizes[:n]) 个 item 字节，
                # 加上 (n-1) 个 ", " 分隔符（json.dumps 默认 separators=(", ", ": ")，2 字节）；
                # 括号本身已计入 skeleton_size，无需重复。
                if n <= 0:
                    return skeleton_size
                items_bytes = prefix[n] + max(0, n - 1) * 2
                return skeleton_size + items_bytes

            lo, hi = 0, len(value)
            best = 0
            while lo <= hi:
                mid = (lo + hi) // 2
                if _estimate(mid) <= max_bytes:
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            trimmed[key] = value[:best]
            # 估算可能存在 ±1~2 字节误差（罕见 unicode 边界），用真实大小校验一次
            if _size(trimmed) <= max_bytes:
                return trimmed
            # 若仍超限，回退一项
            while best > 0 and _size(trimmed) > max_bytes:
                best -= 1
                trimmed[key] = value[:best]
            if _size(trimmed) <= max_bytes:
                return trimmed
        # 非列表类型或二分仍超限，直接丢弃
        trimmed[key] = None if isinstance(value, list) else ""
        if _size(trimmed) <= max_bytes:
            return trimmed

    # 2) 兜底：只保留基础元数据（保证 payload 可用）
    core = {
        "truncated": True,
        "original_size_bytes": original_size,
    }
    for key in ("report_type", "project_name", "original_batch_id"):
        if key in extra_info:
            core[key] = extra_info[key]
    return core


def _enforce_risk_list_limit(risk_list, auto_fixed_list, max_bytes=MAX_RISK_LIST_BYTES):
    """确保 risk_list 与 auto_fixed_list 合计序列化后不超过客户端上限（默认 512 KB）。

    裁剪策略：
    - 按 severity 优先级（critical > high > medium > low）保留
    - 同级内按 risk_confidence 降序保留
    - auto_fixed_list 会同步丢弃被从 risk_list 删除的条目（按 rule_id+file_path+line_number 匹配）

    Args:
        risk_list: 原始 risk_list
        auto_fixed_list: 原始 auto_fixed_list（通常是 risk_list 的子集）
        max_bytes: 两者合计的最大字节数

    Returns:
        tuple: (trimmed_risk_list, trimmed_auto_fixed_list, truncation_info)
            truncation_info: 裁剪元数据，未裁剪时为 None
    """
    def _size(a, b):
        return (
            len(json.dumps(a, ensure_ascii=False).encode("utf-8"))
            + len(json.dumps(b, ensure_ascii=False).encode("utf-8"))
        )

    def _size_one(item):
        return len(json.dumps(item, ensure_ascii=False).encode("utf-8"))

    original_size = _size(risk_list, auto_fixed_list)
    if original_size <= max_bytes:
        return risk_list, auto_fixed_list, None

    original_count = len(risk_list)
    original_fixed_count = len(auto_fixed_list)

    def _item_key(item):
        """基于 rule_id / file_path / line_number 生成 auto_fixed_list 同步裁剪的匹配键"""
        return (
            item.get("rule_id") or "",
            item.get("file_path") or "",
            item.get("line_number"),
        )

    # 按 (severity优先级, -confidence) 排序——数值越小越优先保留
    def _priority(item):
        sev = (item.get("severity") or "low").lower()
        sev_rank = _SEVERITY_PRIORITY.get(sev, 99)
        confidence = item.get("risk_confidence") or 0
        try:
            confidence = int(confidence)
        except (TypeError, ValueError):
            confidence = 0
        return (sev_rank, -confidence)

    # 稳定排序：保留原顺序作为次级 tiebreaker
    sorted_with_idx = sorted(enumerate(risk_list), key=lambda t: (_priority(t[1]), t[0]))

    # 性能优化：预计算各项独立序列化大小并构造前缀和，
    # 使二分循环内的 O(N+M) 全量 json.dumps 退化为 O(1) 估算。
    # 估算依据：JSON 列表 [a, b, ...] 字节数 = 2(括号) + sum(item_sizes) + (n-1)*2(", " 分隔符)。
    # 注：json.dumps 默认 separators=(", ", ": ")，列表项分隔为 2 字节而非 1 字节。
    def _list_bytes(item_sizes_total, n):
        if n <= 0:
            return 2  # "[]"
        return 2 + item_sizes_total + (n - 1) * 2

    # 把 auto_fixed_list 按 key 索引，便于查询每个 risk 对应的 fixed 增量
    fixed_by_key = {}
    for fitem in auto_fixed_list:
        fixed_by_key.setdefault(_item_key(fitem), []).append(fitem)

    # 按 sorted_with_idx 顺序累计：第 k 个 risk 对应的 risk_size、新增 fixed_size
    risk_size_seq = []
    fixed_size_seq = []   # 每加入一条 risk，所引入的 fixed item 总 bytes
    fixed_count_seq = []  # 每加入一条 risk，所引入的 fixed item 数量
    seen_fixed_ids = set()
    for _, ritem in sorted_with_idx:
        risk_size_seq.append(_size_one(ritem))
        rkey = _item_key(ritem)
        added = 0
        added_count = 0
        for fitem in fixed_by_key.get(rkey, []):
            fid = id(fitem)
            if fid in seen_fixed_ids:
                continue
            seen_fixed_ids.add(fid)
            added += _size_one(fitem)
            added_count += 1
        fixed_size_seq.append(added)
        fixed_count_seq.append(added_count)

    # 前缀和
    risk_prefix = [0]
    for s in risk_size_seq:
        risk_prefix.append(risk_prefix[-1] + s)
    fixed_size_prefix = [0]
    for s in fixed_size_seq:
        fixed_size_prefix.append(fixed_size_prefix[-1] + s)
    fixed_count_prefix = [0]
    for c in fixed_count_seq:
        fixed_count_prefix.append(fixed_count_prefix[-1] + c)

    def _estimate(n):
        risk_bytes = _list_bytes(risk_prefix[n], n)
        f_count = fixed_count_prefix[n]
        fixed_bytes = _list_bytes(fixed_size_prefix[n], f_count)
        return risk_bytes + fixed_bytes

    # 二分查找：保留前 N 条能放下的最大 N
    lo, hi, best = 0, len(sorted_with_idx), 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if _estimate(mid) <= max_bytes:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    kept_indices = {idx for idx, _ in sorted_with_idx[:best]}
    trimmed_risk = [item for i, item in enumerate(risk_list) if i in kept_indices]
    kept_keys = {_item_key(item) for item in trimmed_risk}
    trimmed_fixed = [item for item in auto_fixed_list if _item_key(item) in kept_keys]

    # 估算可能存在轻微误差（如 ensure_ascii=False 下的 unicode 多字节差），用真实大小校验一次并回退
    while best > 0 and _size(trimmed_risk, trimmed_fixed) > max_bytes:
        best -= 1
        kept_indices = {idx for idx, _ in sorted_with_idx[:best]}
        trimmed_risk = [item for i, item in enumerate(risk_list) if i in kept_indices]
        kept_keys = {_item_key(item) for item in trimmed_risk}
        trimmed_fixed = [item for item in auto_fixed_list if _item_key(item) in kept_keys]

    # 统计各级别保留情况
    severity_kept = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for item in trimmed_risk:
        sev = (item.get("severity") or "low").lower()
        if sev in severity_kept:
            severity_kept[sev] += 1

    truncation_info = {
        "risk_list_truncated": True,
        "risk_list_original_count": original_count,
        "risk_list_kept_count": len(trimmed_risk),
        "risk_list_original_bytes": original_size,
        "auto_fixed_list_original_count": original_fixed_count,
        "auto_fixed_list_kept_count": len(trimmed_fixed),
        "risk_list_kept_by_severity": severity_kept,
    }
    return trimmed_risk, trimmed_fixed, truncation_info


def _normalize_issue_item(issue):
    """将单条 issue 归一化为上报字段。

    入参契约（v2 统一 schema 之后）：
    - 输入永远是 PascalCase（result-*.json 中的 RiskList 项，或本文件
      lines 128-139 由 merged-scan.json findings 翻译产生的 PascalCase 项）。
    - 这是唯一的「上传边界」翻译层；不再做 camelCase 回退。

    Returns:
        dict: 服务端期望的上报字段；key 缺失返回空字符串/None。
    """
    severity_raw = issue.get("RiskLevel", "")
    return {
        "file_path": issue.get("FilePath", ""),
        "rule_id": issue.get("RiskId") or issue.get("RiskType") or "",
        "rule_name": issue.get("RiskType", ""),
        "severity": get_risk_level_normalized(severity_raw),
        "line_number": issue.get("LineNumber"),
        "risk_confidence": issue.get("RiskConfidence"),
        "code_snippet": issue.get("RiskCode", ""),
        "description": issue.get("RiskDetail", ""),
        "recommendation": issue.get("Suggestions", ""),
        "fixed_code": issue.get("FixedCode", ""),
    }


def build_upload_payload(results, summary, batch_dir, code_branch=None, project_name=None):
    """构建上报 payload（含完整 risk_list 与 auto_fixed_list）

    用户身份由 CodeBuddy 代理网关根据认证信息注入，本地不再采集 username。
    """
    # 统计风险数量并构造列表
    total_issues = 0
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    fixed_count = 0
    risk_list = []
    auto_fixed_list = []

    for result in results:
        # 入参契约：result 来自上文 build 流程（line 141 issues 键）或外部
        # result-*.json（RiskList 键）；二者都是 PascalCase。
        issues = result.get('RiskList', result.get('issues', []))
        for issue in issues:
            total_issues += 1
            risk_level = issue.get('RiskLevel', '')
            level_normalized = get_risk_level_normalized(risk_level)
            if level_normalized == 'critical':
                critical_count += 1
            elif level_normalized == 'high':
                high_count += 1
            elif level_normalized == 'medium':
                medium_count += 1
            else:
                low_count += 1

            normalized = _normalize_issue_item(issue)
            risk_list.append(normalized)
            if normalized["fixed_code"]:
                fixed_count += 1
                auto_fixed_list.append(normalized)

    audit_batch_id = summary.get('auditBatchId') or summary.get('batchId') or (batch_dir.name if batch_dir else 'unknown')

    # 读取审计耗时信息
    timing = _read_audit_timing(batch_dir) if batch_dir else {}

    # scan_time 优先使用审计开始时间，否则使用当前时间
    scan_time = timing.get("audit_start_time", datetime.now(timezone.utc).isoformat())

    # 构建 extra_info，合并耗时信息
    extra_info = {"report_type": "audit"}
    if project_name:
        extra_info["project_name"] = project_name
    extra_info.update(timing)

    # 读取门禁评估结果
    gate_result = _load_gate_result(batch_dir)
    if gate_result:
        extra_info["gate_status"] = gate_result.get("gateStatus", "unknown")
        extra_info["gate_violations_count"] = len(gate_result.get("violations", []))
        extra_info["gate_evaluated_at"] = gate_result.get("evaluatedAt", "")

    # 确保 risk_list / auto_fixed_list 合计不超过 512 KB，裁剪元数据写入 extra_info
    # 先快照裁剪前的 auto_fixed 计数，裁剪后 auto_fixed_list 可能缩短
    pre_trim_fixed_count = fixed_count
    risk_list, auto_fixed_list, list_trunc = _enforce_risk_list_limit(risk_list, auto_fixed_list)
    if list_trunc:
        extra_info.update(list_trunc)

    # 确保 extra_info 不超过服务端 64 KB 限制
    extra_info = _enforce_extra_info_limit(extra_info)

    total_risks = summary.get("totalIssues")
    if total_risks is None:
        total_risks = summary.get("totalFindings")
    if total_risks is None:
        total_risks = total_issues

    payload = {
        "batch_id": audit_batch_id,
        "total_risks": total_risks,
        "critical_risks": summary.get("criticalRisk", critical_count),
        "high_risks": summary.get("highRisk", high_count),
        "medium_risks": summary.get("mediumRisk", medium_count),
        "low_risks": summary.get("lowRisk", low_count),
        "risk_list": risk_list,
        "auto_fixed_list": auto_fixed_list,
        # auto_fixed_count: 本次审计中带 fixed_code 的风险总数（任意严重度，裁剪前）。
        # 裁剪后 auto_fixed_list 可能更短，服务端可通过 extra_info 中的
        # auto_fixed_list_original_count / auto_fixed_list_kept_count 感知差异。
        # 服务端 ReportCreate 已将历史字段名 auto_fixed_high_count 映射到此字段。
        "auto_fixed_count": pre_trim_fixed_count,
        "scan_time": scan_time,
        # audit_duration_seconds: 审计耗时（秒），从 .audit_start_time / .audit_end_time 计算。
        # 缺少时间标记文件时为 None，服务端应按可选字段处理。
        # extra_info 中同时保留完整 timing 三元组（start/end/duration）供调试。
        "audit_duration_seconds": timing.get("audit_duration_seconds"),
        "extra_info": extra_info,
    }

    return payload


def build_fix_upload_payload(fix_report, batch_dir):
    """构建修复结果上报 payload（兼容服务端 ReportCreate schema）

    服务端只有一个 ReportCreate 入口模型，修复上报需要复用该结构：
    - batch_id 添加 "-fix" 后缀，避免与审计上报的去重冲突（409）
    - scan_time 必填，使用 fix_time 填充
    - fixed_risks 转换为 auto_fixed_list 与 risk_list（二者同源，包含完整字段）
    - 原始修复统计保存到 extra_info 以保留完整数据

    Args:
        fix_report: fix-report.json 中加载的数据
        batch_dir: 批次目录路径 (Path)

    Returns:
        dict: 修复上报 payload
    """
    # 原始 batch_id 加 -fix 后缀，避免与审计上报的 Redis 去重冲突
    raw_batch_id = fix_report.get("batch_id", batch_dir.name)
    fix_batch_id = f"{raw_batch_id}-fix"

    fix_time = fix_report.get("fix_time", datetime.now(timezone.utc).isoformat())

    # 将 fixed_risks 转换为服务端列表字段（risk_list 与 auto_fixed_list 同源）
    auto_fixed_list = []
    fixed_risk_ids = []
    for risk in fix_report.get("fixed_risks", []):
        risk_id = str(risk.get("risk_id", "") or "").strip()
        if risk_id:
            fixed_risk_ids.append(risk_id)
        auto_fixed_list.append({
            "file_path": risk.get("file_path", ""),
            # 优先放 RiskId，便于服务端与审计结果精确关联
            "rule_id": risk_id or risk.get("risk_type", ""),
            "rule_name": risk.get("risk_type", ""),
            "severity": get_risk_level_normalized(risk.get("risk_level", "high")),
            "line_number": risk.get("line_number"),
            "risk_confidence": risk.get("risk_confidence"),
            "code_snippet": risk.get("risk_code", "") or risk.get("code_snippet", ""),
            "description": risk.get("risk_detail", "") or risk.get("description", ""),
            "recommendation": risk.get("fix_method", "") or risk.get("recommendation", ""),
            "fixed_code": risk.get("fixed_code", ""),
        })

    fixed_high = fix_report.get("fixed_high", 0)
    fixed_medium = fix_report.get("fixed_medium", 0)
    fixed_low = fix_report.get("fixed_low", 0)
    # 显式区分"字段缺失"和"值为 0"，避免 `0 or len(...)` 的 falsy 陷阱
    _raw_fixed_total = fix_report.get("fixed_total")
    fixed_total = _raw_fixed_total if _raw_fixed_total is not None else len(auto_fixed_list)

    # 修复上报的 risk_list 即已修复的风险集合（与 auto_fixed_list 同源）
    risk_list = list(auto_fixed_list)

    extra_info = {
        "report_type": "fix",
        "original_batch_id": raw_batch_id,
        "fixed_total": fixed_total,
        "fixed_high": fixed_high,
        "fixed_medium": fixed_medium,
        "fixed_low": fixed_low,
        "fixed_risk_ids": fixed_risk_ids,
    }

    # 确保 risk_list / auto_fixed_list 合计不超过 512 KB
    # auto_fixed_count 使用裁剪前的 fixed_total，与 auto_fixed_list 长度可能不一致；
    # 服务端可通过 extra_info 中的 auto_fixed_list_original_count / kept_count 感知差异。
    risk_list, auto_fixed_list, list_trunc = _enforce_risk_list_limit(risk_list, auto_fixed_list)
    if list_trunc:
        extra_info.update(list_trunc)

    payload = {
        "batch_id": fix_batch_id,
        "scan_time": fix_time,
        "total_risks": fixed_total,
        "high_risks": fixed_high,
        "medium_risks": fixed_medium,
        "low_risks": fixed_low,
        "risk_list": risk_list,
        "auto_fixed_list": auto_fixed_list,
        # auto_fixed_count: 本次修复任务实际修复的漏洞总数（不区分严重度，裁剪前）。
        # fixed_total 在上方已对 None（老版缺失字段）做了兜底，此处直接使用。
        "auto_fixed_count": fixed_total,
        "extra_info": _enforce_extra_info_limit(extra_info),
    }

    return payload


def _write_payload(payload, output_dir):
    """保存 payload 到本地"""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        payload_path = output_dir / "report-payload.json"
        with payload_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        return


def _should_retry_status(status_code):
    """判断 HTTP 状态码是否适合重试"""
    return status_code == 429 or 500 <= status_code < 600


def _retry_sleep_seconds(attempt):
    """按指数退避计算等待时间（秒）"""
    return UPLOAD_RETRY_BACKOFF_SECONDS * (2 ** max(0, attempt - 1))


def _trim_response_text(value, max_len=200):
    """裁剪响应文本，避免错误日志过长"""
    text = str(value or "").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _send_payload(payload, max_retries=UPLOAD_MAX_RETRIES):
    """发送 payload 到上报服务

    仅通过 CodeBuddy 代理通道发送，由网关注入认证信息。

    Args:
        payload: 上报数据
        max_retries: 最大重试次数（Hook 路径传 1，CLI 默认 2）

    Returns:
        tuple: (success: bool, error: str or None)
    """
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    url = get_report_url()
    if not url:
        return False, "未注入 CODEBUDDY_SERVICE_PROXY_URL，无可用上报通道"

    headers = {
        "Content-Type": "application/json",
        "x-codebuddy-request": "1",
        "X-Service-Id": "security-scan",
    }
    return _try_send(url, data, headers, max_retries=max_retries)


def _try_send(url, data, headers, max_retries=UPLOAD_MAX_RETRIES):
    """单通道发送，含重试逻辑

    Returns:
        tuple: (success: bool, error: str or None)
    """
    import urllib.error
    import urllib.request

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=UPLOAD_TIMEOUT_SECONDS) as resp:
                resp.read()
            return True, None
        except urllib.error.HTTPError as e:
            status_code = int(getattr(e, "code", 0) or 0)
            response_body = ""
            try:
                response_body = _trim_response_text(e.read().decode("utf-8", errors="ignore"))
            except Exception:
                response_body = ""

            # 服务端去重冲突：视为已成功上报
            if status_code == 409:
                return True, "服务端已存在相同批次（HTTP 409），按成功处理"

            last_error = f"HTTP {status_code}"
            if response_body:
                last_error += f": {response_body}"

            if attempt < max_retries and _should_retry_status(status_code):
                time.sleep(_retry_sleep_seconds(attempt))
                continue
            return False, last_error
        except urllib.error.URLError as e:
            last_error = f"网络错误: {e.reason}"
            if attempt < max_retries:
                time.sleep(_retry_sleep_seconds(attempt))
                continue
            return False, last_error
        except TimeoutError:
            last_error = "请求超时"
            if attempt < max_retries:
                time.sleep(_retry_sleep_seconds(attempt))
                continue
            return False, last_error
        except Exception as e:
            return False, str(e)

    return False, last_error or "上报失败"


def _report_sent_path(batch_dir):
    """获取上报标记文件路径"""
    return batch_dir / "report-sent.json"


def _mark_report_sent(batch_dir, sent, url, error=None):
    """标记上报状态
    
    Args:
        batch_dir: 批次目录
        sent: 是否上报成功
        url: 上报 URL
        error: 失败原因（可选）
    """
    try:
        payload = {
            "sent": bool(sent),
            "url": url or "",
            "timestamp": datetime.now(BEIJING_TZ).strftime(TIME_FORMAT),
        }
        if error:
            payload["error"] = error
        with _report_sent_path(batch_dir).open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        return


def _read_report_sent(batch_dir):
    """读取上报状态"""
    path = _report_sent_path(batch_dir)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict) and "sent" in payload:
            return bool(payload.get("sent"))
    except Exception:
        return None
    return None


def _write_fix_payload(payload, output_dir):
    """保存修复 payload 到本地"""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        payload_path = output_dir / "fix-report-payload.json"
        with payload_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        return


def _fix_report_sent_path(batch_dir):
    """获取修复上报标记文件路径"""
    return batch_dir / "fix-report-sent.json"


def _mark_fix_report_sent(batch_dir, sent, url, error=None):
    """标记修复上报状态"""
    try:
        payload = {
            "sent": bool(sent),
            "url": url or "",
            "timestamp": datetime.now(BEIJING_TZ).strftime(TIME_FORMAT),
        }
        if error:
            payload["error"] = error
        with _fix_report_sent_path(batch_dir).open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        return


def _read_fix_report_sent(batch_dir):
    """读取修复上报状态"""
    path = _fix_report_sent_path(batch_dir)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict) and "sent" in payload:
            return bool(payload.get("sent"))
    except Exception:
        return None
    return None


def resolve_input_path(input_path, audit_batch_id=None, cwd=None):
    """
    解析输入路径

    查找顺序：
    1. 直接使用 input_path（如果指定）
    2. 在 {project}/.codebuddy/security-scan/runs/ 下查找
    3. 在旧版 security-scan-output/ 下查找
    4. 在 /tmp/security-scan-output/ 下查找
    """
    # 如果直接指定了路径
    if input_path:
        path = Path(input_path)
        if path.exists():
            return path
        # 如果路径不存在但看起来像批次 ID，尝试作为批次 ID 查找
        if not path.is_absolute() and audit_batch_id is None:
            audit_batch_id = str(input_path)

    # 构建 .codebuddy/security-scan/runs 目录列表（用于自动查找）
    security_scan_output_dirs = get_scan_output_dirs(cwd)

    # 如果没有 audit_batch_id，尝试查找最新的批次目录
    if not audit_batch_id:
        for security_scan_path in security_scan_output_dirs:
            if security_scan_path.exists() and security_scan_path.is_dir():
                # 查找最新的批次目录
                batch_dirs = sorted(
                    [d for d in security_scan_path.iterdir() if d.is_dir() and d.name.startswith(BATCH_PREFIXES)],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                if batch_dirs:
                    return batch_dirs[0]
    else:
        # 有 audit_batch_id，直接查找
        for security_scan_dir in security_scan_output_dirs:
            full_path = security_scan_dir / audit_batch_id
            if full_path.exists():
                return Path(full_path)

    return None


def upload_report(input_path=None, audit_batch_id=None, cwd=None, quiet=False, max_retries=UPLOAD_MAX_RETRIES):
    """
    上报审计报告（主函数）

    Args:
        input_path: 审计结果目录路径
        audit_batch_id: 审计批次 ID
        cwd: 工作目录（用于查找 .codebuddy/security-scan/runs，旧版 security-scan-output 仅作 fallback）
        quiet: 是否静默模式

    Returns:
        bool: 上报是否成功
    """
    # 解析输入路径
    batch_dir = resolve_input_path(input_path, audit_batch_id, cwd)
    if batch_dir is None:
        if not quiet:
            print_colored("[FAIL] 未找到审计结果目录", Colors.FAIL)
            print_colored("", Colors.ENDC)
            print_colored("已搜索以下位置：", Colors.WARNING)
            for scan_dir in get_scan_output_dirs(cwd):
                print_colored(f"  - {scan_dir}/{audit_batch_id or '<batch-id>'}", Colors.ENDC)
            print_colored("", Colors.ENDC)
            print_colored("请确保：", Colors.WARNING)
            print_colored("  1. 已执行安全审计并生成了 result-*.json 文件", Colors.ENDC)
            print_colored("  2. 使用 --input 指定正确的审计结果目录路径", Colors.ENDC)
            print_colored("  3. 或使用 --cwd 指定项目工作目录", Colors.ENDC)
        return False

    # 检查是否已上报
    if _report_sent_path(batch_dir).exists():
        sent = _read_report_sent(batch_dir)
        if sent is True:
            if not quiet:
                print_colored("[SKIP] 报告已上报，跳过", Colors.WARNING)
            return True
        if sent is False:
            if not quiet:
                print_colored("🔄 上次上报失败，将重试", Colors.WARNING)
        elif not quiet:
            print_colored("[WARN] report-sent.json 无效，将重试", Colors.WARNING)

    # 陈旧数据保护：若批次目录存在 .scan-session.json，但 summary/finding 都早于会话开始时间，
    # 直接拒绝上报 — 避免把上一次扫描的 finding 当成本次结果上报到服务端
    session = load_scan_session(batch_dir)
    if session is not None:
        candidates = []
        candidates.append(batch_dir / "summary.json")
        candidates.extend(sorted(batch_dir.glob("finding-*.json")))
        candidates.extend(sorted(batch_dir.glob("result-*.json")))
        candidates.append(batch_dir / "merged-scan.json")
        candidates.append(batch_dir / "merged-verified.json")

        existing = [p for p in candidates if p.is_file()]
        fresh = [p for p in existing if is_output_fresh(p, session)]
        stale = [p for p in existing if p not in fresh]

        if existing and not fresh:
            if not quiet:
                print_colored(
                    "[FAIL] 批次目录所有 finding/summary 产物均早于本次扫描会话，疑似 agent 失败导致历史数据残留。",
                    Colors.FAIL,
                )
                print_colored(
                    f"   会话起始: {session.get('startedAtIso', '?')} (runId={session.get('runId', '?')})",
                    Colors.WARNING,
                )
                print_colored(
                    f"   陈旧文件: {[p.name for p in stale]}",
                    Colors.WARNING,
                )
                print_colored(
                    "   已拒绝上报陈旧数据。请重新运行扫描或手动确认产物。",
                    Colors.WARNING,
                )
            # 写入失败标记，便于 Hook / 排查工具识别
            try:
                _mark_report_sent(batch_dir, False, get_report_url() or "",
                                  error="all_outputs_stale")
            except Exception:
                pass
            return False
        if stale and not quiet:
            print_colored(
                f"[WARN] 检测到 {len(stale)} 个陈旧产物：{[p.name for p in stale]}（已忽略，仅使用本会话产物）",
                Colors.WARNING,
            )

    # 加载审计结果
    try:
        results, summary = load_audit_results(str(batch_dir), audit_batch_id)
    except Exception as e:
        if not quiet:
            print_colored(f"[FAIL] 加载审计结果失败: {e}", Colors.FAIL)
        return False

    if not results and not summary:
        if not quiet:
            print_colored("[WARN] 未找到审计结果", Colors.WARNING)
        return False

    # 没有 finding-*.json / result-*.json 但有 summary（0 漏洞场景），仍需构建 summary 并上报
    if not summary:
        summary = {
            'auditBatchId': audit_batch_id or batch_dir.name or 'unknown',
            'riskFiles': 0,
            'totalIssues': 0,
            'highRisk': 0,
            'mediumRisk': 0,
            'lowRisk': 0,
        }

    if not quiet:
        issue_count = summary.get('totalIssues', 0)
        file_count = len(results) if results else summary.get('riskFiles', 0)
        print_colored(f"[OK] 加载了 {file_count} 个审计结果，共 {issue_count} 个风险", Colors.GREEN)

    # 获取 Git 分支和项目名称
    git_base = batch_dir.parent.parent
    code_branch = get_git_branch(git_base) or "未知"
    project_name = get_git_project_name(git_base) or "未知"

    # 构建上报 payload
    payload = build_upload_payload(results, summary, batch_dir, code_branch, project_name=project_name)

    # 保存 payload 到本地
    _write_payload(payload, batch_dir)

    # 上报
    report_url = get_report_url()
    report_url_display = report_url or "(代理通道未注入)"
    if not quiet:
        print_colored(f"📤 正在上报到: {report_url_display}", Colors.CYAN)

    sent, error = _send_payload(payload, max_retries=max_retries)
    if sent:
        _mark_report_sent(batch_dir, True, report_url)
        if not quiet:
            print_colored(f"[OK] 报告已上报: {report_url_display}", Colors.GREEN)
            if error:
                print_colored(f"   说明: {error}", Colors.WARNING)
    else:
        _mark_report_sent(batch_dir, False, report_url, error)
        if not quiet:
            print_colored(f"[FAIL] 报告上报失败: {report_url_display}", Colors.FAIL)
            if error:
                print_colored(f"   原因: {error}", Colors.FAIL)

    return sent


def upload_fix_report(input_path=None, audit_batch_id=None, cwd=None, quiet=False, max_retries=UPLOAD_MAX_RETRIES):
    """
    上报修复结果（主函数）

    Args:
        input_path: 审计结果目录路径
        audit_batch_id: 审计批次 ID
        cwd: 工作目录
        quiet: 是否静默模式

    Returns:
        bool: 上报是否成功
    """
    # 解析输入路径（复用已有的 resolve_input_path）
    batch_dir = resolve_input_path(input_path, audit_batch_id, cwd)
    if batch_dir is None:
        if not quiet:
            print_colored("[FAIL] 未找到审计结果目录", Colors.FAIL)
        return False

    # 检查是否已上报修复结果
    if _fix_report_sent_path(batch_dir).exists():
        sent = _read_fix_report_sent(batch_dir)
        if sent is True:
            if not quiet:
                print_colored("[SKIP] 修复结果已上报，跳过", Colors.WARNING)
            return True
        if sent is False:
            if not quiet:
                print_colored("🔄 上次修复上报失败，将重试", Colors.WARNING)
        elif not quiet:
            print_colored("[WARN] fix-report-sent.json 无效，将重试", Colors.WARNING)

    # 加载 fix-report.json
    fix_report = load_fix_report(batch_dir)
    if fix_report is None:
        if not quiet:
            print_colored(f"[FAIL] 未找到 fix-report.json: {batch_dir / 'fix-report.json'}", Colors.FAIL)
            print_colored("   请确保修复完成后已生成 fix-report.json 文件", Colors.ENDC)
        return False

    if not quiet:
        fixed_total = fix_report.get("fixed_total", 0)
        print_colored(f"[OK] 加载修复报告：共修复 {fixed_total} 个漏洞", Colors.GREEN)

    # 构建修复上报 payload
    payload = build_fix_upload_payload(fix_report, batch_dir)

    # 保存 payload 到本地
    _write_fix_payload(payload, batch_dir)

    # 上报
    report_url = get_report_url()
    report_url_display = report_url or "(代理通道未注入)"
    if not quiet:
        print_colored(f"📤 正在上报修复结果到: {report_url_display}", Colors.CYAN)

    sent, error = _send_payload(payload, max_retries=max_retries)
    if sent:
        _mark_fix_report_sent(batch_dir, True, report_url)
        if not quiet:
            print_colored(f"[OK] 修复结果已上报: {report_url_display}", Colors.GREEN)
            if error:
                print_colored(f"   说明: {error}", Colors.WARNING)
    else:
        _mark_fix_report_sent(batch_dir, False, report_url, error)
        if not quiet:
            print_colored(f"[FAIL] 修复结果上报失败: {report_url_display}", Colors.FAIL)
            if error:
                print_colored(f"   原因: {error}", Colors.FAIL)

    return sent


def main():
    parser = argparse.ArgumentParser(
        description="上报审计/修复结果到服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 从审计目录上报审计结果（推荐）
  %(prog)s --input .codebuddy/security-scan/runs/project-deep-20250103120000

  # 使用审计批次 ID 自动查找目录
  %(prog)s --audit-batch-id project-deep-20250103120000

  # 指定项目工作目录（用于定位 .codebuddy/security-scan/runs）
  %(prog)s --audit-batch-id project-deep-20250103120000 --cwd /path/to/project

  # 自动查找最新的审计批次（不指定 batch-id）
  %(prog)s --cwd /path/to/project

  # 上报修复结果
  %(prog)s --input .codebuddy/security-scan/runs/project-deep-20250103120000 --type fix

  # 静默模式
  %(prog)s --input .codebuddy/security-scan/runs/project-deep-20250103120000 --quiet

上报通过 CodeBuddy 代理通道发送（环境变量 CODEBUDDY_SERVICE_PROXY_URL），
由网关注入认证信息。
        """
    )

    parser.add_argument('--input', help='输入路径（审计结果目录的完整路径）')
    parser.add_argument('--audit-batch-id', help='审计批次 ID（用于自动定位目录）')
    parser.add_argument('--cwd', help='工作目录（用于查找 .codebuddy/security-scan/runs 目录）')
    parser.add_argument('--quiet', action='store_true', help='静默模式（不输出日志）')
    parser.add_argument('--type', choices=['audit', 'fix'], default='audit',
                        help='上报类型：audit（审计结果，默认）或 fix（修复结果）')

    args = parser.parse_args()

    if args.quiet:
        Colors.HEADER = Colors.BLUE = Colors.CYAN = Colors.GREEN = ''
        Colors.WARNING = Colors.FAIL = Colors.ENDC = Colors.BOLD = ''

    # 如果没有指定任何参数，但有 --cwd，则自动查找最新批次
    if not args.input and not args.audit_batch_id and not args.cwd:
        print_colored("[FAIL] 请指定 --input、--audit-batch-id 或 --cwd", Colors.FAIL)
        print_colored("", Colors.ENDC)
        print_colored("示例：", Colors.WARNING)
        print_colored("  report_upload.py --input .codebuddy/security-scan/runs/project-deep-20250103120000", Colors.ENDC)
        print_colored("  report_upload.py --audit-batch-id project-deep-20250103120000", Colors.ENDC)
        print_colored("  report_upload.py --cwd /path/to/project  # 自动查找最新批次", Colors.ENDC)
        sys.exit(1)

    if args.type == 'fix':
        success = upload_fix_report(
            input_path=args.input,
            audit_batch_id=args.audit_batch_id,
            cwd=args.cwd,
            quiet=args.quiet
        )
    else:
        success = upload_report(
            input_path=args.input,
            audit_batch_id=args.audit_batch_id,
            cwd=args.cwd,
            quiet=args.quiet
        )

    sys.exit(0 if success else 1)


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
