"""平台无关的日志解析常量。

仅包含日志格式解析相关的正则和常量。
平台特定常量（PS 白名单、勒索后缀等）保留在各平台目录下。
"""

import re


# ---------------------------------------------------------------------------
# Log Structure Parsing Constants (平台无关)
# ---------------------------------------------------------------------------

# 章节分隔线正则
RE_SECTION = re.compile(
    r"^={8}\s+(SECTION|META|REPORT_BEGIN|REPORT_END)(?::\s*(\S+))?\s+={8}$"
)
# 子章节分隔线正则
RE_SUB = re.compile(r"^\s+-{8}\s+(SUB|CATEGORY):\s*(.+?)\s+-{8}$")
# 事件分隔线正则（带记录数）
RE_EVENTS = re.compile(
    r"^\s+-{4}\s+EVENTS:\s*(\S+)\s+\((\d+)\s+records?\)\s+-{4}$"
)
# 事件分隔线正则（不带记录数，Linux 采集脚本格式）
RE_EVENTS_NO_COUNT = re.compile(
    r"^\s+-{8}\s+EVENTS:\s*(\S+)\s+-{8}$"
)
# 表格分隔行正则：多个连续 `-` 段（至少 1 个字符）由 2 个空格分隔
RE_TABLE_SEP = re.compile(r"^(\s+)([-]+(?:\s\s[-]+)+)\s*$")
# whoami 表格分隔行（使用 = 字符）
RE_WHOAMI_TABLE_SEP = re.compile(r"^(\s+)(=+(?:\s+=+)+)\s*$")
# 键值对正则
RE_KV = re.compile(r"^(\s+)(\w[\w.]*)\s*:\s*(.*)$")
# (无数据) 标记
RE_NO_DATA = re.compile(r"^\s*\(无数据\)\s*$")
# SECTION 描述行 [N] 描述
RE_SECTION_DESC = re.compile(r"^\s+\[\d+\]\s+.+$")

# ---------------------------------------------------------------------------
# IP Classification Constants (平台无关)
# ---------------------------------------------------------------------------

# 云元数据 IP（各云厂商通用）
METADATA_IPS = {
    "169.254.169.254",  # 云元数据服务
    "169.254.169.250",  # 云元数据服务
}
