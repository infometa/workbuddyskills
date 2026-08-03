#!/usr/bin/env python3
"""
南非薪酬社保计算器
==================
覆盖 PAYE 累进税 / UIF / SDL / COIDA / ETI / 附加福利 / 净薪 / 雇主总成本。
纯 Python 标准库，无外部依赖。

用法：
    python calculators.py payroll --monthly 35000
    python calculators.py payroll --monthly 35000 --medical 2500 --pension 1750 --travel 5000
    python calculators.py annual --monthly 35000
    python calculators.py eti --age 24 --monthly 6000 --first-year
    python calculators.py severance --monthly 40000 --years 5
    python calculators.py leave --monthly 35000 --days 15
"""

import argparse
import json
import sys
from pathlib import Path

# ============================================================
# 2026/27 税务年度税率表（2026年3月1日 - 2027年2月28日）
# 注：以上为角色定义现行税率；实际申报前请通过 supplement/realtime_sources 的 SARS 源核实最新公报
# ============================================================

# PAYE 累进税率表（年收入 R，2026/27）
PAYE_BRACKETS_2026_27 = [
    (0,           245_100,      0.18),
    (245_101,     383_100,      0.26),
    (383_101,     530_200,      0.31),
    (530_201,     695_800,      0.36),
    (695_801,     887_000,      0.39),
    (887_001,     1_878_600,    0.41),
    (1_878_601,   float('inf'), 0.45),
]

# 退税（2026/27）
PAYE_REBATE_2026_27 = {
    "primary":   17_820,    # 65岁以下
    "secondary": 9_765,     # 65-74岁（额外）
    "tertiary":  3_249,     # 75岁以上（额外）
}

# UIF 上限（月薪）
UIF_MONTHLY_CEILING = 17_712
UIF_RATE_EMPLOYER = 0.01
UIF_RATE_EMPLOYEE = 0.01

# SDL
SDL_RATE = 0.01
SDL_THRESHOLD = 500_000  # 年薪酬支出超过此值才需缴纳

# COIDA（示例费率，实际按行业风险等级浮动）
COIDA_EXAMPLE_RATES = {
    "office_low_risk": 0.0011,     # 办公低风险 0.11%
    "manufacturing": 0.03,         # 制造业 ~3%
    "construction": 0.058,         # 建筑业 ~5.8%
    "mining_high": 0.0779,         # 矿业高风险 7.79%
}

# ETI 参数（2025年4月1日更新）
ETI_MONTHLY_CEILING = 7_500
ETI_HOUR_BASE = 2_500  # 160小时基准月薪
ETI_RATES = {
    "first_year":  {"rate": 0.60, "max": 1_500},
    "second_year": {"rate": 0.30, "max": 750},
}

# 医疗援助税抵免（月度，2026/27）
MEDICAL_TAX_CREDIT_2026_27 = {
    "main":    376,
    "first":   376,
    "additional": 254,
}

# 最低工资（2026年3月1日起）
NMW_HOURLY_2026 = 30.23
NMW_MONTHLY_2026 = NMW_HOURLY_2026 * 160  # ≈ R4,836.80（160小时/月）


def calc_paye(annual_income: float, age: int = 30) -> dict:
    """计算 PAYE（个人所得税）"""
    tax = 0
    brackets_used = []
    for lower, upper, rate in PAYE_BRACKETS_2026_27:
        if annual_income > lower:
            taxable_in_bracket = min(annual_income, upper) - lower
            if taxable_in_bracket > 0:
                bracket_tax = taxable_in_bracket * rate
                tax += bracket_tax
                brackets_used.append({
                    "range": f"R{lower:,.0f} - R{upper:,.0f}" if upper != float('inf') else f"R{lower:,.0f}+",
                    "rate": f"{rate*100:.0f}%",
                    "taxable": round(taxable_in_bracket, 2),
                    "tax": round(bracket_tax, 2),
                })

    # 退税
    rebate = PAYE_REBATE_2026_27["primary"]
    if age >= 65:
        rebate += PAYE_REBATE_2026_27["secondary"]
    if age >= 75:
        rebate += PAYE_REBATE_2026_27["tertiary"]

    tax_after_rebate = max(0, tax - rebate)
    effective_rate = tax_after_rebate / annual_income if annual_income > 0 else 0

    return {
        "annual_gross": round(annual_income, 2),
        "annual_tax_before_rebate": round(tax, 2),
        "rebate": round(rebate, 2),
        "annual_paye": round(tax_after_rebate, 2),
        "monthly_paye": round(tax_after_rebate / 12, 2),
        "effective_rate": f"{effective_rate*100:.2f}%",
        "marginal_rate": f"{[b[2] for b in PAYE_BRACKETS_2026_27 if annual_income > b[0]][-1]*100:.0f}%",
        "brackets_detail": brackets_used,
    }


