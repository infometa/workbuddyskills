#!/usr/bin/env python3
"""
定投模拟器（DCA Simulator）

用蒙特卡洛方式模拟定投在带波动市场中的真实表现，
让小白看到"定投不只是数字增长"，而是要扛住中间的回撤。

用法:
    python dca_simulator.py --monthly 2000 --years 10 --annual_return 0.08 --volatility 0.20
    python dca_simulator.py --monthly 1500 --years 15 --annual_return 0.07 --volatility 0.18 --runs 1000

参数:
    --monthly         每月定投金额（元）
    --years           定投年数
    --annual_return   预期年化收益（小数，如 0.08）
    --volatility      年化波动率（小数，如 0.20 = 20%）
    --runs            模拟路径数（默认 500）
    --seed            随机种子（可复现）
"""
from __future__ import annotations
import argparse
import math
import random
import statistics
import sys as _sys
if _sys.platform == "win32":
    try:
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def fmt_w(n: float) -> str:
    if abs(n) >= 1_0000_0000:
        return f"{n/1_0000_0000:.2f}亿"
    if abs(n) >= 1_0000:
        return f"{n/1_0000:.1f}万"
    return f"{n:,.0f}"


def simulate_one_path(monthly: float, years: int, mu: float, sigma: float, rng: random.Random):
    """单路径月度模拟，使用对数正态收益。"""
    months = years * 12
    monthly_mu = (1 + mu) ** (1/12) - 1
    monthly_sigma = sigma / math.sqrt(12)

    balance = 0.0
    invested = 0.0
    peak = 0.0
    max_drawdown = 0.0
    history = []

    for m in range(1, months + 1):
        # 随机月收益（用正态近似）
        r = rng.gauss(monthly_mu, monthly_sigma)
        balance = balance * (1 + r) + monthly
        invested += monthly
        peak = max(peak, balance)
        if peak > 0:
            dd = (peak - balance) / peak
            max_drawdown = max(max_drawdown, dd)
        history.append(balance)

    return {
        "final": balance,
        "invested": invested,
        "earned": balance - invested,
        "max_drawdown": max_drawdown,
        "history": history,
    }


def percentile(data, p):
    """简易百分位"""
    if not data:
        return 0
    s = sorted(data)
    k = (len(s) - 1) * p
    f = math.floor(k); c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


def main():
    parser = argparse.ArgumentParser(description="定投蒙特卡洛模拟器")
    parser.add_argument("--monthly", type=float, default=2000)
    parser.add_argument("--years", type=int, default=10)
    parser.add_argument("--annual_return", type=float, default=0.08)
    parser.add_argument("--volatility", type=float, default=0.20)
    parser.add_argument("--runs", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    finals = []
    drawdowns = []
    paths = []

    for _ in range(args.runs):
        res = simulate_one_path(args.monthly, args.years, args.annual_return, args.volatility, rng)
        finals.append(res["final"])
        drawdowns.append(res["max_drawdown"])
        paths.append(res)

    invested = paths[0]["invested"]

    p10 = percentile(finals, 0.10)
    p50 = percentile(finals, 0.50)
    p90 = percentile(finals, 0.90)
    avg = statistics.mean(finals)
    avg_dd = statistics.mean(drawdowns) * 100
    worst_dd = max(drawdowns) * 100

    print("\n" + "=" * 70)
    print(f"  定投模拟（{args.runs} 条随机路径）")
    print(f"  每月 {fmt_w(args.monthly)}元 × {args.years}年，"
          f"假设年化 {args.annual_return*100:.1f}%，波动率 {args.volatility*100:.0f}%")
    print("=" * 70)
    print(f"\n累计本金投入：{fmt_w(invested)} 元")
    print(f"\n📊 {args.years} 年后账户最终金额（{args.runs} 条路径分布）：")
    print(f"   悲观情景（10% 分位）：{fmt_w(p10):>10}  → 收益 {fmt_w(p10-invested)} ({(p10-invested)/invested*100:+.0f}%)")
    print(f"   中位数（50% 分位）：  {fmt_w(p50):>10}  → 收益 {fmt_w(p50-invested)} ({(p50-invested)/invested*100:+.0f}%)")
    print(f"   乐观情景（90% 分位）：{fmt_w(p90):>10}  → 收益 {fmt_w(p90-invested)} ({(p90-invested)/invested*100:+.0f}%)")
    print(f"   均值：               {fmt_w(avg):>10}")

    print(f"\n📉 中途最大回撤分布：")
    print(f"   平均最大回撤：{avg_dd:.1f}%")
    print(f"   最糟糕一条路径回撤：{worst_dd:.1f}%")

    # 拿一条代表性路径展示
    sample = paths[len(paths)//2]
    print(f"\n📈 一条样本路径的几个时点（仅供感受波动）：")
    print(f"   {'年份':>4}  {'账户余额':>10}  {'累计投入':>10}")
    for y in [1, 3, 5, 10, 15, 20]:
        if y <= args.years:
            idx = y * 12 - 1
            invested_y = args.monthly * y * 12
            print(f"   {y:>4}  {fmt_w(sample['history'][idx]):>10}  {fmt_w(invested_y):>10}")

    print("\n💡 大白话解读：")
    print(f"  • 这是『假设市场年化 {args.annual_return*100:.0f}%、波动 {args.volatility*100:.0f}%』下的模拟，")
    print(f"    不是预测，更不是承诺。")
    print(f"  • 即使长期年化为正，**中途最深可能回撤 {worst_dd:.0f}%**——")
    print(f"    问自己：账户从 10 万跌到 {10 * (1-worst_dd/100):.1f} 万，你能不能不卖？")
    print(f"  • 悲观和乐观差距能达到 {(p90-p10)/p50*100:.0f}%。")
    print(f"    所以定投是'用纪律换概率'，不是'稳赚不赔'。")

    print("\n🎯 给你的行动建议：")
    print("   1. 把每月定投设为银行卡自动扣款，眼不见为净")
    print("   2. 跌的时候不要停！历史上停止定投的人收益最差")
    print("   3. 设好止盈线（如年化达到 15% 分批止盈）")
    print("   4. 用日历提醒自己：每年只复盘 2 次（年中、年底）")
    print()


if __name__ == "__main__":
    main()
