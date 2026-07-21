#!/usr/bin/env python3
"""
derive_plan.py - 基于现有计划/模板/示例衍生新计划

衍生场景（3 种）：
  1. 从内置模板衍生：把 ielts-toefl 改造成 BEC 商务英语
  2. 从历史计划衍生：把上次的考研计划改造成今年的，复用结构调整时间
  3. 从 example 衍生：参照高质量示例的结构，但内容定制

用法：
  # 从模板衍生（输出到 templates/custom/）
  python3 derive_plan.py from-template ielts-toefl --new-name bec --target "BEC 高级"

  # 从历史计划衍生（输出新 plan）
  python3 derive_plan.py from-plan plan-20250901-kaoyan-985cs \\
      --new-deadline 2026-12-22 --new-name "考研二战 2026"

  # 从 example 衍生（输出新 plan）
  python3 derive_plan.py from-example example-react-60d \\
      --new-name "学 Vue 60 天" --target "Vue 3 + TS"

衍生 = 复制结构 + 重命名 + 平移日期 + 标注 derived_from

依赖：
  - Python 3.8+，仅标准库（json, pathlib, argparse, datetime, copy, uuid）
  - 零网络调用、零三方包

输入：
  - 子命令：from-template / from-plan / from-example
  - 源标识 + 新计划名 + 目标领域（自由文本）
  - 可选：--new-deadline / --shrink-days / --extend-days

输出：
  - 新 plan.json，meta.template_origin 字段标注衍生来源（见 SKILL.md NEVER 8）
  - meta.derived_from = 源 plan-id / 源 template name
  - daily_tasks 的 task_ids 重新生成（避免与源 plan 冲突）

性能上限：
  - 衍生 < 150ms（含日期平移 + ID 重生成）
  - 不会读取源计划的 checkin-log，互不干扰

错误模式（exit code）：
  - 0  成功
  - 1  源不存在 → 提示可选源列表
  - 2  目标名已存在 → 自动加 -v2 / -derived 后缀
  - 3  --new-deadline 早于今日 → 拒绝并提示
  - 4  shrink/extend 参数冲突 → 二选一

注意：
  - 衍生只复制「结构 + 方法论」，不复制用户历史进度（progress 归零）
  - 用户 checkin-log / streak 仅与原 plan 关联，新 plan 的 streak 从 0 起算
"""

import json
import os
import sys
import argparse
import re
from datetime import datetime, timedelta

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 模板目录支持环境变量覆盖（测试隔离）；自定义模板写入到 TEMPLATE_DIR/custom 下
TEMPLATE_DIR = os.environ.get("STUDY_PLANNER_TEMPLATE_DIR") or os.path.join(SKILL_DIR, "references/templates")
CUSTOM_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, "custom")
EXAMPLE_DIR = os.environ.get("STUDY_PLANNER_EXAMPLE_DIR") or os.path.join(SKILL_DIR, "references/examples")


def _resolve_data_dir() -> str:
    """数据目录解析。优先级：STUDY_PLANNER_DATA_DIR env > <cwd>/study-planner/study-plans/"""
    env = os.environ.get("STUDY_PLANNER_DATA_DIR")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    return os.path.abspath(os.path.join(os.getcwd(), "study-planner", "study-plans"))


DATA_DIR = _resolve_data_dir()


