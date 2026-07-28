#!/usr/bin/env python3
"""路演研究报告 docx 结构验证脚本。

用法: python3 validate_docx.py <docx文件路径> [公司名]
  - 公司名为可选参数；提供时会额外校验报告中是否包含该公司名，
    不提供时跳过公司名这一项检查（保持对任意标的通用）。

检查项:
1. 所有表格列数一致
2. 关键章节的 bullet 段落不为空
3. 基本结构元素存在
"""

import sys
import re
from zipfile import ZipFile
from xml.etree import ElementTree as ET

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def para_text(p):
    runs = p.findall('.//w:t', NS)
    return ''.join(t.text or '' for t in runs)

def check_tables(root):
    """检查所有表格列数一致"""
    tables = root.findall('.//w:tbl', NS)
    errors = []
    for ti, table in enumerate(tables):
        rows = table.findall('.//w:tr', NS)
        col_counts = {}
        for ri, row in enumerate(rows):
            nc = len(row.findall('.//w:tc', NS))
            col_counts.setdefault(nc, []).append(ri)
        if len(col_counts) > 1:
            details = " | ".join(f"{k}cols: rows {v}" for k, v in sorted(col_counts.items()))
            errors.append(f"❌ 表 {ti+1} 列数不一致: {details}")
        else:
            print(f"  ✅ 表 {ti+1}: {len(rows)}行 x {list(col_counts.keys())[0]}列")
    return errors

def check_section_content(paras, section_keyword, min_expected=1):
    """检查某节标题后的 bullet 段落是否有内容。
    section_keyword 格式如 '7.2'、'8.1'、'8.2'，会精确匹配 'X.Y ' 开头的标题。"""
    pattern = re.compile(rf"^{re.escape(section_keyword)}\s")
    for i, p in enumerate(paras):
        text = para_text(p)
        if pattern.search(text):
            found = 0
            for j in range(i+1, min(i+15, len(paras))):
                next_text = para_text(paras[j])
                # 跳过下一个节标题（如 7.3、8.1、报告完）
                if re.match(r"^\d+\.\d+\s", next_text.strip()) or '报告完' in next_text:
                    break
                if next_text.strip() and '免责声明' not in next_text:
                    found += 1
            return found >= min_expected, found
    return False, 0

def check_structure(paras, company_name=None):
    """检查基本结构元素。company_name 为可选，提供时才校验公司名。"""
    all_text = "\n".join(para_text(p) for p in paras)
    required = ["路演时间线", "公司概况", "业绩说明会", "时间线",
                "主题演变", "统计分析", "总结与展望", "免责声明"]
    if company_name:
        required.insert(0, company_name)
    missing = [k for k in required if k not in all_text]
    if missing:
        print(f"  ⚠️ 可能缺失的结构元素: {missing}")
    else:
        print("  ✅ 基本结构元素完整")

def main(docx_path, company_name=None):
    with ZipFile(docx_path) as z:
        with z.open('word/document.xml') as f:
            tree = ET.parse(f)
        root = tree.getroot()

    paras = root.findall('.//w:p', NS)
    all_errors = []

    print("\n📊 表格检查:")
    all_errors.extend(check_tables(root))

    print("\n📝 关键章节内容检查:")
    checks = [
        ("7.2", 4),
        ("8.1", 5),
        ("8.2", 2),
    ]
    for keyword, expected in checks:
        ok, found = check_section_content(paras, keyword, expected)
        if ok:
            print(f"  ✅ {keyword}: 找到 {found} 条内容")
        else:
            err = f"❌ {keyword}: 期望至少 {expected} 条但只有 {found} 条"
            print(err)
            all_errors.append(err)

    print("\n🏗️ 结构检查:")
    check_structure(paras, company_name)

    if all_errors:
        print(f"\n❌ 发现 {len(all_errors)} 个错误，请修复后重新生成！")
        sys.exit(1)
    else:
        print("\n✅ 所有检查通过！")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 validate_docx.py <docx文件路径> [公司名]")
        sys.exit(1)
    company = sys.argv[2] if len(sys.argv) >= 3 else None
    main(sys.argv[1], company)
