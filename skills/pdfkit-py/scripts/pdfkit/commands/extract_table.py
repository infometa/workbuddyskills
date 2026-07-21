#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 表格提取脚本。
支持 camelot（有文字层）和 tabula（备选）两种引擎。
"""

COMMAND = "extract_table"
DESCRIPTION = "从 PDF 中提取结构化表格，支持 camelot/tabula/pymupdf 引擎"
CATEGORY = "read"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "PDF 文件路径"},
    {"name": "pages", "type": "json", "required": False, "help": "页码列表（从 0 开始），默认全部"},
    {"name": "format", "type": "str", "required": False, "default": "json", "choices": ["csv", "json", "markdown"], "help": "输出格式"},
    {"name": "output", "type": "str", "required": False, "default": "", "help": "输出文件路径（可选）"},
    {"name": "method", "type": "str", "required": False, "default": "auto", "choices": ["auto", "lattice", "stream"], "help": "提取方法"},
]


def handler(params):
    """从 PDF 中提取结构化表格。

    Args:
        params: {
            "input": PDF 路径,
            "pages": 页码列表（可选，默认全部）,
            "format": 输出格式（csv/json/markdown，默认 json）,
            "output": 输出文件路径（可选）,
            "method": 提取方法（auto/lattice/stream，默认 auto）
        }
    """
    input_path = params["input"]
    pages = params.get("pages", None)
    output_format = params.get("format", "json")
    output_path = params.get("output", "")
    method = params.get("method", "auto")

    # 构建页码字符串
    if pages:
        page_str = ",".join(str(p + 1) for p in pages)  # camelot 使用 1-based
    else:
        page_str = "all"

    tables_data = []
    engine_used = "none"

    # 尝试 camelot
    try:
        import camelot

        flavor = "lattice" if method == "lattice" else "stream" if method == "stream" else "lattice"
        tables = camelot.read_pdf(input_path, pages=page_str, flavor=flavor)

        if len(tables) == 0 and method == "auto":
            # lattice 失败，尝试 stream
            tables = camelot.read_pdf(input_path, pages=page_str, flavor="stream")

        for i, table in enumerate(tables):
            table_info = {
                "index": i,
                "page": table.page,
                "rows": table.shape[0],
                "cols": table.shape[1],
                "accuracy": round(table.accuracy, 2) if hasattr(table, 'accuracy') else None,
            }

            # camelot 返回的 df 列名为整数索引，不代表任何含义
            # 直接原样输出 PDF 中的所有行，不自行推断或添加表头
            df = table.df

            if output_format == "json":
                table_info["data"] = df.values.tolist()
            elif output_format == "csv":
                # header=False：不输出整数列名行，保持 PDF 原始内容
                table_info["csv"] = df.to_csv(index=False, header=False)
            elif output_format == "markdown":
                table_info["markdown"] = table.df.to_markdown(index=False)

            tables_data.append(table_info)

        engine_used = "camelot"

    except ImportError:
        # camelot 不可用，尝试 tabula
        try:
            import tabula

            # header=None：不把第一行当表头，直接原样读取所有行
            dfs = tabula.read_pdf(input_path, pages=page_str if page_str != "all" else "all",
                                  multiple_tables=True, header=None)

            for i, df in enumerate(dfs):
                table_info = {
                    "index": i,
                    "rows": len(df),
                    "cols": len(df.columns),
                }

                if output_format == "json":
                    table_info["data"] = df.values.tolist()
                elif output_format == "csv":
                    # header=False：不输出整数列名行，保持 PDF 原始内容
                    table_info["csv"] = df.to_csv(index=False, header=False)
                elif output_format == "markdown":
                    table_info["markdown"] = df.to_markdown(index=False)

                tables_data.append(table_info)

            engine_used = "tabula"

        except ImportError:
            # 两个引擎都不可用，使用 PyMuPDF 基础提取
            import fitz
            import contextlib
            import io as _io
            doc = fitz.open(input_path)
            target_pages = pages if pages else range(len(doc))

            for page_num in target_pages:
                page = doc[page_num]
                # 使用 PyMuPDF 的表格检测（v1.23+）
                try:
                    # 抑制 PyMuPDF 的提示信息输出
                    with contextlib.redirect_stdout(_io.StringIO()):
                        tabs = page.find_tables()
                    for i, tab in enumerate(tabs):
                        table_info = {
                            "index": len(tables_data),
                            "page": page_num,
                            "rows": tab.row_count,
                            "cols": tab.col_count,
                        }
                        extracted = tab.extract()
                        if output_format == "json":
                            # 直接原样输出所有行，不推断表头
                            table_info["data"] = extracted
                        elif output_format == "csv":
                            import csv
                            import io
                            output = io.StringIO()
                            writer = csv.writer(output)
                            writer.writerows(extracted)
                            table_info["csv"] = output.getvalue()
                        elif output_format == "markdown":
                            # 直接将所有行作为数据行输出，不添加表头分隔符
                            if extracted:
                                md = ""
                                for row in extracted:
                                    md += "| " + " | ".join(str(c) for c in row) + " |\n"
                                table_info["markdown"] = md

                        tables_data.append(table_info)
                except AttributeError:
                    pass  # PyMuPDF 版本不支持 find_tables

            doc.close()
            engine_used = "pymupdf"

    # 保存到文件
    if output_path and tables_data:
        if output_format == "csv":
            # 直接写入标准 CSV 内容，多张表格之间用空行和注释分隔
            # newline='' 避免 Windows 上 csv 写入产生多余的 \r
            # utf-8-sig 写入 BOM 头，Excel 可正确识别 UTF-8 编码，避免中文乱码
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                for i, table_info in enumerate(tables_data):
                    if len(tables_data) > 1:
                        f.write(f"# Table {i + 1}\n")
                    f.write(table_info.get("csv", ""))
                    if i < len(tables_data) - 1:
                        f.write("\n")
        else:
            import json as json_mod
            with open(output_path, 'w', encoding='utf-8') as f:
                json_mod.dump(tables_data, f, ensure_ascii=False, indent=2)

    return {
        "tables_count": len(tables_data),
        "tables": tables_data,
        "engine": engine_used,
        "output": output_path if output_path else None
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, PARAMS, DESCRIPTION)
