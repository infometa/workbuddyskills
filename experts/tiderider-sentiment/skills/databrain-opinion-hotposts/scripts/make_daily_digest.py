#!/usr/bin/env python3
"""
make_daily_digest.py — 每日热帖「取数」入口（脚本层只做确定性取数）。

架构（见 SKILL.md）：
  脚本取数(本文件 --json)
      → agent 填 digest_spec.json（去重/AI摘要/话题/选帖）
      → validate_digest.py 校验
      → render_digest.py 渲染 html/markdown
      → 原样展示

本文件职责（只做"算得出的"）：
  1. 读 platforms.yaml（可被 game_id override 深合并）
  2. 解析 game_id（用户没传时按 game_name 自动查）
  3. 对每个启用平台执行 SQL（尊重最低互动量门槛），取 top_n × 3 候选
  4. 拉整体情感分布（供顶部概况）
  5. 输出候选 JSON（不做去重 / 不做渲染 / 不生成摘要——这些是 agent 的活）

CLI 示例：
  # 取数：输出候选 JSON（agent 接着按 SKILL.md 填 digest_spec）
  python scripts/make_daily_digest.py --game_name "PUBG Mobile"

  # 显式 game_id（跳过自动查询，更快）
  python scripts/make_daily_digest.py \
      --game_id ufc454d9b1af70b40588e2a6fa4da4a8b --game_name "PUBG Mobile"

  # 指定平台 + Top 3 + 写文件
  python scripts/make_daily_digest.py --game_name "PUBG Mobile" \
      --platforms reddit,x,youtube --top_n 3 --out_file /tmp/candidates.json

数据源（feeds 表已实测字段）：
  - 元信息：unified_edition_id, channel_name, comment_time, comment_parent_id, language, country
  - 互动量：tweets_like, tweets_reply, tweets_retweet, follower_number
  - 情感：sentiment_rating (1-2 负, 3 中, 4-5 正)
  - 文本：content（正文）, content_url（单帖永久链接）, reviewer（用户名）
"""
from __future__ import annotations

import argparse
import copy
import datetime as _dt
import json
import os
import sys
import unicodedata
from pathlib import Path
from typing import Optional

import yaml

_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from query_executor import query, RateLimitedError, validate_game_id  # noqa: E402
from game_search import resolve_first_game_id  # noqa: E402

_FEEDS_TABLE = "`tencent-databrain-prod.opinion.feeds`"


def _tz_offset_hours() -> int:
    """feeds.comment_time 相对 UTC 的时区偏移（小时）。

    实测：feeds 入库把 UTC+8 墙钟数字直接写进 comment_time（却被标记成 +00），
    即 comment_time 实为 **UTC+8**。本偏移同时用于：
      - 生成 digest_time（utcnow + offset，与 comment_time 同时区，渲染器才能 naive 比对）
      - SQL 时间窗锚点（把 CURRENT_TIMESTAMP() 推到同一 +offset 标签空间）
    默认 8；可用 env DIGEST_TZ_OFFSET_HOURS 覆盖；非法/越界回落 8。"""
    try:
        off = int(os.environ.get("DIGEST_TZ_OFFSET_HOURS", "8"))
    except (ValueError, TypeError):
        return 8
    return off if -14 <= off <= 14 else 8


def _recent_window_clause(hours: int) -> str:
    """构造「过去 hours 小时」时间窗。

    comment_time 是 +offset 墙钟（标 +00），CURRENT_TIMESTAMP() 是真 UTC，
    故把 now 推到同一 +offset 标签空间再卡窗，得到真正的 hours 窗口（含上界，
    顺带剔除时钟漂移导致的“未来”行）。"""
    off = _tz_offset_hours()
    anchor = f"TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL {off} HOUR)"
    return (
        f"comment_time >= TIMESTAMP_SUB({anchor}, INTERVAL {int(hours)} HOUR)\n"
        f"  AND comment_time <= {anchor}"
    )


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_platforms(yaml_path: Optional[str] = None, game_id: Optional[str] = None) -> dict:
    if yaml_path:
        path = Path(yaml_path)
    else:
        path = _SCRIPTS_DIR.parent / "platforms.yaml"
    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if game_id and config.get("overrides", {}).get(game_id):
        config = _deep_merge(config, config["overrides"][game_id])
    return config


