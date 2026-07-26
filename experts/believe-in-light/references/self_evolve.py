# -*- coding: utf-8 -*-
"""
self_evolve.py — 自进化引擎（光模块信号监控）

自进化范围（参数层，安全边界内）：
  ① 多期快照序列存储 —— references/runs/，每期存盘 + 更新最新指针
  ② R（累计期数）     —— 每跑一期 +1，供权仲校映射为 0.3/0.6/0.9
  ③ 信号命中率         —— 信号 effective_sign vs 下期「统一裁判」方向
                         （旭创/新易盛利润增速方向：加速 +1 / 减速 -1）
                         季度回看写 calibration.json，替换默认 0.5

结构性框架（因果链结构 / 路由规则 / 九宫格映射）保持人定，不自进化。

用法：
  python self_evolve.py --store <本期快照json>     # 存盘 + 触发校准检查
  python self_evolve.py --status                  # 打印期数 / 命中率 / 校准状态
  python self_evolve.py --hitrates                # 从 runs/ 算当前命中率
  python self_evolve.py --self-test               # 模拟多期验证
依赖：标准库 only
"""
from __future__ import annotations
import json
import argparse
import sys
import os

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.join(BASE, "runs")
LATEST = os.path.join(BASE, "last_run_snapshot.json")
CALIB = os.path.join(BASE, "calibration.json")

CAL_INTERVAL_DAYS = 80     # 约一个季度触发一次校准
MIN_SAMPLES = 3            # 冷启动保护：样本不足保留默认 0.5


# ---------- 工具 ----------
def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d")


def ensure_dirs():
    os.makedirs(RUNS_DIR, exist_ok=True)


