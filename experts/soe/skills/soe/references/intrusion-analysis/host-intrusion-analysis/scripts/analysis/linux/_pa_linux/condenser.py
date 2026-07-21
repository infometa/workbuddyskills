"""章节精简框架。

提供通用的子章节提取和精简逻辑，供主编排器和各 handler 使用。

handler 返回值协议：
  - handler(sub_lines) -> list[str]：正常输出精简后的行
  - handler(sub_lines) -> None：跳过此子章节（不输出标题和内容）
"""

import os
import sys

from _common.models import SectionIndex

_DEBUG = os.environ.get("PREANALYZE_DEBUG") == "1"


def get_sub_lines(
    lines: list[str], sections: list[SectionIndex], sub_name: str
) -> list[str]:
    """获取指定子章节的原始文本行。"""
    for sec in sections:
        for sub in sec.subsections:
            if sub["name"] == sub_name:
                start = sub["start_line"]  # 1-based
                end = sub["end_line"]  # 1-based
                return lines[start:end]
    return []


def condense_section(
    lines: list[str],
    sections: list[SectionIndex],
    section_name: str,
    sub_handlers: dict | None = None,
) -> list[str]:
    """精简一个 SECTION 的文本输出。

    sub_handlers: {sub_name: handler_func} 自定义处理器。
    handler_func(sub_lines) -> list[str] | None
      - 返回 list[str]：精简后的行
      - 返回 None：跳过此子章节（不输出 ### 标题和内容）
    未指定处理器的 SUB 默认截断到 MAX_SUB_LINES 行。
    """
    # 无专用 handler 的子章节默认截断行数。
    # 从 30 降至 12 以控制预分析总输出量（v1.5.0）。
    # 大多数关键子章节已配有专用 handler，此值仅影响少量边缘子章节。
    MAX_SUB_LINES = 12
    result = []

    for sec in sections:
        if sec.name != section_name:
            continue

        for sub in sec.subsections:
            sub_name = sub["name"]
            start = sub["start_line"]  # 1-based
            end = sub["end_line"]  # 1-based
            sub_lines = lines[start:end]

            # 去掉尾部空行
            while sub_lines and sub_lines[-1].strip() == "":
                sub_lines.pop()

            # 空 sub_lines（子章节无数据）→ 跳过
            if not sub_lines or not any(l.strip() for l in sub_lines):
                if _DEBUG:
                    print(
                        f"[DEBUG] Skipped sub: {sub_name} (empty sub_lines)",
                        file=sys.stderr,
                    )
                continue

            # 先调 handler，后决定是否输出标题
            if sub_handlers and sub_name in sub_handlers:
                handled = sub_handlers[sub_name](sub_lines)
                if handled is None:
                    if _DEBUG:
                        print(
                            f"[DEBUG] Skipped sub: {sub_name} (handler returned None)",
                            file=sys.stderr,
                        )
                    continue
                result.append(f"### {sub_name}")
                result.extend(handled)
            elif len(sub_lines) > MAX_SUB_LINES:
                result.append(f"### {sub_name}")
                result.extend(sub_lines[:MAX_SUB_LINES])
                result.append(f"... (截断，共 {len(sub_lines)} 行)")
            else:
                result.append(f"### {sub_name}")
                result.extend(sub_lines)
            result.append("")

    return result
