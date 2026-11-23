"""
Walmart 对账比对脚本

用法:
    python walmart_compare.py <csv或xlsx文件路径> [选项]

选项:
    --sheet NAME        指定结算数据所在 sheet（默认自动识别，一般叫“结算单”）
    --list-sheets       只列出各 sheet 的探测结果，不做对账
    --mcp-url URL       nexus-mcp 地址，默认取环境变量 NEXUS_MCP_URL，
                        再默认 http://datacenter.eccang.com/nexus/mcp/stream
                        （本地联调示例：--mcp-url http://127.0.0.1:8070/nexus/mcp/stream）
    --company-code C    客户编码，与 --user-account 一起指定时跳过 MCP 订单归属查询与人工确认
    --user-account U    店铺账号
    --platform P        平台，默认 walmart
    -y, --yes           跳过人工确认（非交互环境必用）

流程:
  1. 识别结算数据所在 sheet（不在第一个 sheet 时会提示确认；确认后仍无法对账则自动换其它 sheet）
  2. 按账期切分结算块（一个 sheet 可包含多个账期，全部纳入对账）
  3. 每个账期调用 MCP 工具 queryProfitSettlement 查询结算利润明细
  4. 逐账期比对 Purchase Order # (Excel) vs orderId (MCP)，得到逐期差异明细（统计与定位用）
  5. 按订单跨账期合并后比对，得出真实差异：同一订单可能出现在多个账期（增量结算），
     只有合并后金额仍对不上的才是真实差异；其余逐期差异属于「跨期归期/分摊」不计入结论

说明:
  订单归属、结算利润明细全部通过 MCP 工具获取，脚本不再直连数据库、
  不内置任何库表 SQL 与账号口令。
"""

import argparse
import os
import re
import sys

from openpyxl import Workbook

from walmart_mcp import (
    McpClient,
    McpError,
    TOOL_QUERY_ORDER,
    TOOL_QUERY_PROFIT_SETTLEMENT,
)
import walmart_source as ws

TOLERANCE = 0.01
STATUS_CANCELLED = "订单已作废"


# ── 对账主体解析 ──────────────────────────────────────────────────────────

def pick_settlement_sheet(file_path, preferred=None, assume_yes=False):
    """识别结算数据所在 sheet，必要时提示确认；都不可用时抛错"""
    candidates = ws.probe_sheets(file_path)
    usable = [c for c in candidates if c["usable"]]

    if preferred is not None:
        chosen, _ = ws.choose_sheet(candidates, preferred=preferred)
        if chosen is None:
            raise ValueError(
                f"sheet 不存在: {preferred}；文件中的 sheet：{ws.list_sheet_names(file_path)}")
        if not chosen["usable"]:
            print(f"      [提示] sheet {chosen['sheet']!r} 未包含结算单必需列，"
                  f"将自动识别其它 sheet")
    else:
        chosen, certain = ws.choose_sheet(candidates)
        if chosen is None:
            raise ValueError(
                "未找到包含结算单必需列的 sheet："
                f"{[c['sheet'] for c in candidates]}；可用 --sheet 指定")

    sheet_names = [c["sheet"] for c in usable]
    first_sheet = ws.list_sheet_names(file_path)[0]
    header_desc = (f"表头在第 {chosen['header_index'] + 1} 行"
                   if chosen["header_index"] is not None else "未找到结算单必需列")
    print(f"      识别到结算数据所在 sheet：{chosen['sheet']!r}"
          f"（可用候选：{sheet_names}，{header_desc}）")

    # 不在第一个 sheet、或存在多个候选时，先提示确认
    if preferred is None and (chosen["sheet"] != first_sheet or len(usable) > 1):
        if assume_yes or not is_interactive():
            print("      [提示] 如果 sheet 识别不正确，请用 --sheet <名称> 指定")
        else:
            answer = input(f"      请确认使用 sheet {chosen['sheet']!r} 进行对账？(y=是 / n=否): ")
            if answer.strip().lower() != "y":
                raise ValueError("已取消；请用 --sheet <名称> 指定要使用的 sheet")
    return chosen


