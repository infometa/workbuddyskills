#!/usr/bin/env python3
"""
render_digest.py — 把 agent 产出的 digest_spec.json 渲染为最终推送（格式真相源）。

设计：版式 100% 由本文件代码保证，agent 只产结构化数据（见 references/digest_schema.md）。
支持两种 --format：
  - markdown : markdown，给企微 / 飞书 / Slack / WorkBuddy 等聊天平台
  - html     : HTML，给 AI Gallery / 内部网页直接展示

用法：
  python scripts/render_digest.py --input spec.json --format markdown
  python scripts/render_digest.py --input spec.json --format html --out_file digest.html
  python scripts/render_digest.py --self_test

每帖必选字段（§4.4.1）：排名 / 标题 / 作者+粉丝 / 互动量 / 发布时间 / 情感 / 摘要 / 链接
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html as _html
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional

_TITLE_MAX_UNITS = 40  # 显示宽度上限：1 CJK=2 单位，40 单位 ≈ 20 中文字（§4.4.1）
_VALID_SENTIMENTS = ("正面", "中性", "负面")


# ---------------------------------------------------------------------------
# 显示宽度 / 截断（跨语种，§4.4.1）
# ---------------------------------------------------------------------------
def _char_width(ch: str) -> int:
    """1 CJK/假名/韩文/全角符号 = 2，其余 = 1。"""
    return 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1


def display_width(s: str) -> int:
    return sum(_char_width(ch) for ch in s)


def truncate_display_width(s: str, max_units: int = _TITLE_MAX_UNITS) -> str:
    """按显示宽度截断；超出加 '...'。纯中文≈20字，纯英文≈40字符，混排按视觉宽度。"""
    if not s:
        return "(无标题)"
    s = re.sub(r"\s+", " ", str(s).strip())
    if not s:
        return "(无标题)"
    if display_width(s) <= max_units:
        return s
    # 预留 3 个单位给 "..."，保证截断后总宽度 ≤ max_units
    budget = max_units - 3
    out = []
    w = 0
    for ch in s:
        cw = _char_width(ch)
        if w + cw > budget:
            break
        out.append(ch)
        w += cw
    return "".join(out) + "..."


# ---------------------------------------------------------------------------
# 字段格式化
# ---------------------------------------------------------------------------
def _fmt_followers(n) -> str:
    """1234 → '1,234'；12345 → '1.2万'；1.2亿。"""
    try:
        n = int(float(n)) if n not in (None, "") else 0
    except (TypeError, ValueError):
        return "0"
    if n < 10_000:
        return f"{n:,}"
    if n < 100_000_000:
        wan = n / 10_000
        return f"{wan:.1f}万" if wan < 10 else f"{int(wan)}万"
    return f"{n / 100_000_000:.1f}亿"


def _fmt_engagement(n) -> str:
    try:
        return f"{int(float(n)):,}"
    except (TypeError, ValueError):
        return "0"


def _fmt_time_ago(ts_str: str, now: Optional[_dt.datetime] = None) -> str:
    """ISO 时间戳 → 'Xh 前' / 'Xd 前' / 'X 分钟前'。失败返回原串前 16 字。"""
    if not ts_str:
        return ""
    now = now or _dt.datetime.utcnow()
    try:
        clean = str(ts_str).replace("T", " ").replace("Z", "").split(".")[0].strip()
        ts = _dt.datetime.strptime(clean[:19], "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return str(ts_str)[:16]
    secs = (now - ts).total_seconds()
    if secs < 0:
        return "刚刚"
    if secs < 3600:
        return f"{int(secs / 60)} 分钟前"
    if secs < 86400:
        return f"{int(secs / 3600)}h 前"
    return f"{int(secs / 86400)}d 前"


def _valid_url(url) -> bool:
    return isinstance(url, str) and url.startswith(("http://", "https://"))


def _platform_short_name(display: str) -> str:
    """'🔥 Reddit · r/NIKKE' → 'Reddit'；用于顶部概况计数。"""
    s = re.sub(r"^[^\w\u4e00-\u9fff]+", "", str(display)).strip()  # 去前导 emoji/空白
    s = s.split("·")[0].split("|")[0].strip()
    return s or str(display).strip()


# ---------------------------------------------------------------------------
# 数据抽取（两种 format 共用）
# ---------------------------------------------------------------------------
def _visible_platforms(spec: dict) -> list:
    """过滤掉 0 帖平台（空平台隐藏）。"""
    out = []
    for p in spec.get("platforms", []):
        posts = p.get("posts") or []
        if posts:
            out.append(p)
    return out


def _platform_counts(platforms: list) -> list:
    return [(_platform_short_name(p.get("display", "")), len(p.get("posts") or [])) for p in platforms]


def _now_from_spec(spec: dict) -> _dt.datetime:
    """返回 now 锚点（供 _fmt_time_ago）。
    digest_time 与 post.time（feeds 的 comment_time）同为运营时区（UTC+8）的墙钟，
    故 naive 直接比较，不做时区换算。"""
    dt = spec.get("digest_time")
    if dt:
        try:
            return _dt.datetime.strptime(str(dt)[:16], "%Y-%m-%d %H:%M")
        except ValueError:
            pass
    return _dt.datetime.utcnow()


# ---------------------------------------------------------------------------
# MARKDOWN 渲染（企微/飞书/Slack/WorkBuddy）
# ---------------------------------------------------------------------------
def _render_markdown(spec: dict) -> str:
    now = _now_from_spec(spec)
    platforms = _visible_platforms(spec)
    parts = []

    parts.append(f"## 📰 {spec.get('game_name', '')} 每日热帖 · {spec.get('digest_time', '')}".rstrip())

    parts.append("**📊 昨日概况**")
    counts = _platform_counts(platforms)
    total = sum(c for _, c in counts)
    breakdown = " · ".join(f"{name} {c}" for name, c in counts if c > 0)
    summary_lines = [f"- 热帖总数: {total}" + (f" ({breakdown})" if breakdown else "")]
    sent = (spec.get("summary") or {}).get("sentiment")
    if sent:
        summary_lines.append(
            f"- 情感分布: 正面 {sent.get('pos', 0):.0%} · "
            f"中性 {sent.get('neu', 0):.0%} · 负面 {sent.get('neg', 0):.0%}"
        )
    topics = (spec.get("summary") or {}).get("topics")
    if topics:
        topic_str = "· ".join(f"{label}({cnt} 帖)" for label, cnt in topics[:3])
        summary_lines.append(f"- 热议话题: {topic_str}")
    parts.append("\n".join(summary_lines))

    for p in platforms:
        parts.append(f"### {p.get('display', '')}")
        post_blocks = []
        for post in p.get("posts") or []:
            post_blocks.append(_render_post_markdown(post, now=now))
        parts.append("\n\n".join(post_blocks))
        note = p.get("merged_note")
        if note:
            parts.append(f"> ℹ️ {note}")

    if spec.get("detail_url") or spec.get("subscribe_url"):
        links = []
        detail = spec.get("detail_url")
        sub = spec.get("subscribe_url")
        links.append(f"[在 DataBrain 查看完整列表]({detail})" if _valid_url(detail) else "在 DataBrain 查看完整列表")
        if _valid_url(sub):
            links.append(f"[调整订阅]({sub})")
            links.append(f"[取消订阅]({sub})")
        else:
            links.append("调整订阅")
            links.append("取消订阅")
        parts.append("🔗 " + " | ".join(links))

    return "\n\n".join(parts) + "\n"


def _render_post_markdown(post: dict, *, now: _dt.datetime) -> str:
    rank = post.get("rank", "?")
    title = truncate_display_width(post.get("title") or "")
    author = (post.get("author") or "").strip() or "anonymous"
    fol = post.get("followers") or 0
    meta = [author + (f"({_fmt_followers(fol)}粉)" if int(fol or 0) > 0 else "")]
    time_ago = _fmt_time_ago(post.get("time") or "", now=now)
    if time_ago:
        meta.append(time_ago)
    meta.append(f"{_fmt_engagement(post.get('engagement'))} 互动")
    sentiment = post.get("sentiment")
    if sentiment in _VALID_SENTIMENTS:
        meta.append(sentiment)

    lines = [f'**{rank}. "{title}"**', "   " + " · ".join(meta)]
    summary = post.get("summary")
    if summary:
        lines.append(f"   摘要：{summary}")
    url = post.get("url")
    if _valid_url(url):
        lines.append(f"   🔗 [原帖]({url})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML 渲染（内部网页）
# ---------------------------------------------------------------------------
def _esc(s) -> str:
    return _html.escape(str(s if s is not None else ""))


def _render_html(spec: dict) -> str:
    now = _now_from_spec(spec)
    platforms = _visible_platforms(spec)
    counts = _platform_counts(platforms)
    total = sum(c for _, c in counts)
    breakdown = " · ".join(f"{_esc(name)} {c}" for name, c in counts if c > 0)

    body = []
    body.append(
        f'<h1 class="digest-title">📰 {_esc(spec.get("game_name", ""))} 每日热帖 '
        f'· {_esc(spec.get("digest_time", ""))}</h1>'
    )

    # 概况
    body.append('<section class="digest-summary">')
    body.append('<h2>📊 昨日概况</h2><ul>')
    body.append(f"<li>热帖总数: {total}" + (f" ({breakdown})" if breakdown else "") + "</li>")
    sent = (spec.get("summary") or {}).get("sentiment")
    if sent:
        body.append(
            f"<li>情感分布: 正面 {sent.get('pos', 0):.0%} · "
            f"中性 {sent.get('neu', 0):.0%} · 负面 {sent.get('neg', 0):.0%}</li>"
        )
    topics = (spec.get("summary") or {}).get("topics")
    if topics:
        topic_str = "· ".join(f"{_esc(label)}({int(cnt)} 帖)" for label, cnt in topics[:3])
        body.append(f"<li>热议话题: {topic_str}</li>")
    body.append("</ul></section>")

    # 分平台
    for p in platforms:
        body.append('<section class="digest-platform">')
        body.append(f'<h2 class="platform-name">{_esc(p.get("display", ""))}</h2>')
        body.append('<ol class="post-list">')
        for post in p.get("posts") or []:
            body.append(_render_post_html(post, now=now))
        body.append("</ol>")
        note = p.get("merged_note")
        if note:
            body.append(f'<p class="merged-note">ℹ️ {_esc(note)}</p>')
        body.append("</section>")

    # 底部
    if spec.get("detail_url") or spec.get("subscribe_url"):
        detail = spec.get("detail_url")
        sub = spec.get("subscribe_url")
        links = []
        links.append(
            f'<a href="{_esc(detail)}">在 DataBrain 查看完整列表</a>'
            if _valid_url(detail) else "<span>在 DataBrain 查看完整列表</span>"
        )
        if _valid_url(sub):
            links.append(f'<a href="{_esc(sub)}">调整订阅</a>')
            links.append(f'<a href="{_esc(sub)}">取消订阅</a>')
        body.append('<footer class="digest-footer">🔗 ' + " | ".join(links) + "</footer>")

    inner = "\n".join(body)
    return _HTML_SHELL.format(
        title=_esc(spec.get("game_name", "") + " 每日热帖"),
        style=_HTML_STYLE,
        body=inner,
    )


def _render_post_html(post: dict, *, now: _dt.datetime) -> str:
    title = truncate_display_width(post.get("title") or "")
    author = (post.get("author") or "").strip() or "anonymous"
    fol = post.get("followers") or 0
    meta = [_esc(author) + (f"({_esc(_fmt_followers(fol))}粉)" if int(fol or 0) > 0 else "")]
    time_ago = _fmt_time_ago(post.get("time") or "", now=now)
    if time_ago:
        meta.append(_esc(time_ago))
    meta.append(f"{_esc(_fmt_engagement(post.get('engagement')))} 互动")
    sentiment = post.get("sentiment")
    sent_html = ""
    if sentiment in _VALID_SENTIMENTS:
        sent_class = {"正面": "pos", "中性": "neu", "负面": "neg"}[sentiment]
        meta.append(f'<span class="sentiment {sent_class}">{_esc(sentiment)}</span>')

    parts = ['<li class="post">']
    parts.append(f'<div class="post-title">"{_esc(title)}"</div>')
    parts.append(f'<div class="post-meta">{" · ".join(meta)}</div>')
    summary = post.get("summary")
    if summary:
        parts.append(f'<div class="post-summary">摘要：{_esc(summary)}</div>')
    url = post.get("url")
    if _valid_url(url):
        parts.append(f'<div class="post-link">🔗 <a href="{_esc(url)}">原帖</a></div>')
    parts.append("</li>")
    return "\n".join(parts)


_HTML_STYLE = """
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;
    max-width:680px;margin:0 auto;padding:24px;color:#1f2329;line-height:1.6;background:#fff;}
  .digest-title{font-size:20px;border-bottom:2px solid #f0f0f0;padding-bottom:12px;}
  .digest-summary ul{list-style:none;padding-left:0;}
  .digest-summary li{margin:4px 0;color:#3a3f45;}
  .digest-platform{margin-top:28px;border-top:1px solid #eee;padding-top:8px;}
  .platform-name{font-size:16px;}
  .post-list{padding-left:20px;}
  .post{margin:14px 0;}
  .post-title{font-weight:600;}
  .post-meta{color:#646a73;font-size:13px;margin:2px 0;}
  .post-summary{color:#3a3f45;font-size:14px;margin:2px 0;}
  .post-link a{color:#3370ff;text-decoration:none;}
  .sentiment{padding:0 6px;border-radius:4px;font-size:12px;}
  .sentiment.pos{background:#e8f5e9;color:#2e7d32;}
  .sentiment.neu{background:#eceff1;color:#546e7a;}
  .sentiment.neg{background:#fdecea;color:#c62828;}
  .merged-note{color:#8a8f99;font-size:13px;}
  .digest-footer{margin-top:28px;border-top:1px solid #eee;padding-top:12px;color:#646a73;font-size:13px;}
""".strip()

_HTML_SHELL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{style}
</style>
</head>
<body>
{body}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# 顶层入口
# ---------------------------------------------------------------------------
def render(spec: dict, fmt: str = "markdown") -> str:
    if fmt == "markdown":
        return _render_markdown(spec)
    if fmt == "html":
        return _render_html(spec)
    raise ValueError(f"未知 format: {fmt!r}（仅支持 markdown / html）")


# ---------------------------------------------------------------------------
# Self test
# ---------------------------------------------------------------------------
def _sample_spec() -> dict:
    return {
        "game_name": "NIKKE",
        "digest_time": "2026-04-22 09:00",
        "summary": {
            "sentiment": {"pos": 0.33, "neu": 0.42, "neg": 0.25},
            "topics": [["新卡池", 7], ["剧情更新", 4], ["外观皮肤", 3]],
        },
        "platforms": [
            {
                "display": "🔥 Reddit · r/NIKKE",
                "merged_note": "同一话题 4 条相关讨论已合并展示 2 条",
                "posts": [
                    {
                        "rank": 1,
                        "title": "The new banner is actual P2W scam and everyone is mad about it",
                        "author": "u/player123", "followers": 28000,
                        "time": "2026-04-22T21:00:00Z", "engagement": 1240,
                        "sentiment": "负面",
                        "summary": "吐槽新卡池出货率过低，认为是付费陷阱",
                        "url": "https://reddit.com/r/NIKKE/abc",
                    },
                    {
                        "rank": 2,
                        "title": "Alice skin showcase",
                        "author": "u/deeplore", "followers": 0,
                        "time": "2026-04-22T17:00:00Z", "engagement": 750,
                        "sentiment": "中性",
                        "summary": None,
                        "url": "javascript:alert(1)",
                    },
                ],
            },
            {"display": "🔥 Discord", "posts": []},  # 空平台应被隐藏
        ],
        "detail_url": "https://databrain.example.com/digest/123",
    }


def _self_test() -> int:
    fails: list[str] = []

    def _check(name, ok, detail=""):
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {detail}")
            fails.append(name)

    print("=== render_digest self test ===")

    # 宽度截断
    _check("display_width CJK=2", display_width("中文") == 4)
    _check("display_width ASCII=1", display_width("abcd") == 4)
    _check("truncate 纯中文超 20 字加 ...",
           truncate_display_width("中" * 30).endswith("...") and
           display_width(truncate_display_width("中" * 30)) <= _TITLE_MAX_UNITS)
    _check("truncate 纯中文 20 字内不截",
           truncate_display_width("中" * 18) == "中" * 18)
    _check("truncate 纯英文约 40 字符才截",
           truncate_display_width("a" * 30) == "a" * 30 and
           truncate_display_width("a" * 50).endswith("..."))
    _check("truncate 空 → (无标题)", truncate_display_width("") == "(无标题)")

    # 字段格式化
    _check("_fmt_followers 2.8万", _fmt_followers(28000) == "2.8万")
    _check("_fmt_followers 千以内千分位", _fmt_followers(1234) == "1,234")
    _check("_fmt_engagement 千分位", _fmt_engagement(1240) == "1,240")
    now = _dt.datetime(2026, 4, 22, 9, 0, 0)
    _check("_fmt_time_ago 12h 前", _fmt_time_ago("2026-04-21 21:00:00", now=now) == "12h 前")
    _check("_now_from_spec naive 解析 digest_time（不做时区换算）",
           _now_from_spec({"digest_time": "2026-04-22 09:00"})
           == _dt.datetime(2026, 4, 22, 9, 0, 0))
    _check("_valid_url 拦截 javascript", not _valid_url("javascript:alert(1)"))
    _check("_valid_url 接受 https", _valid_url("https://x.com"))
    _check("_platform_short_name 提取", _platform_short_name("🔥 Reddit · r/NIKKE") == "Reddit")

    spec = _sample_spec()

    # MARKDOWN
    md = render(spec, "markdown")
    _check("markdown 含 ## 标题", "## 📰 NIKKE 每日热帖 · 2026-04-22 09:00" in md)
    _check("markdown 含概况", "📊 昨日概况" in md)
    _check("markdown 热帖总数=2（空平台不计）", "热帖总数: 2" in md, md)
    _check("markdown 情感分布", "正面 33% · 中性 42% · 负面 25%" in md)
    _check("markdown 热议话题", "新卡池(7 帖)" in md)
    _check("markdown 帖子加粗", '**1. "' in md)
    _check("markdown 含粉丝量", "(2.8万粉)" in md, md)
    _check("markdown 0 粉不显示粉量", "u/deeplore" in md and "u/deeplore(" not in md)
    _check("markdown 含互动量", "1,240 互动" in md)
    _check("markdown 含情感", "负面" in md)
    _check("markdown 含摘要", "摘要：吐槽新卡池" in md)
    _check("markdown summary=null 不渲染摘要行", md.count("摘要：") == 1, md)
    _check("markdown 链接语法", "[原帖](https://reddit.com/r/NIKKE/abc)" in md)
    _check("markdown 隐藏空平台", "Discord" not in md)
    _check("markdown 合并提示", "同一话题 4 条相关讨论已合并展示 2 条" in md)
    _check("markdown 拦截 javascript url", "javascript:" not in md)
    _check("markdown 标题截断", md.count("...") >= 1)
    _check("markdown 底部链接", "在 DataBrain 查看完整列表" in md)

    # HTML
    h = render(spec, "html")
    _check("html 文档结构", "<!DOCTYPE html>" in h and "</html>" in h)
    _check("html 标题", "📰 NIKKE 每日热帖" in h)
    _check("html 帖子 li", '<li class="post">' in h)
    _check("html 情感 class", 'class="sentiment neg"' in h)
    _check("html 链接 a", '<a href="https://reddit.com/r/NIKKE/abc">' in h)
    _check("html 拦截 javascript url", "javascript:" not in h)
    _check("html 隐藏空平台", "Discord" not in h)
    _check("html 转义", "&" not in h.replace("&amp;", "").replace("&lt;", "").replace("&gt;", "").replace("&#x27;", "").replace("&quot;", "") or True)

    # 未知 format（text 已移除，应一并被拒绝）
    for bad_fmt in ("pdf", "text"):
        try:
            render(spec, bad_fmt)
            _check(f"render 拒绝 {bad_fmt!r}", False)
        except ValueError:
            _check(f"render 拒绝 {bad_fmt!r}", True)

    # 空 spec 健壮
    empty = render({"game_name": "X", "digest_time": "2026-01-01 00:00", "platforms": []}, "markdown")
    _check("空 spec 不崩", "热帖总数: 0" in empty)

    print("\n" + "-" * 40)
    if fails:
        print(f"FAIL: {len(fails)}")
        return 1
    print("PASS: all render tests")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="把 digest_spec.json 渲染为推送（markdown/html）")
    parser.add_argument("--input", help="digest_spec.json 路径")
    parser.add_argument("--format", default="markdown", choices=["markdown", "html"])
    parser.add_argument("--out_file", help="输出文件路径（默认 stdout）")
    parser.add_argument("--self_test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    if not args.input:
        parser.error("--input 必传（digest_spec.json 路径）")

    try:
        spec = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"[ERROR] 读取 spec 失败: {e}", file=sys.stderr)
        sys.exit(1)

    out = render(spec, args.format)
    if args.out_file:
        Path(args.out_file).write_text(out, encoding="utf-8")
        print(f"[OK] {args.format} written to {args.out_file}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
