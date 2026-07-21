#!/usr/bin/env python3
"""
parse_memory_leak.py — 解析内存泄漏采集数据, 生成 summary.json.

输入（来自 collect_memory_leak.sh 的产物）:
  <LOG_DIR>/raw/config.json            运行配置
  <LOG_DIR>/raw/sample_<N>.json        单进程采样快照（进程模式）
  <LOG_DIR>/raw/global_sample_<N>.json 全局进程采样快照（全局模式）
  <LOG_DIR>/raw/meminfo_<N>.log        第 N 次采样时的 /proc/meminfo
  <LOG_DIR>/raw/meminfo_baseline.log   基线 meminfo
  <LOG_DIR>/raw/slabinfo.log           内核 slab 信息
  <LOG_DIR>/raw/dmesg_oom.log          dmesg OOM 日志
  <LOG_DIR>/raw/memleak_stack.log      eBPF 调用栈（可选）

输出:
  <LOG_DIR>/summary.json               结构化诊断结果
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── 常量 ────────────────────────────────────────────────────────────────────

# 泄漏判定阈值（%/min）
# 2.0%/min 对应 1 小时 RSS 翻倍，适合业务级泄漏检测
LEAK_CONFIRMED_THRESHOLD = 2.0
# 1.0%/min 对应每分钟增长 1%，缓慢泄漏的起点
LEAK_SUSPECTED_THRESHOLD = 1.0
# 绝对增量阈值：50MB 或内存总量 0.5%，取较大值（在 build_summary 中动态计算）
LARGE_ABS_DELTA_KB_DEFAULT = 50 * 1024    # 50MB 默认值
LARGE_ABS_DELTA_PCT = 0.005               # 0.5% 系统总内存
# fd 泄漏告警阈值（5000 更符合实际，避免高连接数服务误报）
FD_LEAK_THRESHOLD = 5000
# 内核不可回收 slab 告警阈值（MB）
SUNRECLAIM_THRESHOLD_MB = 500
# 最短监控时长（秒），不足则返回 insufficient_data
MIN_MONITORING_SEC = 30

# 泄漏结论的中文映射
VERDICT_CN = {
    "leak_confirmed": "确认泄漏",
    "leak_suspected": "疑似泄漏",
    "normal": "正常波动",
    "insufficient_data": "数据不足",
    "process_disappeared": "进程中途退出",
}


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def _read_json(path: Path) -> Optional[dict]:
    """读取 JSON 文件，失败返回 None."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _parse_meminfo(path: Path) -> dict[str, int]:
    """解析 /proc/meminfo，返回字段名 -> kB 的字典."""
    data: dict[str, int] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\w+):\s+(\d+)", line)
        if m:
            data[m.group(1)] = int(m.group(2))
    return data


def _eta_human(minutes: float) -> str:
    """将分钟数转换为人类可读格式."""
    if minutes < 60:
        return f"约 {int(minutes)} 分钟"
    elif minutes < 60 * 24:
        return f"约 {minutes / 60:.1f} 小时"
    else:
        return f"约 {minutes / 60 / 24:.1f} 天"


def _dynamic_abs_threshold(meminfo: dict[str, int]) -> int:
    """根据系统总内存动态计算绝对增量阈值（KB）."""
    mem_total_kb = meminfo.get("MemTotal", 0)
    dynamic = int(mem_total_kb * LARGE_ABS_DELTA_PCT)
    return max(LARGE_ABS_DELTA_KB_DEFAULT, dynamic)


# ── 进程模式解析 ──────────────────────────────────────────────────────────────

def parse_process_samples(raw_dir: Path) -> list[dict]:
    """读取 sample_<N>.json 文件，按时间戳排序返回（过滤错误条目）."""
    samples = []
    for p in sorted(raw_dir.glob("sample_*.json")):
        data = _read_json(p)
        if data and "error" not in data and "ts" in data and data.get("vm_rss_kb", 0) > 0:
            samples.append(data)
    samples.sort(key=lambda x: x["ts"])
    return samples


