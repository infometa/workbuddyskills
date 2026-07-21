"""暴力破解检测器 (T1110)"""
from __future__ import annotations


def detect_brute_force(parsed: dict, raw_kv: dict) -> dict | None:
    """检测 SSH/RDP/MySQL 等暴力破解行为

    Args:
        parsed: L0 输出的 parsed dict
        raw_kv: L0 输出的 _raw_kv (完整 kv 兜底)

    Returns:
        None (未命中) 或 dict (含 threat_type / confidence / signals)
    """
    rule_name = (parsed.get("rule_name") or "").lower()
    rule_id = parsed.get("rule_id") or ""
    event_name = (parsed.get("rule_name") or "")
    dst_port = parsed.get("dst_port")
    src_ip = parsed.get("src_ip")

    # 1. 规则名命中
    rule_hit = any(kw in rule_name or kw in event_name for kw in [
        "失败", "暴力", "brute", "密码喷洒", "credential",
    ])

    # 2. 端口命中 (SSH / RDP / MySQL / RDP)
    port_hit = dst_port in (22, 3389, 3306, 5432, 6379, 27017)

    if not (rule_hit or port_hit):
        return None

    # 3. count 字段 (多次尝试信号)
    count_raw = raw_kv.get("count", "1")
    try:
        count = int(count_raw)
    except (ValueError, TypeError):
        count = 1

    # 4. 评估置信度
    confidence = 0.0
    reasons = []

    if rule_hit:
        confidence += 0.5
        reasons.append(f"规则名命中: '{event_name}'")

    if port_hit:
        confidence += 0.2
        reasons.append(f"目的端口: {dst_port}")

    if count >= 5:
        confidence += 0.3
        reasons.append(f"count={count} (>=5, 强多次尝试信号)")
    elif count >= 2:
        confidence += 0.15
        reasons.append(f"count={count} (>=2, 弱多次尝试信号)")

    confidence = min(confidence, 1.0)

    if confidence < 0.3:
        return None

    return {
        "threat_type": "暴力破解 (Brute Force)",
        "ttp": "T1110",
        "ttp_name": "Brute Force",
        "confidence": round(confidence, 2),
        "reasons": reasons,
        "signals": {
            "src_ip": src_ip,
            "dst_ip": parsed.get("dst_ip"),
            "dst_port": dst_port,
            "dst_host": parsed.get("host_ip") or parsed.get("hostname"),
            "user": parsed.get("user"),
            "count": count,
            "rule_name": event_name,
        },
        "kill_chain_phase": "Initial Access",
        "correlation_hints": {
            "pivot_keys": ["src_ip", "dst_ip"],
            "time_window_min": 30,
            "rationale": "同 src_ip 短时间多次失败, 后续可能有 T1078 成功登录, 关联 L1 后续事件",
        },
    }
