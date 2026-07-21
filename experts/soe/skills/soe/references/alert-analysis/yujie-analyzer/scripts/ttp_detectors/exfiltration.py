"""数据外传检测器 (T1567 / T1041)"""
from __future__ import annotations


# 已知数据外传协议端口
EXFIL_PORTS = {
    21: "ftp",
    22: "sftp",  # 双向, 不一定外传
    23: "telnet",
    25: "smtp",
    53: "dns",          # DNS Tunnel
    80: "http",
    443: "https",
    465: "smtps",
    587: "smtp-submission",
    993: "imap-s",
    995: "pop3-s",
    8080: "http-alt",
    8443: "https-alt",
}


# 已知矿池 / 跨境外联关键词 (用于规则名匹配)
EXFIL_KEYWORDS = [
    "exfil", "外传", "上传", "数据泄漏", "data leak",
    "mining pool", "矿池", "bitcoin", "monero", "cryptonight",
    "tor exit", "onion",
]


def detect_exfiltration(parsed: dict, nat_bonus: float = 0.0) -> dict | None:
    """检测数据外传

    Args:
        parsed: L0 输出的 parsed dict
        nat_bonus: NAT 加分

    Returns:
        None 或 dict
    """
    flow = parsed.get("flow_stats", {}) or {}
    bytes_to_server = flow.get("bytes_toserver", 0) or 0
    app_proto = parsed.get("app_proto", "")
    rule_name = (parsed.get("rule_name") or "").lower()
    dst_port = parsed.get("dst_port")
    real_attacker = parsed.get("real_attacker_ip")
    real_victim = parsed.get("real_victim_ip")
    score = parsed.get("score", 0) or 0

    from nat_resolve import is_external_ip
    external_attacker = is_external_ip(real_attacker)

    signals = []
    confidence = 0.0

    # 1. 大流量外发 (典型外传)
    if bytes_to_server >= 1024 * 1024:  # >= 1MB
        confidence += 0.5
        signals.append(f"大流量外发: bytes_to_server={bytes_to_server} (>= 1MB)")
    elif bytes_to_server >= 100 * 1024:  # >= 100KB
        confidence += 0.3
        signals.append(f"较大流量外发: bytes_to_server={bytes_to_server}")

    # 2. 规则名命中 (外传 / 矿池)
    for kw in EXFIL_KEYWORDS:
        if kw in rule_name:
            confidence += 0.4
            signals.append(f"规则名命中外传关键字: '{kw}'")
            break

    # 3. 公网目标 + 外发协议
    if external_attacker and dst_port in EXFIL_PORTS and bytes_to_server > 10000:
        confidence += 0.2
        signals.append(f"公网目标 ({real_attacker}) + 协议端口 {dst_port} ({EXFIL_PORTS[dst_port]})")

    # 4. NAT 加分
    confidence += nat_bonus
    if nat_bonus > 0:
        signals.append(f"NAT 异常加分 (+{nat_bonus:.2f})")

    confidence = min(confidence, 1.0)
    if confidence < 0.4:
        return None

    return {
        "threat_type": "数据外传 (Exfiltration)",
        "ttp": "T1567",
        "ttp_name": "Exfiltration Over Web Service",
        "confidence": round(confidence, 2),
        "reasons": signals,
        "signals": {
            "bytes_to_server": bytes_to_server,
            "app_proto": app_proto,
            "rule_name": rule_name,
            "dst_port": dst_port,
            "real_attacker_ip": real_attacker,
            "real_victim_ip": real_victim,
            "external_target": external_attacker,
        },
        "kill_chain_phase": "Exfiltration",
        "correlation_hints": {
            "pivot_keys": ["real_attacker_ip", "real_victim_ip"],
            "time_window_min": 30,
            "rationale": "外传通常是攻击链末端, 关联 cwp 看受害主机的进程 / 文件系统变化",
        },
    }
