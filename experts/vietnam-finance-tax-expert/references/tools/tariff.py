# -*- coding: utf-8 -*-
"""
越南进口关税测算器 v1.0
Vietnam Import Tariff Calculator

计算进口环节税费：进口关税 + 增值税(VAT 10%) + 特别消费税(SCT，如适用)。
基于 data/tariff_reference.json 的大类指示税率。

用法：
  python tariff.py --cif 100_000_000 --category raw_material
  python tariff.py --cif 200_000_000 --category finished_goods
  python tariff.py --cif 500_000_000 --category vehicle

金额单位：越南盾 VND。CIF = 货值+运费+保险费。
"""

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data", "tariff_reference.json")


def _load():
    with open(DATA, "r", encoding="utf-8") as f:
        return json.load(f)


def calc(cif, category, vat_override=None):
    d = _load()
    cats = d["categories"]
    if category not in cats:
        raise ValueError(f"未知类别 {category}，可选：{', '.join(cats.keys())}")
    c = cats[category]
    duty_rate = c["import_duty_pct"] / 100.0
    sct_rate = c["special_consumption_pct"] / 100.0
    vat_rate = (vat_override if vat_override is not None else d["vat_pct"]) / 100.0

    duty = cif * duty_rate
    # 特别消费税计税基 = (CIF + 关税)
    sct = (cif + duty) * sct_rate
    # 增值税计税基 = CIF + 关税 + 特别消费税
    vat = (cif + duty + sct) * vat_rate
    total_tax = duty + sct + vat
    return {
        "currency": "VND",
        "category": c["name_zh"],
        "cif_VND": round(cif),
        "import_duty_pct": c["import_duty_pct"],
        "import_duty_VND": round(duty),
        "special_consumption_pct": c["special_consumption_pct"],
        "special_consumption_VND": round(sct),
        "vat_pct": round(vat_rate * 100, 1),
        "vat_VND": round(vat),
        "total_import_tax_VND": round(total_tax),
        "tax_as_pct_of_cif": round(total_tax / cif * 100, 1),
        "landed_cost_VND": round(cif + total_tax),
        "note": c["note"],
    }


def main():
    p = argparse.ArgumentParser(description="越南进口关税测算器")
    p.add_argument("--cif", type=float, required=True, help="CIF 货值 VND")
    p.add_argument("--category", type=str, required=True, help="类别key（见 tariff_reference.json）")
    p.add_argument("--vat", type=float, default=None, help="覆盖VAT税率%")
    args = p.parse_args()

    r = calc(args.cif, args.category, args.vat)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print(f"\n[解读] {r['category']}：CIF {r['cif_VND']:,} VND，"
          f"进口环节税合计 {r['total_import_tax_VND']:,} VND"
          f"（占货值 {r['tax_as_pct_of_cif']}%），落地总成本 {r['landed_cost_VND']:,} VND。")
    print(f"  说明：{r['note']}")


if __name__ == "__main__":
    main()
