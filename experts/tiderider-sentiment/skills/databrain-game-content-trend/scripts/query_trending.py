#!/usr/bin/env python3
"""
Marketing Hub BigQuery 查询脚本。
通过 Global Query API 查询 tencent-databrain-prod.marketing_hub 数据集，
获取热门视频趋势、KOL 信息和 Gaming Hashtag 趋势。

用法:
  命令行: python query_trending.py
          python query_trending.py --platform tiktok --region na --limit 20
  代码:   videos = await query_trending_videos(platform="tiktok", region="na")
"""
import argparse
import asyncio
import csv
import io
import json
import os
import sys
import threading
from datetime import datetime, timedelta
from typing import Any, Optional

from report_log import new_session_msg_pair, report

import httpx

_DEFAULT_HOST = "https://databrain.mcp.it.woa.com"
_TRUSTED_HOSTS = ("databrain.mcp.it.woa.com",)
_API_PATH = "/api/v1/opinion_pc/global/query"
_BQ_DATASET = "tencent-databrain-prod.marketing_hub"
_BQ_OPINION = "tencent-databrain-prod.opinion"

_VALID_PLATFORMS = {"tiktok", "youtube"}
_VALID_REGIONS = {"af", "eur", "in", "jpn", "kr", "me", "na", "oa", "sa", "sea"}
_VALID_CATEGORIES = {
    "Comedy", "Entertainment", "Film & Animation", "Games",
    "Howto & Style", "Music", "Nonprofits & Activism", "Now",
    "Other", "People & Blogs", "Sports & Outdoor",
}
_VALID_MEME_REGIONS = {"EN", "EN_NA", "ES", "GLOBAL", "KR", "LATAM_MULTI", "SEA_MULTI", "ZH_CN"}
_VALID_MEME_TYPES = {
    "Absurd & Remix Meme Culture", "Audio Memes", "Beautiful Scenery & Aesthetics",
    "Challenge & Participation", "Dance & Movement Trends", "Emotional & Quotes",
    "Emotional Trends", "Entertainment & Media Trends", "Gaming Viral Moments",
    "Lifestyle & Cultural Trends", "Meme & Internet Culture", "Parent and Child",
    "Pet & Animal Content", "Pop Music Trends", "Seasonal & Holiday Trends",
    "Shock / Curiosity Driven Trends", "Technology Trends",
}
_VALID_MEME_ELEMENTS = {
    "ABSTRACT_HYBRID", "ACTION_GESTURE", "AUDIO_SIGNATURE",
    "Abstract / Hybrid Memes", "Iconic Visual Appearance", "NARRATIVE_DRIVEN",
    "Signature Actions & Gestures", "Signature Audio & Sound", "TEXT_EXPRESSION",
    "VISUAL_IDENTITY",
}
_COUNTRY_RE = __import__("re").compile(r"^[a-z]{2}$")

_VIDEO_FIELDS = (
    "date_time, video_url, channel_name, video_title, video_title_zh, "
    "video_title_en, video_release_time, video_duration, anchor_name, "
    "anchors_followers, video_cover, tweets_view, tweets_like, "
    "tweets_comment, tweets_retweet, region, country, category"
)

_MEME_FIELDS = (
    "channels, title, title_zh, content, content_zh, meme_type, meme_type_zh, "
    "meme_elements, meme_elements_zh, tags, raw_url, raw_title, raw_cover, "
    "hot_extension, extend_urls, hot_time, create_time, region_code, region_code_zh"
)


def _is_trusted_host(host: str) -> bool:
    from urllib.parse import urlparse
    hostname = urlparse(host).hostname or ""
    return hostname in _TRUSTED_HOSTS


