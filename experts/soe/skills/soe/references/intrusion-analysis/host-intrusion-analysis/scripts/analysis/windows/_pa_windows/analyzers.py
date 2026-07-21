"""Phase 3: 5 个交叉分析函数 + USN 辅助函数。"""

import ipaddress
from collections import defaultdict
from datetime import datetime
from typing import Optional

from .constants import (
    DEFENDER_PATH_COMPILED,
    PS_CONTENT_PATTERNS,
    PS_PATH_EXTRA_WHITELIST,
    PS_PATH_WHITELIST,
    RANSOM_NOTE_COMPILED,
    RANSOMWARE_EXTENSIONS,
)
from .parsers import classify_ip, is_external_ip


# ---------------------------------------------------------------------------
# Module 1: Brute Force Cross Check
# ---------------------------------------------------------------------------


def analyze_brute_force(
    events_4625: list[dict], events_4624: list[dict]
) -> dict:
    """暴力破解 IP ↔ 成功登录交叉验证。

    提取 4625 中的攻击 IP，在 4624 中逐一检索，
    输出每个攻击 IP 是否出现在成功登录中及对应的登录详情。
    """
    result = {
        "total_attack_ips": 0,
        "total_attempts": 0,
        "attack_ips": [],
    }

    if not events_4625:
        return result

    # 建立 4624 的 IP → 登录记录索引
    login_by_ip: dict[str, list[dict]] = defaultdict(list)
    for rec in events_4624:
        ip = rec.get("IpAddress", "-")
        if ip and ip != "-":
            login_by_ip[ip].append(rec)

    result["total_attack_ips"] = len(events_4625)

    for attack in events_4625:
        ip = attack.get("IpAddress", "")
        attempts = int(attack.get("AttemptCount", "0"))
        result["total_attempts"] += attempts

        found_logins = login_by_ip.get(ip, [])
        ip_result = {
            "ip": ip,
            "attempts": attempts,
            "first_attempt": attack.get("FirstAttempt", ""),
            "last_attempt": attack.get("LastAttempt", ""),
            "target_usernames": attack.get("TargetUserNames", ""),
            "found_in_4624": len(found_logins) > 0,
            "login_count": len(found_logins),
            "login_details": [
                {
                    "time": login.get("TimeCreated", ""),
                    "user": login.get("TargetUserName", ""),
                    "logon_type": login.get("LogonType", ""),
                    "domain": login.get("TargetDomainName", ""),
                }
                for login in found_logins[:20]  # 最多 20 条避免过大
            ],
        }
        result["attack_ips"].append(ip_result)

    return result


# ---------------------------------------------------------------------------
# Module 2: Active Connection Cross Check
# ---------------------------------------------------------------------------


def analyze_active_connections(
    network_tcp: list[dict],
    events_4624: list[dict],
    events_4625: list[dict],
) -> dict:
    """活跃连接 ↔ 登录事件交叉验证。

    从 network_tcp 中提取所有外部 Established 连接，
    与 4624/4625 数据交叉比对。
    """
    result = {
        "total_connections": len(network_tcp),
        "external_established": [],
        "summary": {
            "total_external_established": 0,
            "linked_to_bruteforce": 0,
            "linked_to_success_login": 0,
            "no_login_association": 0,
        },
    }

    # 建立 4624 IP 集合
    login_ips = set()
    for rec in events_4624:
        ip = rec.get("IpAddress", "-")
        if ip and ip != "-":
            login_ips.add(ip)

    # 建立 4625 IP 集合
    bruteforce_ips = set()
    for rec in events_4625:
        ip = rec.get("IpAddress", "")
        if ip:
            bruteforce_ips.add(ip)

    # 扫描 network_tcp
    for conn in network_tcp:
        remote_ip = conn.get("RemoteAddress", "")
        state = conn.get("State", "")

        if state != "Established":
            continue

        if not is_external_ip(remote_ip):
            continue

        # 交叉比对
        in_bruteforce = remote_ip in bruteforce_ips
        in_success = remote_ip in login_ips

        # 威胁等级：暴力破解 IP 或「成功登录 + 活跃 3389 连接」均为 high
        rdp_port = str(conn.get("LocalPort", ""))
        if in_bruteforce or (in_success and rdp_port == "3389"):
            threat_level = "high"
        elif in_success:
            threat_level = "medium"
        else:
            threat_level = "low"

        conn_result = {
            "remote_ip": remote_ip,
            "remote_port": conn.get("RemotePort", ""),
            "local_port": conn.get("LocalPort", ""),
            "local_address": conn.get("LocalAddress", ""),
            "state": state,
            "process_id": conn.get("OwningProcess", ""),
            "creation_time": conn.get("CreationTime", ""),
            "in_4625_bruteforce": in_bruteforce,
            "in_4624_success_login": in_success,
            "threat_level": threat_level,
        }
        result["external_established"].append(conn_result)

    result["summary"]["total_external_established"] = len(
        result["external_established"]
    )
    result["summary"]["linked_to_bruteforce"] = sum(
        1 for c in result["external_established"] if c["in_4625_bruteforce"]
    )
    result["summary"]["linked_to_success_login"] = sum(
        1 for c in result["external_established"] if c["in_4624_success_login"]
    )
    result["summary"]["no_login_association"] = sum(
        1
        for c in result["external_established"]
        if not c["in_4625_bruteforce"] and not c["in_4624_success_login"]
    )

    return result


