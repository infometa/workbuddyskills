#!/usr/bin/env python3
"""
parse_oom_events.py — OOM 事件解析脚本

从 Linux 系统日志（/var/log/messages、/var/log/syslog 等）中提取结构化 OOM 事件.
支持标准内核 OOM、cgroup OOM 两种触发形式.

用法:
    python3 parse_oom_events.py --log-file /var/log/messages --output /tmp/events.json
    python3 parse_oom_events.py --log-file /var/log/messages  # 输出到 stdout
    python3 parse_oom_events.py --log-file /var/log/messages --page-size 16  # ARM64 系统

输出 JSON 格式:
    {
        "oom_events": [
            {
                "trigger_time": "2026-03-30 14:23:15",
                "trigger_type": "standard" | "cgroup",
                "killed_pid": 12345,
                "killed_name": "java",
                "killed_rss_kb": 8388608,
                "total_vm_kb": 16777216,
                "anon_rss_kb": 8000000,
                "file_rss_kb": 388608,
                "oom_score": 900,
                "free_mem_kb": 128000,
                "cgroup_path": "/sys/fs/cgroup/...",  # cgroup OOM 才有
                "top_rss_procs": [
                    {"pid": 12345, "name": "java", "rss_kb": 8388608, "oom_score_adj": 0}
                ],
                "raw_line_count": 42
            }
        ],
        "summary": {
            "total_events": 1,
            "killed_processes": ["java"],
            "earliest_event": "...",
            "latest_event": "..."
        }
    }
"""

import re
import json
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── 时间戳正则（支持 syslog 和 ISO 格式）────────────────────────────────────

# syslog 格式: "Mar 30 14:23:15"（无年份，需从外部补充）
_TS_SYSLOG = re.compile(
    r'(?P<ts>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'
)
# ISO 格式: "2026-03-30 14:23:15" 或 "2026-03-30T14:23:15"
_TS_ISO = re.compile(
    r'(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})'
)


# ── OOM 关键正则 ─────────────────────────────────────────────────────────────

# 标准 OOM 触发: "Out of memory: Kill process 1234 (java) score 900 or sacrifice child"
_OOM_KILL = re.compile(
    r'Out of memory: Kill process (\d+) \((.+?)\) score (\d+)'
)

# cgroup OOM 触发: "Memory cgroup out of memory: Kill process 1234 (java) task_memcg=..."
_OOM_CGROUP = re.compile(
    r'Memory cgroup out of memory: Kill process (\d+) \((.+?)\)'
)

# cgroup 路径提取
_CGROUP_PATH = re.compile(
    r'task_memcg=(\S+)'
)

# 被杀进程行: "Killed process 1234 (java) total-vm:494624kB, anon-rss:409600kB, file-rss:4096kB"
_KILLED = re.compile(
    r'Killed process (\d+) \((.+?)\) total-vm:(\d+)kB,\s*anon-rss:(\d+)kB,\s*file-rss:(\d+)kB'
)

# 进程列表行: "[ 1234]     0  1234   123456   102400   0      0          1000 java"
_PROC_LINE = re.compile(
    r'\[\s*(\d+)\]\s+\d+\s+\d+\s+\d+\s+(\d+)\s+\d+\s+[-\d]+\s+([-\d]+)\s+(\S+)'
)

# Node 内存快照: "Node 0 Normal free:128000kB ..."
_NODE_FREE = re.compile(
    r'Node \d+ \S+ free:(\d+)kB'
)


