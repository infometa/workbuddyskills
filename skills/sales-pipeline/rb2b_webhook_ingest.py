#!/usr/bin/env python3
"""
RB2B Webhook Ingestion Server

Receives RB2B webhook payloads (via Zapier/Make or direct integration),
scores visitor intent based on pages visited, checks ICP fit, and outputs
structured signals for downstream processing.

Can run as:
  1. HTTP webhook server (direct RB2B integration)
  2. Stdin processor (for testing / batch processing)

Usage:
    # Process a single webhook payload from stdin
    echo '{"email":"john@acme.com",...}' | python3 rb2b_webhook_ingest.py

    # Process a batch file (one JSON per line)
    python3 rb2b_webhook_ingest.py --batch webhooks.jsonl

    # Run as HTTP webhook server
    python3 rb2b_webhook_ingest.py --serve --port 4100

    # Dry run (show scoring without side effects)
    python3 rb2b_webhook_ingest.py --dry-run < payload.json
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# ─── Configuration ───────────────────────────────────────────────────────────
LOG = logging.getLogger("rb2b-ingest")
BASE_DIR = Path(os.environ.get("BASE_DIR", Path(__file__).resolve().parent))
OUTPUT_DIR = BASE_DIR / "data" / "signals"

# ─── Intent Scoring ─────────────────────────────────────────────────────────
# Maps URL path patterns to intent scores (0-100).
# Higher score = stronger purchase intent.
# Customize these for your site structure.
PAGE_INTENT_SCORES = {
    # Hot pages — active buying signals
    "pricing": 90,
    "plans": 90,
    "contact": 85,
    "demo": 85,
    "request-demo": 85,
    "book-a-call": 85,
    "get-started": 85,
    "free-consultation": 85,
    "proposal": 80,
    "quote": 80,

    # Warm pages — research/evaluation
    "case-study": 70,
    "case-studies": 70,
    "results": 70,
    "testimonials": 65,
    "about": 60,
    "team": 55,
    "services": 65,
    "solutions": 65,

    # Service pages — customize for your offerings
    # "your-service-1": 75,
    # "your-service-2": 75,

    # Cool pages — awareness/education
    "blog": 30,
    "podcast": 25,
    "webinar": 40,
    "resource": 35,
    "guide": 35,
    "ebook": 40,
}

# Minimum intent score to process (skip pure blog readers)
MIN_INTENT_SCORE = int(os.environ.get("MIN_INTENT_SCORE", "50"))

# ─── ICP Filters ────────────────────────────────────────────────────────────
# Title keywords that indicate decision-maker seniority
ICP_SENIORITY_KEYWORDS = [
    "cmo", "vp", "vice president", "director", "head of", "chief",
    "svp", "evp", "founder", "ceo", "coo", "cto", "partner",
    "senior director", "managing director", "president",
]

# Minimum company size (employees) for ICP match
ICP_MIN_COMPANY_SIZE = int(os.environ.get("ICP_MIN_COMPANY_SIZE", "50"))


def score_pages(pages_visited):
    """Score visitor intent based on pages they viewed.

    Args:
        pages_visited: list of URL strings or page paths

    Returns:
        tuple: (max_score, hot_pages list, page_summary string)
    """
    if not pages_visited:
        return 0, [], "no pages tracked"

    scores = []
    hot_pages = []

    for page_url in pages_visited:
        try:
            path = urlparse(page_url).path if "://" in page_url else page_url
        except Exception:
            path = page_url
        path = path.lower().strip("/")

        best_score = 20  # default for unknown pages
        matched_pattern = None

        for pattern, score in PAGE_INTENT_SCORES.items():
            if pattern in path:
                if score > best_score:
                    best_score = score
                    matched_pattern = pattern

        scores.append(best_score)
        if best_score >= 65:
            hot_pages.append({
                "page": path or "/",
                "score": best_score,
                "pattern": matched_pattern or "unknown",
            })

    max_score = max(scores) if scores else 0
    page_count = len(pages_visited)
    summary = f"{page_count} pages, max intent {max_score}"
    if hot_pages:
        summary += f", hot: {', '.join(p['pattern'] for p in hot_pages[:3])}"

    return max_score, hot_pages, summary


def check_icp_match(visitor):
    """Check if visitor matches ICP criteria.

    Returns:
        tuple: (is_match: bool, reason: str)
    """
    title = (visitor.get("job_title") or visitor.get("title") or "").lower()
    company_size = visitor.get("company_size") or visitor.get("employees") or 0

    if isinstance(company_size, str):
        nums = re.findall(r'\d+', company_size)
        company_size = int(nums[-1]) if nums else 0

    seniority_match = any(kw in title for kw in ICP_SENIORITY_KEYWORDS)
    size_match = company_size >= ICP_MIN_COMPANY_SIZE

    if seniority_match and size_match:
        return True, f"ICP match: {title}, {company_size}+ employees"
    elif seniority_match:
        return True, f"seniority match: {title} (company size unknown/small)"
    elif size_match:
        return False, f"size match but low seniority: {title}"
    else:
        return False, f"no ICP match: {title}, ~{company_size} employees"


def extract_domain(visitor):
    """Extract company domain from visitor data."""
    domain = visitor.get("company_domain") or visitor.get("domain") or ""
    if domain:
        return domain.lower().replace("www.", "")

    email = visitor.get("email") or visitor.get("business_email") or ""
    if email and "@" in email:
        domain = email.split("@")[1].lower()
        generic = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"}
        if domain not in generic:
            return domain

    website = visitor.get("company_website") or visitor.get("website") or ""
    if website:
        try:
            parsed = urlparse(website if "://" in website else f"https://{website}")
            return parsed.netloc.lower().replace("www.", "")
        except Exception:
            pass

    return None


def process_visitor(visitor, dry_run=False, source_site="your-site.com"):
    """Process a single RB2B visitor webhook payload.

    Args:
        visitor: dict with RB2B webhook data
        dry_run: if True, don't write output files
        source_site: which site the visitor came from

    Returns:
        dict with processing result
    """
    # Basic input validation
    if not isinstance(visitor, dict):
        return {"status": "error", "reason": "invalid payload type"}

    # Extract key fields
    name = visitor.get("name") or visitor.get("full_name") or "Unknown"
    first_name = visitor.get("first_name") or (name.split()[0] if name != "Unknown" else "there")
    email = visitor.get("email") or visitor.get("business_email")
    title = visitor.get("job_title") or visitor.get("title") or "Unknown role"
    company = visitor.get("company_name") or visitor.get("company") or "Unknown company"
    linkedin = visitor.get("linkedin_url") or visitor.get("linkedin_profile") or ""
    pages = visitor.get("pages_visited") or visitor.get("page_views") or visitor.get("pages") or []

    if isinstance(pages, str):
        pages = [pages]

    domain = extract_domain(visitor)

    # Score intent
    intent_score, hot_pages, page_summary = score_pages(pages)

    # Check ICP
    is_icp, icp_reason = check_icp_match(visitor)

    # Determine priority
    if intent_score >= 80 and is_icp:
        priority = "high"
    elif intent_score >= 60 or is_icp:
        priority = "medium"
    else:
        priority = "low"

    result = {
        "name": name,
        "email": email,
        "title": title,
        "company": company,
        "domain": domain,
        "intent_score": intent_score,
        "is_icp": is_icp,
        "icp_reason": icp_reason,
        "priority": priority,
        "page_summary": page_summary,
        "source_site": source_site,
    }

    # Skip low-intent visitors
    if intent_score < MIN_INTENT_SCORE and not is_icp:
        result["status"] = "skipped"
        result["reason"] = f"below threshold: intent {intent_score} < {MIN_INTENT_SCORE}, not ICP"
        LOG.info(f"⏭️  Skipped {name} ({company}): {result['reason']}")
        return result

    # Build structured signal output
    hot_page_str = ""
    if hot_pages:
        hot_page_str = f" (viewed: {', '.join(p['pattern'] for p in hot_pages[:2])})"

    signal = {
        "type": "site_visit",
        "topic": f"Website visitor: {name}, {title} at {company}{hot_page_str} — {source_site}",
        "priority": priority,
        "domain": domain,
        "data": {
            "name": name,
            "first_name": first_name,
            "email": email,
            "title": title,
            "company": company,
            "linkedin": linkedin,
            "pages_visited": pages,
            "intent_score": intent_score,
            "hot_pages": hot_pages,
            "is_icp": is_icp,
            "icp_reason": icp_reason,
            "source_site": source_site,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if dry_run:
        result["status"] = "dry_run"
        result["signal"] = signal
        LOG.info(f"🔍 [DRY RUN] Would create signal: {signal['topic']}")
    else:
        # Write signal to output directory as JSON
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_email = (email or "unknown").replace("@", "_at_")
        signal_file = OUTPUT_DIR / f"signal_{ts}_{safe_email}.json"
        signal_file.write_text(json.dumps(signal, indent=2))
        result["status"] = "signal_created"
        result["signal_file"] = str(signal_file)

    LOG.info(
        f"{'✅' if result['status'] == 'signal_created' else '📋'} "
        f"{name} ({company}) — intent:{intent_score} icp:{is_icp} → {result['status']}"
    )
    return result


# ─── Webhook Server ──────────────────────────────────────────────────────────

class RB2BWebhookHandler(BaseHTTPRequestHandler):
    """HTTP handler for direct RB2B webhook integration."""

    dry_run = False
    source_site = "your-site.com"

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 1_000_000:  # 1MB limit
            self.send_response(413)
            self.end_headers()
            return

        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error":"invalid json"}')
            return

        visitors = payload if isinstance(payload, list) else [payload]
        results = [process_visitor(v, dry_run=self.dry_run, source_site=self.source_site)
                   for v in visitors]

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "processed": len(results),
            "signals_created": sum(1 for r in results if r.get("status") == "signal_created"),
            "skipped": sum(1 for r in results if r.get("status") == "skipped"),
        }).encode())

    def do_GET(self):
        """Health check endpoint."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "service": "rb2b-webhook-ingest"}).encode())

    def log_message(self, format, *args):
        LOG.info(format % args)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RB2B Webhook → Signal Pipeline")
    parser.add_argument("--batch", help="Process batch file (one JSON per line)")
    parser.add_argument("--serve", action="store_true", help="Run as HTTP webhook server")
    parser.add_argument("--port", type=int, default=4100, help="Server port (default: 4100)")
    parser.add_argument("--dry-run", action="store_true", help="Don't write signal files")
    parser.add_argument("--source-site", default="your-site.com", help="Source site name")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.serve:
        RB2BWebhookHandler.dry_run = args.dry_run
        RB2BWebhookHandler.source_site = args.source_site
        server = HTTPServer(("0.0.0.0", args.port), RB2BWebhookHandler)
        LOG.info(f"🚀 RB2B webhook server listening on port {args.port}")
        LOG.info(f"   POST http://localhost:{args.port}/ to ingest visitors")
        LOG.info(f"   Dry run: {args.dry_run}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            LOG.info("Shutting down...")
            server.shutdown()

    elif args.batch:
        results = []
        with open(args.batch) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    visitor = json.loads(line)
                    result = process_visitor(visitor, dry_run=args.dry_run, source_site=args.source_site)
                    results.append(result)
                except json.JSONDecodeError as e:
                    LOG.error(f"Invalid JSON line: {e}")

        created = sum(1 for r in results if r.get("status") == "signal_created")
        skipped = sum(1 for r in results if r.get("status") == "skipped")
        print(f"\n📊 Batch complete: {len(results)} processed, {created} signals, {skipped} skipped")

    else:
        try:
            payload = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            LOG.error(f"Invalid JSON on stdin: {e}")
            sys.exit(1)

        visitors = payload if isinstance(payload, list) else [payload]
        for visitor in visitors:
            result = process_visitor(visitor, dry_run=args.dry_run, source_site=args.source_site)
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
