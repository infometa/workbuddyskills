#!/usr/bin/env python3
"""
check_alerts.py — 取数 + 阈值判断，输出告警结果 JSON。

支持三类告警：
  rating   — Steam 好评率低于阈值
  kol      — 高互动量帖子（可过滤负面情绪）
  keyword  — 关键词声量超过历史均值 N 倍

用法:
    python scripts/check_alerts.py \\
        --game_id e11000000262 \\
        --alert_type rating \\
        --start_date 2026-04-13 \\
        --end_date 2026-04-13 \\
        --threshold 70 \\
        --message "用户原始问题" \\
        --output /tmp/alert_result.json

    # KOL 告警（仅负面）
    python scripts/check_alerts.py \\
        --game_id e11000000262 \\
        --alert_type kol \\
        --start_date 2026-04-13 \\
        --end_date 2026-04-13 \\
        --threshold 10000 \\
        --kol_sentiment_filter \\
        --output /tmp/alert_result.json

    # 关键词声量告警
    python scripts/check_alerts.py \\
        --game_id e11000000262 \\
        --alert_type keyword \\
        --start_date 2026-04-13 \\
        --end_date 2026-04-13 \\
        --threshold 3.0 \\
        --keywords "crash,hack,ban" \\
        --output /tmp/alert_result.json

认证:
    DATABRAIN_TOKEN — 必填
    DATABRAIN_HOST  — 可选；未设置时自动 fallback
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import threading
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx
import yaml

from alert_state import DEFAULT_STATE_PATH, load_state, record_trigger, save_state, should_trigger
from report_log import new_session_msg_pair, report

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_QUERY_PATH = "/api/v1/opinion_pc/global/query"
_FALLBACK_HOSTS = (
    "https://databrain.intlgame.com",
    "https://databrain.woa.com",
    "https://databrain-global.intlgame.com",
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_GAME_ID_RE = re.compile(r"^[ue][0-9a-f]+$")
_KEYWORD_SAFE_RE = re.compile(r"['\";\\]")  # SQL injection guard
_NEGATIVE_RATIO_BY_SENSITIVITY = {"low": 0.50, "medium": 0.40, "high": 0.20}
_LEVEL_RANK = {"P0": 0, "P1": 1, "P2": 2}

_resolved_host: str | None = None


# ---------------------------------------------------------------------------
# Env / config
# ---------------------------------------------------------------------------
def _load_dotenv() -> None:
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.is_file():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and os.environ.get(k) is None:
                    os.environ[k] = v


def _is_trusted_host(host: str) -> bool:
    hostname = urlparse(host).hostname or ""
    if hostname in ("databrain.intlgame.com", "databrain.woa.com"):
        return True
    return hostname.startswith("databrain-") and hostname.endswith(".intlgame.com")


def _get_config() -> tuple[str, list[str]]:
    global _resolved_host
    _load_dotenv()
    token = os.environ.get("DATABRAIN_TOKEN", "").strip()
    if not token:
        print("[ERROR] DATABRAIN_TOKEN not set.", file=sys.stderr)
        sys.exit(1)
    explicit = os.environ.get("DATABRAIN_HOST", "").strip().rstrip("/")
    if explicit:
        if not _is_trusted_host(explicit):
            print(f"[ERROR] DATABRAIN_HOST '{explicit}' 不在受信任域名列表中。", file=sys.stderr)
            sys.exit(1)
        return token, [explicit]
    if _resolved_host:
        return token, [_resolved_host]
    return token, list(_FALLBACK_HOSTS)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def _validate_game_id(game_id: str) -> str:
    if not _GAME_ID_RE.match(game_id):
        print(f"[ERROR] Invalid game_id: {game_id!r}. Must be u/e + hex.", file=sys.stderr)
        sys.exit(1)
    return game_id


def _validate_date(date_str: str, label: str) -> str:
    if not _DATE_RE.match(date_str):
        print(f"[ERROR] Invalid {label}: {date_str!r}. Expected YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)
    return date_str


def _validate_keywords(raw: str) -> list[str]:
    keywords = [k.strip() for k in raw.split(",") if k.strip()]
    for kw in keywords:
        if _KEYWORD_SAFE_RE.search(kw) or "--" in kw:
            print(f"[ERROR] Keyword contains unsafe characters: {kw!r}", file=sys.stderr)
            sys.exit(1)
    return keywords


def _load_crisis_terms() -> dict:
    path = Path(__file__).resolve().parent.parent / "keyword_crisis_terms.yaml"
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("categories") or {}


def _match_crisis_terms(keywords: list[str], matched_keywords: list[str]) -> dict:
    categories = _load_crisis_terms()
    candidates = [x.lower() for x in keywords + matched_keywords if x]
    hits = []
    for key, cfg in categories.items():
        terms = cfg.get("terms") or []
        matched_terms = []
        for term in terms:
            term_l = str(term).lower()
            if any(term_l == c or term_l in c or c in term_l for c in candidates):
                matched_terms.append(str(term))
        if matched_terms:
            hits.append({
                "category": key,
                "label": cfg.get("label") or key,
                "default_level": cfg.get("default_level") or "P1",
                "matched_terms": matched_terms,
            })
    if not hits:
        return {"is_crisis": False, "crisis_hits": []}
    primary = sorted(hits, key=lambda x: _LEVEL_RANK.get(x.get("default_level"), 99))[0]
    return {
        "is_crisis": True,
        "crisis_category": primary["category"],
        "crisis_label": primary["label"],
        "level": primary["default_level"],
        "crisis_hits": hits,
    }


def _as_int(v, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _as_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


# ---------------------------------------------------------------------------
# BigQuery query
# ---------------------------------------------------------------------------
def _run_query(host: str, token: str, sql: str) -> list[dict]:
    # API 网关对多行 SQL 解析异常（200 + body_size=0），先压成单行。
    sql_oneline = " ".join(sql.split())
    resp = httpx.post(
        f"{host}{_QUERY_PATH}",
        json={"sql": sql_oneline},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:400]}")
    try:
        body = resp.json()
        if isinstance(body, dict) and body.get("code", 0) != 0:
            raise RuntimeError(f"API error (code={body['code']}): {body.get('msg', '')}")
    except (ValueError, AttributeError):
        pass
    reader = csv.DictReader(io.StringIO(resp.text))
    return list(reader)


def _query_with_fallback(hosts: list[str], token: str, sql: str) -> list[dict]:
    global _resolved_host
    last_err = ""
    for host in hosts:
        try:
            rows = _run_query(host, token, sql)
            _resolved_host = host
            return rows
        except Exception as e:
            last_err = str(e)
            print(f"[fallback] {host} failed: {last_err}", file=sys.stderr)
    print(f"[ERROR] All hosts failed. Last error: {last_err}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Report (background, agent-agnostic)
# ---------------------------------------------------------------------------
def _start_report(message: str, session_id: str, msg_id: str) -> threading.Thread:
    def _do():
        try:
            report(message or "databrain-opinion-alert", session_id, msg_id)
        except Exception:
            pass

    t = threading.Thread(target=_do, daemon=False)
    t.start()
    return t


# ---------------------------------------------------------------------------
# Alert logic: rating
# ---------------------------------------------------------------------------
def _check_rating(game_id: str, start_date: str, end_date: str,
                  threshold: float, hosts: list[str], token: str,
                  rating_mode: str = "rolling", rolling_days: int = 30) -> dict:
    """
    rating_mode:
      period     — 仅统计 start_date ~ end_date 新增评论（追踪版本/事件即时反应）
      rolling    — 以 end_date 为基准向前 rolling_days 天滚动窗口（日常监控推荐）
      cumulative — 统计 end_date 前全部历史评论（整体口碑基线）
    """
    if rating_mode == "rolling":
        actual_start = (
            date.fromisoformat(end_date) - timedelta(days=rolling_days - 1)
        ).isoformat()
        actual_end = end_date
        mode_desc = f"近 {rolling_days} 天滚动"
    elif rating_mode == "cumulative":
        actual_start = "2000-01-01"
        actual_end = end_date
        mode_desc = "累积全量"
    else:  # period
        actual_start = start_date
        actual_end = end_date
        mode_desc = f"{start_date} ~ {end_date} 新增"

    sql = f"""
