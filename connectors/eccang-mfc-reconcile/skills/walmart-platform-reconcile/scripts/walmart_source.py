"""
Walmart 结算文件解析

职责：
  1. 清洗单元格文本（隐藏字符、Excel 文本前缀引号等）
  2. 选择结算数据所在的 sheet（支持提醒确认 + 失败后自动识别）
  3. 按账期切分结算块（一个 sheet 可能包含多个账期）

文件结构说明（真实结算单常见形态，可能由多份原始结算单拼接而成）：
  row0           表头（必需列：Transaction Key / Purchase Order # / Amount /
                 Amount Type / Total Payable / Period Start Date / Period End Date）
  账期汇总行      Total Payable 为数字，Period Start/End 为该账期日期
  费用行          无 Transaction Key（如 Fee/Reimbursement），自带各自 Period，忽略
  订单明细行      Transaction Key 非空，属于上方最近的账期汇总行
  重复表头行      块与块之间可能出现（多份结算单拼接），整行都是列名，跳过
"""

import csv
import os
import re
from datetime import datetime

from openpyxl import load_workbook

# 结算单必需列
COL_TRANSACTION_KEY = "Transaction Key"
COL_PURCHASE_ORDER = "Purchase Order #"
COL_AMOUNT = "Amount"
COL_AMOUNT_TYPE = "Amount Type"
COL_TOTAL_PAYABLE = "Total Payable"
COL_PERIOD_START = "Period Start Date"
COL_PERIOD_END = "Period End Date"

REQUIRED_COLUMNS = [COL_TRANSACTION_KEY, COL_PURCHASE_ORDER, COL_AMOUNT, COL_AMOUNT_TYPE,
                    COL_TOTAL_PAYABLE, COL_PERIOD_START, COL_PERIOD_END]

# sheet 命名特征（一般的结算单 sheet 会叫“结算单”）
PREFERRED_SHEET_KEYWORDS = ("结算单", "结算", "settlement")

# 表头可能不在第一行，向下扫描的最大行数
HEADER_SCAN_ROWS = 15

# Excel 文本前缀等不可见字符
_INVISIBLE_CHARS = dict.fromkeys(
    [c for c in range(0x00, 0x20)] + [0x7f, 0xad, 0xa0, 0x1680]
    + [c for c in range(0x2000, 0x2010)]
    + [0x2028, 0x2029, 0x202f, 0x205f, 0x2060, 0x3000, 0xfeff]
)
# 引号类字符：Excel 文本前缀撇号（双击单元格才能看到的 '1111）、直引号/弯引号/反引号
_QUOTE_CHARS = "'\"“”‘’`´"
_DATE_FORMATS = ("%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d")


# ── 单元格清洗 ────────────────────────────────────────────────────────────

def to_text(value):
    """单元格值转文本：去掉不可见字符与首尾引号、空白；整数型浮点去掉多余的 .0"""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).translate(_INVISIBLE_CHARS)
    return text.strip().strip(_QUOTE_CHARS).strip()


def normalize_id(value):
    """订单号/交易号归一化：清理文本后再去掉所有空白，用于与 MCP 侧 orderId 对齐"""
    text = re.sub(r"\s+", "", to_text(value))
    # 数字被导出成 "1111.0" 这类文本时，去掉小数尾巴
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".")[0]
    return text


def to_number(value):
    """转数字，无法解析返回 None（区别于 0）"""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = to_text(value)
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_amount(value):
    """金额解析：清理隐藏字符后转 float，无法解析按 0 处理"""
    number = to_number(value)
    return 0.0 if number is None else number


def parse_date(value):
    """解析日期值，返回 YYYY-MM-DD；无法解析返回 None"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    text = to_text(value)
    if text == "":
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def find_column_index(header_row, name):
    """按列名找下标（列名做同样的清洗，容忍隐藏字符）"""
    target = normalize_id(name).lower()
    for i, cell in enumerate(header_row):
        if cell is not None and normalize_id(cell).lower() == target:
            return i
    return None


def resolve_columns(header_row):
    """定位必需列，返回 {列名: 下标}；缺列返回 None"""
    columns = {}
    for name in REQUIRED_COLUMNS:
        index = find_column_index(header_row, name)
        if index is None:
            return None
        columns[name] = index
    return columns


# ── 文件读取与 sheet 选择 ─────────────────────────────────────────────────

def is_csv(file_path):
    return os.path.splitext(file_path)[1].lower() == ".csv"


def read_rows(file_path, sheet_name=None):
    """读取文件的原始行；CSV 只有一个“sheet”"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        with open(file_path, "r", encoding="utf-8-sig") as f:
            return [list(r) for r in csv.reader(f)]
    if ext not in (".xlsx", ".xls"):
        raise ValueError(f"不支持的文件格式: {ext}")

    wb = load_workbook(file_path, read_only=True, data_only=True)
    try:
        if sheet_name is not None:
            if sheet_name not in wb.sheetnames:
                raise ValueError(f"sheet 不存在: {sheet_name}（可选：{wb.sheetnames}）")
            ws = wb[sheet_name]
        else:
            ws = wb[wb.sheetnames[0]]
        return [list(r) for r in ws.iter_rows(values_only=True)]
    finally:
        wb.close()


