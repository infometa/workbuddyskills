#!/usr/bin/env python3
"""
RB2B → Instantly Router

Full pipeline: receives RB2B webhook data, runs suppression pipeline,
classifies visitor type, routes to correct Instantly campaign via API.

Can run as:
  1. HTTP server (direct webhook endpoint)
  2. Stdin processor (for testing / batch processing)

Usage:
    python3 rb2b_instantly_router.py --serve --port 4100
    echo '{"email":"..."}' | python3 rb2b_instantly_router.py
    echo '{"email":"..."}' | python3 rb2b_instantly_router.py --dry-run
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

LOG = logging.getLogger("rb2b-router")

# ─── Configuration ───────────────────────────────────────────────────────────
BASE_DIR = Path(os.environ.get("BASE_DIR", Path(__file__).resolve().parent))

# Import the suppression pipeline (lives in same directory)
sys.path.insert(0, str(BASE_DIR))
from rb2b_suppression_pipeline import run_suppression_pipeline, record_enrollment

# Instantly API key — set via environment variable
INSTANTLY_API_KEY = os.environ.get("INSTANTLY_API_KEY", "")

# Campaign configuration file — maps campaign names to Instantly campaign UUIDs
# Format: {"campaigns": {"Campaign-Name": "uuid-here", ...}}
CAMPAIGNS_FILE = BASE_DIR / "data" / "campaigns.json"


def _load_campaigns():
    """Load campaign name → UUID mapping from config file."""
    try:
        data = json.loads(CAMPAIGNS_FILE.read_text())
        return data.get("campaigns", {})
    except Exception:
        return {}


CAMPAIGNS = _load_campaigns()

# ─── Agency Detection ────────────────────────────────────────────────────────
# Keywords that signal the visitor works at a marketing agency.
# Useful for routing agency visitors to agency-specific campaigns
# (e.g., partnership offers vs. client acquisition).

AGENCY_KEYWORDS_COMPANY = [
    "agency", "digital", "media", "creative", "studio", "consultancy",
    "marketing agency", "seo agency", "advertising",
]
AGENCY_KEYWORDS_TITLE = ["agency", "consultant", "freelance"]
AGENCY_INDUSTRIES = ["marketing and advertising", "advertising services"]

# ─── Seniority Tiers (for company-level dedup) ──────────────────────────────
# Lower rank = more senior. When two people from the same company visit,
# keep the more senior one.
SENIORITY_ORDER = {
    "founder": 1, "ceo": 1, "co-founder": 1, "president": 1,
    "cmo": 2, "cto": 2, "coo": 2, "cfo": 2, "chief": 2,
    "svp": 3, "evp": 3, "senior vice president": 3,
    "vp": 4, "vice president": 4,
    "director": 5, "senior director": 5, "managing director": 5,
    "head of": 6,
    "manager": 7, "senior manager": 7,
}

# ─── Intent Scoring ─────────────────────────────────────────────────────────
# Maps URL path patterns to intent scores. Customize for your site.
PAGE_INTENT_SCORES = {
    "pricing": 90, "plans": 90, "contact": 85, "demo": 85,
    "get-started": 85, "free-consultation": 85, "request-demo": 85,
    "case-study": 70, "case-studies": 70, "results": 70,
    "services": 65, "solutions": 65, "about": 60,
    "blog": 30, "podcast": 25,
}

# Visitors below this score are skipped (blog-only readers, etc.)
MIN_INTENT_SCORE = int(os.environ.get("MIN_INTENT_SCORE", "50"))


def score_intent(pages):
    """Score visitor intent from pages visited. Returns 0-100."""
    if not pages:
        return 30  # default low
    if isinstance(pages, str):
        pages = [pages]
    max_score = 20
    for page in pages:
        path = page.lower().strip("/")
        for pattern, score in PAGE_INTENT_SCORES.items():
            if pattern in path:
                max_score = max(max_score, score)
    return max_score


def is_agency(visitor):
    """Classify visitor as agency or non-agency based on multiple signals."""
    signals = 0

    company = (visitor.get("company_name") or visitor.get("company") or "").lower()
    title = (visitor.get("job_title") or visitor.get("title") or "").lower()
    industry = (visitor.get("industry") or "").lower()
    size = visitor.get("company_size") or visitor.get("employees") or 0
    if isinstance(size, str):
        nums = re.findall(r'\d+', size)
        size = int(nums[-1]) if nums else 0

    for kw in AGENCY_KEYWORDS_COMPANY:
        if kw in company:
            signals += 1
            break

    for kw in AGENCY_KEYWORDS_TITLE:
        if kw in title:
            signals += 1
            break

    if industry in AGENCY_INDUSTRIES:
        signals += 1

    if size < 200 and ("marketing" in industry or "advertising" in industry):
        signals += 1

    # Require at least 2 signals to classify as agency
    return signals >= 2


def detect_source_site(visitor):
    """Determine which of your sites the visitor came from.

    Customize the domain checks for your own properties.
    """
    pages = visitor.get("pages_visited") or visitor.get("page_views") or visitor.get("source_url") or ""
    if isinstance(pages, list):
        pages = " ".join(pages)
    pages = pages.lower()

    # Add your site domains here
    # if "product-b.com" in pages:
    #     return "product-b.com"
    # elif "product-a.com" in pages:
    #     return "product-a.com"

    return os.environ.get("DEFAULT_SOURCE_SITE", "your-site.com")


def route_to_campaign(source_site, agency):
    """Determine the correct Instantly campaign based on source site + agency classification.

    Customize campaign names to match your CAMPAIGNS_FILE config.
    Returns a campaign name string that maps to a UUID in campaigns.json.
    """
    # Example routing logic — customize for your campaigns:
    if agency:
        return os.environ.get("CAMPAIGN_AGENCY", "Agency-Default")
    return os.environ.get("CAMPAIGN_GENERAL", "General-Default")


def get_seniority_rank(title):
    """Get seniority rank (lower = more senior). Returns 99 for unknown."""
    title_lower = title.lower()
    for keyword, rank in SENIORITY_ORDER.items():
        if keyword in title_lower:
            return rank
    return 99


def ensure_campaign_active(campaign_name):
    """Check if campaign is active; if paused, activate it via Instantly API."""
    campaign_id = CAMPAIGNS.get(campaign_name)
    if not campaign_id or not INSTANTLY_API_KEY:
        return
    try:
        check = subprocess.run(
            ["curl", "-s", f"https://api.instantly.ai/api/v2/campaigns/{campaign_id}",
             "-H", f"Authorization: Bearer {INSTANTLY_API_KEY}"],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(check.stdout)
        status = data.get("status", 0)
        if status != 1:  # 1 = active
            LOG.info(f"  🔄 Campaign {campaign_name} is paused, activating...")
            subprocess.run(
                ["curl", "-s", "-X", "POST",
                 f"https://api.instantly.ai/api/v2/campaigns/{campaign_id}/activate",
                 "-H", f"Authorization: Bearer {INSTANTLY_API_KEY}",
                 "-H", "Content-Type: application/json",
                 "-d", "{}"],
                capture_output=True, text=True, timeout=10
            )
    except Exception as e:
        LOG.warning(f"  ⚠️ Could not check/activate campaign {campaign_name}: {e}")


def add_to_instantly(visitor, campaign_name):
    """Add lead to Instantly campaign via API."""
    campaign_id = CAMPAIGNS.get(campaign_name)
    if not campaign_id:
        LOG.error(f"Campaign not found in config: {campaign_name}")
        return False

    if not INSTANTLY_API_KEY:
        LOG.error("INSTANTLY_API_KEY not set")
        return False

    ensure_campaign_active(campaign_name)

    email = visitor.get("email") or visitor.get("business_email")
    first_name = visitor.get("first_name") or (
        visitor.get("name", "").split()[0] if visitor.get("name") else "there"
    )
    company = visitor.get("company_name") or visitor.get("company") or ""

    # Format page visited for personalization
    pages = visitor.get("pages_visited") or visitor.get("page_views") or []
    if isinstance(pages, str):
        pages = [pages]
    page_display = pages[0] if pages else ""
    if "://" in page_display:
        page_display = urlparse(page_display).path

    lead_data = {
        "campaign": campaign_id,
        "email": email,
        "first_name": first_name,
        "last_name": visitor.get("last_name", ""),
        "company_name": company,
        "website": visitor.get("company_website") or visitor.get("website") or "",
        "custom_variables": {
            "companyName": company,
            "firstName": first_name,
            "title": visitor.get("job_title") or visitor.get("title") or "",
            "industry": visitor.get("industry") or "",
            "pageVisited": page_display,
        },
    }

    result = subprocess.run(
        ["curl", "-s", "-X", "POST", "https://api.instantly.ai/api/v2/leads",
         "-H", f"Authorization: Bearer {INSTANTLY_API_KEY}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(lead_data)],
        capture_output=True, text=True, timeout=15
    )

    try:
        resp = json.loads(result.stdout)
        if resp.get("email") or resp.get("id"):
            LOG.info(f"  ✅ Added to Instantly: {email} → {campaign_name}")
            return True
        else:
            LOG.warning(f"  ⚠️ Instantly response: {result.stdout[:200]}")
            return False
    except Exception:
        LOG.error(f"  ❌ Instantly error: {result.stdout[:200]}")
        return False


def process_visitor(visitor, dry_run=False):
    """Full pipeline: score → suppress → classify → route → enroll."""
    email = visitor.get("email") or visitor.get("business_email")
    if not email:
        return {"status": "skipped", "reason": "no email"}

    company = visitor.get("company_name") or visitor.get("company") or ""
    title = visitor.get("job_title") or visitor.get("title") or ""
    domain = email.split("@")[1].lower() if "@" in email else ""

    LOG.info(f"\n{'─'*50}")
    LOG.info(f"Processing: {email} ({company}, {title})")

    # 1. Intent scoring
    pages = visitor.get("pages_visited") or visitor.get("page_views") or []
    intent_score = score_intent(pages)
    if intent_score < MIN_INTENT_SCORE:
        LOG.info(f"  ⏭️ Low intent: {intent_score} < {MIN_INTENT_SCORE}")
        return {"status": "skipped", "reason": f"low intent ({intent_score})"}

    # 2. Suppression pipeline
    suppressed, layers = run_suppression_pipeline(email, company, domain)
    if suppressed:
        last_reason = layers[-1][2] if layers else "unknown"
        LOG.info(f"  🚫 Suppressed: {last_reason}")
        return {"status": "suppressed", "reason": last_reason}

    # 3. Classify agency
    agency = is_agency(visitor)

    # 4. Detect source site
    source_site = detect_source_site(visitor)

    # 5. Route to campaign
    campaign = route_to_campaign(source_site, agency)

    LOG.info(f"  📍 Source: {source_site} | Agency: {agency} | Campaign: {campaign}")
    LOG.info(f"  📊 Intent: {intent_score} | Seniority: {get_seniority_rank(title)}")

    if dry_run:
        return {
            "status": "dry_run",
            "email": email,
            "campaign": campaign,
            "intent_score": intent_score,
            "agency": agency,
            "source_site": source_site,
        }

    # 6. Add to Instantly
    success = add_to_instantly(visitor, campaign)

    if success:
        record_enrollment(email, domain, campaign)
        return {"status": "enrolled", "email": email, "campaign": campaign}
    else:
        return {"status": "failed", "email": email, "campaign": campaign}


# ─── Webhook Server ──────────────────────────────────────────────────────────

class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP handler for RB2B webhook."""
    dry_run = False

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        if length > 1_000_000:
            self.send_response(413)
            self.end_headers()
            return

        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        visitors = payload if isinstance(payload, list) else [payload]
        results = [process_visitor(v, dry_run=self.dry_run) for v in visitors]

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "processed": len(results),
            "enrolled": sum(1 for r in results if r["status"] == "enrolled"),
            "suppressed": sum(1 for r in results if r["status"] == "suppressed"),
            "skipped": sum(1 for r in results if r["status"] == "skipped"),
        }).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "service": "rb2b-instantly-router"}).encode())

    def log_message(self, fmt, *args):
        LOG.info(fmt % args)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RB2B → Instantly Router")
    parser.add_argument("--serve", action="store_true", help="Run as HTTP webhook server")
    parser.add_argument("--port", type=int, default=4100, help="Server port (default: 4100)")
    parser.add_argument("--dry-run", action="store_true", help="Score and classify without enrolling")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(message)s", datefmt="%H:%M:%S",
    )

    if args.serve:
        WebhookHandler.dry_run = args.dry_run
        server = HTTPServer(("0.0.0.0", args.port), WebhookHandler)
        LOG.info(f"🚀 RB2B → Instantly router on port {args.port} (dry_run={args.dry_run})")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
    else:
        payload = json.load(sys.stdin)
        visitors = payload if isinstance(payload, list) else [payload]
        for v in visitors:
            result = process_visitor(v, dry_run=args.dry_run)
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
