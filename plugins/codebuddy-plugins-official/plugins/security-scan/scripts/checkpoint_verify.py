#!/usr/bin/env python3
"""
Checkpoint 采样校验脚本：自动化验证 agent 输出的真实性，替代 coordinator 手动 Read 抽检。

子命令：
  verify-explore          校验探索阶段输出（文件列表、入口点、依赖）
  verify-semantic-index   校验语义索引数据库完整性（project-index.db SQLite 表）
  verify-scan             校验扫描阶段合并结果（finding 文件路径、riskCode 真实性 + 严重性统计）

  别名：verify-stage1 = verify-explore, verify-stage2 = verify-scan

设计原则：
  - stdout 仅输出 JSON 摘要供 coordinator 解析
  - 日志输出到 stderr
  - 采样数可配置，默认 5 个
"""
import argparse
import json
import random
import re
import sqlite3
import sys
from pathlib import Path

from _common import (
    Colors, make_logger, stdout_json,
    load_json_file, write_json_file,
    normalize_finding,
)

# ---------------------------------------------------------------------------
# 日志工具
# ---------------------------------------------------------------------------

log_info, log_ok, log_warn, log_error = make_logger("checkpoint")


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------

def sample_items(items, n=None):
    """从列表中动态采样。
    当 n 为 None 时：采样数 = max(5, min(len(items) * 0.1, 20))
    当 n 显式指定时：采样数 = min(n, len(items))
    """
    if not items:
        return []
    if n is None:
        n = max(5, min(int(len(items) * 0.1), 20))
    sample_count = min(n, len(items))
    return random.sample(items, sample_count)


