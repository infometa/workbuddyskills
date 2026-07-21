#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DCF implied terminal profit helper for stock narrative analysis.

The model answers: given current market cap and the next three years of profit
expectations, what stable terminal profit L is implied by today's price?

Assumptions:
- t=1..3: use E1/E2/E3 directly.
- t=4..8: grow from E3 to terminal profit L with constant CAGR.
- t=9 onward: L is stable forever, with no perpetual growth.
- Net profit is treated as an equity cash-flow proxy; callers must qualify this.
"""

from __future__ import annotations

import argparse
import math


R_GRID = (8.0, 10.0, 12.0)
GROWTH_YEARS = 5


def fair_value(l_terminal: float, e1: float, e2: float, e3: float, r_pct: float) -> float:
    """Return fair market cap for terminal profit L and discount rate r_pct."""
    if r_pct <= 0:
        raise ValueError("discount rate must be positive")
    if l_terminal < 0:
        raise ValueError("terminal profit must be non-negative")

    r = r_pct / 100.0
    pv = e1 / (1 + r) + e2 / (1 + r) ** 2 + e3 / (1 + r) ** 3

    if e3 > 0 and l_terminal > 0:
        g = (l_terminal / e3) ** (1.0 / GROWTH_YEARS) - 1.0
        for t in range(4, 4 + GROWTH_YEARS):
            profit_t = e3 * (1 + g) ** (t - 3)
            pv += profit_t / (1 + r) ** t

    pv += (l_terminal / r) / (1 + r) ** (3 + GROWTH_YEARS)
    return pv


def implied_ceiling(cap: float, e1: float, e2: float, e3: float, r_pct: float) -> float:
    """Solve implied terminal profit L with binary search."""
    if cap <= 0:
        raise ValueError("market cap must be positive")
    if e3 <= 0:
        raise ValueError("E3 must be positive for standard implied-L calculation")

    r = r_pct / 100.0
    hi = max(cap * r * (1 + r) ** (3 + GROWTH_YEARS) * 10, e3 * 100, 1000.0)
    lo = 0.0
    for _ in range(240):
        mid = (lo + hi) / 2.0
        if fair_value(mid, e1, e2, e3, r_pct) < cap:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def implied_growth_rate(l_terminal: float, e3: float) -> float:
    """Return CAGR from E3 to terminal profit L over the transition period."""
    if e3 <= 0 or l_terminal <= 0:
        return math.nan
    return ((l_terminal / e3) ** (1.0 / GROWTH_YEARS) - 1.0) * 100.0


def _ratio(value: float, base: float) -> float:
    return value / base if base > 0 else math.nan


def _print_implied(args: argparse.Namespace) -> None:
    print("DCF反算：当前市值隐含的终局利润L")
    print(f"市值: {args.cap:.2f} 亿元")
    print(f"E1/E2/E3: {args.e1:.2f} / {args.e2:.2f} / {args.e3:.2f} 亿元")
    if args.e0 is not None:
        print(f"E0: {args.e0:.2f} 亿元")
    print("假设: 前3年用预期净利润，第4-8年过渡至L，第9年起L永续稳定")
    print()
    headers = ["r", "隐含L(亿元)", "L/E3", "L/E0", "隐含g", "市值/E1"]
    print(" | ".join(f"{h:>12}" for h in headers))
    print("-" * 83)
    for r_pct in R_GRID:
        l_terminal = implied_ceiling(args.cap, args.e1, args.e2, args.e3, r_pct)
        l_e3 = _ratio(l_terminal, args.e3)
        l_e0 = _ratio(l_terminal, args.e0) if args.e0 is not None else math.nan
        g = implied_growth_rate(l_terminal, args.e3)
        pe1 = _ratio(args.cap, args.e1)
        print(
            f"{r_pct:>10.0f}% | {l_terminal:>10.2f} | {l_e3:>10.2f}x | "
            f"{l_e0:>10.2f}x | {g:>10.2f}% | {pe1:>10.2f}x"
        )
    print()
    print("提示: 该结果表示价格隐含预期，不是目标价或投资建议。")


def _print_calc(args: argparse.Namespace) -> None:
    cap = fair_value(args.l, args.e1, args.e2, args.e3, args.r)
    g = implied_growth_rate(args.l, args.e3)
    pe1 = _ratio(cap, args.e1)
    print(f"终局L={args.l:.2f}亿元, r={args.r:.2f}%")
    print(f"对应市值={cap:.2f}亿元")
    print(f"隐含第4-8年复合增速={g:.2f}%")
    print(f"市值/E1={pe1:.2f}x")


def _print_sensitivity(args: argparse.Namespace) -> None:
    print(f"敏感性分析: r={args.r:.2f}%, E1/E2/E3={args.e1:.2f}/{args.e2:.2f}/{args.e3:.2f}亿元")
    headers = ["L/E3", "L(亿元)", "L/E0", "市值(亿元)", "市值/E1"]
    print(" | ".join(f"{h:>12}" for h in headers))
    print("-" * 70)
    for ratio in (0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 10.0, 15.0, 20.0):
        l_terminal = args.e3 * ratio
        cap = fair_value(l_terminal, args.e1, args.e2, args.e3, args.r)
        l_e0 = _ratio(l_terminal, args.e0) if args.e0 is not None else math.nan
        pe1 = _ratio(cap, args.e1)
        print(f"{ratio:>10.1f}x | {l_terminal:>10.2f} | {l_e0:>10.2f}x | {cap:>10.2f} | {pe1:>10.2f}x")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DCF隐含终局利润L反算工具")
    sub = parser.add_subparsers(dest="command", required=True)

    implied = sub.add_parser("implied", help="由市值和E1/E2/E3反算隐含终局利润L")
    implied.add_argument("--cap", type=float, required=True, help="当前市值，单位亿元")
    implied.add_argument("--e1", type=float, required=True, help="第1年预期净利润，单位亿元")
    implied.add_argument("--e2", type=float, required=True, help="第2年预期净利润，单位亿元")
    implied.add_argument("--e3", type=float, required=True, help="第3年预期净利润，单位亿元")
    implied.add_argument("--e0", type=float, default=None, help="最近已完成财年净利润，单位亿元")
    implied.set_defaults(func=_print_implied)

    calc = sub.add_parser("calc", help="由终局L和E1/E2/E3正算市值")
    calc.add_argument("--l", type=float, required=True, help="终局利润L，单位亿元")
    calc.add_argument("--e1", type=float, required=True, help="第1年预期净利润，单位亿元")
    calc.add_argument("--e2", type=float, required=True, help="第2年预期净利润，单位亿元")
    calc.add_argument("--e3", type=float, required=True, help="第3年预期净利润，单位亿元")
    calc.add_argument("--r", type=float, required=True, help="折现率百分比，如10表示10%%")
    calc.set_defaults(func=_print_calc)

    sensitivity = sub.add_parser("sensitivity", help="输出不同L/E3对应的市值敏感性表")
    sensitivity.add_argument("--e1", type=float, required=True, help="第1年预期净利润，单位亿元")
    sensitivity.add_argument("--e2", type=float, required=True, help="第2年预期净利润，单位亿元")
    sensitivity.add_argument("--e3", type=float, required=True, help="第3年预期净利润，单位亿元")
    sensitivity.add_argument("--e0", type=float, default=None, help="最近已完成财年净利润，单位亿元")
    sensitivity.add_argument("--r", type=float, default=10.0, help="折现率百分比，默认10")
    sensitivity.set_defaults(func=_print_sensitivity)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
