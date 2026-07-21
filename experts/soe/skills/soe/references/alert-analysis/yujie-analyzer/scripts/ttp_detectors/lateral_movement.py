"""横向移动弱信号检测 (T1021 / T1210)

单事件级只能给弱信号, 强信号需要 L2 聚合
"""
from __future__ import annotations
import re


LATERAL_PORTS = {22, 23, 135, 139, 445, 3389, 5900, 5985, 5986}  # SSH/Telnet/RPC/SMB/RDP/VNC/WinRM


# 已知漏洞 EXP 特征 (Suricata signature 关键字)
EXPLOIT_SIGNATURES = [
    (r"ms17-?010|eternalblue", "T1210", "MS17-010 EternalBlue"),
    (r"log4j|log4shell|cve-2021-44228", "T1190", "Log4Shell"),
    (r"cve-2017-0144", "T1210", "CVE-2017-0144 (SMB)"),
    (r"cve-2019-0708|bluekeep", "T1210", "BlueKeep RDP"),
    (r"cve-2020-0796|smbghost", "T1210", "SMBGhost"),
    (r"cve-2021-26855|exchange|proxylogon", "T1190", "ProxyLogon"),
    (r"cve-2021-34527|printnightmare", "T1068", "PrintNightmare"),
    (r"struts2.*s2-0\d\d", "T1190", "Apache Struts2 RCE"),
    (r"thinkphp.*rce", "T1190", "ThinkPHP RCE"),
    (r"weblogic.*rce|cve-2020-14882", "T1190", "WebLogic RCE"),
    (r"confluence.*ognl", "T1190", "Confluence OGNL"),
]


def detect_lateral_movement(parsed: dict, nat_bonus: float = 0.0) -> dict | None:
    """横向移动弱信号识别 (单事件级别)

    Args:
        parsed: L0 输出的 parsed dict
        nat_bonus: NAT 加分

    Returns:
        None 或 dict
    """
    dst_port = parsed.get("dst_port")
    src_ip = parsed.get("src_ip") or ""
    real_attacker = parsed.get("real_attacker_ip") or src_ip
    alert = parsed.get("alert", {}) or {}
    signature = (alert.get("signature") or "") + " " + (parsed.get("rule_name") or "")
    score = parsed.get("score", 0) or 0

    signals = []
    confidence = 0.0
    ttp = None
    ttp_name = None

    # 1. 已知 EXP 特征 (最强信号)
    for pattern, ttp_id, name in EXPLOIT_SIGNATURES:
        if re.search(pattern, signature, re.IGNORECASE):
            confidence += 0.7
            ttp = ttp_id
            ttp_name = name
            signals.append(f"命中已知漏洞 EXP: {name} (signature: '{signature[:80]}')")
            break

    # 2. 横向服务端口 + 内网 src
    if dst_port in LATERAL_PORTS:
        from nat_resolve import is_internal_ip
        if is_internal_ip(real_attacker):
            confidence += 0.3
            signals.append(f"内网源 → 横向服务端口 {dst_port}")
            if not ttp:
                ttp = "T1021"
                ttp_name = "Remote Services"

    # 3. 御界打分
    if score >= 80:
        confidence += 0.1
        signals.append(f"御界打分高 (score={score})")

    # 4. NAT 加分 (公网攻击者横向更可疑)
    confidence += nat_bonus
    if nat_bonus > 0:
        signals.append(f"NAT 异常加分 (+{nat_bonus:.2f})")

    confidence = min(confidence, 1.0)
    if confidence < 0.4:
        return None

    return {
        "threat_type": f"横向移动 ({ttp_name or '弱信号'})",
        "ttp": ttp or "T1021",
        "ttp_name": ttp_name or "Remote Services",
        "confidence": round(confidence, 2),
        "reasons": signals,
        "signals": {
            "dst_port": dst_port,
            "src_ip": src_ip,
            "real_attacker_ip": real_attacker,
            "real_victim_ip": parsed.get("real_victim_ip"),
            "signature": signature[:200],
            "score": score,
        },
        "kill_chain_phase": "Lateral Movement",
        "correlation_hints": {
            "pivot_keys": ["real_attacker_ip", "real_victim_ip"],
            "time_window_min": 60,
            "rationale": "横向移动强信号需要 L2 聚合: 同一 attacker 短时间多 dst_port / 多 victim, 跨主机扫描模式",
        },
        "_needs_correlation": True,
    }
