# -*- coding: utf-8 -*-
"""
stage4_snapshot.py — 阶段4快照工作流（光模块信号监控 · 主理人调用）

== 修复前的错误 ==
  旧阶段4把每期 judge_direction 写死为 0。
  而 self_evolve.compute_hit_rates 配对 (t, t1) 时读的是 t1.judge_direction
  当作「对 t 的裁判方向」，为 0 即 continue 跳过。
  → 所有配对都被跳过 → 校准回看永远产不出真实命中率。

== 修复后的正确语义 ==
  本期的 judge_direction = 对「上一期」信号的真实裁判方向
    = 旭创/新易盛 利润增速方向（加速 +1 / 减速 -1 / 持平 0）
    = 主理人在本阶段查询数据源(万得/通达信/互联网)后传入
  数据源不可用时，显式传 0 并标注 verdict_source="unavailable"，
  该校准配对将被诚实跳过（不是假装校准）。

== 用法 ==
  python stage4_snapshot.py \
      --run-date 2026-07-14 \
      --mode 部分 \
      --signal-signs believe-in-light-run1_resolved.json \
      --prosperity-direction 扩张 --prosperity-net 4.6 \
      --confidence-raw 0.24 --confidence-label 低 \
      --judge-direction 1 --verdict-source "互联网:旭创Q2利润加速"

== 数据晚到时回填历史期次 ==
  python self_evolve.py --backfill 2026-07-14 --judge-direction 1 \
      --verdict-source "万得:旭创Q2利润加速"
"""
from __future__ import annotations
import json
import argparse
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import self_evolve  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="阶段4快照工作流（修复版）")
    ap.add_argument("--run-date", required=True, help="本期 run_date (YYYY-MM-DD)")
    ap.add_argument("--mode", required=True, help="🟢专业 / 🟡部分 / 🔴纯网")
    ap.add_argument("--signal-signs", required=True,
                    help="阴果验产出的 {信号名: effective_sign} JSON 文件路径")
    ap.add_argument("--prosperity-direction", required=True, help="扩张 / 收缩")
    ap.add_argument("--prosperity-net", type=float, required=True, help="景气度净值")
    ap.add_argument("--confidence-raw", type=float, required=True, help="置信度原始值")
    ap.add_argument("--confidence-label", required=True, help="高 / 中 / 低")
    ap.add_argument("--judge-direction", type=int, required=True, choices=[-1, 0, 1],
                    help="对上一期的真实裁判方向 (+1加速 / -1减速 / 0持平或不可用)")
    ap.add_argument("--verdict-source", default="unknown",
                    help="裁判方向来源说明（数据源 / 人工）")
    args = ap.parse_args()

    with open(args.signal_signs, encoding="utf-8") as f:
        signal_signs = json.load(f)

    snapshot = {
        "run_date": args.run_date,
        "mode": args.mode,
        "signal_signs": signal_signs,
        "judge_direction": args.judge_direction,
        "verdict_source": args.verdict_source,
        "景气度": {"net": args.prosperity_net, "direction": args.prosperity_direction},
        "置信度": {"raw": args.confidence_raw, "label": args.confidence_label},
    }
    self_evolve.store_run(snapshot)


if __name__ == "__main__":
    main()