def _validate_enum(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise ValueError(f"Invalid {field_name}: '{value}'. Allowed: {sorted(allowed)}")
    return value


def _validate_country(value: str) -> str:
    if not _COUNTRY_RE.match(value):
        raise ValueError(f"Invalid country code: '{value}'. Must be a 2-letter ISO code (e.g. 'us', 'jp').")
    return value


def _sanitize_keyword(value: str) -> str:
    return value.lower().replace("\\", "").replace("'", "\\'").replace(";", "").replace("--", "")


def _quote_sql_string(value: str) -> str:
    return "'" + value.replace("\\", "").replace("'", "\\'") + "'"


def _snapshot_date_string(snapshot_date: Any) -> str:
    return datetime.strptime(str(snapshot_date)[:10], "%Y-%m-%d").date().isoformat()


def _date_cutoff_from_snapshot(snapshot_date: Any, days: int) -> str:
    snapshot = datetime.strptime(_snapshot_date_string(snapshot_date), "%Y-%m-%d").date()
    return (snapshot - timedelta(days=int(days))).isoformat()


def _load_dotenv() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.abspath(os.path.join(script_dir, ".."))
    plugin_root = os.path.abspath(os.path.join(skill_dir, "..", ".."))
    for env_path in [os.path.join(plugin_root, ".env"), os.path.join(skill_dir, ".env"), os.path.join(os.getcwd(), ".env")]:
        if not os.path.isfile(env_path):
            continue
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and os.environ.get(k) is None:
                        os.environ[k] = v


def _get_config(token: Optional[str] = None, host: Optional[str] = None) -> tuple[str, list[str]]:
    """Return (token, hosts_to_try) using DataBrain auth and the Databrain MCP host."""
    _load_dotenv()
    token = (token or os.environ.get("DATABRAIN_TOKEN", "")).strip()
    if not token:
        raise RuntimeError(
            "DATABRAIN_TOKEN not set. "
            "请前往 DataBrain 个人令牌中心获取\"授权访问应用-全部应用\"的 token "
            "（内网 https://databrain.woa.com/v2/user-center/personal-tokens-center，"
            "外网 https://databrain-global.intlgame.com/v2/user-center/personal-tokens-center），"
            "并设置环境变量 DATABRAIN_TOKEN（不含 Bearer 前缀）。"
        )
    target_host = (host or os.environ.get("DATABRAIN_HOST", "") or _DEFAULT_HOST).strip().rstrip("/")
    if not _is_trusted_host(target_host):
        raise RuntimeError(
            f"DATABRAIN_HOST '{target_host}' 不在受信任域名列表中。"
            "允许的域名：databrain.mcp.it.woa.com"
        )
    return token, [target_host]


def _parse_csv(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text), quoting=csv.QUOTE_MINIMAL)
    rows: list[dict[str, Any]] = []
    for row in reader:
        parsed: dict[str, Any] = {}
        for k, v in row.items():
            if v is None or v == "":
                parsed[k] = None
            else:
                try:
                    parsed[k] = int(v)
                except ValueError:
                    try:
                        parsed[k] = float(v)
                    except ValueError:
                        parsed[k] = v
            parsed[k] = parsed.get(k, v)
        rows.append(parsed)
    if not rows and text.strip():
        preview = text.replace("\n", "\\n").replace("\r", "\\r")[:200]
        print(f"[query] CSV parsed 0 rows. Preview: {preview}", file=sys.stderr)
    return rows


