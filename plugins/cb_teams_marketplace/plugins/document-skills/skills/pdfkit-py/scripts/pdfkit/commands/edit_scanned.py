#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描件 PDF 文字编辑脚本。
通过 OCR 定位文字 → 图片处理覆盖 → 重写文字 → 替换回 PDF。
"""

import os
import sys

COMMAND = "edit_scanned"
DESCRIPTION = "扫描件 PDF 文字编辑，通过 OCR 定位 + 图片处理实现文字替换。"
CATEGORY = "edit"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "源 PDF 文件路径"},
    {"name": "output", "type": "str", "required": True, "help": "输出 PDF 文件路径"},
    {"name": "page", "type": "int", "required": False, "default": 0, "help": "目标页码（从 0 开始）"},
    {"name": "find", "type": "str", "required": True, "help": "要查找的文字"},
    {"name": "replace", "type": "str", "required": True, "help": "替换为的文字"},
    {"name": "font", "type": "str", "required": False, "default": "", "help": "字体路径（可选）"},
    {"name": "lang", "type": "str", "required": False, "default": "eng+chi_sim", "help": "OCR 语言"},
]


def handler(params):
    """编辑扫描件 PDF 中的文字。

    Args:
        params: {
            "input": 源 PDF 路径,
            "output": 输出 PDF 路径,
            "page": 目标页码（从 0 开始）,
            "find": 要查找的文字,
            "replace": 替换为的文字,
            "font": 字体路径（可选）,
            "lang": OCR 语言（默认 eng+chi_sim）
        }
    """
    import fitz
    import pytesseract
    from PIL import Image, ImageDraw, ImageFont
    import io
    import shutil
    from pdfkit.commands.smart_edit import _is_cjk, _check_tesseract_langs, _merge_ocr_texts, _get_pil_font

    input_path = params["input"]
    output_path = params["output"]
    page_num = params.get("page", 0)
    find_text = params["find"]
    replace_text = params["replace"]
    font_path = params.get("font", "")
    lang = params.get("lang", "eng+chi_sim")

    # P0 修复：预检测 OCR 语言包是否可用
    # 根据查找文本自动推断需要的语言包
    effective_lang = lang
    if any(_is_cjk(c) for c in find_text):
        if 'chi' not in lang:
            effective_lang = lang + '+chi_sim'
    _check_tesseract_langs(effective_lang)

    # 复制源文件
    shutil.copy2(input_path, output_path)

    doc = fitz.open(output_path)
    page = doc[page_num]

    # 1. 将页面渲染为 300 DPI 高清图片
    zoom = 300.0 / 72.0  # 300 DPI
    mat = fitz.Matrix(zoom, zoom)  # 300 DPI 缩放提高 OCR 精度
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))

    # 2. OCR 定位目标文字（使用检测后的语言包）
    ocr_data = pytesseract.image_to_data(img, lang=effective_lang, output_type=pytesseract.Output.DICT)

    # P0 修复：使用合并匹配算法，解决中文逐字识别问题
    found_regions = _merge_ocr_texts(ocr_data, find_text)

    if not found_regions:
        doc.close()
        return {
            "success": False,
            "message": f"未在第 {page_num} 页找到文字: {find_text}",
            "output": output_path
        }

    # 3. 在图片上覆盖原文字并绘制新文字
    draw = ImageDraw.Draw(img)
    scale = 300.0 / 72.0  # 与渲染缩放一致

    for region in found_regions:
        x, y, w, h = region['x'], region['y'], region['w'], region['h']

        # 采样背景色（取区域周围的像素）
        bg_samples = []
        for sx in range(max(0, x - 5), min(img.width, x + 5)):
            for sy in [max(0, y - 2), min(img.height - 1, y + h + 2)]:
                bg_samples.append(img.getpixel((sx, sy)))
        if bg_samples:
            bg_color = tuple(int(sum(c) / len(bg_samples)) for c in zip(*bg_samples))
        else:
            bg_color = (255, 255, 255)

        # 覆盖原文字区域
        padding = 2
        draw.rectangle([x - padding, y - padding, x + w + padding, y + h + padding], fill=bg_color)

        # P0 修复：使用支持 CJK 的字体绘制新文字
        font_size = max(int(h * 0.8), 12)
        font = _get_pil_font(font_path, font_size, replace_text)

        # 计算文字颜色（与背景对比）
        text_color = (0, 0, 0) if sum(bg_color[:3]) > 384 else (255, 255, 255)
        draw.text((x, y), replace_text, fill=text_color, font=font)

    # 4. 将修改后的图片替换回 PDF
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # 使用 clean_contents + insert_image（与 smart_edit.py 统一策略）
    rect = page.rect
    page.clean_contents()
    page.insert_image(rect, stream=img_bytes.getvalue())

    doc.saveIncr()
    doc.close()

    return {
        "success": True,
        "message": f"成功替换 {len(found_regions)} 处文字",
        "replacements": len(found_regions),
        "output": output_path
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
