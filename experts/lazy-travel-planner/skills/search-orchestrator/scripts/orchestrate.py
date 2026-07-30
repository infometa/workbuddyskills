#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search-orchestrator · orchestrate.py
搜索编排底座主入口。串起 geo_fanout → query_expand → 多源并发执行 → dedupe → deep_read。

用法：
  python orchestrate.py \
    --intent "江西附近游玩 4 天" \
    --profile data/user_profile.json \
    --domain destination \
    --output data/.cache/run-{run_id}/candidates.json

退出码：
  0 = 成功
  1 = 程序错误
  2 = 缺连接器/key（需用户操作）
  3 = 数据为空
  4 = 触发降级（继续但置信度降级）
"""
import argparse, json, sys, os, uuid, datetime, pathlib, traceback

THIS_DIR = pathlib.Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))
sys.path.insert(0, str(THIS_DIR.parent.parent.parent / "shared"))

from check_deps import check_or_block          # noqa
from geo_fanout import geo_fanout              # noqa
from query_expand import expand_queries        # noqa
from xhs_batch_search import xhs_batch_search  # noqa
from dedupe_rank import dedupe_and_rank        # noqa
from deep_read import deep_read                # noqa


def parse_args():
    p = argparse.ArgumentParser(description="搜索编排底座")
    p.add_argument("--intent", required=True, help="用户原始自然语言意图")
    p.add_argument("--profile", required=True, help="user_profile.json 路径")
    p.add_argument("--domain", required=True,
                   choices=["destination", "poi", "accommodation", "risk"])
    p.add_argument("--output", required=True, help="结果输出 JSON 路径")
    p.add_argument("--season", default=None, help="手动指定季节，缺省按当月计算")
    p.add_argument("--duration", default=None, help="手动指定天数，影响查询模板")
    p.add_argument("--max-deep-read", type=int, default=30,
                   help="深读全文笔记数上限，默认 30")
    p.add_argument("--max-deep-comments", type=int, default=5,
                   help="深读评论笔记数上限，默认 5")
    return p.parse_args()


def log(msg):
    print(f"[orchestrate] {msg}", flush=True)


def main():
    args = parse_args()
    run_id = str(uuid.uuid4())[:8]
    log(f"🚀 run_id={run_id} domain={args.domain}")

    # === 0. 数据源体检（软告知，不阻塞） ===
    from check_deps import check_all  # noqa
    deps = check_all()
    log(f"📡 数据源状态: 美团={deps['meituan_travel']['ok']} / "
        f"xhs={deps['xhs_logged_in']['ok']}")
    has_meituan = deps["meituan_travel"]["ok"]
    has_xhs = deps["xhs_logged_in"]["ok"]
    confidence_level = "green" if (has_meituan and has_xhs) \
                       else ("yellow" if (has_meituan or has_xhs) else "gray")

    # === 1. 加载 profile ===
    try:
        with open(args.profile, encoding="utf-8") as f:
            profile = json.load(f)
    except Exception as e:
        log(f"❌ 读 profile 失败: {e}")
        sys.exit(1)

    # === 2. 地理 fan-out（输出"美团调用计划"给 agent） ===
    log("📍 Step 1: 地理意图解析 + 美团调用计划")
    fanout = geo_fanout(args.intent, args.domain)
    candidates = []  # 由 agent 调美团 skill 后写回 candidates_meituan.json
    candidates_meituan_path = pathlib.Path(args.output).parent / "candidates_meituan.json"
    if candidates_meituan_path.exists():
        try:
            candidates = json.loads(candidates_meituan_path.read_text(encoding="utf-8"))
            log(f"   ↳ 从 candidates_meituan.json 读到 {len(candidates)} 个候选")
        except Exception:
            pass
    if not candidates:
        log("⚠️ 没有美团数据 → agent 应先按 meituan_query_plan 调美团再 rerun")
        log("   query plan: " + json.dumps(fanout["meituan_query_plan"], ensure_ascii=False))
        # 把 plan 输出给 agent，sys.exit(0) 让 agent 知道下一步要做什么
        out = {
            "run_id": run_id,
            "intent": args.intent,
            "domain": args.domain,
            "stage": "awaiting_meituan",
            "meituan_query_plan": fanout["meituan_query_plan"],
            "next_step": f"agent 调美团 skill 拿数据 → 写到 {candidates_meituan_path} → rerun"
        }
        pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": True, "stage": "awaiting_meituan",
                          "plan": fanout["meituan_query_plan"]}, ensure_ascii=False))
        sys.exit(0)

    # === 3. 查询矩阵生成 ===
    log("🔍 Step 2: 查询矩阵生成（模板 + LLM 微调）")
    queries = expand_queries(
        candidates=candidates,
        domain=args.domain,
        profile=profile,
        intent=args.intent,
        season=args.season,
        duration=args.duration,
    )
    log(f"   ↳ 生成 {len(queries)} 条查询")

    # === 4. 并发执行（≤2 worker）+ 自动熔断降级 ===
    log("📡 Step 3: 多源串行/并发执行")
    raw_results = xhs_batch_search(queries, concurrency=2, error_threshold=3)
    log(f"   ↳ 总 raw 笔记数 {sum(len(r.get('notes', [])) for r in raw_results)}")

    # === 5. 去重 + 排序 ===
    log("🧹 Step 4: 去重 + 排序")
    ranked = dedupe_and_rank(raw_results)
    log(f"   ↳ 去重后 {len(ranked)} 条")

    # === 6. Top N 深读 ===
    log(f"📖 Step 5: 深读 Top {args.max_deep_read} / 评论 Top {args.max_deep_comments}")
    deeper = deep_read(ranked,
                       max_full=args.max_deep_read,
                       max_comments=args.max_deep_comments)

    # === 7. 组装输出 ===
    out = {
        "run_id": run_id,
        "intent": args.intent,
        "domain": args.domain,
        "geo_candidates": candidates,
        "queries": queries,
        "evidence": deeper,
        "metadata": {
            "queried_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "version": "1.0.0",
            "stats": {
                "candidates": len(candidates),
                "queries": len(queries),
                "raw_notes": sum(len(r.get("notes", [])) for r in raw_results),
                "deduped": len(ranked),
                "deep_read": min(args.max_deep_read, len(ranked)),
            }
        }
    }
    out_path = pathlib.Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"✅ 完成 → {out_path}")
    print(json.dumps({"ok": True, "output": str(out_path), "run_id": run_id}, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        sys.exit(1)
