#!/usr/bin/env python3
"""
公共工具模块：供 merge_findings / generate_report / report_upload / checkpoint_verify / verifier 复用

包含：
  - Colors          终端颜色常量
  - 日志工具        log_info / log_ok / log_warn / log_error（带可配置 prefix）
  - 时间工具        _parse_datetime / format_beijing_time / BEIJING_TZ / LOCAL_TZ / TIME_FORMAT
  - Git 工具        get_git_branch / get_git_project_name / get_git_project_root / resolve_project_root
  - JSON 工具       load_json_file / write_json_file(原子) / incremental_write_findings / init_agent_output / stdout_json
  - 风险等级工具     SEVERITY_ORDER / severity_rank / get_risk_level_normalized
  - 配置工具        load_merged_config / _user_config_path / _project_config_path
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# 终端颜色
# ---------------------------------------------------------------------------

class Colors:
    """终端颜色输出"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


# ---------------------------------------------------------------------------
# 日志工具
# ---------------------------------------------------------------------------

def make_logger(prefix):
    """创建带有指定前缀的日志函数组。

    Returns:
        tuple: (log_info, log_ok, log_warn, log_error)
    """
    def log_info(msg):
        print(f"{Colors.CYAN}[{prefix}] {msg}{Colors.ENDC}", file=sys.stderr)

    def log_ok(msg):
        print(f"{Colors.GREEN}[{prefix}] ✓ {msg}{Colors.ENDC}", file=sys.stderr)

    def log_warn(msg):
        print(f"{Colors.WARNING}[{prefix}] [WARN] {msg}{Colors.ENDC}", file=sys.stderr)

    def log_error(msg):
        print(f"{Colors.FAIL}[{prefix}] ✗ {msg}{Colors.ENDC}", file=sys.stderr)

    return log_info, log_ok, log_warn, log_error


def print_colored(message, color=Colors.ENDC):
    """彩色打印到 stderr"""
    print(f"{color}{message}{Colors.ENDC}", file=sys.stderr)


def stdout_json(data):
    """将 JSON 数据输出到 stdout 供编排器解析"""
    print(json.dumps(data, ensure_ascii=False))


# ---------------------------------------------------------------------------
# 时间工具
# ---------------------------------------------------------------------------

BEIJING_TZ = timezone(timedelta(hours=8))
LOCAL_TZ = datetime.now().astimezone().tzinfo or timezone.utc
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _parse_datetime(value):
    """解析多种格式的日期时间值，返回 aware datetime 或 None"""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=LOCAL_TZ)
        return value
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 1e12:
            timestamp /= 1000.0
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        try:
            timestamp = int(text)
            if len(text) >= 13:
                timestamp /= 1000.0
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (ValueError, OSError):
            return None

    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=LOCAL_TZ)
        return dt
    except ValueError:
        pass

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d",
    ):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=LOCAL_TZ)
        except ValueError:
            continue

    return None


def format_beijing_time(value):
    """格式化为北京时间字符串"""
    dt = _parse_datetime(value)
    if not dt:
        return ""
    return dt.astimezone(BEIJING_TZ).strftime(TIME_FORMAT)


# ---------------------------------------------------------------------------
# Git 工具
# ---------------------------------------------------------------------------

def get_git_branch(base_path=None):
    """获取 Git 分支名"""
    base = Path(base_path) if base_path else Path.cwd()
    try:
        result = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    branch = result.stdout.strip()
    if not branch or branch == "HEAD":
        return ""
    return branch