# ---------------------------------------------------------------------------
# Module 3: PowerShell 4104 Noise Filter (was Module 4)
# ---------------------------------------------------------------------------


def analyze_4104_filter(events_4104: list[dict]) -> dict:
    """PowerShell 4104 系统模块噪声过滤。

    按 Path 前缀白名单和 ScriptBlockText 特征过滤系统内置模块，
    输出过滤后的可疑脚本块列表及过滤统计。
    """
    result = {
        "total": len(events_4104),
        "filtered_system": 0,
        "remaining_suspicious": [],
        "filter_stats": {
            "by_path_whitelist": 0,
            "by_content_pattern": 0,
            "path_empty_kept": 0,
        },
    }

    for rec in events_4104:
        path = rec.get("Path", "").strip()
        script_text = rec.get("ScriptBlockText", "").strip()
        row_num = rec.get("#", "")
        time_created = rec.get("TimeCreated", "")

        # 分类判断
        filtered = False
        filter_reason = ""

        if not path:
            # Path 为空：先检查内容特征是否为系统模块
            for pattern_fn in PS_CONTENT_PATTERNS:
                if pattern_fn(script_text):
                    filtered = True
                    filter_reason = "content_pattern"
                    result["filter_stats"]["by_content_pattern"] += 1
                    break
            # 如果内容特征不匹配，标记为 path_empty 保留
            if not filtered:
                result["filter_stats"]["path_empty_kept"] += 1
        else:
            # 检查 Path 白名单（标准系统 PowerShell 目录）
            path_lower = path.lower()
            for prefix in PS_PATH_WHITELIST:
                if path_lower.startswith(prefix):
                    filtered = True
                    filter_reason = "path_whitelist"
                    result["filter_stats"]["by_path_whitelist"] += 1
                    break

            # 检查额外 Path 白名单（系统诊断等）
            if not filtered:
                for prefix in PS_PATH_EXTRA_WHITELIST:
                    if path_lower.startswith(prefix):
                        filtered = True
                        filter_reason = "path_extra_whitelist"
                        result["filter_stats"]["by_path_whitelist"] += 1
                        break

            # Path 不在白名单，再检查内容特征
            if not filtered:
                for pattern_fn in PS_CONTENT_PATTERNS:
                    if pattern_fn(script_text):
                        filtered = True
                        filter_reason = "content_pattern"
                        result["filter_stats"]["by_content_pattern"] += 1
                        break

        if filtered:
            result["filtered_system"] += 1
        else:
            # 截取 snippet（前 120 字符，大多数可疑命令在此范围内已可识别）
            snippet = script_text[:120] + ("..." if len(script_text) > 120 else "")
            result["remaining_suspicious"].append(
                {
                    "row_num": row_num,
                    "time": time_created,
                    "path": path if path else "(empty)",
                    "script_block_id": rec.get("ScriptBlockId", ""),
                    "snippet": snippet,
                }
            )

    # 可疑项限制上限 50 条，避免 JSON 体积过大
    total_suspicious = len(result["remaining_suspicious"])
    if total_suspicious > 50:
        result["remaining_suspicious"] = result["remaining_suspicious"][:50]
        result["remaining_suspicious_truncated"] = True
        result["remaining_suspicious_total"] = total_suspicious
    else:
        result["remaining_suspicious_truncated"] = False
        result["remaining_suspicious_total"] = total_suspicious

    # 从可疑项中筛选高风险项（含已知危险关键词）
    HIGH_RISK_KEYWORDS = [
        "invoke-expression", "iex ", "iex(", "-encodedcommand",
        "downloadstring", "downloadfile", "downloaddata",
        "net.webclient", "start-bitstransfer",
        "invoke-webrequest", "invoke-restmethod",
        "new-object system.net", "reflection.assembly",
        "convertto-securestring", "frombase64string",
        "invoke-mimikatz", "invoke-shellcode",
        "add-type -typedefinition", "add-type -assemblyname",
        "bypass", "-nop ", "-noni ", "-w hidden",
    ]
    high_risk = []
    for item in result["remaining_suspicious"]:
        snippet_lower = item.get("snippet", "").lower()
        if any(kw in snippet_lower for kw in HIGH_RISK_KEYWORDS):
            high_risk.append(item)
    result["high_risk_suspicious"] = high_risk

    return result


