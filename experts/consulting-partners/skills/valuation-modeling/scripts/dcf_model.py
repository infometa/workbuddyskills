#!/usr/bin/env python3
"""
DCF 估值模型 —— 自由现金流折现 + 敏感性分析
原创实现，供 consulting-partners 专家团的测算顾问（valuation-modeler）使用。

用法：
    python3 dcf_model.py --fcf 100,110,125,140,155 --discount-rate 0.10 --terminal-growth 0.03 --net-debt 200

输出：
    - 企业价值、股权价值（如提供净负债）
    - 折现率 x 永续增长率 交叉敏感性表
"""

import argparse
import json
import sys


def discount_factor(rate: float, year: int) -> float:
    return 1.0 / ((1.0 + rate) ** year)


def pv_of_explicit_fcf(fcf_list, discount_rate: float) -> float:
    return sum(fcf * discount_factor(discount_rate, year) for year, fcf in enumerate(fcf_list, start=1))


def terminal_value(last_fcf: float, discount_rate: float, terminal_growth: float) -> float:
    if discount_rate <= terminal_growth:
        raise ValueError("折现率必须大于永续增长率，否则终值发散，测算无意义")
    tv = last_fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
    return tv


def dcf_valuation(fcf_list, discount_rate: float, terminal_growth: float, net_debt: float = 0.0):
    explicit_pv = pv_of_explicit_fcf(fcf_list, discount_rate)
    n_years = len(fcf_list)
    tv = terminal_value(fcf_list[-1], discount_rate, terminal_growth)
    tv_pv = tv * discount_factor(discount_rate, n_years)
    enterprise_value = explicit_pv + tv_pv
    equity_value = enterprise_value - net_debt
    return {
        "explicit_period_pv": round(explicit_pv, 2),
        "terminal_value": round(tv, 2),
        "terminal_value_pv": round(tv_pv, 2),
        "enterprise_value": round(enterprise_value, 2),
        "net_debt": net_debt,
        "equity_value": round(equity_value, 2),
        "terminal_value_share_of_ev": round(tv_pv / enterprise_value, 4) if enterprise_value else None,
    }


def sensitivity_table(fcf_list, discount_rates, terminal_growths, net_debt: float = 0.0):
    """折现率 x 永续增长率 交叉敏感性表，返回股权价值矩阵"""
    table = []
    header = ["折现率\\永续增长率"] + [f"{g:.1%}" for g in terminal_growths]
    table.append(header)
    for r in discount_rates:
        row = [f"{r:.1%}"]
        for g in terminal_growths:
            try:
                result = dcf_valuation(fcf_list, r, g, net_debt)
                row.append(result["equity_value"])
            except ValueError:
                row.append("N/A（折现率<=增长率）")
        table.append(row)
    return table


def print_table(table):
    widths = [max(len(str(row[i])) for row in table) for i in range(len(table[0]))]
    for row in table:
        print(" | ".join(str(cell).rjust(widths[i]) for i, cell in enumerate(row)))


def main():
    parser = argparse.ArgumentParser(description="DCF 估值 + 敏感性分析")
    parser.add_argument("--fcf", required=True, help="逗号分隔的未来自由现金流预测，如 100,110,125,140,155")
    parser.add_argument("--discount-rate", type=float, required=True, help="基准折现率，如 0.10")
    parser.add_argument("--terminal-growth", type=float, required=True, help="基准永续增长率，如 0.03")
    parser.add_argument("--net-debt", type=float, default=0.0, help="净负债，用于从企业价值推算股权价值")
    parser.add_argument("--sensitivity", action="store_true", help="是否输出折现率x永续增长率敏感性表")
    parser.add_argument("--json-out", help="将结果写入指定 JSON 文件路径")
    args = parser.parse_args()

    fcf_list = [float(x) for x in args.fcf.split(",")]

    base = dcf_valuation(fcf_list, args.discount_rate, args.terminal_growth, args.net_debt)
    print("=== DCF 基准估值 ===")
    for k, v in base.items():
        print(f"{k}: {v}")

    result = {"base_case": base}

    if args.sensitivity:
        rates = [args.discount_rate + delta for delta in (-0.02, -0.01, 0, 0.01, 0.02)]
        growths = [args.terminal_growth + delta for delta in (-0.01, -0.005, 0, 0.005, 0.01)]
        table = sensitivity_table(fcf_list, rates, growths, args.net_debt)
        print("\n=== 敏感性表（股权价值） ===")
        print_table(table)
        result["sensitivity_table"] = table

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已写入 {args.json_out}")


if __name__ == "__main__":
    sys.exit(main())