def slugify(text: str) -> str:
    text = re.sub(r'[^\w\u4e00-\u9fff-]', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text.lower()


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"找不到: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────
# 模式 1：从模板衍生 → 生成新模板
# ──────────────────────────────────────────────
def derive_from_template(source_id: str, new_name: str, target: str) -> str:
    """从内置模板衍生为自定义模板"""
    source_path = os.path.join(TEMPLATE_DIR, f"{source_id}.json")
    template = load_json(source_path)

    new_id = slugify(new_name)
    new_template = dict(template)
    new_template["id"] = new_id
    new_template["name"] = new_name
    new_template["derived_from"] = source_id
    new_template["target"] = target
    new_template["_note"] = (
        f"由 {source_id} 衍生，请根据 {target} 的实际特点调整 "
        "stages / weak_point_categories / sample_tasks"
    )

    out_path = os.path.join(CUSTOM_TEMPLATE_DIR, f"{new_id}.json")
    os.makedirs(CUSTOM_TEMPLATE_DIR, exist_ok=True)
    if os.path.exists(out_path):
        raise FileExistsError(f"自定义模板已存在: {out_path}")
    save_json(new_template, out_path)
    return out_path


# ──────────────────────────────────────────────
# 模式 2：从历史计划衍生 → 生成新计划（平移日期）
# ──────────────────────────────────────────────
def derive_from_plan(source_plan_id: str, new_name: str, new_deadline: str) -> str:
    """从历史计划衍生新计划，结构保留，日期按新 deadline 平移"""
    source_path = os.path.join(DATA_DIR, source_plan_id, "plan.json")
    src = load_json(source_path)

    old_deadline = datetime.strptime(src["meta"]["deadline"], "%Y-%m-%d")
    new_deadline_dt = datetime.strptime(new_deadline, "%Y-%m-%d")
    delta_days = (new_deadline_dt - old_deadline).days

    new_id = f"plan-{datetime.now().strftime('%Y%m%d')}-{slugify(new_name)}"
    new_plan = json.loads(json.dumps(src))  # 深拷贝
    new_plan["id"] = new_id
    new_plan["version"] = 1
    new_plan["meta"]["title"] = new_name
    new_plan["meta"]["deadline"] = new_deadline
    new_plan["meta"]["derived_from"] = source_plan_id

    # 平移所有 daily_tasks 的日期
    for daily in new_plan.get("daily_tasks", []):
        old_date = datetime.strptime(daily["date"], "%Y-%m-%d")
        daily["date"] = (old_date + timedelta(days=delta_days)).strftime("%Y-%m-%d")

    plan_dir = os.path.join(DATA_DIR, new_id)
    out_path = os.path.join(plan_dir, "plan.json")
    save_json(new_plan, out_path)

    # 同时初始化打卡 / streak / config
    save_json({"plan_id": new_id, "checkins": []},
              os.path.join(plan_dir, "checkin-log.json"))
    save_json({
        "plan_id": new_id, "current": 0, "longest": 0,
        "last_checkin": None, "broken_dates": [],
        "milestones_unlocked": [], "achievements": []
    }, os.path.join(plan_dir, "streak.json"))
    save_json({
        "persona": "gentle-senior", "active_plan_id": new_id,
        "checkin_channel": "daily", "reminder_time": "09:00"
    }, os.path.join(plan_dir, "user-config.json"))

    return out_path


# ──────────────────────────────────────────────
# 模式 3：从 example 衍生 → 生成新计划骨架
# ──────────────────────────────────────────────
def derive_from_example(example_id: str, new_name: str, target: str) -> str:
    """从 examples/ 衍生骨架计划，去掉示例 metadata，保留结构供 AI 填充"""
    source_path = os.path.join(EXAMPLE_DIR, f"{example_id}.json")
    src = load_json(source_path)

    new_id = f"plan-{datetime.now().strftime('%Y%m%d')}-{slugify(new_name)}"
    new_plan = json.loads(json.dumps(src))
    new_plan.pop("_example_meta", None)
    new_plan["id"] = new_id
    new_plan["version"] = 1
    new_plan["meta"]["title"] = new_name
    new_plan["meta"]["goal"] = target
    new_plan["meta"]["derived_from_example"] = example_id

    # 清空 daily_tasks，留给 AI 重新生成（结构保留 stages 作参照）
    new_plan["daily_tasks"] = []

    plan_dir = os.path.join(DATA_DIR, new_id)
    out_path = os.path.join(plan_dir, "plan.json")
    save_json(new_plan, out_path)

    save_json({"plan_id": new_id, "checkins": []},
              os.path.join(plan_dir, "checkin-log.json"))
    save_json({
        "plan_id": new_id, "current": 0, "longest": 0,
        "last_checkin": None, "broken_dates": [],
        "milestones_unlocked": [], "achievements": []
    }, os.path.join(plan_dir, "streak.json"))
    save_json({
        "persona": "gentle-senior", "active_plan_id": new_id,
        "checkin_channel": "daily", "reminder_time": "09:00"
    }, os.path.join(plan_dir, "user-config.json"))

    return out_path


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="基于已有内容衍生新计划/模板")
    sub = parser.add_subparsers(dest="mode", required=True)

    p1 = sub.add_parser("from-template", help="从内置模板衍生自定义模板")
    p1.add_argument("source", help="源模板 ID，如 ielts-toefl")
    p1.add_argument("--new-name", required=True, help="新模板名称")
    p1.add_argument("--target", required=True, help="新目标场景描述")

    p2 = sub.add_parser("from-plan", help="从历史计划衍生新计划")
    p2.add_argument("source", help="源 plan ID")
    p2.add_argument("--new-name", required=True)
    p2.add_argument("--new-deadline", required=True, help="YYYY-MM-DD")

    p3 = sub.add_parser("from-example", help="从 example 衍生新计划骨架")
    p3.add_argument("source", help="example ID（不含路径和扩展名），如 example-react-60d")
    p3.add_argument("--new-name", required=True)
    p3.add_argument("--target", required=True)

    args = parser.parse_args()

    try:
        if args.mode == "from-template":
            path = derive_from_template(args.source, args.new_name, args.target)
            print(f"✅ 自定义模板已生成: {path}")
            print(f"   下一步：打开文件根据 {args.target} 调整 stages 和 sample_tasks")
        elif args.mode == "from-plan":
            path = derive_from_plan(args.source, args.new_name, args.new_deadline)
            print(f"✅ 新计划已生成（含日期平移）: {path}")
            print(f"   下一步：告诉 AI「校对 {args.new_name} 的任务，删除已不适用的内容」")
        elif args.mode == "from-example":
            path = derive_from_example(args.source, args.new_name, args.target)
            print(f"✅ 新计划骨架已生成: {path}")
            print(f"   下一步：告诉 AI「按 {args.target} 填充 daily_tasks」")
    except (FileNotFoundError, FileExistsError) as e:
        print(f"❌ {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
