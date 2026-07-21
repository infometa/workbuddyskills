#!/usr/bin/env python3
"""
Windows 入侵检测日志预分析工具

读取 PS1 采集的纯文本日志（.txt），自动完成 5 项交叉分析 + 15 项数据精简提取，
输出 Markdown 格式的结构化中间结果到 stdout，供 AI 分析师直接使用。

用法（通过统一入口）:
  python3 scripts/analysis/preanalyze.py <log_file.txt>

用法（直接调用）:
  cd scripts/analysis/windows && python3 preanalyze_windows.py <log_file.txt>

数据流:
  log_xxx.txt → 章节解析 → 表格解析 → 分析模块 → MdRenderer → stdout (Markdown)
                    │            │
                    v            v
              章节索引      结构化记录
                    │            │
                    v            v
              ┌─────────────────────────────────────────┐
              │  5 项交叉分析:                           │
              │   1. 暴力破解交叉验证                    │
              │   2. 活跃连接交叉验证                    │
              │   3. PowerShell 4104 噪声过滤            │
              │   4. RDP 四证据交叉验证                  │
              │   5. USN 勒索特征扫描                    │
              │                                         │
              │  15 项数据精简提取 (v1.5.0):             │
              │   1-9.  系统画像 + 8类事件日志           │
              │   10-15. 进程/IIS/启动项/签名/命令       │
              └─────────────────────────────────────────┘
                           │
                           v
                   MdRenderer → stdout (Markdown)

模块结构:
  windows/
    ├── preanalyze_windows.py  ← 入口 + PreAnalyzer 编排器 + can_handle/run 接口
    └── _pa_windows/
        ├── __init__.py        ← __version__
        ├── constants.py       ← 正则/白名单/枚举常量
        ├── models.py          ← SectionIndex, SubsectionIndex
        ├── parsers.py         ← Phase 1/2: 日志解析 + IP 分类
        ├── analyzers.py       ← Phase 3: 5 个交叉分析函数
        ├── extractors.py      ← Phase 2.5: ExtractorMixin (15 个提取方法)
        └── renderer.py        ← Phase 5: MdRenderer
"""

import argparse
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# 支持直接调用：确保 _common 和 _pa_windows 均可导入
# 当通过统一入口 preanalyze.py 调用时，sys.path 已由入口设置好；
# 当直接调用本脚本时（cd windows && python3 preanalyze_windows.py），需要自行设置。
_THIS_DIR = Path(__file__).resolve().parent          # .../scripts/analysis/windows
_ANALYSIS_DIR = _THIS_DIR.parent                     # .../scripts/analysis
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))               # 使 _pa_windows 可导入
if str(_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_DIR))            # 使 _common 可导入

from _pa_windows import __version__
from _pa_windows.analyzers import (
    analyze_4104_filter,
    analyze_active_connections,
    analyze_brute_force,
    analyze_rdp_cross_check,
    analyze_usn_ransomware,
    compute_risk_score,
)
from _pa_windows.extractors import ExtractorMixin
from _pa_windows.models import SectionIndex
from _pa_windows.parsers import (
    extract_event_data,
    extract_section_kv_data,
    parse_log_structure,
)
from _pa_windows.renderer import MdRenderer


# ---------------------------------------------------------------------------
# 任务委派接口
# ---------------------------------------------------------------------------

# Windows 日志特征标记（PS1 采集脚本在元数据段写入的固定标识）
_RE_WINDOWS_META = re.compile(
    r"^\s*OSType\s*:\s*Windows", re.MULTILINE
)

# Windows 日志特有的章节（Linux 不会出现）
_WINDOWS_SECTION_MARKERS = [
    "======== SECTION: SystemEvent ========",
    "======== SECTION: USNLogs ========",
    "======== SECTION: CheckSignature ========",
    "======== SECTION: PSReadLineHistory ========",
]


def can_handle(log_path: str) -> bool:
    """判断日志文件是否为 Windows 平台采集的日志。

    检测策略（快速扫描前 200 行 + 关键标记）：
    1. 元数据段包含 OSType: Windows
    2. 包含 Windows 特有的章节标记（SystemEvent/USNLogs/CheckSignature 等）
    """
    try:
        p = Path(log_path)
        text = p.read_text(encoding="utf-8-sig", errors="replace")

        # 策略 1: 元数据标记
        if _RE_WINDOWS_META.search(text[:5000]):
            return True

        # 策略 2: Windows 特有章节标记（扫描全文）
        for marker in _WINDOWS_SECTION_MARKERS:
            if marker in text:
                return True

        return False
    except Exception as e:
        print(f"[WARN] Windows can_handle 检测异常: {e}", file=sys.stderr)
        return False


