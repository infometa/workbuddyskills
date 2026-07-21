#!/usr/bin/env python3
"""
RB2B 5-Layer Suppression Pipeline

Checks a visitor against multiple suppression layers before enrolling in outbound campaigns.
Layers: CRM → Outbound Platform → Payment Provider → Product Analytics → Internal Blocklist

Prevents you from cold-emailing existing customers, active leads, competitors, or
people you already contacted recently.

Usage:
    # Check a single email
    python3 rb2b_suppression_pipeline.py --email john@acme.com --company "Acme Inc"

    # Dry run (show what would happen)
    python3 rb2b_suppression_pipeline.py --email john@acme.com --dry-run
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

LOG = logging.getLogger("rb2b-suppression")

# ─── Configuration ───────────────────────────────────────────────────────────
# Base directory — override with BASE_DIR env var or defaults to script parent
BASE_DIR = Path(os.environ.get("BASE_DIR", Path(__file__).resolve().parent))
DATA_DIR = BASE_DIR / "data"

# API keys loaded from environment
OUTBOUND_API_KEY = os.environ.get("INSTANTLY_API_KEY", "")
CRM_API_KEY = os.environ.get("HUBSPOT_API_KEY", "")

# File paths for local data caches
BLOCKLIST_FILE = DATA_DIR / "blocklist.json"
ENROLLED_FILE = DATA_DIR / "enrolled.json"
STRIPE_CACHE_FILE = DATA_DIR / "stripe-customers.json"
ACTIVE_USERS_CACHE_FILE = DATA_DIR / "active-users.json"

# ─── Competitor domains to auto-suppress ─────────────────────────────────────
# Add your competitors' email domains here
COMPETITOR_DOMAINS = {
    # Example: "competitor1.com", "competitor2.com",
}

# ─── Personal email domains (skip — no business value) ──────────────────────
PERSONAL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "icloud.com", "protonmail.com", "aol.com", "live.com",
    "me.com", "mail.com", "ymail.com",
}

# ─── Company dedup window (days) ────────────────────────────────────────────
# Only enroll 1 contact per company domain within this window
COMPANY_DEDUP_WINDOW_DAYS = int(os.environ.get("COMPANY_DEDUP_WINDOW_DAYS", "7"))


def _curl_json(method, url, headers=None, body=None):
    """Make HTTP request via curl, return parsed JSON."""
    cmd = ["curl", "-s", "-X", method, url]
    for k, v in (headers or {}).items():
        cmd.extend(["-H", f"{k}: {v}"])
    if body:
        cmd.extend(["-d", json.dumps(body)])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return json.loads(result.stdout) if result.stdout.strip() else None
    except Exception as e:
        LOG.warning(f"API error: {e}")
        return None


# ─── Layer 0: Personal Email Filter ─────────────────────────────────────────

def check_personal_email(email):
    """Filter personal email domains (gmail, yahoo, etc.)."""
    domain = email.split("@")[1].lower() if "@" in email else ""
    if domain in PERSONAL_DOMAINS:
        return True, f"personal email domain: {domain}"
    return False, "business email"


# ─── Layer 1: CRM Check (HubSpot) ───────────────────────────────────────────

def check_crm(email, domain=None):
    """Check if contact exists in your CRM. Uses HubSpot API."""
    if not CRM_API_KEY:
        LOG.warning("No CRM API key available, skipping CRM layer")
        return False, "crm key unavailable (skipped)"

    data = _curl_json("POST", "https://api.hubapi.com/crm/v3/objects/contacts/search",
        headers={
            "Authorization": f"Bearer {CRM_API_KEY}",
            "Content-Type": "application/json",
        },
        body={
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email,
                }]
            }],
            "limit": 1,
        }
    )

    if data and data.get("total", 0) > 0:
        return True, f"exists in CRM (contact ID: {data['results'][0].get('id')})"
    return False, "not in CRM"


# ─── Layer 2: Outbound Platform Check (Instantly) ───────────────────────────

def check_outbound_platform(email):
    """Check if email is already in any outbound campaign (90-day window)."""
    if not OUTBOUND_API_KEY:
        LOG.warning("No outbound API key available, skipping outbound layer")
        return False, "outbound key unavailable (skipped)"

    data = _curl_json("GET",
        f"https://api.instantly.ai/api/v2/leads?email={email}&limit=10",
        headers={"Authorization": f"Bearer {OUTBOUND_API_KEY}"}
    )

    if data and isinstance(data, dict):
        items = data.get("items", [])
        if items:
            cutoff = datetime.now(timezone.utc) - timedelta(days=90)
            for lead in items:
                created = lead.get("timestamp_created", "")
                campaign = lead.get("campaign_name", "unknown")
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if dt > cutoff:
                        return True, f"active in outbound campaign: {campaign}"
                except:
                    return True, f"exists in outbound (campaign: {campaign})"

    return False, "not in outbound platform"


# ─── Layer 3: Payment Provider Check (Stripe) ───────────────────────────────

def check_payment_provider(email, domain=None):
    """Check if email/domain matches a paying customer. Uses cached Stripe data."""
    if not STRIPE_CACHE_FILE.exists():
        LOG.info("Payment provider cache not found, skipping layer")
        return False, "payment check skipped (no cache)"

    try:
        customers = json.loads(STRIPE_CACHE_FILE.read_text())
        emails = {c.get("email", "").lower() for c in customers}
        domains = {c.get("email", "").split("@")[1].lower()
                   for c in customers if "@" in c.get("email", "")}

        if email.lower() in emails:
            return True, "paying customer (exact email match)"
        if domain and domain.lower() in domains:
            return True, f"paying customer (domain match: {domain})"
    except Exception:
        pass

    return False, "not a paying customer"


# ─── Layer 4: Product Analytics Check (Mixpanel/Amplitude) ──────────────────

def check_product_analytics(email):
    """Check if user has been active in product recently. Uses cached data."""
    if not ACTIVE_USERS_CACHE_FILE.exists():
        LOG.info("Product analytics cache not found, skipping layer")
        return False, "product analytics check skipped (no cache)"

    try:
        users = json.loads(ACTIVE_USERS_CACHE_FILE.read_text())
        active_emails = {u.get("email", "").lower() for u in users}
        if email.lower() in active_emails:
            return True, "active product user (last 30 days)"
    except Exception:
        pass

    return False, "not an active product user"


# ─── Layer 5: Blocklist (competitors + manual) ──────────────────────────────

def check_blocklist(email, domain=None):
    """Check against competitor domains and manual blocklist."""
    email_domain = email.split("@")[1].lower() if "@" in email else ""
    if email_domain in COMPETITOR_DOMAINS:
        return True, f"competitor domain: {email_domain}"

    if BLOCKLIST_FILE.exists():
        try:
            blocklist = json.loads(BLOCKLIST_FILE.read_text())
            blocked_emails = {e.lower() for e in blocklist.get("emails", [])}
            blocked_domains = {d.lower() for d in blocklist.get("domains", [])}

            if email.lower() in blocked_emails:
                return True, "manually blocklisted (email)"
            if email_domain in blocked_domains:
                return True, f"manually blocklisted (domain: {email_domain})"
        except Exception:
            pass

    return False, "not blocklisted"


# ─── Company-Level Deduplication ─────────────────────────────────────────────

def check_company_dedup(email, company_domain, window_days=None):
    """Only allow 1 contact per company domain within a rolling window."""
    window_days = window_days or COMPANY_DEDUP_WINDOW_DAYS
    if not ENROLLED_FILE.exists():
        return False, "no prior enrollments"

    try:
        enrolled = json.loads(ENROLLED_FILE.read_text())
        cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()

        for entry in enrolled:
            if (entry.get("domain") == company_domain and
                entry.get("enrolled_at", "") > cutoff and
                entry.get("email") != email):
                return True, (f"company already enrolled: {entry.get('email')} "
                              f"on {entry.get('enrolled_at', '')[:10]}")
    except Exception:
        pass

    return False, "no company dedup conflict"


# ─── Pipeline Orchestrator ───────────────────────────────────────────────────

def run_suppression_pipeline(email, company=None, domain=None, dry_run=False):
    """Run all suppression layers in sequence.

    Returns:
        (should_suppress: bool, results: list of (layer_name, suppressed, reason))
    """
    if not domain and "@" in email:
        domain = email.split("@")[1].lower()

    results = []

    layers = [
        ("Personal Email Filter", lambda: check_personal_email(email)),
        ("CRM Check", lambda: check_crm(email, domain)),
        ("Outbound Platform", lambda: check_outbound_platform(email)),
        ("Payment Provider", lambda: check_payment_provider(email, domain)),
        ("Product Analytics", lambda: check_product_analytics(email)),
        ("Blocklist", lambda: check_blocklist(email, domain)),
        ("Company Dedup", lambda: check_company_dedup(email, domain)),
    ]

    for layer_name, check_fn in layers:
        suppressed, reason = check_fn()
        results.append((layer_name, suppressed, reason))
        if suppressed:
            return True, results

    return False, results


def record_enrollment(email, domain, campaign):
    """Record an enrollment for company-level dedup tracking."""
    try:
        enrolled = json.loads(ENROLLED_FILE.read_text()) if ENROLLED_FILE.exists() else []
    except Exception:
        enrolled = []

    enrolled.append({
        "email": email,
        "domain": domain,
        "campaign": campaign,
        "enrolled_at": datetime.now(timezone.utc).isoformat(),
    })

    # Keep only last 90 days
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    enrolled = [e for e in enrolled if e.get("enrolled_at", "") > cutoff]

    ENROLLED_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENROLLED_FILE.write_text(json.dumps(enrolled, indent=2))


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RB2B Suppression Pipeline")
    parser.add_argument("--email", required=True)
    parser.add_argument("--company", default="")
    parser.add_argument("--domain", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    suppressed, results = run_suppression_pipeline(
        args.email, args.company, args.domain, args.dry_run
    )

    print(f"\n📋 Suppression check for: {args.email}")
    print(f"{'─'*50}")
    for layer_name, was_suppressed, reason in results:
        icon = "🚫" if was_suppressed else "✅"
        print(f"  {icon} {layer_name}: {reason}")

    print(f"{'─'*50}")
    if suppressed:
        print(f"  🚫 SUPPRESSED — do not enroll")
    else:
        print(f"  ✅ CLEAR — eligible for enrollment")

    return 0 if not suppressed else 1


if __name__ == "__main__":
    sys.exit(main())