def calc_uif(monthly_salary: float) -> dict:
    """计算 UIF"""
    capped = min(monthly_salary, UIF_MONTHLY_CEILING)
    employee_contribution = capped * UIF_RATE_EMPLOYEE
    employer_contribution = capped * UIF_RATE_EMPLOYER
    return {
        "monthly_salary": round(monthly_salary, 2),
        "capped_at": round(capped, 2),
        "employee_contribution": round(employee_contribution, 2),
        "employer_contribution": round(employer_contribution, 2),
        "total_monthly": round(employee_contribution + employer_contribution, 2),
        "capped": monthly_salary > UIF_MONTHLY_CEILING,
    }


def calc_sdl(monthly_total_payroll: float, headcount: int = 1) -> dict:
    """计算 SDL（技能发展税）"""
    annual_payroll = monthly_total_payroll * 12
    applicable = annual_payroll > SDL_THRESHOLD
    monthly_sdl = monthly_total_payroll * SDL_RATE if applicable else 0
    return {
        "monthly_payroll": round(monthly_total_payroll, 2),
        "annual_payroll": round(annual_payroll, 2),
        "applicable": applicable,
        "rate": f"{SDL_RATE*100:.0f}%",
        "monthly_sdl": round(monthly_sdl, 2),
        "annual_sdl": round(monthly_sdl * 12, 2),
        "note": "年薪酬支出超过R500,000才需缴纳" if not applicable else "",
    }


def calc_coida(monthly_salary: float, industry: str = "office_low_risk") -> dict:
    """计算 COIDA（工伤赔偿）"""
    rate = COIDA_EXAMPLE_RATES.get(industry, 0.0011)
    annual_earnings = monthly_salary * 12
    # COIDA 有最高年收入上限（2026/27 R668,000）
    coida_annual_ceiling = 668_000
    capped_earnings = min(annual_earnings, coida_annual_ceiling)
    annual_coida = capped_earnings * rate
    return {
        "industry": industry,
        "rate": f"{rate*100:.4f}%",
        "annual_earnings": round(annual_earnings, 2),
        "capped_earnings": round(capped_earnings, 2),
        "annual_coida": round(annual_coida, 2),
        "monthly_coida": round(annual_coida / 12, 2),
        "note": "雇主全额承担，费率按行业风险等级浮动（0.11%-7.79%）",
    }


def calc_eti(age: int, monthly_salary: float, first_year: bool = True,
             hours_per_month: int = 160, special_economic_zone: bool = False) -> dict:
    """计算 ETI（雇佣税激励）"""
    # 资格检查
    age_eligible = 18 <= age <= 29 or special_economic_zone
    salary_eligible = monthly_salary <= ETI_MONTHLY_CEILING

    if not age_eligible:
        return {"eligible": False, "reason": f"年龄{age}岁不在18-29岁范围内（非SEZ）"}
    if not salary_eligible:
        return {"eligible": False, "reason": f"月薪R{monthly_salary:,.0f}超过上限R{ETI_MONTHLY_CEILING:,.0f}"}

    # 计算 ETI
    # 月薪不超过R2,000时按R2,000计算
    notional_salary = max(monthly_salary, ETI_HOUR_BASE * (hours_per_month / 160))

    year_key = "first_year" if first_year else "second_year"
    rate_info = ETI_RATES[year_key]
    eti_amount = notional_salary * rate_info["rate"]
    eti_capped = min(eti_amount, rate_info["max"])

    return {
        "eligible": True,
        "age": age,
        "monthly_salary": round(monthly_salary, 2),
        "notional_salary": round(notional_salary, 2),
        "year": year_key,
        "rate": f"{rate_info['rate']*100:.0f}%",
        "eti_monthly": round(eti_capped, 2),
        "eti_annual": round(eti_capped * 12, 2),
        "note": f"ETI可在EMP201中抵扣PAYE，{'第1年' if first_year else '第2年'}每月最高R{rate_info['max']:,.0f}",
    }