def analyze_growth_trend(rss_series: list[int]) -> str:
    """
    分析增长趋势（加速 / 减速 / 线性 / 波动）.

    通过二阶差分（加速度）判断增长是否在加速.
    """
    if len(rss_series) < 3:
        return "insufficient_samples"

    first_diffs = [rss_series[i + 1] - rss_series[i] for i in range(len(rss_series) - 1)]
    # 过滤极值防止单次波动误判
    if len(first_diffs) >= 4:
        first_diffs = sorted(first_diffs)[1:-1]  # 去掉最大和最小

    second_diffs = [first_diffs[i + 1] - first_diffs[i] for i in range(len(first_diffs) - 1)]
    if not second_diffs:
        return "linear"

    avg_accel = sum(second_diffs) / len(second_diffs)
    # 用首次差分的标准差作为噪声基准
    mean_diff = sum(abs(d) for d in first_diffs) / len(first_diffs) if first_diffs else 1
    noise_threshold = mean_diff * 0.3

    if avg_accel > noise_threshold:
        return "accelerating"   # 增长加速（泄漏在恶化）
    elif avg_accel < -noise_threshold:
        return "decelerating"   # 增长减速（可能趋于稳定）
    else:
        return "linear"         # 匀速增长


def calc_process_growth(samples: list[dict]) -> dict:
    """计算进程 RSS/PSS 增长速率及趋势."""
    if len(samples) < 2:
        s0 = samples[0] if samples else {}
        return {
            "rss_start_kb": s0.get("vm_rss_kb", 0),
            "rss_end_kb": s0.get("vm_rss_kb", 0),
            "rss_delta_kb": 0,
            "pss_start_kb": s0.get("pss_kb", 0),
            "pss_end_kb": s0.get("pss_kb", 0),
            "pss_delta_kb": 0,
            "elapsed_sec": 0,
            "growth_rate_kb_per_min": 0.0,
            "growth_pct_per_min": 0.0,
            "is_monotonic": False,
            "trend": "insufficient_samples",
        }

    first = samples[0]
    last = samples[-1]

    # 时间戳合法性校验
    elapsed_sec = last["ts"] - first["ts"]
    if elapsed_sec <= 0:
        elapsed_sec = 1
    elapsed_min = max(elapsed_sec / 60.0, 1 / 60.0)

    rss_start = first["vm_rss_kb"]
    rss_end = last["vm_rss_kb"]
    rss_delta = rss_end - rss_start

    pss_start = first.get("pss_kb") or 0
    pss_end = last.get("pss_kb") or 0
    pss_delta = pss_end - pss_start

    growth_rate = rss_delta / elapsed_min
    growth_pct = (growth_rate / rss_start * 100) if rss_start > 0 else 0.0

    # 四舍五入后用于判定，避免边界精度漂移
    growth_rate_rounded = round(growth_rate, 1)
    growth_pct_rounded = round(growth_pct, 2)

    rss_series = [s["vm_rss_kb"] for s in samples]
    is_monotonic = all(rss_series[i] <= rss_series[i + 1] for i in range(len(rss_series) - 1))
    trend = analyze_growth_trend(rss_series)

    return {
        "rss_start_kb": rss_start,
        "rss_end_kb": rss_end,
        "rss_delta_kb": rss_delta,
        "pss_start_kb": pss_start,
        "pss_end_kb": pss_end,
        "pss_delta_kb": pss_delta,
        "elapsed_sec": elapsed_sec,
        "growth_rate_kb_per_min": growth_rate_rounded,
        "growth_pct_per_min": growth_pct_rounded,
        "is_monotonic": is_monotonic,
        "trend": trend,
        "rss_series_kb": rss_series,
    }


# ── 全局模式解析 ──────────────────────────────────────────────────────────────

