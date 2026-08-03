# -*- coding: utf-8 -*-
"""
越南财税计算器套件 v1.0
Vietnam Finance & Tax Calculator Suite

包含三个可直接运行的测算工具：
  1. CIT 企业所得税估算（含优惠税率与免税/减半期）
  2. 工资总成本测算（含 21.5% 社保 + 工会费 + PIT 代扣估算）
  3. 外国承包商税 FCT 代扣 / gross-up 反算

用法示例：
  python calculators.py cit --revenue 50_000_000_000 --cost 38_000_000_000 --rate 10 --free 4 --half 9
  python calculators.py cit --revenue 50_000_000_000 --cost 38_000_000_000 --rate 10 --free 4 --half 9 --schedule
  python calculators.py cit --revenue 50_000_000_000 --cost 38_000_000_000 --rate 10 --free 4 --half 9 --year 6
  python calculators.py payroll --headcount 100 --wage 12_000_000
  python calculators.py fct --gross 100_000_000 --rate 10
  python calculators.py fct --net 90_000_000 --rate 10 --grossup

说明：
  - 所有金额单位为越南盾 VND。输入可用下划线分隔（Python 数字字面量）。
  - PIT 为简易估算（未逐项扣除家庭减免），实际申报以税务机关核定为准。
  - 社保雇主费率 21.5%（养老遗属14%+疾病生育3%+工伤0.5%+失业1%+医疗3%，
    依据2024年《社会保险法》第32条，2025-07-01生效；语料 vn_social_insurance_chinese_lawma.txt）；
    工会费另计 2%（雇主1%+雇员1%）。CIT 优惠期已按年度排期（--year / --schedule）。
  - 本工具为测算辅助，不构成税务意见，重大事项请咨询持牌越南会计师事务所。
"""

import argparse
import json


# ---------------------------------------------------------------------------
# 1. CIT 企业所得税估算
# ---------------------------------------------------------------------------
def cit_estimate(revenue, cost, rate=20.0, free_years=0, half_years=0,
                 loss_carry=None, year=None):
    """
    估算企业所得税（单年快照，支持免税/减半期）。
    优惠期按"年度排期"建模：前 free_years 年 0%；其后 half_years 年按 rate/2；
    再之后按全额 rate。修复旧版"free>0 即全年 0%"导致减半期被吞掉的缺陷。
    :param revenue: 年营业收入 (VND)
    :param cost:    可税前扣除成本 (VND)
    :param rate:    适用 CIT 税率 (%) 默认 20%；优惠项目常 10%
    :param free_years: 免税年数（运营前 N 年，税率 0%）
    :param half_years: 减半年数（免税年后 N 年，按 rate/2 征收）
    :param loss_carry: 可弥补以前年度亏损 (VND)，可选
    :param year:    指定测算第几年（1-indexed）；缺省按第 1 年处理
    :return: dict
    """
    taxable = max(revenue - cost, 0)
    if loss_carry:
        taxable = max(taxable - loss_carry, 0)

    normal_tax = taxable * rate / 100.0

    # 按所属年度确定有效税率（免税 → 减半 → 全额）
    if free_years or half_years:
        y = year if year is not None else 1
        if y <= free_years:
            eff = 0.0
        elif y <= free_years + half_years:
            eff = rate / 2.0
        else:
            eff = rate
    else:
        eff = rate

    preferential_tax = taxable * eff / 100.0
    saving = normal_tax - preferential_tax

    return {
        "currency": "VND",
        "annual_revenue": round(revenue),
        "deductible_cost": round(cost),
        "taxable_income": round(taxable),
        "applied_cit_rate_pct": rate,
        "tax_holiday_free_years": free_years,
        "tax_holiday_half_years": half_years,
        "query_year": year if year is not None else 1,
        "effective_rate_pct": round(eff, 2),
        "cit_without_incentive_VND": round(normal_tax),
        "cit_with_incentive_VND": round(preferential_tax),
        "annual_tax_saving_VND": round(saving),
    }


def cit_schedule(revenue, cost, rate=20.0, free_years=0, half_years=0,
                 loss_carry=None, horizon=None):
    """
    生成免税/减半期逐年税表，并汇总累计税负与节税。
    :param horizon: 测算年数；缺省 = free_years + half_years（至少 1 年）
    """
    taxable = max(revenue - cost, 0)
    if loss_carry:
        taxable = max(taxable - loss_carry, 0)
    if horizon is None:
        horizon = max(free_years + half_years, 1)

    rows = []
    cum_inc = cum_full = 0.0
    for y in range(1, horizon + 1):
        if y <= free_years:
            eff = 0.0
        elif y <= free_years + half_years:
            eff = rate / 2.0
        else:
            eff = rate
        t_inc = taxable * eff / 100.0
        t_full = taxable * rate / 100.0
        cum_inc += t_inc
        cum_full += t_full
        phase = "免税" if y <= free_years else ("减半" if y <= free_years + half_years else "全额")
        rows.append({
            "year": y, "phase": phase, "eff_rate_pct": eff,
            "cit_VND": round(t_inc), "cit_full_VND": round(t_full),
        })
    saving = cum_full - cum_inc
    avg_eff = (cum_inc / (taxable * horizon) * 100.0) if taxable else 0.0
    return {
        "currency": "VND",
        "taxable_income": round(taxable),
        "applied_cit_rate_pct": rate,
        "horizon_years": horizon,
        "free_years": free_years,
        "half_years": half_years,
        "cit_no_incentive_cum_VND": round(cum_full),
        "cit_with_incentive_cum_VND": round(cum_inc),
        "cumulative_tax_saving_VND": round(saving),
        "avg_effective_rate_pct": round(avg_eff, 2),
        "schedule": rows,
    }


