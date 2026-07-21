"""横向移动检测器 (T1021 / T1570)

注: 单事件级别的横向移动检测有限, 强信号需要历史聚合.
   v0.1 只做弱信号识别, 真正的横向判定留给 L2.
"""
from __future__ import annotations
import re


LATERAL_PROCESSES = {
    "psexec": ("T1021.002", "SMB 横向 (PsExec)"),
    "wmic": ("T1047", "WMI 横向"),
    "smbclient": ("T1021.002", "SMB 横向"),
    "smbmap": ("T1021.002", "SMB 横向"),
    "crackmapexec": ("T1021.002", "SMB 横向"),
    "evil-winrm": ("T1021.001", "WinRM 横向"),
    "winexe": ("T1021.002", "SMB 横向"),
    "nmap": ("T1046", "网络扫描"),
    "masscan": ("T1046", "网络扫描"),
    "zmap": ("T1046", "网络扫描"),
}

LATERAL_KEYWORDS_IN_CMD = [
    (r"mimikatz", "T1003.001", "Mimikatz 凭据窃取"),
    (r"lsadump", "T1003.001", "LSA 凭据窃取"),
    (r"sekurlsa", "T1003.001", "Mimikatz 模块"),
    (r"kerberoast", "T1558.003", "Kerberoasting"),
    (r"asreproast", "T1558.004", "AS-REP Roasting"),
    (r"bloodhound", "T1087", "BloodHound 域枚举"),
    (r"sharpHound", "T1087", "SharpHound 域枚举"),
    (r"/etc/shadow", "T1003.008", "/etc/shadow 读取"),
    (r"/etc/passwd", "T1003.008", "/etc/passwd 读取"),
]


def detect_lateral_movement(parsed: dict, raw_kv: dict) -> dict | None:
    """横向移动弱信号识别 (单事件级别)

    Args:
        parsed: L0 输出的 parsed dict
        raw_kv: L0 输出的 _raw_kv

    Returns:
        None 或 dict
    """
    process = (parsed.get("process") or "").lower()
    cmd = parsed.get("cmd") or raw_kv.get("cmd") or ""
    full_text = f"{process} {cmd}".lower()

    hits = []
    matched_ttps = set()

    # 1. 已知横向工具进程名
    for tool, (ttp, name) in LATERAL_PROCESSES.items():
        if tool in full_text:
            hits.append({"tool": tool, "ttp": ttp, "name": name})
            matched_ttps.add(ttp)

    # 2. cmd 关键字
    for pattern, ttp, name in LATERAL_KEYWORDS_IN_CMD:
        if re.search(pattern, full_text, re.IGNORECASE):
            hits.append({"keyword": pattern, "ttp": ttp, "name": name})
            matched_ttps.add(ttp)

    if not hits:
        return None

    return {
        "threat_type": "横向移动 (Lateral Movement - 弱信号)",
        "ttp": sorted(matched_ttps)[0],
        "ttp_name": hits[0]["name"],
        "confidence": 0.7,  # 单事件只能给 0.7, 强信号需要 L2 聚合
        "reasons": [f"命中: '{h.get('tool') or h.get('keyword')}' → {h['name']}" for h in hits],
        "signals": {
            "matched_signals": hits,
            "host_ip": parsed.get("host_ip"),
            "user": parsed.get("user"),
            "src_ip": parsed.get("src_ip"),
            "dst_ip": parsed.get("dst_ip"),
        },
        "kill_chain_phase": "Lateral Movement",
        "correlation_hints": {
            "pivot_keys": ["host_ip", "user", "src_ip"],
            "time_window_min": 60,
            "rationale": "横向移动强信号需要: 同一 user 跨多 host / 同一 host 跨多 dst_ip. 需要 L2 历史聚合",
        },
        "_needs_correlation": True,  # 标记需要 L2 加持
    }
