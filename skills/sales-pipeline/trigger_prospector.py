#!/usr/bin/env python3
"""
Trigger-Based Prospecting Engine

Monitors job postings, new hires, and funding signals to identify
companies where new marketing leaders are evaluating agency/vendor relationships.

Searches across multiple signal categories:
  - New CMO/VP Marketing hires (leadership change = budget reallocation)
  - Marketing leadership job postings (team building = growth mode)
  - Agency search signals (active evaluation)
  - Funding rounds (capital to deploy on growth)

Each signal is scored, enriched with industry/size estimates, and paired
with a personalized outreach hook and email draft.

Usage:
    python3 trigger_prospector.py --days 7 --top 15 --min-score 50

Requires: BRAVE_API_KEY environment variable
"""

import argparse
import json
import os
import random
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# ─── Configuration ───────────────────────────────────────────────────────────
BASE_DIR = Path(os.environ.get("BASE_DIR", Path(__file__).resolve().parent))
DATA_DIR = BASE_DIR / "data"
OUTPUT_FILE = DATA_DIR / "trigger-prospects-latest.json"

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

# Your company info (for email templates)
YOUR_COMPANY_NAME = os.environ.get("YOUR_COMPANY_NAME", "Your Company")
YOUR_SENDER_NAME = os.environ.get("YOUR_SENDER_NAME", "Your Name")

# ─── Signal Search Queries ───────────────────────────────────────────────────
# Customize these queries for your target market.
# Each category maps to a list of search queries that detect buying signals.
SEARCH_QUERIES = {
    "new_hire": [
        '"hired head of marketing"',
        '"new CMO" announced',
        '"VP marketing joined"',
        '"head of growth" hired',
        '"VP of marketing" appointed',
        '"chief marketing officer" joins',
    ],
    "job_posting": [
        '"head of marketing" job posting site:linkedin.com',
        '"VP of marketing" hiring site:linkedin.com',
        '"CMO" open role site:linkedin.com',
    ],
    "agency_search": [
        '"looking for marketing agency"',
        '"looking for agency" marketing',
        '"seeking marketing partner"',
        '"RFP" "marketing agency"',
    ],
    "funding": [
        '"series A" raised marketing',
        '"series B" raised marketing',
        '"raised" million marketing growth',
        '"funding round" marketing scale',
    ],
}

# ─── Service Keyword Mapping ────────────────────────────────────────────────
# Maps your service offerings to keywords found in signal text.
# Used to suggest which services to pitch to each prospect.
SERVICE_KEYWORDS = {
    "SEO": ["seo", "organic", "search engine", "content marketing", "blog", "rankings"],
    "Paid Media": ["paid", "ppc", "ads", "advertising", "google ads", "facebook ads",
                    "media buy", "paid social", "paid search"],
    "Creative": ["creative", "brand", "design", "video", "content", "storytelling"],
    "CRO": ["conversion", "cro", "optimization", "landing page", "funnel", "a/b test"],
    "AI Marketing": ["ai", "artificial intelligence", "machine learning", "automation",
                      "personalization"],
}


def get_brave_api_key():
    """Get Brave Search API key from environment."""
    key = os.environ.get("BRAVE_API_KEY")
    if not key:
        print("❌ BRAVE_API_KEY not set.", file=sys.stderr)
        print("   Get one at: https://api.search.brave.com/", file=sys.stderr)
        sys.exit(1)
    return key


def brave_search(query: str, api_key: str, freshness: str = "pw", count: int = 10) -> list:
    """Search Brave and return results list."""
    params = urlencode({"q": query, "count": count, "freshness": freshness})
    url = f"{BRAVE_SEARCH_URL}?{params}"
    req = Request(url, headers={
        "Accept": "application/json",
        "Accept-Encoding": "identity",
        "X-Subscription-Token": api_key,
    })
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data.get("web", {}).get("results", [])
    except Exception as e:
        print(f"  Warning: Search failed for '{query[:50]}...': {e}", file=sys.stderr)
        return []


def freshness_for_days(days: int) -> str:
    """Map day count to Brave freshness parameter."""
    if days <= 1:
        return "pd"
    elif days <= 7:
        return "pw"
    elif days <= 30:
        return "pm"
    return "py"


def extract_company_name(title: str, description: str) -> str:
    """Best-effort company name extraction from search result text."""
    patterns = [
        r"(?:at|joins?|hired by|appointed at|named .* at)\s+([A-Z][A-Za-z0-9&\.\- ]{1,40}?)"
        r"(?:\s+as|\s*[,\.\-\|]|\s+to\b)",
        r"([A-Z][A-Za-z0-9&\.\- ]{1,40}?)\s+(?:hires?|appoints?|names?|announces?|welcomes?)\b",
        r"([A-Z][A-Za-z0-9&\.\- ]{1,40}?)\s+(?:raises?|secures?|closes?)\s+\$",
        r"([A-Z][A-Za-z0-9&\.\- ]{1,40}?)\s+(?:series [A-C]|funding)",
    ]
    text = f"{title} {description}"
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            name = m.group(1).strip().rstrip(" -,.|")
            if name.lower() not in {"the", "a", "new", "former", "our", "this", "why", "how", "what"}:
                return name
    parts = re.split(r"[\|\-–—:]", title)
    if parts:
        candidate = parts[0].strip()
        if len(candidate) < 50 and candidate[0:1].isupper():
            return candidate
    return title[:60]


