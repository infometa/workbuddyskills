#!/usr/bin/env python3
"""
大仓分片扫描辅助脚本。

子命令：
  plan       基于 project-index.db 生成 shard-plan.json，并初始化 shards/<id>/ 子批次目录
  status     更新单个 shard 的断点状态
  correlate  基于全局索引生成跨分片关联风险候选 cross-shard-correlation.json

设计目标：
  - 大仓 project 扫描自动拆分为可恢复的子目录扫描，降低中断概率
  - 只生成候选和编排元数据，不凭空生成安全 finding
  - 最终 finding 仍由现有 scan / merge / report / gate 管线消费
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import make_logger, stdout_json, load_json_file, write_json_file


log_info, log_ok, log_warn, log_error = make_logger("sharder")

SOURCE_EXTENSIONS = {
    ".java", ".kt", ".kts", ".py", ".go", ".js", ".ts", ".jsx", ".tsx",
    ".php", ".rb", ".cs", ".cpp", ".c", ".rs", ".swift", ".vue",
}
MONOREPO_MARKERS = (
    "pnpm-workspace.yaml", "lerna.json", "turbo.json", "nx.json", "rush.json",
    "workspace.json", "packages", "apps", "services",
)
SHARED_TOKENS = {
    "auth", "authentication", "authorization", "middleware", "common", "shared",
    "config", "configs", "security", "guard", "guards", "filter", "filters",
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _safe_shard_id(shard_id):
    text = str(shard_id or "")
    if not text.startswith("shard-"):
        raise ValueError(f"invalid shard id: {text}")
    suffix = text.removeprefix("shard-")
    if not suffix.isdigit() or not (1 <= len(suffix) <= 5):
        raise ValueError(f"invalid shard id: {text}")
    return text


def _db_path(batch_dir):
    return Path(batch_dir) / "project-index.db"


def _connect_readonly(batch_dir):
    db = _db_path(batch_dir)
    if not db.exists():
        raise FileNotFoundError(f"project-index.db not found: {db}")
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _rel(path):
    return str(path or "").replace("\\", "/").strip("/")


def _dir_key(file_path):
    path = _rel(file_path)
    parts = [p for p in path.split("/") if p]
    if not parts:
        return "."
    if len(parts) == 1:
        return "."
    if parts[0] in {"src", "lib", "app", "server", "backend", "frontend"} and len(parts) >= 2:
        return "/".join(parts[:2])
    if parts[0] in {"packages", "apps", "services", "modules"} and len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0]


def _is_shared_dir(dir_key):
    tokens = {p.lower().replace("-", "_") for p in _rel(dir_key).split("/")}
    normalized = set()
    for token in tokens:
        normalized.add(token)
        normalized.update(token.split("_"))
    return bool(normalized & SHARED_TOKENS)


def _path_matches(path, prefixes):
    p = _rel(path)
    for prefix in prefixes:
        q = _rel(prefix)
        if not q:
            continue
        if p == q or p.startswith(q + "/"):
            return True
    return False


def _include_globs(paths):
    globs = []
    for path in paths:
        p = _rel(path)
        if not p or p == ".":
            globs.append("*")
        elif any(ch in p for ch in "*?["):
            globs.append(p)
        else:
            globs.append(f"{p}/**")
    return globs


def _load_index_summary(conn):
    def scalar(sql, default=0):
        try:
            row = conn.execute(sql).fetchone()
            return row[0] if row else default
        except sqlite3.OperationalError:
            return default

    return {
        "fileCount": int(scalar("SELECT COUNT(*) FROM files")),
        "totalLines": int(scalar("SELECT COALESCE(SUM(lines), 0) FROM files")),
        "sinkCount": int(scalar("SELECT COUNT(*) FROM sinks")),
        "endpointCount": int(scalar("SELECT COUNT(*) FROM endpoints")),
        "entryPointCount": int(scalar("SELECT COUNT(*) FROM files WHERE is_entry=1")),
    }


def _load_files(conn):
    rows = conn.execute(
        "SELECT path, language, lines, is_entry, category FROM files ORDER BY path ASC"
    ).fetchall()
    return [dict(r) for r in rows]


def _load_sink_stats(conn):
    try:
        rows = conn.execute(
            """
            SELECT file_path, COUNT(*) AS sink_count, MIN(severity_level) AS min_severity
            FROM sinks
            GROUP BY file_path
            """
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    return {
        _rel(r["file_path"]): {
            "sinkCount": int(r["sink_count"] or 0),
            "minSeverity": int(r["min_severity"] or 4),
        }
        for r in rows
    }


def _has_monorepo_markers(project_path):
    root = Path(project_path)
    hits = []
    for marker in MONOREPO_MARKERS:
        if (root / marker).exists():
            hits.append(marker)
    if not hits:
        package_files = list(root.glob("*/package.json"))[:3]
        if len(package_files) >= 2:
            hits.append("multi-package-json")
    return hits


def _build_units(files, sink_stats):
    units = {}
    for item in files:
        path = _rel(item.get("path"))
        if not path:
            continue
        key = _dir_key(path)
        stat = sink_stats.get(path, {})
        unit = units.setdefault(key, {
            "path": key,
            "fileCount": 0,
            "totalLines": 0,
            "entryPointCount": 0,
            "sinkCount": 0,
            "minSeverity": 4,
            "files": [],
        })
        lines = int(item.get("lines") or 0)
        unit["fileCount"] += 1
        unit["totalLines"] += lines
        unit["entryPointCount"] += 1 if int(item.get("is_entry") or 0) else 0
        unit["sinkCount"] += int(stat.get("sinkCount") or 0)
        unit["minSeverity"] = min(unit["minSeverity"], int(stat.get("minSeverity") or 4))
        unit["files"].append(path)
    return list(units.values())


def _pack_shards(units, shared_paths, max_files, max_lines):
    active_units = [u for u in units if u["path"] not in shared_paths]
    if not active_units and shared_paths:
        # 极端项目可能所有目录都命中 sharedContext；此时不能产出空 shard，
        # 回退为按普通目录切分，避免大仓流程无扫描对象。
        active_units = list(units)
        shared_paths = []
    active_units.sort(key=lambda u: (u["minSeverity"], -u["sinkCount"], -u["fileCount"], u["path"]))

    shards = []
    current = None

    def new_shard():
        shard_id = f"shard-{len(shards) + 1:03d}"
        return {
            "id": shard_id,
            "name": shard_id,
            "paths": [],
            "includeGlobs": [],
            "fileCount": 0,
            "totalLines": 0,
            "entryPointCount": 0,
            "sinkCount": 0,
            "minSeverity": 4,
            "priority": "medium",
            "status": "pending",
        }

    for unit in active_units:
        if current is None:
            current = new_shard()
        would_overflow = (
            current["paths"] and (
                current["fileCount"] + unit["fileCount"] > max_files or
                current["totalLines"] + unit["totalLines"] > max_lines
            )
        )
        if would_overflow:
            shards.append(current)
            current = new_shard()
        current["paths"].append(unit["path"])
        current["fileCount"] += unit["fileCount"]
        current["totalLines"] += unit["totalLines"]
        current["entryPointCount"] += unit["entryPointCount"]
        current["sinkCount"] += unit["sinkCount"]
        current["minSeverity"] = min(current["minSeverity"], unit["minSeverity"])
    if current and current["paths"]:
        shards.append(current)

    for shard in shards:
        scan_paths = list(dict.fromkeys(shard["paths"] + shared_paths))
        shard["includeGlobs"] = _include_globs(scan_paths)
        if shard["minSeverity"] <= 1 or shard["sinkCount"] >= 20:
            shard["priority"] = "high"
        elif shard["sinkCount"] == 0 and shard["entryPointCount"] == 0:
            shard["priority"] = "low"
    return shards


def _prepare_shard_dirs(batch_dir, plan):
    batch_path = Path(batch_dir)
    parent_db = batch_path / "project-index.db"
    parent_batch_plan = load_json_file(batch_path / "batch-plan.json") or {}
    for shard in plan.get("shards", []):
        shard_id = _safe_shard_id(shard.get("id"))
        shard_dir = batch_path / "shards" / shard_id
        (shard_dir / "agents").mkdir(parents=True, exist_ok=True)
        shard_plan = dict(parent_batch_plan)
        shard_plan.update({
            "parent_batch_id": batch_path.name,
            "shard_id": shard_id,
            "shard_name": shard.get("name", shard_id),
            "shard_paths": shard.get("paths", []),
            "shared_context": plan.get("sharedContext", []),
            "include_globs": shard.get("includeGlobs", []),
            "total_files": shard.get("fileCount", 0),
            "large_repo_shard": True,
        })
        write_json_file(shard_dir / "batch-plan.json", shard_plan)
        write_json_file(shard_dir / "shard-status.json", {
            "id": shard_id,
            "status": shard.get("status", "pending"),
            "updatedAt": _now_iso(),
            "paths": shard.get("paths", []),
        })
        target_db = shard_dir / "project-index.db"
        if parent_db.exists() and not target_db.exists():
            try:
                rel_target = os.path.relpath(parent_db, shard_dir)
                os.symlink(rel_target, target_db)
            except OSError:
                shutil.copy2(parent_db, target_db)


def cmd_plan(args):
    batch_dir = Path(args.batch_dir)
    conn = _connect_readonly(batch_dir)
    try:
        summary = _load_index_summary(conn)
        files = _load_files(conn)
        sink_stats = _load_sink_stats(conn)
    finally:
        conn.close()

    markers = _has_monorepo_markers(args.project_path)
    large_repo = bool(args.force) or (
        summary["fileCount"] >= args.file_threshold or
        summary["totalLines"] >= args.line_threshold or
        summary["sinkCount"] >= args.sink_threshold or
        bool(markers)
    )

    units = _build_units(files, sink_stats)
    shared_units = [u for u in units if _is_shared_dir(u["path"])]
    shared_limit_files = max(1, args.max_files_per_shard // 2)
    shared_paths = [
        u["path"] for u in sorted(shared_units, key=lambda x: (-x["sinkCount"], x["path"]))
        if u["fileCount"] <= shared_limit_files
    ]

    shards = _pack_shards(units, shared_paths, args.max_files_per_shard, args.max_lines_per_shard) if large_repo else []
    plan = {
        "version": "1.0",
        "generatedAt": _now_iso(),
        "largeRepo": large_repo,
        "strategy": "directory_sharding" if large_repo else "single_batch",
        "rootBatchId": batch_dir.name,
        "scanMode": args.scan_mode,
        "projectPath": str(Path(args.project_path).resolve()),
        "thresholds": {
            "fileThreshold": args.file_threshold,
            "lineThreshold": args.line_threshold,
            "sinkThreshold": args.sink_threshold,
            "maxFilesPerShard": args.max_files_per_shard,
            "maxLinesPerShard": args.max_lines_per_shard,
        },
        "summary": summary,
        "monorepoMarkers": markers,
        "sharedContext": shared_paths if large_repo else [],
        "shardCount": len(shards),
        "shards": shards,
    }
    write_json_file(batch_dir / "shard-plan.json", plan)
    if large_repo:
        _prepare_shard_dirs(batch_dir, plan)
    log_ok(f"已生成 shard-plan.json largeRepo={large_repo} shards={len(shards)}")
    stdout_json({
        "status": "ok",
        "largeRepo": large_repo,
        "shardCount": len(shards),
        "sharedContextCount": len(plan.get("sharedContext", [])),
        "planFile": "shard-plan.json",
    })


def cmd_status(args):
    batch_dir = Path(args.batch_dir)
    try:
        requested_shard_id = _safe_shard_id(args.shard_id)
    except ValueError as exc:
        stdout_json({"status": "error", "message": str(exc)})
        sys.exit(1)
    plan_path = batch_dir / "shard-plan.json"
    plan = load_json_file(plan_path)
    if not plan:
        log_error(f"shard-plan.json 不存在: {plan_path}")
        stdout_json({"status": "error", "message": "shard-plan.json not found"})
        sys.exit(1)

    updated = False
    for shard in plan.get("shards", []):
        try:
            shard_id = _safe_shard_id(shard.get("id"))
        except ValueError:
            continue
        if shard_id == requested_shard_id:
            shard["status"] = args.status
            shard["updatedAt"] = _now_iso()
            if args.message:
                shard["message"] = args.message
            updated = True
            shard_dir = batch_dir / "shards" / shard_id
            write_json_file(shard_dir / "shard-status.json", {
                "id": shard_id,
                "status": args.status,
                "message": args.message or "",
                "updatedAt": shard["updatedAt"],
                "paths": shard.get("paths", []),
            })
            break
    if not updated:
        stdout_json({"status": "error", "message": f"unknown shard: {requested_shard_id}"})
        sys.exit(1)
    write_json_file(plan_path, plan)
    stdout_json({"status": "ok", "shardId": requested_shard_id, "shardStatus": args.status})


def _file_to_shard(plan, file_path):
    path = _rel(file_path)
    for shard in plan.get("shards", []):
        if _path_matches(path, shard.get("paths", [])):
            return shard.get("id")
    if _path_matches(path, plan.get("sharedContext", [])):
        return "shared"
    return "unknown"


def cmd_correlate(args):
    batch_dir = Path(args.batch_dir)
    plan = load_json_file(batch_dir / "shard-plan.json")
    if not plan or not plan.get("largeRepo"):
        result = {
            "generatedAt": _now_iso(),
            "candidateCount": 0,
            "candidates": [],
            "note": "非大仓分片模式，跳过跨分片关联候选生成",
        }
        write_json_file(batch_dir / "cross-shard-correlation.json", result)
        stdout_json({"status": "ok", "candidateCount": 0, "outputFile": "cross-shard-correlation.json"})
        return

    conn = _connect_readonly(batch_dir)
    try:
        sinks = [dict(r) for r in conn.execute(
            "SELECT file_path, line, type, severity_level, defense_status, code_snippet FROM sinks ORDER BY severity_level ASC, file_path ASC"
        ).fetchall()]
        endpoints = [dict(r) for r in conn.execute(
            "SELECT file_path, method, path, handler, line, auth_type, priority FROM endpoints ORDER BY priority ASC, file_path ASC"
        ).fetchall()]
        edges = [dict(r) for r in conn.execute(
            "SELECT caller_file, caller_func, caller_line, callee_file, callee_func, callee_line, depth, source FROM call_graph ORDER BY depth ASC LIMIT ?",
            (args.limit * 10,)
        ).fetchall()]
    except sqlite3.OperationalError as exc:
        log_warn(f"索引表不完整，跨分片关联候选降级为空: {exc}")
        sinks, endpoints, edges = [], [], []
    finally:
        conn.close()

    sinks_by_file = {}
    for sink in sinks:
        sinks_by_file.setdefault(_rel(sink.get("file_path")), []).append(sink)
    endpoints_by_file = {}
    for endpoint in endpoints:
        endpoints_by_file.setdefault(_rel(endpoint.get("file_path")), []).append(endpoint)

    candidates = []
    seen = set()

    def add_candidate(candidate):
        key = json.dumps({k: candidate.get(k) for k in ("kind", "callerFile", "calleeFile", "sinkLine", "sinkType")}, sort_keys=True)
        if key in seen or len(candidates) >= args.limit:
            return
        seen.add(key)
        candidate["id"] = f"XSHARD-{len(candidates) + 1:03d}"
        candidates.append(candidate)

    for edge in edges:
        caller = _rel(edge.get("caller_file"))
        callee = _rel(edge.get("callee_file"))
        if not caller or not callee or caller == callee:
            continue
        caller_shard = _file_to_shard(plan, caller)
        callee_shard = _file_to_shard(plan, callee)
        if caller_shard == callee_shard or "unknown" in (caller_shard, callee_shard):
            continue
        callee_sinks = sinks_by_file.get(callee, [])[:3]
        caller_endpoints = endpoints_by_file.get(caller, [])[:2]
        if callee_sinks:
            for sink in callee_sinks:
                add_candidate({
                    "kind": "cross_shard_sink_call",
                    "callerShard": caller_shard,
                    "calleeShard": callee_shard,
                    "callerFile": caller,
                    "callerFunc": edge.get("caller_func"),
                    "callerLine": edge.get("caller_line"),
                    "calleeFile": callee,
                    "calleeFunc": edge.get("callee_func"),
                    "calleeLine": edge.get("callee_line"),
                    "sinkLine": sink.get("line"),
                    "sinkType": sink.get("type"),
                    "sinkSeverityLevel": sink.get("severity_level"),
                    "defenseStatus": sink.get("defense_status"),
                    "endpoint": caller_endpoints[0] if caller_endpoints else None,
                    "reason": "调用链跨越分片且被调文件存在危险 Sink，需复核入口可达性与防御是否跨模块丢失",
                })
        elif caller_endpoints and callee_shard not in (caller_shard, "unknown"):
            unauth = [e for e in caller_endpoints if not e.get("auth_type") or e.get("auth_type") == "none"]
            if unauth:
                add_candidate({
                    "kind": "cross_shard_noauth_entry_call",
                    "callerShard": caller_shard,
                    "calleeShard": callee_shard,
                    "callerFile": caller,
                    "callerFunc": edge.get("caller_func"),
                    "callerLine": edge.get("caller_line"),
                    "calleeFile": callee,
                    "calleeFunc": edge.get("callee_func"),
                    "calleeLine": edge.get("callee_line"),
                    "endpoint": unauth[0],
                    "reason": "无认证或弱认证入口跨分片调用业务模块，需复核鉴权/租户/所有权校验是否在跨模块链路中保持一致",
                })

    result = {
        "generatedAt": _now_iso(),
        "rootBatchId": batch_dir.name,
        "candidateCount": len(candidates),
        "candidates": candidates,
        "instructions": {
            "consumer": "cross-shard-scan/red-team",
            "output": "agents/cross-shard-scan.json",
            "note": "这些是跨目录关联风险候选，不等同于 confirmed findings；需由 Agent 复核后输出标准 findings。",
        },
    }
    write_json_file(batch_dir / "cross-shard-correlation.json", result)
    log_ok(f"已生成 cross-shard-correlation.json candidates={len(candidates)}")
    stdout_json({"status": "ok", "candidateCount": len(candidates), "outputFile": "cross-shard-correlation.json"})


def main():
    parser = argparse.ArgumentParser(description="大仓分片扫描辅助脚本")
    subparsers = parser.add_subparsers(dest="command")

    p_plan = subparsers.add_parser("plan", help="生成 shard-plan.json")
    p_plan.add_argument("--batch-dir", required=True)
    p_plan.add_argument("--project-path", default=".")
    p_plan.add_argument("--scan-mode", default="deep", choices=["fast", "light", "deep"])
    p_plan.add_argument("--file-threshold", type=int, default=500)
    p_plan.add_argument("--line-threshold", type=int, default=80000)
    p_plan.add_argument("--sink-threshold", type=int, default=200)
    p_plan.add_argument("--max-files-per-shard", type=int, default=180)
    p_plan.add_argument("--max-lines-per-shard", type=int, default=30000)
    p_plan.add_argument("--force", action="store_true")
    p_plan.set_defaults(func=cmd_plan)

    p_status = subparsers.add_parser("status", help="更新 shard 状态")
    p_status.add_argument("--batch-dir", required=True)
    p_status.add_argument("--shard-id", required=True)
    p_status.add_argument("--status", required=True, choices=["pending", "running", "completed", "failed", "skipped"])
    p_status.add_argument("--message", default="")
    p_status.set_defaults(func=cmd_status)

    p_corr = subparsers.add_parser("correlate", help="生成跨分片关联风险候选")
    p_corr.add_argument("--batch-dir", required=True)
    p_corr.add_argument("--project-path", default=".")
    p_corr.add_argument("--limit", type=int, default=80)
    p_corr.set_defaults(func=cmd_correlate)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
