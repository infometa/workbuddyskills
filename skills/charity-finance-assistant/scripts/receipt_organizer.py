#!/usr/bin/env python3
"""
票据自动扫描与分类整理脚本 v1.3

⚠️ 重要警示：脚本输出仅供预分类与打草稿。
    金额、日期、发票号任一字段都必须由财务人工逐张复核，
    复核通过才能进入会计系统入账。

v1.3 更新（圈复杂度优化 + 模块化）:
- 把 1049 行单文件拆为 organizer/ 包：config / patterns / extractors / classifier / pipeline / ledger / reporter
- 关键函数圈复杂度全部降到 ≤ 8（原 extract_image_fields 30 → 5，extract_pdf_fields 25 → 4，organize_files 24 → 2）
- 删除冗余、统一字段抽取流程、修 _build_templates.py CRLF + 未使用 import
- CLI 完全保持兼容：参数、行为、输出格式不变

v1.2 更新:
- 修复金额截断 bug、新增 DOCX、复核清单诚实化、6 大类归档落地

用法:
    python receipt_organizer.py <票据文件夹路径> [--output <输出文件夹路径>]
    python receipt_organizer.py <票据文件夹路径> --scan-only

依赖:
    pip install pdfplumber openpyxl python-docx easyocr pillow
"""
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# 让脚本能在 scripts/ 目录下直接运行（导入同级 organizer 包）
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from organizer.config import ALL_SUPPORTED, EXCLUDE_PATTERNS  # noqa: E402
from organizer.classifier import classify_file  # noqa: E402
from organizer.pipeline import organize_files  # noqa: E402
from organizer.ledger import (  # noqa: E402
    generate_ledger_xlsx,
    generate_ledger_csv,
    HAS_OPENPYXL,
)
from organizer.reporter import generate_summary  # noqa: E402
from organizer.extractors.pdf import HAS_PDFPLUMBER  # noqa: E402
from organizer.extractors.docx import HAS_DOCX  # noqa: E402


def _setup_utf8_stdout():
    """Windows PowerShell 默认 GBK 不支持部分 emoji，强制 UTF-8"""
    if sys.platform != "win32":
        return
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def _print_dependency_warnings():
    """开机时检查依赖并打印警告"""
    if not HAS_PDFPLUMBER:
        print("  [WARN] pdfplumber 未安装，PDF 字段提取将被跳过。建议: pip install pdfplumber")
    if not HAS_OPENPYXL:
        print("  [WARN] openpyxl 未安装，将回退到 CSV 输出。建议: pip install openpyxl")
    if not HAS_DOCX:
        print("  [WARN] python-docx 未安装，DOCX 支持将被跳过。建议: pip install python-docx")


def _scan_files(folder):
    """扫描文件夹，过滤排除模式，返回受支持的文件列表"""
    files = []
    for f in folder.rglob("*"):
        if any(p in str(f) for p in EXCLUDE_PATTERNS):
            continue
        if f.is_file() and f.suffix.lower() in ALL_SUPPORTED:
            files.append(f)
    return files


def _print_classification_preview(files):
    """打印分类预览（圈复杂度 = 2）"""
    preview = defaultdict(int)
    for f in files:
        preview[classify_file(f)] += 1
    print()
    print("📊 分类预览:")
    for cat, count in sorted(preview.items()):
        print(f"   {cat}: {count} 个")


def _resolve_output_folder(folder_path, output_arg):
    """决定输出目录"""
    if output_arg:
        return output_arg
    return os.path.join(folder_path, f"整理结果_{datetime.now():%Y%m%d_%H%M%S}")


def _generate_ledger(organized, output_folder):
    """生成台账（优先 Excel，回落 CSV）"""
    if HAS_OPENPYXL:
        return generate_ledger_xlsx(organized, output_folder)
    return generate_ledger_csv(organized, output_folder)


def _print_completion(output_folder, organized):
    """打印完成统计"""
    pdf_ok = sum(1 for x in organized if "自动提取" in x.get("备注", ""))
    need_manual = sum(1 for x in organized if "需人工复核" in x.get("数据状态", ""))
    print()
    print("=" * 60)
    print("✅ 整理完成！")
    print(f"   📂 结果目录: {output_folder}")
    print(f"   📊 字段自动提取: {pdf_ok} 张")
    print(f"   ⚠️  需人工复核: {need_manual} 张（OCR / 缺字段）")
    print("   ⚠️  脚本金额必须人工逐张复核后方可入账")
    print("=" * 60)


def _parse_args():
    """CLI 参数（与 v1.2 完全兼容）"""
    import argparse
    parser = argparse.ArgumentParser(
        description="票据自动扫描与分类整理工具 v1.3（含发票要素自动提取）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("folder", help="要扫描的票据文件夹路径")
    parser.add_argument("--output", "-o", help="输出文件夹路径")
    parser.add_argument("--scan-only", action="store_true", help="仅扫描统计，不复制文件")
    return parser.parse_args()


def main():
    """
    主流程入口（圈复杂度 ≈ 6）。
    所有业务逻辑都委托给 organizer 子模块。
    """
    _setup_utf8_stdout()
    args = _parse_args()

    folder_path = args.folder
    output_folder = _resolve_output_folder(folder_path, args.output)

    print("=" * 60)
    print("[INFO] 票据自动扫描与分类整理工具 v1.3")
    print("=" * 60)
    print(f"扫描目录: {folder_path}")
    _print_dependency_warnings()
    print()

    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ 文件夹不存在: {folder_path}")
        sys.exit(1)

    files = _scan_files(folder)
    print(f"🔍 找到 {len(files)} 个支持的文件")
    _print_classification_preview(files)

    if args.scan_only:
        print()
        print("✅ 扫描完成（仅扫描模式）")
        return

    print()
    print(f"📂 正在整理到: {output_folder}")
    organized = organize_files(files, output_folder)
    print(f"   归档 {len(organized)} 个文件")

    print()
    print("📝 正在生成台账...")
    ledger_path = _generate_ledger(organized, output_folder)
    print(f"   台账: {ledger_path}")

    summary_path = generate_summary(organized, output_folder, ledger_path)
    print(f"   报告: {summary_path}")

    _print_completion(output_folder, organized)


if __name__ == "__main__":
    main()