def get_git_project_name(base_path=None):
    """从 git remote URL 或目录名推断项目名称"""
    base = Path(base_path) if base_path else Path.cwd()
    try:
        result = subprocess.run(
            ["git", "-C", str(base), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        )
        url = result.stdout.strip()
        if url:
            name = url.rstrip("/").rsplit("/", 1)[-1]
            if ":" in name:
                name = name.rsplit(":", 1)[-1]
            return name.removesuffix(".git") or ""
    except (OSError, subprocess.CalledProcessError):
        pass
    try:
        result = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
        top = result.stdout.strip()
        if top:
            return Path(top).name
    except (OSError, subprocess.CalledProcessError):
        pass
    return ""


def get_git_project_root(base_path=None):
    """获取 Git 仓库根目录，失败返回空字符串。"""
    base = Path(base_path) if base_path else Path.cwd()
    try:
        result = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""

    return result.stdout.strip()


def resolve_project_root(project_root: str = "") -> Path:
    """解析项目根目录。

    优先返回给定路径所在 Git 仓库的 top-level；不在 Git 仓库中时回退到原路径。
    """
    base = Path(project_root) if project_root else Path.cwd()
    git_root = get_git_project_root(base)
    if git_root:
        return Path(git_root)
    return base


# ---------------------------------------------------------------------------
# JSON 工具
# ---------------------------------------------------------------------------

def load_json_file(path):
    """安全加载 JSON 文件，失败返回 None"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def write_json_file(path, data):
    """原子写入 JSON 文件（temp + rename 模式）。

    使用临时文件写入后原子重命名，确保：
    - 写入过程中崩溃不会损坏已有文件
    - 并发读取者始终看到完整有效的 JSON
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), suffix='.tmp', prefix='.write_'
    )
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(path))  # POSIX 原子操作
    except BaseException:
        # 清理临时文件，避免泄漏
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def incremental_write_findings(path, new_findings, agent_name, checkpoint='',
                               status='partial'):
    """增量追加 findings 并原子写入。

    Agent 每完成一个 finding 后调用此函数：
    1. 读取现有输出文件（如存在）
    2. 合并新 findings
    3. 更新元数据（writeCount, lastCheckpoint, _integrity）
    4. 原子写入

    Args:
        path: 输出文件路径（如 agents/vuln-scan.json）
        new_findings: 新增的 finding 列表
        agent_name: Agent 名称
        checkpoint: 当前检查点标识（如 'sink-3' 或 'endpoint-7'）
        status: 当前状态 ('partial' | 'completed')

    Returns:
        更新后的完整数据 dict
    """
    existing = load_json_file(path) or {}
    findings = existing.get('findings', [])
    write_count = existing.get('writeCount', 0)

    # 合并新 findings
    findings.extend(new_findings if isinstance(new_findings, list) else [new_findings])
    write_count += 1

    data = {
        'agent': agent_name,
        'status': status,
        'findings': findings,
        'writeCount': write_count,
        'lastCheckpoint': checkpoint,
        '_integrity': {
            'expectedFindingsCount': len(findings),
            'actualFindingsCount': len(findings),
            'allPhasesCompleted': status == 'completed',
            'lastWriteTimestamp': datetime.now(timezone.utc).isoformat(),
        },
    }
    write_json_file(path, data)
    return data


def init_agent_output(path, agent_name):
    """Agent 启动时初始化输出文件（空 findings）。

    如果文件已存在且 status != 'completed'，返回现有数据供续扫。
    如果不存在，创建初始文件。

    陈旧保护：如果文件 mtime 早于当前扫描会话起始时间（.scan-session.json 中
    的 startedAt），视为上一次扫描遗留的产物，按"新扫描"处理而不是续扫，
    避免本次 agent 在陈旧 partial 数据基础上追加。

    Args:
        path: 输出文件路径
        agent_name: Agent 名称

    Returns:
        tuple: (existing_data_or_None, resume_checkpoint)
            - 如果是续扫：(existing_data, lastCheckpoint)
            - 如果是新扫描：(None, '')
    """
    existing = load_json_file(path)
    if existing and existing.get('status') not in ('completed', None):
        # 续扫前先校验产物是否属于本次会话
        # path 可能在 batch_dir/agents/ 下；向上找两层定位会话锁
        try:
            session_dir = Path(path).resolve().parent
            # 寻找 .scan-session.json：先看 path 同级，再看 path 父级
            session = load_scan_session(session_dir)
            if session is None:
                session = load_scan_session(session_dir.parent)
        except Exception:
            session = None

        if session is not None and not is_output_fresh(path, session):
            # 陈旧：按"新扫描"处理，覆写文件
            pass  # 继续走下面的初始化分支
        else:
            # 续扫：返回现有数据
            return existing, existing.get('lastCheckpoint', '')

    # 新扫描：写入初始文件
    data = {
        'agent': agent_name,
        'status': 'partial',
        'findings': [],
        'writeCount': 1,
        'lastCheckpoint': '',
        '_integrity': {
            'expectedFindingsCount': 0,
            'actualFindingsCount': 0,
            'allPhasesCompleted': False,
            'lastWriteTimestamp': datetime.now(timezone.utc).isoformat(),
        },
    }
    write_json_file(path, data)
    return None, ''


