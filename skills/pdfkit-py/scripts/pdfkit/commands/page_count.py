#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取 PDF 页数。"""

import os

COMMAND = "page_count"
DESCRIPTION = "获取 PDF 文档的页数"
CATEGORY = "read"

PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "Input PDF path"},
]


def handler(params):
    import fitz

    input_path = params["input"]
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    doc = fitz.open(input_path)
    count = len(doc)
    metadata = dict(doc.metadata) if doc.metadata else {}
    doc.close()

    return {
        "page_count": count,
        "file": os.path.basename(input_path),
        "file_size": os.path.getsize(input_path),
        "metadata": metadata,
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