async def run_sql_query(sql: str, *, token: Optional[str] = None, host: Optional[str] = None) -> list[dict[str, Any]]:
    """Execute a BigQuery SQL via the Global Query API. Returns parsed rows."""
    sql = " ".join(sql.split())
    tok, hosts = _get_config(token, host)
    last_error: Optional[Exception] = None

    for h in hosts:
        endpoint = h + _API_PATH
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {tok}",
            "User-Agent": "game-content-trend-skill",
        }
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(endpoint, headers=headers, json={"sql": sql})

                if resp.status_code != 200:
                    body = resp.text.strip()
                    try:
                        err = json.loads(body)
                        msg = str(err.get("msg", ""))[:200]
                    except json.JSONDecodeError:
                        msg = body[:200]
                    raise RuntimeError(f"Query API error (HTTP {resp.status_code}): {msg}")

                if not resp.text.strip():
                    if attempt < 2:
                        if attempt == 1:
                            await asyncio.sleep(2)
                        continue
                    raise RuntimeError("Empty response body from query API")

                content_type = resp.headers.get("content-type", "")
                if "text/csv" in content_type:
                    return _parse_csv(resp.text)

                try:
                    err = json.loads(resp.text)
                    if err.get("code", 0) != 0:
                        raise RuntimeError(f"Query failed: {str(err.get('msg', ''))[:200]}")
                except json.JSONDecodeError:
                    pass
                return _parse_csv(resp.text)

            except (httpx.ConnectError, httpx.TimeoutException, RuntimeError) as exc:
                last_error = exc
                if len(hosts) > 1:
                    print(f"[fallback] {h} failed ({exc.__class__.__name__}), trying next...", file=sys.stderr)
                break

    raise RuntimeError(f"All hosts failed. Last error: {last_error}")


def _build_video_filters(
    *,
    platform: Optional[str] = None,
    region: Optional[str] = None,
    country: Optional[str] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
) -> list[str]:
    filters = []
    if category:
        _validate_enum(category, _VALID_CATEGORIES, "category")
        filters.append(f"AND category = '{category}'")
    if platform:
        _validate_enum(platform, _VALID_PLATFORMS, "platform")
        filters.append(f"AND channel_name = '{platform}'")
    if region:
        _validate_enum(region, _VALID_REGIONS, "region")
        filters.append(f"AND region = '{region}'")
    if country:
        _validate_country(country)
        filters.append(f"AND country = '{country}'")
    if keyword:
        kw = _sanitize_keyword(keyword)
        filters.append(
            "AND (LOWER(video_title) LIKE '%{kw}%' "
            "OR LOWER(video_title_zh) LIKE '%{kw}%' "
            "OR LOWER(video_title_en) LIKE '%{kw}%')".format(kw=kw)
        )
    return filters


async def _latest_video_snapshot_date(
    filters: list[str],
    *,
    before_date: Optional[str] = None,
    token: Optional[str] = None,
    host: Optional[str] = None,
) -> Optional[str]:
    filter_clause = "\n  ".join(filters)
    before_filter = f"AND date_time < DATE '{before_date}'" if before_date else ""
    sql = f"""
SELECT MAX(date_time) AS snapshot_date
FROM `{_BQ_DATASET}.marketing_hub_video_trending`
WHERE 1 = 1
  {before_filter}
  {filter_clause}
""".strip()
    rows = await run_sql_query(sql, token=token, host=host)
    snapshot_date = rows[0].get("snapshot_date") if rows else None
    return _snapshot_date_string(snapshot_date) if snapshot_date else None


