"""
eBay 账单数据提取脚本
用法: python ebay_duizhang.py <csv文件路径>

功能:
  1. 从元数据行提取 Start date / End date，转为 yyyy-MM-dd HH:mm:ss 格式
  2. 删除表头以上的元数据行，定位 Transaction creation date 所在行为真正表头
  3. 删除 Type 为 Payout、Hold 的数据
  4. 只保留 Order number、Net amount 两列，Order number 为空或 '--' 标记为 other
  5. 导出到原文件同目录 <原文件名>_明细.xlsx
"""

import sys
import os
import csv
import re
from datetime import datetime
from openpyxl import Workbook


def parse_ebay_date(raw):
    """解析 eBay 日期格式，返回 yyyy-MM-dd HH:mm:ss"""
    if not raw:
        return None
    raw = raw.strip()

    # 中文月份映射
    cn_months = {
        "1月": "Jan", "2月": "Feb", "3月": "Mar", "4月": "Apr",
        "5月": "May", "6月": "Jun", "7月": "Jul", "8月": "Aug",
        "9月": "Sep", "10月": "Oct", "11月": "Nov", "12月": "Dec",
    }
    for cn, en in cn_months.items():
        raw = raw.replace(cn, en)

    # 处理 上午/下午 → AM/PM
    raw = raw.replace("上午", "AM").replace("下午", "PM")

    # 去掉时区标识如 HKT、PST 等
    raw = re.sub(r'\s+[A-Z]{2,4}\s*$', '', raw)

    # 尝试多种格式
    formats = [
        "%b-%d-%Y %H:%M:%S %p",   # Mar-01-2026 00:00:00 AM
        "%b-%d-%Y %H:%M:%S",       # Mar-01-2026 00:00:00
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    return raw


def run(file_path):
    if not os.path.exists(file_path):
        print(f"[错误] 文件不存在: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)

    print(f"[读取] 共 {len(rows)} 行")

    # ── 1. 提取 Start date / End date ──
    start_time = None
    end_time = None
    header_row_idx = None

    for i, row in enumerate(rows):
        if len(row) >= 2:
            key = row[0].strip()
            if key == "Start date":
                start_time = parse_ebay_date(row[1])
            elif key == "End date":
                end_time = parse_ebay_date(row[1])
        # 定位真正表头行
        if len(row) > 0 and row[0].strip() == "Transaction creation date":
            header_row_idx = i
            break

    if header_row_idx is None:
        print("[错误] 未找到 'Transaction creation date' 表头行")
        sys.exit(1)

    print(f"[账期] start_time: {start_time}")
    print(f"[账期] end_time:   {end_time}")
    print(f"[表头] 第 {header_row_idx + 1} 行")

    # ── 2. 取表头及数据 ──
    header = rows[header_row_idx]
    data = rows[header_row_idx + 1:]

    # 查找列索引
    idx_type = None
    idx_order = None
    idx_net = None
    for j, h in enumerate(header):
        h = h.strip()
        if h == "Type":
            idx_type = j
        elif h == "Order number":
            idx_order = j
        elif h == "Net amount":
            idx_net = j

    for idx, label in [(idx_type, "Type"), (idx_order, "Order number"), (idx_net, "Net amount")]:
        if idx is None:
            print(f"[错误] 未找到列 '{label}'")
            sys.exit(1)

    # ── 3. 过滤 Payout / Hold，保留 Order number + Net amount ──
    results = []
    skipped = 0
    for row in data:
        if len(row) <= max(idx_type, idx_order, idx_net):
            continue
        t = row[idx_type].strip()
        if t in ("Payout", "Hold"):
            skipped += 1
            continue

        order_num = row[idx_order].strip()
        if not order_num or order_num == "--":
            order_num = "other"

        net = row[idx_net].strip().replace(",", "")
        try:
            net_val = float(net) if net and net != "--" else 0
        except (ValueError, TypeError):
            net_val = 0

        results.append({
            "order_number": order_num,
            "net_amount": net_val,
        })

    print(f"[过滤] 删除 Payout/Hold {skipped} 行，剩余 {len(results)} 行")

    # ── 4. 导出 Excel ──
    base, _ = os.path.splitext(file_path)
    output_path = base + "_明细.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "明细数据"
    ws.append(["start_time", start_time, "end_time", end_time])
    ws.append([])
    ws.append(["order_number", "net_amount"])
    for r in results:
        ws.append([r["order_number"], r["net_amount"]])

    wb.save(output_path)
    print(f"\n已导出明细：{output_path}")
    print(f"  账期：{start_time} ~ {end_time}")
    print(f"  明细行数：{len(results)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python ebay_duizhang.py <csv文件路径>")
        sys.exit(1)
    run(sys.argv[1])
