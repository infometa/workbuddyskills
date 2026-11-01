#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快递100 保价费计算器

用法：
    python quote_insurance.py --list
    python quote_insurance.py --brand 顺丰 --value 5000
    python quote_insurance.py --brand 京东重货 --value 3000 --weight 60
    python quote_insurance.py --brand 德邦 --value 20000 --fragile
    python quote_insurance.py --brand 顺丰 --value 500 --json

规则约定：
    - 声明价值区间取左开右闭 (lo, hi]，即 500 元落在 0-500 档。
    - 重量区间取 (lo, hi]，0kg 归入首档。
    - 费率档计算结果四舍五入保留两位小数（ROUND_HALF_UP）。
    - 费率档计算结果低于最低保费时，按最低保费收取。
    - 平费档（如「保费 1 元」）不再套用最低保费。
"""

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")

# 档位类型：
#   ("flat", 金额)           固定保费
#   ("rate", 费率)           按声明价值比例计费
# 最低保费：数字，或 [(lo, hi, 金额)] 按重量（kg）分档
RULES = {
    "顺丰": {
        "上限": None,
        "最低保费": None,
        "档位": [
            (0, 500, "flat", 1),
            (500, 1000, "flat", 2),
            (1000, None, "rate", 0.005),
        ],
        "备注": "1000 元以上按声明价值 × 0.005 计费",
    },
    "京东": {
        "上限": None,
        "最低保费": None,
        "档位": [
            (0, 500, "flat", 1),
            (500, 1000, "flat", 2),
            (1000, None, "rate", 0.005),
        ],
        "备注": "与顺丰同规则",
    },
    "EMS": {
        "上限": "30000",
        "最低保费": None,
        "档位": [
            (0, 300, "flat", 1),
            (300, None, "rate", 0.005),
        ],
        "备注": "单票保价上限 30000 元",
    },
    "申通": {
        "上限": "10000",
        "最低保费": None,
        "档位": [
            (0, 1000, "flat", 1),
            (1000, 2000, "flat", 2),
            (2000, None, "rate", 0.003),
        ],
        "备注": "单票保价上限 10000 元",
    },
    "圆通": {
        "上限": "30000",
        "最低保费": None,
        "档位": [
            (0, 1000, "flat", 1),
            (1000, 2000, "flat", 2),
            (2000, 10000, "rate", 0.003),
            (10000, None, "rate", 0.005),
        ],
        "备注": "单票保价上限 30000 元",
    },
    "极兔": {
        "上限": "30000",
        "最低保费": None,
        "档位": [
            (0, 1000, "flat", 1),
            (1000, 2000, "flat", 2),
            (2000, 10000, "rate", 0.003),
            (10000, None, "rate", 0.005),
        ],
        "备注": "与圆通同规则；单票保价上限 30000 元",
    },
    "菜鸟速递": {
        "上限": None,
        "最低保费": None,
        "档位": [
            (0, 500, "flat", 1),
            (500, 1000, "flat", 2),
            (1000, 10000, "rate", 0.003),
            (10000, None, "rate", 0.004),
        ],
        "备注": "10000 元以上按 0.004 计费",
    },
    "德邦": {
        "上限": "1000000",
        "最低保费": 1,
        "档位": [
            (0, 5000, "rate", 0.004),
            (5000, None, "rate", 0.005),
        ],
        "备注": "易碎易损类统一按 0.008 计费；单票保价上限 1000000 元",
        "易碎费率": 0.008,
    },
    "德邦零担": {
        "上限": None,
        "最低保费": 1,
        "档位": [
            (0, 2000, "flat", 0),
            (2000, None, "rate", 0.006),
        ],
        "备注": "2000 元以内保费 0 元；2000 元以上按 0.006 计费，最低保费 1 元",
    },
    "京东重货": {
        "上限": None,
        "最低保费": [(0, 40, 2), (40, 100, 4), (100, None, 12)],
        "档位": [
            (0, None, "rate", 0.006),
        ],
        "备注": "全段 0.006；最低保费按重量分档：≤40kg 收 2 元，40-100kg 收 4 元，>100kg 收 12 元",
        "需重量": True,
    },
    "顺丰卡航": {
        "上限": None,
        "最低保费": [(0, 40, 2), (40, 100, 4), (100, None, 12)],
        "档位": [
            (0, None, "rate", 0.006),
        ],
        "备注": "与京东重货同规则；最低保费按重量分档",
        "需重量": True,
    },
    "壹米滴答": {
        "上限": None,
        "最低保费": 3,
        "档位": [
            (0, None, "rate", 0.003),
        ],
        "备注": "全段 0.003，最低保费 3 元",
    },
    "中通快运": {
        "上限": None,
        "最低保费": 1,
        "档位": [
            (0, None, "rate", 0.004),
        ],
        "备注": "全段 0.004，最低保费 1 元",
    },
}

BRAND_ALIASES = {
    "顺丰速运": "顺丰",
    "顺丰快递": "顺丰",
    "京东快递": "京东",
    "京东物流": "京东",
    "京东快运": "京东重货",
    "中国邮政": "EMS",
    "邮政EMS": "EMS",
    "邮政": "EMS",
    "中通": "中通快运",
    "菜鸟": "菜鸟速递",
    "德邦快递": "德邦",
    "德邦物流": "德邦",
    "壹米": "壹米滴答",
}


def resolve_brand(name):
    name = (name or "").strip()
    if name in RULES:
        return name
    return BRAND_ALIASES.get(name)


def fmt(v):
    """去掉无意义的小数位：25.00 → 25，5.01 → 5.01"""
    d = Decimal(str(v)).quantize(CENT, rounding=ROUND_HALF_UP)
    if d == d.to_integral_value():
        return str(int(d))
    return str(d.normalize())


def span(lo, hi):
    lo = fmt(lo)
    if hi is None:
        return "%s 元以上" % lo
    return "%s-%s 元" % (lo, fmt(hi))


def min_fee_for(rule, weight):
    mf = rule.get("最低保费")
    if mf is None:
        return Decimal("0")
    if not isinstance(mf, list):
        return Decimal(str(mf))
    if weight is None:
        # 未给重量时按最低档兜底，并在输出中提示
        return Decimal(str(mf[0][2]))
    w = Decimal(str(weight))
    for lo, hi, fee in mf:
        if w > Decimal(str(lo)) and (hi is None or w <= Decimal(str(hi))):
            return Decimal(str(fee))
    return Decimal(str(mf[0][2]))


def pick_tier(rule, value):
    for lo, hi, kind, param in rule["档位"]:
        if value > Decimal(str(lo)) and (hi is None or value <= Decimal(str(hi))):
            return lo, hi, kind, param
    return None


def quote(brand, value, weight=None, fragile=False):
    key = resolve_brand(brand)
    if key is None:
        return {
            "ok": False,
            "error": "brand_not_found",
            "message": "未收录该品牌的保价费率，禁止估算，请引导用户走官方渠道核实。",
            "brand_input": brand,
        }

    rule = RULES[key]
    v = Decimal(str(value))

    cap = rule.get("上限")
    if cap and v > Decimal(cap):
        return {
            "ok": False,
            "error": "over_cap",
            "brand": key,
            "message": "声明价值 %s 元超出单票保价上限 %s 元，不可保价。" % (v, cap),
            "cap": cap,
        }

    if rule.get("需重量") and weight is None:
        weight_warning = "未提供重量，最低保费按 ≤40kg 档（2 元）估算；实际以重量档位为准。"
    else:
        weight_warning = None

    tier = pick_tier(rule, v)
    lo, hi, kind, param = tier

    if fragile and rule.get("易碎费率"):
        kind, param = "rate", rule["易碎费率"]
        tier_label = "易碎易损类专用费率 %s" % param
    elif kind == "flat":
        tier_label = "固定保费 %s 元（%s）" % (fmt(param), span(lo, hi))
    else:
        tier_label = "费率 %s（%s）" % (param, span(lo, hi))

    if kind == "flat":
        raw = Decimal(str(param))
        fee = raw
        floor_applied = False
        floor = Decimal("0")
        formula = "%s 元" % raw
    else:
        raw = (v * Decimal(str(param))).quantize(CENT, rounding=ROUND_HALF_UP)
        floor = min_fee_for(rule, weight)
        fee = max(raw, floor)
        floor_applied = fee > raw
        formula = "%s × %s = %s 元" % (v, param, raw)

    return {
        "ok": True,
        "brand": key,
        "declared_value": str(v),
        "tier": tier_label,
        "formula": formula,
        "raw_fee": str(raw),
        "min_fee": str(floor),
        "floor_applied": floor_applied,
        "final_fee": str(fee),
        "cap": cap,
        "note": rule.get("备注", ""),
        "weight": str(weight) if weight is not None else None,
        "warning": weight_warning,
    }


def render(r):
    if not r["ok"]:
        return "⛔ %s" % r["message"]
    lines = [
        "品牌：%s" % r["brand"],
        "声明价值：%s 元" % fmt(r["declared_value"]),
    ]
    if r.get("weight"):
        lines.append("重量：%s kg" % fmt(r["weight"]))
    lines.append("适用档位：%s" % r["tier"])
    lines.append("计算：%s" % r["formula"])
    if r["floor_applied"]:
        lines.append("触发最低保费：%s 元 → 按最低保费收取" % fmt(r["min_fee"]))
    lines.append("**保价费：%s 元**" % fmt(r["final_fee"]))
    if r["cap"]:
        lines.append("单票保价上限：%s 元" % fmt(r["cap"]))
    if r["note"]:
        lines.append("备注：%s" % r["note"])
    if r["warning"]:
        lines.append("⚠️ %s" % r["warning"])
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="快递100 保价费计算器")
    p.add_argument("--brand", help="快递品牌，如 顺丰 / 京东重货 / 德邦")
    p.add_argument("--value", help="声明价值（元）")
    p.add_argument("--weight", help="重量（kg），京东重货 / 顺丰卡航 必填")
    p.add_argument("--fragile", action="store_true", help="易碎易损类（仅德邦生效）")
    p.add_argument("--json", action="store_true", help="以 JSON 输出")
    p.add_argument("--list", action="store_true", help="列出已收录品牌")
    args = p.parse_args()

    if args.list:
        for name, rule in RULES.items():
            cap = rule.get("上限")
            print("%-8s %s%s" % (name, rule.get("备注", ""), ("；上限 %s 元" % cap) if cap else ""))
        return 0

    if not args.brand or args.value is None:
        p.error("需同时提供 --brand 与 --value")

    try:
        value = Decimal(str(args.value))
        if value <= 0:
            raise ValueError
    except Exception:
        p.error("--value 必须是大于 0 的数字")

    try:
        weight = Decimal(str(args.weight)) if args.weight is not None else None
    except Exception:
        p.error("--weight 必须是数字")

    result = quote(args.brand, value, weight, args.fragile)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
