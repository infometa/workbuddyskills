#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简历诊断编排器 (orchestrate.py)

把「(可选 finalize) -> 注入 LLM 结果 -> build-report -> 渲染 HTML -> 校验」合并到
**单个 Python 进程**里跑完。2026-08-17 提速重构后的调用形态：

  - 上一轮已产出 finalized.json（emit-llm-tasks 的输入）时传 --finalized，
    本脚本直接复用，不再重复跑 finalize；
  - 模型一次批量推理的结果写进**一个** llm.json（{"suggestions":[...],"score":{...}}），
    传 --llm 即可，脚本内部拆成 _suggestions / _gptScore 注入 build-report；
  - 兼容旧接口：--filled + --resume-type 仍可在本脚本内跑 finalize，
    --suggestions / --gpt-score 分文件传参仍可用。

用法：
  python orchestrate.py --resume-id 刘羽茜 \
        --finalized tmp/finalized.json --llm tmp/llm.json \
        --html-out 简历诊断报告_刘羽茜.html --tmp-dir tmp

依赖：本目录下的 resume_pipeline.py（finalize / build-report 子命令）。
"""
import argparse
import html
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent
PIPELINE = BASE / "resume_pipeline.py"
TEMPLATE = BASE.parent / "assets" / "diagnose-report-template.html"

RING_CIRCUMFERENCE = 326.73


def _log(msg: str):
    print(msg, file=sys.stderr, flush=True)


def run_pipeline(subcommand: str, extra_args: list, tmp_dir: Path) -> Path:
    """调用 resume_pipeline.py 的子命令，输出到 tmp 文件，返回输出路径。"""
    out_path = tmp_dir / f"_{subcommand}.json"
    cmd = [
        sys.executable, str(PIPELINE), subcommand,
        "--out", str(out_path),
    ] + extra_args
    _log(f"  ▸ resume_pipeline.py {subcommand}")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(
            f"resume_pipeline.py {subcommand} 失败 (exit={proc.returncode}):\n{proc.stderr}"
        )
    return out_path


def classify_line(line: str):
    """返回 (tag_label, item_css_class, txt_css_class)。"""
    if line.startswith("描述建议"):
        return "描述建议", "t-suggest", "txt suggest-body"
    if "可以为你加分哦" in line:
        return "可加分", "t-nodata", "txt"
    if "是简历中的重要信息，请完善" in line:
        return "需完善", "t-nofill", "txt"
    return "建议", "t-nofill", "txt"


def render_html(report: dict, template_path: Path):
    tpl = template_path.read_text(encoding="utf-8")

    score = report["score"]
    beat = report.get("beatPercent") or "0%"
    ring_offset = round(RING_CIRCUMFERENCE * (1 - score / 100), 2)
    if score >= 70:
        ring_color = "#10b981"
    elif score >= 40:
        ring_color = "#3b6ef6"
    else:
        ring_color = "#f59e0b"

    tpl = tpl.replace("{{RESUME_ID}}", html.escape(str(report.get("resumeId", ""))))
    tpl = tpl.replace("{{GENERATED_AT}}", date.today().strftime("%Y-%m-%d"))
    tpl = tpl.replace("{{SCORE}}", str(score))
    tpl = tpl.replace("{{SCORE_RING_OFFSET}}", f"{ring_offset:.2f}")
    tpl = tpl.replace("{{SCORE_RING_COLOR}}", ring_color)
    tpl = tpl.replace("{{BEAT_TEXT}}", f"击败了 {beat} 的求职者")
    tpl = tpl.replace("{{BEAT_TITLE}}", "你的简历整体表现")

    rows = []
    item_count = 0
    for module in report.get("reportDetails", []):
        items_html = []
        for line in module["diagnoseList"]:
            tag, item_cls, txt_cls = classify_line(line)
            esc = html.escape(line)
            items_html.append(
                f'      <div class="item {item_cls}">\n'
                f'        <span class="tag">{tag}</span>\n'
                f'        <span class="{txt_cls}">{esc}</span>\n'
                f'      </div>'
            )
            item_count += 1
        rows.append(
            '  <div class="module">\n'
            '    <div class="m-head">\n'
            f'      <h2>{html.escape(module["moduleName"])}</h2>\n'
            f'      <span class="badge">{module["diagnoseNum"]} 条</span>\n'
            '    </div>\n'
            '    <div class="m-body">\n'
            + "\n".join(items_html)
            + '\n    </div>\n  </div>'
        )
    module_rows = "\n".join(rows) if rows else '    <div class="empty">暂无诊断明细</div>'
    tpl = tpl.replace("{{MODULE_ROWS}}", module_rows)
    return tpl, item_count


def verify(tpl: str, module_count: int, item_count: int):
    leftover = [p for p in (
        "{{RESUME_ID}}", "{{GENERATED_AT}}", "{{SCORE}}", "{{SCORE_RING_OFFSET}}",
        "{{SCORE_RING_COLOR}}", "{{BEAT_TEXT}}", "{{BEAT_TITLE}}", "{{MODULE_ROWS}}",
    ) if p in tpl]
    if leftover:
        raise RuntimeError(f"HTML 仍存在未替换占位符: {leftover}")
    if not tpl.strip().startswith("<!DOCTYPE html>") or "</html>" not in tpl:
        raise RuntimeError("HTML 结构异常（缺少 DOCTYPE 或 </html>）")
    return {"moduleCount": module_count, "itemCount": item_count}


def _read_json_file(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="简历诊断编排器：(可选 finalize)->build-report->渲染->校验 一步到位")
    ap.add_argument("--resume-id", default="")
    # finalized / filled 二选一：优先 finalized（上一轮 emit-llm-tasks 已用过，避免重复计算）
    ap.add_argument("--finalized", default=None, help="已产出的 finalized.json 路径（优先，跳过 finalize）")
    ap.add_argument("--resume-type", default=None, help="配合 --filled 在本脚本内跑 finalize")
    ap.add_argument("--filled", default=None, help="filled.json 路径（与 --resume-type 连用）")
    # LLM 结果：--llm 单文件合并结果（推荐）；--suggestions/--gpt-score 兼容旧拆分传参
    ap.add_argument("--llm", default=None, help='llm.json 路径，{"suggestions":[...],"score":{...}}')
    ap.add_argument("--suggestions", default=None, help='suggestions.json 路径，含 {"suggestions":[...]}（兼容）')
    ap.add_argument("--gpt-score", default=None, help='gpt_score.json 路径，含 {"score":{...}}（兼容）')
    ap.add_argument("--html-out", required=True, help="最终 HTML 报告输出路径")
    ap.add_argument("--template", default=str(TEMPLATE), help="HTML 模板路径")
    ap.add_argument("--tmp-dir", default=None, help="中间产物目录（默认自动创建并清理）")
    ap.add_argument("--keep-tmp", action="store_true", help="保留中间产物（调试用）")
    args = ap.parse_args()

    if not args.finalized and not (args.filled and args.resume_type):
        ap.error("需要 --finalized，或 --filled + --resume-type")

    tmp_dir = Path(args.tmp_dir) if args.tmp_dir else Path(args.html_out).resolve().parent / "._diag_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    ok = False

    try:
        _log(f"[orchestrate] 输入: finalized={args.finalized or '-'}, filled={args.filled or '-'}")

        # ---- Phase 1c: finalize（仅在未提供 finalized 时执行）----
        if args.finalized:
            finalized_path = Path(args.finalized)
        else:
            finalized_path = run_pipeline(
                "finalize",
                ["--resume-type", args.resume_type, "--filled", args.filled],
                tmp_dir,
            )
        finalized = json.loads(finalized_path.read_text(encoding="utf-8"))

        # ---- 注入 LLM 结果（--llm 合并文件优先，其次兼容拆分文件）----
        if args.llm:
            llm = _read_json_file(args.llm)
            if "suggestions" in llm:
                finalized["_suggestions"] = {"suggestions": llm.get("suggestions") or []}
            if "score" in llm:
                finalized["_gptScore"] = {"score": llm.get("score") or {}}
        if args.suggestions:
            finalized["_suggestions"] = _read_json_file(args.suggestions)
        if args.gpt_score:
            finalized["_gptScore"] = _read_json_file(args.gpt_score)
        merged_path = tmp_dir / "_merged.json"
        merged_path.write_text(json.dumps(finalized, ensure_ascii=False, indent=2), encoding="utf-8")

        # ---- Phase 4: build-report ----
        report_path = run_pipeline(
            "build-report",
            ["--finalized", str(merged_path), "--resume-id", args.resume_id],
            tmp_dir,
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))

        # ---- Phase 5: 渲染 + 校验 ----
        html_out, item_count = render_html(report, Path(args.template))
        verify(html_out, len(report.get("reportDetails", [])), item_count)
        out_path = Path(args.html_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html_out, encoding="utf-8")

        _log(f"[orchestrate] 完成 -> {out_path}  ({out_path.stat().st_size} bytes)")
        # 摘要输出到 stdout（结构化，便于 agent 直接读取）
        summary = {
            "score": report["score"],
            "beatPercent": report.get("beatPercent"),
            "moduleCount": len(report.get("reportDetails", [])),
            "itemCount": item_count,
            "htmlPath": str(out_path),
        }
        print(json.dumps(summary, ensure_ascii=False))
        ok = True
    finally:
        # 仅成功后清理（成功 -> 零残留）；失败时保留 tmp 便于排障重跑，避免输入文件被误删
        if ok and not args.keep_tmp and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
