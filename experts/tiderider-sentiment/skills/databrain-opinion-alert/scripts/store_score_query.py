#!/usr/bin/env python3
"""
store_score_query.py — 三张商店评分表 + feeds 表的取数 + JSON 解析。

数据源
======
1. tencent-databrain-prod.opinion.store_score_steam
   - all_reviews_score / recent_reviews_score（0~1，注意 ×100 得百分比）
   - all_reviews_count / recent_reviews_count（样本量）
   - language_reviews JSON：{"<Language>": {"name":"Very Positive","reviews":25116,"score":0.87}}
   - 每 ~10 分钟一次快照
2. tencent-databrain-prod.opinion.store_score_google_play_daily
3. tencent-databrain-prod.opinion.store_score_app_store_daily
   - 主键 unified_id；按 area + date 一行
   - count_by_rating JSON：{"1":648,"2":0,"3":0,"4":162,"5":0}
4. tencent-databrain-prod.opinion.feeds
   - channel_name 取值带空格：'google play' / 'app store' / 'steam'
   - comment_score：原始 1-5 星（GP/AS 评论自带）
   - sentiment_rating：NLP 情绪 1/3/5（与 comment_score 不一致，告警判定不用）
   - language / country：小写 ISO
   - ID 字段统一用 unified_edition_id

CLI（自带 smoke test）
======================
    python scripts/store_score_query.py --self_test --game_id_steam <e..> --game_id_mobile <u..>
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_QUERY_PATH = "/api/v1/opinion_pc/global/query"
# 优先使用 woa 内网域名（响应稳定、不走 EdgeOne），其他作为 fallback。
_FALLBACK_HOSTS = (
    "https://databrain.intlgame.com",
    "https://databrain.woa.com",
    "https://databrain-global.intlgame.com",
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_GAME_ID_RE = re.compile(r"^[ue][0-9a-f]+$")

# feeds 表 channel_name 与对外 channel 名称的映射
CHANNEL_TO_FEEDS_NAME = {
    "steam": "steam",
    "google_play": "google play",
    "app_store": "app store",
}

# 商店评分表
STORE_TABLE = {
    "google_play": "tencent-databrain-prod.opinion.store_score_google_play_daily",
    "app_store": "tencent-databrain-prod.opinion.store_score_app_store_daily",
}
STEAM_TABLE = "tencent-databrain-prod.opinion.store_score_steam"
FEEDS_TABLE = "tencent-databrain-prod.opinion.feeds"

_resolved_host: Optional[str] = None


class RateLimitedError(RuntimeError):
    """网关限流（HTTP 566 / 200+empty body）已重试耗尽。"""


# ---------------------------------------------------------------------------
# Env / config
# ---------------------------------------------------------------------------
def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
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


def get_config() -> tuple[str, list[str]]:
    """从环境变量读取 token + 候选 host 列表（解析过的优先）。"""
    global _resolved_host
    _load_dotenv()
    token = os.environ.get("DATABRAIN_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DATABRAIN_TOKEN 未设置")
    explicit = os.environ.get("DATABRAIN_HOST", "").strip().rstrip("/")
    if explicit:
        if not _is_trusted_host(explicit):
            raise RuntimeError(f"DATABRAIN_HOST '{explicit}' 不在受信任域名列表")
        return token, [explicit]
    if _resolved_host:
        return token, [_resolved_host]
    return token, list(_FALLBACK_HOSTS)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_game_id(game_id: str) -> str:
    if not _GAME_ID_RE.match(game_id):
        raise ValueError(f"Invalid game_id: {game_id!r} (need ^[ue][0-9a-f]+$)")
    return game_id


# ---------------------------------------------------------------------------
# HTTP 查询（带 fallback + 限流重试）
# ---------------------------------------------------------------------------
def _run_query(host: str, token: str, sql: str, timeout: float = 60) -> list[dict]:
    # API 网关对多行 SQL 解析异常（实测：带 \n 的 SQL → HTTP 200 body_size=0），
    # 统一压成单行后再发送。
    sql_oneline = " ".join(sql.split())
    resp = httpx.post(
        f"{host}{_QUERY_PATH}",
        json={"sql": sql_oneline},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=timeout,
    )
    if resp.status_code == 566:
        raise RuntimeError(f"HTTP 566 (rate limited) on {host}")
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    text = resp.text
    # [Why] 实测网关偶发返回 200 + 完全空 body（连 CSV header 都没有），是限流/反爬的另一种表现。
    # 真正"无数据"的查询至少返回 header 行，故空 body 视为限流并触发重试。
    if not text:
        raise RuntimeError(f"HTTP 200 but empty body on {host} (suspected rate-limit / gateway issue)")
    if "Access Denied" in text[:1000]:
        raise RuntimeError(f"Access denied: {text[:200]}")
    return list(csv.DictReader(io.StringIO(text)))


# 模块级请求间隔节流
# [Why] 实测 1.5s 间隔仍频繁触发 HTTP 566 / 200+empty 限流；3s 间隔可显著降低限流概率
#       但代价是单游戏完整评估约 30~60s。可通过环境变量调小（自担风险）。
_MIN_REQ_INTERVAL = float(os.environ.get("OPINION_ALERT_QUERY_INTERVAL", "3.0"))
_last_req_at: float = 0.0


def _throttle() -> None:
    global _last_req_at
    elapsed = time.time() - _last_req_at
    if elapsed < _MIN_REQ_INTERVAL:
        time.sleep(_MIN_REQ_INTERVAL - elapsed)
    _last_req_at = time.time()


def query(sql: str, *, retry_on_rate_limit: int = 3,
          retry_sleeps: tuple[float, ...] = (5.0, 20.0, 60.0)) -> list[dict]:
    """
    执行 SQL（带 host fallback + 限流退避重试 + 全局节流）。

    [Why] HTTP 566 网关限流是高频问题（一次评估约 10+ SQL 容易触发）；
          采用三段退避（5s/20s/60s）+ 1.5s 全局间隔，可在不让脚本太慢的前提下尽量稳跑。
    """
    global _resolved_host
    token, hosts = get_config()
    last_err: str = ""
    for attempt in range(retry_on_rate_limit + 1):
        rate_limited = False
        for host in hosts:
            _throttle()
            try:
                rows = _run_query(host, token, sql)
                _resolved_host = host
                return rows
            except RuntimeError as e:
                last_err = str(e)
                # 566 与 "200+空 body" 都视为限流类异常，走退避重试
                if "566" in last_err or "empty body" in last_err:
                    rate_limited = True
                    continue
                print(f"[fallback] {host} failed: {last_err}", file=sys.stderr)
        if attempt >= retry_on_rate_limit:
            break
        sleep_s = retry_sleeps[min(attempt, len(retry_sleeps) - 1)] if rate_limited else 2.0
        print(f"[rate-limit] 全部 host 限流（attempt {attempt + 1}），sleep {sleep_s}s 后重试",
              file=sys.stderr)
        time.sleep(sleep_s)
    if rate_limited:
        raise RateLimitedError(f"网关限流，已重试 {retry_on_rate_limit + 1} 次仍失败：{last_err}")
    raise RuntimeError(f"All hosts failed. Last: {last_err}")


# ---------------------------------------------------------------------------
# JSON 解析
# ---------------------------------------------------------------------------
def parse_language_reviews(raw: Optional[str]) -> dict[str, dict]:
    """
    解析 store_score_steam.language_reviews JSON。
    返回 {<Language>: {"name": str, "reviews": int, "score": float}}。
    解析失败或空 → 返回 {}。
    """
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    out: dict[str, dict] = {}
    for lang, info in (data or {}).items():
        if not isinstance(info, dict):
            continue
        try:
            out[lang] = {
                "name": str(info.get("name", "")),
                "reviews": int(info.get("reviews") or 0),
                "score": float(info.get("score") or 0.0),
            }
        except (TypeError, ValueError):
            continue
    return out


def parse_count_by_rating(raw: Optional[str]) -> dict[int, int]:
    """
    解析 store_score_*_daily.count_by_rating JSON。
    返回 {1: count, 2: count, ..., 5: count}（缺位补 0）。
    """
    out = {i: 0 for i in range(1, 6)}
    if not raw:
        return out
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return out
    for k, v in (data or {}).items():
        try:
            star = int(k)
            if 1 <= star <= 5:
                out[star] = int(round(float(v or 0)))
        except (TypeError, ValueError):
            continue
    return out


def one_star_rate(count_by_rating: dict[int, int]) -> float:
    """1 星占比 = count[1] / sum(1..5)。无样本返回 0。"""
    total = sum(count_by_rating.values())
    return (count_by_rating.get(1, 0) / total) if total > 0 else 0.0


def weighted_score(count_by_rating: dict[int, int]) -> float:
    """按 1~5 星加权计算评分。无样本返回 0。"""
    total = sum(count_by_rating.values())
    if total <= 0:
        return 0.0
    s = sum(star * cnt for star, cnt in count_by_rating.items())
    return s / total


# ---------------------------------------------------------------------------
# Steam 查询
# ---------------------------------------------------------------------------
def query_steam_snapshot(
    edition_id: str, *, at: Optional[datetime] = None,
    lookback_days: int = 2,
) -> Optional[dict]:
    """
    取指定时刻最近的一条 store_score_steam 快照（at=None 取最新）。
    返回 None 表示窗口内无快照。

    [Why] store_score_steam 表 1.5 亿行，不加日期过滤会全表扫描触发网关风控（200+empty body）。
          强制加 DATE(create_time) BETWEEN ... 让查询走分区裁剪，限流概率降为零。
          lookback_days 默认 2 天足够覆盖每 ~10 分钟一次的快照频率。
    """
    validate_game_id(edition_id)
    if at is None:
        at = datetime.now(timezone.utc)
    at_utc = at.astimezone(timezone.utc)
    end_date = at_utc.date().isoformat()
    start_date = (at_utc - timedelta(days=lookback_days)).date().isoformat()
    end_ts = at_utc.strftime("%Y-%m-%d %H:%M:%S")

    sql = f"""
