#!/usr/bin/env python3
"""
风险承受力测评（Risk Tolerance Quiz）

10 题快速测出你的风险偏好等级，并给出对应的资产配置建议。

用法:
    python risk_quiz.py             # 交互模式（终端逐题作答）
    python risk_quiz.py --auto 30 5 0 1 2 1 3 2 1 2   # 一次性传入 10 个分数
"""
from __future__ import annotations
import argparse
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


QUESTIONS = [
    {
        "q": "1. 你的年龄段？",
        "options": [
            ("A. 18-30 岁", 4),
            ("B. 31-40 岁", 3),
            ("C. 41-50 岁", 2),
            ("D. 51-60 岁", 1),
            ("E. 60 岁以上", 0),
        ],
    },
    {
        "q": "2. 你的家庭年收入相对稳定吗？",
        "options": [
            ("A. 非常稳定（公务员/国企/事业单位/大厂在编）", 4),
            ("B. 较稳定（民企正式员工）", 3),
            ("C. 一般（中小企业、合同制）", 2),
            ("D. 不稳定（自由职业/创业/打零工）", 1),
            ("E. 已退休/无主动收入", 0),
        ],
    },
    {
        "q": "3. 你的家庭可投资金（不含自住房和应急金）有多少？",
        "options": [
            ("A. 不到 1 万", 1),
            ("B. 1 万-10 万", 2),
            ("C. 10 万-50 万", 3),
            ("D. 50 万-200 万", 4),
            ("E. 200 万以上", 5),
        ],
    },
    {
        "q": "4. 这笔投资的钱，你打算放多久？",
        "options": [
            ("A. 1 年内可能要用", 0),
            ("B. 1-3 年", 1),
            ("C. 3-5 年", 2),
            ("D. 5-10 年", 3),
            ("E. 10 年以上", 4),
        ],
    },
    {
        "q": "5. 如果投资账户一年内亏损 30%，你的反应是？",
        "options": [
            ("A. 失眠焦虑，立刻全部卖掉", 0),
            ("B. 难受，会卖一半止损", 1),
            ("C. 不舒服，但能扛住不动", 2),
            ("D. 比较冷静，可能继续定投", 3),
            ("E. 兴奋，认为是加仓良机", 4),
        ],
    },
    {
        "q": "6. 你的投资经验？",
        "options": [
            ("A. 完全没有", 0),
            ("B. 只买过余额宝/银行理财", 1),
            ("C. 买过基金，没经历过完整熊市", 2),
            ("D. 买过基金/股票，经历过 -30% 的回撤", 3),
            ("E. 有 5 年以上经验，穿越过牛熊", 4),
        ],
    },
    {
        "q": "7. 你的负债情况？",
        "options": [
            ("A. 有信用卡分期 / 网贷", 0),
            ("B. 有车贷 / 装修贷", 1),
            ("C. 只有房贷，月供占收入 > 50%", 2),
            ("D. 只有房贷，月供占收入 < 30%", 3),
            ("E. 无任何负债", 4),
        ],
    },
    {
        "q": "8. 你的应急金（家庭月开支的多少倍）？",
        "options": [
            ("A. 几乎没有", 0),
            ("B. 1-3 个月", 1),
            ("C. 3-6 个月", 2),
            ("D. 6-12 个月", 3),
            ("E. 12 个月以上", 4),
        ],
    },
    {
        "q": "9. 你期望的年化收益率是？",
        "options": [
            ("A. 跑赢通胀就行（3%-4%）", 4),
            ("B. 5%-6%", 3),
            ("C. 7%-9%", 2),
            ("D. 10%-15%", 1),
            ("E. 15% 以上 / 翻倍", 0),
        ],
    },
    {
        "q": "10. 你买保险的情况？",
        "options": [
            ("A. 完全没有", 0),
            ("B. 只有社保 / 单位福利", 1),
            ("C. 有医疗险 + 意外险", 2),
            ("D. 4 张基础保单（医疗/重疾/寿/意外）齐全", 4),
            ("E. 上面齐全且保额匹配收入", 4),
        ],
    },
]