def parse_global_samples(raw_dir: Path, top_n: int) -> tuple[list[dict], dict]:
    """
    读取 global_sample_<N>.json，计算每个进程的 RSS 增量.

    返回:
        (top_processes, extra_info)
        top_processes: 增量 Top N 进程列表
        extra_info: {
            "new_procs": [...],    新出现的进程（首帧没有）
            "gone_procs": [...],   消失的进程（末帧没有）
            "multi_leak_count": N, 增量显著的进程数量
        }
    """
    snapshots = []
    for p in sorted(raw_dir.glob("global_sample_*.json")):
        data = _read_json(p)
        if data and "processes" in data:
            snapshots.append(data)
    snapshots.sort(key=lambda x: x.get("ts", 0))

    extra_info: dict = {"new_procs": [], "gone_procs": [], "multi_leak_count": 0}

    if len(snapshots) < 2:
        if snapshots:
            procs = sorted(snapshots[-1]["processes"], key=lambda x: x["rss_kb"], reverse=True)
            result = [
                {
                    "pid": p["pid"],
                    "name": p["name"],
                    "rss_start_kb": p["rss_kb"],
                    "rss_end_kb": p["rss_kb"],
                    "delta_kb": 0,
                    "growth_basis": "single_snapshot_only",
                }
                for p in procs[:top_n]
            ]
            return result, extra_info
        return [], extra_info

    first_snap = {p["pid"]: p for p in snapshots[0]["processes"]}
    last_snap = {p["pid"]: p for p in snapshots[-1]["processes"]}

    # 新出现的进程（首帧无、末帧有）
    extra_info["new_procs"] = [
        {"pid": p["pid"], "name": p["name"], "rss_kb": p["rss_kb"]}
        for pid, p in last_snap.items() if pid not in first_snap
    ][:5]

    # 消失的进程（首帧有、末帧无）
    extra_info["gone_procs"] = [
        {"pid": p["pid"], "name": p["name"], "rss_kb": p["rss_kb"]}
        for pid, p in first_snap.items() if pid not in last_snap
    ][:5]

    results = []
    for pid, last_proc in last_snap.items():
        if pid in first_snap:
            delta = last_proc["rss_kb"] - first_snap[pid]["rss_kb"]
            results.append({
                "pid": pid,
                "name": last_proc["name"],
                "rss_start_kb": first_snap[pid]["rss_kb"],
                "rss_end_kb": last_proc["rss_kb"],
                "delta_kb": delta,
            })

    results.sort(key=lambda x: x["delta_kb"], reverse=True)

    # 统计显著增长的进程数（delta > 50MB）
    extra_info["multi_leak_count"] = sum(1 for r in results if r["delta_kb"] > 50 * 1024)

    return results[:top_n], extra_info


# ── 泄漏判定 ─────────────────────────────────────────────────────────────────

def determine_verdict(
    growth_pct_per_min: float,
    rss_delta_kb: int,
    elapsed_sec: int,
    sample_count: int,
    is_monotonic: bool,
    large_abs_threshold_kb: int = LARGE_ABS_DELTA_KB_DEFAULT,
) -> str:
    """
    根据增长速率、单调性、绝对增量综合判定泄漏结论.

    使用已四舍五入的 growth_pct_per_min 进行阈值比较，避免浮点边界问题.
    """
    if sample_count < 2 or elapsed_sec < MIN_MONITORING_SEC:
        return "insufficient_data"

    # 初步判定（使用已四舍五入的值）
    if growth_pct_per_min > LEAK_CONFIRMED_THRESHOLD:
        verdict = "leak_confirmed"
    elif growth_pct_per_min > LEAK_SUSPECTED_THRESHOLD:
        verdict = "leak_suspected"
    else:
        # 速率低但绝对增量显著且单调 → 疑似缓慢泄漏
        if rss_delta_kb > large_abs_threshold_kb and is_monotonic:
            verdict = "leak_suspected"
        else:
            verdict = "normal"

    # 单调性加成：单调递增 + 疑似 → 确认；单调递增 + 正常且有增量 → 疑似
    if is_monotonic and verdict == "leak_suspected":
        verdict = "leak_confirmed"
    elif is_monotonic and verdict == "normal" and rss_delta_kb > 0:
        verdict = "leak_suspected"

    return verdict


# ── OOM 预测 ─────────────────────────────────────────────────────────────────

