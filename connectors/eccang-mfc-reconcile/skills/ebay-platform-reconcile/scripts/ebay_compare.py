"""
eBay 对账比对脚本（数据通过 nexus-mcp 获取，不直连数据库）

用法:
  python ebay_compare.py <csv文件路径> [选项]

流程:
  1. 读取 CSV，提取 Start date/End date，过滤 Payout/Hold，按 Order number 汇总 Net amount
  2. 取一个有效 Order number 调用 MCP 工具 queryOrderByReferenceNo 获取 companyCode / userAccount / platform
  3. 调用 MCP 工具 queryProfitSettlement 查询账期结算利润明细
  4. 按 Order number (Excel) vs orderId (MCP) 汇总比对，输出结果并导出 Excel
"""

import argparse
import sys
import os
import csv
import re
from collections import defaultdict
from datetime import datetime

from ebay_mcp import (
    McpClient, McpError,
    TOOL_QUERY_ORDER, TOOL_QUERY_PROFIT_SETTLEMENT,
)

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
except ImportError:
    print("[错误] 缺少依赖: pip install openpyxl")
    sys.exit(1)

TOLERANCE = 0.01
STATUS_CANCELLED = "订单已作废"
# 与原 SQL 口径一致：仅这三种对账结果参与比对（source_type=1 由 MCP 服务端过滤）
ALLOWED_CHECK_RESULTS = ("匹配到订单", "订单已作废", "对账成功")


# ── 工具函数 ──────────────────────────────────────────────────────────────

