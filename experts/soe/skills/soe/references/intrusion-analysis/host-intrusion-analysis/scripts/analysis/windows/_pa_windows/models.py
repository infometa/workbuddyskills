"""预分析工具数据模型（兼容重导出）。

实际定义在 _common.models 中。此文件保持向后兼容，
使 _pa_windows 包内的 `from .models import SectionIndex` 继续工作。
"""

from _common.models import SectionIndex  # noqa: F401

__all__ = ["SectionIndex"]