# ---------------------------------------------------------------------------
# 扫描会话（防陈旧数据复用）
# ---------------------------------------------------------------------------
#
# 问题背景：
#   security-scan 的批次目录（batch-dir）下会写入大量产物，多数为固定文件名：
#     agents/*.json / merged-scan.json / merged-verified.json /
#     finding-*.json / summary.json / gate-result.json
#
#   在以下场景中，固定文件名极易被"上一次扫描的残留"污染：
#     1. 同一 batch-id 内 agent 失败 / 被 killed / 超时未产出新文件
#     2. 同一 batch-id 内重跑，部分 agent 未重新写
#     3. should-launch-agent 仅检查 agent_output.exists() 就跳过执行
#   下游 merge / gate / upload 直接读取这些固定路径，无任何新鲜度校验，
#   会把上一次的旧 finding 当成本次扫描结果，造成误判。
#
# 修复策略 — 扫描会话锁：
#   1. 编排器在每次扫描启动时调用 begin_scan_session() 记录会话开始时间
#   2. begin_scan_session 主动清理 batch-dir 中早于本次会话的旧产物
#   3. 下游消费者通过 is_output_fresh() 校验文件 mtime ≥ 会话开始时间
#   4. 校验失败 → 视为缺失 / 陈旧，不进入合并 / 评估 / 上报

SESSION_LOCK_FILENAME = ".scan-session.json"

# 文件系统 mtime 与会话起始时间之间的容差（秒），
# 用于吸收 NTP 时钟微小漂移和部分文件系统 mtime 1s 精度截断
SESSION_MTIME_GRACE_SECONDS = 2.0

# 会话开启时主动清理的产物 glob（相对 batch-dir）
# 不动 project-index.db / batch-plan.json / 配置文件 / Hook 状态文件等
# 编排器主导的元数据文件（这些在 begin-session 之后由本次会话重新生成或保留）
SESSION_PURGE_GLOBS = (
    # 各 agent 直写产物
    "agents/*.json",
    # stage2 / stage3 合并产物
    "merged-scan.json",
    "merged-verified.json",
    "finding-*.json",
    "summary.json",
    # verifier 中间产物（chain-verify / challenge / score / quality / pre-check）
    "pre-check-results.json",
    "pre-check-results-*.json",
    "score-results.json",
    "quality-assessment.json",
    "chain-verify-results.json",
    "challenge-results.json",
    # 报告与上报
    "result-*.json",
    "security-scan-report.html",
    "security-scan-report.md",
    "gate-result.json",
    "report-sent.json",
    "fix-report-sent.json",
    "discarded-findings.json",
    "upload-payload.json",
    "fix-upload-payload.json",
)


def _scan_session_path(batch_dir):
    return Path(batch_dir) / SESSION_LOCK_FILENAME


def begin_scan_session(batch_dir, run_id, mode='', extra=None, purge=True):
    """开启一次扫描会话，写入会话锁，可选地清理早于本次会话的产物。

    时序保证：先清理旧产物，再写入会话锁。会话锁的 mtime 严格 ≥ 所有保留产物，
    后续以会话锁记录的 startedAt 作为"本次会话产物 mtime 下限"的判断基准。

    Args:
        batch_dir: 批次目录路径（编排器传入）
        run_id: 本次扫描运行标识（建议使用 batch_id 或唯一 UUID）
        mode: 扫描模式（fast / light / deep），便于审计调试
        extra: 额外 metadata，原样写入会话锁
        purge: 是否清理 SESSION_PURGE_GLOBS 匹配的早于本次会话的产物

    Returns:
        dict: 实际写入磁盘的 session 数据
    """
    import time

    batch_path = Path(batch_dir)
    batch_path.mkdir(parents=True, exist_ok=True)

    started_at = time.time()
    started_iso = datetime.fromtimestamp(started_at, tz=timezone.utc).isoformat()

    session = {
        'runId': run_id,
        'mode': mode,
        'startedAt': started_at,
        'startedAtIso': started_iso,
        'pid': os.getpid(),
    }
    if extra:
        # 不允许 extra 覆盖核心字段
        for k, v in extra.items():
            if k not in session:
                session[k] = v

    if purge:
        _purge_stale_outputs(batch_path, started_at)

    write_json_file(_scan_session_path(batch_path), session)
    return session


