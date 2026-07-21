#!/usr/bin/env python3
"""
银行流水自动分类整理脚本
读取银行导出的 Excel/CSV 流水，自动分类为收入/支出，
标记大额交易和疑似捐赠，生成分类汇总表。

用法:
    python bank_statement_sorter.py <银行流水文件> [--output <输出文件路径>]

支持格式: .xlsx, .xls, .csv
"""

import sys
import os
import csv
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# 尝试导入 openpyxl，不强制依赖
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


# ============================================================
# 配置
# ============================================================

# 收入关键词（用于识别捐赠收入）
DONATION_KEYWORDS = [
    "捐赠", "捐款", "donation", "善款", "爱心",
    "月捐", "一次性捐", "配捐", "公益", "99公益",
]

GRANT_KEYWORDS = [
    "拨款", "补助", "政府", "财政", "购买服务",
]

# 支出关键词分类
EXPENSE_CATEGORIES = {
    "人员费用": ["工资", "薪酬", "社保", "公积金", "个税", "劳务费", "讲师费"],
    "项目活动": ["活动", "项目", "培训", "志愿", "走访", "调研"],
    "办公行政": ["房租", "物业", "水电", "办公", "快递", "打印", "文具"],
    "差旅交通": ["差旅", "交通", "机票", "火车", "住宿", "出租", "打车"],
    "通讯网络": ["电话", "网络", "宽带", "通讯"],
    "设备采购": ["电脑", "设备", "打印机", "家具"],
}

# 大额交易阈值
LARGE_AMOUNT_THRESHOLD = 50000  # 5万元以上标记为大额


# ============================================================
# 文件读取
# ============================================================

_CSV_ENCODINGS = ["utf-8-sig", "utf-8", "gbk", "gb2312", "gb18030"]


def _try_read_csv(file_path, encoding):
    """单一编码尝试读取，失败返回 None"""
    try:
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
    except (UnicodeDecodeError, UnicodeError):
        return None
    lines = [l for l in content.strip().split("\n") if l.strip()]
    if not lines:
        return None
    rows = []
    reader = csv.reader(lines)
    for row in reader:
        if row and any(cell.strip() for cell in row):
            rows.append([cell.strip() for cell in row])
    return rows


def read_csv_file(file_path):
    """
    读取 CSV 银行流水，自动尝试多种编码。
    v1.3 重构：拆出 _try_read_csv，圈复杂度从 11 降到 ≈ 3。
    """
    for enc in _CSV_ENCODINGS:
        rows = _try_read_csv(file_path, enc)
        if rows is not None:
            return rows
    return []


def read_excel_file(file_path):
    """读取 Excel 银行流水"""
    if not HAS_OPENPYXL:
        print("⚠️ 需要安装 openpyxl 来读取 Excel 文件:")
        print("   pip install openpyxl")
        sys.exit(1)

    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active
    rows = []
    for row in ws.iter_rows(values_only=True):
        if row and any(cell is not None for cell in row):
            rows.append([str(cell) if cell is not None else "" for cell in row])
    wb.close()
    return rows


def read_file(file_path):
    """根据文件类型选择读取方式"""
    ext = Path(file_path).suffix.lower()
    if ext == ".csv":
        return read_csv_file(file_path)
    elif ext in (".xlsx", ".xls"):
        return read_excel_file(file_path)
    else:
        print(f"❌ 不支持的文件格式: {ext}")
        sys.exit(1)


# ============================================================
# 智能列识别（v1.3 重构：用规则表 + 单遍循环替代 if-elif 链）
# ============================================================

# 列识别规则表：(字段名, [关键词])
# 顺序很重要：party / desc 必须在通用 income/expense 之前匹配，
# 因为"对方户名"可能含"户"字（不会冲突）但确保特异性优先。
COLUMN_RULES = [
    ("date", ["日期", "交易日期", "记账日期", "date", "时间"]),
    ("counterparty", ["对方", "对方户名", "交易对方", "counterparty", "对方名称"]),
    ("description", ["摘要", "备注", "用途", "附言", "说明", "description", "memo"]),
    ("income", ["贷方", "收入", "贷方金额", "转入", "credit"]),
    ("expense", ["借方", "支出", "借方金额", "转出", "debit"]),
    ("amount", ["金额", "交易金额", "发生额", "amount"]),
    ("balance", ["余额", "账户余额", "balance"]),
]

COLUMN_FIELDS = [field for field, _ in COLUMN_RULES]