def list_sheet_names(file_path):
    if is_csv(file_path):
        return [None]
    wb = load_workbook(file_path, read_only=True, data_only=True)
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()


def find_header_index(rows):
    """在文件头部若干行内定位表头行，找不到返回 None"""
    for i, row in enumerate(rows[:HEADER_SCAN_ROWS]):
        if resolve_columns(row) is not None:
            return i
    return None


def probe_sheets(file_path):
    """探测每个 sheet 是否是结算数据表

    返回 [{sheet, header_index, usable}]，usable 表示能找到表头（即含全部必需列）
    """
    candidates = []
    for sheet in list_sheet_names(file_path):
        try:
            rows = read_rows(file_path, sheet)
        except Exception:
            continue
        header_index = find_header_index(rows)
        candidates.append({
            "sheet": sheet,
            "header_index": header_index,
            "usable": header_index is not None,
        })
    return candidates


def score_sheet(sheet_name):
    """按命名特征打分，名字像结算单的优先"""
    if not sheet_name:
        return 0
    name = str(sheet_name)
    return 1 if any(k in name for k in PREFERRED_SHEET_KEYWORDS) else 0


def choose_sheet(candidates, preferred=None):
    """选择结算数据所在 sheet

    返回 (选中项, 是否明确)：--sheet 指定 > 命名像结算单 > 第一个可用
    """
    usable = [c for c in candidates if c["usable"]]
    if preferred is not None:
        for c in candidates:
            if c["sheet"] == preferred:
                return c, True
        for c in candidates:
            if str(c["sheet"]) == str(preferred):
                return c, True
        return None, False
    if not usable:
        return None, False
    if len(usable) == 1:
        return usable[0], True
    scored = sorted(usable, key=lambda c: (score_sheet(c["sheet"]), -usable.index(c)), reverse=True)
    return scored[0], score_sheet(scored[0]["sheet"]) > 0


# ── 账期切分 ──────────────────────────────────────────────────────────────

class SettlementBlock:
    """一个账期块：账期 + 该账期的订单明细"""

    def __init__(self, period_start, period_end, total_payable, row_index):
        self.period_start = period_start
        self.period_end = period_end
        self.total_payable = total_payable
        self.row_index = row_index
        self.details = []

    @property
    def period(self):
        return f"{self.period_start} ~ {self.period_end}"

    def amount_summary(self):
        """按 Purchase Order # 汇总 Amount，返回 {order_id: amount}"""
        summary = {}
        for detail in self.details:
            if detail["purchase_order"] == "":
                continue
            summary[detail["purchase_order"]] = (
                summary.get(detail["purchase_order"], 0.0) + detail["amount"])
        return summary

    def __repr__(self):
        return (f"SettlementBlock({self.period}, details={len(self.details)}, "
                f"total_payable={self.total_payable})")


def parse_blocks(rows, header_index):
    """按账期切分结算块

    账期汇总行 = Total Payable 为数字且 Period Start/End 可解析为日期；
    订单明细行 = Transaction Key 非空，归属其上方最近的账期汇总行；
    其余行（费用行、重复表头行、空行）忽略。
    """
    header = rows[header_index]
    columns = resolve_columns(header)
    if columns is None:
        raise ValueError("表头缺少必需列")

    blocks = []
    orphans = []
    current = None
    for row_index in range(header_index + 1, len(rows)):
        row = rows[row_index]

        # 重复表头行（多份结算单拼接时块与块之间会出现）：整行都是列名，直接跳过，
        # 否则 Transaction Key 一列是字面量 "Transaction Key"，会被当成订单明细
        if resolve_columns(row) is not None:
            continue

        def cell(name):
            index = columns[name]
            return row[index] if index < len(row) else None

        total_payable = to_number(cell(COL_TOTAL_PAYABLE))
        period_start = parse_date(cell(COL_PERIOD_START))
        period_end = parse_date(cell(COL_PERIOD_END))
        if total_payable is not None and period_start and period_end:
            current = SettlementBlock(period_start, period_end, total_payable, row_index)
            blocks.append(current)
            continue

        transaction_key = to_text(cell(COL_TRANSACTION_KEY))
        if transaction_key == "":
            continue

        detail = {
            "transaction_key": transaction_key,
            "purchase_order": normalize_id(cell(COL_PURCHASE_ORDER)),
            "amount": parse_amount(cell(COL_AMOUNT)),
            "amount_type": to_text(cell(COL_AMOUNT_TYPE)),
        }
        if current is None:
            orphans.append(detail)
        else:
            current.details.append(detail)

    # 明细出现在第一个账期汇总行之前时，归入第一个账期（兼容“明细在前、汇总在后”的文件）
    if orphans and blocks:
        blocks[0].details = orphans + blocks[0].details

    return blocks
