#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_dashboard.py — 本地看板（零连接器、零端口，单文件静态 HTML）

汇总三类数据源生成 dashboard.html：
  1. .tietu_versions/versions.db —— 版本时间线 + 决策记录（SELECT-only 审计查询）
  2. .tietu_inbox/editorial_log.jsonl —— 构建日志统计（通过率、模板频率、auto/manual）
  3. .tietu_inbox/*/NEEDS_HUMAN.md —— 待人工确认清单

任何数据源缺失都降级而不是失败：versions.db 不可用只读 JSONL，
全部缺失则生成「暂无数据」页。file:// 双击即看，不起任何服务。

用法：
  python make_dashboard.py --workspace <工作区根> --output dashboard.html
"""

import argparse
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import version_manager as vm
except ImportError:
    vm = None

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>贴图头条 · 本地看板</title>
<style>
  body {{ font-family:"Microsoft YaHei","PingFang SC",sans-serif; margin:0;
          background:#f7f5f0; color:#1a1a1a; }}
  header {{ background:#8c1f28; color:#fff; padding:14px 24px; }}
  main {{ padding:20px 24px; max-width:1100px; }}
  section {{ background:#fff; border:1px solid #ddd3c4; border-radius:8px;
             padding:14px 18px; margin-bottom:16px; }}
  h2 {{ font-size:16px; margin:4px 0 10px; border-left:4px solid #8c1f28; padding-left:8px; }}
  table {{ border-collapse:collapse; width:100%; font-size:13px; }}
  th, td {{ border-bottom:1px solid #eee; padding:6px 8px; text-align:left; }}
  th {{ color:#666; font-weight:600; }}
  .pill {{ display:inline-block; padding:1px 10px; border-radius:10px; font-size:12px;
           background:#eee; margin-right:6px; }}
  .auto {{ background:#e4efe4; }} .manual {{ background:#fdeaea; }}
  .warn {{ color:#8a5b00; }} .ok {{ color:#2c6b2f; }}
  .muted {{ color:#888; font-size:13px; }}
</style>
</head>
<body>
<header><h1>贴图头条 · 本地看板</h1></header>
<main>
{sections}
</main>
</body>
</html>"""


def _table(headers, rows):
    if not rows:
        return '<p class="muted">（暂无记录）</p>'
    head = "".join("<th>%s</th>" % html.escape(str(h)) for h in headers)
    body = "".join(
        "<tr>%s</tr>" % "".join("<td>%s</td>" % html.escape(str(c)) for c in row)
        for row in rows)
    return "<table><tr>%s</tr>%s</table>" % (head, body)


def _versions_section(workspace):
    rows = []
    note = ""
    if vm is not None:
        try:
            data = vm.db_query(workspace, "SELECT name, timestamp, revision_id, source "
                                           "FROM versions ORDER BY id DESC LIMIT 30")
            rows = [(n, t, rid or "—", s) for (n, t, rid, s) in data]
        except Exception as exc:  # db 缺失/损坏 → 降级
            note = '<p class="muted">versions.db 不可用（%s），仅展示 JSONL 数据。</p>' % html.escape(str(exc))
    return "<section><h2>版本时间线（最近 30）</h2>%s%s</section>" % (
        note, _table(["版本", "时间", "revision", "来源"], rows))


def _decisions_section(workspace):
    rows = []
    if vm is not None:
        try:
            data = vm.db_query(workspace, "SELECT recorded_at, narrative, confirmed_by, channel "
                                          "FROM decisions ORDER BY id DESC LIMIT 20")
            rows = [(t, (n or "")[:60], c or "—", ch) for (t, n, c, ch) in data]
        except Exception:
            pass
    return "<section><h2>决策记录（最近 20）</h2>%s</section>" % _table(
        ["时间", "叙事", "确认人", "渠道"], rows)


def _jsonl_section(inbox_dir):
    jsonl = inbox_dir / "editorial_log.jsonl"
    stats = {"total": 0, "auto": 0, "manual": 0, "passed": 0, "templates": {}}
    rows = []
    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            stats["total"] += 1
            mode = rec.get("mode") or ("auto" if rec.get("auto_review") else "manual")
            stats[mode] = stats.get(mode, 0) + 1
            review = rec.get("review") or {}
            if review.get("passed"):
                stats["passed"] += 1
            for t in (rec.get("templates") or [rec.get("template")]):
                if t:
                    stats["templates"][t] = stats["templates"].get(t, 0) + 1
            rows.append((rec.get("timestamp") or rec.get("built_at") or "—",
                         mode, "✓" if review.get("passed") else "✗"))
    pills = ('<span class="pill">构建 %d</span><span class="pill auto">auto %d</span>'
             '<span class="pill manual">manual %d</span><span class="pill ok">review 通过 %d</span>'
             % (stats["total"], stats.get("auto", 0), stats.get("manual", 0), stats["passed"]))
    tpl = " ".join('<span class="pill">%s ×%d</span>' % (html.escape(k), v)
                   for k, v in sorted(stats["templates"].items()))
    return "<section><h2>构建统计（editorial_log.jsonl）</h2><p>%s %s</p>%s</section>" % (
        pills, tpl, _table(["时间", "模式", "自审"], rows))


def _needs_human_section(inbox_dir):
    rows = []
    if inbox_dir.is_dir():
        for p in sorted(inbox_dir.glob("*/NEEDS_HUMAN.md"), reverse=True):
            first = ""
            for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if ln.strip() and not ln.startswith("#"):
                    first = ln.strip()[:80]
                    break
            rows.append((p.parent.name, first or "（见文件）"))
    body = _table(["日期", "待确认摘要"], rows) if rows else \
        '<p class="muted ok">没有待人工确认项。</p>'
    return "<section><h2>待人工确认（NEEDS_HUMAN）</h2>%s</section>" % body


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build local zero-connector dashboard")
    parser.add_argument("--workspace", default=".", help="工作区根（含 .tietu_versions/.tietu_inbox）")
    parser.add_argument("--output", default="dashboard.html", help="输出 HTML 路径")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).resolve()
    inbox_dir = workspace / ".tietu_inbox"

    sections = "".join([
        _versions_section(workspace),
        _decisions_section(workspace),
        _jsonl_section(inbox_dir),
        _needs_human_section(inbox_dir),
    ])
    out = Path(args.output)
    out.write_text(PAGE.format(sections=sections), encoding="utf-8")
    print("[DASH] 已生成 %s（%.1f KB）" % (out.resolve(), out.stat().st_size / 1024))
    print("[DASH] 零端口：双击或 file:// 打开即可，不起任何服务。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
