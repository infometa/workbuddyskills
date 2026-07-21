#!/usr/bin/env python3
"""
ICP Learning Analyzer — learns from your prospect approve/reject decisions.

Reads prospect approval/rejection history from a PostgreSQL database,
analyzes patterns by source type (cold, trigger, warm, revival), and
outputs recommended ICP filter changes.

Your ICP evolves from your own data instead of guesswork.

Analyzes:
  - Industry patterns (which industries convert vs. get rejected)
  - Company size sweet spots (employee count ranges that win)
  - Title patterns (which seniority levels get approved)
  - Revenue ranges (what deal sizes work)
  - Approval rates per source type

Usage:
    python3 icp_learning_analyzer.py
    python3 icp_learning_analyzer.py --config data/icp-config.json

Requires:
    - DATABASE_URL environment variable (PostgreSQL connection string)
    - psycopg2-binary package
    - A prospects table with status, source, and company/contact joins

Configuration:
    Create data/icp-config.json with source_type_mapping and min_sample_size.
    See .env.example and data/icp-config.example.json for templates.
"""

import argparse
import json
import logging
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ICP-Analyzer] %(message)s")
log = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────────────────────────
BASE_DIR = Path(os.environ.get("BASE_DIR", Path(__file__).resolve().parent))
DATA_DIR = BASE_DIR / "data"
OUTPUT_PATH = DATA_DIR / "icp-recommendations.json"

# Database connection string
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Default ICP config (override with --config flag)
DEFAULT_CONFIG = {
    # Maps your prospect source names to analysis categories
    "source_type_mapping": {
        "cold_outbound": "cold",
        "trigger_prospector": "trigger",
        "website_visitor": "warm",
        "deal_revival": "revival",
        "referral": "warm",
        "inbound": "warm",
    },
    # Minimum approved samples before generating recommendations
    "min_sample_size": 30,
}


def load_config(config_path=None):
    """Load ICP config from file or use defaults."""
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            return json.load(f)
    default_path = DATA_DIR / "icp-config.json"
    if default_path.exists():
        with open(default_path) as f:
            return json.load(f)
    log.info("No config file found, using defaults")
    return DEFAULT_CONFIG


