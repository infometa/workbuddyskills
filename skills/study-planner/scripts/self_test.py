#!/usr/bin/env python3
"""
self_test.py - 5 题水平自检 → 自动 patch plan.meta.current_level + daily_budget

用法：
  # 交互模式（推荐人工）
  python3 self_test.py <plan-id>

  # 非交互模式（AI 直接传答案，5 个数字逗号分隔）
  python3 self_test.py <plan-id> --answers 3,2,3,2,2

  # 仅查看题目（dry-run，不写盘）
  python3 self_test.py <plan-id> --show

  # 指定题库（默认按 plan.meta.template_origin 匹配；找不到回退到 _generic）
  python3 self_test.py <plan-id> --quiz ielts-toefl

设计原则（NEVER 1 - 始终给用户回控制权）：
  - 默认仅 patch current_level，不强改 daily_budget（除非加 --apply-budget）
  - 总是打印评估结果 + 建议，由用户决定是否 apply
  - 写盘前自动 backup（沿用 edit_plan 的 v{N}.bak.json 机制）

依赖：仅标准库（json, argparse, os, sys）
错误码：
  - 0  成功
  - 1  plan 不存在
  - 2  题库不存在
  - 3  答案数量/格式错误
"""
import json
import os
import sys
import argparse
import shutil
from datetime import datetime


def _resolve_data_dir() -> str:
    """数据目录解析。优先级：STUDY_PLANNER_DATA_DIR env > <cwd>/study-planner/study-plans/"""
    env = os.environ.get("STUDY_PLANNER_DATA_DIR")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    return os.path.abspath(os.path.join(os.getcwd(), "study-planner", "study-plans"))


DATA_DIR = _resolve_data_dir()