def calc_medical_tax_credit(medical_beneficiaries: int = 1) -> dict:
    """计算医疗援助税抵免"""
    main = MEDICAL_TAX_CREDIT_2026_27["main"]
    first = MEDICAL_TAX_CREDIT_2026_27["first"]
    additional = MEDICAL_TAX_CREDIT_2026_27["additional"]

    if medical_beneficiaries == 0:
        monthly_credit = 0
    elif medical_beneficiaries == 1:
        monthly_credit = main
    elif medical_beneficiaries == 2:
        monthly_credit = main + first
    else:
        monthly_credit = main + first + additional * (medical_beneficiaries - 2)

    return {
        "beneficiaries": medical_beneficiaries,
        "monthly_credit": round(monthly_credit, 2),
        "annual_credit": round(monthly_credit * 12, 2),
        "breakdown": {
            "main": main,
            "first_dependant": first if medical_beneficiaries >= 2 else 0,
            "additional_per_person": additional if medical_beneficiaries > 2 else 0,
            "additional_count": max(0, medical_beneficiaries - 2),
        },
    }


def calc_payroll(monthly_basic: float, age: int = 30,
                 medical_aid: float = 0, medical_beneficiaries: int = 0,
                 pension_rate: float = 0, travel_allowance: float = 0,
                 company_car_value: float = 0, industry: str = "office_low_risk",
                 headcount: int = 1) -> dict:
    """
    完整薪酬计算（单人或多人）
    """
    # 附加福利
    fringe_benefits = 0
    fringe_detail = {}

    if travel_allowance > 0:
        # Travel allowance 80% 计入应税收入
        taxable_travel = travel_allowance * 0.80
        fringe_benefits += taxable_travel
        fringe_detail["travel_allowance"] = {
            "monthly": round(travel_allowance, 2),
            "taxable_portion": round(taxable_travel, 2),
            "taxable_rate": "80%",
        }

    if company_car_value > 0:
        # 公司车：按价值的3.5%/月计入（或3.25%如果车辆有维护计划）
        company_car_monthly = company_car_value * 0.035
        fringe_benefits += company_car_monthly
        fringe_detail["company_car"] = {
            "vehicle_value": round(company_car_value, 2),
            "monthly_benefit": round(company_car_monthly, 2),
            "rate": "3.5%/月",
        }

    # 养老金缴款（员工部分）
    pension_employee = monthly_basic * (pension_rate / 100) if pension_rate > 0 else 0
    # 养老金可税前扣除（上限为应税收入的27.5%）
    pension_deductible = min(pension_employee, monthly_basic * 0.275)

    # 应税收入（月度）
    monthly_taxable = monthly_basic + fringe_benefits - pension_deductible
    annual_taxable = monthly_taxable * 12

    # 医疗援助税抵免
    med_credit = calc_medical_tax_credit(medical_beneficiaries) if medical_beneficiaries > 0 else None
    med_credit_monthly = med_credit["monthly_credit"] if med_credit else 0

    # PAYE（扣除医疗税抵免后）
    paye_result = calc_paye(annual_taxable, age)
    annual_paye_after_med = max(0, paye_result["annual_paye"] - med_credit_monthly * 12)
    monthly_paye = annual_paye_after_med / 12

    # UIF
    uif = calc_uif(monthly_basic)

    # SDL（雇主）
    sdl = calc_sdl(monthly_basic * headcount, headcount)

    # COIDA（雇主）
    coida = calc_coida(monthly_basic, industry)

    # 员工净薪
    total_deductions = monthly_paye + uif["employee_contribution"] + pension_employee + medical_aid
    net_pay = monthly_basic + fringe_benefits - total_deductions

    # 雇主总成本
    employer_cost = monthly_basic + uif["employer_contribution"] + sdl["monthly_sdl"] + coida["monthly_coida"] + medical_aid
    # 雇主养老金匹配（如适用）
    employer_pension = monthly_basic * (pension_rate / 100) if pension_rate > 0 else 0
    employer_cost += employer_pension

    return {
        "input": {
            "monthly_basic": round(monthly_basic, 2),
            "age": age,
            "headcount": headcount,
            "industry": industry,
        },
        "fringe_benefits": fringe_detail,
        "pension": {
            "employee_monthly": round(pension_employee, 2),
            "employer_monthly": round(employer_pension, 2),
            "rate": f"{pension_rate}%",
            "deductible": round(pension_deductible, 2),
        },
        "monthly_taxable_income": round(monthly_taxable, 2),
        "annual_taxable_income": round(annual_taxable, 2),
        "paye": {
            "monthly_paye": round(monthly_paye, 2),
            "annual_paye": round(annual_paye_after_med, 2),
            "marginal_rate": paye_result["marginal_rate"],
            "effective_rate": paye_result["effective_rate"],
        },
        "medical_tax_credit": med_credit,
        "uif": uif,
        "sdl": sdl,
        "coida": coida,
        "employee_net_pay": round(net_pay, 2),
        "employer_total_cost": round(employer_cost, 2),
        "employer_cost_ratio": f"{(employer_cost / monthly_basic - 1) * 100:.1f}%" if monthly_basic > 0 else "N/A",
        "total_deductions": round(total_deductions, 2),
    }


