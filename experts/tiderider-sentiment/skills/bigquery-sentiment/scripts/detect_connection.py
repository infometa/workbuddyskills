#!/usr/bin/env python3
"""
Connection-method auto-detector for TideRider sentiment queries.

Three execution methods exist, but they are NOT equal — they form a
PRIORITY / FALLBACK CHAIN. Direct-BigQuery methods return COMPLETE result sets;
the Databrain fallback hard-caps DETAIL results at 5000 rows, which can distort
detail-level analysis. So whenever a direct-BigQuery credential is configured on
the backend, it must be preferred.

Priority (highest first):
    1) bigquery_sa   -- Direct BigQuery via Service Account JSON
                        (env GOOGLE_APPLICATION_CREDENTIALS points to a file)      full results, no cap
    2) bigquery_adc  -- Direct BigQuery via local gcloud ADC
                        (application_default_credentials.json present)             full results, no cap
    3) databrain     -- Databrain exec_sql API via tiderider_sql.py
                        (env DATABRAIN_TOKEN set)                                   DETAIL results capped at 5000

Detection is silent and internal. The analyst/backend calls this ONCE before the
first query and connects accordingly WITHOUT announcing the method to the user.
Methods 1 & 2 are hidden from end users; method 3 (Databrain Token, user-applied)
is the default user-facing method.

Usage:
    python detect_connection.py            # prints the chosen method id (silent, machine-readable)
    python detect_connection.py --verbose  # prints method + why + all candidates (JSON, INTERNAL only)

This is a SILENT, side-effect-free, offline check (it only inspects whether a few
local files / env vars exist — no network, no query, no cost). The expert runs it
ONCE before the first query and connects accordingly WITHOUT asking the user to
confirm and WITHOUT announcing the method. Do not surface `--verbose` output to
end users — it names the internal methods.

When NOTHING is configured, use `--user-hint` to get the ONLY message that is
safe to show a user: it mentions solely the Databrain Token path (apply → save to
a file → hand the file to the expert). Methods A/B (direct BigQuery) are never
mentioned to users unless the user themselves brings up having a BigQuery
credential or gcloud access.

Exit code is always 0 when a method is found; 3 if NOTHING is configured.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _sa_json_available() -> tuple[bool, str]:
    """Method 1: GOOGLE_APPLICATION_CREDENTIALS env points to an existing file."""
    p = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not p:
        return False, "GOOGLE_APPLICATION_CREDENTIALS not set"
    if not Path(p).expanduser().is_file():
        return False, f"GOOGLE_APPLICATION_CREDENTIALS set but file missing: {p}"
    return True, f"Service Account JSON at {p}"


def _adc_available() -> tuple[bool, str]:
    """Method 2: local gcloud Application Default Credentials present."""
    # Explicit override first.
    override = os.environ.get("CLOUDSDK_CONFIG", "").strip()
    candidates = []
    if override:
        candidates.append(Path(override) / "application_default_credentials.json")
    # Standard locations (macOS/Linux and Windows).
    home = Path.home()
    candidates += [
        home / ".config" / "gcloud" / "application_default_credentials.json",
        home / "AppData" / "Roaming" / "gcloud" / "application_default_credentials.json",
    ]
    for c in candidates:
        if c.is_file():
            return True, f"gcloud ADC at {c}"
    return False, "no application_default_credentials.json found"


def _databrain_available() -> tuple[bool, str]:
    """Method 3: Databrain Token present (env or skill-root .env)."""
    tok = os.environ.get("DATABRAIN_TOKEN", "").strip()
    if tok:
        return True, "DATABRAIN_TOKEN set in environment"
    # Mirror _utils._load_dotenv behaviour: skill root is scripts/..
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("DATABRAIN_TOKEN=") and line.split("=", 1)[1].strip():
                return True, f"DATABRAIN_TOKEN found in {env_file}"
    return False, "DATABRAIN_TOKEN not set (env or .env)"


# Ordered priority chain: (method_id, label, full_results?, detector)
_CHAIN = [
    ("bigquery_sa", "Direct BigQuery · Service Account JSON", True, _sa_json_available),
    ("bigquery_adc", "Direct BigQuery · local ADC", True, _adc_available),
    ("databrain", "Databrain Token · tiderider_sql.py", False, _databrain_available),
]


def detect() -> dict:
    """Return the chosen method plus the full evaluation trail."""
    candidates = []
    chosen = None
    for method_id, label, full, detector in _CHAIN:
        ok, why = detector()
        candidates.append({
            "method": method_id,
            "label": label,
            "full_results": full,
            "available": ok,
            "detail": why,
        })
        if ok and chosen is None:
            chosen = {
                "method": method_id,
                "label": label,
                "full_results": full,
                "detail": why,
                "capped_at_5000": (method_id == "databrain"),
            }
    return {"chosen": chosen, "candidates": candidates}


# The ONLY user-facing message when nothing is configured. Mentions the token path only.
_USER_HINT_NONE = (
    "还没有检测到可用的连接。请按 3 步接入（很简单）：\n"
    "  1) 打开 DataBrain 用户中心 - 个人令牌中心申请你自己的 Token，"
    "授权范围选「授权访问应用 - 全部应用」，复制原始值（不含 Bearer 前缀）。\n"
    "     内网: https://databrain.woa.com/v2/user-center/personal-tokens-center\n"
    "     外网: https://databrain-global.intlgame.com/v2/user-center/personal-tokens-center\n"
    "  2) 把这个值随手存进任意一个文本文件（记事本 / .txt 都行）。\n"
    "  3) 把文件路径告诉我，我来帮你完成剩下的部署和验证。\n"
    "如果申请或权限上遇到问题，可在企业微信联系 chandwang。"
)


def main():
    ap = argparse.ArgumentParser(description="Detect the preferred TideRider SQL execution method.")
    ap.add_argument("--verbose", action="store_true",
                    help="Print full JSON (method + reasons + all candidates). INTERNAL only — never show users.")
    ap.add_argument("--user-hint", action="store_true",
                    help="On 'none', print the user-safe onboarding hint (Databrain Token path only).")
    args = ap.parse_args()

    res = detect()

    if res["chosen"]:
        if args.verbose:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(res["chosen"]["method"])
        sys.exit(0)

    # Nothing configured.
    if args.user_hint:
        # Safe to show the user: only the token path, never methods A/B.
        print(_USER_HINT_NONE)
    elif args.verbose:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("none")
    sys.exit(3)


if __name__ == "__main__":
    main()
