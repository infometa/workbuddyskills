#!/usr/bin/env python3
"""
入侵检测日志预分析统一入口

AI 分析师调用此入口即可，无需关心日志来自哪个平台。
脚本通过【任务委派机制】自动识别平台并路由到对应的预分析器。

用法:
  python3 scripts/analysis/preanalyze.py <log_file.txt>        # 采集脚本输出（单主机）
  python3 scripts/analysis/preanalyze.py <incident.zip>        # 多主机 ZIP 包
  python3 scripts/analysis/preanalyze.py </path/to/var/log/>   # 原始 var/log 目录

输出: 预分析结果 → stdout（Markdown）

任务委派流程:
  ┌──────────────┐     can_handle?     ┌─────────────────────────────────────┐
  │  输入路径     │ ──── Yes ──────────▶│  Linux-Zip（多主机 ZIP 包）         │
  │  incident.zip │                     │  解压 → 逐主机 → 联合预分析         │
  └──────┬───────┘                     └─────────────────────────────────────┘
         │ No
         ▼
  ┌──────────────┐     can_handle?     ┌─────────────────────────────────────┐
  │  继续检测     │ ──── Yes ──────────▶│  Linux-LogFolder（原始 var/log/）   │
  │  /var/log/    │                     │  syslog 合成 → LinuxPreAnalyzer     │
  └──────┬───────┘                     └─────────────────────────────────────┘
         │ No
         ▼
  ┌──────────────┐     can_handle?     ┌─────────────────────────────────────┐
  │  继续检测     │ ──── Yes ──────────▶│  Windows 预分析器                   │
  │  log_xxx.txt  │                     │  (6 项交叉 + 15 项提取)             │
  └──────┬───────┘                     └─────────────────────────────────────┘
         │ No
         ▼
  ┌──────────────┐     can_handle?     ┌─────────────────────────────────────┐
  │  继续检测     │ ──── Yes ──────────▶│  Linux 预分析器（采集脚本 .txt）    │
  │              │                     │  (SSH交叉验证+章节精简)              │
  └──────┬───────┘                     └─────────────────────────────────────┘
         │ No
         ▼
  [ERROR] 无法识别日志平台

设计原则:
  1. AI 无需知道原日志是哪个平台的
  2. 逐个调用平台预分析器的 can_handle()，命中即处理
  3. 新增平台只需在 ANALYZERS 列表中注册即可
"""

import argparse
import importlib
import os
import sys
import traceback
from pathlib import Path

# 确保本脚本所在目录在 sys.path 中（支持任意工作目录调用）
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# ---------------------------------------------------------------------------
# 平台预分析器注册表
# ---------------------------------------------------------------------------
# 每个条目: (模块路径, 平台目录名, 平台名称)
# 按优先级排序——先检测更具体的平台
# 平台目录名用于将该目录加入 sys.path（子模块需要 _pa_xxx 等内部包可见）

ANALYZERS = [
    ("linux_zip.preanalyze_linux_zip",             "linux_zip",         "Linux-Zip"),
    ("linux_log_folder.preanalyze_linux_log_folder", "linux_log_folder", "Linux-LogFolder"),
    ("windows.preanalyze_windows",                 "windows",           "Windows"),
    ("linux_check.preanalyze_linuxcheck",           "linux_check",       "LinuxCheck"),
    ("linux.preanalyze_linux",                     "linux",             "Linux"),
]


def _load_analyzer(module_path: str, platform_dir: str):
    """动态加载平台预分析器模块。

    在导入前将平台子目录加入 sys.path，使各平台的 _pa_xxx 内部包可被导入。

    历史背景：早期各平台都使用同名 `_preanalyze` 包，导致跨平台 sys.modules
    污染（先被加载的平台 _preanalyze 会"绑架"后续平台的同名 import）。
    现已改为带平台前缀的真实包名（_pa_linux / _pa_linuxcheck / _pa_windows），
    根本杜绝了同名冲突，因此不再需要清理 sys.modules 缓存。
    """
    subdir = str(_SCRIPT_DIR / platform_dir)
    if subdir not in sys.path:
        sys.path.insert(0, subdir)
    return importlib.import_module(module_path)


def main():
    parser = argparse.ArgumentParser(
        description="入侵检测日志预分析统一入口。自动识别日志平台并路由到对应预分析器。",
        epilog=(
            "示例:\n"
            "  python3 preanalyze.py log_host_20260401.txt       # 采集脚本输出（单主机）\n"
            "  python3 preanalyze.py /path/to/incident.zip        # 多主机 ZIP 包\n"
            "  python3 preanalyze.py /path/to/var/log/            # 原始 var/log 目录\n"
            "  python3 preanalyze.py incident.zip --debug         # 启用 INFO 调试日志\n"
            "\n"
            f"已注册平台: {', '.join(name for _, _, name in ANALYZERS)}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("log_path", help="日志文件路径 (.txt)、ZIP 包路径 (.zip) 或 var/log 目录路径")
    parser.add_argument("--debug", action="store_true", help="输出 INFO 级别调试日志到 stderr（默认静默）")

    args = parser.parse_args()

    if args.debug:
        os.environ["PREANALYZE_DEBUG"] = "1"

    log_path = Path(args.log_path)

    if not log_path.exists():
        print(f"[ERROR] 路径不存在: {log_path}", file=sys.stderr)
        sys.exit(1)

    # --- 任务委派：逐个检测平台 ---
    for module_path, platform_dir, platform_name in ANALYZERS:
        try:
            analyzer_mod = _load_analyzer(module_path, platform_dir)
        except ImportError as e:
            print(
                f"[WARN] 加载 {platform_name} 预分析器失败: {e}",
                file=sys.stderr,
            )
            continue

        if analyzer_mod.can_handle(str(log_path)):
            try:
                output = analyzer_mod.run(str(log_path))
                print(output)
                sys.exit(0)
            except Exception as e:
                print(
                    f"[ERROR] {platform_name} 预分析失败: {e}",
                    file=sys.stderr,
                )
                traceback.print_exc(file=sys.stderr)
                sys.exit(1)

    # 所有平台都无法识别
    print(
        f"[ERROR] 无法识别输入格式。已尝试: "
        f"{', '.join(name for _, _, name in ANALYZERS)}。"
        f"\n支持: .txt（采集脚本输出）/ .zip（多主机包）/ var/log 目录。",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
