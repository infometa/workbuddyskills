"""
v1.3 报告生成模块：Markdown 汇总报告。

拆解策略：
- _compute_stats()       计算统计数据
- _build_overview()      生成"总体概况"段
- _build_categories()    生成"分类明细"段
- _build_manual_items()  生成"需人工处理事项"段
- generate_summary()     编排（圈复杂度 = 2）
"""
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def _is_numeric(s):
    return s and str(s).replace(".", "").replace("-", "").isdigit()


def _compute_stats(organized):
    """汇总统计"""
    total_amt = sum(
        float(x["价税合计(元)"])
        for x in organized
        if _is_numeric(x.get("价税合计(元)"))
    )
    return {
        "total_files": len(organized),
        "auto_extracted": sum(1 for x in organized if "自动提取" in x.get("备注", "")),
        "need_manual": sum(1 for x in organized if "需人工复核" in x.get("数据状态", "")),
        "total_amt": total_amt,
    }


def _group_by_category(organized):
    by_cat = defaultdict(list)
    for item in organized:
        by_cat[item["票据类型"]].append(item)
    return by_cat


def _build_overview(stats, ledger_path):
    """生成“总体概况”段"""
    lines = [
        "# 票据自动整理汇总报告",
        "",
        "> ⚠️ **警示**：本报告及配套台账中的金额、日期、发票号均由脚本自动提取，使用前必须人工逐张复核，复核通过后方可入账。",
        "",
        f"> 生成时间：{datetime.now():%Y-%m-%d %H:%M:%S}",
    ]
    if ledger_path:
        lines.append(f"> 台账文件：`{Path(ledger_path).name}`")
    lines.extend([
        "",
        "---",
        "",
        "## 一、总体概况",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 扫描文件总数 | **{stats['total_files']}** 张 |",
        f"| 字段自动提取成功 | {stats['auto_extracted']} 张 |",
        f"| 需人工复核（OCR / 缺字段） | {stats['need_manual']} 张 |",
        f"| 已抓取金额合计 | **¥{stats['total_amt']:,.2f}** |",
        "",
    ])
    return lines


def _build_categories_section(by_cat):
    """生成“分类明细”段"""
    lines = [
        "## 二、分类明细",
        "",
        "| 票据类型 | 张数 |",
        "|---------|:---:|",
    ]
    for cat in sorted(by_cat.keys()):
        lines.append(f"| {cat} | {len(by_cat[cat])} |")
    lines.append("")
    return lines


def _build_manual_section(organized):
    """生成“需人工处理事项”段"""
    lines = ["## 三、需人工处理事项", ""]
    manual_items = [
        x for x in organized if "需人工复核" in x.get("数据状态", "")
    ]
    if not manual_items:
        lines.append("✅ 本次整理所有票据核心字段均已自动提取，但仍建议逐行核对金额和日期。")
        lines.append("")
        return lines

    lines.append(f"### ⚠️ 以下 {len(manual_items)} 张票据需人工复核（OCR 或缺字段）：")
    lines.append("")
    lines.append("| 序号 | 文件名 | 票据类型 | 数据状态 | 建议科目 |")
    lines.append("|:-:|---|---|---|---|")
    for x in manual_items:
        lines.append(
            f"| {x['序号']} | {x['票据名称']} | {x['票据类型']} | "
            f"{x['数据状态']} | {x['建议科目']} |"
        )
    lines.extend([
        "",
        "> 复核要点：",
        "> 1. 金额：对照原票小数点、千分位、正负号",
        "> 2. 日期：注意年份跨度和格式（YYYY-MM-DD）",
        "> 3. 发票号：18 位纳税人识别号、8~20 位发票号码",
        "> 4. 复核后在台账「数据状态」列改为「已复核」",
        "",
    ])
    return lines


def _build_next_steps():
    """生成“下一步建议”段"""
    return [
        "## 四、下一步建议",
        "",
        "1. 打开 Excel 台账，逐行复核「发票代码、发票号码、开票日期」三个关键字段",
        "2. 将「数据状态」=「需人工复核」的行优先处理",
        "3. 增值税发票上国税平台查验（https://inv-veri.chinatax.gov.cn）",
        "4. 捐赠票据登记到《票据使用情况汇总表》，年末向财政部门申报核销",
        "",
        "---",
        "",
        "> 💡 本报告由 公益票据自动整理脚本 v1.3 生成。"
        "PDF 解析基于 pdfplumber，图片 OCR 基于 easyocr，DOCX 基于 python-docx。"
        "如需更高精度，建议使用腾讯云 OCR API。",
    ]


def generate_summary(organized, output_folder, ledger_path):
    """
    生成汇总报告 Markdown。
    圈复杂度 = 2（仅一次文件写入）。
    """
    output = Path(output_folder)
    summary_path = output / "整理汇总报告.md"

    stats = _compute_stats(organized)
    by_cat = _group_by_category(organized)

    lines = []
    lines.extend(_build_overview(stats, ledger_path))
    lines.extend(_build_categories_section(by_cat))
    lines.extend(_build_manual_section(organized))
    lines.extend(_build_next_steps())

    with open(str(summary_path), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return summary_path