def read_lines(file_path, center_line, radius=3):
    """读取文件指定行号附近的内容，返回行列表"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        start = max(0, center_line - 1 - radius)
        end = min(len(lines), center_line + radius)
        return [l.rstrip('\n') for l in lines[start:end]]
    except Exception:
        return []


def file_exists(path):
    return Path(path).is_file()


# ---------------------------------------------------------------------------
# verify-artifacts：校验阶段 2/3 关键产物是否完整落盘
# ---------------------------------------------------------------------------

FINAL_AGENT_STATUSES = {"completed", "partial"}
ALL_AGENT_STATUSES = FINAL_AGENT_STATUSES | {"in_progress", "failed"}

AGENT_OUTPUT_SPECS = {
    "indexer": {
        "path": "agents/{prefix}indexer.json",
        "required_keys": ["agent", "status", "fileList", "projectInfo", "dependencyFiles", "hasPaymentLogic", "dbPath"],
    },
    "vuln-scan": {
        "path": "agents/{prefix}vuln-scan.json",
        "required_keys": ["agent", "status", "findings"],
        "companion_files": [
            {
                "path": "{prefix}pattern-scan-results.json",
                "required_keys": ["sinkLocations"],
                "optional": True,
            }
        ],
    },
    "logic-scan": {
        "path": "agents/{prefix}logic-scan.json",
        "required_keys": ["agent", "status", "findings"],
    },
    "red-team": {
        "path": "agents/{prefix}red-team.json",
        "required_keys": ["agent", "status", "findings"],
    },
    "verifier": {
        "path": "agents/{prefix}verifier.json",
        "required_keys": ["agent", "status"],
        "alternative_keys": {
            "validatedFindings": ["findings"],
            "summary": ["metrics"],
        },
    },
}


def _validate_json_artifact(path, expected_agent=None, required_keys=None, alternative_keys=None):
    data = load_json_file(path)
    if data is None:
        return False, "missing_or_invalid_json", None

    if expected_agent and data.get("agent") != expected_agent:
        return False, f"agent_mismatch:{data.get('agent', '')}", data

    alt = alternative_keys or {}
    for key in required_keys or []:
        if key not in data:
            # Check alternative key names
            alternatives = alt.get(key, [])
            found = any(alt_key in data for alt_key in alternatives)
            if not found:
                return False, f"missing_key:{key}", data

    status = str(data.get("status", "")).strip().lower()
    if status and status not in ALL_AGENT_STATUSES:
        return False, f"invalid_status:{status}", data

    if status and status not in FINAL_AGENT_STATUSES:
        return False, f"non_final_status:{status}", data

    if "writeCount" in data and isinstance(data.get("writeCount"), int) and data["writeCount"] <= 0:
        return False, "invalid_write_count", data

    # --- 改进 1: findings 文件存在性抽检 ---
    # 对含 findings 数组的 Agent 输出，随机抽检 3 个 finding 的文件路径是否真实存在。
    # 目的：在 merge 之前拦截幻觉严重的 Agent 输出，避免后续无效的合并和验证流程。
    findings = data.get("findings", [])
    if findings and isinstance(findings, list) and len(findings) > 0:
        sample_count = min(3, len(findings))
        sample_findings = random.sample(findings, sample_count)
        ghost_count = 0
        for f in sample_findings:
            nf = normalize_finding(f)
            fp = nf.get('filePath', '')
            if fp and not Path(fp).is_file():
                ghost_count += 1
        if ghost_count == sample_count and sample_count >= 2:
            # 抽检全部命中幽灵文件，高度疑似幻觉输出
            return False, f"findings_hallucination_detected:sampled_{sample_count}_all_ghost", data
        elif ghost_count > 0:
            # 部分幽灵，记录警告但不阻断（merge 阶段会做全量清洗）
            log_warn(f"findings 抽检发现 {ghost_count}/{sample_count} 个指向不存在文件的 finding")

    return True, "ok", data


def verify_artifacts(batch_dir, agents, prefix=""):
    """校验关键 agent 产物是否已落盘且状态可用于下游交接。"""
    log_info("开始关键产物完整性校验...")

    requested_agents = [a.strip() for a in agents.split(",") if a.strip()]
    if not requested_agents:
        stdout_json({"status": "error", "message": "未指定 --agents"})
        sys.exit(1)

    results = {
        "status": "ok",
        "checkedAgents": requested_agents,
        "readyAgents": [],
        "failedAgents": [],
        "missingFiles": [],
        "details": [],
    }

    for agent_name in requested_agents:
        spec = AGENT_OUTPUT_SPECS.get(agent_name)
        if spec is None:
            results["failedAgents"].append(agent_name)
            results["details"].append({
                "agent": agent_name,
                "status": "fail",
                "reason": "unknown_agent",
            })
            continue

        artifact_path = batch_dir / spec["path"].format(prefix=prefix)
        ok, reason, data = _validate_json_artifact(
            artifact_path,
            expected_agent=agent_name,
            required_keys=spec.get("required_keys", []),
            alternative_keys=spec.get("alternative_keys"),
        )
        if not ok:
            results["failedAgents"].append(agent_name)
            if reason == "missing_or_invalid_json":
                results["missingFiles"].append(str(artifact_path))
            results["details"].append({
                "agent": agent_name,
                "path": str(artifact_path),
                "status": "fail",
                "reason": reason,
            })
            continue

        companion_failures = []
        for companion in spec.get("companion_files", []):
            companion_path = batch_dir / companion["path"].format(prefix=prefix)
            is_optional = companion.get("optional", False)
            c_ok, c_reason, _ = _validate_json_artifact(
                companion_path,
                expected_agent=None if is_optional else agent_name,
                required_keys=companion.get("required_keys", []),
            )
            if not c_ok:
                if is_optional:
                    pass  # optional companion missing is not a failure
                else:
                    companion_failures.append({
                        "path": str(companion_path),
                        "reason": c_reason,
                    })
                    if c_reason == "missing_or_invalid_json":
                        results["missingFiles"].append(str(companion_path))

        if companion_failures:
            results["failedAgents"].append(agent_name)
            results["details"].append({
                "agent": agent_name,
                "path": str(artifact_path),
                "status": "fail",
                "reason": "companion_artifact_invalid",
                "companionFailures": companion_failures,
            })
            continue

        results["readyAgents"].append(agent_name)
        results["details"].append({
            "agent": agent_name,
            "path": str(artifact_path),
            "status": "ok",
            "agentStatus": data.get("status", ""),
            "writeCount": data.get("writeCount"),
        })

    if results["failedAgents"]:
        results["status"] = "fail"
        failures_name = f"{prefix}checkpoint-artifact-failures.json" if prefix else "checkpoint-artifact-failures.json"
        try:
            write_json_file(batch_dir / failures_name, results)
        except OSError as exc:
            results["failureReportWriteError"] = str(exc)
            log_warn(f"写入 {failures_name} 失败：{exc}")
        log_error(
            "关键产物校验失败："
            + ", ".join(f"{item['agent']}({item['reason']})" for item in results["details"] if item["status"] == "fail")
        )
    else:
        log_ok(f"关键产物校验通过：{', '.join(results['readyAgents'])}")

    stdout_json(results)


# ---------------------------------------------------------------------------
# verify-stage1：校验阶段 1 输出
# ---------------------------------------------------------------------------

def verify_explore(batch_dir, sample_size=5):
    """校验探索阶段输出 stage1-context.json 中的文件列表、入口点、依赖"""
    log_info("开始探索阶段交接校验...")

    ctx_path = batch_dir / "stage1-context.json"
    ctx = load_json_file(ctx_path)
    if ctx is None:
        stdout_json({"status": "error", "message": f"无法读取 {ctx_path}"})
        sys.exit(1)

    results = {"status": "ok", "checks": [], "failedItems": [], "passRate": 1.0}
    total_checks = 0
    passed_checks = 0

    # 1. 校验 fileList
    file_list = ctx.get("fileList", [])
    if isinstance(file_list, list) and file_list:
        sampled = sample_items(file_list, sample_size)
        for fp in sampled:
            total_checks += 1
            if file_exists(fp):
                passed_checks += 1
            else:
                results["failedItems"].append({"type": "fileList", "path": fp, "reason": "文件不存在"})
        results["checks"].append({
            "type": "fileList", "total": len(file_list),
            "sampled": len(sampled), "passed": passed_checks
        })
        log_info(f"fileList 抽检 {len(sampled)}/{len(file_list)}，通过 {passed_checks}")
    else:
        results["checks"].append({"type": "fileList", "total": 0, "sampled": 0, "passed": 0})
        log_warn("fileList 为空")

    # 2. 校验 entryPoints
    entry_points = ctx.get("entryPoints", [])
    if isinstance(entry_points, list) and entry_points:
        sampled_ep = sample_items(entry_points, sample_size)
        ep_passed = 0
        for ep in sampled_ep:
            total_checks += 1
            ep_file = ep.get("file", ep.get("filePath", ""))
            ep_method = ep.get("method", ep.get("name", ""))
            if not ep_file or not file_exists(ep_file):
                results["failedItems"].append({
                    "type": "entryPoint", "file": ep_file,
                    "method": ep_method, "reason": "文件不存在"
                })
                continue
            # 检查方法名是否出现在文件中
            try:
                with open(ep_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if ep_method and ep_method in content:
                    ep_passed += 1
                    passed_checks += 1
                else:
                    results["failedItems"].append({
                        "type": "entryPoint", "file": ep_file,
                        "method": ep_method, "reason": "方法名未找到"
                    })
            except Exception:
                results["failedItems"].append({
                    "type": "entryPoint", "file": ep_file,
                    "method": ep_method, "reason": "读取文件失败"
                })
        results["checks"].append({
            "type": "entryPoints", "total": len(entry_points),
            "sampled": len(sampled_ep), "passed": ep_passed
        })
        log_info(f"entryPoints 抽检 {len(sampled_ep)}/{len(entry_points)}，通过 {ep_passed}")

    # 3. 校验 dependencies
    deps = ctx.get("dependencies", [])
    if isinstance(deps, list) and deps:
        sampled_deps = sample_items(deps, min(3, sample_size))
        dep_passed = 0
        for dep in sampled_deps:
            total_checks += 1
            dep_file = dep.get("file", dep.get("filePath", ""))
            if dep_file and file_exists(dep_file):
                dep_passed += 1
                passed_checks += 1
            else:
                results["failedItems"].append({
                    "type": "dependency", "file": dep_file, "reason": "依赖文件不存在"
                })
        results["checks"].append({
            "type": "dependencies", "total": len(deps),
            "sampled": len(sampled_deps), "passed": dep_passed
        })
        log_info(f"dependencies 抽检 {len(sampled_deps)}/{len(deps)}，通过 {dep_passed}")

    # 汇总
    results["totalChecks"] = total_checks
    results["passedChecks"] = passed_checks
    results["passRate"] = round(passed_checks / total_checks, 2) if total_checks > 0 else 1.0

    if results["passRate"] < 0.6:
        results["status"] = "fail"
        log_error(f"探索阶段校验失败：通过率 {results['passRate']}")
    else:
        results["status"] = "ok"
        log_ok(f"探索阶段校验通过：{passed_checks}/{total_checks} (通过率 {results['passRate']})")

    stdout_json(results)


# ---------------------------------------------------------------------------
# verify-scan：校验扫描阶段合并结果
# ---------------------------------------------------------------------------

def verify_scan(batch_dir, sample_size=None, prefix=""):
    """校验 merged-stage2.json 中的 findings 真实性，包含严重性分布统计"""
    log_info("开始扫描阶段交接校验...")

    merged_name = f"{prefix}merged-stage2.json" if prefix else "merged-stage2.json"
    merged_path = batch_dir / merged_name
    merged = load_json_file(merged_path)
    if merged is None:
        # 回退到 merged-scan.json
        fallback_name = f"{prefix}merged-scan.json" if prefix else "merged-scan.json"
        fallback_path = batch_dir / fallback_name
        merged = load_json_file(fallback_path)
        if merged is not None:
            log_info(f"使用 {fallback_name} 作为 {merged_name} 的回退")
    if merged is None:
        stdout_json({"status": "error", "message": f"无法读取 {merged_path}"})
        sys.exit(1)

    findings = merged.get("findings", [])
    if not isinstance(findings, list):
        findings = []

    results = {
        "status": "ok",
        "totalFindings": len(findings),
        "sampled": 0,
        "passed": 0,
        "failed": 0,
        "failedItems": [],
        "hallucinations": [],
    }

    if not findings:
        log_info("无 findings 需要校验")
        stdout_json(results)
        return

    sampled = sample_items(findings, sample_size)
    results["sampled"] = len(sampled)
    passed = 0

    for finding in sampled:
        # 归一化字段名
        nf = normalize_finding(finding)
        fp = nf.get('filePath', '')
        line_num = nf.get('lineNumber', 0)
        risk_code = nf.get('riskCode', '')
        finding_id = nf.get('findingId', 'unknown')

        # 检查 1：文件存在性
        if not fp or not file_exists(fp):
            results["failedItems"].append({
                "findingId": finding_id, "filePath": fp,
                "reason": "文件不存在"
            })
            results["hallucinations"].append(finding_id)
            continue

        # 检查 2：行号有效性 + riskCode 匹配
        if line_num and risk_code:
            nearby_lines = read_lines(fp, int(line_num), radius=3)
            combined = "\n".join(nearby_lines)
            # 取 riskCode 的前 40 字符做模糊匹配（agent 可能有轻微格式差异）
            snippet = risk_code.strip()[:40]
            # 转义正则特殊字符后做子串匹配
            snippet_escaped = re.escape(snippet)
            if nearby_lines and re.search(snippet_escaped, combined):
                passed += 1
            elif nearby_lines:
                # 行号附近有内容但代码片段不匹配
                results["failedItems"].append({
                    "findingId": finding_id, "filePath": fp,
                    "lineNumber": line_num,
                    "reason": "riskCode 在行号 ±3 行范围内未匹配"
                })
                results["hallucinations"].append(finding_id)
            else:
                results["failedItems"].append({
                    "findingId": finding_id, "filePath": fp,
                    "lineNumber": line_num,
                    "reason": "行号超出文件范围"
                })
                results["hallucinations"].append(finding_id)
        elif not risk_code:
            # 无 riskCode 时仅验证文件存在即通过
            passed += 1
        else:
            passed += 1

    results["passed"] = passed
    results["failed"] = results["sampled"] - passed
    results["passRate"] = round(passed / results["sampled"], 2) if results["sampled"] > 0 else 1.0

    # 写入失败详情文件
    if results["failedItems"]:
        failures_name = f"{prefix}checkpoint-stage2-failures.json" if prefix else "checkpoint-stage2-failures.json"
        write_json_file(batch_dir / failures_name, {
            "failedItems": results["failedItems"],
            "hallucinations": results["hallucinations"],
        })

    # 严重性分布统计（字段名以 output-schemas.md 定义的 severity 为准）
    severity_dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        nf = normalize_finding(f)
        sev = nf.get('severity', '').lower().strip()
        if sev in ("critical", "严重"):
            severity_dist["critical"] += 1
        elif sev in ("high", "高"):
            severity_dist["high"] += 1
        elif sev in ("medium", "moderate", "中", "中等"):
            severity_dist["medium"] += 1
        elif sev in ("low", "低"):
            severity_dist["low"] += 1
    results["bySeverity"] = severity_dist

    # 证据链完整性抽检（sourceAgent 名称以当前版本 agent 名为准）
    evidence_checked = 0
    evidence_missing = 0
    for f in sampled:
        evidence_checked += 1
        has_attack_chain = bool(f.get("attackChain"))
        has_trace = bool(f.get("traceMethod"))
        source_agent = f.get("sourceAgent", "")
        if not source_agent:
            ab = f.get("auditedBy")
            source_agent = ab[0] if isinstance(ab, list) and ab else ""
        if source_agent in ("vuln-scan", "logic-scan", "red-team"):
            if not has_attack_chain and not has_trace:
                evidence_missing += 1
    results["evidenceChecked"] = evidence_checked
    results["evidenceMissing"] = evidence_missing

    if results["passRate"] < 0.6:
        results["status"] = "fail"
        log_error(f"扫描阶段校验失败：{passed}/{results['sampled']} (通过率 {results['passRate']})")
    else:
        results["status"] = "ok"
        log_ok(f"扫描阶段校验通过：{passed}/{results['sampled']} (通过率 {results['passRate']})")
    log_info(f"严重性分布: critical={severity_dist['critical']} high={severity_dist['high']} medium={severity_dist['medium']} low={severity_dist['low']}")

    stdout_json(results)


# ---------------------------------------------------------------------------
# verify-semantic-index：校验 project-index.db（SQLite）完整性
# ---------------------------------------------------------------------------

# 当前架构使用 SQLite 数据库 project-index.db，核心表定义参见 indexer.md
SEMANTIC_INDEX_TABLES = {
    "project_meta": {
        "description": "项目元数据",
        "phase": "1",
        "required": True,
        "validate_fn": None,
    },
    "files": {
        "description": "源文件清单",
        "phase": "1",
        "required": True,
        "validate_fn": "_validate_files_table",
    },
    "sinks": {
        "description": "危险操作点",
        "phase": "1+1.5+2",
        "required": True,
        "validate_fn": "_validate_sinks_table",
    },
    "endpoints": {
        "description": "API 端点",
        "phase": "2",
        "required": False,
        "validate_fn": None,
    },
    "call_graph": {
        "description": "调用图边",
        "phase": "2",
        "required": False,
        "validate_fn": "_validate_call_graph_table",
    },
    "defenses": {
        "description": "防御映射",
        "phase": "2",
        "required": False,
        "validate_fn": None,
    },
    "framework_bridges": {
        "description": "框架桥接",
        "phase": "2",
        "required": False,
        "validate_fn": None,
    },
    "indexer_findings": {
        "description": "密钥/配置/CVE",
        "phase": "1",
        "required": False,
        "validate_fn": None,
    },
    "attack_surface": {
        "description": "攻击面映射",
        "phase": "1",
        "required": False,
        "validate_fn": None,
    },
    "ast_functions": {
        "description": "函数/方法签名（AST 缓存）",
        "phase": "1.5",
        "required": False,
        "validate_fn": None,
    },
    "ast_calls": {
        "description": "调用表达式（AST 缓存）",
        "phase": "1.5",
        "required": False,
        "validate_fn": None,
    },
    "ast_refined_sinks": {
        "description": "Sink AST 验证结果",
        "phase": "1.5",
        "required": False,
        "validate_fn": None,
    },
    "ast_parse_meta": {
        "description": "文件解析元数据（hash 增量）",
        "phase": "1.5",
        "required": False,
        "validate_fn": None,
    },
}


def _query_db(db_path, sql, params=()):
    """安全查询 SQLite 数据库，返回结果列表（启用 WAL 模式和 busy_timeout，带重试）"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=15000")
            cursor = conn.execute(sql, params)
            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rows
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                import time
                time.sleep(1 * (attempt + 1))
                continue
            log_warn(f"SQLite 查询失败: {e}")
            return None
        except Exception as e:
            log_warn(f"SQLite 查询失败: {e}")
            return None


