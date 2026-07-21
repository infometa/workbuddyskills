#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 文本搜索原子工具。
支持多引擎搜索：pymupdf / pdfplumber / fuzzy / ocr。
返回精确坐标 + 上下文 + 匹配方法，让 AI 可以看到匹配结果并决定后续策略。
"""

import os
import sys

COMMAND = "search_text"
DESCRIPTION = "PDF 文本搜索工具，支持多引擎（pymupdf/pdfplumber/fuzzy/ocr）。"
CATEGORY = "edit"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "find", "type": "str", "required": True, "help": "要查找的文本"},
    {"name": "page", "type": "int", "required": False, "default": -1, "help": "目标页码（从 0 开始，-1=全部页）"},
    {"name": "engine", "type": "str", "required": False, "default": "auto", "choices": ["pymupdf", "pdfplumber", "fuzzy", "ocr", "auto"], "help": "搜索引擎"},
    {"name": "ocr_engine", "type": "str", "required": False, "default": "auto", "choices": ["auto", "paddleocr", "tesseract"], "help": "OCR 引擎选择"},
]


def _ocr_search(doc, page, pg, input_path, find_text, lang="eng+chi_sim", ocr_engine="auto"):
    """使用 OCR 引擎在扫描件页面中搜索文本。

    将 OCR 识别的像素坐标转换为 PDF 坐标系，使结果可直接传给 pdf_overlay_text。

    Args:
        doc: fitz.Document 对象
        page: fitz.Page 对象
        pg: 页码
        input_path: PDF 文件路径
        find_text: 要查找的文本
        lang: OCR 语言
        ocr_engine: OCR 引擎 ("auto" / "paddleocr" / "tesseract")

    Returns:
        list: 匹配结果列表
    """
    import fitz
    from pdfkit.commands.smart_edit import _is_cjk, _check_tesseract_langs, _get_page_ocr, _merge_ocr_texts

    matches = []
    try:
        # 自动推断 OCR 语言
        effective_lang = lang
        if any(_is_cjk(c) for c in find_text):
            if 'chi' not in lang:
                effective_lang = lang + '+chi_sim'

        # 预检测语言包
        _check_tesseract_langs(effective_lang)

        # 获取 OCR 结果（带缓存，支持多引擎）
        img, ocr_data = _get_page_ocr(doc, page, pg, input_path, effective_lang, ocr_engine=ocr_engine)

        # 合并匹配
        found_regions = _merge_ocr_texts(ocr_data, find_text)

        if not found_regions:
            return matches

        # 像素坐标 → PDF 坐标转换
        # OCR 使用 300 DPI 渲染，zoom = 300 / 72 ≈ 4.1667
        zoom = 300.0 / 72.0
        page_height = page.rect.height

        for region in found_regions:
            px_x = region['x']
            px_y = region['y']
            px_w = region['w']
            px_h = region['h']

            # 像素坐标转 PDF 坐标
            # PDF 坐标系：原点在左下角，y 轴向上
            # 但 PyMuPDF 的 Rect 使用的是 (x0, y0, x1, y1)，y0 < y1，y0 在上方
            pdf_x0 = px_x / zoom
            pdf_y0 = px_y / zoom
            pdf_x1 = (px_x + px_w) / zoom
            pdf_y1 = (px_y + px_h) / zoom

            # 计算置信度（取涉及字符的平均置信度）
            confidence = 0.0
            conf_count = 0
            for blk in region.get('char_boxes', []):
                idx = blk.get('index', -1)
                if idx >= 0 and idx < len(ocr_data.get('conf', [])):
                    c = ocr_data['conf'][idx]
                    if c != '' and int(c) >= 0:
                        confidence += int(c)
                        conf_count += 1
            avg_confidence = round(confidence / conf_count, 1) if conf_count > 0 else 0.0

            matches.append({
                "page": pg,
                "engine": "ocr",
                "bbox": [round(pdf_x0, 2), round(pdf_y0, 2),
                         round(pdf_x1, 2), round(pdf_y1, 2)],
                "width": round(pdf_x1 - pdf_x0, 2),
                "height": round(pdf_y1 - pdf_y0, 2),
                "confidence": avg_confidence,
                "ocr_text": region.get('text', ''),
                "lang": effective_lang,
            })

    except RuntimeError as e:
        print(f"[WARN] OCR search failed: {e}", file=sys.stderr)
    except ImportError as e:
        print(f"[WARN] OCR dependencies missing: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] OCR search error: {e}", file=sys.stderr)

    return matches


def handler(params):
    """在 PDF 中搜索文本，返回精确坐标和上下文。

    Args:
        params: {
            "input": PDF 文件路径,
            "find": 要查找的文本,
            "page": 目标页码（从 0 开始，-1=全部页），默认 -1,
            "engine": 搜索引擎（pymupdf / pdfplumber / fuzzy / ocr / auto），默认 auto,
        }
    """
    import fitz
    from pdfkit.commands.smart_edit import _fuzzy_search

    input_path = params["input"]
    find_text = params["find"]
    page_num = params.get("page", -1)
    engine = params.get("engine", "auto")
    ocr_engine = params.get("ocr_engine", "auto")  # OCR 引擎选择: auto/paddleocr/tesseract

    doc = fitz.open(input_path)
    total_pages = len(doc)

    if page_num == -1:
        target_pages = list(range(total_pages))
    else:
        target_pages = [page_num]

    all_matches = []

    for pg in target_pages:
        if pg >= total_pages:
            continue
        page = doc[pg]

        matches = []

        # 文字层搜索引擎
        if engine in ("pymupdf", "auto"):
            instances = page.search_for(find_text)
            for rect in instances:
                matches.append({
                    "page": pg,
                    "engine": "pymupdf",
                    "bbox": [round(rect.x0, 2), round(rect.y0, 2),
                             round(rect.x1, 2), round(rect.y1, 2)],
                    "width": round(rect.width, 2),
                    "height": round(rect.height, 2),
                })

        if engine in ("fuzzy", "auto") and not matches:
            fuzzy_instances = _fuzzy_search(page, find_text)
            for rect in fuzzy_instances:
                matches.append({
                    "page": pg,
                    "engine": "fuzzy",
                    "bbox": [round(rect.x0, 2), round(rect.y0, 2),
                             round(rect.x1, 2), round(rect.y1, 2)],
                    "width": round(rect.width, 2),
                    "height": round(rect.height, 2),
                })

        if engine in ("pdfplumber", "auto") and not matches:
            try:
                import pdfplumber
                with pdfplumber.open(input_path) as pdf:
                    if pg < len(pdf.pages):
                        plumber_page = pdf.pages[pg]
                        hits = plumber_page.search(find_text, regex=False)
                        for hit in hits:
                            matches.append({
                                "page": pg,
                                "engine": "pdfplumber",
                                "bbox": [round(float(hit["x0"]), 2),
                                         round(float(hit["top"]), 2),
                                         round(float(hit["x1"]), 2),
                                         round(float(hit["bottom"]), 2)],
                                "width": round(float(hit["x1"]) - float(hit["x0"]), 2),
                                "height": round(float(hit["bottom"]) - float(hit["top"]), 2),
                            })
            except ImportError:
                pass
            except Exception as e:
                print(f"[WARN] pdfplumber search failed: {e}", file=sys.stderr)

        # OCR 引擎：对纯扫描件或文字层搜索无结果时使用
        if engine == "ocr" or (engine == "auto" and not matches):
            ocr_matches = _ocr_search(doc, page, pg, input_path, find_text, ocr_engine=ocr_engine)
            if ocr_matches:
                matches.extend(ocr_matches)

        # 获取上下文（文字层引擎）
        if matches:
            page_text = page.get_text("text")
            for m in matches:
                if m.get("engine") == "ocr":
                    # OCR 引擎的上下文使用 ocr_text 字段
                    if "ocr_text" not in m:
                        m["context"] = find_text
                    else:
                        m["context"] = m.get("ocr_text", find_text)
                else:
                    idx = page_text.find(find_text)
                    if idx >= 0:
                        ctx_start = max(0, idx - 20)
                        ctx_end = min(len(page_text), idx + len(find_text) + 20)
                        m["context"] = page_text[ctx_start:ctx_end].replace("\n", " ")

        all_matches.extend(matches)

    doc.close()

    return {
        "success": True,
        "find": find_text,
        "total_matches": len(all_matches),
        "matches": all_matches,
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