SELECT
  COUNT(CASE WHEN is_recommend = 1 THEN 1 END) AS positive_count,
  COUNT(CASE WHEN is_recommend = 0 THEN 1 END) AS negative_count,
  COUNT(*) AS total_count,
  ROUND(
    COUNT(CASE WHEN is_recommend = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0),
    2
  ) AS positive_rate
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '{game_id}'
  AND channel_name = 'steam'
  AND comment_time >= '{actual_start} 00:00:00'
  AND comment_time <= '{actual_end} 23:59:59'
""".strip()

    rows = _query_with_fallback(hosts, token, sql)
    if not rows:
        return {"triggered": False, "alert_type": "rating", "game_id": game_id,
                "rating_mode": rating_mode, "detail": "无数据（Steam 评论为空）", "rows": []}

    row = rows[0]
    total = int(row.get("total_count") or 0)
    positive_rate = float(row.get("positive_rate") or 0)

    triggered = total > 0 and positive_rate < threshold
    detail = (
        f"Steam 好评率 {positive_rate:.1f}%（{mode_desc}，阈值 {threshold:.1f}%），"
        f"共 {total} 条评论，正面 {row.get('positive_count', 0)} 条，负面 {row.get('negative_count', 0)} 条。"
    )
    if triggered:
        detail = f"⚠️ 触发告警！{detail}"
    else:
        detail = f"✅ 正常。{detail}"

    return {
        "triggered": triggered,
        "alert_type": "rating",
        "rating_mode": rating_mode,
        "game_id": game_id,
        "date_range": {"start": actual_start, "end": actual_end},
        "current_value": positive_rate,
        "threshold": threshold,
        "detail": detail,
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Alert logic: KOL
# ---------------------------------------------------------------------------
def _check_kol(game_id: str, start_date: str, end_date: str,
               threshold: float, sentiment_filter: bool,
               hosts: list[str], token: str) -> dict:
    sentiment_clause = "AND sentiment_rating IN (1, 2)" if sentiment_filter else ""
    sql = f"""
