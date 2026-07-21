#!/usr/bin/env python3
"""
负债优先级排序（Debt Priority Sorter）

把多笔负债按"应该先还哪个"排序——遵循"利率高的先还"（雪崩法），
并对比"先还小金额"（雪球法）的心理优势。

用法（每笔债务用 名称:金额:年化:最低月供 表示，多笔用空格分隔）:
    python debt_priority.py --debts "信用卡分期:30000:0.18:1500" "网贷:50000:0.24:2500" "车贷:80000:0.045:2000" --extra_monthly 2000
"""
from __future__ import annotations
import argparse
from typing import List
import sys as _sys
if _sys.platform == "win32":
    try:
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def fmt(n: float) -> str:
    return f"{n:,.0f}"


def parse_debt(s: str):
    parts = s.split(":")
    if len(parts) != 4:
        raise ValueError(f"格式错误：{s} 应为 名称:金额:年化:最低月供")
    return {
        "name": parts[0],
        "amount": float(parts[1]),
        "rate": float(parts[2]),
        "min_pay": float(parts[3]),
    }


def simulate(debts: List[dict], extra_monthly: float, strategy: str):
    """模拟还债过程，返回总月数和总利息"""
    debts = [d.copy() for d in debts]
    months = 0
    total_interest = 0
    while any(d["amount"] > 0 for d in debts):
        months += 1
        if months > 600:
            break
        # 计算每月利息
        for d in debts:
            if d["amount"] > 0:
                interest = d["amount"] * d["rate"] / 12
                total_interest += interest
                d["amount"] += interest

        # 先所有最低还款
        budget = extra_monthly
        for d in debts:
            if d["amount"] > 0:
                pay = min(d["min_pay"], d["amount"])
                d["amount"] -= pay

        # 把额外预算砸到目标
        active = [d for d in debts if d["amount"] > 0]
        if not active:
            break
        if strategy == "avalanche":
            # 利率最高
            target = max(active, key=lambda x: x["rate"])
        else:
            # 金额最小
            target = min(active, key=lambda x: x["amount"])
        pay = min(budget, target["amount"])
        target["amount"] -= pay

    return months, total_interest


def main():
    parser = argparse.ArgumentParser(description="负债优先级排序")
    parser.add_argument("--debts", nargs="+", required=True,
                        help="每笔债务格式：名称:金额:年化(0.18):最低月供")
    parser.add_argument("--extra_monthly", type=float, default=0,
                        help="除最低还款外，每月你还能多还多少（元）")
    args = parser.parse_args()

    try:
        debts = [parse_debt(d) for d in args.debts]
    except ValueError as e:
        print(f"❌ {e}")
        return

    print("\n" + "=" * 70)
    print("       负债优先级排序 · 小白理财教练")
    print("=" * 70)

    total_amount = sum(d["amount"] for d in debts)
    total_min = sum(d["min_pay"] for d in debts)
    weighted_rate = sum(d["amount"] * d["rate"] for d in debts) / total_amount

    print(f"\n💼 你的负债概况：")
    print(f"   债务笔数：{len(debts)} 笔")
    print(f"   总负债：  {fmt(total_amount)} 元")
    print(f"   每月最低还款：{fmt(total_min)} 元")
    print(f"   每月额外可投入：{fmt(args.extra_monthly)} 元")
    print(f"   加权平均年化：{weighted_rate*100:.2f}%")

    # 红线告警
    print(f"\n🚨 红线检查：")
    if weighted_rate >= 0.15:
        print(f"   ⚠️  你的平均债务利率 {weighted_rate*100:.0f}% ≥ 15%，")
        print(f"       这意味着任何投资收益都难以跑赢——必须优先全力还债。")
        print(f"       【铁律】这种情况下，停止一切投资（除应急金）。")
    elif weighted_rate >= 0.08:
        print(f"   ⚠️  平均利率 {weighted_rate*100:.0f}% 偏高，建议先还债再投资。")
    else:
        print(f"   ✅ 平均利率 {weighted_rate*100:.0f}% 较低（如房贷），可同步进行投资。")

    # 排序
    print("\n" + "=" * 70)
    print("📋 推荐还款顺序（雪崩法 = 先还利率最高的，省钱最多）")
    print("=" * 70)
    sorted_debts = sorted(debts, key=lambda x: x["rate"], reverse=True)
    print(f"   {'优先级':<6}{'名称':<15}{'余额':>12}{'年化':>10}{'最低月供':>12}{'建议':<20}")
    for i, d in enumerate(sorted_debts, 1):
        if d["rate"] >= 0.15:
            comment = "🔴 高息，立刻全力还"
        elif d["rate"] >= 0.08:
            comment = "🟡 中息，加速还"
        elif d["rate"] >= 0.04:
            comment = "🟢 低息，按计划还"
        else:
            comment = "⚪ 极低息，保留"
        print(f"   {i:<6}{d['name']:<15}{fmt(d['amount']):>12}{d['rate']*100:>9.2f}%"
              f"{fmt(d['min_pay']):>12}  {comment}")

    # 模拟两种策略
    if args.extra_monthly > 0 and total_amount > 0:
        m1, i1 = simulate(debts, args.extra_monthly, "avalanche")
        m2, i2 = simulate(debts, args.extra_monthly, "snowball")

        print("\n" + "=" * 70)
        print("📊 两种策略对比")
        print("=" * 70)
        print(f"\n   方案 A · 雪崩法（先还利率最高的，理性最优）：")
        print(f"      共需 {m1} 个月（约 {m1/12:.1f} 年）还清")
        print(f"      总利息支出：{fmt(i1)} 元")

        print(f"\n   方案 B · 雪球法（先还金额最小的，心理鼓励）：")
        print(f"      共需 {m2} 个月（约 {m2/12:.1f} 年）还清")
        print(f"      总利息支出：{fmt(i2)} 元")

        if i1 < i2:
            print(f"\n   💡 雪崩法可省 {fmt(i2-i1)} 元利息，省 {m2-m1} 个月。")
        elif i2 < i1:
            print(f"\n   💡 雪球法在你这种债务结构下更省（罕见情况）。")
        else:
            print(f"\n   💡 两种方案差不多。")

    print("\n🎯 接下来 3 件事：")
    print("   1. 把所有信用卡分期能提前结清的全部结清（即便有手续费）")
    print("   2. 联系网贷/消费贷平台，问能否降息或一次性结清减免")
    print("   3. 还债期间停止所有非必要投资，应急金保留 1-2 个月即可")

    print("\n⚠️  绝对不要做：")
    print("   • 用网贷还信用卡（利率更高）")
    print("   • 借钱投资期望『赚回来』（这是赌博，不是投资）")
    print("   • 还款焦虑下做『高收益翻本』决策（往往进诈骗陷阱）\n")


if __name__ == "__main__":
    main()
