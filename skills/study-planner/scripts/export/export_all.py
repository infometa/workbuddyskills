#!/usr/bin/env python3
"""
统一导出入口：study-planner 计划导出

设计哲学（v1.3 演化）：
    本 skill 保留五种导出 —— Markdown（屏读 / 复制粘贴）+ HTML 报告
    （屏幕浏览 / 含 SVG 图）+ 每周任务清单 + 每日学习卡片 + 打印版（物理贴墙 / 离线打卡）。
    第三方导出（滴答 / iCal / Notion / 飞书 / Markmap）已砍掉，原因：
    多入口 = 心智断裂、第三方系统的勾选状态不会回流 plan.json，会和
    详见 SKILL.md「导出格式」章节。

v1.3 默认行为变更（与 v1.2 的差异）：
    v1.2：默认只出 2 个文件（md + report）
    v1.3：默认出 4 个文件（md + report + weekly-checklist + daily-cards）
    理由：每周任务清单和每日学习卡片是用户高频需求，默认生成。
    打印版仍按需补（--with-print）。

v1.4 新增：报告输出目录解耦（数据 / 报告分离）
    --output-dir CLI 参数 / STUDY_PLANNER_OUTPUT_DIR env / 默认 plan-dir
    支持占位符 {plan_id} / {cwd}，例如：
        --output-dir './study-reports/{plan_id}'
        STUDY_PLANNER_OUTPUT_DIR='~/Documents/study-reports/{plan_id}'

用法：
    python3 export_all.py [plan_id]                              # 默认：md + report + weekly + daily（写入 plan-dir）
    python3 export_all.py [plan_id] --output-dir ./reports       # 报告写到 ./reports/ 下
    python3 export_all.py [plan_id] --output-dir './reports/{plan_id}'   # 每个计划独立子目录
    python3 export_all.py [plan_id] --with-print                 # 加打印版（HTML + TXT）
    python3 export_all.py [plan_id] --all                        # 等价于 --with-print（向后兼容）
"""
import sys
import argparse
import subprocess
from pathlib import Path

# 默认导出（覆盖 90% 场景）
DEFAULT_EXPORTERS = [
    ("Markdown",   "to_markdown.py"),
    ("HTML 报告",  "to_html_report.py"),
    ("每周任务清单", "to_weekly_checklist.py"),
    ("每日学习卡片", "to_daily_cards.py"),
]

# 按需补充：打印版（HTML + TXT 由同一脚本产出，绑定关系）
PRINT_EXPORTER = ("打印版", "to_print.py")


def main():
    parser = argparse.ArgumentParser(
        description="study-planner 导出（默认：Markdown + HTML 报告 + 每周清单 + 每日卡片）"
    )
    parser.add_argument("plan_id", nargs="?", default=None)
    parser.add_argument(
        "--with-print",
        action="store_true",
        help="额外导出打印版（plan-print.html + plan-print.txt，A4 / 含复选框）",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="导出全部（等价于 --with-print，保留是为了向后兼容）",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "报告输出目录（支持占位符 {plan_id} / {cwd}）；不传则与 plan.json 同目录。"
            "也可用环境变量 STUDY_PLANNER_OUTPUT_DIR 全局配置。"
        ),
    )
    args = parser.parse_args()

    include_print = args.with_print or args.all
    exporters = list(DEFAULT_EXPORTERS)
    if include_print:
        exporters.append(PRINT_EXPORTER)

    here = Path(__file__).parent
    label = "Markdown + HTML 报告 + 每周清单 + 每日卡片 + 打印版" if include_print else "Markdown + HTML 报告 + 每周清单 + 每日卡片"
    print(f"=== study-planner 导出 ({label}) ===\n")
    if args.output_dir:
        print(f"  报告输出目录：{args.output_dir}\n")

    success, fail = 0, 0
    for name, script in exporters:
        cmd = [sys.executable, str(here / script)]
        if args.plan_id:
            cmd.append(args.plan_id)
        if args.output_dir:
            cmd.extend(["--output-dir", args.output_dir])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                print(f"[OK] {name:<15}")
                success += 1
            else:
                print(f"[FAIL] {name:<15}  {r.stderr.strip()[:120]}")
                fail += 1
        except Exception as e:
            print(f"[FAIL] {name:<15}  {e}")
            fail += 1

    print()
    print(f"完成：{success} 成功 / {fail} 失败")
    print()
    print("产物：")
    print("  · plan.md                  屏读 / 复制粘贴友好")
    print("  · plan-report.html           屏幕浏览 · SVG 图 · 阶段节奏 · 对照段")
    print("  · weekly-checklist.md       每周任务清单 · 按周汇总任务")
    print("  · daily-cards/day-XXX.md   每日学习卡片 · 按天生成（时间精度=天时）")
    if include_print:
        print("  · plan-print.html          A4 打印 · 每周一页 · ☐ 复选框 · ★ 弱项标记")
        print("  · plan-print.txt           纯文本兜底（打印场景的备份）")
    else:
        print()
        print("如需打印贴墙（A4 / 每周一页 / ☐ 复选框）：")
        hint_id = args.plan_id or "<plan_id>"
        hint_outdir = f" --output-dir {args.output_dir}" if args.output_dir else ""
        print(f"  python3 {Path(__file__).name} {hint_id} --with-print{hint_outdir}")
    print()
    print("如需把报告输出到独立目录（例如当前工作区下的 reports/）：")
    print("  python3 export_all.py [plan_id] --output-dir ./reports")
    print("  python3 export_all.py [plan_id] --output-dir './study-reports/{plan_id}'")
    print("  STUDY_PLANNER_OUTPUT_DIR='./study-reports/{plan_id}' python3 export_all.py [plan_id]")
    print()
    print("如需导入第三方工具（滴答 / 日历 / Notion / 飞书 / Markmap）：")
    print("  本 skill 不再提供原生导出，请直接复制 plan.md 内容粘贴。")


if __name__ == "__main__":
    main()
