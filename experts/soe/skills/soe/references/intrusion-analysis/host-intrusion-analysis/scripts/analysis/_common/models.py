"""预分析工具数据模型（平台无关）。"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SectionIndex:
    """章节索引条目"""

    name: str
    section_type: str  # SECTION | META | REPORT_BEGIN | REPORT_END
    start_line: int  # 1-based
    end_line: int  # 1-based, inclusive
    description: str = ""
    subsections: list = field(default_factory=list)
    record_count: Optional[int] = None
