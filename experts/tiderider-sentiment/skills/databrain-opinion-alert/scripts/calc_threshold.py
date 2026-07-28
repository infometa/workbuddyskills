#!/usr/bin/env python3
"""
calc_threshold.py — 分析历史数据，为三类告警输出建议阈值。

用法:
    python scripts/calc_threshold.py --game_id e11000000262 --alert_type rating
    python scripts/calc_threshold.py --game_id e11000000262 --alert_type kol
    python scripts/calc_threshold.py --game_id e11000000262 --alert_type keyword --keywords "crash,hack"

认证:
    DATABRAIN_TOKEN — 必填
    DATABRAIN_HOST  — 可选；未设置时自动 fallback
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

import httpx

_QUERY_PATH = "/api/v1/opinion_pc/global/query"
_FALLBACK_HOSTS = (
    "https://databrain.intlgame.com",
    "https://databrain.woa.com",
    "https://databrain-global.intlgame.com",
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_GAME_ID_RE = re.compile(r"^[ue][0-9a-f]+$")
_KEYWORD_SAFE_RE = re.compile(r"['\";\\-]")

_resolved_host: str | None = None


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
    return list(csv.DictReader(io.StringIO(resp.text)))


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
            print(f"[fallback] {host}: {last_err}", file=sys.stderr)
    print(f"[ERROR] All hosts failed. Last: {last_err}", file=sys.stderr)
    sys.exit(1)


def _stats(values: list[float]) -> dict:
    if not values:
        return {}
    n = len(values)
    mu = sum(values) / n
    variance = sum((x - mu) ** 2 for x in values) / n
    sigma = math.sqrt(variance)
    sorted_v = sorted(values)

    def pct(p: float) -> float:
        idx = p / 100 * (n - 1)
        lo, hi = int(idx), min(int(idx) + 1, n - 1)
        return sorted_v[lo] + (sorted_v[hi] - sorted_v[lo]) * (idx - lo)

    return {
        "count": n,
        "mean": round(mu, 2),
        "std": round(sigma, 2),
        "min": round(sorted_v[0], 2),
        "max": round(sorted_v[-1], 2),
        "p10": round(pct(10), 2),
        "p25": round(pct(25), 2),
        "p50": round(pct(50), 2),
        "p75": round(pct(75), 2),
        "p90": round(pct(90), 2),
        "p95": round(pct(95), 2),
    }


# ---------------------------------------------------------------------------
# Rating threshold
# ---------------------------------------------------------------------------
def _calc_rating(game_id: str, lookback_start: str, lookback_end: str,
                 hosts: list[str], token: str) -> dict:
    sql = f"""
SELECT
  DATE(comment_time) AS date,
  ROUND(
    COUNT(CASE WHEN is_recommend = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0),
    2
  ) AS positive_rate,
  COUNT(*) AS total_count
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '{game_id}'
  AND channel_name = 'steam'
  AND comment_time >= '{lookback_start} 00:00:00'
  AND comment_time <= '{lookback_end} 23:59:59'
GROUP BY date
HAVING COUNT(*) >= 10
ORDER BY date
""".strip()

    rows = _query_with_fallback(hosts, token, sql)
    if not rows:
        return {"error": "无 Steam 评论数据，无法计算阈值"}

    rates = [float(r["positive_rate"]) for r in rows if r.get("positive_rate")]
    s = _stats(rates)
    threshold = round(s["mean"] - 2 * s["std"], 1) if s else 70.0

    return {
        "alert_type": "rating",
        "game_id": game_id,
        "lookback_days": (date.fromisoformat(lookback_end) - date.fromisoformat(lookback_start)).days + 1,
        "analysis": s,
        "recommendation": {
            "threshold": threshold,
            "method": "mean - 2×std",
            "note": (
                f"近期日均好评率 {s['mean']}%，σ={s['std']}%。"
                f"建议下限阈值 {threshold}%（覆盖 95% 正常波动）。"
                f"若历史有口碑事件，可参考 p10={s['p10']}% 作为更保守下限。"
            ),
        },
        "daily_data": rows,
    }


# ---------------------------------------------------------------------------
# KOL threshold
# ---------------------------------------------------------------------------
def _calc_kol(game_id: str, lookback_start: str, lookback_end: str,
              hosts: list[str], token: str) -> dict:
    sql = f"""
SELECT
  DATE(comment_time) AS date,
  APPROX_QUANTILES(IF(tweets_like<0,0,tweets_like)+IF(tweets_reply<0,0,tweets_reply)+IF(tweets_retweet<0,0,tweets_retweet), 100)[OFFSET(90)] AS p90_engagement,
  APPROX_QUANTILES(IF(tweets_like<0,0,tweets_like)+IF(tweets_reply<0,0,tweets_reply)+IF(tweets_retweet<0,0,tweets_retweet), 100)[OFFSET(95)] AS p95_engagement,
  MAX(IF(tweets_like<0,0,tweets_like)+IF(tweets_reply<0,0,tweets_reply)+IF(tweets_retweet<0,0,tweets_retweet)) AS max_engagement,
  ROUND(AVG(IF(tweets_like<0,0,tweets_like)+IF(tweets_reply<0,0,tweets_reply)+IF(tweets_retweet<0,0,tweets_retweet)), 0) AS avg_engagement,
  COUNT(*) AS post_count
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '{game_id}'
  AND comment_time >= '{lookback_start} 00:00:00'
  AND comment_time <= '{lookback_end} 23:59:59'
