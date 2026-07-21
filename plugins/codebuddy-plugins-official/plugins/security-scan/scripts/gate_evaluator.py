#!/usr/bin/env python3
"""
门禁评估器 — 读取扫描结果 + 门禁策略，评估门禁状态

跨平台：Python3 内置模块 + _common.py，零外部依赖。

子命令：
  1. evaluate   — 执行门禁评估，产出 gate-result.json
  2. check      — 检查最近一次门禁状态（供 Hook 快速查询）
  3. summary    — 输出门禁评估摘要（人类可读格式到 stderr）

设计原则：
  - 纯确定性评估：读取 summary.json + finding-*.json + gate-policy.yaml
  - 无 side effect（evaluate 除外：写入 gate-result.json）
  - 所有输出为 JSON（stdout），日志到 stderr
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    make_logger,
    load_json_file,
    load_merged_config,
    write_json_file,
    stdout_json,
    SEVERITY_ORDER,
    severity_rank,
    get_risk_level_normalized,
    get_git_project_root,
    resolve_project_root_from_batch_dir,
    get_scan_output_dirs,
    BEIJING_TZ,
    load_scan_session,
    is_output_fresh,
    session_started_at,
)


# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------

log_info, log_ok, log_warn, log_error = make_logger("gate")

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

GATE_RESULT_FILENAME = "gate-result.json"
GATE_VERSION = "1.0"

# 批次目录前缀（用于自动查找）
BATCH_DIR_PREFIXES = ("project-deep-", "project-light-", "project-fast-",
                      "diff-deep-", "diff-light-", "diff-fast-")

# ---------------------------------------------------------------------------
# YAML 简单解析器（不依赖 pyyaml）
# ---------------------------------------------------------------------------

def _parse_policy_yaml(policy_path):
    """简单 YAML 解析器，仅处理 gate-policy.yaml 的固定结构。

    支持:
    - 顶层键值对: key: value
    - 两级嵌套: section.subsection.field: value
    - 字符串/数字/布尔值
    - # 注释

    Returns:
        dict: 解析后的策略配置
    """
    result = {}

    with open(policy_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    stack = [result]   # 嵌套上下文栈
    indent_stack = [-1]  # 对应缩进级别栈

    for line in lines:
        # 去除注释和右侧空白
        stripped = line.split("#")[0].rstrip()
        if not stripped or stripped.isspace():
            continue

        # 计算缩进
        indent = len(line) - len(line.lstrip())

        # 回退到正确的嵌套级别
        while len(indent_stack) > 1 and indent <= indent_stack[-1]:
            stack.pop()
            indent_stack.pop()

        # 解析 key: value
        match = re.match(r'^(\s*)([\w_]+)\s*:\s*(.*?)\s*$', line)
        if not match:
            continue

        key = match.group(2)
        value_str = match.group(3)

        if value_str:
            # 有值 → 解析标量
            stack[-1][key] = _parse_yaml_value(value_str)
        else:
            # 无值 → 嵌套对象
            new_dict = {}
            stack[-1][key] = new_dict
            stack.append(new_dict)
            indent_stack.append(indent)

    return result


def _parse_yaml_value(value_str):
    """解析 YAML 标量值。"""
    # 去引号
    if (value_str.startswith('"') and value_str.endswith('"')) or \
       (value_str.startswith("'") and value_str.endswith("'")):
        return value_str[1:-1]

    # 布尔值
    lower = value_str.lower()
    if lower in ("true", "yes"):
        return True
    if lower in ("false", "no"):
        return False

    # 数字
    try:
        if "." in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass

    return value_str


# ---------------------------------------------------------------------------
# 数据加载
# ---------------------------------------------------------------------------

def _load_summary(batch_dir, session=None):
    """加载 summary.json。

    若提供了 session 且 summary.json mtime 早于会话起始，视为陈旧产物（来自上一次扫描），
    返回空 dict 并记录 stderr 警告 — 防止门禁误读历史 0 漏洞 / 历史评分通过。
    """
    path = Path(batch_dir) / "summary.json"
    if session is not None and path.is_file() and not is_output_fresh(path, session):
        log_warn(
            f"summary.json 早于本次会话（陈旧），拒绝读取以避免门禁误判: {path}"
        )
        return {}
    data = load_json_file(str(path))
    if data is None:
        log_warn(f"summary.json 不存在: {path}")
    return data or {}


def _load_all_findings(batch_dir, session=None):
    """从 finding-*.json 加载所有 findings。

    若提供了 session，每个候选文件都做新鲜度校验，陈旧文件不进入合并集合。

    Returns:
        tuple[list[dict], dict]:
            findings — 合并后的 findings 列表
            stats    — {'staleFiles': [...], 'loadedFiles': [...]}
    """
    batch_path = Path(batch_dir)
    findings = []
    stale_files = []
    loaded_files = []

    def _accept(path):
        """根据 session 决定是否接受该 finding 源文件。"""
        if session is None:
            return True
        if not path.is_file():
            return False
        if is_output_fresh(path, session):
            return True
        stale_files.append(str(path))
        return False

    # Deep 模式: finding-*.json
    for fp in sorted(batch_path.glob("finding-*.json")):
        if not _accept(fp):
            continue
        data = load_json_file(str(fp))
        if data and isinstance(data, dict):
            issues = data.get("findings", [])
            if isinstance(issues, list):
                findings.extend(issues)
                loaded_files.append(fp.name)

    # Light 模式: merged-scan.json
    if not findings:
        merged_path = batch_path / "merged-scan.json"
        if _accept(merged_path):
            merged = load_json_file(str(merged_path))
            if merged and isinstance(merged, dict):
                merged_findings = merged.get("findings", [])
                if isinstance(merged_findings, list):
                    findings.extend(merged_findings)
                    loaded_files.append(merged_path.name)

    # Deep 模式验证后: merged-verified.json
    if not findings:
        verified_path = batch_path / "merged-verified.json"
        if _accept(verified_path):
            verified = load_json_file(str(verified_path))
            if verified and isinstance(verified, dict):
                verified_findings = verified.get("findings", [])
                if isinstance(verified_findings, list):
                    findings.extend(verified_findings)
                    loaded_files.append(verified_path.name)

    if stale_files:
        log_warn(
            f"陈旧数据保护：拒绝读取 {len(stale_files)} 个早于本次会话的 finding 源 — "
            f"{[Path(p).name for p in stale_files]}"
        )

    return findings, {"staleFiles": stale_files, "loadedFiles": loaded_files}


def _get_finding_confidence(finding):
    """从 finding 中提取置信度（v2: 严格 camelCase confidence）。"""
    val = finding.get("confidence")
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _get_finding_severity(finding):
    """从 finding 中提取风险等级（v2: 严格 camelCase severity）。"""
    val = finding.get("severity")
    if val:
        return get_risk_level_normalized(str(val))
    return "low"


# ---------------------------------------------------------------------------
# 规则评估
# ---------------------------------------------------------------------------

def _evaluate_high_severity(summary, findings, rule):
    """评估高危/严重漏洞数量规则。

    Returns:
        dict: 违规详情，或 None（通过）
    """
    if not rule.get("enabled", True):
        return None

    max_count = rule.get("max_count", 0)
    include_critical = rule.get("include_critical", True)
    include_high = rule.get("include_high", True)

    # 优先从 summary 取值
    critical = summary.get("criticalRisk", 0) or 0
    high = summary.get("highRisk", 0) or 0

    # 如果 summary 没有分级数据，从 findings 统计
    if critical == 0 and high == 0 and findings:
        for f in findings:
            sev = _get_finding_severity(f)
            if sev == "critical":
                critical += 1
            elif sev == "high":
                high += 1

    actual = 0
    if include_critical:
        actual += critical
    if include_high:
        actual += high

    if actual > max_count:
        details_parts = []
        if include_critical:
            details_parts.append(f"critical: {critical}")
        if include_high:
            details_parts.append(f"high: {high}")
        return {
            "rule": "high_severity_threshold",
            "description": rule.get("description", "严重+高危漏洞总数超过阈值"),
            "threshold": max_count,
            "actual": actual,
            "details": ", ".join(details_parts),
        }

    return None


def _evaluate_high_confidence(findings, rule):
    """评估高置信度漏洞数量规则。

    Returns:
        dict: 违规详情，或 None（通过）
    """
    if not rule.get("enabled", True):
        return None

    min_confidence = rule.get("min_confidence", 90)
    max_count = rule.get("max_count", 0)

    high_conf_count = 0
    for f in findings:
        conf = _get_finding_confidence(f)
        if conf >= min_confidence:
            high_conf_count += 1

    if high_conf_count > max_count:
        return {
            "rule": "high_confidence_threshold",
            "description": rule.get("description", "高置信度漏洞数量超过限制"),
            "threshold": max_count,
            "actual": high_conf_count,
            "minConfidence": min_confidence,
            "details": f"{high_conf_count} 个漏洞置信度 >= {min_confidence}",
        }

    return None


def _evaluate_total_issues(summary, rule):
    """评估总漏洞数阈值规则。"""
    if not rule.get("enabled", True):
        return None

    max_count = rule.get("max_count", 20)
    total = summary.get("totalIssues", 0) or summary.get("totalFindings", 0) or 0

    if total > max_count:
        return {
            "rule": "total_issues_threshold",
            "description": rule.get("description", "漏洞总数超过阈值"),
            "threshold": max_count,
            "actual": total,
            "details": f"总漏洞数 {total} > {max_count}",
        }

    return None


def _evaluate_fix_rate(batch_dir, summary, rule):
    """评估修复率阈值规则。"""
    if not rule.get("enabled", True):
        return None

    min_rate = rule.get("min_rate", 0.8)

    # 加载 fix-report.json
    fix_report = load_json_file(str(Path(batch_dir) / "fix-report.json"))
    if fix_report is None:
        # 没有修复报告，无法评估
        return None

    total = summary.get("totalIssues", 0) or summary.get("totalFindings", 0) or 0
    if total == 0:
        return None

    fixed_total = fix_report.get("fixed_total", 0) or 0
    fix_rate = fixed_total / total if total > 0 else 0

    if fix_rate < min_rate:
        return {
            "rule": "fix_rate_threshold",
            "description": rule.get("description", "修复率低于阈值"),
            "threshold": min_rate,
            "actual": round(fix_rate, 3),
            "details": f"修复率 {fix_rate:.1%} < {min_rate:.0%} (已修复 {fixed_total}/{total})",
        }

    return None


def _determine_gate_status(violations, gate_mode):
    """根据违规列表和门禁模式确定最终状态。

    Returns:
        "pass" | "warn" | "soft-block"
    """
    if not violations:
        return "pass"

    if gate_mode == "strict":
        return "soft-block"

    return "warn"


# ---------------------------------------------------------------------------
# 默认策略路径
# ---------------------------------------------------------------------------

def _default_policy_path():
    """获取默认的 gate-policy.yaml 路径。"""
    plugin_root = os.environ.get(
        "CODEBUDDY_PLUGIN_ROOT",
        str(Path(__file__).resolve().parent.parent),
    )
    return os.path.join(plugin_root, "resource", "gate-policy.yaml")


def _project_root_from_batch_dir(batch_dir: Path) -> str:
    """从批次目录推断项目根目录，兼容 .codebuddy 新路径和旧 security-scan-output。"""
    candidate = resolve_project_root_from_batch_dir(batch_dir)
    git_root = get_git_project_root(candidate)
    return git_root if git_root else ""


# ---------------------------------------------------------------------------
# 子命令: evaluate
# ---------------------------------------------------------------------------

def cmd_evaluate(args):
    """执行门禁评估，产出 gate-result.json。"""
    batch_dir = Path(args.batch_dir)
    project_root = getattr(args, "project_root", None) or _project_root_from_batch_dir(batch_dir)
    policy_path = args.policy or _default_policy_path()

    # 1. 加载策略
    if not os.path.exists(policy_path):
        log_error(f"门禁策略文件不存在: {policy_path}")
        stdout_json({"gateStatus": "unknown", "reason": "policy_not_found"})
        return

    try:
        policy = _parse_policy_yaml(policy_path)
    except Exception as e:
        log_error(f"门禁策略解析失败: {e}")
        stdout_json({"gateStatus": "unknown", "reason": "policy_parse_error"})
        return

    # gate_mode 优先从 config.json 读取（setup 配置），fallback 到 gate-policy.yaml
    merged_config = load_merged_config(project_root)
    gate_mode = merged_config.get("gate_mode") or policy.get("gate_mode", "warn")
    rules = policy.get("rules", {})
    messages = policy.get("messages", {})

    # 2. 加载扫描结果
    if not batch_dir.is_dir():
        log_error(f"批次目录不存在: {batch_dir}")
        stdout_json({"gateStatus": "unknown", "reason": "batch_dir_not_found"})
        return

    # 加载会话锁（防止读到上一次扫描遗留的陈旧产物）
    session = load_scan_session(batch_dir)
    if session is None:
        log_warn(
            "未找到 .scan-session.json，按兼容模式评估门禁，无法保证产物属于本次扫描。"
        )

    summary = _load_summary(batch_dir, session=session)
    findings, finding_stats = _load_all_findings(batch_dir, session=session)
    stale_files = finding_stats.get("staleFiles", [])
    loaded_files = finding_stats.get("loadedFiles", [])

    # 陈旧保护：会话存在但所有产物都早于会话 → 标记为 stale，不沿用历史结果
    if session is not None and not summary and not findings and stale_files:
        reason = "all_outputs_stale"
        log_error(
            f"门禁评估失败：批次目录所有 summary/finding 产物均早于本次扫描会话 — {len(stale_files)} 个陈旧文件"
        )
        gate_result = {
            "version": GATE_VERSION,
            "batchId": batch_dir.name,
            "evaluatedAt": datetime.now(BEIJING_TZ).isoformat(),
            "gateMode": gate_mode,
            "gateStatus": "stale",
            "reason": reason,
            "runId": session.get("runId"),
            "sessionStartedAt": session_started_at(session),
            "staleFiles": [Path(p).name for p in stale_files],
            "summary": {
                "totalFindings": 0,
                "criticalRisk": 0,
                "highRisk": 0,
                "mediumRisk": 0,
                "lowRisk": 0,
                "highConfidenceCount": 0,
            },
            "violations": [],
            "passedRules": [],
            "message": "门禁评估终止：当前批次目录所有产物均早于本次扫描会话，疑似 agent 失败导致历史数据残留。",
        }
        write_json_file(str(batch_dir / GATE_RESULT_FILENAME), gate_result)
        stdout_json(gate_result)
        return

    log_info(f"加载扫描结果: {summary.get('totalIssues', 0) or summary.get('totalFindings', 0)} 个漏洞, {len(findings)} 个详细 findings")

    # 3. 评估规则
    violations = []
    passed_rules = []

    # 规则 1: 高危/严重漏洞
    rule_cfg = rules.get("high_severity_threshold", {})
    if rule_cfg.get("enabled", True):
        result = _evaluate_high_severity(summary, findings, rule_cfg)
        if result:
            violations.append(result)
        else:
            passed_rules.append("high_severity_threshold")
    else:
        passed_rules.append("high_severity_threshold (disabled)")

    # 规则 2: 高置信度漏洞
    rule_cfg = rules.get("high_confidence_threshold", {})
    if rule_cfg.get("enabled", True):
        result = _evaluate_high_confidence(findings, rule_cfg)
        if result:
            violations.append(result)
        else:
            passed_rules.append("high_confidence_threshold")
    else:
        passed_rules.append("high_confidence_threshold (disabled)")

    # 规则 3: 总漏洞数
    rule_cfg = rules.get("total_issues_threshold", {})
    if rule_cfg.get("enabled", True):
        result = _evaluate_total_issues(summary, rule_cfg)
        if result:
            violations.append(result)
        else:
            passed_rules.append("total_issues_threshold")
    else:
        passed_rules.append("total_issues_threshold (disabled)")

    # 规则 4: 修复率
    rule_cfg = rules.get("fix_rate_threshold", {})
    if rule_cfg.get("enabled", True):
        result = _evaluate_fix_rate(batch_dir, summary, rule_cfg)
        if result:
            violations.append(result)
        else:
            passed_rules.append("fix_rate_threshold")
    else:
        passed_rules.append("fix_rate_threshold (disabled)")

    # 4. 确定门禁状态
    gate_status = _determine_gate_status(violations, gate_mode)

    # 5. 构建消息
    violation_count = len(violations)
    if gate_status == "pass":
        message = messages.get("gate_pass", "门禁通过：本次扫描结果符合安全策略要求。")
    elif gate_status == "soft-block":
        template = messages.get("gate_soft_block",
                                "门禁未通过：发现 {violation_count} 项严重安全策略违规，强烈建议修复后再推送。")
        message = template.replace("{violation_count}", str(violation_count))
    else:
        template = messages.get("gate_warn",
                                "门禁告警：发现 {violation_count} 项安全策略违规，建议在推送前修复。")
        message = template.replace("{violation_count}", str(violation_count))

    # 6. 统计高置信度漏洞数
    high_conf_count = 0
    for f in findings:
        if _get_finding_confidence(f) >= 90:
            high_conf_count += 1

    # 7. 构建 gate-result.json
    batch_id = summary.get("auditBatchId") or batch_dir.name

    # 从 summary 取分级统计，如果全为 0 则依次尝试 merged-scan.json 和 findings 重新统计
    s_critical = summary.get("criticalRisk", 0) or 0
    s_high = summary.get("highRisk", 0) or 0
    s_medium = summary.get("mediumRisk", 0) or 0
    s_low = summary.get("lowRisk", 0) or 0

    if s_critical == 0 and s_high == 0 and s_medium == 0 and s_low == 0:
        # 兜底 1: 尝试从 merged-scan.json 的 bySeverity 读取
        # 注意：必须经过 session 新鲜度校验，否则会从上次扫描的陈旧 merged-scan.json
        # 捞出历史分级统计，污染本次门禁结果
        merged_scan_path = batch_dir / "merged-scan.json"
        if session is not None and merged_scan_path.is_file() and not is_output_fresh(merged_scan_path, session):
            log_warn("merged-scan.json 早于本次会话，跳过分级兜底")
            merged_scan = None
        else:
            merged_scan = load_json_file(str(merged_scan_path))
        if merged_scan and isinstance(merged_scan, dict):
            by_sev = merged_scan.get("bySeverity", {})
            s_critical = by_sev.get("critical", 0) or 0
            s_high = by_sev.get("high", 0) or 0
            s_medium = by_sev.get("medium", 0) or 0
            s_low = by_sev.get("low", 0) or 0

        # 兜底 2: 仍全为 0 但有 findings，从 findings 逐条统计
        # findings 已经在 _load_all_findings 中做过 session 校验，此处可直接使用
        if s_critical == 0 and s_high == 0 and s_medium == 0 and s_low == 0 and findings:
            for f in findings:
                sev = _get_finding_severity(f)
                if sev == "critical":
                    s_critical += 1
                elif sev == "high":
                    s_high += 1
                elif sev == "medium":
                    s_medium += 1
                else:
                    s_low += 1

    gate_result = {
        "version": GATE_VERSION,
        "batchId": batch_id,
        "evaluatedAt": datetime.now(BEIJING_TZ).isoformat(),
        "gateMode": gate_mode,
        "gateStatus": gate_status,
        "summary": {
            "totalFindings": summary.get("totalIssues", 0) or summary.get("totalFindings", 0) or len(findings),
            "criticalRisk": s_critical,
            "highRisk": s_high,
            "mediumRisk": s_medium,
            "lowRisk": s_low,
            "highConfidenceCount": high_conf_count,
        },
        "violations": violations,
        "passedRules": passed_rules,
        "message": message,
    }

    # 注入会话标识与陈旧文件清单（便于事后排查）
    if session is not None:
        gate_result["runId"] = session.get("runId")
        gate_result["sessionStartedAt"] = session_started_at(session)
        if stale_files:
            gate_result["staleFiles"] = [Path(p).name for p in stale_files]
        if loaded_files:
            gate_result["loadedFiles"] = loaded_files

    # 8. 写入 gate-result.json
    gate_result_path = batch_dir / GATE_RESULT_FILENAME
    write_json_file(str(gate_result_path), gate_result)
    log_ok(f"门禁评估完成: {gate_status} → {gate_result_path}")

    # 9. stdout 输出
    stdout_json(gate_result)


# ---------------------------------------------------------------------------
# 子命令: check
# ---------------------------------------------------------------------------

def _find_latest_batch_dir(scan_output_dir):
    """查找最新的批次目录。"""
    scan_path = Path(scan_output_dir)
    if not scan_path.is_dir():
        return None

    batch_dirs = []
    for d in scan_path.iterdir():
        if d.is_dir() and d.name.startswith(BATCH_DIR_PREFIXES):
            batch_dirs.append(d)

    if not batch_dirs:
        return None

    # 按修改时间倒序
    batch_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return batch_dirs[0]


def _find_latest_gate_result(scan_output_dir):
    """查找最新批次目录中的 gate-result.json。"""
    scan_path = Path(scan_output_dir)
    if not scan_path.is_dir():
        return None

    batch_dirs = []
    for d in scan_path.iterdir():
        if d.is_dir() and d.name.startswith(BATCH_DIR_PREFIXES):
            batch_dirs.append(d)

    if not batch_dirs:
        return None

    # 按修改时间倒序，找第一个有 gate-result.json 的
    batch_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    for bd in batch_dirs:
        gate_path = bd / GATE_RESULT_FILENAME
        if gate_path.exists():
            return gate_path

    return None


def cmd_check(args):
    """检查最近一次门禁状态。"""
    gate_data = None

    # 优先使用 --batch-dir
    if args.batch_dir:
        gate_path = Path(args.batch_dir) / GATE_RESULT_FILENAME
        gate_data = load_json_file(str(gate_path))

    # 其次使用 --scan-output-dir
    if gate_data is None and args.scan_output_dir:
        gate_path = _find_latest_gate_result(args.scan_output_dir)
        if gate_path:
            gate_data = load_json_file(str(gate_path))

    # 最后尝试默认扫描目录（新路径优先，旧路径兼容）
    if gate_data is None:
        for scan_dir in get_scan_output_dirs(os.getcwd()):
            gate_path = _find_latest_gate_result(str(scan_dir))
            if gate_path:
                gate_data = load_json_file(str(gate_path))
                break

    if gate_data and isinstance(gate_data, dict) and "gateStatus" in gate_data:
        stdout_json(gate_data)
    else:
        stdout_json({"gateStatus": "unknown", "reason": "no_gate_result"})


# ---------------------------------------------------------------------------
# 子命令: summary
# ---------------------------------------------------------------------------

def cmd_summary(args):
    """输出门禁评估摘要（人类可读格式到 stderr）。"""
    batch_dir = Path(args.batch_dir)
    gate_path = batch_dir / GATE_RESULT_FILENAME
    gate_data = load_json_file(str(gate_path))

    if not gate_data or not isinstance(gate_data, dict):
        log_warn(f"gate-result.json 不存在或无效: {gate_path}")
        stdout_json({"gateStatus": "unknown", "reason": "no_gate_result"})
        return

    gate_status = gate_data.get("gateStatus", "unknown")
    violations = gate_data.get("violations", [])
    gate_summary = gate_data.get("summary", {})
    message = gate_data.get("message", "")

    # 彩色 stderr 输出
    from _common import Colors
    separator = "─" * 50

    print(f"\n{Colors.BOLD}{separator}{Colors.ENDC}", file=sys.stderr)
    print(f"{Colors.BOLD}  安全门禁评估结果{Colors.ENDC}", file=sys.stderr)
    print(f"{Colors.BOLD}{separator}{Colors.ENDC}", file=sys.stderr)

    # 状态行
    if gate_status == "pass":
        status_color = Colors.GREEN
        status_icon = "PASS"
    elif gate_status == "soft-block":
        status_color = Colors.FAIL
        status_icon = "BLOCK"
    else:
        status_color = Colors.WARNING
        status_icon = "WARN"

    print(f"\n  状态: {status_color}[{status_icon}] {gate_status}{Colors.ENDC}", file=sys.stderr)

    # 摘要数据
    total = gate_summary.get("totalFindings", 0)
    critical = gate_summary.get("criticalRisk", 0)
    high = gate_summary.get("highRisk", 0)
    medium = gate_summary.get("mediumRisk", 0)
    low = gate_summary.get("lowRisk", 0)
    high_conf = gate_summary.get("highConfidenceCount", 0)

    print(f"  漏洞: {total} 个 (严重:{critical} 高:{high} 中:{medium} 低:{low})", file=sys.stderr)
    print(f"  高置信度: {high_conf} 个", file=sys.stderr)

    # 违规详情
    if violations:
        print(f"\n  {Colors.WARNING}违规项 ({len(violations)}):{Colors.ENDC}", file=sys.stderr)
        for v in violations:
            print(f"    - [{v.get('rule', '?')}] {v.get('details', '')}", file=sys.stderr)

    # 消息
    if message:
        print(f"\n  {message}", file=sys.stderr)

    print(f"\n{Colors.BOLD}{separator}{Colors.ENDC}\n", file=sys.stderr)

    # stdout 输出 JSON
    stdout_json(gate_data)


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="门禁评估器 — 评估扫描结果是否满足安全策略",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 执行门禁评估
  %(prog)s evaluate --batch-dir .codebuddy/security-scan/runs/project-deep-xxx

  # 检查最近一次门禁状态（供 Hook 快速查询）
  %(prog)s check --scan-output-dir .codebuddy/security-scan/runs

  # 输出门禁摘要
  %(prog)s summary --batch-dir .codebuddy/security-scan/runs/project-deep-xxx
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # evaluate
    p_eval = subparsers.add_parser("evaluate", help="执行门禁评估")
    p_eval.add_argument("--batch-dir", required=True,
                        help="扫描批次目录路径")
    p_eval.add_argument("--policy", default=None,
                        help="gate-policy.yaml 路径（默认: 插件 resource 目录）")
    p_eval.add_argument("--project-root", default=None,
                        help="项目根目录（自定义输出位置时显式传入；未传则从批次目录反推 + git 兜底）")
    p_eval.set_defaults(func=cmd_evaluate)

    # check
    p_check = subparsers.add_parser("check", help="检查最近一次门禁状态")
    p_check.add_argument("--batch-dir", default=None,
                         help="扫描批次目录路径")
    p_check.add_argument("--scan-output-dir", default=None,
                         help=".codebuddy/security-scan/runs 目录")
    p_check.set_defaults(func=cmd_check)

    # summary
    p_summary = subparsers.add_parser("summary", help="输出门禁摘要")
    p_summary.add_argument("--batch-dir", required=True,
                           help="扫描批次目录路径")
    p_summary.set_defaults(func=cmd_summary)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        log_error(f"未预期的错误: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
