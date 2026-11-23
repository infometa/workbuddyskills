"""
Walmart 账单数据提取脚本

用法: python walmart_duizhang.py <csv或xlsx文件路径> [--sheet NAME]

功能:
  1. 识别结算数据所在 sheet（自动识别，一般叫“结算单”，不在第一个 sheet 也支持）
  2. 按账期切分：Total Payable 为数字的行作为账期汇总行，
     其后 Transaction Key 不为空的行归属于该账期（一个文件可含多个账期）
  3. 输出订单明细到原文件同目录下 <原文件名>_订单明细.xlsx（带账期列）
"""

import argparse
import os
import sys

from openpyxl import Workbook

import walmart_source as ws


def run(file_path, sheet=None):
    candidates = ws.probe_sheets(file_path)
    chosen, _certain = ws.choose_sheet(candidates, preferred=sheet)
    if chosen is None:
        if sheet is not None:
            raise ValueError(f"sheet 不存在或缺少必需列: {sheet}；"
                             f"文件中的 sheet：{ws.list_sheet_names(file_path)}")
        raise ValueError("未找到包含结算单必需列的 sheet："
                         f"{[c['sheet'] for c in candidates]}；可用 --sheet 指定")

    print(f"[1/2] 读取文件: {file_path}")
    print(f"      结算 sheet：{chosen['sheet']!r}"
          f"（表头第 {chosen['header_index'] + 1} 行），"
          f"候选：{[c['sheet'] for c in candidates if c['usable']]}")

    rows = ws.read_rows(file_path, chosen["sheet"])
    blocks = ws.parse_blocks(rows, chosen["header_index"])
    blocks = [b for b in blocks if b.details]
    if not blocks:
        raise ValueError(f"未在 sheet {chosen['sheet']!r} 中解析出账期与订单明细，"
                         f"请确认文件内容或用 --sheet 指定")

    for block in blocks:
        print(f"      {block.period}  明细 {len(block.details)} 行 / "
              f"{len(block.amount_summary())} 个订单")

    # ── 导出订单明细 ──
    base, _ = os.path.splitext(file_path)
    output_path = base + "_订单明细.xlsx"

    wb = Workbook()
    worksheet = wb.active
    worksheet.title = "订单明细"
    worksheet.append(["结算 sheet", chosen["sheet"], "账期数", len(blocks),
                      "明细行数", sum(len(b.details) for b in blocks)])
    worksheet.append([])
    for block in blocks:
        worksheet.append(["账期", block.period, "Total Payable", block.total_payable,
                          "明细行数", len(block.details)])
    worksheet.append([])
    worksheet.append(["账期", "transaction_key", "purchase_order", "amount", "amount_type"])
    for block in blocks:
        for detail in block.details:
            worksheet.append([block.period, detail["transaction_key"],
                              detail["purchase_order"], detail["amount"],
                              detail["amount_type"]])
    wb.save(output_path)

    print(f"\n[2/2] 已导出订单明细：{output_path}")
    print(f"      账期数：{len(blocks)}，明细行数：{sum(len(b.details) for b in blocks)}")


def main():
    parser = argparse.ArgumentParser(description="Walmart 账单数据提取")
    parser.add_argument("file", help="Walmart 结算 CSV 或 XLSX 文件路径")
    parser.add_argument("--sheet", default=None,
                        help="结算数据所在 sheet 名称，默认自动识别（一般叫“结算单”）")
    args = parser.parse_args()

    try:
        run(args.file, sheet=args.sheet)
    except (ValueError, FileNotFoundError) as e:
        print(f"\n[错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
