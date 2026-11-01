#!/usr/bin/env python3
"""扫呗数电票金额换算与汇总计算工具（唯一权威计算入口）。

⚠️ 存在的理由：接口所有金额字段单位是「分」，历史上出现过把它当「元」
直接展示、导致金额放大 100 倍的事故。本脚本把换算固化下来，
**禁止心算、禁止手工除以 100**，一律调用本脚本。

用法一：汇总发票明细（推荐）
    输入：接口 invoice_getInvoiceList 返回的 invoice_list（JSON 字符串或数组）
    命令：python calc_amount.py list '<invoice_list JSON>'
    输出：开票数量 / 开票金额 / 有效开票金额 / 蓝票 / 红票（单位：元）

用法二：直接换算汇总接口的金额字段
    命令：python calc_amount.py fields <total_amount> <normal_amount> <refund_amount> [total_count normal_count refund_count]
    输出：换算后的元值 + 派生有效开票金额

用法三：单张金额换算
    命令：python calc_amount.py one <total_fee>
    输出：¥金额

设计约束：
  - 仅使用 Python 标准库
  - 只做计算与打印，不联网、不读写业务文件
  - 金额一律以 Decimal 处理，避免浮点误差
  - 有效开票金额 = |蓝票| - |红票|，红票取绝对值后再相减
"""

import json
import sys
from decimal import Decimal, ROUND_HALF_UP


def to_yuan(cents) -> str:
    """分 → 元，保留两位小数，四舍五入。"""
    return str(
        (Decimal(str(cents)) / Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    )


def build_summary(records):
    """由明细记录列表计算汇总。

    蓝票判定用 invoice_type == 0，红票用 invoice_type == 1；
    金额取 total_fee（单位：分）。
    """
    blue_count = 0
    red_count = 0
    blue_cents = 0
    red_cents = 0

    for r in records:
        fee = r.get("total_fee")
        if fee is None:
            continue
        fee = int(fee)
        if r.get("invoice_type") == 1:  # 红票
            red_count += 1
            red_cents += abs(fee)
        else:  # 蓝票
            blue_count += 1
            blue_cents += abs(fee)

    total_count = len(records)
    total_cents = blue_cents + red_cents          # 开票金额：各张绝对值累加
    effective_cents = blue_cents - red_cents       # 有效开票金额：|蓝| - |红|

    return {
        "开票数量": f"{total_count}张",
        "开票金额": f"¥{to_yuan(total_cents)}",
        "有效开票金额": f"¥{to_yuan(effective_cents)}",
        "蓝票（正常开具）": f"{blue_count}张，¥{to_yuan(blue_cents)}",
        "红票（红冲）": f"{red_count}张，¥{to_yuan(red_cents)}",
    }


def cmd_list(raw):
    records = json.loads(raw)
    if isinstance(records, dict):
        records = records.get("invoice_list", [])
        if isinstance(records, str):
            records = json.loads(records)
    summary = build_summary(records)
    print("单位：元（接口原始值单位为分，已 ÷100）")
    for k, v in summary.items():
        print(f"{k}：{v}")
    print()
    print("输出模板：")
    for k, v in summary.items():
        print(f"{k}：{v}")


def cmd_fields(total_amount, normal_amount, refund_amount, *extra):
    total_count, normal_count, refund_count = (list(extra) + [None] * 3)[:3]
    blue = abs(int(normal_amount))
    red = abs(int(refund_amount))
    print("单位：元（接口原始值单位为分，已 ÷100）")
    if total_count is not None:
        print(f"开票数量：{int(total_count)}张")
    print(f"开票金额：¥{to_yuan(blue + red)}")
    print(f"有效开票金额：¥{to_yuan(blue - red)}")
    print(f"蓝票（正常开具）：¥{to_yuan(blue)}")
    print(f"红票（红冲）：¥{to_yuan(red)}")
    print()
    print(f"参考：接口 total_amount 原始值 {total_amount}（{to_yuan(total_amount)}），"
          f"该字段为带符号净值口径 = normal + refund，不等于上面的「开票金额」。")


def cmd_one(total_fee):
    fee = int(total_fee)
    print(f"¥{to_yuan(abs(fee))}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    mode = sys.argv[1]
    if mode == "list":
        if len(sys.argv) < 3:
            print("用法：python calc_amount.py list '<invoice_list JSON>'")
            return 2
        cmd_list(sys.argv[2])
    elif mode == "fields":
        if len(sys.argv) < 5:
            print("用法：python calc_amount.py fields <total_amount> <normal_amount> "
                  "<refund_amount> [total_count normal_count refund_count]")
            return 2
        cmd_fields(*sys.argv[2:])
    elif mode == "one":
        if len(sys.argv) < 3:
            print("用法：python calc_amount.py one <total_fee>")
            return 2
        cmd_one(sys.argv[2])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
