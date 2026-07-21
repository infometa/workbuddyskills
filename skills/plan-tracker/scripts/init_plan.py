#!/usr/bin/env python3
"""
init_plan.py - plan-tracker 自有的目标拆解 + 落盘入口

用法（两种模式）：

  模式 A：JSON 一次性传入（推荐 AI 调用）
    python3 init_plan.py --goal-json goal.json [--skeleton-json skel.json]

  模式 B：命令行参数（手动测试）
    python3 init_plan.py --title "考研英语二" \\
                          --specific "真题 65 分" \\
                          --deadline 2026-07-15 \\
                          --current-level "四级 480" \\
                          --weekday-min 90 --weekend-min 180

依赖：
  - Python 3.8+，仅标准库
  - 共享 _plan_utils.DATA_DIR / MAX_PLAN_DAYS（与打卡数据目录一致）
  - 拆解算法来自同目录 decompose.py

输出：
  - <DATA_DIR>/<plan-id>/plan.json      —— SMART/OKR/ABC/anti-goals/if-then 全收
  - <DATA_DIR>/<plan-id>/checkin-log.json —— 空骨架
  - <DATA_DIR>/<plan-id>/streak.json     —— 空骨架
  - .gitignore 自动追加 .plan-tracker/ 规则（NEVER 5：保护用户数据不被 commit）

错误模式（exit code）：
  - 0  成功
  - 1  SMART 校验失败（缺字段 / 截止日过期 / >180 天）
  - 2  目标 JSON 文件不存在或解析失败
  - 3  目标目录已存在 → 自动追加 -v2/v3 后缀
  - 4  写入失败（磁盘 / 权限）

设计取舍：
  - 不绑模板（与 study-planner 的"模板路线"区分；plan-tracker 走对话式拆解）
  - 不调用 LLM；所有"创意决策"必须由调用方在 goal/skeleton 里给出
  - 默认填充 anti_goals=[] 和 if_then_plans=[]，AI 可在 init 后再 patch
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _plan_utils import DATA_DIR, MAX_PLAN_DAYS, regenerate_dashboard  # noqa: E402
from decompose import build_decomposition, slugify  # noqa: E402


# ──────────────────────────────────────────────
# .gitignore 守护（与 study-planner 一致的 NEVER 5）
# ──────────────────────────────────────────────

def _ensure_gitignore() -> None:
    """首次落盘时，在 cwd/.gitignore 自动追加 .plan-tracker/ 忽略规则。"""
    gi_path = os.path.join(os.getcwd(), ".gitignore")
    rule = ".plan-tracker/"
    try:
        if os.path.exists(gi_path):
            with open(gi_path, "r", encoding="utf-8") as f:
                content = f.read()
            if rule in content.splitlines():
                return
            sep = "" if (not content or content.endswith("\n")) else "\n"
            with open(gi_path, "a", encoding="utf-8") as f:
                f.write(f"{sep}\n# plan-tracker skill 个人学习数据（避免 commit）\n{rule}\n")
        else:
            with open(gi_path, "w", encoding="utf-8") as f:
                f.write(f"# plan-tracker skill 个人学习数据（避免 commit）\n{rule}\n")
    except OSError:
        # 写不进 .gitignore 不阻塞主流程
        pass


# ──────────────────────────────────────────────
# 写盘
# ──────────────────────────────────────────────

def _make_plan_id(title: str) -> str:
    """生成 plan_id：plan-YYYYMMDD-<slug>。"""
    return f"plan-{datetime.now().strftime('%Y%m%d')}-{slugify(title)}"


def _resolve_unique_dir(plan_id: str) -> tuple:
    """若目录已存在，自动追加 -v2/v3。返回 (final_id, abs_dir)。"""
    base = plan_id
    final_id = base
    suffix = 2
    while os.path.exists(os.path.join(DATA_DIR, final_id)):
        final_id = f"{base}-v{suffix}"
        suffix += 1
        if suffix > 99:
            raise RuntimeError(f"无法为 {base} 找到可用后缀（已尝试到 -v99）")
    return final_id, os.path.join(DATA_DIR, final_id)


def save_plan(plan: dict) -> str:
    """写盘：plan.json + checkin-log.json（空）+ streak.json（空）+ user-config.json 联动。

    Returns:
        plan.json 的绝对路径
    """
    plan_id = plan["id"]
    plan_dir = plan["_plan_dir"]
    os.makedirs(plan_dir, exist_ok=True)

    # 写 plan.json（去掉内部字段 _plan_dir）
    plan_to_write = {k: v for k, v in plan.items() if not k.startswith("_")}
    plan_path = os.path.join(plan_dir, "plan.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan_to_write, f, ensure_ascii=False, indent=2)

    # 空 checkin-log
    checkin_path = os.path.join(plan_dir, "checkin-log.json")
    if not os.path.exists(checkin_path):
        with open(checkin_path, "w", encoding="utf-8") as f:
            json.dump({"plan_id": plan_id, "checkins": []}, f, ensure_ascii=False, indent=2)

    # 空 streak
    streak_path = os.path.join(plan_dir, "streak.json")
    if not os.path.exists(streak_path):
        with open(streak_path, "w", encoding="utf-8") as f:
            json.dump({
                "plan_id": plan_id,
                "current": 0,
                "longest": 0,
                "last_checkin": None,
                "broken_dates": [],
                "milestones_unlocked": [],
                "achievements": [],
                "bottleneck_tasks": [],
            }, f, ensure_ascii=False, indent=2)

    # 顶层 user-config.json：把 active_plan_id 切到新 plan
    user_config_path = os.path.abspath(
        os.path.join(os.getcwd(), ".plan-tracker", "user-config.json")
    )
    os.makedirs(os.path.dirname(user_config_path), exist_ok=True)
    if os.path.exists(user_config_path):
        try:
            with open(user_config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except (json.JSONDecodeError, OSError):
            cfg = {}
    else:
        cfg = {}
    cfg.setdefault("persona", "gentle-senior")
    cfg.setdefault("checkin_channel", "daily")
    cfg.setdefault("reminder_time", "09:00")
    cfg["active_plan_id"] = plan_id
    with open(user_config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    _ensure_gitignore()
    return plan_path


# ──────────────────────────────────────────────
# 顶层 init_plan
# ──────────────────────────────────────────────

def init_plan(goal: dict, daily_skeleton: dict = None) -> dict:
    """组合 build_decomposition + 写盘。

    Returns:
        plan dict（含 id 和 _plan_dir）
    """
    decomp = build_decomposition(goal, daily_skeleton)

    plan_id = _make_plan_id(goal["title"])
    final_id, plan_dir = _resolve_unique_dir(plan_id)

    plan = {
        "id": final_id,
        "version": 2,  # v2 = plan-tracker 拆解（带 abc_levels / anti_goals / if_then_plans）
        "schema": "plan-tracker.v2",
        "meta": decomp["meta"],
        "stages": decomp["stages"],
        "daily_tasks": decomp["daily_tasks"],
        "_plan_dir": plan_dir,
    }
    return plan


# ──────────────────────────────────────────────
# 命令行
# ──────────────────────────────────────────────

def _load_json_arg(path: str, label: str) -> dict:
    if not path:
        return {}
    if not os.path.isfile(path):
        print(f"❌ {label} 文件不存在：{path}", file=sys.stderr)
        sys.exit(2)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ {label} JSON 解析失败：{e}", file=sys.stderr)
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(
        description="plan-tracker 目标拆解：SMART → OKR → 每日 ABC 三档"
    )
    # 模式 A：JSON 文件
    parser.add_argument("--goal-json", help="目标 JSON 文件路径（含 title/specific/deadline 等）")
    parser.add_argument("--skeleton-json", help="每日骨架 JSON 文件路径（可选）")

    # 模式 B：命令行参数
    parser.add_argument("--title", help="目标标题（如『考研英语二 65+』）")
    parser.add_argument("--specific", help="可衡量验收标准（如『真题平均 65 分』）")
    parser.add_argument("--deadline", help="截止日期 YYYY-MM-DD")
    parser.add_argument("--current-level", default="", help="当前水平描述")
    parser.add_argument("--weekday-min", type=int, default=0, help="工作日每天可投入分钟数")
    parser.add_argument("--weekend-min", type=int, default=0, help="周末每天可投入分钟数")
    parser.add_argument("--anti-goals", default="", help="反目标，逗号分隔（如『熬夜,放弃运动』）")

    # 通用
    parser.add_argument("--dry-run", action="store_true", help="只打印结果，不写盘")
    parser.add_argument("--list", action="store_true", help="列出所有已存在的 plan")

    args = parser.parse_args()

    # --list 模式
    if args.list:
        if not os.path.exists(DATA_DIR):
            print("（暂无任何 plan）")
            return 0
        plans = sorted(os.listdir(DATA_DIR), reverse=True)
        if not plans:
            print("（暂无任何 plan）")
            return 0
        print(f"📋 当前 plans（数据目录: {DATA_DIR}）：")
        for pid in plans:
            pp = os.path.join(DATA_DIR, pid, "plan.json")
            if not os.path.exists(pp):
                continue
            try:
                with open(pp, "r", encoding="utf-8") as f:
                    p = json.load(f)
                meta = p.get("meta", {})
                print(f"  • {pid}")
                print(f"      title: {meta.get('title', '?')}")
                print(f"      goal:  {meta.get('goal', '')[:50]}")
                print(f"      span:  {meta.get('start_date', '?')} → {meta.get('deadline', '?')}")
            except (json.JSONDecodeError, OSError):
                continue
        return 0

    # 拼出 goal
    goal_from_json = _load_json_arg(args.goal_json, "goal-json")
    skel_from_json = _load_json_arg(args.skeleton_json, "skeleton-json") if args.skeleton_json else None

    goal = dict(goal_from_json)
    if args.title:
        goal["title"] = args.title
    if args.specific:
        goal["specific"] = args.specific
    if args.deadline:
        goal["deadline"] = args.deadline
    if args.current_level:
        goal["current_level"] = args.current_level
    if args.weekday_min or args.weekend_min:
        goal["daily_minutes"] = {
            "weekday": int(args.weekday_min or 0),
            "weekend": int(args.weekend_min or 0),
        }
    if args.anti_goals:
        existing = goal.get("anti_goals") or []
        if isinstance(existing, list):
            goal["anti_goals"] = existing + [s.strip() for s in re.split(r"[,，]", args.anti_goals) if s.strip()]
        else:
            goal["anti_goals"] = [s.strip() for s in re.split(r"[,，]", args.anti_goals) if s.strip()]

    if not goal:
        parser.print_help()
        print("\n❌ 必须提供 --goal-json 或 --title/--specific/--deadline/--weekday-min", file=sys.stderr)
        return 1

    # 拆解 + 写盘
    try:
        plan = init_plan(goal, skel_from_json)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(json.dumps(
            {k: v for k, v in plan.items() if not k.startswith("_")},
            ensure_ascii=False, indent=2,
        ))
        return 0

    try:
        plan_path = save_plan(plan)
    except OSError as e:
        print(f"❌ 写盘失败：{e}", file=sys.stderr)
        return 4

    # 友好回显
    meta = plan["meta"]
    n_days = len(plan["daily_tasks"])
    abc_first = (plan["daily_tasks"][0]["tasks"][0].get("abc_levels") or {}) if n_days else {}
    print(f"✅ plan 已创建：{plan_path}")
    print(f"   id: {plan['id']}")
    print(f"   📐 SMART 验收: {meta.get('goal', '')}")
    print(f"   📅 周期: {meta.get('start_date')} → {meta.get('deadline')}（{n_days} 天）")
    print(f"   🎯 阶段: {len(plan['stages'])} 个 OKR phase")
    if abc_first:
        a = abc_first.get("a", {}).get("minutes", 0)
        b = abc_first.get("b", {}).get("minutes", 0)
        c = abc_first.get("c", {}).get("minutes", 0)
        print(f"   ⚡ 首日 ABC: A={a}分钟 / B={b}分钟 / C={c}分钟（C 档 = 累的时候做这个就不断签）")
    if meta.get("anti_goals"):
        print(f"   🛡️  反目标: {' / '.join(meta['anti_goals'])}")
    if meta.get("if_then_plans"):
        print(f"   🆘 If-Then: {len(meta['if_then_plans'])} 条应急方案")
    print(f"\n下一步：跑 today.py 看今日任务，或继续完善 OKR 的 key_results。")

    # 首次生成 dashboard.html（静默失败，绝不阻断主流程）
    regenerate_dashboard(plan_id=plan["id"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
