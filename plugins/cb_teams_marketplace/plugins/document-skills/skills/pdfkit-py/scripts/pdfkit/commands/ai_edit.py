#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 辅助 PDF 编辑工具（占位模块）。
通过 AI 模型理解编辑意图，自动选择合适的编辑策略。
"""

import os
import sys

COMMAND = "ai_edit"
DESCRIPTION = "AI 辅助 PDF 编辑工具（占位模块，待实现）。"
CATEGORY = "edit"
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "源 PDF 文件路径"},
    {"name": "output", "type": "str", "required": True, "help": "输出 PDF 文件路径"},
    {"name": "instruction", "type": "str", "required": True, "help": "自然语言编辑指令"},
    {"name": "model", "type": "str", "required": False, "default": "auto", "help": "AI 模型名称"},
    {"name": "dry_run", "type": "bool", "required": False, "default": False, "help": "是否为预览模式"},
]


def handler(params):
    """AI 辅助编辑 PDF（占位实现）。

    Args:
        params: {
            "input": 源 PDF 文件路径,
            "output": 输出 PDF 文件路径,
            "instruction": 自然语言编辑指令,
            "model": AI 模型名称（默认 auto）,
        }
    """
    return {
        "success": False,
        "error": "ai_edit 功能尚未实现，请使用 smart_edit 命令进行 PDF 编辑。",
        "suggestion": "smart_edit",
    }


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
