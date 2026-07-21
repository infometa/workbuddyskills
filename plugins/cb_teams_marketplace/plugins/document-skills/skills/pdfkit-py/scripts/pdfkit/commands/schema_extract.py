#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schema-based 结构化提取脚本。

根据用户定义的 JSON Schema 从 PDF 中提取结构化数据。
支持提取文本字段、表格、列表等结构化信息。

依赖：PyMuPDF (fitz), pdfplumber (可选)
"""

import json
import sys
import os
import re

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

COMMAND = "schema_extract"
DESCRIPTION = "根据 JSON Schema 从 PDF 中提取结构化数据。"
CATEGORY = "read"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "schema", "type": "json", "required": True, "help": "JSON Schema 定义，描述要提取的字段"},
    {"name": "pages", "type": "json", "required": False, "help": "指定页码列表（从 0 开始），JSON 数组"},
]


def extract_by_schema(input_path, schema, pages=None):
    """根据 JSON Schema 从 PDF 中提取结构化数据。

    Args:
        input_path: PDF 文件路径
        schema: JSON Schema 定义，描述要提取的字段
        pages: 指定页码列表（从 0 开始），None 表示全部页
    """
    doc = fitz.open(input_path)
    total_pages = len(doc)

    if pages is None:
        pages = list(range(total_pages))

    # 提取全文（按页）
    all_text = ""
    page_texts = {}
    for p_idx in pages:
        if p_idx < 0 or p_idx >= total_pages:
            continue
        page = doc[p_idx]
        text = page.get_text("text").strip()
        page_texts[p_idx] = text
        all_text += text + "\n\n"

    # 根据 Schema 提取数据
    result = {}
    properties = schema.get("properties", {})

    for field_name, field_def in properties.items():
        field_type = field_def.get("type", "string")
        description = field_def.get("description", "")
        pattern = field_def.get("pattern", "")
        extract_method = field_def.get("extract_method", "regex")

        if extract_method == "regex" and pattern:
            # 正则表达式提取
            matches = re.findall(pattern, all_text)
            if field_type == "array":
                result[field_name] = matches
            elif matches:
                result[field_name] = matches[0]
            else:
                result[field_name] = None

        elif extract_method == "keyword" or (extract_method == "regex" and not pattern):
            # 关键词定位提取（查找关键词后面的内容）
            # 当没有指定 pattern 时，自动使用 description 或 field_name 作为关键词
            keyword = field_def.get("keyword", description if description else field_name)
            for line in all_text.split("\n"):
                if keyword in line:
                    # 提取关键词后面的内容
                    idx = line.index(keyword) + len(keyword)
                    value = line[idx:].strip().lstrip(":：").strip()
                    if value:
                        result[field_name] = _cast_value(value, field_type)
                        break
            if field_name not in result:
                result[field_name] = None

        elif extract_method == "page_range":
            # 按页码范围提取
            start = field_def.get("page_start", 0)
            end = field_def.get("page_end", total_pages - 1)
            texts = []
            for p_idx in range(start, min(end + 1, total_pages)):
                if p_idx in page_texts:
                    texts.append(page_texts[p_idx])
            result[field_name] = "\n".join(texts) if texts else None

        elif extract_method == "table":
            # 表格提取（简单实现）
            try:
                import pdfplumber
                with pdfplumber.open(input_path) as pdf:
                    tables = []
                    target_pages = field_def.get("pages", pages)
                    for p_idx in target_pages:
                        if p_idx < len(pdf.pages):
                            page_tables = pdf.pages[p_idx].extract_tables()
                            for t in page_tables:
                                if t:
                                    # 第一行作为表头
                                    headers = t[0] if t else []
                                    rows = t[1:] if len(t) > 1 else []
                                    tables.append({
                                        "headers": headers,
                                        "rows": rows,
                                        "page": p_idx
                                    })
                    result[field_name] = tables
            except ImportError:
                result[field_name] = None

        else:
            # 默认：全文搜索
            result[field_name] = None

    doc.close()

    return {
        "success": True,
        "extracted_fields": len([v for v in result.values() if v is not None]),
        "total_fields": len(properties),
        "data": result,
        "metadata": {
            "file": os.path.basename(input_path),
            "total_pages": total_pages,
            "pages_scanned": len(pages)
        }
    }


def _cast_value(value, field_type):
    """将字符串值转换为指定类型。"""
    try:
        if field_type == "integer":
            return int(re.sub(r'[^\d]', '', value))
        elif field_type == "number":
            return float(re.sub(r'[^\d.]', '', value))
        elif field_type == "boolean":
            return value.lower() in ("true", "yes", "是", "1")
        else:
            return value
    except (ValueError, TypeError):
        return value


def handler(params):
    """Schema-based 结构化提取入口。

    Args:
        params: {
            "input": PDF 文件路径,
            "schema": JSON Schema 定义,
            "pages": 指定页码列表（可选）
        }
    """
    if fitz is None:
        raise ImportError("需要安装 PyMuPDF: pip install PyMuPDF")

    input_path = params.get("input", "")
    schema = params.get("schema", {})
    pages = params.get("pages")

    if not input_path:
        raise ValueError("'input' 参数必填")

    if not os.path.exists(input_path):
        raise ValueError(f"文件不存在: {input_path}")

    if not schema or not schema.get("properties"):
        raise ValueError("'schema' 参数必须包含 'properties' 字段")

    return extract_by_schema(input_path, schema, pages)


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