def predict_oom(meminfo: dict[str, int], growth_rate_kb_per_min: float) -> dict:
    """
    预测 OOM 到来时间.

    策略:
    - 基于 MemAvailable 线性外推（主预测）
    - 若存在 Swap，附加说明实际时间更长
    - 声明线性外推的局限性
    """
    available_kb = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
    swap_free_kb = meminfo.get("SwapFree", 0)

    if growth_rate_kb_per_min <= 0 or available_kb <= 0:
        return {
            "available_mem_kb": available_kb,
            "swap_free_kb": swap_free_kb,
            "eta_minutes": None,
            "eta_human": "内存未增长，无 OOM 风险",
            "note": "",
        }

    eta_minutes = available_kb / growth_rate_kb_per_min

    notes = []
    if swap_free_kb > 0:
        swap_eta = swap_free_kb / growth_rate_kb_per_min
        notes.append(f"含 Swap({swap_free_kb // 1024}MB 可用) 实际约 {_eta_human(eta_minutes + swap_eta)}")
    notes.append("线性外推，实际受内核回收、业务波动影响，仅供参考")

    return {
        "available_mem_kb": available_kb,
        "swap_free_kb": swap_free_kb,
        "eta_minutes": round(eta_minutes, 1),
        "eta_human": _eta_human(eta_minutes),
        "note": "；".join(notes),
    }


# ── slab/内核泄漏检测 ─────────────────────────────────────────────────────────

def check_slab(meminfo: dict[str, int]) -> Optional[str]:
    """检查内核 slab 是否存在不可回收内存异常."""
    sunreclaim_kb = meminfo.get("SUnreclaim", 0)
    if sunreclaim_kb > SUNRECLAIM_THRESHOLD_MB * 1024:
        return (
            f"内核不可回收 slab 内存过高: {sunreclaim_kb // 1024}MB"
            f"（> {SUNRECLAIM_THRESHOLD_MB}MB），可能存在内核对象泄漏，建议检查 /proc/slabinfo"
        )
    return None


# ── eBPF 调用栈摘要 ───────────────────────────────────────────────────────────

def parse_ebpf_stacks(raw_dir: Path) -> Optional[str]:
    """提取 memleak_stack.log 的摘要（前 30 行）."""
    stack_file = raw_dir / "memleak_stack.log"
    if not stack_file.exists() or stack_file.stat().st_size < 50:
        return None
    lines = stack_file.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        return None
    summary_lines = lines[:30]
    if len(lines) > 30:
        summary_lines.append(f"... (共 {len(lines)} 行, 完整输出见 raw/memleak_stack.log)")
    return "\n".join(summary_lines)


# ── 辅助函数：配置与内存信息加载 ─────────────────────────────────────────────

def load_config_and_meminfo(raw_dir: Path) -> tuple:
    """读取运行配置及最后一次 meminfo，并计算动态绝对增量阈值。

    Returns:
        (config, mode, target_pid, process_name, monitor_interval,
         last_meminfo, large_abs_threshold)
    """
    config = _read_json(raw_dir / "config.json") or {}
    mode = config.get("mode", "global")
    target_pid = config.get("target_pid", "")
    process_name = config.get("process_name", "")
    monitor_interval = int(config.get("monitor_interval", 10))

    last_meminfo: dict[str, int] = {}
    meminfo_files = sorted(raw_dir.glob("meminfo_*.log"))
    if meminfo_files:
        last_meminfo = _parse_meminfo(meminfo_files[-1])
    if not last_meminfo:
        last_meminfo = _parse_meminfo(raw_dir / "meminfo_baseline.log")

    large_abs_threshold = _dynamic_abs_threshold(last_meminfo)
    return config, mode, target_pid, process_name, monitor_interval, last_meminfo, large_abs_threshold


# ── 辅助函数：进程模式 key_findings 生成 ────────────────────────────────────

