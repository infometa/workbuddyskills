#!/usr/bin/env python3
"""
Databrain Intl Opinion SQL 查询脚本。
从环境变量 DATABRAIN_TOKEN 读取 token，依次执行两条 SQL 查询：
  1. 官号主贴（official_posts）
  2. 官帖下的评论（post_comments）— 仅查 comment_parent_id IN (官帖 comment_id 集合)
两个结果分别保存为 CSV 文件，输出路径以 JSON 形式打印到 stdout。

用法:
  python opinion_query.py "<game_id>" "<game_name>" "<start_time>" "<end_time>" [<timestamp>]
                          [--country=<country>] [--language=<language>]
  例（全局）：
    python opinion_query.py "u36542a7ff008ac4ab8440c34b8f02f40" "Honkai Star Rail" "2025-01-01 00:00:00" "2025-03-31 23:59:59"
  例（按国家）：
    python opinion_query.py "u36542a7ff008ac4ab8440c34b8f02f40" "Honkai Star Rail" "2025-01-01 00:00:00" "2025-03-31 23:59:59" --country=us
  例（多个国家）：
    python opinion_query.py "u36542a7ff008ac4ab8440c34b8f02f40" "Honkai Star Rail" "2025-01-01 00:00:00" "2025-03-31 23:59:59" --country=us,ca,mx
  例（按语言）：
    python opinion_query.py "u36542a7ff008ac4ab8440c34b8f02f40" "Honkai Star Rail" "2025-01-01 00:00:00" "2025-03-31 23:59:59" --language=ja
  例（同时指定）：
    python opinion_query.py "u36542a7ff008ac4ab8440c34b8f02f40" "Honkai Star Rail" "2025-01-01 00:00:00" "2025-03-31 23:59:59" --country=jp --language=ja
"""
import argparse
import io
import os
import sys
import json
import datetime

import httpx
import pandas as pd

_DEFAULT_INTL_HOST = "https://databrain.intlgame.com"
API_PATH = "/api/v1/opinion_pc/global/query"

# ── SQL 模板 ────────────────────────────────────────────────────────────────

_OFFICIAL_POSTS_SQL = """\
WITH media_accounts AS (
    SELECT account_url AS account_link
    FROM `tencent-databrain-prod.opinion.dim_media_account`
    WHERE unified_edition_id='{game_id}'
      AND category='official-accounts'{country_filter}
)
SELECT
    comment_uin,
    DATETIME(comment_time) AS comment_time,
    comment_id,
    comment_parent_id,
    follower_number,
    sources,
    media_type,
    image,
    video_detail,
    description,
    reviewer,
    content,
    content_to_en,
    content_to_zh,
    isvalid,
    sentiment_rating,
    keywords,
    topics,
    channel_name,
    country,
    language,
    content_url,
    tweets_view,
    tweets_like,
    tweets_reply,
    tweets_retweet
FROM `tencent-databrain-prod.opinion.feeds`, UNNEST(sources) s
WHERE unified_edition_id='{game_id}'
  AND comment_parent_id = '-1'
  AND comment_time>='{start_time}'
  AND comment_time<='{end_time}'{language_filter}
  AND s.url IN (SELECT account_link FROM media_accounts)\
"""

_POST_COMMENTS_SQL = """\
SELECT
    comment_uin,
    DATETIME(comment_time) AS comment_time,
    comment_id,
    comment_parent_id,
    follower_number,
    sources,
    media_type,
    image,
    video_detail,
    description,
    reviewer,
    content,
    content_to_en,
    content_to_zh,
    isvalid,
    sentiment_rating,
    keywords,
    topics,
    channel_name,
    country,
    language,
    content_url,
    tweets_view,
    tweets_like,
    tweets_reply,
    tweets_retweet
FROM `tencent-databrain-prod.opinion.feeds`, UNNEST(sources) s
WHERE unified_edition_id='{game_id}'
  AND comment_time>='{start_time}'
  AND comment_time<='{end_time}'
  AND comment_parent_id IN ({comment_ids})\
"""

# ── 工具函数 ─────────────────────────────────────────────────────────────────

