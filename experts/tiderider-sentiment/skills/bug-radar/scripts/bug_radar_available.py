#!/usr/bin/env python3
"""
Bug-radar availability probe — SILENT, offline, side-effect-free.

WHY THIS EXISTS (different from the sentiment lane):
  The bug tables live in the `tiderider` dataset. The DataBrain `exec_sql`
  token API is scoped to `opinion` only and returns HTTP 403 for the whole
  `tiderider` dataset (verified 2026-07-30). So — unlike the sentiment lane,
  which works over either a direct-BigQuery credential OR the Databrain token —
  the BUG lane is reachable ONLY through a direct-BigQuery credential
  (Service-Account JSON or gcloud ADC).

This helper reuses `detect_connection.py` (no new detection logic) and maps its
result to a bug-lane verdict:

    bigquery_sa  -> "available"    (direct BQ, full access to tiderider)
    bigquery_adc -> "available"    (direct BQ, full access to tiderider)
    databrain    -> "unavailable"  (token only -> 403 on tiderider)
    none         -> "unconfigured" (nothing set up at all)

Usage:
    python bug_radar_available.py            # prints: available | unavailable | unconfigured
    python bug_radar_available.py --user-hint  # user-safe message when not available

Exit code: 0 when available; 3 otherwise. Offline, no network, no cost.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_DETECTOR = Path(__file__).parent / "detect_connection.py"

_UNAVAILABLE_HINT = (
    "Bug 库分析目前依赖直连 BigQuery 的凭证（服务账号 JSON 或 gcloud ADC）。\n"
    "当前只检测到 DataBrain Token —— 它可以做舆情分析，但访问不到 Bug 库数据。\n"
    "如需 Bug 库联动，请联系 chandwang（企业微信）开通直连 BigQuery 的读权限。"
)
_UNCONFIGURED_HINT = (
    "还没有配置任何数据连接。舆情分析可以用 DataBrain Token（个人令牌中心申请后我来部署）；\n"
    "但 Bug 库分析额外需要直连 BigQuery 的凭证（服务账号 JSON 或 gcloud ADC）。\n"
    "两者的开通都可以联系 chandwang（企业微信）。"
)


def _detect() -> str:
    try:
        out = subprocess.run(
            [sys.executable, str(_DETECTOR)],
            capture_output=True, text=True, timeout=20,
        )
        return (out.stdout or "").strip().splitlines()[-1].strip() if out.stdout.strip() else "none"
    except Exception:
        return "none"


def verdict() -> str:
    method = _detect()
    if method in ("bigquery_sa", "bigquery_adc"):
        return "available"
    if method == "databrain":
        return "unavailable"
    return "unconfigured"


def main():
    ap = argparse.ArgumentParser(description="Bug-radar availability probe (direct-BigQuery required).")
    ap.add_argument("--user-hint", action="store_true",
                    help="Print the user-safe message when the bug lane is not available.")
    args = ap.parse_args()

    v = verdict()
    if args.user_hint:
        if v == "available":
            print("Bug 库已可用。")
        elif v == "unavailable":
            print(_UNAVAILABLE_HINT)
        else:
            print(_UNCONFIGURED_HINT)
    else:
        print(v)
    sys.exit(0 if v == "available" else 3)


if __name__ == "__main__":
    main()
