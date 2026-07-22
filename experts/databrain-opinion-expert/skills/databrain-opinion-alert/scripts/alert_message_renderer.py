#!/usr/bin/env python3
"""
alert_message_renderer.py — deterministic alert copy renderer.

The alert message is a high-trust operational artifact: structure and numbers
must be deterministic. This module turns alert_result.json + attribution.json
into the six-section message format defined in `舆情告警模版.md §1.3`.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Optional

WECOM_MAX_CHARS = 4096
SEP = "━━━━━━━━━━━━━━━━━━━━━━━━━━"

LEVEL_BADGE = {
    "P0": ("🔴", "P0"),
    "P1": ("🟠", "P1"),
    "P2": ("🔵", "P2"),
}

CHANNEL_LABEL = {
    "steam": "Steam",
    "google_play": "Google Play",
    "app_store": "App Store",
}

SCOPE_LABEL = {
    "all_reviews": "历史累计",
    "recent_reviews": "近期",
}

LANGUAGE_LABEL_ZH = {
    "en": "英语",
    "english": "英语",
    "ja": "日语",
    "japanese": "日语",
    "ko": "韩语",
    "korean": "韩语",
    "koreana": "韩语",
    "zh-cn": "简中",
    "schinese": "简中",
    "simplified chinese": "简中",
    "zh-tw": "繁中",
    "tchinese": "繁中",
    "traditional chinese": "繁中",
    "de": "德语",
    "german": "德语",
    "fr": "法语",
    "french": "法语",
    "ru": "俄语",
    "russian": "俄语",
    "es": "西语",
    "spanish": "西语",
    "spanish - spain": "西语",
    "pt-br": "葡语",
    "brazilian": "葡语",
    "portuguese - brazil": "葡语",
}

# Fallbacks only. `check_store_score_alerts.py` writes `thresholds_applied` to
# result JSON; renderer prefers that so game-specific overrides stay accurate.
DEFAULT_THRESHOLDS = {
    "steam": {
        "P0": {"absolute_pp": 60, "drop_6h_pp": 5, "baseline": "p5", "min_sample": 100},
        "P1": {"absolute_pp": 75, "drop_6h_pp": 2, "baseline": "p25", "min_sample": 50},
        "P2": {"absolute_pp": 80, "drop_24h_pp": 1, "baseline": "median_7d", "min_sample": 20},
    },
    "google_play": {
        "P0": {"absolute_score": 3.0, "one_star_rate": 0.40, "drop_6h": 0.3,
               "baseline": "p5", "min_sample": 200},
        "P1": {"absolute_score": 3.5, "one_star_rate": 0.25, "drop_6h": 0.1,
               "baseline": "p25", "min_sample": 100},
        "P2": {"absolute_score": 4.0, "drop_24h": 0.05,
               "baseline": "median_7d", "min_sample": 50},
    },
    "app_store": {
        "P0": {"absolute_score": 3.0, "one_star_rate": 0.40, "drop_6h": 0.3,
               "baseline": "p5", "min_sample": 200},
        "P1": {"absolute_score": 3.5, "one_star_rate": 0.25, "drop_6h": 0.1,
               "baseline": "p25", "min_sample": 100},
        "P2": {"absolute_score": 4.0, "drop_24h": 0.05,
               "baseline": "median_7d", "min_sample": 50},
    },
}

TEMPLATES = {
    "steam_all_reviews": Template(
        "$title\n$sep\n"
        "▎一句话总结: $summary\n"
        "▎触发原因:  $trigger_reason\n\n"
        "📊 核心数据\n$core_data\n\n"
        "$attribution_block"
        "$sep\n"
        "首次触发 $first_trigger_time\n"
        "$detail_line"
    ),
    "steam_recent_reviews": Template(
        "$title\n$sep\n"
        "▎一句话总结: $summary\n"
        "▎触发原因: $trigger_reason\n\n"
        "📊 核心数据\n$core_data\n\n"
        "$attribution_block"
        "$sep\n"
        "首次触发 $first_trigger_time\n"
        "$detail_line"
    ),
    "steam_language_slice": Template(
        "$title\n$sep\n"
        "▎一句话总结: $summary\n"
        "▎触发原因: $trigger_reason\n\n"
        "📊 核心数据\n$core_data\n\n"
        "$attribution_block"
        "$sep\n"
        "首次触发 $first_trigger_time\n"
        "$detail_line"
    ),
    "google_play_global_score": Template(
        "$title\n$sep\n"
        "▎一句话总结: $summary\n"
        "▎触发原因: $trigger_reason\n\n"
        "📊 核心数据\n$core_data\n\n"
        "$attribution_block"
        "$sep\n"
        "首次触发 $first_trigger_time\n"
        "$detail_line"
    ),
    "google_play_country_score": Template(
        "$title\n$sep\n"
        "▎一句话总结: $summary\n"
        "▎触发原因: $trigger_reason\n\n"
        "📊 核心数据\n$core_data\n\n"
        "$attribution_block"
        "$sep\n"
        "首次触发 $first_trigger_time\n"
        "$detail_line"
    ),
    "google_play_one_star": Template(
        "$title\n$sep\n"
        "▎一句话总结: $summary\n"
        "▎触发原因: $trigger_reason\n\n"
        "📊 核心数据\n$core_data\n\n"
        "$attribution_block"
        "$sep\n"
        "首次触发 $first_trigger_time\n"
        "$detail_line"
    ),
    "app_store_country_score": Template(
        "$title\n$sep\n"
        "▎一句话总结: $summary\n"
        "▎触发原因: $trigger_reason\n\n"
        "📊 核心数据\n$core_data\n\n"
        "$attribution_block"
        "$sep\n"
        "首次触发 $first_trigger_time\n"
        "$detail_line"
    ),
}


@dataclass
class AlertMessageContext:
    template_key: str
    title: str
    summary: str
    trigger_reason: str
    core_data: list[str]
    attribution_clues: list[str]
    first_trigger_time: str
    detail_url: str
    level: str
    slice_key: str


def is_store_score_result(result: dict) -> bool:
    return "slices" in result and "channel" in result and "scope" in result


def _num(v) -> Optional[float]:
    return v if isinstance(v, (int, float)) else None


def _fmt_int(v) -> str:
    try:
        return f"{int(v):,}"
    except Exception:
        return "0"


def _fmt_metric(v, channel: str, *, delta: bool = False) -> str:
    n = _num(v)
    if n is None:
        return "—"
    if channel == "steam":
        return f"{n:.0f}pp" if delta else f"{n:.0f}%"
    return f"{n:.2f}" if not delta else f"{n:.2f}"


def _metric_name(channel: str, scope: str, slice_label: str = "") -> str:
    if channel == "steam":
        prefix = SCOPE_LABEL.get(scope, "历史累计")
        return f"{slice_label}{prefix}好评率"
    if channel == "google_play":
        return f"{slice_label}历史累计评分"
    if channel == "app_store":
        return f"{slice_label}评分"
    return f"{slice_label}评分"


def _value_key(channel: str) -> str:
    return "score_pp" if channel == "steam" else "score"


def _is_global_slice(s: dict) -> bool:
    return s.get("slice_key") == "__global__"


def _language_display(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return LANGUAGE_LABEL_ZH.get(raw.lower().replace("_", "-"), raw)


def _slice_display_for_title(s: dict, channel: str) -> str:
    if _is_global_slice(s):
        if channel == "google_play":
            return "全球"
        return ""
    label = str(s.get("label") or "")
    if label.endswith(" 语种"):
        return _language_display(s.get("language_code") or label.replace(" 语种", ""))
    return label.replace(" 语区", "区") if label else ""


def _slice_display_for_metric(s: dict) -> str:
    if _is_global_slice(s):
        return "全球"
    label = str(s.get("label") or "")
    if label.endswith(" 语种"):
        return _language_display(s.get("language_code") or label.replace(" 语种", ""))
    if label.endswith(" 语区"):
        return label.replace(" 语区", "区")
    return label


def _parse_time_utc8(ts: str) -> str:
    if not ts:
        return "—"
    try:
        dt = _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        utc8 = _dt.timezone(_dt.timedelta(hours=8))
        return dt.astimezone(utc8).strftime("%H:%M UTC+8")
    except Exception:
        return ts[:16]


def _ranked_triggered_slices(result: dict) -> list[dict]:
    rank = {"P0": 0, "P1": 1, "P2": 2}
    slices = result.get("slices") or []
    triggered = [s for s in slices if s.get("should_push")]
    return sorted(triggered, key=lambda s: rank.get(s.get("level"), 99))


def _thresholds_for(result: dict, level: str) -> dict:
    channel = result.get("channel", "")
    applied = result.get("thresholds_applied") or {}
    return (applied.get(level) or DEFAULT_THRESHOLDS.get(channel, {}).get(level) or {})


def _select_template_key(result: dict, s: dict) -> str:
    channel = result.get("channel", "")
    scope = result.get("scope") or ""
    dims = set(s.get("matched_dims") or [])
    if channel == "steam":
        if not _is_global_slice(s):
            return "steam_language_slice"
        if scope == "recent_reviews":
            return "steam_recent_reviews"
        return "steam_all_reviews"
    if channel == "google_play":
        if "A_one_star_rate" in dims:
            return "google_play_one_star"
        if _is_global_slice(s):
            return "google_play_global_score"
        return "google_play_country_score"
    if channel == "app_store":
        return "app_store_country_score"
    return "google_play_global_score"


def _is_one_star_alert(result: dict, s: dict) -> bool:
    return result.get("channel") == "google_play" and "A_one_star_rate" in set(s.get("matched_dims") or [])


def _top_source_from_attribution(att: dict | None, channel: str, *, scoped: bool = True) -> Optional[str]:
    if not att:
        return None
    dist = att.get("complaint_distribution") or {}
    by_lang = dist.get("by_language") or []
    by_country = dist.get("by_country") or []
    source_kind = "语种" if channel == "steam" and by_lang else "国家"
    top = by_lang[:1] if source_kind == "语种" else by_country[:1]
    if not top:
        return None
    item = top[0]
    ratio = item.get("ratio", 0)
    try:
        pct = int(float(ratio) * 100)
    except Exception:
        pct = 0
    prefix = "新增差评" if scoped else "整体新增差评"
    source_key = _language_display(item.get("key")) if source_kind == "语种" else str(item.get("key", ""))
    return f"{prefix} {pct}% 来自 {source_key} {source_kind}"


def _top_keywords(att: dict | None) -> str:
    if not att:
        return ""
    keywords = att.get("top_keywords") or att.get("keywords") or []
    if not keywords:
        return ""
    pieces = []
    for item in keywords[:3]:
        word = item.get("word") or item.get("keyword") or item.get("key") or ""
        count = item.get("count") or item.get("cnt") or ""
        if word:
            pieces.append(f"{word}({count})" if count != "" else str(word))
    return "· ".join(pieces)


def _summary(result: dict, s: dict, att: dict | None) -> str:
    channel = result.get("channel", "")
    scope = result.get("scope") or ""
    cur = s.get("current") or {}
    prev6 = s.get("previous_6h") or {}
    prev24 = s.get("previous_24h") or {}
    baseline = s.get("baseline") or {}
    dims = set(s.get("matched_dims") or [])
    key = _value_key(channel)
    cur_v = _num(cur.get(key))
    prev_v = _num(prev6.get(key))
    window = "6h"
    if prev_v is None or ("B_drop_6h" not in dims and _num(prev24.get(key)) is not None):
        prev_v = _num(prev24.get(key))
        window = "24h"

    slice_name = "" if _is_global_slice(s) else _slice_display_for_metric(s)
    metric = _metric_name(channel, scope, slice_name)
    pieces: list[str] = []
    one_star = _num(cur.get("one_star_rate"))
    if _is_one_star_alert(result, s) and one_star is not None:
        prev_one = _num(prev6.get("one_star_rate"))
        if prev_one is not None:
            pieces.append(f"过去 6h 新增 1 星占比 {prev_one * 100:.0f}% → {one_star * 100:.0f}%")
        else:
            pieces.append(f"新增 1 星占比飙至 {one_star * 100:.0f}%")
        if "C_below_p25" in dims:
            pieces.append("低于近 30 天常态水平（低于 P25）")
        elif "C_below_p5" in dims:
            pieces.append("创近 30 天最低")

    has_drop_dim = "B_drop_6h" in dims or "B_drop_24h" in dims
    if cur_v is not None and prev_v is not None and has_drop_dim:
        # 新增 1 星占比告警的主语必须是一星占比；评分变化作为补充。
        if _is_one_star_alert(result, s):
            pieces.append(f"评分 {_fmt_metric(prev_v, channel)} → {_fmt_metric(cur_v, channel)}")
        else:
            pieces.append(f"过去 {window} {metric} {_fmt_metric(prev_v, channel)} → {_fmt_metric(cur_v, channel)}")
    elif cur_v is not None:
        pieces.append(f"当前{metric} {_fmt_metric(cur_v, channel)}")

    if (not _is_one_star_alert(result, s)
            and cur_v is not None
            and _num(baseline.get("p5")) is not None
            and cur_v <= baseline["p5"]):
        pieces.append("创近 30 天最低")

    if not _is_one_star_alert(result, s) and "A_one_star_rate" in dims and one_star is not None:
        prev_one = _num(prev6.get("one_star_rate"))
        if prev_one is not None:
            pieces.append(f"1 星占比 {prev_one * 100:.0f}% → {one_star * 100:.0f}%")
        else:
            pieces.append(f"1 星占比飙至 {one_star * 100:.0f}%")

    source = _top_source_from_attribution(att, channel, scoped=_is_global_slice(s))
    if source:
        pieces.append(source)
    else:
        kw = _top_keywords(att)
        if kw:
            pieces.append(f"集中反馈{kw.split('(')[0]}问题")

    return "，".join(pieces) if pieces else "—"


def _baseline_desc(dim: str) -> str:
    if dim.endswith("p5"):
        return "30 天 P5"
    if dim.endswith("p25"):
        return "30 天 P25"
    if dim.endswith("median_7d"):
        return "7 天中位数"
    return "历史基准"


def _trigger_reason(result: dict, s: dict) -> str:
    channel = result.get("channel", "")
    scope = result.get("scope") or ""
    level = s.get("level", "")
    thresholds = _thresholds_for(result, level)
    cur = s.get("current") or {}
    prev6 = s.get("previous_6h") or {}
    prev24 = s.get("previous_24h") or {}
    baseline = s.get("baseline") or {}
    dims = s.get("matched_dims") or []
    key = _value_key(channel)
    cur_v = _num(cur.get(key))

    metric = _metric_name(channel, scope, "" if _is_global_slice(s) else _slice_display_for_metric(s))
    reasons: list[str] = []
    for dim in dims:
        if dim == "A_absolute":
            th = thresholds.get("absolute_pp")
            reasons.append(f"{metric} {_fmt_metric(cur_v, channel)} < {_fmt_metric(th, channel)} 阈值")
        elif dim == "A_absolute_score":
            th = thresholds.get("absolute_score")
            reasons.append(f"{metric} {_fmt_metric(cur_v, channel)} < {_fmt_metric(th, channel)} 阈值")
        elif dim == "A_one_star_rate":
            th = thresholds.get("one_star_rate")
            one = _num(cur.get("one_star_rate"))
            threshold = f"{th * 100:.0f}%" if isinstance(th, (int, float)) else "阈值"
            reasons.append(f"1 星占比 {one * 100:.0f}% > {threshold} 阈值" if one is not None else "1 星占比超过阈值")
        elif dim == "B_drop_6h":
            prev = _num(prev6.get(key))
            th = thresholds.get("drop_6h_pp") if channel == "steam" else thresholds.get("drop_6h")
            drop = prev - cur_v if prev is not None and cur_v is not None else None
            reasons.append(f"6h 下跌 {_fmt_metric(drop, channel, delta=True)} > {_fmt_metric(th, channel, delta=True)} 阈值")
        elif dim == "B_drop_24h":
            prev = _num(prev24.get(key))
            th = thresholds.get("drop_24h_pp") if channel == "steam" else thresholds.get("drop_24h")
            drop = prev - cur_v if prev is not None and cur_v is not None else None
            reasons.append(f"24h 下跌 {_fmt_metric(drop, channel, delta=True)} > {_fmt_metric(th, channel, delta=True)} 阈值")
        elif dim.startswith("C_below_"):
            base_name = dim.replace("C_below_", "")
            base_val = baseline.get(base_name)
            reasons.append(f"{metric} {_fmt_metric(cur_v, channel)} 低于 {_baseline_desc(dim)}（{_fmt_metric(base_val, channel)}）")

    return "，且 ".join(reasons) if reasons else "命中触发条件（详见 HTML 详情页）"


def _core_data(result: dict, s: dict, all_slices: list[dict]) -> list[str]:
    channel = result.get("channel", "")
    scope = result.get("scope") or ""
    cur = s.get("current") or {}
    prev6 = s.get("previous_6h") or {}
    baseline = s.get("baseline") or {}
    dims = set(s.get("matched_dims") or [])
    key = _value_key(channel)
    cur_v = _num(cur.get(key))
    prev_v = _num(prev6.get(key))
    metric = _metric_name(channel, scope, "" if _is_global_slice(s) else _slice_display_for_metric(s))

    lines: list[str] = []
    if cur_v is not None:
        suffix = ""
        if prev_v is not None:
            delta = prev_v - cur_v
            # [Why] 纯绝对阈值触发时常出现 6h 无变化；展示 “↓0pp” 会制造误导。
            if abs(delta) >= 0.005 or "B_drop_6h" in dims:
                arrow = "↓" if delta >= 0 else "↑"
                suffix = f"(6h 前 {_fmt_metric(prev_v, channel)}, {arrow}{_fmt_metric(abs(delta), channel, delta=True)})"
        lines.append(f"●{metric}: {_fmt_metric(cur_v, channel)}{suffix}")

    one = _num(cur.get("one_star_rate"))
    if channel != "steam" and one is not None:
        prev_one = _num(prev6.get("one_star_rate"))
        suffix = ""
        if prev_one is not None:
            diff = one - prev_one
            arrow = "↑" if diff >= 0 else "↓"
            suffix = f"(6h 前 {prev_one * 100:.0f}%, {arrow}{abs(diff) * 100:.0f}pp)"
        label = "新增 1 星占比" if _is_one_star_alert(result, s) else "1 星占比"
        lines.append(f"●{label}: {one * 100:.0f}%{suffix}")

    sample = s.get("sample_in_window", 0)
    avg = ""
    samples = baseline.get("samples")
    if isinstance(samples, int) and samples > 0 and cur.get("count"):
        avg = f"(日均 {int(cur.get('count', 0) / samples):,})"
    count_label = "评论量" if channel == "steam" else "评价量"
    lines.append(f"●{count_label}: 6h 新增 {_fmt_int(sample)} 条{avg}")

    if _is_global_slice(s):
        triggered_slices = [
            x for x in all_slices
            if not _is_global_slice(x) and x.get("should_push") and x.get("level") != "OK"
        ]
        if triggered_slices:
            pieces = []
            for x in triggered_slices[:5]:
                label = _slice_display_for_metric(x) or str(x.get("slice_key") or "")
                value = (x.get("current") or {}).get(key)
                pieces.append(f"{label} {_fmt_metric(value, channel)}({x.get('level')})")
            suffix = f" 等 {len(triggered_slices)} 个" if len(triggered_slices) > len(pieces) else ""
            lines.append(f"●同时触发切片: {'、'.join(pieces)}{suffix}")

    if not _is_global_slice(s):
        global_slice = next((x for x in all_slices if _is_global_slice(x)), None)
        if global_slice:
            g_cur = (global_slice.get("current") or {}).get(key)
            g_status = "未触发" if not global_slice.get("should_push") else str(global_slice.get("level", "触发"))
            g_metric = _metric_name(channel, scope, "全球")
            lines.append(f"●{g_metric}: {_fmt_metric(g_cur, channel)}({g_status})")

    return lines


def _attribution_clues(att: dict | None, channel: str) -> list[str]:
    if not att:
        return []
    dist = att.get("complaint_distribution") or {}
    clues: list[str] = []
    by_lang = dist.get("by_language") or []
    by_country = dist.get("by_country") or []
    if channel == "steam" and by_lang:
        vals = " · ".join(
            f"{_language_display(x.get('key'))} {int(float(x.get('ratio', 0)) * 100)}%"
            for x in by_lang[:4]
        )
        clues.append(f"- 整体负面集中语种: {vals}")
    elif by_country:
        vals = " · ".join(f"{x.get('key', '')} {int(float(x.get('ratio', 0)) * 100)}%" for x in by_country[:4])
        clues.append(f"- 负面集中国家: {vals}")

    keywords = _top_keywords(att)
    if keywords:
        clues.append(f"- 高频吐槽: {keywords}")

    reviews = att.get("top_negative_reviews") or []
    if reviews:
        r = reviews[0]
        text = (r.get("snippet") or r.get("text") or r.get("content") or "").strip()
        if not text:
            text = r.get("reviewer") or "代表性差评"
        text = " ".join(text.split())[:80]
        likes = r.get("likes") or r.get("thumbs_up") or r.get("engagement")
        url = r.get("url") or ""
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            review_text = f"[「{text}」]({url})"
        else:
            review_text = f"「{text}」"
        line = f"- 代表差评: {review_text}"
        if likes:
            line += f"· {likes} 票有用"
        clues.append(line)

    if not clues:
        win_h = dist.get("window_hours") or (att.get("window") or {}).get("hours") or 6
        total_negative = dist.get("total_negative", 0)
        try:
            total_negative = int(total_negative)
        except Exception:
            total_negative = 0
        if total_negative <= 0:
            clues.append(
                f"- 最近 {win_h}h 未检索到可归因负面反馈；"
                "本次告警由评分指标触发，可能存在评分窗口与评论窗口不一致、评论入库延迟或低频切片。"
            )
        else:
            clues.append(
                f"- 最近 {win_h}h 检索到 {total_negative} 条负面反馈，"
                "但暂无可展示的来源分布或代表性评论。"
            )

    return clues


def _title(result: dict, s: dict, template_key: str, game_name: str) -> str:
    channel = result.get("channel", "")
    scope = result.get("scope") or ""
    level = s.get("level", "?")
    icon = LEVEL_BADGE.get(level, ("🔔", level))[0]
    channel_label = CHANNEL_LABEL.get(channel, channel)
    title_slice = _slice_display_for_title(s, channel)
    if template_key == "google_play_one_star":
        return f"{icon} [{level}] {game_name} {channel_label} 新增 1 星占比预警"
    metric = _metric_name(channel, scope, title_slice)
    return f"{icon} [{level}] {game_name} {channel_label} {metric}告警"


def _context_for(result: dict, s: dict, att: dict | None, game_name: str, detail_url: str) -> AlertMessageContext:
    template_key = _select_template_key(result, s)
    all_slices = result.get("slices") or []
    return AlertMessageContext(
        template_key=template_key,
        title=_title(result, s, template_key, game_name or result.get("game_id", "")),
        summary=_summary(result, s, att),
        trigger_reason=_trigger_reason(result, s),
        core_data=_core_data(result, s, all_slices),
        attribution_clues=_attribution_clues(att, result.get("channel", "")),
        first_trigger_time=_parse_time_utc8(result.get("evaluated_at", "")),
        detail_url=detail_url or "",
        level=s.get("level", ""),
        slice_key=s.get("slice_key", ""),
    )


def build_alert_contexts(
    result: dict,
    game_name: str,
    attribution: dict | None = None,
    detail_url: str | None = None,
    max_blocks: int = 1,
) -> list[AlertMessageContext]:
    contexts: list[AlertMessageContext] = []
    for s in _ranked_triggered_slices(result)[:max_blocks]:
        contexts.append(_context_for(result, s, attribution, game_name, detail_url or ""))
    return contexts


def _render_context(ctx: AlertMessageContext) -> str:
    template = TEMPLATES[ctx.template_key]
    attribution_block = ""
    if ctx.attribution_clues:
        attribution_block = "🔍 归因线索\n" + "\n".join(ctx.attribution_clues) + "\n"
    # [Why] 企业微信 Markdown 支持链接语法；用可点击文字避免在告警卡片里暴露长 URL。
    detail_url = ctx.detail_url.replace(")", "%29") if ctx.detail_url else ""
    detail_line = f"[查看详情]({detail_url})" if detail_url else "查看详情"
    return template.safe_substitute(
        title=ctx.title,
        sep=SEP,
        summary=ctx.summary,
        trigger_reason=ctx.trigger_reason,
        core_data="\n".join(ctx.core_data),
        attribution_block=attribution_block,
        first_trigger_time=ctx.first_trigger_time,
        detail_line=detail_line,
    ).rstrip()


def render_store_score_message(
    result: dict,
    game_name: str,
    attribution: dict | None = None,
    detail_url: str | None = None,
    max_blocks: int = 1,
) -> str:
    contexts = build_alert_contexts(result, game_name, attribution, detail_url, max_blocks=max_blocks)
    if not contexts:
        return ""
    blocks = [_render_context(ctx) for ctx in contexts]
    extra = max(0, len(_ranked_triggered_slices(result)) - max_blocks)
    if extra:
        blocks[-1] += f"\n…另有 {extra} 个切片触发，详情见 HTML 详情页。"
    msg = "\n\n".join(blocks)
    if len(msg) > WECOM_MAX_CHARS:
        msg = msg[:WECOM_MAX_CHARS - 20] + "\n…（内容已截断）"
    return msg


def validate_alert_message(message: str, *, require_attribution: bool = False) -> list[str]:
    """Return validation errors. Empty list means valid six-section copy."""
    errors: list[str] = []
    if not message.strip():
        return ["message is empty"]
    markers = [
        ("title", r"^[🔴🟠🔵🔔] \[P[0-2]\] .+告警|^[🔴🟠🔵🔔] \[P[0-2]\] .+预警"),
        ("sep_top", SEP),
        ("summary", "▎一句话总结:"),
        ("reason", "▎触发原因:"),
        ("core", "📊 核心数据"),
        ("sep_bottom", SEP),
        ("first_trigger", "首次触发 "),
        ("detail", "查看详情"),
    ]
    pos = -1
    for name, marker in markers:
        if name == "title":
            match = re.search(marker, message, flags=re.MULTILINE)
            idx = match.start() if match else -1
        elif name == "sep_bottom":
            idx = message.find(marker, pos + 1)
        else:
            idx = message.find(marker)
        if idx < 0:
            errors.append(f"missing {name}")
            continue
        if idx < pos:
            errors.append(f"{name} appears out of order")
        pos = idx

    if require_attribution and "🔍 归因线索" not in message:
        errors.append("missing attribution")
    if "▎一句话总结:" in message:
        summary_line = next((ln for ln in message.splitlines() if ln.startswith("▎一句话总结:")), "")
        if not summary_line.replace("▎一句话总结:", "").strip():
            errors.append("summary is empty")
    return errors


def _load_fixture_cases() -> list[dict]:
    path = Path(__file__).resolve().parent / "tests" / "fixtures" / "store_score_message_cases.json"
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def self_test() -> int:
    failures: list[str] = []
    cases = _load_fixture_cases()
    if not cases:
        failures.append("missing golden fixtures")
    for case in cases:
        msg = render_store_score_message(
            case["result"],
            case["game_name"],
            case.get("attribution"),
            case.get("detail_url"),
        )
        errors = validate_alert_message(msg, require_attribution=bool(case.get("attribution")))
        if errors:
            failures.append(f"{case['name']}: validation {errors}")
        for expected in case.get("expected_substrings", []):
            if expected not in msg:
                failures.append(f"{case['name']}: missing {expected!r}")
    print(f"PASS: {len(cases)} renderer golden cases" if not failures else f"FAIL: {len(failures)}")
    for item in failures:
        print(f"  - {item}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(self_test())
