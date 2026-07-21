#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 页面操作工具（旋转、裁剪）。
"""

import json
import sys
import os

COMMAND = "page_ops"
DESCRIPTION = "PDF 页面操作（旋转、裁剪），通过 action 参数选择操作类型。"
CATEGORY = "organize"
PARAMS = [
    {"name": "action", "type": "str", "required": True, "choices": ["rotate", "crop"], "help": "操作类型：rotate 或 crop"},
    {"name": "input", "type": "str", "required": True, "help": "输入 PDF 路径"},
    {"name": "output", "type": "str", "required": True, "help": "输出 PDF 路径"},
    {"name": "pages", "type": "json", "required": False, "help": "页码列表（从 0 开始），JSON 数组"},
    {"name": "angle", "type": "int", "required": False, "default": 90, "choices": [90, 180, 270, -90, -180, -270], "help": "旋转角度（rotate 时使用）"},
    {"name": "left", "type": "float", "required": False, "default": 0, "help": "裁剪左边界（crop 时使用）"},
    {"name": "bottom", "type": "float", "required": False, "default": 0, "help": "裁剪下边界（crop 时使用）"},
    {"name": "right", "type": "float", "required": False, "default": 612, "help": "裁剪右边界（crop 时使用）"},
    {"name": "top", "type": "float", "required": False, "default": 792, "help": "裁剪上边界（crop 时使用）"},
]


def rotate_pages(input_path, output_path, angle, pages=None):
    """旋转 PDF 页面。"""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(input_path)
    writer = PdfWriter()
    total_pages = len(reader.pages)

    if pages is None:
        pages = list(range(total_pages))

    rotated_count = 0
    for i, page in enumerate(reader.pages):
        if i in pages:
            page.rotate(angle)
            rotated_count += 1
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "success": True,
        "action": "rotate",
        "angle": angle,
        "rotated_pages": rotated_count,
        "total_pages": total_pages,
        "output": output_path
    }


def crop_pages(input_path, output_path, left, bottom, right, top, pages=None):
    """裁剪 PDF 页面。"""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(input_path)
    writer = PdfWriter()
    total_pages = len(reader.pages)

    if pages is None:
        pages = list(range(total_pages))

    cropped_count = 0
    for i, page in enumerate(reader.pages):
        if i in pages:
            page.mediabox.left = left
            page.mediabox.bottom = bottom
            page.mediabox.right = right
            page.mediabox.top = top
            cropped_count += 1
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return {
        "success": True,
        "action": "crop",
        "crop_box": {"left": left, "bottom": bottom, "right": right, "top": top},
        "cropped_pages": cropped_count,
        "total_pages": total_pages,
        "output": output_path
    }


def handler(params):
    """PDF 页面操作入口。

    Args:
        params: {
            "action": "rotate" | "crop",
            "input": 输入 PDF 路径,
            "output": 输出 PDF 路径,
            "pages": 页码列表（可选）,
            # rotate 专用
            "angle": 旋转角度,
            # crop 专用
            "left", "bottom", "right", "top": 裁剪边界
        }
    """
    action = params.get("action")
    input_path = params.get("input", "")
    output_path = params.get("output", "")
    pages = params.get("pages")

    if not input_path:
        raise ValueError("'input' 参数必填")
    if not output_path:
        raise ValueError("'output' 参数必填")
    if not os.path.exists(input_path):
        raise ValueError(f"文件不存在: {input_path}")

    if action == "rotate":
        angle = int(params.get("angle", 90))
        if angle not in [90, 180, 270, -90, -180, -270]:
            raise ValueError(f"不支持的旋转角度: {angle}，支持 90/180/270/-90/-180/-270")
        return rotate_pages(input_path, output_path, angle, pages)

    elif action == "crop":
        left = float(params.get("left", 0))
        bottom = float(params.get("bottom", 0))
        right = float(params.get("right", 612))
        top = float(params.get("top", 792))
        return crop_pages(input_path, output_path, left, bottom, right, top, pages)

    else:
        raise ValueError(f"未知操作: {action}，支持 rotate 或 crop")


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
