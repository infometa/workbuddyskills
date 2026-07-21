#!/usr/bin/env python3
"""
LinuxCheck.sh 日志预分析工具

适配第三方开源脚本 al0ne/LinuxCheck (V3.0) 产生的 Markdown 格式安全检查日志。
对日志进行激进精简（目标 ~4K token），输出格式保持 Markdown 不变。

与自研 get_log_all_in_one.sh 的 Linux 预分析器不同：
  - LinuxCheck 日志为 Markdown 格式（## / ### / ```shell）
  - LinuxCheck 不采集原始 syslog → 无法做 SSH 交叉验证
  - 本预分析器激进压缩以适配 LLM 上下文窗口

用法（通过统一入口）:
  python3 scripts/analysis/preanalyze.py <linuxcheck_log.md>

用法（直接调用）:
  cd scripts/analysis/linux_check && python3 preanalyze_linuxcheck.py <log.md>

数据流:
  LinuxCheck.md → 空块清理 → 整节删除 → 章节级精简 → 空节移除 → Markdown stdout
"""

import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# 支持直接调用：确保内部包可导入
_THIS_DIR = Path(__file__).resolve().parent
_ANALYSIS_DIR = _THIS_DIR.parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
if str(_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_DIR))

from _pa_linuxcheck import __version__
from _pa_linuxcheck.cleaners import (
    collapse_consecutive_blank_lines,
    compress_last_login,
    filter_authorized_keys,
    filter_file_mtime,
    filter_history_commands,
    filter_initd,
    filter_lastlog,
    filter_mining_self_process,
    filter_network_connections,
    filter_port_listening,
    filter_process_top,
    filter_running_services,
    filter_sensitive_files,
    filter_suid_files,
    filter_tmp_directory,
    remove_empty_code_blocks,
    remove_empty_sections,
)
from _pa_linuxcheck.constants import LINUXCHECK_MARKERS, SECTIONS_TO_REMOVE

# ---------------------------------------------------------------------------
# 任务委派接口
# ---------------------------------------------------------------------------

# LinuxCheck.sh 特征检测：至少命中 3 个标记才算 LinuxCheck 日志
_MIN_MARKER_HITS = 3


def can_handle(log_path: str) -> bool:
    """判断日志文件是否为 LinuxCheck.sh 产生的 Markdown 日志。"""
    try:
        p = Path(log_path)
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        hits = sum(1 for marker in LINUXCHECK_MARKERS if marker in text)
        return hits >= _MIN_MARKER_HITS
    except Exception as e:
        print(f"[WARN] LinuxCheck can_handle 检测异常: {e}", file=sys.stderr)
        return False


def run(log_path: str) -> str:
    """执行 LinuxCheck.sh 预分析，返回精简后的 Markdown 文本。"""
    analyzer = LinuxCheckPreAnalyzer(log_path)
    return analyzer.run()


# ---------------------------------------------------------------------------
# 章节解析
# ---------------------------------------------------------------------------

_RE_H2 = re.compile(r"^## (.+)$")
_RE_H3 = re.compile(r"^### (.+)$")


def _parse_sections(lines: list[str]) -> list[dict]:
    """解析 LinuxCheck Markdown 日志的章节结构。

    返回: [{"level": 2|3, "title": str, "start": int, "end": int}, ...]
    """
    sections = []
    for i, line in enumerate(lines):
        m2 = _RE_H2.match(line)
        m3 = _RE_H3.match(line) if not m2 else None
        if m2:
            sections.append({
                "level": 2, "title": m2.group(1).strip(),
                "start": i + 1, "end": len(lines),
            })
        elif m3:
            sections.append({
                "level": 3, "title": m3.group(1).strip(),
                "start": i + 1, "end": len(lines),
            })

    # 修正 end
    for idx in range(len(sections)):
        if idx + 1 < len(sections):
            sections[idx]["end"] = sections[idx + 1]["start"] - 1

    return sections


# ---------------------------------------------------------------------------
# Main Analyzer
# ---------------------------------------------------------------------------


