#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 排版引擎 — 处理文本回写时的位置计算。
解决翻译后文本回写和格式转换中的排版问题。
"""

import os
import sys

COMMAND = "layout_engine"
DESCRIPTION = "PDF 排版引擎，处理文本回写时的位置计算（reflow / batch_reflow）。"
CATEGORY = "meta"
PARAMS = [
    {"name": "action", "type": "str", "required": False, "default": "reflow", "choices": ["reflow", "batch_reflow"], "help": "操作类型"},
    {"name": "block", "type": "json", "required": False, "help": "单个布局块（reflow 时使用）"},
    {"name": "blocks", "type": "json", "required": False, "help": "布局块列表（batch_reflow 时使用）"},
    {"name": "text", "type": "str", "required": False, "help": "新文本（reflow 时使用）"},
    {"name": "texts", "type": "json", "required": False, "help": "新文本列表（batch_reflow 时使用）"},
    {"name": "constraints", "type": "json", "required": False, "help": "排版约束 {min_font_size, line_spacing, overflow_mode}"},
    {"name": "font_path", "type": "str", "required": False, "help": "字体文件路径"},
]


class LayoutEngine:
    """PDF 排版引擎 — 处理文本回写时的位置计算"""

    def __init__(self, font_path=None):
        """初始化排版引擎。

        Args:
            font_path: 字体文件路径（用于精确计算文本宽度）
        """
        self.font_path = font_path
        self._font_cache = {}

    def reflow_text(self, block, new_text, constraints=None):
        """重新排版文本块。

        Args:
            block: 原始布局块，包含 bbox、font_size、font_name
            new_text: 新文本内容
            constraints: 排版约束 {min_font_size, line_spacing, overflow_mode}

        Returns:
            排版结果 {lines, font_size, total_height, overflow, bbox}
        """
        if constraints is None:
            constraints = {}

        bbox = block.get("bbox", [0, 0, 100, 100])
        max_width = bbox[2] - bbox[0]
        max_height = bbox[3] - bbox[1]
        font_size = block.get("font_size", 12)
        min_font_size = constraints.get("min_font_size", 6)
        line_spacing = constraints.get("line_spacing", 1.2)

        # 1. 尝试原字号排版
        lines = self._wrap_text(new_text, font_size, max_width)
        total_height = len(lines) * font_size * line_spacing

        # 2. 如果超出高度，逐步缩小字号
        while total_height > max_height and font_size > min_font_size:
            font_size -= 0.5
            lines = self._wrap_text(new_text, font_size, max_width)
            total_height = len(lines) * font_size * line_spacing

        # 3. 判断是否溢出
        overflow = total_height > max_height
        overflow_mode = constraints.get("overflow_mode", "truncate")

        if overflow:
            if overflow_mode == "truncate":
                # 截断到可显示的行数
                max_lines = max(1, int(max_height / (font_size * line_spacing)))
                lines = lines[:max_lines]
                if len(lines) > 0:
                    lines[-1] = lines[-1].rstrip() + "..."
                total_height = len(lines) * font_size * line_spacing
            elif overflow_mode == "expand":
                # 扩展块高度（不截断）
                pass

        return {
            "lines": lines,
            "font_size": round(font_size, 1),
            "total_height": round(total_height, 1),
            "overflow": overflow,
            "line_count": len(lines),
            "bbox": [
                bbox[0],
                bbox[1],
                bbox[2],
                bbox[1] + total_height if overflow_mode == "expand" else bbox[3],
            ],
        }

    def _wrap_text(self, text, font_size, max_width):
        """文本自动换行。

        支持中文字符级换行和英文单词级换行。

        Args:
            text: 文本内容
            font_size: 字号
            max_width: 最大宽度（PDF 点）

        Returns:
            换行后的文本行列表
        """
        if not text:
            return [""]

        # 估算字符宽度（PDF 点）
        # 中文字符约等于 font_size，英文字符约等于 font_size * 0.5
        lines = []
        paragraphs = text.split("\n")

        for para in paragraphs:
            if not para.strip():
                lines.append("")
                continue

            current_line = ""
            current_width = 0.0

            i = 0
            while i < len(para):
                ch = para[i]
                ch_width = self._char_width(ch, font_size)

                if current_width + ch_width > max_width and current_line:
                    # 英文单词不拆分
                    if ch.isalpha() and current_line and current_line[-1].isalpha():
                        # 回退到最近的空格或非字母字符
                        break_pos = len(current_line) - 1
                        while break_pos > 0 and current_line[break_pos].isalpha():
                            break_pos -= 1
                        if break_pos > 0:
                            lines.append(current_line[:break_pos + 1].rstrip())
                            remaining = current_line[break_pos + 1:]
                            current_line = remaining + ch
                            current_width = sum(
                                self._char_width(c, font_size) for c in current_line
                            )
                            i += 1
                            continue

                    lines.append(current_line)
                    current_line = ch
                    current_width = ch_width
                else:
                    current_line += ch
                    current_width += ch_width
                i += 1

            if current_line:
                lines.append(current_line)

        return lines if lines else [""]

    def _char_width(self, ch, font_size):
        """估算单个字符的宽度（PDF 点）。

        Args:
            ch: 字符
            font_size: 字号

        Returns:
            字符宽度
        """
        code = ord(ch)
        # CJK 统一表意文字范围
        if (0x4E00 <= code <= 0x9FFF or  # CJK 基本
            0x3400 <= code <= 0x4DBF or  # CJK 扩展 A
            0xF900 <= code <= 0xFAFF or  # CJK 兼容
            0x3000 <= code <= 0x303F or  # CJK 标点
            0xFF00 <= code <= 0xFFEF):   # 全角字符
            return font_size * 1.0
        elif ch == ' ':
            return font_size * 0.25
        elif ch in '.,;:!?':
            return font_size * 0.3
        elif ch.isupper():
            return font_size * 0.65
        else:
            return font_size * 0.5

    def compute_text_positions(self, blocks, translations, constraints=None):
        """批量计算翻译后文本的排版位置。

        Args:
            blocks: 原始布局块列表
            translations: 翻译后的文本列表（与 blocks 一一对应）
            constraints: 排版约束

        Returns:
            排版结果列表
        """
        results = []
        for block, new_text in zip(blocks, translations):
            result = self.reflow_text(block, new_text, constraints)
            result["original_text"] = block.get("text", "")
            result["translated_text"] = new_text
            results.append(result)
        return results


def handler(params):
    """排版引擎入口。

    Args:
        params: {
            "action": "reflow" | "batch_reflow",
            "blocks": 布局块列表,
            "texts": 新文本列表（batch_reflow 时使用）,
            "text": 新文本（reflow 时使用）,
            "constraints": 排版约束（可选）,
            "font_path": 字体路径（可选）
        }
    """
    action = params.get("action", "reflow")
    font_path = params.get("font_path")
    constraints = params.get("constraints", {})

    engine = LayoutEngine(font_path=font_path)

    if action == "reflow":
        block = params["block"]
        new_text = params["text"]
        result = engine.reflow_text(block, new_text, constraints)
        return result

    elif action == "batch_reflow":
        blocks = params["blocks"]
        texts = params["texts"]
        results = engine.compute_text_positions(blocks, texts, constraints)
        return {"results": results, "count": len(results)}

    else:
        raise ValueError(f"未知的 action: {action}")


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