SELECT
  content,
  comment_uin,
  channel_name,
  follower_number,
  IF(tweets_like<0,0,tweets_like)+IF(tweets_reply<0,0,tweets_reply)+IF(tweets_retweet<0,0,tweets_retweet) AS engagement,
  IF(tweets_like<0,0,tweets_like) AS likes,
  sentiment_rating,
  DATE(comment_time) AS date
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '{game_id}'
  AND comment_time >= '{start_date} 00:00:00'
  AND comment_time <= '{end_date} 23:59:59'
  AND (IF(tweets_like<0,0,tweets_like)+IF(tweets_reply<0,0,tweets_reply)+IF(tweets_retweet<0,0,tweets_retweet)) >= {int(threshold)}
  {sentiment_clause}
ORDER BY engagement DESC
LIMIT 20
""".strip()

    rows = _query_with_fallback(hosts, token, sql)
    triggered = len(rows) > 0
    filter_desc = "（仅负面情绪）" if sentiment_filter else ""
    detail = (
        f"⚠️ 触发告警！发现 {len(rows)} 条高互动帖子{filter_desc}，最高 engagement {rows[0].get('engagement', 0)}。"
        if triggered
        else f"✅ 正常。未发现 engagement ≥ {int(threshold)} 的帖子{filter_desc}。"
    )

    return {
        "triggered": triggered,
        "alert_type": "kol",
        "game_id": game_id,
        "date_range": {"start": start_date, "end": end_date},
        "current_value": len(rows),
        "threshold": threshold,
        "kol_sentiment_filter": sentiment_filter,
        "detail": detail,
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Alert logic: keyword
# ---------------------------------------------------------------------------
def _keyword_array_sql(keywords: list[str]) -> str:
    return "[" + ", ".join(f"'{kw.lower()}'" for kw in keywords) + "]"


def _keyword_text_expr() -> str:
    return "LOWER(CONCAT(IFNULL(content_to_zh, ''), ' ', IFNULL(content, '')))"


def _keyword_match_for_var(var_name: str = "kw") -> str:
    text_expr = _keyword_text_expr()
    return (
        f"EXISTS (SELECT 1 FROM UNNEST(keywords) k WHERE LOWER(k.value) = {var_name}) "
        f"OR STRPOS({text_expr}, {var_name}) > 0"
    )


def _any_keyword_match_clause(keywords: list[str]) -> str:
    kw_array = _keyword_array_sql(keywords)
    return f"EXISTS (SELECT 1 FROM UNNEST({kw_array}) kw WHERE {_keyword_match_for_var('kw')})"


def _matched_keywords_expr(keywords: list[str]) -> str:
    kw_array = _keyword_array_sql(keywords)
    return (
        "ARRAY_TO_STRING(ARRAY("
        f"SELECT kw FROM UNNEST({kw_array}) kw WHERE {_keyword_match_for_var('kw')}"
        "), ',')"
    )


def _keyword_window_bounds(end_date: str, window_hours: int) -> tuple[str, str]:
    end_ts = f"{end_date} 23:59:59"
    start_expr = f"TIMESTAMP('{end_ts}') - INTERVAL {int(window_hours)} HOUR"
    end_expr = f"TIMESTAMP('{end_ts}')"
    return start_expr, end_expr


def _keyword_min_mentions(window_hours: int, baseline_avg: float, override: int | None) -> int:
    if override is not None and override > 0:
        return override
    if window_hours <= 1:
        return max(10, int(baseline_avg * 0.5))
    if window_hours <= 6:
        return max(30, int(baseline_avg * 0.4))
    return max(100, int(baseline_avg * 0.3))


def _check_keyword(game_id: str, start_date: str, end_date: str,
                   threshold_multiple: float, keywords: list[str],
                   hosts: list[str], token: str, *, window_hours: int = 24,
                   sensitivity: str = "medium", min_mentions: int | None = None,
                   viral_threshold: int = 500, user_id: str = "_",
                   state_file: str = DEFAULT_STATE_PATH, dry_run: bool = False) -> dict:
    match_any = _any_keyword_match_clause(keywords)
    current_start, current_end = _keyword_window_bounds(end_date, window_hours)
    baseline_start = f"{current_start} - INTERVAL 7 DAY"
    baseline_end = current_start
    negative_expr = "CAST(sentiment_rating AS STRING) IN ('1', '2')"

    sql_current = f"""
