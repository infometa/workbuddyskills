#!/usr/bin/env python3
"""
query_executor.py — 通用 SQL 执行器（移植自 databrain-opinion-metrics，兼容 Python 3.9+）。

为什么独立一份：
  - opinion-metrics 用 Python 3.10+ 的 `str | None` 注解，本 skill 锁 3.9 兼容
  - 复用同一套 EdgeOne 关键字黑名单、空 body 检测、host fallback 行为

用法（CLI）：
    python scripts/query_executor.py \\
        --sql "SELECT ... FROM ..." \\
        --game_id ufc454d9b1af70b40588e2a6fa4da4a8b
    python scripts/query_executor.py --self_test

用法（库）：
    from query_executor import query
    rows = query(sql)   # rows: list[dict[str, str]]，CSV 解析后的原始行

EdgeOne 限制（必读）：
    SQL 含以下关键字会被 HTTP 566 拦截：IF / IFNULL / COALESCE / CASE WHEN / OR 1=1
    替换：
      IF(x<0,0,x)            → GREATEST(x, 0)
      COUNT(CASE WHEN c THEN col END) → COUNTIF(c)
      IFNULL(col, 0)          → 在 Python 端做 None 处理
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
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

_QUERY_API = "/api/v1/opinion_pc/global/query"

# 优先使用 woa 内网域名（响应稳定、不走 EdgeOne），其他作为 fallback。
_FALLBACK_HOSTS = (
    "https://databrain.woa.com",
    "https://databrain.intlgame.com",
    "https://databrain-global.intlgame.com",
)

_resolved_host: Optional[str] = None

_GAME_ID_RE = re.compile(r"^[ue][0-9a-f]+$")
_FORBIDDEN_SQL_RE = re.compile(
    r"\b(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER|TRUNCATE|MERGE|REPLACE|CALL|EXEC)\b",
    re.IGNORECASE,
)
_PLACEHOLDER_RE = re.compile(r"<(game_id|start_date|end_date|hours|top_n|threshold|[a-z_]+)>")


class RateLimitedError(RuntimeError):
    """HTTP 566 / 200 + empty body，需要外层做退避重试。"""


# ---------------------------------------------------------------------------
# Env
# ---------------------------------------------------------------------------
def _load_dotenv() -> None:
    """Load .env from skill root（本地开发用；生产由服务端注入环境变量）."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.is_file():
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
    if hostname.startswith("databrain-") and hostname.endswith(".intlgame.com"):
        return True
    return False


def get_config():
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


def validate_sql(sql: str) -> str:
    placeholder = _PLACEHOLDER_RE.search(sql)
    if placeholder:
        raise ValueError(f"SQL 含未替换占位符: {placeholder.group()!r}")
    match = _FORBIDDEN_SQL_RE.search(sql)
    if match:
        raise ValueError(f"SQL 含禁止关键字: {match.group()!r}（仅允许 SELECT）")
    return sql


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
_MIN_REQ_INTERVAL = float(os.environ.get("HOTPOSTS_QUERY_INTERVAL", "3.0"))
_last_req_at: float = 0.0


def _throttle() -> None:
    global _last_req_at
    elapsed = time.time() - _last_req_at
    if elapsed < _MIN_REQ_INTERVAL:
        time.sleep(_MIN_REQ_INTERVAL - elapsed)
    _last_req_at = time.time()


def _run_query(host: str, token: str, sql: str, timeout: float = 60.0) -> list:
    # API 网关对多行 SQL 解析异常（实测：带 \n 的 SQL → HTTP 200 但 body_size=0；
    # 同一 SQL 压成单行后正常返回 CSV）。这里统一 normalize：换行 → 空格、合并多空格。
    sql_oneline = " ".join(sql.split())
    resp = httpx.post(
        host + _QUERY_API,
        json={"sql": sql_oneline},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=timeout,
    )
    if resp.status_code == 566:
        raise RateLimitedError(f"HTTP 566 (rate limited) on {host}")
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    text = resp.text
    if not text:
        # SQL 字段不存在 / 表无权限 / 网关静默拦截，三种都返回 200 + empty body。
        # 当作可重试错误抛出，由调用方决定退避还是放弃。
        raise RateLimitedError(
            f"HTTP 200 但 body 为空 on {host}（SQL 字段不存在 / 表无权限 / 限流）"
        )
    if "Access Denied" in text[:1000]:
        raise RuntimeError(f"Access denied: {text[:200]}")
    # 部分错误返回 JSON 体而非 CSV
    if text.strip().startswith("{"):
        try:
            j = json.loads(text)
            if j.get("code", 0) != 0:
                raise RuntimeError(f"API code={j.get('code')}: {j.get('msg', '')[:200]}")
        except json.JSONDecodeError:
            pass
    return list(csv.DictReader(io.StringIO(text)))


