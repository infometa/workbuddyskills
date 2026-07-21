#!/usr/bin/env python3
"""
pacing-alert.py — API-based pacing check for marketing campaigns.

Monitors campaign health across channels:
- Checks pipeline/lead staging rates against daily targets
- Monitors email campaign sending status and capacity
- Tracks candidate sourcing pacing against weekly targets
- Reports cron job health

Exit 0 = on pace (all green), Exit 1 = alert needed (output contains issues).

Configure via environment variables (see .env.example).

Usage:
  python3 pacing-alert.py              # Run full pacing check
  python3 pacing-alert.py --json       # Output as JSON instead of formatted text
"""

import argparse
import sys
import json
import subprocess
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error
import os

# ── Configuration ──────────────────────────────────────────────────────────────

# API authentication tokens (set via environment variables)
PIPELINE_API_URL = os.environ.get("PIPELINE_API_URL", "https://your-dashboard.example.com/api/pipeline")
PIPELINE_AUTH = os.environ.get("PIPELINE_AUTH_TOKEN", "")  # Bearer token for pipeline API

RECRUITING_API_URL = os.environ.get("RECRUITING_API_URL", "https://your-dashboard.example.com/api/recruiting/candidates")
RECRUITING_AUTH = os.environ.get("RECRUITING_AUTH_TOKEN", "")  # Bearer token for recruiting API

# Email platform API (e.g., Instantly, Lemlist, Smartlead)
EMAIL_API_URL = os.environ.get("EMAIL_API_URL", "")  # e.g., https://api.your-email-platform.com/v2/campaigns
EMAIL_AUTH = os.environ.get("EMAIL_AUTH_TOKEN", "")  # Bearer token for email platform

# Campaign IDs for outbound email. Format: JSON object {"Campaign Name": "campaign-uuid"}
OUTBOUND_CAMPAIGNS = json.loads(os.environ.get("OUTBOUND_CAMPAIGNS", "{}"))
RECRUITING_CAMPAIGNS = json.loads(os.environ.get("RECRUITING_CAMPAIGNS", "{}"))

# Pacing targets
DAILY_LEAD_TARGET = int(os.environ.get("DAILY_LEAD_TARGET", "10"))       # Min leads staged per day
WEEKLY_CANDIDATE_TARGET = int(os.environ.get("WEEKLY_CANDIDATE_TARGET", "400"))  # Candidates per week

# Timezone offset from UTC (e.g., -7 for PDT, -8 for PST)
TZ_OFFSET = int(os.environ.get("TZ_OFFSET", "-7"))
LOCAL_TZ = timezone(timedelta(hours=TZ_OFFSET))
TZ_LABEL = os.environ.get("TZ_LABEL", "PDT")

# ── Helpers ────────────────────────────────────────────────────────────────────

def api_get(url, auth):
    """Make authenticated GET request. Returns parsed JSON or error dict."""
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = auth if auth.startswith("Bearer ") else f"Bearer {auth}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"_error": str(e)}

def now_local():
    return datetime.now(LOCAL_TZ)

def today_date():
    return now_local().date()

def week_start():
    now = now_local()
    monday = now - timedelta(days=now.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)

def parse_ts(ts_str):
    """Parse ISO timestamp string to local timezone datetime."""
    if not ts_str:
        return None
    try:
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str).astimezone(LOCAL_TZ)
    except Exception:
        return None

def is_today(ts_str):
    dt = parse_ts(ts_str)
    return dt is not None and dt.date() == today_date()

def is_this_week(ts_str):
    dt = parse_ts(ts_str)
    return dt is not None and dt >= week_start()

# ── Pipeline API ───────────────────────────────────────────────────────────────

def get_pipeline_stats():
    """Fetch pipeline/lead staging stats. Returns (stats_dict, error_string)."""
    if not PIPELINE_AUTH:
        return None, "PIPELINE_AUTH_TOKEN not configured"
    
    data = api_get(f"{PIPELINE_API_URL}?page=1&limit=200", PIPELINE_AUTH)
    if "_error" in data:
        return None, data["_error"]
    
    prospects = data.get("prospects", [])
    stats = data.get("stats", {})
    
    today_total = 0
    today_approved = 0
    today_sent = 0
    
    for p in prospects:
        created = p.get("queued_at") or p.get("created_at") or ""
        if is_today(created):
            today_total += 1
            status = (p.get("status") or "").lower()
            if status == "approved":
                today_approved += 1
            elif status == "sent":
                today_sent += 1
    
    return {
        "today_total": today_total,
        "today_approved": today_approved,
        "today_sent": today_sent,
        "total": stats.get("total", len(prospects)),
    }, None