class LinuxCheckPreAnalyzer:
    """LinuxCheck.sh 预分析器主类。"""

    def __init__(self, log_path: str):
        self.log_path = Path(log_path)

    def run(self) -> str:
        """执行预分析，返回精简后的 Markdown 文本。"""
        start_time = time.time()

        text = self.log_path.read_text(encoding="utf-8-sig", errors="replace")
        original_lines = text.splitlines()
        original_chars = len(text)

        # Phase 1: 全局清理——移除空代码块
        text = remove_empty_code_blocks(text)

        # Phase 2: 删除无价值整节
        text = self._remove_sections(text)

        # Phase 3: 章节级精简
        lines = text.splitlines()
        sections = _parse_sections(lines)
        text = self._process_sections(lines, sections)

        # Phase 4: 处理非代码块内容（系统文件修改时间等）
        text = self._process_inline_content(text)

        # Phase 5: 移除空章节
        text = remove_empty_sections(text)

        # Phase 5.5: 再次清理空代码块（filter 函数可能产生新的空块）
        text = remove_empty_code_blocks(text)

        # Phase 5.6: 清理孤立的 markdown 标记（如 **UDP连接** 后跟空内容）
        text = re.sub(r"\n\*\*UDP连接\*\*\s*\n", "\n", text)

        # Phase 6: 压缩连续空行
        text = collapse_consecutive_blank_lines(text)

        elapsed = time.time() - start_time
        final_lines = text.splitlines()

        # 构建预分析头部
        header = []
        header.append("# 预分析报告")
        header.append("")
        header.append(
            "platform: Linux (LinuxCheck.sh) | "
            f"preanalyze_version: {__version__} | "
            "template: templates/analysis_report_template.md"
        )
        header.append(
            f"log: {self.log_path.name} | "
            f"分析: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"原始: {len(original_lines)} 行 ({original_chars} 字节) | "
            f"精简后: {len(final_lines)} 行 | "
            f"耗时: {round(elapsed, 2)}s"
        )
        header.append("")
        header.append("---")
        header.append("")

        return "\n".join(header) + text.strip() + "\n"

    def _remove_sections(self, text: str) -> str:
        """删除 SECTIONS_TO_REMOVE 中列出的整个子章节。"""
        lines = text.splitlines()
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]
            # 检测 ### 标题
            if line.startswith("### "):
                title = line[4:].strip()
                if title in SECTIONS_TO_REMOVE:
                    # 跳过整个子章节直到下一个 ## 或 ###
                    i += 1
                    while i < len(lines):
                        if lines[i].startswith("## ") or lines[i].startswith(
                            "### "
                        ):
                            break
                        i += 1
                    continue
            result.append(line)
            i += 1

        return "\n".join(result)

    def _process_inline_content(self, text: str) -> str:
        """处理非代码块内的内容（如系统文件修改时间行）。"""
        lines = text.splitlines()
        result = []
        has_file_timestamps = False
        for line in lines:
            # 过滤空日期的系统文件修改时间行
            if "修改日期：" in line:
                date_part = line.split("修改日期：")[-1].strip()
                if not date_part:
                    continue  # 无日期数据，跳过
                has_file_timestamps = True
            result.append(line)
        # 如果所有条目都被过滤了，也删除标题行
        if not has_file_timestamps:
            result = [
                l for l in result
                if "系统文件修改时间" not in l
            ]
        return "\n".join(result)

    def _process_sections(
        self, lines: list[str], sections: list[dict]
    ) -> str:
        """对各章节应用精简处理器。"""
        # 子章节标题 → 处理函数映射
        section_handlers = {
            "登录信息 lastlog": self._handle_lastlog,
            "登录信息 last": self._handle_last_login,
            "CPU占用TOP 15": self._handle_process_top,
            "内存占用TOP 15": self._handle_process_top,
            "SUID": self._handle_suid,
            "/tmp": self._handle_tmp_dir,
            "敏感文件 ": self._handle_sensitive_files,
            "env": self._handle_env,
            "常规挖矿进程检测": self._handle_mining,
            "正在运行的Service": self._handle_running_services,
            "History敏感操作": self._handle_history,
            "网络连接": self._handle_network_connections,
            "端口监听": self._handle_port_listening,
            "/etc/init.d 记录": self._handle_initd,
            "近七天文件改动 mtime": self._handle_file_mtime,
            "authorized_keys": self._handle_authorized_keys,
        }

        # 按 section 从后向前替换
        replacements = []
        for sec in sections:
            title = sec["title"]
            handler = None
            for key, func in section_handlers.items():
                if title.strip().startswith(key.strip()):
                    handler = func
                    break
            if handler:
                sub_lines = lines[sec["start"]:sec["end"]]
                new_lines = handler(sub_lines)
                if new_lines is not None:
                    replacements.append(
                        (sec["start"], sec["end"], new_lines)
                    )

        # 从后向前替换
        result_lines = list(lines)
        for start, end, new_lines in sorted(
            replacements, key=lambda x: x[0], reverse=True
        ):
            result_lines[start:end] = new_lines

        return "\n".join(result_lines)

    def _handle_last_login(self, sub_lines: list[str]) -> list[str]:
        """压缩 last 登录历史。"""
        in_code = False
        code_lines = []
        before = []
        after = []

        for line in sub_lines:
            stripped = line.strip()
            if stripped == "```shell" or stripped == "```":
                if not in_code and stripped == "```shell":
                    in_code = True
                    continue
                elif in_code and stripped == "```":
                    in_code = False
                    continue
            if in_code:
                code_lines.append(line)
            elif not code_lines:
                before.append(line)
            else:
                after.append(line)

        if not code_lines:
            return None

        compressed = compress_last_login(code_lines)
        return before + compressed + after

    def _handle_process_top(self, sub_lines: list[str]) -> list[str]:
        """过滤 CPU/MEM TOP 中的标准系统进程。"""
        return self._apply_code_block_filter(sub_lines, filter_process_top)

    def _handle_suid(self, sub_lines: list[str]) -> list[str]:
        """过滤标准 SUID/SGID 文件。"""
        return self._apply_code_block_filter(sub_lines, filter_suid_files)

    def _handle_tmp_dir(self, sub_lines: list[str]) -> list[str]:
        """过滤 /tmp 目录中的噪声。"""
        return self._apply_code_block_filter(sub_lines, filter_tmp_directory)

    def _handle_sensitive_files(self, sub_lines: list[str]) -> list[str]:
        """过滤敏感文件检测中的误报。"""
        return self._apply_code_block_filter(
            sub_lines, filter_sensitive_files
        )

    def _handle_env(self, sub_lines: list[str]) -> list[str]:
        """精简 env 环境变量：隐藏 API token 值。"""
        sensitive_patterns = re.compile(
            r"^(\w*(?:TOKEN|KEY|SECRET|PASSWORD|AUTH)\w*)=(.+)$",
            re.IGNORECASE,
        )
        result = []
        for line in sub_lines:
            stripped = line.strip()
            m = sensitive_patterns.match(stripped)
            if m:
                result.append(f"{m.group(1)}=[REDACTED]")
            else:
                result.append(line)
        return result

    def _handle_lastlog(self, sub_lines: list[str]) -> list[str]:
        """过滤 lastlog 中 Never logged in 的系统账户。"""
        return self._apply_code_block_filter(sub_lines, filter_lastlog)

    def _handle_mining(self, sub_lines: list[str]) -> list[str]:
        """过滤挖矿检测中 LinuxCheck.sh 自身进程的误报。"""
        return self._apply_code_block_filter(
            sub_lines, filter_mining_self_process
        )

    def _handle_running_services(self, sub_lines: list[str]) -> list[str]:
        """过滤正在运行的 Service 中的标准系统服务。"""
        return self._apply_code_block_filter(
            sub_lines, filter_running_services
        )

    def _handle_history(self, sub_lines: list[str]) -> list[str]:
        """过滤 History 敏感操作中的脚本源码噪声。"""
        return self._apply_code_block_filter(
            sub_lines, filter_history_commands
        )

    def _handle_network_connections(self, sub_lines: list[str]) -> list[str]:
        """过滤网络连接中的 localhost 回环。"""
        return self._apply_code_block_filter(
            sub_lines, filter_network_connections
        )

    def _handle_port_listening(self, sub_lines: list[str]) -> list[str]:
        """精简端口监听。"""
        return self._apply_code_block_filter(
            sub_lines, filter_port_listening
        )

    def _handle_initd(self, sub_lines: list[str]) -> list[str]:
        """过滤 /etc/init.d 标准系统脚本。"""
        return self._apply_code_block_filter(sub_lines, filter_initd)

    def _handle_file_mtime(self, sub_lines: list[str]) -> list[str]:
        """过滤文件 mtime 中的噪声。"""
        return self._apply_code_block_filter(sub_lines, filter_file_mtime)

    def _handle_authorized_keys(self, sub_lines: list[str]) -> list[str]:
        """截断 SSH 公钥内容。"""
        return self._apply_code_block_filter(
            sub_lines, filter_authorized_keys
        )

    @staticmethod
    def _apply_code_block_filter(
        sub_lines: list[str], filter_func
    ) -> list[str]:
        """通用代码块过滤器：提取 ```shell``` 内的行，应用过滤函数。"""
        in_code = False
        code_lines = []
        result = []

        for line in sub_lines:
            stripped = line.strip()
            if stripped == "```shell":
                if not in_code:
                    in_code = True
                    result.append(line)
                    continue
            elif stripped == "```" and in_code:
                in_code = False
                filtered = filter_func(code_lines)
                result.extend(filtered)
                result.append(line)
                code_lines = []
                continue
            if in_code:
                code_lines.append(line)
            else:
                result.append(line)

        return result


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="LinuxCheck.sh 日志预分析工具（Markdown 输出到 stdout）",
        epilog=(
            "示例:\n"
            "  python3 preanalyze_linuxcheck.py linuxcheck_log.md\n"
            "\n"
            "推荐通过统一入口调用:\n"
            "  python3 scripts/analysis/preanalyze.py linuxcheck_log.md\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("log_file", help="LinuxCheck.sh 日志文件路径 (.md)")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args()

    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"[ERROR] 日志文件不存在: {log_path}", file=sys.stderr)
        sys.exit(1)

    if not can_handle(str(log_path)):
        print("[ERROR] 该日志文件不是 LinuxCheck.sh 产生的日志", file=sys.stderr)
        sys.exit(1)

    print(run(str(log_path)))


if __name__ == "__main__":
    main()
