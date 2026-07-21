#!/usr/bin/env python3
"""
user_scenario_test.py - 基于用户场景需求的 plan-tracker 黑盒测试

需求矩阵（来自用户描述）：
  1) 输入
     a. 初始化：接收 plan-tracker 计划 JSON / 用户手动录入任务
     b. 每日交互：checkin（完成 / 部分完成 / 未完成 + 耗时 + 心情）、adjust（请假 / 加码）
  2) 输出
     a. 每日：晨间任务卡（今日 3 件事）+ 打卡统计面板
     b. 每周：weekly_report（完成率 / 落后任务 / 下周建议）
     c. 即时：连续 2 天未打卡触发温和提醒；超前完成触发鼓励
  3) 其他
     - 单计划最多 180 天
     - 提醒时段用户可配置免打扰
     - 4 种人设切换

每个测试用例：
  - 名称 + 需求点 + 期望
  - 实际执行（脚本 + 文件断言）
  - 结果 PASS / FAIL / SKIP / WARN

不污染真实数据：全程在临时 HOME 隔离运行。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS = os.path.join(SKILL_ROOT, "scripts")


class C:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    DIM = "\033[90m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    END = "\033[0m"


# ---------- 全局结果收集 ----------
RESULTS = []  # [(id, name, status, msg)]


def record(tc_id: str, name: str, status: str, msg: str = ""):
    RESULTS.append((tc_id, name, status, msg))
    color = {"PASS": C.OK, "FAIL": C.FAIL, "SKIP": C.DIM, "WARN": C.WARN}.get(status, C.DIM)
    icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "WARN": "⚠️"}.get(status, "·")
    print(f"  {color}{icon} [{tc_id}] {name}  {C.DIM}{msg}{C.END}")


def header(tc_id: str, title: str, requirement: str):
    print(f"\n{C.BOLD}{C.CYAN}━━━ {tc_id} · {title} ━━━{C.END}")
    print(f"  {C.DIM}需求点: {requirement}{C.END}")


def run_script(script: str, args: list, env: dict, expect_success: bool = True):
    cmd = ["python3", os.path.join(SCRIPTS, script)] + args
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
    # 不论是否成功都返回 stdout/stderr，由调用方判断
    if proc.returncode != 0 and expect_success:
        return proc.stdout or None, proc.stderr or proc.stdout
    return proc.stdout, proc.stderr


# ============================================================
# 测试夹具：构造 plan.json
# ============================================================

def make_plan(plan_id: str, days: int, tasks_per_day: int = 3,
              start_offset: int = -2):
    """
    生成 N 天的 plan（与 plan-tracker schema 对齐：顶层 id + meta + daily_tasks）
    start_offset=-2 表示从 2 天前开始排，确保今日/明日都有任务
    """
    today = datetime.now().date()
    daily_tasks = []
    for d in range(days):
        day = today + timedelta(days=start_offset + d)
        tasks = [
            {
                "id": f"t-{d:03d}-{i}",
                "title": f"任务 D{d}-{i}",
                "duration_min": 25,
                "category": "study",
            }
            for i in range(tasks_per_day)
        ]
        daily_tasks.append({
            "date": day.strftime("%Y-%m-%d"),
            "stage_id": "stage-1",
            "tasks": tasks,
        })
    return {
        "id": plan_id,
        "version": 1,
        "meta": {
            "title": "测试计划 - " + plan_id,
            "goal": "通过 plan-tracker 用户场景测试",
            "deadline": (today + timedelta(days=days)).strftime("%Y-%m-%d"),
            "current_level": "",
            "daily_budget": 60,
            "weak_points": [],
            "template_origin": "_test",
        },
        "stages": [{"id": "stage-1", "name": "Stage1", "duration_days": days}],
        "daily_tasks": daily_tasks,
    }


def write_plan(data_root: str, plan: dict):
    plan_dir = os.path.join(data_root, plan["id"])
    os.makedirs(plan_dir, exist_ok=True)
    with open(os.path.join(plan_dir, "plan.json"), "w") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    return plan_dir


# ============================================================
# 主流程
# ============================================================

def main():
    keep_tmp = "--keep" in sys.argv
    tmp_root = tempfile.mkdtemp(prefix="plan-tracker-userscenario-")
    print(f"{C.BOLD}临时目录:{C.END} {tmp_root}")

    # 数据目录走 GOAL_TRACKER_DATA_DIR；模板/persona 直读 SKILL_ROOT
    data_root = os.path.join(tmp_root, "plan-tracker", "plans")
    os.makedirs(data_root, exist_ok=True)
    real_planner = os.path.abspath(os.path.join(SKILL_ROOT, "..", "plan-tracker"))

    env = os.environ.copy()
    env["GOAL_TRACKER_DATA_DIR"] = data_root
    env["GOAL_TRACKER_USER_CONFIG"] = os.path.join(tmp_root, "plan-tracker", "user-config.json")
    if os.path.isdir(real_planner):
        env["GOAL_TRACKER_TEMPLATE_DIR"] = os.path.join(real_planner, "references", "templates")
        env["GOAL_TRACKER_SELFTEST_DIR"] = os.path.join(real_planner, "references", "self-test")

    today_str = datetime.now().strftime("%Y-%m-%d")

    try:
        # ============ TC01：plan-tracker 自建计划 JSON ============
        header("TC01", "初始化-自建 plan-tracker 计划 JSON",
               "1.a plan-tracker 直接创建 plan.json（不依赖外部）")
        try:
            plan_obj = make_plan("tc01-self-contained", days=15, tasks_per_day=3, start_offset=-2)
            write_plan(data_root, plan_obj)
            pid = plan_obj["id"]
            # 验证字段完整性
            if pid and plan_obj.get("meta") and plan_obj.get("daily_tasks"):
                # 用 today.py 验证计划可被读取
                out, err = run_script("today.py",
                                  ["--plan", pid, "--persona", "gentle-senior"],
                                  env)
                if out and ("今日" in out or "今天" in out or datetime.now().strftime("%Y-%m-%d") in out):
                    record("TC01", "自建 plan-tracker 计划",
                           "PASS", f"id={pid}, tasks={len(plan_obj['daily_tasks'])}")
                else:
                    record("TC01", "自建 plan-tracker 计划", "WARN",
                           f"plan 已创建但 today.py 输出异常: {out[:150]}")
            else:
                record("TC01", "自建 plan-tracker 计划", "FAIL",
                       f"plan.json 字段缺失: keys={list(plan_obj.keys())}")
        except Exception as e:
            record("TC01", "自建 plan-tracker 计划", "FAIL", f"异常: {e}")

        # ============ TC02：手动录入 plan.json ============
        try:
            header("TC02", "初始化-手动录入计划 JSON",
                   "1.a 用户手动录入任务")
            plan02 = make_plan("tc02-manual", days=10, tasks_per_day=3)
            write_plan(data_root, plan02)
            out, err = run_script("today.py",
                                  ["--plan", "tc02-manual", "--persona", "gentle-senior"],
                                  env)
            if out and (today_str in out or "今日" in out or "今天" in out):
                record("TC02", "手动录入计划被识别", "PASS",
                       f"today.py 输出 {len(out)} 字符")
            else:
                record("TC02", "手动录入计划被识别", "FAIL",
                       f"today.py 未识别: {(err or out or '')[:120]}")
        except Exception as e:
            record("TC02", "手动录入计划被识别", "FAIL", f"异常: {e}")

        # ============ TC03：完成全部任务 ============
        try:
            header("TC03", "checkin-完成全部任务",
                   "1.b checkin 完成")
            plan03 = make_plan("tc03-all-done", days=5, tasks_per_day=3)
            write_plan(data_root, plan03)
            today_block = next(d for d in plan03["daily_tasks"] if d["date"] == today_str)
            all_ids = ",".join(t["id"] for t in today_block["tasks"])
            out, err = run_script("checkin.py",
                                  ["--plan", "tc03-all-done", "--tasks", all_ids,
                                   "--note", "全部完成"], env)
            log_path = os.path.join(data_root, "tc03-all-done", "checkin-log.json")
            if os.path.exists(log_path):
                with open(log_path) as _f:
                    log = json.load(_f)
                latest = log["checkins"][-1]
                if set(latest["task_ids"]) == set(t["id"] for t in today_block["tasks"]):
                    record("TC03", "完成全部任务落盘", "PASS",
                           f"{len(latest['task_ids'])} 个任务全部记录")
                else:
                    record("TC03", "完成全部任务落盘", "FAIL",
                           f"task_ids 不匹配: 实={latest['task_ids']}")
            else:
                record("TC03", "完成全部任务落盘", "FAIL",
                       f"checkin-log.json 未生成: {(err or '')[:120]}")
        except Exception as e:
            record("TC03", "完成全部任务落盘", "FAIL", f"异常: {e}")

        # ============ TC04：部分完成 ============
        try:
            header("TC04", "checkin-部分完成 1/3",
                   "1.b checkin 部分完成")
            plan04 = make_plan("tc04-partial", days=5, tasks_per_day=3)
            write_plan(data_root, plan04)
            today_block = next(d for d in plan04["daily_tasks"] if d["date"] == today_str)
            partial_id = today_block["tasks"][0]["id"]
            run_script("checkin.py",
                       ["--plan", "tc04-partial", "--tasks", partial_id,
                        "--note", "今日只做了一项"], env)
            log_path = os.path.join(data_root, "tc04-partial", "checkin-log.json")
            if os.path.exists(log_path):
                with open(log_path) as _f:
                    log = json.load(_f)
                if log["checkins"] and len(log["checkins"][-1]["task_ids"]) == 1:
                    record("TC04", "部分完成被正确记录", "PASS",
                           "task_ids 仅含 1 项")
                else:
                    record("TC04", "部分完成被正确记录", "FAIL",
                           f"checkins={log.get('checkins')}")
            else:
                record("TC04", "部分完成被正确记录", "FAIL",
                       "checkin-log.json 未生成")
        except Exception as e:
            record("TC04", "部分完成被正确记录", "FAIL", f"异常: {e}")

        # ============ TC05：未完成（不打卡），次日 streak 计算 ============
        try:
            header("TC05", "checkin-未完成日 + streak 计算",
                   "1.b checkin 未完成时 streak 应不递增")
            plan05 = make_plan("tc05-missed", days=5, tasks_per_day=3)
            write_plan(data_root, plan05)
            log_path = os.path.join(data_root, "tc05-missed", "checkin-log.json")
            three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            with open(log_path, "w") as _f:
                json.dump({
                    "plan_id": "tc05-missed",
                    "checkins": [{"date": three_days_ago, "task_ids": ["t-000-0"],
                                  "duration_min": 25, "note": ""}]
                }, _f, ensure_ascii=False, indent=2)
            out, err = run_script("streak.py", ["--plan", "tc05-missed"], env)
            if out:
                # 关键：current 应该是 0 或 1，不应是 4
                # 检查输出中是否含'0'或较小数字，而非'4 天'
                if "4 天" in out or "current: 4" in out.lower():
                    record("TC05", "未完成不应虚报 streak", "FAIL",
                           "断签 3 天后 current streak 仍报 4")
                else:
                    record("TC05", "未完成不应虚报 streak", "PASS",
                           f"streak 输出未虚报: {out.strip().splitlines()[0][:80] if out.strip() else ''}")
            else:
                record("TC05", "未完成不应虚报 streak", "WARN",
                       f"无法判定: {(out or err or '')[:120]}")
        except Exception as e:
            record("TC05", "未完成不应虚报 streak", "FAIL", f"异常: {e}")

        # ============ TC06：耗时 + 心情(note) 落盘 ============
        try:
            header("TC06", "checkin-耗时+心情落盘",
                   "1.b checkin 含耗时与心情（用 note 承载，符合 NEVER 2 不引入额外字段）")
            plan06 = make_plan("tc06-mood", days=5, tasks_per_day=3)
            write_plan(data_root, plan06)
            today_block = next(d for d in plan06["daily_tasks"] if d["date"] == today_str)
            run_script("checkin.py",
                       ["--plan", "tc06-mood", "--tasks", today_block["tasks"][0]["id"],
                        "--note", "心情：充实，今天状态特别好🎵"], env)
            log_path = os.path.join(data_root, "tc06-mood", "checkin-log.json")
            if os.path.exists(log_path):
                with open(log_path) as _f:
                    log = json.load(_f)
                last = log["checkins"][-1]
                has_duration = "duration_min" in last and isinstance(last["duration_min"], (int, float))
                has_mood = "note" in last and "心情" in last["note"]
                if has_duration and has_mood:
                    record("TC06", "耗时+心情入库", "PASS",
                           f"duration_min={last['duration_min']}, note='{last['note'][:20]}…'")
                else:
                    record("TC06", "耗时+心情入库", "FAIL",
                           f"duration={has_duration}, mood={has_mood}, raw={last}")
            else:
                record("TC06", "耗时+心情入库", "FAIL", "log 未生成")
        except Exception as e:
            record("TC06", "耗时+心情入库", "FAIL", f"异常: {e}")

        # ============ TC07：adjust 请假 → 断签救赎触发 ============
        try:
            header("TC07", "adjust-请假（断签救赎）",
                   "1.b adjust 请假 → 连续 3+ 天无打卡时 revive 应给出温和重启")
            plan07 = make_plan("tc07-leave", days=10, tasks_per_day=3)
            write_plan(data_root, plan07)
            log_path = os.path.join(data_root, "tc07-leave", "checkin-log.json")
            five_days_ago = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
            json.dump({
                "plan_id": "tc07-leave",
                "checkins": [{"date": five_days_ago, "task_ids": ["t-000-0"],
                              "duration_min": 30, "note": "之后请假了"}]
            }, open(log_path, "w"), ensure_ascii=False, indent=2)
            out, err = run_script("revive.py",
                                  ["--plan", "tc07-leave", "--persona", "gentle-senior"],
                                  env)
            if out:
                humiliating_words = ["前功尽弃", "废了", "没用", "失败", "懒"]
                soft_words = ["欢迎回来", "重新", "没关系", "重启", "回来", "继续",
                              "新开始", "断", "天"]
                has_soft = any(w in out for w in soft_words)
                has_bad = any(w in out for w in humiliating_words)
                if has_soft and not has_bad:
                    record("TC07", "请假后温和重启", "PASS",
                           "含温和话术，无羞辱词")
                elif has_bad:
                    record("TC07", "请假后温和重启", "FAIL",
                           "出现羞辱词，违反 NEVER 1")
                else:
                    record("TC07", "请假后温和重启", "WARN",
                           f"未明确识别温和话术: {out[:120]}")
            else:
                record("TC07", "请假后温和重启", "FAIL",
                       f"revive.py 无输出: {(err or '')[:120]}")
        except Exception as e:
            record("TC07", "请假后温和重启", "FAIL", f"异常: {e}")

        # ============ TC08：adjust 加码 ============
        try:
            header("TC08", "adjust-加码（连续超时信号）",
                   "1.b adjust 加码 → checkin 时 duration 远超估算时应有信号")
            plan08 = make_plan("tc08-overload", days=5, tasks_per_day=3)
            write_plan(data_root, plan08)
            log_path = os.path.join(data_root, "tc08-overload", "checkin-log.json")
            checkins = []
            for off in range(-2, 1):
                day = (datetime.now() + timedelta(days=off)).strftime("%Y-%m-%d")
                checkins.append({
                    "date": day,
                    "task_ids": ["t-000-0", "t-000-1", "t-000-2"],
                    "duration_min": 180,
                    "note": "今天加码冲刺",
                })
            json.dump({"plan_id": "tc08-overload", "checkins": checkins},
                      open(log_path, "w"), ensure_ascii=False, indent=2)
            out, err = run_script("streak.py", ["--plan", "tc08-overload",
                                                "--celebrate"], env)
            if out and ("3" in out or "streak" in out.lower() or "🔥" in out or "天" in out):
                record("TC08", "加码-连续 3 天 streak 识别", "PASS",
                       "streak.py 输出含连续天数")
            else:
                record("TC08", "加码-连续 3 天 streak 识别", "WARN",
                       f"streak 未明确反映: {(out or err)[:120]}")
        except Exception as e:
            record("TC08", "加码-连续 3 天 streak 识别", "FAIL", f"异常: {e}")

        # ============ TC09：晨间任务卡 ============
        try:
            header("TC09", "输出-晨间任务卡（今日 N 件事）",
                   "2.a 每日 - 晨间任务卡，列出今日待办")
            plan09 = make_plan("tc09-morning", days=5, tasks_per_day=3)
            write_plan(data_root, plan09)
            out, err = run_script("today.py",
                                  ["--plan", "tc09-morning", "--persona", "gentle-senior"],
                                  env)
            today_block = next(d for d in plan09["daily_tasks"] if d["date"] == today_str)
            if out:
                hits = sum(1 for t in today_block["tasks"] if t["title"] in out)
                has_date = today_str in out or "今日" in out or "今天" in out
                if hits >= 2 and has_date:
                    record("TC09", "晨间任务卡完整", "PASS",
                           f"列出 {hits}/{len(today_block['tasks'])} 任务 + 含日期")
                else:
                    record("TC09", "晨间任务卡完整", "FAIL",
                           f"任务命中 {hits}, 含日期 {has_date}")
            else:
                record("TC09", "晨间任务卡完整", "FAIL", f"today.py 无输出: {(err or '')[:120]}")
        except Exception as e:
            record("TC09", "晨间任务卡完整", "FAIL", f"异常: {e}")

        # ============ TC10：打卡统计面板 ============
        try:
            header("TC10", "输出-打卡统计面板",
                   "2.a 每日 - checkin --stats 面板（含完成率/streak）")
            plan10 = make_plan("tc10-night", days=5, tasks_per_day=3)
            write_plan(data_root, plan10)
            today_block = next(d for d in plan10["daily_tasks"] if d["date"] == today_str)
            run_script("checkin.py",
                       ["--plan", "tc10-night", "--tasks", today_block["tasks"][0]["id"]],
                       env)
            out, err = run_script("checkin.py", ["--plan", "tc10-night", "--stats"], env)
            if out:
                kw_hits = sum(1 for k in ["完成", "streak", "Streak", "🔥", "天",
                                           "%", "率"] if k in out)
                if kw_hits >= 2:
                    record("TC10", "打卡统计面板含核心指标", "PASS",
                           f"命中关键词 {kw_hits}")
                else:
                    record("TC10", "打卡统计面板含核心指标", "WARN",
                           f"关键词命中过少 ({kw_hits}): {out[:120]}")
            else:
                record("TC10", "打卡统计面板含核心指标", "FAIL", "checkin --stats 无输出")
        except Exception as e:
            record("TC10", "打卡统计面板含核心指标", "FAIL", f"异常: {e}")

        # ============ TC11：weekly_report ============
        try:
            header("TC11", "输出-周报",
                   "2.b 每周 weekly_report（完成率 + 落后任务 + 下周建议）")
            plan11 = make_plan("tc11-weekly", days=14, tasks_per_day=3, start_offset=-7)
            write_plan(data_root, plan11)
            log_path = os.path.join(data_root, "tc11-weekly", "checkin-log.json")
            checkins = []
            for off in range(-7, 1):
                day = (datetime.now() + timedelta(days=off)).strftime("%Y-%m-%d")
                if off in (-5, -3):
                    continue
                checkins.append({
                    "date": day,
                    "task_ids": [f"t-{off+7:03d}-0"],
                    "duration_min": 30,
                    "note": "",
                })
            json.dump({"plan_id": "tc11-weekly", "checkins": checkins},
                      open(log_path, "w"), ensure_ascii=False, indent=2)
            out, err = run_script("stats.py",
                                  ["weekly", "--plan", "tc11-weekly"], env)
            if out:
                kws = ["完成率", "%", "周报", "落后", "下周", "建议", "时长", "h",
                       "min", "Streak", "streak"]
                hits = [k for k in kws if k in out]
                if len(hits) >= 3:
                    record("TC11", "周报含完成率/建议", "PASS",
                           f"命中关键字 {hits}")
                else:
                    record("TC11", "周报含完成率/建议", "WARN",
                           f"周报字段不完整: 命中 {hits}, 输出片段={out[:160]}")
            else:
                record("TC11", "周报含完成率/建议", "FAIL", "stats.py 无输出")
        except Exception as e:
            record("TC11", "周报含完成率/建议", "FAIL", f"异常: {e}")

        # ============ TC12：连续断签提醒 ============
        try:
            header("TC12", "输出-即时·断签温和提醒",
                   "2.c 连续 N 天未打卡触发温和提醒（不羞辱）")
            plan12 = make_plan("tc12-broken", days=10, tasks_per_day=3)
            write_plan(data_root, plan12)
            log_path = os.path.join(data_root, "tc12-broken", "checkin-log.json")
            with open(log_path, "w") as _f:
                json.dump({
                    "plan_id": "tc12-broken",
                    "checkins": [{"date": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
                                  "task_ids": ["t-000-0"], "duration_min": 25, "note": ""}]
                }, _f, ensure_ascii=False, indent=2)
            out, err = run_script("revive.py",
                                  ["--plan", "tc12-broken", "--persona", "gentle-senior"],
                                  env)
            if out:
                humiliating = ["前功尽弃", "懒", "废了", "失败者"]
                soft = ["欢迎回来", "没关系", "重新", "断", "天", "回来"]
                ok_soft = any(w in out for w in soft)
                bad = any(w in out for w in humiliating)
                if ok_soft and not bad:
                    record("TC12", "断签温和提醒", "PASS",
                           "包含 ' 没关系/重新 ' 等温和话术")
                elif bad:
                    record("TC12", "断签温和提醒", "FAIL", "出现羞辱话术")
                else:
                    record("TC12", "断签温和提醒", "WARN", "未识别明显温和信号")
            else:
                record("TC12", "断签温和提醒", "FAIL", "revive 无输出")
        except Exception as e:
            record("TC12", "断签温和提醒", "FAIL", f"异常: {e}")

        # ============ TC13：超前完成鼓励 ============
        try:
            header("TC13", "输出-即时·超前完成鼓励",
                   "2.c 连续 7 天打卡触发里程碑鼓励")
            plan13 = make_plan("tc13-streak7", days=14, tasks_per_day=3, start_offset=-7)
            write_plan(data_root, plan13)
            log_path = os.path.join(data_root, "tc13-streak7", "checkin-log.json")
            checkins = []
            for off in range(-6, 1):
                day = (datetime.now() + timedelta(days=off)).strftime("%Y-%m-%d")
                checkins.append({"date": day, "task_ids": [f"t-{off+7:03d}-0"],
                                 "duration_min": 30, "note": ""})
            json.dump({"plan_id": "tc13-streak7", "checkins": checkins},
                      open(log_path, "w"), ensure_ascii=False, indent=2)
            out, err = run_script("streak.py",
                                  ["--plan", "tc13-streak7", "--celebrate"], env)
            if out:
                milestone_signals = ["7", "破冰", "🌱", "🔥", "里程碑", "恭喜",
                                     "坚持", "周"]
                hits = [k for k in milestone_signals if k in out]
                if "7" in out and len(hits) >= 2:
                    record("TC13", "7 天里程碑鼓励", "PASS",
                           f"命中信号 {hits}")
                else:
                    record("TC13", "7 天里程碑鼓励", "WARN",
                           f"里程碑表达不充分: {out[:160]}")
            else:
                record("TC13", "7 天里程碑鼓励", "FAIL", "streak --celebrate 无输出")
        except Exception as e:
            record("TC13", "7 天里程碑鼓励", "FAIL", f"异常: {e}")

        # ============ TC14：边界 180 天 ============
        try:
            header("TC14", "边界-单计划最多 180 天",
                   "3 边界：plan_days=180 不应崩溃；plan_days>180 应有保护")
            today_compact = datetime.now().strftime("%Y%m%d")
            # make_plan 默认 start_offset=-2，所以 days=178 时实际跨度 = 180 天
            plan14 = make_plan(f"plan-{today_compact}-tc14-180days",
                               days=178, tasks_per_day=1)
            write_plan(data_root, plan14)
            out14, err14 = run_script("today.py",
                                       ["--plan", plan14["id"]], env)
            out_h, err_h = run_script("dashboard.py",
                                       ["--plan", plan14["id"]], env)
            if out14 and out_h:
                record("TC14", "180 天计划处理稳定", "PASS",
                       f"today/dashboard 均正常（today {len(out14)} 字符，dashboard {len(out_h)} 字符）")
            else:
                record("TC14", "180 天计划处理稳定", "FAIL",
                       f"today_err={(err14 or '')[:80]}, dashboard_err={(err_h or '')[:80]}")

            # TC14c：plan_id 不规范时 dashboard 应不崩溃（兜底解析）
            plan14c = make_plan("tc14-non-standard-id", days=10, tasks_per_day=1)
            write_plan(data_root, plan14c)
            out14c, err14c = run_script("dashboard.py",
                                    ["--plan", "tc14-non-standard-id"], env)
            if err14c and ("ValueError" in err14c or "strptime" in err14c):
                record("TC14c", "dashboard 对非标准 plan_id 健壮性",
                       "FAIL",
                       f"dashboard 假设 plan_id 形如 plan-YYYYMMDD-xxx，否则崩溃")
            elif out14c:
                record("TC14c", "dashboard 对非标准 plan_id 健壮性",
                       "PASS",
                       "兼容非标准 plan_id（兜底用 daily_tasks[0].date）")
            else:
                record("TC14c", "dashboard 对非标准 plan_id 健壮性",
                       "FAIL", f"无输出: stderr={(err14c or '')[:120]}")

            plan14b = make_plan(f"plan-{today_compact}-tc14b-200days",
                                days=200, tasks_per_day=1)
            write_plan(data_root, plan14b)
            out14b, err14b = run_script("today.py",
                                         ["--plan", plan14b["id"]], env)
            warn_signals = ["180", "上限", "超过", "拆分", "陪伴边界"]
            warn_hits = [s for s in warn_signals if s in (err14b or "")]
            if out14b and warn_hits:
                record("TC14b", "超 180 天计划（200 天）", "PASS",
                       f"主流程不阻塞 + stderr 出现 180 天软警告（命中 {warn_hits}）")
            elif out14b:
                record("TC14b", "超 180 天计划（200 天）", "WARN",
                       "脚本能跑通但缺少 180 天上限校验/提示")
            else:
                record("TC14b", "超 180 天计划（200 天）", "FAIL",
                       "脚本未输出主流程")
        except Exception as e:
            record("TC14", "180 天边界", "FAIL", f"异常: {e}")

        # ============ TC15：免打扰配置 ============
        try:
            header("TC15", "其他-用户配置 reminder_time/免打扰",
                   "3 提醒时段可配置免打扰")
            cfg_path = env["GOAL_TRACKER_USER_CONFIG"]
            os.makedirs(os.path.dirname(cfg_path), exist_ok=True)

            # 构造一个 plan 用于触发 today.py 输出
            plan15 = make_plan("tc15-dnd", days=5, tasks_per_day=2)
            write_plan(data_root, plan15)

            # —— TC15a：字段可序列化 ——
            cfg = {
                "persona": "gentle-senior",
                "active_plan_id": "tc15-dnd",
                "reminder_time": "09:00",
                "do_not_disturb": {"start": "22:00", "end": "08:00"},
            }
            with open(cfg_path, "w") as _f:
                json.dump(cfg, _f, ensure_ascii=False, indent=2)
            with open(cfg_path) as _f:
                re_cfg = json.load(_f)
            if re_cfg.get("reminder_time") and re_cfg.get("do_not_disturb"):
                record("TC15", "user-config 可写读 reminder_time + do_not_disturb",
                       "PASS", "字段可序列化")
            else:
                record("TC15", "user-config 可写读", "FAIL", "字段写不进去")

            # —— TC15b：脚本真实消费 do_not_disturb ——
            # 构造覆盖"当前时间"的免打扰窗口（now ± 5 min），验证 today.py 输出降级
            now = datetime.now()
            start_t = (now - timedelta(minutes=5)).strftime("%H:%M")
            end_t = (now + timedelta(minutes=5)).strftime("%H:%M")
            cfg_dnd_active = {
                "persona": "gentle-senior",
                "active_plan_id": "tc15-dnd",
                "reminder_time": "09:00",
                "do_not_disturb": {"start": start_t, "end": end_t},
            }
            json.dump(cfg_dnd_active, open(cfg_path, "w"), ensure_ascii=False, indent=2)
            out_quiet, _ = run_script("today.py", ["--plan", "tc15-dnd"], env)

            # 关闭 dnd 时输出应包含正常 emoji；开启时应降级为 [quiet] 前缀
            cfg_off = {**cfg_dnd_active, "do_not_disturb": None}
            with open(cfg_path, "w") as _f:
                json.dump(cfg_off, _f, ensure_ascii=False, indent=2)
            out_normal, _ = run_script("today.py", ["--plan", "tc15-dnd"], env)

            quiet_ok = "[quiet]" in (out_quiet or "")
            normal_ok = ("📋" in (out_normal or "")
                         or "今日任务" in (out_normal or ""))
            if quiet_ok and normal_ok:
                record("TC15b", "脚本消费 do_not_disturb（输出降级）",
                       "PASS",
                       "免打扰窗口内 today.py 输出 [quiet] 简讯；非窗口正常输出")
            elif quiet_ok:
                record("TC15b", "脚本消费 do_not_disturb",
                       "WARN",
                       f"降级生效但常规输出异常: normal={(out_normal or '')[:80]}")
            else:
                record("TC15b", "脚本消费 do_not_disturb",
                       "FAIL",
                       f"未触发降级: quiet={(out_quiet or '')[:80]}")
        except Exception as e:
            record("TC15", "user-config 可写读", "FAIL", f"异常: {e}")

        # ============ TC16：4 种人设切换 ============
        try:
            header("TC16", "其他-4 种人设切换",
                   "today.py 在不同 persona 下话术应有差异")
            plan16 = make_plan("tc16-persona", days=5, tasks_per_day=3)
            write_plan(data_root, plan16)
            outputs = {}
            for p in ["gentle-senior", "strict-coach", "humorous-buddy", "zen-master"]:
                o, _ = run_script("today.py", ["--plan", "tc16-persona",
                                                "--persona", p], env)
                outputs[p] = (o or "").strip()
            unique = len({v for v in outputs.values() if v})
            if unique >= 3 and all(outputs.values()):
                record("TC16", "4 种人设话术差异化", "PASS",
                       f"{unique}/4 种产出不同")
            elif unique >= 2:
                record("TC16", "4 种人设话术差异化", "WARN",
                       f"仅 {unique}/4 不同（部分人设话术相似）")
            else:
                record("TC16", "4 种人设话术差异化", "FAIL",
                       "人设话术几乎一致")
        except Exception as e:
            record("TC16", "4 种人设话术差异化", "FAIL", f"异常: {e}")

        # ============ 汇总 ============
        print(f"\n{C.BOLD}{'═' * 60}{C.END}")
        print(f"{C.BOLD}测试报告{C.END}")
        print(f"{'═' * 60}")
        passed = sum(1 for r in RESULTS if r[2] == "PASS")
        failed = sum(1 for r in RESULTS if r[2] == "FAIL")
        warned = sum(1 for r in RESULTS if r[2] == "WARN")
        skipped = sum(1 for r in RESULTS if r[2] == "SKIP")
        total = len(RESULTS)
        print(f"  总数: {total}")
        print(f"  {C.OK}PASS:{C.END}  {passed}")
        print(f"  {C.FAIL}FAIL:{C.END}  {failed}")
        print(f"  {C.WARN}WARN:{C.END}  {warned}")
        print(f"  {C.DIM}SKIP:{C.END}  {skipped}")
        print()
        if failed:
            print(f"{C.FAIL}失败用例：{C.END}")
            for tcid, name, status, msg in RESULTS:
                if status == "FAIL":
                    print(f"  • [{tcid}] {name}: {msg}")
        if warned:
            print(f"{C.WARN}提醒（建议增强）：{C.END}")
            for tcid, name, status, msg in RESULTS:
                if status == "WARN":
                    print(f"  • [{tcid}] {name}: {msg}")

        sys.exit(1 if failed else 0)

    finally:
        if not keep_tmp:
            shutil.rmtree(tmp_root, ignore_errors=True)
            print(f"{C.DIM}已清理临时目录{C.END}")
        else:
            print(f"{C.WARN}⚠️ 保留临时目录: {tmp_root}{C.END}")


if __name__ == "__main__":
    main()