SELECT
  all_reviews_score, recent_reviews_score,
  all_reviews_count, recent_reviews_count,
  language_reviews, create_time
FROM `{STEAM_TABLE}`
WHERE edition_id = '{edition_id}'
  AND DATE(create_time) BETWEEN '{start_date}' AND '{end_date}'
  AND create_time <= '{end_ts}'
ORDER BY create_time DESC
LIMIT 1
""".strip()

    rows = query(sql)
    if not rows:
        return None
    r = rows[0]
    return {
        "all_reviews_score": _to_float(r.get("all_reviews_score")),
        "recent_reviews_score": _to_float(r.get("recent_reviews_score")),
        "all_reviews_count": _to_int(r.get("all_reviews_count")),
        "recent_reviews_count": _to_int(r.get("recent_reviews_count")),
        "language_reviews": parse_language_reviews(r.get("language_reviews")),
        "create_time": _parse_ts(r.get("create_time")),
    }


def query_steam_history_daily(edition_id: str, days: int) -> list[dict]:
    """
    取近 N 天 Steam 每日 23:59 前最新一条快照（用于 baseline 计算）。
    返回 [{"date": "YYYY-MM-DD", "all_reviews_score": ..., "recent_reviews_score": ...}]。
    """
    validate_game_id(edition_id)
    sql = f"""