def build_process_findings(
    name: str,
    pid,
    growth: dict,
    verdict: str,
    sample_count: int,
    fd_count: int,
) -> list:
    """根据进程模式的增长数据和判定结论，生成 key_findings 列表。"""
    findings: list[str] = []
    elapsed_sec = growth.get("elapsed_sec", 0)
    elapsed_min = elapsed_sec / 60 if elapsed_sec > 0 else 1
    rss_delta_mb = growth["rss_delta_kb"] / 1024
    verdict_cn = VERDICT_CN.get(verdict, verdict)

    if verdict in ("leak_confirmed", "leak_suspected"):
        findings.append(
            f"进程 {name} (PID {pid}) RSS 增长 {rss_delta_mb:.1f}MB"
            f"/{elapsed_min:.0f}min，速率 {growth['growth_pct_per_min']}%/min"
            f"，判定: {verdict_cn}"
        )
    elif verdict not in ("process_disappeared",):
        findings.append(
            f"进程 {name} (PID {pid}) RSS 变化 {rss_delta_mb:+.1f}MB"
            f"/{elapsed_min:.0f}min，判定: {verdict_cn}"
        )

    trend = growth.get("trend", "")
    if trend == "accelerating" and verdict in ("leak_confirmed", "leak_suspected"):
        findings.append("内存增长正在加速，泄漏情况在恶化，建议尽快处置")
    elif trend == "decelerating" and verdict in ("leak_confirmed", "leak_suspected"):
        findings.append("内存增长有减速趋势，可能是业务峰值已过或缓存逐渐稳定")

    if growth.get("is_monotonic") and verdict in ("leak_confirmed", "leak_suspected"):
        findings.append(f"RSS {sample_count} 次采样持续单调递增，无回落，泄漏特征明显")

    if fd_count > FD_LEAK_THRESHOLD:
        findings.append(
            f"文件描述符数量偏高: {fd_count}（> {FD_LEAK_THRESHOLD}），可能存在 fd 泄漏，"
            f"建议执行 lsof -p {pid} | head -30 排查"
        )

    return findings


# ── 辅助函数：进程模式整体分析 ───────────────────────────────────────────────

def build_process_mode_result(
    raw_dir: Path,
    target_pid,
    process_name: str,
    large_abs_threshold: int,
) -> tuple:
    """进程模式下：采集样本、判定泄漏、生成 findings。

    Returns:
        (verdict, growth, top_processes, fd_count, target_info, key_findings)
    """
    key_findings: list[str] = []
    growth: dict = {}
    verdict = "insufficient_data"
    top_processes: list[dict] = []
    fd_count = 0
    target_info: dict = {"mode": "process"}

    samples = parse_process_samples(raw_dir)
    sample_count = len(samples)

    # 检测进程中途退出（有 sample 文件但含 error 字段）
    all_sample_files = list(raw_dir.glob("sample_*.json"))
    error_samples = [
        data for p in all_sample_files
        for data in [_read_json(p)]
        if data and "error" in data
    ]
    process_disappeared = len(error_samples) > 0 and sample_count > 0

    if samples:
        pid = samples[0].get("pid", target_pid)
        name = samples[0].get("name", process_name or str(pid))
        target_info["pid"] = pid
        target_info["process_name"] = name
        fd_count = samples[-1].get("fd_count", 0)

        growth = calc_process_growth(samples)
        elapsed_sec = growth.get("elapsed_sec", 0)

        if process_disappeared:
            verdict = "process_disappeared"
            key_findings.append(
                f"进程 {name} (PID {pid}) 在监控期间退出，共采集 {sample_count} 次数据"
            )
            if sample_count >= 2:
                pre_verdict = determine_verdict(
                    growth_pct_per_min=growth["growth_pct_per_min"],
                    rss_delta_kb=growth["rss_delta_kb"],
                    elapsed_sec=elapsed_sec,
                    sample_count=sample_count,
                    is_monotonic=growth.get("is_monotonic", False),
                    large_abs_threshold_kb=large_abs_threshold,
                )
                key_findings.append(
                    f"退出前趋势: {VERDICT_CN.get(pre_verdict, pre_verdict)}"
                    f"（{sample_count} 次采样，增速 {growth['growth_pct_per_min']}%/min）"
                )
        else:
            verdict = determine_verdict(
                growth_pct_per_min=growth["growth_pct_per_min"],
                rss_delta_kb=growth["rss_delta_kb"],
                elapsed_sec=elapsed_sec,
                sample_count=sample_count,
                is_monotonic=growth.get("is_monotonic", False),
                large_abs_threshold_kb=large_abs_threshold,
            )

        key_findings.extend(
            build_process_findings(name, pid, growth, verdict, sample_count, fd_count)
        )

        top_processes = [{
            "pid": pid,
            "name": name,
            "rss_start_kb": growth["rss_start_kb"],
            "rss_end_kb": growth["rss_end_kb"],
            "delta_kb": growth["rss_delta_kb"],
            "trend": growth.get("trend", ""),
        }]
    else:
        target_info["pid"] = target_pid
        target_info["process_name"] = process_name
        verdict = "process_disappeared"
        key_findings.append(f"未能采集到进程有效数据（PID={target_pid} 可能已退出或权限不足）")

    return verdict, growth, top_processes, fd_count, target_info, key_findings