# ---------------------------------------------------------------------------
# 2. 工资总成本测算
# ---------------------------------------------------------------------------
# 社保费率（雇主侧）——依据 2024 年《社会保险法》第32条，2025-07-01 生效（语料 vn_social_insurance_chinese_lawma.txt）
# 雇主合计 21.5% = 养老遗属 14% + 疾病生育 3% + 工伤 0.5% + 失业 1% + 医疗 3%
SI_EMPLOYER_RATE = 21.5      # % 雇主社保合计（2025 新法）
UNION_EMPLOYER_RATE = 1.0    # % 工会费雇主部分（工会费总 2%，雇主 1%）
PIT_BASIC_DEDUCTION = 11_000_000   # VND 个人免税额（2020 起）
PIT_DEPENDENT_DEDUCTION = 4_400_000  # VND 每位赡养人


def _pit_estimate(monthly_gross, dependents=0):
    """简易 PIT 月度估算（居民，按累进税表近似）。"""
    taxable = monthly_gross - PIT_BASIC_DEDUCTION - dependents * PIT_DEPENDENT_DEDUCTION
    if taxable <= 0:
        return 0.0
    # 月度累进税率档（VND）
    brackets = [
        (0, 5_000_000, 5),
        (5_000_000, 10_000_000, 10),
        (10_000_000, 18_000_000, 15),
        (18_000_000, 32_000_000, 20),
        (32_000_000, 52_000_000, 25),
        (52_000_000, 80_000_000, 30),
        (80_000_000, float("inf"), 35),
    ]
    tax = 0.0
    for low, high, r in brackets:
        if taxable <= low:
            break
        portion = min(taxable, high) - low
        if portion <= 0:
            continue
        tax += portion * r / 100.0
    return tax


def payroll_total(headcount, monthly_gross_wage, dependents=0):
    """
    测算雇主月度/年度工资总成本。
    :param headcount: 员工人数
    :param monthly_gross_wage: 人均月应税工资 (VND)
    :param dependents: 人均赡养人数（用于 PIT 估算）
    :return: dict
    """
    si_employer = monthly_gross_wage * SI_EMPLOYER_RATE / 100.0
    union_employer = monthly_gross_wage * UNION_EMPLOYER_RATE / 100.0
    pit_per_head = _pit_estimate(monthly_gross_wage, dependents)
    # 雇员侧社保（10.5%：养老8+医疗1.5+失业1）由工资代扣，不计入雇主成本但影响实发
    si_employee = monthly_gross_wage * 10.5 / 100.0

    employer_cost_per_head = monthly_gross_wage + si_employer + union_employer
    net_per_head = monthly_gross_wage - si_employee - pit_per_head

    return {
        "currency": "VND",
        "headcount": headcount,
        "avg_monthly_gross_wage": round(monthly_gross_wage),
        "si_employer_rate_pct": SI_EMPLOYER_RATE,
        "union_employer_rate_pct": UNION_EMPLOYER_RATE,
        "pit_per_head_monthly_VND": round(pit_per_head),
        "employer_cost_per_head_monthly_VND": round(employer_cost_per_head),
        "employer_cost_total_monthly_VND": round(employer_cost_per_head * headcount),
        "employer_cost_total_annual_VND": round(employer_cost_per_head * headcount * 12),
        "net_pay_per_head_monthly_VND": round(net_per_head),
        "si_employee_deduction_pct": 10.5,
    }


# ---------------------------------------------------------------------------
# 3. 外国承包商税 FCT
# ---------------------------------------------------------------------------
def fct_withhold(gross_payment, rate=10.0):
    """
    FCT 代扣：已知对外国承包商的含税支付总额，计算应代扣税额。
    越南 FCT 通常以含税法（gross-up）计征：税 = 支付额 × 税率/(100+税率)。
    :param gross_payment: 含税支付总额 (VND)
    :param rate: FCT 综合税率 (%) 视收入类型而定（如技术服务 10%、利息 5% 等）
    :return: dict
    """
    tax = gross_payment * rate / (100.0 + rate)
    net = gross_payment - tax
    return {
        "currency": "VND",
        "gross_payment_VND": round(gross_payment),
        "fct_rate_pct": rate,
        "fct_tax_VND": round(tax),
        "net_to_contractor_VND": round(net),
    }


