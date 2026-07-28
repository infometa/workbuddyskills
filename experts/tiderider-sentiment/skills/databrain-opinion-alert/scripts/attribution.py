#!/usr/bin/env python3
"""
attribution.py — 商店评分告警归因。

模板要求两类归因：
  1) 高频投诉：负面样本的来源分布（国家 / 语种 / 子渠道 Top N）
  2) 代表性差评：按互动量挑出 Top N 条差评（reviewer + 时间 + 链接，便于人工跟进）

仅使用 feeds 表已确认存在的字段：
  comment_time, channel_type, channel_name, country, language,
  sentiment_rating, is_recommend, comment_uin, reviewer,
  content, content_to_zh, content_url,
  tweets_like, tweets_reply, tweets_retweet, sources

用法
====
    python scripts/attribution.py \\
        --game_id e7f672beaa5fddd166df98bc046ba4bd4 \\
        --channel steam \\
        --hours 6 \\
        --output /tmp/attribution.json
    python scripts/attribution.py --self_test
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from store_score_query import (
    CHANNEL_TO_FEEDS_NAME,
    RateLimitedError,
    query,
    validate_game_id,
)

# 「负面」筛选条件按渠道区分：
# - Steam：is_recommend = 0 是商店原生差评信号（最准）
# - GP / App Store：sentiment_rating IN (1, 2) 是 NLP 负面信号（评论文本字段未确认）
NEGATIVE_FILTER = {
    "steam": "is_recommend = 0",
    "google_play": "sentiment_rating IN (1, 2)",
    "app_store": "sentiment_rating IN (1, 2)",
}


def _ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _channel_clause(channel: str) -> str:
    """
    feeds.channel_name 的实际值带空格：'google play' / 'app store'。
    Steam 大小写未确认，用 LOWER 兜底。
    """
    cn = CHANNEL_TO_FEEDS_NAME[channel]
    return f"LOWER(channel_name) = '{cn.lower()}'"


# ---------------------------------------------------------------------------
# 高频投诉：来源分布（country / language / sub_channel）
# ---------------------------------------------------------------------------
def query_complaint_distribution(
    channel: str,
    game_id: str,
    start: datetime,
    end: datetime,
    top_n: int = 5,
) -> dict:
    """统计窗口内负面样本的国家、语种、子渠道分布 Top N。返回 {by_country, by_language, by_channel_name, total_negative}"""
    validate_game_id(game_id)
    if channel not in NEGATIVE_FILTER:
        raise ValueError(f"unsupported channel: {channel!r}")
    top_n = max(1, min(int(top_n), 50))
    sql = f"""
SELECT
  IFNULL(NULLIF(country, ''), 'unknown') AS country,
  IFNULL(NULLIF(language, ''), 'unknown') AS language,
  channel_name,
  COUNT(*) AS cnt,
  COUNT(DISTINCT comment_uin) AS uniq_users
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '{game_id}'
  AND {_channel_clause(channel)}
  AND comment_time >= TIMESTAMP('{_ts(start)}')
  AND comment_time <  TIMESTAMP('{_ts(end)}')
  AND {NEGATIVE_FILTER[channel]}
