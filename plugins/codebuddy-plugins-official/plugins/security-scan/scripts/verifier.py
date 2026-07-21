#!/usr/bin/env python3
"""
验证脚本：对 merged-scan.json 执行确定性验证和智能分级

子命令：
  pre-check     代码存在性校验 + 攻击链分级，输出 filtered-findings.json（仅 grade_verifiable）和 pre-check-results.json（全量）
                支持 --input 指定输入文件（默认 merged-scan.json），支持 --source-agent 生成分片输出
  split         按 sourceAgent 将 filtered-findings.json 拆分为多个分片，供并行 verifier 实例消费
                支持 --input 指定输入文件（默认 filtered-findings.json）
  chain-verify  攻击链索引验证：利用 project-index.db 的 sinks/endpoints/call_graph/defenses 表，
                对每个 finding 的 attackChain 做确定性验证，产出 verificationStatus
  challenge     确定性对抗审查：利用 defenses 表交叉验证 + 误报模式检测 + 死代码检测 + 冲突检查，
                产出 challengeVerdict（confirmed/dismissed/downgraded）
  score         确定性置信度评分（三维度基础分 + traceMethod 上限 + 高置信度门控），减少 LLM turns
  quality       确定性全局审计质量评估（覆盖率计算 + 盲点识别），减少 LLM turns

设计原则：
  - 确定性操作（文件/行号/片段校验、置信度计算、覆盖率统计）由脚本完成，不消耗 LLM turns
  - 完整结果写入文件，stdout 仅输出 JSON 摘要供编排器解析
  - 日志信息输出到 stderr
"""
import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

from _common import (
    Colors, make_logger, stdout_json,
    load_json_file, write_json_file,
    normalize_finding, SEVERITY_ORDER,
)


log_info, log_ok, log_warn, log_error = make_logger('verifier')


# ---------------------------------------------------------------------------
# 数据库连接辅助
# ---------------------------------------------------------------------------