WITH ranked AS (
  SELECT
    DATE(create_time) AS d,
    all_reviews_score, recent_reviews_score,
    all_reviews_count, recent_reviews_count,
    create_time,
    ROW_NUMBER() OVER (PARTITION BY DATE(create_time) ORDER BY create_time DESC) AS rn
  FROM `{STEAM_TABLE}`
  WHERE edition_id = '{edition_id}'
    AND DATE(create_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)
)
SELECT d, all_reviews_score, recent_reviews_score,
       all_reviews_count, recent_reviews_count
FROM ranked
WHERE rn = 1
ORDER BY d
""".strip()

    rows = query(sql)
    out = []
    for r in rows:
        out.append({
            "date": r.get("d", ""),
            "all_reviews_score": _to_float(r.get("all_reviews_score")),
            "recent_reviews_score": _to_float(r.get("recent_reviews_score")),
            "all_reviews_count": _to_int(r.get("all_reviews_count")),
            "recent_reviews_count": _to_int(r.get("recent_reviews_count")),
        })
    return out


# ---------------------------------------------------------------------------
# GP / App Store 查询
# ---------------------------------------------------------------------------
def query_store_current(channel: str, unified_id: str) -> dict:
    """
    取 GP/App Store 最新一日的 area 分布。
    返回 {"date": "YYYY-MM-DD", "by_area": {area: {"store_score": ..., "comments_number": ...,
                                                  "count_by_rating": {1: ..., 5: ...}}}}
    """
    if channel not in STORE_TABLE:
        raise ValueError(f"channel must be google_play / app_store, got {channel!r}")
    validate_game_id(unified_id)
    table = STORE_TABLE[channel]

    # 最新日期
    sql_latest = f"""