# ── 辅助函数：全局扫描模式整体分析 ──────────────────────────────────────────

def build_global_mode_result(
    raw_dir: Path,
    top_n: int,
    monitor_interval: int,
    large_abs_threshold: int,
) -> tuple:
    """全局扫描模式下：汇总各进程增长情况、判定泄漏、生成 findings。

    Returns:
        (verdict, growth, top_processes, target_info, key_findings)
    """
    key_findings: list[str] = []
    growth: dict = {}
    verdict = "insufficient_data"
    target_info: dict = {"mode": "global", "pid": None, "process_name": None}

    top_processes, extra_info = parse_global_samples(raw_dir, top_n)

    n_snapshots = len(list(raw_dir.glob("global_sample_*.json")))
    elapsed_global = monitor_interval * max(n_snapshots - 1, 1)
    elapsed_min_global = elapsed_global / 60 if elapsed_global > 0 else 1

    growing = [
        p for p in top_processes
        if p.get("delta_kb", 0) > 0
        and p.get("growth_basis") != "single_snapshot_only"
    ]
    multi_leak = extra_info.get("multi_leak_count", 0)

    if growing:
        top = growing[0]
        delta_mb = top["delta_kb"] / 1024
        key_findings.append(
            f"内存增长最快进程: {top['name']} (PID {top['pid']})"
            f"，增长 {delta_mb:.1f}MB/{elapsed_min_global:.0f}min"
        )

        rate = top["delta_kb"] / elapsed_min_global if elapsed_min_global > 0 else 0
        rate_pct = (rate / top["rss_start_kb"] * 100) if top["rss_start_kb"] > 0 else 0
        rate_pct_rounded = round(rate_pct, 2)

        verdict = determine_verdict(
            growth_pct_per_min=rate_pct_rounded,
            rss_delta_kb=top["delta_kb"],
            elapsed_sec=elapsed_global,
            sample_count=n_snapshots,
            is_monotonic=False,
            large_abs_threshold_kb=large_abs_threshold,
        )
        growth = {
            "rss_start_kb": top["rss_start_kb"],
            "rss_end_kb": top["rss_end_kb"],
            "rss_delta_kb": top["delta_kb"],
            "growth_rate_kb_per_min": round(rate, 1),
            "growth_pct_per_min": rate_pct_rounded,
        }

        if multi_leak >= 2:
            key_findings.append(
                f"检测到 {multi_leak} 个进程 RSS 增量 > 50MB，可能是共享库泄漏或批量服务异常，"
                f"建议改用单进程模式逐一确认"
            )
    else:
        verdict = "normal"
        key_findings.append("监控期间所有进程 RSS 无明显增长")

    new_procs = extra_info.get("new_procs", [])
    gone_procs = extra_info.get("gone_procs", [])
    if new_procs:
        names = ", ".join(f"{p['name']}({p['pid']})" for p in new_procs[:3])
        key_findings.append(f"监控期间出现新进程: {names}")
    if gone_procs:
        names = ", ".join(f"{p['name']}({p['pid']})" for p in gone_procs[:3])
        key_findings.append(f"监控期间消失进程: {names}（可能影响全局内存统计）")

    return verdict, growth, top_processes, target_info, key_findings


