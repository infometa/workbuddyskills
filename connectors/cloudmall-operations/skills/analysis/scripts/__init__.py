"""
__init__.py — ecommerce-data-analyst scripts 包入口

实际渲染入口：
    python3 scripts/generate_report.py --help

辅助工具：
    GateChecker     — Gate Check 校验

报告通过 generate_report.py 写入指定的本地输出目录；交付实际生成的文件路径。
"""

from .gate_check import GateChecker, GateCheckResult, CheckItem
from .execution_logger import generate_execution_log

__all__ = [
    "GateChecker", "GateCheckResult", "CheckItem",
    "generate_execution_log",
]

__version__ = "3.0.0"