SELECT
  COUNT(*) AS mentions,
  COUNT(CASE WHEN {negative_expr} THEN 1 END) AS negative_mentions
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '{game_id}'
  AND comment_time >= {current_start}
  AND comment_time <= {current_end}
  AND ({match_any})
""".strip()

    sql_baseline = f"""
SELECT
  ROUND(COUNT(*) / 7.0, 2) AS mention_avg,
  COUNT(*) AS total_mentions,
  COUNT(CASE WHEN {negative_expr} THEN 1 END) AS negative_mentions
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '{game_id}'
  AND comment_time >= {baseline_start}
  AND comment_time < {baseline_end}
  AND ({match_any})
""".strip()

    kw_array = _keyword_array_sql(keywords)
    match_for_kw = _keyword_match_for_var("kw")
    sql_by_keyword = f"""
SELECT
  kw AS keyword,
  COUNT(*) AS volume
FROM `tencent-databrain-prod.opinion.feeds`, UNNEST({kw_array}) kw
WHERE unified_edition_id = '{game_id}'
  AND comment_time >= {current_start}
  AND comment_time <= {current_end}
  AND ({match_for_kw})
GROUP BY keyword
ORDER BY volume DESC
""".strip()

    matched_keywords = _matched_keywords_expr(keywords)
    sql_posts = f"""
SELECT
  channel_name,
  IFNULL(country, '') AS country,
  IFNULL(language, '') AS language,
  reviewer,
  comment_uin,
  comment_time,
  sentiment_rating,
  SUBSTR(COALESCE(NULLIF(content_to_zh, ''), NULLIF(content, ''), ''), 1, 240) AS snippet,
  GREATEST(IFNULL(tweets_like, 0), 0) AS likes,
  GREATEST(IFNULL(tweets_reply, 0), 0) AS replies,
  GREATEST(IFNULL(tweets_retweet, 0), 0) AS retweets,
  (GREATEST(IFNULL(tweets_like, 0), 0) + GREATEST(IFNULL(tweets_reply, 0), 0) + GREATEST(IFNULL(tweets_retweet, 0), 0)) AS engagement,
  {matched_keywords} AS matched_keywords,
  COALESCE(
    NULLIF(content_url, ''),
    ARRAY(
      SELECT s.url FROM UNNEST(sources) s
      WHERE s.url IS NOT NULL AND s.url != '' AND LOWER(s.url) != 'null'
      LIMIT 1
    )[SAFE_OFFSET(0)],
    ''
  ) AS url
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '{game_id}'
  AND comment_time >= {current_start}
  AND comment_time <= {current_end}
  AND ({match_any})
