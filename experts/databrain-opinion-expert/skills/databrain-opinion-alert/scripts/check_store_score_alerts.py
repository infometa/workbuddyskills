#!/usr/bin/env python3
"""
check_store_score_alerts.py — 商店评分告警主脚本（P0/P1/P2 三级 × 三渠道 × 全切片）。

设计要点
========
* 一次查询取回「全球聚合 + 全部切片」，用同一套 defaults 阈值对每个切片独立评估
* 4 维度 + 样本量门槛：A 绝对水位 / B 相对下跌 / C 历史基准 / 样本量硬条件
* 等级判定从 P0 开始，任一维度命中且样本量达标 → 触发该等级；全不命中 → OK
* 静默期：每个 (game_id, channel, scope, slice_key) 独立维护；升级打破

用法
====
    python scripts/check_store_score_alerts.py \\
        --game_id e7f672beaa5fddd166df98bc046ba4bd4 \\
        --channel steam --scope all_reviews \\
        --output /tmp/alert_result.json

    python scripts/check_store_score_alerts.py --self_test
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from alert_state import (
    DEFAULT_STATE_PATH,
    LEVEL_RANK,
    clear_state,
    load_state,
    make_key,
    record_trigger,
    save_state,
    should_trigger,
)
from report_log import new_session_msg_pair, report
from store_score_query import (
    RateLimitedError,
    one_star_rate,
    query_feeds_window,
    query_steam_history_daily,
    query_steam_snapshot,
    query_store_current,
    query_store_history,
    validate_game_id,
    weighted_score,
)
from thresholds import (
    LEVELS,
    get_channel_thresholds,
    get_silence_seconds,
    get_slicing_config,
    load_thresholds,
)

LEVELS_PO_TO_P2 = ("P0", "P1", "P2")  # 评估顺序：P0 优先

# [Why] 浮点精度容差：避免日级 store_score 30 天稳定不变时，
#       baseline 与 current 完全相等却因浮点尾数被判为"低于"。
_EPS_PP = 0.05      # 百分点单位（Steam 好评率 0~100）
_EPS_SCORE = 0.005  # 评分单位（GP/AS 0~5）


# ---------------------------------------------------------------------------
# Baseline 计算
# ---------------------------------------------------------------------------
def _percentile(values: list[float], p: float) -> Optional[float]:
    """简单线性插值百分位；values 为空返回 None。p 取 0~100。"""
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    if n == 1:
        return s[0]
    idx = (p / 100.0) * (n - 1)
    lo, hi = int(idx), min(int(idx) + 1, n - 1)
    return s[lo] + (s[hi] - s[lo]) * (idx - lo)


def _median(values: list[float]) -> Optional[float]:
    return _percentile(values, 50)


def compute_baseline(history: list[float]) -> dict:
    """
    返回 {"p5": ..., "p25": ..., "median_7d": ..., "samples": N}
    history: 30 天每日值序列（最新在末尾）
    """
    last_7 = history[-7:] if len(history) >= 7 else history
    return {
        "p5": _percentile(history, 5),
        "p25": _percentile(history, 25),
        "median_7d": _median(last_7),
        "samples": len(history),
    }


# ---------------------------------------------------------------------------
# 等级评估
# ---------------------------------------------------------------------------
def _baseline_value(baseline: dict, name: Any) -> Optional[float]:
    if not name:
        return None
    return baseline.get(str(name))


def evaluate_steam_level(
    cur_value_pp: float,             # 好评率 × 100（百分比）
    prev_6h_pp: Optional[float],
    prev_24h_pp: Optional[float],
    baseline: dict,                  # {"p5": pp, "p25": pp, "median_7d": pp, ...} 单位百分比
    sample_in_window: int,
    levels_cfg: dict,                # {"P0": {...}, "P1": {...}, "P2": {...}}
) -> dict:
    """评估 Steam 单切片等级。返回 {level, matched_dims, min_sample}"""
    for lvl in LEVELS_PO_TO_P2:
        cfg = levels_cfg.get(lvl) or {}
        if not cfg:
            continue
        min_sample = cfg.get("min_sample", 0)
        if sample_in_window < min_sample:
            continue

        matched: list[str] = []
        abs_th = cfg.get("absolute_pp")
        if abs_th is not None and cur_value_pp < abs_th - _EPS_PP:
            matched.append("A_absolute")
        drop6_th = cfg.get("drop_6h_pp")
        if drop6_th is not None and prev_6h_pp is not None:
            if (prev_6h_pp - cur_value_pp) >= drop6_th - _EPS_PP:
                matched.append("B_drop_6h")
        drop24_th = cfg.get("drop_24h_pp")
        if drop24_th is not None and prev_24h_pp is not None:
            if (prev_24h_pp - cur_value_pp) >= drop24_th - _EPS_PP:
                matched.append("B_drop_24h")
        bl_name = cfg.get("baseline")
        bl_val = _baseline_value(baseline, bl_name)
        if bl_val is not None and cur_value_pp < bl_val - _EPS_PP:
            matched.append(f"C_below_{bl_name}")

        if matched:
            return {"level": lvl, "matched_dims": matched, "min_sample": min_sample}

    return {"level": "OK", "matched_dims": [], "min_sample": 0}


def evaluate_store_level(
    cur_score: float,                # 0~5
    cur_one_star_rate: float,        # 0~1
    prev_6h_score: Optional[float],
    prev_24h_score: Optional[float],
    baseline: dict,                  # 单位 0~5
    sample_in_window: int,
    levels_cfg: dict,
) -> dict:
    """评估 GP / App Store 单切片等级。"""
    for lvl in LEVELS_PO_TO_P2:
        cfg = levels_cfg.get(lvl) or {}
        if not cfg:
            continue
        min_sample = cfg.get("min_sample", 0)
        if sample_in_window < min_sample:
            continue

        matched: list[str] = []
        abs_th = cfg.get("absolute_score")
        if abs_th is not None and cur_score < abs_th - _EPS_SCORE:
            matched.append("A_absolute_score")
        one_th = cfg.get("one_star_rate")
        if one_th is not None and cur_one_star_rate > one_th + 0.001:
            matched.append("A_one_star_rate")
        drop6_th = cfg.get("drop_6h")
        if drop6_th is not None and prev_6h_score is not None:
            if (prev_6h_score - cur_score) >= drop6_th - _EPS_SCORE:
                matched.append("B_drop_6h")
        drop24_th = cfg.get("drop_24h")
        if drop24_th is not None and prev_24h_score is not None:
            if (prev_24h_score - cur_score) >= drop24_th - _EPS_SCORE:
                matched.append("B_drop_24h")
        bl_name = cfg.get("baseline")
        bl_val = _baseline_value(baseline, bl_name)
        if bl_val is not None and cur_score < bl_val - _EPS_SCORE:
            matched.append(f"C_below_{bl_name}")

        if matched:
            return {"level": lvl, "matched_dims": matched, "min_sample": min_sample}

    return {"level": "OK", "matched_dims": [], "min_sample": 0}


# ---------------------------------------------------------------------------
# Steam 渠道评估
# ---------------------------------------------------------------------------
def _score_field_for_scope(scope: str) -> str:
    return {"all_reviews": "all_reviews_score", "recent_reviews": "recent_reviews_score"}[scope]


def _count_field_for_scope(scope: str) -> str:
    return {"all_reviews": "all_reviews_count", "recent_reviews": "recent_reviews_count"}[scope]


def _to_pp(v: Optional[float]) -> Optional[float]:
    """0~1 → 0~100；None 透传。"""
    return None if v is None else round(v * 100, 2)


STEAM_LANGUAGE_ALIASES = {
    "EN": ["English"],
    "JA": ["Japanese"],
    "KO": ["Korean", "Koreana"],
    "ZH-CN": ["Simplified Chinese", "Schinese"],
    "ZH-TW": ["Traditional Chinese", "TChinese"],
    "DE": ["German"],
    "FR": ["French"],
    "RU": ["Russian"],
    "ES": ["Spanish - Spain", "Spanish"],
    "PT-BR": ["Portuguese - Brazil", "Brazilian"],
}

STEAM_LANGUAGE_CODE_BY_NAME = {
    alias: code
    for code, aliases in STEAM_LANGUAGE_ALIASES.items()
    for alias in aliases
}


def _norm_lang_token(token: Any) -> str:
    return str(token or "").strip().upper().replace("_", "-")


def _resolve_steam_language(token: Any, available: dict) -> tuple[str, str] | None:
    """把配置里的标准代码或 language_reviews 原始 key 解析为 (code, raw_key)。"""
    raw = str(token or "").strip()
    if not raw:
        return None
    if raw in available:
        return STEAM_LANGUAGE_CODE_BY_NAME.get(raw, raw), raw
    code = _norm_lang_token(raw)
    for alias in STEAM_LANGUAGE_ALIASES.get(code, []):
        if alias in available:
            return code, alias
    # 支持自定义维度直接写近似大小写的 language_reviews key
    for key in available:
        if key.lower() == raw.lower():
            return STEAM_LANGUAGE_CODE_BY_NAME.get(key, key), key
    return None


def _iter_steam_language_slices(available: dict, slicing_cfg: dict) -> list[tuple[str, str, dict]]:
    """返回按官方优先级 + 自定义 + 其余语种排序后的 (code, raw_key, data)。"""
    exclude_tokens = slicing_cfg.get("exclude") or []
    excluded: set[str] = set()
    for token in exclude_tokens:
        resolved = _resolve_steam_language(token, available)
        if resolved:
            excluded.add(resolved[1])
        raw = str(token or "").strip()
        if raw in available:
            excluded.add(raw)

    ordered_keys: list[tuple[str, str]] = []
    seen: set[str] = set()
    configured = list(slicing_cfg.get("language_priority") or []) + list(slicing_cfg.get("custom_languages") or [])
    for token in configured:
        resolved = _resolve_steam_language(token, available)
        if not resolved:
            continue
        code, key = resolved
        if key not in seen and key not in excluded:
            ordered_keys.append((code, key))
            seen.add(key)

    if slicing_cfg.get("include_unlisted_languages", True):
        for key in sorted(available):
            if key in seen or key in excluded:
                continue
            ordered_keys.append((STEAM_LANGUAGE_CODE_BY_NAME.get(key, key), key))
            seen.add(key)

    return [(code, key, available[key]) for code, key in ordered_keys]


def evaluate_steam(
    game_id: str,
    scope: str,
    levels_cfg: dict,
    slicing_cfg: dict,
    now: datetime,
) -> dict:
    """评估一个 Steam 渠道（all_reviews 或 recent_reviews），返回 {slices: [...]}"""
    score_field = _score_field_for_scope(scope)
    count_field = _count_field_for_scope(scope)

    # 1) 取当前快照
    snap_now = query_steam_snapshot(game_id, at=now)
    if snap_now is None:
        return {"error": "no_snapshot", "slices": []}

    # 2) 取 6h / 24h 前快照
    snap_6h = query_steam_snapshot(game_id, at=now - timedelta(hours=6))
    snap_24h = query_steam_snapshot(game_id, at=now - timedelta(hours=24))

    # 3) 30 天每日时序（用于 baseline）
    history_rows = query_steam_history_daily(game_id, days=30)

    # 4) 全局评估
    cur_pp = _to_pp(snap_now[score_field])
    prev_6h_pp = _to_pp(snap_6h[score_field]) if snap_6h else None
    prev_24h_pp = _to_pp(snap_24h[score_field]) if snap_24h else None
    history_global = [r[score_field] * 100 for r in history_rows
                      if r.get(score_field, 0) > 0]
    baseline_global = compute_baseline(history_global)
    # Steam 样本量 = 6h 内新增评论数（current.count - 6h前.count）
    sample_global = max(0, snap_now[count_field] - (snap_6h[count_field] if snap_6h else 0))

    slices: list[dict] = []
    eval_global = evaluate_steam_level(
        cur_pp, prev_6h_pp, prev_24h_pp, baseline_global, sample_global, levels_cfg
    )
    slices.append({
        "slice_key": "__global__",
        "label": "全球",
        "level": eval_global["level"],
        "matched_dims": eval_global["matched_dims"],
        "current": {"score_pp": cur_pp, "count": snap_now[count_field]},
        "previous_6h": {"score_pp": prev_6h_pp,
                        "count": snap_6h[count_field] if snap_6h else None,
                        "snapshot_time": snap_6h["create_time"].isoformat() if snap_6h else None},
        "previous_24h": {"score_pp": prev_24h_pp,
                         "count": snap_24h[count_field] if snap_24h else None,
                         "snapshot_time": snap_24h["create_time"].isoformat() if snap_24h else None},
        "baseline": baseline_global,
        # [Why] 详情页 SVG 趋势图需要原始 30 天序列
        "history_values": history_global,
        "sample_in_window": sample_global,
        "min_sample_required": eval_global.get("min_sample", 0),
    })

    # 5) 分语种切片（如果启用）
    if slicing_cfg.get("enabled"):
        cur_langs = snap_now.get("language_reviews") or {}
        prev6_langs = (snap_6h or {}).get("language_reviews") or {}
        prev24_langs = (snap_24h or {}).get("language_reviews") or {}

        for lang_code, lang_name, lang_data in _iter_steam_language_slices(cur_langs, slicing_cfg):
            cur_lang_pp = _to_pp(lang_data.get("score"))
            prev6_lang_pp = _to_pp((prev6_langs.get(lang_name) or {}).get("score")) if prev6_langs else None
            prev24_lang_pp = _to_pp((prev24_langs.get(lang_name) or {}).get("score")) if prev24_langs else None
            cur_count = int(lang_data.get("reviews", 0))
            prev6_count = int((prev6_langs.get(lang_name) or {}).get("reviews", 0)) if prev6_langs else 0
            sample_lang = max(0, cur_count - prev6_count)

            # 分语种 baseline 暂用全球（语种级 30 天历史需要 store_score_steam.language_reviews 30 天解析，
            # 实现成本高且数据稀疏；先用全球基准近似）
            eval_lang = evaluate_steam_level(
                cur_lang_pp, prev6_lang_pp, prev24_lang_pp, baseline_global,
                sample_lang, levels_cfg
            )
            slices.append({
                "slice_key": f"lang_{lang_code}",
                "label": f"{lang_code} 语种",
                "language_code": lang_code,
                "language_raw_key": lang_name,
                "level": eval_lang["level"],
                "matched_dims": eval_lang["matched_dims"],
                "current": {"score_pp": cur_lang_pp, "count": cur_count},
                "previous_6h": {"score_pp": prev6_lang_pp, "count": prev6_count},
                "previous_24h": {"score_pp": prev24_lang_pp},
                "baseline": baseline_global,  # 沿用全局 baseline
                "baseline_note": "切片沿用全局 baseline（语种级历史基准未实现）",
                "sample_in_window": sample_lang,
                "min_sample_required": eval_lang.get("min_sample", 0),
            })

    return {"slices": slices}


# ---------------------------------------------------------------------------
# GP / App Store 渠道评估
# ---------------------------------------------------------------------------
def evaluate_store(
    channel: str,
    game_id: str,
    levels_cfg: dict,
    slicing_cfg: dict,
    now: datetime,
) -> dict:
    """评估 GP 或 App Store 渠道。"""
    # 1) 当前快照（最新一日的 area 分布）
    cur = query_store_current(channel, game_id)
    if not cur.get("date") or not cur.get("by_area"):
        return {"error": "no_snapshot", "slices": []}

    # 2) 30 天全球加权 score 时序（baseline）
    history_rows = query_store_history(channel, game_id, days=30)
    history_global = [r["global_score"] for r in history_rows if r.get("global_score", 0) > 0]
    baseline_global = compute_baseline(history_global)

    # 3) feeds 实时窗口（6h / 24h~6h / 6h 样本量）
    end_6h = now
    start_6h = now - timedelta(hours=6)
    end_24h = now - timedelta(hours=6)
    start_24h = now - timedelta(hours=24)

    feeds_6h = query_feeds_window(channel, game_id, start_6h, end_6h, by="country")
    feeds_24h = query_feeds_window(channel, game_id, start_24h, end_24h, by="country")

    # 4) 全球聚合（按 comments_number 加权）
    by_area = cur["by_area"]
    exclude = set(slicing_cfg.get("exclude") or [])

    total_weight = 0.0
    weighted_sum = 0.0
    total_one_star = 0
    total_count = 0
    for area, data in by_area.items():
        if any(_glob_match(area, p) for p in exclude):
            continue
        comments = data.get("comments_number", 0)
        if comments <= 0:
            continue
        total_weight += comments
        weighted_sum += data.get("store_score", 0) * comments
        cbr = data.get("count_by_rating") or {}
        total_one_star += cbr.get(1, 0)
        total_count += sum(cbr.values())

    cur_global_score = weighted_sum / total_weight if total_weight > 0 else 0.0
    cur_global_one = (total_one_star / total_count) if total_count > 0 else 0.0
    sample_global = feeds_6h["global"]["sample"]

    slices: list[dict] = []
    if _should_emit_global_store_slice(channel):
        # Google Play 模板要求：全球历史累计评分 + 分国家历史累计评分。
        eval_global = evaluate_store_level(
            cur_score=cur_global_score,
            cur_one_star_rate=cur_global_one,
            prev_6h_score=feeds_6h["global"].get("avg_score"),
            prev_24h_score=feeds_24h["global"].get("avg_score"),
            baseline=baseline_global,
            sample_in_window=sample_global,
            levels_cfg=levels_cfg,
        )
        slices.append({
            "slice_key": "__global__",
            "label": "全球",
            "level": eval_global["level"],
            "matched_dims": eval_global["matched_dims"],
            "current": {
                "score": round(cur_global_score, 4),
                "one_star_rate": round(cur_global_one, 4),
                "areas_count": len(by_area),
                "snapshot_date": cur["date"],
            },
            "feeds_6h": _summary_feeds(feeds_6h["global"]),
            "feeds_24h": _summary_feeds(feeds_24h["global"]),
            "baseline": baseline_global,
            # [Why] 详情页 SVG 趋势图需要原始 30 天序列
            "history_values": history_global,
            "sample_in_window": sample_global,
            "min_sample_required": eval_global.get("min_sample", 0),
        })
    # App Store 模板要求按国家独立运行，不做全球均分。这里仍计算 baseline_global
    # 供国家切片临时沿用，但不产出/评估 __global__ 告警切片。

    # 5) 分国家切片
    if slicing_cfg.get("enabled"):
        for area, data in by_area.items():
            if any(_glob_match(area, p) for p in exclude):
                continue
            cbr = data.get("count_by_rating") or {}
            cur_one = one_star_rate(cbr)
            cur_score = data.get("store_score", 0)
            f6 = (feeds_6h.get("by_country") or {}).get(area, {})
            f24 = (feeds_24h.get("by_country") or {}).get(area, {})
            sample_area = int(f6.get("sample", 0))

            eval_area = evaluate_store_level(
                cur_score=cur_score,
                cur_one_star_rate=cur_one,
                prev_6h_score=f6.get("avg_score"),
                prev_24h_score=f24.get("avg_score"),
                baseline=baseline_global,  # 沿用全球 baseline
                sample_in_window=sample_area,
                levels_cfg=levels_cfg,
            )
            slices.append({
                "slice_key": f"country_{area}",
                "label": f"{area} 区",
                "level": eval_area["level"],
                "matched_dims": eval_area["matched_dims"],
                "current": {
                    "score": cur_score,
                    "one_star_rate": round(cur_one, 4),
                    "comments_total": data.get("comments_number", 0),
                },
                "feeds_6h": _summary_feeds(f6),
                "feeds_24h": _summary_feeds(f24),
                "baseline": baseline_global,
                "baseline_note": "切片沿用全球 baseline（国家级历史基准未实现）",
                "sample_in_window": sample_area,
                "min_sample_required": eval_area.get("min_sample", 0),
            })

    return {"slices": slices}


def _summary_feeds(d: dict) -> dict:
    if not d:
        return {"avg_score": None, "sample": 0, "one_star_rate": 0.0}
    return {
        "avg_score": d.get("avg_score"),
        "sample": d.get("sample", 0),
        "one_star_rate": round(d.get("one_star_rate", 0.0), 4),
    }


def _glob_match(s: str, pattern: str) -> bool:
    """支持简单 glob：'lang_*' / 'jp'。空串不匹配任何模式。"""
    if not s:
        return False
    if "*" not in pattern:
        return s == pattern
    if pattern.endswith("*"):
        return s.startswith(pattern[:-1])
    if pattern.startswith("*"):
        return s.endswith(pattern[1:])
    head, tail = pattern.split("*", 1)
    return s.startswith(head) and s.endswith(tail)


def _should_emit_global_store_slice(channel: str) -> bool:
    """Google Play 需要全球聚合；App Store 按国家独立，不产出全球均分切片。"""
    return channel == "google_play"


# ---------------------------------------------------------------------------
# 静默期联动
# ---------------------------------------------------------------------------
def apply_silence(
    state: dict,
    game_id: str,
    channel: str,
    scope: Optional[str],
    eval_result: dict,
    merged_thresholds: dict,
    now: datetime,
    dry_run: bool,
) -> None:
    """对 eval_result 的每个 slice 注入 should_push / push_reason 字段，并更新 state。"""
    for sl in eval_result.get("slices", []):
        key = make_key(game_id, channel, scope, sl["slice_key"])
        level = sl["level"]
        if level == "OK":
            sl["should_push"] = False
            sl["push_reason"] = "level_is_ok"
            clear_state(state, key)
            continue
        silence_s = get_silence_seconds(merged_thresholds, level)
        if dry_run:
            sl["should_push"] = True
            sl["push_reason"] = "dry_run"
            continue
        should, reason = should_trigger(state, key, level, now, silence_s)
        sl["should_push"] = should
        sl["push_reason"] = reason
        if should:
            record_trigger(state, key, level, silence_s, now)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------
def _start_report(message: str) -> threading.Thread:
    session_id, msg_id = new_session_msg_pair()

    def _do():
        try:
            report(message or "databrain-opinion-alert", session_id, msg_id)
        except Exception:
            pass

    t = threading.Thread(target=_do, daemon=False)
    t.start()
    return t


def run_check(
    game_id: str,
    channel: str,
    scope: Optional[str],
    config_path: str,
    state_path: str,
    output_path: str,
    dry_run: bool,
    now: Optional[datetime] = None,
) -> dict:
    """对外可调用入口（便于 self_test 复用）。"""
    if now is None:
        now = datetime.now(timezone.utc)
    validate_game_id(game_id)
    if channel == "steam":
        if scope not in ("all_reviews", "recent_reviews"):
            raise ValueError("steam 渠道 --scope 必填且为 all_reviews/recent_reviews")
    elif channel not in ("google_play", "app_store"):
        raise ValueError(f"不支持的 channel: {channel}")

    merged = load_thresholds(config_path, game_id)
    levels_cfg = get_channel_thresholds(merged, channel, scope)
    slicing_cfg = get_slicing_config(merged, channel)

    if channel == "steam":
        eval_result = evaluate_steam(game_id, scope, levels_cfg, slicing_cfg, now)
    else:
        eval_result = evaluate_store(channel, game_id, levels_cfg, slicing_cfg, now)

    state = load_state(state_path)
    apply_silence(state, game_id, channel, scope, eval_result, merged, now, dry_run)
    if not dry_run:
        save_state(state_path, state)

    triggered_slices = [s for s in eval_result.get("slices", []) if s.get("should_push")]
    any_p0 = any(s["level"] == "P0" for s in triggered_slices)

    result = {
        "game_id": game_id,
        "channel": channel,
        "scope": scope,
        "evaluated_at": now.isoformat(),
        "triggered": len(triggered_slices) > 0,
        "any_p0": any_p0,
        "thresholds_applied": levels_cfg,
        "slicing_config": slicing_cfg,
        "summary": {
            "slices_total": len(eval_result.get("slices", [])),
            "slices_triggered": len(triggered_slices),
            "triggered_levels": sorted({s["level"] for s in triggered_slices}),
        },
        "slices": eval_result.get("slices", []),
        "error": eval_result.get("error"),
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="商店评分告警检查（P0/P1/P2 三级 × 三渠道 × 全切片）")
    parser.add_argument("--game_id", required=False, default="",
                        help="游戏 ID（unified_edition_id），u 开头手游 / e 开头 PC")
    parser.add_argument("--channel", choices=["steam", "google_play", "app_store"],
                        help="渠道")
    parser.add_argument("--scope", choices=["all_reviews", "recent_reviews"],
                        help="仅 channel=steam 必填")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parent.parent / "thresholds.yaml"),
                        help="thresholds.yaml 路径")
    parser.add_argument("--state_file", default=DEFAULT_STATE_PATH, help="静默期状态文件")
    parser.add_argument("--output", default="/tmp/alert_result.json", help="输出 JSON 路径")
    parser.add_argument("--dry_run", action="store_true",
                        help="跳过静默期判定，强制评估并标记 should_push=true")
    parser.add_argument("--message", default="", help="用户原始问题，用于埋点上报")
    parser.add_argument("--self_test", action="store_true", help="跑内置 smoke test")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    if not args.game_id or not args.channel:
        parser.error("需要 --game_id 和 --channel（或使用 --self_test）")

    rt = _start_report(args.message)
    try:
        result = run_check(
            game_id=args.game_id.strip(),
            channel=args.channel,
            scope=args.scope,
            config_path=args.config,
            state_path=args.state_file,
            output_path=args.output,
            dry_run=args.dry_run,
        )
        s = result["summary"]
        print(f"[INFO] triggered={result['triggered']} any_p0={result['any_p0']}",
              file=sys.stderr)
        print(f"评估完成：{s['slices_triggered']}/{s['slices_total']} 个切片触发，"
              f"等级 {s['triggered_levels']}。详情见 {args.output}")
    except RateLimitedError as e:
        print(f"[ERROR] 网关限流，无法完成评估：{e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        rt.join(timeout=1.0)


# ---------------------------------------------------------------------------
# Self test
# ---------------------------------------------------------------------------
def _self_test() -> int:
    """纯逻辑单测：evaluate_*_level 与 baseline 计算（不依赖网关）。"""
    failures: list[str] = []
    print("=== 单元测试：baseline / evaluate_* ===")

    def _check(name, ok, detail=""):
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {detail}")
            failures.append(name)

    # baseline
    bl = compute_baseline([78, 80, 79, 77, 82, 81, 75, 76, 78, 79])
    _check("baseline.median_7d 正确", bl["median_7d"] is not None and 76 <= bl["median_7d"] <= 80,
           f"got {bl}")
    _check("baseline.p5 < p25", bl["p5"] <= bl["p25"], f"got {bl}")

    levels_steam = {
        "P0": {"absolute_pp": 60, "drop_6h_pp": 5, "baseline": "p5", "min_sample": 100},
        "P1": {"absolute_pp": 75, "drop_6h_pp": 2, "baseline": "p25", "min_sample": 50},
        "P2": {"absolute_pp": 80, "drop_24h_pp": 1, "baseline": "median_7d", "min_sample": 20},
    }
    bl_steam = {"p5": 70, "p25": 75, "median_7d": 78}

    # 场景 1：A 命中 P0（绝对水位 55 < 60）
    r = evaluate_steam_level(55, 78, 79, bl_steam, 200, levels_steam)
    _check("S1 P0.A 命中", r["level"] == "P0" and "A_absolute" in r["matched_dims"], f"{r}")

    # 场景 2：B 命中 P0（6h 下跌 8pp >= 5）
    r = evaluate_steam_level(70, 78, 78, bl_steam, 200, levels_steam)
    _check("S2 P0.B 命中", r["level"] == "P0" and "B_drop_6h" in r["matched_dims"], f"{r}")

    # 场景 3：样本量不足 → P0 跳过 → 命中 P1
    r = evaluate_steam_level(55, 78, 79, bl_steam, 80, levels_steam)
    _check("S3 P0 样本不足跳到 P1", r["level"] == "P1", f"{r}")

    # 场景 4：所有维度都正常 → OK
    r = evaluate_steam_level(82, 81, 81, bl_steam, 200, levels_steam)
    _check("S4 全正常 → OK", r["level"] == "OK", f"{r}")

    # 场景 5：C 命中 P0（当前 65 < p5 70）
    r = evaluate_steam_level(65, 70, 70, bl_steam, 200, levels_steam)
    _check("S5 P0.C 命中", r["level"] == "P0"
           and any(d.startswith("C_below_") for d in r["matched_dims"]), f"{r}")

    # GP 评估
    levels_gp = {
        "P0": {"absolute_score": 3.0, "one_star_rate": 0.40, "drop_6h": 0.3,
               "baseline": "p5", "min_sample": 200},
        "P1": {"absolute_score": 3.5, "one_star_rate": 0.25, "drop_6h": 0.1,
               "baseline": "p25", "min_sample": 100},
        "P2": {"absolute_score": 4.0, "drop_24h": 0.05, "baseline": "median_7d",
               "min_sample": 50},
    }
    bl_gp = {"p5": 3.5, "p25": 4.0, "median_7d": 4.2}

    # 场景 6：1 星占比 50% > 40% → P0
    r = evaluate_store_level(2.8, 0.50, 4.2, 4.2, bl_gp, 500, levels_gp)
    _check("S6 GP P0.1星占比 命中", r["level"] == "P0"
           and "A_one_star_rate" in r["matched_dims"], f"{r}")

    # 场景 7：评分 3.95，sample=100 → P0 因样本不足跳过 → P1 因 C 命中（3.95 < p25=4.0）
    r = evaluate_store_level(3.95, 0.10, 4.0, 4.0, bl_gp, 100, levels_gp)
    _check("S7 GP P1.C 命中", r["level"] == "P1" and "C_below_p25" in r["matched_dims"], f"{r}")

    # 场景 7b：构造一个真正只命中 P2 的场景（绝对值 OK，1 星 OK，6h 不下跌，但 < median_7d）
    levels_p2only = {
        "P0": {"absolute_score": 1.0, "one_star_rate": 0.99, "drop_6h": 5.0, "baseline": "p5", "min_sample": 50},
        "P1": {"absolute_score": 1.0, "one_star_rate": 0.99, "drop_6h": 5.0, "baseline": "p25", "min_sample": 50},
        "P2": {"absolute_score": 4.5, "drop_24h": 0.05, "baseline": "median_7d", "min_sample": 50},
    }
    r = evaluate_store_level(4.0, 0.05, 4.05, 4.06, {"p5": 3.0, "p25": 3.0, "median_7d": 4.2},
                             100, levels_p2only)
    _check("S7b GP P2 唯一命中", r["level"] == "P2", f"{r}")

    # _glob_match
    _check("glob lang_te matches lang_*", _glob_match("lang_te", "lang_*"), "")
    _check("glob jp matches jp", _glob_match("jp", "jp"), "")
    _check("glob jp NOT match lang_*", not _glob_match("jp", "lang_*"), "")
    _check("Google Play 产出全球聚合切片", _should_emit_global_store_slice("google_play"), "")
    _check("App Store 不产出全球均分切片", not _should_emit_global_store_slice("app_store"), "")

    print(f"\n{'-' * 40}")
    if failures:
        print(f"FAIL: {len(failures)} — {failures}")
        return 1
    print("PASS: all unit tests")
    return 0


if __name__ == "__main__":
    main()