def _resolve_quiz_dir() -> str:
    env_dir = os.environ.get("STUDY_PLANNER_SELFTEST_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir
    here = os.path.dirname(os.path.abspath(__file__))
    rel = os.path.normpath(os.path.join(here, "..", "references", "self-test"))
    return rel


QUIZ_DIR = _resolve_quiz_dir()


def load_quiz(quiz_id: str) -> dict:
    path = os.path.join(QUIZ_DIR, f"{quiz_id}.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"题库不存在: {quiz_id}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_quizzes() -> list:
    if not os.path.isdir(QUIZ_DIR):
        return []
    return sorted(
        f[:-5] for f in os.listdir(QUIZ_DIR)
        if f.endswith(".json") and not f.startswith(".")
    )


def load_plan(plan_id: str) -> dict:
    p = os.path.join(DATA_DIR, plan_id, "plan.json")
    if not os.path.isfile(p):
        raise FileNotFoundError(f"找不到计划: {plan_id}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_plan(plan: dict, plan_id: str):
    p = os.path.join(DATA_DIR, plan_id, "plan.json")
    bak = os.path.join(DATA_DIR, plan_id, f"plan.v{plan.get('version', 1)}.bak.json")
    shutil.copy2(p, bak)
    plan["version"] = plan.get("version", 1) + 1
    with open(p, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)


def show_quiz(quiz: dict):
    """仅打印题目，不收答案。"""
    print(f"\n📝 {quiz['title']}")
    if quiz.get("description"):
        print(f"   {quiz['description']}\n")
    for i, q in enumerate(quiz["questions"], 1):
        print(f"  Q{i}. {q['prompt']}")
        for opt in q["options"]:
            print(f"      {opt['value']}. {opt['label']}")
        print()


def collect_answers_interactive(quiz: dict) -> list:
    """交互式收集答案，返回每题的 value 列表。"""
    print(f"\n📝 {quiz['title']}（共 {len(quiz['questions'])} 题）")
    if quiz.get("description"):
        print(f"   {quiz['description']}")
    print()

    answers = []
    for i, q in enumerate(quiz["questions"], 1):
        print(f"Q{i}. {q['prompt']}")
        for opt in q["options"]:
            print(f"  {opt['value']}. {opt['label']}")
        valid = {opt["value"] for opt in q["options"]}
        while True:
            try:
                raw = input(f"  你的选择 [{min(valid)}-{max(valid)}]: ").strip()
                if not raw:
                    continue
                v = int(raw)
                if v in valid:
                    answers.append(v)
                    print()
                    break
                print(f"  ❌ 请输入 {sorted(valid)} 之一")
            except (ValueError, EOFError, KeyboardInterrupt):
                print("\n已取消")
                sys.exit(0)
    return answers


def parse_answers_arg(arg: str, expected: int) -> list:
    """解析 --answers '3,2,3,2,2' 这种形式。"""
    raw = [s.strip() for s in arg.split(",") if s.strip()]
    if len(raw) != expected:
        raise ValueError(f"--answers 需要 {expected} 个数字（当前 {len(raw)} 个）")
    out = []
    for i, s in enumerate(raw, 1):
        try:
            out.append(int(s))
        except ValueError:
            raise ValueError(f"--answers 第 {i} 项不是数字: {s}")
    return out


def score_to_band(score: int, scoring: dict) -> dict:
    """把总分映射到 scoring 表里的 band。
    scoring key 形如 '5-9' / '10-14'。
    """
    for band, info in scoring.items():
        # 解析 "lo-hi"
        try:
            lo_s, hi_s = band.split("-", 1)
            lo, hi = int(lo_s), int(hi_s)
        except ValueError:
            continue
        if lo <= score <= hi:
            return {"band": band, **info}
    # 超界兜底（可能题库 scoring 不全）
    return {"band": "?", "current_level": "未知（题库 scoring 缺失）",
            "daily_budget": None, "advice": ""}


def evaluate(quiz: dict, answers: list) -> dict:
    """计算总分 + 给出 band。"""
    if len(answers) != len(quiz["questions"]):
        raise ValueError(f"答案数量不匹配（期望 {len(quiz['questions'])}，得到 {len(answers)}）")
    # 校验每题 value 合法
    for i, (q, a) in enumerate(zip(quiz["questions"], answers), 1):
        valid = {opt["value"] for opt in q["options"]}
        if a not in valid:
            raise ValueError(f"Q{i} 答案 {a} 不在合法选项 {sorted(valid)} 中")
    total = sum(answers)
    band = score_to_band(total, quiz.get("scoring", {}))
    return {"total": total, **band}


def main():
    ap = argparse.ArgumentParser(description="5 题水平自检 → 自动估算 current_level")
    ap.add_argument("plan_id", help="目标 plan-id")
    ap.add_argument("--quiz", default=None,
                    help="题库 id（默认按 plan.meta.template_origin 匹配；找不到回退 _generic）")
    ap.add_argument("--answers", default=None,
                    help="非交互模式：逗号分隔的答案，如 '3,2,3,2,2'")
    ap.add_argument("--show", action="store_true",
                    help="只打印题目，不收答案、不写盘")
    ap.add_argument("--apply-budget", action="store_true",
                    help="同时把题库建议的 daily_budget 写入 plan（默认仅写 current_level）")
    args = ap.parse_args()

    # 1) 载入 plan
    try:
        plan = load_plan(args.plan_id)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    # 2) 决定 quiz id
    quiz_id = args.quiz or plan["meta"].get("template_origin", "_generic")
    try:
        quiz = load_quiz(quiz_id)
    except FileNotFoundError:
        # 回退到通用题库
        if quiz_id != "_generic":
            print(f"ℹ️  未找到题库 {quiz_id}，回退到 _generic")
            try:
                quiz = load_quiz("_generic")
                quiz_id = "_generic"
            except FileNotFoundError:
                print(f"❌ 题库目录损坏：连 _generic 都找不到", file=sys.stderr)
                print(f"   QUIZ_DIR = {QUIZ_DIR}", file=sys.stderr)
                print(f"   现存题库: {list_quizzes()}", file=sys.stderr)
                sys.exit(2)
        else:
            print(f"❌ 题库 _generic 不存在（QUIZ_DIR={QUIZ_DIR}）", file=sys.stderr)
            sys.exit(2)

    # 3) 仅展示模式
    if args.show:
        show_quiz(quiz)
        return

    # 4) 收集答案
    try:
        if args.answers is not None:
            answers = parse_answers_arg(args.answers, len(quiz["questions"]))
        else:
            answers = collect_answers_interactive(quiz)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(3)

    # 5) 评分
    try:
        result = evaluate(quiz, answers)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(3)

    # 6) 输出 + patch
    print("\n" + "─" * 50)
    print(f"📊 自检结果")
    print("─" * 50)
    print(f"  题库：{quiz['title']} ({quiz_id})")
    print(f"  答案：{answers}（总分 {result['total']}，区间 {result['band']}）")
    print(f"  评估水平：{result['current_level']}")
    if result.get("advice"):
        print(f"  建议：{result['advice']}")
    if result.get("daily_budget"):
        print(f"  推荐 daily_budget：工作日 {result['daily_budget']['weekday']}min / 周末 {result['daily_budget']['weekend']}min")

    # 7) 写盘
    plan["meta"]["current_level"] = result["current_level"]
    plan["meta"]["self_test"] = {
        "quiz_id": quiz_id,
        "answers": answers,
        "total": result["total"],
        "band": result["band"],
        "evaluated_at": datetime.now().isoformat(timespec="seconds"),
    }

    if args.apply_budget and result.get("daily_budget"):
        plan["meta"]["daily_budget"] = result["daily_budget"]
        budget_msg = f"+ daily_budget"
    else:
        budget_msg = ""
        if result.get("daily_budget"):
            print(f"\n💡 提示：daily_budget 未自动应用。如需应用，请加 --apply-budget；")
            print(f"   或手动跑 'edit_plan.py update-meta {args.plan_id} --field daily_budget.weekday --value {result['daily_budget']['weekday']}'")

    save_plan(plan, args.plan_id)
    print(f"\n✅ 已写入 plan.meta.current_level{(' ' + budget_msg) if budget_msg else ''}（version → v{plan['version']}）")
    if args.apply_budget:
        print(f"   ⚠️  daily_budget 改了，建议接着跑：python3 edit_plan.py rebalance {args.plan_id}")


if __name__ == "__main__":
    main()
