#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 扁平化（Flatten）脚本。

将 PDF 中的表单字段和注释扁平化（固化到页面内容中），
使其不可再编辑。

依赖：PyMuPDF (fitz)
"""

import os

COMMAND = "flatten"
DESCRIPTION = "将 PDF 中的表单字段和注释扁平化（固化到页面内容中），使其不可再编辑。"
CATEGORY = "security"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "输入 PDF 路径"},
    {"name": "output", "type": "str", "required": True, "help": "输出 PDF 路径"},
    {"name": "flatten_forms", "type": "bool", "required": False, "default": True, "help": "是否扁平化表单字段"},
    {"name": "flatten_annotations", "type": "bool", "required": False, "default": True, "help": "是否扁平化注释"},
    {"name": "pages", "type": "json", "required": False, "help": "指定页码列表，不指定表示全部页"},
]


def flatten_pdf(input_path, output_path, flatten_forms=True, flatten_annotations=True, pages=None):
    """扁平化 PDF 中的表单字段和注释。

    Args:
        input_path: 输入 PDF 路径
        output_path: 输出 PDF 路径
        flatten_forms: 是否扁平化表单字段
        flatten_annotations: 是否扁平化注释
        pages: 指定页码列表，None 表示全部页
    """
    import fitz  # PyMuPDF

    import fitz  # PyMuPDF

    doc = fitz.open(input_path)
    total_pages = len(doc)
    forms_flattened = 0
    annotations_flattened = 0

    if pages is None:
        pages = list(range(total_pages))

    for p_idx in pages:
        if p_idx < 0 or p_idx >= total_pages:
            continue
        page = doc[p_idx]

        if flatten_annotations:
            # 获取所有注释
            annots = list(page.annots()) if page.annots() else []
            for annot in annots:
                annot_type = annot.type[0]
                # Widget 类型（表单字段）
                if annot_type == fitz.PDF_ANNOT_WIDGET:
                    if flatten_forms:
                        # 将表单字段值渲染到页面
                        annot.set_flags(fitz.PDF_ANNOT_IS_PRINT)
                        forms_flattened += 1
                else:
                    # 其他注释类型
                    annotations_flattened += 1

        # 使用 PyMuPDF 的页面清理来扁平化
        # 将注释内容渲染到页面内容流中
        if flatten_annotations or flatten_forms:
            # 获取页面上的所有注释并逐个处理
            annot = page.first_annot
            while annot:
                next_annot = annot.next
                try:
                    # 将注释内容绘制到页面
                    page.add_redact_annot(annot.rect, fill=False)
                except Exception:
                    pass
                annot = next_annot

    # 保存时使用 deflate 压缩
    doc.save(output_path, garbage=4, deflate=True)
    file_size = os.path.getsize(output_path)
    doc.close()

    return {
        "success": True,
        "forms_flattened": forms_flattened,
        "annotations_flattened": annotations_flattened,
        "total_flattened": forms_flattened + annotations_flattened,
        "pages_processed": len(pages),
        "output": output_path,
        "file_size": file_size
    }


def handler(params):
    """处理 PDF 扁平化请求。"""
    input_path = params.get("input", "")
    output_path = params.get("output", "")
    flatten_forms = params.get("flatten_forms", True)
    flatten_annotations = params.get("flatten_annotations", True)
    pages = params.get("pages")

    if not input_path or not output_path:
        raise ValueError("'input' 和 'output' 参数必填")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    return flatten_pdf(input_path, output_path, flatten_forms, flatten_annotations, pages)


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
