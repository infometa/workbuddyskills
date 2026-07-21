"""隧道 / 代理检测器 (T1572 / T1090)"""
from __future__ import annotations


# 已知隧道 / 代理端口
TUNNEL_PORTS = {
    # VPN
    51820: ("WireGuard", "T1572"),
    1194: ("OpenVPN", "T1572"),
    1723: ("PPTP", "T1572"),
    500: ("IPsec IKE", "T1572"),
    4500: ("IPsec NAT-T", "T1572"),
    1701: ("L2TP", "T1572"),
    # Proxy
    1080: ("SOCKS", "T1090.001"),
    3128: ("HTTP Proxy (Squid)", "T1090.001"),
    8080: ("HTTP Proxy (alt)", "T1090.001"),
    8888: ("HTTP Proxy (alt)", "T1090.001"),
}


def detect_tunnel(parsed: dict, nat_bonus: float = 0.0) -> dict | None:
    """检测 VPN 隧道 / 代理建立

    Args:
        parsed: L0 输出的 parsed dict
        nat_bonus: NAT 异常加分

    Returns:
        None 或 dict
    """
    dst_port = parsed.get("dst_port")
    src_port = parsed.get("src_port")
    app_proto = parsed.get("app_proto", "")
    rule_name = parsed.get("rule_name", "")
    nat_chain = parsed.get("encapsulation", {}).get("gre") is not None

    signals = []
    confidence = 0.0
    tunnel_name = None
    ttp = None

    # 1. 端口命中
    if dst_port in TUNNEL_PORTS:
        tunnel_name, ttp = TUNNEL_PORTS[dst_port]
        confidence += 0.5
        signals.append(f"目的端口 {dst_port} 命中已知隧道/代理: {tunnel_name}")

    # 2. 规则名命中
    if any(kw in rule_name.lower() for kw in ["wireguard", "vpn", "openvpn", "tunnel", "proxy", "ipsec", "pptp", "l2tp"]):
        confidence += 0.3
        signals.append(f"规则名命中 VPN/代理: '{rule_name}'")

    # 3. DPI 失败 + 加密端口
    if app_proto == "failed" and dst_port in (51820, 1194, 500, 4500):
        confidence += 0.2
        signals.append(f"DPI 失败 + 加密 VPN 端口")

    # 4. GRE 封装 (跨 VPC 隐蔽通道)
    if nat_chain:
        confidence += 0.3
        gre = parsed.get("encapsulation", {}).get("gre", {}) or {}
        vpcid = gre.get("vpcid") if isinstance(gre, dict) else None
        if vpcid:
            signals.append(f"GRE 跨 VPC 隧道 (vpcid={vpcid})")
        else:
            signals.append("GRE 封装")

    # 5. NAT 加分
    confidence += nat_bonus
    if nat_bonus > 0:
        signals.append(f"NAT 异常加分 (+{nat_bonus:.2f})")

    confidence = min(confidence, 1.0)
    if confidence < 0.4:
        return None

    return {
        "threat_type": f"隧道/代理 ({tunnel_name or 'unknown'})",
        "ttp": ttp or "T1572",
        "ttp_name": "Protocol Tunneling" if (ttp or "").startswith("T1572") else "Proxy",
        "confidence": round(confidence, 2),
        "reasons": signals,
        "signals": {
            "dst_port": dst_port,
            "src_port": src_port,
            "app_proto": app_proto,
            "rule_name": rule_name,
            "tunnel_type": tunnel_name,
            "has_gre_encap": nat_chain,
            "real_attacker_ip": parsed.get("real_attacker_ip"),
            "real_victim_ip": parsed.get("real_victim_ip"),
        },
        "kill_chain_phase": "Command and Control",
        "correlation_hints": {
            "pivot_keys": ["real_victim_ip", "real_attacker_ip"],
            "time_window_min": 30,
            "rationale": "隧道一旦建立, 后续会有 C2 / 数据外传告警, 应拉时间窗内同受害 IP 的所有告警; 关联 cwp 看受害主机是否有 VPN 客户端进程",
        },
    }
