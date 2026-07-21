#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF IR 精准修改。

直接修改 PDF 中的低级对象（文本替换、图片替换、注释操作等），
无需导出/导入完整 IR。适用于精确、可控的文档修改。
"""

import os

COMMAND = "ir_modify"
DESCRIPTION = "Modify PDF objects directly (text replace, image swap, annotations)"
CATEGORY = "ir"

PARAMS = [
    {"name": "input",  "type": "str",  "required": True,  "help": "Input PDF path"},
    {"name": "output", "type": "str",  "required": True,  "help": "Output PDF path"},
    {"name": "operations", "type": "json", "required": True,
     "help": "JSON array of modification operations"},
]


def _op_replace_text(doc, page, op):
    """替换文本（基于 search_for + redact + TextWriter）。"""
    import fitz

    find = op.get("find", "")
    replace = op.get("replace", "")
    if not find:
        return {"success": False, "error": "find is empty"}

    instances = page.search_for(find)
    if not instances:
        return {"success": False, "error": f"Text not found: {find}"}

    # 获取原始字号
    font_size = 12
    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if find in span.get("text", ""):
                    font_size = span.get("size", 12)
                    break

    # Redact + rewrite
    for rect in instances:
        page.add_redact_annot(rect, fill=(1, 1, 1))
    page.apply_redactions()

    tw = fitz.TextWriter(page.rect)
    font = fitz.Font("helv")
    replaced = 0
    for rect in instances:
        try:
            tw.append(fitz.Point(rect.x0, rect.y1 - 2), replace,
                      font=font, fontsize=font_size)
            replaced += 1
        except Exception:
            pass
    tw.write_text(page, color=(0, 0, 0))

    return {"success": True, "replaced": replaced}


def _op_replace_image(doc, page, op):
    """替换指定页上的图片实例，避免修改共享 xref 影响其他页面。"""
    import fitz

    image_index = op.get("image_index", 0)
    new_image = op.get("new_image", "")

    if not new_image or not os.path.exists(new_image):
        return {"success": False, "error": f"Image not found: {new_image}"}

    images = page.get_images(full=True)
    if image_index >= len(images):
        return {"success": False, "error": f"Image index {image_index} out of range ({len(images)})"}

    try:
        image_info = images[image_index]
        xref = image_info[0]
        image_name = image_info[7] if len(image_info) > 7 else xref

        rects = page.get_image_rects(image_name)
        if not rects:
            rects = page.get_image_rects(xref)
        if not rects:
            return {"success": False, "error": f"Image instance not found for index {image_index}"}

        target_rect = rects[0]
        page.add_redact_annot(target_rect, fill=(1, 1, 1))
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE, text=fitz.PDF_REDACT_TEXT_NONE)
        page.insert_image(target_rect, filename=new_image, overlay=True)

        return {
            "success": True,
            "xref": xref,
            "rect": [
                round(target_rect.x0, 2),
                round(target_rect.y0, 2),
                round(target_rect.x1, 2),
                round(target_rect.y1, 2),
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _op_add_annotation(doc, page, op):
    """添加注释。"""
    import fitz

    annot_type = op.get("annot_type", "text")
    rect = fitz.Rect(op.get("rect", [50, 50, 200, 80]))
    content = op.get("content", "")

    try:
        if annot_type == "highlight":
            annot = page.add_highlight_annot(rect)
        elif annot_type == "strikeout":
            annot = page.add_strikeout_annot(rect)
        elif annot_type == "underline":
            annot = page.add_underline_annot(rect)
        elif annot_type == "rect":
            annot = page.add_rect_annot(rect)
        elif annot_type == "freetext":
            annot = page.add_freetext_annot(rect, content,
                                             fontsize=op.get("font_size", 12))
        else:
            annot = page.add_text_annot(fitz.Point(rect.x0, rect.y0), content)

        if content and annot_type != "freetext":
            annot.set_info(content=content)
        annot.update()

        return {"success": True, "annot_type": annot_type}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _op_delete_annotation(doc, page, op):
    """删除注释。"""
    index = op.get("annot_index", 0)
    annots = list(page.annots()) if page.annots() else []
    if index >= len(annots):
        return {"success": False, "error": f"Annotation index {index} out of range ({len(annots)})"}

    page.delete_annot(annots[index])
    return {"success": True}


def handler(params):
    """执行 IR 级精准修改操作。"""
    import fitz

    input_path = params["input"]
    output_path = params["output"]
    operations = params["operations"]

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    if not operations:
        raise ValueError("operations 列表不能为空")

    doc = fitz.open(input_path)
    total_pages = len(doc)
    results = []

    op_handlers = {
        "replace_text": _op_replace_text,
        "replace_image": _op_replace_image,
        "add_annotation": _op_add_annotation,
        "delete_annotation": _op_delete_annotation,
    }

    for op in operations:
        op_type = op.get("type", "")
        page_num = op.get("page", 0)

        if page_num < 0 or page_num >= total_pages:
            results.append({"type": op_type, "page": page_num,
                            "success": False, "error": f"Page {page_num} out of range"})
            continue

        page = doc[page_num]
        handler_fn = op_handlers.get(op_type)

        if handler_fn:
            result = handler_fn(doc, page, op)
            result["type"] = op_type
            result["page"] = page_num
        else:
            result = {"type": op_type, "page": page_num,
                      "success": False, "error": f"Unknown operation: {op_type}"}

        results.append(result)

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    success_count = sum(1 for r in results if r.get("success"))

    return {
        "success": True,
        "output": output_path,
        "total_operations": len(results),
        "success_count": success_count,
        "fail_count": len(results) - success_count,
        "results": results,
        "file_size": os.path.getsize(output_path),
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
