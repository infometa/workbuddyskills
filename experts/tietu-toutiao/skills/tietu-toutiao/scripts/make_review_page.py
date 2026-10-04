#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_review_page.py — 审核页生成器（可选出口，单文件静态 HTML，零端口）

把 content-state 与已渲染头图打包成**一个自包含的 review.html**：
  - 图片默认 base64 内嵌（单文件可直接发送/双击打开）；--no-embed 改用相对路径；
  - 展示入选条目、落选条目及理由、综合标题警示（如 state 标注了
    synthesized_headline:true 会显眼提示）；
  - 表单只有两件事：选一个方案（A/B/C/D）+ 填修改意见；
  - 「生成审核回执」把选择序列化为一段 JSON 文本，复制贴回 WorkBuddy 会话，
    由专家转结构化 patch——**零后端、零端口、零外部 CDN**。

用法：
  python make_review_page.py --state content-state.json \
      --covers cover_authoritative.png cover_visual.png cover_digest.png \
      --output review.html [--no-embed]
"""

import argparse
import base64
import html
import json
import sys
from pathlib import Path

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>贴图头条 · 审核页</title>
<style>
  :root {{ --ink:#1a1a1a; --paper:#f7f5f0; --card:#ffffff; --accent:#8c1f28; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:24px; font-family:"Microsoft YaHei","PingFang SC",sans-serif;
         background:var(--paper); color:var(--ink); line-height:1.6; }}
  h1 {{ font-size:20px; border-bottom:3px double var(--accent); padding-bottom:8px; }}
  .warn {{ background:#fdf3d7; border:1px solid #d8b24a; padding:10px 14px; border-radius:6px; }}
  .grid {{ display:flex; flex-wrap:wrap; gap:18px; margin-top:16px; }}
  .card {{ background:var(--card); border:1px solid #ddd3c4; border-radius:8px; padding:14px; width:320px; }}
  .card img {{ width:100%; height:auto; border:1px solid #eee; }}
  .card h3 {{ margin:8px 0 4px; font-size:15px; }}
  .items, .excluded {{ background:var(--card); border:1px solid #ddd3c4; border-radius:8px;
                       padding:14px 18px; margin-top:14px; max-width:1000px; }}
  .items li {{ margin:4px 0; }}
  .muted {{ color:#777; font-size:13px; }}
  form {{ margin-top:18px; max-width:1000px; background:var(--card); border:1px solid #ddd3c4;
          border-radius:8px; padding:16px 18px; }}
  label {{ display:block; margin:6px 0; }}
  textarea {{ width:100%; min-height:64px; }}
  button {{ padding:8px 18px; background:var(--accent); color:#fff; border:0; border-radius:4px;
            cursor:pointer; font-size:14px; }}
  #receipt {{ width:100%; min-height:120px; margin-top:10px; font-family:monospace; }}
</style>
</head>
<body>
<h1>贴图头条 · 审核页</h1>
{synth_warning}
<div class="items">
  <b>入选条目</b>
  <ul>{items_html}</ul>
</div>
<div class="excluded">
  <b>落选条目及理由</b>
  <ul>{excluded_html}</ul>
</div>
<div class="grid">{cards_html}</div>
<form onsubmit="return makeReceipt()">
  <h3>审核</h3>
  <label>选择方案：
{radios_html}
  </label>
  <label>修改意见（自然语言即可，例如「标题换回原版，主图往左一点」）：<br>
    <textarea id="feedback" placeholder="可留空，仅选择方案"></textarea></label>
  <button type="submit">生成审核回执</button>
  <p class="muted">点上方按钮生成回执 → 全选复制下面文本框 → 贴回 WorkBuddy 会话，由专家转结构化修改。</p>
  <textarea id="receipt" readonly placeholder="回执会出现在这里"></textarea>
</form>
<script>
function makeReceipt() {{
  var sel = document.querySelector('input[name=plan]:checked');
  var r = document.getElementById('receipt');
  if (!sel) {{ r.value = '请先选择一个方案。'; return false; }}
  var receipt = {{
    kind: 'tietu_review_receipt',
    selected_template: sel.value,
    selected_label: sel.dataset.label,
    feedback: document.getElementById('feedback').value.trim()
  }};
  r.value = JSON.stringify(receipt, null, 2);
  r.select();
  return false;
}}
</script>
</body>
</html>"""