def load_scan_session(batch_dir):
    """读取当前批次目录的会话锁，找不到 / 损坏返回 None。"""
    return load_json_file(str(_scan_session_path(batch_dir)))


def session_started_at(session):
    """从 session 中提取 startedAt（float 秒）。无效返回 None。"""
    if not session:
        return None
    started_at = session.get('startedAt')
    if isinstance(started_at, (int, float)):
        return float(started_at)
    return None


def is_output_fresh(path, session, grace=SESSION_MTIME_GRACE_SECONDS):
    """判断给定文件是否属于当前会话（mtime + grace ≥ session.startedAt）。

    任一条件不满足都视为陈旧 / 缺失：
      - session 不存在或缺少 startedAt
      - 文件不存在或不可 stat

    Args:
        path: 文件路径（str / Path）
        session: load_scan_session 返回的 dict，None 一律视为陈旧
        grace: 文件系统 mtime 容差秒数

    Returns:
        bool: 是否新鲜
    """
    started_at = session_started_at(session)
    if started_at is None:
        return False
    try:
        mtime = Path(path).stat().st_mtime
    except (OSError, FileNotFoundError):
        return False
    return mtime + grace >= started_at


def _purge_stale_outputs(batch_path, started_at):
    """删除 batch_path 下早于 started_at 的指定产物。

    会话锁文件自身、目录、不在 SESSION_PURGE_GLOBS 范围内的其他文件不动。
    单个文件删除失败不阻塞会话开启，下游 mtime 校验会兜底拦截。
    """
    grace = SESSION_MTIME_GRACE_SECONDS
    lock_path = _scan_session_path(batch_path)
    for pattern in SESSION_PURGE_GLOBS:
        for fp in batch_path.glob(pattern):
            if fp == lock_path:
                continue
            try:
                if not fp.is_file():
                    continue
                if fp.stat().st_mtime + grace < started_at:
                    fp.unlink()
            except OSError:
                continue


# ---------------------------------------------------------------------------
# 风险等级标准化（4 级制）
# ---------------------------------------------------------------------------

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def severity_rank(level):
    """将风险等级映射为数值（用于排序/比较）"""
    return SEVERITY_ORDER.get(str(level).lower(), 0)


def get_risk_level_normalized(level):
    """标准化风险等级（4 级制：critical / high / medium / low）"""
    level_lower = str(level).lower()
    if level_lower in ('critical', '严重'):
        return 'critical'
    elif level_lower in ('high', '高'):
        return 'high'
    elif level_lower in ('medium', '中', 'moderate', '中等'):
        return 'medium'
    else:
        return 'low'


# ---------------------------------------------------------------------------
# 字段归一化：统一 camelCase 字段名（fail-fast，不接受任何别名）
# ---------------------------------------------------------------------------
#
# 设计原则（v2 严格模式）：
#   - Agent / merge / verifier / report 全链路只接受 camelCase 规范字段名
#   - 任何 PascalCase / snake_case / 旧别名 一律 fail-fast 抛 ValueError
#   - 本模块只做：(1) 空值规整；(2) 类型校正；(3) description 兜底拼装
#   - **不再做 PascalCase 翻译**：finding-*.json 与上游字段同名（camelCase）
#   - 唯一允许的 PascalCase 出口：scripts/report_upload.py 的 HTTP 上传载荷
#
# 规范字段（必填核心 + 可选扩展）：
#   核心: filePath, lineNumber, riskType, severity, riskCode, confidence,
#         description, recommendation, attackChain, findingId, sourceAgent,
#         verificationStatus
#   扩展: traceMethod, fixedCode, evidence, severityRationale, missingDefenses,
#         exploitScenario, fixSuggestion, callPath, cwe, endpoint, auditedBy,
#         challengeVerdict, defenses, attackPayload,
#         callChain, confidenceBreakdown, confidenceCeiling,
#         confidenceCeilingReason, component, currentVersion, fixedVersion,
#         cve, source, reasoning, dependencyFile, manifestFile
#
# 已废弃（任何输入若包含此类 key 立即拒绝）：
#   FilePath, LineNumber, RiskType, RiskLevel, riskLevel, RiskCode,
#   CodeSnippet, codeSnippet, RiskConfidence, riskConfidence, RiskDetail,
#   riskDetail, detail, Suggestions, suggestions, suggestion, remediation,
#   recommendedFix, recommended_fix, fix, FixedCode, fixed_code, FindingId,
#   finding_id, mergedId, file, file_path, line, line_number, type, category,
#   Severity, level, Confidence, risk_confidence, code, code_snippet, snippet,
#   originalCode, source_agent, trace_method, attackScenario, attackChains
# ---------------------------------------------------------------------------

