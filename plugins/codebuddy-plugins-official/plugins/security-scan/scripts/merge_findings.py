#!/usr/bin/env python3
"""
审计结果合并脚本：将多个 agent 的审计输出合并、去重、校验，减少编排器上下文消耗

子命令：
  merge-scan     合并扫描阶段所有 agent 输出（格式校验 + 去重 + 分配 findingId）
  merge-verify   合并验证阶段结果（代码存在性校验 + 攻击链验证 + 对抗审查 + 全局审计质量评估 + 置信度评分）

  别名：merge-stage2 = merge-scan, merge-stage3 = merge-verify

设计原则：
  - 完整结果写入文件，stdout 仅输出机器可读的 JSON 摘要供编排器解析
  - 日志信息输出到 stderr，不污染 stdout
  - 缺失可选输入文件时降级处理，不中断流程

Sink 分批 / 续扫模式：
  merge-scan --extra-agents vuln-scan-cont
  动态加载额外 agent 产物文件，支持 Sink 分批和续扫场景。
"""
import argparse
import contextlib
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import (
    Colors, make_logger, stdout_json,
    load_json_file, write_json_file,
    SEVERITY_ORDER, normalize_finding, to_report_format,
    load_scan_session, is_output_fresh, session_started_at,
    LegacyFieldError,
)


# Fast P0：bypass 路径前置的 pre-check 兜底
# 采用函数级 lazy import，避免 verifier 模块在单元测试或非 fast 路径下被强加载
def _lazy_import_run_pre_check():
    try:
        from verifier import run_pre_check  # type: ignore
        return run_pre_check
    except Exception:
        return None


def _lazy_import_fast_plus_verifiers():
    try:
        from verifier import run_chain_verify, run_challenge  # type: ignore
        return run_chain_verify, run_challenge
    except Exception:
        return None, None


def _lazy_import_severity_compliance():
    """加载 verifier.apply_severity_compliance（纯函数级别合规校验，不依赖 index.db）。

    用于 Light bypass 路径：Light 不跑完整 challenge，但 §4 级别合规本就只依赖
    taxonomy 基线 + finding 字段，可零开销强制执行，避免越级噪声进报告。
    """
    try:
        from verifier import apply_severity_compliance  # type: ignore
        return apply_severity_compliance
    except Exception:
        return None


