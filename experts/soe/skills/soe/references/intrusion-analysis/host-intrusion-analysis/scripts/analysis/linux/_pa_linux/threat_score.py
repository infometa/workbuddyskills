"""Linux 入侵威胁评分计算。

从预分析结果计算威胁评分（0-100），支持独立调用。
不依赖预分析器实例，仅依赖结构化数据。

用法：
    from _pa_linux.threat_score import compute_threat_score
    score = compute_threat_score(brute_force, ssh_successes, persistence_vectors)
"""

import sys
from collections import defaultdict

from _common.parsers import classify_ip
from _pa_linux.constants import (
    PERSIST_AUTHKEY,
    PERSIST_CRONTAB,
    PERSIST_INITD,
    PERSIST_PROFILE,
    PERSIST_RCLOCAL,
    PERSIST_SYSTEMD,
)


def compute_threat_score(
    brute_force: dict,
    ssh_successes: list[dict],
    persistence_vectors: list[dict],
) -> dict:
    """基于确定性数据自动计算入侵威胁评分（0-100）。

    数据源：
      - brute_force: analyze_ssh_brute_force() 的输出
      - ssh_successes: parse_ssh_successes() / _parse_ssh_successes_raw() 的输出
      - persistence_vectors: extract_persistence_vectors() 的输出（可为空列表）

    当 persistence_vectors 为空时（如 linux_log_folder），维度 D 自动为 0，
    等效于"无持久化数据源"的正确评分。

    返回结构：
    {
        "dimensions": [...],
        "raw_total": float,
        "override_rules": [...],
        "final_score": int,
        "risk_level": str,
        "risk_label": str,
    }

    评分体系（动态分值）:
    ┌──────────────────────────────────────────────────────────────┐
    │  各维度先按固定基础分独立评分（0-20 各维度内部评判标准）:      │
    │    维度 A: 暴力破解严重度        0-20                        │
    │    维度 B: 异常登录指标           0-20                        │
    │    维度 C: 网络连接可疑度         0-20                        │
    │    维度 D: 持久化指标             0-20                        │
    │    维度 E: 勒索/破坏指标          0-20 (Linux 暂无数据源)     │
    │                                                              │
    │  动态分值汇总:                                                │
    │    1. 识别"活跃维度"（有数据源且 raw_max > 0 的维度）         │
    │    2. 将 100 分按得分率加权分配给各活跃维度                    │
    │       weight_i = ratio_i / sum(ratio_all)                    │
    │    3. 最终得分 = sum(ratio_i × allocated_i)                  │
    │       即: 数据丰富且威胁高的维度自然拿到更多分               │
    │                                                              │
    │  压倒性规则:                                                  │
    │    当 A+B ≥ 25(原始) → 最终得分下限 80                       │
    │    当 D = 20(满分)   → 最终得分下限 80                       │
    │                                                              │
    │  风险等级: 🔴 高危 80-100 | 🟠 中高 60-79                    │
    │           🟡 中 30-59    | 🟢 低 0-29                        │
    └──────────────────────────────────────────────────────────────┘
    """

    # ── 维度 A: 暴力破解严重度 (0-20) ──
    a_score = 0
    a_triggers: list[str] = []

    attack_ips = brute_force.get("attack_ips", [])
    has_external_bf = len(attack_ips) > 0
    penetrated_ips = [a for a in attack_ips if a.get("found_in_success")]
    penetrated_count = len(penetrated_ips)

    if has_external_bf:
        a_score += 5
        a_triggers.append(f"外部暴力破解IP: {len(attack_ips)}个")
    if len(attack_ips) >= 5:
        a_score += 5
        a_triggers.append(f"暴力破解源IP≥5: {len(attack_ips)}个")
    if penetrated_count > 0:
        a_score += 5
        a_triggers.append(f"渗透成功IP: {penetrated_count}个")
    if penetrated_count >= 3:
        a_score += 5
        a_triggers.append(f"渗透成功≥3 ({penetrated_count})")

    # ── 维度 B: 异常登录指标 (0-20) ──
    b_score = 0
    b_triggers: list[str] = []

    # 成功登录中来自外部 IP 且不在暴力破解列表中的 → 低噪入侵者
    bf_ip_set = {a["ip"] for a in attack_ips}
    stealth_external = []
    for s in ssh_successes:
        ip = s.get("ip", "")
        if ip and ip not in bf_ip_set and classify_ip(ip) == "external":
            stealth_external.append(ip)
    stealth_external = list(dict.fromkeys(stealth_external))

    if stealth_external:
        b_score += 5
        b_triggers.append(
            f"低噪入侵者(成功但不在失败列表): {len(stealth_external)}个"
        )
        if len(stealth_external) >= 3:
            b_score += 5
            b_triggers.append(
                f"低噪入侵者≥3: {len(stealth_external)}个"
            )

    # 外部 IP 成功登录数
    external_success_ips = set()
    for s in ssh_successes:
        ip = s.get("ip", "")
        if ip and classify_ip(ip) == "external":
            external_success_ips.add(ip)
    if len(external_success_ips) >= 3:
        b_score += 5
        b_triggers.append(
            f"外部IP成功登录≥3: {len(external_success_ips)}个"
        )

    # publickey + password 双方式成功登录（同一外部 IP）→ 额外信号
    ext_success_methods: dict[str, set[str]] = defaultdict(set)
    for s in ssh_successes:
        ip = s.get("ip", "")
        method = s.get("method", "")
        if ip and classify_ip(ip) == "external":
            ext_success_methods[ip].add(method)
    multi_method_ips = [
        ip for ip, methods in ext_success_methods.items() if len(methods) >= 2
    ]
    if multi_method_ips:
        b_score += 5
        b_triggers.append(
            f"外部IP多认证方式成功: {len(multi_method_ips)}个"
        )

    # ── 维度 C: 网络连接可疑度 (0-20) ──
    # 基于 SSH 登录数据（brute_force/ssh_successes）推断网络层威胁，
    # 所有提供 SSH 日志的场景（linux / linux_log_folder）均可评分。
    c_score = 0
    c_triggers: list[str] = []

    if len(external_success_ips) >= 5:
        c_score += 10
        c_triggers.append(
            f"外部成功登录IP≥5: {len(external_success_ips)}个"
        )
    elif len(external_success_ips) >= 2:
        c_score += 5
        c_triggers.append(
            f"外部成功登录IP≥2: {len(external_success_ips)}个"
        )

    if len(attack_ips) >= 20:
        c_score += 5
        c_triggers.append(f"暴力破解源IP≥20: {len(attack_ips)}个")

    total_attempts = brute_force.get("total_attempts", 0)
    if total_attempts >= 1000:
        c_score += 5
        c_triggers.append(f"暴力破解尝试≥1000: {total_attempts}次")

    # 攻击链连贯性: 暴力破解 + 成功登录同时存在 → 攻击者可能已突破
    if has_external_bf and len(external_success_ips) >= 1:
        c_score += 5
        c_triggers.append("暴力破解+外部成功登录并存")

    # ── 维度 D: 持久化指标 (0-20) ──
    # 当 persistence_vectors 为空时（如 linux_log_folder），自动为 0
    d_score = 0
    d_triggers: list[str] = []

    if persistence_vectors:
        # 按类型分组
        type_counts: dict[str, int] = defaultdict(int)
        for v in persistence_vectors:
            t = v.get("type", "unknown")
            type_counts[t] += 1

        # 防御性检查: 发现未识别的持久化类型时记录警告
        _KNOWN_PERSIST_TYPES = {
            PERSIST_CRONTAB, PERSIST_SYSTEMD, PERSIST_PROFILE,
            PERSIST_AUTHKEY, PERSIST_INITD, PERSIST_RCLOCAL,
            "unknown",
        }
        unknown_types = set(type_counts.keys()) - _KNOWN_PERSIST_TYPES
        if unknown_types:
            print(
                f"[WARN] risk_score: 未识别的持久化类型 {unknown_types}"
                " — 这些向量未被评分",
                file=sys.stderr,
            )

        cron_count = type_counts.get(PERSIST_CRONTAB, 0)
        systemd_count = type_counts.get(PERSIST_SYSTEMD, 0)
        initd_count = type_counts.get(PERSIST_INITD, 0)
        rclocal_count = type_counts.get(PERSIST_RCLOCAL, 0)
        shell_profile_count = type_counts.get(PERSIST_PROFILE, 0)
        auth_keys_count = type_counts.get(PERSIST_AUTHKEY, 0)

        if cron_count >= 1 or systemd_count >= 1 or initd_count >= 1 or rclocal_count >= 1:
            d_score += 10
            parts = []
            if cron_count:
                parts.append(f"crontab:{cron_count}")
            if systemd_count:
                parts.append(f"systemd:{systemd_count}")
            if initd_count:
                parts.append(f"init.d:{initd_count}")
            if rclocal_count:
                parts.append(f"rc.local:{rclocal_count}")
            d_triggers.append(f"持久化向量: {', '.join(parts)}")

        if shell_profile_count >= 1:
            d_score += 5
            d_triggers.append(f"shell_profile恶意修改: {shell_profile_count}处")

        if auth_keys_count >= 1:
            d_score += 5
            d_triggers.append(f"SSH authorized_keys: {auth_keys_count}条")

    # ── 维度 E: 勒索/破坏指标 (0-20) ──
    # Linux 暂无 USN 等数据源，保留结构待扩展
    e_score = 0
    e_triggers: list[str] = []

    # ── 动态分值汇总 ──
    raw_max = 20
    dimensions_raw = [
        ("A", "暴力破解严重度", a_score, a_triggers, True),
        ("B", "异常登录指标", b_score, b_triggers, True),
        ("C", "网络连接可疑度", c_score, c_triggers, True),
        ("D", "持久化指标", d_score, d_triggers, bool(persistence_vectors)),
        ("E", "勒索/破坏指标(暂无数据源)", e_score, e_triggers, False),
    ]

    # 活跃维度: 有数据源的维度
    active_dims = [(d_id, name, score, triggers)
                   for d_id, name, score, triggers, has_source in dimensions_raw
                   if has_source]

    # 各活跃维度的得分率
    ratios = [min(score / raw_max, 1.0) for _, _, score, _ in active_dims]

    # 动态加权: 得分率平方加权平均
    weights = [r ** 2 for r in ratios]
    total_weight = sum(weights)

    if total_weight > 0:
        weighted_score = sum(w * r for w, r in zip(weights, ratios))
        raw_total = round(weighted_score / total_weight * 100)
    else:
        raw_total = 0

    # 构建维度输出
    dimension_list = []
    for d_id, name, score, triggers, has_source in dimensions_raw:
        if has_source and total_weight > 0:
            ratio = min(score / raw_max, 1.0)
            w = ratio ** 2
            allocated = round(w * ratio / total_weight * 100)
        else:
            allocated = 0
        dimension_list.append({
            "id": d_id,
            "name": name,
            "max": raw_max if has_source else 0,
            "score": score,
            "allocated": allocated,
            "triggers": triggers,
        })

    # 压倒性规则
    override_rules = []
    final_score = raw_total

    ab_sum = a_score + b_score
    rule_ab = {
        "rule": "A+B≥25(原始) → 下限80",
        "applied": ab_sum >= 25,
        "floor": 80,
    }
    override_rules.append(rule_ab)
    if rule_ab["applied"] and final_score < 80:
        final_score = 80

    rule_d = {
        "rule": "D=20(满分) → 下限80",
        "applied": d_score >= 20,
        "floor": 80,
    }
    override_rules.append(rule_d)
    if rule_d["applied"] and final_score < 80:
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
        "dimensions": dimension_list,
        "raw_total": raw_total,
        "override_rules": override_rules,
        "final_score": final_score,
        "risk_level": risk_level,
        "risk_label": risk_label,
    }