# ---------- ① 多期快照序列存储 ----------
def store_run(snapshot: dict) -> bool:
    """存本期快照到 runs/ 并更新最新指针；返回是否触发了校准。

    阶段4快照工作流（修复后语义）：
      本期的 judge_direction = 对「上一期」信号的真实裁判方向
        = 旭创/新易盛 利润增速方向（加速 +1 / 减速 -1 / 持平 0）
        = 主理人在本阶段查询数据源(万得/通达信/互联网)后传入
      数据源不可用时显式传 0 + verdict_source="unavailable"，
      该校准配对将被诚实跳过（不假装校准）。
    """
    ensure_dirs()
    run_date = snapshot.get("run_date")
    if not run_date:
        print("错误: 快照缺 run_date")
        sys.exit(1)
    # 补全自进化所需字段
    if "signal_signs" not in snapshot:
        snapshot["signal_signs"] = {}
    jd = snapshot.get("judge_direction", 0)
    if "verdict_source" not in snapshot:
        snapshot["verdict_source"] = ("unknown" if jd != 0 else "n/a")
    if jd == 0:
        print(f"[store] ⚠ judge_direction=0 (verdict_source={snapshot['verdict_source']})"
              f" → 本期未携带「对上一期裁判」，校准回看将跳过涉及本期的配对")
    with open(os.path.join(RUNS_DIR, f"{run_date}_snapshot.json"), "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    with open(LATEST, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"[store] 已存 {run_date} 至 runs/ 并更新基线指针 (累计期数={get_run_count()})")
    return maybe_calibrate(run_date_str=run_date)


def backfill_verdict(run_date_str: str, judge_direction: int,
                     verdict_source: str = "manual") -> bool:
    """回填历史快照的 judge_direction（真实裁判方向）。

    用于：数据源晚到 / 此前某期 verdict 标记为 unavailable，
    现已能取得「对上一期」的真实方向时，补填使校准回看能覆盖该期。
    例：python self_evolve.py --backfill 2026-07-14 --judge-direction 1 --verdict-source "万得:旭创Q2利润加速"
    """
    ensure_dirs()
    path = os.path.join(RUNS_DIR, f"{run_date_str}_snapshot.json")
    if not os.path.isfile(path):
        print(f"错误: 找不到快照 {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        snap = json.load(f)
    snap["judge_direction"] = int(judge_direction)
    snap["verdict_source"] = verdict_source
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    # 若恰为最新指针，同步更新
    if os.path.isfile(LATEST):
        with open(LATEST, encoding="utf-8") as f:
            latest = json.load(f)
        if latest.get("run_date") == run_date_str:
            with open(LATEST, "w", encoding="utf-8") as f:
                json.dump(snap, f, ensure_ascii=False, indent=2)
    print(f"[backfill] {run_date_str} 的 judge_direction 已设为 {judge_direction}"
          f" (verdict_source={verdict_source})")
    return True


# ---------- ② R：累计期数 ----------
def get_run_count() -> int:
    if not os.path.isdir(RUNS_DIR):
        return 0
    return len([f for f in os.listdir(RUNS_DIR) if f.endswith("_snapshot.json")])


# ---------- ③ 命中率回看 ----------
def load_history():
    if not os.path.isdir(RUNS_DIR):
        return []
    hist = []
    for fn in [f for f in os.listdir(RUNS_DIR) if f.endswith("_snapshot.json")]:
        with open(os.path.join(RUNS_DIR, fn), encoding="utf-8") as f:
            hist.append(json.load(f))
    hist.sort(key=lambda s: s.get("run_date", ""))
    return hist


def compute_hit_rates(history=None):
    """信号 effective_sign(t) vs 下期统一裁判方向 judge_direction(t+1)。"""
    if history is None:
        history = load_history()
    stat = {}
    for i in range(len(history) - 1):
        t, t1 = history[i], history[i + 1]
        jd = t1.get("judge_direction", 0)
        if jd == 0:
            continue  # 持平无法判定
        for name, sign in t.get("signal_signs", {}).items():
            if sign == 0:
                continue
            st = stat.setdefault(name, {"hit": 0, "miss": 0})
            if sign == jd:
                st["hit"] += 1
            else:
                st["miss"] += 1
    out = {}
    for name, s in stat.items():
        tot = s["hit"] + s["miss"]
        if tot > 0:
            out[name] = {"hit_rate": round(s["hit"] / tot, 3), "samples": tot}
    return out


def load_calib():
    if os.path.isfile(CALIB):
        with open(CALIB, encoding="utf-8") as f:
            return json.load(f)
    return {"last_calibrated": None, "next_calibration": None,
            "signals": {}, "note": "未校准，权重第三轴用默认0.5"}


def get_hit_rate(signal, calib=None):
    """给权仲校读取：样本足则返回真实命中率，否则默认 0.5（冷启动保护）。"""
    if calib is None:
        calib = load_calib()
    rec = calib.get("signals", {}).get(signal)
    if rec and rec.get("samples", 0) >= MIN_SAMPLES:
        return rec["hit_rate"]
    return 0.5


# ---------- 校准编排 ----------
def maybe_calibrate(run_date_str=None, force=False):
    history = load_history()
    if len(history) < 2:
        print("[calibrate] 历史不足2期,跳过")
        return False
    calib = load_calib()
    today = parse_date(run_date_str) if run_date_str else datetime.now()
    last = calib.get("last_calibrated")
    due = (force or last is None or
           (today - parse_date(last)).days >= CAL_INTERVAL_DAYS)
    if not due:
        print(f"[calibrate] 未到期(上次{last}, 下次{calib.get('next_calibration')})")
        return False

    hit = compute_hit_rates(history)
    calibrated_signals = {k: v for k, v in hit.items() if v["samples"] >= MIN_SAMPLES}
    if not calibrated_signals:
        print("[calibrate] 无有效命中率样本(配对为空或所有样本<3), "
              "跳过写回, 不锁定校准窗口(保持开放待后续期次累积)")
        return False
    calib["last_calibrated"] = today.strftime("%Y-%m-%d")
    calib["next_calibration"] = (today + timedelta(days=CAL_INTERVAL_DAYS)).strftime("%Y-%m-%d")
    calib["signals"] = calibrated_signals
    calib["note"] = (f"季度末自校准({today.strftime('%Y-%m-%d')}): 命中率回看覆盖"
                     f"{len(calib['signals'])}个信号(样本≥{MIN_SAMPLES}); "
                     f"裁判=下期旭创/新易盛利润增速方向")
    with open(CALIB, "w", encoding="utf-8") as f:
        json.dump(calib, f, ensure_ascii=False, indent=2)
    print(f"[calibrate] ✅ 已校准: {len(calib['signals'])}信号命中率写回, "
          f"下次校准 {calib['next_calibration']}")
    return True


def status():
    calib = load_calib()
    print(f"累计期数(R): {get_run_count()}")
    print(f"上次校准: {calib.get('last_calibrated')} | 下次校准: {calib.get('next_calibration')}")
    print(f"已校准信号数: {len(calib.get('signals', {}))}")
    hr = compute_hit_rates()
    print(f"当前命中率(样本≥1): {json.dumps(hr, ensure_ascii=False)}")


def self_test():
    import tempfile
    global RUNS_DIR, LATEST, CALIB
    tmp = tempfile.mkdtemp(prefix="self_evolve_test_")
    RUNS_DIR = os.path.join(tmp, "runs")
    LATEST = os.path.join(tmp, "last_run_snapshot.json")
    CALIB = os.path.join(tmp, "calibration.json")
    ensure_dirs()
    # 模拟：10 期，信号方向总体与下期利润增速方向一致（90% 命中）
    base_signs = {"云厂Capex": 1, "GPU出货": 1, "EML缺口": 1, "光芯片价格": 1, "CPO时间表": -1}
    dates = [f"2026-{m:02d}-{d:02d}" for m, d in
             [(1, 5), (1, 26), (2, 16), (3, 9), (3, 30), (4, 20),
              (5, 11), (6, 1), (6, 22), (7, 13)]]
    import random
    random.seed(7)
    for i, dt in enumerate(dates):
        jd = 1 if random.random() > 0.1 else -1     # 下期利润增速方向
        signs = dict(base_signs)
        if jd == -1 and random.random() < 0.2:       # 10% 噪音：个别信号反向
            signs["光芯片价格"] = -1
        snap = {
            "run_date": dt,
            "mode": "专业",
            "signal_signs": signs,
            "judge_direction": jd,
            "景气度": {"net": 1.0 * jd, "direction": "扩张" if jd > 0 else "收缩"},
            "置信度": {"raw": 0.4, "label": "中"},
        }
        store_run(snap)
    print("\n=== 模拟10期后 ===")
    hr = compute_hit_rates(load_history())
    print(json.dumps(hr, ensure_ascii=False, indent=2))
    maybe_calibrate(run_date_str=dates[-1], force=True)
    print(json.dumps(load_calib(), ensure_ascii=False, indent=2))
    print(f"\n[test] 隔离目录: {tmp}")


def main():
    ap = argparse.ArgumentParser(description="光模块信号监控 · 自进化引擎")
    ap.add_argument("--store", help="存本期快照(json)并触发校准检查")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--hitrates", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--force-calibrate", action="store_true")
    ap.add_argument("--backfill", help="回填历史快照的 judge_direction, 值为 run_date(YYYY-MM-DD)")
    ap.add_argument("--judge-direction", type=int, choices=[-1, 0, 1],
                    help="配合 --backfill: 真实裁判方向 +1/-1/0")
    ap.add_argument("--verdict-source", default="manual",
                    help="配合 --backfill: 裁判方向来源说明(数据源/人工)")
    args = ap.parse_args()

    if args.self_test:
        self_test()
    elif args.backfill:
        if args.judge_direction is None:
            print("错误: --backfill 必须配合 --judge-direction")
            sys.exit(1)
        backfill_verdict(args.backfill, args.judge_direction, args.verdict_source)
    elif args.store:
        with open(args.store, encoding="utf-8") as f:
            snap = json.load(f)
        store_run(snap)
        if args.force_calibrate:
            maybe_calibrate(force=True)
    elif args.status:
        status()
    elif args.hitrates:
        print(json.dumps(compute_hit_rates(), ensure_ascii=False, indent=2))
    else:
        print("用法: --store <快照> | --status | --hitrates | --self-test")


if __name__ == "__main__":
    main()