# 旧字段名 → 规范 camelCase 映射（仅用于产生有用的报错信息）
_LEGACY_FIELD_HINTS = {
    'FilePath': 'filePath', 'file': 'filePath', 'file_path': 'filePath',
    'LineNumber': 'lineNumber', 'line': 'lineNumber', 'line_number': 'lineNumber',
    'RiskType': 'riskType', 'type': 'riskType', 'category': 'riskType',
    'RiskLevel': 'severity', 'riskLevel': 'severity', 'risk_level': 'severity',
    'Severity': 'severity', 'level': 'severity',
    'RiskConfidence': 'confidence', 'riskConfidence': 'confidence',
    'Confidence': 'confidence', 'risk_confidence': 'confidence',
    'RiskCode': 'riskCode', 'CodeSnippet': 'riskCode', 'codeSnippet': 'riskCode',
    'code': 'riskCode', 'code_snippet': 'riskCode', 'snippet': 'riskCode',
    'originalCode': 'riskCode',
    'RiskDetail': 'description', 'riskDetail': 'description', 'detail': 'description',
    'Suggestions': 'recommendation', 'suggestions': 'recommendation',
    'suggestion': 'recommendation', 'remediation': 'recommendation',
    'recommendedFix': 'recommendation', 'recommended_fix': 'recommendation',
    'fix': 'recommendation',
    'FixedCode': 'fixedCode', 'fixed_code': 'fixedCode',
    'FindingId': 'findingId', 'finding_id': 'findingId', 'mergedId': 'findingId',
    'source_agent': 'sourceAgent',
    'trace_method': 'traceMethod',
    'attackChains': 'attackChain', 'attackScenario': 'attackChain',
}


class LegacyFieldError(ValueError):
    """检测到旧字段名时抛出，由 merge_findings.py 捕获并 fail-fast 终止。"""
    pass


def assert_no_legacy_fields(f, source_agent=''):
    """检查 finding dict 是否包含已废弃字段名；命中即抛 LegacyFieldError。

    Args:
        f: finding dict
        source_agent: 来源标识（用于报错信息）

    Raises:
        LegacyFieldError: 若 dict 顶层 key 命中 _LEGACY_FIELD_HINTS
    """
    if not isinstance(f, dict):
        return
    bad = [k for k in f.keys() if k in _LEGACY_FIELD_HINTS]
    if bad:
        hints = ', '.join(f"{k}→{_LEGACY_FIELD_HINTS[k]}" for k in bad)
        src = source_agent or f.get('sourceAgent') or '<unknown>'
        raise LegacyFieldError(
            f"finding from {src} contains legacy field name(s): {hints}. "
            f"All findings MUST use canonical camelCase schema only "
            f"(see references/contracts/output-schemas.md)."
        )


def _coalesce(*values):
    """返回第一个非空/非None值（保留作为通用工具，部分历史脚本仍可能引用）。"""
    for v in values:
        if v is not None and v != '' and v != 0:
            return v
    return values[-1] if values else None