def estimate_company_size(text: str) -> str:
    """Estimate company size from context clues in signal text."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["enterprise", "fortune 500", "10,000", "global"]):
        return "1000+"
    if any(w in text_lower for w in ["series c", "series d", "ipo", "public"]):
        return "500-1000"
    if any(w in text_lower for w in ["series b", "growth stage", "scale"]):
        return "200-500"
    if any(w in text_lower for w in ["series a", "startup", "seed"]):
        return "50-200"
    if any(w in text_lower for w in ["pre-seed", "bootstrapped", "early stage"]):
        return "10-50"
    return "50-500"


def estimate_industry(text: str) -> str:
    """Estimate industry from signal text."""
    text_lower = text.lower()
    industries = {
        "SaaS": ["saas", "software", "platform", "cloud", "app"],
        "E-commerce": ["ecommerce", "e-commerce", "retail", "shop", "store", "dtc", "d2c"],
        "Fintech": ["fintech", "financial", "banking", "payments", "insurance"],
        "Healthcare": ["health", "medical", "biotech", "pharma", "wellness"],
        "Education": ["edtech", "education", "learning", "course"],
        "AI/ML": ["artificial intelligence", "machine learning", "ai-powered", "ai company"],
        "Crypto/Web3": ["crypto", "blockchain", "web3", "defi", "nft"],
        "Media": ["media", "publishing", "news", "content"],
        "B2B Services": ["b2b", "consulting", "services", "agency"],
    }
    for industry, keywords in industries.items():
        if any(k in text_lower for k in keywords):
            return industry
    return "Technology"


def suggest_services(text: str) -> list:
    """Suggest which of your services to pitch based on signal text."""
    text_lower = text.lower()
    matched = []
    for service, keywords in SERVICE_KEYWORDS.items():
        if any(k in text_lower for k in keywords):
            matched.append(service)
    if not matched:
        matched = ["SEO", "Paid Media"]  # Sensible defaults
    return matched


def score_prospect(signal_type: str, size_est: str, services: list, text: str) -> int:
    """Score a prospect 0-100 based on signal type, company fit, and context."""
    score = 0

    # Signal type scoring
    signal_scores = {"new_hire": 35, "job_posting": 25, "funding": 30, "agency_search": 40}
    score += signal_scores.get(signal_type, 20)

    # Company size fit (mid-market is ideal for most agencies)
    size_scores = {"10-50": 10, "50-200": 25, "200-500": 25, "500-1000": 15, "1000+": 5}
    score += size_scores.get(size_est, 15)

    # Service alignment
    score += min(len(services) * 5, 20)

    # Bonus signals in text
    text_lower = text.lower()
    if "cmo" in text_lower or "chief marketing" in text_lower:
        score += 10
    if "agency" in text_lower:
        score += 5
    if any(w in text_lower for w in ["review", "evaluate", "looking for", "rfp"]):
        score += 5

    return min(score, 100)


def generate_outreach_hook(company: str, signal_type: str) -> str:
    """Generate a casual outreach hook based on the signal type."""
    hooks = {
        "new_hire": [
            f"New marketing leadership at {company}. The first 90 days is when the best "
            f"leaders figure out what's actually working.",
            f"Congrats on the new hire at {company}. Leadership changes are the best time "
            f"to audit what's driving results and what's noise.",
        ],
        "job_posting": [
            f"Noticed {company} is hiring marketing roles. Usually means growth is the "
            f"priority. We help companies hit targets while the team ramps up.",
            f"{company} is building out the marketing team. We've been the bridge for "
            f"companies in that exact phase.",
        ],
        "funding": [
            f"Congrats on the raise. Post-funding is when the pressure to scale "
            f"acquisition hits. We help turn capital into pipeline efficiently.",
            f"Saw the funding news for {company}. The companies that win post-raise "
            f"scale acquisition without burning through runway.",
        ],
        "agency_search": [
            f"Saw {company} is evaluating marketing partners. Happy to throw our hat in.",
            f"Noticed you're looking for a marketing partner at {company}.",
        ],
    }
    options = hooks.get(signal_type, [f"Noticed some movement at {company}."])
    return random.choice(options)


def generate_email_draft(company, signal_type, services):
    """Generate a trigger-based cold email draft."""
    services_str = ", ".join(services[:3]) if services else "growth marketing"
    cta = random.choice([
        "Worth exploring?", "Curious if relevant?", "Worth a conversation?",
        "Make sense to chat?", "Worth 15 min?",
    ])
    signoff = YOUR_SENDER_NAME

    templates = {
        "new_hire": {
            "subject": f"{company}, new leadership = fresh eyes",
            "body": (f"Hey,\n\nSaw the leadership change at {company}. The first 90 days "
                     f"are when the best marketing leaders audit what's working and cut what's not.\n\n"
                     f"We specialize in {services_str} and figured the timing might be right.\n\n"
                     f"{cta}\n\n{signoff}"),
        },
        "job_posting": {
            "subject": f"{company} is hiring, we can help now",
            "body": (f"Hey,\n\nNoticed {company} is hiring marketing roles. Hiring takes time, "
                     f"but growth targets don't wait.\n\n"
                     f"We've been the bridge for companies in that exact gap, handling "
                     f"{services_str} while the team ramps up.\n\n{cta}\n\n{signoff}"),
        },
        "funding": {
            "subject": f"congrats on the raise, {company}",
            "body": (f"Hey,\n\nSaw the funding news. Congrats. Post-raise is when the pressure "
                     f"to scale acquisition really hits.\n\n"
                     f"We help companies turn funding into efficient pipeline growth, "
                     f"specifically through {services_str}.\n\n{cta}\n\n{signoff}"),
        },
        "agency_search": {
            "subject": f"{company} + {YOUR_COMPANY_NAME}",
            "body": (f"Hey,\n\nSaw you're evaluating marketing partners at {company}.\n\n"
                     f"We specialize in {services_str}. Happy to share a few quick wins "
                     f"we'd go after in the first 30 days. No commitment.\n\n{cta}\n\n{signoff}"),
        },
    }

    t = templates.get(signal_type, templates["agency_search"])
    return f"Subject: {t['subject']}\n\n{t['body']}"


def suggest_channel(signal_type: str) -> str:
    """Suggest the best outreach channel for this signal type."""
    channels = {
        "new_hire": "LinkedIn (congratulate + connect)",
        "agency_search": "Email (direct response)",
        "funding": "LinkedIn + Email (warm congrats)",
        "job_posting": "Email",
    }
    return channels.get(signal_type, "Email")


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def run(days: int = 7, top: int = 15, min_score: int = 50):
    api_key = get_brave_api_key()
    freshness = freshness_for_days(days)

    print(f"🔍 Trigger-Based Prospecting Engine")
    print(f"   Scanning last {days} days | Top {top} | Min score: {min_score}")
    print(f"   {'-'*50}")

    all_prospects = []
    seen_urls = set()

    for signal_type, queries in SEARCH_QUERIES.items():
        print(f"\n📡 Scanning: {signal_type.replace('_', ' ').title()}")
        for query in queries:
            print(f"   → {query[:60]}...")
            results = brave_search(query, api_key, freshness=freshness, count=8)

            for r in results:
                url = r.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                title = r.get("title", "")
                desc = r.get("description", "")
                full_text = f"{title} {desc}"

                company = extract_company_name(title, desc)
                size_est = estimate_company_size(full_text)
                industry = estimate_industry(full_text)
                services = suggest_services(full_text)
                score = score_prospect(signal_type, size_est, services, full_text)

                if score < min_score:
                    continue

                prospect = {
                    "company": company,
                    "signal_type": signal_type,
                    "signal_detail": title,
                    "signal_url": url,
                    "signal_date": datetime.now().strftime("%Y-%m-%d"),
                    "prospect_score": score,
                    "industry": industry,
                    "est_company_size": size_est,
                    "suggested_services": services,
                    "suggested_channel": suggest_channel(signal_type),
                    "outreach_hook": generate_outreach_hook(company, signal_type),
                    "email_draft": generate_email_draft(company, signal_type, services),
                }
                all_prospects.append(prospect)

    # Deduplicate by company (keep highest score)
    company_best = {}
    for p in all_prospects:
        key = p["company"].lower().strip()
        if key not in company_best or p["prospect_score"] > company_best[key]["prospect_score"]:
            company_best[key] = p

    prospects = sorted(company_best.values(),
                       key=lambda x: x["prospect_score"], reverse=True)[:top]

    # Save output
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "generated_at": datetime.now().isoformat(),
        "params": {"days": days, "top": top, "min_score": min_score},
        "total_signals_found": len(all_prospects),
        "prospects": prospects,
    }
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))

    # Print summary
    print(f"\n{'='*60}")
    print(f"🎯 TOP {len(prospects)} PROSPECTS (of {len(all_prospects)} signals found)")
    print(f"{'='*60}\n")

    for i, p in enumerate(prospects, 1):
        print(f"  {i:2d}. [{p['prospect_score']:3d}] {p['company']}")
        print(f"      Signal: {p['signal_type']} — {p['signal_detail'][:70]}")
        print(f"      Size: {p['est_company_size']} | Industry: {p['industry']}")
        print(f"      Services: {', '.join(p['suggested_services'])}")
        print(f"      Channel: {p['suggested_channel']}")
        print()

    print(f"📁 Saved to: {OUTPUT_FILE}")
    return prospects


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger-Based Prospecting Engine")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days (default: 7)")
    parser.add_argument("--top", type=int, default=15, help="Number of top prospects (default: 15)")
    parser.add_argument("--min-score", type=int, default=50, help="Minimum prospect score (default: 50)")
    args = parser.parse_args()

    run(days=args.days, top=args.top, min_score=args.min_score)
