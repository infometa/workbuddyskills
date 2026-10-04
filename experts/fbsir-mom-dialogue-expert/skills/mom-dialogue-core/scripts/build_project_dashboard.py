#!/usr/bin/env python3
"""Build the ordinary-user project dashboard from canonical ledgers."""
from __future__ import annotations

import argparse
import html

from common import assert_project_root, safe_project_path, write_text_atomic
from project_status import collect_state, update_project_status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--summary", default="")
    args = parser.parse_args()
    root = assert_project_root(args.project_dir)
    state = update_project_status(root)
    types: dict[str, int] = {}
    for row in state["visible_sources"]:
        media_type = row.get("media_type", "unknown")
        types[media_type] = types.get(media_type, 0) + 1
    type_text = "、".join(f"{html.escape(name)} {count} 份" for name, count in sorted(types.items())) or "尚未盘点"
    summary = args.summary or "已更新生活资料、人物、故事、媒体、权限和章节的当前状态。"
    cards = [
        (len(state["visible_sources"]), "已盘点资料"),
        (len(state["changed_sources"]), "新增或变化"),
        (len(state["pending_people"]), "人物待确认"),
        (len(state["stories"]), "故事卡"),
        (len(state["pending_media"]), "视频/录音待处理"),
        (len(state["pending_consents"]), "权限待确认"),
        (len(state["chapters"]), "当前章节"),
    ]
    card_html = "".join(
        f'<div class="card"><div class="num">{value}</div><div class="label">{html.escape(label)}</div></div>'
        for value, label in cards
    )
    dashboard = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>福帮手｜项目总览</title>
<style>:root{{--ink:#24354a;--muted:#66788d;--blue:#116dc1;--cyan:#11a7dc;--coral:#e9756d;--cream:#fffaf2;--line:#dbe6ef}}*{{box-sizing:border-box}}body{{margin:0;background:var(--cream);color:var(--ink);font-family:system-ui,-apple-system,'Microsoft YaHei',sans-serif}}main{{max-width:1080px;margin:auto;padding:34px 22px 56px}}h1{{margin:0;font-size:32px}}p{{color:var(--muted);line-height:1.75}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:24px 0}}.card{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:17px;box-shadow:0 5px 18px #19446112}}.num{{font-size:30px;font-weight:750;color:var(--blue)}}.label{{font-size:14px;color:var(--muted)}}section{{margin-top:22px}}.next{{border-left:5px solid var(--coral);background:#fff;padding:18px 20px;border-radius:12px}}code{{background:#eef5fa;padding:2px 5px;border-radius:4px}}</style></head>
<body><main><h1>福帮手</h1><p>从妈妈出发，整理一个家的故事。先看本轮成果，再决定唯一的下一步。</p>
<div class="grid">{card_html}</div>
<section class="card"><h2>资料概览</h2><p>{type_text}</p><p>统计包含 active、modified、pending 与 unreadable 等仍在项目中的有效资料；暂时失联的来源单独保留，不会被误删。</p></section>
<section class="card"><h2>本轮结果</h2><p>{html.escape(summary)}</p><p>来源账：<code>02_素材账/source-ledger.csv</code>　故事卡：<code>08_故事卡/</code>　生活轨迹：<code>06_事件与生活轨迹/</code></p></section>
<section class="next"><strong>推荐下一步：</strong>{html.escape(state['next_step'])}</section>
</main></body></html>"""
    html_path = safe_project_path(root, "00_项目看板/项目总览.html")
    write_text_atomic(html_path, dashboard, project_root=root)
    result_lines = [
        "# 本轮结果",
        "",
        f"已盘点资料：{len(state['visible_sources'])}",
        f"新增或变化：{len(state['changed_sources'])}",
        f"人物待确认：{len(state['pending_people'])}",
        f"故事卡：{len(state['stories'])}",
        f"视频或录音待处理：{len(state['pending_media'])}",
        f"权限待确认：{len(state['pending_consents'])}",
        f"当前章节：{len(state['chapters'])}",
        "",
        f"资料类型：{type_text}",
        "",
        f"推荐下一步：{state['next_step']}",
        "",
    ]
    write_text_atomic(safe_project_path(root, "00_项目看板/本轮结果.md"), "\n".join(result_lines), project_root=root)
    print(f"dashboard: {html_path}")


if __name__ == "__main__":
    main()
