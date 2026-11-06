#!/usr/bin/env python3
"""毫秒时间戳转可读时间：python transform.py 1791452769307 [1791452769308 ...] [格式]

注意：
- 固定使用 GMT+8（北京时间），不使用本机时区
- 如果输入不是数字，原样返回（不报错）
- 如果是数字，尝试转换为毫秒时间戳，失败则原样返回
"""
import sys
from datetime import datetime, timezone, timedelta

GMT8 = timezone(timedelta(hours=8))

def convert(v, fmt):
    try:
        return datetime.fromtimestamp(int(v) / 1000, tz=GMT8).strftime(fmt)
    except (ValueError, TypeError, OSError):
        return v

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit('Usage: python transform.py <timestamp>... ["%Y-%m-%d %H:%M:%S"]')
    fmt = args[-1] if args[-1].startswith('%') else "%Y-%m-%d %H:%M:%S"
    values = args[:-1] if args[-1].startswith('%') else args
    print('\n'.join(convert(v, fmt) for v in values))
