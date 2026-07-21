"""平台无关的日志结构解析 + 数据提取 + IP 分类工具函数。

从 windows/_pa_windows/parsers.py 提取，供 Windows 和 Linux 预分析器共同复用。
"""

import ipaddress
import re

from .constants import (
    METADATA_IPS,
    RE_EVENTS,
    RE_EVENTS_NO_COUNT,
    RE_KV,
    RE_NO_DATA,
    RE_SECTION,
    RE_SECTION_DESC,
    RE_SUB,
    RE_TABLE_SEP,
    RE_WHOAMI_TABLE_SEP,
)
from .models import SectionIndex


# ---------------------------------------------------------------------------
# Phase 1: Log Structure Parser
# ---------------------------------------------------------------------------


def parse_fixed_width_columns(sep_line: str) -> list[tuple[int, int]]:
    """从表格分隔行解析列边界。

    分隔行格式: "    ---  ---  -------  ------"
    返回每列的 (start, end) 位置列表（基于原始行的字符位置）。

    例如 "    ---  ---" → [(4, 7), (9, 12)]
    """
    columns = []
    i = 0
    sep_char = "-" if "-" in sep_line else "="

    while i < len(sep_line):
        if sep_line[i] == sep_char:
            start = i
            while i < len(sep_line) and sep_line[i] == sep_char:
                i += 1
            columns.append((start, i))
        else:
            i += 1

    return columns


def parse_table_row(line: str, columns: list[tuple[int, int]]) -> list[str]:
    """按列边界切割一行数据，返回每列的值（去首尾空格）。"""
    values = []
    for start, end in columns:
        if start < len(line):
            val = line[start : min(end, len(line))].strip()
        else:
            val = ""
        values.append(val)
    return values


def char_display_width(ch: str) -> int:
    """返回单个字符的终端显示宽度。

    CJK 字符和全角符号占 2 列，其余占 1 列。
    参考 Unicode East Asian Width 属性简化版。
    """
    cp = ord(ch)
    # CJK Radicals Supplement + CJK Unified Ideographs + Extensions
    if 0x2E80 <= cp <= 0x9FFF:
        return 2
    # CJK Compatibility Ideographs
    if 0xF900 <= cp <= 0xFAFF:
        return 2
    # CJK Compatibility Forms
    if 0xFE30 <= cp <= 0xFE4F:
        return 2
    # Halfwidth and Fullwidth Forms (excluding halfwidth portion FF65-FFDC)
    if 0xFF01 <= cp <= 0xFF60:
        return 2
    if 0xFFE0 <= cp <= 0xFFEF:
        return 2
    # CJK Unified Ideographs Extension B+
    if 0x20000 <= cp <= 0x2FA1F:
        return 2
    # Hangul Syllables
    if 0xAC00 <= cp <= 0xD7AF:
        return 2
    return 1


def string_display_width(s: str) -> int:
    """返回字符串的终端显示宽度。"""
    return sum(char_display_width(ch) for ch in s)


def parse_table_row_wide(
    line: str, columns: list[tuple[int, int]]
) -> list[str]:
    """按 **显示宽度** 列边界切割含 CJK 宽字符的行。

    columns 是从 ASCII 分隔行解析的 (start, end) 显示宽度区间。
    对 line 中的每个字符累加显示宽度，按区间提取对应列内容。
    """
    values = []
    for col_start, col_end in columns:
        chars = []
        dw = 0  # 当前显示宽度位置
        for ch in line:
            cw = char_display_width(ch)
            if dw >= col_end:
                break
            if dw >= col_start:
                chars.append(ch)
            elif dw + cw > col_start:
                # 字符跨越列起始位置（宽字符部分落入区间）
                chars.append(ch)
            dw += cw
        values.append("".join(chars).strip())
    return values