# ---------------------------------------------------------------------------
# 描述性字段（description）的兜底**组装器**
#
# 背景：v2 严格模式下 agent 必须直接填写 description 字段。本组装器仅作为
# 兜底（当 description 为空时），按预定义顺序收集 rationale/impact/...
# 等可选扩展字段，用中文小标题分段。
#
# 调用关系：
#   agent 产出 → normalize_finding() → description（兜底拼装）
#   → to_report_format() → finding-*.json（camelCase 同名输出）
# ---------------------------------------------------------------------------

# 描述性字段来源：(字段名, 中文小标题)。顺序即最终展示顺序。
_DESCRIPTION_SECTIONS = [
    ('summary', '概述'),
    ('rationale', '分析'),
    ('impact', '影响'),
    ('impactAnalysis', '影响分析'),
    ('defenseAnalysis', '防御分析'),
    ('attackNarrative', '攻击剧本'),
    ('exploitComplexity', '利用难度'),
    ('huntQuestion', '猎杀问题'),
]


def _format_attack_chain(chain):
    """把 attackChain 对象格式化为可读多行文本。支持 dict 和字符串两种输入。"""
    if isinstance(chain, str):
        return chain.strip()
    if not isinstance(chain, dict):
        return ''
    src = chain.get('source')
    sink = chain.get('sink')
    prop = chain.get('propagation') or []
    lines = []
    if src:
        lines.append(f"source: {src}")
    for step in prop:
        lines.append(f"  → {step}")
    if sink:
        lines.append(f"sink: {sink}")
    return '\n'.join(lines)


def _format_evidence_for_detail(evidence):
    """把 evidence 提取为描述文本。evidence 为列表（每个元素是 dict 或 str）或 str。"""
    if not evidence:
        return ''
    if isinstance(evidence, str):
        return evidence.strip()
    if isinstance(evidence, dict):
        for k in ('message', 'note', 'reason', 'detail', 'description'):
            v = evidence.get(k)
            if v:
                return str(v)
        return ''
    if isinstance(evidence, list):
        parts = []
        for item in evidence:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                for k in ('message', 'note', 'reason', 'detail', 'description'):
                    v = item.get(k)
                    if v:
                        parts.append(str(v))
                        break
        return '\n'.join(p for p in parts if p)
    return ''


def _compose_description(f):
    """返回 finding 的 description 文本。

    严格模式：只读 `description` 字段。如 description 为空，按
    _DESCRIPTION_SECTIONS 顺序拼装 rationale/impact/... 等可选扩展字段，
    并附加 attackChain（格式化）和 evidence（文本部分）作为兜底。

    Args:
        f: finding dict（已通过 assert_no_legacy_fields 校验）

    Returns:
        description 字符串（可能为空）
    """
    explicit = f.get('description')
    if explicit:
        return str(explicit)

    sections = []
    for key, label in _DESCRIPTION_SECTIONS:
        v = f.get(key)
        if v:
            sections.append(f"【{label}】{v}")

    chain_text = _format_attack_chain(f.get('attackChain'))
    if chain_text:
        sections.append(f"【攻击链】\n{chain_text}")

    evidence_text = _format_evidence_for_detail(f.get('evidence'))
    if evidence_text:
        sections.append(f"【证据】{evidence_text}")

    return '\n\n'.join(sections).strip()