def calc_severance(monthly_remuneration: float, years_of_service: float) -> dict:
    """计算遣散费（BCEA Section 41）"""
    weekly_remuneration = monthly_remuneration * 12 / 52
    severance_pay = weekly_remuneration * years_of_service  # 每完整年1周薪酬
    # 注意：仅完整年计入
    complete_years = int(years_of_service)
    severance_statutory = weekly_remuneration * complete_years

    return {
        "monthly_remuneration": round(monthly_remuneration, 2),
        "weekly_remuneration": round(weekly_remuneration, 2),
        "years_of_service": years_of_service,
        "complete_years": complete_years,
        "statutory_severance": round(severance_statutory, 2),
        "formula": "周薪 × 完整年数（每完整年1周薪酬）",
        "note": "BCEA Section 41法定最低标准，协商通常更高（2-4周/年行业惯例）",
        "tax_note": "遣散费需申请SARS税务指令（Tax Directive），退休遣散费首R550,000免税",
    }


def calc_leave_pay(monthly_remuneration: float, leave_days: float,
                   work_days_per_month: int = 21) -> dict:
    """计算休假薪酬"""
    daily_rate = monthly_remuneration / work_days_per_month
    leave_pay = daily_rate * leave_days
    return {
        "monthly_remuneration": round(monthly_remuneration, 2),
        "daily_rate": round(daily_rate, 2),
        "leave_days": leave_days,
        "leave_pay": round(leave_pay, 2),
        "note": "BCEA法定年假21天（连续工作），休假期间薪酬不变",
    }


def calc_overtime(hourly_rate: float, overtime_hours: float,
                  sunday: bool = False, public_holiday: bool = False) -> dict:
    """计算加班费"""
    normal_pay = hourly_rate * overtime_hours

    if public_holiday:
        rate = 2.0
        label = "公共假日 2倍"
    elif sunday:
        rate = 2.0
        label = "周日 2倍"
    else:
        rate = 1.5
        label = "工作日加班 1.5倍"

    overtime_pay = hourly_rate * rate * overtime_hours
    return {
        "hourly_rate": round(hourly_rate, 2),
        "overtime_hours": overtime_hours,
        "rate": f"{rate}x",
        "rate_label": label,
        "overtime_pay": round(overtime_pay, 2),
        "normal_equivalent": round(normal_pay, 2),
        "extra_pay": round(overtime_pay - normal_pay, 2),
    }