async def query_trending_videos(
    *,
    platform: Optional[str] = None,
    region: Optional[str] = None,
    country: Optional[str] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    sort_by: str = "views",
    max_video_age_days: int = 7,
    limit: int = 50,
    token: Optional[str] = None,
    host: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Query recent trending videos with basic filters and snapshot growth."""
    filters = _build_video_filters(platform=platform, region=region, country=country, category=category, keyword=keyword)
    snapshot_filter_clause = "\n  ".join(filters)
    fetch_limit = max(int(limit) * 3, int(limit))

    current_snapshot_date = await _latest_video_snapshot_date(filters, token=token, host=host)
    if not current_snapshot_date:
        return []

    cutoff_date = _date_cutoff_from_snapshot(current_snapshot_date, max_video_age_days)
    query_filters = [f"AND video_release_time >= '{cutoff_date}'", *filters]
    filter_clause = "\n  ".join(query_filters)

    sql = f"""
SELECT {_VIDEO_FIELDS}
FROM `{_BQ_DATASET}.marketing_hub_video_trending`
WHERE date_time = DATE '{current_snapshot_date}'
  {filter_clause}
ORDER BY tweets_view DESC
LIMIT {fetch_limit}
""".strip()

    rows = _dedupe_videos(await run_sql_query(sql, token=token, host=host), fetch_limit)

    if sort_by == "growth":
        urls = [str(row["video_url"]) for row in rows if row.get("video_url")]
        if not urls:
            return rows[: int(limit)]

        previous_snapshot_date = await _latest_video_snapshot_date(filters, before_date=current_snapshot_date, token=token, host=host)
        if not previous_snapshot_date:
            _attach_growth(rows, [])
            rows.sort(key=lambda r: r.get("growth_24h") if r.get("growth_24h") is not None else float("-inf"), reverse=True)
            return rows[: int(limit)]

        urls_csv = ", ".join(_quote_sql_string(url) for url in urls)
        previous_sql = f"""
SELECT video_url, tweets_view
FROM `{_BQ_DATASET}.marketing_hub_video_trending`
WHERE date_time = DATE '{previous_snapshot_date}'
  AND video_url IN ({urls_csv})
  {snapshot_filter_clause}
""".strip()
        previous_rows = await run_sql_query(previous_sql, token=token, host=host)
        _attach_growth(rows, previous_rows)
        rows.sort(key=lambda r: r.get("growth_24h") if r.get("growth_24h") is not None else float("-inf"), reverse=True)

    return rows[: int(limit)]


def _dedupe_videos(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_url: dict[str, dict[str, Any]] = {}
    for row in rows:
        url = row.get("video_url")
        if not url:
            continue
        current = by_url.get(url)
        if current is None or (row.get("tweets_view") or 0) > (current.get("tweets_view") or 0):
            by_url[url] = row
    return list(by_url.values())[:limit]


def _attach_growth(rows: list[dict[str, Any]], previous_rows: list[dict[str, Any]]) -> None:
    previous: dict[str, int | float] = {}
    for row in previous_rows:
        url = row.get("video_url")
        views = row.get("tweets_view")
        if url and isinstance(views, (int, float)):
            previous[url] = max(previous.get(url, 0), views)

    for row in rows:
        current_views = row.get("tweets_view")
        previous_views = previous.get(row.get("video_url"))
        if isinstance(current_views, (int, float)) and previous_views:
            row["growth_24h"] = round((current_views - previous_views) / previous_views * 100, 1)
        else:
            row["growth_24h"] = None


async def query_kol_info(anchor_names: list[str], *, token: Optional[str] = None, host: Optional[str] = None) -> list[dict[str, Any]]:
    if not anchor_names:
        return []
    names_csv = ", ".join(f"'{n}'" for n in anchor_names)
    sql = f"""
SELECT anchor_name, description, followers_number, posts_number, likes_number, country, region
FROM `{_BQ_DATASET}.marketing_hub_kol_info`
WHERE anchor_name IN ({names_csv})
""".strip()
    return await run_sql_query(sql, token=token, host=host)


async def query_hashtag_trends(
    *,
    region: Optional[str] = None,
    country: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 20,
    token: Optional[str] = None,
    host: Optional[str] = None,
) -> list[dict[str, Any]]:
    filters = []
    if region:
        _validate_enum(region, _VALID_REGIONS, "region")
        filters.append(f"AND region = '{region}'")
    if country:
        _validate_country(country)
        filters.append(f"AND country = '{country}'")
    if keyword:
        kw = _sanitize_keyword(keyword)
        filters.append(f"AND LOWER(hashtag) LIKE '%{kw}%'")
    filter_clause = "\n    ".join(filters)

    sql = f"""
SELECT date, country, region, time_range, hashtag, tweets_views
FROM `{_BQ_DATASET}.marketing_hub_hashtag_trending_tiktok_gaming`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
  AND time_range = 'last_7_days'
    {filter_clause}
ORDER BY tweets_views DESC
LIMIT {limit}
""".strip()
    return await run_sql_query(sql, token=token, host=host)


async def query_hashtag_videos(hashtag: str, *, limit: int = 20, token: Optional[str] = None, host: Optional[str] = None) -> list[dict[str, Any]]:
    sql = f"""
SELECT hashtag, video_url, video_title_zh, video_title_en, anchor_name,
       tweets_view, tweets_like, tweets_comment, tweets_retweet, country, region
FROM `{_BQ_DATASET}.marketing_hub_hashtag_video`
WHERE hashtag = '{hashtag}'
ORDER BY tweets_view DESC
LIMIT {limit}
""".strip()
    return await run_sql_query(sql, token=token, host=host)


async def query_memes(
    *,
    region_code: Optional[str] = None,
    meme_type: Optional[str] = None,
    meme_elements: Optional[str] = None,
    days: int = 14,
    limit: int = 30,
    token: Optional[str] = None,
    host: Optional[str] = None,
) -> list[dict[str, Any]]:
    filters = []
    if region_code:
        _validate_enum(region_code, _VALID_MEME_REGIONS, "region_code")
        filters.append(f"AND region_code = '{region_code}'")
    if meme_type:
        _validate_enum(meme_type, _VALID_MEME_TYPES, "meme_type")
        filters.append(f"AND meme_type = '{meme_type}'")
    if meme_elements:
        _validate_enum(meme_elements, _VALID_MEME_ELEMENTS, "meme_elements")
        filters.append(f"AND meme_elements = '{meme_elements}'")
    filter_clause = "\n  ".join(filters)

    sql = f"""
SELECT {_MEME_FIELDS}
FROM `{_BQ_OPINION}.memes`
WHERE hot_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {int(days)} DAY)
  {filter_clause}
