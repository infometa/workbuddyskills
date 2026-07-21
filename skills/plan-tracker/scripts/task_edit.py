#!/usr/bin/env python3
"""
task_edit.py - 手动录入/编辑任务（plan-tracker P2 能力）

用法：
  # 1) 临时新增今日任务（最高频）
  python3 task_edit.py add --title "背 30 个核心词" --duration 20 --category vocabulary
  python3 task_edit.py add --title "晚 8 点小测" --date 2026-05-09 --duration 25

  # 2) 删除今日某任务（用户："今天的生词复习不做了"）
  python3 task_edit.py remove --id t-101
  python3 task_edit.py remove --title "生词复习"      # 模糊匹配，命中 1 条才执行

  # 3) 任务延后到指定日期（用户："今天的阅读 P3 挪到明天"）
  python3 task_edit.py postpone --id t-101 --to 2026-05-09
  python3 task_edit.py postpone --title "阅读 P3" --to tomorrow

  # 4) 任意动作叠加 --dry-run，仅预览改动，绝不写盘
  python3 task_edit.py add --title "背单词" --duration 20 --dry-run

依赖：
  - Python 3.8+，仅标准库
  - 零网络、零三方包；所有改动只落到 <cwd>/plan-tracker/plans/<plan>/plan.json

设计准则（与 SKILL.md NEVER 对齐）：
  - NEVER 1（不绑架）：编辑只动 plan.json，绝不动 checkin-log.json / streak.json
  - NEVER 2（低摩擦）：单条命令完成；title 必填，其它字段都有合理默认
  - NEVER 3（不串）：本脚本不做 persona 化文案；只做"操作回执 + 改动摘要"
  - NEVER 5（零网络/零遥测）
  - NEVER 6（无 plan 不空聊）：找不到 active plan → 引导到 plan-tracker，exit 1

护栏（关键）：
  - 已打卡的任务不允许被 remove / postpone，必须先撤销打卡（避免数据不一致）
  - postpone 目标日期必须在 plan 起止区间内（含 deadline）
  - 同日 add 不重复（按 title 去重，幂等）
  - 写盘走"先写临时文件再 rename"原子替换，避免半写状态

错误模式（exit code）：
  - 0  成功（含 dry-run）
  - 1  无 active plan
  - 2  参数缺失/非法（title 为空、duration < 1、--to 解析失败等）
  - 3  目标 task 不存在（按 id/title 都未找到）
  - 4  目标 title 模糊匹配命中 ≥ 2 条，要求用 --id 显式指定
  - 5  目标 task 已打卡，拒绝 remove/postpone
  - 6  postpone 目标日期超出 plan 范围
  - 7  写盘失败（IO 异常）
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _plan_utils import (  # noqa: E402
    DATA_DIR,
    load_user_config,
    resolve_start_date,
    resolve_end_date,
    regenerate_dashboard,
)

# DATA_DIR 由 _plan_utils 统一解析（兼容 GOAL_TRACKER_DATA_DIR + cwd）

# 合法 category（与 plan-tracker 统一；未在此列也允许，但会软警告）
KNOWN_CATEGORIES = {
    "listening", "reading", "writing", "speaking",
    "vocabulary", "grammar", "review", "practice",
    "lecture", "homework", "project", "other",
}

MAX_TITLE_LEN = 80
MAX_DURATION_MIN = 240  # 单任务上限 4h（防误填 600 让一天爆掉）


# ---------- 数据加载 ----------

def get_active_plan_path(plan_id: str = None) -> str:
    """返回 plan.json 路径（不读内容）。"""
    if plan_id:
        p = os.path.join(DATA_DIR, plan_id, "plan.json")
        return p if os.path.exists(p) else None

    cfg = load_user_config()
    pid = cfg.get("active_plan_id")
    if pid:
        p = os.path.join(DATA_DIR, pid, "plan.json")
        if os.path.exists(p):
            return p

    if not os.path.exists(DATA_DIR):
        return None
    for pid in sorted(os.listdir(DATA_DIR), reverse=True):
        p = os.path.join(DATA_DIR, pid, "plan.json")
        if os.path.exists(p):
            return p
    return None


def load_plan(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_checkin_task_ids(plan_id: str) -> set:
    """返回 checkin-log 里所有出现过的 task_id 集合（用于 remove/postpone 护栏）。"""
    log_path = os.path.join(DATA_DIR, plan_id, "checkin-log.json")
    if not os.path.exists(log_path):
        return set()
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            log = json.load(f)
    except (json.JSONDecodeError, OSError):
        return set()
    ids = set()
    for c in log.get("checkins", []):
        for tid in c.get("task_ids", []):
            ids.add(tid)
    return ids


def atomic_dump(path: str, plan: dict) -> None:
    """原子写：tmp 文件 + os.replace，避免半写。"""
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".plan-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------- 日期解析 ----------

def parse_date_arg(s: str) -> date:
    """解析 --date / --to 参数：YYYY-MM-DD / today / tomorrow / +N。失败 → ValueError。"""
    if not s:
        return date.today()
    s = s.strip().lower()
    if s in ("today", "今天"):
        return date.today()
    if s in ("tomorrow", "明天"):
        return date.today() + timedelta(days=1)
    if s.startswith("+"):
        try:
            return date.today() + timedelta(days=int(s[1:]))
        except ValueError:
            raise ValueError(f"无法解析相对日期：{s}")
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"日期格式应为 YYYY-MM-DD / today / tomorrow / +N，得到：{s}")


# ---------- task 查找 ----------

def find_day_entry(plan: dict, target_date: date) -> dict:
    """找 daily_tasks 里 date == target_date 的那一项。没找到返回 None。"""
    target_str = target_date.isoformat()
    for day in plan.get("daily_tasks", []):
        if day.get("date") == target_str:
            return day
    return None


def find_task(plan: dict, task_id: str = None, title: str = None):
    """按 id 精确 / 按 title 模糊 查找 task。

    返回：(day_entry, task_entry, day_index_in_daily_tasks, task_index_in_day) 元组列表。
    支持模糊匹配命中多条 → 由调用方根据数量决定走哪条错误路径。
    """
    matches = []
    daily = plan.get("daily_tasks", [])
    for di, day in enumerate(daily):
        for ti, t in enumerate(day.get("tasks", [])):
            if task_id and t.get("id") == task_id:
                matches.append((day, t, di, ti))
            elif title and not task_id:
                tt = t.get("title", "")
                if title in tt or tt in title:
                    matches.append((day, t, di, ti))
    return matches


def gen_task_id(plan: dict) -> str:
    """生成不冲突的新 task id：t-9XXX 段（9 开头与 plan-tracker 自动生成的 t-NNN 段错开）。"""
    used = set()
    for day in plan.get("daily_tasks", []):
        for t in day.get("tasks", []):
            tid = t.get("id", "")
            used.add(tid)
    n = 9001
    while f"t-{n}" in used:
        n += 1
        if n > 9999:
            # 极端情况降级用毫秒戳
            return f"t-u{int(datetime.now().timestamp() * 1000) % 1000000}"
    return f"t-{n}"


# ---------- 三个动作 ----------

def do_add(plan: dict, args: argparse.Namespace) -> dict:
    """新增任务到指定日（默认今天）。返回 {action,...} 描述结构供回执打印。"""
    title = (args.title or "").strip()
    if not title:
        raise SystemExit(_err(2, "缺少 --title（任务标题不能为空）"))
    if len(title) > MAX_TITLE_LEN:
        title = title[:MAX_TITLE_LEN].rstrip() + "…"
        print(f"⚠️ title 超过 {MAX_TITLE_LEN} 字符，已截断", file=sys.stderr)

    duration = args.duration if args.duration is not None else 30
    if duration < 1 or duration > MAX_DURATION_MIN:
        raise SystemExit(_err(2, f"--duration 必须在 1~{MAX_DURATION_MIN} 之间，得到 {duration}"))

    category = (args.category or "other").strip().lower()
    if category not in KNOWN_CATEGORIES:
        print(f"⚠️ 未知 category「{category}」，已保留但建议从 {sorted(KNOWN_CATEGORIES)} 选", file=sys.stderr)

    try:
        target = parse_date_arg(args.date)
    except ValueError as e:
        raise SystemExit(_err(2, str(e)))

    # 越界软处理：允许超出 plan 范围（用户可能就是要在结束后再加一项）
    start = resolve_start_date(plan)
    end = resolve_end_date(plan, fallback=start)
    if not (start <= target <= end):
        print(f"⚠️ 目标日 {target} 超出 plan 范围 {start}~{end}，仍然写入（也会扩展 daily_tasks）", file=sys.stderr)

    # 找/造对应日条目
    day = find_day_entry(plan, target)
    created_day = False
    if not day:
        day = {"date": target.isoformat(), "tasks": []}
        plan.setdefault("daily_tasks", []).append(day)
        plan["daily_tasks"].sort(key=lambda d: d.get("date", ""))
        created_day = True

    # 同日同 title 幂等
    for t in day.get("tasks", []):
        if t.get("title", "").strip() == title:
            return {
                "action": "add",
                "status": "noop",
                "reason": "same-title-exists",
                "date": target.isoformat(),
                "task": t,
            }

    new_task = {
        "id": gen_task_id(plan),
        "title": title,
        "duration_min": duration,
        "category": category,
        "checkable": True,
        "manual": True,  # 标记为手动录入，便于将来在 stats 里区分
    }
    if args.note:
        new_task["note"] = args.note.strip()[:200]

    day["tasks"].append(new_task)

    return {
        "action": "add",
        "status": "ok",
        "date": target.isoformat(),
        "created_day": created_day,
        "task": new_task,
    }


def do_remove(plan: dict, args: argparse.Namespace, plan_id: str) -> dict:
    """删除任务。已打卡的禁止删，必须先撤销打卡。"""
    if not args.id and not args.title:
        raise SystemExit(_err(2, "remove 必须提供 --id 或 --title 之一"))

    matches = find_task(plan, task_id=args.id, title=args.title)
    if not matches:
        raise SystemExit(_err(3, f"未找到任务（id={args.id}, title={args.title}）"))
    if len(matches) > 1 and not args.id:
        titles = [t.get("title", "") for _, t, *_ in matches[:5]]
        raise SystemExit(_err(4, f"title 模糊匹配命中 {len(matches)} 条：{titles}，请改用 --id 指定"))

    day, task, _di, ti = matches[0]
    tid = task.get("id")

    # 护栏：已打卡禁止删
    done_ids = load_checkin_task_ids(plan_id)
    if tid in done_ids:
        raise SystemExit(_err(5,
            f"任务「{task.get('title')}」(id={tid}) 已经打卡，不允许删除。\n"
            f"   如确需调整，请先用 checkin 工具撤销打卡，或改用 postpone。"))

    removed = day["tasks"].pop(ti)
    return {
        "action": "remove",
        "status": "ok",
        "date": day.get("date"),
        "task": removed,
    }


def do_postpone(plan: dict, args: argparse.Namespace, plan_id: str) -> dict:
    """把任务挪到 --to 指定的日期。已打卡禁止挪，目标日越界禁止挪。"""
    if not args.to:
        raise SystemExit(_err(2, "postpone 必须提供 --to YYYY-MM-DD / tomorrow / +N"))
    if not args.id and not args.title:
        raise SystemExit(_err(2, "postpone 必须提供 --id 或 --title 之一"))

    try:
        target = parse_date_arg(args.to)
    except ValueError as e:
        raise SystemExit(_err(2, str(e)))

    start = resolve_start_date(plan)
    end = resolve_end_date(plan, fallback=start)
    if not (start <= target <= end):
        raise SystemExit(_err(6,
            f"目标日 {target} 超出 plan 范围 {start}~{end}。\n"
            f"   若计划已结束，请用 plan-tracker 新建延展计划；"
            f"   若希望强制写入，请改用 add 命令。"))

    matches = find_task(plan, task_id=args.id, title=args.title)
    if not matches:
        raise SystemExit(_err(3, f"未找到任务（id={args.id}, title={args.title}）"))
    if len(matches) > 1 and not args.id:
        titles = [t.get("title", "") for _, t, *_ in matches[:5]]
        raise SystemExit(_err(4, f"title 模糊匹配命中 {len(matches)} 条：{titles}，请改用 --id 指定"))

    day, task, _di, ti = matches[0]
    tid = task.get("id")
    if day.get("date") == target.isoformat():
        return {"action": "postpone", "status": "noop", "reason": "same-date", "task": task}

    done_ids = load_checkin_task_ids(plan_id)
    if tid in done_ids:
        raise SystemExit(_err(5,
            f"任务「{task.get('title')}」(id={tid}) 已经打卡，不允许延后。"))

    # 弹出原日条目
    moved = day["tasks"].pop(ti)
    src_date = day.get("date")

    # 写到目标日
    target_day = find_day_entry(plan, target)
    created_day = False
    if not target_day:
        target_day = {"date": target.isoformat(), "tasks": []}
        plan.setdefault("daily_tasks", []).append(target_day)
        plan["daily_tasks"].sort(key=lambda d: d.get("date", ""))
        created_day = True
    target_day["tasks"].append(moved)

    return {
        "action": "postpone",
        "status": "ok",
        "from_date": src_date,
        "to_date": target.isoformat(),
        "created_day": created_day,
        "task": moved,
    }


# ---------- 错误格式化 ----------

def _err(code: int, msg: str) -> int:
    """打印一条错误并返回 exit code（用于 raise SystemExit 链）。"""
    print(f"❌ {msg}", file=sys.stderr)
    return code


# ---------- 回执打印 ----------

def print_receipt(result: dict, plan_path: str, dry_run: bool) -> None:
    """统一的中性化回执（不带 persona 文案，由上层 chat 层包裹）。"""
    action = result.get("action")
    status = result.get("status")
    task = result.get("task") or {}

    head = "🧪 [dry-run]" if dry_run else "✅"
    if action == "add":
        if status == "noop":
            print(f"{head} 同日同名任务已存在，跳过：{task.get('title')}（{result['date']}）")
        else:
            day_note = "（新建当日条目）" if result.get("created_day") else ""
            print(f"{head} 已新增任务 → {result['date']}{day_note}")
            print(f"   • id        : {task.get('id')}")
            print(f"   • 标题       : {task.get('title')}")
            print(f"   • 时长       : {task.get('duration_min')} 分钟")
            print(f"   • 类别       : {task.get('category')}")
    elif action == "remove":
        print(f"{head} 已删除任务 ← {result['date']}")
        print(f"   • id        : {task.get('id')}")
        print(f"   • 标题       : {task.get('title')}")
    elif action == "postpone":
        if status == "noop":
            print(f"{head} 任务已经在目标日，无需移动：{task.get('title')}")
        else:
            day_note = "（新建目标日条目）" if result.get("created_day") else ""
            print(f"{head} 已延后任务 {result['from_date']} → {result['to_date']}{day_note}")
            print(f"   • id        : {task.get('id')}")
            print(f"   • 标题       : {task.get('title')}")

    if dry_run:
        print(f"   ↳ 未写盘（移除 --dry-run 后才会真正生效）。文件路径：{plan_path}")


# ---------- main ----------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task_edit.py",
        description="plan-tracker 手动录入/编辑任务（add / remove / postpone）",
    )
    parser.add_argument("action", choices=["add", "remove", "postpone"],
                        help="动作类型")
    parser.add_argument("--plan", help="指定 plan_id（默认使用 user-config.active_plan_id）")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅预览改动，不写盘")

    # add 专用
    parser.add_argument("--title", help="任务标题（add 必填，remove/postpone 可作为模糊匹配 key）")
    parser.add_argument("--duration", type=int, help="时长（分钟，默认 30，1~240）")
    parser.add_argument("--category", help=f"类别（默认 other，建议从 {sorted(KNOWN_CATEGORIES)} 选）")
    parser.add_argument("--note", help="选填备注（≤ 200 字符）")
    parser.add_argument("--date", default="today",
                        help="目标日（add 用，默认 today；支持 YYYY-MM-DD / today / tomorrow / +N）")

    # remove / postpone 专用
    parser.add_argument("--id", help="task id（精确匹配，优先于 --title）")
    parser.add_argument("--to", help="postpone 目标日期（YYYY-MM-DD / today / tomorrow / +N）")

    return parser


def main(argv: list = None) -> int:
    args = build_parser().parse_args(argv)

    plan_path = get_active_plan_path(args.plan)
    if not plan_path:
        print(
            "📭 还没找到有效的学习计划。\n"
            "   要先用 plan-tracker 创建一个，再回来手动加任务～\n"
            "   例：python3 plan-tracker/scripts/generate.py --goal '雅思6分' --deadline 2026-08-01",
            file=sys.stderr,
        )
        return 1

    plan_id = os.path.basename(os.path.dirname(plan_path))

    try:
        plan = load_plan(plan_path)
    except (json.JSONDecodeError, OSError) as e:
        print(f"❌ 读取 plan.json 失败：{e}", file=sys.stderr)
        return 7

    try:
        if args.action == "add":
            result = do_add(plan, args)
        elif args.action == "remove":
            result = do_remove(plan, args, plan_id)
        else:  # postpone
            result = do_postpone(plan, args, plan_id)
    except SystemExit as e:
        # do_xxx 内部抛 SystemExit(code)，直接透传 code
        return int(e.code) if isinstance(e.code, int) else 2

    if not args.dry_run and result.get("status") == "ok":
        try:
            atomic_dump(plan_path, plan)
        except OSError as e:
            print(f"❌ 写入 plan.json 失败：{e}", file=sys.stderr)
            return 7
        # 写盘成功后自动重渲染 dashboard（静默失败，绝不阻断主流程）
        regenerate_dashboard(plan_id=plan_id)

    print_receipt(result, plan_path, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
