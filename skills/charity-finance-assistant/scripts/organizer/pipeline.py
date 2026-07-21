"""
v1.3 文件整理流水线：拆解原 organize_files（圈复杂度 24 → ≤ 5）。

拆解策略：
- _judge_data_status()    数据状态判断（独立逻辑）
- _archive_to_category()  归档到目录（含去重）
- _build_record()         构造单条台账记录
- _process_one_file()     处理单文件（圈复杂度 ≈ 4）
- organize_files()        只编排（圈复杂度 = 2）
"""
import shutil
from pathlib import Path

from organizer.config import IMAGE_EXTS, CATEGORY_ARCHIVE_DIR
from organizer.extractors import dispatch_extract
from organizer.classifier import (
    classify_file,
    suggest_expense_category,
    extract_date_from_name,
    extract_amount_from_name,
)


def _judge_data_status(ext, total_amt, issue_date, invoice_no):
    """
    数据状态判断（诚实原则）：
    - 图片 OCR → 默认需人工复核
    - 缺核心字段（金额/日期/号码任一缺失）→ 需人工复核
    - 否则 → 待复核
    圈复杂度 = 3。
    """
    if ext in IMAGE_EXTS:
        return "需人工复核（OCR）"
    core_missing = not (total_amt and issue_date and invoice_no)
    if core_missing:
        return "需人工复核（缺字段）"
    return "待复核"


def _archive_to_category(src, category, issue_date, output_root):
    """
    归档到对应类别目录，含同名冲突处理。
    圈复杂度 = 3（while 重命名循环）。
    """
    archive_dir = CATEGORY_ARCHIVE_DIR.get(category, "06_其他")
    cat_folder = output_root / archive_dir
    cat_folder.mkdir(parents=True, exist_ok=True)
    new_name = f"{issue_date}_{src.name}" if issue_date else src.name
    dest = cat_folder / new_name
    counter = 1
    while dest.exists():
        dest = cat_folder / f"{dest.stem}_{counter}{dest.suffix}"
        counter += 1
    shutil.copy2(str(src), str(dest))
    return dest


def _merge_field(extracted, name_fallback):
    """字段合并：抽取到的优先，文件名做兜底"""
    return extracted or name_fallback or ""


def _build_record(seq, src, dest, fields, category, expense_cat, data_status, parse_status):
    """构造单条台账记录"""
    tax_rate = fields.get("税率", "")
    tax_amt = fields.get("税额", "")
    return {
        "序号": seq,
        "票据类型": category,
        "票据名称": src.stem,
        "发票代码": fields.get("发票代码", ""),
        "发票号码": fields.get("发票号码", ""),
        "开票日期": fields.get("开票日期", ""),
        "购买方/捐赠方": fields.get("购买方/捐赠方", ""),
        "销售方/受赠方": fields.get("销售方/受赠方", ""),
        "货物或服务项目": "",  # 项目明细一般较长，需人工补录
        "不含税金额": "",
        "税率/税额": f"{tax_rate}/{tax_amt}" if tax_rate or tax_amt else "",
        "价税合计(元)": fields.get("价税合计", ""),
        "建议科目": expense_cat,
        "备注": "自动提取" if data_status == "待复核" else f"[{parse_status}] {data_status}",
        "数据状态": data_status,
        "原文件路径": str(src),
        "新文件路径": str(dest),
        "文件类型": src.suffix.lower(),
    }


def _process_one_file(src, output_root, seq):
    """
    处理单文件：抽取 → 分类 → 归档 → 生成记录。
    圈复杂度 ≈ 4（主要是字段合并）。
    """
    ext = src.suffix.lower()
    fields = dispatch_extract(src)
    raw_text = fields.get("_raw_text", "")
    parse_status = fields.get("_parse_status", "未解析")

    # 分类（内容优先，文件名兜底）
    category = classify_file(src, raw_text)
    expense_cat = suggest_expense_category(src, category)

    # 字段合并（抽取优先，文件名兜底）
    name_date = extract_date_from_name(src)
    name_amount = extract_amount_from_name(src)
    fields["开票日期"] = _merge_field(fields.get("开票日期", ""), name_date)
    if not fields.get("价税合计", "") and name_amount:
        fields["价税合计"] = str(name_amount)

    # 数据状态判断
    data_status = _judge_data_status(
        ext,
        fields.get("价税合计", ""),
        fields.get("开票日期", ""),
        fields.get("发票号码", ""),
    )

    # 归档
    dest = _archive_to_category(
        src, category, fields.get("开票日期", ""), output_root
    )

    return _build_record(
        seq, src, dest, fields, category, expense_cat, data_status, parse_status
    )


def organize_files(files, output_folder):
    """
    主编排：遍历文件 → 单文件处理 → 收集记录。
    圈复杂度 = 2（仅一个 for 循环）。
    """
    output_root = Path(output_folder)
    output_root.mkdir(parents=True, exist_ok=True)
    organized = []
    for f in files:
        record = _process_one_file(f, output_root, len(organized) + 1)
        organized.append(record)
    return organized