def get_recruiting_stats():
    """Fetch candidate sourcing stats with pagination. Returns (stats_dict, error_string)."""
    if not RECRUITING_AUTH:
        return None, "RECRUITING_AUTH_TOKEN not configured"
    
    data = api_get(f"{RECRUITING_API_URL}?page=1&limit=50", RECRUITING_AUTH)
    if "_error" in data:
        return None, data["_error"]
    
    stats = data.get("stats", {})
    pagination = data.get("pagination", {})
    total_pages = pagination.get("total_pages", 1)
    
    today_total = 0
    week_total = 0
    
    def count_page(candidates):
        nonlocal today_total, week_total
        for c in candidates:
            created = c.get("created_at") or c.get("createdAt") or ""
            if is_today(created):
                today_total += 1
            if is_this_week(created):
                week_total += 1
    
    count_page(data.get("candidates", []))
    
    # Paginate (stop early when we hit records older than this week)
    max_pages = min(total_pages, 7)
    for page in range(2, max_pages + 1):
        pdata = api_get(f"{RECRUITING_API_URL}?page={page}&limit=50", RECRUITING_AUTH)
        if "_error" in pdata:
            break
        candidates = pdata.get("candidates", [])
        if not candidates:
            break
        last = candidates[-1]
        last_ts = parse_ts(last.get("created_at") or "")
        count_page(candidates)
        if last_ts and last_ts < week_start():
            break
    
    return {
        "today_total": today_total,
        "week_total": week_total,
        "stats_total": stats.get("total", "?"),
        "stats_in_pipeline": stats.get("in_pipeline", "?"),
        "stats_approved": stats.get("approved", "?"),
        "stats_meetings": stats.get("meetings", "?"),
    }, None

# ── Email Campaign Status ─────────────────────────────────────────────────────

NOT_SENDING_LABELS = {0: "sending", 2: "daily limit hit", 4: "issue"}

def get_campaign_status(campaign_id, name):
    """Check single email campaign health."""
    if not EMAIL_AUTH:
        return {"name": name, "error": "EMAIL_AUTH_TOKEN not configured", "sending": False, "active": False, "daily_limit": 0}
    
    data = api_get(f"{EMAIL_API_URL}/{campaign_id}", EMAIL_AUTH)
    if "_error" in data:
        return {"name": name, "error": data["_error"], "sending": False, "active": False, "daily_limit": 0}
    
    status = data.get("status", -1)
    ns_status = data.get("not_sending_status", 0)
    daily_limit = data.get("daily_limit", 0)
    
    return {
        "name": name,
        "active": status == 1,
        "ns_status": ns_status,
        "ns_label": NOT_SENDING_LABELS.get(ns_status, f"unknown({ns_status})"),
        "daily_limit": daily_limit,
        "sending": status == 1 and ns_status == 0,
    }

def get_campaigns_summary(campaigns_dict):
    """Get aggregate health for a set of campaigns."""
    if not campaigns_dict:
        return {"results": [], "sending_count": 0, "total": 0, "capacity": 0, "any_issue": False, "all_paused": True}
    
    results = [get_campaign_status(cid, name) for name, cid in campaigns_dict.items()]
    sending_count = sum(1 for r in results if r.get("sending"))
    total_capacity = sum(r.get("daily_limit", 0) for r in results if r.get("sending"))
    any_issue = any(r.get("ns_status", 0) in (2, 4) for r in results)
    all_paused = all(not r.get("active") for r in results)
    
    return {
        "results": results,
        "sending_count": sending_count,
        "total": len(results),
        "capacity": total_capacity,
        "any_issue": any_issue,
        "all_paused": all_paused,
    }

# ── Pacing Logic ───────────────────────────────────────────────────────────────

def pace_icon(issues):
    if issues == 0:   return "🟢"
    elif issues == 1: return "🟡"
    else:             return "🔴"

