"""反弹 Shell 检测器 (T1059.004)"""
from __future__ import annotations
import re


# 反弹 Shell 命令模式
REVERSE_SHELL_PATTERNS = [
    (r"bash\s+-i\s+>&\s*/dev/tcp/", "T1059.004", "bash /dev/tcp"),
    (r"/dev/tcp/[^\s'\"]+", "T1059.004", "bash /dev/tcp"),
    (r"nc\s+-e\s+/bin/(ba)?sh", "T1059.004", "netcat -e"),
    (r"nc\s+-c\s+/bin/(ba)?sh", "T1059.004", "netcat -c"),
    (r"ncat\s+-e", "T1059.004", "ncat -e"),
    (r"python[23]?\s+-c\s+['\"].*socket.*connect", "T1059.006", "python socket"),
    (r"python[23]?\s+-c\s+['\"].*subprocess.*Popen", "T1059.006", "python subprocess"),
    (r"perl\s+-e\s+['\"].*socket", "T1059", "perl socket"),
    (r"curl\s+[^\s]+\s*\|\s*bash", "T1059.004", "curl | bash"),
    (r"wget\s+[^\s]+\s*\|\s*bash", "T1059.004", "wget | bash"),
    (r"curl\s+[^\s]+\s*\|\s*sh", "T1059.004", "curl | sh"),
    (r"wget\s+[^\s]+\s*\|\s*sh", "T1059.004", "wget | sh"),
    (r"php\s+-r\s+['\"].*fsockopen", "T1059", "php fsockopen"),
    (r"php\s+-r\s+['\"].*exec", "T1059", "php exec"),
    (r"ruby\s+-rsocket", "T1059", "ruby socket"),
    (r"exec\s+\d+<>.*tcp", "T1059.004", "bash exec"),
    (r"mkfifo\s+/tmp/", "T1059.004", "mkfifo"),
    (r"telnet\s+[^\s]+\s+\d+", "T1059", "telnet"),
    (r"bash\s+-c\s+['\"]?bash\s+-i", "T1059.004", "嵌套 bash -i"),
]


def detect_reverse_shell(parsed: dict, raw_kv: dict) -> dict | None:
    """检测反弹 Shell 行为

    Args:
        parsed: L0 输出的 parsed dict
        raw_kv: L0 输出的 _raw_kv (完整 kv 兜底)

    Returns:
        None (未命中) 或 dict (含 threat_type / confidence / signals)
    """
    cmd = parsed.get("cmd") or raw_kv.get("cmd") or ""
    if not cmd:
        return None

    hits = []
    for pattern, ttp, name in REVERSE_SHELL_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            hits.append((pattern, ttp, name))

    if not hits:
        return None

    # 高置信度: 命中任何反弹 Shell 模式都视为高危
    confidence = 0.95 if len(hits) >= 1 else 0.0

    return {
        "threat_type": "反弹 Shell (Reverse Shell)",
        "ttp": hits[0][1],  # 取首个命中的 TTP
        "ttp_name": hits[0][2],
        "confidence": confidence,
        "reasons": (
            [f"cmd 命中反弹 Shell 模式: '{cmd[:100]}'"]
            + [f"模式: {h[2]}" for h in hits]
        ),
        "signals": {
            "cmd": cmd,
            "process": parsed.get("process"),
            "process_path": parsed.get("process_path"),
            "user": parsed.get("user"),
            "matched_patterns": [h[2] for h in hits],
        },
        "kill_chain_phase": "Execution",
        "correlation_hints": {
            "pivot_keys": ["host_ip", "dst_ip", "process_path"],
            "time_window_min": 60,
            "rationale": "反弹 Shell 通常伴随外联, 应关联御界 C2 / 数据外传告警",
        },
    }