def main():
    parser = argparse.ArgumentParser(
        description="南非薪酬社保计算器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s payroll --monthly 35000
  %(prog)s payroll --monthly 35000 --medical 2500 --beneficiaries 2 --pension 7.5
  %(prog)s payroll --monthly 25000 --travel 5000 --industry manufacturing --headcount 50
  %(prog)s eti --age 24 --monthly 6000 --first-year
  %(prog)s eti --age 22 --monthly 4500 --second-year
  %(prog)s severance --monthly 40000 --years 5
  %(prog)s leave --monthly 35000 --days 15
  %(prog)s overtime --hourly 150 --hours 10
  %(prog)s overtime --hourly 150 --hours 8 --sunday
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="计算类型")

    # payroll 子命令
    p_payroll = subparsers.add_parser("payroll", help="完整薪酬计算（PAYE+UIF+SDL+COIDA+附加福利）")
    p_payroll.add_argument("--monthly", type=float, required=True, help="月基本工资 (R)")
    p_payroll.add_argument("--age", type=int, default=30, help="员工年龄（影响退税）")
    p_payroll.add_argument("--medical", type=float, default=0, help="医疗援助月缴 (R)")
    p_payroll.add_argument("--beneficiaries", type=int, default=0, help="医疗援助受抚养人数")
    p_payroll.add_argument("--pension", type=float, default=0, help="养老金缴款比例 (%%)")
    p_payroll.add_argument("--travel", type=float, default=0, help="交通津贴月额 (R)")
    p_payroll.add_argument("--car-value", type=float, default=0, help="公司车价值 (R)")
    p_payroll.add_argument("--industry", default="office_low_risk",
                           choices=list(COIDA_EXAMPLE_RATES.keys()),
                           help="行业风险等级（影响COIDA费率）")
    p_payroll.add_argument("--headcount", type=int, default=1, help="员工人数（影响SDL）")

    # eti 子命令
    p_eti = subparsers.add_parser("eti", help="ETI 雇佣税激励计算")
    p_eti.add_argument("--age", type=int, required=True, help="员工年龄")
    p_eti.add_argument("--monthly", type=float, required=True, help="月工资 (R)")
    p_eti.add_argument("--first-year", action="store_true", help="第1年（60%%最高R1,500）")
    p_eti.add_argument("--second-year", action="store_true", help="第2年（30%%最高R750）")
    p_eti.add_argument("--sez", action="store_true", help="经济特区（不限年龄）")

    # severance 子命令
    p_sev = subparsers.add_parser("severance", help="遣散费计算（BCEA Section 41）")
    p_sev.add_argument("--monthly", type=float, required=True, help="月薪酬 (R)")
    p_sev.add_argument("--years", type=float, required=True, help="服务年数")

    # leave 子命令
    p_leave = subparsers.add_parser("leave", help="休假薪酬计算")
    p_leave.add_argument("--monthly", type=float, required=True, help="月薪酬 (R)")
    p_leave.add_argument("--days", type=float, required=True, help="休假天数")
    p_leave.add_argument("--work-days", type=int, default=21, help="每月工作日")

    # overtime 子命令
    p_ot = subparsers.add_parser("overtime", help="加班费计算")
    p_ot.add_argument("--hourly", type=float, required=True, help="时薪 (R)")
    p_ot.add_argument("--hours", type=float, required=True, help="加班小时数")
    p_ot.add_argument("--sunday", action="store_true", help="周日加班（2倍）")
    p_ot.add_argument("--holiday", action="store_true", help="公共假日加班（2倍）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "payroll":
        result = calc_payroll(
            monthly_basic=args.monthly, age=args.age,
            medical_aid=args.medical, medical_beneficiaries=args.beneficiaries,
            pension_rate=args.pension, travel_allowance=args.travel,
            company_car_value=args.car_value, industry=args.industry,
            headcount=args.headcount,
        )
    elif args.command == "eti":
        first_year = args.first_year and not args.second_year
        result = calc_eti(
            age=args.age, monthly_salary=args.monthly,
            first_year=first_year, special_economic_zone=args.sez,
        )
    elif args.command == "severance":
        result = calc_severance(args.monthly, args.years)
    elif args.command == "leave":
        result = calc_leave_pay(args.monthly, args.days, args.work_days)
    elif args.command == "overtime":
        result = calc_overtime(args.hourly, args.hours, args.sunday, args.holiday)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
