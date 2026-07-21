#!/usr/bin/env python3
"""
fix_detector — 检测 PR diff 中"被本次变更修复的 Sink 位置"。

产出 diff-fixes.json，供 merge_findings.py 在 merge-scan 阶段过滤
"已被本次 diff 修复的 finding"，避免把修复型变更误报为风险。

触发方式: commands/diff.md 阶段 1 探索末尾、agents/bg-scan.md 步骤 1.2
输入: --batch-dir / --project-path / [--commit | --mode | --base+--head]
输出: {batch_dir}/diff-fixes.json

退出码:
  0 - 成功（无论是否检测到修复）
  1 - 参数错误
  2 - git diff 执行失败
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

# diff 中的一行变更：(file_path, line_no, content)
# 对 removed_lines 用旧行号，对 added_lines 用新行号
DiffLine = Tuple[str, int, str]

# removed 行的扩展信息，携带所属 hunk 的函数上下文与新文件行号区间。
# newRangeStart/newRangeEnd 为该 hunk 在 **新文件** 中的行号区间（与扫描
# finding 同基准），用于 merge 端"区间兜底匹配"消除新旧行号漂移。
# 纯删除 hunk（无 + 行）时区间为 (new_line, new_line-1)（空区间），
# 兜底匹配自动失效，退化到旧 ±容差逻辑，不引入误杀。
# 结构：(file_path, old_line, content, func_ctx, new_range_start, new_range_end)
RemovedLine = Tuple[str, int, str, str, int, int]

# ---------------------------------------------------------------------------
# diff hunk 解析
# ---------------------------------------------------------------------------

# diff --git a/path b/path  → 取 b/path
_DIFF_GIT_HEADER_RE = re.compile(r'^diff --git a/(.+?) b/(.+)$')
# --- a/path  或  --- /dev/null
_OLD_FILE_RE = re.compile(r'^--- (?:a/(.+)|/dev/null)$')
# +++ b/path  或  +++ /dev/null
_NEW_FILE_RE = re.compile(r'^\+\+\+ (?:b/(.+)|/dev/null)$')
# @@ -l1,n1 +l2,n2 @@ [func context]  （n1/n2 可选，默认 1；尾部函数上下文可选）
_HUNK_HEADER_RE = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:\s?(.*))?$')


def parse_diff_hunks(diff_text: str) -> Tuple[List[RemovedLine], List[DiffLine]]:
    """解析 `git diff --unified=0` 输出，返回 (removed_lines, added_lines)。

    - removed_lines 用旧行号（- 行在旧文件中的行号），并额外携带所属 hunk 的
      函数上下文（@@ 尾部文本）与该 hunk 在 **新文件** 中的行号区间
      (new_range_start, new_range_end)，用于 merge 端区间兜底匹配。
    - added_lines 用新行号（+ 行在新文件中的行号）
    - 上下文行（空格开头）不收集，但会推进行号计数器
    - \\ No newline at end of file 标记忽略
    - 纯重命名（无 +/- 内容）返回两个空列表
    """
    removed: List[RemovedLine] = []
    added: List[DiffLine] = []

    current_file: str = ""
    old_line = 0
    new_line = 0
    in_hunk = False

    # 当前 hunk 的元信息，用于在 hunk 结束时回填新行号区间
    hunk_func_ctx: str = ""
    hunk_new_start = 0
    pending_removed: List[Tuple[str, int, str]] = []

    def flush_hunk() -> None:
        """把当前 hunk 缓冲的 removed 行按最终新行号区间回填到 removed。"""
        if not pending_removed:
            return
        # new_line 此时指向 hunk 之后的下一行，故区间末尾为 new_line - 1；
        # 纯删除 hunk（无 +/空格行）时 new_line 未推进，区间为空 → 兜底失效。
        new_range_start = hunk_new_start
        new_range_end = new_line - 1
        for fp, oln, cont in pending_removed:
            removed.append((fp, oln, cont, hunk_func_ctx, new_range_start, new_range_end))
        pending_removed.clear()

    for raw in diff_text.splitlines():
        if not raw:
            # hunk 内的空行：git diff --unified=0 不会在 hunk 内产生空行
            # （所有行都有前缀字符）。遇到空行视为分隔，跳过。
            flush_hunk()
            in_hunk = False
            continue

        # diff --git a/x b/x
        m = _DIFF_GIT_HEADER_RE.match(raw)
        if m:
            flush_hunk()
            current_file = m.group(2)
            in_hunk = False
            continue

        # --- a/x  或  --- /dev/null
        m = _OLD_FILE_RE.match(raw)
        if m:
            # /dev/null 时 group(1) 为 None，不改 current_file（保持 b/ 路径）
            if m.group(1) is not None and current_file == "":
                # 仅当 diff --git 头未出现时才用 --- 路径（兜底）
                current_file = m.group(1)
            in_hunk = False
            continue

        # +++ b/x  或  +++ /dev/null
        m = _NEW_FILE_RE.match(raw)
        if m:
            if m.group(1) is not None:
                current_file = m.group(1)
            in_hunk = False
            continue

        # @@ -l1,n1 +l2,n2 @@ [func ctx]
        m = _HUNK_HEADER_RE.match(raw)
        if m:
            flush_hunk()
            old_line = int(m.group(1))
            new_line = int(m.group(3))
            hunk_new_start = new_line
            hunk_func_ctx = (m.group(5) or "").strip()
            in_hunk = True
            continue

        if not in_hunk:
            continue

        prefix = raw[0]
        rest = raw[1:]

        if prefix == '-':
            pending_removed.append((current_file, old_line, rest))
            old_line += 1
        elif prefix == '+':
            added.append((current_file, new_line, rest))
            new_line += 1
        elif prefix == ' ':
            old_line += 1
            new_line += 1
        elif prefix == '\\':
            # \ No newline at end of file — 忽略
            pass
        # 其他前缀（如 index 行）忽略

    flush_hunk()
    return removed, added


# ---------------------------------------------------------------------------
# 修复检测
# ---------------------------------------------------------------------------

# 内置 Sink 模式（fallback，当 sinks 表为空或检测 - 行用）
DEFAULT_SINK_PATTERNS: List[str] = [
    r"\.execute\s*\(",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"Runtime\.getRuntime\(\)\.exec",
    r"ProcessBuilder\s*\(",
    r"cursor\.execute\s*\(",
    r"db\.query\s*\(",
    r"\$\{.*\}",          # MyBatis ${} 拼接
    r"innerHTML\s*=",
    r"dangerouslySetInnerHTML",
    r"readObject\s*\(",   # 反序列化
    r"pickle\.loads?\s*\(",
    r"YAML\.load\s*\(",
    r"new\s+Function\s*\(",
    r"vm\.runInContext\s*\(",
]

# 内置防御模式（fallback，当 defenses 表为空用）
DEFAULT_DEFENSE_PATTERNS: List[str] = [
    r"PreparedStatement",
    r"\?\s*\)",            # 参数化占位符
    r"#\{",                # MyBatis #{} 参数化
    r"%s",                 # Python 格式化参数
    r"\.escape\s*\(",
    r"\.sanitize\s*\(",
    r"\.validate\s*\(",
    r"allowList",
    r"allowlist",
    r"AssumeRole",
    r"sessionToken",
    r"x-cos-security-token",
    r"Security\.checkOs",
    r"escapeHtml",
    r"encode\s*\(",
]

# 全局防御模式（fallback，当 defenses 表无 scope=global 记录用）。
# 这类防御一旦新增即覆盖同文件全局（框架级过滤/拦截/切面/中间件），
# 不需要贴着 Sink，故不受 DEFENSE_PROXIMITY_LINES 限制。
# 依据 pattern_grep.py 的 global-filter 组（scope=global）。
GLOBAL_DEFENSE_PATTERNS: List[str] = [
    "OncePerRequestFilter",
    "SecurityFilterChain",
    "addInterceptor",
    "@ControllerAdvice",
    "@ExceptionHandler",
    "@RestControllerAdvice",
    "implements Filter",
    "extends HandlerInterceptor",
    "HandlerInterceptorAdapter",
    "@Aspect",
    "@Around",
    "@Before",
    "app.use(",         # Express / Koa 中间件
    "middleware",
    "FilterRegistrationBean",
]

# 防御新增场景下 Sink 行号匹配容差
DEFENSE_PROXIMITY_LINES = 5


def _is_global_defense(pattern: str, scope: str) -> bool:
    """判断某防御是否为全局作用域。

    Args:
        pattern: 防御关键字
        scope: defenses 表的 scope 字段（global/package/file/method），可能为空

    Returns:
        True 当 scope=='global'，或 pattern 命中 GLOBAL_DEFENSE_PATTERNS 子串
    """
    if scope and scope.lower() == "global":
        return True
    return any(g in pattern for g in GLOBAL_DEFENSE_PATTERNS)


def _defense_matches(content: str, pattern: str) -> bool:
    """检查 diff 行是否包含某个防御模式。

    defenses 表的 name/type 字段可能是代码片段原文（含正则特殊字符、
    引号、截断语句），直接 re.search 会抛 re.PatternError。
    因此防御匹配用子串包含（in），不编译为正则。

    Args:
        content: diff + 行内容
        pattern: 防御关键字（来自 defenses 表或 DEFAULT_DEFENSE_PATTERNS）

    Returns:
        True if content contains pattern as substring
    """
    if not pattern:
        return False
    return pattern in content


def detect_fixes(
    removed_lines: List[RemovedLine],
    added_lines: List[DiffLine],
    sinks: List[dict],
    defense_patterns: List[Tuple[str, str]],
    sink_patterns: List[str],
) -> List[dict]:
    """从 +/- 行与 sinks 表检测被本次 diff 修复的 Sink 位置。

    Args:
        removed_lines: parse_diff_hunks 返回的 - 行列表
            (file, old_line, content, func_ctx, new_range_start, new_range_end)
        added_lines: parse_diff_hunks 返回的 + 行列表 (file, new_line, content)
        sinks: index_db sinks 表记录，字段 file_path/line/type
        defense_patterns: (防御关键字, scope) 元组列表，scope 为 global/method/…
        sink_patterns: Sink 关键字正则列表（用于检测 - 行移除的 Sink）

    Returns:
        fixed_sink_locations 列表，每项：
        {"filePath", "lineNumber", "fixReason", "sinkType", "defenseType",
         "enclosingContext", "newRangeStart", "newRangeEnd"}
        - sink_removed: lineNumber 为旧行号；newRangeStart/End 为该 hunk 新文件
          行号区间（供 merge 端区间兜底匹配，消除新旧行号漂移）
        - defense_added: lineNumber 为 sinks 表中的 post-diff 行号（±N 行局部）
        - global_defense_added: 同文件所有 Sink，全局防御新增触发（不受 ±N 限制）
    """
    fixes: List[dict] = []

    # 检测 A: sink_removed — - 行匹配 Sink 模式
    for file_path, line_no, content, func_ctx, new_start, new_end in removed_lines:
        for pattern in sink_patterns:
            if re.search(pattern, content):
                fixes.append({
                    "filePath": file_path,
                    "lineNumber": line_no,
                    "fixReason": "sink_removed",
                    "sinkType": "",
                    "defenseType": "",
                    "enclosingContext": func_ctx,
                    "newRangeStart": new_start,
                    "newRangeEnd": new_end,
                })
                break

    # 检测 B: defense_added — + 行匹配防御
    #   - 局部防御（scope=method/默认）：同文件 ±N 行内有 Sink 才标记
    #   - 全局防御（scope=global 或命中 GLOBAL_DEFENSE_PATTERNS）：同文件所有
    #     Sink 均标记，fixReason=global_defense_added，不受 ±N 限制
    for file_path, line_no, content in added_lines:
        matched_defense = ""
        matched_scope = ""
        for pattern, scope in defense_patterns:
            if _defense_matches(content, pattern):
                matched_defense = pattern
                matched_scope = scope
                break
        if not matched_defense:
            continue

        is_global = _is_global_defense(matched_defense, matched_scope)
        for sink in sinks:
            if sink.get("file_path") != file_path:
                continue
            sink_line = int(sink.get("line", 0) or 0)
            if sink_line <= 0:
                continue
            if is_global:
                fixes.append({
                    "filePath": file_path,
                    "lineNumber": sink_line,
                    "fixReason": "global_defense_added",
                    "sinkType": sink.get("type", ""),
                    "defenseType": matched_defense,
                    "enclosingContext": "",
                    "newRangeStart": 0,
                    "newRangeEnd": 0,
                })
            elif abs(sink_line - line_no) <= DEFENSE_PROXIMITY_LINES:
                fixes.append({
                    "filePath": file_path,
                    "lineNumber": sink_line,
                    "fixReason": "defense_added",
                    "sinkType": sink.get("type", ""),
                    "defenseType": matched_defense,
                    "enclosingContext": "",
                    "newRangeStart": 0,
                    "newRangeEnd": 0,
                })

    return fixes


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def derive_diff_range(commit: str, mode: str) -> dict:
    """由 commit/mode 推导 diff 范围 {base, head, mode, commit}。

    **全项目唯一真相源**：commands/diff.md 与 agents/bg-scan.md 的 batch-plan
    内联脚本均 import 本函数生成 diffRange，merge_findings.py 再据此与
    diff-fixes.json 做一致性校验。任何 diff 范围规则变更只需改这一处。

    解析规则（优先级 commit > mode > 默认 all）：
    - commit "abc..def"   → base="abc",   head="def"
    - commit "abc~1..def" → base="abc~1", head="def"
    - commit "abc"        → base="abc^",  head="abc"
    - mode "staged"       → base="",      head="--cached"
    - mode "unstaged"     → base="",      head=""
    - mode "all" / 默认   → base="",      head="HEAD"

    Args:
        commit: --commit 参数（可为空）
        mode: --mode 参数（staged/unstaged/all，可为空）

    Returns:
        {"base": str, "head": str, "mode": str, "commit": str}
    """
    commit = (commit or "").strip()
    mode = (mode or "").strip()
    if commit and ".." in commit:
        base, head = commit.split("..", 1)
    elif commit:
        base, head = commit + "^", commit
    elif mode == "staged":
        base, head = "", "--cached"
    elif mode == "unstaged":
        base, head = "", ""
    else:  # all / 默认
        base, head = "", "HEAD"
    return {"base": base, "head": head, "mode": mode, "commit": commit}


def build_git_diff_cmd(args) -> List[str]:
    """把 --commit/--mode/--base+--head 参数转成 git diff 命令参数列表。

    优先级：--base+--head > --commit > --mode > 默认(--mode all)。
    commit/mode 分支复用 derive_diff_range（唯一真相源），
    unstaged 的空 head 需还原为"无 revision 参数"。
    """
    diff_args = ["git", "diff", "--unified=0", "--diff-filter=ACMR"]

    if args.base and args.head:
        return diff_args + [args.base, args.head]

    rng = derive_diff_range(args.commit or "", args.mode or "")
    base, head = rng["base"], rng["head"]
    # base 非空 → 两点 diff（commit 区间 / abc^ abc）
    if base:
        return diff_args + [base, head]
    # base 为空：head 为 revision（HEAD/--cached）或空串（unstaged 工作区）
    if head:
        return diff_args + [head]
    return diff_args


def _run_git_diff(project_path: str, cmd: List[str]) -> str:
    """执行 git diff 命令，返回 stdout。失败时返回空字符串。"""
    try:
        result = subprocess.run(
            cmd, cwd=project_path, capture_output=True, text=True, timeout=60
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"[fix-detector] git diff 执行异常: {e}", file=sys.stderr)
        return ""
    if result.returncode != 0:
        print(f"[fix-detector] git diff 失败 (exit={result.returncode}): {result.stderr.strip()}",
              file=sys.stderr)
        return ""
    return result.stdout


def _query_index_db(batch_dir: str, sql: str) -> list:
    """通过 index_db.py query --sql 拉取数据。失败返回空列表。"""
    index_db = str(Path(__file__).resolve().parent / "index_db.py")
    try:
        result = subprocess.run(
            ["python3", index_db, "query",
             "--batch-dir", batch_dir, "--sql", sql],
            capture_output=True, text=True, timeout=30
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return []
    # index_db query 返回 {rows: [...], count: N} 或直接 list
    if isinstance(data, dict):
        return data.get("rows", []) or data.get("sinks", []) or data.get("defenses", [])
    if isinstance(data, list):
        return data
    return []


def _load_defense_patterns(batch_dir: str) -> List[Tuple[str, str]]:
    """从 defenses 表加载 (防御关键字, scope) 元组，空表时用 DEFAULT_DEFENSE_PATTERNS。

    scope 用于区分全局防御（global）与局部防御，供 detect_fixes 决定是否
    对同文件所有 Sink 生效。DEFAULT_DEFENSE_PATTERNS 均视为局部（scope=""）。
    """
    rows = _query_index_db(batch_dir, "SELECT DISTINCT type, name, scope FROM defenses")
    patterns: List[Tuple[str, str]] = []
    seen = set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        # 优先 name（更具体），其次 type
        name = r.get("name", "")
        type_ = r.get("type", "")
        scope = r.get("scope", "") or ""
        for v in (name, type_):
            if v and v not in seen:
                seen.add(v)
                patterns.append((v, scope))
    return patterns if patterns else [(p, "") for p in DEFAULT_DEFENSE_PATTERNS]


def _load_sinks(batch_dir: str) -> List[dict]:
    """从 sinks 表加载所有 Sink 记录。"""
    index_db = str(Path(__file__).resolve().parent / "index_db.py")
    try:
        result = subprocess.run(
            ["python3", index_db, "query",
             "--batch-dir", batch_dir, "--preset", "sinks-by-severity", "--limit", "9999"],
            capture_output=True, text=True, timeout=30
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return []
    return data.get("sinks", []) if isinstance(data, dict) else []


def _write_diff_fixes(batch_dir: str, fixes: List[dict], base: str, head: str,
                      mode: str = "", commit: str = "") -> Path:
    """写 diff-fixes.json 到 batch_dir，返回文件路径。

    mode/commit 一并写入，供 merge_findings 与 batch-plan.json 的 diffRange
    做一致性校验（避免 diff 范围注入不一致导致过滤对错位置）。
    """
    out_path = Path(batch_dir) / "diff-fixes.json"
    payload = {
        "generatedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "base": base,
        "head": head,
        "mode": mode,
        "commit": commit,
        "fixedSinkLocations": fixes,
        "totalFixed": len(fixes),
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def cmd_detect(args) -> int:
    """detect 子命令入口。返回退出码。"""
    git_cmd = build_git_diff_cmd(args)
    # base/head/mode/commit 统一由 derive_diff_range 推导（唯一真相源），
    # 与 batch-plan.json 的 diffRange 保持逐字段一致，供 merge 端一致性校验。
    if args.base and args.head:
        base, head = args.base, args.head
        mode, commit = args.mode or "", args.commit or ""
    else:
        rng = derive_diff_range(args.commit or "", args.mode or "")
        base, head, mode, commit = rng["base"], rng["head"], rng["mode"], rng["commit"]

    diff_text = _run_git_diff(args.project_path, git_cmd)
    if not diff_text:
        # 空变更或失败，写空结果
        out = _write_diff_fixes(args.batch_dir, [], base, head, mode, commit)
        print(f"[fix-detector] 无变更或 git diff 为空，写入空 diff-fixes.json: {out}")
        return 0

    removed, added = parse_diff_hunks(diff_text)
    if not removed and not added:
        out = _write_diff_fixes(args.batch_dir, [], base, head, mode, commit)
        print(f"[fix-detector] diff 无 +/- 内容（可能纯重命名），写入空 diff-fixes.json: {out}")
        return 0

    sinks = _load_sinks(args.batch_dir)
    defense_patterns = _load_defense_patterns(args.batch_dir)

    fixes = detect_fixes(removed, added, sinks, defense_patterns, DEFAULT_SINK_PATTERNS)

    out = _write_diff_fixes(args.batch_dir, fixes, base, head, mode, commit)
    print(f"[fix-detector] 检测到 {len(fixes)} 个被本次 diff 修复的 Sink 位置 → {out}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="fix_detector",
        description="检测 PR diff 中被本次变更修复的 Sink 位置",
    )
    parser.add_argument("command", choices=["detect"], help="子命令")
    parser.add_argument("--batch-dir", required=True)
    parser.add_argument("--project-path", required=True)
    parser.add_argument("--commit", default="", help="commit 参数（abc..def / abc / abc~1..def）")
    parser.add_argument("--mode", choices=["staged", "unstaged", "all"], default="")
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="")
    args = parser.parse_args()

    exit_code = cmd_detect(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