def load_blocks(file_path, chosen, preferred=None, assume_yes=False):
    """按账期切分结算块；当前 sheet 解析不出内容时自动尝试其它候选 sheet"""
    attempts = []
    if chosen["header_index"] is not None:
        attempts.append((chosen, False))
    for candidate in ws.probe_sheets(file_path):
        if candidate["usable"] and candidate["sheet"] != chosen["sheet"]:
            attempts.append((candidate, True))
    if not attempts:
        raise ValueError(f"sheet {chosen['sheet']!r} 未包含结算单必需列，"
                         f"请用 --sheet 指定结算数据所在 sheet")

    for candidate, is_fallback in attempts:
        rows = ws.read_rows(file_path, candidate["sheet"])
        blocks = ws.parse_blocks(rows, candidate["header_index"])
        usable_blocks = [b for b in blocks if b.details]
        if usable_blocks:
            if is_fallback:
                print(f"      [自动识别] sheet {chosen['sheet']!r} 无法对账，"
                      f"已改用 {candidate['sheet']!r}")
            return candidate, usable_blocks
        if not is_fallback:
            print(f"      [提示] sheet {chosen['sheet']!r} 未解析出账期明细，尝试其它 sheet")

    raise ValueError(
        f"未能在 sheet {chosen['sheet']!r} 中解析出账期与订单明细，"
        f"请用 --sheet <名称> 指定结算数据所在 sheet")


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


def query_settlement_data(client, company_code, user_account, platform, start_date, end_date):
    """通过 MCP 工具 queryProfitSettlement 查询指定账期的结算利润明细

    返回 {order_id: {'fee_amount': float, 'status': str}}
    同一订单可能返回多个对账结果（匹配到订单/订单已作废/对账成功），聚合规则：
    优先取非「订单已作废」的记录并累加；若只有作废记录，则保留作废金额。
    """
    rows = client.call_tool(TOOL_QUERY_PROFIT_SETTLEMENT, {
        "companyCode": company_code,
        "userAccount": user_account,
        "platform": platform,
        "startTime": start_date,
        "endTime": end_date,
    })

    result = {}
    for row in rows:
        order_id = ws.normalize_id(row.get("orderId"))
        if order_id == "":
            continue
        fee = float(row.get("settlementAmount") or 0)
        status = str(row.get("accountCheckResult") or "未知")

        if order_id in result:
            if status != STATUS_CANCELLED and result[order_id]['status'] == STATUS_CANCELLED:
                result[order_id] = {'fee_amount': fee, 'status': status}
            elif status != STATUS_CANCELLED:
                result[order_id]['fee_amount'] += fee
        else:
            result[order_id] = {'fee_amount': fee, 'status': status}
    return result


