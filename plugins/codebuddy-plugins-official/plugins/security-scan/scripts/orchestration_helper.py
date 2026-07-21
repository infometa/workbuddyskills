#!/usr/bin/env python3
"""
编排器辅助工具 — 集中处理编排器中的确定性决策逻辑

跨平台：Python3 内置模块，零外部依赖。

子命令：
  1. check-phase-gate     — 检查 phase 完成状态
  2. should-launch-agent  — 根据 phase 状态决定是否启动 agent
  3. should-rerun-agent   — 检测 phase 更新，决定是否需要 re-run
  4. determine-trace-method — 根据工具可用性决定 traceMethod
  5. summarize-progress   — 汇总当前扫描进度
  6. detect-framework     — 检测项目框架/技术栈
  7. begin-session        — 开启扫描会话（写入 .scan-session.json，清理陈旧产物）
  8. check-stale-outputs  — 列出 batch-dir 中早于当前会话的陈旧产物

设计原则：
  - 替代编排器 Agent 中的判断逻辑（if/else），确保确定性
  - 所有输出为 JSON，无 side effect（不写 DB，不修改文件）
  - 编排器只需读 stdout 中的 action 字段，做对应操作即可
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    begin_scan_session,
    load_scan_session,
    is_output_fresh,
    session_started_at,
    SESSION_PURGE_GLOBS,
)


# ─── 工具函数 ────────────────────────────────────────────────

def _connect_db(batch_dir, readonly=True):
    """连接 project-index.db，启用 WAL 模式和 busy_timeout，带重试机制"""
    db_path = str(Path(batch_dir) / "project-index.db")
    if not os.path.exists(db_path):
        return None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            uri = f"file:{db_path}?mode=ro" if readonly else db_path
            conn = sqlite3.connect(uri if readonly else db_path, uri=readonly)
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


def _get_phase_status(conn):
    """获取所有 phase 的状态"""
    phases = {}
    for row in conn.execute("SELECT phase, status, completed_at FROM phase_status"):
        phases[row["phase"]] = {
            "status": row["status"],
            "completed_at": row["completed_at"],
        }
    return phases


def _get_table_counts(conn):
    """获取关键表的行数"""
    counts = {}
    for table in ["files", "sinks", "endpoints", "defenses", "call_graph",
                   "attack_surface", "indexer_findings", "ast_functions", "ast_refined_sinks"]:
        try:
            row = conn.execute(f"SELECT COUNT(*) as c FROM {table}").fetchone()
            counts[table] = row["c"]
        except sqlite3.OperationalError:
            counts[table] = 0
    return counts


# ─── Agent 依赖定义 ──────────────────────────────────────────

# 每个 agent 启动所需的最低 phase 和表依赖
AGENT_REQUIREMENTS = {
    "vuln-scan": {
        "min_phase": "phase1",
        "required_tables": ["sinks"],
        "optimal_phase": "phase2",
        "description": "Sink-Driven 漏洞扫描",
    },
    "logic-scan": {
        "min_phase": "phase2",
        "required_tables": ["endpoints"],
        "optimal_phase": "phase2",
        "description": "认证授权 + 业务逻辑审计",
    },
    "red-team": {
        "min_phase": "phase1",
        "required_tables": [],  # 可在空数据下运行（Grep-first）
        "optimal_phase": "phase2",
        "description": "红队对抗深度审计",
    },
}

# Phase 优先级排序（用于比较 phase 新旧）
PHASE_ORDER = {"phase1": 1, "phase1_5": 2, "phase2": 3}


# ─── 命令: check-phase-gate ──────────────────────────────────

def cmd_check_phase_gate(args):
    """检查指定 phase 是否已完成"""
    conn = _connect_db(args.batch_dir)
    if not conn:
        print(json.dumps({
            "phase": args.required_phase,
            "status": "unknown",
            "can_proceed": False,
            "reason": "database_not_found"
        }))
        return

    try:
        phases = _get_phase_status(conn)
        phase_info = phases.get(args.required_phase, {"status": "pending", "completed_at": None})

        can_proceed = phase_info["status"] == "completed"

        # 也检查当前最高已完成 phase
        completed_phases = [p for p, info in phases.items() if info["status"] == "completed"]
        highest_completed = max(completed_phases, key=lambda p: PHASE_ORDER.get(p, 0)) if completed_phases else None

        result = {
            "phase": args.required_phase,
            "status": phase_info["status"],
            "completed_at": phase_info["completed_at"],
            "can_proceed": can_proceed,
            "all_phases": {p: info["status"] for p, info in phases.items()},
            "highest_completed_phase": highest_completed,
        }
    finally:
        conn.close()

    print(json.dumps(result, ensure_ascii=False))


# ─── 命令: should-launch-agent ───────────────────────────────

def cmd_should_launch_agent(args):
    """根据 phase 状态和 agent 依赖决定是否启动 agent"""
    agent_name = args.agent
    req = AGENT_REQUIREMENTS.get(agent_name)

    if not req:
        print(json.dumps({
            "agent": agent_name,
            "action": "error",
            "reason": f"Unknown agent: {agent_name}. Known: {list(AGENT_REQUIREMENTS.keys())}"
        }))
        return

    conn = _connect_db(args.batch_dir)
    if not conn:
        print(json.dumps({
            "agent": agent_name,
            "action": "wait",
            "reason": "database_not_found"
        }))
        return

    try:
        phases = _get_phase_status(conn)
        counts = _get_table_counts(conn)

        # 检查最低 phase 是否已完成
        min_phase = req["min_phase"]
        min_phase_info = phases.get(min_phase, {"status": "pending"})
        phase_ready = min_phase_info["status"] == "completed"

        # 检查必需表是否有数据
        tables_ready = all(counts.get(t, 0) > 0 for t in req["required_tables"])

        # 检查 agent 是否已有输出
        # 接入扫描会话锁：仅当输出文件 mtime ≥ 会话起始时间才算"本会话已运行"
        # 否则视为陈旧产物，需要重新启动 agent（避免使用上一次扫描的残留 finding）
        agent_output = Path(args.batch_dir) / "agents" / f"{agent_name}.json"
        session = load_scan_session(args.batch_dir)
        output_exists = agent_output.exists()
        output_fresh = is_output_fresh(agent_output, session) if session else output_exists
        already_run = output_exists and output_fresh
        stale_output = output_exists and session is not None and not output_fresh

        # 决定 action
        if already_run:
            action = "already_run"
            reason = f"Output exists and fresh: {agent_output}"
        elif stale_output:
            action = "launch"
            reason = (
                f"Stale output detected (mtime < session.startedAt): {agent_output}; "
                f"will be overwritten by new run"
            )
        elif phase_ready and tables_ready:
            action = "launch"
            reason = f"{min_phase} completed, required tables populated"
        elif phase_ready and not tables_ready:
            missing = [t for t in req["required_tables"] if counts.get(t, 0) == 0]
            action = "wait"
            reason = f"Phase ready but missing data in: {missing}"
        else:
            action = "wait"
            reason = f"Waiting for {min_phase} (current: {min_phase_info['status']})"

        # 判断当前 phase 是否已达最优
        optimal_phase = req["optimal_phase"]
        optimal_info = phases.get(optimal_phase, {"status": "pending"})
        at_optimal = optimal_info["status"] == "completed"

        result = {
            "agent": agent_name,
            "action": action,
            "reason": reason,
            "required_phase": min_phase,
            "optimal_phase": optimal_phase,
            "phase_ready": phase_ready,
            "at_optimal_phase": at_optimal,
            "tables_ready": tables_ready,
            "already_run": already_run,
            "stale_output": stale_output,
            "session_runId": session.get("runId") if session else None,
            "table_counts": {t: counts.get(t, 0) for t in req["required_tables"]},
            "all_phases": {p: info["status"] for p, info in phases.items()},
        }

    finally:
        conn.close()

    print(json.dumps(result, ensure_ascii=False))


# ─── 命令: should-rerun-agent ────────────────────────────────

def cmd_should_rerun_agent(args):
    """检测 phase 更新，决定是否需要 re-run agent"""
    agent_name = args.agent
    req = AGENT_REQUIREMENTS.get(agent_name)

    if not req:
        print(json.dumps({
            "agent": agent_name,
            "action": "error",
            "reason": f"Unknown agent: {agent_name}"
        }))
        return

    agent_output = Path(args.batch_dir) / "agents" / f"{agent_name}.json"

    if not agent_output.exists():
        print(json.dumps({
            "agent": agent_name,
            "action": "not_applicable",
            "reason": "no_prior_run"
        }))
        return

    # 校验产物是否属于本次扫描会话：陈旧产物（mtime < session.startedAt）应当忽略，
    # 走 not_applicable 让 should-launch-agent 后续把 stale_output 转化为 launch
    session = load_scan_session(args.batch_dir)
    if session is not None and not is_output_fresh(agent_output, session):
        print(json.dumps({
            "agent": agent_name,
            "action": "not_applicable",
            "reason": "stale_prior_run",
            "stale_output": str(agent_output),
            "session_runId": session.get("runId"),
        }))
        return

    # 读取 agent 输出中的 metadata.index_phase
    try:
        with open(agent_output, "r", encoding="utf-8") as f:
            agent_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(json.dumps({
            "agent": agent_name,
            "action": "error",
            "reason": f"Cannot read agent output: {e}"
        }))
        return

    prior_phase = agent_data.get("metadata", {}).get("index_phase", "unknown")
    agent_status = agent_data.get("status", "unknown")

    # 获取当前 DB 中的 phase 状态
    conn = _connect_db(args.batch_dir)
    if not conn:
        print(json.dumps({
            "agent": agent_name,
            "action": "error",
            "reason": "database_not_found"
        }))
        return

    try:
        phases = _get_phase_status(conn)
        completed_phases = [p for p, info in phases.items() if info["status"] == "completed"]
        latest_phase = max(completed_phases, key=lambda p: PHASE_ORDER.get(p, 0)) if completed_phases else None

        prior_order = PHASE_ORDER.get(prior_phase, 0)
        latest_order = PHASE_ORDER.get(latest_phase, 0) if latest_phase else 0

        # 检查 re-run 次数限制
        max_reruns = int(args.max_reruns) if args.max_reruns else 2
        rerun_count = agent_data.get("metadata", {}).get("rerun_count", 0)

        if rerun_count >= max_reruns:
            action = "skip"
            reason = f"Max reruns reached ({rerun_count}/{max_reruns})"
        elif latest_order > prior_order:
            action = "rerun"
            reason = f"New data available: {prior_phase} → {latest_phase}"
        elif agent_status == "partial":
            action = "continue"
            reason = "Agent reported partial completion, can continue"
        else:
            action = "no_action"
            reason = f"Phase unchanged ({prior_phase})"

        result = {
            "agent": agent_name,
            "action": action,
            "reason": reason,
            "prior_phase": prior_phase,
            "latest_phase": latest_phase,
            "agent_status": agent_status,
            "rerun_count": rerun_count,
            "max_reruns": max_reruns,
            "instruction": None,
        }

        if action == "rerun":
            result["instruction"] = (
                f"rm -f {agent_output} && relaunch {agent_name} "
                f"(new data from {latest_phase})"
            )
        elif action == "continue":
            pending = agent_data.get("metadata", {}).get("pendingSinks", [])
            result["instruction"] = (
                f"Resume {agent_name} with {len(pending)} pending items"
            )

    finally:
        conn.close()

    print(json.dumps(result, ensure_ascii=False))


# ─── 命令: begin-session ──────────────────────────────────────
#
# 职责：在每次扫描启动前调用，写入 .scan-session.json 并清理早于本次会话的固定文件名产物。
#
# 编排器调用时机：
#   - 全量扫描启动时（创建新 batch-dir 后立即调用）
#   - 续扫时（即便沿用同 batch-id，也应重新 begin-session 以拉新会话起始时间）
#   - 用户明确要求 force-rescan 时
#
# 不应在以下场景调用（避免误清理本次扫描产物）：
#   - merge / gate / upload 阶段
#   - 单独 re-run 一个 agent

def cmd_begin_session(args):
    """开启扫描会话，写入会话锁，可选地清理陈旧产物。"""
    batch_dir = Path(args.batch_dir)
    run_id = args.run_id or batch_dir.name
    purge = args.no_purge is False

    extra = {}
    if args.scan_command:
        extra["scanCommand"] = args.scan_command
    if args.project_path:
        extra["projectPath"] = args.project_path

    session = begin_scan_session(
        batch_dir=batch_dir,
        run_id=run_id,
        mode=args.mode or "",
        extra=extra or None,
        purge=purge,
    )

    print(json.dumps({
        "status": "ok",
        "runId": session["runId"],
        "mode": session.get("mode", ""),
        "startedAt": session["startedAt"],
        "startedAtIso": session["startedAtIso"],
        "purge": purge,
        "purgeGlobs": list(SESSION_PURGE_GLOBS) if purge else [],
        "batchDir": str(batch_dir),
    }, ensure_ascii=False))


# ─── 命令: check-stale-outputs ────────────────────────────────
#
# 职责：列出 batch-dir 中早于当前会话的陈旧产物，编排器可据此决定是否需要重跑某个 agent。

def cmd_check_stale_outputs(args):
    """列出 batch_dir 中早于会话起始时间的 finding/summary 产物。"""
    batch_dir = Path(args.batch_dir)
    session = load_scan_session(batch_dir)

    if session is None:
        print(json.dumps({
            "status": "no_session",
            "reason": "scan_session_not_found",
            "hint": "Run begin-session first to enable stale detection.",
        }, ensure_ascii=False))
        return

    stale = []
    fresh = []
    if batch_dir.is_dir():
        for pattern in SESSION_PURGE_GLOBS:
            for fp in sorted(batch_dir.glob(pattern)):
                if not fp.is_file():
                    continue
                try:
                    mtime = fp.stat().st_mtime
                except OSError:
                    continue
                entry = {
                    "path": str(fp.relative_to(batch_dir)),
                    "mtime": mtime,
                }
                if is_output_fresh(fp, session):
                    fresh.append(entry)
                else:
                    stale.append(entry)

    print(json.dumps({
        "status": "ok",
        "runId": session.get("runId"),
        "startedAt": session_started_at(session),
        "startedAtIso": session.get("startedAtIso"),
        "staleCount": len(stale),
        "freshCount": len(fresh),
        "stale": stale,
        "fresh": fresh,
    }, ensure_ascii=False))


# ─── 命令: determine-trace-method ────────────────────────────

def cmd_determine_trace_method(args):
    """根据工具可用性和 phase 状态决定 traceMethod"""
    conn = _connect_db(args.batch_dir)

    lsp_available = args.lsp_available == "true" if args.lsp_available else False
    has_ast = False
    has_call_graph = False

    if conn:
        try:
            counts = _get_table_counts(conn)
            has_ast = counts.get("ast_functions", 0) > 0
            has_call_graph = counts.get("call_graph", 0) > 0

            phases = _get_phase_status(conn)
            phase2_done = phases.get("phase2", {}).get("status") == "completed"

            # 如果 phase2 完成且 call_graph 有数据，LSP 数据已完整
            if phase2_done and has_call_graph:
                lsp_available = True
        finally:
            conn.close()

    if lsp_available and has_call_graph:
        trace_method = "LSP"
        confidence_cap = 100
        quality = "optimal"
    elif has_ast:
        trace_method = "Grep+AST"
        confidence_cap = 95
        quality = "good"
    else:
        trace_method = "Grep+Read"
        confidence_cap = 90
        quality = "baseline"

    result = {
        "traceMethod": trace_method,
        "confidence_cap": confidence_cap,
        "quality": quality,
        "lsp_available": lsp_available,
        "has_ast": has_ast,
        "has_call_graph": has_call_graph,
    }
    print(json.dumps(result, ensure_ascii=False))


# ─── 命令: summarize-progress ────────────────────────────────

def cmd_summarize_progress(args):
    """汇总当前扫描进度"""
    conn = _connect_db(args.batch_dir)
    if not conn:
        print(json.dumps({"error": "database_not_found"}))
        return

    try:
        phases = _get_phase_status(conn)
        counts = _get_table_counts(conn)

        # 检查各 agent 输出状态
        agents_dir = Path(args.batch_dir) / "agents"
        agent_statuses = {}
        for agent_name in ["vuln-scan", "logic-scan", "red-team"]:
            output_file = agents_dir / f"{agent_name}.json"
            if output_file.exists():
                try:
                    with open(output_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    agent_statuses[agent_name] = {
                        "status": data.get("status", "unknown"),
                        "findings": len(data.get("findings", [])),
                        "index_phase": data.get("metadata", {}).get("index_phase", "unknown"),
                    }
                except (json.JSONDecodeError, IOError):
                    agent_statuses[agent_name] = {"status": "error", "findings": 0}
            else:
                agent_statuses[agent_name] = {"status": "not_started", "findings": 0}

        # 检查验证状态
        verifier_statuses = {}
        for vname in ["verifier-vuln", "verifier-logic", "verifier-redteam"]:
            vfile = agents_dir / f"{vname}.json"
            if vfile.exists():
                try:
                    with open(vfile, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    verifier_statuses[vname] = {
                        "status": data.get("status", "unknown"),
                        "findings": len(data.get("findings", [])),
                    }
                except (json.JSONDecodeError, IOError):
                    verifier_statuses[vname] = {"status": "error"}
            else:
                verifier_statuses[vname] = {"status": "not_started"}

        # 检查 merged-scan.json
        merged_file = Path(args.batch_dir) / "merged-scan.json"
        merged_status = "completed" if merged_file.exists() else "not_started"

        # 检查报告
        report_file = Path(args.batch_dir) / "security-scan-report.html"
        report_status = "completed" if report_file.exists() else "not_started"

        # 计算总体进度
        total_steps = 8  # phase1 + phase1_5 + phase2 + 3 agents + merge + report
        completed_steps = 0
        completed_steps += sum(1 for p in phases.values() if p["status"] == "completed")
        completed_steps += sum(1 for a in agent_statuses.values() if a["status"] in ("completed", "partial"))
        if merged_status == "completed":
            completed_steps += 1
        if report_status == "completed":
            completed_steps += 1

        # 判断下一步操作
        next_actions = _determine_next_actions(phases, counts, agent_statuses)

        result = {
            "phases": {p: info["status"] for p, info in phases.items()},
            "table_counts": counts,
            "agents": agent_statuses,
            "verifiers": verifier_statuses,
            "merged_scan": merged_status,
            "report": report_status,
            "progress": f"{completed_steps}/{total_steps}",
            "progress_pct": round(completed_steps / total_steps * 100),
            "next_actions": next_actions,
        }
    finally:
        conn.close()

    print(json.dumps(result, ensure_ascii=False))


def _determine_next_actions(phases, counts, agent_statuses):
    """根据当前状态确定下一步操作"""
    actions = []

    phase_map = {p: info["status"] for p, info in phases.items()}

    # 如果 indexer 还在运行
    if phase_map.get("phase1") != "completed":
        actions.append({"action": "wait_indexer", "detail": "Waiting for indexer phase1"})
        return actions

    # Phase1 完成后的操作
    for agent_name in ["vuln-scan", "red-team"]:
        status = agent_statuses.get(agent_name, {}).get("status", "not_started")
        if status == "not_started":
            actions.append({"action": "launch_agent", "agent": agent_name, "phase": "phase1"})

    # Phase1_5 完成后的操作
    if phase_map.get("phase1_5") == "completed":
        for agent_name in ["vuln-scan", "red-team"]:
            status = agent_statuses.get(agent_name, {})
            if status.get("status") in ("completed", "partial") and status.get("index_phase") == "phase1":
                actions.append({"action": "rerun_agent", "agent": agent_name, "reason": "phase1_5 data available"})

    # Phase2 完成后的操作
    if phase_map.get("phase2") == "completed":
        logic_status = agent_statuses.get("logic-scan", {}).get("status", "not_started")
        if logic_status == "not_started":
            actions.append({"action": "launch_agent", "agent": "logic-scan", "phase": "phase2"})

        for agent_name in ["vuln-scan", "red-team"]:
            status = agent_statuses.get(agent_name, {})
            if status.get("index_phase") not in ("phase2", None):
                actions.append({"action": "rerun_agent", "agent": agent_name, "reason": "phase2 LSP data available"})

    # 所有 agent 完成后
    all_done = all(
        agent_statuses.get(a, {}).get("status") in ("completed", "partial")
        for a in ["vuln-scan", "logic-scan", "red-team"]
    )
    if all_done and phase_map.get("phase2") == "completed":
        actions.append({"action": "start_verification", "detail": "All agents completed, ready for verification"})

    if not actions:
        actions.append({"action": "wait", "detail": "Waiting for ongoing operations to complete"})

    return actions


# ─── 命令: detect-framework ──────────────────────────────────

FRAMEWORK_MARKERS = {
    "spring-boot": {
        "files": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "content_patterns": ["spring-boot"],
        "language": "java",
    },
    "spring-mvc": {
        "files": ["pom.xml", "build.gradle"],
        "content_patterns": ["spring-webmvc", "spring-web"],
        "language": "java",
    },
    "spring-security": {
        "files": ["pom.xml", "build.gradle"],
        "content_patterns": ["spring-security"],
        "language": "java",
    },
    "ktor": {
        "files": ["build.gradle.kts", "build.gradle"],
        "content_patterns": ["io.ktor"],
        "language": "kotlin",
    },
    "spring-boot-kotlin": {
        "files": ["build.gradle.kts"],
        "content_patterns": ["kotlin-spring", "kotlin(\"spring\")", "kotlin(\"jpa\")"],
        "language": "kotlin",
    },
    "django": {
        "files": ["manage.py", "requirements.txt", "setup.py", "pyproject.toml"],
        "content_patterns": ["django"],
        "language": "python",
    },
    "flask": {
        "files": ["requirements.txt", "setup.py", "pyproject.toml"],
        "content_patterns": ["flask"],
        "language": "python",
    },
    "fastapi": {
        "files": ["requirements.txt", "setup.py", "pyproject.toml"],
        "content_patterns": ["fastapi"],
        "language": "python",
    },
    "express": {
        "files": ["package.json"],
        "content_patterns": ["express"],
        "language": "javascript",
    },
    "nestjs": {
        "files": ["package.json"],
        "content_patterns": ["@nestjs/core"],
        "language": "typescript",
    },
    "gin": {
        "files": ["go.mod"],
        "content_patterns": ["gin-gonic"],
        "language": "go",
    },
    "laravel": {
        "files": ["composer.json", "artisan"],
        "content_patterns": ["laravel"],
        "language": "php",
    },
}

BUILD_TOOL_MARKERS = {
    "maven": ["pom.xml"],
    "gradle": ["build.gradle", "build.gradle.kts"],
    "npm": ["package.json"],
    "pip": ["requirements.txt", "setup.py", "pyproject.toml"],
    "go-mod": ["go.mod"],
    "composer": ["composer.json"],
}

KNOWLEDGE_FILE_MAP = {
    "spring-boot": ["spring-security.yaml", "java-common.yaml"],
    "spring-mvc": ["spring-security.yaml", "java-common.yaml"],
    "spring-security": ["spring-security.yaml"],
    "ktor": ["kotlin-common.yaml"],
    "spring-boot-kotlin": ["spring-security.yaml", "kotlin-common.yaml"],
    "django": ["python-common.yaml"],
    "flask": ["python-common.yaml"],
    "fastapi": ["python-common.yaml"],
    "express": ["node-common.yaml"],
    "nestjs": ["node-common.yaml"],
    "gin": ["go-common.yaml"],
    "laravel": ["php-common.yaml"],
}

# ─── 业务场景识别（仅 Light 模式消费） ─────────────────────────
# Fast/Deep 不读取 scenarios / lightScenarioRules 字段，行为不变。
#
# 设计要点：
#   - manifest 命中加 30 分（核心信号）
#   - 代码 pattern 命中加 20 分（最多累计 40 分）
#   - 文件布局命中加 20 分（最多累计 20 分）
#   - 单场景置信度封顶 100；scenarioConfidence ≥ SCENARIO_MIN_CONFIDENCE 才入选
#   - 同时活跃场景 ≤ SCENARIO_MAX_ACTIVE；> 3 场景时追加 "mixed" 标签
import re as _re_scen

SCENARIO_ENUM = (
    "web",
    "cloud_native_service",
    "ai_agent_app",
    "sandbox_runtime",
    "business_payment",
    "mobile_app",
    "desktop_app",
    "mixed",
)

# 场景信号（manifest 依赖正则 / 代码模式正则 / 文件布局 glob）
SCENARIO_MARKERS = {
    "cloud_native_service": {
        "deps": [
            r"\bcos-python-sdk-v5\b",
            r"\bqcloud-cos\b",
            r"\bcos-nodejs-sdk\b",
            r"\btencentcloud-sdk(-python|-nodejs|-go|-java)?\b",
            r"\bboto3\b",
            r"\baws-sdk\b",
            r"\baliyun-(oss|sdk)",
            r"\bgoogle-cloud-storage\b",
        ],
        "code_patterns": [
            r"\bput_object\(",
            r"\bget_object\(",
            r"\bcos_client\b",
            r"\bcoscgi\b",
            r"qcloud_cos",
            r"\bSTS\b.*temporary",
            r"169\.254\.169\.254",
            r"metadata\.tencentyun\.com",
        ],
        "fs_layout": ["**/cos*.py", "**/oss*.go", "**/coscgi*", "k8s/**/*.yaml"],
    },
    "ai_agent_app": {
        "deps": [
            r"\blangchain\b",
            r"\blangchain-core\b",
            r"\bllama-?index\b",
            r"\bllamaindex\b",
            r"\bautogen\b",
            r"\bcrewai\b",
            r"\bopenai\b",
            r"\banthropic\b",
            r"\bdashscope\b",
            r"\bsemantic-kernel\b",
            r"\bmcp\b",
            r"@modelcontextprotocol/",
        ],
        "code_patterns": [
            r"AgentExecutor",
            r"create_react_agent",
            r"create_openai_functions_agent",
            r"create_tool_calling_agent",
            r"\.bind_tools\(",
            r"@tool\b",
            r"PromptTemplate\(",
            r"ChatPromptTemplate",
            r"client\.chat\.completions\.create",
            r"anthropic\.messages\.create",
            r"StdioServerParameters",
        ],
        "fs_layout": ["**/agents/**/*.py", "**/agents/**/*.ts", "**/tools/**/*.py"],
    },
    "sandbox_runtime": {
        "deps": [
            r"\bvm2\b",
            r"\bisolated-vm\b",
            r"\bRestrictedPython\b",
            r"\bpyodide\b",
            r"\bwasmer\b",
            r"\bwasmtime\b",
            r"\bdocker\b",
            r"\bkubernetes\b",
        ],
        "code_patterns": [
            r"\bvm\.runIn[A-Za-z]+Context\(",
            r"\bnew\s+Function\s*\(",
            r"\beval\s*\(",
            r"\bexec\s*\(",
            r"compile_restricted",
            r"privileged\s*:\s*true",
            r"hostPath\s*:",
            r"docker\.sock",
            r"CAP_SYS_ADMIN",
            r"seccompProfile",
            r"WasiCtxBuilder",
        ],
        "fs_layout": [
            "Dockerfile",
            "docker-compose*.yml",
            "docker-compose*.yaml",
            "k8s/**/*.yaml",
            "**/*.Dockerfile",
        ],
    },
    "business_payment": {
        "deps": [
            r"\bstripe\b",
            r"\balipay-sdk\b",
            r"\bwechatpay\b",
            r"\bwxpay\b",
            r"\bpaypal-rest-sdk\b",
            r"\bbraintree\b",
        ],
        "code_patterns": [
            r"\bcreate_charge\(",
            r"\bpay_callback\b",
            r"\border_create\b",
            r"\brefund\(",
            r"prepay_id",
            r"\bidempotency_key\b",
            r"\bnotify_url\b",
        ],
        "fs_layout": ["**/payment/**", "**/order/**", "**/billing/**"],
    },
    "mobile_app": {
        "deps": [
            r"\breact-native\b",
            r"@react-native/",
            r"\bflutter\b",
            r"\bcordova\b",
            r"\bcapacitor\b",
            r"\b@ionic/",
            r"\bexpo\b",
        ],
        "code_patterns": [
            r"addJavascriptInterface\s*\(",
            r"setJavaScriptEnabled\s*\(\s*true",
            r"getSharedPreferences\s*\(",
            r"NSUserDefaults",
            r"android:exported\s*=",
            r"UIApplicationDelegate",
            r"@JavascriptInterface",
        ],
        "fs_layout": [
            "**/AndroidManifest.xml",
            "**/*.gradle",
            "**/Info.plist",
            "**/*.xcodeproj/**",
            "**/pubspec.yaml",
            "ios/**",
            "android/**",
        ],
    },
    "desktop_app": {
        "deps": [
            r"\belectron\b",
            r"\belectron-builder\b",
            r"\belectron-updater\b",
            r"@electron/remote",
            r"\bnw\.js\b",
            r"\bnwjs\b",
            r"\btauri\b",
            r"@tauri-apps/",
        ],
        "code_patterns": [
            r"new\s+BrowserWindow\s*\(",
            r"nodeIntegration\s*:",
            r"contextIsolation\s*:",
            r"ipcMain\.(handle|on)\s*\(",
            r"shell\.openExternal\s*\(",
            r"contextBridge\.exposeInMainWorld\s*\(",
            r"autoUpdater\.",
        ],
        "fs_layout": [
            "**/electron.js",
            "**/electron/main.js",
            "**/main.js",
            "**/preload.js",
            "**/electron-builder.*",
            "**/forge.config.*",
        ],
    },
}

# 场景 → 知识 yaml 列表（Light 阶段 1.5 触发场景时按需追加）
SCENARIO_KNOWLEDGE_MAP = {
    "cloud_native_service": ["tencent-cloud-security.yaml"],
    "ai_agent_app": ["ai-agent-security.yaml"],
    "sandbox_runtime": ["sandbox-escape-patterns.yaml"],
    "business_payment": ["payment-logic-rules.yaml"],
    "mobile_app": ["mobile-security-patterns.yaml"],
    "desktop_app": ["desktop-security-patterns.yaml"],
    "web": [],   # baseline，沿用现有 web_default 优先级
    "mixed": [],
}

# 场景 → Light 问答集 + 每文件 finding 上限（仅 Light 消费）
SCENARIO_LIGHT_RULES = {
    "cloud_native_service": {
        "ask_set": ["isImdsReachable", "isIamWildcard", "isPublicBucket"],
        "max_findings_per_file": 1,
        "max_files": 50,
    },
    "ai_agent_app": {
        "ask_set": [
            "isToolBoundToAgent",
            "isLLMOutputUnconstrained",
            "isToolDangerous",
            "isOutputSinkUnsafe",
        ],
        "max_findings_per_file": 2,
        "max_files": 50,
    },
    "sandbox_runtime": {
        "ask_set": [
            "isUserInputReachable",
            "isContextWeak",
            "isCapDangerous",
            "isSeccompMissing",
            "isWasiOverPermissive",
        ],
        "max_findings_per_file": 2,
        "max_files": 50,
    },
    "business_payment": {
        "ask_set": [
            "isPriceFromClient",
            "isIdempotencyKeyMissing",
            "isCallbackUnsigned",
        ],
        "max_findings_per_file": 1,
        "max_files": 50,
    },
    "mobile_app": {
        "ask_set": [
            "isComponentExported",
            "isWebViewBridgeExposed",
            "isCertValidationDisabled",
            "isSecretStoredPlaintext",
        ],
        "max_findings_per_file": 2,
        "max_files": 50,
    },
    "desktop_app": {
        "ask_set": [
            "isNodeIntegrationEnabled",
            "isIpcSenderUnvalidated",
            "isShellInputControllable",
            "isRemoteContentLoaded",
        ],
        "max_findings_per_file": 2,
        "max_files": 50,
    },
    "web": {"ask_set": [], "max_findings_per_file": 2, "max_files": 200},
}

SCENARIO_MIN_CONFIDENCE = 60
SCENARIO_MAX_ACTIVE = 3

# 文件遍历排除集（避免 test fixture 误伤）
_SCENARIO_PATH_EXCLUDES = (
    "/tests/",
    "/test/",
    "/__tests__/",
    "/example/",
    "/examples/",
    "/fixtures/",
    "/spec/",
    "/node_modules/",
    "/venv/",
    "/.venv/",
    "/dist/",
    "/build/",
    "/__pycache__/",
    "/.git/",
)
_SCENARIO_FILE_SUFFIX_EXCLUDES = (".test.js", ".test.ts", ".spec.js", ".spec.ts", "_test.go")
_SCENARIO_SCAN_FILE_LIMIT = 5000
_SCENARIO_SCAN_HIT_LIMIT = 200
_SCENARIO_MANIFEST_FILES = (
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "composer.json",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
)


def _scenario_should_skip(path_str):
    if any(seg in path_str for seg in _SCENARIO_PATH_EXCLUDES):
        return True
    return any(path_str.endswith(suf) for suf in _SCENARIO_FILE_SUFFIX_EXCLUDES)


def _detect_scenarios(project_path):
    """
    返回 (scenarios_list, scenario_confidence_dict)。

    scenarios_list 已按置信度降序，>= SCENARIO_MIN_CONFIDENCE，最多 SCENARIO_MAX_ACTIVE 项。
    若实际命中场景数 > SCENARIO_MAX_ACTIVE，列表尾追加 "mixed"。
    web 场景：检测到任意 FRAMEWORK_MARKERS → 100（保证 baseline 不变）。
    """
    project_path = Path(project_path)
    scores = {name: 0 for name in SCENARIO_MARKERS.keys()}

    # 1) manifest 依赖匹配（每场景 30 分）
    for mf in _SCENARIO_MANIFEST_FILES:
        mp = project_path / mf
        if not mp.exists():
            continue
        try:
            content = mp.read_text(encoding="utf-8", errors="ignore")
        except IOError:
            continue
        for scen, markers in SCENARIO_MARKERS.items():
            for pat in markers["deps"]:
                if _re_scen.search(pat, content):
                    scores[scen] = min(scores[scen] + 30, 100)
                    break

    # 2) 代码模式匹配（每命中 20，每场景累计上限 40）
    code_scores = {name: 0 for name in SCENARIO_MARKERS.keys()}
    file_count = 0
    hit_count = 0
    code_exts = (".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".kt", ".rs", ".php")

    for fp in project_path.rglob("*"):
        if file_count >= _SCENARIO_SCAN_FILE_LIMIT or hit_count >= _SCENARIO_SCAN_HIT_LIMIT:
            break
        if not fp.is_file():
            continue
        path_str = "/" + str(fp.relative_to(project_path)).replace("\\", "/") + "/"
        if _scenario_should_skip(path_str):
            continue
        suffix = fp.suffix.lower()
        is_code = suffix in code_exts
        is_yaml = suffix in (".yaml", ".yml")
        is_dockerfile = fp.name.lower().startswith("dockerfile") or fp.name.lower().endswith(".dockerfile")
        if not (is_code or is_yaml or is_dockerfile):
            continue
        file_count += 1
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except (IOError, OSError):
            continue
        for scen, markers in SCENARIO_MARKERS.items():
            if code_scores[scen] >= 40:
                continue
            for pat in markers["code_patterns"]:
                if _re_scen.search(pat, content):
                    code_scores[scen] = min(code_scores[scen] + 20, 40)
                    hit_count += 1
                    break

    for scen in scores:
        scores[scen] = min(scores[scen] + code_scores[scen], 100)

    # 3) 文件布局加权（每场景上限 20）
    for scen, markers in SCENARIO_MARKERS.items():
        for layout_pat in markers.get("fs_layout", []):
            try:
                if any(True for _ in project_path.glob(layout_pat)):
                    scores[scen] = min(scores[scen] + 20, 100)
                    break
            except (OSError, ValueError):
                continue

    # 4) web 场景：任意 FRAMEWORK_MARKERS → 100（baseline 保持不变）
    web_score = 0
    for framework, config in FRAMEWORK_MARKERS.items():
        for marker_file in config["files"]:
            mp = project_path / marker_file
            if not mp.exists():
                continue
            try:
                content = mp.read_text(encoding="utf-8", errors="ignore")
            except IOError:
                continue
            if any(p in content.lower() for p in config["content_patterns"]):
                web_score = 100
                break
        if web_score == 100:
            break

    # 5) 汇总入选 + 排序
    candidates = []
    if web_score >= SCENARIO_MIN_CONFIDENCE:
        candidates.append(("web", web_score))
    for scen, sc in scores.items():
        if sc >= SCENARIO_MIN_CONFIDENCE:
            candidates.append((scen, sc))

    candidates.sort(key=lambda x: -x[1])
    total_hits = len(candidates)
    selected = candidates[:SCENARIO_MAX_ACTIVE]

    scenarios = [name for name, _ in selected]
    if total_hits > SCENARIO_MAX_ACTIVE and "mixed" not in scenarios:
        scenarios.append("mixed")

    if not scenarios:
        # 最低保底：始终回落 web，保证既有 Light 流程不崩
        scenarios = ["web"]
        confidence = {"web": max(web_score, SCENARIO_MIN_CONFIDENCE)}
    else:
        confidence = {name: sc for name, sc in selected}
        if "mixed" in scenarios:
            confidence["mixed"] = SCENARIO_MIN_CONFIDENCE

    return scenarios, confidence


# ─── 项目类型检测 ────────────────────────────────────────────

# Web 框架信号（与 FRAMEWORK_MARKERS 互补，这里检测是否存在 HTTP 端点）
WEB_FRAMEWORK_NAMES = set(FRAMEWORK_MARKERS.keys())


def cmd_detect_framework(args):
    """检测项目框架和技术栈"""
    project_path = Path(args.project_path).resolve()

    detected_frameworks = []
    detected_languages = set()
    detected_build_tools = []

    # 检测框架
    for framework, config in FRAMEWORK_MARKERS.items():
        for marker_file in config["files"]:
            marker_path = project_path / marker_file
            if marker_path.exists():
                # 检查文件内容是否包含特征模式
                try:
                    content = marker_path.read_text(encoding="utf-8", errors="ignore")
                    if any(p in content.lower() for p in config["content_patterns"]):
                        detected_frameworks.append(framework)
                        detected_languages.add(config["language"])
                        break
                except IOError:
                    continue

    # 检测构建工具
    for tool, markers in BUILD_TOOL_MARKERS.items():
        for marker in markers:
            if (project_path / marker).exists():
                detected_build_tools.append(tool)
                break

    # 推断 knowledge 文件
    knowledge_files = []
    for fw in detected_frameworks:
        for kf in KNOWLEDGE_FILE_MAP.get(fw, []):
            if kf not in knowledge_files:
                knowledge_files.append(kf)

    result = {
        "status": "completed",
        "frameworks": detected_frameworks,
        "primary_framework": detected_frameworks[0] if detected_frameworks else "unknown",
        "languages": sorted(detected_languages),
        "build_tools": detected_build_tools,
        "knowledge_files": knowledge_files,
        "project_path": str(project_path),
    }
    print(json.dumps(result, ensure_ascii=False))


# ─── 命令: detect-project-type ────────────────────────────────

def cmd_detect_project_type(args):
    """
    兼容旧命令：不再执行脚本化产品形态判定。

    产品形态必须由 Agent 在探索阶段直接分析并写入 project-type.json；本命令只读取既有结论。
    """
    project_path = Path(args.project_path).resolve()
    batch_dir = Path(args.batch_dir).resolve() if getattr(args, "batch_dir", None) else None
    project_type_file = batch_dir / "project-type.json" if batch_dir else None

    if project_type_file and project_type_file.exists():
        try:
            agent_profile = json.loads(project_type_file.read_text(encoding="utf-8"))
        except Exception:
            agent_profile = {}
    else:
        agent_profile = {}

    if not agent_profile:
        decision = "detect-project-type 已废弃：产品形态必须由 Agent 直接分析真实文件证据后写入 project-type.json；脚本不再猜测。"
        agent_profile = {
            "project_type": "未知",
            "project_type_code": "unknown",
            "product_category": "未知",
            "product_subtype": "",
            "product_shape": "未知",
            "product_shape_decision": decision,
            "product_shape_evidence_chain": {
                "conclusion": "未知",
                "decision": decision,
                "standard": "不使用脚本判定；缺少 Agent 直接分析产物时只能返回未知。",
                "basis": ["script_classifier=disabled", "evidence=missing"],
                "evidence": [],
                "competingCandidates": [],
            },
        }

    project_type = agent_profile.get("project_type") or agent_profile.get("product_shape") or "未知"
    project_type_code = agent_profile.get("project_type_code") or "unknown"

    scenarios, scenario_confidence = _detect_scenarios(project_path)
    if str(project_type_code).startswith("ai_agent") and "ai_agent_app" not in scenarios:
        scenarios = ["ai_agent_app"] + [s for s in scenarios if s != "ai_agent_app"]
        scenario_confidence["ai_agent_app"] = max(80, scenario_confidence.get("ai_agent_app", 0))

    audit_strategy = _build_audit_strategy(
        project_type_code,
        scenarios=scenarios,
        scenario_confidence=scenario_confidence,
    )

    result = {
        "status": "deprecated",
        "message": "产品形态不再由脚本识别；请使用 Agent 直接分析写入的 project-type.json。",
        "project_type": project_type,
        "projectType": project_type_code,
        "agentProfile": agent_profile,
        "productCategory": agent_profile.get("product_category", ""),
        "productSubtype": agent_profile.get("product_subtype", ""),
        "product_shape": agent_profile.get("product_shape", project_type),
        "product_shape_decision": agent_profile.get("product_shape_decision", ""),
        "product_shape_evidence_chain": agent_profile.get("product_shape_evidence_chain", {}),
        "productShape": agent_profile.get("product_shape", project_type),
        "productShapeDecision": agent_profile.get("product_shape_decision", ""),
        "productShapeEvidenceChain": agent_profile.get("product_shape_evidence_chain", {}),
        "scenarios": scenarios,
        "scenarioConfidence": scenario_confidence,
        "auditStrategy": audit_strategy,
        "project_path": str(project_path),
    }
    print(json.dumps(result, ensure_ascii=False))


def _build_audit_strategy(project_type, scenarios=None, scenario_confidence=None):
    """根据项目类型 + 业务场景生成审计维度策略。

    `scenarios` / `scenario_confidence` 仅 Light 阶段 1.5 消费；Fast/Deep 调用方
    不传这两个参数，走默认 web 场景，行为与旧版本一致。
    """
    if scenarios is None or len(scenarios) == 0:
        scenarios = ["web"]
    if scenario_confidence is None:
        scenario_confidence = {s: 100 for s in scenarios}

    # knowledge_files 按场景去重收集
    knowledge_files = []
    for scen in scenarios:
        for kf in SCENARIO_KNOWLEDGE_MAP.get(scen, []):
            if kf not in knowledge_files:
                knowledge_files.append(kf)

    # lightScenarioRules：按置信度降序取 top SCENARIO_MAX_ACTIVE，仅 Light 消费
    ranked = sorted(
        ((s, scenario_confidence.get(s, 0)) for s in scenarios if s in SCENARIO_LIGHT_RULES),
        key=lambda x: -x[1],
    )[:SCENARIO_MAX_ACTIVE]
    light_scenario_rules = []
    for scen, conf in ranked:
        rule = dict(SCENARIO_LIGHT_RULES[scen])
        rule["scenario"] = scen
        rule["confidence"] = conf
        light_scenario_rules.append(rule)

    return {
        "vuln_scan": {
            "dimensions": ["C1"],
            "skip": [],
            "note": "Web 项目注入类审计",
        },
        "logic_scan": {
            "dimensions": ["C3", "C7.1-C7.7"],
            "skip": [],
            "note": "业务逻辑审计",
        },
        "red_team": {
            "dimensions": ["Q1", "Q2", "Q3"],
            "skip": [],
            "budget": {"Q1": 40, "Q2": 40, "Q3": 20},
            "note": "标准三问题猎杀",
        },
        "sink_prioritization": "web_default",
        "knowledge_files": knowledge_files,
        "lightScenarioRules": light_scenario_rules,
    }


# ─── CLI 入口 ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="编排器辅助工具 — 确定性编排决策",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查 phase 完成状态
  %(prog)s check-phase-gate \\
    --batch-dir .codebuddy/security-scan/runs/project-deep-xxx \\
    --required-phase phase1_5

  # 决定是否启动 vuln-scan
  %(prog)s should-launch-agent \\
    --batch-dir .codebuddy/security-scan/runs/project-deep-xxx \\
    --agent vuln-scan

  # 检查是否需要 re-run agent
  %(prog)s should-rerun-agent \\
    --batch-dir .codebuddy/security-scan/runs/project-deep-xxx \\
    --agent vuln-scan

  # 决定 traceMethod
  %(prog)s determine-trace-method \\
    --batch-dir .codebuddy/security-scan/runs/project-deep-xxx

  # 扫描进度汇总
  %(prog)s summarize-progress \\
    --batch-dir .codebuddy/security-scan/runs/project-deep-xxx

  # 检测项目框架
  %(prog)s detect-framework \\
    --project-path /path/to/project
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # check-phase-gate
    p_gate = subparsers.add_parser("check-phase-gate", help="检查 phase 完成状态")
    p_gate.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_gate.add_argument("--required-phase", required=True, help="需要检查的 phase")

    # should-launch-agent
    p_launch = subparsers.add_parser("should-launch-agent", help="决定是否启动 agent")
    p_launch.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_launch.add_argument("--agent", required=True, help="Agent 名称")

    # should-rerun-agent
    p_rerun = subparsers.add_parser("should-rerun-agent", help="决定是否 re-run agent")
    p_rerun.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_rerun.add_argument("--agent", required=True, help="Agent 名称")
    p_rerun.add_argument("--max-reruns", default="2", help="最大 re-run 次数 (默认 2)")

    # determine-trace-method
    p_trace = subparsers.add_parser("determine-trace-method", help="决定 traceMethod")
    p_trace.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_trace.add_argument("--lsp-available", help="LSP 是否可用 (true/false)")

    # summarize-progress
    p_progress = subparsers.add_parser("summarize-progress", help="扫描进度汇总")
    p_progress.add_argument("--batch-dir", required=True, help="扫描批次目录")

    # detect-framework
    p_detect = subparsers.add_parser("detect-framework", help="检测项目框架")
    p_detect.add_argument("--project-path", required=True, help="项目根目录")

    # detect-project-type
    p_ptype = subparsers.add_parser("detect-project-type", help="已废弃：只读取 Agent 写入的产品形态结论")
    p_ptype.add_argument("--project-path", required=True, help="项目根目录")
    p_ptype.add_argument("--batch-dir", help="扫描批次目录；读取其中的 project-type.json")

    # begin-session
    p_session = subparsers.add_parser(
        "begin-session",
        help="开启扫描会话（写入 .scan-session.json，并清理陈旧产物）",
    )
    p_session.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_session.add_argument("--run-id", help="本次扫描运行标识，缺省取 batch-dir 名称")
    p_session.add_argument("--mode", default="", help="扫描模式 (fast / light / deep)")
    p_session.add_argument("--scan-command", default="", help="扫描命令名（写入 session metadata）")
    p_session.add_argument("--project-path", default="", help="项目根目录（写入 session metadata）")
    p_session.add_argument(
        "--no-purge",
        action="store_true",
        help="跳过陈旧产物清理（仅写入会话锁，下游仍会按 mtime 过滤）",
    )

    # check-stale-outputs
    p_stale = subparsers.add_parser(
        "check-stale-outputs",
        help="列出 batch-dir 中早于当前会话的陈旧产物",
    )
    p_stale.add_argument("--batch-dir", required=True, help="扫描批次目录")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "check-phase-gate": cmd_check_phase_gate,
        "should-launch-agent": cmd_should_launch_agent,
        "should-rerun-agent": cmd_should_rerun_agent,
        "determine-trace-method": cmd_determine_trace_method,
        "summarize-progress": cmd_summarize_progress,
        "detect-framework": cmd_detect_framework,
        "detect-project-type": cmd_detect_project_type,
        "begin-session": cmd_begin_session,
        "check-stale-outputs": cmd_check_stale_outputs,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