def _table_exists(db_path, table_name):
    """检查表是否存在"""
    rows = _query_db(db_path, "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return rows is not None and len(rows) > 0


def _table_row_count(db_path, table_name):
    """获取表行数"""
    rows = _query_db(db_path, f"SELECT COUNT(*) as cnt FROM [{table_name}]")
    if rows and len(rows) > 0:
        return rows[0]["cnt"]
    return 0


def _validate_files_table(db_path, sample_size):
    """抽检 files 表中文件路径的有效性"""
    rows = _query_db(db_path, "SELECT * FROM files ORDER BY RANDOM() LIMIT ?", (sample_size,))
    if not rows:
        return {"sampled": 0, "passed": 0, "failed": 0, "failedItems": []}

    passed = 0
    failed_items = []
    for row in rows:
        fp = row.get("path", row.get("file", ""))
        if fp and file_exists(fp):
            passed += 1
        else:
            failed_items.append({"file": fp, "reason": "文件不存在"})

    return {
        "sampled": len(rows),
        "passed": passed,
        "failed": len(rows) - passed,
        "failedItems": failed_items,
    }


def _validate_sinks_table(db_path, sample_size):
    """抽检 sinks 表中 Sink 的文件路径和行号有效性"""
    rows = _query_db(db_path, "SELECT * FROM sinks ORDER BY RANDOM() LIMIT ?", (sample_size,))
    if not rows:
        return {"sampled": 0, "passed": 0, "failed": 0, "failedItems": []}

    passed = 0
    failed_items = []
    for row in rows:
        fp = row.get("file_path", row.get("file", ""))
        line = row.get("line", 0)
        if not fp or not file_exists(fp):
            failed_items.append({
                "sinkId": row.get("id", "?"),
                "file": fp,
                "reason": "文件不存在"
            })
            continue
        if line and int(line) > 0:
            nearby = read_lines(fp, int(line), radius=3)
            code = row.get("code_snippet", row.get("code", row.get("pattern", "")))
            if nearby and code:
                snippet = str(code).strip()[:40]
                snippet_escaped = re.escape(snippet)
                combined = "\n".join(nearby)
                if re.search(snippet_escaped, combined):
                    passed += 1
                else:
                    failed_items.append({
                        "sinkId": row.get("id", "?"),
                        "file": fp,
                        "line": line,
                        "reason": "code 片段在行号 ±3 行范围内未匹配"
                    })
            else:
                passed += 1
        else:
            passed += 1

    return {
        "sampled": len(rows),
        "passed": passed,
        "failed": len(rows) - passed,
        "failedItems": failed_items,
    }


def _validate_call_graph_table(db_path, sample_size):
    """抽检 call_graph 表中调用边的文件路径有效性"""
    rows = _query_db(db_path, "SELECT * FROM call_graph ORDER BY RANDOM() LIMIT ?", (sample_size,))
    if not rows:
        return {"sampled": 0, "passed": 0, "failed": 0, "failedItems": []}

    passed = 0
    failed_items = []
    for row in rows:
        caller_file = row.get("caller_file", "")
        callee_file = row.get("callee_file", "")
        caller_ok = caller_file and file_exists(caller_file)
        callee_ok = callee_file and file_exists(callee_file)
        if caller_ok and callee_ok:
            passed += 1
        else:
            failed_items.append({
                "callerFile": caller_file,
                "calleeFile": callee_file,
                "reason": f"{'caller' if not caller_ok else 'callee'} 文件不存在"
            })

    return {
        "sampled": len(rows),
        "passed": passed,
        "failed": len(rows) - passed,
        "failedItems": failed_items,
    }


def verify_semantic_index(batch_dir, sample_size=5):
    """校验 project-index.db（SQLite）的表完整性和数据有效性"""
    log_info("开始语义索引完整性校验...")

    db_path = batch_dir / "project-index.db"
    results = {
        "status": "ok",
        "dbPath": str(db_path),
        "tables": {},
        "summary": {
            "total": len(SEMANTIC_INDEX_TABLES),
            "present": 0,
            "valid": 0,
            "invalid": 0,
            "missing": 0,
            "missingRequired": 0,
            "missingOptional": 0,
        },
    }

    if not db_path.is_file():
        results["status"] = "skip"
        results["summary"]["missing"] = results["summary"]["total"]
        log_info("project-index.db 不存在，下游 Agent 将回退到自行发现模式")
        stdout_json(results)
        return

    for table_name, spec in SEMANTIC_INDEX_TABLES.items():
        table_result = {
            "exists": False,
            "valid": False,
            "rowCount": 0,
            "reason": None,
            "validation": None,
            "description": spec["description"],
            "phase": spec["phase"],
            "required": spec["required"],
        }

        if not _table_exists(db_path, table_name):
            table_result["reason"] = "table_not_found"
            results["summary"]["missing"] += 1
            if spec["required"]:
                results["summary"]["missingRequired"] += 1
            else:
                results["summary"]["missingOptional"] += 1
            results["tables"][table_name] = table_result
            continue

        table_result["exists"] = True
        results["summary"]["present"] += 1

        row_count = _table_row_count(db_path, table_name)
        table_result["rowCount"] = row_count

        # 必需表行数为 0 视为无效
        if spec["required"] and row_count == 0:
            table_result["reason"] = "required_table_empty"
            results["summary"]["invalid"] += 1
            results["tables"][table_name] = table_result
            continue

        # 内容抽检
        validate_fn_name = spec.get("validate_fn")
        if validate_fn_name and row_count > 0:
            if validate_fn_name == "_validate_files_table":
                validation = _validate_files_table(db_path, sample_size)
            elif validate_fn_name == "_validate_sinks_table":
                validation = _validate_sinks_table(db_path, sample_size)
            elif validate_fn_name == "_validate_call_graph_table":
                validation = _validate_call_graph_table(db_path, sample_size)
            else:
                validation = None

            if validation:
                table_result["validation"] = validation
                if validation.get("failed", 0) > 0 and validation.get("sampled", 0) > 0:
                    pass_rate = validation["passed"] / validation["sampled"]
                    if pass_rate < 0.6:
                        table_result["reason"] = f"content_validation_failed (pass_rate={pass_rate:.2f})"
                        results["summary"]["invalid"] += 1
                        results["tables"][table_name] = table_result
                        continue

        table_result["valid"] = True
        results["summary"]["valid"] += 1
        results["tables"][table_name] = table_result

    # 汇总判定
    required_missing = sum(
        1 for t, s in SEMANTIC_INDEX_TABLES.items()
        if s["required"] and results["tables"].get(t, {}).get("reason") in ("table_not_found", "required_table_empty")
    )

    if results["summary"]["invalid"] > 0 or required_missing > 0:
        results["status"] = "warn" if required_missing == 0 else "fail"
        log_warn(
            f"语义索引校验：{results['summary']['valid']}/{results['summary']['present']} 有效，"
            f"{results['summary']['invalid']} 无效，{results['summary']['missing']} 缺失"
            + (f"（其中 {required_missing} 个必需表缺失/为空）" if required_missing > 0 else "")
        )
    elif results["summary"]["present"] == 0:
        results["status"] = "skip"
        log_info("project-index.db 中无索引表，下游 Agent 将回退到自行发现模式")
    else:
        log_ok(
            f"语义索引校验通过：{results['summary']['valid']}/{results['summary']['present']} 有效，"
            f"{results['summary']['missing']} 缺失（可选）"
        )

    stdout_json(results)


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Checkpoint 采样校验脚本：自动化验证 agent 输出真实性",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
子命令说明：
  verify-artifacts       校验关键 agent 产物是否完整落盘（推荐在 merge 前执行）
  verify-explore         校验探索阶段输出（文件列表、入口点、依赖）
  verify-semantic-index  校验语义索引数据库完整性（project-index.db SQLite 表）
  verify-scan            校验扫描阶段合并结果（finding 路径 + riskCode 真实性 + 严重性统计）

  别名：verify-stage1 = verify-explore, verify-stage2 = verify-scan

示例：
  %(prog)s verify-artifacts --batch-dir .codebuddy/security-scan/runs/project-audit-xxx --agents indexer,vuln-scan
  %(prog)s verify-explore --batch-dir .codebuddy/security-scan/runs/project-audit-xxx
  %(prog)s verify-semantic-index --batch-dir .codebuddy/security-scan/runs/project-audit-xxx
  %(prog)s verify-scan --batch-dir .codebuddy/security-scan/runs/project-audit-xxx
  %(prog)s verify-scan --batch-dir .codebuddy/security-scan/runs/project-audit-xxx --prefix batch-1-
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # verify-artifacts
    sp0 = subparsers.add_parser('verify-artifacts', help='校验关键 agent 产物是否已完整落盘')
    sp0.add_argument('--batch-dir', required=True, help='审计批次目录路径')
    sp0.add_argument('--agents', required=True, help='需要检查的 agent 列表，逗号分隔')
    sp0.add_argument('--prefix', default='', help='文件名前缀（分批模式用，如 batch-1-）')

    # verify-explore + verify-stage1 (别名)
    for cmd_name in ('verify-explore', 'verify-stage1'):
        sp = subparsers.add_parser(cmd_name, help='校验探索阶段输出')
        sp.add_argument('--batch-dir', required=True, help='审计批次目录路径')
        sp.add_argument('--sample-size', type=int, default=5, help='采样数量（默认 5）')

    # verify-semantic-index
    sp_si = subparsers.add_parser('verify-semantic-index', help='校验语义索引数据库完整性（project-index.db）')
    sp_si.add_argument('--batch-dir', required=True, help='审计批次目录路径')
    sp_si.add_argument('--sample-size', type=int, default=5, help='采样数量（默认 5）')

    # verify-scan + verify-stage2 (别名)
    for cmd_name in ('verify-scan', 'verify-stage2'):
        sp = subparsers.add_parser(cmd_name, help='校验扫描阶段合并结果')
        sp.add_argument('--batch-dir', required=True, help='审计批次目录路径')
        sp.add_argument('--prefix', default='', help='文件名前缀（分批模式用，如 batch-1-）')
        sp.add_argument('--sample-size', type=int, default=5, help='采样数量（默认 5）')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    batch_dir = Path(args.batch_dir)
    if not batch_dir.is_dir():
        log_error(f"批次目录不存在: {batch_dir}")
        stdout_json({"status": "error", "message": f"batch dir not found: {batch_dir}"})
        sys.exit(1)

    if args.command == 'verify-artifacts':
        verify_artifacts(batch_dir, args.agents, args.prefix)
    elif args.command in ('verify-explore', 'verify-stage1'):
        verify_explore(batch_dir, args.sample_size)
    elif args.command == 'verify-semantic-index':
        verify_semantic_index(batch_dir, args.sample_size)
    elif args.command in ('verify-scan', 'verify-stage2'):
        verify_scan(batch_dir, args.sample_size, args.prefix)


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