ORDER BY hot_time DESC
LIMIT {int(limit)}
""".strip()
    return await run_sql_query(sql, token=token, host=host)


async def query_memes_by_keyword(keyword: str, *, days: int = 90, limit: int = 10, token: Optional[str] = None, host: Optional[str] = None) -> list[dict[str, Any]]:
    kw = _sanitize_keyword(keyword)
    sql = f"""
SELECT {_MEME_FIELDS}
FROM `{_BQ_OPINION}.memes`
WHERE (LOWER(title) LIKE '%{kw}%'
   OR LOWER(title_zh) LIKE '%{kw}%'
   OR LOWER(content_zh) LIKE '%{kw}%')
  AND hot_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {int(days)} DAY)
ORDER BY hot_time DESC
LIMIT {int(limit)}
""".strip()
    return await run_sql_query(sql, token=token, host=host)


async def query_video_ai_tags(video_urls: list[str], *, token: Optional[str] = None, host: Optional[str] = None) -> list[dict[str, Any]]:
    if not video_urls:
        return []
    urls_csv = ", ".join(_quote_sql_string(u) for u in video_urls)
    sql = f"""
SELECT video_url, summary, meme_trend, text, language_country
FROM `{_BQ_DATASET}.marketing_hub_video_ai_tags`
WHERE video_url IN ({urls_csv})
""".strip()
    return await run_sql_query(sql, token=token, host=host)


async def query_videos_by_ai_tags(
    keyword: str,
    *,
    platform: Optional[str] = None,
    region: Optional[str] = None,
    country: Optional[str] = None,
    category: Optional[str] = None,
    max_video_age_days: int = 7,
    limit: int = 20,
    token: Optional[str] = None,
    host: Optional[str] = None,
) -> list[dict[str, Any]]:
    filters = _build_video_filters(platform=platform, region=region, country=country, category=category)
    urls = await _lookup_ai_tag_urls(keyword, limit=max(limit * 10, 100), token=token, host=host)
    if not urls:
        return []

    current_snapshot_date = await _latest_video_snapshot_date(filters, token=token, host=host)
    if not current_snapshot_date:
        return []

    cutoff_date = _date_cutoff_from_snapshot(current_snapshot_date, max_video_age_days)
    filters = [f"AND video_release_time >= '{cutoff_date}'", *filters]
    filter_clause = "\n  ".join(filters)
    urls_csv = ", ".join(_quote_sql_string(u) for u in urls[:200])
    fetch_limit = max(int(limit) * 3, int(limit))

    sql = f"""