PROFILES = [
    (0, 12, "保守型", {"现金": 30, "债券": 60, "股票/指数": 10, "黄金": 0},
     "最大回撤承受 < 5%，建议以保本和跑赢通胀为目标。"),
    (13, 20, "稳健型", {"现金": 20, "债券": 50, "股票/指数": 25, "黄金": 5},
     "最大回撤承受 5%-15%，可以小仓位试水股票/指数。"),
    (21, 28, "平衡型", {"现金": 15, "债券": 35, "股票/指数": 40, "黄金": 10},
     "最大回撤承受 15%-25%，适合股债平衡的经典配置。"),
    (29, 35, "进取型", {"现金": 10, "债券": 20, "股票/指数": 60, "黄金": 10},
     "最大回撤承受 25%-40%，可重仓权益类资产长期投资。"),
    (36, 100, "激进型", {"现金": 5, "债券": 10, "股票/指数": 75, "黄金/海外": 10},
     "最大回撤承受 > 40%，但仍要遵守'单只仓位 < 20%''不上杠杆'两条铁律。"),
]


def ask_question(idx, q):
    print(f"\n{q['q']}")
    for i, (text, _) in enumerate(q["options"]):
        print(f"   {text}")
    while True:
        ans = input("请选择 A/B/C/D/E: ").strip().upper()
        mapping = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
        if ans in mapping and mapping[ans] < len(q["options"]):
            return q["options"][mapping[ans]][1]
        print("⚠️  请输入 A、B、C、D 或 E")


def get_profile(score: int):
    for low, high, name, alloc, comment in PROFILES:
        if low <= score <= high:
            return name, alloc, comment
    return "未知", {}, ""


def main():
    parser = argparse.ArgumentParser(description="风险承受力测评")
    parser.add_argument("--auto", type=int, nargs="*",
                        help="跳过交互，直接传入 10 个题目得分")
    args = parser.parse_args()

    print("=" * 60)
    print("       小白理财教练 · 风险承受力测评")
    print("=" * 60)
    print("共 10 题，约 3 分钟完成。请凭直觉如实作答——\n"
          "不要选'你以为该选'的，要选'真实情况'的。")

    scores = []
    if args.auto:
        if len(args.auto) != 10:
            print("❌ --auto 必须传入 10 个分数")
            sys.exit(1)
        scores = args.auto
    else:
        for idx, q in enumerate(QUESTIONS):
            scores.append(ask_question(idx, q))

    total = sum(scores)
    name, alloc, comment = get_profile(total)

    print("\n" + "=" * 60)
    print(f"  你的总分：{total} / 41")
    print(f"  风险类型：【{name}】")
    print("=" * 60)
    print(f"\n📌 风险特征：{comment}")
    print("\n📊 推荐资产配置骨架：")
    for k, v in alloc.items():
        bar = "█" * (v // 3)
        print(f"   {k:>10s}  {v:>3d}%  {bar}")

    print("\n🎯 下一步建议：")
    if total <= 12:
        print("   1. 先把货币基金/国债/银行理财（R2）配置好")
        print("   2. 任何'高收益保本'产品都拒绝")
        print("   3. 不必勉强进股市，3%-4% 稳健收益已经合格")
    elif total <= 20:
        print("   1. 应急金 + 4 张保单优先")
        print("   2. 70%-80% 放债券基金，20%-30% 试水宽基指数定投")
        print("   3. 每月定投 1000-3000 元宽基指数（沪深 300 / 标普 500）")
    elif total <= 28:
        print("   1. 股债 6:4 经典配置")
        print("   2. 核心仓宽基指数 + 卫星仓行业基金")
        print("   3. 每年再平衡一次")
    elif total <= 35:
        print("   1. 重仓权益（指数 + 优质主动基金）")
        print("   2. 适度尝试个股（< 总仓位 20%）")
        print("   3. 关注海外配置（QDII）分散区域风险")
    else:
        print("   1. 你的风险偏好很高，但仍要守住三条铁律：")
        print("      - 单只标的仓位 < 20%")
        print("      - 应急金 + 保险必须配齐")
        print("      - 永远不上杠杆（融资融券、合约、配资）")
        print("   2. 强烈建议每年读 2 本投资经典，避免过度自信")

    print("\n⚠️  重要提示：")
    print("   • 这只是参考骨架，不是个性化投顾建议")
    print("   • 客观条件（年龄/收入）和主观偏好打架时，以保守为准")
    print("   • 半年后建议重新测一次，人在变，配置也要变\n")


if __name__ == "__main__":
    main()