# ---------------------------------------------------------------------------
# SQL 拼装
# ---------------------------------------------------------------------------
def _build_top_sql(
    game_id: str,
    channel_name: str,
    *,
    hours: int,
    min_engagement: int,
    candidate_limit: int,
) -> str:
    """
    单平台 Top 候选 SQL。
    - 仅取主帖（comment_parent_id = '-1'），过滤回复
    - 互动量 = like + reply + retweet（GREATEST 清洗负值，规避 IF / IFNULL EdgeOne 拦截）
    - candidate_limit = top_n * 3，便于 agent 去重后补位
    """
    validate_game_id(game_id)
    if not channel_name.replace("_", "").replace(" ", "").isalnum():
        raise ValueError(f"channel_name 含非法字符: {channel_name!r}")
    if not (1 <= int(hours) <= 168):
        raise ValueError(f"hours 越界: {hours}（仅允许 1-168）")
    if not (0 <= int(min_engagement) <= 1_000_000):
        raise ValueError(f"min_engagement 越界: {min_engagement}")
    if not (1 <= int(candidate_limit) <= 100):
        raise ValueError(f"candidate_limit 越界: {candidate_limit}")

    # EdgeOne 关键字黑名单坑见 references/sql_templates.md。
    return f"""
SELECT
    reviewer,
    comment_time,
    follower_number,
    sentiment_rating,
    content_url,
    language,
    country,
    SUBSTR(content, 0, 400) AS snippet,
    GREATEST(tweets_like, 0)
      + GREATEST(tweets_reply, 0)
      + GREATEST(tweets_retweet, 0)                                  AS engagement
FROM {_FEEDS_TABLE}
WHERE unified_edition_id = '{game_id}'
  AND channel_name = '{channel_name.lower()}'
  AND {_recent_window_clause(hours)}
  AND comment_parent_id = '-1'
  AND (
        GREATEST(tweets_like, 0)
      + GREATEST(tweets_reply, 0)
      + GREATEST(tweets_retweet, 0)
      ) >= {int(min_engagement)}
ORDER BY engagement DESC
LIMIT {int(candidate_limit)}
""".strip()


def _build_sentiment_sql(game_id: str, hours: int) -> str:
    validate_game_id(game_id)
    return f"""
SELECT
    COUNTIF(sentiment_rating IN (4, 5)) AS positive,
    COUNTIF(sentiment_rating = 3)        AS neutral,
    COUNTIF(sentiment_rating IN (1, 2))  AS negative
FROM {_FEEDS_TABLE}
WHERE unified_edition_id = '{game_id}'
  AND {_recent_window_clause(hours)}
  AND comment_parent_id = '-1'
""".strip()


# ---------------------------------------------------------------------------
# 取数 + 归一化
# ---------------------------------------------------------------------------
def _to_int(v, default: int = 0) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _clip_display_width(s: str, max_units: int = 400) -> str:
    """按显示宽度截取：CJK/假名/韩文/全角=2，ASCII=1。

    跨语种归一信息量：400 显示单位 = 中文≈200 字 = 拉丁≈400 字符。
    SQL 已 SUBSTR(content, 0, 400) 拉足原料，这里按宽度收口（SQL 不能用 CASE WHEN
    按语种分支——EdgeOne 黑名单拦截，故归一放 Python）。
    """
    if not s:
        return ""
    out = []
    w = 0
    for ch in s:
        cw = 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
        if w + cw > max_units:
            break
        out.append(ch)
        w += cw
    return "".join(out)


def _sentiment_word(rating: int) -> Optional[str]:
    """sentiment_rating → 单词标签（4-5 正面 / 3 中性 / 1-2 负面 / 其他 None）。"""
    if rating >= 4:
        return "正面"
    if rating == 3:
        return "中性"
    if 1 <= rating <= 2:
        return "负面"
    return None


def _normalize_candidate(row: dict) -> dict:
    """SQL 行 → 候选帖 dict（字段名向 digest_spec 靠拢，方便 agent 直接搬）。"""
    url = (row.get("content_url") or "").strip()
    if not url or url.lower() == "null":
        url = ""

    snippet = (row.get("snippet") or row.get("content") or "").strip()
    # 按显示宽度归一（中文≈200字 / 拉丁≈400字符），保证喂给 agent 摘要/去重的信息量对等
    snippet = _clip_display_width(" ".join(snippet.split()))

    rating = _to_int(row.get("sentiment_rating"), default=-1)
    return {
        "author": (row.get("reviewer") or "").strip(),
        "followers": _to_int(row.get("follower_number")),
        "time": (row.get("comment_time") or "").strip(),
        "engagement": _to_int(row.get("engagement")),
        "sentiment_rating": rating,
        "sentiment": _sentiment_word(rating),
        "url": url,
        "snippet": snippet,
        "title": "",  # feeds 无独立 title；agent 用 snippet 作标题来源，原文不翻译
        "language": (row.get("language") or "").strip(),
        "country": (row.get("country") or "").strip(),
    }