SELECT DATE(MAX(date)) AS max_d
FROM `{table}`
WHERE unified_id = '{unified_id}'
""".strip()
    latest_rows = query(sql_latest)
    if not latest_rows or not latest_rows[0].get("max_d"):
        return {"date": "", "by_area": {}}
    max_d = latest_rows[0]["max_d"]

    sql = f"""
SELECT area, store_score, comments_number, count_by_rating
FROM `{table}`
WHERE unified_id = '{unified_id}'
  AND DATE(date) = '{max_d}'
""".strip()
    rows = query(sql)
    by_area = {}
    for r in rows:
        by_area[r.get("area", "")] = {
            "store_score": _to_float(r.get("store_score")),
            "comments_number": _to_int(r.get("comments_number")),
            "count_by_rating": parse_count_by_rating(r.get("count_by_rating")),
        }
    return {"date": max_d, "by_area": by_area}


def query_store_history(channel: str, unified_id: str, days: int) -> list[dict]:
    """
    取 GP/AS 近 N 天每日全球加权平均评分时序（用于 baseline）。
    全球聚合 = 所有 area 按 comments_number 加权平均。
    返回 [{"date": "YYYY-MM-DD", "global_score": float, "comments_total": int}]
    """
    if channel not in STORE_TABLE:
        raise ValueError(f"channel must be google_play / app_store, got {channel!r}")
    validate_game_id(unified_id)
    table = STORE_TABLE[channel]

    sql = f"""
SELECT
  DATE(date) AS d,
  ROUND(SAFE_DIVIDE(
    SUM(store_score * CAST(comments_number AS FLOAT64)),
    SUM(CAST(comments_number AS FLOAT64))
  ), 4) AS global_score,
  SUM(CAST(comments_number AS INT64)) AS comments_total
FROM `{table}`
WHERE unified_id = '{unified_id}'
  AND DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL {int(days)} DAY)
GROUP BY d
ORDER BY d
""".strip()
    rows = query(sql)
    out = []
    for r in rows:
        out.append({
            "date": r.get("d", ""),
            "global_score": _to_float(r.get("global_score")),
            "comments_total": _to_int(r.get("comments_total")),
        })
    return out


# ---------------------------------------------------------------------------
# Feeds 实时窗口（用于 GP/AS 短时下跌、样本量）
# ---------------------------------------------------------------------------
def query_feeds_window(
    channel: str,
    unified_edition_id: str,
    start_dt: datetime,
    end_dt: datetime,
    *,
    by: str = "none",  # 'none' | 'country' | 'language'
) -> dict:
    """
    取窗口 [start_dt, end_dt] 内的新增评论统计。

    返回：
      {
        "global": {"avg_score": float|None, "sample": int, "one_star_rate": float},
        "by_<dim>": {<key>: {"avg_score":..., "sample":..., "one_star_rate":...}}
      }

    [Why] GP/AS 的 store_score_*_daily 是日级累计，无法做 6h/24h 短时下跌；
          故用 feeds 实时评论流（comment_score 1-5 星）算窗口内的"新增评论平均评分"
          及 1 星占比。Steam 的 6h/24h 下跌从 store_score_steam 历史快照取，
          但样本量门槛仍可以用此函数算"窗口内新增评论数"。
    """
    feeds_channel = CHANNEL_TO_FEEDS_NAME.get(channel)
    if not feeds_channel:
        raise ValueError(f"unsupported channel: {channel!r}")
    validate_game_id(unified_edition_id)

    start_s = start_dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    end_s = end_dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # comment_score=0 / NULL 表示无评分内容（如 Twitter 帖），排除
    base_where = f"""
