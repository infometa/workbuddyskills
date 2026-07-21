#!/usr/bin/env python3
"""
Deal Resurrector v2 — Three intelligence layers on dead deals:
  Layer 1: Time Decay Scoring (composite score with configurable decay windows)
  Layer 2: POC Expansion (verify contacts, find replacements)
  Layer 3: Follow the Champion (track departed POCs to new companies)

Pulls closed-lost deals from HubSpot, scores them using a composite formula
(time decay + deal value + loss reason + engagement triggers), then generates
personalized revival emails per loss reason category.

Usage:
    python3 deal_resurrector.py --top 10 --dry-run
    python3 deal_resurrector.py --top 5 --include-champion
    python3 deal_resurrector.py --add-exclusion "Acme Corp"
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# ─── Configuration ───────────────────────────────────────────────────────────
BASE_DIR = Path(os.environ.get("BASE_DIR", Path(__file__).resolve().parent))
DATA_DIR = BASE_DIR / "data"
EXCLUSIONS_FILE = DATA_DIR / "resurrector-exclusions.json"
OUTPUT_FILE = DATA_DIR / "deal-resurrector-latest.json"

# HubSpot API
HUBSPOT_BASE_URL = "https://api.hubapi.com"
HUBSPOT_TOKEN = os.environ.get("HUBSPOT_API_KEY", "")

# ─── Closed-Lost Stage IDs ──────────────────────────────────────────────────
# Map your HubSpot closed-lost stage IDs to pipeline names.
# Find these in HubSpot → Settings → Objects → Deals → Pipelines
CLOSED_LOST_STAGES = {
    # "stage_id_here": "Pipeline Name",
    # Example:
    # "1079884213": "Enterprise Pipeline",
    # "960522377": "ABM Pipeline",
}

# ─── HubSpot Properties to Fetch ────────────────────────────────────────────
DEAL_PROPERTIES = [
    "dealname", "amount", "closedate", "dealstage",
    "closed_lost_reason", "hs_closed_amount", "pipeline",
    "hubspot_owner_id", "notes_last_updated",
]
CONTACT_PROPERTIES = [
    "firstname", "lastname", "email", "jobtitle", "company",
    "hs_last_sales_activity_date", "notes_last_updated",
    "hs_email_last_open_date", "hs_email_last_click_date",
    "hs_analytics_last_visit_timestamp", "hs_analytics_num_page_views",
    "num_associated_deals", "recent_conversion_event_name",
]
COMPANY_PROPERTIES = [
    "name", "domain", "industry", "numberofemployees",
    "annualrevenue", "hs_last_sales_activity_date",
    "notes_last_updated", "num_associated_deals",
    "hs_analytics_last_visit_timestamp",
]

# ─── Time Decay Windows ─────────────────────────────────────────────────────
# (min_days, max_days, weight)
# Deals in the 60-90 day window get full weight; older deals decay.
DECAY_WINDOWS = [
    (60, 90, 1.0),    # Sweet spot — enough time has passed, still fresh
    (91, 180, 0.8),   # Good window
    (181, 365, 0.6),  # Getting stale but still viable
    (366, 540, 0.4),  # Long shot unless trigger present
    (541, 99999, 0.2),  # Only if engagement trigger detected
]

# ─── Loss Reason → Bonus Multiplier ─────────────────────────────────────────
# Deals lost to "timing" are more likely to convert than "bad fit".
LOSS_REASON_BONUS = {
    "timing": 1.3,
    "not ready": 1.25,
    "budget": 1.15,
    "price": 1.1,
    "internal": 1.05,
    "no decision": 1.0,
    "competitor": 0.7,
    "no need": 0.5,
    "bad fit": 0.3,
}

# Rate limit delay between HubSpot API calls (seconds)
SEARCH_DELAY = float(os.environ.get("HUBSPOT_RATE_DELAY", "1.5"))

# ─── Your Company Info (for email templates) ────────────────────────────────
YOUR_COMPANY_NAME = os.environ.get("YOUR_COMPANY_NAME", "Your Company")
YOUR_SENDER_NAME = os.environ.get("YOUR_SENDER_NAME", "Your Name")
YOUR_SENDER_TITLE = os.environ.get("YOUR_SENDER_TITLE", "CEO")
# A brief value prop to include in emails
YOUR_VALUE_PROP = os.environ.get("YOUR_VALUE_PROP",
    "We've built new capabilities since we last talked that I think you'd find interesting.")


# ─── Exclusion List ──────────────────────────────────────────────────────────

def load_exclusions() -> set:
    """Load excluded company names (lowercased) from the exclusions file."""
    if not EXCLUSIONS_FILE.exists():
        return set()
    try:
        data = json.loads(EXCLUSIONS_FILE.read_text())
        return {e["company"].lower() for e in data.get("excluded_deals", [])}
    except Exception as ex:
        print(f"⚠️ Could not load exclusions: {ex}", file=sys.stderr)
        return set()


def add_exclusion(company: str, deal_id: str = "", reason: str = "manually_excluded") -> None:
    """Append a company to the exclusions file."""
    data = {"excluded_deals": []}
    if EXCLUSIONS_FILE.exists():
        try:
            data = json.loads(EXCLUSIONS_FILE.read_text())
        except Exception:
            pass
    existing = {e["company"].lower() for e in data["excluded_deals"]}
    if company.lower() in existing:
        print(f"ℹ️  {company} is already excluded.")
        return
    data["excluded_deals"].append({
        "deal_id": deal_id or company.lower().replace(" ", "-"),
        "company": company,
        "reason": reason,
        "excluded_date": datetime.now().strftime("%Y-%m-%d"),
    })
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXCLUSIONS_FILE.write_text(json.dumps(data, indent=2))
    print(f"✅ Added {company} to exclusion list")


# ─── HubSpot Client ─────────────────────────────────────────────────────────

class HubSpotClient:
    def __init__(self, token: str):
        self.token = token.strip()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        })
        self._rate_wait = 0.12

    def _request(self, method, path, **kwargs):
        url = f"{HUBSPOT_BASE_URL}{path}"
        for attempt in range(4):
            resp = self.session.request(method, url, **kwargs)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 2))
                print(f"  ⏳ Rate limited, waiting {wait}s…", file=sys.stderr)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            time.sleep(self._rate_wait)
            return resp.json()
        raise RuntimeError(f"Too many retries for {path}")

    def get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)

    def search_closed_lost_deals(self, since_date: str):
        """Search for all closed-lost deals across configured pipelines."""
        all_deals = []
        for stage_id in CLOSED_LOST_STAGES:
            all_deals.extend(self._search_by_stage(stage_id, since_date))
        return all_deals

    def _search_by_stage(self, stage_id, since_date):
        deals = []
        after = None
        while True:
            body = {
                "filterGroups": [{"filters": [
                    {"propertyName": "dealstage", "operator": "EQ", "value": stage_id},
                    {"propertyName": "closedate", "operator": "GTE", "value": since_date},
                ]}],
                "properties": DEAL_PROPERTIES,
                "sorts": [{"propertyName": "closedate", "direction": "DESCENDING"}],
                "limit": 100,
            }
            if after:
                body["after"] = after
            data = self.post("/crm/v3/objects/deals/search", json=body)
            deals.extend(data.get("results", []))
            paging = data.get("paging", {}).get("next")
            if paging:
                after = paging["after"]
            else:
                break
        return deals

    def get_deal_associations(self, deal_id, to_type="contacts"):
        try:
            data = self.get(f"/crm/v4/objects/deals/{deal_id}/associations/{to_type}")
            return data.get("results", [])
        except Exception:
            return []

    def get_contact(self, contact_id):
        try:
            return self.get(
                f"/crm/v3/objects/contacts/{contact_id}",
                params={"properties": ",".join(CONTACT_PROPERTIES)},
            )
        except Exception:
            return None

    def get_company_for_contact(self, contact_id):
        try:
            assocs = self.get(f"/crm/v4/objects/contacts/{contact_id}/associations/companies")
            results = assocs.get("results", [])
            if not results:
                return None
            company_id = results[0].get("toObjectId")
            return self.get(
                f"/crm/v3/objects/companies/{company_id}",
                params={"properties": ",".join(COMPANY_PROPERTIES)},
            )
        except Exception:
            return None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def parse_ts(val):
    """Parse a timestamp value (epoch ms or ISO string) to datetime."""
    if not val:
        return None
    try:
        if isinstance(val, (int, float)) or (isinstance(val, str) and val.isdigit()):
            return datetime.fromtimestamp(int(val) / 1000, tz=timezone.utc)
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except Exception:
        return None


# ─── Layer 1: Time Decay Scoring ────────────────────────────────────────────

def compute_time_decay_score(days_since_close: int, deal_value: float,
                              max_deal_value: float, loss_reason: str,
                              has_trigger: bool) -> dict:
    """Compute composite score (0-100) using additive formula:
      Time component:    up to 35 pts (decay weight × 35)
      Value component:   up to 30 pts (normalized value × 30)
      Reason component:  up to 20 pts (loss reason bonus × 20)
      Trigger component: up to 15 pts (engagement signals)
    """
    # Time decay weight
    time_weight = 0.0
    for lo, hi, weight in DECAY_WINDOWS:
        if lo <= days_since_close <= hi:
            time_weight = weight
            break

    # Too fresh (<60 days) — penalize (deal is still raw)
    if days_since_close < 60:
        time_weight = 0.2

    # Very old deals only score if trigger present
    if days_since_close > 540 and not has_trigger:
        time_weight = 0.0

    # Normalize deal value (0-1)
    value_norm = min(deal_value / max(max_deal_value, 1), 1.0)

    # Loss reason bonus
    reason_lower = (loss_reason or "").lower()
    reason_score = 0.5  # default for unknown reasons
    for keyword, bonus in LOSS_REASON_BONUS.items():
        if keyword in reason_lower:
            reason_score = min(bonus, 1.0)
            break

    # Trigger bonus
    trigger_pts = 15.0 if has_trigger else 0.0

    # Additive composite
    time_pts = time_weight * 35
    value_pts = value_norm * 30
    reason_pts = reason_score * 20

    composite = min(100, round(time_pts + value_pts + reason_pts + trigger_pts))

    return {
        "time_decay_weight": time_weight,
        "value_normalized": round(value_norm, 3),
        "trigger_bonus": round(reason_score, 2),
        "composite_score": composite,
    }


# ─── Email Generation ───────────────────────────────────────────────────────

def _random_cta():
    return random.choice([
        "Worth revisiting?",
        "Open to a quick catch-up?",
        "Curious if the timing is better now?",
        "Worth 15 min to compare notes?",
        "Any interest in reconnecting?",
        "Make sense to chat again?",
    ])


def _random_signoff():
    return random.choice([
        YOUR_SENDER_NAME,
        f"{YOUR_SENDER_NAME}\n{YOUR_SENDER_TITLE}, {YOUR_COMPANY_NAME}",
        f"- {YOUR_SENDER_NAME}",
    ])


# Revival email angles — rotated based on loss reason
REVIVAL_ANGLES = {
    "timing": [
        {
            "subject": "{first}, checking back in",
            "hook": "When we last talked, you mentioned the timing wasn't right. "
                    "It's been {months} months. Figured I'd check in rather than assume.",
        },
        {
            "subject": "been a while, {first}",
            "hook": "It's been {months} months since we last connected on {company}. "
                    "A lot has probably changed on both sides.",
        },
    ],
    "competitor": [
        {
            "subject": "how's the current setup, {first}?",
            "hook": "Last time, you went with another partner. Totally respect that. "
                    "Curious how it's going and whether there's room to compare notes.",
        },
    ],
    "budget": [
        {
            "subject": "new pricing options",
            "hook": "Pricing was the sticking point last time. We've restructured since then. "
                    "We now offer performance-based models where you pay for results.",
        },
    ],
    "internal": [
        {
            "subject": "{first}, dust settled yet?",
            "hook": "Last time, internal changes at {company} put things on hold. "
                    "Wanted to see if the original initiative is back on the table.",
        },
    ],
    "ghost": [
        {
            "subject": "{first}, one more try",
            "hook": "We connected {months} months ago but lost touch. No hard feelings. "
                    "Just wanted to resurface in case the need is still there.",
        },
    ],
    "default": [
        {
            "subject": "quick update for {first}",
            "hook": "We connected {months} months ago about growing {company}. "
                    "A lot has changed on our end since then.",
        },
    ],
}


def _categorize_loss_reason(loss_reason):
    """Map a free-text loss reason to a category for email angle selection."""
    lr = (loss_reason or "").lower()
    if any(w in lr for w in ["timing", "not ready", "circle back", "follow up"]):
        return "timing"
    if any(w in lr for w in ["competitor", "chose", "existing relationship"]):
        return "competitor"
    if any(w in lr for w in ["budget", "price", "pricing", "cost"]):
        return "budget"
    if any(w in lr for w in ["internal", "restructur", "reorg", "change"]):
        return "internal"
    if any(w in lr for w in ["ghost", "unresponsive", "no response"]):
        return "ghost"
    return "default"


def draft_revival_email(contact_name, company_name, deal_value, loss_reason,
                         days_since_close, contact_title=""):
    """Draft a personalized revival email based on loss reason category."""
    first = contact_name.split()[0] if contact_name else "there"
    months = days_since_close // 30
    category = _categorize_loss_reason(loss_reason)

    angle = random.choice(REVIVAL_ANGLES.get(category, REVIVAL_ANGLES["default"]))
    subject = angle["subject"].format(first=first, company=company_name, months=months)
    hook = angle["hook"].format(first=first, company=company_name, months=months)

    cta = _random_cta()
    signoff = _random_signoff()

    body = f"Hey {first},\n\n{hook}\n\n{YOUR_VALUE_PROP}\n\n{cta}\n\n{signoff}"

    return {"subject": subject, "body": body}


def draft_replacement_email(replacement_name, company_name, original_contact):
    """Draft email to a replacement POC at the same company."""
    first = replacement_name.split()[0] if replacement_name else "there"
    orig_first = original_contact.split()[0] if original_contact else "your predecessor"
    cta = _random_cta()
    signoff = _random_signoff()

    return {
        "subject": f"picking up where {orig_first} left off at {company_name}",
        "body": (
            f"Hey {first},\n\n"
            f"We were in conversation with {original_contact} about growth for "
            f"{company_name} before the team change.\n\n"
            f"{YOUR_VALUE_PROP}\n\n"
            f"{cta}\n\n{signoff}"
        ),
    }


def draft_champion_email(champion_name, new_company, new_title, old_company):
    """Draft email to a champion who moved to a new company."""
    first = champion_name.split()[0] if champion_name else "there"
    cta = _random_cta()
    signoff = _random_signoff()

    return {
        "subject": f"congrats on the move, {first}",
        "body": (
            f"Hey {first},\n\n"
            f"Saw you moved to {new_company}. Congrats on the {new_title} role.\n\n"
            f"We had a great conversation when you were at {old_company}. "
            f"Now that you're settling in, I'd love to show you what we can do "
            f"for {new_company}.\n\n"
            f"{cta}\n\n{signoff}"
        ),
    }


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Deal Resurrector v2 — Time Decay + POC Expansion + Champion Tracking"
    )
    parser.add_argument("--top", type=int, default=10, help="Number of top deals (default: 10)")
    parser.add_argument("--min-score", type=int, default=40, help="Minimum composite score (default: 40)")
    parser.add_argument("--min-deal-value", type=float, default=5000, help="Min deal value (default: 5000)")
    parser.add_argument("--months", type=int, default=24, help="Look back N months (default: 24)")
    parser.add_argument("--include-champion", action="store_true", help="Enable Layer 3: Follow the Champion")
    parser.add_argument("--dry-run", action="store_true", help="Print results, don't save")
    parser.add_argument("--skip-search", action="store_true", help="Skip web searches (faster)")
    parser.add_argument("--add-exclusion", metavar="COMPANY", help="Add a company to exclusion list and exit")
    args = parser.parse_args()

    if args.add_exclusion:
        add_exclusion(args.add_exclusion)
        return

    if not HUBSPOT_TOKEN:
        print("❌ HUBSPOT_API_KEY environment variable not set.", file=sys.stderr)
        print("   Set it: export HUBSPOT_API_KEY='your-token-here'", file=sys.stderr)
        sys.exit(1)

    print("🔥 Deal Resurrector v2")
    print(f"   Layers: Time Decay + POC Expansion"
          f"{ ' + Champion Tracking' if args.include_champion else ''}")
    print(f"   Top {args.top} | min score {args.min_score} | min value ${args.min_deal_value:,.0f}")
    print()

    excluded_companies = load_exclusions()
    if excluded_companies:
        print(f"🚫 Exclusion list: {len(excluded_companies)} companies will be skipped")
    print()

    client = HubSpotClient(HUBSPOT_TOKEN)

    # Step 1: Pull closed-lost deals
    since = (datetime.now(timezone.utc) - timedelta(days=args.months * 30)).strftime("%Y-%m-%d")
    print(f"📥 Fetching closed-lost deals since {since}…")
    deals = client.search_closed_lost_deals(since)
    print(f"   Found {len(deals)} closed-lost deals")

    # Filter by value
    filtered = []
    for d in deals:
        amt = float(d["properties"].get("amount") or 0)
        if amt >= args.min_deal_value:
            filtered.append(d)
    print(f"   {len(filtered)} deals above ${args.min_deal_value:,.0f}")

    # Filter exclusions
    if excluded_companies:
        pre = len(filtered)
        filtered = [
            d for d in filtered
            if d["properties"].get("dealname", "").lower() not in excluded_companies
            and not any(excl in d["properties"].get("dealname", "").lower()
                        for excl in excluded_companies)
        ]
        excluded_count = pre - len(filtered)
        if excluded_count:
            print(f"   🚫 {excluded_count} deal(s) excluded")

    if not filtered:
        print("No deals to process. Exiting.")
        return

    max_value = max(float(d["properties"].get("amount") or 0) for d in filtered)
    now = datetime.now(timezone.utc)

    # Step 2: Score and enrich
    results = []
    for i, deal in enumerate(filtered):
        dp = deal["properties"]
        deal_id = deal["id"]
        deal_name = dp.get("dealname", "Unknown")
        amount = float(dp.get("amount") or 0)
        loss_reason = dp.get("closed_lost_reason") or "Unknown"
        close_dt = parse_ts(dp.get("closedate"))
        days_since = (now - close_dt).days if close_dt else 999

        print(f"  [{i+1}/{len(filtered)}] {deal_name} (${amount:,.0f}, {days_since}d ago)…",
              end="", flush=True)

        # Get primary contact
        assocs = client.get_deal_associations(deal_id, "contacts")
        contact_name = "Unknown"
        contact_email = ""
        contact_title = ""
        company_name = deal_name
        contact_data = None

        if assocs:
            cid = str(assocs[0].get("toObjectId"))
            contact_data = client.get_contact(cid)
            if contact_data:
                cp = contact_data.get("properties", {})
                fn = cp.get("firstname") or ""
                ln = cp.get("lastname") or ""
                contact_name = f"{fn} {ln}".strip() or "Unknown"
                contact_email = cp.get("email", "")
                contact_title = cp.get("jobtitle", "")
                company_name = cp.get("company") or company_name

                company_data = client.get_company_for_contact(cid)
                if company_data:
                    company_name = company_data.get("properties", {}).get("name") or company_name

        # Detect engagement triggers
        triggers = []
        if contact_data and contact_data.get("properties"):
            cp = contact_data["properties"]
            if parse_ts(cp.get("hs_email_last_open_date")):
                if (now - parse_ts(cp.get("hs_email_last_open_date"))).days < 60:
                    triggers.append("recent_email_open")
            if parse_ts(cp.get("hs_analytics_last_visit_timestamp")):
                if (now - parse_ts(cp.get("hs_analytics_last_visit_timestamp"))).days < 90:
                    triggers.append("recent_site_visit")

        has_trigger = len(triggers) > 0

        # Layer 1: Time Decay Score
        decay = compute_time_decay_score(days_since, amount, max_value, loss_reason, has_trigger)
        composite = decay["composite_score"]

        if composite < args.min_score:
            print(f" → score {composite} (skip)")
            continue

        print(f" → score {composite}")

        # Generate revival email
        original_email = draft_revival_email(
            contact_name, company_name, amount, loss_reason, days_since, contact_title
        )

        # Determine revival type
        revival_type = "trigger" if has_trigger else "time_decay"

        entry = {
            "deal_id": deal_id,
            "company": company_name,
            "original_contact": {
                "name": contact_name,
                "email": contact_email,
                "title": contact_title,
            },
            "deal_value": amount,
            "days_since_close": days_since,
            "close_date": dp.get("closedate", ""),
            "loss_reason": loss_reason,
            "pipeline": CLOSED_LOST_STAGES.get(dp.get("dealstage"), "Unknown"),
            "time_decay_score": decay["time_decay_weight"],
            "composite_score": composite,
            "poc_status": "unknown",
            "triggers": triggers,
            "revival_emails": {
                "original": original_email,
                "replacement": None,
                "champion": None,
            },
            "revival_type": revival_type,
        }
        results.append(entry)

    # Sort by composite score
    results.sort(key=lambda x: x["composite_score"], reverse=True)
    top_results = results[:args.top]

    # Output
    output = {
        "generated_at": now.isoformat(),
        "version": "v2",
        "total_closed_lost": len(deals),
        "above_min_value": len(filtered),
        "scored_above_threshold": len(results),
        "returned": len(top_results),
        "parameters": {
            "months": args.months,
            "min_score": args.min_score,
            "min_deal_value": args.min_deal_value,
            "top": args.top,
            "include_champion": args.include_champion,
        },
        "deals": top_results,
    }

    # Print summary
    print(f"\n{'='*70}")
    print(f"🔥 TOP {len(top_results)} REVIVAL OPPORTUNITIES")
    print(f"{'='*70}")
    for i, d in enumerate(top_results, 1):
        print(f"\n#{i} | Score: {d['composite_score']}/100 | {d['company']}")
        print(f"   Deal Value: ${d['deal_value']:,.0f} | Days Since Close: {d['days_since_close']}")
        print(f"   Contact: {d['original_contact']['name']} ({d['original_contact']['email']})")
        print(f"   Title: {d['original_contact']['title']}")
        print(f"   Loss Reason: {d['loss_reason']}")
        print(f"   Revival Type: {d['revival_type']}")
        print(f"   Triggers: {', '.join(d['triggers']) or 'none'}")

    if not args.dry_run:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text(json.dumps(output, indent=2, default=str))
        print(f"\n📁 Saved to {OUTPUT_FILE}")
    else:
        print(f"\n🏃 Dry run — not saving.")

    print(f"\n{'='*70}")
    print(f"✅ Deal Resurrector v2 complete. {len(top_results)} deals ready for review.")


if __name__ == "__main__":
    main()