def run(log_path: str) -> str:
    """执行 Windows 预分析，返回 Markdown 文本。

    供统一入口 preanalyze.py 调用。
    """
    analyzer = PreAnalyzer(log_path=log_path)
    result = analyzer.run()
    renderer = MdRenderer(result)
    return renderer.render()


# ---------------------------------------------------------------------------
# Main Analyzer
# ---------------------------------------------------------------------------


class PreAnalyzer(ExtractorMixin):
    """预分析器主类。"""

    def __init__(
        self,
        log_path: str,
    ):
        self.log_path = Path(log_path)
        self.lines: list[str] = []
        self.sections: list[SectionIndex] = []
        self.meta: dict = {}

    def run(self) -> dict:
        """执行全部分析，返回完整 JSON 结构（含 summary 摘要）。"""
        start_time = time.time()

        # 读取日志文件（去除 BOM 标记）
        text = self.log_path.read_text(encoding="utf-8-sig", errors="replace")
        self.lines = text.splitlines()

        # Phase 1: 结构解析
        self.sections = parse_log_structure(self.lines)

        # 提取元数据
        self.meta = extract_section_kv_data(
            self.lines, self.sections, "_CollectionMeta"
        )

        # Phase 2: 数据提取（交叉分析所需的原始数据）
        # 【架构约束 (D4)】以下变量仅供 Phase 3 使用，Phase 2.5 禁止引用或修改：
        #   events_4624, events_4625, events_4104, events_1149,
        #   events_21_25, network_tcp, usn_records
        events_4624 = extract_event_data(
            self.lines, self.sections, "login_success_4624"
        )
        events_4625 = extract_event_data(
            self.lines, self.sections, "login_failed_4625"
        )
        events_4104 = extract_event_data(
            self.lines, self.sections, "powershell_scriptblock_4104"
        )
        events_1149 = extract_event_data(
            self.lines, self.sections, "rdp_connection_1149"
        )
        events_21_25 = extract_event_data(
            self.lines, self.sections, "rdp_session_logon_21_25"
        )
        network_tcp = extract_event_data(
            self.lines, self.sections, "network_tcp"
        )
        usn_records = extract_event_data(
            self.lines, self.sections, "USNLogs"
        )

        # ─── Phase 2.5: 精简数据提取 (v1.5.0 新增) ───
        system_info = self._extract_system_info()                    # 模块 1: 📐 结构化提取 6 子段
        events_4672 = self._extract_simple_events(                   # 模块 2: ✅ 直接保留
            "login_privilege_4672", drop_cols=["#", "count"])
        events_4720 = self._extract_simple_events(                   # 模块 3: ✅ 声明空
            "account_created_4720")
        events_4688 = self._extract_4688_process_creation()          # 模块 4: 📊 启动周期去重
        events_4657 = self._extract_simple_events(                   # 模块 5: ✅ 声明空
            "registry_changes_4657")
        events_7045 = self._extract_simple_events(                   # 模块 6: ✅ 直接保留
            "service_install_7045", drop_cols=["#"])
        events_7040 = self._extract_simple_events(                   # 模块 7: ✅ 直接保留
            "service_change_startup_type_7040", drop_cols=["#", "count"])
        events_start_stop = self._extract_system_start_stop()        # 模块 8: 📊 启停时间线聚合
        events_4103 = self._extract_simple_events(                   # 模块 9: ✅ 声明空
            "powershell_module_4103")
        processes = self._extract_processes()                        # 模块 10: 📊 非标准进程过滤
        iis_logs = self._extract_iis_logs()                         # 模块 12: 📊 IP 聚合 + 攻击分类
        startup_items = self._extract_startup_items()                # 模块 13: 🔍 过滤标准任务
        check_sig = self._extract_simple_events(                     # 模块 14: ✅ 直接保留
            "CheckSignature", drop_cols=["#"])
        psreadline = self._extract_psreadline()                      # 模块 15: ✅ 直接保留

        # Phase 3: 交叉分析
        brute_force = analyze_brute_force(events_4625, events_4624)
        active_conn = analyze_active_connections(
            network_tcp, events_4624, events_4625
        )

        ps_filter = analyze_4104_filter(events_4104)
        rdp = analyze_rdp_cross_check(
            events_4624, events_1149, events_21_25, network_tcp
        )
        usn_ransomware = analyze_usn_ransomware(usn_records)

        # Phase 3.5: 低噪入侵者检测 + 威胁评分自动计算
        from _pa_windows.parsers import is_external_ip as _is_ext
        bruteforce_ip_set = {a["ip"] for a in brute_force["attack_ips"]}
        stealth_intruders = []
        for rec in events_4624:
            if rec.get("LogonType") == "10":
                ip = rec.get("IpAddress", "-")
                if ip and ip not in ("-", "") and ip not in bruteforce_ip_set:
                    if _is_ext(ip):
                        stealth_intruders.append(ip)
        stealth_intruders = list(dict.fromkeys(stealth_intruders))  # 去重保序

        threat_score = compute_risk_score(
            brute_force=brute_force,
            active_conn=active_conn,
            rdp=rdp,
            usn_ransomware=usn_ransomware,
            startup_items=startup_items,
            system_info=system_info,
            stealth_intruders=stealth_intruders,
        )

        # Phase 4: 汇总输出
        elapsed = time.time() - start_time

        # 构建精简摘要
        summary = self._build_summary(
            events_4624, events_4625, events_4104, events_1149,
            events_21_25, network_tcp, usn_records,
            brute_force, active_conn, ps_filter, rdp,
            usn_ransomware, elapsed,
            # Phase 2.5 新数据（用于扩展摘要行）
            system_info, processes, startup_items, iis_logs, psreadline,
            # Phase 3.5
            stealth_intruders=stealth_intruders,
            threat_score=threat_score,
        )

        output = {
            # --- 已有字段 (不变) ---
            "meta": {
                "script_version": __version__,
                "log_file": str(self.log_path.name),
                "log_path": str(self.log_path),
                "hostname": self.meta.get("ComputerName", "unknown"),
                "collection_time": self.meta.get("CollectionTimestamp", ""),
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "analysis_elapsed_seconds": round(elapsed, 1),
                "total_lines": len(self.lines),
            },
            "summary": summary,
            "threat_score": threat_score,
            "brute_force_cross_check": brute_force,
            "active_connection_cross_check": active_conn,
            "powershell_4104_filter": ps_filter,
            "rdp_cross_check": rdp,
            "usn_ransomware_scan": usn_ransomware,
            # --- 新增字段 (v1.5.0，每个包含 status 字段) ---
            "system_info": system_info,
            "events_4672_privilege": events_4672,
            "events_4720_account_created": events_4720,
            "events_4688_process_creation": events_4688,
            "events_4657_registry": events_4657,
            "events_7045_service_install": events_7045,
            "events_7040_service_change": events_7040,
            "events_system_start_stop": events_start_stop,
            "events_4103_powershell_module": events_4103,
            "processes": processes,
            "iis_logs": iis_logs,
            "startup_items": startup_items,
            "check_signature": check_sig,
            "psreadline_history": psreadline,
        }

        # Phase 4.5: 数据质量校验
        output["data_quality_warnings"] = self._check_data_quality(output)

        return output


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Windows 入侵检测日志预分析工具（Markdown 输出到 stdout）",
        epilog=(
            "示例:\n"
            "  python3 preanalyze_windows.py log_host_20260324.txt\n"
            "\n"
            "推荐通过统一入口调用:\n"
            "  python3 scripts/analysis/preanalyze.py log_host_20260324.txt\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("log_file", help="PS1 采集的日志文件路径 (.txt)")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args()

    # 验证输入文件
    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"[ERROR] 日志文件不存在: {log_path}", file=sys.stderr)
        sys.exit(1)

    # 运行分析
    analyzer = PreAnalyzer(
        log_path=str(log_path),
    )

    try:
        result = analyzer.run()
    except Exception as e:
        print(f"[ERROR] 分析失败: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    # Markdown 输出到 stdout（禁止中间文件落地）
    renderer = MdRenderer(result)
    print(renderer.render())


if __name__ == "__main__":
    main()