def fetch_platform_candidates(
    game_id: str,
    platform_key: str,
    cfg: dict,
    *,
    hours: int,
    top_n: int,
) -> dict:
    """
    返回单平台候选（不去重、不渲染）：
      {key, display, candidates: [...], candidate_total, skipped, error}
    """
    base_top = cfg.get("default_top_n", top_n)
    n = max(1, min(int(top_n or base_top), 10))
    candidate_limit = n * 3

    try:
        sql = _build_top_sql(
            game_id,
            cfg["channel_name"],
            hours=hours,
            min_engagement=int(cfg.get("min_engagement", 0)),
            candidate_limit=candidate_limit,
        )
        rows = query(sql)
    except RateLimitedError as e:
        return _skip_result(platform_key, cfg, f"rate_limited: {e}")
    except (RuntimeError, ValueError) as e:
        return _skip_result(platform_key, cfg, str(e))

    candidates = [_normalize_candidate(r) for r in rows]
    return {
        "key": platform_key,
        "display": cfg["display"],
        "candidates": candidates,
        "candidate_total": len(candidates),
        "skipped": False,
        "error": None,
    }


def _skip_result(platform_key: str, cfg: dict, err: str) -> dict:
    return {
        "key": platform_key,
        "display": cfg["display"],
        "candidates": [],
        "candidate_total": 0,
        "skipped": True,
        "error": err,
    }


def fetch_overall_sentiment(game_id: str, hours: int) -> dict:
    """整体情感分布 → {pos, neu, neg} 占比（0~1）。失败返回 {}。"""
    try:
        rows = query(_build_sentiment_sql(game_id, hours))
    except (RateLimitedError, RuntimeError, ValueError):
        return {}
    if not rows:
        return {}
    r = rows[0]
    pos = _to_int(r.get("positive"))
    neu = _to_int(r.get("neutral"))
    neg = _to_int(r.get("negative"))
    total = pos + neu + neg
    if total <= 0:
        return {}
    return {
        "pos": round(pos / total, 4),
        "neu": round(neu / total, 4),
        "neg": round(neg / total, 4),
    }