def parse_fixed_width_table(
    lines: list[str], start_idx: int
) -> tuple[list[dict[str, str]], int]:
    """解析固定列宽表格。

    从 start_idx 开始向下扫描，找到表头行和分隔行，然后解析数据行。
    返回 (记录列表, 结束行索引)。

    表格结构:
      表头行:  #    TimeCreated   EventID   ...
      分隔行:  ---  -----------   -------   ...
      数据行:  1    2026-03-24    4104      ...
    """
    records = []
    idx = start_idx

    # 跳过空行
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1

    if idx >= len(lines):
        return records, idx

    # 检查是否是 (无数据)
    if RE_NO_DATA.match(lines[idx]):
        return records, idx + 1

    # 找表头行（第一个非空行）
    header_line = lines[idx]
    header_idx = idx
    idx += 1

    # 找分隔行
    if idx >= len(lines):
        return records, idx

    sep_line = lines[idx]
    # 验证是否为分隔行
    if not (RE_TABLE_SEP.match(sep_line) or RE_WHOAMI_TABLE_SEP.match(sep_line)):
        # 不是标准表格，回退
        return records, header_idx

    # 解析列边界
    columns = parse_fixed_width_columns(sep_line)
    if not columns:
        return records, header_idx

    # 解析表头
    headers = parse_table_row(header_line, columns)
    idx += 1  # 跳过分隔行

    # 解析数据行
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        # 遇到空行或新的章节/子章节标记，结束表格
        if stripped == "":
            idx += 1
            break
        if RE_SECTION.match(stripped):
            break
        if RE_SUB.match(stripped):
            break
        if RE_EVENTS.match(stripped):
            break

        # 解析数据行
        values = parse_table_row(line, columns)
        record = {}
        for h, v in zip(headers, values):
            if h:  # 跳过空列名
                record[h] = v
        if any(v for v in record.values()):  # 跳过全空行
            records.append(record)

        idx += 1

    return records, idx


def parse_kv_pairs(
    lines: list[str], start_idx: int, indent_level: int
) -> tuple[dict[str, str], int]:
    """解析键值对区域。

    从 start_idx 开始，解析 "Key: Value" 格式的行，
    直到遇到不同缩进的行或章节标记。
    返回 (键值字典, 结束行索引)。
    """
    kv = {}
    idx = start_idx

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        # 空行跳过
        if stripped == "":
            idx += 1
            continue

        # 遇到章节/子章节标记，结束
        if RE_SECTION.match(stripped):
            break
        if RE_SUB.match(stripped):
            break
        if RE_EVENTS.match(stripped):
            break
        if RE_EVENTS_NO_COUNT.match(stripped):
            break

        m = RE_KV.match(line)
        if m:
            current_indent = len(m.group(1))
            if current_indent >= indent_level:
                key = m.group(2)
                value = m.group(3).strip()
                kv[key] = value
                idx += 1

                # 特殊处理：嵌套子表格（如 Firewall_Profiles: (3 条记录)）
                if "条记录" in value:
                    # 跳过后面的嵌套子表格
                    sub_records, idx = parse_fixed_width_table(lines, idx)
                    kv[key + "_data"] = sub_records
            else:
                break
        else:
            # 不是键值对，可能是列表项或其他格式
            # 检查是否为 [N] 格式的列表
            if re.match(r"^\s+\[\d+\]", line):
                idx += 1
                continue
            # 检查是否为纯文本内容（如管理员列表）
            if len(line) - len(line.lstrip()) >= indent_level:
                idx += 1
                continue
            break

    return kv, idx


def parse_log_structure(lines: list[str]) -> list[SectionIndex]:
    """解析日志的完整章节结构。

    遍历所有行，识别 SECTION/META/REPORT_BEGIN/REPORT_END 分隔线，
    建立层级索引。
    """
    sections: list[SectionIndex] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()
        m = RE_SECTION.match(line)

        if m:
            sec_type = m.group(1)
            sec_name = m.group(2) or sec_type

            # 对于 SECTION 和 REPORT_BEGIN/REPORT_END，它们成对出现
            # 第一行是开始标记，中间是描述行，第三行是重复标记
            start_line = i + 1  # 1-based

            desc = ""
            if sec_type in ("SECTION", "REPORT_BEGIN", "REPORT_END"):
                # 跳过描述行和重复标记行
                if i + 1 < n:
                    desc_line = lines[i + 1].strip()
                    if RE_SECTION_DESC.match(lines[i + 1]) or desc_line:
                        desc = desc_line
                if i + 2 < n and RE_SECTION.match(lines[i + 2].strip()):
                    i = i + 3  # 跳过三行（标记 + 描述 + 重复标记）
                else:
                    i += 1
            else:
                # META 只出现一次
                i += 1

            section = SectionIndex(
                name=sec_name,
                section_type=sec_type,
                start_line=start_line,
                end_line=n,  # 暂时设为文件末尾，后面修正
                description=desc,
            )
            sections.append(section)
        else:
            i += 1

    # 修正每个 section 的 end_line
    for idx in range(len(sections)):
        if idx + 1 < len(sections):
            sections[idx].end_line = sections[idx + 1].start_line - 1
        else:
            sections[idx].end_line = n

    # 为每个 SECTION 解析子章节
    for sec in sections:
        if sec.section_type not in ("SECTION", "META"):
            continue

        sec.subsections = parse_subsections(
            lines, sec.start_line - 1, sec.end_line - 1
        )

    return sections


