"""持久化检测器 (T1543 / T1546 / T1053)"""
from __future__ import annotations
import re


PERSISTENCE_PATTERNS = [
    # (pattern, ttp, name, sub_phase)
    (r"crontab\s+-e", "T1053.003", "crontab 编辑", "cron"),
    (r"/etc/cron\.", "T1053.003", "cron 目录写入", "cron"),
    (r"authorized_keys", "T1098.004", "SSH 公钥植入", "ssh_backdoor"),
    (r"systemd.*service", "T1543.002", "systemd 服务植入", "systemd"),
    (r"/etc/systemd/system", "T1543.002", "systemd 目录写入", "systemd"),
    (r"/etc/rc\.local", "T1546", "rc.local 植入", "init"),
    (r"\.bashrc", "T1546", "bashrc 植入", "shell_init"),
    (r"\.bash_profile", "T1546", "bash_profile 植入", "shell_init"),
    (r"\.zshrc", "T1546", "zshrc 植入", "shell_init"),
    (r"chmod\s+\+s", "T1548.001", "SUID 设置", "suid"),
    (r"chmod\s+4[0-7]{3}", "T1548.001", "SUID 权限", "suid"),
    (r"ld.so.preload", "T1574.006", "动态链接库劫持", "ld_preload"),
    (r"/etc/ld.so.preload", "T1574.006", "动态链接库配置", "ld_preload"),
    (r"at\s+", "T1053.002", "at 计划任务", "at"),
]


def detect_persistence(parsed: dict, raw_kv: dict) -> dict | None:
    """检测持久化行为

    Args:
        parsed: L0 输出的 parsed dict
        raw_kv: L0 输出的 _raw_kv (完整 kv 兜底)

    Returns:
        None (未命中) 或 dict
    """
    # 检查 cmd, process_path, process, 各种写入路径
    fields_to_check = [
        parsed.get("cmd") or "",
        parsed.get("process_path") or "",
        parsed.get("process") or "",
        raw_kv.get("cmd", ""),
        raw_kv.get("file_path", ""),
        raw_kv.get("target_path", ""),
    ]
    full_text = " ".join(f for f in fields_to_check if f)
    if not full_text:
        return None

    hits = []
    for pattern, ttp, name, sub_phase in PERSISTENCE_PATTERNS:
        if re.search(pattern, full_text, re.IGNORECASE):
            hits.append({"pattern": pattern, "ttp": ttp, "name": name, "sub_phase": sub_phase})

    if not hits:
        return None

    return {
        "threat_type": "持久化 (Persistence)",
        "ttp": hits[0]["ttp"],
        "ttp_name": hits[0]["name"],
        "confidence": 0.85,
        "reasons": [
            f"字段命中持久化模式: '{full_text[:200]}'",
        ] + [f"- {h['name']} (TTP: {h['ttp']})" for h in hits],
        "signals": {
            "matched": [h["name"] for h in hits],
            "sub_phases": list({h["sub_phase"] for h in hits}),
            "host_ip": parsed.get("host_ip"),
            "user": parsed.get("user"),
            "process": parsed.get("process"),
        },
        "kill_chain_phase": "Persistence",
        "correlation_hints": {
            "pivot_keys": ["host_ip", "user"],
            "time_window_min": 1440,  # 持久化排查需要拉较长时间窗
            "rationale": "持久化通常在入侵后写入, 关联同一 host 的早期入侵告警",
        },
    }
