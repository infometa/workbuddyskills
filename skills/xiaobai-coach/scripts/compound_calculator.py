#!/usr/bin/env python3
"""
复利计算器（Compound Calculator）

帮助小白直观看到"复利+时间"的威力。

用法示例:
    python compound_calculator.py --principal 0 --monthly 2000 --years 20 --rate 0.07
    python compound_calculator.py --principal 100000 --monthly 0 --years 10 --rate 0.06

参数:
    --principal  起始本金（元）
    --monthly    每月新增投入（元）
    --years      投资年限（年）
    --rate       预期年化收益率（小数形式，0.07 表示 7%）
    --inflation  通胀率（默认 0.025），用于计算购买力
"""
from __future__ import annotations
import argparse
import sys as _sys
if _sys.platform == "win32":
    try:
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def simulate(principal: float, monthly: float, years: int, annual_rate: float, inflation: float = 0.025):
    """逐月复利模拟，返回逐年明细。"""
    monthly_rate = annual_rate / 12
    balance = principal
    rows = []
    total_invested = principal

    for year in range(1, years + 1):
        for _ in range(12):
            balance = balance * (1 + monthly_rate) + monthly
            total_invested += monthly
        # 计算实际购买力
        real_value = balance / ((1 + inflation) ** year)
        rows.append({
            "year": year,
            "balance": balance,
            "invested": total_invested,
            "earned": balance - total_invested,
            "real_value": real_value,
        })
    return rows


def fmt(n: float) -> str:
    if abs(n) >= 1_0000_0000:
        return f"{n/1_0000_0000:.2f} 亿"
    if abs(n) >= 1_0000:
        return f"{n/1_0000:.2f} 万"
    return f"{n:,.0f}"


def print_table(rows, annual_rate: float, inflation: float):
    print("\n" + "=" * 78)
    print(f"  复利计算结果（年化 {annual_rate*100:.1f}%，通胀假设 {inflation*100:.1f}%）")
    print("=" * 78)
    header = f"{'年份':>4}  {'账户余额':>14}  {'累计投入':>14}  {'复利贡献':>14}  {'今日购买力':>14}"
    print(header)
    print("-" * 78)
    show_years = sorted(set([1, 3, 5, 10, 15, 20, 25, 30, rows[-1]["year"]]))
    for r in rows:
        if r["year"] in show_years:
            print(f"{r['year']:>4}  {fmt(r['balance']):>14}  {fmt(r['invested']):>14}  "
                  f"{fmt(r['earned']):>14}  {fmt(r['real_value']):>14}")
    print("=" * 78)


def insights(rows, annual_rate: float):
    final = rows[-1]
    earned_pct = (final["earned"] / final["invested"]) * 100 if final["invested"] else 0
    years = final["year"]
    print("\n📊 大白话解读：")
    print(f"  • {years} 年后，你的账户会变成 {fmt(final['balance'])} 元")
    print(f"  • 其中 {fmt(final['invested'])} 是你自己存的本金")
    print(f"  • 另外 {fmt(final['earned'])} 是复利长出来的（相当于本金的 {earned_pct:.0f}%）")
    print(f"  • 考虑通胀后，相当于今天的 {fmt(final['real_value'])} 购买力")

    # 72 法则
    if annual_rate > 0:
        double_years = 72 / (annual_rate * 100)
        print(f"  • 按 72 法则，{annual_rate*100:.1f}% 年化下本金翻倍约需 {double_years:.1f} 年")

    print("\n💡 启示：")
    print("  1) 时间 > 金额。同样存 30 年，前 10 年和后 10 年的『复利产出』差距悬殊。")
    print("  2) 7% 年化是历史上宽基指数基金的合理预期，**不是承诺**。")
    print("  3) 真实路径会有大幅波动，请用 dca_simulator.py 看波动版的模拟。")
    print("  4) 假设里没有税费、申赎费——真实收益要再扣 0.5%-1%/年。\n")


def normalize_rate(value: float, name: str) -> float:
    """把"直觉输入"的收益率/通胀率纠正为小数形式。

    小白常把 7% 直接填成 7（而非 0.07）。这里做容错：
      - |value| > 1：判定为百分数误填，自动除以 100 并提示
      - 纠正后若仍 > 0.5（即 >50% 年化）：极可能不现实，给出风险警告但不强行阻断
    """
    corrected = value
    if abs(value) > 1:
        corrected = value / 100
        print(f"⚠️  检测到 {name}={value:g}，看起来像百分数。已自动按 {corrected*100:.2f}% 计算"
              f"（如果你确实想要 {value:g} 的小数收益率，请直接填 {value:g} 对应的百分比形式）。")
    if corrected > 0.5:
        print(f"⚠️  {name} 高达 {corrected*100:.1f}%／年，这在长期投资里几乎不可能持续。"
              f"宽基指数基金的历史合理预期约 6%-8%（即 0.06-0.08），请谨慎对待任何"
              f"承诺高息的产品——年化 > 10% 通常意味着高风险或骗局。")
    return corrected


def main():
    parser = argparse.ArgumentParser(description="复利计算器")
    parser.add_argument("--principal", type=float, default=0, help="起始本金（元）")
    parser.add_argument("--monthly", type=float, default=2000, help="每月投入（元）")
    parser.add_argument("--years", type=int, default=20, help="年限")
    parser.add_argument("--rate", type=float, default=0.07, help="年化收益率（如 0.07 表示 7%%；填 7 也会自动纠正）")
    parser.add_argument("--inflation", type=float, default=0.025, help="通胀率（默认 2.5%%）")
    args = parser.parse_args()

    if args.years <= 0:
        print("❌ 参数不合法：投资年限必须大于 0")
        return
    if args.rate < -1:
        print("❌ 参数不合法：年化收益率不能低于 -100%")
        return

    rate = normalize_rate(args.rate, "年化收益率")
    inflation = normalize_rate(args.inflation, "通胀率")

    rows = simulate(args.principal, args.monthly, args.years, rate, inflation)
    print_table(rows, rate, inflation)
    insights(rows, rate)


if __name__ == "__main__":
    main()
