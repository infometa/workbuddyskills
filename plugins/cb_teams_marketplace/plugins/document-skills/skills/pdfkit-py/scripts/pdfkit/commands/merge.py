#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并多个 PDF 文档。"""

import os

COMMAND = "merge"
DESCRIPTION = "合并多个 PDF 文件为一个"
CATEGORY = "organize"

PARAMS = [
    {"name": "inputs", "type": "json", "required": True,
     "help": "JSON array of input PDF paths"},
    {"name": "output", "type": "str",  "required": True, "help": "Output PDF path"},
]


def handler(params):
    import fitz

    input_paths = params["inputs"]
    output_path = params["output"]

    if not input_paths or not isinstance(input_paths, list):
        raise ValueError("inputs 必须是 PDF 路径数组")

    for p in input_paths:
        if not os.path.exists(p):
            raise FileNotFoundError(f"文件不存在: {p}")

    merged = fitz.open()
    source_info = []

    for p in input_paths:
        doc = fitz.open(p)
        page_count = len(doc)
        merged.insert_pdf(doc)
        source_info.append({
            "path": p,
            "page_count": page_count,
        })
        doc.close()

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    merged.save(output_path, garbage=4, deflate=True)
    total_pages = len(merged)
    merged.close()

    return {
        "success": True,
        "output": output_path,
        "files_merged": len(input_paths),
        "total_pages": total_pages,
        "file_size": os.path.getsize(output_path),
        "sources": source_info,
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