def fct_grossup(net_amount, rate=10.0):
    """
    FCT 反算（gross-up）：已知承包商净到手金额，反算含税总支付与税额。
    :param net_amount: 承包商净到手 (VND)
    :param rate: FCT 综合税率 (%)
    :return: dict
    """
    gross = net_amount * (100.0 + rate) / 100.0
    tax = gross - net_amount
    return {
        "currency": "VND",
        "net_to_contractor_VND": round(net_amount),
        "fct_rate_pct": rate,
        "gross_payment_VND": round(gross),
        "fct_tax_VND": round(tax),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _fmt(v):
    return f"{v:,.0f}"


def main():
    p = argparse.ArgumentParser(description="越南财税计算器套件")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("cit", help="CIT 企业所得税估算")
    pc.add_argument("--revenue", type=float, required=True, help="年营业收入 VND")
    pc.add_argument("--cost", type=float, required=True, help="可扣除成本 VND")
    pc.add_argument("--rate", type=float, default=20.0, help="CIT 税率%% 默认20")
    pc.add_argument("--free", type=int, default=0, help="免税年数")
    pc.add_argument("--half", type=int, default=0, help="减半年数")
    pc.add_argument("--loss", type=float, default=0.0, help="可弥补亏损 VND")
    pc.add_argument("--year", type=int, default=None, help="测算第几年(1起)；与--schedule二选一")
    pc.add_argument("--schedule", action="store_true", help="输出免税/减半期逐年税表")

    pp = sub.add_parser("payroll", help="工资总成本测算")
    pp.add_argument("--headcount", type=int, required=True, help="员工人数")
    pp.add_argument("--wage", type=float, required=True, help="人均月应税工资 VND")
    pp.add_argument("--dependents", type=int, default=0, help="人均赡养人数")

    pf = sub.add_parser("fct", help="外国承包商税 FCT")
    pf.add_argument("--gross", type=float, default=0.0, help="含税支付总额 VND")
    pf.add_argument("--net", type=float, default=0.0, help="承包商净到手 VND")
    pf.add_argument("--rate", type=float, default=10.0, help="FCT 税率%%")
    pf.add_argument("--grossup", action="store_true", help="启用 gross-up 反算")

    args = p.parse_args()

    if args.cmd == "cit":
        if args.schedule:
            s = cit_schedule(args.revenue, args.cost, args.rate,
                             args.free, args.half, args.loss)
            print(f"应税所得 {_fmt(s['taxable_income'])} VND ｜ 适用税率 {s['applied_cit_rate_pct']}% ｜ 测算 {s['horizon_years']} 年")
            print(f"{'年':>4}{'阶段':>6}{'有效税率':>10}{'当年税(VND)':>20}{'无优惠(VND)':>20}")
            print("-" * 62)
            for r in s["schedule"]:
                print(f"{r['year']:>4}{r['phase']:>6}{r['eff_rate_pct']:>9}%{r['cit_VND']:>20,}{r['cit_full_VND']:>20,}")
            print("-" * 62)
            print(f"累计税负(有优惠) {_fmt(s['cit_with_incentive_cum_VND'])} ｜ 无优惠 {_fmt(s['cit_no_incentive_cum_VND'])} ｜ 节税 {_fmt(s['cumulative_tax_saving_VND'])}")
            print(f"优惠期平均实际税率 {s['avg_effective_rate_pct']}%")
        else:
            r = cit_estimate(args.revenue, args.cost, args.rate,
                             args.free, args.half, args.loss, args.year)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            print(f"\n[解读] 第 {r['query_year']} 年：应税所得 {_fmt(r['taxable_income'])} VND；"
                  f"无优惠年税 {_fmt(r['cit_without_incentive_VND'])}，"
                  f"享优惠后 {_fmt(r['cit_with_incentive_VND'])}，"
                  f"年省 {_fmt(r['annual_tax_saving_VND'])} VND（有效税率 {r['effective_rate_pct']}%）。")
            if args.free or args.half:
                print(f"  提示：免税/减半期为多年安排，加 --schedule 看逐年税表与累计节税。")
    elif args.cmd == "payroll":
        r = payroll_total(args.headcount, args.wage, args.dependents)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        print(f"\n[解读] 雇主月总成本 {_fmt(r['employer_cost_total_monthly_VND'])} VND，"
              f"年总成本 {_fmt(r['employer_cost_total_annual_VND'])} VND；"
              f"人均实发 {_fmt(r['net_pay_per_head_monthly_VND'])} VND/月。")
    elif args.cmd == "fct":
        if args.grossup:
            r = fct_grossup(args.net, args.rate)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            print(f"\n[解读] 净到手 {_fmt(r['net_to_contractor_VND'])} 需含税支付 "
                  f"{_fmt(r['gross_payment_VND'])}，代扣 FCT {_fmt(r['fct_tax_VND'])} VND。")
        else:
            r = fct_withhold(args.gross, args.rate)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            print(f"\n[解读] 含税支付 {_fmt(r['gross_payment_VND'])} 需代扣 FCT "
                  f"{_fmt(r['fct_tax_VND'])}，承包商净得 {_fmt(r['net_to_contractor_VND'])} VND。")


if __name__ == "__main__":
    main()
