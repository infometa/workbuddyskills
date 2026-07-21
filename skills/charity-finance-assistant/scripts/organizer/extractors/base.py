"""
v1.3 抽取器基础模块：共用的字段字典工厂 + 文本字段抽取辅助函数。

PDF 和 DOCX 共享同一套字段抽取逻辑（因为正则一致），
图片 OCR 使用单独的逻辑（在 image.py 中）。
"""
from organizer import patterns as P


# ============================================================
# 字段字典工厂
# ============================================================

FIELD_KEYS = (
    "发票代码",
    "发票号码",
    "开票日期",
    "购买方/捐赠方",
    "销售方/受赠方",
    "税率",
    "税额",
    "价税合计",
)


def empty_fields(parse_status="未解析"):
    """生成空字段字典（含解析状态）"""
    fields = {k: "" for k in FIELD_KEYS}
    fields["_raw_text"] = ""
    fields["_parse_status"] = parse_status
    return fields


# ============================================================
# 单字段抽取（每个函数圈复杂度 ≤ 3）
# ============================================================

def extract_invoice_code(text):
    m = P.RE_INVOICE_CODE.search(text)
    return m.group(1) if m else ""


def extract_invoice_no(text):
    m = P.RE_INVOICE_NO.search(text)
    return m.group(1) if m else ""


def extract_issue_date(text):
    """开票日期 → YYYY-MM-DD（解析失败返回空）"""
    m = P.RE_DATE.search(text)
    if not m:
        return ""
    y, mo, d = m.groups()
    try:
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    except ValueError:
        return ""


def extract_tax_rate(text):
    """税率：取首个非 100% 的匹配"""
    rates = P.RE_TAX_RATE.findall(text)
    for r in rates:
        if r != "100%":
            return r
    return ""


def extract_tax_amount(text):
    m = P.RE_TAX_AMOUNT.search(text)
    return m.group(1).replace(",", "") if m else ""


def extract_total_amount(text):
    """
    价税合计 5 级兜底（v1.3 用循环替代原 if-elif 链）：
    1~4) 按 AMOUNT_PATTERNS_PRIORITY 顺序尝试
    5) 兜底取全文最后一个 ¥XXX
    """
    for pat in P.AMOUNT_PATTERNS_PRIORITY:
        m = pat.search(text)
        if m:
            return m.group(1).replace(",", "")
    all_amounts = P.RE_ANY_AMOUNT.findall(text)
    if all_amounts:
        return all_amounts[-1].replace(",", "")
    return ""


def extract_buyer(text):
    m = P.RE_BUYER_NAME.search(text)
    return m.group(1).strip() if m else ""


def extract_seller(text):
    m = P.RE_SELLER_NAME.search(text)
    return m.group(1).strip() if m else ""


# ============================================================
# 字段表驱动抽取（圈复杂度 = 2）
# ============================================================

# 字段名 → 抽取函数 的映射
FIELD_EXTRACTORS = {
    "发票代码": extract_invoice_code,
    "发票号码": extract_invoice_no,
    "开票日期": extract_issue_date,
    "税率": extract_tax_rate,
    "税额": extract_tax_amount,
    "价税合计": extract_total_amount,
    "购买方/捐赠方": extract_buyer,
    "销售方/受赠方": extract_seller,
}


def fill_fields_from_text(fields, text):
    """
    用字段抽取器表填充 fields 字典。
    圈复杂度 = 2（只有 for 循环 + 一次空值跳过）。
    """
    for key, fn in FIELD_EXTRACTORS.items():
        value = fn(text)
        if value:
            fields[key] = value
    return fields