def _load_dotenv() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.abspath(os.path.join(script_dir, ".."))
    plugin_root = os.path.abspath(os.path.join(skill_dir, "..", ".."))
    for base in [plugin_root, skill_dir, os.getcwd(), script_dir]:
        env_path = os.path.join(base, ".env")
        if os.path.isfile(env_path):
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and os.environ.get(k) is None:
                            os.environ[k] = v


def _query_csv(sql: str, token: str, host: str) -> bytes | dict:
    """执行单条 SQL，返回 CSV bytes 或 error dict。"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    try:
        resp = httpx.post(host + API_PATH, headers=headers, json={"sql": sql}, timeout=120.0)
    except httpx.HTTPError as e:
        return {"error": {"code": "REQUEST", "message": str(e)}}

    if resp.status_code != 200:
        msg = resp.text.strip()[:500] or ("Unauthorized: token 无效、过期或无权限" if resp.status_code == 401 else "")
        return {"error": {"code": resp.status_code, "message": msg}}

    content_type = resp.headers.get("content-type", "")
    if "text/csv" not in content_type:
        return {"error": {"code": "UNEXPECTED_CONTENT_TYPE", "message": f"期望 text/csv，实际收到: {content_type}"}}

    return resp.content


def _preprocess_official_posts(data: bytes) -> bytes:
    """为 official_posts 添加 engagement 列，按 engagement 降序排列后按 comment_uin 去重，返回处理后的 CSV bytes。"""
    df = pd.read_csv(io.BytesIO(data), encoding="utf-8-sig")
    df["engagement"] = (
        df.get("tweets_like", pd.Series(0, index=df.index)).fillna(0)
        + df.get("tweets_reply", pd.Series(0, index=df.index)).fillna(0)
        + df.get("tweets_retweet", pd.Series(0, index=df.index)).fillna(0)
    ).astype(int)
    df = df.sort_values("engagement", ascending=False)
    df = df.drop_duplicates(subset=["comment_uin"], keep="first")
    return df.to_csv(index=False).encode("utf-8-sig")


def _preprocess_post_comments(data: bytes) -> bytes:
    """对 post_comments 按 comment_uin 去重，返回处理后的 CSV bytes。"""
    df = pd.read_csv(io.BytesIO(data), encoding="utf-8-sig")
    df = df.drop_duplicates(subset=["comment_uin"], keep="first")
    return df.to_csv(index=False).encode("utf-8-sig")


def _save_csv(data: bytes, filename: str) -> tuple[str, int]:
    """保存 CSV，返回 (文件路径, 数据行数（不含表头）)。"""
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = os.path.join(skill_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, filename)
    with open(path, "wb") as f:
        f.write(data)

    import csv as _csv
    reader = _csv.reader(io.StringIO(data.decode("utf-8-sig")))
    row_count = max(0, sum(1 for _ in reader) - 1)  # 减去表头行
    return path, row_count


# ── 主入口 ───────────────────────────────────────────────────────────────────

def run_queries(
    game_id: str,
    game_name: str,
    start_time: str,
    end_time: str,
    *,
    token: str | None = None,
    host: str | None = None,
    timestamp: str | None = None,
    country: str | None = None,
    language: str | None = None,
) -> dict:
    """
    执行两条 SQL 查询，保存 CSV 文件。

    country:
      - 若指定单个国家（如 "us"），在 media_accounts CTE 中追加：
            AND country = 'us'
      - 若指定多个国家（如 "us,ca,mx" 或 "us, ca, mx"），在 media_accounts CTE 中追加：
            AND country IN ('us', 'ca', 'mx')

    language:
      - 若指定，在主查询 WHERE 中追加：
            AND language = '<language>'

    两者可同时使用，均不指定时等同于原有全局查询。

    返回:
      {"official_posts": {"path": ..., "rows": ...}, "post_comments": {"path": ..., "rows": ...}}
    或
      {"error": {"code": ..., "message": ...}}
    """
    _load_dotenv()

    token = (token or os.environ.get("DATABRAIN_TOKEN", "")).strip()
    if not token:
        return {"error": {"code": "CONFIG", "message": "DATABRAIN_TOKEN not set"}}

    host = (host or os.environ.get("DATABRAIN_INTL_HOST", _DEFAULT_INTL_HOST)).strip().rstrip("/")
    safe_name = game_name.replace(" ", "_").replace(":", "")

    # 解析 country：支持单个国家，也支持逗号分隔的多个国家
    countries = [c.strip() for c in country.split(",")] if country else []
    countries = [c for c in countries if c]

    # 计算文件命名前缀：有区域标识时追加 _{REGION}
    country_label = "_".join(countries) if countries else None
    region_parts = [p for p in [country_label, language] if p]
    region_suffix = "_".join(region_parts)
    file_key = f"{safe_name}_{region_suffix}" if region_suffix else safe_name

    # 计算 SQL 可选过滤子句
    if countries:
        if len(countries) == 1:
            country_filter = f"\n      AND country = '{countries[0]}'"
        else:
            in_list = ", ".join(f"'{c}'" for c in countries)
            country_filter = f"\n      AND country IN ({in_list})"
    else:
        country_filter = ""

    language_filter = f"\n  AND language = '{language}'" if language else ""

    base_params = {
        "game_id": game_id,
        "start_time": start_time,
        "end_time": end_time,
        "country_filter": country_filter,
        "language_filter": language_filter,
    }

    if not timestamp:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    result = {}

    # ── 第一步：查询官号主贴 ──────────────────────────────────────────────────
    region_label = f" [{region_suffix}]" if region_suffix else ""
    print(f"[opinion_query] 正在查询 official_posts{region_label} ...", file=sys.stderr)

    data = _query_csv(_OFFICIAL_POSTS_SQL.format(**base_params), token, host)
    if isinstance(data, dict):
        return data

    data = _preprocess_official_posts(data)
    path, rows = _save_csv(data, f"{file_key}_official_posts_{timestamp}.csv")
    result["official_posts"] = {"path": path, "rows": rows}
    print(f"[opinion_query] official_posts 已保存：{path}（{rows} 行）", file=sys.stderr)

    # ── 第二步：从官帖提取 comment_id，精准查询帖子评论 ──────────────────────
    official_df = pd.read_csv(io.BytesIO(data), encoding="utf-8-sig")
    comment_ids = official_df["comment_id"].dropna().astype(str).tolist()
    if not comment_ids:
        return {"error": {"code": "NO_POSTS", "message": "official_posts 为空，无法查询评论"}}

    ids_literal = ", ".join(f"'{cid}'" for cid in comment_ids)
    post_comments_sql = _POST_COMMENTS_SQL.format(
        game_id=game_id,
        start_time=start_time,
        end_time=end_time,
        comment_ids=ids_literal,
    )

    print(f"[opinion_query] 正在查询 post_comments（共 {len(comment_ids)} 个官帖）...", file=sys.stderr)
    data = _query_csv(post_comments_sql, token, host)
    if isinstance(data, dict):
        return data

    data = _preprocess_post_comments(data)
    path, rows = _save_csv(data, f"{file_key}_post_comments_{timestamp}.csv")
    result["post_comments"] = {"path": path, "rows": rows}
    print(f"[opinion_query] post_comments 已保存：{path}（{rows} 行）", file=sys.stderr)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Databrain Intl 官号舆情查询脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("game_id", help="unified_edition_id")
    parser.add_argument("game_name", help="游戏名称")
    parser.add_argument("start_time", help="查询起始时间，如 '2025-01-01 00:00:00'")
    parser.add_argument("end_time", help="查询结束时间，如 '2025-03-31 23:59:59'")
    parser.add_argument("timestamp", nargs="?", default=None, help="全局 timestamp（可选）")
    parser.add_argument(
        "--country",
        default=None,
        help="按国家筛选官号账号。支持单个国家（如 us）或多个国家（如 us,ca,mx）",
    )
    parser.add_argument("--language", default=None, help="按语言筛选帖子，如 en、ja、zh-CN")
    args = parser.parse_args()

    result = run_queries(
        args.game_id,
        args.game_name,
        args.start_time,
        args.end_time,
        timestamp=args.timestamp,
        country=args.country,
        language=args.language,
    )

    if "error" in result:
        print("Error:", json.dumps(result["error"], ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())