def normalize_finding(raw, source_agent=''):
    """对 finding dict 做最小化规整（不再做字段别名翻译）。

    严格模式（v2）：
      - 输入必须是已经使用规范 camelCase 字段名的 dict
      - 包含任何旧字段名（FilePath/LineNumber/RiskCode/...）将抛
        LegacyFieldError，由 merge_findings.py 捕获并 fail-fast
      - 本函数只做：(1) 类型规整（lineNumber→int, confidence→int,
        severity→ critical/high/medium/low）；(2) 必填字段缺省值（空串/0）；
        (3) sourceAgent 缺省补全；(4) description 兜底拼装（仅当为空时）

    Args:
        raw: agent 输出的 finding dict
        source_agent: 来源 agent 名称（用于报错和缺省补全）

    Returns:
        规整后的 finding dict（保留所有原始字段，新增/覆盖核心字段）

    Raises:
        LegacyFieldError: raw 中包含已废弃字段名
    """
    if not isinstance(raw, dict):
        return raw

    assert_no_legacy_fields(raw, source_agent)

    f = dict(raw)  # 浅拷贝

    # ---- filePath ----
    f['filePath'] = str(f.get('filePath') or '')

    # ---- lineNumber ----
    raw_line = f.get('lineNumber')
    f['lineNumber'] = int(raw_line) if raw_line else 0

    # ---- riskType ----
    f['riskType'] = str(f.get('riskType') or '')

    # ---- severity ----
    f['severity'] = get_risk_level_normalized(f.get('severity') or '')

    # ---- confidence ----
    raw_conf = f.get('confidence')
    f['confidence'] = int(raw_conf) if raw_conf else 0

    # ---- riskCode ----
    f['riskCode'] = str(f.get('riskCode') or '')

    # ---- description（兜底拼装：仅当原始为空时才组装扩展字段）----
    f['description'] = _compose_description(f)

    # ---- recommendation ----
    f['recommendation'] = str(f.get('recommendation') or '')

    # ---- fixedCode ----
    f['fixedCode'] = str(f.get('fixedCode') or '')

    # ---- findingId ----
    f['findingId'] = str(f.get('findingId') or '')

    # ---- sourceAgent ----
    f['sourceAgent'] = str(f.get('sourceAgent') or source_agent or '')

    # ---- attackChain ----（仅做形态规整：list→取首元素）
    chain = f.get('attackChain')
    if isinstance(chain, list) and chain:
        chain = chain[0] if isinstance(chain[0], (dict, str)) else None
    if isinstance(chain, (dict, str)):
        f['attackChain'] = chain

    # ---- traceMethod（可从 attackChain 内嵌字段提升）----
    trace = f.get('traceMethod')
    if not trace and isinstance(f.get('attackChain'), dict):
        trace = f['attackChain'].get('traceMethod')
    if trace:
        f['traceMethod'] = str(trace)

    return f


def to_report_format(f):
    """报告层 finding 输出格式（恒等透传 camelCase）。

    v2 严格模式下不再做 PascalCase 翻译。本函数保留是为了：
      - 维持 merge_findings.py / generate_report.py 现有调用点不破坏
      - 集中 default 处理（severity/confidence 等核心字段缺省补全）

    输入应已通过 normalize_finding() 规整。

    Args:
        f: 已规整的 finding dict（camelCase）

    Returns:
        camelCase 格式的 finding dict（含核心字段默认值）
    """
    out = dict(f)  # 浅拷贝
    # 核心字段默认值兜底（避免下游 KeyError）
    out.setdefault('filePath', '')
    out.setdefault('riskType', '')
    out.setdefault('severity', 'medium')
    out.setdefault('lineNumber', 0)
    out.setdefault('riskCode', '')
    out.setdefault('confidence', 50)
    out.setdefault('description', '')
    out.setdefault('recommendation', '')
    out.setdefault('fixedCode', '')
    out.setdefault('verificationStatus', 'unverified')
    out.setdefault('challengeVerdict', '')
    out.setdefault('findingId', '')
    out.setdefault('sourceAgent', '')
    return out


# ---------------------------------------------------------------------------
# 分层配置加载
# ---------------------------------------------------------------------------
#
# 配置分为两级：
#   用户级: ~/.codebuddy/security-scan/config.json （Webhook URL 等个人配置）
#   项目级: {project}/.codebuddy/security-scan/config.json （门禁策略、auto_scan 等项目配置）
#
# 合并规则: 项目级 > 用户级 > 内置默认值（浅合并，顶层 key 覆盖）
# ---------------------------------------------------------------------------

_SCAN_CONFIG_DIR = "security-scan"
_SCAN_CONFIG_FILENAME = "config.json"


def _user_config_path() -> Path:
    """获取用户级配置文件路径: ~/.codebuddy/security-scan/config.json"""
    return Path.home() / ".codebuddy" / _SCAN_CONFIG_DIR / _SCAN_CONFIG_FILENAME


def _project_config_path(project_root: str = "") -> Path:
    """获取项目级配置文件路径: {project}/.codebuddy/security-scan/config.json"""
    base = resolve_project_root(project_root)
    return base / ".codebuddy" / _SCAN_CONFIG_DIR / _SCAN_CONFIG_FILENAME