def _match_column_field(col_lower):
    """单列文本 → 匹配的字段名（按规则表顺序，首个命中即返回）"""
    for field, keywords in COLUMN_RULES:
        if any(k in col_lower for k in keywords):
            return field
    return None


def identify_columns(header_row):
    """
    智能识别列含义。
    圈复杂度 ≈ 4：初始化 + 遍历表头 + 跳过已占用 + 赋值。
    """
    col_map = {field: None for field in COLUMN_FIELDS}
    for i, col in enumerate(header_row):
        col_lower = col.lower().strip()
        field = _match_column_field(col_lower)
        if field and col_map[field] is None:
            col_map[field] = i
    return col_map


# ============================================================
# 交易分类
# ============================================================

def parse_amount(value):
    """解析金额字符串为浮点数"""
    if not value or value == "None":
        return 0.0
    # 去除千分位逗号、空格、货币符号
    cleaned = re.sub(r"[,，\s¥￥$]", "", str(value))
    # 处理括号表示负数
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def classify_transaction(description, counterparty=""):
    """根据摘要和对方户名分类交易"""
    text = f"{description} {counterparty}".lower()

    # 检查是否为捐赠收入
    for kw in DONATION_KEYWORDS:
        if kw in text:
            return "捐赠收入", "捐赠收入"

    # 检查是否为政府补助
    for kw in GRANT_KEYWORDS:
        if kw in text:
            return "政府补助收入", "政府补助收入"

    # 检查支出类别
    for category, keywords in EXPENSE_CATEGORIES.items():
        for kw in keywords:
            if kw in text:
                return "支出", category

    return "待分类", "待分类"


# ============================================================
# 处理与输出
# ============================================================

def _row_has_enough_columns(row, col_map):
    """跳过列数不够的残行（圈复杂度 = 2）"""
    indices = [v for v in col_map.values() if v is not None]
    if not indices:
        return False
    return len(row) > max(indices)


def _safe_get(row, idx):
    """按索引安全取值，None 索引或越界返回空串"""
    if idx is None or idx >= len(row):
        return ""
    return row[idx]


def _parse_income_expense(row, col_map):
    """
    从单行解析收入/支出金额。
    返回 (income, expense)。
    圈复杂度 ≈ 4。
    """
    if col_map["income"] is not None and col_map["expense"] is not None:
        return (
            parse_amount(row[col_map["income"]]),
            parse_amount(row[col_map["expense"]]),
        )
    if col_map["amount"] is not None:
        amt = parse_amount(row[col_map["amount"]])
        if amt > 0:
            return amt, 0.0
        return 0.0, abs(amt)
    return 0.0, 0.0


def _direction_and_amount(income_amt, expense_amt):
    """收支方向 + 金额（圈复杂度 = 2）"""
    if income_amt > 0:
        return "收入", income_amt
    return "支出", expense_amt


def _build_transaction_record(row_idx, row, col_map, income_amt, expense_amt):
    """构造单条交易记录"""
    direction, amount = _direction_and_amount(income_amt, expense_amt)
    description = _safe_get(row, col_map["description"])
    counterparty = _safe_get(row, col_map["counterparty"])
    trans_type, sub_category = classify_transaction(description, counterparty)
    return {
        "行号": row_idx,
        "日期": _safe_get(row, col_map["date"]),
        "收支方向": direction,
        "金额": amount,
        "对方名称": counterparty,
        "摘要": description,
        "自动分类": trans_type,
        "科目建议": sub_category,
        "大额标记": "⚠️大额" if amount >= LARGE_AMOUNT_THRESHOLD else "",
        "状态": "待确认",
    }


def process_transactions(rows, col_map):
    """
    处理所有交易记录。
    v1.3 重构：拆出 _parse_income_expense / _build_transaction_record 等辅助函数，
    圈复杂度从 16 降到 ≈ 5。
    """
    results = []
    for row_idx, row in enumerate(rows[1:], start=2):
        if not _row_has_enough_columns(row, col_map):
            continue
        income_amt, expense_amt = _parse_income_expense(row, col_map)
        if income_amt == 0 and expense_amt == 0:
            continue
        results.append(
            _build_transaction_record(row_idx, row, col_map, income_amt, expense_amt)
        )
    return results


def generate_output(results, output_path):
    """生成分类汇总CSV"""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = [
            "行号", "日期", "收支方向", "金额", "对方名称", "摘要",
            "自动分类", "科目建议", "大额标记", "状态"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)


