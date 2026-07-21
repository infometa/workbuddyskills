"""NAT 还原与封装链识别 (L1 御界核心能力)

L0 已经在 parsed.real_attacker_ip / real_victim_ip 填了真实 IP (基于 ext.attacker_ip / ext.victim_ip).
L1 负责:
  1. 校验: IP 是否一致
  2. 增强: 推断 NAT 链 (跳数 / 类型)
  3. 评估: 还原可信度
  4. 联动: 异常 NAT 模式的威胁评分
"""
from __future__ import annotations
import ipaddress
from typing import Any


def classify_ip(ip: str | None) -> str:
    """识别 IP 性质: public / private / loopback / multicast / invalid / unknown"""
    if not ip:
        return "unknown"
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_loopback:
            return "loopback"
        if ip_obj.is_multicast:
            return "multicast"
        if ip_obj.is_reserved:
            return "reserved"
        if ip_obj.is_private:
            return "private"
        if ip_obj.is_global:
            return "public"
        return "other"
    except (ValueError, TypeError):
        return "invalid"


def is_internal_ip(ip: str | None) -> bool:
    return classify_ip(ip) == "private"


def is_external_ip(ip: str | None) -> bool:
    return classify_ip(ip) == "public"


def detect_nat_chain(parsed: dict) -> list[str]:
    """从 parsed 提取 NAT 链 (封装类型列表)"""
    chain = []
    encap = parsed.get("encapsulation", {}) or {}
    if encap.get("gre"):
        chain.append("gre")
    if encap.get("vxlan"):
        chain.append("vxlan")
    if encap.get("ipip"):
        chain.append("ipip")

    # 从 packet_header 推断
    pkt = parsed.get("packet_header", {}) or {}
    if pkt.get("gre"):
        chain.append("gre")
    if pkt.get("inner"):
        chain.append("nested_ip")

    return list(set(chain))  # 去重


def assess_nat_suspicion(parsed: dict) -> tuple[float, list[str]]:
    """评估 NAT 模式的异常性, 返回 (加分值, 原因列表)

    分数加到 detector 的 confidence 上
    """
    bonus = 0.0
    reasons = []

    real_attacker = parsed.get("real_attacker_ip")
    real_victim = parsed.get("real_victim_ip")
    src_ip = parsed.get("src_ip")
    dst_ip = parsed.get("dst_ip")
    nat_chain = detect_nat_chain(parsed)

    # 1. 公网攻击者 → 私网受害
    if is_external_ip(real_attacker) and is_internal_ip(real_victim):
        bonus += 0.3
        reasons.append(f"公网攻击者 {real_attacker} → 私网受害 {real_victim} (高危)")

    # 2. 私网攻击者 → 公网受害 (不寻常)
    if is_internal_ip(real_attacker) and is_external_ip(real_victim):
        bonus += 0.2
        reasons.append(f"私网攻击者 {real_attacker} → 公网受害 {real_victim} (中危)")

    # 3. GRE 跨 VPC 隐蔽通道
    if "gre" in nat_chain:
        gre = parsed.get("encapsulation", {}).get("gre") or {}
        vpcid = gre.get("vpcid") if isinstance(gre, dict) else None
        if vpcid:
            bonus += 0.4
            reasons.append(f"GRE 跨 VPC 隧道 (vpcid={vpcid})")
        else:
            bonus += 0.2
            reasons.append("GRE 封装 (跨网段)")

    # 4. 嵌套 IP (GRE + 内层 VPN)
    if "nested_ip" in nat_chain:
        bonus += 0.1
        reasons.append("嵌套 IP 封装 (多层 VPN)")

    # 5. IP 不一致 (OCSF 透出 ≠ 真实)
    if parsed.get("ip_discrepancy"):
        bonus += 0.1
        reasons.append(f"OCSF 透出 IP 与真实 IP 不一致 (NAT 隐藏)")

    return min(bonus, 0.5), reasons  # 最多 +0.5


def resolve_nat_chain(parsed: dict) -> dict[str, Any]:
    """主入口: NAT 还原 + 封装链 + 可信度评估

    Args:
        parsed: L0 输出的 parsed dict

    Returns:
        {
            "real_attacker_ip": str,
            "real_victim_ip": str,
            "ocsf_src_ip": str,
            "ocsf_dst_ip": str,
            "ip_discrepancy": bool,
            "nat_chain": list[str],
            "attacker_class": str,    # public/private/...
            "victim_class": str,
            "trust_level": str,       # high/medium/low
            "nat_suspicion_bonus": float,  # 异常 NAT 加分
            "nat_suspicion_reasons": list[str],
            "rationale": str,
        }
    """
    src_ip = parsed.get("src_ip")
    dst_ip = parsed.get("dst_ip")
    real_attacker = parsed.get("real_attacker_ip") or src_ip
    real_victim = parsed.get("real_victim_ip") or dst_ip

    discrepancy = bool(
        (real_attacker and src_ip and real_attacker != src_ip)
        or (real_victim and dst_ip and real_victim != dst_ip)
    )

    nat_chain = detect_nat_chain(parsed)
    bonus, nat_reasons = assess_nat_suspicion(parsed)

    # 可信度: 优先看 L0 是不是从 ext 填的
    has_ext_data = bool(parsed.get("encapsulation", {}).get("gre") or parsed.get("src_mac"))
    if has_ext_data:
        trust = "high"
    elif discrepancy:
        trust = "medium"
    else:
        trust = "high"

    # 拼 rationale
    parts = []
    if not discrepancy:
        parts.append("OCSF IP 与真实 IP 一致, 无 NAT")
    else:
        parts.append(f"OCSF: {src_ip}→{dst_ip}, 真实: {real_attacker}→{real_victim}")
    if nat_chain:
        parts.append(f"封装链: {' → '.join(nat_chain)}")
    if nat_reasons:
        parts.append("异常: " + "; ".join(nat_reasons))

    return {
        "real_attacker_ip": real_attacker,
        "real_victim_ip": real_victim,
        "ocsf_src_ip": src_ip,
        "ocsf_dst_ip": dst_ip,
        "ip_discrepancy": discrepancy,
        "nat_chain": nat_chain,
        "attacker_class": classify_ip(real_attacker),
        "victim_class": classify_ip(real_victim),
        "trust_level": trust,
        "nat_suspicion_bonus": bonus,
        "nat_suspicion_reasons": nat_reasons,
        "rationale": "; ".join(parts),
    }