# ---------------------------------------------------------------------------
# Module 4: RDP Triple Evidence Cross Check
# ---------------------------------------------------------------------------


def analyze_rdp_cross_check(
    events_4624: list[dict],
    events_1149: list[dict],
    events_21_25: list[dict],
    network_tcp: list[dict],
) -> dict:
    """RDP 四证据交叉验证。

    将 4624 Type 10/7 登录、RDP 1149 连接、RDP 21/25 会话、
    network_tcp 3389 Established 连接四个数据源按 IP 对齐。
    """
    result = {"rdp_ips": []}

    # 收集所有 RDP 相关 IP
    rdp_ip_set: set[str] = set()
    evidence_by_ip: dict[str, dict] = defaultdict(
        lambda: {
            "4624_type10": [],
            "4624_type7": [],
            "1149": [],
            "21_25": [],
            "tcp_3389": [],
        }
    )

    # 4624 Type 10 (RemoteInteractive) 和 Type 7 (Unlock)
    for rec in events_4624:
        logon_type = rec.get("LogonType", "")
        ip = rec.get("IpAddress", "-")

        if logon_type == "10" and ip and ip != "-":
            rdp_ip_set.add(ip)
            evidence_by_ip[ip]["4624_type10"].append(
                {
                    "time": rec.get("TimeCreated", ""),
                    "user": rec.get("TargetUserName", ""),
                    "domain": rec.get("TargetDomainName", ""),
                }
            )
        elif logon_type == "7" and ip and ip != "-":
            rdp_ip_set.add(ip)
            evidence_by_ip[ip]["4624_type7"].append(
                {
                    "time": rec.get("TimeCreated", ""),
                    "user": rec.get("TargetUserName", ""),
                    "domain": rec.get("TargetDomainName", ""),
                }
            )

    # 1149 RDP 连接
    for rec in events_1149:
        # 1149 事件的 IP 可能在 Param1/Param2/Param3 字段中
        # 实际字段名取决于 PS1 输出
        ip = rec.get("Param1", "").strip()
        if not ip:
            # 尝试其他字段
            for key in ("Param2", "Param3", "IpAddress"):
                val = rec.get(key, "").strip()
                if val and _looks_like_ip(val):
                    ip = val
                    break

        if ip:
            rdp_ip_set.add(ip)
            evidence_by_ip[ip]["1149"].append(
                {
                    "time": rec.get("TimeCreated", ""),
                    "event_id": rec.get("EventID", ""),
                }
            )
        else:
            # IP 字段为空也记录
            evidence_by_ip["(unknown)"]["1149"].append(
                {
                    "time": rec.get("TimeCreated", ""),
                    "event_id": rec.get("EventID", ""),
                    "raw": rec,
                }
            )

    # 21/25 RDP 会话
    for rec in events_21_25:
        # 21/25 事件的 IP 可能在 Address 字段
        ip = rec.get("Address", "").strip()
        user = rec.get("User", "").strip()

        if ip and _looks_like_ip(ip):
            rdp_ip_set.add(ip)
            evidence_by_ip[ip]["21_25"].append(
                {
                    "time": rec.get("TimeCreated", ""),
                    "event_id": rec.get("EventID", ""),
                    "user": user,
                    "session_id": rec.get("SessionID", ""),
                }
            )
        else:
            evidence_by_ip["(unknown)"]["21_25"].append(
                {
                    "time": rec.get("TimeCreated", ""),
                    "event_id": rec.get("EventID", ""),
                    "user": user,
                    "raw": rec,
                }
            )

    # network_tcp 3389 Established
    for conn in network_tcp:
        local_port = conn.get("LocalPort", "")
        state = conn.get("State", "")
        remote_ip = conn.get("RemoteAddress", "")

        if local_port == "3389" and state == "Established" and remote_ip:
            rdp_ip_set.add(remote_ip)
            evidence_by_ip[remote_ip]["tcp_3389"].append(
                {
                    "remote_port": conn.get("RemotePort", ""),
                    "process_id": conn.get("OwningProcess", ""),
                    "creation_time": conn.get("CreationTime", ""),
                }
            )

    # 汇总每个 IP 的证据完整度
    for ip in sorted(rdp_ip_set):
        ev = evidence_by_ip[ip]
        has_4624 = bool(ev["4624_type10"]) or bool(ev["4624_type7"])
        has_1149 = bool(ev["1149"])
        has_21_25 = bool(ev["21_25"])
        has_tcp = bool(ev["tcp_3389"])

        # 评估完整度
        evidence_count = sum([has_4624, has_1149, has_21_25, has_tcp])
        if evidence_count >= 3:
            completeness = "full"
        elif evidence_count == 2:
            completeness = "partial"
        elif has_tcp and evidence_count == 1:
            completeness = "tcp_only"
        elif evidence_count == 1:
            completeness = "single_source"
        else:
            completeness = "none"

        ip_result = {
            "ip": ip,
            "ip_type": classify_ip(ip),
            "evidence": {
                "4624_type10": ev["4624_type10"],
                "4624_type7": ev["4624_type7"],
                "1149": ev["1149"],
                "21_25": ev["21_25"],
                "tcp_3389": ev["tcp_3389"],
            },
            "evidence_sources": evidence_count,
            "completeness": completeness,
        }
        result["rdp_ips"].append(ip_result)

    # 处理 (unknown) IP 的事件（字段为空的情况）
    if "(unknown)" in evidence_by_ip:
        ev = evidence_by_ip["(unknown)"]
        if any(ev.values()):
            result["events_with_empty_ip"] = {
                "1149": ev["1149"],
                "21_25": ev["21_25"],
            }

    return result


