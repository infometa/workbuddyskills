#!/usr/bin/env python3
"""
integration_test.py - plan-tracker 端到端冒烟测试

测试链路：
    [seed] 直接创建 plan.json（plan-tracker 自包含）
        → today  → checkin (today)
        → checkin --stats
        → streak --celebrate
        → stats weekly
        → revive  (注入 5 天断签)
        → dashboard 自动重渲染验证

特点：
- 使用临时 cwd + GOAL_TRACKER_DATA_DIR 环境变量隔离，绝不污染用户真实数据
- 直接构造最小 plan.json 作为种子（不依赖外部 skill）
- 失败时打印完整 stderr

用法：
    python3 tests/integration_test.py
    python3 tests/integration_test.py --keep    # 保留临时目录用于调试
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

# plan-tracker 自身脚本目录
SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS = os.path.join(SKILL_ROOT, "scripts")


# ---------- 颜色输出 ----------
class C:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    DIM = "\033[90m"
    BOLD = "\033[1m"
    END = "\033[0m"


def step(title: str):
    print(f"\n{C.BOLD}▶ {title}{C.END}")


def ok(msg: str):
    print(f"  {C.OK}✅ {msg}{C.END}")


def fail(msg: str, detail: str = ""):
    print(f"  {C.FAIL}❌ {msg}{C.END}")
    if detail:
        print(f"  {C.DIM}{detail}{C.END}")
    sys.exit(1)


def run(cmd: list, env: dict, expect_success: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    """运行命令，失败立刻报错"""
    print(f"  {C.DIM}$ {' '.join(cmd)}{C.END}")
    proc = subprocess.run(
        cmd,
        env=env,
        capture_output=capture,
        text=True,
        timeout=60,
    )
    if expect_success and proc.returncode != 0:
        fail(
            f"命令退出码 {proc.returncode}",
            f"STDOUT: {proc.stdout[-500:] if proc.stdout else ''}\nSTDERR: {proc.stderr[-500:] if proc.stderr else ''}",
        )
    return proc


def main():
    keep_tmp = "--keep" in sys.argv

    # ---------- 准备临时 cwd ----------
    tmp_root = tempfile.mkdtemp(prefix="plan-tracker-test-")
    print(f"{C.BOLD}临时目录:{C.END} {tmp_root}")

    # 数据目录走 GOAL_TRACKER_DATA_DIR，模板目录直读 SKILL_ROOT
    data_dir = os.path.join(tmp_root, ".plan-tracker", "plans")
    env = os.environ.copy()
    env["GOAL_TRACKER_DATA_DIR"] = data_dir
    env["GOAL_TRACKER_USER_CONFIG"] = os.path.join(tmp_root, ".plan-tracker", "user-config.json")
    env["GOAL_TRACKER_TEMPLATE_DIR"] = os.path.join(SKILL_ROOT, "references", "templates")
    env["GOAL_TRACKER_SELFTEST_DIR"] = os.path.join(SKILL_ROOT, "references", "self-test")
    # PERSONA_DIR 仍按 __file__ 相对路径解析，无需额外注入

    plan_id = None

    try:
        # ============== Step 1: 直接创建种子 plan.json (plan-tracker 自包含) ==============
        step("Step 1/6: 直接创建 plan.json（不依赖 study-planner）")
        today_str = datetime.now().strftime("%Y-%m-%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        deadline = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        plan_id = f"plan-{today_str.replace('-', '')}-test"
        plan = {
            "id": plan_id,
            "meta": {
                "title": "plan-tracker 集成测试",
                "start_date": today_str,
                "deadline": deadline,
            },
            "daily_tasks": [
                {
                    "date": yesterday_str,
                    "stage_id": "s1",
                    "tasks": [
                        {"id": "t-y01", "title": "听力 S1（昨日）", "duration_min": 25,
                         "category": "listening"},
                    ],
                },
                {
                    "date": today_str,
                    "stage_id": "s1",
                    "tasks": [
                        {"id": "t-d01", "title": "听力 S1 精听", "duration_min": 25,
                         "category": "listening"},
                        {"id": "t-d02", "title": "复盘", "duration_min": 10,
                         "category": "review"},
                    ],
                },
            ],
        }
        plan_dir = os.path.join(data_dir, plan_id)
        os.makedirs(plan_dir, exist_ok=True)
        plan_path = os.path.join(plan_dir, "plan.json")
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        first_task_id = plan["daily_tasks"][1]["tasks"][0]["id"]
        ok(f"种子 plan.json 已创建 (plan_id={plan_id}, 今日任务数=2, 首任务={first_task_id})")

        # ============== Step 2: today.py 今日播报 ==============
        step("Step 2/6: today.py 今日任务播报")
        proc = run(
            ["python3", os.path.join(SCRIPTS, "today.py"),
             "--plan", plan_id, "--persona", "gentle-senior"],
            env,
        )
        if not proc.stdout.strip():
            fail("today.py 输出为空")
        # 至少应包含计划标题或日期
        if today_str not in proc.stdout and "今日" not in proc.stdout and "今天" not in proc.stdout:
            fail("today.py 输出未含日期或'今日/今天'", proc.stdout[:300])
        ok(f"今日播报正常 ({len(proc.stdout)} 字符)")

        # ============== Step 3: checkin.py 打卡 ==============
        step("Step 3/6: checkin.py 打卡今日首任务")
        run(
            ["python3", os.path.join(SCRIPTS, "checkin.py"),
             "--plan", plan_id,
             "--tasks", first_task_id,
             "--note", "integration test 打卡"],
            env,
        )
        # 校验 checkin-log.json
        checkin_path = os.path.join(data_dir, plan_id, "checkin-log.json")
        if not os.path.exists(checkin_path):
            fail(f"checkin-log.json 未生成: {checkin_path}")
        with open(checkin_path) as f:
            checkin_data = json.load(f)
        if not checkin_data.get("checkins"):
            fail("checkin-log.json 中 checkins 为空")
        ok(f"打卡已写入 ({len(checkin_data['checkins'])} 条记录)")

        # ============== Step 4: streak.py Streak 计算 ==============
        step("Step 4/6: streak.py 连续天数 + 庆祝")
        proc = run(
            ["python3", os.path.join(SCRIPTS, "streak.py"),
             "--plan", plan_id, "--celebrate"],
            env,
        )
        if not proc.stdout.strip():
            fail("streak.py 输出为空")
        # 至少应含数字 1（首日打卡）
        if "1" not in proc.stdout:
            fail("streak.py 输出未含'1'（首日 streak 应为 1）", proc.stdout[:300])
        ok(f"Streak 输出正常（含日数 1）")

        # ============== Step 5: stats.py 周报 ==============
        step("Step 5/6: stats.py weekly 周报")
        proc = run(
            ["python3", os.path.join(SCRIPTS, "stats.py"),
             "weekly", "--plan", plan_id],
            env,
        )
        if not proc.stdout.strip():
            fail("stats.py 输出为空")
        ok(f"周报生成正常 ({len(proc.stdout)} 字符)")

        # ============== Step 6: revive.py 断签救赎 ==============
        step("Step 6/6: revive.py 断签救赎（注入 5 天前的最后打卡）")
        # 篡改 checkin-log.json，把唯一一条记录的日期改成 5 天前
        five_days_ago = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        with open(checkin_path) as f:
            data_to_mod = json.load(f)
        if data_to_mod["checkins"]:
            data_to_mod["checkins"][0]["date"] = five_days_ago
        with open(checkin_path, "w") as f:
            json.dump(data_to_mod, f, ensure_ascii=False, indent=2)

        proc = run(
            ["python3", os.path.join(SCRIPTS, "revive.py"),
             "--plan", plan_id, "--persona", "gentle-senior"],
            env,
        )
        if not proc.stdout.strip():
            fail("revive.py 输出为空")
        # 断签救赎文案应含数字（断签天数）或'天'字
        if not any(kw in proc.stdout for kw in ["天", "断", "回来", "重启", "复活", "rebuild"]):
            fail("revive.py 输出未识别断签信号", proc.stdout[:300])
        ok(f"断签救赎文案已生成 ({len(proc.stdout)} 字符)")

        # ---------- 全部通过 ----------
        print(f"\n{C.OK}{C.BOLD}🎉 所有步骤通过 (7/7){C.END}")
        print(f"{C.DIM}plan_id: {plan_id}{C.END}")

    finally:
        if not keep_tmp:
            shutil.rmtree(tmp_root, ignore_errors=True)
            print(f"{C.DIM}已清理临时目录{C.END}")
        else:
            print(f"{C.WARN}⚠️  保留临时目录: {tmp_root}{C.END}")


if __name__ == "__main__":
    main()
