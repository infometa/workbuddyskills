#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 文字定位脚本。
使用 pytesseract 识别 PDF 页面中的文字及其精确坐标。
"""

import os
import sys

# smart_edit 辅助函数从 lite 包导入
from pdfkit.commands.smart_edit import _is_cjk, _check_tesseract_langs

COMMAND = "ocr_locate"
DESCRIPTION = "OCR 定位 PDF 页面中的文字位置，支持 CJK 文本"
CATEGORY = "read"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "page", "type": "int", "required": False, "default": 0, "help": "目标页码（从 0 开始）"},
    {"name": "text", "type": "str", "required": False, "default": "", "help": "要定位的文字（不填返回全部 OCR 结果）"},
    {"name": "lang", "type": "str", "required": False, "default": "eng+chi_sim", "help": "OCR 语言"},
]


def handler(params):
    """OCR 定位 PDF 页面中的文字位置。

    Args:
        params: {
            "input": PDF 路径,
            "page": 目标页码（从 0 开始）,
            "text": 要定位的文字（可选，不填返回全部 OCR 结果）,
            "lang": OCR 语言（默认 eng+chi_sim）
        }
    """
    import fitz
    import pytesseract
    from PIL import Image
    import io

    input_path = params["input"]
    page_num = params.get("page", 0)
    target_text = params.get("text", "")
    lang = params.get("lang", "eng+chi_sim")

    # P0 修复：预检测 OCR 语言包是否可用
    # 根据目标文本自动推断需要的语言包
    effective_lang = lang
    if target_text and any(_is_cjk(c) for c in target_text):
        if 'chi' not in lang:
            effective_lang = lang + '+chi_sim'
    _check_tesseract_langs(effective_lang)

    doc = fitz.open(input_path)
    page = doc[page_num]

    # 渲染为 300 DPI 高清图片
    zoom = 300.0 / 72.0  # 300 DPI
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))

    # OCR 识别（使用检测后的语言包）
    ocr_data = pytesseract.image_to_data(img, lang=effective_lang, output_type=pytesseract.Output.DICT)

    scale = 300.0 / 72.0  # 与渲染缩放一致
    page_width = page.rect.width
    page_height = page.rect.height

    # 构建结果
    blocks = []
    n_boxes = len(ocr_data['text'])

    for i in range(n_boxes):
        text = ocr_data['text'][i].strip()
        if not text:
            continue

        conf = int(ocr_data['conf'][i])
        if conf < 0:
            continue

        # 将像素坐标转换为 PDF 坐标（考虑缩放）
        x = ocr_data['left'][i] / scale
        y = ocr_data['top'][i] / scale
        w = ocr_data['width'][i] / scale
        h = ocr_data['height'][i] / scale

        block = {
            "text": text,
            "x": round(x, 1),
            "y": round(y, 1),
            "width": round(w, 1),
            "height": round(h, 1),
            "confidence": conf,
            "level": ocr_data['level'][i],
            "block_num": ocr_data['block_num'][i],
            "line_num": ocr_data['line_num'][i],
            "word_num": ocr_data['word_num'][i],
        }
        blocks.append(block)

    doc.close()

    # 如果指定了目标文字，过滤匹配结果
    if target_text:
        matched = []
        target_lower = target_text.lower()

        # 精确匹配
        for block in blocks:
            if target_lower in block["text"].lower():
                block["match_type"] = "exact"
                matched.append(block)

        # 如果精确匹配失败，尝试连续词匹配（支持 CJK 逐字合并）
        if not matched:
            # P0 修复：对于 CJK 文本，不加空格拼接
            full_text_parts = []
            for b in blocks:
                if full_text_parts:
                    last_char = full_text_parts[-1][-1] if full_text_parts[-1] else ''
                    first_char = b["text"][0] if b["text"] else ''
                    if _is_cjk(last_char) or _is_cjk(first_char):
                        full_text_parts.append(b["text"])
                    else:
                        full_text_parts.append(" " + b["text"])
                else:
                    full_text_parts.append(b["text"])
            full_text = "".join(full_text_parts)

            if target_lower in full_text.lower():
                # 找到连续的词组成目标文本
                for i, block in enumerate(blocks):
                    combined = block["text"]
                    region = {
                        "text": combined,
                        "x": block["x"],
                        "y": block["y"],
                        "width": block["width"],
                        "height": block["height"],
                        "confidence": block["confidence"],
                    }
                    for j in range(i + 1, min(i + 10, len(blocks))):
                        next_text = blocks[j]["text"]
                        # P0 修复：CJK 字符之间不加空格
                        if combined and next_text:
                            if _is_cjk(combined[-1]) or _is_cjk(next_text[0]):
                                combined += next_text
                            else:
                                combined += " " + next_text
                        else:
                            combined += next_text
                        region["width"] = (blocks[j]["x"] + blocks[j]["width"]) - region["x"]
                        region["height"] = max(region["height"], blocks[j]["height"])
                        region["text"] = combined

                        if target_lower in combined.lower():
                            region["match_type"] = "combined"
                            matched.append(region)
                            break

        return {
            "page": page_num,
            "page_size": {"width": round(page_width, 1), "height": round(page_height, 1)},
            "target": target_text,
            "matches": matched,
            "match_count": len(matched),
        }

    return {
        "page": page_num,
        "page_size": {"width": round(page_width, 1), "height": round(page_height, 1)},
        "blocks": blocks,
        "total_blocks": len(blocks),
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
