#!/usr/bin/env python3

"""
Stop Hook: 检测本轮对话中是否执行了 git commit，
根据配置决定静默执行扫描或交互询问用户。

配置项（.codebuddy/security-scan/config.json > auto_scan）：
  - enabled:    开启/关闭 hook（默认 true）
  - scan_level: fast / light / deep（默认 fast）
  - blocking:   阻断式/非阻断（默认 false，即非阻断静默执行）
  - background: 后台执行（默认 true，仅 scan_level=fast 生效；非 fast 自动走前台）

检测策略：从 transcript 尾部读取有限字节（2 MB），在已读范围内定位最后一条
user 消息并正向扫描至文件末尾，识别成功的 git commit 操作。

触发方式: hooks/hooks.json > Stop Hook
输入: stdin JSON (包含 session_id, transcript_path, stop_hook_active, cwd 等)
输出: stdout JSON (控制 Agent 是否继续)

退出码:
  0 - 允许 Agent 正常停止
  2 - 阻止停止，reason 传递给 Agent
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

# 共享解析模块
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _git_parse import extract_git_op, COMMIT_HASH_RE

# ---------------------------------------------------------------------------
# 日志 (写入 stderr，不影响 stdout JSON 输出)
# ---------------------------------------------------------------------------
_PREFIX = "git-detector"

# transcript 尾部最大读取字节数（约 5000 行 × 300 字节 ≈ 1.5 MB）
# 限制 IO 和内存占用，适配 Stop Hook 的 10s 超时
MAX_TAIL_BYTES = 2 * 1024 * 1024  # 2 MB

# transcript 文件大小硬上限（200 MB）。
# 超过该上限直接拒绝，防止被诱导路径指向极大文件（如虚拟磁盘/日志）导致 stat/seek 阻塞 Hook。
MAX_TRANSCRIPT_FILE_SIZE = 200 * 1024 * 1024


def _log(msg: str) -> None:
    print(f"[{_PREFIX}] {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# 配置读取
# ---------------------------------------------------------------------------
_DEFAULT_CONFIG = {"enabled": True, "scan_level": "fast", "blocking": False, "background": True}
_VALID_SCAN_LEVELS = {"light", "deep", "fast"}


def _load_hook_config(cwd: str = "") -> dict:
    """从分层配置中读取 auto_scan 设置。

    配置合并规则: 项目级 > 用户级 > 默认值
    对每个字段做类型/范围校验，非法值回退到默认值并输出警告。

    Returns:
        dict: {"enabled": bool, "scan_level": str, "blocking": bool, "background": bool}
    """
    try:
        from _common import load_merged_config
    except ImportError as e:
        _log(f"_common 模块导入失败: {e}")
        return dict(_DEFAULT_CONFIG)
    except Exception as e:
        _log(f"_common 模块导入异常: {e}")
        return dict(_DEFAULT_CONFIG)

    try:
        merged = load_merged_config(cwd)
    except Exception as e:
        _log(f"配置文件加载失败: {e}")
        return dict(_DEFAULT_CONFIG)

    if not merged:
        return dict(_DEFAULT_CONFIG)

    auto_scan = merged.get("auto_scan", {})
    if not isinstance(auto_scan, dict):
        return dict(_DEFAULT_CONFIG)

    # --- 校验 enabled: 必须为 bool ---
    raw_enabled = auto_scan.get("enabled", _DEFAULT_CONFIG["enabled"])
    if not isinstance(raw_enabled, bool):
        _log(f"配置 auto_scan.enabled 类型非法({type(raw_enabled).__name__}: {raw_enabled!r})，回退默认值 True")
        raw_enabled = _DEFAULT_CONFIG["enabled"]

    # --- 校验 scan_level: 必须为 "fast"、"light" 或 "deep" ---
    raw_level = auto_scan.get("scan_level", _DEFAULT_CONFIG["scan_level"])
    if raw_level not in _VALID_SCAN_LEVELS:
        _log(f"配置 auto_scan.scan_level 值非法({raw_level!r})，回退默认值 {_DEFAULT_CONFIG['scan_level']!r}")
        raw_level = _DEFAULT_CONFIG["scan_level"]

    # --- 校验 blocking: 必须为 bool ---
    raw_blocking = auto_scan.get("blocking", _DEFAULT_CONFIG["blocking"])
    if not isinstance(raw_blocking, bool):
        _log(f"配置 auto_scan.blocking 类型非法({type(raw_blocking).__name__}: {raw_blocking!r})，回退默认值 False")
        raw_blocking = _DEFAULT_CONFIG["blocking"]

    # --- 校验 background: 必须为 bool ---
    raw_background = auto_scan.get("background", _DEFAULT_CONFIG["background"])
    if not isinstance(raw_background, bool):
        _log(f"配置 auto_scan.background 类型非法({type(raw_background).__name__}: {raw_background!r})，回退默认值 True")
        raw_background = _DEFAULT_CONFIG["background"]

    return {
        "enabled": raw_enabled,
        "scan_level": raw_level,
        "blocking": raw_blocking,
        "background": raw_background,
    }


# ---------------------------------------------------------------------------
# Transcript 扫描
#
# CodeBuddy Code transcript 使用两种格式（需要同时兼容）：
#   格式 A (Claude API 原始格式，嵌套在 content 数组中):
#     type: "tool_use",   name, id, input: {command: ...}
#     type: "tool_result", tool_use_id, content, is_error
#   格式 B (CodeBuddy Code 原生格式，每条独立一行):
#     type: "function_call",        name, callId, arguments (JSON string)
#     type: "function_call_result", name, callId, status, output: {text: ...}
# ---------------------------------------------------------------------------


def _extract_commands_from_entry(entry: dict):
    """从 transcript 条目中提取所有 Bash 命令信息（generator）。

    单个 entry 的 content[] 可能包含多个 tool_use/tool_result block
    （Claude API 并行工具调用），逐个 yield 而非只返回第一个。

    Yields:
        (entry_type, call_id, command, result_entry)
        entry_type: "call" | "result"
        result_entry: 供 _result_succeeded / _extract_result_text 使用的 dict
                      （格式 B 为 entry 本身，格式 A 嵌套时为单个 block）
    """
    etype = entry.get("type", "")

    # 格式 B: function_call / function_call_result（CodeBuddy Code 原生）
    # 格式 B 每条 entry 只有一个操作，无需循环
    if etype == "function_call" and entry.get("name") == "Bash":
        call_id = entry.get("callId", "")
        arguments = entry.get("arguments", "")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except (json.JSONDecodeError, ValueError):
                return
        command = arguments.get("command", "") if isinstance(arguments, dict) else ""
        yield "call", call_id, command, entry
        return

    if etype == "function_call_result" and entry.get("name") == "Bash":
        call_id = entry.get("callId", "")
        yield "result", call_id, "", entry
        return

    # 格式 A: tool_use / tool_result（Claude API 原始格式，可能嵌套在 content 中）
    # content[] 可包含多个 tool_use 或 tool_result block，全部处理
    blocks: list[dict] = []
    if etype in {"tool_use", "tool_result"}:
        blocks.append(entry)
    content = entry.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") in {"tool_use", "tool_result"}:
                blocks.append(block)

    for block in blocks:
        btype = block.get("type", "")
        if btype == "tool_use" and block.get("name") == "Bash":
            call_id = block.get("id") or block.get("tool_use_id", "")
            command = block.get("input", {}).get("command", "")
            yield "call", call_id, command, block
        elif btype == "tool_result":
            # 格式 A 的 tool_result 不含 name 字段，通过 tool_use_id
            # 关联到 pending_git_ops 中已确认的 Bash tool_use，无需单独过滤
            call_id = block.get("tool_use_id", "")
            yield "result", call_id, "", block


def _result_succeeded(entry: dict) -> bool:
    """判断工具执行结果是否成功（兼容两种 transcript 格式）。"""
    etype = entry.get("type", "")

    # 格式 B: function_call_result
    if etype == "function_call_result":
        status = entry.get("status", "")
        if status == "error":
            return False
        # 从 output.text 中检查 Exit Code
        output = entry.get("output", {})
        if isinstance(output, dict):
            text = output.get("text", "")
        elif isinstance(output, str):
            text = output
        else:
            text = ""
        if text and "Exit Code: " in text:
            for line in text.split("\n"):
                if line.startswith("Exit Code: "):
                    try:
                        return int(line.split(":", 1)[1].strip()) == 0
                    except (ValueError, IndexError):
                        pass
        return status != "error"  # 无明确失败标识时假定成功

    # 格式 A: tool_result
    if entry.get("is_error") is True:
        return False
    metadata = entry.get("metadata")
    if isinstance(metadata, dict) and metadata.get("exit_code") is not None:
        return metadata.get("exit_code") == 0
    if entry.get("exit_code") is not None:
        return entry.get("exit_code") == 0
    return True


def _extract_result_text(entry: dict) -> str:
    """从工具执行结果中提取文本内容（兼容两种 transcript 格式）。"""
    etype = entry.get("type", "")

    # 格式 B: function_call_result
    if etype == "function_call_result":
        output = entry.get("output", {})
        if isinstance(output, dict):
            return output.get("text", "")
        if isinstance(output, str):
            return output
        return ""

    # 格式 A: tool_result
    content = entry.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                parts.append(b.get("text", ""))
            elif isinstance(b, str):
                parts.append(b)
        return "\n".join(parts)
    return ""


def _is_user_turn_boundary(entry: dict) -> bool:
    """判断 entry 是否为用户发起的新一轮对话（轮次边界）。

    两种 transcript 格式中，用户消息均使用 role="user"：

    Claude API 格式：
    1. 用户输入: {"role": "user", "content": "请帮我..."}  → 轮次边界
    2. 工具结果: {"role": "user", "content": [{"type": "tool_result", ...}]}  → 非边界

    CodeBuddy Code 原生格式：
    3. 用户输入: {"role": "user", "content": "请帮我..."}  → 轮次边界
       （原生格式中 user 消息不嵌套 tool_result）

    若未来格式变更导致 role 字段不存在，_read_last_turn_lines 会退化为
    全量扫描（安全 fallback），不会漏检。
    """
    if entry.get("role") != "user":
        return False
    content = entry.get("content")
    # content 是 list 且包含 tool_result block → 工具结果，非边界
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                return False
    return True


def _read_last_turn_lines(path: Path) -> list[str]:
    """读取 transcript 文件尾部，定位最后一轮对话的所有行。

    IO 策略：用 seek 只读取文件尾部 MAX_TAIL_BYTES 字节（约 2 MB），
    而非全量 readlines()，控制内存和 IO 时间。

    搜索策略：在已读取的所有行中从后往前搜索轮次边界（无人为行数窗口），
    确保已读范围内的 commit 不会被遗漏。

    极端情况：当前轮 > 2 MB 时，更早的 commit 可能被截断。
    但对于 Stop Hook 10s 超时约束，这是合理的取舍。

    Returns:
        从最后一条用户消息（轮次边界）开始到文件末尾的行列表。
        如果找不到轮次边界，返回所有已读取的行。
    """
    try:
        file_size = path.stat().st_size
    except OSError as e:
        _log(f"获取文件大小失败: {e}")
        return []

    if file_size == 0:
        return []

    try:
        with open(path, "rb") as bf:
            if file_size > MAX_TAIL_BYTES:
                bf.seek(file_size - MAX_TAIL_BYTES)
                bf.readline()  # 丢弃被截断的首行（可能是半行/半字符）
            raw = bf.read()
        tail_lines = raw.decode("utf-8", errors="replace").splitlines(keepends=True)
    except Exception as e:
        _log(f"读取 transcript 失败: {e}")
        return []

    if not tail_lines:
        return []

    # 在所有已读行中从后往前搜索最后一条轮次边界
    # 优化：先用字符串匹配跳过明显不是 user 消息的行，减少 json.loads 调用
    last_user_idx = -1
    for i in range(len(tail_lines) - 1, -1, -1):
        line = tail_lines[i].strip()
        if not line or '"role"' not in line or '"user"' not in line:
            continue
        try:
            entry = json.loads(line)
            if _is_user_turn_boundary(entry):
                last_user_idx = i
                break
        except (json.JSONDecodeError, ValueError):
            continue

    if last_user_idx >= 0:
        return tail_lines[last_user_idx:]
    else:
        _log("已读范围内未找到用户消息，使用全部已读行")
        return tail_lines


def _scan_transcript(transcript_path: str) -> tuple[bool, str, str]:
    """扫描 transcript 文件，检测成功的 git commit 操作。

    兼容 CodeBuddy Code 原生格式 (function_call) 和 Claude API 格式 (tool_use)。

    Returns:
        (found, op_type, diff_args)
    """
    path = Path(transcript_path)
    if ".." in transcript_path:
        _log(f"拒绝可疑路径: {transcript_path}")
        return False, "", ""
    # 拒绝 symlink，防止经由符号链接指向敏感大文件
    try:
        if path.is_symlink():
            _log(f"拒绝符号链接 transcript: {transcript_path}")
            return False, "", ""
    except OSError as e:
        _log(f"transcript symlink 检测失败: {e}")
        return False, "", ""
    if not path.is_file():
        _log(f"transcript 文件不存在: {transcript_path}")
        return False, "", ""
    # 文件大小硬上限：防止极端大文件 stat/seek/read 卡住 Hook
    try:
        file_size = path.stat().st_size
    except OSError as e:
        _log(f"获取 transcript 文件大小失败: {e}")
        return False, "", ""
    if file_size > MAX_TRANSCRIPT_FILE_SIZE:
        _log(
            f"transcript 文件过大({file_size} 字节 > {MAX_TRANSCRIPT_FILE_SIZE})，"
            f"跳过避免阻塞 Hook"
        )
        return False, "", ""

    lines = _read_last_turn_lines(path)
    if not lines:
        return False, "", ""

    entries: list[dict] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    pending_git_ops: dict[str, str] = {}  # call_id -> git_op
    commit_detected = False
    collected_commit_hashes: list[str] = []

    for entry in entries:
        for entry_type, call_id, command, result_entry in _extract_commands_from_entry(entry):
            if entry_type == "call" and call_id:
                try:
                    git_op = extract_git_op(command)
                except Exception:
                    git_op = ""
                if git_op:
                    pending_git_ops[call_id] = git_op

            elif entry_type == "result" and call_id and call_id in pending_git_ops:
                git_op = pending_git_ops.pop(call_id)
                if _result_succeeded(result_entry) and git_op == "commit":
                    commit_detected = True
                    result_text = _extract_result_text(result_entry)
                    m = COMMIT_HASH_RE.search(result_text)
                    if m:
                        collected_commit_hashes.append(m.group(1))

    if not commit_detected:
        return False, "", ""

    # 构建 diff_args
    diff_args = "--commit HEAD"
    if collected_commit_hashes:
        if len(collected_commit_hashes) > 1:
            diff_args = f"--commit {collected_commit_hashes[0]}^..{collected_commit_hashes[-1]}"
        else:
            diff_args = f"--commit {collected_commit_hashes[0]}"

    return True, "commit", diff_args


# ---------------------------------------------------------------------------
# 输出构建
# ---------------------------------------------------------------------------
def _build_silent_output(git_op: str, diff_args: str, scan_level: str, background: bool = False) -> dict:
    """非阻断模式：直接指示 Agent 静默执行扫描，不询问用户。

    background=True 且 scan_level == "fast" 时追加 --background，让增量扫描在
    后台 Agent（bg-scan）中执行，不占用主对话上下文。后台模式当前仅支持 fast，
    其它扫描级别即使配置 background=True 也走前台（带说明）。
    """
    skill_name = "security-scan:diff"
    use_background = background and scan_level == "fast"
    bg_flag = " --background" if use_background else ""
    skill_args = f"{diff_args} --scan-level {scan_level} --auto{bg_flag}"
    lines = [
        f"Security-Scan 插件检测到本轮对话执行了 git {git_op}。",
        f"根据项目的 auto_scan 配置，",
        f"请对本次变更执行增量安全扫描。",
        "",
        f'调用方式: Skill(skill: "{skill_name}", args: "{skill_args}")',
    ]
    if use_background:
        lines.append("")
        lines.append("（后台模式：扫描将在独立 bg-scan Agent 中执行，完成后回流摘要，不占用当前对话。）")
    elif background and scan_level != "fast":
        lines.append("")
        lines.append(f"（注：auto_scan.background 已开启，但后台模式当前仅支持 fast；scan_level={scan_level} 走前台执行。）")
    # continue=False + exit code 2：Hook 框架以 exit code 2 判定"阻止停止"，
    # 将 reason 注入给 Agent 继续执行。continue 字段为框架保留字段。
    return {
        "continue": False,
        "reason": "\n".join(lines),
    }


def _build_blocking_output(git_op: str, diff_args: str, scan_level: str) -> dict:
    """阻断模式：指示 Agent 使用 AskUserQuestion 询问用户。

    scan_level 参数用于将配置的扫描模式标记为推荐选项（排在第一位）。
    """
    # 三个模式的固定描述文案
    _desc = {
        "fast": "极速扫描（Fast）— Light 的纪律化版本，并行 Read / 扫描验证合并",
        "light": "快速扫描（Light）— 基于 Grep 模式匹配的快速增量扫描",
        "deep": "深度扫描（Deep）— 多 Agent 并行 + 语义追踪的深度增量扫描",
    }
    # 根据配置的 scan_level 决定选项排序，推荐项排第一
    if scan_level in _VALID_SCAN_LEVELS:
        recommended = scan_level
    else:
        recommended = _DEFAULT_CONFIG["scan_level"]

    ordered_levels = [recommended] + [lv for lv in ("fast", "light", "deep") if lv != recommended]
    option_lines = []
    for idx, lv in enumerate(ordered_levels, start=1):
        suffix = "（推荐，当前配置）" if lv == recommended else ""
        option_lines.append(f"{idx}) {_desc[lv]}{suffix}；")
    option_lines.append(f"{len(ordered_levels) + 1}) 跳过 — 本次不执行安全扫描。")

    instruction = {
        "action": "ask_user_security_scan",
        "detected_op": git_op,
        "diff_command": f"/security-scan:diff {diff_args}",
        "recommended": recommended,
        "options": {
            "fast": f"/security-scan:diff {diff_args} --scan-level fast",
            "light": f"/security-scan:diff {diff_args} --scan-level light",
            "deep": f"/security-scan:diff {diff_args} --scan-level deep",
            "skip": None,
        },
    }

    lines = [
        f"[Security-Scan] 检测到本轮执行了 git {git_op} 操作。",
        "指令参数:",
        "```json",
        json.dumps(instruction, ensure_ascii=False, indent=2),
        "```",
        "",
        "请使用 AskUserQuestion 工具询问用户是否对本次变更执行增量安全扫描，提供以下选项：",
        *option_lines,
        "用户选择扫描后，执行上述 options 中对应的命令。用户选择跳过则正常结束。",
    ]

    return {
        "continue": False,
        "reason": "\n".join(lines),
    }


def _build_output(git_op: str, diff_args: str, config: dict) -> dict:
    """根据配置构建 Hook 输出。"""
    if config["blocking"]:
        return _build_blocking_output(git_op, diff_args, config["scan_level"])
    return _build_silent_output(
        git_op, diff_args, config["scan_level"], config.get("background", False)
    )


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        _log(f"无法解析 stdin JSON: {e}")
        sys.exit(0)

    # 防止无限循环: stop_hook_active=true 表示 Agent 已因本 Hook 继续过一次
    if hook_input.get("stop_hook_active", False):
        _log("stop_hook_active=true, 跳过检测避免循环")
        sys.exit(0)

    cwd = hook_input.get("cwd", "")

    # 读取配置
    config = _load_hook_config(cwd)
    if not config["enabled"]:
        _log("auto_scan 已禁用，跳过")
        sys.exit(0)

    _log(f"配置: enabled={config['enabled']}, scan_level={config['scan_level']}, blocking={config['blocking']}, background={config.get('background')}")

    transcript_path = hook_input.get("transcript_path", "")
    if not transcript_path:
        _log("无 transcript_path，跳过")
        sys.exit(0)

    found, git_op, diff_args = _scan_transcript(transcript_path)
    if not found:
        sys.exit(0)

    mode = "阻断询问" if config["blocking"] else "静默执行"
    _log(f"检测到 git {git_op}，diff 参数: {diff_args}，模式: {mode}")
    output = _build_output(git_op, diff_args, config)
    json.dump(output, sys.stdout, ensure_ascii=False)
    sys.exit(2)


if __name__ == "__main__":
    main()