def _compute_summary_stats(results):
    """汇总统计（v1.3 用累加循环替代多个 sum-generator，圈复杂度 ≈ 6）"""
    stats = {
        "total_income": 0.0, "total_expense": 0.0,
        "income_count": 0, "expense_count": 0,
        "large_count": 0, "unclassified": 0,
    }
    for r in results:
        if r["收支方向"] == "收入":
            stats["income_count"] += 1
            stats["total_income"] += r["金额"]
        elif r["收支方向"] == "支出":
            stats["expense_count"] += 1
            stats["total_expense"] += r["金额"]
        if r["大额标记"]:
            stats["large_count"] += 1
        if r["自动分类"] == "待分类":
            stats["unclassified"] += 1
    return stats


def _group_by_subcategory(results):
    """按 收支方向-分类 分组（圈复杂度 = 2）"""
    by_cat = defaultdict(lambda: {"count": 0, "amount": 0})
    for r in results:
        key = f"{r['收支方向']}-{r['自动分类']}"
        by_cat[key]["count"] += 1
        by_cat[key]["amount"] += r["金额"]
    return by_cat


def _print_donation_alert(results):
    """打印疑似捐赠提示（圈复杂度 = 2）"""
    donations = [r for r in results if r["自动分类"] == "捐赠收入"]
    if not donations:
        return
    total = sum(d["金额"] for d in donations)
    print()
    print(f"   💰 疑似捐赠收入: {len(donations)} 笔, 合计 {total:,.2f} 元")
    print("      请核对是否均已开具捐赠票据")


def print_summary(results):
    """
    打印汇总统计。
    v1.3 重构：拆出 _compute_summary_stats / _group_by_subcategory / _print_donation_alert，
    圈复杂度从 19 降到 ≈ 2。
    """
    s = _compute_summary_stats(results)
    print()
    print("📊 流水分析汇总:")
    print(f"   收入: {s['income_count']} 笔, 合计 {s['total_income']:,.2f} 元")
    print(f"   支出: {s['expense_count']} 笔, 合计 {s['total_expense']:,.2f} 元")
    print(f"   大额交易: {s['large_count']} 笔 (≥{LARGE_AMOUNT_THRESHOLD:,}元)")
    print(f"   待人工分类: {s['unclassified']} 笔")
    print()
    print("   分类明细:")
    by_cat = _group_by_subcategory(results)
    for key in sorted(by_cat.keys()):
        info = by_cat[key]
        print(f"     {key}: {info['count']}笔, {info['amount']:,.2f}元")
    _print_donation_alert(results)


# ============================================================
# 主流程
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="银行流水自动分类整理工具")
    parser.add_argument("file", help="银行流水文件路径（Excel 或 CSV）")
    parser.add_argument("--output", "-o", help="输出文件路径（默认: 原文件名_分类整理.csv）")

    args = parser.parse_args()

    file_path = args.file
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    if not args.output:
        stem = Path(file_path).stem
        output_path = str(Path(file_path).parent / f"{stem}_分类整理.csv")
    else:
        output_path = args.output

    print("=" * 60)
    print("🏦 银行流水自动分类整理工具")
    print("=" * 60)
    print(f"📄 输入文件: {file_path}")

    # 读取文件
    print("📖 正在读取文件...")
    rows = read_file(file_path)
    print(f"   读取到 {len(rows)} 行数据")

    if len(rows) < 2:
        print("⚠️ 数据行数不足，请检查文件内容")
        sys.exit(0)

    # 识别列
    print("🔍 正在识别列结构...")
    col_map = identify_columns(rows[0])
    identified = {k: v for k, v in col_map.items() if v is not None}
    print(f"   已识别列: {', '.join(identified.keys())}")

    if col_map["date"] is None:
        print("⚠️ 未识别到日期列，请检查表头是否包含'日期'字样")
    if col_map["amount"] is None and col_map["income"] is None:
        print("⚠️ 未识别到金额列，请检查表头是否包含'金额/贷方/借方'字样")

    # 处理交易
    print("⚙️ 正在分类处理...")
    results = process_transactions(rows, col_map)
    print(f"   处理了 {len(results)} 笔有效交易")

    # 输出汇总
    print_summary(results)

    # 生成文件
    print()
    print(f"💾 正在保存: {output_path}")
    generate_output(results, output_path)

    print()
    print("=" * 60)
    print("✅ 整理完成！")
    print(f"   📄 分类结果: {output_path}")
    print()
    print("⚡ 下一步:")
    print("   1. 打开CSV确认每笔交易的分类是否正确")
    print("   2. 核对'疑似捐赠收入'是否均已开具票据")
    print("   3. 关注'大额标记'的交易是否有审批记录")
    print("=" * 60)


if __name__ == "__main__":
    main()
