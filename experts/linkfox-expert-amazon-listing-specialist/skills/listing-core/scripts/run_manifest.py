#!/usr/bin/env python3
"""run-manifest — listing-core 前后端契约（spec §7.6）。只写 JSON，不碰文案。"""
from __future__ import annotations
import argparse, json, os, time
from datetime import datetime, timezone

STAGES = [("facts", "采集商品信息"), ("insight", "洞察与关键词"), ("write", "生成 Listing")]
STATUSES = {"pending", "active", "complete", "failed"}

def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _save(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _now() -> tuple[str, int]:
    return datetime.now(timezone.utc).isoformat(), time.time_ns() // 1_000_000

def parse_profile(value: str | None) -> dict:
    """档位参数：接受 JSON 串，也接受裸值（fast 档已并入 standard，传入仅作记录）。

    调用方最自然的写法是 `--profile standard`；早期只认 JSON 串，导致反复试错。
    """
    text = (value or "").strip()
    if not text:
        return {}
    if text.startswith("{"):
        return json.loads(text)
    return {"profile": text}


def init_manifest(run_dir: str, mode: str, profile: dict) -> str:
    """初始化 manifest。幂等：同一 run-dir 重复 init 不重置已推进的阶段。

    分段交付要求 run 一开始（S1 之前）就 init 并逐阶段 update，前端靠 manifest 的
    `Saved full response:` 行实时渲染任务进度；而 `run_full.py start` 在写作阶段
    会再走一次 init——此时必须保留 facts/insight 已记录的状态、产物与 final。
    """
    run_dir = os.path.abspath(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, "run-manifest.json")
    created_at, created_epoch_ms = _now()
    fresh = {
        "kind": "listingRunManifest", "schema_version": 1,
        "run_id": os.path.basename(run_dir), "mode": mode,
        "profile": profile or {}, "created_at": created_at,
        "timing": {
            "started_at": created_at,
            "_started_at_epoch_ms": created_epoch_ms,
            "steps": {},
        },
        "stages": [{"id": sid, "label": label, "status": "pending", "artifacts": []}
                   for sid, label in STAGES],
        "final": {},
    }
    if os.path.isfile(path):
        try:
            existing = _load(path)
        except (OSError, json.JSONDecodeError):
            existing = None
        if isinstance(existing, dict) and existing.get("kind") == "listingRunManifest":
            if isinstance(existing.get("created_at"), str):
                fresh["created_at"] = existing["created_at"]
            if isinstance(existing.get("timing"), dict):
                fresh["timing"] = existing["timing"]
            if isinstance(existing.get("stages"), list) and existing["stages"]:
                fresh["stages"] = existing["stages"]
            if isinstance(existing.get("final"), dict):
                fresh["final"] = existing["final"]
    _save(path, fresh)
    return path


def record_timing(manifest_path: str, step_id: str, status: str,
                  duration_ms: int | float | None = None,
                  metrics: dict | None = None) -> dict:
    """记录真实子步骤时间；供跨进程 pipeline 统一计时，不靠文件时间戳推算。"""
    if status not in {"active", "complete", "failed"}:
        raise ValueError(f"illegal timing status: {status}")
    manifest_path = os.path.abspath(manifest_path)
    m = _load(manifest_path)
    timing = m.setdefault("timing", {"steps": {}})
    steps = timing.setdefault("steps", {})
    step = steps.setdefault(step_id, {})
    now_iso, now_ms = _now()
    step["status"] = status
    if status == "active":
        step.setdefault("started_at", now_iso)
        step.setdefault("_started_at_epoch_ms", now_ms)
    else:
        step.setdefault("started_at", now_iso)
        step["completed_at"] = now_iso
        if duration_ms is None:
            started_ms = step.get("_started_at_epoch_ms")
            if isinstance(started_ms, int):
                duration_ms = max(0, now_ms - started_ms)
        if duration_ms is not None:
            step["duration_ms"] = max(0, round(float(duration_ms)))
    if metrics:
        step.setdefault("metrics", {}).update(metrics)
    _save(manifest_path, m)
    return m


def complete_timing(manifest_path: str) -> dict:
    """完成端到端计时，覆盖 pre-manifest 到 final stdout 前的全部墙钟时间。"""
    manifest_path = os.path.abspath(manifest_path)
    m = _load(manifest_path)
    timing = m.setdefault("timing", {"steps": {}})
    now_iso, now_ms = _now()
    timing["completed_at"] = now_iso
    started_ms = timing.get("_started_at_epoch_ms")
    if isinstance(started_ms, int):
        timing["total_duration_ms"] = max(0, now_ms - started_ms)
    _save(manifest_path, m)
    return m

def update_stage(manifest_path: str, stage_id: str, status: str,
                 artifacts: list | None = None, branches: list | None = None,
                 activate: str | None = None, metrics: dict | None = None) -> dict:
    """更新单个阶段；`activate` 可在同一次写盘里把下一阶段置为 active。

    分段交付：阶段边界只需要一条 Bash、一行 `Saved full response:` 就能同时
    收尾上一阶段并点亮下一阶段（如 facts complete + insight active）。
    """
    manifest_path = os.path.abspath(manifest_path)
    if status not in STATUSES:
        raise ValueError(f"illegal status: {status}")
    m = _load(manifest_path)
    stage = next((s for s in m["stages"] if s["id"] == stage_id), None)
    if stage is None:
        raise ValueError(f"unknown stage: {stage_id}")
    previous_status = stage.get("status")
    now_iso, now_ms = _now()
    stage["status"] = status
    if status == "active" and previous_status != "active":
        stage["started_at"] = now_iso
        stage["_started_at_epoch_ms"] = now_ms
        stage["attempts"] = int(stage.get("attempts") or 0) + 1
    if status in {"complete", "failed"}:
        stage["completed_at"] = now_iso
        started_ms = stage.get("_started_at_epoch_ms")
        if isinstance(started_ms, int):
            stage["duration_ms"] = max(0, now_ms - started_ms)
    if metrics:
        stage.setdefault("metrics", {}).update(metrics)
    if artifacts:
        stage.setdefault("artifacts", []).extend(artifacts)
    if branches is not None:
        stage["branches"] = branches
    if activate:
        nxt = next((s for s in m["stages"] if s["id"] == activate), None)
        if nxt is None:
            raise ValueError(f"unknown stage: {activate}")
        if nxt["status"] == "pending":
            nxt["status"] = "active"
            nxt["started_at"] = now_iso
            nxt["_started_at_epoch_ms"] = now_ms
            nxt["attempts"] = int(nxt.get("attempts") or 0) + 1
    _save(manifest_path, m)
    return m

def set_final(manifest_path: str, **paths: str) -> dict:
    manifest_path = os.path.abspath(manifest_path)
    m = _load(manifest_path)
    m["final"].update({k: v for k, v in paths.items() if v})
    _save(manifest_path, m)
    return m

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # init subcommand
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--run-dir", required=True)
    init_parser.add_argument("--mode", required=True)
    init_parser.add_argument(
        "--profile", default="{}",
        help='档位：固定 standard（旧 fast 已并入，传入仅作记录），也可写 JSON 串',
    )
    # 下面三个是最常被顺手带上的参数；早期版本不认，导致调用方反复试错。
    init_parser.add_argument("--marketplace", default=None, help="站点代码，如 US/UK/DE")
    init_parser.add_argument("--output-language", default=None, help="输出语言，如 en_US")
    init_parser.add_argument("--auto-run", default=None, help="true/false")

    # update subcommand
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--manifest", required=True)
    update_parser.add_argument("--stage", required=True)
    update_parser.add_argument("--status", required=True)
    update_parser.add_argument("--artifact", action="append", default=[],
                               help="name=...,path=...,kind=... (repeatable)")
    update_parser.add_argument("--branches", default=None)
    update_parser.add_argument("--activate", default=None,
        help='同一次写盘顺带把该阶段从 pending 置为 active（阶段边界一条命令收尾+点亮）')
    update_parser.add_argument("--metric", action="append", default=[],
                               help="key=value 性能指标（可重复）")

    # final subcommand
    final_parser = subparsers.add_parser("final")
    final_parser.add_argument("--manifest", required=True)
    final_parser.add_argument("--listing-md")
    final_parser.add_argument("--listing-json")
    final_parser.add_argument("--check-report")
    final_parser.add_argument("--ai-readiness")
    final_parser.add_argument("--detail-preview")
    final_parser.add_argument("--score-report")

    args = parser.parse_args()

    if args.cmd == "init":
        profile = parse_profile(args.profile)
        if args.marketplace:
            profile["marketplace"] = args.marketplace
        if args.output_language:
            profile["output_language"] = args.output_language
        if args.auto_run is not None:
            profile["auto_run"] = args.auto_run.strip().lower() not in ("false", "0", "no")
        manifest_path = init_manifest(args.run_dir, args.mode, profile)
        print(f"Saved full response: {manifest_path}")

    elif args.cmd == "update":
        artifacts = []
        for artifact_str in args.artifact:
            parts = {}
            for kv in artifact_str.split(","):
                k, v = kv.split("=", 1)
                parts[k] = v
            artifacts.append(parts)
        branches = json.loads(args.branches) if args.branches else None
        metrics = {}
        for metric_str in args.metric:
            key, value = metric_str.split("=", 1)
            try:
                metrics[key] = float(value) if "." in value else int(value)
            except ValueError:
                metrics[key] = value
        update_stage(args.manifest, args.stage, args.status,
                     artifacts=artifacts or None, branches=branches,
                     activate=args.activate, metrics=metrics or None)
        normalized_manifest = os.path.abspath(args.manifest)
        print(f"Saved full response: {normalized_manifest}")

    elif args.cmd == "final":
        set_final(args.manifest,
                  listing_json=args.listing_json,
                  listing_md=args.listing_md,
                  check_report=args.check_report,
                  ai_readiness=args.ai_readiness,
                  detail_preview=args.detail_preview,
                  score_report=args.score_report)
        normalized_manifest = os.path.abspath(args.manifest)
        print(f"Saved full response: {normalized_manifest}")
