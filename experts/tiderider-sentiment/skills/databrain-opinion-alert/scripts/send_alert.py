#!/usr/bin/env python3
"""
send_alert.py — 把告警结果 JSON 渲染成企业微信 Markdown 并推送。

支持两类输入：
  1) 商店评分告警（check_store_score_alerts.py 输出，含 slices/levels/should_push）
  2) 旧版 KOL / keyword 告警（check_alerts.py 输出，保持向后兼容）

可选合并归因（attribution.py 输出）：
    --attribution_file /tmp/attribution.json

用法
====
    python scripts/send_alert.py \\
        --webhook_url "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx" \\
        --result_file /tmp/alert_result.json \\
        --attribution_file /tmp/attribution.json \\
        --game_name "PUBG Mobile"
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

from alert_message_renderer import (
    WECOM_MAX_CHARS as _WECOM_MAX_CHARS,
    is_store_score_result as _is_store_score_result,
    render_store_score_message,
    self_test as _renderer_self_test,
    validate_alert_message,
)

# ---------------------------------------------------------------------------
# 旧版告警类型（向后兼容）
# ---------------------------------------------------------------------------
_LEGACY_ALERT_TYPE_ZH = {
    "rating": "评分告警",
    "kol": "KOL 热帖告警",
    "keyword": "关键词声量告警",
}

_DIMENSION_LABEL = {
    "mention_spike": "讨论量激增",
    "negative_ratio": "负面占比升高",
    "viral_post": "单帖爆款",
}


def _pct(v: float) -> str:
    try:
        return f"{float(v) * 100:.0f}%"
    except Exception:
        return "0%"


def _top_dist(dist: dict, total: int, limit: int = 3) -> str:
    if not dist:
        return "无数据"
    total = sum(int(v or 0) for v in dist.values()) or total
    if total <= 0:
        return "无数据"
    items = sorted(dist.items(), key=lambda kv: int(kv[1] or 0), reverse=True)[:limit]
    return " · ".join(f"{k} {int(int(v or 0) / total * 100)}%" for k, v in items)


def _keyword_first_time(result: dict) -> str:
    end = (result.get("date_range") or {}).get("end") or ""
    return f"{end} UTC+8" if end else "—"


def _post_title(post: dict) -> str:
    text = (post.get("snippet") or post.get("content") or "").strip()
    return " ".join(text.split())[:80] or "代表高互动帖"


def _post_url(post: dict) -> str:
    url = str(post.get("url") or "").strip()
    if url.startswith(("http://", "https://")):
        return url
    return ""


def _md_link(label: str, url: str) -> str:
    if not url:
        return label
    safe_label = label.replace("[", "\\[").replace("]", "\\]")
    safe_url = url.replace(")", "%29")
    return f"[{safe_label}]({safe_url})"


def _post_title_link(post: dict) -> str:
    return _md_link(_post_title(post), _post_url(post))


def _build_crisis_keyword_message(result: dict, game_name: str) -> str:
    metrics = result.get("metrics") or {}
    attribution = result.get("attribution") or {}
    keywords = result.get("triggered_keywords") or result.get("keywords") or []
    keyword_text = " / ".join(keywords[:4]) if keywords else "风险词"
    level = result.get("level") or "P0"
    label = result.get("crisis_label") or "风险话题"
    mentions = int(metrics.get("mentions") or 0)
    baseline = float(metrics.get("baseline_mentions") or 0)
    multiple = float(metrics.get("multiple") or 0)
    neg_ratio = float(metrics.get("negative_ratio") or 0)
    top_posts = attribution.get("top_posts") or []
    top_post = top_posts[0] if top_posts else {}
    top_keywords = sorted((result.get("today_volumes") or {}).items(), key=lambda kv: kv[1], reverse=True)[:4]
    keyword_hits = " · ".join(f"{k}({v})" for k, v in top_keywords) or keyword_text
    return "\n".join([
        f"🚨 [{level}] {game_name} 风险话题告警 · {label}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"▎一句话总结: {game_name} 相关「{keyword_text}」讨论 {result.get('window_hours', 1)}h 内激增 {mentions:,} 条，(基准 {baseline:.0f} 条,↑{multiple:.0f}倍)，集中出现在 {_top_dist(attribution.get('platform_distribution') or {}, mentions, 2)}",
        "",
        "📊 风险话题",
        f"- 类别: {result.get('crisis_category') or 'risk'} · {label}",
        f"- 命中关键词: {keyword_hits}",
        "",
        "📈 异常信号",
        f"- {result.get('window_hours', 1)}h 提及量: {mentions:,} (基准 {baseline:.0f}, ↑{multiple:.0f}×)",
        f"- 负面情感占比: {_pct(neg_ratio)}",
        f"- 平台分布: {_top_dist(attribution.get('platform_distribution') or {}, mentions)}",
        f"- 地区分布: {_top_dist(attribution.get('language_distribution') or {}, mentions)}",
        "",
        "💬 评论区摘要",
        f"- 主要抱怨: {_post_title(top_post)}",
        f"- 代表高赞评论: \"{_post_title(top_post)}\"({top_post.get('likes', top_post.get('engagement', 0))} 赞)",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"首次触发 {_keyword_first_time(result)}",
    ])


def _build_keyword_message(result: dict, game_name: str) -> str:
    if result.get("is_crisis") and any(d in result.get("triggered_dimensions", []) for d in ("mention_spike", "negative_ratio")):
        return _build_crisis_keyword_message(result, game_name)
    metrics = result.get("metrics") or {}
    attribution = result.get("attribution") or {}
    dims = result.get("triggered_dimensions") or []
    keywords = result.get("triggered_keywords") or result.get("keywords") or []
    keyword_text = " / ".join(keywords[:3]) if keywords else "关键词"
    level = "P1"
    icon = "🔥" if dims == ["viral_post"] else "🟠"
    window = result.get("window_hours", 24)
    mentions = int(metrics.get("mentions") or 0)
    baseline = float(metrics.get("baseline_mentions") or 0)
    multiple = float(metrics.get("multiple") or 0)
    neg_ratio = float(metrics.get("negative_ratio") or 0)
    baseline_neg = float((result.get("baselines") or {}).get("negative_ratio") or 0)
    top_posts = attribution.get("top_posts") or []
    top_post = top_posts[0] if top_posts else {}
    top_engagement = int(metrics.get("top_engagement") or top_post.get("engagement") or 0)
    dim_text = "、".join(_DIMENSION_LABEL.get(d, d) for d in dims) or "关键词命中"

    if dims == ["viral_post"]:
        title = f"{icon} [{level}] {game_name} · {top_post.get('channel_name') or '社媒'} 爆款帖命中 \"{keyword_text}\""
        post_link = _post_title_link(top_post)
        summary = (
            f"帖子互动已达 {top_engagement:,}，超过阈值 {int(result.get('viral_threshold') or 500):,}，"
            f"命中监控关键词 \"{keyword_text}\""
        )
        reason = f"单帖互动量超过阈值 {int(result.get('viral_threshold') or 500):,}"
        body = [
            title,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"▎一句话总结: {summary}",
            f"▎触发原因: {reason}",
            "",
            "📮 帖子信息",
            f"● 平台: {top_post.get('channel_name') or '未知'}",
            f"● 作者: {top_post.get('reviewer') or 'anonymous'}",
            f"● 标题: \"{post_link}\"",
            f"● 发布: {str(top_post.get('comment_time') or '')[:16]} · 互动: 👍 {top_post.get('likes', 0)} · 💬 {top_post.get('replies', 0)}",
            f"● 情感: {top_post.get('sentiment_rating') or '—'}",
            "",
            "🎯 命中关键词",
            f"- 监控词组: {', '.join(result.get('keywords') or [])}",
            f"- 帖子命中: {top_post.get('matched_keywords') or keyword_text}",
            "",
            "🔍 归因线索",
            f"- 平台分布: {_top_dist(attribution.get('platform_distribution') or {}, mentions)}",
            f"- 语种分布: {_top_dist(attribution.get('language_distribution') or {}, mentions)}",
            f"- 代表高互动帖: \"{post_link}\"({top_engagement:,} 互动)",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"首次触发 {_keyword_first_time(result)}",
        ]
        return "\n".join(body)

    title = f"{icon} [{level}] {game_name} · \"{keyword_text}\" 讨论激增"
    summary = (
        f"过去 {window}h 讨论 {mentions:,} 条，是平常水平的 {multiple:.1f} 倍，"
        f"负面占比 {_pct(neg_ratio)}(平常 {_pct(baseline_neg)})"
    )
    reason_bits = []
    if "mention_spike" in dims:
        reason_bits.append(f"讨论量达到 {multiple:.1f}×，超过阈值 {float(result.get('threshold') or 0):.1f}×")
    if "negative_ratio" in dims:
        reason_bits.append(f"负面讨论占比提升 {int((neg_ratio - baseline_neg) * 100)}pp")
    if "viral_post" in dims:
        reason_bits.append(f"存在互动量 {top_engagement:,} 的高互动帖")
    reason = "；".join(reason_bits) if reason_bits else dim_text
    top_keywords = sorted((result.get("today_volumes") or {}).items(), key=lambda kv: kv[1], reverse=True)[:3]
    hot_topics = " · ".join(f"{k}({v})" for k, v in top_keywords) or keyword_text
    representative = _post_title_link(top_post)
    body = [
        title,
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"▎一句话总结: {summary}",
        f"▎触发原因: {reason}",
        "",
        "📊 核心数据",
        f"● 讨论量: {mentions:,} 条(平常 {baseline:.1f} 条,↑{multiple:.1f}×)",
        f"● 负面占比: {_pct(neg_ratio)}(平常 {_pct(baseline_neg)},↑{int((neg_ratio - baseline_neg) * 100)}pp)",
        f"● 窗口: {window}h · 灵敏度: {result.get('sensitivity', 'medium')}",
        "",
        "🔍 归因线索",
        f"- 平台分布: {_top_dist(attribution.get('platform_distribution') or {}, mentions)}",
        f"- 语种分布: {_top_dist(attribution.get('language_distribution') or {}, mentions)}",
        f"- 热议话题: {hot_topics}",
        f"- 代表高互动帖: {top_post.get('channel_name') or '未知'} · \"{representative}\"，{top_engagement:,} 互动",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"首次触发 {_keyword_first_time(result)}",
    ]
    return "\n".join(body)


# ---------------------------------------------------------------------------
# 旧版（KOL / keyword / rating）渲染——保持向后兼容
# ---------------------------------------------------------------------------
def _build_legacy_message(result: dict, game_name: str) -> str:
    alert_type = result.get("alert_type", "unknown")
    type_zh = _LEGACY_ALERT_TYPE_ZH.get(alert_type, alert_type)
    triggered = result.get("triggered", False)
    date_range = result.get("date_range", {})
    start = date_range.get("start", "")
    end = date_range.get("end", "")
    date_str = start if start == end else f"{start} ~ {end}"
    detail = result.get("detail", "")

    status_icon = "⚠️" if triggered else "✅"
    status_text = "触发告警" if triggered else "正常（未触发）"

    lines = [
        f"## {status_icon} 舆情告警 · {type_zh}",
        f"**游戏**：{game_name or result.get('game_id', '')}",
        f"**时间**：{date_str}",
        f"**状态**：{status_text}",
        "",
        detail,
    ]
    if alert_type == "rating" and triggered:
        rows = result.get("rows", [])
        if rows:
            r = rows[0]
            lines += [
                "",
                f"> 好评率 {result.get('current_value', 0):.1f}% | "
                f"总评论 {r.get('total_count', 0)} 条 | "
                f"正面 {r.get('positive_count', 0)} 条 | "
                f"负面 {r.get('negative_count', 0)} 条",
            ]
    elif alert_type == "kol" and triggered:
        rows = result.get("rows", [])[:3]
        if rows:
            lines += ["", "**Top 帖子**："]
            for i, r in enumerate(rows, 1):
                content_preview = (r.get("content") or "")[:80].replace("\n", " ")
                lines.append(
                    f"{i}. [{r.get('channel','')}] engagement={r.get('engagement',0)} | "
                    f"{content_preview}..."
                )
    elif alert_type == "keyword" and triggered:
        triggered_kws = result.get("triggered_keywords", [])
        today_vol = result.get("today_volumes", {})
        baselines = result.get("baselines", {})
        if triggered_kws:
            lines += ["", "**触发关键词**："]
            for kw in triggered_kws:
                vol = today_vol.get(kw, 0)
                avg = baselines.get(kw, 0)
                multiple = f"{vol / avg:.1f}×" if avg > 0 else "首次出现"
                lines.append(f"- `{kw}`：今日 {vol} 条 / 均值 {avg:.1f} 条（{multiple}）")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Webhook 推送
# ---------------------------------------------------------------------------
# [Why] 仅允许企业微信官方 Webhook 域名，避免 SSRF（file:// / localhost / 内网 IP 等）。
_ALLOWED_WEBHOOK_PREFIX = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"


def _validate_webhook_url(url: str) -> None:
    if not url.startswith(_ALLOWED_WEBHOOK_PREFIX):
        raise ValueError(
            f"webhook_url 必须以 {_ALLOWED_WEBHOOK_PREFIX} 开头，"
            f"拒绝 {url[:60]!r}"
        )


def _send_to_webhook(webhook_url: str, content: str) -> bool:
    _validate_webhook_url(webhook_url)
    chunks = [content[i:i + _WECOM_MAX_CHARS] for i in range(0, len(content), _WECOM_MAX_CHARS)]
    success = True
    for idx, chunk in enumerate(chunks, 1):
        if len(chunks) > 1:
            chunk = f"（{idx}/{len(chunks)}）\n" + chunk
        payload = json.dumps(
            {"msgtype": "markdown", "markdown": {"content": chunk}},
            ensure_ascii=False,
        ).encode("utf-8")
        req = Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            resp = urlopen(req, timeout=15)
            body = json.loads(resp.read().decode("utf-8"))
            if body.get("errcode", -1) != 0:
                print(f"[WARN] Webhook 返回错误: {body}", file=sys.stderr)
                success = False
            else:
                print(f"[INFO] 推送成功（第 {idx} 段）", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] 推送失败: {e}", file=sys.stderr)
            success = False
    return success


def _generate_detail_html(
    result: dict,
    attribution: dict | None,
    game_name: str,
    html_dir: str = "/tmp",
) -> str | None:
    """
    生成 HTML 详情页并返回 file:// URL。失败返回 None（不影响主推送）。
    [Why] 仅在商店评分告警场景生成；旧版 KOL/keyword 不生成。
    """
    try:
        # 延迟 import：让旧版 KOL 告警场景下不强制依赖 render_html
        from render_html import render_to_file
        gid = result.get("game_id", "noid")
        ch = result.get("channel", "noch")
        ts = time.strftime("%Y%m%d-%H%M%S")
        out = Path(html_dir) / f"alert_{gid}_{ch}_{ts}.html"
        return render_to_file(result, attribution, game_name, str(out))
    except Exception as e:
        print(f"[WARN] HTML 生成失败：{e}", file=sys.stderr)
        return None


def _publish_detail_html_to_gallery(
    file_url: str,
    result: dict,
    game_name: str,
) -> str | None:
    """[Why] 使用当前用户 token 发布详情页，让告警消息里有可访问链接。"""
    if not file_url.startswith("file://"):
        return None
    html_path = file_url[len("file://"):]
    if not html_path:
        return None

    script = Path(__file__).resolve().parent / "publish_gallery_html.py"
    channel = result.get("channel", "")
    title = f"{game_name or result.get('game_id', '')} {channel} alert detail".strip()
    name_cn = f"{game_name or result.get('game_id', '')} 告警详情"[:40]
    name_en = title[:60] if title else "Databrain Alert Detail"
    cmd = [
        sys.executable,
        str(script),
        "--file",
        html_path,
        "--title",
        title or "Databrain Alert Detail",
        "--name-cn",
        name_cn,
        "--name-en",
        name_en,
        "--desc-cn",
        "databrain-opinion-alert 自动生成的告警详情页",
        "--desc-en",
        "Alert detail page generated by databrain-opinion-alert",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240, check=False)
    except Exception as exc:
        print(f"[WARN] AI Gallery 发布失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        return None
    if proc.returncode != 0:
        msg = (proc.stdout or proc.stderr or "").strip()
        print(f"[WARN] AI Gallery 发布失败：{msg}", file=sys.stderr)
        return None
    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:
        print(f"[WARN] AI Gallery 发布响应解析失败：{exc}; raw={proc.stdout[:300]!r}", file=sys.stderr)
        return None
    display_url = payload.get("display_url")
    if isinstance(display_url, str) and display_url:
        print(f"[INFO] AI Gallery 详情页：{display_url}", file=sys.stderr)
        return display_url
    print(f"[WARN] AI Gallery 发布未返回 display_url：{payload}", file=sys.stderr)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="推送舆情告警到企业微信 Webhook")
    parser.add_argument("--webhook_url", required=False, default="",
                        help="企业微信 Webhook URL，多个用 ; 分隔；不传则只渲染、不推送（用于预览）")
    parser.add_argument("--result_file", default="/tmp/alert_result.json")
    parser.add_argument("--attribution_file", default="",
                        help="可选，attribution.py 输出 JSON 路径，仅商店评分告警使用")
    parser.add_argument("--game_name", default="")
    parser.add_argument("--preview_only", action="store_true",
                        help="只打印渲染结果，不发送")
    parser.add_argument("--no_html", action="store_true",
                        help="不生成 HTML 详情页（默认生成到 /tmp）")
    parser.add_argument("--no_gallery", action="store_true",
                        help="不使用当前用户 token 上传 AI Gallery；仅保留本地 HTML 或 --detail_url_base 链接")
    parser.add_argument("--html_dir", default="/tmp",
                        help="HTML 详情页输出目录（默认 /tmp）")
    parser.add_argument("--detail_url_base", default="",
                        help="如已自行托管详情页，传 base URL 前缀；为空时默认用当前用户 token 上传 AI Gallery")
    parser.add_argument("--self_test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    try:
        with open(args.result_file, encoding="utf-8") as f:
            result = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] result_file not found: {args.result_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in result_file: {e}", file=sys.stderr)
        sys.exit(1)

    attribution = None
    if args.attribution_file:
        try:
            with open(args.attribution_file, encoding="utf-8") as f:
                attribution = json.load(f)
        except Exception as e:
            print(f"[WARN] 读取 attribution_file 失败：{e}", file=sys.stderr)

    if _is_store_score_result(result):
        if not result.get("triggered"):
            print("[INFO] triggered=false，无需推送。", file=sys.stderr)
            print("✅ 未触发告警，无需推送。")
            return
        detail_url: str | None = None
        if not args.no_html:
            file_url = _generate_detail_html(result, attribution, args.game_name, args.html_dir)
            if file_url:
                if args.detail_url_base:
                    fname = file_url.rsplit("/", 1)[-1]
                    base = args.detail_url_base.rstrip("/")
                    detail_url = f"{base}/{fname}"
                elif not args.no_gallery:
                    detail_url = _publish_detail_html_to_gallery(file_url, result, args.game_name) or file_url
                else:
                    detail_url = file_url
                print(f"[INFO] 详情页：{detail_url}", file=sys.stderr)
        message = render_store_score_message(result, args.game_name, attribution, detail_url)
        validation_errors = validate_alert_message(message, require_attribution=bool(attribution))
        if validation_errors:
            print(f"[ERROR] 告警文案格式校验失败：{validation_errors}", file=sys.stderr)
            sys.exit(1)
    else:
        if not result.get("triggered"):
            print("[INFO] triggered=false，无需推送。", file=sys.stderr)
            print("✅ 未触发告警，无需推送。")
            return
        if result.get("alert_type") == "keyword" and result.get("version") == "keyword_v2" and not result.get("should_push", True):
            print("[INFO] keyword should_push=false，仍在静默期，无需推送。", file=sys.stderr)
            print("✅ 关键词告警仍在静默期，无需推送。")
            return
        if result.get("alert_type") == "keyword" and result.get("version") == "keyword_v2":
            message = _build_keyword_message(result, args.game_name)
        else:
            message = _build_legacy_message(result, args.game_name)

    if not message:
        print("[INFO] 渲染结果为空，无需推送。", file=sys.stderr)
        return

    if args.preview_only or not args.webhook_url:
        print("=== Preview ===")
        print(message)
        print("=== End ===")
        return

    webhooks = [u.strip() for u in args.webhook_url.split(";") if u.strip()]
    all_ok = True
    for webhook in webhooks:
        if not _send_to_webhook(webhook, message):
            all_ok = False

    if all_ok:
        print(f"[INFO] 已推送到 {len(webhooks)} 个 Webhook。", file=sys.stderr)
        print(f"✅ 告警已推送到 {len(webhooks)} 个企业微信群。")
    else:
        print("[WARN] 部分 Webhook 推送失败，请检查 URL 是否有效。", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Self test
# ---------------------------------------------------------------------------
def _self_test() -> int:
    print("=== send_alert renderer self test ===")
    failures: list[str] = []

    def _check(name, ok, detail=""):
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {detail}")
            failures.append(name)

    fake = {
        "channel": "google_play",
        "scope": None,
        "evaluated_at": "2026-05-07T17:30:00+00:00",
        "triggered": True,
        "any_p0": True,
        "slices": [
            {
                "slice_key": "__global__",
                "label": "全球",
                "level": "P0",
                "matched_dims": ["A_one_star_rate", "B_drop_6h"],
                "current": {"score": 3.42, "one_star_rate": 0.45},
                "baseline": {"p5": 4.10, "median_7d": 4.30},
                "sample_in_window": 587,
                "should_push": True,
                "push_reason": "first_trigger",
            },
            {
                "slice_key": "country_us",
                "label": "us 区",
                "level": "P1",
                "matched_dims": ["B_drop_6h"],
                "current": {"score": 3.7, "one_star_rate": 0.20},
                "baseline": {"p5": 4.0, "median_7d": 4.2},
                "sample_in_window": 220,
                "should_push": True,
                "push_reason": "first_trigger",
            },
            {
                "slice_key": "country_jp",
                "label": "jp 区",
                "level": "OK",
                "matched_dims": [],
                "current": {"score": 4.5},
                "should_push": False,
            },
        ],
    }
    fake_attribution = {
        "complaint_distribution": {
            "total_negative": 412,
            "window_hours": 6.0,
            "by_country": [{"key": "us", "count": 168, "ratio": 0.408},
                           {"key": "br", "count": 73, "ratio": 0.177}],
            "by_language": [{"key": "en", "count": 290, "ratio": 0.704}],
        },
        "top_negative_reviews": [
            {"reviewer": "PlayerOne", "comment_time": "2026-05-07 12:30:00",
             "likes": 153, "replies": 22, "url": "https://play.google.com/r/abc"},
            {"reviewer": "AngryGamer", "comment_time": "2026-05-07 11:50:00",
             "likes": 98, "replies": 17, "url": ""},
        ],
    }

    msg = render_store_score_message(fake, "PUBG Mobile", fake_attribution)
    errors = validate_alert_message(msg, require_attribution=True)
    _check("新版商店评分渲染通过 6 段格式校验", not errors, f"errors={errors}\n{msg[:300]}")
    _check("新版渲染含标题与游戏", "[P0] PUBG Mobile Google Play" in msg, msg[:160])
    _check("新版渲染含核心数据", "📊 核心数据" in msg and "●历史累计评分" in msg, msg[:300])
    _check("新版渲染含归因线索", "🔍 归因线索" in msg and "负面集中国家" in msg, msg[:300])

    empty_attribution = {
        "complaint_distribution": {
            "total_negative": 0,
            "window_hours": 6.0,
            "by_country": [],
            "by_language": [],
        },
        "top_negative_reviews": [],
    }
    msg_empty_attr = render_store_score_message(fake, "PUBG Mobile", empty_attribution)
    errors_empty_attr = validate_alert_message(msg_empty_attr, require_attribution=True)
    _check("归因为空时仍保留归因段并通过校验",
           not errors_empty_attr and "未检索到可归因负面反馈" in msg_empty_attr,
           f"errors={errors_empty_attr}\n{msg_empty_attr[:400]}")

    fake_legacy = {
        "alert_type": "kol", "triggered": True,
        "date_range": {"start": "2026-05-07", "end": "2026-05-07"},
        "detail": "今日 KOL 热帖触达 100w+",
        "rows": [{"channel": "twitter", "engagement": 12000, "content": "this game is buggy"}],
    }
    msg2 = _build_legacy_message(fake_legacy, "Test Game")
    _check("旧版 KOL 渲染兼容", "KOL 热帖" in msg2 and "twitter" in msg2)

    fake_keyword = {
        "alert_type": "keyword",
        "version": "keyword_v2",
        "triggered": True,
        "date_range": {"start": "2026-06-30", "end": "2026-06-30"},
        "window_hours": 1,
        "sensitivity": "medium",
        "threshold": 3.0,
        "viral_threshold": 500,
        "keywords": ["AZ3"],
        "triggered_keywords": ["AZ3"],
        "triggered_dimensions": ["mention_spike", "negative_ratio"],
        "today_volumes": {"AZ3": 127},
        "baselines": {"mention_avg": 30.0, "negative_ratio": 0.30},
        "metrics": {
            "mentions": 127,
            "baseline_mentions": 30.0,
            "multiple": 4.2,
            "negative_ratio": 0.68,
            "top_engagement": 1240,
        },
        "attribution": {
            "platform_distribution": {"Reddit": 54, "X": 31, "Discord": 15},
            "language_distribution": {"美国": 42, "日本": 28, "韩国": 18},
            "top_posts": [{
                "channel_name": "Reddit",
                "reviewer": "u/test",
                "snippet": "AZ3 nuclear plant map is full of campers",
                "engagement": 1240,
                "likes": 856,
                "replies": 384,
                "sentiment_rating": "1",
                "matched_keywords": "az3",
                "url": "https://example.com/post/az3",
            }],
        },
    }
    msg_keyword = _build_keyword_message(fake_keyword, "Delta Force")
    _check("关键词 v2 渲染含归因段",
           "🔍 归因线索" in msg_keyword and "平台分布" in msg_keyword and "AZ3" in msg_keyword,
           msg_keyword[:400])

    fake_viral = dict(fake_keyword)
    fake_viral["triggered_dimensions"] = ["viral_post"]
    msg_viral = _build_keyword_message(fake_viral, "Delta Force")
    _check("单帖爆款帖子标题渲染为链接",
           "[AZ3 nuclear plant map is full of campers](https://example.com/post/az3)" in msg_viral,
           msg_viral[:500])

    fake_crisis = dict(fake_keyword)
    fake_crisis.update({
        "keywords": ["account hacked", "盗号"],
        "triggered_keywords": ["account hacked", "盗号"],
        "is_crisis": True,
        "crisis_category": "data_security",
        "crisis_label": "数据安全",
        "level": "P0",
        "triggered_dimensions": ["mention_spike", "negative_ratio"],
        "today_volumes": {"account hacked": 12, "盗号": 4},
    })
    msg_crisis = _build_keyword_message(fake_crisis, "PUBGM")
    _check("危机词渲染使用专用模板",
           "风险话题告警 · 数据安全" in msg_crisis and "📈 异常信号" in msg_crisis,
           msg_crisis[:400])

    # SSRF 防护
    bad_urls = [
        "file:///etc/passwd",
        "http://localhost/abc",
        "http://169.254.169.254/latest/meta-data",
        "https://evil.example.com/cgi-bin/webhook/send?key=x",
        "https://qyapi.weixin.qq.com.evil.com/cgi-bin/webhook/send?key=x",
    ]
    for u in bad_urls:
        try:
            _validate_webhook_url(u)
            failures.append(f"SSRF 校验未阻止 {u!r}")
            print(f"  ❌ SSRF 校验未阻止 {u!r}")
        except ValueError:
            print(f"  ✅ SSRF 校验阻止 {u[:50]!r}")
    try:
        _validate_webhook_url("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=abc-123")
        print("  ✅ 合法 webhook URL 通过")
    except ValueError as e:
        failures.append(f"合法 URL 被错误阻止：{e}")

    if _renderer_self_test() != 0:
        failures.append("renderer golden tests failed")

    print("\n" + "-" * 40)
    print(f"FAIL: {len(failures)}" if failures else "PASS: all renderer tests")
    if failures:
        print("\n--- 渲染示例 ---")
        print(msg)
    return 1 if failures else 0


if __name__ == "__main__":
    main()