def _items_html(state):
    items = state.get("items") or []
    rows = []
    for it in items:
        if not isinstance(it, dict):
            continue
        title = html.escape(str(it.get("headline") or it.get("title") or ""))
        summary = html.escape(str(it.get("summary") or ""))
        source = html.escape(str(it.get("source_label") or it.get("source") or ""))
        weight = it.get("weight")
        rows.append("<li><b>%s</b>（来源：%s，权重：%s）<br><span class=\"muted\">%s</span></li>"
                    % (title, source or "—", weight if weight is not None else "—", summary))
    return "".join(rows) or "<li class=\"muted\">（无条目信息）</li>"


def _excluded_html(state):
    log = state.get("editorial_log") or {}
    excluded = log.get("excluded") or []
    rows = []
    for ex in excluded:
        if not isinstance(ex, dict):
            continue
        title = html.escape(str(ex.get("headline") or ex.get("title") or ex.get("item") or ""))
        reason = html.escape(str(ex.get("reason") or ""))
        rows.append("<li><b>%s</b>：%s</li>" % (title or "（未命名）", reason))
    return "".join(rows) or "<li class=\"muted\">（无落选记录）</li>"


def _cards_and_radios(covers, embed):
    cards, radios = [], []
    letters = "ABCD"
    for i, cover in enumerate(covers):
        p = Path(cover)
        label = "%s · %s" % (letters[i] if i < len(letters) else str(i + 1), p.stem)
        if embed:
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            img_src = "data:image/png;base64,%s" % b64
        else:
            img_src = p.name  # 与 html 同目录的相对路径
        cards.append(
            '<div class="card"><img src="%s" alt="%s"><h3>%s</h3></div>'
            % (img_src, html.escape(label), html.escape(label)))
        radios.append('    <label><input type="radio" name="plan" value="%s" data-label="%s"> %s</label>'
                      % (html.escape(p.stem), html.escape(label), html.escape(label)))
    return "".join(cards), "".join(radios)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build self-contained review.html")
    parser.add_argument("--state", required=True, help="content-state JSON 路径")
    parser.add_argument("--covers", nargs="+", required=True, help="已渲染头图 PNG（可多张）")
    parser.add_argument("--output", required=True, help="输出 review.html 路径")
    parser.add_argument("--no-embed", action="store_true", help="图片用相对路径而非 base64 内嵌")
    args = parser.parse_args(argv)

    state_path = Path(args.state)
    if not state_path.exists():
        print("[REVIEW][ERROR] state 不存在：%s" % state_path, file=sys.stderr)
        return 2
    state = json.loads(state_path.read_text(encoding="utf-8"))

    for cover in args.covers:
        if not Path(cover).exists():
            print("[REVIEW][ERROR] 封面不存在：%s" % cover, file=sys.stderr)
            return 2

    log = state.get("editorial_log") or {}
    synth = ""
    if state.get("synthesized_headline") or log.get("synthesized_headline"):
        synth = ('<p class="warn"><b>警示：</b>本版主标题为编辑合成（synthesized_headline），'
                 '尚未经用户确认，签发前必须核对是否忠于原文。</p>')

    cards_html, radios_html = _cards_and_radios(args.covers, embed=not args.no_embed)
    page = TEMPLATE.format(
        synth_warning=synth,
        items_html=_items_html(state),
        excluded_html=_excluded_html(state),
        cards_html=cards_html,
        radios_html=radios_html,
    )
    out = Path(args.output)
    out.write_text(page, encoding="utf-8")
    print("[REVIEW] 已生成 %s（%.1f KB，%d 张封面）"
          % (out, out.stat().st_size / 1024, len(args.covers)))
    print("[REVIEW] 零端口零后端：双击打开即可；审核回执贴回 WorkBuddy 会话。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
