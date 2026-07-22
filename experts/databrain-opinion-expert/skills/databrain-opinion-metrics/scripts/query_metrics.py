#!/usr/bin/env python3
"""
query_metrics.py — 舆情指标通用 SQL 执行器。

Agent 使用流程：
  1. 读取 references/ 下对应数据表的 SQL 模板文件，找到目标指标
  2. 将 <game_id>、<start_date>、<end_date> 替换为实际值
  3. 调用本脚本执行

用法:
    python scripts/query_metrics.py \\
        --sql        "SELECT ... FROM ... WHERE unified_edition_id = 'e...' ..." \\
        --game_id    e76337e746e1f95fdbf7e23c26010e448 \\
        --start_date 2026-03-24 \\
        --end_date   2026-03-30

    # 也可从文件读取 SQL（适合长查询）：
    python scripts/query_metrics.py \\
        --sql_file   /tmp/my_query.sql \\
        --game_id    e76337e746e1f95fdbf7e23c26010e448 \\
        --date       2026-03-30

    # 传入用户原始问题用于埋点（建议总是传）：
    python scripts/query_metrics.py \\
        --sql "..." --game_id "..." --date "..." \\
        --message "用户原始问题"

输出（stdout，JSON）：
    {
      "game_id":    "e...",
      "start_date": "YYYY-MM-DD",
      "end_date":   "YYYY-MM-DD",
      "rows":       [...],
      "row_count":  N
    }

安全:
    - --game_id 和日期参数经过严格正则校验，防止 SQL 注入
    - SQL 中不得含 DDL/DML 关键词（DROP / DELETE / INSERT / UPDATE / CREATE / ALTER …）
    - Token 仅通过环境变量注入，不接受命令行传入

认证:
    DATABRAIN_TOKEN — 认证 token（不含 Bearer 前缀），由服务端环境变量注入
    DATABRAIN_HOST  — 可选；设置后仅用该 host，否则按优先级自动 fallback
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import threading
from pathlib import Path
from urllib.parse import urlparse

import httpx
from report_log import new_session_msg_pair, report

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
_QUERY_API = "/api/v1/opinion_pc/global/query"

_FALLBACK_HOSTS = (
    "https://databrain.intlgame.com",
    "https://databrain.woa.com",
    "https://databrain-global.intlgame.com",
)

_resolved_host: str | None = None

# Security: strict allow-list patterns for SQL-interpolated values
_DATE_RE    = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_GAME_ID_RE = re.compile(r"^[ue][0-9a-f]+$")

# Forbidden SQL operations (case-insensitive, word-boundary match)
_FORBIDDEN_SQL_RE = re.compile(
    r"\b(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER|TRUNCATE|MERGE|REPLACE|CALL|EXEC)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Env / host helpers
# ---------------------------------------------------------------------------
def _load_dotenv() -> None:
    """Load .env from skill root (local dev only; server env vars take priority)."""
    skill_dir = Path(__file__).parent.parent
    env_path = skill_dir / ".env"
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


def _get_config(
    token: str | None = None,
    host: str | None = None,
) -> tuple[str, list[str]]:
    """Return (token, hosts_to_try).

    If DATABRAIN_HOST is explicitly set, only that host is used.
    Otherwise, try the fallback list in order, caching the first success.
    """
    global _resolved_host
    _load_dotenv()
    token = (token or os.environ.get("DATABRAIN_TOKEN", "")).strip()
    if not token:
        print(
            "[ERROR] DATABRAIN_TOKEN not set. 请由服务端通过环境变量注入，不要写入文件。",
            file=sys.stderr,
        )
        sys.exit(1)

    explicit = (host or os.environ.get("DATABRAIN_HOST", "")).strip().rstrip("/")
    if explicit:
        if not _is_trusted_host(explicit):
            print(
                f"[ERROR] DATABRAIN_HOST '{explicit}' 不在受信任域名列表中。"
                "允许: databrain.intlgame.com / databrain.woa.com / databrain-*.intlgame.com",
                file=sys.stderr,
            )
            sys.exit(1)
        return token, [explicit]

    if _resolved_host:
        return token, [_resolved_host]

    return token, list(_FALLBACK_HOSTS)


# ---------------------------------------------------------------------------
# Security validation
# ---------------------------------------------------------------------------
def _validate_game_id(game_id: str) -> str:
    if not _GAME_ID_RE.match(game_id):
        print(
            f"[ERROR] Invalid game_id: {game_id!r}. "
            "Must start with 'u' (mobile) or 'e' (PC) followed by hex characters.",
            file=sys.stderr,
        )
        sys.exit(1)
    return game_id


def _validate_date(date_str: str, label: str = "date") -> str:
    if not _DATE_RE.match(date_str):
        print(
            f"[ERROR] Invalid {label}: {date_str!r}. Expected YYYY-MM-DD.",
            file=sys.stderr,
        )
        sys.exit(1)
    return date_str


_PLACEHOLDER_RE = re.compile(r"<(game_id|start_date|end_date|[a-z_]+)>")


def _validate_sql(sql: str) -> str:
    # Detect unreplaced template placeholders (e.g. <game_id>, <start_date>)
    placeholder = _PLACEHOLDER_RE.search(sql)
    if placeholder:
        print(
            f"[ERROR] SQL contains unreplaced placeholder: {placeholder.group()!r}. "
            "Replace all <...> tokens with actual values before calling this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    match = _FORBIDDEN_SQL_RE.search(sql)
    if match:
        print(
            f"[ERROR] SQL contains forbidden keyword: {match.group()!r}. "
            "Only SELECT queries are permitted.",
            file=sys.stderr,
        )
        sys.exit(1)
    return sql


# ---------------------------------------------------------------------------
# REST API execution (with multi-host fallback)
# ---------------------------------------------------------------------------
def _execute_sql(tok: str, hosts: list[str], sql: str) -> list[dict]:
    """POST SQL to the opinion query API; try each host in order, cache winner."""
    global _resolved_host
    last_error: Exception | None = None

    for h in hosts:
        endpoint = h + _QUERY_API
        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {tok}",
        }
        try:
            resp = httpx.post(endpoint, headers=headers, json={"sql": sql}, timeout=60.0)
        except httpx.HTTPError as e:
            last_error = e
            if len(hosts) > 1:
                print(f"[fallback] {h} failed ({e.__class__.__name__}), trying next...", file=sys.stderr)
            continue

        if resp.status_code != 200:
            msg = resp.text.strip()[:300]
            try:
                err = json.loads(msg)
                msg = str(err.get("msg", msg))[:300]
            except json.JSONDecodeError:
                pass
            last_error = RuntimeError(f"API error (HTTP {resp.status_code}): {msg}")
            if len(hosts) > 1:
                print(f"[fallback] {h} returned {resp.status_code}, trying next...", file=sys.stderr)
            continue

        content = resp.text.strip()
        if not content:
            if len(hosts) > 1:
                _resolved_host = h
            return []

        # Detect JSON error response: API may return HTTP 200 with
        # {"code": 500, "msg": "Query failed: ..."} instead of CSV.
        if content.startswith("{"):
            try:
                api_resp = json.loads(content)
                code = api_resp.get("code", 0)
                if code != 0:
                    last_error = RuntimeError(
                        f"API query failed (code={code}): {api_resp.get('msg', 'unknown error')}"
                    )
                    if len(hosts) > 1:
                        print(f"[fallback] {h} query error (code={code}), trying next...", file=sys.stderr)
                    continue
            except json.JSONDecodeError:
                pass  # not JSON, fall through to CSV parsing

        if len(hosts) > 1:
            _resolved_host = h
        reader = csv.DictReader(io.StringIO(content))
        return [dict(row) for row in reader]

    msg = str(last_error) if last_error else "unknown error"
    print(f"[ERROR] All hosts failed. Last error: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Skill invocation reporting (background thread, non-blocking)
# ---------------------------------------------------------------------------
def _do_report(message: str, session_id: str, msg_id: str) -> None:
    """Fire-and-forget: report this skill invocation to operationLog API."""
    try:
        report(
            message=message or "databrain-opinion-metrics query",
            session_id=session_id,
            msg_id=msg_id,
        )
    except Exception:
        pass  # reporting failure must never affect the main query


def _start_report_thread(message: str, session_id: str, msg_id: str) -> threading.Thread:
    t = threading.Thread(
        target=_do_report,
        args=(message, session_id, msg_id),
        daemon=False,  # non-daemon so thread can complete even if main exits
    )
    t.start()
    return t


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="舆情指标通用 SQL 执行器（参见 references/ 下各数据表模板文件）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # SQL source (mutually exclusive)
    sql_group = parser.add_mutually_exclusive_group(required=True)
    sql_group.add_argument("--sql",      metavar="SQL",  help="已完成参数替换的完整 SQL 字符串")
    sql_group.add_argument("--sql_file", metavar="PATH", help="包含完整 SQL 的文件路径（适合长查询）")

    # Identity (required for validation + reporting)
    parser.add_argument("--game_id", required=True, metavar="GAME_ID",
                        help="游戏 ID（u.../e...），用于安全校验和打点上报")

    # Date range
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument("--date",       metavar="YYYY-MM-DD", help="单日查询")
    date_group.add_argument("--start_date", metavar="YYYY-MM-DD", help="范围起（配合 --end_date）")
    parser.add_argument(    "--end_date",   metavar="YYYY-MM-DD", help="范围止（配合 --start_date）")

    # User message for reporting
    parser.add_argument("--message", default="", metavar="MSG",
                        help="用户原始问题，用于埋点上报（建议总是传入）")

    # Output format
    parser.add_argument("--format", choices=["json", "csv"], default="json",
                        help="输出格式，默认 json")

    args = parser.parse_args()

    tok, hosts = _get_config()

    # ── Start background reporting immediately after auth succeeds ────────────
    # session_id/msg_id generated here in main(), not inside the thread,
    # so the thread only calls report() with pre-built IDs (no dynamic import needed)
    session_id, msg_id = new_session_msg_pair()
    report_thread = _start_report_thread(args.message, session_id, msg_id)

    # ── Validate game_id ─────────────────────────────────────────────────────
    game_id = _validate_game_id(args.game_id.strip())

    # ── Resolve and validate date range ──────────────────────────────────────
    if args.date:
        start_date = end_date = _validate_date(args.date, "--date")
    elif args.start_date and args.end_date:
        start_date = _validate_date(args.start_date, "--start_date")
        end_date   = _validate_date(args.end_date,   "--end_date")
    elif args.start_date:
        start_date = end_date = _validate_date(args.start_date, "--start_date")
    else:
        print("[ERROR] Provide --date or both --start_date and --end_date.", file=sys.stderr)
        sys.exit(1)

    # ── Load SQL ──────────────────────────────────────────────────────────────
    if args.sql:
        sql = args.sql.strip()
    else:
        sql_path = Path(args.sql_file)
        if not sql_path.exists():
            print(f"[ERROR] SQL file not found: {args.sql_file}", file=sys.stderr)
            sys.exit(1)
        sql = sql_path.read_text(encoding="utf-8").strip()

    if not sql:
        print("[ERROR] SQL is empty.", file=sys.stderr)
        sys.exit(1)

    # ── Security: reject DDL/DML ──────────────────────────────────────────────
    _validate_sql(sql)

    # ── Execute ───────────────────────────────────────────────────────────────
    rows = _execute_sql(tok, hosts, sql)

    # ── Output ────────────────────────────────────────────────────────────────
    if args.format == "csv":
        if rows:
            writer = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    else:
        result = {
            "game_id":    game_id,
            "start_date": start_date,
            "end_date":   end_date,
            "rows":       rows,
            "row_count":  len(rows),
        }
        print(json.dumps(result, default=str, ensure_ascii=False, indent=2))

    # ── Wait for report thread (max 1 s) ──────────────────────────────────────
    report_thread.join(timeout=1.0)


if __name__ == "__main__":
    main()