WHERE unified_edition_id = '{unified_edition_id}'
  AND channel_name = '{feeds_channel}'
  AND comment_time >= '{start_s}'
  AND comment_time <= '{end_s}'
  AND comment_score > 0
""".strip()

    select_metrics = """
  AVG(CAST(comment_score AS FLOAT64)) AS avg_score,
  COUNT(*) AS sample,
  COUNTIF(comment_score = 1) AS one_star,
  COUNTIF(comment_score = 5) AS five_star
""".rstrip()

    out: dict = {"global": {"avg_score": None, "sample": 0, "one_star_rate": 0.0,
                            "five_star_rate": 0.0}}

    # 全局
    sql_g = f"SELECT {select_metrics}\nFROM `{FEEDS_TABLE}`\n{base_where}"
    rows = query(sql_g)
    if rows:
        r = rows[0]
        sample = _to_int(r.get("sample"))
        one = _to_int(r.get("one_star"))
        five = _to_int(r.get("five_star"))
        out["global"] = {
            "avg_score": _to_float_opt(r.get("avg_score")),
            "sample": sample,
            "one_star_rate": (one / sample) if sample > 0 else 0.0,
            "five_star_rate": (five / sample) if sample > 0 else 0.0,
        }

    if by == "none":
        return out

    dim = "language" if by == "language" else "country"
    sql_d = f"""