def load_merged_config(project_root: str = "") -> dict:
    """加载合并后的配置（项目级 > 用户级）。

    合并策略：浅合并（shallow merge），顶层 key 项目级覆盖用户级。
    对于嵌套对象（如 notification, auto_scan），项目级整体覆盖用户级的同名 key。

    Args:
        project_root: 项目根目录路径。为空时使用 cwd。

    Returns:
        dict: 合并后的配置。无配置文件时返回空 dict。
    """
    merged = {}

    # 1. 加载用户级（基础层）
    user_path = _user_config_path()
    user_config = load_json_file(str(user_path))
    if user_config and isinstance(user_config, dict):
        merged.update(user_config)

    # 2. 加载项目级（覆盖层）
    project_path = _project_config_path(project_root)
    project_config = load_json_file(str(project_path))
    if project_config and isinstance(project_config, dict):
        merged.update(project_config)

    return merged


# ---------------------------------------------------------------------------
# 批次目录相关
# ---------------------------------------------------------------------------

SCAN_DIR = "security-scan"
RUNS_DIR = "runs"
MEMORY_DIR = "memory"
LEGACY_OUTPUT_DIR = "security-scan-output"
BATCH_PREFIXES = ("project-deep-", "project-light-", "project-fast-",
                  "diff-deep-", "diff-light-", "diff-fast-")


def get_security_scan_dir(project_root=""):
    """返回项目级 Security-Scan 目录：{project}/.codebuddy/security-scan。"""
    base = resolve_project_root(project_root)
    return base / ".codebuddy" / SCAN_DIR


def get_scan_runs_dir(project_root=""):
    """返回扫描批次根目录：{project}/.codebuddy/security-scan/runs。"""
    return get_security_scan_dir(project_root) / RUNS_DIR


def get_default_batch_dir(audit_batch_id, project_root=""):
    """返回默认批次目录：{project}/.codebuddy/security-scan/runs/{audit_batch_id}。"""
    return get_scan_runs_dir(project_root) / str(audit_batch_id)


def get_memory_db_path(project_root=""):
    """返回长期记忆库路径：{project}/.codebuddy/security-scan/memory/project-memory.db。"""
    return get_security_scan_dir(project_root) / MEMORY_DIR / "project-memory.db"


def get_legacy_memory_db_path(batch_dir):
    """返回旧版长期记忆库路径：{legacy-output}/.memory/project-memory.db。"""
    return Path(batch_dir).parent / ".memory" / "project-memory.db"


def resolve_project_root_from_batch_dir(batch_dir):
    """从批次目录反推项目根目录，支持新旧产物路径。"""
    batch_path = Path(batch_dir)
    candidate = None

    if (
        batch_path.parent.name == RUNS_DIR
        and batch_path.parent.parent.name == SCAN_DIR
        and batch_path.parent.parent.parent.name == ".codebuddy"
    ):
        candidate = batch_path.parent.parent.parent.parent
    elif batch_path.parent.name == LEGACY_OUTPUT_DIR:
        candidate = batch_path.parent.parent
    else:
        candidate = batch_path.parent

    git_root = get_git_project_root(candidate)
    return Path(git_root) if git_root else Path(candidate)


def get_scan_output_dirs(cwd=None):
    """返回扫描批次候选根目录列表（按优先级排序，去重）。

    新路径优先：{project}/.codebuddy/security-scan/runs；旧路径保留只读兼容。

    Args:
        cwd: 项目工作目录（可选）

    Returns:
        list[Path]: 候选目录列表（已去重），可能不存在
    """
    candidates = []
    base = Path(cwd) if cwd else Path.cwd()
    project_root = resolve_project_root(str(base))
    candidates.append(get_scan_runs_dir(str(project_root)))
    candidates.append(project_root / LEGACY_OUTPUT_DIR)
    if cwd:
        candidates.append(Path(cwd) / LEGACY_OUTPUT_DIR)
    candidates.append(Path.cwd() / LEGACY_OUTPUT_DIR)
    candidates.append(Path("/tmp") / LEGACY_OUTPUT_DIR)

    dirs = []
    seen = set()
    for p in candidates:
        resolved = p.resolve()
        if resolved not in seen:
            seen.add(resolved)
            dirs.append(p)
    return dirs