# ---------------------------------------------------------------------------
# 主流程（取数）
# ---------------------------------------------------------------------------
def fetch_candidates(
    *,
    game_id: Optional[str] = None,
    game_name: str,
    platforms: Optional[list] = None,
    top_n: Optional[int] = None,
    hours: Optional[int] = None,
    config_path: Optional[str] = None,
    digest_time: Optional[str] = None,
) -> dict:
    """
    返回候选数据包（供 agent 填 digest_spec）：
      {
        "params": {...},
        "summary_data": {"sentiment": {pos, neu, neg}},
        "platforms": [{key, display, candidates, candidate_total, skipped, error}, ...]
      }
    """
    if not game_id:
        if not game_name:
            raise ValueError("game_id 与 game_name 至少传一个")
        gid, resolved_name = resolve_first_game_id(game_name)
        if not gid:
            raise RuntimeError(
                f"未找到游戏 {game_name!r} 的 game_id；"
                "请检查游戏名拼写，或显式传 --game_id"
            )
        print(f"[game_search] {game_name!r} → game_id={gid} ({resolved_name})", file=sys.stderr)
        game_id = gid
        if resolved_name and not game_name:
            game_name = resolved_name
    validate_game_id(game_id)

    cfg = load_platforms(config_path, game_id=game_id)
    defaults = cfg.get("defaults", {})
    hours = int(defaults.get("hours", 24)) if hours is None else int(hours)
    top_n_default = int(defaults.get("top_n", 5)) if top_n is None else int(top_n)
    if not (1 <= hours <= 168):
        raise ValueError(f"hours 越界: {hours}（应在 1-168）")
    if not (1 <= top_n_default <= 10):
        raise ValueError(f"top_n 越界: {top_n_default}（应在 1-10）")

    enabled_keys = []
    if platforms:
        enabled_keys = [p.strip() for p in platforms if p.strip()]
    else:
        enabled_keys = [k for k, v in cfg["platforms"].items() if v.get("enabled", True)]

    platform_results = []
    for key in enabled_keys:
        if key not in cfg["platforms"]:
            print(f"[WARN] 未知平台 {key!r}，跳过", file=sys.stderr)
            continue
        pr = fetch_platform_candidates(
            game_id, key, cfg["platforms"][key],
            hours=hours, top_n=top_n_default,
        )
        platform_results.append(pr)
        status = "ok" if not pr["skipped"] else f"skipped({pr['error']})"
        print(f"[platform] {key:10s} candidates={pr['candidate_total']}  {status}",
              file=sys.stderr)

    sentiment = fetch_overall_sentiment(game_id, hours)

    # digest_time 与 comment_time 同时区（默认 UTC+8），渲染器才能 naive 比对算「Xh 前」。
    digest_time = digest_time or (
        _dt.datetime.utcnow() + _dt.timedelta(hours=_tz_offset_hours())
    ).strftime("%Y-%m-%d %H:%M")

    return {
        "params": {
            "game_id": game_id,
            "game_name": game_name,
            "hours": hours,
            "top_n": top_n_default,
            "platforms": enabled_keys,
            "digest_time": digest_time,
        },
        "summary_data": {"sentiment": sentiment} if sentiment else {},
        "platforms": platform_results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="每日热帖取数（输出候选 JSON，供 agent 填 digest_spec；参见 SKILL.md）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--game_id",
                        help="unified_edition_id（u/e 前缀 + hex）；缺省时由 --game_name 自动查询")
    parser.add_argument("--game_name", help="游戏名（标题 + game_id 查询关键字）")
    parser.add_argument("--platforms", help="逗号分隔覆盖 yaml enabled（如 reddit,x,youtube）")
    parser.add_argument("--top_n", type=int, help="每榜 Top N（默认 5，1-10）；候选取 top_n×3")
    parser.add_argument("--hours", type=int, help="时间窗（默认 24，1-168）")
    parser.add_argument("--config", help="自定义 platforms.yaml 路径")
    parser.add_argument("--out_file", help="候选 JSON 输出文件路径（默认 stdout）")
    parser.add_argument("--self_test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    if not args.game_name:
        parser.error("--game_name 必传（标题；不传 --game_id 时也用作查询关键字）")

    platforms = args.platforms.split(",") if args.platforms else None

    try:
        result = fetch_candidates(
            game_id=args.game_id,
            game_name=args.game_name,
            platforms=platforms,
            top_n=args.top_n,
            hours=args.hours,
            config_path=args.config,
        )
    except (ValueError, RuntimeError) as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out_file:
        Path(args.out_file).write_text(out, encoding="utf-8")
        print(f"[OK] candidates written to {args.out_file}", file=sys.stderr)
    else:
        print(out)


# ---------------------------------------------------------------------------
# Self test（不联网）
# ---------------------------------------------------------------------------
def _self_test() -> int:
    fails: list[str] = []

    def _check(name, ok, detail=""):
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {detail}")
            fails.append(name)

    print("=== make_daily_digest (fetch) self test ===")

    cfg = load_platforms()
    _check("platforms.yaml 含 9 平台",
           len(cfg["platforms"]) == 9, f"got={list(cfg['platforms'].keys())}")
    _check("platforms.yaml defaults 完整",
           all(k in cfg["defaults"] for k in ["top_n", "hours"]))

    for k, p in cfg["platforms"].items():
        _check(f"platform[{k}] 含 channel_name+display+min_engagement",
               all(x in p for x in ["channel_name", "display", "min_engagement"]))

    cfg2 = _deep_merge(cfg, {"overrides": {"u_test": {"defaults": {"top_n": 3}}}})
    _check("_deep_merge 不丢字段",
           cfg2["defaults"]["hours"] == 24 and cfg2["overrides"]["u_test"]["defaults"]["top_n"] == 3)

    # SQL 拼装
    sql = _build_top_sql("ufc454d9b1af70b40588e2a6fa4da4a8b", "reddit",
                         hours=24, min_engagement=200, candidate_limit=15)
    _check("_build_top_sql 含 unified_edition_id 过滤",
           "unified_edition_id = 'ufc454d9b1af70b40588e2a6fa4da4a8b'" in sql)
    _check("_build_top_sql 含 channel_name 过滤", "channel_name = 'reddit'" in sql)
    _check("_build_top_sql 含 INTERVAL 24 HOUR", "INTERVAL 24 HOUR" in sql)
    _check("_build_top_sql 窗口锚点 +8（comment_time 实为 UTC+8）",
           "TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 8 HOUR)" in sql)
    _check("_build_top_sql 含窗口上界", "comment_time <= TIMESTAMP_ADD" in sql)
    _check("_build_top_sql 含 comment_parent_id 主帖过滤", "comment_parent_id = '-1'" in sql)
    _check("_build_top_sql 含 content_url", "content_url" in sql)
    _check("_build_top_sql 含 snippet", "AS snippet" in sql)
    _check("_build_top_sql 不含 IS NULL OR", "IS NULL OR" not in sql.upper())
    _check("_build_top_sql 不含 IFNULL", "IFNULL" not in sql.upper())
    _check("_build_top_sql 不含 LOWER(channel_name)", "LOWER(channel_name)" not in sql)
    _check("_build_top_sql 含 LIMIT 15", "LIMIT 15" in sql)

    # 注入防御
    for bad_call in (
        lambda: _build_top_sql("u' OR 1=1--", "reddit", hours=24, min_engagement=0, candidate_limit=15),
        lambda: _build_top_sql("ufc4abcd", "reddit'; DROP--", hours=24, min_engagement=0, candidate_limit=15),
        lambda: _build_top_sql("ufc4abcd", "reddit", hours=999, min_engagement=0, candidate_limit=15),
        lambda: _build_top_sql("ufc4abcd", "reddit", hours=24, min_engagement=0, candidate_limit=999),
    ):
        try:
            bad_call()
            _check("_build_top_sql 拒绝非法入参", False)
        except ValueError:
            _check("_build_top_sql 拒绝非法入参", True)

    # _normalize_candidate
    c = _normalize_candidate({})
    _check("_normalize_candidate 空 row → 默认",
           c["followers"] == 0 and c["sentiment_rating"] == -1 and c["url"] == "" and c["sentiment"] is None)
    c2 = _normalize_candidate({
        "reviewer": " u/abc ", "engagement": "1234", "content_url": "https://x",
        "sentiment_rating": "5", "content": "  hello  world  ",
    })
    _check("_normalize_candidate 字段映射",
           c2["author"] == "u/abc" and c2["engagement"] == 1234 and c2["url"] == "https://x"
           and c2["sentiment"] == "正面" and c2["snippet"] == "hello world",
           f"got={c2}")
    c3 = _normalize_candidate({"content_url": "null", "sentiment_rating": "3"})
    _check("_normalize_candidate 'null' url 清空 + 中性",
           c3["url"] == "" and c3["sentiment"] == "中性")

    # _clip_display_width（跨语种归一）
    _check("_clip 纯中文 ~200 字（400 单位）",
           _clip_display_width("中" * 300) == "中" * 200,
           f"len={len(_clip_display_width('中' * 300))}")
    _check("_clip 纯英文 ~400 字符（400 单位）",
           _clip_display_width("a" * 600) == "a" * 400,
           f"len={len(_clip_display_width('a' * 600))}")
    _check("_clip 短串原样", _clip_display_width("hello 世界") == "hello 世界")
    _check("_clip 空串安全", _clip_display_width("") == "")
    _check("_clip 200 中文字内不截", _clip_display_width("中" * 150) == "中" * 150)
    # _normalize_candidate 应用 clip：长中文正文被收口到 200 字
    c_long = _normalize_candidate({"content": "卡" * 500})
    _check("_normalize_candidate 长中文 snippet 归一到 200 字",
           len(c_long["snippet"]) == 200, f"len={len(c_long['snippet'])}")

    # _sentiment_word
    _check("_sentiment_word 5→正面/3→中性/1→负面/-1→None",
           _sentiment_word(5) == "正面" and _sentiment_word(3) == "中性"
           and _sentiment_word(1) == "负面" and _sentiment_word(-1) is None)

    # _to_int
    _check("_to_int 异常 → default", _to_int("abc", default=9) == 9)
    _check("_to_int float 字符串", _to_int("3.7") == 3)

    print("\n" + "-" * 40)
    if fails:
        print(f"FAIL: {len(fails)}")
        return 1
    print("PASS: all make_daily_digest (fetch) tests")
    return 0


if __name__ == "__main__":
    main()