def parse_subsections(
    lines: list[str], start_idx: int, end_idx: int
) -> list[dict]:
    """解析一个 SECTION 内的子章节（SUB / CATEGORY / EVENTS）。"""
    subsections = []
    i = start_idx

    while i <= end_idx and i < len(lines):
        line = lines[i]

        m_sub = RE_SUB.match(line)
        m_events = RE_EVENTS.match(line)
        m_events_nc = RE_EVENTS_NO_COUNT.match(line) if not m_events else None

        if m_sub:
            sub = {
                "type": m_sub.group(1),
                "name": m_sub.group(2).strip(),
                "start_line": i + 1,  # 1-based
                "end_line": end_idx + 1,  # 暂设末尾
                "record_count": None,
            }
            subsections.append(sub)
            i += 1
        elif m_events:
            sub = {
                "type": "EVENTS",
                "name": m_events.group(1),
                "start_line": i + 1,
                "end_line": end_idx + 1,
                "record_count": int(m_events.group(2)),
            }
            subsections.append(sub)
            i += 1
        elif m_events_nc:
            sub = {
                "type": "EVENTS",
                "name": m_events_nc.group(1),
                "start_line": i + 1,
                "end_line": end_idx + 1,
                "record_count": None,
            }
            subsections.append(sub)
            i += 1
        else:
            i += 1

    # 修正 end_line
    for idx in range(len(subsections)):
        if idx + 1 < len(subsections):
            subsections[idx]["end_line"] = subsections[idx + 1]["start_line"] - 1
        else:
            subsections[idx]["end_line"] = end_idx + 1

    return subsections


# ---------------------------------------------------------------------------
# Phase 2: Data Extraction
# ---------------------------------------------------------------------------


def extract_event_data(
    lines: list[str], sections: list[SectionIndex], event_name: str
) -> list[dict[str, str]]:
    """从解析后的章节结构中提取指定事件/子章节的表格数据。

    同时搜索 EVENTS 和 SUB 类型的子章节。
    """
    for sec in sections:
        for sub in sec.subsections:
            if sub["name"] == event_name:
                start = sub["start_line"]  # 1-based
                records, _ = parse_fixed_width_table(lines, start)
                return records

    # 也检查直接 SECTION 下的表格（如 Processes、Services、Startup、USNLogs）
    for sec in sections:
        if sec.name == event_name and not sec.subsections:
            if sec.section_type == "SECTION":
                start = sec.start_line + 2  # 0-based: 跳过标记区域到空行/表头
            else:
                start = sec.start_line  # META 类型保持原逻辑
            records, _ = parse_fixed_width_table(lines, start)
            return records

    return []


def extract_kv_data(
    lines: list[str], sections: list[SectionIndex], sub_name: str
) -> dict[str, str]:
    """从解析后的章节结构中提取指定子章节的键值对数据。"""
    for sec in sections:
        for sub in sec.subsections:
            if sub["name"] == sub_name and sub["type"] == "SUB":
                start = sub["start_line"]  # 1-based
                kv, _ = parse_kv_pairs(lines, start, indent_level=4)
                return kv
    return {}


def extract_section_kv_data(
    lines: list[str], sections: list[SectionIndex], section_name: str
) -> dict[str, str]:
    """从指定 SECTION（无子章节）中提取键值对数据。"""
    for sec in sections:
        if sec.name == section_name and sec.section_type in ("SECTION", "META"):
            start = sec.start_line  # 1-based
            kv, _ = parse_kv_pairs(lines, start, indent_level=2)
            return kv
    return {}


# ---------------------------------------------------------------------------
# IP Classification
# ---------------------------------------------------------------------------


def classify_ip(ip_str: str) -> str:
    """IP 分类。

    Returns:
        'external' | 'internal' | 'loopback' | 'link_local' |
        'metadata' | 'unspecified' | 'cgn' | 'invalid'
    """
    if not ip_str or ip_str in ("-", "(空)", "::"):
        return "unspecified"

    # 元数据 IP 特殊判断
    if ip_str in METADATA_IPS:
        return "metadata"

    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return "invalid"

    if addr.is_loopback:
        return "loopback"
    if addr.is_link_local:
        return "link_local"
    if addr.is_private:
        return "internal"
    if addr.is_unspecified:
        return "unspecified"

    # 100.64.0.0/10 - Carrier-Grade NAT (RFC 6598)
    if isinstance(addr, ipaddress.IPv4Address):
        if addr in ipaddress.ip_network("100.64.0.0/10"):
            return "cgn"

    return "external"


def is_external_ip(ip_str: str) -> bool:
    """判断是否为外部 IP（排除内部、环回、CGN、元数据等）。"""
    return classify_ip(ip_str) == "external"
