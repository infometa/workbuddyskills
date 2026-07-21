#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF IR 结构差异对比。

对比两个 PDF 文档（或两个 IR JSON）的结构差异，
输出页面级和块级的变更摘要。
"""

import json
import os

COMMAND = "ir_diff"
DESCRIPTION = "Compare structure differences between two PDFs or IR files"
CATEGORY = "ir"

PARAMS = [
    {"name": "left",  "type": "str", "required": True, "help": "Left PDF/IR path (base)"},
    {"name": "right", "type": "str", "required": True, "help": "Right PDF/IR path (changed)"},
    {"name": "output", "type": "str", "required": False, "help": "Output diff JSON path (optional, prints to stdout if omitted)"},
    {"name": "text_only", "type": "bool", "required": False, "default": False, "help": "Only compare text content"},
]


def _extract_page_texts(path):
    """从 PDF 或 IR JSON 提取每页文本。"""
    if path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            ir = json.load(f)
        pages = {}
        for page in ir.get("pages", []):
            idx = page.get("index", 0)
            texts = []
            for block in page.get("blocks", []):
                if block.get("type") == "text":
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            texts.append(span.get("text", ""))
            pages[idx] = " ".join(texts)
        return pages, ir.get("metadata", {}).get("page_count", len(pages))
    else:
        import fitz
        doc = fitz.open(path)
        pages = {}
        for i in range(len(doc)):
            pages[i] = doc[i].get_text("text")
        count = len(doc)
        doc.close()
        return pages, count


def _extract_page_images(path):
    """从 PDF 提取每页图片数量。"""
    if path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            ir = json.load(f)
        return {p.get("index", i): len(p.get("images", []))
                for i, p in enumerate(ir.get("pages", []))}
    else:
        import fitz
        doc = fitz.open(path)
        result = {i: len(doc[i].get_images()) for i in range(len(doc))}
        doc.close()
        return result


def handler(params):
    """对比两个 PDF/IR 的结构差异。"""
    left_path = params["left"]
    right_path = params["right"]
    output_path = params.get("output")
    text_only = params.get("text_only", False)

    for p in [left_path, right_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"文件不存在: {p}")

    left_texts, left_count = _extract_page_texts(left_path)
    right_texts, right_count = _extract_page_texts(right_path)

    diff = {
        "left": os.path.basename(left_path),
        "right": os.path.basename(right_path),
        "page_count_diff": right_count - left_count,
        "left_pages": left_count,
        "right_pages": right_count,
        "page_diffs": [],
        "summary": {
            "added_pages": 0,
            "removed_pages": 0,
            "modified_pages": 0,
            "unchanged_pages": 0,
        },
    }

    all_pages = sorted(set(list(left_texts.keys()) + list(right_texts.keys())))

    for i in all_pages:
        l_text = left_texts.get(i)
        r_text = right_texts.get(i)

        if l_text is None and r_text is not None:
            diff["page_diffs"].append({
                "page": i, "status": "added",
                "right_chars": len(r_text),
            })
            diff["summary"]["added_pages"] += 1

        elif l_text is not None and r_text is None:
            diff["page_diffs"].append({
                "page": i, "status": "removed",
                "left_chars": len(l_text),
            })
            diff["summary"]["removed_pages"] += 1

        elif l_text != r_text:
            page_diff = {
                "page": i, "status": "modified",
                "left_chars": len(l_text),
                "right_chars": len(r_text),
                "char_diff": len(r_text) - len(l_text),
            }

            # 简单行级 diff
            l_lines = l_text.splitlines()
            r_lines = r_text.splitlines()
            added_lines = []
            removed_lines = []
            l_set = set(l_lines)
            r_set = set(r_lines)
            for line in r_lines:
                if line not in l_set and line.strip():
                    added_lines.append(line[:100])
            for line in l_lines:
                if line not in r_set and line.strip():
                    removed_lines.append(line[:100])

            page_diff["added_lines"] = added_lines[:10]
            page_diff["removed_lines"] = removed_lines[:10]
            page_diff["added_line_count"] = len(added_lines)
            page_diff["removed_line_count"] = len(removed_lines)

            diff["page_diffs"].append(page_diff)
            diff["summary"]["modified_pages"] += 1
        else:
            diff["summary"]["unchanged_pages"] += 1

    # 图片差异
    if not text_only:
        left_imgs = _extract_page_images(left_path)
        right_imgs = _extract_page_images(right_path)
        img_diffs = []
        for i in all_pages:
            l_count = left_imgs.get(i, 0)
            r_count = right_imgs.get(i, 0)
            if l_count != r_count:
                img_diffs.append({
                    "page": i,
                    "left_images": l_count,
                    "right_images": r_count,
                })
        if img_diffs:
            diff["image_diffs"] = img_diffs

    # 输出
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(diff, f, ensure_ascii=False, indent=2)
        diff["output"] = output_path

    return diff


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
