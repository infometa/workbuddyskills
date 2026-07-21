#!/usr/bin/env python3
"""
退休金缺口测算（Retirement Gap Calculator）

帮助小白搞清"我现在这点钱，退休真的够花吗？"

用法:
    python retirement_gap.py --age 30 --retire_age 60 --life_expect 85 \
        --current_savings 50000 --monthly_save 3000 \
        --monthly_expense_today 8000 --inflation 0.03 --return_pre 0.07 --return_post 0.04
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


def fmt(n: float) -> str:
    if abs(n) >= 1_0000_0000:
        return f"{n/1_0000_0000:.2f} 亿"
    if abs(n) >= 1_0000:
        return f"{n/1_0000:.1f} 万"
    return f"{n:,.0f}"


def main():
    parser = argparse.ArgumentParser(description="退休金缺口测算")
    parser.add_argument("--age", type=int, required=True, help="当前年龄")
    parser.add_argument("--retire_age", type=int, default=60, help="计划退休年龄")
    parser.add_argument("--life_expect", type=int, default=85, help="预期寿命")
    parser.add_argument("--current_savings", type=float, default=0, help="当前可投资资产（元）")
    parser.add_argument("--monthly_save", type=float, default=0, help="每月新增储蓄（元）")
    parser.add_argument("--monthly_expense_today", type=float, default=8000,
                        help="按今天物价水平，退休后月开支多少（元）")
    parser.add_argument("--inflation", type=float, default=0.03, help="通胀率（默认3%%）")
    parser.add_argument("--return_pre", type=float, default=0.07,
                        help="退休前年化收益（默认7%%）")
    parser.add_argument("--return_post", type=float, default=0.04,
                        help="退休后年化收益（默认4%%，因配置更稳健）")
    parser.add_argument("--social_pension", type=float, default=0,
                        help="预估退休后每月社保养老金（按今天购买力，元）")
    args = parser.parse_args()

    work_years = args.retire_age - args.age
    retire_years = args.life_expect - args.retire_age

    if work_years <= 0:
        print("❌ 退休年龄必须大于当前年龄")
        return
    if retire_years <= 0:
        print("❌ 预期寿命必须大于退休年龄")
        return

    print("\n" + "=" * 70)
    print("       退休金缺口测算 · 小白理财教练")
    print("=" * 70)
    print(f"\n📋 你的参数：")
    print(f"   当前年龄：{args.age} 岁，计划退休：{args.retire_age} 岁，预期寿命：{args.life_expect} 岁")
    print(f"   还要工作：{work_years} 年，退休后预期生活：{retire_years} 年")
    print(f"   今天可投资产：{fmt(args.current_savings)} 元")
    print(f"   每月新增储蓄：{fmt(args.monthly_save)} 元")
    print(f"   按今天物价水平退休月开支：{fmt(args.monthly_expense_today)} 元")
    print(f"   通胀假设：{args.inflation*100:.1f}%/年")
    print(f"   退休前后年化收益假设：{args.return_pre*100:.1f}% / {args.return_post*100:.1f}%")
    if args.social_pension > 0:
        print(f"   预估社保养老金（今日购买力）：{fmt(args.social_pension)} 元/月")

    # 1) 计算退休时的月开支（考虑通胀）
    future_monthly_expense = args.monthly_expense_today * (1 + args.inflation) ** work_years
    future_social_pension = args.social_pension * (1 + args.inflation) ** work_years
    net_future_expense = future_monthly_expense - future_social_pension

    # 2) 计算退休时需要的总金额
    # 假设退休后投资仍能跑赢通胀一点 (return_post > inflation)
    # 用真实收益率折现
    real_rate_post = (1 + args.return_post) / (1 + args.inflation) - 1
    if abs(real_rate_post) < 0.0001:
        # 近似：纯按通胀走，需要总额 = 月开支 × 12 × 退休年数
        needed_at_retirement = net_future_expense * 12 * retire_years
    else:
        # 年金现值公式（按真实利率折现）：
        # PV = C * [1 - (1+r)^-n] / r
        annual_expense = net_future_expense * 12
        n = retire_years
        r = real_rate_post
        needed_at_retirement = annual_expense * (1 - (1 + r) ** (-n)) / r

    # 3) 计算到退休时已经能积累多少钱
    # 现有资产复利 + 每月定投终值
    fv_current = args.current_savings * (1 + args.return_pre) ** work_years
    monthly_rate = (1 + args.return_pre) ** (1/12) - 1
    months = work_years * 12
    if monthly_rate > 0:
        fv_savings = args.monthly_save * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    else:
        fv_savings = args.monthly_save * months
    fv_total = fv_current + fv_savings

    gap = needed_at_retirement - fv_total

    # 4) 输出
    print("\n" + "=" * 70)
    print("📊 测算结果")
    print("=" * 70)
    print(f"\n💰 退休时（{args.retire_age}岁）应该有多少钱：")
    print(f"   退休时月开支（含通胀）：    {fmt(future_monthly_expense)} 元/月")
    if args.social_pension > 0:
        print(f"   预计社保养老金（含通胀）：  {fmt(future_social_pension)} 元/月")
        print(f"   需自筹覆盖：                {fmt(net_future_expense)} 元/月")
    print(f"   退休时需准备的总金额：      🎯 {fmt(needed_at_retirement)} 元")

    print(f"\n💪 你能积累到多少：")
    print(f"   当前 {fmt(args.current_savings)} 复利{work_years}年（{args.return_pre*100:.0f}%）：  {fmt(fv_current)} 元")
    print(f"   每月{fmt(args.monthly_save)}定投{work_years}年终值：     {fmt(fv_savings)} 元")
    print(f"   你的退休账户预计：          📈 {fmt(fv_total)} 元")

    print(f"\n📐 缺口分析：")
    if gap <= 0:
        print(f"   ✅ 你将盈余 {fmt(-gap)} 元，远超退休所需！")
        print(f"   建议：")
        print(f"   • 不必再加大储蓄，可以适度提升生活品质")
        print(f"   • 或考虑提前退休（FIRE 路线），用 retire_age 调小再算一次")
    else:
        print(f"   🚨 缺口 {fmt(gap)} 元")
        # 计算需要每月多存多少
        if monthly_rate > 0:
            extra_monthly = gap / (((1 + monthly_rate) ** months - 1) / monthly_rate)
        else:
            extra_monthly = gap / months
        print(f"\n   要补上这个缺口，有 4 条路：")
        print(f"   1. 每月再多存 {fmt(extra_monthly)} 元（共 {fmt(args.monthly_save + extra_monthly)} 元/月）")
        # 提高收益
        # 找到使 fv = needed 的 return_pre
        target_fv = needed_at_retirement
        lo, hi = 0.0, 0.20
        for _ in range(60):
            mid = (lo + hi) / 2
            fv1 = args.current_savings * (1 + mid) ** work_years
            mr = (1 + mid) ** (1/12) - 1
            fv2 = args.monthly_save * (((1 + mr) ** months - 1) / mr) if mr > 0 else args.monthly_save * months
            if fv1 + fv2 < target_fv:
                lo = mid
            else:
                hi = mid
        print(f"   2. 提高年化到 {hi*100:.1f}%（当前假设 {args.return_pre*100:.0f}%）—— 需要更激进的配置")
        print(f"      但记住：高收益伴随高波动，**不建议为了缺口去博**")
        # 推迟退休
        print(f"   3. 推迟 3-5 年退休（继续工作 + 复利时间变长）")
        print(f"   4. 降低退休生活标准（把月开支从 {fmt(args.monthly_expense_today)} 调到 "
              f"{fmt(args.monthly_expense_today * 0.8)} ）")
        print(f"\n   💡 现实建议：组合使用上面 4 条，不要把希望全压在某一条上。")

    # 通胀冲击警示
    print(f"\n⚠️  通胀的可怕：")
    print(f"   今天 {fmt(args.monthly_expense_today)} 元/月的生活，")
    print(f"   {work_years} 年后需要 {fmt(future_monthly_expense)} 元/月才能买到一样的东西")
    factor = future_monthly_expense / args.monthly_expense_today
    print(f"   购买力的『重量』放大了 {factor:.2f} 倍")

    print(f"\n🎯 行动清单：")
    print(f"   1. 把退休金账户和日常账户**物理隔离**（独立的基金账户）")
    print(f"   2. 选择『宽基指数 + 债券』的简单配置，不去追风口")
    print(f"   3. 每年检查一次缺口，参数有变化就重算")
    print(f"   4. 别忘了『个人养老金账户』——每年 1.2 万额度，可抵税\n")


if __name__ == "__main__":
    main()
