#!/usr/bin/env python3
"""一键生成项目日报（跨平台入口，替代旧的 Windows 专用 生成日报.bat）。

不指定日期时自动使用昨天的日期；其余参数原样透传给 generate_report.py。

用法:
    python3 run.py                            # 用昨天的日期
    python3 run.py 2026-05-19                  # 指定日期
    python3 run.py --project-name "示例项目"   # 透传 generate_report.py 的参数
"""

import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def main() -> int:
    args = sys.argv[1:]
    # 没有位置日期参数时，补上昨天的日期
    if not any(DATE_RE.match(a) for a in args):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        args = [yesterday, *args]
        print(f"未指定日期，使用昨天：{yesterday}")
    cmd = [sys.executable, str(SCRIPT_DIR / "generate_report.py"), *args]
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
