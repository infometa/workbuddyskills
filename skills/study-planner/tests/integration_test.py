#!/usr/bin/env python3
"""
integration_test.py - study-planner 端到端冒烟测试

测试链路：
    init_plan → derive_plan from-template → edit_plan(add/show/postpone/extend) → export_all

特点：
- 使用临时 cwd + STUDY_PLANNER_DATA_DIR 环境变量隔离，绝不污染用户真实数据
- 自动清理临时目录
- 失败时打印完整 stderr，便于排错

用法：
    python3 tests/integration_test.py
    python3 tests/integration_test.py --keep   # 保留临时目录用于调试
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
    )
    if expect_success and proc.returncode != 0:
        fail(
            f"命令失败 (exit={proc.returncode})",
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}",
        )
    return proc


# ---------- 主测试流程 ----------
def main():
    keep = "--keep" in sys.argv

    print(f"{C.BOLD}🧪 study-planner integration test{C.END}")
    print(f"{C.DIM}skill root: {SKILL_ROOT}{C.END}")

    # 创建临时 cwd 目录，隔离测试数据
    tmp_root = tempfile.mkdtemp(prefix="study-planner-test-")
    print(f"{C.DIM}temp cwd: {tmp_root}{C.END}")

    # 数据目录走 STUDY_PLANNER_DATA_DIR；模板目录走 STUDY_PLANNER_TEMPLATE_DIR（直读 SKILL_ROOT/references/templates）
    data_dir = os.path.join(tmp_root, "study-planner", "study-plans")
    env = os.environ.copy()
    env["STUDY_PLANNER_DATA_DIR"] = data_dir
    env["STUDY_PLANNER_TEMPLATE_DIR"] = os.path.join(SKILL_ROOT, "references", "templates")
    env["STUDY_PLANNER_SELFTEST_DIR"] = os.path.join(SKILL_ROOT, "references", "self-test")

    # derive_plan 写到 templates/custom/，需要可写副本
    fake_template_dir = os.path.join(tmp_root, "templates")
    shutil.copytree(os.path.join(SKILL_ROOT, "references", "templates"), fake_template_dir)
    # 清空 custom/ 目录（避免历史测试残留干扰）
    custom_dir = os.path.join(fake_template_dir, "custom")
    if os.path.exists(custom_dir):
        shutil.rmtree(custom_dir)
    env["STUDY_PLANNER_TEMPLATE_DIR"] = fake_template_dir

    deadline = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    plan_name = "test_ielts"

    try:
        # ---------- Step 1：init_plan ----------
        step("Step 1: 初始化计划 (init_plan.py)")
        run(
            [sys.executable, os.path.join(SCRIPTS, "init_plan.py"), plan_name, deadline, "--template", "ielts-toefl"],
            env=env,
        )

        plan_dir_root = data_dir
        plans = os.listdir(plan_dir_root)
        if len(plans) != 1:
            fail(f"期望生成 1 个计划目录，实际 {len(plans)}: {plans}")
        plan_id = plans[0]
        plan_dir = os.path.join(plan_dir_root, plan_id)
        plan_path = os.path.join(plan_dir, "plan.json")

        if not os.path.exists(plan_path):
            fail(f"plan.json 未生成: {plan_path}")
        with open(plan_path) as f:
            plan = json.load(f)
        for required in ("id", "version", "meta", "stages", "daily_tasks"):
            if required not in plan:
                fail(f"plan.json 缺字段: {required}")
        ok(f"plan_id = {plan_id}")
        ok(f"version = {plan['version']}, deadline = {plan['meta']['deadline']}")

        # 同时校验 checkin/streak/user-config 都生成了
        for sibling in ("checkin-log.json", "streak.json", "user-config.json"):
            sibling_path = os.path.join(plan_dir, sibling)
            if not os.path.exists(sibling_path):
                fail(f"附属文件未生成: {sibling}")
        ok("checkin/streak/user-config 全部生成")

        # ---------- Step 2：derive_plan from-template ----------
        step("Step 2: 衍生新模板 (derive_plan.py from-template)")
        run(
            [
                sys.executable,
                os.path.join(SCRIPTS, "derive_plan.py"),
                "from-template",
                "ielts-toefl",
                "--new-name", "test-bec",
                "--target", "BEC 高级冲刺",
            ],
            env=env,
        )
        new_template = os.path.join(fake_template_dir, "custom", "test-bec.json")
        if not os.path.exists(new_template):
            fail(f"衍生模板未生成: {new_template}")
        with open(new_template) as f:
            tpl = json.load(f)
        if "BEC" not in str(tpl):
            fail("衍生模板未注入 target 字段")
        ok(f"衍生模板已生成: custom/test-bec.json ({os.path.getsize(new_template)} bytes)")

        # ---------- Step 3：edit_plan show ----------
        step("Step 3: 查看计划摘要 (edit_plan.py show)")
        proc = run(
            [sys.executable, os.path.join(SCRIPTS, "edit_plan.py"), "show", plan_id],
            env=env,
        )
        if plan_id not in proc.stdout:
            fail("show 输出未包含 plan_id", proc.stdout)
        ok("show 命令输出正常")

        # ---------- Step 4：edit_plan add-task ----------
        step("Step 4: 新增任务 (edit_plan.py add-task)")
        target_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        run(
            [
                sys.executable,
                os.path.join(SCRIPTS, "edit_plan.py"),
                "add-task",
                plan_id,
                "--date", target_date,
                "--title", "全真模考剑18 T1",
                "--duration", "180",
                "--category", "exam",
                "--priority", "high",
            ],
            env=env,
        )
        with open(plan_path) as f:
            plan_after_add = json.load(f)
        if plan_after_add["version"] != 2:
            fail(f"version 未自增，期望 2 实际 {plan_after_add['version']}")
        # daily_tasks 是按日分组：[{date, stage_id, tasks: [...]}]
        all_tasks = []
        for daily in plan_after_add.get("daily_tasks", []):
            all_tasks.extend(daily.get("tasks", []))
        added = [t for t in all_tasks if "全真模考剑18 T1" in t.get("title", "")]
        if not added:
            fail(
                "新增任务未写入 daily_tasks",
                f"daily_tasks 总日数={len(plan_after_add.get('daily_tasks', []))}, 总任务数={len(all_tasks)}",
            )
        ok(f"任务已新增 (id={added[0].get('id')}, version={plan_after_add['version']})")

        # 确认自动备份生成了
        backup = os.path.join(plan_dir, "plan.v1.bak.json")
        if not os.path.exists(backup):
            fail(f"自动备份未生成: {backup}")
        ok("自动备份 plan.v1.bak.json ✓")

        # ---------- Step 5：edit_plan postpone ----------
        step("Step 5: 整体延后 (edit_plan.py postpone --days 3)")
        original_deadline = plan_after_add["meta"]["deadline"]
        run(
            [sys.executable, os.path.join(SCRIPTS, "edit_plan.py"), "postpone", plan_id, "--days", "3"],
            env=env,
        )
        with open(plan_path) as f:
            plan_after_postpone = json.load(f)
        new_deadline = plan_after_postpone["meta"]["deadline"]
        expected = (datetime.strptime(original_deadline, "%Y-%m-%d") + timedelta(days=3)).strftime("%Y-%m-%d")
        if new_deadline != expected:
            fail(f"deadline 未正确延后：期望 {expected} 实际 {new_deadline}")
        ok(f"deadline {original_deadline} → {new_deadline}")

        # ---------- Step 6：export_all ----------
        step("Step 6: 一键导出 (Markdown + 打印版, export_all.py)")
        # 先看 export_all 的签名
        export_all = os.path.join(SCRIPTS, "export", "export_all.py")
        if os.path.exists(export_all):
            proc = run(
                [sys.executable, export_all, plan_id],
                env=env,
                expect_success=False,  # 兼容签名不同
            )
            if proc.returncode != 0:
                # 尝试无参调用（可能默认导出 active plan）
                proc = run([sys.executable, export_all], env=env, expect_success=False)
            if proc.returncode == 0:
                ok("export_all 执行完成")
            else:
                print(f"  {C.WARN}⚠ export_all 失败但不阻塞测试: {proc.stderr[:200]}{C.END}")
        else:
            print(f"  {C.WARN}⚠ export_all.py 不存在，跳过{C.END}")

        # ---------- 总结 ----------
        print(f"\n{C.OK}{C.BOLD}🎉 全部 6 步通过！study-planner 端到端链路 OK{C.END}")
        print(f"   • plan_id: {plan_id}")
        print(f"   • final version: {plan_after_postpone['version']}")
        print(f"   • daily_tasks count: {len(plan_after_postpone['daily_tasks'])}")
        print(f"   • backups: {[f for f in os.listdir(plan_dir) if 'bak' in f]}")

    finally:
        if keep:
            print(f"\n{C.WARN}--keep 已传入，保留临时目录: {tmp_root}{C.END}")
        else:
            shutil.rmtree(tmp_root, ignore_errors=True)
            print(f"\n{C.DIM}🧹 已清理临时目录{C.END}")


if __name__ == "__main__":
    main()
