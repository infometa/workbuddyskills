#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 公式识别（LaTeX）脚本。

从 PDF 中识别数学公式并转换为 LaTeX 格式。
使用 pix2tex 或 nougat 模型进行公式识别。

依赖：PyMuPDF (fitz), pix2tex (可选), Pillow
"""

import os
import io

COMMAND = "formula_detect"
DESCRIPTION = "从 PDF 中识别数学公式区域，支持启发式和模型两种检测方式"
CATEGORY = "read"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "pages", "type": "json", "required": False, "help": "页码列表（从 0 开始），默认全部页"},
    {"name": "method", "type": "str", "required": False, "default": "heuristic", "choices": ["heuristic", "model"], "help": "检测方法"},
]


def handler(params):
    """检测 PDF 中的数学公式区域。

    Args:
        params: {
            "input": PDF 文件路径,
            "pages": 页码列表，None 表示全部页,
            "method": 检测方法 - "heuristic"(启发式), "model"(模型)
        }
    """
    import fitz
    from PIL import Image

    input_path = params["input"]
    pages = params.get("pages", None)
    method = params.get("method", "heuristic")

    doc = fitz.open(input_path)
    total_pages = len(doc)

    if pages is None:
        pages = list(range(total_pages))

    formulas = []

    for p_idx in pages:
        if p_idx < 0 or p_idx >= total_pages:
            continue
        page = doc[p_idx]

        if method == "heuristic":
            # 启发式检测：查找包含数学符号的文本块
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block["type"] != 0:
                    continue
                for line in block.get("lines", []):
                    line_text = ""
                    has_math_font = False
                    for span in line.get("spans", []):
                        line_text += span["text"]
                        # 检测数学字体
                        font_name = span.get("font", "").lower()
                        if any(mf in font_name for mf in ["math", "symbol", "cmmi", "cmsy", "cmex"]):
                            has_math_font = True

                    # 检测数学符号
                    math_chars = set("∑∏∫∂∇√∞±≤≥≠≈∈∉⊂⊃∪∩αβγδεζηθικλμνξπρστυφχψω")
                    has_math_symbols = bool(set(line_text) & math_chars)

                    # 检测 LaTeX 风格的公式标记
                    has_latex_markers = any(m in line_text for m in ["\\frac", "\\sum", "\\int", "^{", "_{"])

                    if has_math_font or has_math_symbols or has_latex_markers:
                        bbox = line["bbox"]
                        formulas.append({
                            "page": p_idx,
                            "text": line_text.strip(),
                            "bbox": list(bbox),
                            "type": "inline" if len(line_text) < 50 else "display",
                            "confidence": 0.8 if has_math_font else 0.6,
                            "detection_method": "heuristic"
                        })

        elif method == "model":
            # 模型检测：渲染页面为图片，使用 pix2tex 识别
            mat = fitz.Matrix(2, 2)  # 2x 缩放
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            try:
                from pix2tex.cli import LatexOCR
                model = LatexOCR()
                # 对整页进行识别
                latex = model(img)
                if latex:
                    formulas.append({
                        "page": p_idx,
                        "latex": latex,
                        "type": "page_level",
                        "confidence": 0.9,
                        "detection_method": "pix2tex"
                    })
            except ImportError:
                # pix2tex 未安装，回退到启发式
                formulas.append({
                    "page": p_idx,
                    "error": "pix2tex 未安装，请执行: pip install pix2tex",
                    "detection_method": "model_unavailable"
                })

    doc.close()

    return {
        "success": True,
        "total_formulas": len(formulas),
        "formulas": formulas,
        "method": method,
        "metadata": {
            "file": os.path.basename(input_path),
            "total_pages": total_pages,
            "pages_scanned": len(pages)
        }
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
