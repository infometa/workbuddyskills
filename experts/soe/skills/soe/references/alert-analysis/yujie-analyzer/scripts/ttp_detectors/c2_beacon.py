"""C2 Beacon 检测器 (T1071 / T1095 / T1572)"""
from __future__ import annotations


def detect_c2_beacon(parsed: dict, nat_bonus: float = 0.0) -> dict | None:
    """检测 C2 Beacon 行为

    Args:
        parsed: L0 输出的 parsed dict
        nat_bonus: NAT 异常加分 (从 nat_resolve 算)

    Returns:
        None 或 dict
    """
    flow = parsed.get("flow_stats")
    if not flow:
        return None

    bytes_to_server = flow.get("bytes_toserver", 0) or 0
    bytes_to_client = flow.get("bytes_toclient", 0) or 0
    pkts_to_server = flow.get("pkts_toserver", 0) or 0
    pkts_to_client = flow.get("pkts_toclient", 0) or 0

    app_proto = parsed.get("app_proto", "")
    score = parsed.get("score", 0) or 0

    signals = []
    confidence = 0.0

    # 1. 单向流: 强 Beacon 信号
    if bytes_to_client == 0 and pkts_to_client == 0 and bytes_to_server > 0:
        confidence += 0.6
        signals.append(f"单向流 (bytes_toclient=0, pkts_toclient=0), 符合 Beacon 特征")
    elif bytes_to_client == 0 and bytes_to_server > 0:
        confidence += 0.3
        signals.append(f"近单向流 (bytes_toclient=0)")

    # 2. 小包频繁: 典型心跳
    if 0 < bytes_to_server < 500 and pkts_to_server > 0:
        confidence += 0.2
        signals.append(f"小包请求 (avg={bytes_to_server // max(pkts_to_server, 1)}B/pkt)")

    # 3. DPI 失败: 可能是加密/混淆协议
    if app_proto == "failed":
        confidence += 0.15
        signals.append(f"DPI 协议识别失败 (app_proto=failed)")

    # 4. 御界打分高
    if score >= 80:
        confidence += 0.1
        signals.append(f"御界内部打分高 (score={score})")

    # 5. NAT 加分
    confidence += nat_bonus
    if nat_bonus > 0:
        signals.append(f"NAT 异常加分 (+{nat_bonus:.2f})")

    confidence = min(confidence, 1.0)
    if confidence < 0.4:
        return None

    return {
        "threat_type": "C2 Beacon",
        "ttp": "T1071",
        "ttp_name": "Application Layer Protocol",
        "confidence": round(confidence, 2),
        "reasons": signals,
        "signals": {
            "bytes_to_server": bytes_to_server,
            "bytes_to_client": bytes_to_client,
            "pkts_to_server": pkts_to_server,
            "pkts_to_client": pkts_to_client,
            "app_proto": app_proto,
            "score": score,
            "real_attacker_ip": parsed.get("real_attacker_ip"),
            "real_victim_ip": parsed.get("real_victim_ip"),
        },
        "kill_chain_phase": "Command and Control",
        "correlation_hints": {
            "pivot_keys": ["real_attacker_ip", "real_victim_ip"],
            "time_window_min": 15,
            "rationale": "Beacon 通常持续时间长, 应拉时间窗内同 attacker 的所有告警, 并关联 cwp 看受害主机状态",
        },
    }
