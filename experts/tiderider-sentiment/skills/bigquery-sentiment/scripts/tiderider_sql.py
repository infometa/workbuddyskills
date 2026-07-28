#!/usr/bin/env python3
"""
TideRider -> Databrain SQL adapter.

Purpose
-------
TideRider builds excellent SQL already. This thin wrapper lets that SQL run
through the Databrain `exec_sql` HTTP API (Databrain-Token auth) instead of a
direct BigQuery client, WITHOUT rewriting any query logic.

It solves the three concerns raised during integration review:

  1. PROJECT PREFIX  -- Databrain's API is already bound to a project. A
     fully-qualified `tencent-databrain-prod.opinion.feeds` prefix is stripped
     down to `opinion.feeds` automatically, so existing TideRider templates run
     unchanged.

  2. 5000-ROW HARD CAP  -- The Databrain API silently caps detail results at
     5000 rows (code=0, no truncation flag in the payload). A detail query that
     matches 7,511 rows comes back as exactly 5000 with NO error. Analyzing
     those 5000 rows as if they were the full set produces systematically biased
     conclusions. This adapter DETECTS that case (runs a companion COUNT(*) for
     detail queries) and attaches an explicit `_tiderider_guard` block flagging
     `TRUNCATED_AT_5000` plus a human-facing warning string.

  3. AGGREGATE vs DETAIL classification  -- Aggregate queries (GROUP BY / bare
     COUNT|AVG|SUM with no per-row projection) return few rows and never hit the
     cap; they are marked SAFE and skip the companion COUNT. Detail queries
     (per-row projection, no GROUP BY) are the risky ones and get the guard.

Auth / env (delegated to the official _utils.py):
  - DATABRAIN_TOKEN : DataBrain Token (raw JWT value, required)
  - DATABRAIN_HOST  : optional, trusted-host validated

Usage
-----
    export DATABRAIN_TOKEN="eyJ..."
    python tiderider_sql.py --sql "SELECT ... FROM opinion.feeds WHERE ..."
    python tiderider_sql.py --sql_file /tmp/q.sql --output_file /tmp/out.json

Output: same JSON envelope as execute_sql, plus a top-level `_tiderider_guard`:
    {
      "code": 0,
      "data": { ... original ... },
      "_tiderider_guard": {
        "query_type": "detail" | "aggregate",
        "returned_rows": 5000,
        "real_total": 7511,          # only for detail queries
        "truncated": true,
        "status": "TRUNCATED_AT_5000",
        "warning": "⚠️ ..."
      }
    }
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from pathlib import Path

# Reuse the official Databrain execution + auth code verbatim.
sys.path.insert(0, str(Path(__file__).parent))
from execute_sql import execute_sql, assert_readonly  # noqa: E402
from _utils import get_host, require_token  # noqa: E402

HARD_ROW_CAP = 5000  # Databrain API detail-row hard limit (verified 2026-07-16)


# ── Skill invocation reporting (background thread, non-blocking) ──────────────
# Ports databrain's standard埋点. HARD RULE (per project铁律): reporting must
# NEVER affect the main query — the import, the thread launch, and the report
# call are all wrapped so any failure is swallowed. If DATABRAIN_TOKEN is not
# set (e.g. the user connects via direct BigQuery), report() silently no-ops.
def _do_report(message: str) -> None:
    """Fire-and-forget: report this skill invocation to operationLog API.
    Everything (import, id generation, network) lives inside one try/except so
    a failure at ANY step is swallowed and never touches the main query."""
    try:
        from report_log import new_session_msg_pair, report  # isolate import err
        session_id, msg_id = new_session_msg_pair()
        report(message, session_id, msg_id)
    except Exception:
        pass  # reporting failure must never affect the main query


def _start_report_thread(message: str):
    """Launch埋点 in a non-daemon background thread. Returns the thread (or None
    if even launching it failed — which still must not break the main flow)."""
    try:
        t = threading.Thread(target=_do_report, args=(message,), daemon=False)
        t.start()
        return t
    except Exception:
        return None

# Fully-qualified project prefix that Databrain's API does NOT want (it is
# already bound to the project). Strip it so TideRider templates run unchanged.
#
# Two shapes must be handled WITHOUT breaking backtick pairing:
#   1) backticked whole identifier:  `tencent-databrain-prod.opinion.feeds`
#      -> `opinion.feeds`   (keep the outer backticks, drop only the project seg)
#   2) bare / project-only backtick:  tencent-databrain-prod.opinion.feeds
#      -> opinion.feeds
_PREFIX_IN_BACKTICKS_RE = re.compile(
    r"`\s*tencent-databrain-prod\.", re.IGNORECASE
)  # `tencent-databrain-prod.xxx`  ->  `xxx`
_PREFIX_BARE_RE = re.compile(
    r"`?tencent-databrain-prod`?\.", re.IGNORECASE
)  # any leftover  tencent-databrain-prod.  ->  ""  (do NOT eat leading space)


def strip_project_prefix(sql: str) -> str:
    """Remove the `tencent-databrain-prod.` project segment so that
    `tencent-databrain-prod.opinion.feeds` -> `opinion.feeds` (backticks kept)
    and tencent-databrain-prod.opinion.feeds -> opinion.feeds.

    Order matters: handle the backticked form first (preserving the opening
    backtick), then any bare leftover."""
    # Case 1: `tencent-databrain-prod.  ->  `   (preserve opening backtick)
    sql = _PREFIX_IN_BACKTICKS_RE.sub("`", sql)
    # Case 2: bare  tencent-databrain-prod.  ->  (nothing)
    sql = _PREFIX_BARE_RE.sub("", sql)
    return sql


def classify_query(sql: str) -> str:
    """Heuristically classify a SELECT as 'aggregate' (safe, few rows) or
    'detail' (risky, may hit the 5000 cap).

    Aggregate signals (any -> aggregate):
      - contains GROUP BY
      - is a bare aggregate over the whole set (COUNT/AVG/SUM/MIN/MAX/COUNTIF)
        with no other projected raw columns
    Everything else that projects per-row columns is treated as 'detail'.
    """
    upper = sql.upper()

    # GROUP BY -> aggregate (one row per group, never the raw feed).
    if re.search(r"\bGROUP\s+BY\b", upper):
        return "aggregate"

    m = re.search(r"\bSELECT\b(.*?)\bFROM\b", upper, re.DOTALL)
    if not m:
        return "detail"
    select_list = m.group(1)

    # A bare `*` (SELECT *), i.e. a star NOT immediately preceded by '(' as in
    # COUNT(*), means raw per-row projection -> detail.
    if re.search(r"(^|[^(\w])\*", select_list):
        return "detail"

    # No GROUP BY and no bare star: if the SELECT list contains ANY aggregate
    # function, it is a whole-table aggregate that collapses to a single row and
    # therefore cannot hit the 5000-row cap. This single, robust signal avoids
    # fragile per-alias parsing (implicit aliases, expressions, etc.).
    if re.search(r"\b(COUNT|AVG|SUM|MIN|MAX|COUNTIF|APPROX_COUNT_DISTINCT)\s*\(", select_list):
        return "aggregate"

    return "detail"


_TRAILING_LIMIT_RE = re.compile(r"\bLIMIT\s+(\d+)\s*;?\s*$", re.IGNORECASE)


def extract_user_limit(sql: str) -> int | None:
    """Return the row count of a trailing `LIMIT n` the user wrote themselves,
    or None if the query has no explicit trailing LIMIT.

    This matters for truncation detection: a user who writes `LIMIT 50` and
    gets 50 rows is NOT truncated — they asked for exactly 50. Only a query
    with no user LIMIT (or a LIMIT >= the hard cap) that comes back at exactly
    5000 rows is a genuine API-side truncation."""
    m = _TRAILING_LIMIT_RE.search(sql.strip().rstrip(";"))
    return int(m.group(1)) if m else None


def build_count_sql(sql: str) -> str | None:
    """Wrap a detail query as `SELECT COUNT(*) FROM ( <sql> )` to learn the real
    total. Strips a trailing LIMIT/ORDER BY so the count reflects the full match.
    Returns None if we cannot safely build one."""
    body = sql.strip().rstrip(";")
    # Remove a trailing ORDER BY ... and trailing LIMIT ... (outermost only,
    # best-effort). We only strip if they appear at the very end.
    body = re.sub(r"\bLIMIT\s+\d+\s*$", "", body, flags=re.IGNORECASE).rstrip()
    body = re.sub(r"\bORDER\s+BY\b[^)]*$", "", body, flags=re.IGNORECASE).rstrip()
    if not body:
        return None
    return f"SELECT COUNT(*) AS __real_total FROM (\n{body}\n) AS __sub"


def attach_guard(
    result: dict,
    query_type: str,
    real_total: int | None,
    user_limit: int | None = None,
) -> dict:
    """Attach a `_tiderider_guard` block describing truncation risk.

    Truncation is the API silently capping results at HARD_ROW_CAP (5000) when
    the caller wanted more. A user-supplied `LIMIT n` (n < 5000) is NOT
    truncation — they asked for exactly n rows. So a detail query is flagged
    TRUNCATED_AT_5000 only when it comes back at the hard cap (5000 rows) AND
    the user did not deliberately limit to fewer than that."""
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    returned = data.get("count") or 0

    guard: dict = {
        "query_type": query_type,
        "returned_rows": returned,
    }

    if query_type == "aggregate":
        guard["truncated"] = False
        guard["status"] = "SAFE_AGGREGATE"
        guard["warning"] = ""
    else:
        guard["real_total"] = real_total
        # The user deliberately capped rows below the hard cap -> respect it,
        # never call that a truncation even if real_total is larger.
        user_capped_below_hard = user_limit is not None and user_limit < HARD_ROW_CAP

        # Genuine API truncation: hit the hard cap AND user didn't ask for less.
        hit_hard_cap = returned >= HARD_ROW_CAP
        truncated = hit_hard_cap and not user_capped_below_hard and (
            real_total is None or real_total > returned
        )
        guard["truncated"] = bool(truncated)
        if truncated:
            guard["status"] = "TRUNCATED_AT_5000"
            total_txt = f"{real_total:,}" if real_total is not None else "unknown (>5000)"
            guard["warning"] = (
                f"⚠️ 明细结果被 Databrain API 截断在 {returned:,} 条，"
                f"实际匹配 {total_txt} 条。本次分析仅对返回的 {returned:,} 条负责，"
                f"不代表全量。若需全量结论，请改用聚合查询（GROUP BY / COUNT / AVG / COUNTIF）。"
            )
        else:
            guard["status"] = "OK_DETAIL"
            guard["warning"] = ""
            # Informational note when the user's own LIMIT trimmed a larger set.
            if user_capped_below_hard and real_total is not None and real_total > returned:
                guard["warning"] = (
                    f"ℹ️ 按你指定的 LIMIT 返回 {returned:,} 条（该条件实际匹配 {real_total:,} 条）。"
                    f"这是你主动限定的行数，非接口截断。"
                )

    result["_tiderider_guard"] = guard
    return result


def main():
    parser = argparse.ArgumentParser(
        description="TideRider->Databrain SQL adapter (project-prefix strip + 5000-row truncation guard)."
    )
    parser.add_argument("--sql", default=None, help="SQL statement")
    parser.add_argument("--sql_file", default=None, help="Read SQL from file")
    parser.add_argument("--schema", default="opinion", help="Schema (default: opinion)")
    parser.add_argument("--timeout_ms", type=int, default=60000, help="Timeout ms (max 120000)")
    parser.add_argument("--limit", type=int, default=HARD_ROW_CAP,
                        help=f"Row limit (default/max {HARD_ROW_CAP})")
    parser.add_argument("--output_file", default=None,
                        help="Write full JSON (incl. guard) to this path.")
    parser.add_argument("--no_count_probe", action="store_true",
                        help="Skip the companion COUNT(*) for detail queries (faster, but real_total unknown).")
    parser.add_argument("--message", default="", metavar="MSG",
                        help="用户原始问题，用于埋点上报（可选；不传也不影响查询）。")
    args = parser.parse_args()

    sql = args.sql
    if args.sql_file:
        try:
            sql = Path(args.sql_file).read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            print(f"Error: SQL file not found: {args.sql_file}", file=sys.stderr)
            sys.exit(1)
    if not sql:
        print("Error: provide SQL via --sql or --sql_file.", file=sys.stderr)
        sys.exit(1)

    # 1) normalize table names
    sql = strip_project_prefix(sql)
    # 2) reuse official read-only guard
    assert_readonly(sql)

    token = require_token()
    host = get_host()

    # ── Start background埋点 immediately (non-blocking; no-op without token) ──
    # This does NOT gate or delay the query in any way. If it fails, it fails
    # silently in its own thread. Started here (after we know we're proceeding).
    report_thread = _start_report_thread(args.message)

    limit = min(args.limit, HARD_ROW_CAP)
    qtype = classify_query(sql)
    user_limit = extract_user_limit(sql)  # explicit trailing LIMIT the user wrote

    # 3) run the main query
    import requests  # imported by execute_sql already; safe here
    try:
        result = execute_sql(
            host=host, token=token, sql=sql, schema=args.schema,
            timeout_ms=min(args.timeout_ms, 120000), limit=limit,
        )
    except requests.exceptions.RequestException as e:  # type: ignore
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 4) for detail queries, learn the real total via a companion COUNT
    real_total = None
    if qtype == "detail" and not args.no_count_probe and result.get("code") == 0:
        count_sql = build_count_sql(sql)
        if count_sql:
            try:
                cres = execute_sql(
                    host=host, token=token, sql=count_sql, schema=args.schema,
                    timeout_ms=min(args.timeout_ms, 120000), limit=1,
                )
                if cres.get("code") == 0:
                    rows = (cres.get("data") or {}).get("data") or []
                    if rows:
                        real_total = int(rows[0].get("__real_total", 0))
            except Exception:
                pass  # count probe is best-effort; never block main result

    # 5) attach guard
    result = attach_guard(result, qtype, real_total, user_limit=user_limit)

    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output_file:
        Path(args.output_file).expanduser().write_text(output_json, encoding="utf-8")
        guard = result["_tiderider_guard"]
        print(f"✓ Result written to {args.output_file}")
        print(f"  query_type={guard['query_type']} | returned={guard['returned_rows']} | status={guard['status']}")
        if guard.get("warning"):
            print(guard["warning"])
    else:
        print(output_json)

    # Give the埋点 thread a brief moment to finish, but never hang on it.
    if report_thread is not None:
        try:
            report_thread.join(timeout=1.0)
        except Exception:
            pass


if __name__ == "__main__":
    main()
