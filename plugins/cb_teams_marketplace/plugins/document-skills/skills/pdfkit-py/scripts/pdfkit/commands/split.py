#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拆分 PDF 文档。"""

import os

COMMAND = "split"
DESCRIPTION = "拆分 PDF 为多个文件（按页或按范围）"
CATEGORY = "organize"

PARAMS = [
    {"name": "input",  "type": "str",  "required": True,  "help": "Input PDF path"},
    {"name": "output_dir", "type": "str", "required": True, "help": "Output directory"},
    {"name": "ranges", "type": "json", "required": False,
     "help": 'Page ranges as JSON array, e.g. [[0,2],[3,5]] or "each" for one file per page'},
    {"name": "mode",   "type": "str",  "required": False, "default": "each",
     "choices": ["each", "ranges"], "help": "Split mode: each page or by ranges"},
]


def handler(params):
    import fitz

    input_path = params["input"]
    output_dir = params["output_dir"]
    mode = params.get("mode", "each")
    ranges = params.get("ranges")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(input_path)
    total_pages = len(doc)
    basename = os.path.splitext(os.path.basename(input_path))[0]

    outputs = []

    if mode == "ranges" and ranges:
        # 按指定范围拆分
        for idx, r in enumerate(ranges):
            if isinstance(r, (list, tuple)) and len(r) == 2:
                start, end = int(r[0]), int(r[1])
            elif isinstance(r, int):
                start, end = r, r
            else:
                continue

            start = max(0, start)
            end = min(total_pages - 1, end)

            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start, to_page=end)

            filename = f"{basename}_pages_{start}-{end}.pdf"
            filepath = os.path.join(output_dir, filename)
            new_doc.save(filepath)
            new_doc.close()

            outputs.append({
                "path": filepath,
                "pages": list(range(start, end + 1)),
                "page_count": end - start + 1,
                "file_size": os.path.getsize(filepath),
            })
    else:
        # 每页一个文件
        for i in range(total_pages):
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=i)

            filename = f"{basename}_page_{i}.pdf"
            filepath = os.path.join(output_dir, filename)
            new_doc.save(filepath)
            new_doc.close()

            outputs.append({
                "path": filepath,
                "pages": [i],
                "page_count": 1,
                "file_size": os.path.getsize(filepath),
            })

    doc.close()

    return {
        "success": True,
        "files_created": len(outputs),
        "total_source_pages": total_pages,
        "output_dir": output_dir,
        "files": outputs,
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