GROUP BY country, language, channel_name
""".strip()
    rows = query(sql)
    total = sum(int(r.get("cnt", 0)) for r in rows)

    by_country: dict[str, dict] = {}
    by_language: dict[str, dict] = {}
    by_subchannel: dict[str, dict] = {}
    for r in rows:
        cnt = int(r.get("cnt", 0))
        uniq = int(r.get("uniq_users", 0))
        c = r.get("country") or "unknown"
        lng = r.get("language") or "unknown"
        sc = r.get("channel_name") or "unknown"
        by_country.setdefault(c, {"count": 0, "uniq_users": 0})
        by_country[c]["count"] += cnt
        by_country[c]["uniq_users"] += uniq
        by_language.setdefault(lng, {"count": 0, "uniq_users": 0})
        by_language[lng]["count"] += cnt
        by_language[lng]["uniq_users"] += uniq
        by_subchannel.setdefault(sc, {"count": 0, "uniq_users": 0})
        by_subchannel[sc]["count"] += cnt
        by_subchannel[sc]["uniq_users"] += uniq

    def _topn(d: dict) -> list[dict]:
        items = sorted(d.items(), key=lambda kv: kv[1]["count"], reverse=True)[:top_n]
        return [
            {
                "key": k,
                "count": v["count"],
                "uniq_users": v["uniq_users"],
                "ratio": round(v["count"] / total, 4) if total else 0.0,
            }
            for k, v in items
        ]

    by_country_top = _topn(by_country)
    country_available = not (
        channel == "steam"
        and by_country_top
        and all(str(x.get("key")) in {"global", "unknown"} for x in by_country_top)
    )

    return {
        "total_negative": total,
        "window_hours": round((end - start).total_seconds() / 3600, 2),
        "country_available": country_available,
        "country_note": "" if country_available else "Steam 评论源未提供可用国家字段，归因展示按语种切分。",
        "by_country": by_country_top if country_available else [],
        "by_language": _topn(by_language),
        "by_channel_name": _topn(by_subchannel),
    }


# ---------------------------------------------------------------------------
# 代表性差评：按互动量挑选 Top N
# ---------------------------------------------------------------------------
def query_top_negative_reviews(
    channel: str,
    game_id: str,
    start: datetime,
    end: datetime,
    top_n: int = 5,
) -> list[dict]:
    """
    取窗口内负面样本中互动量最高的 N 条（reviewer / 时间 / 国家 / 语种 / 来源 URL）。
    互动量 = LIKE + REPLY + RETWEET（去掉负值）。

    [Why] 用户要求"必须有 URL 的"，所以 SQL 端做硬过滤。
          feeds 表里 Steam 样本常见 sources.url 为空，但 content_url 有可跳转原帖；
          因此优先取 content_url，再 fallback 到 sources.url。LIMIT 取 top_n * 3 候选，
          Python 端再次校验 URL 后裁到 top_n，规避少数 url 字段为字面 'NULL' 字符串的脏数据。
    """
    validate_game_id(game_id)
    if channel not in NEGATIVE_FILTER:
        raise ValueError(f"unsupported channel: {channel!r}")
    top_n = max(1, min(int(top_n), 50))
    candidate_n = top_n * 3
    sql = f"""
SELECT
  reviewer,
  comment_uin,
  comment_time,
  IFNULL(country, '') AS country,
  IFNULL(language, '') AS language,
  channel_name,
  sentiment_rating,
  is_recommend,
  SUBSTR(COALESCE(NULLIF(content_to_zh, ''), NULLIF(content, ''), ''), 1, 240) AS snippet,
  GREATEST(IFNULL(tweets_like, 0), 0) AS likes,
  GREATEST(IFNULL(tweets_reply, 0), 0) AS replies,
  GREATEST(IFNULL(tweets_retweet, 0), 0) AS retweets,
  COALESCE(
    NULLIF(content_url, ''),
    ARRAY(
      SELECT s.url FROM UNNEST(sources) s
      WHERE s.url IS NOT NULL AND s.url != '' AND LOWER(s.url) != 'null'
      LIMIT 1
    )[SAFE_OFFSET(0)],
    ''
  ) AS source_url
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '{game_id}'
  AND {_channel_clause(channel)}
  AND comment_time >= TIMESTAMP('{_ts(start)}')
  AND comment_time <  TIMESTAMP('{_ts(end)}')
  AND {NEGATIVE_FILTER[channel]}
  AND (
    (content_url IS NOT NULL AND content_url != '' AND LOWER(content_url) != 'null')
    OR EXISTS (
      SELECT 1 FROM UNNEST(sources) s
      WHERE s.url IS NOT NULL AND s.url != '' AND LOWER(s.url) != 'null'
    )
  )