ORDER BY engagement DESC, comment_time DESC
LIMIT 20
""".strip()

    current_row = (_query_with_fallback(hosts, token, sql_current) or [{}])[0]
    baseline_row = (_query_with_fallback(hosts, token, sql_baseline) or [{}])[0]
    by_keyword_rows = _query_with_fallback(hosts, token, sql_by_keyword)
    post_rows = _query_with_fallback(hosts, token, sql_posts)

    mentions = _as_int(current_row.get("mentions"))
    negative_mentions = _as_int(current_row.get("negative_mentions"))
    baseline_avg = _as_float(baseline_row.get("mention_avg"))
    baseline_total = _as_int(baseline_row.get("total_mentions"))
    baseline_negative = _as_int(baseline_row.get("negative_mentions"))
    multiple = mentions / baseline_avg if baseline_avg > 0 else (float("inf") if mentions > 0 else 0.0)
    negative_ratio = negative_mentions / mentions if mentions else 0.0
    baseline_negative_ratio = baseline_negative / baseline_total if baseline_total else 0.0
    min_abs = _keyword_min_mentions(window_hours, baseline_avg, min_mentions)
    negative_threshold = _NEGATIVE_RATIO_BY_SENSITIVITY.get(sensitivity, 0.40)

    top_post = post_rows[0] if post_rows else {}
    top_engagement = _as_int(top_post.get("engagement"))
    triggered_dimensions: list[str] = []
    if mentions >= min_abs and (baseline_avg == 0 and mentions > 0 or multiple >= threshold_multiple):
        triggered_dimensions.append("mention_spike")
    if mentions >= 30 and negative_ratio >= negative_threshold and negative_ratio >= baseline_negative_ratio + 0.05:
        triggered_dimensions.append("negative_ratio")
    if top_engagement >= viral_threshold:
        triggered_dimensions.append("viral_post")

    lower_to_raw = {kw.lower(): kw for kw in keywords}
    today_map = {
        lower_to_raw.get(str(r.get("keyword") or "").lower(), str(r.get("keyword") or "")): _as_int(r.get("volume"))
        for r in by_keyword_rows
    }
    triggered_keywords = [kw for kw in keywords if today_map.get(kw, 0) > 0]
    matched_terms = list(triggered_keywords)
    for row in post_rows:
        matched_terms.extend(str(row.get("matched_keywords") or "").split(","))
    crisis_info = _match_crisis_terms(keywords, [x.strip() for x in matched_terms if x.strip()])
    platform_dist: dict[str, int] = {}
    language_dist: dict[str, int] = {}
    for row in post_rows:
        platform = row.get("channel_name") or "unknown"
        language = row.get("language") or row.get("country") or "unknown"
        platform_dist[platform] = platform_dist.get(platform, 0) + 1
        language_dist[language] = language_dist.get(language, 0) + 1

    triggered = bool(triggered_dimensions)
    if triggered:
        detail = f"⚠️ 触发关键词告警：{','.join(triggered_dimensions)}；窗口 {window_hours}h 提及 {mentions} 条。"
    else:
        detail = f"✅ 正常。窗口 {window_hours}h 提及 {mentions} 条，未命中关键词告警触发条件。"

    keyword_group = "|".join(sorted(k.lower() for k in keywords))
    now = datetime.now(timezone.utc)
    silence_seconds = int(window_hours) * 3600
    state = load_state(state_file)
    dimension_states = {}
    should_push = False
    for dim in triggered_dimensions:
        key = f"keyword:{user_id or '_'}:{game_id}:{keyword_group}:{dim}"
        if dry_run:
            dim_should, reason = True, "dry_run"
        else:
            dim_should, reason = should_trigger(state, key, crisis_info.get("level", "P1"), now, silence_seconds)
            if dim_should:
                record_trigger(state, key, crisis_info.get("level", "P1"), silence_seconds, now)
        should_push = should_push or dim_should
        dimension_states[dim] = {"state_key": key, "should_push": dim_should, "push_reason": reason}
    if triggered_dimensions and not dry_run:
        save_state(state_file, state)

    return {
        "triggered": triggered,
        "should_push": should_push if triggered else False,
        "alert_type": "keyword",
        "version": "keyword_v2",
        "game_id": game_id,
        "date_range": {"start": start_date, "end": end_date},
        "window_hours": window_hours,
        "sensitivity": sensitivity,
        "threshold": threshold_multiple,
        "min_mentions": min_abs,
        "viral_threshold": viral_threshold,
        "keywords": keywords,
        "triggered_keywords": triggered_keywords,
        **crisis_info,
        "triggered_dimensions": triggered_dimensions,
        "dimension_states": dimension_states,
        "detail": detail,
        "today_volumes": today_map,
        "baselines": {"mention_avg": baseline_avg, "negative_ratio": baseline_negative_ratio},
        "metrics": {
            "mentions": mentions,
            "baseline_mentions": baseline_avg,
            "multiple": multiple,
            "negative_mentions": negative_mentions,
            "negative_ratio": negative_ratio,
            "top_engagement": top_engagement,
        },
        "attribution": {
            "platform_distribution": platform_dist,
            "language_distribution": language_dist,
            "top_posts": post_rows[:5],
        },
        "rows": post_rows,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="舆情告警检查：取数 + 阈值判断 → 输出 JSON")
    parser.add_argument("--game_id", required=True)
    parser.add_argument("--alert_type", required=True, choices=["rating", "kol", "keyword"])
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date", required=True)
    parser.add_argument("--threshold", type=float, required=True,
                        help="rating: 好评率下限%；kol: 最低 engagement；keyword: 声量倍数")
    parser.add_argument(
        "--rating_mode",
        choices=["period", "rolling", "cumulative"],
        default="rolling",
        help=(
            "评分口径（仅 alert_type=rating 生效）："
            "rolling=近 N 天滚动（默认，适合日常监控）；"
            "period=仅统计 start_date~end_date 新增（适合追踪版本/事件）；"
            "cumulative=全部历史评论（适合整体基线）"
        ),
    )
    parser.add_argument("--rolling_days", type=int, default=30,
                        help="rolling 模式的滚动天数，默认 30（仅 --rating_mode rolling 生效）")
    parser.add_argument("--kol_sentiment_filter", action="store_true",
                        help="KOL 告警仅关注 sentiment_rating IN (1,2) 的负面帖")
    parser.add_argument("--keywords", default="",
                        help="关键词告警：逗号分隔关键词列表，如 crash,hack,ban")
    parser.add_argument("--window_hours", type=int, default=24,
                        help="关键词告警当前窗口小时数，默认 24")
    parser.add_argument("--sensitivity", choices=["low", "medium", "high"], default="medium",
                        help="关键词负面占比灵敏度：low=50%%, medium=40%%, high=20%%")
    parser.add_argument("--min_mentions", type=int, default=0,
                        help="关键词提及量最小绝对量；0 表示按窗口自动计算")
    parser.add_argument("--viral_threshold", type=int, default=500,
                        help="关键词单帖爆款互动量阈值，默认 500")
    parser.add_argument("--user_id", default="_",
                        help="关键词告警静默 key 的用户 ID，默认 '_'")
    parser.add_argument("--state_file", default=DEFAULT_STATE_PATH,
                        help="静默期状态文件，默认 /tmp/databrain_alert_state.json")
    parser.add_argument("--dry_run", action="store_true",
                        help="关键词告警跳过静默写入，所有命中维度标记 should_push=true")
    parser.add_argument("--message", default="", help="用户原始问题，用于埋点上报")
    parser.add_argument("--output", default="/tmp/alert_result.json",
                        help="输出 JSON 路径，默认 /tmp/alert_result.json")
    args = parser.parse_args()

    token, hosts = _get_config()
    session_id, msg_id = new_session_msg_pair()
    report_thread = _start_report(args.message, session_id, msg_id)

    try:
        game_id = _validate_game_id(args.game_id.strip())
        start_date = _validate_date(args.start_date.strip(), "--start_date")
        end_date = _validate_date(args.end_date.strip(), "--end_date")
        if end_date < start_date:
            print(f"[ERROR] --end_date {end_date!r} < --start_date {start_date!r}", file=sys.stderr)
            sys.exit(1)

        if args.alert_type == "rating":
            result = _check_rating(game_id, start_date, end_date, args.threshold, hosts, token,
                                   rating_mode=args.rating_mode, rolling_days=args.rolling_days)

        elif args.alert_type == "kol":
            result = _check_kol(game_id, start_date, end_date, args.threshold,
                                 args.kol_sentiment_filter, hosts, token)

        else:  # keyword
            if not args.keywords:
                print("[ERROR] --keywords is required for alert_type=keyword", file=sys.stderr)
                sys.exit(1)
            keywords = _validate_keywords(args.keywords)
            result = _check_keyword(game_id, start_date, end_date, args.threshold,
                                    keywords, hosts, token,
                                    window_hours=args.window_hours,
                                    sensitivity=args.sensitivity,
                                    min_mentions=args.min_mentions or None,
                                    viral_threshold=args.viral_threshold,
                                    user_id=args.user_id,
                                    state_file=args.state_file,
                                    dry_run=args.dry_run)

        output_path = args.output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[INFO] triggered={result['triggered']}", file=sys.stderr)
        print(result["detail"])

    finally:
        report_thread.join(timeout=1.0)


if __name__ == "__main__":
    main()
