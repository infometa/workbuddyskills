#!/usr/bin/env python3
"""
基金/理财产品费率体检（Fee Checker）

帮小白快速判断一只基金或理财产品的费率水平是否合理。
长期看，费率每年差 1%，30 年下来收益差距能到 30%-40%！

用法:
    python fee_checker.py --type indexfund --mgmt 0.5 --custody 0.1 --sales_a 1.5 --redeem_lt7d 1.5 --redeem_7d_1y 0.5 --redeem_1y 0
    python fee_checker.py --type active --mgmt 1.5 --custody 0.25 --sales_a 1.5
    python fee_checker.py --type bank_wealth --mgmt 0.3 --sales_service 0.4 --custody 0.05
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


BENCHMARKS = {
    "indexfund": {  # 场外指数基金
        "name": "场外指数基金",
        "mgmt": (0.15, 0.5),       # 优秀-合理-偏贵
        "custody": (0.05, 0.1),
        "sales_a_excellent": 0.8,   # A类申购费打折后
        "sales_a_acceptable": 1.5,
    },
    "etf": {
        "name": "场内 ETF",
        "mgmt": (0.15, 0.5),
        "custody": (0.05, 0.1),
        "trade_commission": 0.005,   # 券商交易佣金 < 0.005% 优秀
    },
    "active": {
        "name": "主动权益基金",
        "mgmt": (1.0, 1.5),
        "custody": (0.2, 0.25),
        "sales_a_excellent": 0.8,
        "sales_a_acceptable": 1.5,
    },
    "bond": {
        "name": "债券基金",
        "mgmt": (0.3, 0.7),
        "custody": (0.1, 0.2),
    },
    "bank_wealth": {
        "name": "银行理财",
        "mgmt": (0.1, 0.3),
        "sales_service": (0.1, 0.4),
        "custody": (0.02, 0.1),
    },
    "qdii": {
        "name": "QDII / 海外基金",
        "mgmt": (0.6, 1.5),
        "custody": (0.15, 0.3),
    },
}


def grade(value, excellent, acceptable):
    """返回评级文字"""
    if value <= excellent:
        return "🟢 优秀"
    if value <= acceptable:
        return "🟡 合理"
    return "🔴 偏贵"


def main():
    parser = argparse.ArgumentParser(description="基金/理财费率体检")
    parser.add_argument("--type", required=True, choices=list(BENCHMARKS.keys()),
                        help="产品类型")
    parser.add_argument("--mgmt", type=float, default=0, help="管理费 (%%/年)")
    parser.add_argument("--custody", type=float, default=0, help="托管费 (%%/年)")
    parser.add_argument("--sales_service", type=float, default=0,
                        help="销售服务费 C类/银行理财 (%%/年)")
    parser.add_argument("--sales_a", type=float, default=0,
                        help="A类申购费打折后 (%%/笔)")
    parser.add_argument("--redeem_lt7d", type=float, default=1.5, help="7日内赎回费 (%%)")
    parser.add_argument("--redeem_7d_1y", type=float, default=0.5, help="7日-1年赎回费 (%%)")
    parser.add_argument("--redeem_1y", type=float, default=0, help="持有1年以上赎回费 (%%)")
    parser.add_argument("--years", type=int, default=10, help="假设持有年限")
    parser.add_argument("--principal", type=float, default=100000, help="假设本金（元）")
    args = parser.parse_args()

    bench = BENCHMARKS[args.type]
    print("\n" + "=" * 70)
    print(f"  费率体检 · {bench['name']}")
    print("=" * 70)

    # 年化费用
    annual_fee = args.mgmt + args.custody + args.sales_service
    print(f"\n📊 年化持有费用：{annual_fee:.3f}%")
    print(f"   = 管理费 {args.mgmt}% + 托管费 {args.custody}% + 销售服务费 {args.sales_service}%")

    # 单项评级
    print("\n📋 各项费用评级：")
    if "mgmt" in bench:
        e, a = bench["mgmt"]
        print(f"   管理费 {args.mgmt}%   {grade(args.mgmt, e, a)}   "
              f"（{bench['name']}基准：优秀<{e}%、合理<{a}%）")
    if "custody" in bench:
        e, a = bench["custody"]
        print(f"   托管费 {args.custody}%   {grade(args.custody, e, a)}   "
              f"（基准：优秀<{e}%、合理<{a}%）")
    if "sales_service" in bench and args.sales_service > 0:
        e, a = bench["sales_service"]
        print(f"   销售服务费 {args.sales_service}%   {grade(args.sales_service, e, a)}")
    if args.sales_a > 0 and "sales_a_excellent" in bench:
        e = bench["sales_a_excellent"]
        a = bench["sales_a_acceptable"]
        print(f"   A类申购费 {args.sales_a}%   {grade(args.sales_a, e, a)}   "
              f"（A类基准：< {e}% 优秀，< {a}% 合理；持有< 1年建议选 C 类）")

    # 赎回费提示
    if args.redeem_lt7d > 0 or args.redeem_7d_1y > 0:
        print("\n⚠️  赎回费阶梯：")
        print(f"   < 7天：    {args.redeem_lt7d}%   {'🚨 这是『惩罚费』用来防短线' if args.redeem_lt7d >= 1.5 else ''}")
        print(f"   7天-1年：  {args.redeem_7d_1y}%")
        print(f"   ≥ 1年：    {args.redeem_1y}%   {'🟢 持有满 1 年免赎回费' if args.redeem_1y == 0 else ''}")

    # 长期影响测算
    print("\n💸 费率对长期收益的『侵蚀』测算：")
    print(f"   假设本金 {args.principal:,.0f} 元，持有 {args.years} 年")
    print(f"   假设市场年化 8%（毛收益）")
    gross = args.principal * (1.08 ** args.years)
    net = args.principal * ((1.08 - annual_fee/100) ** args.years)
    eaten = gross - net
    print(f"   • 不收费的理想收益：    {gross:>12,.0f} 元")
    print(f"   • 扣完每年 {annual_fee:.2f}% 后：  {net:>12,.0f} 元")
    print(f"   • 被费率吃掉了：        {eaten:>12,.0f} 元 ({eaten/(gross-args.principal)*100:.1f}% 的潜在收益)")

    # 综合判断
    print("\n🎯 综合判断与建议：")
    if args.type in ("indexfund", "etf"):
        if annual_fee <= 0.25:
            print("   ✅ 费率水平很优秀，是同类中的『良心产品』。")
        elif annual_fee <= 0.6:
            print("   🟡 费率合理。同样的指数还有更便宜的，可以对比。")
        else:
            print("   🔴 费率偏贵。同样跟踪沪深300 / 标普500，市面有 < 0.2% 的产品，建议换。")
            print("      搜索关键词：'XX指数 ETF/联接 C类' 在天天基金/蛋卷按费率排序。")
    elif args.type == "active":
        if annual_fee <= 1.5:
            print("   🟡 主动基金的费率天花板。能否值回票价取决于经理。")
            print("      • 看基金经理任职 ≥ 5 年")
            print("      • 看历史最大回撤是否扛住过 2018/2022 这种熊市")
            print("      • 看规模：50 亿-200 亿之间最佳")
        else:
            print("   🔴 主动基金的总费率已经超 1.7%，长期看大概率跑不赢同指数。")
    elif args.type == "bank_wealth":
        if annual_fee <= 0.4:
            print("   ✅ 银行理财费率合理。")
        else:
            print("   🟡 银行理财收的费用 0.5%+ 算不便宜，注意'业绩比较基准'≠'承诺收益'。")

    print("\n📌 普适提醒：")
    print("   • 持有 < 1 年，选 C 类（无申购费有销售服务费，短期更划算）")
    print("   • 持有 > 1 年，选 A 类（有申购费但没有销售服务费）")
    print("   • 申购费一般打 1 折（如 1.5% → 0.15%），看清是否打折后")
    print("   • 同一只基金，不同渠道（券商 / 第三方 / 银行）费率差很多，多比较\n")


if __name__ == "__main__":
    main()