SELECT {_VIDEO_FIELDS}
FROM `{_BQ_DATASET}.marketing_hub_video_trending`
WHERE date_time = DATE '{current_snapshot_date}'
  AND video_url IN ({urls_csv})
  {filter_clause}
ORDER BY tweets_view DESC
LIMIT {fetch_limit}
""".strip()
    return _dedupe_videos(await run_sql_query(sql, token=token, host=host), int(limit))


async def _lookup_ai_tag_urls(keyword: str, *, limit: int = 200, token: Optional[str] = None, host: Optional[str] = None) -> list[str]:
    kw = _sanitize_keyword(keyword)
    sql = f"""
SELECT DISTINCT video_url
FROM `{_BQ_DATASET}.marketing_hub_video_ai_tags`
WHERE LOWER(summary) LIKE '%{kw}%'
   OR LOWER(meme_trend) LIKE '%{kw}%'
   OR LOWER(text) LIKE '%{kw}%'
LIMIT {int(limit)}
""".strip()
    rows = await run_sql_query(sql, token=token, host=host)
    return [str(row["video_url"]) for row in rows if row.get("video_url")]


def _format_number(n: Any) -> str:
    if n is None:
        return "N/A"
    if isinstance(n, (int, float)):
        if n >= 1_000_000_000:
            return f"{n / 1_000_000_000:.1f}B"
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(int(n))
    return str(n)


async def amain() -> int:
    parser = argparse.ArgumentParser(description="Query marketing_hub trending videos")
    parser.add_argument("--platform", choices=["tiktok", "youtube"], default=None)
    parser.add_argument("--region", default=None, help="Region code: na, eur, sea, jpn, kr, ...")
    parser.add_argument("--country", default=None, help="Country ISO code: us, gb, jp, ...")
    parser.add_argument("--category", default=None, help="Content category filter (e.g. Games, Music, Entertainment). Default: no filter")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--keyword", default=None, help="Search videos by title keyword")
    parser.add_argument("--sort-by", choices=["views", "growth"], default="views", help="Sort order for videos")
    parser.add_argument("--max-age", type=int, default=7, help="Max video publish age in days")
    parser.add_argument("--hashtag-trends", action="store_true", help="Show hashtag trends instead")
    parser.add_argument("--hashtag", default=None, help="Query videos under a specific hashtag")
    parser.add_argument("--hashtag-keyword", default=None, help="Search hashtag trends by name")
    parser.add_argument("--memes", action="store_true", help="Query trending memes")
    parser.add_argument("--meme-type", default=None, help="Filter memes by type")
    parser.add_argument("--meme-elements", default=None, help="Filter memes by element type")
    parser.add_argument("--meme-keyword", default=None, help="Search memes by keyword")
    parser.add_argument("--ai-tag-keyword", default=None, help="Search videos by AI tag content (summary/meme_trend)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    session_id, msg_id = new_session_msg_pair()
    log_parts = [f"platform={args.platform}", f"region={args.region}", f"limit={args.limit}"]
    if args.hashtag:
        log_parts.append(f"hashtag={args.hashtag}")
    if args.hashtag_trends:
        log_parts.append("hashtag_trends=true")
    if args.memes:
        log_parts.append("memes=true")
    if args.meme_keyword:
        log_parts.append(f"meme_keyword={args.meme_keyword}")
    if args.keyword:
        log_parts.append(f"keyword={args.keyword}")
    if args.ai_tag_keyword:
        log_parts.append(f"ai_tag_keyword={args.ai_tag_keyword}")
    log_message = "query: " + " ".join(log_parts)

    def _report_skill_invocation():
        report(message=log_message, session_id=session_id, msg_id=msg_id)

    report_thread = threading.Thread(target=_report_skill_invocation, daemon=False)
    report_thread.start()

    try:
        if args.ai_tag_keyword:
            rows = await query_videos_by_ai_tags(
                args.ai_tag_keyword,
                platform=args.platform,
                region=args.region,
                country=args.country,
                category=args.category,
                max_video_age_days=args.max_age,
                limit=args.limit,
            )
            label = f"Videos by AI Tag (keyword: {args.ai_tag_keyword})"
        elif args.meme_keyword:
            rows = await query_memes_by_keyword(args.meme_keyword, limit=args.limit)
            label = f"Memes (keyword: {args.meme_keyword})"
        elif args.memes:
            rows = await query_memes(meme_type=args.meme_type, meme_elements=args.meme_elements, limit=args.limit)
            label = "Trending Memes"
        elif args.hashtag:
            rows = await query_hashtag_videos(args.hashtag, limit=args.limit)
            label = f"Hashtag: {args.hashtag}"
        elif args.hashtag_trends:
            rows = await query_hashtag_trends(region=args.region, country=args.country, keyword=args.hashtag_keyword, limit=args.limit)
            label = "Gaming Hashtag Trends"
        else:
            rows = await query_trending_videos(
                platform=args.platform,
                region=args.region,
                country=args.country,
                category=args.category,
                keyword=args.keyword,
                sort_by=args.sort_by,
                max_video_age_days=args.max_age,
                limit=args.limit,
            )
            label = "Trending Videos"
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        report_thread.join(timeout=1.0)
        return 1

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        report_thread.join(timeout=1.0)
        return 0

    sep = "=" * 70
    print(sep)
    print(f"  {label} ({len(rows)} results)")
    print(sep)

    if not rows:
        print("  No results found.")
        report_thread.join(timeout=1.0)
        return 0

    for i, row in enumerate(rows, 1):
        if "meme_type" in row:
            name = row.get("title_zh") or row.get("title") or ""
            print(f"\n  {i}. {name}")
            print(f"     Type: {row.get('meme_type_zh') or row.get('meme_type', '')} | Elements: {row.get('meme_elements_zh') or row.get('meme_elements', '')}")
            print(f"     Region: {row.get('region_code_zh') or row.get('region_code', '')}")
            if row.get("raw_url"):
                print(f"     Ref: {row['raw_url']}")
        elif "video_url" in row:
            title = row.get("video_title_zh") or row.get("video_title") or ""
            growth = row.get("growth_24h")
            growth_str = f"+{growth}%" if growth is not None and growth >= 0 else (f"{growth}%" if growth is not None else "N/A")
            print(f"\n  {i}. {title}")
            print(f"     {row.get('video_url', '')}")
            print(f"     {row.get('channel_name', '')}-{row.get('region', '')}/{row.get('country', '')} | {row.get('video_release_time', '')}")
            print(f"     Views: {_format_number(row.get('tweets_view'))} | 24h: {growth_str} | Likes: {_format_number(row.get('tweets_like'))} | Comments: {_format_number(row.get('tweets_comment'))}")
            print(f"     Author: {row.get('anchor_name', '')} ({_format_number(row.get('anchors_followers', row.get('followers_number')))} followers)")
        elif "hashtag" in row:
            print(f"\n  {i}. {row.get('hashtag', '')}")
            print(f"     Views: {_format_number(row.get('tweets_views'))} | {row.get('country', '')}/{row.get('region', '')} | {row.get('time_range', '')}")

    print(f"\n{sep}")
    report_thread.join(timeout=1.0)
    return 0


def main() -> int:
    return asyncio.run(amain())


if __name__ == "__main__":
    sys.exit(main())