GROUP BY date
ORDER BY date
""".strip()

    rows = _query_with_fallback(hosts, token, sql)
    if not rows:
        return {"error": "无数据，无法计算 KOL 阈值"}

    p90_values = [float(r["p90_engagement"]) for r in rows if r.get("p90_engagement")]
    s = _stats(p90_values)
    threshold = int(s.get("p50", 10000)) if s else 10000

    return {
        "alert_type": "kol",
        "game_id": game_id,
        "lookback_days": (date.fromisoformat(lookback_end) - date.fromisoformat(lookback_start)).days + 1,
        "analysis": {"daily_p90_stats": s},
        "recommendation": {
            "threshold": threshold,
            "method": "近期每日 P90 engagement 的中位数",
            "note": (
                f"近期每日 P90 engagement 中位数为 {threshold}，"
                f"建议以此作为「高互动帖」门槛，超过此值约为 Top 10% 传播力帖子。"
            ),
        },
        "daily_data": rows,
    }


# ---------------------------------------------------------------------------
# Keyword threshold
# ---------------------------------------------------------------------------
def _calc_keyword(game_id: str, lookback_start: str, lookback_end: str,
                  keywords: list[str], hosts: list[str], token: str) -> dict:
    kw_list = ", ".join(f"'{k}'" for k in keywords)
    days = (date.fromisoformat(lookback_end) - date.fromisoformat(lookback_start)).days + 1

    sql = f"""
SELECT
  k.value AS keyword,
  DATE(comment_time) AS date,
  COUNT(*) AS daily_volume
FROM `tencent-databrain-prod.opinion.feeds`,
  UNNEST(keywords) AS k
WHERE unified_edition_id = '{game_id}'
  AND comment_time >= '{lookback_start} 00:00:00'
  AND comment_time <= '{lookback_end} 23:59:59'
  AND k.value IN ({kw_list})
GROUP BY keyword, date
ORDER BY keyword, date
""".strip()

    rows = _query_with_fallback(hosts, token, sql)

    kw_data: dict[str, list[float]] = {k: [] for k in keywords}
    for r in rows:
        kw = r.get("keyword", "")
        if kw in kw_data:
            kw_data[kw].append(float(r.get("daily_volume") or 0))

    recommendations = {}
    for kw, volumes in kw_data.items():
        if not volumes:
            recommendations[kw] = {"daily_avg": 0, "threshold_multiple": 3.0,
                                    "note": "无历史数据，建议首次出现即告警（threshold=1）"}
            continue
        s = _stats(volumes)
        recommendations[kw] = {
            "daily_avg": s["mean"],
            "daily_std": s["std"],
            "p90": s["p90"],
            "threshold_multiple": 3.0,
            "alert_volume": round(s["mean"] * 3, 0),
            "note": (
                f"日均 {s['mean']} 条，σ={s['std']}。"
                f"建议 3× 均值（{round(s['mean'] * 3, 0)} 条）为告警触发阈值。"
            ),
        }

    return {
        "alert_type": "keyword",
        "game_id": game_id,
        "keywords": keywords,
        "lookback_days": days,
        "recommendation": {
            "threshold_multiple": 3.0,
            "by_keyword": recommendations,
            "note": "threshold 参数填 3.0，即当日声量超过近 30 天均值 3 倍时触发告警。",
        },
        "daily_data": rows,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="分析历史数据，输出告警阈值建议")
    parser.add_argument("--game_id", required=True)
    parser.add_argument("--alert_type", required=True, choices=["rating", "kol", "keyword"])
    parser.add_argument("--lookback_days", type=int, default=30)
    parser.add_argument("--keywords", default="", help="关键词类型必填，逗号分隔")
    args = parser.parse_args()

    if not _GAME_ID_RE.match(args.game_id.strip()):
        print(f"[ERROR] Invalid game_id: {args.game_id!r}", file=sys.stderr)
        sys.exit(1)

    token, hosts = _get_config()
    today = date.today()
    lookback_end = (today - timedelta(days=1)).isoformat()
    lookback_start = (today - timedelta(days=args.lookback_days)).isoformat()
    game_id = args.game_id.strip()

    print(f"[INFO] 分析 {args.alert_type} 告警阈值，lookback {lookback_start} → {lookback_end}", file=sys.stderr)

    if args.alert_type == "rating":
        result = _calc_rating(game_id, lookback_start, lookback_end, hosts, token)
    elif args.alert_type == "kol":
        result = _calc_kol(game_id, lookback_start, lookback_end, hosts, token)
    else:
        if not args.keywords:
            print("[ERROR] --keywords is required for alert_type=keyword", file=sys.stderr)
            sys.exit(1)
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
        for kw in keywords:
            if _KEYWORD_SAFE_RE.search(kw):
                print(f"[ERROR] Unsafe keyword: {kw!r}", file=sys.stderr)
                sys.exit(1)
        result = _calc_keyword(game_id, lookback_start, lookback_end, keywords, hosts, token)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
