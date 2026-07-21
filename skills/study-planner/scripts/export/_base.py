#!/usr/bin/env python3
"""
study-planner export base · 公共加载逻辑
所有 export/* 脚本共享：从 plan.json 加载学习计划
"""
import json
import os
import sys
from pathlib import Path


def _resolve_data_root() -> Path:
    """数据目录解析。优先级：STUDY_PLANNER_DATA_DIR env > <cwd>/study-planner/study-plans/"""
    env = os.environ.get("STUDY_PLANNER_DATA_DIR")
    if env:
        return Path(os.path.abspath(os.path.expanduser(env)))
    return Path(os.path.abspath(os.path.join(os.getcwd(), "study-planner", "study-plans")))


DATA_ROOT = _resolve_data_root()


def resolve_output_dir(plan_dir: Path, plan_id: str, cli_arg: str = None) -> Path:
    """报告产物输出目录解析（与 plan.json 数据目录解耦）。

    优先级（高 → 低）：
      1. CLI 参数 --output-dir
      2. 环境变量 STUDY_PLANNER_OUTPUT_DIR
      3. 默认：plan_dir 自身（向后兼容旧行为）

    支持的占位符（CLI / env value 中可用）：
      {plan_id}   → 当前计划 id
      {cwd}       → 当前工作目录
      ~           → 用户家目录

    返回值：Path（已 mkdir -p，确保可写）

    用法示例：
      python3 to_markdown.py --output-dir ./reports
        → ./reports/plan.md
      python3 export_all.py --output-dir './reports/{plan_id}'
        → ./reports/plan-20260512-xxx/{plan.md, plan-report.html, daily-cards/...}
      STUDY_PLANNER_OUTPUT_DIR='~/Documents/study-reports/{plan_id}' python3 export_all.py
        → ~/Documents/study-reports/plan-20260512-xxx/...
    """
    # 1. CLI 优先
    raw = cli_arg
    # 2. 环境变量兜底
    if not raw:
        raw = os.environ.get("STUDY_PLANNER_OUTPUT_DIR")
    # 3. 默认：和 plan.json 同目录（向后兼容）
    if not raw:
        return plan_dir

    # 占位符替换
    raw = raw.replace("{plan_id}", plan_id or "").replace("{cwd}", os.getcwd())
    out = Path(os.path.abspath(os.path.expanduser(raw)))
    out.mkdir(parents=True, exist_ok=True)
    return out


def find_plan(plan_id: str = None):
    """根据 plan_id 加载 plan.json；不传则取最近的活跃计划。返回 (plan_dict, plan_dir)"""
    if not DATA_ROOT.exists():
        print(f"[ERR] 数据目录不存在: {DATA_ROOT}", file=sys.stderr)
        print("提示：请先用 study-planner 创建一份学习计划", file=sys.stderr)
        sys.exit(1)

    if plan_id:
        plan_file = DATA_ROOT / plan_id / "plan.json"
        if not plan_file.exists():
            print(f"[ERR] 计划不存在: {plan_id}", file=sys.stderr)
            sys.exit(1)
    else:
        # 取最近修改的 plan.json
        plans = sorted(
            DATA_ROOT.glob("*/plan.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not plans:
            print(f"[ERR] {DATA_ROOT} 下没有任何计划", file=sys.stderr)
            sys.exit(1)
        plan_file = plans[0]

    with open(plan_file, "r", encoding="utf-8") as f:
        return json.load(f), plan_file.parent


def get_plan_dir(plan_id: str = None) -> Path:
    """获取计划目录路径"""
    _, plan_dir = find_plan(plan_id)
    return plan_dir


CATEGORY_LABEL = {
    "listening": "听力",
    "reading": "阅读",
    "writing": "写作",
    "speaking": "口语",
    "vocabulary": "词汇",
    "grammar": "语法",
    "review": "复盘",
    "exam": "模考",
    "output": "输出",
    "rest": "休息",
    # —— 编程/技能学习 ——
    "coding": "编码",
    "debug": "调试",
    "algorithm": "算法",
    "deploy": "部署",
    "testing": "测试",
    "weak_focus": "弱项专项",
}


def category_of(task: dict) -> str:
    return CATEGORY_LABEL.get(task.get("category"), task.get("category", "其他"))