def _silenced_call(fn, *args, **kwargs):
    """调用会向 stdout 写 JSON 的 verifier 函数，吞掉其 stdout，避免污染 merge-verify 协议。

    merge_findings.py 的 stdout 契约是"最终只输出一条 JSON 摘要"，而 verifier 里
    run_chain_verify / run_challenge 内部会通过 stdout_json 打印自身摘要。内嵌调用时
    必须重定向 stdout 到内存 buffer 再丢弃，stderr 保持原样以保留日志。
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn(*args, **kwargs)


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 从权威文件 risk-type-taxonomy.yaml 动态加载风险类型映射
# ---------------------------------------------------------------------------

def _load_taxonomy_yaml(path):
    """加载 YAML 文件，优先用 pyyaml，降级到内置简单解析器。"""
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        return _parse_taxonomy_yaml_simple(path)


def _parse_taxonomy_yaml_simple(path):
    """简单 YAML 解析器（仅支持 risk-type-taxonomy.yaml 的嵌套列表格式）。

    解析逻辑：逐行读取，识别 slug/name/name_en/aliases 字段，返回与 pyyaml 兼容的结构。
    """
    import re
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    result = {"risk_types": {}}
    current_category = None
    current_item = {}
    in_aliases = False

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # 顶层 category key（如 injection:, frontend_security:）
        m_cat = re.match(r'^(\w+):\s*$', line.rstrip())
        if m_cat and not line.startswith(' '):
            current_category = m_cat.group(1)
            result["risk_types"][current_category] = {"types": []}
            in_aliases = False
            continue

        # 新列表项（- slug: "xxx"）
        m_slug = re.match(r'^\s+-\s+slug:\s*["\']?([^"\']+)["\']?\s*$', line)
        if m_slug:
            if current_item.get("slug") and current_category:
                result["risk_types"][current_category]["types"].append(current_item)
            current_item = {"slug": m_slug.group(1).strip()}
            in_aliases = False
            continue

        # name 字段
        m_name = re.match(r'^\s+name:\s*["\']?([^"\']+)["\']?\s*$', line)
        if m_name:
            current_item["name"] = m_name.group(1).strip()
            in_aliases = False
            continue

        # name_en 字段
        m_name_en = re.match(r'^\s+name_en:\s*["\']?([^"\']+)["\']?\s*$', line)
        if m_name_en:
            current_item["name_en"] = m_name_en.group(1).strip()
            in_aliases = False
            continue

        # aliases 字段（内联数组格式：aliases: ["a", "b", "c"]）
        m_al_inline = re.match(r'^\s+aliases:\s*\[(.+)\]\s*$', line)
        if m_al_inline:
            raw = m_al_inline.group(1)
            aliases = [k.strip().strip('"').strip("'") for k in raw.split(",")]
            current_item["aliases"] = [k for k in aliases if k]
            in_aliases = False
            continue

        # aliases 字段（多行列表格式：aliases:\n  - "a"\n  - "b"）
        m_al_start = re.match(r'^\s+aliases:\s*$', line)
        if m_al_start:
            current_item["aliases"] = []
            in_aliases = True
            continue

        # 多行 aliases 列表项
        if in_aliases:
            m_al_item = re.match(r'^\s+-\s*["\']?([^"\']+)["\']?\s*$', stripped)
            if m_al_item:
                current_item.setdefault("aliases", []).append(m_al_item.group(1).strip())
                continue
            else:
                in_aliases = False

    # 追加最后一个 item
    if current_item.get("slug") and current_category:
        result["risk_types"][current_category]["types"].append(current_item)

    return result


def _build_mappings_from_taxonomy(taxonomy_path):
    """从 taxonomy YAML 构建 slug↔中文名 双向映射。

    利用 name、name_en、aliases 字段构建完整的名称→slug 映射。
    返回 (slug_to_name, name_to_slug) 两个 dict。
    """
    slug_to_name = {}
    name_to_slug = {}

    data = _load_taxonomy_yaml(taxonomy_path)
    if not data:
        return slug_to_name, name_to_slug

    risk_types = data.get("risk_types", {})
    for _category_key, category_val in risk_types.items():
        if not isinstance(category_val, dict):
            continue
        types_list = category_val.get("types", [])
        if not isinstance(types_list, list):
            continue
        for item in types_list:
            slug = item.get("slug", "")
            name = item.get("name", "")
            if not slug:
                continue
            if name:
                slug_to_name[slug] = name
                name_to_slug[name] = slug
            # slug 自身也映射到自身（支持直接传入 slug 的精确匹配）
            name_to_slug[slug] = slug
            # name_en → slug
            name_en = item.get("name_en", "")
            if name_en:
                name_to_slug[name_en] = slug
                # 也注册小写形式
                name_to_slug[name_en.lower()] = slug
            # aliases 中的每个别名 → slug
            aliases = item.get("aliases", [])
            if isinstance(aliases, list):
                for alias in aliases:
                    if alias:
                        name_to_slug[alias] = slug

    return slug_to_name, name_to_slug


# 定位权威文件路径（相对于本脚本位置）
_TAXONOMY_PATH = Path(__file__).resolve().parent.parent / "resource" / "risk-type-taxonomy.yaml"

# 从 taxonomy 动态构建基础映射
_SLUG_DISPLAY_NAME_BASE, _NAME_TO_SLUG_BASE = _build_mappings_from_taxonomy(_TAXONOMY_PATH)

# ---------------------------------------------------------------------------
# 合并构建最终映射表
# ---------------------------------------------------------------------------

# slug → 标准中文显示名（权威来源：taxonomy YAML）
SLUG_DISPLAY_NAME = dict(_SLUG_DISPLAY_NAME_BASE)

# 风险类型名称/别名 → slug（全部来自 taxonomy YAML，单一数据源）
RISK_TYPE_SLUG = dict(_NAME_TO_SLUG_BASE)

# slug → 中文名 的反向映射（兜底）
SLUG_RISK_TYPE = {v: k for k, v in RISK_TYPE_SLUG.items()}


def normalize_risk_type(risk_type):
    """将 agent 产出的 riskType 归一化为标准中文显示名。

    流程：先通过 risk_type_to_slug() 归一化为 slug，
    再通过 SLUG_DISPLAY_NAME 反查标准中文名。
    若 slug 无对应中文名，返回 slug 本身。
    """
    slug = risk_type_to_slug(risk_type)
    return SLUG_DISPLAY_NAME.get(slug, slug)

# 语义分析 agent（需要检查 traceMethod）
SEMANTIC_AGENTS = {"vuln-scan", "logic-scan", "red-team"}

# 语义分析 agent 去重优先级（值越大越优先保留）
AGENT_PRIORITY = {
    "vuln-scan": 3,
    "logic-scan": 3,
    "red-team": 3,
    "light-inline": 2,
    "indexer-findings": 1,
    "pattern-matching": 0,
}


# ---------------------------------------------------------------------------
# attackChain 验证
# ---------------------------------------------------------------------------


def _is_valid_chain_node(node):
    """Check if a chain node (source/sink) is valid.

    Accepts two formats:
      - string: non-empty string (e.g. "src/routes.js:39")
      - object: dict with at least a 'file' key (e.g. {"file": "src/routes.js", "line": 39, "code": "..."})
    """
    if isinstance(node, str):
        return bool(node.strip())
    if isinstance(node, dict):
        return bool(node.get('file'))
    return False


def validate_attack_chain(chain):
    """Validate attackChain conforms to schema. Returns (valid, reason).

    source/sink accept both string and object {"file", "line", "code"} formats,
    since scanner produces structured objects while pattern-matching uses strings.
    """
    if not isinstance(chain, dict):
        return False, "attackChain is not a dict"
    source = chain.get('source')
    if not _is_valid_chain_node(source):
        return False, "missing or empty source"
    propagation = chain.get('propagation')
    if not isinstance(propagation, list):
        return False, "propagation is not a list"
    sink = chain.get('sink')
    if not _is_valid_chain_node(sink):
        return False, "missing or empty sink"
    trace = chain.get('traceMethod')
    if not trace or not isinstance(trace, str):
        return False, "missing traceMethod"
    return True, ""


# ---------------------------------------------------------------------------
# 日志工具
# ---------------------------------------------------------------------------

log_info, log_ok, log_warn, log_error = make_logger("merge")


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------

def _extract_scan_mode_from_batch_id(batch_id):
    """从 batch_id 推导扫描模式。

    batch_id 格式: {command}-{mode}-{timestamp}, 如 "project-deep-20260324152056"
    """
    if not batch_id:
        return 'unknown'
    parts = batch_id.split('-')
    known_modes = {'deep', 'light', 'fast'}
    if len(parts) >= 2 and parts[1] in known_modes:
        return parts[1]
    if len(parts) >= 1 and parts[0] in known_modes:
        return parts[0]
    return 'unknown'


# 风险编号前缀映射：命令 / 模式 → 单字母缩写
_RISK_ID_COMMAND_MAP = {'project': 'P', 'diff': 'D'}
_RISK_ID_MODE_MAP = {'light': 'L', 'deep': 'D', 'fast': 'F'}


def compute_risk_id_prefix(batch_name):
    """从批次目录名推导风险编号前缀（确定性）。

    目录名格式: {command}-{mode}-{timestamp}, 如 "project-light-20260623201219"
      - command: project→P, diff→D
      - mode:    light→L, deep→D, fast→F
      - timestamp: 原样保留（纯数字）

    返回示例: "PL20260623201219"
    无法解析（缺字段 / 未知命令或模式 / 时间戳非数字）时返回 None，
    调用方据此回退到旧的 'f-NNN' 编号格式。
    """
    if not batch_name:
        return None
    parts = batch_name.split('-')
    if len(parts) < 3:
        return None
    command, mode, timestamp = parts[0], parts[1], parts[2]
    cmd_abbr = _RISK_ID_COMMAND_MAP.get(command)
    mode_abbr = _RISK_ID_MODE_MAP.get(mode)
    if not cmd_abbr or not mode_abbr or not timestamp.isdigit():
        return None
    return f"{cmd_abbr}{mode_abbr}{timestamp}"


# diff-fixes 过滤容差：防御新增场景下 Sink 行号可能因代码增删而漂移
_DIFF_FIXES_LINE_TOLERANCE = 3


def _diff_range_consistent(diff_fixes_data, batch_path):
    """校验 diff-fixes.json 的 diff 范围与 batch-plan.json 的 diffRange 是否一致。

    避免 diff 范围参数注入不一致（fix_detector 用的范围 ≠ 本次扫描实际范围）
    导致过滤对错位置。

    Returns:
        (consistent: bool, reason: str)
        - batch-plan 无 diffRange（旧批次/向后兼容）→ (True, "")：正常过滤
        - 两者 base/head/mode/commit 任一实质不同 → (False, 说明)：跳过过滤
    """
    plan_path = batch_path / "batch-plan.json"
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception:
        return True, ""  # 无 batch-plan，向后兼容，不阻塞

    diff_range = plan.get("diffRange")
    if not diff_range or not isinstance(diff_range, dict):
        return True, ""  # 旧批次无 diffRange，向后兼容

    # 逐字段比对（空串视为未指定，不参与冲突判定）
    for key in ("base", "head", "mode", "commit"):
        plan_v = str(diff_range.get(key, "") or "")
        fix_v = str(diff_fixes_data.get(key, "") or "")
        if plan_v and fix_v and plan_v != fix_v:
            return False, f"{key}: batch-plan={plan_v!r} vs diff-fixes={fix_v!r}"
    return True, ""


def _apply_diff_fixes_filter(findings, diff_fixes_path, batch_path=None):
    """过滤掉本次 diff 已修复的 finding。

    匹配规则（任一命中即过滤）：
    1. 精确匹配 + ±3 行容差：finding 的 (filePath, lineNumber) 与 diff-fixes
       的 (filePath, lineNumber) 同文件且行号差 ≤3。
    2. 区间兜底匹配：finding 的 lineNumber 落在 diff-fixes 的
       [newRangeStart, newRangeEnd]（该 hunk 在新文件中的行号区间）内。
       此区间与 finding 同基准（新行号），消除 sink_removed 旧行号 vs
       finding 新行号的漂移问题。区间为空（纯删除 hunk）时自动失效。

    一致性校验：若提供 batch_path，先校验 diff-fixes 的 diff 范围与
    batch-plan.json 的 diffRange 一致；不一致则跳过过滤（安全优先，宁可
    保留 finding 不误过滤）。

    Args:
        findings: 已归一化的 finding 列表（filePath/lineNumber 为 camelCase）
        diff_fixes_path: diff-fixes.json 路径，不存在时原样返回
        batch_path: 批次目录 Path，用于读 batch-plan.json 做一致性校验（可选）

    Returns:
        过滤后的 findings 列表
    """
    try:
        data = json.loads(diff_fixes_path.read_text(encoding="utf-8"))
    except Exception:
        return findings

    # 一致性校验：diff 范围不一致时跳过过滤，避免过滤对错位置
    if batch_path is not None:
        consistent, reason = _diff_range_consistent(data, batch_path)
        if not consistent:
            log_info(f"diff 范围不一致，跳过 diff-fixes 过滤（{reason}）")
            return findings

    # (filePath, lineNumber) 精确/容差匹配集
    fixed_locations = []
    # (filePath, newRangeStart, newRangeEnd) 区间兜底匹配集
    fixed_ranges = []
    for loc in data.get("fixedSinkLocations", []):
        fp = loc.get("filePath", "")
        ln = int(loc.get("lineNumber", 0) or 0)
        if fp and ln > 0:
            fixed_locations.append((fp, ln))
        rs = int(loc.get("newRangeStart", 0) or 0)
        re_ = int(loc.get("newRangeEnd", 0) or 0)
        # 有效区间需 rs>0 且 re_>=rs（纯删除 hunk 区间为空，rs>re_，自动跳过）
        if fp and rs > 0 and re_ >= rs:
            fixed_ranges.append((fp, rs, re_))

    if not fixed_locations and not fixed_ranges:
        return findings

    filtered = []
    for f in findings:
        fp = f.get("filePath", "")
        ln = int(f.get("lineNumber", 0) or 0)
        # 匹配 1：精确 + ±3 行容差
        matched = any(
            fp == ffp and abs(ln - fln) <= _DIFF_FIXES_LINE_TOLERANCE
            for ffp, fln in fixed_locations
        )
        # 匹配 2：区间兜底（新行号落在 hunk 修改区间内）
        if not matched:
            matched = any(
                fp == rfp and rs <= ln <= re_
                for rfp, rs, re_ in fixed_ranges
            )
        if not matched:
            filtered.append(f)
    return filtered


_SELF_DECLARED_FIXED_MARKERS = (
    "此变更已修复",
    "本变更已修复",
    "当前变更已修复",
    "本 PR 已修复",
    "当前 PR 已修复",
    "此 PR 已修复",
    "已修复该漏洞",
    "已修复此漏洞",
    "无需额外处理",
    "无需处理",
    "no further action",
    "already fixed by this change",
    "fixed by this change",
    "fixed in this change",
)

_CURRENT_CHANGE_MARKERS = (
    "此变更",
    "本变更",
    "当前变更",
    "本次变更",
    "本次修改",
    "本次改动",
    "本次提交",
    "本次 PR",
    "本次 pr",
    "本 PR",
    "当前 PR",
    "此 PR",
    "this change",
    "current change",
    "this modification",
    "this commit",
    "this pr",
    "current pr",
    "pull request",
)

_FIXED_MARKERS = (
    "已修复",
    "已得到修复",
    "得到修复",
    "已被修复",
    "修复该漏洞",
    "修复此漏洞",
    "修复该问题",
    "修复此问题",
    "消除了此风险",
    "消除该风险",
    "消除风险",
    "不再存在",
    "已不存在",
    "fixed",
    "remediated",
    "resolved",
    "no longer",
)


def _load_batch_plan(batch_path):
    """加载 batch-plan.json，失败返回空 dict。"""
    plan = load_json_file(Path(batch_path) / "batch-plan.json")
    return plan if isinstance(plan, dict) else {}


def _is_diff_batch(batch_path):
    """判断当前批次是否为 diff 扫描。

    diff 修复型 finding 过滤只允许在增量扫描中生效。project 扫描没有
    "本次变更"语义，不能仅凭 recommendation 文案删除风险。
    """
    batch_path = Path(batch_path)
    plan = _load_batch_plan(batch_path)
    command = str(
        plan.get("scan_command")
        or plan.get("scanCommand")
        or plan.get("command")
        or ""
    ).strip().lower()
    if command == "diff":
        return True
    if isinstance(plan.get("diffRange"), dict):
        return True
    return batch_path.name.startswith("diff-")


def _self_declares_fixed_by_current_diff(finding):
    """识别 finding 自身已声明"当前变更已修复，无需处理"的自相矛盾结果。

    这类 finding 不应作为待处理风险进入最终报告。规则刻意保守：
    - 命中明确短语直接成立；
    - 或同时出现"当前变更/PR"语义和"已修复/消除风险"语义。
    """
    fields = (
        finding.get("recommendation", ""),
        finding.get("description", ""),
        finding.get("riskDetail", ""),
        finding.get("attackScenario", ""),
    )
    text = " ".join(str(v or "") for v in fields).strip()
    if not text:
        return False
    folded = " ".join(text.lower().split())
    if any(marker.lower() in folded for marker in _SELF_DECLARED_FIXED_MARKERS):
        return True
    has_current_change = any(marker.lower() in folded for marker in _CURRENT_CHANGE_MARKERS)
    has_fixed = any(marker.lower() in folded for marker in _FIXED_MARKERS)
    return has_current_change and has_fixed


def _apply_diff_remediation_filter(findings, batch_path):
    """过滤 diff 批次中自声明已由当前变更修复的 findings。

    Returns:
        (kept_findings, removed_findings)
    """
    if not _is_diff_batch(batch_path):
        return findings, []

    kept = []
    removed = []
    for f in findings:
        if _self_declares_fixed_by_current_diff(f):
            removed_item = dict(f)
            removed_item["_removed_by"] = "diff-remediation:self-declared-fixed"
            removed_item["_removedReason"] = "finding states current diff already fixed the vulnerability"
            removed.append(removed_item)
        else:
            kept.append(f)
    return kept, removed


def _write_remediated_findings(batch_path, removed_findings, stage):
    """写入被 diff remediation gate 移除的 finding，保留审计证据。"""
    if not removed_findings:
        return
    batch_path = Path(batch_path)
    out_path = batch_path / "remediated-findings.json"
    existing = load_json_file(out_path)
    existing_items = []
    if isinstance(existing, dict) and isinstance(existing.get("findings"), list):
        existing_items = existing.get("findings", [])
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "count": len(existing_items) + len(removed_findings),
        "findings": existing_items + removed_findings,
    }
    write_json_file(out_path, payload)


def assign_finding_ids(findings, batch_name):
    """为 findings 统一分配确定性风险编号（findingId）。

    新格式: {prefix}-{NNN}，prefix 由 compute_risk_id_prefix 推导，
    序号从 000 起按列表顺序递增（3 位补零），如 "PL20260623201219-000"。
    当目录名无法解析时回退旧格式 "f-NNN"（序号从 001 起）以保证向后兼容。
    """
    prefix = compute_risk_id_prefix(batch_name)
    if prefix:
        for i, f in enumerate(findings):
            f['findingId'] = f"{prefix}-{i:03d}"
    else:
        log_warn(f"无法从批次目录名 '{batch_name}' 推导风险编号前缀，回退 'f-NNN' 格式")
        for i, f in enumerate(findings, 1):
            f['findingId'] = f"f-{i:03d}"


def normalize_severity(level):
    """标准化风险等级为 critical/high/medium/low 四级"""
    if not level:
        return ""
    level_lower = str(level).lower().strip()
    if level_lower in ('critical', '严重'):
        return 'critical'
    elif level_lower in ('high', '高'):
        return 'high'
    elif level_lower in ('medium', 'moderate', '中', '中等'):
        return 'medium'
    elif level_lower in ('low', '低'):
        return 'low'
    return level_lower


def normalized_severity_rank(sev):
    """获取严重性排序值（高值优先），先标准化再排序"""
    return SEVERITY_ORDER.get(normalize_severity(sev), 0)


def lower_severity(sev):
    """降低一级严重性"""
    s = normalize_severity(sev)
    if s == 'critical':
        return 'high'
    elif s == 'high':
        return 'medium'
    elif s == 'medium':
        return 'low'
    return 'low'


def raise_severity(sev):
    """提升一级严重性"""
    s = normalize_severity(sev)
    if s == 'low':
        return 'medium'
    elif s == 'medium':
        return 'high'
    elif s == 'high':
        return 'critical'
    return 'critical'


def group_findings_by_file(findings):
    """按文件路径分组 findings"""
    by_file = {}
    for f in findings:
        fp = f.get('filePath', '')
        if fp:
            by_file.setdefault(fp, []).append(f)
    return by_file


def detect_vulnerability_chains(findings):
    """标记潜在漏洞链候选：同一文件存在 ≥2 个不同类型的漏洞时，标记为链候选。
    返回 chain_candidates 列表，每项包含 file、findingIds、riskTypes。
    """
    by_file = group_findings_by_file(findings)
    chain_candidates = []
    for file_path, file_findings in by_file.items():
        risk_types = set(f.get('riskType', '') for f in file_findings)
        if len(file_findings) >= 2 and len(risk_types) >= 2:
            chain_candidates.append({
                "file": file_path,
                "findingIds": [f.get('findingId', '') for f in file_findings],
                "riskTypes": list(risk_types),
            })
    return chain_candidates


def risk_type_to_slug(risk_type):
    """将风险类型转换为 slug。

    匹配策略（按优先级）：
      1. 精确匹配 RISK_TYPE_SLUG
      2. 大小写无关精确匹配
      3. 截取 " — " / " - " 前缀后重新匹配（处理描述性 riskType）
      4. 关键词包含匹配（riskType 包含某个已知 key）
      5. 自动生成 slug（兜底）
    """
    if not risk_type:
        return "unknown"
    # 1. 精确匹配
    slug = RISK_TYPE_SLUG.get(risk_type)
    if slug:
        return slug
    # 2. 大小写无关精确匹配
    rt_lower = risk_type.lower().strip()
    for cn, sl in RISK_TYPE_SLUG.items():
        if rt_lower == cn.lower() or rt_lower == sl:
            return sl
    # 3. 截取分隔符各段后重新匹配（scanner 常见格式："IDOR — 水平越权查看..."、"密钥管理 / 硬编码敏感信息"）
    for sep in (' — ', ' - ', '（', '—', ' / ', '／'):
        if sep in risk_type:
            parts = [p.strip() for p in risk_type.split(sep) if p.strip()]
            # 对每个段尝试精确匹配和大小写无关匹配
            for part in parts:
                slug = RISK_TYPE_SLUG.get(part)
                if slug:
                    return slug
                part_lower = part.lower()
                for cn, sl in RISK_TYPE_SLUG.items():
                    if part_lower == cn.lower() or part_lower == sl:
                        return sl
            # 对每个段尝试关键词包含匹配（段中包含某个已知 key）
            for part in parts:
                for cn, sl in RISK_TYPE_SLUG.items():
                    if len(cn) >= 2 and cn in part:
                        return sl
    # 4. 关键词包含匹配（riskType 中包含已知关键词）
    for cn, sl in RISK_TYPE_SLUG.items():
        if len(cn) >= 2 and cn in risk_type:
            return sl
    # 5. 自动生成 slug（兜底）
    return rt_lower.replace(' ', '-').replace('_', '-')


# ---------------------------------------------------------------------------
# 阶段 2 合并逻辑
# ---------------------------------------------------------------------------

def extract_findings_from_agent(data, agent_name):
    """从 agent 输出中提取 findings 列表并标记来源。

    当 finding 包含 affectedFiles[] 时，为每个 affected file 自动生成
    一个派生 finding（继承 riskType、severity、attackChain 等字段，
    但 filePath 和 lineNumber 更新为 affected file 的信息）。
    """
    if data is None:
        return []

    findings = []
    # 兼容裸数组 [...] 和对象 {"findings": [...]} 两种格式
    if isinstance(data, list):
        raw_findings = data
    else:
        raw_findings = data.get('findings', [])

    for f in raw_findings:
        # 使用集中归一化函数统一字段名
        normalized = normalize_finding(f, source_agent=agent_name)

        findings.append(normalized)

        # --- affectedFiles 自动展开 ---
        affected_files = f.get('affectedFiles', [])
        if isinstance(affected_files, list) and affected_files:
            parent_file = normalized['filePath']
            for af in affected_files:
                af_path = af if isinstance(af, str) else (af.get('filePath') or '')
                af_line = 0 if isinstance(af, str) else (af.get('lineNumber') or 0)
                if not af_path or af_path == parent_file:
                    continue  # 跳过空路径或与父 finding 相同的文件
                derived = dict(normalized)
                derived['filePath'] = af_path
                derived['lineNumber'] = int(af_line) if af_line else 1
                derived['_derivedFrom'] = normalized.get('filePath', '')
                derived['_derivedFromLine'] = normalized.get('lineNumber', 0)
                # 移除原始的 affectedFiles，避免派生 finding 再次被展开
                derived.pop('affectedFiles', None)
                # description 标记为派生
                parent_detail = normalized.get('description', '')
                derived['description'] = f"[同类漏洞，派生自 {parent_file}] {parent_detail}"
                findings.append(derived)
            log_info(f"  affectedFiles 展开：{parent_file} → {len(affected_files)} 个派生 finding")

    return findings


def extract_findings_from_pattern_scan(data):
    """从 pattern-scan-results.json 提取 findings（只支持 camelCase）"""
    if data is None:
        return []

    findings = []

    # 提取 cveFindings
    for f in data.get('cveFindings', []):
        # pattern-matching 内部使用专用字段（dependencyFile / declarationLine /
        # component / version / cve），这些不在 LegacyFieldError 黑名单里。
        # 这里直接映射到规范 finding 字段，所有"代码侧"字段一律 camelCase。
        dependency_file = (
            f.get('dependencyFile') or f.get('manifestFile') or
            f.get('declFile') or f.get('filePath') or ''
        )
        line_number = (
            f.get('declarationLine') or f.get('lineNumber') or 1
        )
        component = f.get('component') or f.get('package') or ''
        version = f.get('currentVersion') or f.get('version') or ''
        cve = f.get('cve') or f.get('advisoryId') or ''
        risk_code = f.get('riskCode') or ''
        if not risk_code and component:
            risk_code = f"{component}:{version}" if version else component
        desc = f.get('description') or ''
        if not desc and component:
            parts = [component]
            if version:
                parts.append(version)
            if cve:
                parts.append(cve)
            desc = " / ".join(parts)

        raw_finding = dict(f)
        # 移除 pattern-matching 自有的非规范字段（避免 normalize_finding fail-fast）
        for legacy_in in ('declFile', 'declarationLine', 'package', 'version',
                          'advisoryId'):
            raw_finding.pop(legacy_in, None)
        raw_finding.update({
            'filePath': dependency_file,
            'lineNumber': int(line_number),
            'riskType': f.get('riskType') or '高危组件漏洞',
            'severity': f.get('severity') or 'medium',
            'riskCode': risk_code,
            'description': desc,
        })
        findings.append(normalize_finding(raw_finding, source_agent='pattern-matching'))

    # 提取 configFindings
    for f in data.get('configFindings', []):
        raw_finding = dict(f)
        # configFindings 常用 'pattern' 表征命中规则，保留为业务字段；
        # 仅在缺 riskType 时用 pattern 兜底
        if not raw_finding.get('riskType'):
            raw_finding['riskType'] = f.get('pattern') or ''
        findings.append(normalize_finding(raw_finding, source_agent='pattern-matching'))

    # 提取 findings（通用数组，部分 pattern-matching 直接用这个字段）
    for f in data.get('findings', []):
        findings.append(normalize_finding(f, source_agent='pattern-matching'))

    return findings


def validate_finding(finding):
    """[deprecated] v2 已被 validate_finding_schema 取代；保留作为外部脚本回退入口。"""
    return validate_finding_schema(finding)


# --- v2 严格 schema 校验：fail-fast 拒绝任何使用旧字段名的 finding ---
# 设计原则：
#   - 不再做任何字段别名翻译（取消 _FIELD_ALIASES / normalize_finding_schema）
#   - 出现旧字段名（FilePath/RiskCode/...）一律抛 LegacyFieldError
#   - 由 stage2 主流程捕获并把违规 finding 写入 schema-violations.json，再 fail-fast 终止
#   - 详细旧字段→规范字段映射见 _common.py:_LEGACY_FIELD_HINTS

def _safe_extract(extractor, data, agent_name, violations):
    """以 fail-fast 模式调用 extractor。

    - 命中 LegacyFieldError 时把违规信息追加到 violations 列表（不抛出，
      由主流程在所有 agent 加载完后统一汇总并终止）
    - extractor 内部其他异常（数据格式异常等）原样抛出
    """
    try:
        if extractor is extract_findings_from_pattern_scan:
            return extractor(data)
        return extractor(data, agent_name)
    except LegacyFieldError as e:
        violations.append({'agent': agent_name, 'error': str(e)})
        return []


def validate_finding_schema(finding):
    """对单条 finding 做 v2 严格 schema 校验。

    校验项：
      1. 顶层 key 不得包含任何旧字段名（PascalCase / snake_case / 已废弃别名）
      2. 必填核心字段非空：filePath, lineNumber, riskType, severity

    Returns:
        (ok, reason_or_legacy_field): ok=True 时 reason 为空字符串
    """
    if not isinstance(finding, dict):
        return False, "finding is not a dict"
    if not finding.get('filePath'):
        return False, "missing filePath"
    if not finding.get('lineNumber'):
        return False, "missing lineNumber"
    if not finding.get('riskType'):
        return False, "missing riskType"
    if not finding.get('severity'):
        return False, "missing severity"
    return True, ""


def dedup_key(finding):
    """生成去重键（riskType 归一化为 slug 后再去重）"""
    return (
        str(finding.get('filePath', '')),
        int(finding.get('lineNumber', 0)),
        risk_type_to_slug(finding.get('riskType', '')),
    )


def _load_agent_findings_if_fresh(agent_file, session, agent_name, stale_records):
    """加载并校验 agent 产物的新鲜度。

    返回 (data, status):
        data 为 None 表示未加载（不存在 / 损坏 / 陈旧 / 会话缺失）
        status ∈ {'missing', 'stale', 'ok'}：missing/stale 会写入 stale_records
    """
    p = Path(agent_file)
    if not p.is_file():
        return None, 'missing'
    if session is None:
        # 无会话锁视为兼容模式：保留旧行为，但仍按时间记录方便排查
        data = load_json_file(p)
        return data, 'ok' if data is not None else 'missing'
    if not is_output_fresh(p, session):
        try:
            mtime = p.stat().st_mtime
        except OSError:
            mtime = None
        stale_records.append({
            'agent': agent_name,
            'path': str(p),
            'mtime': mtime,
            'sessionStartedAt': session_started_at(session),
        })
        return None, 'stale'
    data = load_json_file(p)
    if data is None:
        return None, 'missing'
    return data, 'ok'


def merge_stage2(batch_dir, prefix='', output_path=None, extra_agents=''):
    """执行阶段 2 合并。

    v3.2.0 架构：通过 --extra-agents 加载各 agent 产物（vuln-scan, logic-scan, red-team 等）。
    兼容模式：如果存在旧版 scanner.json / pattern-scan-results.json 也会加载。

    extra_agents: 逗号分隔的 agent 名称（如 'indexer-findings,vuln-scan,logic-scan,red-team'），
                  这是 v3.2.0 主要的 agent 产物加载方式。也支持续扫实例如 'vuln-scan-cont'。
    """
    batch_path = Path(batch_dir)
    agents_dir = batch_path / 'agents'

    # 加载会话锁，用于校验产物新鲜度（防止陈旧 agent 产物污染本次 merge）
    session = load_scan_session(batch_path)
    if session is None:
        log_warn(
            "未找到 .scan-session.json，无法判定产物新鲜度，按兼容模式加载所有产物。"
            "建议编排器在扫描启动前调用 orchestration_helper begin-session 写入会话锁。"
        )
    else:
        log_info(
            f"会话: runId={session.get('runId', '?')} startedAt={session.get('startedAtIso', '?')}"
        )

    all_findings = []
    loaded_agents = []
    stale_agents = []  # 因 mtime 早于会话开始时间而被拒绝的 agent
    schema_violations = []  # v2: 命中旧字段名的 agent 产物（fail-fast 触发器）
    current_pipeline_loaded = False

    # --- 主要加载路径：--extra-agents 指定的 agent 产物 ---
    if extra_agents:
        for agent_name in extra_agents.split(','):
            agent_name = agent_name.strip()
            if not agent_name:
                continue
            # pattern-matching 使用专用加载函数
            if agent_name == 'pattern-matching':
                ps_path = batch_path / f'{prefix}pattern-scan-results.json'
                ps_data, ps_status = _load_agent_findings_if_fresh(
                    ps_path, session, 'pattern-matching', stale_agents
                )
                if ps_data is not None:
                    findings = _safe_extract(
                        extract_findings_from_pattern_scan, ps_data,
                        'pattern-matching', schema_violations
                    )
                    all_findings.extend(findings)
                    loaded_agents.append('pattern-matching')
                    current_pipeline_loaded = True
                    log_info(f"pattern-matching: {len(findings)} findings")
                elif ps_status == 'stale':
                    log_warn(
                        f"pattern-matching 产物 {ps_path.name} 早于本次会话，已拒绝加载（陈旧数据保护）"
                    )
                else:
                    log_warn(f"{prefix}pattern-scan-results.json 不存在或为空，跳过")
                continue
            # 避免重复加载
            if agent_name in loaded_agents:
                log_warn(f"跳过重复的 agent: {agent_name}")
                continue
            # indexer-findings 使用 batch 根目录
            if agent_name == 'indexer-findings':
                agent_file = batch_path / f'{prefix}{agent_name}.json'
            else:
                agent_file = agents_dir / f'{prefix}{agent_name}.json'
            agent_data, status = _load_agent_findings_if_fresh(
                agent_file, session, agent_name, stale_agents
            )
            # 兼容 fork agent 输出的 {agent}-findings.json 文件名
            if agent_data is None and status != 'stale':
                alt_file = agents_dir / f'{prefix}{agent_name}-findings.json'
                agent_data, alt_status = _load_agent_findings_if_fresh(
                    alt_file, session, f'{agent_name}-findings', stale_agents
                )
                status = alt_status if agent_data is None else 'ok'
            if agent_data is not None:
                findings = _safe_extract(
                    extract_findings_from_agent, agent_data, agent_name, schema_violations
                )
                all_findings.extend(findings)
                loaded_agents.append(agent_name)
                current_pipeline_loaded = True
                log_info(f"{agent_name}: {len(findings)} findings")
            elif status == 'stale':
                log_warn(
                    f"{agent_name} 产物 {agent_file.name} 早于本次会话，已拒绝加载（陈旧数据保护）"
                )
            else:
                log_warn(f"{agent_name}.json 不存在或为空，跳过")

    # --- 兼容加载：旧版 pattern-scan-results.json（如果尚未通过 extra-agents 加载）---
    if 'pattern-matching' not in loaded_agents:
        ps_path = batch_path / f'{prefix}pattern-scan-results.json'
        pattern_data, ps_status = _load_agent_findings_if_fresh(
            ps_path, session, 'pattern-matching', stale_agents
        )
        if pattern_data is not None:
            findings = _safe_extract(
                extract_findings_from_pattern_scan, pattern_data,
                'pattern-matching', schema_violations
            )
            all_findings.extend(findings)
            loaded_agents.append('pattern-matching')
            current_pipeline_loaded = True
            log_info(f"pattern-matching (兼容加载): {len(findings)} findings")
        elif ps_status == 'stale':
            log_warn("pattern-matching 兼容加载产物早于本次会话，已拒绝")

    # --- 兼容加载：旧版 scanner.json（如果尚未通过 extra-agents 加载）---
    if 'scanner' not in loaded_agents:
        sc_path = agents_dir / f'{prefix}scanner.json'
        scanner_data, sc_status = _load_agent_findings_if_fresh(
            sc_path, session, 'scanner', stale_agents
        )
        if scanner_data is not None:
            findings = _safe_extract(
                extract_findings_from_agent, scanner_data, 'scanner', schema_violations
            )
            all_findings.extend(findings)
            loaded_agents.append('scanner')
            current_pipeline_loaded = True
            log_info(f"scanner (兼容加载): {len(findings)} findings")
        elif sc_status == 'stale':
            log_warn("scanner 兼容加载产物早于本次会话，已拒绝")

    # --- 兼容加载：light-scan.json（Light 模式编排器未传 --extra-agents 时的防御性兜底）---
    if 'light-scan' not in loaded_agents:
        ls_path = agents_dir / f'{prefix}light-scan.json'
        light_data, ls_status = _load_agent_findings_if_fresh(
            ls_path, session, 'light-scan', stale_agents
        )
        # 兼容 fork agent 输出的 light-scan-findings.json 文件名
        if light_data is None and ls_status != 'stale':
            alt_ls = agents_dir / f'{prefix}light-scan-findings.json'
            light_data, ls_status = _load_agent_findings_if_fresh(
                alt_ls, session, 'light-scan-findings', stale_agents
            )
        if light_data is not None:
            findings = _safe_extract(
                extract_findings_from_agent, light_data, 'light-scan', schema_violations
            )
            all_findings.extend(findings)
            loaded_agents.append('light-scan')
            current_pipeline_loaded = True
            log_info(f"light-scan (兼容加载): {len(findings)} findings")
        elif ls_status == 'stale':
            log_warn("light-scan 兼容加载产物早于本次会话，已拒绝")

    if stale_agents:
        log_warn(
            f"陈旧数据保护：拒绝了 {len(stale_agents)} 个早于本次会话的 agent 产物 — "
            f"{[s['agent'] for s in stale_agents]}"
        )

    # --- v2 fail-fast：任意 agent 产物含旧字段名都立即终止 ---
    if schema_violations:
        violations_path = batch_path / f'{prefix}schema-violations.json'
        write_json_file(violations_path, {
            'reportedAt': datetime.now(timezone.utc).isoformat(),
            'count': len(schema_violations),
            'violations': schema_violations,
        })
        for v in schema_violations:
            log_error(f"[schema-violation] {v['agent']}: {v['error']}")
        log_error(
            f"检测到 {len(schema_violations)} 个 agent 产物使用了已废弃字段名。"
            f"v2 严格 schema 模式禁止任何回退/兼容字段，请修复 agent 输出后重试。"
            f"详情见 {violations_path}"
        )
        stdout_json({
            "status": "error",
            "reason": "legacy_field_in_agent_output",
            "violationCount": len(schema_violations),
            "violationsFile": str(violations_path.name),
        })
        sys.exit(2)

    log_info(f"合计加载 {len(all_findings)} 个原始 findings (来自 {len(loaded_agents)} 个 agent)")

    # 格式校验（v2：仅做必填字段校验，不做字段别名归一化——已在 normalize_finding 阶段 fail-fast）
    valid_findings = []
    discarded_count = 0
    discarded_by_agent = {}
    discarded_findings = []
    for f in all_findings:
        valid, reason = validate_finding_schema(f)
        if valid:
            valid_findings.append(f)
        else:
            discarded_count += 1
            agent = f.get('sourceAgent', 'unknown')
            discarded_by_agent[agent] = discarded_by_agent.get(agent, 0) + 1
            discarded_findings.append({
                'filePath': f.get('filePath', '?'),
                'lineNumber': f.get('lineNumber', '?'),
                'riskType': f.get('riskType', '?'),
                'sourceAgent': agent,
                'discardReason': reason,
            })
            log_warn(
                f"丢弃不完整 finding: {reason} — "
                f"agent={agent} file={f.get('filePath', '?')}:{f.get('lineNumber', '?')} "
                f"riskType={f.get('riskType', '?')}"
            )

    if discarded_count > 0:
        log_warn(f"共丢弃 {discarded_count} 个格式不完整的 finding")
        for agent, cnt in sorted(discarded_by_agent.items(), key=lambda x: -x[1]):
            log_warn(f"  {agent}: {cnt} 个丢弃")
        # 写入丢弃记录供调试
        discard_log_path = batch_path / f'{prefix}discarded-findings.json'
        write_json_file(discard_log_path, {
            'discardedCount': discarded_count,
            'byAgent': discarded_by_agent,
            'findings': discarded_findings,
        })
        log_info(f"丢弃记录已写入 {discard_log_path}")

    # traceMethod 检查（仅语义分析 agent）
    trace_fixed = 0
    for f in valid_findings:
        if f.get('sourceAgent') in SEMANTIC_AGENTS:
            if not f.get('traceMethod') and not f.get('attackChain', {}).get('traceMethod'):
                # 语义分析 agent 默认使用 Grep+Read
                f['traceMethod'] = 'Grep+Read'
                trace_fixed += 1
    if trace_fixed > 0:
        log_warn(f"为 {trace_fixed} 个语义分析 finding 补充 traceMethod（按 agent 类型推断）")

    # attackChain 合约校验（仅语义分析 agent）
    chain_invalid = 0
    for f in valid_findings:
        if f.get('sourceAgent') in SEMANTIC_AGENTS:
            chain = f.get('attackChain')
            if chain:
                ok, reason = validate_attack_chain(chain)
                if not ok:
                    chain_invalid += 1
                    log_warn(
                        f"attackChain 不合规 ({reason}): "
                        f"{f.get('filePath', '?')}:{f.get('lineNumber', '?')} [{f.get('riskType', '?')}]"
                    )
                    # 标记为不完整，供 finding-validator 识别并执行完整追踪
                    f.setdefault('_chainIncomplete', True)
    if chain_invalid > 0:
        log_warn(f"共 {chain_invalid} 个语义分析 finding 的 attackChain 不符合合约")

    # 去重（按 file+line+riskType，语义分析优先 > 最高 severity）
    dedup_groups = {}
    for f in valid_findings:
        key = dedup_key(f)
        if key in dedup_groups:
            existing = dedup_groups[key]
            existing_sev = normalized_severity_rank(existing['severity'])
            new_sev = normalized_severity_rank(f['severity'])
            existing_prio = AGENT_PRIORITY.get(existing.get('sourceAgent', ''), 0)
            new_prio = AGENT_PRIORITY.get(f.get('sourceAgent', ''), 0)
            # 优先保留规则：
            # 1. 如果 severity 不同，保留更高 severity 的
            # 2. 如果 severity 相同，保留语义分析 agent 优先级更高的
            if new_sev > existing_sev:
                dedup_groups[key] = f
            elif new_sev == existing_sev and new_prio > existing_prio:
                dedup_groups[key] = f
        else:
            dedup_groups[key] = f

    deduplicated_count = len(valid_findings) - len(dedup_groups)
    merged_findings = list(dedup_groups.values())

    if deduplicated_count > 0:
        log_info(f"去重移除 {deduplicated_count} 个重复 finding")

    # --- 文件存在性全量网关（反幻觉硬门禁）---
    # 对所有 findings 做 file_exists 检查，移除指向不存在文件的幽灵 finding。
    # 这是代码级确定性逻辑，不依赖 prompt 层的反幻觉合约。
    ghost_count = 0
    for f in merged_findings:
        fp = f.get('filePath', '')
        if fp and not Path(fp).is_file():
            f['_ghost'] = True
            ghost_count += 1

    if ghost_count > 0:
        ghost_rate = ghost_count / len(merged_findings) if merged_findings else 0
        log_warn(f"文件存在性网关：检测到 {ghost_count} 个 finding 指向不存在的文件（{ghost_rate:.0%}）")
        if ghost_rate > 0.5:
            log_error(f"幽灵率 {ghost_rate:.0%} 超过 50%，审计质量堪忧，请检查 Agent 输出")
        merged_findings = [f for f in merged_findings if not f.get('_ghost')]
        log_info(f"文件存在性网关移除 {ghost_count} 个幽灵 finding，剩余 {len(merged_findings)} 个")

    # --- diff-fixes 过滤（仅 diff 模式生效）---
    # 过滤掉"已被本次 diff 修复"的 finding，避免把修复型变更误报为风险。
    # diff-fixes.json 由 scripts/fix_detector.py 在探索阶段产出，project 模式无此文件。
    diff_fixes_path = batch_path / "diff-fixes.json"
    if diff_fixes_path.exists():
        before_fix_filter = len(merged_findings)
        merged_findings = _apply_diff_fixes_filter(merged_findings, diff_fixes_path, batch_path)
        removed_by_fix = before_fix_filter - len(merged_findings)
        if removed_by_fix > 0:
            log_info(f"diff-fixes 过滤移除 {removed_by_fix} 个已被本次 diff 修复的 finding，剩余 {len(merged_findings)} 个")

    # --- diff remediation gate（仅 diff 模式生效）---
    # 兜底处理 agent 自身已经声明"此变更已修复/无需额外处理"却仍作为风险输出的结果。
    merged_findings, remediated_findings = _apply_diff_remediation_filter(merged_findings, batch_path)
    if remediated_findings:
        _write_remediated_findings(batch_path, remediated_findings, "merge-scan")
        log_info(
            f"diff remediation gate 移除 {len(remediated_findings)} 个当前变更已修复的 finding，"
            f"剩余 {len(merged_findings)} 个"
        )

    # 分配统一的风险编号 findingId（确定性脚本生成）。
    # 格式: {prefix}-{NNN}，prefix 由批次目录名推导（如 PL20260623201219-000）。
    # 无论 Light / Deep / Fast 模式，都走同一确定性逻辑。
    assign_finding_ids(merged_findings, batch_path.name)

    # 统计
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_risk_type = {}
    for f in merged_findings:
        sev = normalize_severity(f['severity'])
        by_severity[sev] = by_severity.get(sev, 0) + 1
        # 归一化 riskType：回写标准中文名到 finding 本体
        f['riskType'] = normalize_risk_type(f['riskType'])
        slug = risk_type_to_slug(f['riskType'])
        by_risk_type[slug] = by_risk_type.get(slug, 0) + 1

    # 写入 merged-scan.json
    output_data = {
        "mergedAt": datetime.now(timezone.utc).isoformat(),
        "totalFindings": len(merged_findings),
        "byRiskType": by_risk_type,
        "bySeverity": by_severity,
        "deduplicatedCount": deduplicated_count,
        "discardedCount": discarded_count,
        "loadedAgents": loaded_agents,
        "staleAgents": stale_agents,
        "session": {
            "runId": (session or {}).get("runId"),
            "startedAt": session_started_at(session),
            "startedAtIso": (session or {}).get("startedAtIso"),
        } if session else None,
        "findings": merged_findings,
    }
    out_file = output_path or (batch_path / f'{prefix}merged-scan.json')
    write_json_file(out_file, output_data)
    log_ok(f"已写入 {out_file} ({len(merged_findings)} findings)")

    # 漏洞链检测
    chain_candidates = detect_vulnerability_chains(merged_findings)
    if chain_candidates:
        log_info(f"检测到 {len(chain_candidates)} 个潜在漏洞链候选")
        output_data["chainCandidates"] = chain_candidates

    # stdout 摘要
    stdout_json({
        "status": "ok",
        "totalFindings": len(merged_findings),
        "criticalCount": by_severity.get("critical", 0),
        "bySeverity": by_severity,
        "byRiskType": by_risk_type,
        "deduplicatedCount": deduplicated_count,
        "discardedCount": discarded_count,
        "ghostRemovedCount": ghost_count,
        "chainCandidates": len(chain_candidates),
        "outputFile": str(out_file.name),
        "staleAgentCount": len(stale_agents),
        "runId": (session or {}).get("runId"),
    })


# ---------------------------------------------------------------------------
# 阶段 3 合并逻辑
# ---------------------------------------------------------------------------

def build_finding_index(findings):
    """构建 finding 索引（findingId → finding, file+line+riskType → finding）"""
    by_id = {}
    by_key = {}
    for f in findings:
        fid = f.get('findingId')
        if fid:
            by_id[fid] = f
        key = dedup_key(f)
        by_key[key] = f
    return by_id, by_key


def match_finding(by_id, by_key, ref):
    """匹配 finding：先按 findingId（带文件一致性校验），再按 filePath+lineNumber+riskType。

    v2: ref 必须使用规范 camelCase 字段名。
    """
    ref_file = ref.get('filePath') or ''

    # 尝试 findingId（需校验文件路径一致性，防止重新编号后错配）
    fid = ref.get('findingId')
    if fid and fid in by_id:
        candidate = by_id[fid]
        candidate_file = candidate.get('filePath', '')
        if not ref_file or not candidate_file or ref_file == candidate_file:
            return candidate
        # findingId 匹配但文件不一致，说明 findingId 已重新编号，回退到 key 匹配

    # 尝试 filePath+lineNumber+riskType
    line_val = ref.get('lineNumber') or 0
    rt_val = ref.get('riskType') or ''
    key = (str(ref_file), int(line_val), risk_type_to_slug(str(rt_val)))
    if key in by_key:
        return by_key[key]

    # 最后尝试仅按文件路径匹配（当 lineNumber/riskType 不可用时）
    if ref_file and not line_val and not rt_val:
        for f in by_id.values():
            f_file = f.get('filePath', '')
            if f_file == ref_file:
                return f
    return None


def _set_confidence_cap(finding, cap):
    current = finding.get('confidence') or 0
    try:
        current = int(current)
    except (TypeError, ValueError):
        current = 0
    if current <= 0:
        current = 90
    new_confidence = min(current, cap)
    finding['confidence'] = new_confidence


def _has_fast_plus_targets(findings):
    return any(normalize_severity(f.get('severity', '')) in ('critical', 'high') for f in findings)


def _apply_challenge_severity_corrections(findings, challenge_data):
    """将 challenge-results.json 中的 severityCorrection 回写到 findings。

    Fast bypass 会在没有 verifier 产出的情况下提前 return，若不在 return 之前
    显式应用这些修正，Fast+ challenge 产出的严重级别下调会丢失。
    """
    if not challenge_data:
        return 0

    challenge_results = challenge_data.get('results', [])
    if not challenge_results:
        return 0

    ch_by_id = {}
    ch_by_key = {}
    for cr in challenge_results:
        fid = cr.get('findingId', '')
        if fid:
            ch_by_id[fid] = cr
        fp = str(cr.get('filePath', ''))
        ln = int(cr.get('lineNumber', 0))
        rt = risk_type_to_slug(cr.get('riskType', ''))
        ch_by_key[(fp, ln, rt)] = cr

    severity_corrected_applied = 0
    for f in findings:
        if f.get('_removed'):
            continue
        fid = f.get('findingId', '')
        ch_record = ch_by_id.get(fid)
        if not ch_record:
            key = dedup_key(f)
            ch_record = ch_by_key.get(key)
        if not ch_record:
            continue

        sev_correction = ch_record.get('severityCorrection')
        if sev_correction and sev_correction.get('to'):
            from_sev = sev_correction.get('from', f.get('severity', ''))
            to_sev = sev_correction.get('to')
            # 不要重复降级：仅在 finding 当前 severity 仍高于 to_sev 时下调
            cur_rank = normalized_severity_rank(f.get('severity', ''))
            to_rank = normalized_severity_rank(to_sev)
            if cur_rank > to_rank:
                f['severity'] = to_sev
                f['severityCorrection'] = {
                    'from': from_sev,
                    'to': to_sev,
                    'reason': sev_correction.get('reason', 'agent-rules.md §4'),
                    'correctedBy': sev_correction.get('correctedBy', 'verifier.py:challenge'),
                }
                severity_corrected_applied += 1

    return severity_corrected_applied


def _apply_fast_plus_results(batch_path, findings, by_id, by_key):
    """将 Fast+ 的 chain/challenge 确定性结果应用回 bypass findings。

    返回按来源拆分的"匹配到 finding 的条数"（不是"修改了字段的条数"）：
      {
        "chain": <chain-verify 匹配数>,
        "challenge": <challenge 匹配数>,
        "total": <两者之和>,
      }
    计数统一为"匹配"语义，避免 chain / challenge 计数口径不一致。
    """
    chain_matched = 0
    challenge_matched = 0
    chain_data = load_json_file(batch_path / 'chain-verify-results.json')
    if chain_data:
        for result in chain_data.get('results', []):
            matched = match_finding(by_id, by_key, result)
            if not matched:
                continue
            verdict = result.get('verdict')
            if verdict:
                matched['verificationStatus'] = verdict
            if result.get('defenseChecked'):
                matched['defenseSearchRecord'] = (
                    f"fast-plus chain-verify: defenseChecked={result.get('defenseChecked')}, "
                    f"hasKnownDefense={result.get('hasKnownDefense')}"
                )
            if result.get('defenseRecords'):
                matched['defenses'] = result.get('defenseRecords')
            if normalize_severity(matched.get('severity', '')) in ('critical', 'high') and verdict == 'unverified':
                _set_confidence_cap(matched, 70)
                matched['_fastPlusAction'] = 'downgrade_unverified_chain'
            chain_matched += 1

    challenge_data = load_json_file(batch_path / 'challenge-results.json')
    if challenge_data:
        for result in challenge_data.get('results', []):
            matched = match_finding(by_id, by_key, result)
            if not matched:
                continue
            verdict = result.get('challengeVerdict')
            if verdict:
                matched['challengeVerdict'] = verdict
            if result.get('challenges'):
                matched['fastPlusChallenges'] = result.get('challenges')
            # 仅对 Critical/High 根据 verdict 调整置信度；其它等级仅回写字段
            if normalize_severity(matched.get('severity', '')) in ('critical', 'high'):
                if verdict == 'dismissed':
                    # 不直接删除：安全扫描中误删真实高危比多报假阳性代价更大。
                    # 降置信度到 40 + severity 降级到 low + 标记人工审核。
                    # severity 降级确保不触发门禁的 high_severity_threshold 规则，
                    # 同时 originalSeverity 保留原始严重度供人工审查参考。
                    _set_confidence_cap(matched, 40)
                    matched['originalSeverity'] = matched.get('severity', 'high')
                    matched['severity'] = 'low'
                    matched['humanReviewRequired'] = True
                    matched['challengeDismissed'] = True
                    matched['_fastPlusAction'] = 'downgrade_dismissed_by_challenge'
                elif verdict == 'downgraded':
                    _set_confidence_cap(matched, 70)
                    matched['_fastPlusAction'] = 'downgrade_by_challenge'
            challenge_matched += 1

    return {
        'chain': chain_matched,
        'challenge': challenge_matched,
        'total': chain_matched + challenge_matched,
    }


def _normalize_vf(vf):
    """将 verifier 各种产出格式归一化为统一 camelCase 嵌套结构。

    v2 严格模式下，verifier 应直接输出统一字段；本函数仅做格式适配以兼容现存
    单实例 / 并行 / step-based 三种历史 schema。最终归一化为：
      vf['antiHallucination']  = {ahAction, fileExists, lineValid, codeMatches}
      vf['verification']       = {verificationStatus, challengeVerdict, traceMethod}
      vf['confidence']         = <int 0-100>          # 扁平整数
      vf['confidenceBreakdown']= {reachability, defense, dataSource}  # 顶层
    """
    # --- step 格式 → 标准嵌套格式 ---
    step1 = vf.get('step1Existence')
    step2 = vf.get('step2AttackChain')
    step3 = vf.get('step3AdversarialReview')
    step5 = vf.get('step5Confidence')

    if step1 and 'antiHallucination' not in vf and 'ahAction' not in vf:
        vf['antiHallucination'] = {
            'ahAction': step1.get('ahAction', 'pass'),
            'fileExists': step1.get('fileExists'),
            'lineValid': step1.get('lineInRange', step1.get('lineValid')),
            'codeMatches': step1.get('codeMatch', step1.get('codeMatches')),
        }

    if step2 and 'verification' not in vf and 'verificationStatus' not in vf:
        trace_method = step2.get('traceMethod', '')
        if not trace_method:
            # 从 step5 推断 traceMethod（step5 包含 traceMethodCap 和 highConfidenceGate 描述）
            if step5:
                gate_text = str(step5.get('highConfidenceGate', ''))
                cap = step5.get('traceMethodCap')
                if 'Grep+Read' in gate_text or step5.get('grepReadExemption'):
                    trace_method = 'Grep+Read'
                elif 'LSP' in gate_text:
                    trace_method = 'LSP'
                elif cap == 100:
                    trace_method = 'LSP'
                elif cap is not None:
                    trace_method = 'Grep+Read'
            if not trace_method:
                trace_method = 'unknown'
        vf['verification'] = {
            'verificationStatus': step2.get('verificationStatus', 'unverified'),
            'challengeVerdict': step3.get('challengeVerdict', '') if step3 else '',
            'traceMethod': trace_method,
        }

    if step5 and 'confidence' not in vf:
        vf['confidence'] = int(step5.get('finalConfidence', step5.get('rawScore', 50)) or 0)
        vf['confidenceBreakdown'] = {
            'reachability': step5.get('reachability', 0),
            'defense': step5.get('defense', 0),
            'dataSource': step5.get('dataSource', 0),
        }

    # --- 扁平格式 → 标准嵌套格式 ---
    if 'antiHallucination' not in vf and 'ahAction' in vf:
        phase_a_detail = vf.get('phaseADetail', {})
        vf['antiHallucination'] = {
            'ahAction': vf.get('ahAction', 'pass'),
            'fileExists': phase_a_detail.get('fileExists', vf.get('fileExists')),
            'lineValid': phase_a_detail.get('lineValid', vf.get('lineValid')),
            'codeMatches': phase_a_detail.get('codeMatches', vf.get('codeMatches')),
        }
    if 'verification' not in vf and 'verificationStatus' in vf:
        vf['verification'] = {
            'verificationStatus': vf.get('verificationStatus'),
            'challengeVerdict': vf.get('challengeVerdict', ''),
            'traceMethod': (vf.get('attackChain') or {}).get('traceMethod',
                           vf.get('traceMethod', 'unknown')),
        }
    # confidence 必须是顶层 int（v2 严格 schema）；非 int 视为缺失并丢弃
    raw_conf = vf.get('confidence')
    if raw_conf is not None and not isinstance(raw_conf, (int, float)):
        # 任何非数值的 confidence（含旧 dict 形态）一律丢弃，由下游使用默认值
        vf.pop('confidence', None)
    elif isinstance(raw_conf, float):
        vf['confidence'] = int(raw_conf)
    return vf


def _apply_finding_validator(fv_data, findings, by_id, by_key, ah_actions):
    """从 finding-validator.json 统一格式中提取并应用三阶段验证结果。
    返回 (removed_by_ah, downgraded_by_ah, removed_by_challenge, downgraded_by_rv, escalated_by_rv)。
    """
    removed_by_ah = 0
    downgraded_by_ah = 0
    removed_by_challenge = 0
    downgraded_by_rv = 0
    escalated_by_rv = 0
    confidence_applied = 0

    # 兼容 validatedFindings / findings 两种键名
    validated = fv_data.get('validatedFindings', fv_data.get('findings', []))
    for vf in validated:
        vf = _normalize_vf(vf)
        # 先尝试 findingId 匹配，再尝试全字段匹配
        ref = dict(vf)  # 传递所有字段以便 match_finding 做多策略匹配
        if 'findingId' not in ref:
            ref['findingId'] = ''
        finding = match_finding(by_id, by_key, ref)
        if finding is None:
            log_warn(f"finding-validator 引用未知 finding: {vf.get('findingId', '?')} "
                     f"file={vf.get('filePath', '?')} "
                     f"riskType={vf.get('riskType', '?')}")
            continue

        fid = finding.get('findingId', '')

        # --- 步骤一: 代码存在性校验 ---
        ah = vf.get('antiHallucination', {})
        ah_action = ah.get('ahAction', 'pass')
        ah_actions[fid] = ah_action

        if ah_action == 'remove':
            finding['_removed'] = True
            finding['_removed_by'] = 'finding-validator:anti-hallucination'
            removed_by_ah += 1
            continue  # 已移除，跳过后续阶段
        elif ah_action == 'downgrade':
            current_conf = finding.get('confidence', 50)
            finding['confidence'] = max(0, int(current_conf) - 20)
            downgraded_by_ah += 1

        # --- 步骤二/三: 攻击链验证 + 对抗审查 ---
        verif = vf.get('verification', {})
        finding['verificationStatus'] = verif.get('verificationStatus', 'unverified')
        finding['traceMethod'] = verif.get('traceMethod', finding.get('traceMethod', 'unknown'))

        verdict = verif.get('challengeVerdict', '')
        finding['challengeVerdict'] = verdict

        if finding['verificationStatus'] == 'false_positive':
            finding['_removed'] = True
            finding['_removed_by'] = 'finding-validator:false_positive'
            removed_by_challenge += 1
            continue
        elif verdict == 'dismissed':
            finding['_removed'] = True
            finding['_removed_by'] = 'finding-validator:dismissed'
            removed_by_challenge += 1
            continue
        elif verdict == 'downgraded':
            finding['severity'] = lower_severity(finding.get('severity', 'medium'))
            downgraded_by_rv += 1
        elif verdict == 'escalated':
            finding['severity'] = raise_severity(finding.get('severity', 'medium'))
            escalated_by_rv += 1

        # --- 步骤五: 置信度评分 ---
        if 'confidence' in vf and not isinstance(vf.get('confidence'), dict):
            try:
                finding['confidence'] = int(vf['confidence'])
                confidence_applied += 1
            except (TypeError, ValueError):
                pass
        if vf.get('confidenceBreakdown'):
            finding['confidenceBreakdown'] = vf['confidenceBreakdown']

    log_info(
        f"finding-validator: AH 移除 {removed_by_ah}, AH 降级 {downgraded_by_ah}, "
        f"验证移除 {removed_by_challenge}, 验证降级 {downgraded_by_rv}, 升级 {escalated_by_rv}, "
        f"置信度赋值 {confidence_applied}"
    )

    # P2 修复：验证覆盖率告警 — 当有 findings 但所有操作均为 0 时，说明 schema 可能不匹配
    total_effects = (removed_by_ah + downgraded_by_ah + removed_by_challenge +
                     downgraded_by_rv + escalated_by_rv + confidence_applied)
    if len(validated) > 0 and total_effects == 0:
        log_warn("⚠ finding-validator 未对任何 finding 产生效果，可能存在 schema 不匹配")

    return removed_by_ah, downgraded_by_ah, removed_by_challenge, downgraded_by_rv, escalated_by_rv


def _collect_verifier_files(agents_dir, prefix='', session=None, stale_records=None):
    """收集所有 verifier 实例产出文件。

    查找顺序：
      1. agents/verifier-*.json（并行分片模式）
      2. agents/finding-validator.json（单实例模式）
      3. agents/verifier.json（单实例回退）

    若提供 session，则按 mtime 拒绝早于会话起始时间的陈旧文件，避免上次扫描遗留
    的 verifier 结果被套用到本次 stage2 findings。

    Returns:
        list of (path, data) tuples
    """
    collected = []
    if stale_records is None:
        stale_records = []

    def _accept(path):
        if session is None:
            return True
        if not is_output_fresh(path, session):
            stale_records.append(str(path))
            return False
        return True

    # 1. 并行模式：verifier-{group}.json
    parallel_files = sorted(agents_dir.glob(f'{prefix}verifier-*.json'))
    for vf_path in parallel_files:
        if not _accept(vf_path):
            log_warn(f"verifier 产物 {vf_path.name} 早于本次会话，已拒绝加载（陈旧数据保护）")
            continue
        data = load_json_file(vf_path)
        if data is not None:
            collected.append((vf_path, data))
            log_info(f"加载并行 verifier 产出: {vf_path.name}")

    if collected:
        return collected

    # 2. 单实例模式：finding-validator.json
    fv_path = agents_dir / f'{prefix}finding-validator.json'
    if fv_path.is_file() and _accept(fv_path):
        data = load_json_file(fv_path)
        if data is not None:
            log_info(f"加载单实例 verifier 产出: {fv_path.name}")
            return [(fv_path, data)]
    elif fv_path.is_file():
        log_warn(f"finding-validator.json 早于本次会话，已拒绝加载（陈旧数据保护）")

    # 3. 回退：verifier.json
    v_path = agents_dir / f'{prefix}verifier.json'
    if v_path.is_file() and _accept(v_path):
        data = load_json_file(v_path)
        if data is not None:
            log_info(f"加载单实例 verifier 回退: {v_path.name}")
            return [(v_path, data)]
    elif v_path.is_file():
        log_warn(f"verifier.json 早于本次会话，已拒绝加载（陈旧数据保护）")

    return []


def merge_stage3(batch_dir, prefix=''):
    """执行阶段 3 合并。prefix 用于分批模式（如 'batch-1-'）。

    支持两种验证模式：
      - 并行模式：从 verifier-*.json 加载
      - 单实例模式：从 finding-validator.json / verifier.json 加载

    可选集成：
      - score-results.json（verifier.py score 产出的确定性置信度评分）
      - quality-assessment.json（verifier.py quality 产出的质量评估）
      - chain-verify-results.json（verifier.py chain-verify 产出的攻击链索引验证）
      - challenge-results.json（verifier.py challenge 产出的确定性对抗审查）
    """
    batch_path = Path(batch_dir)
    agents_dir = batch_path / 'agents'

    # 加载会话锁，校验 stage2 / verifier 产物新鲜度
    session = load_scan_session(batch_path)
    if session is None:
        log_warn(
            "未找到 .scan-session.json，无法判定产物新鲜度，按兼容模式加载所有产物。"
        )

    # 加载 merged-scan.json（必选）
    merged_scan_path = batch_path / f'{prefix}merged-scan.json'
    if session is not None and merged_scan_path.is_file() and not is_output_fresh(merged_scan_path, session):
        log_error(
            f"{merged_scan_path.name} 早于本次会话（陈旧数据），拒绝执行 stage3。"
            "请先运行 merge-scan 重建合并产物。"
        )
        stdout_json({
            "status": "error",
            "message": f"{prefix}merged-scan.json is stale (older than current scan session)",
            "runId": session.get("runId"),
        })
        sys.exit(1)
    stage2_data = load_json_file(merged_scan_path)
    if stage2_data is None:
        log_error(f"{prefix}merged-scan.json 不存在，无法执行阶段 3 合并")
        stdout_json({"status": "error", "message": f"{prefix}merged-scan.json not found"})
        sys.exit(1)

    findings = stage2_data.get('findings', [])
    input_count = len(findings)
    log_info(f"加载 {input_count} 个 stage2 findings")

    # 构建索引
    by_id, by_key = build_finding_index(findings)

    # 跟踪每个 finding 的 anti-hallucination action
    ah_actions = {}  # findingId → action

    # ===== Fast P0：bypass 路径前置的 pre-check 兜底 =====
    # 触发条件（全部满足才运行）：
    #   1. scan_mode == "fast"
    #   2. 既无 pre-check-results.json 也无分片 pre-check-results-*.json
    #      （说明上游未执行 verifier.py pre-check）
    #   3. 环境变量 SECURITY_SCAN_FAST_V2 != "0"
    # 成功后 run_pre_check 会落 pre-check-results.json，下方 1118 行起的
    # 原有加载逻辑会自然读取并应用，无需在此重复实现 match_finding 循环。
    _fast_plan = load_json_file(batch_path / 'batch-plan.json')
    _fast_scan_mode = (_fast_plan or {}).get('scan_mode', 'deep') if _fast_plan else 'deep'
    _fast_v2_enabled = os.environ.get('SECURITY_SCAN_FAST_V2', '1') != '0'
    _existing_pc = (batch_path / 'pre-check-results.json').exists() \
        or any(batch_path.glob('pre-check-results-*.json'))
    if _fast_scan_mode == 'fast' and _fast_v2_enabled and not _existing_pc:
        _run_pre_check = _lazy_import_run_pre_check()
        if _run_pre_check is None:
            log_info("fast-v2: verifier.run_pre_check 不可用，跳过 bypass 前置兜底")
        else:
            try:
                log_info("fast-v2: bypass 路径前置执行 pre-check 兜底（基于 merged-scan.json）")
                _silenced_call(_run_pre_check, str(batch_path))
            except SystemExit:
                log_info("fast-v2: pre-check 兜底 SystemExit，保持 bypass 原行为")
            except Exception as _e:
                log_info(f"fast-v2: pre-check 兜底异常 {_e}，保持 bypass 原行为")
    # ===== 结束 Fast P0 兜底 =====

    # --- 应用 verifier.py pre-check 结果（如果存在）---
    # 支持分片模式：聚合所有 pre-check-results-*.json 分片 + 标准 pre-check-results.json
    pre_check_data = None
    pre_check_shards = sorted(batch_path.glob('pre-check-results-*.json'))
    if pre_check_shards:
        # 流式验证模式：聚合多个分片
        log_info(f"检测到 {len(pre_check_shards)} 个 pre-check 分片，聚合应用")
        pre_check_data = {
            'metrics': {'input': 0, 'grade_static': 0, 'grade_degraded': 0,
                        'grade_verifiable': 0, 'removed': 0},
            'grade_static': [],
            'grade_degraded': [],
            'grade_verifiable': [],
            'removed': [],
        }
        for shard_path in pre_check_shards:
            shard = load_json_file(shard_path)
            if not shard:
                continue
            log_info(f"  聚合分片: {shard_path.name}")
            for key in ('grade_static', 'grade_degraded', 'grade_verifiable', 'removed'):
                pre_check_data[key].extend(shard.get(key, []))
            shard_metrics = shard.get('metrics', {})
            for mkey in ('input', 'grade_static', 'grade_degraded', 'grade_verifiable', 'removed'):
                pre_check_data['metrics'][mkey] = pre_check_data['metrics'].get(mkey, 0) + shard_metrics.get(mkey, 0)
    else:
        # 标准模式：单个 pre-check-results.json
        pre_check_data = load_json_file(batch_path / 'pre-check-results.json')
    stage1_removed = 0
    stage1_downgraded = 0
    fast_plus_applied = {'chain': 0, 'challenge': 0, 'total': 0}
    if pre_check_data:
        log_info("检测到 pre-check-results.json，应用确定性验证结果")
        # 标记 removed findings
        for rf in pre_check_data.get('removed', []):
            matched = match_finding(by_id, by_key, rf)
            if matched:
                matched['_removed'] = True
                matched['ahAction'] = rf.get('ahAction', 'remove')
                stage1_removed += 1
        # 应用 grade_degraded 降级
        for tf in pre_check_data.get('grade_degraded', []):
            matched = match_finding(by_id, by_key, tf)
            if matched:
                matched['ahAction'] = 'downgrade'
                if tf.get('confidence') is not None:
                    matched['confidence'] = tf['confidence']
                stage1_downgraded += 1
        # 标记 grade_static 的 verificationStatus
        for tf in pre_check_data.get('grade_static', []):
            matched = match_finding(by_id, by_key, tf)
            if matched:
                matched['_verificationGrade'] = 'grade_static'
                if not matched.get('verificationStatus'):
                    matched['verificationStatus'] = 'static'
        log_info(f"pre-check 应用完成: 移除 {stage1_removed}，降级 {stage1_downgraded}，"
                 f"grade_static {len(pre_check_data.get('grade_static', []))}，"
                 f"grade_verifiable {len(pre_check_data.get('grade_verifiable', []))}")

    # --- Fast+：对 Critical/High 运行确定性链路验证与对抗审查（不启动 verifier Agent）---
    if _fast_scan_mode == 'fast' and _fast_v2_enabled and _has_fast_plus_targets(findings):
        filtered_data = load_json_file(batch_path / 'filtered-findings.json')
        filtered_findings = filtered_data.get('findings', []) if filtered_data else []
        if filtered_findings:
            _run_chain_verify, _run_challenge = _lazy_import_fast_plus_verifiers()
            if _run_chain_verify and _run_challenge:
                try:
                    if not (batch_path / 'chain-verify-results.json').exists():
                        log_info("fast-v2: 执行 Critical/High 确定性攻击链验证")
                        _silenced_call(_run_chain_verify, str(batch_path))
                    if not (batch_path / 'challenge-results.json').exists():
                        log_info("fast-v2: 执行 Critical/High 确定性对抗审查")
                        _silenced_call(_run_challenge, str(batch_path))
                    fast_plus_applied = _apply_fast_plus_results(batch_path, findings, by_id, by_key)
                    if fast_plus_applied.get('total'):
                        log_info(
                            f"fast-v2: Fast+ 确定性结果已应用 chain={fast_plus_applied['chain']}, "
                            f"challenge={fast_plus_applied['challenge']}"
                        )
                except SystemExit:
                    log_info("fast-v2: Fast+ 确定性验证 SystemExit，保持 bypass 原行为")
                except Exception as _e:
                    log_info(f"fast-v2: Fast+ 确定性验证异常 {_e}，保持 bypass 原行为")
            else:
                log_info("fast-v2: Fast+ 验证函数不可用，跳过")
        else:
            log_info("fast-v2: 无 filtered-findings，跳过 Fast+ 确定性验证")

    challenge_data = load_json_file(batch_path / 'challenge-results.json')

    # --- 收集 verifier 产出（支持并行多实例 + 单实例回退）---
    verifier_stale = []
    verifier_files = _collect_verifier_files(
        agents_dir, prefix, session=session, stale_records=verifier_stale
    )
    if not verifier_files:
        # Light/Fast 模式兼容：检查 scan_mode，允许无 verifier 产出时跳过验证合并
        # Fast 模式复用 Light 的 bypass 路径（因为扫描阶段已内联完成校验）
        batch_plan = load_json_file(batch_path / 'batch-plan.json')
        scan_mode = batch_plan.get('scan_mode', 'deep') if batch_plan else 'deep'
        if scan_mode in ('light', 'fast'):
            log_info(f"{scan_mode} 模式下无 verifier 产出，跳过阶段 3 验证合并，直接使用 stage2 结果")
            severity_corrected_applied = _apply_challenge_severity_corrections(findings, challenge_data)
            if severity_corrected_applied > 0:
                log_info(f"§4 严重级别合规：{severity_corrected_applied} 个 finding 被强制下调")
            final_findings = [f for f in findings if not f.get('_removed')]
            final_findings, remediated_findings = _apply_diff_remediation_filter(final_findings, batch_path)
            if remediated_findings:
                _write_remediated_findings(batch_path, remediated_findings, "merge-verify-bypass")
                log_info(
                    f"diff remediation gate 移除 {len(remediated_findings)} 个当前变更已修复的 finding，"
                    f"剩余 {len(final_findings)} 个"
                )
            final_count = len(final_findings)
            # Early exit reason 处理：
            # - batch-plan 预置的 early_exit_reason 优先透传（不区分 light/fast）
            # - 仅 fast 模式在 findings 为空时自动补充 no_findings（light 模式不自动补）
            # - 如果实际有 findings，抑制 early_exit（预置 reason 可能已过时）
            early_exit_reason = (batch_plan or {}).get('early_exit_reason', '')
            skip_detail = (batch_plan or {}).get('skip_detail', '')
            if not early_exit_reason and scan_mode == 'fast' and final_count == 0:
                early_exit_reason = 'no_findings'
                skip_detail = '阶段 2 扫描后无可报告的有效 findings'
            if early_exit_reason and final_count > 0:
                # 实际有 findings，抑制 early_exit 以避免 banner 误显
                early_exit_reason = ''
                skip_detail = ''

            # 直接输出 merged-scan.json 的内容作为最终结果
            output_metadata = dict(stage2_data.get('metadata', {}))
            if early_exit_reason:
                output_metadata['early_exit_reason'] = early_exit_reason
                output_metadata['skip_detail'] = skip_detail
            if session is not None:
                output_metadata['runId'] = session.get('runId')
                output_metadata['sessionStartedAt'] = session_started_at(session)
            output = {
                'metadata': output_metadata,
                'findings': final_findings,
                'stats': {
                    'input': input_count,
                    'output': final_count,
                    'removed_by_ah': stage1_removed,
                    'downgraded_by_ah': stage1_downgraded,
                    'removed_by_diff_remediation': len(remediated_findings),
                    'fast_plus_applied': fast_plus_applied,
                }
            }
            write_json_file(batch_path / f'{prefix}merged-verified.json', output)

            # 生成 summary.json（与 Deep 模式保持一致，确保 gate_evaluator 能正确读取分级统计）
            by_severity_light = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            risk_file_set_light = set()
            for f in final_findings:
                sev = normalize_severity(f.get('severity', 'low'))
                if sev in by_severity_light:
                    by_severity_light[sev] += 1
                else:
                    by_severity_light['low'] += 1
                fp = f.get('filePath', '')
                if fp:
                    risk_file_set_light.add(fp)

            total_files_light = 0
            if batch_plan:
                total_files_light = batch_plan.get('total_files', 0)

            light_summary = {
                "batchId": batch_path.name,
                "scanMode": scan_mode,
                "command": "project" if "project" in batch_path.name else "diff",
                "totalFiles": total_files_light,
                "riskFiles": len(risk_file_set_light),
                "totalFindings": final_count,
                "criticalRisk": by_severity_light.get("critical", 0),
                "highRisk": by_severity_light.get("high", 0),
                "mediumRisk": by_severity_light.get("medium", 0),
                "lowRisk": by_severity_light.get("low", 0),
            }
            if session is not None:
                light_summary["runId"] = session.get("runId")
                light_summary["sessionStartedAt"] = session_started_at(session)
            if early_exit_reason:
                light_summary['early_exit_reason'] = early_exit_reason
                light_summary['skip_detail'] = skip_detail
            write_json_file(batch_path / 'summary.json', light_summary)
            log_ok(f"已写入 summary.json ({final_count} findings, {scan_mode} bypass)")

            stdout_json({
                'status': 'ok',
                'mode': f'{scan_mode}-bypass',
                'totalFindings': final_count,
                'bySeverity': by_severity_light,
                'message': f'{scan_mode} mode: no verifier files, using stage2 results directly'
            })
            return
        log_error(f"未找到任何 verifier 产出文件，无法执行阶段 3 合并")
        stdout_json({"status": "error", "message": "no verifier output files found"})
        sys.exit(1)

    # 依次应用所有 verifier 实例的结果
    total_removed_by_ah = 0
    total_downgraded_by_ah = 0
    total_removed_by_challenge = 0
    total_downgraded_by_rv = 0
    total_escalated_by_rv = 0

    for vf_path, fv_data in verifier_files:
        r_ah, d_ah, r_ch, d_rv, e_rv = \
            _apply_finding_validator(fv_data, findings, by_id, by_key, ah_actions)
        total_removed_by_ah += r_ah
        total_downgraded_by_ah += d_ah
        total_removed_by_challenge += r_ch
        total_downgraded_by_rv += d_rv
        total_escalated_by_rv += e_rv

    removed_by_ah = total_removed_by_ah
    downgraded_by_ah = total_downgraded_by_ah
    removed_by_challenge = total_removed_by_challenge
    downgraded_by_rv = total_downgraded_by_rv
    escalated_by_rv = total_escalated_by_rv

    # --- 应用 verifier.py score 结果（确定性置信度评分，如果存在）---
    score_data = load_json_file(batch_path / 'score-results.json')
    score_applied = 0
    if score_data:
        log_info("检测到 score-results.json，应用确定性置信度评分")
        score_findings = score_data.get('findings', [])
        score_by_id = {}
        score_by_key = {}
        for sf in score_findings:
            fid = sf.get('findingId', '')
            if fid:
                score_by_id[fid] = sf
            fp = str(sf.get('filePath', ''))
            ln = int(sf.get('lineNumber', 0))
            rt = risk_type_to_slug(sf.get('riskType', ''))
            score_by_key[(fp, ln, rt)] = sf

        for f in findings:
            if f.get('_removed'):
                continue
            fid = f.get('findingId', '')
            # 匹配 score 结果
            scored = score_by_id.get(fid)
            if not scored:
                key = dedup_key(f)
                scored = score_by_key.get(key)
            if scored:
                # 仅当 score 给出有效的更高置信度时才覆盖
                # 避免覆盖 verifier agent 的精确评分
                if scored.get('confidence') is not None:
                    scored_conf = scored.get('confidence', 0)
                    current_conf = f.get('confidence', 0)
                    # 仅当 score 的置信度更高或首次设置时才应用
                    if scored_conf > current_conf or current_conf == 0:
                        f['confidence'] = scored_conf
                if scored.get('confidenceBreakdown'):
                    f['confidenceBreakdown'] = scored['confidenceBreakdown']
                score_applied += 1
        log_info(f"确定性评分应用完成: {score_applied} 个 findings 更新置信度")

    # --- 应用 verifier.py challenge 结果（agent-rules.md §4 严重级别契约）---
    # 来源：scripts/verifier.py challenge 在 challenge-results.json 中产出 severityCorrection
    # 目的：将 §4 + taxonomy.severity_default 的强制下调 propagate 到最终 findings 字段
    severity_corrected_applied = _apply_challenge_severity_corrections(findings, challenge_data)
    if severity_corrected_applied > 0:
        log_info(f"§4 严重级别合规：{severity_corrected_applied} 个 finding 被强制下调")

    # 移除标记删除的 findings
    findings = [f for f in findings if not f.get('_removed')]
    findings, remediated_findings = _apply_diff_remediation_filter(findings, batch_path)
    if remediated_findings:
        _write_remediated_findings(batch_path, remediated_findings, "merge-verify")
        log_info(
            f"diff remediation gate 移除 {len(remediated_findings)} 个当前变更已修复的 finding，"
            f"剩余 {len(findings)} 个"
        )

    # 重建索引
    by_id, by_key = build_finding_index(findings)

    # --- traceMethod 分级上限兜底 ---
    # verification agent 应已执行置信度上限，此处做最终兜底
    # Grep+Read 上限 90（LSP 不可用时的最高置信度）
    GREP_READ_CAP = 90
    trace_capped = 0
    for f in findings:
        confidence = f.get('confidence', 0)
        trace_method = (f.get('traceMethod') or
                        (f.get('attackChain') or {}).get('traceMethod', 'unknown'))

        if trace_method == 'unknown' and confidence > 70:
            f['confidence'] = 70
            trace_capped += 1
        elif trace_method == 'Grep+Read' and confidence > GREP_READ_CAP:
            f['confidence'] = GREP_READ_CAP
            trace_capped += 1

    if trace_capped > 0:
        log_info(f"traceMethod 分级上限: {trace_capped} 个 finding 置信度被上限约束")

    # --- 高置信度门禁 ---
    # finding-validator 已做门禁，此处做最终兜底校验
    gate_demoted = 0
    for f in findings:
        confidence = f.get('confidence', 0)
        if confidence >= 90:
            verified = f.get('verificationStatus') == 'verified'
            confirmed = f.get('challengeVerdict') in ('confirmed', 'escalated')
            ah_pass = ah_actions.get(f.get('findingId', ''), 'pass') == 'pass'

            if not (verified and confirmed and ah_pass):
                f['confidence'] = GREP_READ_CAP - 1  # 降至 Grep+Read 上限以下
                gate_demoted += 1

    if gate_demoted > 0:
        log_info(f"高置信度门禁: {gate_demoted} 个 finding 置信度降至 {GREP_READ_CAP - 1}")

    # --- 步骤 5: 按风险类型分组输出 finding-{slug}.json ---
    final_count = len(findings)
    groups = {}
    for f in findings:
        slug = risk_type_to_slug(f.get('riskType', ''))
        if slug not in groups:
            groups[slug] = []
        groups[slug].append(f)

    finding_files = []
    by_severity_final = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for slug, group_findings in sorted(groups.items()):
        # 构建标准输出格式（v2: 统一 camelCase + findings 数组）
        findings_out = []
        critical = high = medium = low = 0
        for f in group_findings:
            sev = normalize_severity(f.get('severity', 'medium'))
            if sev == 'critical':
                critical += 1
            elif sev == 'high':
                high += 1
            elif sev == 'medium':
                medium += 1
            else:
                low += 1
            by_severity_final[sev] = by_severity_final.get(sev, 0) + 1

            # 直接输出 camelCase finding（to_report_format 已转为恒等透传 + 默认值）
            findings_out.append(to_report_format(f))

        cn_name = SLUG_RISK_TYPE.get(slug, slug)
        file_name = f"finding-{slug}.json"
        finding_metadata = {
            "riskTypeSlug": slug,
            "riskTypeName": cn_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.0",
        }
        if session is not None:
            finding_metadata["runId"] = session.get("runId")
            finding_metadata["sessionStartedAt"] = session_started_at(session)
        finding_data = {
            "metadata": finding_metadata,
            "summary": {
                "totalIssues": len(findings_out),
                "criticalRisk": critical,
                "highRisk": high,
                "mediumRisk": medium,
                "lowRisk": low,
            },
            "findings": findings_out,
        }
        write_json_file(batch_path / file_name, finding_data)
        finding_files.append(file_name)
        log_info(f"  {file_name} — {cn_name}（{len(findings_out)} 个风险）")

    # --- 步骤 6: 写 summary.json ---
    # 从 batch-plan.json 读取扫描文件总数（由编排器生成）
    total_files = 0
    batch_plan = {}
    batch_plan_path = batch_path / 'batch-plan.json'
    if batch_plan_path.exists():
        batch_plan = load_json_file(batch_plan_path) or {}
        if batch_plan:
            total_files = batch_plan.get('total_files', 0)
    # 收集涉及风险的文件数
    risk_file_set = set()
    for f in findings:
        fp = f.get('filePath', '')
        if fp:
            risk_file_set.add(fp)
    risk_files = len(risk_file_set)

    # 从 batch_id 推导 scanMode
    batch_name = batch_path.name
    _scan_mode = _extract_scan_mode_from_batch_id(batch_name)

    summary = {
        "batchId": batch_name,
        "scanMode": _scan_mode,
        "command": "project" if "project-audit" in batch_name else "diff",
        "totalFiles": total_files,
        "riskFiles": risk_files,
        "totalFindings": final_count,
        "criticalRisk": by_severity_final.get("critical", 0),
        "highRisk": by_severity_final.get("high", 0),
        "mediumRisk": by_severity_final.get("medium", 0),
        "lowRisk": by_severity_final.get("low", 0),
        "mergeMetrics": {
            "inputFindings": input_count,
            "removedByAntiHallucination": removed_by_ah,
            "removedByChallenge": removed_by_challenge,
            "downgradedByAntiHallucination": downgraded_by_ah,
            "downgradedByVerification": downgraded_by_rv,
            "escalatedByVerification": escalated_by_rv,
            "severityCorrected": severity_corrected_applied,
            "highConfidenceGateDemoted": gate_demoted,
            "scoreApplied": score_applied,
            "finalFindings": final_count,
        },
    }

    for key in (
        "project_type",
        "project_type_code",
        "product_category",
        "product_subtype",
        "product_shape",
        "product_shape_decision",
        "product_shape_evidence_chain",
    ):
        if batch_plan.get(key) not in (None, "", {}):
            summary[key] = batch_plan[key]

    # 集成 quality-assessment.json（如果存在）
    quality_data = load_json_file(batch_path / 'quality-assessment.json')
    if quality_data:
        summary["qualityAssessment"] = {
            "coveragePercent": quality_data.get('coveragePercent', 0),
            "coveredDimensions": quality_data.get('coveredDimensions', 0),
            "totalDimensions": quality_data.get('totalDimensions', 0),
            "blindSpotCount": quality_data.get('blindSpotCount', 0),
            "inconsistencyCount": quality_data.get('inconsistencyCount', 0),
            "qualityVerdict": quality_data.get('qualityVerdict', 'unknown'),
        }
        log_info(f"质量评估集成: 覆盖率 {quality_data.get('coveragePercent', 0)}%, "
                 f"判定 {quality_data.get('qualityVerdict', 'unknown')}")

    # 注入会话标识，供 gate / upload 校验本会话产物
    if session is not None:
        summary["runId"] = session.get("runId")
        summary["sessionStartedAt"] = session_started_at(session)

    write_json_file(batch_path / 'summary.json', summary)
    log_ok(f"已写入 summary.json ({final_count} findings)")

    # stdout 摘要
    stdout_json({
        "status": "ok",
        "inputFindings": input_count,
        "removedByAntiHallucination": removed_by_ah,
        "removedByChallenge": removed_by_challenge,
        "downgraded": downgraded_by_ah + downgraded_by_rv,
        "severityCorrected": severity_corrected_applied,
        "highConfidenceGateDemoted": gate_demoted,
        "scoreApplied": score_applied,
        "finalFindings": final_count,
        "criticalCount": by_severity_final.get("critical", 0),
        "bySeverity": by_severity_final,
        "findingFiles": finding_files,
        "summaryFile": "summary.json",
    })


# ---------------------------------------------------------------------------
# merge-shards: 大仓分片结果合并
# ---------------------------------------------------------------------------

def _safe_shard_id(shard_id):
    text = str(shard_id or '')
    if not text.startswith('shard-'):
        raise ValueError(f'invalid shard id: {text}')
    suffix = text.removeprefix('shard-')
    if not suffix.isdigit() or not (1 <= len(suffix) <= 5):
        raise ValueError(f'invalid shard id: {text}')
    return text


def _load_findings_from_result_file(result_file):
    data = load_json_file(result_file)
    if not data:
        return []
    if isinstance(data, list):
        return data
    findings = data.get('findings')
    if isinstance(findings, list):
        return findings
    return []


def _load_shard_findings(shard_dir):
    """优先读取 shard 的验证终态，其次读取扫描合并态，最后回退 finding-*.json。"""
    for name in ('merged-verified.json', 'merged-scan.json'):
        path = shard_dir / name
        if path.exists():
            findings = _load_findings_from_result_file(path)
            if findings:
                return findings, name
    findings = []
    for fp in sorted(shard_dir.glob('finding-*.json')):
        findings.extend(_load_findings_from_result_file(fp))
    return findings, 'finding-*.json' if findings else ''


def _prefer_finding(existing, candidate):
    old_rank = normalized_severity_rank(existing.get('severity', 'low'))
    new_rank = normalized_severity_rank(candidate.get('severity', 'low'))
    if new_rank != old_rank:
        return candidate if new_rank > old_rank else existing
    old_conf = int(existing.get('confidence') or 0)
    new_conf = int(candidate.get('confidence') or 0)
    return candidate if new_conf > old_conf else existing


def _write_final_finding_files(batch_path, findings, session, metadata_extra=None):
    groups = {}
    for f in findings:
        slug = risk_type_to_slug(f.get('riskType', ''))
        groups.setdefault(slug, []).append(f)

    finding_files = []
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for old in batch_path.glob('finding-*.json'):
        try:
            old.unlink()
        except OSError:
            pass

    for slug, group in sorted(groups.items()):
        findings_out = []
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in group:
            sev = normalize_severity(f.get('severity', 'medium')) or 'low'
            if sev not in counts:
                sev = 'low'
            counts[sev] += 1
            by_severity[sev] += 1
            findings_out.append(to_report_format(f))
        metadata = {
            "riskTypeSlug": slug,
            "riskTypeName": SLUG_RISK_TYPE.get(slug, slug),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.0",
            "source": "merge-shards",
        }
        if metadata_extra:
            metadata.update(metadata_extra)
        if session is not None:
            metadata["runId"] = session.get("runId")
            metadata["sessionStartedAt"] = session_started_at(session)
        file_name = f"finding-{slug}.json"
        write_json_file(batch_path / file_name, {
            "metadata": metadata,
            "summary": {
                "totalIssues": len(findings_out),
                "criticalRisk": counts["critical"],
                "highRisk": counts["high"],
                "mediumRisk": counts["medium"],
                "lowRisk": counts["low"],
            },
            "findings": findings_out,
        })
        finding_files.append(file_name)
    return finding_files, by_severity


def merge_shards(batch_dir, shard_plan_path=None, include_failed=False):
    """合并大仓 shards/* 的最终 findings，并写父级 merged/summary/report 输入产物。"""
    batch_path = Path(batch_dir)
    plan_path = Path(shard_plan_path) if shard_plan_path else batch_path / 'shard-plan.json'
    plan = load_json_file(plan_path)
    if not plan:
        log_error(f"shard-plan.json 不存在或不可读: {plan_path}")
        stdout_json({"status": "error", "message": "shard-plan.json not found"})
        sys.exit(1)

    session = load_scan_session(batch_path)
    all_findings = []
    shard_stats = []
    skipped_shards = []
    failed_shards = []

    for shard in plan.get('shards', []):
        try:
            shard_id = _safe_shard_id(shard.get('id'))
        except ValueError as exc:
            log_warn(f"跳过非法 shard id: {exc}")
            continue
        shard_dir = batch_path / 'shards' / shard_id
        status_data = load_json_file(shard_dir / 'shard-status.json') or {}
        shard_status = status_data.get('status') or shard.get('status') or 'pending'
        if shard_status == 'failed' and not include_failed:
            failed_shards.append(shard_id)
            continue
        findings, source_file = _load_shard_findings(shard_dir)
        if not findings:
            skipped_shards.append(shard_id)
            continue
        normalized_findings = []
        for raw in findings:
            if not isinstance(raw, dict):
                continue
            item = dict(raw)
            item['shardId'] = shard_id
            item['shardName'] = shard.get('name') or shard_id
            item.setdefault('sourceShard', shard_id)
            item.setdefault('sourceAgent', item.get('sourceAgent') or f"{shard_id}:{source_file}")
            try:
                normalized_findings.append(normalize_finding(item, source_agent=item.get('sourceAgent', 'merge-shards')))
            except LegacyFieldError as exc:
                log_warn(f"跳过 shard legacy finding: {shard_id} {exc}")
        all_findings.extend(normalized_findings)
        shard_stats.append({
            "id": shard_id,
            "status": shard_status,
            "sourceFile": source_file,
            "findingCount": len(normalized_findings),
        })

    cross_agent = batch_path / 'agents' / 'cross-shard-scan.json'
    cross_findings_count = 0
    if cross_agent.exists():
        cross_data = load_json_file(cross_agent)
        for raw in extract_findings_from_agent(cross_data, 'cross-shard-scan'):
            raw['shardId'] = 'cross-shard'
            raw['sourceShard'] = 'cross-shard'
            all_findings.append(raw)
            cross_findings_count += 1

    dedup = {}
    for f in all_findings:
        key = dedup_key(f)
        if key in dedup:
            existing = dedup[key]
            merged_from = set(existing.get('mergedFromShards') or [existing.get('shardId', '')])
            merged_from.add(f.get('shardId', ''))
            chosen = _prefer_finding(existing, f)
            chosen['mergedFromShards'] = sorted(s for s in merged_from if s)
            dedup[key] = chosen
        else:
            dedup[key] = f

    findings = list(dedup.values())
    findings.sort(key=lambda f: (
        -normalized_severity_rank(f.get('severity', 'low')),
        f.get('filePath', ''),
        int(f.get('lineNumber') or 0),
        risk_type_to_slug(f.get('riskType', '')),
    ))
    assign_finding_ids(findings, batch_path.name)

    by_risk_type = {}
    for f in findings:
        f['riskType'] = normalize_risk_type(f.get('riskType', ''))
        slug = risk_type_to_slug(f.get('riskType', ''))
        by_risk_type[slug] = by_risk_type.get(slug, 0) + 1

    finding_files, by_severity = _write_final_finding_files(
        batch_path, findings, session,
        metadata_extra={"largeRepo": True, "shardPlan": plan_path.name}
    )
    risk_files = len({f.get('filePath', '') for f in findings if f.get('filePath')})
    total_files = (load_json_file(batch_path / 'batch-plan.json') or {}).get('total_files') \
        or (plan.get('summary') or {}).get('fileCount', 0)

    merged_payload = {
        "mergedAt": datetime.now(timezone.utc).isoformat(),
        "totalFindings": len(findings),
        "byRiskType": by_risk_type,
        "bySeverity": by_severity,
        "deduplicatedCount": len(all_findings) - len(findings),
        "loadedAgents": ["merge-shards"],
        "largeRepo": True,
        "shardStats": shard_stats,
        "failedShards": failed_shards,
        "skippedShards": skipped_shards,
        "crossShardFindings": cross_findings_count,
        "findings": findings,
    }
    write_json_file(batch_path / 'merged-scan.json', merged_payload)
    write_json_file(batch_path / 'merged-verified.json', {
        "metadata": {
            "source": "merge-shards",
            "largeRepo": True,
            "shardPlan": plan_path.name,
            "runId": (session or {}).get("runId"),
            "sessionStartedAt": session_started_at(session) if session else None,
        },
        "findings": findings,
        "stats": {
            "input": len(all_findings),
            "output": len(findings),
            "deduplicated": len(all_findings) - len(findings),
        },
    })

    batch_name = batch_path.name
    scan_mode = _extract_scan_mode_from_batch_id(batch_name)
    summary = {
        "batchId": batch_name,
        "scanMode": scan_mode,
        "command": "project" if "project" in batch_name else "diff",
        "totalFiles": total_files,
        "riskFiles": risk_files,
        "totalFindings": len(findings),
        "criticalRisk": by_severity.get("critical", 0),
        "highRisk": by_severity.get("high", 0),
        "mediumRisk": by_severity.get("medium", 0),
        "lowRisk": by_severity.get("low", 0),
        "largeRepo": True,
        "shardCount": len(plan.get('shards', [])),
        "completedShards": len(shard_stats),
        "failedShards": len(failed_shards),
        "skippedShards": len(skipped_shards),
        "crossShardFindings": cross_findings_count,
        "mergeMetrics": {
            "inputFindings": len(all_findings),
            "deduplicatedCount": len(all_findings) - len(findings),
            "finalFindings": len(findings),
        },
    }
    if session is not None:
        summary["runId"] = session.get("runId")
        summary["sessionStartedAt"] = session_started_at(session)
    write_json_file(batch_path / 'summary.json', summary)

    log_ok(f"已合并 {len(shard_stats)} 个 shard，输出 {len(findings)} 个最终 findings")
    stdout_json({
        "status": "ok",
        "totalFindings": len(findings),
        "inputFindings": len(all_findings),
        "deduplicatedCount": len(all_findings) - len(findings),
        "bySeverity": by_severity,
        "findingFiles": finding_files,
        "summaryFile": "summary.json",
        "mergedScanFile": "merged-scan.json",
        "mergedVerifiedFile": "merged-verified.json",
        "completedShards": len(shard_stats),
        "failedShards": failed_shards,
        "skippedShards": skipped_shards,
    })


# ---------------------------------------------------------------------------
# audit-stats: 产物质量统计
# ---------------------------------------------------------------------------

def audit_stats(batch_path, source='merged'):
    """统计产物质量：attackChain、recommendation、fixedCode 覆盖率。"""
    # 加载 findings
    findings = []
    if source == 'merged':
        merged_file = batch_path / 'merged-scan.json'
        data = load_json_file(merged_file)
        if data is None:
            log_error(f"merged-scan.json 不存在: {merged_file}")
            stdout_json({"status": "error", "message": "merged-scan.json not found"})
            return
        findings = data.get('findings', []) if isinstance(data, dict) else data
    else:
        for fp in sorted(batch_path.glob('finding-*.json')):
            data = load_json_file(fp)
            if data is None:
                continue
            issues = data.get('findings', [])
            findings.extend(issues)

    if not findings:
        log_warn("未找到任何 findings")
        stdout_json({"status": "ok", "totalFindings": 0})
        return

    total = len(findings)

    # 统计各字段覆盖
    has_chain = 0
    has_rec = 0
    has_fixed = 0
    by_severity = {}
    by_risk_type = {}

    for f in findings:
        sev = normalize_severity(f.get('severity', 'low'))
        rtype = f.get('riskType', '未知')

        chain = f.get('attackChain')
        rec = f.get('recommendation', '')
        fixed = f.get('fixedCode', '')

        has_chain_flag = bool(chain)
        has_rec_flag = bool(rec and len(str(rec)) > 5)
        has_fixed_flag = bool(fixed and len(str(fixed)) > 5)

        if has_chain_flag:
            has_chain += 1
        if has_rec_flag:
            has_rec += 1
        if has_fixed_flag:
            has_fixed += 1

        # 按 severity 统计
        entry = by_severity.setdefault(sev, {"total": 0, "chain": 0, "rec": 0, "fixed": 0})
        entry["total"] += 1
        if has_chain_flag:
            entry["chain"] += 1
        if has_rec_flag:
            entry["rec"] += 1
        if has_fixed_flag:
            entry["fixed"] += 1

        # 按 riskType 统计
        entry2 = by_risk_type.setdefault(rtype, {"total": 0, "chain": 0, "rec": 0, "fixed": 0})
        entry2["total"] += 1
        if has_chain_flag:
            entry2["chain"] += 1
        if has_rec_flag:
            entry2["rec"] += 1
        if has_fixed_flag:
            entry2["fixed"] += 1

    def _pct(n, t):
        return f"{n}/{t} ({round(n * 100 / t)}%)" if t else "0/0"

    # 日志输出
    log_info(f"产物质量统计 ({total} findings)")
    log_info(f"  attackChain 覆盖: {_pct(has_chain, total)}")
    log_info(f"  recommendation 覆盖: {_pct(has_rec, total)}")
    log_info(f"  fixedCode 覆盖: {_pct(has_fixed, total)}")

    for sev in ('critical', 'high', 'medium', 'low'):
        e = by_severity.get(sev)
        if not e:
            continue
        log_info(f"  [{sev}] chain={_pct(e['chain'], e['total'])} rec={_pct(e['rec'], e['total'])} fixed={_pct(e['fixed'], e['total'])}")

    # JSON 输出
    stdout_json({
        "status": "ok",
        "totalFindings": total,
        "coverage": {
            "attackChain": {"count": has_chain, "total": total, "pct": round(has_chain * 100 / total) if total else 0},
            "recommendation": {"count": has_rec, "total": total, "pct": round(has_rec * 100 / total) if total else 0},
            "fixedCode": {"count": has_fixed, "total": total, "pct": round(has_fixed * 100 / total) if total else 0},
        },
        "bySeverity": by_severity,
        "byRiskType": by_risk_type,
    })


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="审计结果合并脚本：合并多 agent 输出、去重、校验",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
子命令说明：
  merge-scan     合并扫描阶段所有 agent 输出（格式校验 + 去重 + findingId 分配 + 漏洞链检测）
  merge-verify   合并验证阶段结果，生成最终 finding-*.json 和 summary.json
  merge-shards   合并大仓分片 shards/* 的最终结果，生成父级统一报告输入
  audit-stats    统计产物质量（attackChain/recommendation/fixedCode 覆盖率）

  别名：merge-stage2 = merge-scan, merge-stage3 = merge-verify

示例：
  %(prog)s merge-scan --batch-dir .codebuddy/security-scan/runs/project-audit-20250302120000
  %(prog)s merge-verify --batch-dir .codebuddy/security-scan/runs/project-audit-20250302120000
  %(prog)s audit-stats --batch-dir .codebuddy/security-scan/runs/project-audit-20250302120000
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # merge-scan + merge-stage2 (别名)
    scan_help = '合并扫描阶段 agent 输出（格式校验 + 去重 + findingId 分配 + 漏洞链检测）'
    for cmd_name in ('merge-scan', 'merge-stage2'):
        sp = subparsers.add_parser(cmd_name, help=scan_help)
        sp.add_argument('--batch-dir', required=True,
                        help='审计批次目录路径（如 .codebuddy/security-scan/runs/project-audit-xxx）')
        sp.add_argument('--prefix', default='',
                        help='agent 输出文件名前缀（分批模式用，如 batch-1-）')
        sp.add_argument('--extra-agents', default='',
                        help='逗号分隔的 agent 名称（如 indexer-findings,vuln-scan,logic-scan,red-team），'
                             'v3.2.0 主要 agent 产物加载方式')
        sp.add_argument('--output', '-o',
                        help='输出文件路径（默认 batch-dir/merged-scan.json）')

    # merge-verify + merge-stage3 (别名)
    verify_help = '合并验证阶段结果，生成 finding-*.json 和 summary.json'
    for cmd_name in ('merge-verify', 'merge-stage3'):
        sp = subparsers.add_parser(cmd_name, help=verify_help)
        sp.add_argument('--batch-dir', required=True,
                        help='审计批次目录路径（如 .codebuddy/security-scan/runs/project-audit-xxx）')
        sp.add_argument('--prefix', default='',
                        help='agent 输出文件名前缀（分批模式用，如 batch-1-）')
        sp.add_argument('--output', '-o',
                        help='输出文件路径（默认按风险类型分文件）')

    # merge-shards
    sp = subparsers.add_parser('merge-shards', help='合并大仓分片 shards/* 的最终结果')
    sp.add_argument('--batch-dir', required=True,
                    help='父级审计批次目录路径')
    sp.add_argument('--shard-plan', default='',
                    help='shard-plan.json 路径（默认 batch-dir/shard-plan.json）')
    sp.add_argument('--include-failed', action='store_true',
                    help='即使 shard-status=failed 也尝试加载其已落盘结果')

    # audit-stats
    sp = subparsers.add_parser('audit-stats', help='统计产物质量（attackChain/recommendation/fixedCode 覆盖率）')
    sp.add_argument('--batch-dir', required=True,
                    help='审计批次目录路径')
    sp.add_argument('--source', choices=['merged', 'summary'], default='merged',
                    help='数据源：merged（merged-scan.json）或 summary（finding-*.json）')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 校验 batch-dir 存在
    batch_dir = Path(args.batch_dir)
    if not batch_dir.is_dir():
        log_error(f"批次目录不存在: {batch_dir}")
        stdout_json({"status": "error", "message": f"batch dir not found: {batch_dir}"})
        sys.exit(1)

    prefix = getattr(args, 'prefix', '')
    output_file = getattr(args, 'output', None)
    extra_agents = getattr(args, 'extra_agents', '')

    if args.command in ('merge-scan', 'merge-stage2'):
        merge_stage2(batch_dir, prefix=prefix, output_path=Path(output_file) if output_file else None,
                     extra_agents=extra_agents)
    elif args.command in ('merge-verify', 'merge-stage3'):
        merge_stage3(batch_dir, prefix=prefix)
    elif args.command == 'merge-shards':
        merge_shards(
            batch_dir,
            shard_plan_path=getattr(args, 'shard_plan', '') or None,
            include_failed=getattr(args, 'include_failed', False),
        )
    elif args.command == 'audit-stats':
        audit_stats(batch_dir, source=args.source)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log_warn("用户中断操作")
        sys.exit(130)
    except Exception as e:
        log_error(f"未预期的错误: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        stdout_json({"status": "error", "message": str(e)})
        sys.exit(1)