ORDER BY (
  GREATEST(IFNULL(tweets_like, 0), 0)
  + GREATEST(IFNULL(tweets_reply, 0), 0)
  + GREATEST(IFNULL(tweets_retweet, 0), 0)
) DESC, comment_time DESC
LIMIT {candidate_n}
""".strip()
    rows = query(sql)
    out: list[dict] = []
    for r in rows:
        url = str(r.get("source_url") or "").strip()
        if not url.startswith(("http://", "https://")):
            continue
        likes = int(r.get("likes", 0))
        replies = int(r.get("replies", 0))
        retweets = int(r.get("retweets", 0))
        country = r.get("country") or ""
        if channel == "steam" and country in {"global", "unknown"}:
            country = ""
        out.append({
            "reviewer": r.get("reviewer") or "",
            "comment_uin": r.get("comment_uin") or "",
            "comment_time": str(r.get("comment_time") or ""),
            "country": country,
            "language": r.get("language") or "",
            "channel_name": r.get("channel_name") or "",
            "sentiment_rating": r.get("sentiment_rating"),
            "is_recommend": r.get("is_recommend"),
            "snippet": r.get("snippet") or "",
            "engagement": likes + replies + retweets,
            "likes": likes,
            "replies": replies,
            "retweets": retweets,
            "url": url,
        })
        if len(out) >= top_n:
            break
    return out


# ---------------------------------------------------------------------------
# 对外入口
# ---------------------------------------------------------------------------
def build_attribution(
    channel: str,
    game_id: str,
    hours: int = 6,
    top_n: int = 5,
    now: Optional[datetime] = None,
) -> dict:
    """生成完整归因结果（高频投诉来源分布 + 代表性差评 Top N）。"""
    if channel not in NEGATIVE_FILTER:
        raise ValueError(f"不支持的 channel: {channel}")
    validate_game_id(game_id)
    if now is None:
        now = datetime.now(timezone.utc)
    start = now - timedelta(hours=hours)

    distribution = query_complaint_distribution(channel, game_id, start, now, top_n=top_n)
    top_reviews = query_top_negative_reviews(channel, game_id, start, now, top_n=top_n)

    return {
        "channel": channel,
        "game_id": game_id,
        "window": {"start": _ts(start), "end": _ts(now), "hours": hours},
        "complaint_distribution": distribution,
        "top_negative_reviews": top_reviews,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="商店评分告警归因（投诉分布 + 代表性差评 Top N）")
    parser.add_argument("--game_id", required=False, default="")
    parser.add_argument("--channel", choices=["steam", "google_play", "app_store"])
    parser.add_argument("--hours", type=int, default=6, help="归因窗口（小时）")
    parser.add_argument("--top_n", type=int, default=5)
    parser.add_argument("--output", default="/tmp/attribution.json")
    parser.add_argument("--self_test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    if not args.game_id or not args.channel:
        parser.error("需要 --game_id 和 --channel（或使用 --self_test）")

    try:
        result = build_attribution(args.channel, args.game_id.strip(),
                                   hours=args.hours, top_n=args.top_n)
    except RateLimitedError as e:
        print(f"[ERROR] 限流：{e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    d = result["complaint_distribution"]
    print(f"窗口 {args.hours}h 共 {d['total_negative']} 条负面；"
          f"Top 国家 {[x['key'] for x in d['by_country'][:3]]}；"
          f"代表性差评 {len(result['top_negative_reviews'])} 条 → {args.output}")


# ---------------------------------------------------------------------------
# Self test
# ---------------------------------------------------------------------------
def _self_test() -> int:
    """端到端 smoke test：用 PUBGM GP 跑 6h 归因，能取到数据就 PASS（限流容忍 SKIP）。"""
    failures, skipped = [], []
    print("=== attribution self test ===")

    test_cases = [
        ("google_play", "ufc454d9b1af70b40588e2a6fa4da4a8b", "PUBGM GP"),
        ("app_store", "ufc454d9b1af70b40588e2a6fa4da4a8b", "PUBGM AS"),
    ]

    for channel, game_id, label in test_cases:
        try:
            r = build_attribution(channel, game_id, hours=6, top_n=3)
            d = r["complaint_distribution"]
            print(f"  ✅ {label}: total={d['total_negative']}, "
                  f"top_country={[x['key'] for x in d['by_country'][:3]]}, "
                  f"top_reviews={len(r['top_negative_reviews'])}")
        except RateLimitedError:
            print(f"  ⚠️  {label}: 限流跳过")
            skipped.append(label)
        except Exception as e:
            print(f"  ❌ {label}: {type(e).__name__}: {e}")
            failures.append(label)

    print(f"\n{'-' * 40}")
    print(f"PASS={len(test_cases) - len(failures) - len(skipped)} "
          f"FAIL={len(failures)} SKIP={len(skipped)}")
    return 1 if failures else 0


if __name__ == "__main__":
    main()
