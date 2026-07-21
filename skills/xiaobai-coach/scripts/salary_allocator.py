#!/usr/bin/env python3
"""
工资分配器（Salary Allocator）

把月薪按"理财四步走"的优先级，自动分配到各个账户。

用法:
    python salary_allocator.py --salary 15000 --rent 3500 --has_debt 1 --debt 50000 --debt_rate 0.18 --emergency_now 0 --emergency_target 60000
    python salary_allocator.py --salary 8000 --rent 1500 --has_debt 0 --emergency_now 30000 --emergency_target 30000
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
    return f"{n:,.0f}"


def main():
    parser = argparse.ArgumentParser(description="工资分配建议工具")
    parser.add_argument("--salary", type=float, required=True, help="税后月薪（元）")
    parser.add_argument("--rent", type=float, default=0, help="月房租/月供（元）")
    parser.add_argument("--living", type=float, default=0,
                        help="基本生活开支（吃饭/通勤/水电网）。不填则按 35%% 工资估算")
    parser.add_argument("--has_debt", type=int, default=0, help="是否有高息债务 1=是 0=否")
    parser.add_argument("--debt", type=float, default=0, help="高息负债总额")
    parser.add_argument("--debt_rate", type=float, default=0.18, help="高息债务年化")
    parser.add_argument("--emergency_now", type=float, default=0, help="目前应急金（元）")
    parser.add_argument("--emergency_target", type=float, default=0,
                        help="应急金目标（不填则按月开支 6 倍）")
    parser.add_argument("--has_insurance", type=int, default=0, help="基础保险是否齐全 1=是 0=否")
    args = parser.parse_args()

    salary = args.salary
    rent = args.rent
    living = args.living if args.living > 0 else salary * 0.35
    fixed = rent + living
    disposable = salary - fixed
    monthly_expense = fixed  # 大致月支出

    if args.emergency_target <= 0:
        args.emergency_target = monthly_expense * 6

    print("\n" + "=" * 60)
    print("       小白理财教练 · 工资分配建议")
    print("=" * 60)
    print(f"\n📋 输入信息：")
    print(f"   税后月薪：       {fmt(salary)} 元")
    print(f"   房租/房贷：      {fmt(rent)} 元")
    print(f"   基本生活开支：   {fmt(living)} 元")
    print(f"   每月可支配：     {fmt(disposable)} 元 ({disposable/salary*100:.0f}%)")

    if disposable <= 0:
        print("\n⚠️  你的可支配收入 ≤ 0，先想办法增加收入或降低开支")
        print("   建议：")
        print("   • 评估房租是否过高（建议 ≤ 工资 30%）")
        print("   • 列出所有月度账单，砍掉一个不必要订阅")
        return

    # 按"理财四步走"优先级分配
    print("\n" + "=" * 60)
    print("🪜  按【理财四步走】优先级分配")
    print("=" * 60)

    remaining = disposable
    allocations = []

    # 第 1 步：还高息债
    debt_amount = 0
    if args.has_debt and args.debt > 0:
        # 把可支配的 50% 用于还债（最低）
        debt_amount = min(remaining, max(remaining * 0.5, 1000))
        if args.debt_rate >= 0.10:
            debt_amount = remaining * 0.6
        debt_amount = min(debt_amount, remaining)
        allocations.append(("【第1步】还高息债务", debt_amount,
                            f"年化{args.debt_rate*100:.0f}%相当于'无风险投资'，必须先还"))
        remaining -= debt_amount

    # 第 2 步：应急金
    emergency_gap = max(args.emergency_target - args.emergency_now, 0)
    emergency_amount = 0
    if remaining > 0 and emergency_gap > 0:
        # 没债优先攒应急金
        if debt_amount == 0:
            emergency_amount = min(remaining, max(remaining * 0.5, 1500))
        else:
            emergency_amount = min(remaining, remaining * 0.4)
        emergency_amount = min(emergency_amount, emergency_gap)
        if emergency_amount > 0:
            months_to_target = emergency_gap / emergency_amount if emergency_amount > 0 else 0
            allocations.append(("【第2步】应急金（货币基金）", emergency_amount,
                                f"距目标{fmt(emergency_gap)}元，按此速度{months_to_target:.1f}个月攒满"))
            remaining -= emergency_amount

    # 第 3 步：保险
    insurance_amount = 0
    if remaining > 0 and not args.has_insurance:
        # 保险年支出 < 收入 10%
        annual_premium = min(salary * 12 * 0.05, 6000)  # 年保费目标
        insurance_amount = min(remaining * 0.1, annual_premium / 12)
        if insurance_amount > 100:
            allocations.append(("【第3步】保险（折算到月）", insurance_amount,
                                f"百万医疗+重疾+定寿+意外，年保费目标 {fmt(annual_premium)} 元"))
            remaining -= insurance_amount

    # 第 4 步：投资 + 享受生活
    if remaining > 0:
        invest_amount = remaining * 0.7
        enjoy_amount = remaining * 0.3
        allocations.append(("【第4步】指数基金定投", invest_amount,
                            "建议 70% 沪深300 + 30% 标普500（QDII），月度自动扣款"))
        allocations.append(("享受生活（旅游/兴趣/送礼）", enjoy_amount,
                            "理财不是苦行——给现在的自己留 30% 的快乐"))

    # 输出分配
    print()
    for i, (label, amount, comment) in enumerate(allocations, 1):
        pct = amount / salary * 100
        bar = "█" * int(pct // 2)
        print(f"  {label}")
        print(f"    {fmt(amount):>8} 元 ({pct:.1f}%)  {bar}")
        print(f"    💬 {comment}\n")

    # 完整收支表
    print("=" * 60)
    print("📊 完整月度收支表")
    print("=" * 60)
    print(f"  收入：                  {fmt(salary):>10} 元")
    print(f"  房租/房贷：            -{fmt(rent):>10} 元")
    print(f"  基本生活：             -{fmt(living):>10} 元")
    for label, amount, _ in allocations:
        print(f"  {label[:20]:<20s} -{fmt(amount):>10} 元")
    final_balance = salary - fixed - sum(a for _, a, _ in allocations)
    if abs(final_balance) > 1:
        print(f"  {'结余/缺口':<20s}  {fmt(final_balance):>10} 元")

    # 行动建议
    print("\n🎯 本周可以做的 3 件事：")
    if args.has_debt and args.debt > 0:
        print("   1. 列出所有负债（金额/利率/还款日），用 Excel 排序")
        print("   2. 设置每月工资到账后自动扣款还高息部分")
        print("   3. 同时申请把信用卡分期手续费协商减免（很多银行可申诉）")
    elif emergency_gap > 0:
        print("   1. 在工行/招行 App 设置『工资到账自动转入货币基金』")
        print("   2. 把应急金账户和日常消费卡分开，避免被『顺手花掉』")
        print("   3. 在日历上标记下次工资日，按本表执行第一次完整分配")
    elif not args.has_insurance:
        print("   1. 用『小雨伞』『慧择』『蚂蚁保』对比百万医疗（300-1000元/年）")
        print("   2. 30 岁前买重疾险——越年轻保费越便宜")
        print("   3. 意外险（一年100元起）今晚就能买，立刻生效")
    else:
        print("   1. 在支付宝/天天基金搜索沪深300ETF联接（C类），开启月度定投")
        print("   2. 设置每月发薪日次日自动扣款")
        print("   3. 把'享受生活'那部分转入一个独立账户，落实下个月的小确幸")

    print("\n⚠️  提醒：")
    print("   • 本分配是参考骨架，不是个性化投顾建议")
    print("   • 收入或家庭状况变化时，重新跑一次")
    print("   • 投资部分不要碰你 3 年内要用的钱\n")


if __name__ == "__main__":
    main()