def _connect_db_safe(db_path):
    """连接 SQLite 数据库，启用 WAL 模式和 busy_timeout，带重试机制。"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=15000")
            return conn
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                import time
                time.sleep(1 * (attempt + 1))
                continue
            raise


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# 无需攻击链验证的 sourceAgent（静态事实类）
STATIC_AGENTS = {'indexer', 'pattern-matching'}

# 无需攻击链验证的风险类型 slug
STATIC_RISK_TYPES = {
    'hardcoded-secret', 'vulnerable-dependency', 'weak-crypto-config',
    'config-issue', 'information-leak-config',
}

# 代码片段 fuzzy match 行号容忍度
LINE_TOLERANCE = 5

# 代码片段不匹配时置信度扣减
MISMATCH_PENALTY = 15

# 严重级别 rank ↔ severity 反向映射（用于 §4 确定性级别收敛）
RANK_TO_SEVERITY = {4: 'critical', 3: 'high', 2: 'medium', 1: 'low'}

# ---------------------------------------------------------------------------
# 聚焦模式黑名单（focus-filter 确定性过滤使用）
# 来源: resource/high-focus-sinks.yaml > focus_blacklist（拍平为 set）
# 不在黑名单中的类型 → 保留（宁可放过，不可误杀）
# ---------------------------------------------------------------------------

FOCUS_BLACKLIST = {
    # 需用户交互
    "xss", "csrf", "open-redirect", "clickjacking",
    # 间接利用 / 需链式组合
    "ssrf", "path-traversal", "xxe", "file-upload",
    "ldap-injection", "crlf-injection", "second-order-injection",
    # 需认证 + 特定上下文
    "idor", "access-control", "mass-assignment", "session-fixation",
    "credential-enumeration",
    # DoS 类
    "denial-of-service", "redos", "xml-bomb", "zip-bomb",
    "resource-exhaustion",
    # 线索级
    "information-leak", "insecure-config", "weak-crypto",
    "missing-security-headers", "csv-injection",
    "weak-password-hash", "missing-security-audit",
    "brute-force-unprotected", "missing-lockfile",
    "insecure-cookie", "jwt-weak-key", "jwt-algorithm-confusion",
    "log-injection", "predictable-reset-token",
    "sensitive-data-logging", "endpoint-exposure",
    "plaintext-password",
    # 前端 / 客户端本地攻击面
    "prototype-pollution", "postmessage-origin-bypass",
    "dom-clobbering", "websocket-hijacking",
    "cors-misconfiguration", "client-side-bypass",
    "insecure-localstorage", "exported-component",
    "insecure-webview", "electron-node-integration",
    "electron-disabled-websecurity",
    "electron-shell-command-injection", "electron-ipc-no-validation",
    "electron-remote-content", "electron-preload-overexposure",
    "unsigned-auto-update", "protocol-handler-hijack",
    "cleartext-traffic", "debuggable-backup-enabled",
    "screen-data-leak", "weak-root-jailbreak-detection",
    "improper-cert-validation", "insecure-mobile-storage",
    "intent-redirection",
    # 业务逻辑
    "race-condition", "business-logic", "missing-idempotency",
    "data-isolation-failure", "missing-audit-log", "callback-trust",
    "transaction-integrity", "input-boundary", "rate-limit-missing",
    "state-machine-violation",
    # 依赖/配置低风险
    "dependency-confusion", "typosquatting", "insecure-dependency-source",
    # 低风险云配置
    "serverless-no-auth", "cloud-db-exposed", "iam-overprivilege",
    "cloud-imds",
    # AI Agent 低风险
    "system-prompt-leak", "vector-store-poisoning",
    # Ghost Bits
    "ghost-bits-truncation",
}


def _rank_to_severity(rank):
    """将 rank 数值收敛到合法区间 [1,4] 并映射回 severity 字符串。"""
    rank = max(1, min(4, int(rank)))
    return RANK_TO_SEVERITY[rank]


# ---------------------------------------------------------------------------
# 分级判定
# ---------------------------------------------------------------------------

def has_attack_chain(finding):
    """判断 finding 是否具备有效攻击链"""
    chain = finding.get('attackChain')
    if not chain or not isinstance(chain, dict):
        return False
    source = chain.get('source')
    sink = chain.get('sink')
    propagation = chain.get('propagation')
    # source 和 sink 都非空，且 propagation 是非空列表
    if source and sink and isinstance(propagation, list) and len(propagation) > 0:
        return True
    # 仅有 source + sink（无中间传播）也算有效
    if source and sink:
        return True
    return False


def classify_verification_grade(finding):
    """
    对 finding 进行验证等级分级：
      - grade_static:     静态事实类（来自 indexer/pattern-matching，或属于静态风险类型），跳过攻击链验证
      - grade_verifiable: 有完整攻击链且代码存在，进入 verifier agent 深度验证
    注意：grade_degraded 不在此初始分级中产生，它在后续代码片段校验失败时由 grade_verifiable 降级而来。
    """
    source_agent = finding.get('sourceAgent', '')
    risk_type = finding.get('riskType', '') or finding.get('riskTypeSlug', '')

    # 静态事实类：无需攻击链验证
    if source_agent in STATIC_AGENTS:
        return 'grade_static'
    if risk_type in STATIC_RISK_TYPES:
        return 'grade_static'

    # 有攻击链 → grade_verifiable（后续校验可能降级为 grade_degraded）
    if has_attack_chain(finding):
        return 'grade_verifiable'

    # 无攻击链但不属于静态类 → 仍归为 grade_static（无法深度验证）
    return 'grade_static'


# ---------------------------------------------------------------------------
# 代码存在性校验
# ---------------------------------------------------------------------------

def check_file_exists(file_path):
    """检查文件是否存在"""
    if not file_path:
        return False
    return os.path.isfile(file_path)


def check_line_range(file_path, line_number):
    """检查行号是否在文件范围内"""
    if not file_path or not line_number:
        return False
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            total_lines = sum(1 for _ in f)
        return 1 <= line_number <= total_lines
    except (OSError, IOError):
        return False


def read_code_around_line(file_path, line_number, tolerance=LINE_TOLERANCE):
    """读取行号附近的代码（±tolerance 行）"""
    if not file_path or not line_number:
        return ''
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        start = max(0, line_number - 1 - tolerance)
        end = min(len(lines), line_number + tolerance)
        return ''.join(lines[start:end])
    except (OSError, IOError):
        return ''


def snippet_matches(code_sample, actual_code):
    """
    模糊匹配代码片段：
    - 去除空白后比较
    - 提取关键标识符做 regex 匹配
    """
    if not code_sample or not actual_code:
        return False

    # 清理：去除首尾空白、多余空格
    clean_sample = ' '.join(code_sample.split())
    clean_actual = ' '.join(actual_code.split())

    # 完全包含
    if clean_sample in clean_actual:
        return True

    # 提取代码中的标识符/关键字做模糊匹配
    # 从 code_sample 提取至少 3 个 token
    tokens = re.findall(r'[a-zA-Z_]\w+', code_sample)
    if len(tokens) < 2:
        # token 太少，无法有效匹配
        return clean_sample in clean_actual

    # 至少 60% 的 token 在实际代码中出现
    matched = sum(1 for t in tokens if t in actual_code)
    return matched >= len(tokens) * 0.6


# ---------------------------------------------------------------------------
# Stage 1 主逻辑
# ---------------------------------------------------------------------------

def run_pre_check(batch_dir, input_file=None, source_agent=None):
    """执行确定性预校验 + 智能分级。

    Args:
        batch_dir: 批次目录路径
        input_file: 输入文件路径（默认 merged-scan.json），支持流式验证场景
        source_agent: 来源 agent 标识（如 'vuln-scan'），指定后输出分片文件
                      pre-check-results-{agent_slug}.json 和 filtered-findings-{agent_slug}.json
    """
    batch_path = Path(batch_dir)

    # 加载输入文件
    if input_file:
        input_path = Path(input_file) if os.path.isabs(input_file) else batch_path / input_file
        merged_data = load_json_file(input_path)
        if not merged_data:
            log_error(f"未找到指定输入文件: {input_path}")
            stdout_json({"status": "error", "message": f"input file not found: {input_path}"})
            sys.exit(1)
    else:
        merged_path = batch_path / 'merged-scan.json'
        merged_data = load_json_file(merged_path)
        if not merged_data:
            merged_path = batch_path / 'merged-stage2.json'
            merged_data = load_json_file(merged_path)
        if not merged_data:
            log_error(f"未找到 merged-scan.json 或 merged-stage2.json: {batch_path}")
            stdout_json({"status": "error", "message": "merged-scan.json not found"})
            sys.exit(1)

    findings = merged_data.get('findings', [])
    log_info(f"加载 {len(findings)} 个 findings，开始预校验")

    static_results = []
    degraded_results = []
    verifiable_results = []
    removed = []

    for f in findings:
        # 确保使用统一字段名
        f = normalize_finding(f)
        file_path = f.get('filePath', '')
        line = f.get('lineNumber', 0)
        code_sample = f.get('riskCode', '')

        # 1. 分级
        grade = classify_verification_grade(f)
        f['_verificationGrade'] = grade

        if grade == 'grade_static':
            # 静态事实：仅做文件存在性校验
            if file_path and not check_file_exists(file_path):
                f['ahAction'] = 'remove'
                f['_removedReason'] = 'FILE_NOT_FOUND'
                removed.append(f)
                continue
            f['ahAction'] = 'pass'
            static_results.append(f)
            continue

        # grade_verifiable 候选：完整代码存在性校验
        # 2. 文件存在
        if not check_file_exists(file_path):
            f['ahAction'] = 'remove'
            f['_removedReason'] = 'FILE_NOT_FOUND'
            f['_verificationGrade'] = 'removed'
            removed.append(f)
            continue

        # 3. 行号范围
        if line and not check_line_range(file_path, line):
            f['ahAction'] = 'remove'
            f['_removedReason'] = 'LINE_OUT_OF_RANGE'
            f['_verificationGrade'] = 'removed'
            removed.append(f)
            continue

        # 4. 代码片段匹配
        if code_sample and line:
            actual_code = read_code_around_line(file_path, line)
            if actual_code and not snippet_matches(code_sample, actual_code):
                # 降级为 grade_degraded
                f['ahAction'] = 'downgrade'
                f['_verificationGrade'] = 'grade_degraded'
                f['_downgradedReason'] = 'CODE_MISMATCH'
                confidence = f.get('confidence', 50)
                f['confidence'] = max(0, confidence - MISMATCH_PENALTY)
                degraded_results.append(f)
                continue

        # 通过所有校验 → grade_verifiable
        f['ahAction'] = 'pass'
        verifiable_results.append(f)

    # 统计
    metrics = {
        'input': len(findings),
        'grade_static': len(static_results),
        'grade_degraded': len(degraded_results),
        'grade_verifiable': len(verifiable_results),
        'removed': len(removed),
    }

    log_ok(f"预校验完成: {metrics['grade_static']} grade_static + {metrics['grade_degraded']} grade_degraded + "
           f"{metrics['grade_verifiable']} grade_verifiable, 移除 {metrics['removed']}")

    # 构建输出数据
    results_data = {
        'metrics': metrics,
        'grade_static': static_results,
        'grade_degraded': degraded_results,
        'grade_verifiable': verifiable_results,
        'removed': removed,
    }
    if source_agent:
        results_data['sourceAgent'] = source_agent

    filtered_data = dict(merged_data)
    filtered_data['findings'] = verifiable_results
    filtered_data['_preCheckMetrics'] = metrics

    # 写入分片文件（流式验证模式）
    if source_agent:
        # 使用 AGENT_GROUP_MAP 保证文件名一致性（与 split 逻辑相同）
        agent_slug = AGENT_GROUP_MAP.get(source_agent, source_agent)
        shard_results_path = batch_path / f'pre-check-results-{agent_slug}.json'
        write_json_file(shard_results_path, results_data)
        log_info(f"分片结果已写入 {shard_results_path}")

        shard_filtered_path = batch_path / f'filtered-findings-{agent_slug}.json'
        write_json_file(shard_filtered_path, filtered_data)
        log_info(f"分片 grade_verifiable findings 已写入 {shard_filtered_path} ({len(verifiable_results)} 个)")

    # 写入标准文件（全量聚合场景）
    results_path = batch_path / 'pre-check-results.json'
    write_json_file(results_path, results_data)
    log_info(f"全量结果已写入 {results_path}")

    filtered_path = batch_path / 'filtered-findings.json'
    write_json_file(filtered_path, filtered_data)
    log_info(f"grade_verifiable findings 已写入 {filtered_path} ({len(verifiable_results)} 个)")

    # stdout 摘要
    output_info = {
        "status": "ok",
        **metrics,
        "preCheckResultsFile": str(results_path.name),
        "filteredFindingsFile": str(filtered_path.name),
    }
    if source_agent:
        agent_slug = AGENT_GROUP_MAP.get(source_agent, source_agent)
        output_info["shardPreCheckFile"] = f'pre-check-results-{agent_slug}.json'
        output_info["shardFilteredFile"] = f'filtered-findings-{agent_slug}.json'
    stdout_json(output_info)


# ---------------------------------------------------------------------------
# split: 按 sourceAgent 拆分 findings 供并行 verifier 实例消费
# ---------------------------------------------------------------------------

# 扫描 Agent 分组映射（sourceAgent → 分片名）
AGENT_GROUP_MAP = {
    'vuln-scan': 'vuln',
    'logic-scan': 'logic',
    'red-team': 'redteam',
}

# 默认分片（未匹配到 AGENT_GROUP_MAP 的 sourceAgent 归入此分片）
DEFAULT_GROUP = 'vuln'


def run_split(batch_dir, input_file=None):
    """按 sourceAgent 将 filtered-findings.json 拆分为多个分片文件。

    输出文件：
      - filtered-findings-vuln.json    (sourceAgent in [vuln-scan] + 未知来源)
      - filtered-findings-logic.json   (sourceAgent in [logic-scan])
      - filtered-findings-redteam.json (sourceAgent in [red-team])

    空分片不输出文件。

    Args:
        batch_dir: 批次目录路径
        input_file: 输入文件路径（默认 filtered-findings.json），支持流式验证场景
    """
    batch_path = Path(batch_dir)

    # 加载输入文件
    if input_file:
        filtered_path = Path(input_file) if os.path.isabs(input_file) else batch_path / input_file
    else:
        filtered_path = batch_path / 'filtered-findings.json'
    filtered_data = load_json_file(filtered_path)
    if not filtered_data:
        log_error(f"未找到 {filtered_path}")
        stdout_json({"status": "error", "message": f"{filtered_path.name} not found"})
        sys.exit(1)

    findings = filtered_data.get('findings', [])
    log_info(f"加载 {len(findings)} 个 grade_verifiable findings，按 sourceAgent 拆分")

    # 按 sourceAgent 分组
    groups = {}  # group_name -> [finding, ...]
    for f in findings:
        agent = f.get('sourceAgent', '')
        group = AGENT_GROUP_MAP.get(agent, DEFAULT_GROUP)
        groups.setdefault(group, []).append(f)

    # 写入各分片文件
    output_files = []
    split_metrics = {}
    for group_name, group_findings in sorted(groups.items()):
        if not group_findings:
            continue

        file_name = f'filtered-findings-{group_name}.json'
        out_path = batch_path / file_name
        out_data = dict(filtered_data)
        out_data['findings'] = group_findings
        out_data['_splitGroup'] = group_name
        out_data['_splitTotal'] = len(group_findings)
        write_json_file(out_path, out_data)

        output_files.append(file_name)
        split_metrics[group_name] = len(group_findings)
        log_info(f"  {file_name}: {len(group_findings)} findings")

    log_ok(f"拆分完成: {len(output_files)} 个分片, 合计 {len(findings)} findings")

    stdout_json({
        "status": "ok",
        "totalFindings": len(findings),
        "groups": split_metrics,
        "outputFiles": output_files,
    })


# ---------------------------------------------------------------------------
# score: 确定性置信度评分（下沉自 verifier agent 步骤四）
# ---------------------------------------------------------------------------

# traceMethod 置信度上限
TRACE_METHOD_CAP = {
    'LSP': 100,
    'Grep+AST': 95,
    'Grep+Read': 90,
    'unknown': 50,
}

# 覆盖率维度（用于 quality 子命令）
COVERAGE_DIMENSIONS = {
    'C1': {'name': '注入类', 'riskTypes': {
        'sql-injection', 'command-injection', 'xss', 'xxe', 'log-injection',
        'csv-injection', 'insecure-deserialization',
    }},
    'C2': {'name': '凭证/密钥', 'riskTypes': {
        'hardcoded-secret',
    }},
    'C3': {'name': '认证授权', 'riskTypes': {
        'missing-auth', 'missing-access-control', 'idor', 'authentication-bypass',
        'endpoint-exposure',
    }},
    'C4': {'name': '配置安全', 'riskTypes': {
        'insecure-configuration', 'missing-security-headers', 'missing-rate-limit',
        'csrf-disabled', 'csrf', 'insecure-cookie',
    }},
    'C5': {'name': '文件操作', 'riskTypes': {
        'path-traversal',
    }},
    'C6': {'name': 'SSRF/反序列化', 'riskTypes': {
        'ssrf', 'ssrf-defense-disabled', 'insecure-deserialization',
    }},
    'C7': {'name': '业务逻辑', 'riskTypes': {
        'business-logic', 'open-redirect', 'host-header-injection',
    }},
    'C8': {'name': '依赖安全', 'riskTypes': {
        'vulnerable-dependency',
    }},
    'C9': {'name': '密码/会话', 'riskTypes': {
        'insecure-password-storage', 'insecure-session', 'weak-hash',
        'weak-crypto', 'insecure-random', 'jwt-security',
    }},
    'C10': {'name': '信息泄露', 'riskTypes': {
        'information-leak', 'information-disclosure',
    }},
}


def _normalize_severity(sev):
    """标准化严重性等级"""
    if not sev:
        return 'low'
    s = str(sev).lower().strip()
    if s in ('critical', '严重'):
        return 'critical'
    elif s in ('high', '高'):
        return 'high'
    elif s in ('medium', 'moderate', '中', '中等'):
        return 'medium'
    return 'low'


def _risk_type_to_slug(risk_type):
    """risk_type -> slug 映射，复用 merge_findings 的完整 RISK_TYPE_SLUG 映射"""
    if not risk_type:
        return 'unknown'
    try:
        from merge_findings import risk_type_to_slug
        return risk_type_to_slug(risk_type)
    except ImportError:
        # fallback: 简单转换
        return risk_type.lower().strip().replace(' ', '-').replace('_', '-')


def score_attack_chain_reachability(finding):
    """维度 1：攻击链可达性（满分 40）

    基于已有的 verificationStatus 和 challengeVerdict 确定性评分。
    """
    status = finding.get('verificationStatus', 'unverified')
    verdict = finding.get('challengeVerdict', '')
    chain = finding.get('attackChain')

    # verified + confirmed/escalated -> 高分区间
    if status == 'verified':
        if verdict in ('confirmed', 'escalated'):
            # 完整验证 + 对抗确认
            base = 36
            # 有完整 propagation 链路加分
            if chain and isinstance(chain, dict):
                prop = chain.get('propagation', [])
                if isinstance(prop, list) and len(prop) >= 2:
                    base = 38
                if isinstance(prop, list) and len(prop) >= 3:
                    base = 40
            return base
        else:
            # verified 但未经对抗审查（Medium/Low 级别）
            return 30

    # unverified 但有攻击链
    if status == 'unverified' and chain and isinstance(chain, dict):
        source = chain.get('source')
        sink = chain.get('sink')
        prop = chain.get('propagation', [])
        if source and sink and isinstance(prop, list) and len(prop) > 0:
            return 18  # 有完整链但未验证
        if source and sink:
            return 12  # 仅 source+sink
        return 8

    # false_positive / not_verifiable
    if status == 'false_positive':
        return 0
    if status == 'not_verifiable':
        return 5

    return 10  # 默认中低分


def score_defense_measures(finding):
    """维度 2：防御措施（满分 30）

    分数越高 = 防御越弱 = 风险越大。
    基于 defenses 字段和 challengeVerdict 确定性推断。
    """
    defenses = finding.get('defenses', [])
    verdict = finding.get('challengeVerdict', '')
    defense_search = finding.get('defenseSearchRecord', finding.get('_defenseSearched'))

    # 对抗审查结论直接映射
    if verdict == 'escalated':
        return 30  # 无有效防御，已升级
    if verdict == 'dismissed':
        return 5  # 有有效防御，已驳回

    # 有 defenses 字段
    if isinstance(defenses, list) and defenses:
        # 有防御记录
        effective_count = sum(1 for d in defenses
                             if isinstance(d, dict) and d.get('effective') is True)
        if effective_count > 0:
            return 8  # 有已确认的有效防御
        return 18  # 有防御但有效性不确定
    elif isinstance(defenses, str) and defenses:
        # 字符串描述的防御
        lower_def = defenses.lower()
        if any(kw in lower_def for kw in ('effective', '有效', 'mitigated', '已缓解')):
            return 8
        if any(kw in lower_def for kw in ('partial', '部分', 'bypass', '绕过')):
            return 22
        return 15

    # 无防御记录
    if defense_search:
        return 27  # 搜索过但无防御
    if verdict == 'confirmed':
        return 25  # 对抗确认无有效防御

    return 20  # 默认不确定


def score_data_source_controllability(finding):
    """维度 3：数据源可控性（满分 30）

    基于 attackChain.source 类型推断。
    """
    chain = finding.get('attackChain')
    if not chain or not isinstance(chain, dict):
        return 15  # 默认不确定

    source = chain.get('source', '')
    source_str = json.dumps(source, ensure_ascii=False).lower() if isinstance(source, dict) else str(source).lower()

    # 直接可控：HTTP 参数/请求体/URL/上传
    direct_keywords = [
        'request.getparameter', 'req.body', 'req.query', 'req.params',
        'request.form', 'request.args', 'request.json', '@requestbody',
        '@requestparam', '@pathvariable', 'upload', 'multipart',
        'httpservletrequest', 'getinputstream', 'getreader',
        'c.param', 'c.query', 'c.postform', 'r.formvalue', 'r.url.query',
        'request.get', 'request.post', 'input(', 'file_get_contents',
    ]
    if any(kw in source_str for kw in direct_keywords):
        return 28

    # 间接可控：数据库/消息队列/文件
    indirect_keywords = [
        'database', 'db.', 'repository', 'dao.', 'mapper.',
        'redis', 'cache', 'session', 'cookie',
        'kafka', 'rabbitmq', 'mq', 'queue',
        'file', 'readfile', 'fread',
    ]
    if any(kw in source_str for kw in indirect_keywords):
        return 22

    # 内部生成/不可控
    internal_keywords = [
        'uuid', 'random', 'system.', 'env.', 'config.',
        'constant', 'static', 'hardcoded', 'internal',
    ]
    if any(kw in source_str for kw in internal_keywords):
        return 6

    return 15  # 默认来源不明


def run_score(batch_dir):
    """对验证后的 findings 执行确定性置信度评分。

    输入：agents/ 下的 verifier-*.json（多个并行 verifier 实例的产出）
    输出：score-results.json（含每个 finding 的三维度评分 + 最终置信度）
    """
    batch_path = Path(batch_dir)
    agents_dir = batch_path / 'agents'

    # 收集所有 verifier 实例的产出
    all_verified = []
    verifier_files = sorted(agents_dir.glob('verifier-*.json')) if agents_dir.is_dir() else []

    # 也支持单实例 verifier.json / finding-validator.json
    for fallback_name in ('finding-validator.json', 'verifier.json'):
        fb_path = agents_dir / fallback_name
        if fb_path.exists() and not verifier_files:
            verifier_files = [fb_path]
            break

    if not verifier_files:
        log_error("未找到任何 verifier 实例产出文件")
        stdout_json({"status": "error", "message": "no verifier output files found"})
        sys.exit(1)

    for vf_path in verifier_files:
        data = load_json_file(vf_path)
        if data is None:
            log_warn(f"无法加载: {vf_path}")
            continue
        findings = data.get('validatedFindings', data.get('findings', []))
        if isinstance(findings, list):
            all_verified.extend(findings)
            log_info(f"加载 {vf_path.name}: {len(findings)} findings")

    # 加载 merged-scan.json 作为回填源（兼容精简格式的 verifier 输出）
    merged_data = load_json_file(batch_path / 'merged-scan.json')
    merged_index = {}  # findingId -> finding
    if merged_data:
        for mf in merged_data.get('findings', []):
            fid = mf.get('findingId', '')
            if fid:
                merged_index[fid] = mf
        if merged_index:
            log_info(f"加载 merged-scan.json 作为回填源: {len(merged_index)} findings")

    log_info(f"合计 {len(all_verified)} 个已验证 findings，开始确定性评分")

    scored = []
    high_conf = med_conf = low_conf = 0

    for f in all_verified:
        # 精简格式回填：若 verifier 输出缺少核心字段，从 merged-scan 补充
        fid = f.get('findingId', '')
        if fid and fid in merged_index:
            merged_f = merged_index[fid]
            for key in ('riskType', 'filePath', 'lineNumber', 'severity',
                        'attackChain', 'sourceAgent', 'traceMethod', 'riskCode'):
                if not f.get(key) and merged_f.get(key):
                    f[key] = merged_f[key]
        f = normalize_finding(f)

        # 三维度评分
        dim1 = score_attack_chain_reachability(f)
        dim2 = score_defense_measures(f)
        dim3 = score_data_source_controllability(f)
        raw_score = dim1 + dim2 + dim3

        # traceMethod 上限
        trace_method = (f.get('traceMethod') or
                        (f.get('attackChain') or {}).get('traceMethod', 'unknown'))
        trace_cap = TRACE_METHOD_CAP.get(trace_method, TRACE_METHOD_CAP['unknown'])

        # 高置信度门控（>=90 需满足全部 3 项）
        gate_cap = 100
        verification_status = f.get('verificationStatus', 'unverified')
        challenge_verdict = f.get('challengeVerdict', '')
        # 多字段兼容性检查（防止字段缺失导致误判）
        defense_searched = bool(
            f.get('defenseSearchRecord') or 
            f.get('_defenseSearched') or
            f.get('defenseSearched') or
            f.get('defenseSearch') or
            f.get('_defenseSearch')
        )

        is_verified = verification_status == 'verified'
        is_confirmed = challenge_verdict in ('confirmed', 'escalated')

        if raw_score >= 90:
            if not (is_verified and is_confirmed and defense_searched):
                gate_cap = 89

        # 步骤二调整
        if challenge_verdict == 'downgraded':
            raw_score = max(0, raw_score - 10)
        ah_action = f.get('ahAction', f.get('_ahAction', 'pass'))
        if ah_action == 'downgrade':
            raw_score = max(0, raw_score - 20)

        # confidenceCeiling（scanner 产出的外部上限）
        external_cap = f.get('confidenceCeiling', 100)
        if not isinstance(external_cap, (int, float)):
            external_cap = 100

        # 最终置信度 = min(所有上限, 三维度评分)
        final_score = min(raw_score, trace_cap, gate_cap, int(external_cap))
        final_score = max(0, min(100, final_score))

        # 写回 finding
        f['confidence'] = final_score
        f['confidenceBreakdown'] = {
            'reachability': dim1,
            'defense': dim2,
            'dataSource': dim3,
            'rawScore': raw_score,
            'traceMethodCap': trace_cap,
            'gateCapApplied': gate_cap < 100,
            'externalCap': int(external_cap),
        }

        # 统计
        if final_score >= 90:
            high_conf += 1
        elif final_score >= 60:
            med_conf += 1
        else:
            low_conf += 1

        scored.append(f)

    # 写入 score-results.json
    out_path = batch_path / 'score-results.json'
    write_json_file(out_path, {
        'totalScored': len(scored),
        'highConfidence': high_conf,
        'mediumConfidence': med_conf,
        'lowConfidence': low_conf,
        'findings': scored,
    })
    log_ok(f"评分完成: 高置信度 {high_conf}, 中置信度 {med_conf}, 低置信度 {low_conf}")

    stdout_json({
        "status": "ok",
        "totalScored": len(scored),
        "highConfidence": high_conf,
        "mediumConfidence": med_conf,
        "lowConfidence": low_conf,
        "outputFile": "score-results.json",
    })


# ---------------------------------------------------------------------------
# quality: 确定性全局审计质量评估（下沉自 verifier agent 步骤三）
# ---------------------------------------------------------------------------

def run_quality(batch_dir):
    """执行确定性全局审计质量评估。

    输入：
      - score-results.json（已评分的 findings）
      - pre-check-results.json（分级结果）
      - project-index.db 的 summary（通过 batch-plan.json 推断文件数）
    输出：
      - quality-assessment.json（覆盖率 + 盲点 + 统计）
    """
    batch_path = Path(batch_dir)

    # 加载已评分 findings
    score_data = load_json_file(batch_path / 'score-results.json')
    if not score_data:
        # fallback: 直接从 verifier 产出加载
        log_warn("score-results.json 不存在，尝试从 verifier 产出加载")
        score_data = {'findings': []}
        agents_dir = batch_path / 'agents'
        for vf_path in sorted(agents_dir.glob('verifier-*.json')) if agents_dir.is_dir() else []:
            data = load_json_file(vf_path)
            if data:
                score_data['findings'].extend(data.get('validatedFindings', data.get('findings', [])))

    # 加载 pre-check 结果
    pre_check_data = load_json_file(batch_path / 'pre-check-results.json')
    pre_check_metrics = pre_check_data.get('metrics', {}) if pre_check_data else {}

    # 合并所有 findings（已评分 + grade_static）
    scored_findings = score_data.get('findings', [])
    static_findings = pre_check_data.get('grade_static', []) if pre_check_data else []
    degraded_findings = pre_check_data.get('grade_degraded', []) if pre_check_data else []
    all_findings = scored_findings + static_findings + degraded_findings

    log_info(f"质量评估输入: {len(scored_findings)} 已评分 + {len(static_findings)} 静态 + "
             f"{len(degraded_findings)} 降级 = {len(all_findings)} 合计")

    # 计算覆盖率
    found_risk_types = set()
    for f in all_findings:
        rt = f.get('riskType', '')
        slug = _risk_type_to_slug(rt)
        found_risk_types.add(slug)

    covered_dims = []
    uncovered_dims = []
    for dim_id, dim_info in sorted(COVERAGE_DIMENSIONS.items()):
        dim_types = dim_info['riskTypes']
        if found_risk_types & dim_types:
            covered_dims.append({
                'dimension': dim_id,
                'name': dim_info['name'],
                'matchedTypes': list(found_risk_types & dim_types),
            })
        else:
            uncovered_dims.append({
                'dimension': dim_id,
                'name': dim_info['name'],
                'expectedTypes': list(dim_types)[:3],  # 截取前 3 个示例
            })

    total_dims = len(COVERAGE_DIMENSIONS)
    covered_count = len(covered_dims)
    coverage_pct = round(covered_count * 100 / total_dims) if total_dims else 0

    # 严重性分布
    severity_dist = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for f in all_findings:
        sev = _normalize_severity(f.get('severity', 'low'))
        severity_dist[sev] = severity_dist.get(sev, 0) + 1

    # 置信度分布
    conf_dist = {'high': 0, 'medium': 0, 'low': 0}
    for f in scored_findings:
        conf = f.get('confidence', 0)
        if conf >= 90:
            conf_dist['high'] += 1
        elif conf >= 60:
            conf_dist['medium'] += 1
        else:
            conf_dist['low'] += 1

    # 一致性检查：同一位置不同 agent 的判定是否一致
    location_agents = {}  # (file, line) -> {agent: verificationStatus}
    inconsistencies = []
    for f in scored_findings:
        loc = (f.get('filePath', ''), f.get('lineNumber', 0))
        agent = f.get('sourceAgent', '')
        status = f.get('verificationStatus', '')
        if loc[0] and loc[1]:
            location_agents.setdefault(loc, {})[agent] = status

    for loc, agents in location_agents.items():
        statuses = set(agents.values())
        if len(statuses) > 1 and 'false_positive' in statuses:
            inconsistencies.append({
                'file': loc[0],
                'line': loc[1],
                'agents': agents,
            })

    # 质量等级
    if coverage_pct >= 80 and len(inconsistencies) == 0:
        quality_verdict = 'good'
    elif coverage_pct >= 60:
        quality_verdict = 'acceptable'
    else:
        quality_verdict = 'needs_improvement'

    # 写入结果
    result = {
        'coveragePercent': coverage_pct,
        'coveredDimensions': covered_count,
        'totalDimensions': total_dims,
        'covered': covered_dims,
        'blindSpots': uncovered_dims,
        'blindSpotCount': len(uncovered_dims),
        'severityDistribution': severity_dist,
        'confidenceDistribution': conf_dist,
        'inconsistencies': inconsistencies,
        'inconsistencyCount': len(inconsistencies),
        'qualityVerdict': quality_verdict,
        'preCheckMetrics': pre_check_metrics,
    }

    out_path = batch_path / 'quality-assessment.json'
    write_json_file(out_path, result)
    log_ok(f"质量评估完成: 覆盖率 {coverage_pct}% ({covered_count}/{total_dims})，"
           f"盲点 {len(uncovered_dims)} 个，一致性冲突 {len(inconsistencies)} 个，"
           f"判定: {quality_verdict}")

    stdout_json({
        "status": "ok",
        "coveragePercent": coverage_pct,
        "coveredDimensions": covered_count,
        "totalDimensions": total_dims,
        "blindSpotCount": len(uncovered_dims),
        "inconsistencyCount": len(inconsistencies),
        "qualityVerdict": quality_verdict,
        "outputFile": "quality-assessment.json",
    })


# ---------------------------------------------------------------------------
# chain-verify: 攻击链索引验证（利用 project-index.db）
# ---------------------------------------------------------------------------

# 已知有效防御类型映射：riskTypeSlug → 有效防御 defense_type 列表
KNOWN_EFFECTIVE_DEFENSES = {
    'sql-injection': ['parameterized_query', 'prepared_statement', 'orm_auto', 'input_validation'],
    'command-injection': ['input_validation', 'whitelist', 'parameterized_api'],
    'xss': ['output_encoding', 'html_escape', 'content_security_policy', 'template_auto_escape'],
    'path-traversal': ['path_validation', 'whitelist', 'chroot', 'canonicalize'],
    'ssrf': ['url_validation', 'whitelist', 'network_isolation'],
    'xxe': ['disable_external_entities', 'xml_parser_config'],
    'insecure-deserialization': ['type_whitelist', 'input_validation'],
    'log-injection': ['output_encoding', 'log_sanitizer'],
    'open-redirect': ['url_validation', 'whitelist'],
    'csrf': ['csrf_token', 'same_site_cookie', 'referer_check'],
}

# 测试文件路径模式
TEST_PATH_PATTERNS = re.compile(
    r'(^|/)(test[s]?|__test__|spec[s]?|__spec__|fixture[s]?|mock[s]?|stub[s]?|fake[s]?|e2e|integration[-_]test)(/|$)|'
    r'[._-](test|spec|mock)\.(java|py|go|js|ts|jsx|tsx|rb|php)$',
    re.IGNORECASE,
)


def _parse_chain_node_location(node):
    """从攻击链节点（source/sink）中解析文件路径和行号。

    支持两种格式：
      - string: "src/routes.js:39"
      - object: {"file": "src/routes.js", "line": 39, "code": "..."}
    """
    if isinstance(node, dict):
        file_path = node.get('file') or node.get('filePath') or ''
        line = node.get('line') or node.get('lineNumber') or 0
        return str(file_path), int(line) if line else 0
    if isinstance(node, str):
        # "file:line" 格式
        if ':' in node:
            parts = node.rsplit(':', 1)
            if parts[1].isdigit():
                return parts[0], int(parts[1])
        return node, 0
    return '', 0


def _db_has_record(conn, table, file_path, line_number, tolerance=5):
    """检查数据库表中是否存在匹配的记录（行号容忍度 ±tolerance）。"""
    # 根据表名选择正确的行号列名
    line_col = 'start_line' if table == 'ast_functions' else 'line'
    try:
        if line_number > 0:
            row = conn.execute(
                f"SELECT COUNT(*) as c FROM {table} WHERE file_path = ? AND "
                f"ABS(CAST({line_col} AS INTEGER) - ?) <= ?",
                (file_path, line_number, tolerance)
            ).fetchone()
        else:
            row = conn.execute(
                f"SELECT COUNT(*) as c FROM {table} WHERE file_path = ?",
                (file_path,)
            ).fetchone()
        return row['c'] > 0
    except Exception:
        return False


def _call_graph_reachable(conn, source_file, sink_file, max_depth=5):
    """在 call_graph 表中做 BFS 判断 source_file 到 sink_file 是否可达。"""
    if source_file == sink_file:
        return True
    try:
        visited = {source_file}
        frontier = [source_file]
        for _ in range(max_depth):
            if not frontier:
                break
            next_frontier = []
            placeholders = ','.join('?' for _ in frontier)
            rows = conn.execute(
                f"SELECT DISTINCT callee_file FROM call_graph WHERE caller_file IN ({placeholders})",
                frontier
            ).fetchall()
            for row in rows:
                callee = row['callee_file']
                if callee == sink_file:
                    return True
                if callee not in visited:
                    visited.add(callee)
                    next_frontier.append(callee)
            frontier = next_frontier
        return False
    except Exception:
        return False


# 攻击请求（PoC）可得性封顶：豁免类型（按存在性定级，不受 PoC 封顶约束）
POC_CAP_EXEMPT_SLUGS = {
    'malicious-package', 'vulnerable-dependency', 'typosquatting',
    'dependency-confusion',
    'hardcoded-secret', 'hardcoded-credentials', 'sensitive-info-leak',
    'public-bucket', 'public-storage', 'iam-overprivilege', 'cam-overprivilege',
}

# 无需认证即视为可直接远程的 auth_type 取值
_OPEN_AUTH_TYPES = {'', 'none', 'public', 'anonymous', 'no', 'null'}


def _endpoint_auth_type(conn, file_path, line_number, line_tolerance=10):
    """查询 endpoints 表中匹配位置的 auth_type；找到返回字符串（小写），否则返回 None。"""
    if not conn or not file_path:
        return None
    try:
        cur = conn.execute(
            "SELECT line_number, auth_type FROM endpoints WHERE file_path = ? OR file_path LIKE ?",
            (file_path, f"%{file_path}")
        )
        rows = cur.fetchall()
        if not rows:
            return None
        best = None
        for row in rows:
            ln = row['line_number'] if 'line_number' in row.keys() else row[0]
            auth = row['auth_type'] if 'auth_type' in row.keys() else row[1]
            auth = (auth or '').strip().lower()
            if ln is None:
                return auth
            try:
                if abs(int(ln) - int(line_number)) <= line_tolerance:
                    return auth
            except (TypeError, ValueError):
                pass
            if best is None:
                best = auth
        return best
    except Exception as e:
        log_warn(f"_endpoint_auth_type 查询失败: {e}")
        return None


def _derive_poc_hint(conn, finding, source_file, source_line, sink_file,
                     source_verified, sink_verified, path_exists, has_endpoints):
    """基于索引派生 poc 初值（保守：仅给正向 / 不确定提示，绝不主动判 available='no'，
    避免索引不全导致误杀；available='no' 由 verifier Agent 实证后填写）。

    返回 poc dict 或 None（无足够信息 / 已有 agent 产出时不写）。
    """
    existing = finding.get('poc')
    if isinstance(existing, dict) and existing.get('available'):
        return None  # 不覆盖 agent 已产出的 poc

    # 仅在有触发路径（sink 存在且可达）时给出初值
    if not (path_exists and sink_verified):
        return None

    auth_type = (_endpoint_auth_type(conn, source_file or sink_file, source_line)
                 if has_endpoints else None)
    evidence = []
    if source_verified:
        evidence.append(f"endpoints/functions: {source_file}:{source_line}")
    if sink_verified:
        evidence.append(f"sinks: {sink_file}")

    if auth_type is not None:
        if auth_type in _OPEN_AUTH_TYPES:
            reachability, available = 'remote-direct', 'yes'
        else:
            reachability, available = 'remote-conditional', 'conditional'
        evidence.append(f"endpoints.auth_type={auth_type or 'none'}")
        entry_type = 'http'
    elif source_verified:
        reachability, available, entry_type = 'remote-conditional', 'conditional', 'none'
    else:
        # 有 sink/路径但未定位外部入口 → 不确定，交由 Agent 实证
        reachability, available, entry_type = 'none', 'conditional', 'none'

    return {
        'available': available,
        'entryType': entry_type,
        'reachability': reachability,
        'evidenceRefs': evidence,
        'derivedBy': 'verifier.py:chain-verify',
    }


def _poc_cap_severity(finding):
    """攻击请求(PoC)不可得封顶：poc.available=='no' 且非豁免类型时，severity 封顶 Medium。

    返回 severityCorrection dict（若发生封顶）或 None。
    """
    poc = finding.get('poc')
    if not isinstance(poc, dict):
        return None
    if (poc.get('available') or '').strip().lower() != 'no':
        return None

    slug = _normalize_risk_slug(finding.get('riskType', ''))
    if slug in POC_CAP_EXEMPT_SLUGS:
        return None

    sev_order = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
    current = (finding.get('severity') or '').lower()
    if current not in sev_order or sev_order[current] <= sev_order['medium']:
        return None  # 已 <= medium 或非法值，无需封顶

    finding['severity'] = 'medium'
    finding['humanReviewRequired'] = True
    return {
        'from': current,
        'to': 'medium',
        'reason': 'poc_not_obtainable',
        'correctedBy': 'verifier.py:challenge',
    }


def _db_query_defenses(conn, file_path, line_number=0, tolerance=10):
    """从 defenses 表查询指定位置的防御记录。"""
    try:
        if line_number > 0:
            rows = conn.execute(
                "SELECT * FROM defenses WHERE file_path = ? AND "
                "ABS(CAST(line AS INTEGER) - ?) <= ?",
                (file_path, line_number, tolerance)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM defenses WHERE file_path = ?",
                (file_path,)
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def run_chain_verify(batch_dir):
    """Stage 2: 攻击链索引验证

    对 filtered-findings.json 中的 grade_verifiable findings，
    利用 project-index.db 验证攻击链节点的真实性。

    验证 4 个维度：
      1. sourceVerified: source 在 endpoints/ast_functions 表中存在
      2. sinkVerified: sink 在 sinks 表中存在
      3. pathExists: 调用图中存在 source→sink 文件级可达路径
      4. defenseChecked: 是否查询过 defenses 表

    产出 verificationStatus:
      - verified: 3/3 维度通过
      - partially_verified: 1-2/3 维度通过
      - unverified: 0/3 维度通过
    """
    batch_path = Path(batch_dir)
    db_path = batch_path / 'project-index.db'

    # 加载 filtered-findings.json
    filtered_data = load_json_file(batch_path / 'filtered-findings.json')
    if not filtered_data:
        log_warn("filtered-findings.json 不存在，跳过攻击链索引验证")
        stdout_json({"status": "skip", "message": "filtered-findings.json not found"})
        return

    findings = filtered_data.get('findings', [])
    if not findings:
        log_info("无待验证 findings，跳过攻击链索引验证")
        stdout_json({"status": "ok", "totalVerified": 0, "message": "no findings to verify"})
        return

    # 检查数据库是否存在
    has_db = db_path.exists()
    conn = None
    if has_db:
        conn = _connect_db_safe(str(db_path))
        # 检查必要的表是否存在
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        has_sinks = 'sinks' in tables
        has_endpoints = 'endpoints' in tables
        has_call_graph = 'call_graph' in tables
        has_defenses = 'defenses' in tables
        has_functions = 'ast_functions' in tables or 'functions' in tables
        func_table = 'ast_functions' if 'ast_functions' in tables else ('functions' if 'functions' in tables else None)
        log_info(f"数据库表: sinks={has_sinks}, endpoints={has_endpoints}, "
                 f"call_graph={has_call_graph}, defenses={has_defenses}, functions={has_functions}")
    else:
        log_warn(f"数据库不存在: {db_path}，攻击链验证将降级为纯结构校验")
        has_sinks = has_endpoints = has_call_graph = has_defenses = has_functions = False
        func_table = None

    verified_count = partially_count = unverified_count = 0
    defense_found_count = 0
    results = []

    try:
        for f in findings:
            f = normalize_finding(f)
            chain = f.get('attackChain')
            result = {
                'findingId': f.get('findingId', ''),
                'filePath': f.get('filePath', ''),
                'lineNumber': f.get('lineNumber', 0),
                'riskType': f.get('riskType', ''),
                'sourceVerified': False,
                'sinkVerified': False,
                'pathExists': False,
                'defenseChecked': False,
                'hasKnownDefense': False,
                'defenseRecords': [],
            }

            if not chain or not isinstance(chain, dict):
                # 无攻击链 → unverified
                f['verificationStatus'] = 'unverified'
                result['verdict'] = 'unverified'
                unverified_count += 1
                results.append(result)
                continue

            source_file, source_line = _parse_chain_node_location(chain.get('source'))
            sink_file, sink_line = _parse_chain_node_location(chain.get('sink'))

            # 如果 source/sink 无文件信息，用 finding 自身位置补充
            if not sink_file:
                sink_file = f.get('filePath', '')
                sink_line = f.get('lineNumber', 0)

            # 2.1 Source 验证：查 endpoints + ast_functions
            if conn and source_file:
                if has_endpoints:
                    result['sourceVerified'] = _db_has_record(conn, 'endpoints', source_file, source_line)
                if not result['sourceVerified'] and func_table:
                    result['sourceVerified'] = _db_has_record(conn, func_table, source_file, source_line)
            elif source_file and os.path.isfile(source_file):
                # 降级：文件存在即算通过
                result['sourceVerified'] = True

            # 2.2 Sink 验证：查 sinks 表
            if conn and sink_file and has_sinks:
                result['sinkVerified'] = _db_has_record(conn, 'sinks', sink_file, sink_line)
            elif sink_file and os.path.isfile(sink_file):
                result['sinkVerified'] = True

            # 2.3 路径验证：查 call_graph（BFS 可达性）
            if conn and has_call_graph and source_file and sink_file:
                result['pathExists'] = _call_graph_reachable(conn, source_file, sink_file)
            elif source_file == sink_file:
                result['pathExists'] = True  # 同文件默认可达

            # 2.4 防御交叉验证：查 defenses 表
            if conn and has_defenses and sink_file:
                defense_records = _db_query_defenses(conn, sink_file, sink_line)
                result['defenseChecked'] = True
                if defense_records:
                    result['hasKnownDefense'] = True
                    result['defenseRecords'] = defense_records[:3]  # 最多保留 3 条
                    defense_found_count += 1
                    f['_chainDefenseFound'] = True
            else:
                result['defenseChecked'] = True  # 无表也算检查过

            # 综合判定
            core_checks = [result['sourceVerified'], result['sinkVerified'], result['pathExists']]
            passed = sum(core_checks)

            if passed == 3:
                f['verificationStatus'] = 'verified'
                result['verdict'] = 'verified'
                verified_count += 1
            elif passed >= 1:
                f['verificationStatus'] = 'partially_verified'
                result['verdict'] = 'partially_verified'
                partially_count += 1
            else:
                f['verificationStatus'] = 'unverified'
                result['verdict'] = 'unverified'
                unverified_count += 1

            # 派生攻击请求(PoC)可得性初值（保守：绝不主动判 no，仅给正向/不确定提示）
            poc_hint = _derive_poc_hint(
                conn, f, source_file, source_line, sink_file,
                result['sourceVerified'], result['sinkVerified'],
                result['pathExists'], has_endpoints,
            )
            if poc_hint:
                f['poc'] = poc_hint
                result['poc'] = poc_hint

            results.append(result)

    finally:
        if conn:
            conn.close()

    # 写入 chain-verify-results.json
    out_data = {
        'totalFindings': len(findings),
        'verified': verified_count,
        'partiallyVerified': partially_count,
        'unverified': unverified_count,
        'defenseFound': defense_found_count,
        'hasDatabase': has_db,
        'results': results,
    }
    out_path = batch_path / 'chain-verify-results.json'
    write_json_file(out_path, out_data)

    # 更新 filtered-findings.json（回写 verificationStatus）
    write_json_file(batch_path / 'filtered-findings.json', filtered_data)

    log_ok(f"攻击链索引验证完成: verified={verified_count}, "
           f"partially={partially_count}, unverified={unverified_count}, "
           f"defenseFound={defense_found_count}")

    stdout_json({
        "status": "ok",
        "totalFindings": len(findings),
        "verified": verified_count,
        "partiallyVerified": partially_count,
        "unverified": unverified_count,
        "defenseFound": defense_found_count,
        "outputFile": "chain-verify-results.json",
    })


# ---------------------------------------------------------------------------
# challenge: 确定性对抗审查
# ---------------------------------------------------------------------------

def _load_taxonomy_severity_defaults():
    """加载 risk-type-taxonomy.yaml 中的 severity_default 字段。

    返回 {risk_slug: severity_default} 映射；找不到 / 解析失败时返回 {}。
    用于强制对照 agent-rules.md §4 的严重级别契约。
    """
    plugin_root = os.environ.get('CODEBUDDY_PLUGIN_ROOT')
    if not plugin_root:
        # 回退：以脚本路径推断插件根目录
        plugin_root = str(Path(__file__).resolve().parent.parent)
    taxonomy_path = Path(plugin_root) / 'resource' / 'risk-type-taxonomy.yaml'
    if not taxonomy_path.exists():
        return {}

    severity_map = {}
    try:
        # 不依赖 PyYAML：用简单文本解析提取 slug + severity_default
        # 适配格式（缩进 2 空格）：
        #   - slug: "weak-crypto"
        #     name_en: "..."
        #     aliases: [...]
        #     severity_default: "low"  # agent-rules.md §4
        current_slug = None
        with taxonomy_path.open('r', encoding='utf-8') as fh:
            for line in fh:
                line_stripped = line.rstrip('\n')
                m_slug = re.match(r'\s*-\s*slug:\s*["\']?([a-z0-9_\-]+)["\']?\s*$', line_stripped)
                if m_slug:
                    current_slug = m_slug.group(1).strip()
                    continue
                if current_slug:
                    m_sev = re.match(r'\s*severity_default:\s*["\']?(critical|high|medium|low)["\']?', line_stripped, re.IGNORECASE)
                    if m_sev:
                        severity_map[current_slug] = m_sev.group(1).lower()
    except Exception as exc:
        log_warn(f"加载 taxonomy.severity_default 失败: {exc}")
        return {}

    return severity_map


def _normalize_risk_slug(risk_type):
    """将 finding.riskType 归一化为 taxonomy slug 形式（小写、下划线/空格转 -）。"""
    if not risk_type:
        return ''
    return str(risk_type).strip().lower().replace(' ', '-').replace('_', '-')


def correct_one_severity(finding, severity_defaults, corrected_by='verifier.py:challenge'):
    """对单个 finding 执行 agent-rules.md §4 + taxonomy.severity_default 的确定性级别收敛。

    纯函数，**不依赖 index.db / 攻击链**，仅基于 finding 自身字段
    （severity / severityRationale / riskType）与 taxonomy 基线。可被
    challenge 阶段（Deep/Fast）与 Light bypass 路径共同复用，确保级别契约单一来源。

    规则（与 §4.2 完全一致）：
      - 基线优先：以 taxonomy.severity_default 为基线
      - 越级且无 severityRationale → 强制回落基线
      - 越级有 severityRationale 但超过 +1 档 → 上限收敛到 default+1
      - 线索级(default=low)因 +1 封顶，任何理由都不得升到 high/critical

    命中收敛时就地修改 finding['severity'] 与 finding['severityCorrection']，
    返回 severityCorrection dict；无需收敛时返回 None。
    """
    if not severity_defaults:
        return None
    risk_type_slug = _normalize_risk_slug(finding.get('riskType', ''))
    if not risk_type_slug:
        return None
    actual_sev = str(finding.get('severity', '')).strip().lower()
    default_sev = severity_defaults.get(risk_type_slug)
    if not (default_sev and actual_sev):
        return None
    actual_rank = SEVERITY_ORDER.get(actual_sev, 0)
    default_rank = SEVERITY_ORDER.get(default_sev, 0)
    has_rationale = bool(str(finding.get('severityRationale', '')).strip())
    target_sev = None
    correction_reason = None
    if actual_rank > default_rank:
        if not has_rationale:
            target_sev = default_sev
            correction_reason = ('agent-rules.md §4：越级且无 severityRationale，'
                                 '强制回落 taxonomy.severity_default')
        elif actual_rank > default_rank + 1:
            target_sev = _rank_to_severity(default_rank + 1)
            correction_reason = ('agent-rules.md §4：越级超过 +1 档，'
                                 '上限收敛到 severity_default+1')
    if target_sev and target_sev != actual_sev:
        record = {
            'from': actual_sev,
            'to': target_sev,
            'reason': correction_reason,
            'correctedBy': corrected_by,
        }
        finding['severity'] = target_sev
        finding['severityCorrection'] = record
        return record
    return None


def apply_severity_compliance(findings, severity_defaults=None,
                              corrected_by='verifier.py:severity-compliance'):
    """对一批 findings 执行确定性级别合规收敛（agent-rules.md §4），返回修正数量。

    供 Light bypass 路径复用：Light 不跑完整 challenge（无 index.db / 攻击链验证），
    但级别合规校验本就只依赖 taxonomy 基线 + finding 字段，可零额外开销地强制执行，
    避免越级噪声直接进报告打扰用户。severity_defaults 缺省时自动加载 taxonomy。
    """
    if severity_defaults is None:
        severity_defaults = _load_taxonomy_severity_defaults()
    if not severity_defaults:
        return 0
    corrected = 0
    for f in findings or []:
        if correct_one_severity(f, severity_defaults, corrected_by=corrected_by):
            corrected += 1
    return corrected


def _is_test_file(file_path):
    """判断文件是否为测试文件。"""
    return bool(TEST_PATH_PATTERNS.search(file_path or ''))


def _is_dead_code(conn, file_path, line_number, func_table):
    """通过 call_graph 判断是否为死代码（无任何入站调用）。"""
    if not conn or not file_path:
        return False
    try:
        # 防御: call_graph 表为空说明索引阶段未构建调用图，无法判断死代码
        total_row = conn.execute(
            "SELECT COUNT(*) as c FROM call_graph"
        ).fetchone()
        if total_row['c'] == 0:
            return False  # 无调用图数据，跳过死代码检测

        # 查询是否有任何调用者
        row = conn.execute(
            "SELECT COUNT(*) as c FROM call_graph WHERE callee_file = ?",
            (file_path,)
        ).fetchone()
        if row['c'] == 0:
            # 进一步检查是否为端点（端点无入站调用是正常的）
            ep_row = conn.execute(
                "SELECT COUNT(*) as c FROM endpoints WHERE file_path = ?",
                (file_path,)
            ).fetchone()
            if ep_row['c'] == 0:
                return True  # 非端点且无入站调用 → 可能是死代码
    except Exception:
        pass
    return False


def run_challenge(batch_dir):
    """Stage 3: 确定性对抗审查

    对每个 verified/partially_verified finding 执行自动化的对抗审查，
    挑战其结论是否成立。

    审查维度：
      1. 防御有效性挑战：查 defenses 表，看是否存在该 riskType 的有效防御
      2. 误报模式检测：测试文件、示例代码
      3. 死代码检测：无入站调用且非端点
      4. 攻击链完整性挑战：traceMethod == unknown 则降级
      5. 冲突检查：同一位置如果有相反结论

    产出 challengeVerdict:
      - confirmed: 通过对抗审查，结论成立
      - dismissed: 被驳回（有有效防御、测试代码等）
      - downgraded: 被降级（死代码、不完整追踪等）
    """
    batch_path = Path(batch_dir)
    db_path = batch_path / 'project-index.db'

    # 加载 filtered-findings.json（已包含 chain-verify 产出的 verificationStatus）
    filtered_data = load_json_file(batch_path / 'filtered-findings.json')
    if not filtered_data:
        log_warn("filtered-findings.json 不存在，跳过对抗审查")
        stdout_json({"status": "skip", "message": "filtered-findings.json not found"})
        return

    findings = filtered_data.get('findings', [])
    if not findings:
        log_info("无待审查 findings，跳过对抗审查")
        stdout_json({"status": "ok", "totalChallenged": 0})
        return

    # 连接数据库（可选）
    conn = None
    func_table = None
    has_defenses = False
    if db_path.exists():
        conn = _connect_db_safe(str(db_path))
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        has_defenses = 'defenses' in tables
        func_table = 'ast_functions' if 'ast_functions' in tables else ('functions' if 'functions' in tables else None)

    confirmed_count = dismissed_count = downgraded_count = 0
    severity_corrected_count = 0
    results = []

    # 加载 §4 契约：taxonomy.severity_default 映射
    severity_defaults = _load_taxonomy_severity_defaults()
    if severity_defaults:
        log_info(f"已加载 {len(severity_defaults)} 个 riskType 的 severity_default（§4 契约源）")

    try:
        for f in findings:
            f = normalize_finding(f)
            challenges = []
            file_path = f.get('filePath', '')
            line_number = f.get('lineNumber', 0)
            risk_type_slug = _normalize_risk_slug(f.get('riskType', ''))

            # 4.1 防御有效性挑战
            if conn and has_defenses and file_path:
                defense_records = _db_query_defenses(conn, file_path, line_number)
                for d in defense_records:
                    d_type = d.get('type', '')
                    effective_types = KNOWN_EFFECTIVE_DEFENSES.get(risk_type_slug, [])
                    if d_type in effective_types:
                        challenges.append({
                            'type': 'effective_defense',
                            'defense_type': d_type,
                            'verdict': 'dismiss',
                        })
                        break  # 一个有效防御即可驳回

            # 4.2 误报模式检测
            if _is_test_file(file_path):
                challenges.append({
                    'type': 'test_code',
                    'verdict': 'dismiss',
                })

            # 4.3 死代码检测
            if conn and func_table:
                if _is_dead_code(conn, file_path, line_number, func_table):
                    challenges.append({
                        'type': 'dead_code',
                        'verdict': 'downgrade',
                    })

            # 4.4 攻击链完整性挑战
            chain = f.get('attackChain', {})
            trace_method = ''
            if isinstance(chain, dict):
                trace_method = chain.get('traceMethod', f.get('traceMethod', ''))
            if trace_method == 'unknown' or not trace_method:
                challenges.append({
                    'type': 'incomplete_trace',
                    'verdict': 'downgrade',
                })

            # 4.5 严重级别合规校验（agent-rules.md §4 + taxonomy.severity_default）
            # 确定性规则（与 §4.2 完全一致）：
            #   - 基线优先：以 taxonomy.severity_default 为基线
            #   - 越级且无 severityRationale → 强制回落基线
            #   - 越级有 severityRationale 但超过 +1 档 → 上限收敛到 default+1
            #   - 线索级(default=low)因 +1 封顶自动限制为最高 medium，任何理由都不得升到 high/critical
            # 复用 correct_one_severity（与 Light bypass 单一来源），保持行为一致
            severity_correction_record = None
            if severity_defaults and risk_type_slug:
                severity_correction_record = correct_one_severity(
                    f, severity_defaults, corrected_by='verifier.py:challenge'
                )
                if severity_correction_record:
                    challenges.append({
                        'type': 'severity_violation',
                        'fromSeverity': severity_correction_record['from'],
                        'toSeverity': severity_correction_record['to'],
                        'riskType': risk_type_slug,
                        'verdict': 'downgrade',
                    })
                    severity_corrected_count += 1

            # 4.5b 攻击请求(PoC)不可得封顶（agent-rules.md §4.2 规则 6）
            # poc.available=='no' 且非豁免类型 → severity 封顶 Medium + humanReviewRequired
            poc_correction = _poc_cap_severity(f)
            if poc_correction:
                challenges.append({
                    'type': 'poc_not_obtainable',
                    'fromSeverity': poc_correction['from'],
                    'toSeverity': poc_correction['to'],
                    'riskType': risk_type_slug,
                    'verdict': 'downgrade',
                })
                severity_corrected_count += 1
                # PoC 封顶为最终（更低）约束，作为绑定的 severityCorrection 记录
                severity_correction_record = poc_correction

            # 4.6 跨 finding 冲突检查
            # （在后面的全局阶段处理，此处仅标记）

            # 综合判定
            has_dismiss = any(c['verdict'] == 'dismiss' for c in challenges)
            has_downgrade = any(c['verdict'] == 'downgrade' for c in challenges)

            if has_dismiss:
                f['challengeVerdict'] = 'dismissed'
                dismissed_count += 1
            elif has_downgrade:
                f['challengeVerdict'] = 'downgraded'
                downgraded_count += 1
            else:
                f['challengeVerdict'] = 'confirmed'
                confirmed_count += 1

            results.append({
                'findingId': f.get('findingId', ''),
                'filePath': file_path,
                'lineNumber': line_number,
                'riskType': f.get('riskType', ''),
                'severity': f.get('severity', ''),
                'severityCorrection': severity_correction_record,
                'verificationStatus': f.get('verificationStatus', ''),
                'challengeVerdict': f['challengeVerdict'],
                'challenges': challenges,
            })

        # 4.6 全局冲突检查：同一位置不同结论
        location_map = {}
        for r in results:
            loc_key = (r['filePath'], r['lineNumber'])
            location_map.setdefault(loc_key, []).append(r)
        conflict_count = 0
        for loc_key, loc_results in location_map.items():
            if len(loc_results) > 1:
                verdicts = set(r['challengeVerdict'] for r in loc_results)
                if len(verdicts) > 1:
                    conflict_count += 1
                    for r in loc_results:
                        r['challenges'].append({
                            'type': 'conflicting_findings',
                            'verdict': 'review',
                        })

    finally:
        if conn:
            conn.close()

    # 写入 challenge-results.json
    out_data = {
        'totalFindings': len(findings),
        'confirmed': confirmed_count,
        'dismissed': dismissed_count,
        'downgraded': downgraded_count,
        'severityCorrected': severity_corrected_count,
        'conflicts': conflict_count,
        'taxonomySeverityDefaultsLoaded': len(severity_defaults),
        'results': results,
    }
    out_path = batch_path / 'challenge-results.json'
    write_json_file(out_path, out_data)

    # 更新 filtered-findings.json（回写 challengeVerdict + severity 修正）
    write_json_file(batch_path / 'filtered-findings.json', filtered_data)

    log_ok(f"对抗审查完成: confirmed={confirmed_count}, "
           f"dismissed={dismissed_count}, downgraded={downgraded_count}, "
           f"severityCorrected={severity_corrected_count}, conflicts={conflict_count}")

    stdout_json({
        "status": "ok",
        "totalFindings": len(findings),
        "confirmed": confirmed_count,
        "dismissed": dismissed_count,
        "downgraded": downgraded_count,
        "severityCorrected": severity_corrected_count,
        "conflicts": conflict_count,
        "outputFile": "challenge-results.json",
    })


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def run_focus_filter(batch_dir):
    """聚焦模式确定性过滤（纯函数，不依赖 LLM / index.db）。

    5 条硬规则：
      1. severity 非 critical/high → 排除
      2. severity 违反 taxonomy.severity_default → 收敛后不在 critical/high → 排除
      3. poc.available == "no" → 封顶 medium → 排除
      4. poc.reachability 为 local-only/none → 排除
      5. riskType slug 在黑名单中 → 排除

    输入: merged-verified.json
    输出: focus-filtered.json（保留）, focus-excluded.json（排除+原因）
    更新: merged-verified.json, summary.json
    """
    batch_path = Path(batch_dir)
    merged_file = batch_path / 'merged-verified.json'

    if not merged_file.exists():
        log_warn("merged-verified.json 不存在，跳过聚焦过滤")
        stdout_json({"status": "skip", "message": "merged-verified.json not found"})
        return

    merged = load_json_file(merged_file)
    if not merged:
        log_warn("merged-verified.json 为空，跳过聚焦过滤")
        stdout_json({"status": "skip", "message": "merged-verified.json empty"})
        return

    findings = merged.get('findings', [])
    if not findings:
        log_info("无 findings，跳过聚焦过滤")
        stdout_json({"status": "ok", "totalKept": 0, "totalExcluded": 0})
        return

    # 加载 taxonomy 基线
    severity_defaults = _load_taxonomy_severity_defaults()

    kept, excluded = [], []
    exclude_counts = {}

    for f in findings:
        reasons = []
        slug = _normalize_risk_slug(f.get('riskType', ''))

        # 规则 2a: severity_default 基线校验（复用现有纯函数）
        if severity_defaults and slug:
            correct_one_severity(f, severity_defaults,
                                 corrected_by='verifier.py:focus-filter')

        # 规则 2b: PoC 不可得封顶（复用现有纯函数）
        _poc_cap_severity(f)

        # 规则 1: severity 排除
        sev = str(f.get('severity', '')).lower()
        if sev not in ('critical', 'high'):
            reasons.append({
                'rule': 'severity_below_high',
                'severity': sev,
            })

        # 规则 3: 外部可控性
        poc = f.get('poc', {})
        if isinstance(poc, dict):
            reach = (poc.get('reachability') or '').lower()
            if reach in ('local-only', 'none'):
                reasons.append({
                    'rule': 'not_externally_reachable',
                    'reachability': reach,
                })

        # 规则 4: 风险类型黑名单
        if slug in FOCUS_BLACKLIST:
            reasons.append({
                'rule': 'risk_type_not_high_focus',
                'riskType': slug,
            })

        if reasons:
            f['_focusExcludeReasons'] = reasons
            excluded.append(f)
        else:
            kept.append(f)

    # 统计排除原因
    for e in excluded:
        for r in e.get('_focusExcludeReasons', []):
            rule_name = r['rule']
            exclude_counts[rule_name] = exclude_counts.get(rule_name, 0) + 1

    # 写入聚焦产物
    write_json_file(batch_path / 'focus-filtered.json', {
        'findings': kept,
        'totalFindings': len(kept),
        'filteredAt': datetime.now(timezone.utc).isoformat(),
    })
    write_json_file(batch_path / 'focus-excluded.json', {
        'findings': excluded,
        'totalExcluded': len(excluded),
        'filteredAt': datetime.now(timezone.utc).isoformat(),
    })

    # 更新 downstream 产物
    merged['findings'] = kept
    summary = merged.get('summary', {})
    if summary:
        summary['mediumRisk'] = 0
        summary['lowRisk'] = 0
        summary['focusFiltered'] = len(excluded)
        summary['totalFindings'] = len(kept)
        summary['focusMode'] = True
    merged['summary'] = summary
    write_json_file(merged_file, merged)

    # 同步更新 summary.json
    summary_file = batch_path / 'summary.json'
    if summary_file.exists():
        sm = load_json_file(summary_file)
        if sm:
            sm['mediumRisk'] = 0
            sm['lowRisk'] = 0
            sm['focusFiltered'] = len(excluded)
            sm['totalFindings'] = len(kept)
            sm['focusMode'] = True
            write_json_file(summary_file, sm)

    log_ok(f"聚焦过滤完成：保留 {len(kept)} 个，排除 {len(excluded)} 个")
    stdout_json({
        'status': 'ok',
        'focusMode': True,
        'kept': len(kept),
        'excluded': len(excluded),
        'excludeReasons': exclude_counts,
    })


def main():
    parser = argparse.ArgumentParser(
        description='验证脚本：确定性验证 + 智能分级 + 并行拆分 + 攻击链索引验证 + 对抗审查 + 置信度评分 + 质量评估',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
子命令说明：
  pre-check     代码存在性校验 + 攻击链分级
  chain-verify  攻击链索引验证（利用 project-index.db 验证 source/sink/path/defense）
  split         按 sourceAgent 拆分 filtered-findings.json，供并行 verifier 实例消费
  challenge     确定性对抗审查（防御有效性、误报模式、死代码、攻击链完整性）
  score         确定性置信度评分（三维度 + traceMethod 上限 + 门控）
  quality       确定性全局审计质量评估（覆盖率 + 盲点 + 一致性）
  coverage      Deep 模式覆盖率门控检查
  focus-filter  聚焦模式确定性过滤（仅保留 critical+high，排除黑名单类型）

示例：
  %(prog)s pre-check --batch-dir .codebuddy/security-scan/runs/project-deep-20260325120000
  %(prog)s pre-check --batch-dir .codebuddy/security-scan/runs/project-deep-20260325120000 --input agents/vuln-scan.json --source-agent vuln-scan
  %(prog)s chain-verify --batch-dir .codebuddy/security-scan/runs/project-deep-20260325120000
  %(prog)s split --batch-dir .codebuddy/security-scan/runs/project-deep-20260325120000
  %(prog)s split --batch-dir .codebuddy/security-scan/runs/project-deep-20260325120000 --input filtered-findings-vuln.json
  %(prog)s challenge --batch-dir .codebuddy/security-scan/runs/project-deep-20260325120000
  %(prog)s score --batch-dir .codebuddy/security-scan/runs/project-deep-20260325120000
  %(prog)s quality --batch-dir .codebuddy/security-scan/runs/project-deep-20260325120000
  %(prog)s coverage --batch-dir .codebuddy/security-scan/runs/project-deep-20260325120000
  %(prog)s focus-filter --batch-dir .codebuddy/security-scan/runs/project-deep-20260325120000
        """
    )
    subparsers = parser.add_subparsers(dest='command')

    sp_pre_check = subparsers.add_parser('pre-check',
                                          help='代码存在性校验 + 攻击链分级')
    sp_pre_check.add_argument('--batch-dir', required=True,
                              help='批次目录路径')
    sp_pre_check.add_argument('--input', default=None,
                              help='输入文件路径（默认 merged-scan.json）。'
                                   '支持指定单个 agent 产物文件，实现流式验证。')
    sp_pre_check.add_argument('--source-agent', default=None,
                              help='来源 agent 标识（如 vuln-scan）。'
                                   '指定后额外输出分片文件 pre-check-results-{agent_slug}.json')

    sp_chain_verify = subparsers.add_parser('chain-verify',
                                            help='攻击链索引验证（利用 project-index.db）')
    sp_chain_verify.add_argument('--batch-dir', required=True,
                                 help='批次目录路径')

    sp_split = subparsers.add_parser('split',
                                      help='按 sourceAgent 拆分 findings 供并行验证')
    sp_split.add_argument('--batch-dir', required=True,
                          help='批次目录路径')
    sp_split.add_argument('--input', default=None,
                          help='输入文件路径（默认 filtered-findings.json）。'
                                '支持指定分片 filtered-findings 文件。')

    sp_score = subparsers.add_parser('score',
                                      help='确定性置信度评分')
    sp_score.add_argument('--batch-dir', required=True,
                          help='批次目录路径')

    sp_challenge = subparsers.add_parser('challenge',
                                         help='确定性对抗审查')
    sp_challenge.add_argument('--batch-dir', required=True,
                              help='批次目录路径')

    sp_quality = subparsers.add_parser('quality',
                                        help='确定性全局审计质量评估')
    sp_quality.add_argument('--batch-dir', required=True,
                            help='批次目录路径')

    sp_focus = subparsers.add_parser('focus-filter',
                                      help='聚焦模式确定性过滤（仅保留 critical+high）')
    sp_focus.add_argument('--batch-dir', required=True,
                           help='批次目录路径')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    batch_dir = Path(args.batch_dir)
    if not batch_dir.is_dir():
        log_error(f"批次目录不存在: {batch_dir}")
        stdout_json({"status": "error", "message": f"batch dir not found: {batch_dir}"})
        sys.exit(1)

    if args.command == 'pre-check':
        run_pre_check(batch_dir, input_file=getattr(args, 'input', None),
                      source_agent=getattr(args, 'source_agent', None))
    elif args.command == 'chain-verify':
        run_chain_verify(batch_dir)
    elif args.command == 'split':
        run_split(batch_dir, input_file=getattr(args, 'input', None))
    elif args.command == 'challenge':
        run_challenge(batch_dir)
    elif args.command == 'score':
        run_score(batch_dir)
    elif args.command == 'quality':
        run_quality(batch_dir)
    elif args.command == 'focus-filter':
        run_focus_filter(batch_dir)


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
