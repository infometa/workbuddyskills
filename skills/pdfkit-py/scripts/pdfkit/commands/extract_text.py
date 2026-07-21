#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取 PDF 文本内容。

- 有文字层的页面：直接提取文字层文本
- 纯扫描件页面（无文字层）：启用 --ocr_fallback 时自动 OCR 提取
- 混合型页面（文字层 + 嵌入图片）：仅提取文字层文本，不对图片做 OCR
"""

import os

COMMAND = "extract_text"
DESCRIPTION = "提取 PDF 文本内容，支持按页输出。仅对纯扫描件（无文字层）页面支持 --ocr_fallback OCR 降级，混合型页面中嵌入图片上的文字不会被提取"
CATEGORY = "read"

PARAMS = [
    {"name": "input",  "type": "str",  "required": True,  "help": "Input PDF path"},
    {"name": "pages",  "type": "json", "required": False, "help": "Page indices (0-based JSON array)"},
    {"name": "output", "type": "str",  "required": False, "help": "Output text file path (optional)"},
    {"name": "format", "type": "str",  "required": False, "default": "text",
     "choices": ["text", "dict", "blocks", "words", "html"], "help": "Output format"},
    {"name": "ocr_fallback", "type": "bool", "required": False, "default": False,
     "help": "当页面完全无文字层时自动使用 OCR 提取（仅针对纯扫描件页面，混合型页面中的图片不会 OCR，需要 tesseract）"},
    {"name": "lang", "type": "str", "required": False, "default": "eng+chi_sim",
     "help": "OCR 语言（仅 ocr_fallback=true 时生效）"},
]


def handler(params):
    import fitz
    import json

    input_path = params["input"]
    target_pages = params.get("pages")
    output_path = params.get("output")
    fmt = params.get("format", "text")
    ocr_fallback = params.get("ocr_fallback", False)
    ocr_lang = params.get("lang", "eng+chi_sim")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    doc = fitz.open(input_path)
    total_pages = len(doc)
    page_indices = target_pages if target_pages else list(range(total_pages))

    results = []
    total_chars = 0
    empty_pages = []  # 记录无文字的页面（可能是扫描件）
    ocr_pages = []    # 记录通过 OCR 提取的页面

    for i in page_indices:
        if i < 0 or i >= total_pages:
            continue
        page = doc[i]

        if fmt == "text":
            content = page.get_text("text")
        elif fmt == "dict":
            content = page.get_text("dict")
        elif fmt == "blocks":
            content = page.get_text("blocks")
        elif fmt == "words":
            content = page.get_text("words")
        elif fmt == "html":
            content = page.get_text("html")
        else:
            content = page.get_text("text")

        char_count = len(page.get_text("text").strip())
        total_chars += char_count

        # 检测无文字层页面（纯扫描件/图片型页面）
        # 注意：混合型页面（char_count > 0）不会触发 OCR，图片上的文字不提取
        if char_count == 0:
            empty_pages.append(i)

            # 自动 OCR 降级：仅当页面完全无文字层时才使用 OCR 提取
            if ocr_fallback and fmt == "text":
                ocr_text = _ocr_extract_page_text(page, ocr_lang)
                if ocr_text:
                    content = ocr_text
                    char_count = len(ocr_text.strip())
                    total_chars += char_count
                    ocr_pages.append(i)

        results.append({
            "page": i,
            "chars": char_count,
            "content": content,
            "source": "ocr" if i in ocr_pages else "text_layer",
        })

    doc.close()

    # 可选写入文件
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            if fmt == "text":
                for r in results:
                    f.write(f"--- Page {r['page']} ---\n")
                    f.write(r["content"])
                    f.write("\n")
            else:
                json.dump(results, f, ensure_ascii=False, indent=2)

    # 构建返回结果
    result = {
        "success": True,
        "pages_extracted": len(results),
        "total_chars": total_chars,
        "format": fmt,
        "output": output_path,
        "pages": results if fmt == "text" else None,
    }

    # 当存在空白页时，添加扫描件提示
    if empty_pages:
        # 过滤掉已通过 OCR 成功提取的页面
        still_empty = [p for p in empty_pages if p not in ocr_pages]
        result["empty_pages"] = empty_pages
        result["ocr_pages"] = ocr_pages

        if still_empty and not ocr_fallback:
            # 未启用 OCR 降级，提示用户
            result["hint"] = (
                f"检测到 {len(empty_pages)} 个页面完全无文字层（页码: {empty_pages}），"
                "这些页面可能是纯扫描件或图片型 PDF。"
                "请添加 --ocr_fallback 参数自动对这些页面进行 OCR 识别，"
                "或使用 ocr_locate 命令手动提取。"
                "注意：混合型页面（有文字层+嵌入图片）中图片上的文字不会被提取。"
                "示例：pdfkit.py extract_text --input <file> --pages '[0]' --ocr_fallback"
            )
        elif still_empty:
            # 启用了 OCR 但仍有页面提取失败
            result["hint"] = (
                f"OCR 降级已启用，但仍有 {len(still_empty)} 个页面无法提取文字（页码: {still_empty}）。"
                "请检查这些页面是否为空白页，或尝试调整 --lang 参数。"
            )

    return result


def _ocr_extract_page_text(page, lang="eng+chi_sim"):
    """对单个页面进行 OCR 提取纯文本。

    Args:
        page: fitz.Page 对象
        lang: OCR 语言

    Returns:
        提取的文本字符串，失败返回空字符串
    """
    try:
        import pytesseract
        from PIL import Image
        import io
        from pdfkit.commands.smart_edit import _check_tesseract_langs

        # 预检测 OCR 语言包
        _check_tesseract_langs(lang)

        # 渲染为 300 DPI 高清图片
        import fitz
        zoom = 300.0 / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        # OCR 识别，直接提取纯文本
        text = pytesseract.image_to_string(img, lang=lang)
        return text.strip()
    except ImportError:
        return ""
    except Exception as e:
        # OCR 失败不应阻断整个提取流程，返回空并在结果中体现
        import sys
        print(f"[warn] OCR 提取第 {page.number} 页失败: {e}", file=sys.stderr)
        return ""


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
