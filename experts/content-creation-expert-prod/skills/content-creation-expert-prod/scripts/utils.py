"""
公共工具函数（生产版精简）
"""

import sys


def log_info(msg: str):
    """输出信息日志到 stderr（不污染 stdout JSON 输出）"""
    print(f"[INFO] {msg}", file=sys.stderr)


def log_warn(msg: str):
    """输出警告日志到 stderr"""
    print(f"[WARN] {msg}", file=sys.stderr)


def log_error(msg: str):
    """输出错误日志到 stderr"""
    print(f"[ERROR] {msg}", file=sys.stderr)