SELECT {dim} AS k, {select_metrics}
FROM `{FEEDS_TABLE}`
{base_where}
GROUP BY k
HAVING COUNT(*) > 0
""".strip()
    rows_d = query(sql_d)
    out[f"by_{dim}"] = {}
    for r in rows_d:
        key = r.get("k") or ""
        sample = _to_int(r.get("sample"))
        one = _to_int(r.get("one_star"))
        five = _to_int(r.get("five_star"))
        if not key:
            continue
        out[f"by_{dim}"][key] = {
            "avg_score": _to_float_opt(r.get("avg_score")),
            "sample": sample,
            "one_star_rate": (one / sample) if sample > 0 else 0.0,
            "five_star_rate": (five / sample) if sample > 0 else 0.0,
        }
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_float(v: Any) -> float:
    try:
        x = float(v)
        # store_score_steam 用 -1 表示无数据
        return x if x >= 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def _to_float_opt(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v: Any) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def _parse_ts(s: Any) -> Optional[datetime]:
    if not s:
        return None
    s = str(s).replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Self test
# ---------------------------------------------------------------------------
def _self_test(edition_id: str, mobile_id: str) -> int:
    """
    Smoke test 分两类：
      A. 解析单测 (T1~T3)：纯本地，必须通过
      B. 集成测试 (T4~T10)：依赖网关，遇限流标记 SKIP 不算 FAIL
    """
    failures: list[str] = []
    skipped: list[str] = []
    print(f"[self_test] steam edition_id={edition_id} mobile unified_id={mobile_id}\n")
    print("=== A. 解析单测（必跑）===")

    raw_lr = ('{"English":{"name":"Very Positive","reviews":25116,"score":0.87},'
              '"Japanese":{"name":"Mixed","reviews":300,"score":0.5}}')
    lr = parse_language_reviews(raw_lr)
    if lr.get("English", {}).get("score") == 0.87 and lr.get("Japanese", {}).get("reviews") == 300:
        print("  ✅ T1 parse_language_reviews")
    else:
        print(f"  ❌ T1 parse_language_reviews: {lr}")
        failures.append("T1")

    raw_cr = '{"1":648,"2":0,"3":0,"4":162,"5":0}'
    cr = parse_count_by_rating(raw_cr)
    if cr == {1: 648, 2: 0, 3: 0, 4: 162, 5: 0}:
        print("  ✅ T2 parse_count_by_rating")
    else:
        print(f"  ❌ T2: {cr}")
        failures.append("T2")

    if abs(one_star_rate(cr) - 0.8) < 0.01:
        print("  ✅ T3 one_star_rate")
    else:
        print(f"  ❌ T3: {one_star_rate(cr)}")
        failures.append("T3")

    print("\n=== B. 集成测试（遇限流跳过）===")

    def _run(name: str, fn) -> None:
        try:
            ret = fn()
            print(f"  ✅ {name}: {ret}")
        except RateLimitedError as e:
            print(f"  ⏭ {name} SKIP (rate limited): {e}")
            skipped.append(name)
        except Exception as e:
            print(f"  ❌ {name} ERROR: {type(e).__name__}: {e}")
            failures.append(name)

    def _t4():
        snap = query_steam_snapshot(edition_id)
        assert snap and snap["all_reviews_score"] > 0, f"got {snap}"
        return (f"score={snap['all_reviews_score']}, count={snap['all_reviews_count']}, "
                f"lang_count={len(snap['language_reviews'])}")

    def _t5():
        snap = query_steam_snapshot(edition_id, at=datetime.now(timezone.utc) - timedelta(hours=6))
        return f"score_6h_ago={(snap or {}).get('all_reviews_score')}"

    def _t6():
        hist = query_steam_history_daily(edition_id, 30)
        assert len(hist) > 0, "empty"
        return f"{len(hist)} 天"

    def _t7():
        gp = query_store_current("google_play", mobile_id)
        assert gp.get("date") and len(gp.get("by_area", {})) > 0, f"got {gp}"
        sample_area = next(iter(gp["by_area"].keys()))
        sample = gp["by_area"][sample_area]
        return (f"date={gp['date']}, areas={len(gp['by_area'])}, sample={sample_area}:"
                f" score={sample['store_score']}, "
                f"1star={one_star_rate(sample['count_by_rating']):.2%}")

    def _t8():
        gp_hist = query_store_history("google_play", mobile_id, 30)
        assert len(gp_hist) > 0
        return f"{len(gp_hist)} 天，最新 global_score={gp_hist[-1]['global_score']}"

    def _t9():
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=7)
        f = query_feeds_window("steam", edition_id, start_dt, end_dt, by="none")
        return f"sample={f['global']['sample']}"

    def _t10():
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=7)
        f = query_feeds_window("google_play", mobile_id, start_dt, end_dt, by="country")
        return (f"sample={f['global']['sample']}, "
                f"countries={len(f.get('by_country', {}))}")

    _run("T4 query_steam_snapshot", _t4)
    _run("T5 query_steam_snapshot(at=6h_ago)", _t5)
    _run("T6 query_steam_history_daily", _t6)
    _run("T7 query_store_current(GP)", _t7)
    _run("T8 query_store_history(GP)", _t8)
    _run("T9 query_feeds_window(steam,7d)", _t9)
    _run("T10 query_feeds_window(GP,7d,by_country)", _t10)

    print(f"\n{'-' * 40}")
    print(f"PASS={10 - len(failures) - len(skipped)} / FAIL={len(failures)} / SKIP={len(skipped)}")
    if failures:
        print(f"FAIL: {failures}")
        return 1
    if skipped:
        print(f"SKIP（网关限流，稍后单独验证）: {skipped}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="store_score_query — 取数 + JSON 解析模块")
    parser.add_argument("--self_test", action="store_true")
    parser.add_argument("--game_id_steam", default="e7f672beaa5fddd166df98bc046ba4bd4",
                        help="Steam 测试用 edition_id（默认 POE2）")
    parser.add_argument("--game_id_mobile", default="ufc454d9b1af70b40588e2a6fa4da4a8b",
                        help="移动端测试用 unified_id（默认 PUBGM）")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test(args.game_id_steam, args.game_id_mobile))
    parser.print_help()


if __name__ == "__main__":
    main()