def _looks_like_ip(s: str) -> bool:
    """简单判断字符串是否像 IP 地址。"""
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Module 5: USN Ransomware Scan
# ---------------------------------------------------------------------------


def _extract_extension(filename: str) -> str:
    """从文件名提取后缀（小写化），处理多后缀情况。

    例如:
      "bootTel.dat.rox" → ".rox"
      "readme.txt"      → ".txt"
      "no_ext"          → ""
    """
    # 从最后一个点开始
    dot_pos = filename.rfind(".")
    if dot_pos <= 0:  # 没有点，或以点开头（隐藏文件）
        return ""
    return filename[dot_pos:].lower()


def _extract_original_extension(filename: str) -> str:
    """从被加密文件名提取原始后缀（倒数第二个后缀）。

    例如:
      "bootTel.dat.rox"   → ".dat"
      "file.docx.locked"  → ".docx"
      "file.rox"          → ""
    """
    # 去掉最后一个后缀
    dot_pos = filename.rfind(".")
    if dot_pos <= 0:
        return ""
    base = filename[:dot_pos]
    dot_pos2 = base.rfind(".")
    if dot_pos2 <= 0:
        return ""
    return base[dot_pos2:].lower()


def _match_ransom_note(filename: str) -> bool:
    """判断文件名是否匹配已知勒索信模式。"""
    for pattern in RANSOM_NOTE_COMPILED:
        if pattern.search(filename):
            return True
    return False


def _match_defender_path(abs_path: str) -> bool:
    """判断路径是否涉及 Windows Defender 组件。"""
    if not abs_path:
        return False
    for pattern in DEFENDER_PATH_COMPILED:
        if pattern.search(abs_path):
            return True
    return False


