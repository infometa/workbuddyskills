#!/usr/bin/env python3
"""
review_utils.py — expert-reviewer 通用工具

提供 ai_action 构造、JSON 输出、版本解析和安全文件读取工具。
"""

import json
import re
import sys
from pathlib import Path

# Windows 终端 UTF-8 兼容
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass






# ── ai_action 构造（expert 专用类型） ─────────────────

EXPERT_ACTION_TYPES = {
    "team-rule-check",
    "member-rule-check",
    "prompt-completeness",
    "display-text-quality",
    "platform-claim-check",
    "category-validity",
    "agent-name-semantics",
    "tools-field-completeness",
    "finance-compliance",
    "security-hygiene-review",
    "dependency-guide-check",
    "deep-quality-review",
}

PRIORITIES = {"required", "recommended", "optional"}


def build_ai_action(
    action_id: str,
    action_type: str,
    instruction: str,
    *,
    priority: str = "required",
    target_file: str = "",
    reference_doc: str = "",
    context: dict | None = None,
) -> dict:
    """构造统一格式的 ai_action 条目。

    Args:
        action_id: 唯一 ID（如 AI-01）
        action_type: 必须 ∈ EXPERT_ACTION_TYPES
        instruction: 给 LLM 的执行指令（中文）
        priority: required / recommended / optional
        target_file: 相对 expert_dir 的目标文件路径
        reference_doc: 规范出处（如 "CODEBUDDY.md §4.4"）
        context: 辅助上下文 dict
    """
    if action_type not in EXPERT_ACTION_TYPES:
        raise ValueError(f"未知 action_type: {action_type}")
    if priority not in PRIORITIES:
        raise ValueError(f"未知 priority: {priority}")

    entry: dict = {
        "id": action_id,
        "action_type": action_type,
        "priority": priority,
        "instruction": instruction,
    }
    if target_file:
        entry["target_file"] = target_file
    if reference_doc:
        entry["reference_doc"] = reference_doc
    if context:
        entry["context"] = context
    return entry


# ── 结构性 finding 构造 ───────────────────────────────

FINDING_SEVERITIES = {"blocker", "suggestion", "info"}


def build_finding(
    finding_id: str,
    severity: str,
    finding_type: str,
    title: str,
    *,
    evidence: str = "",
    target_file: str = "",
    reference_doc: str = "",
    fix_hint: str = "",
    auto_fixable: bool = False,
) -> dict:
    """构造一个 structure_findings 条目。"""
    if severity not in FINDING_SEVERITIES:
        raise ValueError(f"未知 severity: {severity}")
    return {
        "id": finding_id,
        "severity": severity,
        "type": finding_type,
        "title": title,
        "evidence": evidence,
        "target_file": target_file,
        "reference_doc": reference_doc,
        "fix_hint": fix_hint,
        "auto_fixable": auto_fixable,
    }


# ── 版本解析 ──────────────────────────────────────────

def parse_version_tuple(text: str) -> tuple[int, ...] | None:
    """解析 semver 为可比较元组，仅接受纯数字版本号。"""
    text = (text or "").strip().strip("\"'")
    m = re.match(r"^(\d+(?:\.\d+)*)$", text)
    if not m:
        return None
    parts = [int(x) for x in m.group(1).split(".")]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)






# ── 文件 I/O 工具 ─────────────────────────────────────


def ensure_dir(path: Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def read_text_safe(path: Path) -> str:
    """以 utf-8-sig 读取文本（自动剥离 BOM），失败时尝试 GBK。"""
    p = Path(path)
    try:
        return p.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            return p.read_text(encoding="gbk")
        except Exception:
            return p.read_bytes().decode("utf-8", errors="replace")


def read_json_safe(path: Path) -> dict | list | None:
    """安全读取 JSON。返回 None 表示文件不存在或解析失败。"""
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return None


def write_output_file(output_path: str | None, data, stdout_summary: str = "") -> None:
    """统一输出处理：指定 --output-file 时写文件，否则打印 stdout。

    解决 PowerShell CLIXML/编码截断问题。
    """
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json_str, encoding="utf-8")
        if stdout_summary:
            print(stdout_summary)
        else:
            print(f"[OK] 结果已写入 {output_path}")
    else:
        print(json_str)


def print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))






