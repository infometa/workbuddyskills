#!/usr/bin/env python3
"""
instantly-audit.py
Pulls campaign data, account inventory, and warmup scores from the Instantly v2 API.

Usage:
    python3 instantly-audit.py --api-key YOUR_KEY
    python3 instantly-audit.py  # uses INSTANTLY_API_KEY env var
    python3 instantly-audit.py --api-key YOUR_KEY --output report.md
    python3 instantly-audit.py --api-key YOUR_KEY --json  # raw JSON output

Instantly v2 API docs: https://developer.instantly.ai/
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Run: pip install requests")
    sys.exit(1)

BASE_URL = "https://api.instantly.ai/api/v2"


def get_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def paginate(url: str, headers: dict, params: dict = None, limit: int = 100) -> list:
    """Handle Instantly v2 cursor-based pagination."""
    results = []
    params = params or {}
    params["limit"] = limit
    starting_after = None

    while True:
        if starting_after:
            params["starting_after"] = starting_after

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Request failed: {e}")
            break

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 5))
            print(f"  ⏳ Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            continue

        if resp.status_code == 401:
            print("  🔴 Authentication failed. Check your API key.")
            sys.exit(1)

        if not resp.ok:
            print(f"  ⚠️  API error {resp.status_code}: {resp.text[:200]}")
            break

        data = resp.json()
        items = data.get("items", data if isinstance(data, list) else [])
        results.extend(items)

        next_cursor = data.get("next_starting_after") or data.get("next_cursor")
        if not next_cursor or len(items) < limit:
            break
        starting_after = next_cursor

    return results


def fetch_campaigns(headers: dict) -> list:
    """Fetch all campaigns with analytics."""
    print("📋 Fetching campaigns...")
    campaigns = paginate(f"{BASE_URL}/campaigns", headers)
    print(f"   Found {len(campaigns)} campaigns")
    return campaigns


def fetch_campaign_analytics(headers: dict, campaign_ids: list) -> dict:
    """Fetch analytics summary for campaigns."""
    if not campaign_ids:
        return {}

    print("📊 Fetching campaign analytics...")
    analytics = {}

    for i in range(0, len(campaign_ids), 10):
        batch = campaign_ids[i:i+10]
        try:
            resp = requests.get(
                f"{BASE_URL}/campaigns/analytics/overview",
                headers=headers,
                params={"campaign_id": batch},
                timeout=30,
            )
            if resp.ok:
                data = resp.json()
                if isinstance(data, dict):
                    analytics.update(data)
                elif isinstance(data, list):
                    for item in data:
                        cid = item.get("campaign_id") or item.get("id")
                        if cid:
                            analytics[cid] = item
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Analytics fetch failed for batch: {e}")

        time.sleep(0.3)

    return analytics


def fetch_accounts(headers: dict) -> list:
    """Fetch all sending accounts with warmup status."""
    print("📧 Fetching sending accounts...")
    accounts = paginate(f"{BASE_URL}/accounts", headers)
    print(f"   Found {len(accounts)} accounts")
    return accounts


def fetch_warmup_scores(headers: dict, account_emails: list) -> dict:
    """Fetch warmup analytics for accounts."""
    if not account_emails:
        return {}

    print("🔥 Fetching warmup scores...")
    warmup_data = {}

    for email in account_emails:
        try:
            resp = requests.get(
                f"{BASE_URL}/accounts/{email}/warmup/analytics",
                headers=headers,
                timeout=30,
            )
            if resp.ok:
                warmup_data[email] = resp.json()
            elif resp.status_code == 404:
                warmup_data[email] = {"score": None, "status": "no_warmup_data"}
            time.sleep(0.1)
        except requests.exceptions.RequestException:
            warmup_data[email] = {"score": None, "status": "fetch_error"}

    return warmup_data


def assess_warmup_readiness(account: dict, warmup: dict) -> tuple:
    """Return (ready: bool, issues: list) for an account."""
    issues = []

    score = (warmup.get("warmup_score") or warmup.get("score")
             or account.get("stat_warmup_score") or account.get("warmup_score"))
    if score is None:
        issues.append("No warmup data available")
    elif score < 80:
        issues.append(f"Warmup score {score} < 80 (minimum required)")

    warmup_start = account.get("warmup_start_date") or account.get("created_at")
    if warmup_start:
        try:
            start_dt = datetime.fromisoformat(warmup_start.replace("Z", "+00:00"))
            days_warmed = (datetime.now(start_dt.tzinfo) - start_dt).days
            if days_warmed < 14:
                issues.append(f"Only {days_warmed} days warmed (need 14+)")
        except (ValueError, AttributeError):
            pass

    status = str(account.get("status", "")).lower()
    if status in ("paused", "error", "suspended", "disabled"):
        issues.append(f"Account status: {status}")

    ready = len(issues) == 0
    return ready, issues


def format_pct(value, total, decimals=1) -> str:
    if not total:
        return "N/A"
    return f"{(value / total * 100):.{decimals}f}%"


def generate_report(campaigns: list, analytics: dict, accounts: list, warmup_scores: dict) -> str:
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append(f"# Instantly Audit Report")
    lines.append(f"Generated: {now}\n")

    # ── Account Inventory ──
    lines.append("## Sending Account Inventory\n")

    ready_accounts = []
    not_ready_accounts = []

    for acct in accounts:
        email = acct.get("email", "unknown")
        warmup = warmup_scores.get(email, {})
        ready, issues = assess_warmup_readiness(acct, warmup)
        score = (warmup.get("warmup_score") or warmup.get("score")
                 or acct.get("stat_warmup_score") or acct.get("warmup_score") or "N/A")
        daily_limit = acct.get("sending_limit") or acct.get("daily_limit", 30)

        row = {
            "email": email,
            "status": acct.get("status", "unknown"),
            "warmup_score": score,
            "daily_limit": daily_limit,
            "ready": ready,
            "issues": issues,
        }

        if ready:
            ready_accounts.append(row)
        else:
            not_ready_accounts.append(row)

    total_accounts = len(accounts)
    total_ready = len(ready_accounts)

    lines.append(f"**Total accounts:** {total_accounts}")
    lines.append(f"**Ready to send:** {total_ready} ✅")
    lines.append(f"**Not ready:** {len(not_ready_accounts)} ⚠️\n")

    if ready_accounts:
        conservative_daily = total_ready * 30
        aggressive_daily = total_ready * 50
        conservative_monthly = conservative_daily * 22
        aggressive_monthly = aggressive_daily * 22
        lines.append("### Capacity Math (ready accounts only)")
        lines.append(f"- Conservative (30/day/account): **{conservative_daily:,}/day → {conservative_monthly:,}/month**")
        lines.append(f"- Aggressive (50/day/account): **{aggressive_daily:,}/day → {aggressive_monthly:,}/month**\n")

    lines.append("### ✅ Ready Accounts")
    if ready_accounts:
        lines.append("| Account | Status | Warmup Score | Daily Limit |")
        lines.append("|---------|--------|-------------|------------|")
        for a in ready_accounts:
            lines.append(f"| {a['email']} | {a['status']} | {a['warmup_score']} | {a['daily_limit']} |")
    else:
        lines.append("_None — no accounts meet warmup requirements_")

    lines.append("\n### ⚠️ Not Ready Accounts")
    if not_ready_accounts:
        lines.append("| Account | Status | Warmup Score | Issues |")
        lines.append("|---------|--------|-------------|--------|")
        for a in not_ready_accounts:
            issues_str = "; ".join(a["issues"]) if a["issues"] else "unknown"
            lines.append(f"| {a['email']} | {a['status']} | {a['warmup_score']} | {issues_str} |")
    else:
        lines.append("_None — all accounts are ready_")

    # ── Campaign Performance ──
    lines.append("\n---\n## Campaign Performance\n")
    lines.append(f"**Total campaigns:** {len(campaigns)}\n")

    if not campaigns:
        lines.append("_No campaigns found_")
    else:
        lines.append("| Campaign | Status | Sent | Open Rate | Reply Rate | Positive Reply Rate |")
        lines.append("|----------|--------|------|-----------|-----------|-------------------|")

        for c in campaigns:
            cid = c.get("id", "")
            name = c.get("name", "Unnamed")[:50]
            status = c.get("status", "unknown")

            a = analytics.get(cid, {})
            sent = a.get("emails_sent", 0) or c.get("emails_sent", 0)
            opened = a.get("emails_opened", 0)
            replied = a.get("emails_replied", 0)
            positive = a.get("positive_replies", 0)

            open_rate = format_pct(opened, sent)
            reply_rate = format_pct(replied, sent)
            pos_rate = format_pct(positive, sent)

            lines.append(f"| {name} | {status} | {sent:,} | {open_rate} | {reply_rate} | {pos_rate} |")

    # ── Flags & Recommendations ──
    lines.append("\n---\n## Flags & Recommendations\n")

    flags = []

    if total_ready == 0:
        flags.append("🔴 **BLOCKER:** No accounts are ready to send. All fail warmup requirements. Do not launch campaigns.")
    elif total_ready < 3:
        flags.append(f"⚠️ Only {total_ready} account(s) ready. Low volume capacity. Consider warming more accounts.")

    low_open = []
    low_reply = []
    for c in campaigns:
        cid = c.get("id", "")
        a = analytics.get(cid, {})
        sent = a.get("emails_sent", 0)
        if sent < 50:
            continue
        opened = a.get("emails_opened", 0)
        replied = a.get("emails_replied", 0)
        open_pct = (opened / sent * 100) if sent else 0
        reply_pct = (replied / sent * 100) if sent else 0
        if open_pct < 40:
            low_open.append(c.get("name", cid))
        if reply_pct < 3:
            low_reply.append(c.get("name", cid))

    if low_open:
        flags.append(f"⚠️ Low open rate (<40%) campaigns (subject line issue): {', '.join(low_open[:5])}")
    if low_reply:
        flags.append(f"⚠️ Low reply rate (<3%) campaigns (copy/offer issue): {', '.join(low_reply[:5])}")

    if not flags:
        flags.append("✅ No critical flags detected.")

    for f in flags:
        lines.append(f"- {f}")

    lines.append(f"\n---\n_Audit complete. {total_accounts} accounts, {len(campaigns)} campaigns analyzed._")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Instantly v2 API Audit Tool")
    parser.add_argument("--api-key", help="Instantly API key (or set INSTANTLY_API_KEY env var)")
    parser.add_argument("--output", help="Write report to this file (default: print to stdout)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of markdown report")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("INSTANTLY_API_KEY")
    if not api_key:
        api_key = input("Instantly API key: ").strip()
    if not api_key:
        print("ERROR: API key required. Set INSTANTLY_API_KEY env var or pass --api-key.")
        sys.exit(1)

    headers = get_headers(api_key)

    print(f"\n🔍 Starting Instantly audit...\n")

    campaigns = fetch_campaigns(headers)
    campaign_ids = [c.get("id") for c in campaigns if c.get("id")]
    analytics = fetch_campaign_analytics(headers, campaign_ids)

    accounts = fetch_accounts(headers)
    account_emails = [a.get("email") for a in accounts if a.get("email")]
    warmup_scores = fetch_warmup_scores(headers, account_emails)

    if args.json:
        output = json.dumps({
            "campaigns": campaigns,
            "analytics": analytics,
            "accounts": accounts,
            "warmup_scores": warmup_scores,
        }, indent=2, default=str)
    else:
        output = generate_report(campaigns, analytics, accounts, warmup_scores)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"\n✅ Report written to: {args.output}")
    else:
        print("\n" + output)


if __name__ == "__main__":
    main()
