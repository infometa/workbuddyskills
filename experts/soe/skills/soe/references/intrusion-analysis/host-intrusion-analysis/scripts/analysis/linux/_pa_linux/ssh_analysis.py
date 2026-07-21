"""SSH 暴力破解交叉验证分析。

从 AuthLogs 的 SSH 子章节提取失败/成功登录记录，
按 IP 聚合并交叉验证暴力破解 → 成功渗透的攻击链。

SA-R003: 新增 SSH 协议异常检测（kex_exchange_identification / Bad protocol version），
捕获通过 SSH 端口发送 HTTP 请求等非 SSH 协议流量（路径遍历探测信号）。
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta

from _common.models import SectionIndex
from _common.parsers import classify_ip

from .condenser import get_sub_lines
from .constants import (
    RE_SSH_BAD_PROTOCOL,
    RE_SSH_FAIL_DISCONNECT,
    RE_SSH_FAIL_PASSWORD,
    RE_SSH_KEX_ERROR,
    RE_SSH_SUCCESS,
    _RE_FROM_IP,
)


def parse_ssh_failures(lines: list[str], sections: list[SectionIndex]) -> list[dict]:
    """从 AuthLogs > SSH > ssh_login_failed 提取失败登录。

    同时匹配两种 syslog 格式：
    - Disconnecting ... user <user> <ip> port ...
    - Failed password for [invalid user] <user> from <ip> port ...
    """
    sub_lines = get_sub_lines(lines, sections, "ssh_login_failed")
    return _parse_ssh_failures_raw(sub_lines)


def _parse_ssh_failures_raw(auth_lines: list[str]) -> list[dict]:
    """从原始 auth log 行列表直接提取 SSH 失败登录。

    不依赖 sections 结构，供 linux_log_folder 直接调用。
    同时匹配两种 syslog 格式：
    - Disconnecting ... user <user> <ip> port ...
    - Failed password for [invalid user] <user> from <ip> port ...
    """
    results = []
    for line in auth_lines:
        m = RE_SSH_FAIL_DISCONNECT.search(line)
        if not m:
            m = RE_SSH_FAIL_PASSWORD.search(line)
        if m:
            results.append({
                "time": m.group(1),
                "user": m.group(2),
                "ip": m.group(3),
            })
    return results


def parse_ssh_successes(lines: list[str], sections: list[SectionIndex]) -> list[dict]:
    """从 AuthLogs > SSH > ssh_login_success 提取成功登录。"""
    sub_lines = get_sub_lines(lines, sections, "ssh_login_success")
    return _parse_ssh_successes_raw(sub_lines)


def _parse_ssh_successes_raw(auth_lines: list[str]) -> list[dict]:
    """从原始 auth log 行列表直接提取 SSH 成功登录。

    不依赖 sections 结构，供 linux_log_folder 直接调用。
    """
    results = []
    for line in auth_lines:
        m = RE_SSH_SUCCESS.search(line)
        if m:
            results.append({
                "time": m.group(1),
                "method": m.group(2),
                "user": m.group(3),
                "ip": m.group(4),
                "port": m.group(5),
            })
    return results


def parse_syslog_time(time_str: str) -> datetime | None:
    """解析 syslog 格式时间（如 "Mar 24 09:52:47"）为 datetime。

    syslog 不含年份，默认使用当前年。
    跨年修正：如果解析后的时间超过当前时间 1 天以上，说明日志来自上一年
    （例如 1 月分析 12 月的日志），自动回退到上一年。
    返回 None 表示解析失败。
    """
    try:
        dt = datetime.strptime(time_str, "%b %d %H:%M:%S")
        now = datetime.now()
        dt = dt.replace(year=now.year)
        # 跨年修正：日志时间超过当前时间 1 天以上，回退到上一年
        # 容忍 1 天的时钟漂移/时区差异
        if dt > now + timedelta(days=1):
            dt = dt.replace(year=now.year - 1)
        return dt
    except (ValueError, TypeError):
        return None


def analyze_ssh_brute_force(
    failures: list[dict], successes: list[dict]
) -> dict:
    """SSH 暴力破解交叉验证。"""
    if not failures:
        return {
            "total_attack_ips": 0,
            "total_attempts": 0,
            "attack_ips": [],
        }

    # 按 IP 聚合失败尝试
    ip_stats: dict[str, dict] = defaultdict(lambda: {
        "attempts": 0,
        "users": set(),
        "first_dt": None,   # datetime 对象，用于正确比较
        "last_dt": None,
        "first": None,       # 原始字符串，用于输出
        "last": None,
    })

    for f in failures:
        ip = f["ip"]
        stats = ip_stats[ip]
        stats["attempts"] += 1
        stats["users"].add(f["user"])
        t = f["time"]
        dt = parse_syslog_time(t)
        if dt:
            if stats["first_dt"] is None or dt < stats["first_dt"]:
                stats["first_dt"] = dt
                stats["first"] = t
            if stats["last_dt"] is None or dt > stats["last_dt"]:
                stats["last_dt"] = dt
                stats["last"] = t
        else:
            # 解析失败时回退到字符串赋值（保证不丢数据）
            if stats["first"] is None:
                stats["first"] = t
            stats["last"] = t

    # 成功登录 IP 索引
    success_by_ip: dict[str, list[dict]] = defaultdict(list)
    for s in successes:
        success_by_ip[s["ip"]].append(s)

    # target_users 截断上限：最多展示前 10 个，超出的记录总数而非丢失
    # 避免字典穷举 IP（尝试了几百个用户名）导致 Markdown 表格单行过宽
    _MAX_TARGET_USERS = 10

    attack_ips = []
    total_attempts = 0
    for ip, stats in sorted(ip_stats.items(), key=lambda x: -x[1]["attempts"]):
        total_attempts += stats["attempts"]
        found_logins = success_by_ip.get(ip, [])
        all_users = sorted(stats["users"])
        if len(all_users) > _MAX_TARGET_USERS:
            users_str = ", ".join(all_users[:_MAX_TARGET_USERS]) + f" (+{len(all_users) - _MAX_TARGET_USERS} more)"
        else:
            users_str = ", ".join(all_users)
        attack_ips.append({
            "ip": ip,
            "ip_type": classify_ip(ip),
            "attempts": stats["attempts"],
            "first_attempt": stats["first"],
            "last_attempt": stats["last"],
            "target_users": users_str,
            "found_in_success": len(found_logins) > 0,
            "success_count": len(found_logins),
        })

    return {
        "total_attack_ips": len(attack_ips),
        "total_attempts": total_attempts,
        "attack_ips": attack_ips,
    }


# ---------------------------------------------------------------------------
# SA-R003: SSH 协议异常检测
# ---------------------------------------------------------------------------
#
# 攻击场景：
#   攻击者对 SSH 端口（通常 22）发送 HTTP 请求进行路径遍历探测，
#   如 GET /..%2F..%2Fetc%2Fpasswd HTTP/1.1
#   sshd 无法完成密钥交换，记录以下类型的错误日志：
#
#   kex_exchange_identification: banner line contains invalid characters
#   kex_exchange_identification: ... from <IP> port <port>
#   Bad protocol version identification 'GET /..%2F..' from <IP> port <port>
#
# 这些日志不属于 SSH 认证失败（不含用户名/密码），
# 传统暴力破解检测器不会匹配，需要独立检测。
# ---------------------------------------------------------------------------


def parse_ssh_protocol_anomalies(
    lines: list[str], sections: list[SectionIndex],
) -> list[dict]:
    """SA-R003: 从 AuthLogs SECTION 扫描 SSH 协议异常日志。

    检测两类异常：
    1. kex_exchange_identification 错误（HTTP 探测/非 SSH 协议连接）
    2. Bad protocol version identification（明确的非 SSH 协议版本字符串）

    优先扫描 AuthLogs SECTION 范围（这类日志通常出现在 auth.log/secure 中）。
    如果 AuthLogs SECTION 不存在，则回退到全文扫描。

    返回 [{"time": str, "type": str, "ip": str|None, "detail": str}, ...]
    """
    # 确定扫描范围：优先 AuthLogs SECTION，回退全文
    scan_lines = lines  # 默认全文
    for sec in sections:
        if sec.name == "AuthLogs" and sec.section_type == "SECTION":
            scan_lines = lines[sec.start_line:sec.end_line]
            break

    return _parse_ssh_protocol_anomalies_raw(scan_lines)


def _parse_ssh_protocol_anomalies_raw(ssh_lines: list[str]) -> list[dict]:
    """SA-R003: 从原始 SSH auth log 行列表直接扫描协议异常。

    不依赖 sections 结构，供 linux_log_folder 直接调用。
    检测两类异常：
    1. kex_exchange_identification 错误
    2. Bad protocol version identification

    返回 [{"time": str, "type": str, "ip": str|None, "detail": str}, ...]
    """
    results: list[dict] = []
    seen: set[str] = set()  # 去重：(time, ip, type)

    for line in ssh_lines:
        if "sshd" not in line:
            continue

        # --- 类型 1: kex_exchange_identification ---
        m = RE_SSH_KEX_ERROR.search(line)
        if m:
            time_str = m.group(1)
            detail = m.group(2).strip()
            # 尝试从消息体提取源 IP
            ip_m = _RE_FROM_IP.search(detail)
            ip = ip_m.group(1) if ip_m else None

            dedup_key = (time_str, ip or "", "kex_error")
            if dedup_key not in seen:
                seen.add(dedup_key)
                results.append({
                    "time": time_str,
                    "type": "kex_exchange_identification",
                    "ip": ip,
                    "detail": detail[:150],
                })
            continue

        # --- 类型 2: Bad protocol version identification ---
        m = RE_SSH_BAD_PROTOCOL.search(line)
        if m:
            time_str = m.group(1)
            bad_version = m.group(2).strip()
            ip = m.group(3)
            port = m.group(4)

            dedup_key = (time_str, ip, "bad_protocol")
            if dedup_key not in seen:
                seen.add(dedup_key)
                results.append({
                    "time": time_str,
                    "type": "bad_protocol_version",
                    "ip": ip,
                    "detail": f"'{bad_version}' port {port}",
                })

    return results


def analyze_ssh_protocol_anomalies(
    anomalies: list[dict],
) -> dict:
    """SA-R003: 按 IP 聚合 SSH 协议异常，识别探测行为。

    返回:
    {
        "total_events": int,
        "total_ips": int,
        "unknown_ip_events": int,    # 无法提取 IP 的事件数
        "ip_stats": [
            {
                "ip": str,
                "ip_type": str,
                "count": int,
                "types": list[str],
                "first_seen": str,
                "last_seen": str,
                "sample_details": list[str],  # 最多 3 条示例
            },
            ...
        ]
    }
    """
    if not anomalies:
        return {
            "total_events": 0,
            "total_ips": 0,
            "unknown_ip_events": 0,
            "ip_stats": [],
        }

    ip_data: dict[str, dict] = defaultdict(lambda: {
        "count": 0,
        "types": set(),
        "first_seen": None,
        "last_seen": None,
        "sample_details": [],
    })
    unknown_ip_count = 0

    for evt in anomalies:
        ip = evt["ip"]
        if ip is None:
            unknown_ip_count += 1
            ip = "(未知)"

        stats = ip_data[ip]
        stats["count"] += 1
        stats["types"].add(evt["type"])
        time_str = evt["time"]
        if stats["first_seen"] is None:
            stats["first_seen"] = time_str
        stats["last_seen"] = time_str
        if len(stats["sample_details"]) < 3:
            stats["sample_details"].append(evt["detail"])

    ip_stats = []
    for ip, stats in sorted(ip_data.items(), key=lambda x: -x[1]["count"]):
        ip_stats.append({
            "ip": ip,
            "ip_type": classify_ip(ip) if ip != "(未知)" else "unknown",
            "count": stats["count"],
            "types": sorted(stats["types"]),
            "first_seen": stats["first_seen"],
            "last_seen": stats["last_seen"],
            "sample_details": stats["sample_details"],
        })

    return {
        "total_events": len(anomalies),
        "total_ips": len([s for s in ip_stats if s["ip"] != "(未知)"]),
        "unknown_ip_events": unknown_ip_count,
        "ip_stats": ip_stats,
    }
