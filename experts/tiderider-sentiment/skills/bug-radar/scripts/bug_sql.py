#!/usr/bin/env python3
"""
Bug-radar -> BigQuery/Databrain SQL adapter.

This is the bug-library twin of `tiderider_sql.py`. It reuses the exact same
connection chain (direct BigQuery SA/ADC preferred, Databrain Token fallback,
5000-row truncation guard, project-prefix strip, read-only guard, background
埋点) but is tuned for the four `tiderider.bug_*` tables instead of the
`opinion.*` feeds tables:

  1. DEFAULT SCHEMA is `tiderider` (not `opinion`), because every bug table
     lives in the `tiderider` dataset.

  2. PARTITION-FILTER SAFETY NET. Three of the four bug tables enforce
     `require_partition_filter = TRUE`:
        - bug_issue_summary  -> partition column `FirstSeen`  (DATE)
        - bug_daily_metrics  -> partition column `Date`       (DATE)
        - bug_comment_detail -> partition column `CommentDate`(DATE)
        - bug_category_mapping -> NOT partitioned (small lookup, 9 rows)
     A query that hits one of the partitioned tables without a filter on its
     partition column fails hard with a BigQuery 400 (invalidQuery). This
     wrapper emits a loud, actionable stderr warning BEFORE sending the query,
     so the agent fixes the SQL instead of eating an opaque 400.

Everything else (auth, guard, prefix strip) is delegated verbatim to the shared
modules, so there is zero logic drift from the sentiment lane.

Usage
-----
    python bug_sql.py --sql "SELECT ... FROM tiderider.bug_issue_summary WHERE FirstSeen BETWEEN ... "
    python bug_sql.py --sql_file /tmp/q.sql --output_file /tmp/out.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from execute_sql import execute_sql, assert_readonly  # noqa: E402
from _utils import get_host, require_token  # noqa: E402
from tiderider_sql import (  # noqa: E402
    HARD_ROW_CAP,
    strip_project_prefix,
    classify_query,
    extract_user_limit,
    build_count_sql,
    attach_guard,
)

# ── Partition-filter safety net ──────────────────────────────────────────────
# (table token in SQL, required partition column). The category-mapping table is
# intentionally absent: it is a tiny unpartitioned lookup and needs no filter.
_PARTITIONED = {
    "BUG_ISSUE_SUMMARY": "FirstSeen",
    "BUG_DAILY_METRICS": "Date",
    "BUG_COMMENT_DETAIL": "CommentDate",
}


def warn_partition_filters(sql: str) -> None:
    """Soft-warn (stderr) when a partitioned bug table is queried without a
    filter on its partition column. BigQuery would reject it with a 400 anyway;
    this makes the fix obvious instead of opaque."""
    upper = sql.upper()
    for table_token, part_col in _PARTITIONED.items():
        if table_token in upper and part_col.upper() not in upper:
            print(
                f"⚠ SQL hits `tiderider.{table_token.lower()}` but is missing a filter on its "
                f"partition column `{part_col}` (require_partition_filter=TRUE). "
                f"BigQuery will reject this with a 400. "
                f"Fix: add e.g. `AND {part_col} BETWEEN DATE('<start>') AND DATE('<end>')`.",
                file=sys.stderr,
            )


def _do_report(message: str) -> None:
    try:
        from report_log import new_session_msg_pair, report
        session_id, msg_id = new_session_msg_pair()
        report(message, session_id, msg_id)
    except Exception:
        pass


def _start_report_thread(message: str):
    try:
        t = threading.Thread(target=_do_report, args=(message,), daemon=False)
        t.start()
        return t
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Bug-radar -> BigQuery/Databrain SQL adapter (tiderider schema + bug partition-filter net + 5000-row guard)."
    )
    parser.add_argument("--sql", default=None, help="SQL statement")
    parser.add_argument("--sql_file", default=None, help="Read SQL from file")
    parser.add_argument("--schema", default="tiderider", help="Schema (default: tiderider)")
    parser.add_argument("--timeout_ms", type=int, default=60000, help="Timeout ms (max 120000)")
    parser.add_argument("--limit", type=int, default=HARD_ROW_CAP,
                        help=f"Row limit (default/max {HARD_ROW_CAP})")
    parser.add_argument("--output_file", default=None,
                        help="Write full JSON (incl. guard) to this path.")
    parser.add_argument("--no_count_probe", action="store_true",
                        help="Skip the companion COUNT(*) for detail queries.")
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

    sql = strip_project_prefix(sql)
    assert_readonly(sql)
    warn_partition_filters(sql)

    token = require_token()
    host = get_host()
    report_thread = _start_report_thread(args.message)

    limit = min(args.limit, HARD_ROW_CAP)
    qtype = classify_query(sql)
    user_limit = extract_user_limit(sql)

    import requests
    try:
        result = execute_sql(
            host=host, token=token, sql=sql, schema=args.schema,
            timeout_ms=min(args.timeout_ms, 120000), limit=limit,
        )
    except requests.exceptions.RequestException as e:  # type: ignore
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)

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
                pass

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

    if report_thread is not None:
        try:
            report_thread.join(timeout=1.0)
        except Exception:
            pass


if __name__ == "__main__":
    main()