def pipeline_pace(today_total, campaign_summary):
    issues = 0
    if today_total == 0: issues += 2
    elif today_total < DAILY_LEAD_TARGET // 2: issues += 1
    if campaign_summary["sending_count"] == 0: issues += 2
    elif campaign_summary["any_issue"]: issues += 1
    return pace_icon(issues)

def recruiting_pace(week_total, campaign_summary):
    issues = 0
    if week_total < WEEKLY_CANDIDATE_TARGET // 4: issues += 2
    elif week_total < WEEKLY_CANDIDATE_TARGET // 2: issues += 1
    if campaign_summary["sending_count"] == 0: issues += 2
    elif campaign_summary["any_issue"]: issues += 1
    return pace_icon(issues)

def campaign_line(summary):
    if summary["all_paused"]:
        return "🔴 all paused | 0 emails/day"
    elif summary["sending_count"] == 0:
        return "🔴 not sending | 0 emails/day"
    elif summary["any_issue"]:
        return f"🟡 {summary['sending_count']}/{summary['total']} sending | {summary['capacity']:,} emails/day"
    else:
        return f"🟢 {summary['sending_count']}/{summary['total']} sending | {summary['capacity']:,} emails/day"

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Campaign pacing alert")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    now = now_local()
    date_str = now.strftime("%a %b %-d")
    time_str = now.strftime("%-I:%M %p") + " " + TZ_LABEL
    
    alerts = []
    
    # Fetch data
    pipeline_stats, pipeline_err = get_pipeline_stats()
    recruiting_stats, recruiting_err = get_recruiting_stats()
    outbound_summary = get_campaigns_summary(OUTBOUND_CAMPAIGNS)
    recruiting_campaign_summary = get_campaigns_summary(RECRUITING_CAMPAIGNS)
    
    if args.json:
        output = {
            "timestamp": now.isoformat(),
            "pipeline": pipeline_stats or {"error": pipeline_err},
            "recruiting": recruiting_stats or {"error": recruiting_err},
            "outbound_campaigns": outbound_summary,
            "recruiting_campaigns": recruiting_campaign_summary,
        }
        print(json.dumps(output, indent=2, default=str))
        has_alerts = pipeline_err or recruiting_err or outbound_summary["any_issue"]
        sys.exit(1 if has_alerts else 0)
    
    lines = [f"⚠️ *Pacing Alert — {date_str} {time_str}*", ""]
    
    # ── Pipeline / Outbound ──
    if pipeline_err:
        p_icon = "🔴"
        p_line = f"API error: {pipeline_err}"
        alerts.append(f"Pipeline API error: {pipeline_err}")
    else:
        pt = pipeline_stats["today_total"]
        pa = pipeline_stats["today_approved"]
        ps = pipeline_stats["today_sent"]
        p_icon = pipeline_pace(pt, outbound_summary)
        p_line = f"{pt} leads staged today | {pa} approved | {ps} sent"
        if pt == 0:
            alerts.append("Pipeline: 0 leads staged today")
    
    lines.append(f"{p_icon} 📧 *Outbound Pipeline:*")
    lines.append(f"• {p_line}")
    lines.append(f"• Campaigns: {campaign_line(outbound_summary)}")
    lines.append("")
    
    # ── Recruiting / Sourcing ──
    if recruiting_err:
        r_icon = "🔴"
        r_line = f"API error: {recruiting_err}"
        alerts.append(f"Recruiting API error: {recruiting_err}")
    else:
        rt = recruiting_stats["today_total"]
        rw = recruiting_stats["week_total"]
        r_icon = recruiting_pace(rw, recruiting_campaign_summary)
        r_line = f"{rt} candidates added today | {rw} this week | target: {WEEKLY_CANDIDATE_TARGET}/week"
        if rw < WEEKLY_CANDIDATE_TARGET // 4:
            alerts.append(f"Recruiting: only {rw} candidates this week (target {WEEKLY_CANDIDATE_TARGET})")
    
    lines.append(f"{r_icon} 🔍 *Recruiting Pipeline:*")
    lines.append(f"• {r_line}")
    lines.append(f"• Campaigns: {campaign_line(recruiting_campaign_summary)}")
    
    print("\n".join(lines))
    
    if alerts:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
