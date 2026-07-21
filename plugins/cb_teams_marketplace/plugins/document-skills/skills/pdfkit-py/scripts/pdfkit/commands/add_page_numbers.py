#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 添加页码脚本。

为 PDF 每页添加页码，支持自定义位置、格式和样式。

依赖：PyMuPDF (fitz)
"""

import os
import sys

COMMAND = "add_page_numbers"
DESCRIPTION = "为 PDF 每页添加页码，支持自定义位置、格式和样式。"
CATEGORY = "edit"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "输入 PDF 路径"},
    {"name": "output", "type": "str", "required": True, "help": "输出 PDF 路径"},
    {"name": "position", "type": "str", "required": False, "default": "bottom_center", "choices": ["bottom_center", "bottom_left", "bottom_right", "top_center", "top_left", "top_right"], "help": "页码位置"},
    {"name": "format", "type": "str", "required": False, "default": "{page} / {total}", "help": "页码格式，支持 {page} 和 {total} 占位符"},
    {"name": "start_number", "type": "int", "required": False, "default": 1, "help": "起始页码"},
    {"name": "font_size", "type": "int", "required": False, "default": 10, "help": "字号"},
    {"name": "font_color", "type": "json", "required": False, "default": [0, 0, 0], "help": "字体颜色 [r, g, b]，0-1 范围"},
    {"name": "margin", "type": "int", "required": False, "default": 36, "help": "页边距（点）"},
    {"name": "pages", "type": "json", "required": False, "help": "指定页码列表，不指定表示全部页"},
    {"name": "font_path", "type": "str", "required": False, "help": "字体文件路径（中文页码需要）"},
]


def add_page_numbers(input_path, output_path, position="bottom_center",
                     format_str="{page} / {total}", start_number=1,
                     font_size=10, font_color=(0, 0, 0), margin=36,
                     pages=None, font_path=None):
    """为 PDF 添加页码。

    Args:
        input_path: 输入 PDF 路径
        output_path: 输出 PDF 路径
        position: 页码位置 - bottom_center, bottom_left, bottom_right,
                  top_center, top_left, top_right
        format_str: 页码格式，支持 {page} 和 {total} 占位符
        start_number: 起始页码
        font_size: 字号
        font_color: 字体颜色 (r, g, b)，0-1 范围
        margin: 页边距（点）
        pages: 指定页码列表，None 表示全部页
        font_path: 字体文件路径（中文页码需要）
    """
    import fitz  # PyMuPDF

    doc = fitz.open(input_path)
    total_pages = len(doc)

    if pages is None:
        pages = list(range(total_pages))

    pages_numbered = 0

    for i, p_idx in enumerate(pages):
        if p_idx < 0 or p_idx >= total_pages:
            continue
        page = doc[p_idx]
        page_rect = page.rect

        # 生成页码文本
        page_num = start_number + i
        text = format_str.replace("{page}", str(page_num)).replace("{total}", str(len(pages)))

        # 计算位置
        if "bottom" in position:
            y = page_rect.height - margin
        else:
            y = margin + font_size

        if "center" in position:
            # 居中需要计算文本宽度
            text_width = fitz.get_text_length(text, fontsize=font_size)
            x = (page_rect.width - text_width) / 2
        elif "right" in position:
            text_width = fitz.get_text_length(text, fontsize=font_size)
            x = page_rect.width - margin - text_width
        else:
            x = margin

        point = fitz.Point(x, y)

        # 插入页码文本
        if font_path and os.path.exists(font_path):
            # 对 .ttc 字体集合，需通过 fontbuffer 指定正确的子字体
            if font_path.lower().endswith('.ttc'):
                from pdfkit.font_manager import get_font_index
                _idx = get_font_index(font_path)
                _font_obj = fitz.Font(fontfile=font_path, fontindex=_idx)
                page.insert_text(point, text, fontsize=font_size,
                               color=font_color, fontbuffer=_font_obj.buffer)
            else:
                page.insert_text(point, text, fontsize=font_size,
                               color=font_color, fontfile=font_path)
        else:
            # 自动查找系统中文字体
            from pdfkit.font_manager import resolve_font
            auto_font_path = resolve_font(require_full_cjk=True)
            if auto_font_path:
                if auto_font_path.lower().endswith('.ttc'):
                    from pdfkit.font_manager import get_font_index
                    _idx = get_font_index(auto_font_path)
                    _font_obj = fitz.Font(fontfile=auto_font_path, fontindex=_idx)
                    page.insert_text(point, text, fontsize=font_size,
                                   color=font_color, fontbuffer=_font_obj.buffer)
                else:
                    page.insert_text(point, text, fontsize=font_size,
                                   color=font_color, fontfile=auto_font_path)
                print(f"[add_page_numbers] 自动使用中文字体: {auto_font_path}", file=sys.stderr)
            else:
                page.insert_text(point, text, fontsize=font_size,
                               color=font_color)

        pages_numbered += 1

    doc.save(output_path)
    file_size = os.path.getsize(output_path)
    doc.close()

    return {
        "success": True,
        "pages_numbered": pages_numbered,
        "position": position,
        "format": format_str,
        "output": output_path,
        "file_size": file_size
    }


def handler(params):
    """处理 PDF 添加页码请求。"""
    input_path = params.get("input", "")
    output_path = params.get("output", "")

    if not input_path or not output_path:
        raise ValueError("'input' 和 'output' 参数必填")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    position = params.get("position", "bottom_center")
    format_str = params.get("format", "{page} / {total}")
    start_number = params.get("start_number", 1)
    font_size = params.get("font_size", 10)
    font_color = tuple(params.get("font_color", [0, 0, 0]))
    margin = params.get("margin", 36)
    pages = params.get("pages")
    font_path = params.get("font_path")

    return add_page_numbers(input_path, output_path, position, format_str,
                            start_number, font_size, font_color, margin,
                            pages, font_path)


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
