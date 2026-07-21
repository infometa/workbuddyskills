"""Phase 1 & 2: 日志结构解析 + 数据提取 + IP 分类工具函数（兼容重导出）。

实际定义在 _common.parsers 中。此文件保持向后兼容，
使 _pa_windows 包内的 import 继续工作。
"""

from _common.parsers import (  # noqa: F401
    char_display_width,
    parse_table_row_wide,
    string_display_width,
    classify_ip,
    extract_event_data,
    extract_kv_data,
    extract_section_kv_data,
    is_external_ip,
    parse_fixed_width_columns,
    parse_fixed_width_table,
    parse_kv_pairs,
    parse_log_structure,
    parse_subsections,
    parse_table_row,
)

__all__ = [
    "parse_fixed_width_columns",
    "parse_table_row",
    "char_display_width",
    "string_display_width",
    "parse_table_row_wide",
    "parse_fixed_width_table",
    "parse_kv_pairs",
    "parse_log_structure",
    "parse_subsections",
    "extract_event_data",
    "extract_kv_data",
    "extract_section_kv_data",
    "classify_ip",
    "is_external_ip",
]
