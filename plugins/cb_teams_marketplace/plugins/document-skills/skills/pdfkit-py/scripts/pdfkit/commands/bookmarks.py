#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 书签/目录编辑脚本。

支持读取、添加、修改和删除 PDF 书签（大纲/目录）。

依赖：PyMuPDF (fitz)
"""

import os

COMMAND = "bookmarks"
DESCRIPTION = "读取、添加、修改和删除 PDF 书签（大纲/目录）。"
CATEGORY = "organize"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "输入 PDF 路径"},
    {"name": "action", "type": "str", "required": False, "default": "get", "choices": ["get", "set"], "help": "操作类型：get 读取，set 设置"},
    {"name": "output", "type": "str", "required": False, "help": "输出 PDF 路径（action=set 时必填）"},
    {"name": "bookmarks", "type": "json", "required": False, "help": "书签列表 [{\"level\": 1, \"title\": \"...\", \"page\": 0}, ...]"},
    {"name": "mode", "type": "str", "required": False, "default": "replace", "choices": ["replace", "append"], "help": "设置模式：replace 替换全部，append 追加"},
]


def get_bookmarks(input_path):
    """读取 PDF 书签/目录。"""
    import fitz  # PyMuPDF

    doc = fitz.open(input_path)
    toc = doc.get_toc(simple=False)
    doc.close()

    bookmarks = []
    for item in toc:
        level, title, page = item[0], item[1], item[2]
        bookmarks.append({
            "level": level,
            "title": title,
            "page": page - 1  # 转为 0-based
        })

    return bookmarks


def set_bookmarks(input_path, output_path, bookmarks, mode="replace"):
    """设置 PDF 书签/目录。

    Args:
        input_path: 输入 PDF 路径
        output_path: 输出 PDF 路径
        bookmarks: 书签列表，每项包含 level, title, page
        mode: "replace"(替换全部), "append"(追加)
    """
    import fitz  # PyMuPDF

    doc = fitz.open(input_path)

    if mode == "append":
        # 追加模式：获取现有书签
        existing_toc = doc.get_toc()
    else:
        existing_toc = []

    # 构建 TOC 列表
    new_toc = list(existing_toc)
    for bm in bookmarks:
        level = bm.get("level", 1)
        title = bm.get("title", "")
        page = bm.get("page", 0) + 1  # 转为 1-based
        if title:
            new_toc.append([level, title, page])

    # 设置书签
    doc.set_toc(new_toc)
    doc.save(output_path)
    file_size = os.path.getsize(output_path)
    doc.close()

    return {
        "success": True,
        "bookmarks_count": len(new_toc),
        "mode": mode,
        "output": output_path,
        "file_size": file_size
    }


def handler(params):
    """处理 PDF 书签操作请求。"""
    action = params.get("action", "get")
    input_path = params.get("input", "")

    if not input_path:
        raise ValueError("'input' 参数必填")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    if action == "get":
        bookmarks = get_bookmarks(input_path)
        return {
            "success": True,
            "bookmarks_count": len(bookmarks),
            "bookmarks": bookmarks
        }

    elif action == "set":
        output_path = params.get("output", "")
        bookmarks = params.get("bookmarks", [])
        mode = params.get("mode", "replace")

        if not output_path:
            raise ValueError("'output' 参数必填")

        return set_bookmarks(input_path, output_path, bookmarks, mode)

    else:
        raise ValueError(f"未知操作: {action}，支持 get/set")


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
