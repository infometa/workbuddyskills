# -*- coding: utf-8 -*-
"""
越南建厂选址成本模拟器 v1.0
Vietnam Factory Location Cost Simulator

读取 data/cost_reference.json，根据用户设定的工厂规模，跨多省测算年度综合运营成本，
并可选叠加 CIT（需提供年营收）。

用法：
  python location_sim.py --headcount 100 --factory_area 5000 --land_area 50000
  python location_sim.py --headcount 200 --factory_area 8000 --land_area 80000 \
      --provinces bac_ninh,binh_duong,quang_ngai --revenue 50_000_000_000

金额单位：土地/厂房为 USD，工资为 VND（内部换算 USD 用于汇总，汇率见 EXCHANGE_RATE）。
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calculators import payroll_total  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data", "cost_reference.json")
EXCHANGE_RATE = 26300.0  # 1 USD = 26,300 VND（2026-07 指示性）


def _load():
    with open(DATA, "r", encoding="utf-8") as f:
        return json.load(f)


def simulate(headcount, factory_area, land_area, provinces=None,
             profit=None, cit_override=None):
    """
    :param profit: 可选，年税前利润 USD；提供则单列 CIT 估算（不并入运营成本合计）
    :param cit_override: 可选，强制 CIT 税率%
    """
    data = _load()
    provs = data["provinces"]
    if provinces:
        keys = [p.strip() for p in provinces.split(",") if p.strip() in provs]
    else:
        keys = list(provs.keys())

    rows = []
    for k in keys:
        p = provs[k]
        # 土地年租金 USD
        land_cost = p["land_rent_usd_per_m2_year"] * land_area
        # 厂房年租金 USD
        factory_cost = p["factory_rent_usd_per_m2_month"] * factory_area * 12
        # 工资年成本（用计算器，返回 VND 再换算 USD）
        pr = payroll_total(headcount, p["avg_gross_wage_vnd"])
        payroll_usd = pr["employer_cost_total_annual_VND"] / EXCHANGE_RATE
        # CIT（可选，单列，不计入运营成本合计）
        cit_usd = 0.0
        cit_note = "未提供利润，未计"
        if profit:
            rate = cit_override if cit_override else p["cit_rate_pct"]
            cit_usd = profit * rate / 100.0
            cit_note = f"税前利润计，税率 {rate}%"

        total = land_cost + factory_cost + payroll_usd
        rows.append({
            "key": k,
            "name_zh": p["name_zh"],
            "region": p["region"],
            "land_cost_usd": round(land_cost),
            "factory_cost_usd": round(factory_cost),
            "payroll_cost_usd": round(payroll_usd),
            "cit_usd": round(cit_usd),
            "cit_note": cit_note,
            "total_annual_usd": round(total),
            "cit_rate_pct": p["cit_rate_pct"],
        })

    rows.sort(key=lambda r: r["total_annual_usd"])
    return rows


def main():
    p = argparse.ArgumentParser(description="越南建厂选址成本模拟器")
    p.add_argument("--headcount", type=int, required=True, help="员工人数")
    p.add_argument("--factory_area", type=float, required=True, help="厂房面积 m2")
    p.add_argument("--land_area", type=float, required=True, help="用地面积 m2")
    p.add_argument("--provinces", type=str, default=None, help="逗号分隔省key，默认全部")
    p.add_argument("--profit", type=float, default=None, help="年税前利润 USD（用于单列CIT）")
    p.add_argument("--cit_override", type=float, default=None, help="强制CIT税率%")
    args = p.parse_args()

    rows = simulate(args.headcount, args.factory_area, args.land_area,
                    args.provinces, args.profit, args.cit_override)

    print(f"{'省份':<10}{'土地':>12}{'厂房':>12}{'工资':>12}{'CIT(单列)':>14}{'运营成本合计':>16}")
    print("-" * 78)
    for r in rows:
        print(f"{r['name_zh']:<10}{r['land_cost_usd']:>12,}{r['factory_cost_usd']:>12,}"
              f"{r['payroll_cost_usd']:>12,}{r['cit_usd']:>14,}{r['total_annual_usd']:>16,}")
    if rows:
        best = rows[0]
        print("-" * 78)
        print(f"★ 最低运营成本：{best['name_zh']}（{best['region']}），"
              f"约 ${best['total_annual_usd']:,}/年（不含CIT）")
        print(f"  成本结构：土地 ${best['land_cost_usd']:,} / 厂房 ${best['factory_cost_usd']:,} "
              f"/ 工资 ${best['payroll_cost_usd']:,}")
        if args.profit:
            print(f"  CIT 单列（{best['cit_note']}）：{best['name_zh']} ${best['cit_usd']:,}，"
                  f"平阳(20%)将显著更高——选址的税率差异直接决定税后利润。")


if __name__ == "__main__":
    main()