def _parse_usn_time(time_str: str) -> Optional[datetime]:
    """解析 USN 记录中的时间字段。

    格式: "2026-03-24 09:52:47" 或 "(空)"
    """
    if not time_str or time_str == "(空)":
        return None
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def analyze_usn_ransomware(usn_records: list[dict]) -> dict:
    """USN 日志勒索软件特征扫描。

    分析维度:
    ┌─────────────────────────────────────────────────────┐
    │  1. 加密后缀匹配 — 扫描已知勒索后缀                │
    │  2. 后缀分布统计 — 聚合每种勒索后缀的出现频次      │
    │  3. 勒索信检测   — 匹配已知勒索信文件名模式         │
    │  4. 路径聚合     — 按目录聚合加密文件分布           │
    │  5. 时间窗口     — 计算加密活动的起止时间           │
    │  6. 原始后缀分布 — 被加密前的文件类型分布           │
    │  7. Defender 变更 — 检测 Defender 组件状态变化       │
    └─────────────────────────────────────────────────────┘

    Returns:
        包含扫描结果的字典，供 AI 分析师直接使用。
    """
    result = {
        "total_usn_records": len(usn_records),
        "encrypted_files": {
            "count": 0,
            "extension_distribution": {},  # {".rox": 12, ".locked": 3}
            "original_extension_distribution": {},  # {".dat": 5, ".pma": 3}
            "samples": [],  # 前 50 个样本
        },
        "ransom_notes": {
            "count": 0,
            "by_name": {},  # 按文件名聚合: {"RECOVERY INFO.txt": {count, sample_paths, time_range}}
        },
        "path_distribution": {},  # {"C:\\Users\\": 15, "C:\\ProgramData\\": 8}
        "time_window": {
            "earliest": None,
            "latest": None,
            "duration_seconds": None,
        },
        "defender_changes": {
            "count": 0,
            "files": [],  # Defender 相关变更记录
        },
        "risk_indicators": {
            "has_ransomware_extensions": False,
            "has_ransom_notes": False,
            "has_mass_encryption": False,  # 加密文件 >= 10
            "has_defender_changes": False,
            "encryption_in_short_window": False,  # 加密集中在 < 60s 窗口
            "risk_score": 0,  # 0-100
        },
    }

    if not usn_records:
        return result

    # 遍历每条 USN 记录
    encrypted_times: list[datetime] = []

    for rec in usn_records:
        name = rec.get("Name", "").strip()
        abs_path = rec.get("AbsolutePath", "").strip()
        time_str = rec.get("Time", "").strip()

        if not name:
            continue

        ext = _extract_extension(name)

        # 1. 勒索后缀匹配
        if ext in RANSOMWARE_EXTENSIONS:
            result["encrypted_files"]["count"] += 1

            # 后缀分布
            result["encrypted_files"]["extension_distribution"][ext] = (
                result["encrypted_files"]["extension_distribution"].get(ext, 0) + 1
            )

            # 原始后缀分布
            orig_ext = _extract_original_extension(name)
            if orig_ext:
                result["encrypted_files"]["original_extension_distribution"][orig_ext] = (
                    result["encrypted_files"]["original_extension_distribution"].get(orig_ext, 0) + 1
                )

            # 样本（前 50 条）
            if len(result["encrypted_files"]["samples"]) < 50:
                result["encrypted_files"]["samples"].append({
                    "name": name,
                    "path": abs_path,
                    "time": time_str,
                    "extension": ext,
                })

            # 路径聚合 — 取前两级目录
            dir_path = _extract_top_dir(abs_path)
            if dir_path:
                result["path_distribution"][dir_path] = (
                    result["path_distribution"].get(dir_path, 0) + 1
                )

            # 记录时间用于时间窗口计算
            ts = _parse_usn_time(time_str)
            if ts:
                encrypted_times.append(ts)

        # 2. 勒索信检测
        if _match_ransom_note(name):
            result["ransom_notes"]["count"] += 1
            note_key = name  # 按文件名聚合
            if note_key not in result["ransom_notes"]["by_name"]:
                result["ransom_notes"]["by_name"][note_key] = {
                    "count": 0,
                    "sample_paths": [],
                    "time_range": {"earliest": time_str, "latest": time_str},
                }
            bucket = result["ransom_notes"]["by_name"][note_key]
            bucket["count"] += 1
            if len(bucket["sample_paths"]) < 10:
                bucket["sample_paths"].append(abs_path)
            # 更新时间范围
            if time_str:
                if not bucket["time_range"]["earliest"] or time_str < bucket["time_range"]["earliest"]:
                    bucket["time_range"]["earliest"] = time_str
                if not bucket["time_range"]["latest"] or time_str > bucket["time_range"]["latest"]:
                    bucket["time_range"]["latest"] = time_str

        # 3. Defender 变更检测
        if _match_defender_path(abs_path):
            result["defender_changes"]["count"] += 1
            # 限制存储条目数
            if len(result["defender_changes"]["files"]) < 30:
                result["defender_changes"]["files"].append({
                    "name": name,
                    "path": abs_path,
                    "time": time_str,
                })

    # 计算时间窗口
    if encrypted_times:
        encrypted_times.sort()
        earliest = encrypted_times[0]
        latest = encrypted_times[-1]
        duration = (latest - earliest).total_seconds()

        result["time_window"]["earliest"] = earliest.strftime("%Y-%m-%d %H:%M:%S")
        result["time_window"]["latest"] = latest.strftime("%Y-%m-%d %H:%M:%S")
        result["time_window"]["duration_seconds"] = duration

    # 按数量降序排列路径分布
    result["path_distribution"] = dict(
        sorted(
            result["path_distribution"].items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )

    # 按数量降序排列后缀分布
    result["encrypted_files"]["extension_distribution"] = dict(
        sorted(
            result["encrypted_files"]["extension_distribution"].items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )
    result["encrypted_files"]["original_extension_distribution"] = dict(
        sorted(
            result["encrypted_files"]["original_extension_distribution"].items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )

    # 风险指标计算
    enc_count = result["encrypted_files"]["count"]
    ri = result["risk_indicators"]

    ri["has_ransomware_extensions"] = enc_count > 0
    ri["has_ransom_notes"] = result["ransom_notes"]["count"] > 0
    ri["has_mass_encryption"] = enc_count >= 10
    ri["has_defender_changes"] = result["defender_changes"]["count"] > 0
    ri["encryption_in_short_window"] = (
        result["time_window"]["duration_seconds"] is not None
        and result["time_window"]["duration_seconds"] < 60
        and enc_count >= 5
    )

    # 风险评分（0-100）
    #   加密后缀存在: +20
    #   大量加密文件 (>=10): +25
    #   勒索信存在: +25
    #   短时间窗口集中加密: +15
    #   Defender 变更 + 加密文件同时存在: +15
    #   注意：单独的 Defender 变更（无加密文件）不加分，避免正常系统误报
    score = 0
    if ri["has_ransomware_extensions"]:
        score += 20
    if ri["has_mass_encryption"]:
        score += 25
    if ri["has_ransom_notes"]:
        score += 25
    if ri["encryption_in_short_window"]:
        score += 15
    if ri["has_defender_changes"] and ri["has_ransomware_extensions"]:
        score += 15
    ri["risk_score"] = score

    return result


def _extract_top_dir(abs_path: str) -> str:
    """从绝对路径提取前两级目录用于路径聚合。

    例如:
      "C:\\Users\\Administrator\\Desktop\\file.rox" → "C:\\Users\\Administrator"
      "C:\\ProgramData\\Microsoft\\..." → "C:\\ProgramData\\Microsoft"
      "Error:  Access is denied." → ""
    """
    if not abs_path or abs_path.startswith("Error:"):
        return ""

    # 统一使用 \\ 分隔（Windows 路径）
    parts = abs_path.replace("/", "\\").split("\\")
    if len(parts) >= 3:
        return "\\".join(parts[:3])
    elif len(parts) >= 2:
        return "\\".join(parts[:2])
    return ""


# ---------------------------------------------------------------------------
# Module 6: Threat Risk Score (Auto-computed)
# ---------------------------------------------------------------------------


def compute_risk_score(
    brute_force: dict,
    active_conn: dict,
    rdp: dict,
    usn_ransomware: dict,
    startup_items: dict,
    system_info: dict,
    stealth_intruders: list[str],
) -> dict:
    """基于预分析确定性数据自动计算入侵威胁评分（0-100）。

    纯函数，入参全是 Phase 3/2.5 的输出 dict，不引入新依赖。

    评分体系:
    ┌──────────────────────────────────────────────────────────────┐
    │  维度 A: 暴力破解严重度       0-20                           │
    │  维度 B: 异常登录指标          0-20                           │
    │  维度 C: 网络连接可疑度        0-20                           │
    │  维度 D: 持久化指标            0-20                           │
    │  维度 E: 勒索/破坏指标         0-20                           │
    │                                                              │
    │  压倒性规则:                                                  │
    │    当 A+B ≥ 25 → 最终得分下限 80                             │
    │    当 D ≥ 15   → 最终得分下限 80                             │
    │    当 E ≥ 15   → 最终得分下限 80                             │
    │                                                              │
    │  风险等级: 🔴 高危 80-100 | 🟠 中高 60-79                    │
    │           🟡 中 30-59    | 🟢 低 0-29                        │
    └──────────────────────────────────────────────────────────────┘

    Returns:
        {
            "dimensions": [
                {"id": "A", "name": "暴力破解严重度", "max": 20, "score": int, "triggers": [str]},
                ...
            ],
            "raw_total": int,
            "override_rules": [{"rule": str, "applied": bool, "floor": int}],
            "final_score": int,
            "risk_level": str,  # "critical" / "high" / "medium" / "low"
            "risk_label": str,  # "🔴 高危" / "🟠 中高" / "🟡 中风险" / "🟢 低风险"
        }
    """

    # ── 维度 A: 暴力破解严重度 (0-20) ──
    a_score = 0
    a_triggers: list[str] = []

    attack_ips = brute_force.get("attack_ips", [])
    has_external_bf = len(attack_ips) > 0
    penetrated_ips = [a for a in attack_ips if a.get("found_in_4624")]
    penetrated_count = len(penetrated_ips)

    if has_external_bf:
        a_score += 5
        a_triggers.append(f"外部暴力破解IP: {len(attack_ips)}个")
    if penetrated_count > 0:
        a_score += 10
        a_triggers.append(f"渗透成功IP: {penetrated_count}个")
    if penetrated_count >= 3:
        a_score += 5
        a_triggers.append(f"渗透成功≥3 ({penetrated_count})")

    # ── 维度 B: 异常登录指标 (0-20) ──
    b_score = 0
    b_triggers: list[str] = []

    stealth_count = len(stealth_intruders)
    if stealth_count > 0:
        b_score += 10
        b_triggers.append(
            f"低噪入侵者(Type10成功但不在4625): {stealth_count}个"
        )

    # 统计外部 IP 成功登录数（来自 RDP 交叉验证中的外部 IP）
    rdp_ips = rdp.get("rdp_ips", [])
    external_rdp_success = [
        ip_info for ip_info in rdp_ips
        if ip_info.get("ip_type") == "external"
        and (ip_info.get("evidence", {}).get("4624_type10")
             or ip_info.get("evidence", {}).get("4624_type7"))
    ]
    if len(external_rdp_success) >= 3:
        b_score += 5
        b_triggers.append(
            f"外部IP成功登录≥3: {len(external_rdp_success)}个"
        )

    # RDP 证据完整度 ≥ full 的外部 IP
    full_evidence_external = [
        ip_info for ip_info in rdp_ips
        if ip_info.get("ip_type") == "external"
        and ip_info.get("completeness") == "full"
    ]
    if full_evidence_external:
        b_score += 5
        b_triggers.append(
            f"外部IP RDP证据完整(full): {len(full_evidence_external)}个"
        )

    # ── 维度 C: 网络连接可疑度 (0-20) ──
    c_score = 0
    c_triggers: list[str] = []

    ext_conns = active_conn.get("external_established", [])
    high_threat = [c for c in ext_conns if c.get("threat_level") == "high"]
    medium_threat = [c for c in ext_conns if c.get("threat_level") == "medium"]

    if len(high_threat) >= 1:
        c_score += 10
        c_triggers.append(f"high威胁连接: {len(high_threat)}个")
    if len(medium_threat) >= 3:
        c_score += 5
        c_triggers.append(f"medium威胁连接: {len(medium_threat)}个")

    # 外部 Established 中关联登录事件占比
    ac_summary = active_conn.get("summary", {})
    total_ext = ac_summary.get("total_external_established", 0)
    linked = (
        ac_summary.get("linked_to_bruteforce", 0)
        + ac_summary.get("linked_to_success_login", 0)
    )
    if total_ext > 0 and linked / total_ext >= 0.5:
        c_score += 5
        c_triggers.append(
            f"外部连接≥50%关联登录事件: {linked}/{total_ext}"
        )

    # ── 维度 D: 持久化指标 (0-20) ──
    d_score = 0
    d_triggers: list[str] = []

    if startup_items and startup_items.get("status") == "ok":
        # 非标准计划任务
        sched = startup_items.get("scheduled_tasks") or {}
        non_std_tasks = sched.get("non_standard", [])
        if len(non_std_tasks) >= 1:
            d_score += 10
            d_triggers.append(f"非标准计划任务: {len(non_std_tasks)}个")

        # 注册表启动项异常
        reg_startup = startup_items.get("registry_startup") or []
        if reg_startup:
            d_score += 5
            d_triggers.append(f"注册表启动项: {len(reg_startup)}个")

        # WMI 启动命令
        wmi = startup_items.get("wmi_startup_commands") or []
        if wmi:
            d_score += 5
            d_triggers.append(f"WMI启动命令: {len(wmi)}个")

    # ── 维度 E: 勒索/破坏指标 (0-20) ──
    e_score = 0
    e_triggers: list[str] = []

    usn_risk = usn_ransomware.get("risk_indicators", {})
    usn_score = usn_risk.get("risk_score", 0)

    if usn_score >= 40:
        e_score += 10
        e_triggers.append(f"USN勒索风险评分≥40: {usn_score}/100")
    if usn_score >= 70:
        e_score += 5
        e_triggers.append(f"USN勒索风险评分≥70: {usn_score}/100")

    # Defender 异常 + 加密文件同时存在
    has_defender = usn_risk.get("has_defender_changes", False)
    has_ransom_ext = usn_risk.get("has_ransomware_extensions", False)
    if has_defender and has_ransom_ext:
        e_score += 5
        e_triggers.append("Defender变更+加密文件同时存在")

    # ── 汇总 ──
    raw_total = a_score + b_score + c_score + d_score + e_score

    # 压倒性规则
    override_rules = []
    final_score = raw_total

    ab_sum = a_score + b_score
    rule_ab = {
        "rule": "A+B≥25 → 下限80",
        "applied": ab_sum >= 25,
        "floor": 80,
    }
    override_rules.append(rule_ab)
    if rule_ab["applied"] and final_score < 80:
        final_score = 80

    rule_d = {
        "rule": "D≥15 → 下限80",
        "applied": d_score >= 15,
        "floor": 80,
    }
    override_rules.append(rule_d)
    if rule_d["applied"] and final_score < 80:
        final_score = 80

    rule_e = {
        "rule": "E≥15 → 下限80",
        "applied": e_score >= 15,
        "floor": 80,
    }
    override_rules.append(rule_e)
    if rule_e["applied"] and final_score < 80:
        final_score = 80

    # 风险等级映射
    if final_score >= 80:
        risk_level, risk_label = "critical", "🔴 高危"
    elif final_score >= 60:
        risk_level, risk_label = "high", "🟠 中高"
    elif final_score >= 30:
        risk_level, risk_label = "medium", "🟡 中风险"
    else:
        risk_level, risk_label = "low", "🟢 低风险"

    return {
        "dimensions": [
            {"id": "A", "name": "暴力破解严重度", "max": 20, "score": a_score, "triggers": a_triggers},
            {"id": "B", "name": "异常登录指标", "max": 20, "score": b_score, "triggers": b_triggers},
            {"id": "C", "name": "网络连接可疑度", "max": 20, "score": c_score, "triggers": c_triggers},
            {"id": "D", "name": "持久化指标", "max": 20, "score": d_score, "triggers": d_triggers},
            {"id": "E", "name": "勒索/破坏指标", "max": 20, "score": e_score, "triggers": e_triggers},
        ],
        "raw_total": raw_total,
        "override_rules": override_rules,
        "final_score": final_score,
        "risk_level": risk_level,
        "risk_label": risk_label,
    }