# ── 辅助函数：OOM 预测与 slab 告警 ───────────────────────────────────────────

def build_oom_findings(last_meminfo: dict, growth: dict) -> tuple:
    """执行 OOM 预测和 slab 检查，返回 oom_pred 及告警 findings。

    Returns:
        (oom_pred, extra_findings)
    """
    oom_pred: dict = {
        "available_mem_kb": 0, "swap_free_kb": 0,
        "eta_minutes": None, "eta_human": "无法预测", "note": ""
    }
    extra_findings: list[str] = []

    if last_meminfo:
        rate_for_oom = growth.get("growth_rate_kb_per_min", 0.0)
        oom_pred = predict_oom(last_meminfo, rate_for_oom)
        if oom_pred["eta_minutes"] is not None:
            if oom_pred["eta_minutes"] < 60:
                extra_findings.append(
                    f"紧急警告: 按当前增速预计 {oom_pred['eta_human']} 后触发 OOM！"
                )
            elif oom_pred["eta_minutes"] < 60 * 24:
                extra_findings.append(f"按当前增速，预计 {oom_pred['eta_human']} 后可用内存耗尽")

    slab_finding = check_slab(last_meminfo)
    if slab_finding:
        extra_findings.append(slab_finding)

    return oom_pred, extra_findings


# ── 主函数 ───────────────────────────────────────────────────────────────────

def build_summary(log_dir: Path, task_id: str, top_n: int) -> dict:
    raw_dir = log_dir / "raw"

    config, mode, target_pid, process_name, monitor_interval, \
        last_meminfo, large_abs_threshold = load_config_and_meminfo(raw_dir)

    if mode == "process":
        verdict, growth, top_processes, fd_count, target_info, key_findings = \
            build_process_mode_result(raw_dir, target_pid, process_name, large_abs_threshold)
    else:
        verdict, growth, top_processes, target_info, key_findings = \
            build_global_mode_result(raw_dir, top_n, monitor_interval, large_abs_threshold)
        fd_count = 0

    oom_pred, oom_findings = build_oom_findings(last_meminfo, growth)
    key_findings.extend(oom_findings)

    ebpf_stacks = parse_ebpf_stacks(raw_dir)
    monitor_duration_sec = int(config.get("monitor_count", 1)) * int(config.get("monitor_interval", 10))

    summary = {
        "task_id": task_id,
        "collected_at": datetime.now().isoformat(),
        "monitor_duration_sec": monitor_duration_sec,
        "target": target_info,
        "leak_verdict": verdict,
        "growth": growth,
        "oom_prediction": oom_pred,
        "fd_count": fd_count,
        "top_processes": top_processes,
        "ebpf_available": ebpf_stacks is not None,
        "ebpf_stacks": ebpf_stacks,
        "key_findings": key_findings,
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="解析内存泄漏采集数据, 生成 summary.json")
    parser.add_argument("--log-dir", required=True, help="日志目录（含 raw/ 子目录）")
    parser.add_argument("--task-id", default="unknown", help="任务 ID")
    parser.add_argument("--top-n", type=int, default=5, help="全局扫描显示 Top N 进程")
    parser.add_argument("--elapsed-sec", type=int, default=0, help="实际采样窗口秒数（由采集脚本传入）")
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    summary = build_summary(log_dir, args.task_id, args.top_n)

    # 若采集脚本传入了精确 elapsed，覆盖 config 计算的值
    if args.elapsed_sec > 0:
        summary["monitor_duration_sec"] = args.elapsed_sec

    summary_path = log_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[parse_memory_leak] summary.json 已写入: {summary_path}")

    verdict_cn = VERDICT_CN.get(summary["leak_verdict"], summary["leak_verdict"])
    print(f"[parse_memory_leak] 诊断结论: {verdict_cn}")
    for finding in summary.get("key_findings", []):
        print(f"[parse_memory_leak] >> {finding}")


if __name__ == "__main__":
    main()