def query(
    sql: str,
    *,
    retry_on_rate_limit: int = 3,
    retry_sleeps: tuple = (5.0, 20.0, 60.0),
) -> list:
    """
    执行 SELECT，含 host fallback + 限流退避 + 全局节流。
    抛出 RateLimitedError / RuntimeError / ValueError。
    """
    validate_sql(sql)
    global _resolved_host
    token, hosts = get_config()
    last_err = ""
    for attempt in range(retry_on_rate_limit + 1):
        rate_limited = False
        for host in hosts:
            _throttle()
            try:
                rows = _run_query(host, token, sql)
                _resolved_host = host
                return rows
            except RateLimitedError as e:
                last_err = str(e)
                rate_limited = True
                continue
            except RuntimeError as e:
                last_err = str(e)
                print(f"[fallback] {host} failed: {last_err}", file=sys.stderr)
        if attempt >= retry_on_rate_limit:
            break
        sleep_s = retry_sleeps[min(attempt, len(retry_sleeps) - 1)]
        print(f"[rate-limit] 全部 host 限流（attempt {attempt + 1}），sleep {sleep_s}s 后重试",
              file=sys.stderr)
        time.sleep(sleep_s)
    if rate_limited:
        raise RateLimitedError(f"网关限流，已重试 {retry_on_rate_limit + 1} 次仍失败：{last_err}")
    raise RuntimeError(f"All hosts failed. Last: {last_err}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="通用 SQL 执行器（移植自 metrics，3.9 兼容）")
    parser.add_argument("--sql", help="完整 SQL")
    parser.add_argument("--sql_file", help="SQL 文件路径")
    parser.add_argument("--game_id", help="可选；会做 game_id 校验")
    parser.add_argument("--self_test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    if not args.sql and not args.sql_file:
        parser.error("--sql 或 --sql_file 必须传一个")
    sql = args.sql or Path(args.sql_file).read_text(encoding="utf-8")
    if args.game_id:
        validate_game_id(args.game_id)

    try:
        rows = query(sql)
    except (RateLimitedError, RuntimeError, ValueError) as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2 if isinstance(e, RateLimitedError) else 1)

    print(json.dumps({"row_count": len(rows), "rows": rows}, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Self test
# ---------------------------------------------------------------------------
def _self_test() -> int:
    fails = []

    def _check(name, ok, detail=""):
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {detail}")
            fails.append(name)

    print("=== query_executor self test ===")

    # validate_game_id
    _check("validate_game_id 接受合法", validate_game_id("ufc4abcd") == "ufc4abcd")
    for bad in ("xyz", "u", "u1' OR 1=1", "uABC"):
        try:
            validate_game_id(bad)
            _check(f"validate_game_id 拒绝 {bad!r}", False)
        except ValueError:
            _check(f"validate_game_id 拒绝 {bad!r}", True)

    # validate_sql 占位符
    try:
        validate_sql("SELECT 1 WHERE id = '<game_id>'")
        _check("validate_sql 拦截 <game_id>", False)
    except ValueError:
        _check("validate_sql 拦截 <game_id>", True)

    # validate_sql 禁止关键字
    for bad in ("SELECT 1; DROP TABLE x", "INSERT INTO ...", "select 1 from x where col = 'a' OR 1=1; DELETE"):
        try:
            validate_sql(bad)
            _check(f"validate_sql 拦截 {bad[:30]}", False)
        except ValueError:
            _check(f"validate_sql 拦截 {bad[:30]}", True)

    # validate_sql 通过合法
    try:
        validate_sql("SELECT a, b FROM `proj.dataset.tbl` WHERE x = 'y'")
        _check("validate_sql 接受合法 SELECT", True)
    except Exception as e:
        _check("validate_sql 接受合法 SELECT", False, str(e))

    # _is_trusted_host
    _check("_is_trusted_host 接受 global", _is_trusted_host("https://databrain-global.intlgame.com"))
    _check("_is_trusted_host 拒绝 evil", not _is_trusted_host("https://evil.intlgame.com.evil/"))

    print("\n" + "-" * 40)
    print(f"FAIL: {len(fails)}" if fails else f"PASS: {len(fails) == 0}")
    return 1 if fails else 0


if __name__ == "__main__":
    main()