def fetch_prospects():
    """Fetch approved/rejected prospects from database.

    Expected schema:
        prospects: source, status, signal, conviction_score, company_id, contact_id
        companies: id, industry, employees, revenue_range
        contacts:  id, title

    Status values: approved, skipped, sent, opened, replied, meeting, won, lost
    """
    try:
        import psycopg2
    except ImportError:
        log.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        return []

    if not DATABASE_URL:
        log.error("DATABASE_URL not set. Set it in your environment or .env file.")
        return []

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT p.source, p.status, p.signal, p.conviction_score,
                   c.industry, c.employees, c.revenue_range,
                   ct.title
            FROM prospects p
            LEFT JOIN companies c ON p.company_id = c.id
            LEFT JOIN contacts ct ON p.contact_id = ct.id
            WHERE p.status IN ('approved', 'skipped', 'sent', 'opened',
                               'replied', 'meeting', 'won', 'lost')
        """)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        conn.close()
        log.info(f"Fetched {len(rows)} prospect records")
        return rows
    except Exception as e:
        log.error(f"Database query failed: {e}")
        return []


def classify_status(status):
    """Map database status to binary approved/rejected for analysis."""
    approved_statuses = {"approved", "sent", "opened", "replied", "meeting", "won"}
    return "approved" if status in approved_statuses else "rejected"


def parse_revenue(revenue_range):
    """Parse revenue_range string to midpoint integer.

    Handles formats like: "$10M-$50M", "10M-50M", "$5M - $10M"
    Returns None if unparseable.
    """
    if not revenue_range:
        return None
    cleaned = str(revenue_range).replace("$", "").replace(",", "").strip()
    parts = (cleaned
             .replace("M", "000000")
             .replace("B", "000000000")
             .replace("K", "000")
             .split("-"))
    try:
        nums = [int(float(p.strip())) for p in parts if p.strip()]
        return sum(nums) // len(nums) if nums else None
    except (ValueError, ZeroDivisionError):
        return None


def analyze_source_group(prospects, min_sample):
    """Analyze a group of prospects and return filter recommendations.

    Returns recommendations for:
      - industries: which to target, which to exclude
      - employees: min/max employee count range
      - titles: top-performing job titles
      - revenue: min/max revenue range
      - confidence: overall approval rate
    """
    approved = [p for p in prospects if classify_status(p["status"]) == "approved"]
    rejected = [p for p in prospects if classify_status(p["status"]) == "rejected"]

    if len(approved) < min_sample:
        return {
            "status": "insufficient_data",
            "sample_size": len(approved),
            "min_required": min_sample,
            "filters": {},
        }

    total_approved = len(approved)
    total_rejected = max(len(rejected), 1)

    # ── Industry Analysis ────────────────────────────────────────────────
    approved_industries = Counter(p["industry"] for p in approved if p.get("industry"))
    rejected_industries = Counter(p["industry"] for p in rejected if p.get("industry"))

    # Industries with >10% of approvals = recommend targeting
    rec_industries = [ind for ind, cnt in approved_industries.most_common(10)
                      if cnt / total_approved >= 0.10]
    # Industries with >30% of rejections and <5% of approvals = recommend excluding
    exclude_industries = [ind for ind, cnt in rejected_industries.most_common()
                          if cnt / total_rejected >= 0.30
                          and approved_industries.get(ind, 0) / total_approved < 0.05]

    # ── Employee Count Analysis ──────────────────────────────────────────
    approved_emp = sorted([p["employees"] for p in approved if p.get("employees")])
    emp_filters = {}
    if approved_emp:
        p10 = approved_emp[max(0, len(approved_emp) // 10)]
        p90 = approved_emp[min(len(approved_emp) - 1, len(approved_emp) * 9 // 10)]
        emp_filters["min_employees"] = p10
        emp_filters["max_employees"] = p90

    # ── Title Analysis ───────────────────────────────────────────────────
    approved_titles = Counter(p["title"] for p in approved if p.get("title"))
    top_titles = [t for t, _ in approved_titles.most_common(8)]

    # ── Revenue Analysis ─────────────────────────────────────────────────
    approved_rev = [parse_revenue(p.get("revenue_range")) for p in approved]
    approved_rev = sorted([r for r in approved_rev if r is not None])
    rev_filters = {}
    if approved_rev:
        rev_filters["revenue_min"] = approved_rev[max(0, len(approved_rev) // 10)]
        rev_filters["revenue_max"] = approved_rev[min(len(approved_rev) - 1,
                                                       len(approved_rev) * 9 // 10)]

    # ── Compile Filters ──────────────────────────────────────────────────
    approval_rate = total_approved / (total_approved + len(rejected))
    filters = {**emp_filters, **rev_filters}
    if rec_industries:
        filters["industries"] = rec_industries
    if exclude_industries:
        filters["exclude_industries"] = exclude_industries
    if top_titles:
        filters["titles"] = top_titles

    return {
        "status": "ready",
        "filters": filters,
        "confidence": round(approval_rate, 3),
        "sample_size": total_approved,
        "rejected_count": len(rejected),
        "approval_rate": round(approval_rate, 3),
    }


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ICP Learning Analyzer")
    parser.add_argument("--config", help="Path to icp-config.json")
    args = parser.parse_args()

    config = load_config(args.config)
    source_mapping = config.get("source_type_mapping", DEFAULT_CONFIG["source_type_mapping"])
    min_sample = config.get("min_sample_size", DEFAULT_CONFIG["min_sample_size"])

    prospects = fetch_prospects()

    # Group by mapped source type
    grouped = defaultdict(list)
    for p in prospects:
        mapped = source_mapping.get(p.get("source", ""), "other")
        grouped[mapped].append(p)

    recommendations = {}
    for source_type in ["cold", "trigger", "warm", "revival"]:
        group = grouped.get(source_type, [])
        log.info(f"[{source_type}] {len(group)} total prospects")
        recommendations[source_type] = analyze_source_group(group, min_sample)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "complete" if prospects else "no_data",
        "total_prospects_analyzed": len(prospects),
        "recommendations": recommendations,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    log.info(f"Wrote recommendations to {OUTPUT_PATH}")

    # Summary
    print(f"\n📊 ICP Learning Analyzer Results")
    print(f"   Total prospects analyzed: {len(prospects)}")
    print(f"   {'─'*40}")
    for src, rec in recommendations.items():
        status = rec.get("status", "unknown")
        sample = rec.get("sample_size", 0)
        rate = rec.get("approval_rate", 0)
        print(f"   {src:10s}: {status:20s} (n={sample}, approval={rate:.0%})")
        if rec.get("filters"):
            f = rec["filters"]
            if f.get("industries"):
                print(f"              → Target: {', '.join(f['industries'][:5])}")
            if f.get("exclude_industries"):
                print(f"              → Exclude: {', '.join(f['exclude_industries'][:3])}")
            if f.get("min_employees"):
                print(f"              → Employees: {f['min_employees']}-{f.get('max_employees', '?')}")


if __name__ == "__main__":
    main()