def _detect_page_size_kb() -> int:
    """自动检测当前系统页面大小（KB）.

    优先使用 os.sysconf，失败时返回默认值 4.
    仅在分析本机日志时有意义；分析离线日志时应通过 --page-size 手动指定.
    """
    try:
        page_bytes = os.sysconf('SC_PAGE_SIZE')
        return max(1, page_bytes // 1024)
    except (ValueError, OSError):
        return 4


def _infer_log_year(log_lines: list[str], log_path: Path) -> int:
    """从日志内容或文件元数据推断年份，用于补全 syslog 时间戳.

    推断优先级：
    1. 扫描前 50 行，从 ISO 格式时间戳提取年份
    2. 使用日志文件的 mtime（文件最后修改时间）的年份
    3. 兜底：返回当前年份

    Args:
        log_lines: 日志行列表（取前 50 行扫描）
        log_path: 日志文件路径（用于读取 mtime）

    Returns:
        推断出的 4 位年份整数
    """
    # 方案 1：从前 50 行 ISO 时间戳提取年份
    for line in log_lines[:50]:
        m = _TS_ISO.search(line)
        if m:
            year_str = m.group('ts')[:4]
            try:
                return int(year_str)
            except ValueError:
                continue

    # 方案 2：使用文件 mtime
    try:
        mtime = log_path.stat().st_mtime
        return datetime.fromtimestamp(mtime).year
    except OSError:
        pass

    # 方案 3：当前年份
    return datetime.now().year


def _parse_timestamp(line: str, syslog_year: int = 0) -> Optional[str]:
    """从日志行提取时间戳字符串.

    Args:
        line: 单条日志行.
        syslog_year: 补全 syslog 格式时间戳使用的年份（0 表示不补全）.

    Returns:
        可读时间戳字符串，无法解析时返回 None.
    """
    # ISO 格式优先（自带年份）
    m = _TS_ISO.search(line)
    if m:
        return m.group('ts').replace('T', ' ')

    # syslog 格式（补充年份）
    m = _TS_SYSLOG.search(line)
    if m:
        ts = m.group('ts')
        if syslog_year:
            return f'{syslog_year} {ts}'
        return ts

    return None


def _pages_to_kb(pages: int, page_size_kb: int = 4) -> int:
    """内核进程列表中 RSS 列的单位是 page，转换为 KB.

    Args:
        pages: 页数（来自内核进程列表）.
        page_size_kb: 页面大小（KB），x86-64 默认 4，ARM64 可能为 16 或 64.
    """
    return pages * page_size_kb


def parse_oom_events(
    log_lines: list[str],
    syslog_year: int = 0,
    page_size_kb: int = 4,
) -> list[dict]:
    """主解析函数，从日志行列表中提取所有 OOM 事件.

    Args:
        log_lines: 日志行列表（已按时间排序）
        syslog_year: 补全 syslog 格式时间戳的年份（0 表示不补全）
        page_size_kb: 页面大小（KB），用于进程列表 RSS 列换算

    Returns:
        OOM 事件列表，每个事件为字典
    """
    events = []
    i = 0
    n = len(log_lines)

    while i < n:
        line = log_lines[i]

        # 检测 OOM 事件开始
        m_kill = _OOM_KILL.search(line)
        m_cgroup = _OOM_CGROUP.search(line)

        if not m_kill and not m_cgroup:
            i += 1
            continue

        event_lines = [line]
        ts = _parse_timestamp(line, syslog_year)

        if m_kill:
            trigger_type = 'standard'
            killed_pid = int(m_kill.group(1))
            killed_name = m_kill.group(2).strip()
            oom_score = int(m_kill.group(3))
        else:
            trigger_type = 'cgroup'
            killed_pid = int(m_cgroup.group(1))
            killed_name = m_cgroup.group(2).strip()
            oom_score = 0

        # 从触发行提取 cgroup 路径（task_memcg= 常与触发行同行）
        cgroup_path = ''
        m_cg_trigger = _CGROUP_PATH.search(line)
        if m_cg_trigger:
            cgroup_path = m_cg_trigger.group(1)

        # 向后扫描最多 500 行，收集完整事件信息
        # 大型机器进程列表可能超过 200 行，使用 500 行避免截断
        killed_rss_kb = 0
        total_vm_kb = 0
        anon_rss_kb = 0
        file_rss_kb = 0
        free_mem_kb = 0
        top_procs: list[dict] = []

        j = i + 1
        while j < min(i + 500, n):
            sub = log_lines[j]

            # 遇到下一个 OOM 事件时停止（必须在处理该行内容之前 break）
            if j > i + 1 and (_OOM_KILL.search(sub) or _OOM_CGROUP.search(sub)):
                break

            event_lines.append(sub)

            # 被杀进程详情
            m_killed = _KILLED.search(sub)
            if m_killed and int(m_killed.group(1)) == killed_pid:
                total_vm_kb = int(m_killed.group(3))
                anon_rss_kb = int(m_killed.group(4))
                file_rss_kb = int(m_killed.group(5))
                killed_rss_kb = anon_rss_kb + file_rss_kb

            # 进程列表行
            m_proc = _PROC_LINE.search(sub)
            if m_proc:
                rss_kb = _pages_to_kb(int(m_proc.group(2)), page_size_kb)
                top_procs.append({
                    'pid': int(m_proc.group(1)),
                    'rss_kb': rss_kb,
                    'oom_score_adj': int(m_proc.group(3)),
                    'name': m_proc.group(4),
                })

            # Node 内存快照（取最小 free 值作为 OOM 时的剩余内存）
            m_free = _NODE_FREE.search(sub)
            if m_free:
                free_kb = int(m_free.group(1))
                if free_mem_kb == 0 or free_kb < free_mem_kb:
                    free_mem_kb = free_kb

            # cgroup 路径
            m_cg = _CGROUP_PATH.search(sub)
            if m_cg and not cgroup_path:
                cgroup_path = m_cg.group(1)

            j += 1

        # 按 RSS 降序取 Top 10 进程
        top_procs.sort(key=lambda x: x['rss_kb'], reverse=True)

        event = {
            'trigger_time': ts or '',
            'trigger_type': trigger_type,
            'killed_pid': killed_pid,
            'killed_name': killed_name,
            'oom_score': oom_score,
            'killed_rss_kb': killed_rss_kb,
            'total_vm_kb': total_vm_kb,
            'anon_rss_kb': anon_rss_kb,
            'file_rss_kb': file_rss_kb,
            'free_mem_kb': free_mem_kb,
            'cgroup_path': cgroup_path,
            'top_rss_procs': top_procs[:10],
            'raw_line_count': len(event_lines),
        }
        events.append(event)
        i = j

    return events


def build_summary(events: list[dict]) -> dict:
    """生成汇总信息."""
    if not events:
        return {
            'total_events': 0,
            'killed_processes': [],
            'earliest_event': '',
            'latest_event': '',
        }

    killed = list({e['killed_name'] for e in events})
    times = [e['trigger_time'] for e in events if e['trigger_time']]

    return {
        'total_events': len(events),
        'killed_processes': killed,
        'earliest_event': min(times) if times else '',
        'latest_event': max(times) if times else '',
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description='从 Linux 系统日志中解析 OOM 事件',
    )
    parser.add_argument(
        '--log-file', '-f',
        required=True,
        help='日志文件路径（支持纯文本，每行一条日志）',
    )
    parser.add_argument(
        '--output', '-o',
        default='',
        help='输出 JSON 文件路径（不指定则输出到 stdout）',
    )
    parser.add_argument(
        '--pretty', '-p',
        action='store_true',
        default=False,
        help='JSON 格式化输出（默认关闭，输出紧凑 JSON）',
    )
    parser.add_argument(
        '--page-size',
        type=int,
        default=0,
        help='内核页面大小（KB），用于进程列表 RSS 换算。'
             '默认自动检测当前系统页面大小（x86-64=4，ARM64 可能为 16 或 64）。'
             '分析离线日志时建议手动指定目标机器的页面大小。',
    )
    args = parser.parse_args()

    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f'[ERROR] 日志文件不存在: {log_path}', file=sys.stderr)
        sys.exit(1)

    log_lines = log_path.read_text(encoding='utf-8', errors='replace').splitlines()
    print(f'[INFO] 共读取 {len(log_lines)} 行日志，开始解析...', file=sys.stderr)

    # 确定页面大小：CLI 参数 > 系统自动检测 > 默认 4
    if args.page_size > 0:
        page_size_kb = args.page_size
        print(f'[INFO] 使用指定页面大小: {page_size_kb} KB', file=sys.stderr)
    else:
        page_size_kb = _detect_page_size_kb()
        print(f'[INFO] 自动检测页面大小: {page_size_kb} KB', file=sys.stderr)

    # 推断 syslog 时间戳年份
    syslog_year = _infer_log_year(log_lines, log_path)
    print(f'[INFO] 使用年份补全 syslog 时间戳: {syslog_year}', file=sys.stderr)

    events = parse_oom_events(log_lines, syslog_year=syslog_year, page_size_kb=page_size_kb)
    summary = build_summary(events)

    result = {
        'oom_events': events,
        'summary': summary,
    }

    indent = 2 if args.pretty else None
    output_str = json.dumps(result, ensure_ascii=False, indent=indent)

    if args.output:
        Path(args.output).write_text(output_str, encoding='utf-8')
        print(f'[INFO] 解析完成，共找到 {len(events)} 个 OOM 事件，结果写入: {args.output}', file=sys.stderr)
    else:
        print(output_str)


if __name__ == '__main__':
    main()