def resolve_owner(client, blocks, company_code, user_account, platform, assume_yes):
    """确定对账主体：显式传入优先，否则通过 MCP 查询订单归属并与用户确认"""
    if company_code and user_account:
        resolved_platform = platform or "walmart"
        print(f"[2/4] 使用指定的客户/店铺：客户={company_code}，店铺={user_account}，"
              f"平台={resolved_platform}")
        return company_code, user_account, resolved_platform

    sample_po = None
    for block in blocks:
        sample_po = next((po for po in block.amount_summary() if po.isdigit()), None)
        if sample_po:
            break
    if not sample_po:
        raise McpError("未从结算文件中提取到纯数字的 Purchase Order #，无法查询订单归属，"
                       "请使用 --company-code / --user-account 手动指定")

    print(f"[2/4] 查询订单归属（MCP 工具 {TOOL_QUERY_ORDER}，refrence_no={sample_po}）")
    info = query_order_info(client, sample_po)
    if not info:
        raise McpError(f"订单号 {sample_po} 在 MCP 中未找到对应记录，"
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
            platform = input("  请输入正确的平台(platform) [默认walmart]: ").strip() or "walmart"
            print(f"      已更新 → 客户：{company_code}，店铺：{user_account}，平台：{platform}")
            confirm2 = input("确认这次输入正确吗？(y=正确继续 / n=重新输入): ").strip().lower()
            if confirm2 == "y":
                return company_code, user_account, platform
        else:
            print("      请输入 y 或 n")


# ── 比对 ──────────────────────────────────────────────────────────────────

def compare_block(block, db_summary):
    """单个账期比对，返回 (diffs, matched, cancelled)，元素为 (order_id, excel, db, 备注, 状态)"""
    excel_summary = block.amount_summary()
    db_amounts = {k: v['fee_amount'] for k, v in db_summary.items()}

    diffs = []
    matched = []
    cancelled = []
    for order_id in set(excel_summary.keys()) | set(db_amounts.keys()):
        excel_amount = excel_summary.get(order_id)
        db_amount = db_amounts.get(order_id)
        status = db_summary.get(order_id, {}).get('status', '')

        if excel_amount is None:
            diffs.append((order_id, excel_amount, db_amount, "仅在结算利润中", status))
        elif db_amount is None:
            if abs(excel_amount) < TOLERANCE:
                matched.append((order_id, excel_amount, db_amount, "忽略(金额为0)", status))
            else:
                diffs.append((order_id, excel_amount, db_amount, "仅在Excel中", status))
        elif abs(excel_amount - db_amount) > TOLERANCE:
            diffs.append((order_id, excel_amount, db_amount, "金额不一致", status))
        elif status == STATUS_CANCELLED:
            cancelled.append((order_id, excel_amount, db_amount, STATUS_CANCELLED, status))
        else:
            matched.append((order_id, excel_amount, db_amount, "匹配", status))

    return excel_summary, db_amounts, diffs, matched, cancelled


def compare_all_blocks(client, blocks, company_code, user_account, platform):
    """逐账期查询 MCP 并比对"""
    results = []
    for block in blocks:
        print(f"      账期 {block.period}：Excel {len(block.details)} 行明细 / "
              f"{len(block.amount_summary())} 个订单")
        try:
            db_summary = query_settlement_data(
                client, company_code, user_account, platform,
                block.period_start, block.period_end)
        except McpError as e:
            raise McpError(f"账期 {block.period} 查询结算利润明细失败: {e}") from None
        excel_summary, db_amounts, diffs, matched, cancelled = compare_block(block, db_summary)
        print(f"            DB {len(db_amounts)} 个订单，差异 {len(diffs)} 条")
        results.append({
            "block": block,
            "excel": excel_summary,
            "db": db_amounts,
            "db_status": {key: value["status"] for key, value in db_summary.items()},
            "diffs": diffs,
            "matched": matched,
            "cancelled": cancelled,
        })
    return results


def merge_orders(results):
    """按订单跨账期合并，判定真实差异

    逐账期比对用于统计与定位；最终差异以「订单为单位、跨账期金额合并」为准：
    同一订单本来就可能出现在多个账期（增量结算），合并后金额仍对不上的才是真实差异，
    其余逐期差异属于「跨期归期/分摊」（两边把金额归到不同账期或分摊比例不同）。

    返回:
      excel / db               跨期合并后的 {order_id: 金额}
      excel_periods/db_periods {order_id: [账期, ...]}
      diffs                    [(order_id, excel, db, 备注, 结算单账期, DB账期)] 真实差异
      matched / cancelled      合并后一致 / 作废
      entry_total/entry_cross  逐期差异条目总数 / 其中跨期归期分摊条数
      diff_ids / cross_ids     真实差异订单号 / 跨期归期分摊订单号
    """
    excel_all, db_all = {}, {}
    excel_periods, db_periods = {}, {}
    status_map = {}
    for item in results:
        period = item["block"].period
        for order_id, amount in item["excel"].items():
            excel_all[order_id] = excel_all.get(order_id, 0.0) + amount
            excel_periods.setdefault(order_id, []).append(period)
        for order_id, amount in item["db"].items():
            db_all[order_id] = db_all.get(order_id, 0.0) + amount
            db_periods.setdefault(order_id, []).append(period)
        for order_id, status in item["db_status"].items():
            if status != STATUS_CANCELLED or order_id not in status_map:
                status_map[order_id] = status

    diffs, matched, cancelled = [], [], []
    for order_id in sorted(set(excel_all) | set(db_all)):
        excel_amount = excel_all.get(order_id)
        db_amount = db_all.get(order_id)
        periods = (" / ".join(excel_periods.get(order_id, [])) or "—",
                   " / ".join(db_periods.get(order_id, [])) or "—")

        if excel_amount is None and abs(db_amount) < TOLERANCE:
            matched.append((order_id, excel_amount, db_amount, "忽略(金额为0)", *periods))
        elif db_amount is None and abs(excel_amount) < TOLERANCE:
            matched.append((order_id, excel_amount, db_amount, "忽略(金额为0)", *periods))
        elif excel_amount is None:
            diffs.append((order_id, excel_amount, db_amount, "仅在结算利润中", *periods))
        elif db_amount is None:
            diffs.append((order_id, excel_amount, db_amount, "仅在Excel中", *periods))
        elif abs(excel_amount - db_amount) > TOLERANCE:
            diffs.append((order_id, excel_amount, db_amount, "金额不一致", *periods))
        elif status_map.get(order_id) == STATUS_CANCELLED:
            cancelled.append((order_id, excel_amount, db_amount, STATUS_CANCELLED, *periods))
        else:
            matched.append((order_id, excel_amount, db_amount, "匹配", *periods))

    diff_ids = {diff[0] for diff in diffs}
    entry_total = sum(len(item["diffs"]) for item in results)
    cross_ids = {order_id for item in results for order_id, *_ in item["diffs"]
                 if order_id not in diff_ids}
    entry_real = sum(1 for item in results for diff in item["diffs"] if diff[0] in diff_ids)

    return {
        "excel": excel_all,
        "db": db_all,
        "excel_periods": excel_periods,
        "db_periods": db_periods,
        "diffs": diffs,
        "matched": matched,
        "cancelled": cancelled,
        "diff_ids": diff_ids,
        "cross_ids": cross_ids,
        "entry_total": entry_total,
        "entry_real": entry_real,
        "entry_cross": entry_total - entry_real,
    }


def diff_scope(order_id, merged):
    """逐期差异条目的归属：真实差异 / 跨期归期分摊"""
    return "真实差异" if order_id in merged["diff_ids"] else "跨期归期/分摊"


def short_period(text):
    """账期简称：2026-04-18 ~ 2026-05-02 -> 04-18~05-02，便于控制台并排展示"""
    return re.sub(r"\d{4}-(\d{2}-\d{2})\s*~\s*\d{4}-(\d{2}-\d{2})", r"\1~\2", text)


# ── 输出 ──────────────────────────────────────────────────────────────────

def print_console(result, merged, company_code, user_account, platform, sheet_name):
    excel_orders = sum(len(r["excel"]) for r in result)
    db_orders = sum(len(r["db"]) for r in result)
    excel_total = sum(sum(r["excel"].values()) for r in result)
    db_total = sum(sum(r["db"].values()) for r in result)
    cancelled_count = sum(len(r["cancelled"]) for r in result)
    real_diffs = merged["diffs"]

    verdict = "完全一致" if not real_diffs else f"有差异（{len(real_diffs)} 个订单需核对）"

    print("\n" + "=" * 78)
    print(f"{'项目':<16}\t{'值'}")
    print("-" * 40)
    print(f"{'客户':<16}\t{company_code}")
    print(f"{'店铺':<16}\t{user_account}")
    print(f"{'平台':<16}\t{platform}")
    print(f"{'结算 sheet':<13}\t{sheet_name}")
    print(f"{'账期数':<16}\t{len(result)}")
    print(f"{'订单数(逐期)':<13}\tExcel {excel_orders} / DB {db_orders}")
    print(f"{'订单数(去重)':<13}\tExcel {len(merged['excel'])} / DB {len(merged['db'])}")
    print(f"{'Excel总金额':<16}\t{excel_total:,.2f}")
    print(f"{'DB总金额':<16}\t{db_total:,.2f}")
    if cancelled_count > 0:
        print(f"{'订单已作废':<16}\t{cancelled_count} 条")
    print(f"{'逐期差异条目':<14}\t{merged['entry_total']} 条（统计与定位用）")
    if merged["entry_cross"] > 0:
        print(f"{'跨期归期/分摊':<14}\t{merged['entry_cross']} 条 / "
              f"{len(merged['cross_ids'])} 个订单（合并后金额一致，不计入差异）")
    print(f"{'真实差异':<16}\t{len(real_diffs)} 个订单"
          + (f"（{format_diff_types(real_diffs)}）" if real_diffs else ""))
    print(f"{'匹配结果':<16}\t{verdict}")
    print("=" * 78)

    # 各账期汇总（统计与定位用）
    if len(result) > 1:
        print(f"\n各账期汇总（按账期统计，最终结论见下方真实差异）：")
        print(f"{'账期':<25} {'Excel订单':>8} {'DB订单':>7} {'Excel总金额':>15} "
              f"{'DB总金额':>15} {'逐期差异':>6} {'跨期归期':>6}")
        print("-" * 92)
        for item in result:
            print(format_period_row(item, merged))
        print("-" * 92)
        print(f"{'合计':<25} {excel_orders:>8} {db_orders:>7} {excel_total:>15,.2f} "
              f"{db_total:>15,.2f} {merged['entry_total']:>6} {merged['entry_cross']:>6}")

    # 真实差异明细（订单级：跨账期合并后比对）
    if real_diffs:
        print(f"\n真实差异明细（{len(real_diffs)} 个订单，按订单跨账期合并后比对）：")
        print(f"{'order_id':<20} {'类型':<16} {'excel':>13} {'db':>13}  "
              f"结算单账期 → DB账期")
        print("-" * 108)
        for order_id, excel_amount, db_amount, note, excel_period, db_period in real_diffs:
            es = f"{excel_amount:,.2f}" if excel_amount is not None else "—"
            ds = f"{db_amount:,.2f}" if db_amount is not None else "—"
            print(f"{order_id:<20} {note:<16} {es:>13} {ds:>13}  "
                  f"{short_period(excel_period)} → {short_period(db_period)}")
        print("=" * 78)

    # 跨期归期/分摊（不计入差异）
    if merged["entry_cross"] > 0:
        print(f"\n跨期归期/分摊（不计入差异）：逐期条目 {merged['entry_cross']} 条 / "
              f"订单 {len(merged['cross_ids'])} 个")
        print("  这些订单两边合并后金额一致，只是归期或各期分摊比例不同；"
              "逐期明细见导出文件「逐期差异明细」sheet")


def format_diff_types(diffs):
    """真实差异类型汇总，如「仅在Excel中 24 / 仅在结算利润中 12 / 金额不一致 9」"""
    counts = {}
    for *_rest, note, _excel_period, _db_period in diffs:
        counts[note] = counts.get(note, 0) + 1
    return " / ".join(f"{note} {counts[note]}" for note in
                      ["仅在Excel中", "仅在结算利润中", "金额不一致"] if note in counts)


def format_period_row(item, merged):
    block = item["block"]
    cross = sum(1 for diff in item["diffs"] if diff[0] not in merged["diff_ids"])
    return (f"{block.period:<25} {len(item['excel']):>8} {len(item['db']):>7} "
            f"{sum(item['excel'].values()):>15,.2f} {sum(item['db'].values()):>15,.2f} "
            f"{len(item['diffs']):>6} {cross:>6}")


def export_excel(result, merged, company_code, user_account, platform, sheet_name,
                 file_path):
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

    excel_orders = sum(len(r["excel"]) for r in result)
    db_orders = sum(len(r["db"]) for r in result)
    excel_total = sum(sum(r["excel"].values()) for r in result)
    db_total = sum(sum(r["db"].values()) for r in result)
    cancelled_count = sum(len(r["cancelled"]) for r in result)
    real_diffs = merged["diffs"]

    verdict = "完全一致" if not real_diffs else f"有差异（{len(real_diffs)} 个订单需核对）"

    base, _ = os.path.splitext(file_path)
    output_path = base + "_比对结果.xlsx"
    out_wb = Workbook()

    header_font_white = Font(bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    border = Border(left=Side(style='thin'), right=Side(style='thin'),
                    top=Side(style='thin'), bottom=Side(style='thin'))
    center_align = Alignment(horizontal='center', vertical='center')
    right_align = Alignment(horizontal='right', vertical='center')
    money_format = '#,##0.00'
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    yellow_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

    def style_table(worksheet, header_row, first_col, last_col, money_cols=()):
        for cell in worksheet[header_row]:
            if cell.column < first_col or cell.column > last_col:
                continue
            cell.font = header_font_white
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center_align
        for row in worksheet.iter_rows(min_row=header_row + 1, max_row=worksheet.max_row,
                                       min_col=first_col, max_col=last_col):
            for cell in row:
                cell.border = border
                if cell.column in money_cols:
                    cell.number_format = money_format
                    cell.alignment = right_align

    # Sheet1: 汇总信息
    ws_info = out_wb.active
    ws_info.title = "汇总信息"
    ws_info.append(["项目", "值"])
    ws_info.append(["客户", company_code])
    ws_info.append(["店铺", user_account])
    ws_info.append(["平台", platform])
    ws_info.append(["结算 sheet", sheet_name])
    ws_info.append(["账期数", len(result)])
    ws_info.append(["Excel订单数(逐期累计)", excel_orders])
    ws_info.append(["DB订单数(逐期累计)", db_orders])
    ws_info.append(["Excel订单数(跨期去重)", len(merged["excel"])])
    ws_info.append(["DB订单数(跨期去重)", len(merged["db"])])
    ws_info.append(["Excel总金额", excel_total])
    ws_info.append(["DB总金额", db_total])
    if cancelled_count > 0:
        ws_info.append(["订单已作废", cancelled_count])
    ws_info.append(["逐期差异条目", merged["entry_total"]])
    if merged["entry_cross"] > 0:
        ws_info.append(["跨期归期/分摊", merged["entry_cross"]])
    ws_info.append(["真实差异订单数", len(real_diffs)])
    ws_info.append(["匹配结果", verdict])
    ws_info.append([])
    period_header_row = ws_info.max_row + 1
    ws_info.append(["账期", "Excel订单数", "DB订单数", "Excel总金额", "DB总金额",
                    "订单已作废", "逐期差异条目", "其中跨期归期分摊"])
    for item in result:
        cross = sum(1 for diff in item["diffs"] if diff[0] not in merged["diff_ids"])
        ws_info.append([item["block"].period, len(item["excel"]), len(item["db"]),
                        sum(item["excel"].values()), sum(item["db"].values()),
                        len(item["cancelled"]), len(item["diffs"]), cross])
    if len(result) > 1:
        ws_info.append(["合计", excel_orders, db_orders, excel_total, db_total,
                        cancelled_count, merged["entry_total"], merged["entry_cross"]])
    for row in ws_info.iter_rows(min_row=1, max_row=period_header_row - 2, min_col=1, max_col=1):
        for cell in row:
            cell.font = Font(bold=True)
    style_table(ws_info, period_header_row, 1, 8, money_cols=(4, 5))

    # Sheet: 真实差异（订单级结论：按订单跨账期合并后比对）
    ws_real = out_wb.create_sheet("真实差异")
    ws_real.append(["客户", company_code, "店铺", user_account, "结算 sheet", sheet_name])
    ws_real.append(["真实差异订单数", len(real_diffs), "逐期差异条目", merged["entry_total"],
                    "其中跨期归期分摊", merged["entry_cross"]])
    ws_real.append(["Excel总金额", excel_total, "DB总金额", db_total, "匹配结果", verdict])
    ws_real.append([])
    ws_real.append(["order_id", "类型", "excel金额", "db金额", "结算单所在账期", "DB所在账期"])
    for order_id, excel_amount, db_amount, note, excel_period, db_period in real_diffs:
        ws_real.append([order_id, note, excel_amount, db_amount, excel_period, db_period])
    style_table(ws_real, 5, 1, 6, money_cols=(3, 4))
    for row in ws_real.iter_rows(min_row=6, max_row=ws_real.max_row, min_col=2, max_col=2):
        for cell in row:
            cell.fill = red_fill

    # Sheet: 逐期差异明细（逐期条目 + 归属，统计与定位用）
    ws_period = out_wb.create_sheet("逐期差异明细")
    ws_period.append(["客户", company_code, "店铺", user_account, "结算 sheet", sheet_name])
    ws_period.append(["逐期差异条目", merged["entry_total"], "跨期归期/分摊",
                      merged["entry_cross"], "真实差异订单数", len(real_diffs)])
    ws_period.append(["Excel总金额", excel_total, "DB总金额", db_total, "匹配结果", verdict])
    ws_period.append([])
    ws_period.append(["账期", "order_id", "excel_fee_amount", "db_fee_amount", "备注", "归属"])
    for item in result:
        for order_id, excel_amount, db_amount, note, _status in sorted(item["diffs"]):
            ws_period.append([item["block"].period, order_id, excel_amount, db_amount, note,
                              diff_scope(order_id, merged)])
    style_table(ws_period, 5, 1, 6, money_cols=(3, 4))

    # Sheet: 订单已作废
    cancelled_rows = [(item["block"].period, *c) for item in result for c in item["cancelled"]]
    if cancelled_rows:
        ws_cancel = out_wb.create_sheet("订单已作废")
        ws_cancel.append(["客户", company_code, "店铺", user_account, "结算 sheet", sheet_name])
        ws_cancel.append(["作废订单数", len(cancelled_rows)])
        ws_cancel.append([])
        ws_cancel.append(["账期", "order_id", "金额"])
        for period, order_id, excel_amount, _db, _note, _status in sorted(cancelled_rows):
            ws_cancel.append([period, order_id, excel_amount])
        style_table(ws_cancel, 4, 1, 3, money_cols=(3,))
        for row in ws_cancel.iter_rows(min_row=5, max_row=ws_cancel.max_row, min_col=3, max_col=3):
            for cell in row:
                cell.fill = yellow_fill

    # Sheet: 全量比对（逐期全量）
    ws_all = out_wb.create_sheet("全量比对")
    ws_all.append(["客户", company_code, "店铺", user_account, "结算 sheet", sheet_name])
    ws_all.append(["账期数", len(result), "Excel订单数", excel_orders,
                   "DB订单数", db_orders])
    ws_all.append(["Excel总金额", excel_total, "DB总金额", db_total,
                   "逐期差异条目", merged["entry_total"]])
    ws_all.append([])
    ws_all.append(["账期", "order_id", "excel_fee_amount", "db_fee_amount", "状态"])
    for item in result:
        rows = [(item["block"].period, *r) for r in
                item["matched"] + item["cancelled"] + item["diffs"]]
        for period, order_id, excel_amount, db_amount, note, _status in sorted(rows):
            ws_all.append([period, order_id, excel_amount, db_amount, note])
    style_table(ws_all, 5, 1, 5, money_cols=(3, 4))

    out_wb.save(output_path)
    print(f"\n已导出比对结果：{output_path}")


def is_interactive():
    """当前是否为可交互终端"""
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except (ValueError, AttributeError):
        return False


# ── 入口 ──────────────────────────────────────────────────────────────────

def run(file_path, sheet=None, mcp_url=None, company_code=None, user_account=None,
        platform=None, assume_yes=False):
    if not os.path.exists(file_path):
        raise ValueError(f"文件不存在: {file_path}")

    print(f"[1/4] 读取结算文件: {file_path}")
    chosen = pick_settlement_sheet(file_path, preferred=sheet, assume_yes=assume_yes)
    chosen, blocks = load_blocks(file_path, chosen, preferred=sheet, assume_yes=assume_yes)
    detail_rows = sum(len(b.details) for b in blocks)
    print(f"      识别到 {len(blocks)} 个账期、{detail_rows} 行订单明细：")
    for block in blocks:
        print(f"        {block.period}  明细 {len(block.details)} 行 / "
              f"{len(block.amount_summary())} 个订单")

    client = McpClient(url=mcp_url)
    print(f"      MCP 地址：{client.url}")

    company_code, user_account, platform = resolve_owner(
        client, blocks, company_code, user_account, platform, assume_yes)

    print(f"\n[3/4] 逐账期查询结算利润明细（MCP 工具 {TOOL_QUERY_PROFIT_SETTLEMENT}）")
    print(f"      条件：companyCode={company_code}, userAccount={user_account}, "
          f"platform={platform}")
    result = compare_all_blocks(client, blocks, company_code, user_account, platform)

    print("[4/4] 按订单跨账期合并，得出真实差异")
    merged = merge_orders(result)
    print(f"      订单 {len(merged['excel'])} 个（逐期累计 "
          f"{sum(len(item['excel']) for item in result)}），"
          f"逐期差异条目 {merged['entry_total']} 条，"
          f"真实差异 {len(merged['diffs'])} 个订单")

    print_console(result, merged, company_code, user_account, platform, chosen["sheet"])
    export_excel(result, merged, company_code, user_account, platform, chosen["sheet"],
                 file_path)


def main():
    parser = argparse.ArgumentParser(
        description="Walmart 结算单对账（数据通过 nexus-mcp 获取）")
    parser.add_argument("file", help="Walmart 结算 CSV 或 XLSX 文件路径")
    parser.add_argument("--sheet", default=None,
                        help="结算数据所在 sheet 名称，默认自动识别（一般叫“结算单”）")
    parser.add_argument("--list-sheets", action="store_true",
                        help="只列出各 sheet 的探测结果，不做对账")
    parser.add_argument("--mcp-url", default=None,
                        help="nexus-mcp 地址，默认取环境变量 NEXUS_MCP_URL，"
                             "再默认 https://datacenter.eccang.com/nexus/mcp/stream")
    parser.add_argument("--company-code", default=None, help="客户编码")
    parser.add_argument("--user-account", default=None, help="店铺账号")
    parser.add_argument("--platform", default=None, help="平台，默认 walmart")
    parser.add_argument("-y", "--yes", action="store_true", help="跳过人工确认")
    args = parser.parse_args()

    try:
        if args.list_sheets:
            for candidate in ws.probe_sheets(args.file):
                flag = "结算数据候选" if candidate["usable"] else "无必需列"
                header = ("" if candidate["header_index"] is None
                          else f"，表头第 {candidate['header_index'] + 1} 行")
                print(f"{candidate['sheet']!r}\t{flag}{header}")
            return
        run(args.file, sheet=args.sheet, mcp_url=args.mcp_url,
            company_code=args.company_code, user_account=args.user_account,
            platform=args.platform, assume_yes=args.yes)
    except (McpError, ValueError, FileNotFoundError) as e:
        print(f"\n[错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