def parse_ebay_date(raw):
    """解析 eBay 日期格式，返回 yyyy-MM-dd HH:mm:ss"""
    if not raw:
        return None
    raw = raw.strip()
    cn_months = {
        "1月": "Jan", "2月": "Feb", "3月": "Mar", "4月": "Apr",
        "5月": "May", "6月": "Jun", "7月": "Jul", "8月": "Aug",
        "9月": "Sep", "10月": "Oct", "11月": "Nov", "12月": "Dec",
    }
    for cn, en in cn_months.items():
        raw = raw.replace(cn, en)
    raw = raw.replace("上午", "AM").replace("下午", "PM")
    raw = re.sub(r'\s+[A-Z]{2,4}\s*$', '', raw)
    for fmt in ("%b-%d-%Y %H:%M:%S %p", "%b-%d-%Y %H:%M:%S",
                "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return raw


def is_interactive():
    """当前是否为可交互终端"""
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except (ValueError, AttributeError):
        return False


# ── 核心步骤 ──────────────────────────────────────────────────────────────

def load_data(file_path):
    """读取 CSV，返回 (excel_summary, start_time, end_time, sample_order)
    excel_summary: {order_number: total_net_amount}  (不含 other)
    """
    if not os.path.exists(file_path):
        print(f"[错误] 文件不存在: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)

    print(f"      读取 {len(rows)} 行")

    # 提取 Start date / End date，定位表头行
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
        if len(row) > 0 and row[0].strip() == "Transaction creation date":
            header_row_idx = i
            break

    if header_row_idx is None:
        print("[错误] 未找到 'Transaction creation date' 表头行")
        sys.exit(1)
    if start_time is None or end_time is None:
        print("[错误] 未找到 Start date / End date")
        sys.exit(1)

    header = rows[header_row_idx]
    data = rows[header_row_idx + 1:]

    # 查找列索引
    idx_type = idx_order = idx_net = None
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

    # 过滤 Payout/Hold，按 Order number 汇总
    summary = defaultdict(float)
    other_count = 0
    sample_order = None

    for row in data:
        if len(row) <= max(idx_type, idx_order, idx_net):
            continue
        t = row[idx_type].strip()
        if t in ("Payout", "Hold"):
            continue

        order_num = row[idx_order].strip()
        net = row[idx_net].strip().replace(",", "")
        try:
            net_val = float(net) if net and net != "--" else 0
        except (ValueError, TypeError):
            net_val = 0

        if not order_num or order_num == "--":
            order_num = "other"
            other_count += 1

        summary[order_num] += net_val
        if sample_order is None and order_num != "other":
            sample_order = order_num

    if other_count > 0:
        print(f"      Order number 为空的行: {other_count} 行，金额合计: {summary.get('other', 0):,.2f}（归入 other）")

    return summary, start_time, end_time, sample_order


# ── MCP 数据获取 ──────────────────────────────────────────────────────────

def query_order_info(client, order_id):
    """通过 MCP 工具 queryOrderByReferenceNo 查询订单归属"""
    rows = client.call_tool(TOOL_QUERY_ORDER, {"orderId": order_id})
    if not rows:
        return None
    first = rows[0]
    return {
        "company_code": first.get("companyCode"),
        "user_account": first.get("userAccount"),
        "platform": first.get("platform"),
    }


def query_settlement_data(client, company_code, user_account, platform, start_time, end_time):
    """通过 MCP 工具 queryProfitSettlement 查询结算利润明细

    返回 (summary, rows)：
      summary: {order_id: {'fee_amount': float, 'status': str}}，空 orderId 归为 other
      rows:    原始明细行列表（供单订单复核使用）
    口径与原 SQL 一致：仅 ALLOWED_CHECK_RESULTS 三种状态参与比对；同一订单
    多种状态时优先取非「订单已作废」的记录并累加。
    """
    rows = client.call_tool(TOOL_QUERY_PROFIT_SETTLEMENT, {
        "companyCode": company_code,
        "userAccount": user_account,
        "platform": platform,
        "startTime": start_time,
        "endTime": end_time,
    })
    if rows is None:
        rows = []

    result = {}
    for row in rows:
        status = str(row.get("accountCheckResult") or "未知")
        if status not in ALLOWED_CHECK_RESULTS:
            continue
        order_id = str(row.get("orderId") or "").strip() or "other"
        try:
            fee = float(row.get("settlementAmount") or 0)
        except (ValueError, TypeError):
            fee = 0.0

        if order_id in result:
            if status != STATUS_CANCELLED and result[order_id]['status'] == STATUS_CANCELLED:
                result[order_id] = {'fee_amount': fee, 'status': status}
            elif status != STATUS_CANCELLED:
                result[order_id]['fee_amount'] += fee
        else:
            result[order_id] = {'fee_amount': fee, 'status': status}
    return result, rows


def query_order_fee_amount(rows, order_id):
    """从已获取的结算明细中复核单订单金额（accountCheckResult='匹配到订单'）

    对应原实现中的单订单 SQL 确认；数据已在账期查询时取回，无需二次请求。
    """
    total = 0.0
    found = False
    for row in rows:
        if str(row.get("orderId") or "").strip() != order_id:
            continue
        if str(row.get("accountCheckResult") or "") != "匹配到订单":
            continue
        try:
            total += float(row.get("settlementAmount") or 0)
        except (ValueError, TypeError):
            pass
        found = True
    return total if found else None


def resolve_owner(client, sample_order, company_code, user_account, platform, assume_yes):
    """确定对账主体：显式传入优先，否则通过 MCP 查询订单归属并与用户确认"""
    if company_code and user_account:
        resolved_platform = platform or "ebay"
        print(f"[2/4] 使用指定的客户/店铺：客户={company_code}，店铺={user_account}，"
              f"平台={resolved_platform}")
        return company_code, user_account, resolved_platform

    if not sample_order:
        raise McpError("未从 CSV 中提取到有效 Order number，无法查询订单归属，"
                       "请使用 --company-code / --user-account 手动指定")

    print(f"[2/4] 查询订单归属（MCP 工具 {TOOL_QUERY_ORDER}，refrence_no={sample_order}）")
    info = query_order_info(client, sample_order)
    if not info:
        raise McpError(f"订单号 {sample_order} 在 MCP 中未找到对应记录，"
                       f"请使用 --company-code / --user-account 手动指定")

    company_code = info["company_code"]
    user_account = info["user_account"]
    platform = info["platform"]
    print(f"      查询结果 → 客户：{company_code}，店铺：{user_account}，平台：{platform}")

    if assume_yes or not is_interactive():
        print("      已跳过人工确认（非交互环境）；如需指定请使用 "
              "--company-code / --user-account / --platform")
        return company_code, user_account, platform

    while True:
        confirm = input("\n请确认以上客户和店铺信息是否正确？(y=正确继续 / n=手动输入): ").strip().lower()
        if confirm == "y":
            return company_code, user_account, platform
        elif confirm == "n":
            company_code = input("  请输入正确的客户(company_code): ").strip()
            user_account = input("  请输入正确的店铺(user_account): ").strip()
            platform = input("  请输入正确的平台(platform) [默认ebay]: ").strip() or "ebay"
            print(f"      已更新 → 客户：{company_code}，店铺：{user_account}，平台：{platform}")
            confirm2 = input("确认这次输入正确吗？(y=正确继续 / n=重新输入): ").strip().lower()
            if confirm2 == "y":
                return company_code, user_account, platform
        else:
            print("      请输入 y 或 n")


def compare_and_output(excel_summary, db_summary, rows, company_code, user_account,
                       start_time, end_time, file_path, platform=None):
    """比对两份数据，输出最终结果并导出 Excel
    db_summary 格式: {order_id: {'fee_amount': float, 'status': str}}
    """
    # 提取 db 金额用于计算
    db_amounts = {k: v['fee_amount'] for k, v in db_summary.items()}

    excel_total = sum(excel_summary.values())
    db_total = sum(db_amounts.values())
    settled_time = f"{start_time} ~ {end_time}"

    all_ids = set(excel_summary.keys()) | set(db_amounts.keys())
    diffs = []
    matched = []
    cancelled = []  # 作废订单列表

    for oid in all_ids:
        ev = excel_summary.get(oid)
        dv = db_amounts.get(oid)
        status = db_summary.get(oid, {}).get('status', '')

        if ev is None:
            diffs.append((oid, ev, dv, "仅在结算利润中", status))
        elif dv is None:
            if abs(ev) < TOLERANCE:
                matched.append((oid, ev, dv, "忽略(金额为0)", status))
                continue
            if oid == "other":
                diffs.append((oid, ev, dv, "仅在Excel中(MCP无记录)", status))
            else:
                db_fee = query_order_fee_amount(rows, oid)
                if db_fee is not None:
                    diffs.append((oid, ev, db_fee, "金额不一致", status))
                else:
                    diffs.append((oid, ev, dv, "仅在Excel中(MCP无记录)", status))
        elif abs(ev - dv) > TOLERANCE:
            diffs.append((oid, ev, dv, "金额不一致", status))
        else:
            # 金额匹配，检查是否为作废订单
            if status == STATUS_CANCELLED:
                cancelled.append((oid, ev, dv, STATUS_CANCELLED, status))
            else:
                matched.append((oid, ev, dv, "匹配", status))

    cancelled_count = len(cancelled)

    # 输出汇总信息表
    print("\n" + "=" * 70)
    print(f"{'项目':<16}\t{'值'}")
    print("-" * 40)
    print(f"{'客户':<16}\t{company_code}")
    print(f"{'店铺':<16}\t{user_account}")
    print(f"{'平台':<16}\t{platform}")
    print(f"{'对账时间':<16}\t{settled_time}")
    print(f"{'Excel订单数':<16}\t{len(excel_summary)}")
    print(f"{'MCP订单数':<15}\t{len(db_amounts)}")
    print(f"{'Excel总金额':<16}\t{excel_total:,.2f}")
    print(f"{'MCP总金额':<15}\t{db_total:,.2f}")
    if cancelled_count > 0:
        print(f"{'订单已作废':<16}\t{cancelled_count} 条")
    print(f"{'差异':<16}\t{len(diffs)} 条")
    print(f"{'匹配结果':<16}\t{'完全一致' if not diffs else '有差异'}")
    print("=" * 70)

    # 输出作废订单明细
    if cancelled:
        print(f"\n订单已作废（共 {cancelled_count} 条）：")
        print(f"{'order_id':<36} {'金额':>18}")
        print("-" * 60)
        for oid, ev, dv, note, status in sorted(cancelled):
            print(f"{oid:<36} {ev:>18,.2f}")
        print("=" * 70)

    # 输出差异明细
    if diffs:
        print(f"\n差异明细（共 {len(diffs)} 条）：")
        print(f"{'order_id':<36} {'excel_fee_amount':>18} {'mcp_fee_amount':>16} {'备注'}")
        print("-" * 90)
        for oid, ev, dv, note, status in sorted(diffs):
            es = f"{ev:,.2f}" if ev is not None else "—"
            ds = f"{dv:,.2f}" if dv is not None else "—"
            print(f"{oid:<36} {es:>18} {ds:>16} {note}")
        print("=" * 70)

    # 导出比对结果到 Excel
    base, _ = os.path.splitext(file_path)
    output_path = base + "_比对结果.xlsx"
    out_wb = Workbook()

    # 样式定义
    header_font_white = Font(bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center')
    right_align = Alignment(horizontal='right', vertical='center')
    money_format = '#,##0.00'
    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    yellow_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

    # Sheet1: 汇总信息
    ws_info = out_wb.active
    ws_info.title = "汇总信息"
    ws_info.append(["项目", "值"])
    ws_info.append(["客户", company_code])
    ws_info.append(["店铺", user_account])
    ws_info.append(["平台", platform])
    ws_info.append(["对账时间", settled_time])
    ws_info.append(["Excel订单数", len(excel_summary)])
    ws_info.append(["MCP订单数", len(db_amounts)])
    ws_info.append(["Excel总金额", excel_total])
    ws_info.append(["MCP总金额", db_total])
    if cancelled_count > 0:
        ws_info.append(["订单已作废", cancelled_count])
    ws_info.append(["差异条数", len(diffs)])
    ws_info.append(["匹配结果", "完全一致" if not diffs else "有差异"])

    # 汇总信息样式
    ws_info.column_dimensions['A'].width = 15
    ws_info.column_dimensions['B'].width = 40
    for row in ws_info.iter_rows(min_row=1, max_row=1, min_col=1, max_col=2):
        for cell in row:
            cell.font = header_font_white
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center_align
    for row in ws_info.iter_rows(min_row=2, max_row=ws_info.max_row, min_col=1, max_col=2):
        for cell in row:
            cell.border = border
            if cell.column == 1:
                cell.font = Font(bold=True)
            cell.alignment = Alignment(vertical='center')
    # 金额格式
    ws_info['B8'].number_format = money_format
    ws_info['B9'].number_format = money_format
    # 匹配结果颜色
    result_cell = ws_info['B' + str(11 + (1 if cancelled_count > 0 else 0))]
    if "完全一致" in str(result_cell.value):
        result_cell.fill = green_fill
    else:
        result_cell.fill = red_fill

    # Sheet2: 差异明细
    ws_diff = out_wb.create_sheet("差异明细")
    ws_diff.append(["客户", company_code, "店铺", user_account, "对账时间", settled_time])
    ws_diff.append(["Excel订单数", len(excel_summary), "MCP订单数", len(db_amounts),
                    "Excel总金额", excel_total, "MCP总金额", db_total])
    ws_diff.append(["差异条数", len(diffs), "匹配结果", "完全一致" if not diffs else "有差异"])
    ws_diff.append([])
    ws_diff.append(["order_id", "excel_fee_amount", "mcp_fee_amount", "备注"])
    for item in sorted(diffs):
        oid, ev, dv, note, status = item
        ws_diff.append([oid, ev, dv, note])

    # 差异明细样式
    ws_diff.column_dimensions['A'].width = 38
    ws_diff.column_dimensions['B'].width = 18
    ws_diff.column_dimensions['C'].width = 18
    ws_diff.column_dimensions['D'].width = 25
    # 汇总行
    for row in ws_diff.iter_rows(min_row=1, max_row=3, min_col=1, max_col=6):
        for cell in row:
            cell.border = border
    # 表头
    for row in ws_diff.iter_rows(min_row=5, max_row=5, min_col=1, max_col=4):
        for cell in row:
            cell.font = header_font_white
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center_align
    # 数据行
    for row in ws_diff.iter_rows(min_row=6, max_row=ws_diff.max_row, min_col=1, max_col=4):
        for cell in row:
            cell.border = border
            if cell.column in [2, 3]:
                cell.number_format = money_format
                cell.alignment = right_align
            elif cell.column == 4:
                cell.alignment = Alignment(vertical='center')

    # Sheet3: 订单已作废
    if cancelled:
        ws_cancel = out_wb.create_sheet("订单已作废")
        ws_cancel.append(["客户", company_code, "店铺", user_account, "对账时间", settled_time])
        ws_cancel.append(["作废订单数", cancelled_count])
        ws_cancel.append([])
        ws_cancel.append(["order_id", "金额"])
        for item in sorted(cancelled):
            oid, ev, dv, note, status = item
            ws_cancel.append([oid, ev])

        ws_cancel.column_dimensions['A'].width = 38
        ws_cancel.column_dimensions['B'].width = 18
        for row in ws_cancel.iter_rows(min_row=1, max_row=2, min_col=1, max_col=6):
            for cell in row:
                cell.border = border
        for row in ws_cancel.iter_rows(min_row=4, max_row=4, min_col=1, max_col=2):
            for cell in row:
                cell.font = header_font_white
                cell.fill = header_fill
                cell.border = border
                cell.alignment = center_align
        for row in ws_cancel.iter_rows(min_row=5, max_row=ws_cancel.max_row, min_col=1, max_col=2):
            for cell in row:
                cell.border = border
                if cell.column == 2:
                    cell.number_format = money_format
                    cell.alignment = right_align
                    cell.fill = yellow_fill

    # Sheet4: 全量比对
    ws_all = out_wb.create_sheet("全量比对")
    ws_all.append(["客户", company_code, "店铺", user_account, "对账时间", settled_time])
    ws_all.append(["Excel订单数", len(excel_summary), "MCP订单数", len(db_amounts),
                    "Excel总金额", excel_total, "MCP总金额", db_total])
    ws_all.append(["差异条数", len(diffs), "匹配条数", len(matched), "作废订单", cancelled_count])
    ws_all.append([])
    ws_all.append(["order_id", "excel_fee_amount", "mcp_fee_amount", "状态"])
    # 合并匹配+作废+差异
    all_items = [(oid, ev, dv, note, status) for oid, ev, dv, note, status in matched]
    all_items += [(oid, ev, dv, note, status) for oid, ev, dv, note, status in cancelled]
    all_items += [(oid, ev, dv, note, status) for oid, ev, dv, note, status in diffs]
    for item in sorted(all_items, key=lambda x: x[0]):
        oid, ev, dv, note, status = item
        ws_all.append([oid, ev, dv, note])

    # 全量比对样式
    ws_all.column_dimensions['A'].width = 38
    ws_all.column_dimensions['B'].width = 18
    ws_all.column_dimensions['C'].width = 18
    ws_all.column_dimensions['D'].width = 15
    # 汇总行
    for row in ws_all.iter_rows(min_row=1, max_row=3, min_col=1, max_col=8):
        for cell in row:
            cell.border = border
    # 表头
    for row in ws_all.iter_rows(min_row=5, max_row=5, min_col=1, max_col=4):
        for cell in row:
            cell.font = header_font_white
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center_align
    # 数据行
    for row in ws_all.iter_rows(min_row=6, max_row=ws_all.max_row, min_col=1, max_col=4):
        for cell in row:
            cell.border = border
            if cell.column in [2, 3]:
                cell.number_format = money_format
                cell.alignment = right_align
            elif cell.column == 4:
                cell.alignment = Alignment(vertical='center')
                # 根据状态着色
                if cell.value == "匹配":
                    cell.fill = green_fill
                elif cell.value == STATUS_CANCELLED:
                    cell.fill = yellow_fill
                elif cell.value and ("差异" in str(cell.value) or "仅在" in str(cell.value)
                                     or "不一致" in str(cell.value)):
                    cell.fill = red_fill

    out_wb.save(output_path)
    print(f"\n已导出比对结果：{output_path}")


# ── 入口 ──────────────────────────────────────────────────────────────────

def run(file_path, mcp_url=None, company_code=None, user_account=None,
        platform=None, assume_yes=False):
    print(f"[1/4] 读取文件: {file_path}")
    excel_summary, start_time, end_time, sample_order = load_data(file_path)
    print(f"      {len(excel_summary)} 个 Order number，账期：{start_time} ~ {end_time}，样本订单：{sample_order}")

    client = McpClient(url=mcp_url)
    print(f"      MCP 地址：{client.url}")

    company_code, user_account, platform = resolve_owner(
        client, sample_order, company_code, user_account, platform, assume_yes)

    print(f"\n[3/4] 查询结算利润明细（MCP 工具 {TOOL_QUERY_PROFIT_SETTLEMENT}）")
    print(f"      条件：companyCode={company_code}, userAccount={user_account}, platform={platform}")
    print(f"      statement_time >= {start_time}, statement_time <= {end_time}")
    db_summary, rows = query_settlement_data(
        client, company_code, user_account, platform, start_time, end_time)
    print(f"      结算利润明细共 {len(db_summary)} 个订单（原始记录 {len(rows)} 条）")

    print(f"[4/4] 比对数据")
    compare_and_output(excel_summary, db_summary, rows, company_code, user_account,
                       start_time, end_time, file_path, platform=platform)


def main():
    parser = argparse.ArgumentParser(
        description="eBay 结算单对账（数据通过 nexus-mcp 获取）")
    parser.add_argument("file", help="eBay Transaction Report CSV 文件路径")
    parser.add_argument("--mcp-url", default=None,
                        help="nexus-mcp 地址，默认取环境变量 NEXUS_MCP_URL，"
                             "再默认 https://datacenter.eccang.com/nexus/mcp/stream")
    parser.add_argument("--company-code", default=None, help="客户编码")
    parser.add_argument("--user-account", default=None, help="店铺账号")
    parser.add_argument("--platform", default=None, help="平台，默认 ebay")
    parser.add_argument("-y", "--yes", action="store_true", help="跳过人工确认")
    args = parser.parse_args()

    try:
        run(args.file, mcp_url=args.mcp_url,
            company_code=args.company_code, user_account=args.user_account,
            platform=args.platform, assume_yes=args.yes)
    except (McpError, ValueError, FileNotFoundError) as e:
        print(f"\n[错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
