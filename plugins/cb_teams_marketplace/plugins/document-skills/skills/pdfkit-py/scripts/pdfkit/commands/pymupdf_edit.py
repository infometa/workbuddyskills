#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyMuPDF 文本编辑 fallback 脚本。
当 C++ PDFium 引擎无法完成编辑时（如跨 span 匹配失败），
使用 PyMuPDF 的 redact + TextWriter 方案作为备选。
"""

import os
import sys

COMMAND = "pymupdf_edit"
DESCRIPTION = "PyMuPDF 文本编辑 fallback，使用 redact + TextWriter 方案。"
CATEGORY = "edit"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "源 PDF 文件路径"},
    {"name": "output", "type": "str", "required": True, "help": "输出 PDF 文件路径"},
    {"name": "edits", "type": "json", "required": True, "help": "编辑操作列表 JSON 数组"},
]


def handler(params):
    """使用 PyMuPDF 编辑 PDF 文本。

    Args:
        params: {
            "input": 源 PDF 路径,
            "output": 输出 PDF 路径,
            "edits": [
                {
                    "page": 页码（从 0 开始，-1 表示全部页），
                    "find": 查找文本,
                    "replace": 替换文本,
                    "font_size": 字号（可选）,
                    "font_path": 字体路径（可选）
                }
            ]
        }
    """
    import fitz
    import shutil
    from pdfkit.commands.smart_edit import _find_cjk_font_path

    input_path = params["input"]
    output_path = params["output"]
    edits = params.get("edits", [])

    if not edits:
        return {"success": False, "error": "未提供编辑操作", "replacements": 0}

    # 复制源文件
    shutil.copy2(input_path, output_path)

    doc = fitz.open(output_path)
    total_replacements = 0

    for edit in edits:
        page_num = edit.get("page", -1)
        find_text = edit.get("find", "")
        replace_text = edit.get("replace", "")
        font_size = edit.get("font_size", 0)
        font_path = edit.get("font_path", "")

        if not find_text:
            continue

        # 确定目标页面
        if page_num == -1:
            target_pages = range(len(doc))
        else:
            target_pages = [page_num]

        for pn in target_pages:
            if pn >= len(doc):
                continue

            page = doc[pn]

            # 搜索文本位置
            text_instances = page.search_for(find_text)
            if not text_instances:
                continue

            for inst in text_instances:
                # 获取原始文本的字体信息
                original_size = font_size
                if original_size <= 0:
                    # 尝试从页面文本中获取字号
                    blocks = page.get_text("dict")["blocks"]
                    for block in blocks:
                        if block.get("type") != 0:
                            continue
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                if find_text in span.get("text", ""):
                                    original_size = span.get("size", 12)
                                    break
                            if original_size > 0:
                                break
                        if original_size > 0:
                            break
                    if original_size <= 0:
                        original_size = 11

                # 使用 redact 删除原文本
                annot = page.add_redact_annot(inst)
                page.apply_redactions()

                # 使用 TextWriter 写入新文本
                tw = fitz.TextWriter(page.rect)

                # 选择字体（复用 smart_edit 的统一字体查找逻辑）
                from pdfkit.font_manager import make_fitz_font
                if font_path and os.path.exists(font_path):
                    font = make_fitz_font(font_path)
                else:
                    cjk_path = _find_cjk_font_path()
                    if cjk_path:
                        try:
                            font = make_fitz_font(cjk_path)
                        except Exception:
                            font = fitz.Font("helv")
                    else:
                        print(
                            f"[WARN] pymupdf_edit: 未找到 CJK 中文字体，中文文字可能显示异常。"
                            f"请安装中文字体或将字体文件放入 {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')} 目录",
                            file=sys.stderr
                        )
                        font = fitz.Font("helv")

                # 在原位置写入新文本
                insert_point = fitz.Point(inst.x0, inst.y1 - 2)
                tw.append(insert_point, replace_text, font=font, fontsize=original_size)
                tw.write_text(page)

                total_replacements += 1

    # 增量保存
    if total_replacements > 0:
        doc.saveIncr()

    doc.close()

    return {
        "success": True,
        "replacements": total_replacements,
        "engine": "pymupdf",
        "output": output_path,
        "message": f"成功替换 {total_replacements} 处文本（PyMuPDF fallback）"
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
