#!/usr/bin/env python3
"""
Revenue Attribution Mapper

Connects content pieces to pipeline and closed deals. Proves content ROI.
Maps blog posts, videos, podcasts to first-touch and multi-touch attribution
using GA4 + HubSpot deal data.

Usage:
    python revenue_attribution.py --report
    python revenue_attribution.py --report --model linear
    python revenue_attribution.py --cpa --costs content_costs.json
    python revenue_attribution.py --gaps
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# API Configuration
# ---------------------------------------------------------------------------

# HubSpot: Set HUBSPOT_API_KEY to your private app token
# Required scopes: crm.objects.deals.read, crm.objects.contacts.read
HUBSPOT_API_KEY = os.environ.get("HUBSPOT_API_KEY", "")
HUBSPOT_BASE_URL = "https://api.hubapi.com"

# GA4: Set GA4_PROPERTY_ID and GA4_CREDENTIALS_JSON
# GA4_CREDENTIALS_JSON should point to a service account JSON file
# Required: Google Analytics Data API (v1beta) enabled
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID", "")
GA4_CREDENTIALS_JSON = os.environ.get("GA4_CREDENTIALS_JSON", "")

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./output")

# ---------------------------------------------------------------------------
# Content type classification
# ---------------------------------------------------------------------------

CONTENT_TYPE_PATTERNS = {
    "blog": ["/blog/", "/posts/", "/article/", "/insights/"],
    "video": ["/video/", "/youtube/", "/watch/", "/webinar-recording/"],
    "podcast": ["/podcast/", "/episode/", "/listen/"],
    "webinar": ["/webinar/", "/live/", "/register/"],
    "case_study": ["/case-study/", "/case-studies/", "/success-story/", "/customer-story/"],
    "landing_page": ["/lp/", "/landing/", "/offer/", "/download/"],
    "tool": ["/tool/", "/calculator/", "/grader/", "/analyzer/"],
    "comparison": ["/vs/", "/compare/", "/alternative/", "/versus/"],
}

# Funnel stage classification
FUNNEL_STAGE_PATTERNS = {
    "awareness": ["/blog/", "/posts/", "/article/", "/podcast/", "/video/"],
    "consideration": ["/case-study/", "/webinar/", "/guide/", "/comparison/", "/vs/"],
    "decision": ["/pricing/", "/demo/", "/contact/", "/trial/", "/start/", "/lp/"],
}


def classify_content_type(url: str) -> str:
    """Classify a URL into a content type."""
    url_lower = url.lower()
    for content_type, patterns in CONTENT_TYPE_PATTERNS.items():
        if any(p in url_lower for p in patterns):
            return content_type
    return "other"


def classify_funnel_stage(url: str) -> str:
    """Classify a URL into a funnel stage."""
    url_lower = url.lower()
    for stage, patterns in FUNNEL_STAGE_PATTERNS.items():
        if any(p in url_lower for p in patterns):
            return stage
    return "unknown"


# ---------------------------------------------------------------------------
# GA4 Data Client
# ---------------------------------------------------------------------------

def fetch_ga4_page_data(start_date: str, end_date: str) -> list[dict]:
    """
    Fetch page-level session and conversion data from GA4.

    Returns list of dicts:
    [{"page_path": "/blog/foo", "sessions": 1234, "conversions": 5, "users": 900}]

    NOTE: Requires google-analytics-data library.
    pip install google-analytics-data

    Setup:
    1. Create a service account in Google Cloud Console
    2. Enable the Google Analytics Data API
    3. Add the service account email as a viewer on your GA4 property
    4. Download the JSON key file and set GA4_CREDENTIALS_JSON env var
    """
    if not GA4_PROPERTY_ID or not GA4_CREDENTIALS_JSON:
        print("WARNING: GA4_PROPERTY_ID or GA4_CREDENTIALS_JSON not set. Using sample data.", file=sys.stderr)
        return _sample_ga4_data()

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            DateRange,
            Dimension,
            Metric,
            RunReportRequest,
        )

        client = BetaAnalyticsDataClient.from_service_account_json(GA4_CREDENTIALS_JSON)

        request = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[
                Dimension(name="pagePath"),
                Dimension(name="sessionDefaultChannelGroup"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="conversions"),
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )

        response = client.run_report(request)

        results = []
        for row in response.rows:
            results.append({
                "page_path": row.dimension_values[0].value,
                "channel": row.dimension_values[1].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "conversions": int(row.metric_values[2].value),
            })

        return results

    except ImportError:
        print("WARNING: google-analytics-data not installed. Using sample data.", file=sys.stderr)
        return _sample_ga4_data()
    except Exception as e:
        print(f"WARNING: GA4 API error: {e}. Using sample data.", file=sys.stderr)
        return _sample_ga4_data()


def _sample_ga4_data() -> list[dict]:
    """Sample GA4 data for testing/demo purposes."""
    return [
        {"page_path": "/blog/seo-strategy-2025", "channel": "Organic Search", "sessions": 4200, "users": 3800, "conversions": 12},
        {"page_path": "/blog/content-marketing-roi", "channel": "Organic Search", "sessions": 3100, "users": 2900, "conversions": 8},
        {"page_path": "/blog/ai-marketing-tools", "channel": "Organic Search", "sessions": 5600, "users": 5100, "conversions": 15},
        {"page_path": "/case-study/saas-company-3x-pipeline", "channel": "Direct", "sessions": 890, "users": 820, "conversions": 9},
        {"page_path": "/case-study/ecommerce-seo-growth", "channel": "Organic Search", "sessions": 1200, "users": 1100, "conversions": 7},
        {"page_path": "/podcast/episode-42-growth-loops", "channel": "Social", "sessions": 2300, "users": 2100, "conversions": 3},
        {"page_path": "/webinar/ai-ops-for-marketers", "channel": "Email", "sessions": 650, "users": 600, "conversions": 11},
        {"page_path": "/video/youtube-seo-masterclass", "channel": "Social", "sessions": 8900, "users": 8200, "conversions": 6},
        {"page_path": "/blog/paid-media-benchmarks", "channel": "Organic Search", "sessions": 2700, "users": 2500, "conversions": 4},
        {"page_path": "/lp/free-seo-audit", "channel": "Paid Search", "sessions": 1800, "users": 1700, "conversions": 22},
        {"page_path": "/pricing", "channel": "Direct", "sessions": 3200, "users": 2900, "conversions": 18},
        {"page_path": "/blog/b2b-lead-generation", "channel": "Organic Search", "sessions": 3400, "users": 3100, "conversions": 5},
        {"page_path": "/vs/hubspot-alternative", "channel": "Organic Search", "sessions": 1500, "users": 1400, "conversions": 10},
    ]


# ---------------------------------------------------------------------------
# HubSpot Deal Data
# ---------------------------------------------------------------------------

def fetch_hubspot_deals(start_date: str, end_date: str) -> list[dict]:
    """
    Fetch closed-won deals from HubSpot with touchpoint history.

    Returns list of dicts:
    [{
        "deal_id": "123",
        "deal_name": "Acme Corp",
        "amount": 50000,
        "close_date": "2025-03-15",
        "touchpoints": [
            {"url": "/blog/seo-strategy", "timestamp": "2025-01-10", "type": "first_touch"},
            {"url": "/case-study/saas", "timestamp": "2025-02-20", "type": "page_view"},
            {"url": "/pricing", "timestamp": "2025-03-01", "type": "page_view"},
        ]
    }]

    NOTE: Requires requests library.
    Touchpoints come from HubSpot's contact timeline / page views.
    You need a private app with crm.objects.deals.read + crm.objects.contacts.read scopes.
    """
    if not HUBSPOT_API_KEY:
        print("WARNING: HUBSPOT_API_KEY not set. Using sample data.", file=sys.stderr)
        return _sample_hubspot_deals()

    try:
        import requests

        headers = {"Authorization": f"Bearer {HUBSPOT_API_KEY}"}

        # Fetch closed-won deals in date range
        # Using the search API for better filtering
        search_body = {
            "filterGroups": [{
                "filters": [
                    {"propertyName": "dealstage", "operator": "EQ", "value": "closedwon"},
                    {"propertyName": "closedate", "operator": "GTE", "value": f"{start_date}T00:00:00Z"},
                    {"propertyName": "closedate", "operator": "LTE", "value": f"{end_date}T23:59:59Z"},
                ]
            }],
            "properties": ["dealname", "amount", "closedate", "dealstage"],
            "limit": 100,
        }

        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/deals/search",
            headers=headers,
            json=search_body,
        )
        resp.raise_for_status()
        deals_data = resp.json().get("results", [])

        deals = []
        for deal in deals_data:
            props = deal.get("properties", {})
            deal_id = deal["id"]

            # Get associated contacts
            assoc_resp = requests.get(
                f"{HUBSPOT_BASE_URL}/crm/v3/objects/deals/{deal_id}/associations/contacts",
                headers=headers,
            )
            contact_ids = [r["id"] for r in assoc_resp.json().get("results", [])] if assoc_resp.ok else []

            # Get page views for each contact (from engagement timeline)
            touchpoints = []
            for cid in contact_ids[:5]:  # Limit to avoid rate limits
                # Fetch contact's page views from the timeline API
                timeline_resp = requests.get(
                    f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/{cid}/engagements",
                    headers=headers,
                    params={"limit": 50},
                )
                if timeline_resp.ok:
                    for eng in timeline_resp.json().get("results", []):
                        # Extract page view URLs from engagement metadata
                        metadata = eng.get("properties", {})
                        if metadata.get("hs_page_url"):
                            touchpoints.append({
                                "url": metadata["hs_page_url"],
                                "timestamp": metadata.get("hs_timestamp", ""),
                                "type": "page_view",
                            })

            # Mark first and last touch
            if touchpoints:
                touchpoints.sort(key=lambda t: t["timestamp"])
                touchpoints[0]["type"] = "first_touch"
                touchpoints[-1]["type"] = "last_touch"

            deals.append({
                "deal_id": deal_id,
                "deal_name": props.get("dealname", "Unknown"),
                "amount": float(props.get("amount", 0) or 0),
                "close_date": props.get("closedate", "")[:10],
                "touchpoints": touchpoints,
            })

        return deals

    except ImportError:
        print("WARNING: requests not installed. Using sample data.", file=sys.stderr)
        return _sample_hubspot_deals()
    except Exception as e:
        print(f"WARNING: HubSpot API error: {e}. Using sample data.", file=sys.stderr)
        return _sample_hubspot_deals()


def _sample_hubspot_deals() -> list[dict]:
    """Sample HubSpot deal data for testing/demo."""
    return [
        {
            "deal_id": "deal_001",
            "deal_name": "Acme Corp - SEO Retainer",
            "amount": 120000,
            "close_date": "2025-03-15",
            "touchpoints": [
                {"url": "/blog/seo-strategy-2025", "timestamp": "2025-01-05", "type": "first_touch"},
                {"url": "/blog/content-marketing-roi", "timestamp": "2025-01-22", "type": "page_view"},
                {"url": "/case-study/saas-company-3x-pipeline", "timestamp": "2025-02-10", "type": "page_view"},
                {"url": "/pricing", "timestamp": "2025-02-28", "type": "page_view"},
                {"url": "/lp/free-seo-audit", "timestamp": "2025-03-05", "type": "last_touch"},
            ],
        },
        {
            "deal_id": "deal_002",
            "deal_name": "TechStart Inc - Full Service",
            "amount": 240000,
            "close_date": "2025-02-20",
            "touchpoints": [
                {"url": "/blog/ai-marketing-tools", "timestamp": "2024-12-01", "type": "first_touch"},
                {"url": "/podcast/episode-42-growth-loops", "timestamp": "2024-12-15", "type": "page_view"},
                {"url": "/webinar/ai-ops-for-marketers", "timestamp": "2025-01-10", "type": "page_view"},
                {"url": "/vs/hubspot-alternative", "timestamp": "2025-01-25", "type": "page_view"},
                {"url": "/pricing", "timestamp": "2025-02-10", "type": "last_touch"},
            ],
        },
        {
            "deal_id": "deal_003",
            "deal_name": "GrowthCo - Content Marketing",
            "amount": 84000,
            "close_date": "2025-03-01",
            "touchpoints": [
                {"url": "/blog/content-marketing-roi", "timestamp": "2025-01-15", "type": "first_touch"},
                {"url": "/case-study/ecommerce-seo-growth", "timestamp": "2025-02-01", "type": "page_view"},
                {"url": "/pricing", "timestamp": "2025-02-20", "type": "last_touch"},
            ],
        },
        {
            "deal_id": "deal_004",
            "deal_name": "SaaS Corp - Paid Media",
            "amount": 180000,
            "close_date": "2025-01-30",
            "touchpoints": [
                {"url": "/video/youtube-seo-masterclass", "timestamp": "2024-11-15", "type": "first_touch"},
                {"url": "/blog/paid-media-benchmarks", "timestamp": "2024-12-10", "type": "page_view"},
                {"url": "/blog/b2b-lead-generation", "timestamp": "2025-01-05", "type": "page_view"},
                {"url": "/lp/free-seo-audit", "timestamp": "2025-01-20", "type": "last_touch"},
            ],
        },
        {
            "deal_id": "deal_005",
            "deal_name": "Enterprise Ltd - SEO + Content",
            "amount": 360000,
            "close_date": "2025-03-20",
            "touchpoints": [
                {"url": "/blog/seo-strategy-2025", "timestamp": "2024-12-20", "type": "first_touch"},
                {"url": "/blog/ai-marketing-tools", "timestamp": "2025-01-08", "type": "page_view"},
                {"url": "/case-study/saas-company-3x-pipeline", "timestamp": "2025-01-25", "type": "page_view"},
                {"url": "/webinar/ai-ops-for-marketers", "timestamp": "2025-02-05", "type": "page_view"},
                {"url": "/pricing", "timestamp": "2025-03-01", "type": "page_view"},
                {"url": "/lp/free-seo-audit", "timestamp": "2025-03-10", "type": "last_touch"},
            ],
        },
    ]


# ---------------------------------------------------------------------------
# Attribution Models
# ---------------------------------------------------------------------------

def first_touch_attribution(deals: list[dict]) -> dict[str, float]:
    """100% credit to the first touchpoint."""
    attribution = defaultdict(float)
    for deal in deals:
        tps = deal.get("touchpoints", [])
        if tps:
            first = tps[0]
            attribution[first["url"]] += deal["amount"]
    return dict(attribution)


def last_touch_attribution(deals: list[dict]) -> dict[str, float]:
    """100% credit to the last touchpoint."""
    attribution = defaultdict(float)
    for deal in deals:
        tps = deal.get("touchpoints", [])
        if tps:
            last = tps[-1]
            attribution[last["url"]] += deal["amount"]
    return dict(attribution)


def linear_attribution(deals: list[dict]) -> dict[str, float]:
    """Equal credit to all touchpoints."""
    attribution = defaultdict(float)
    for deal in deals:
        tps = deal.get("touchpoints", [])
        if tps:
            credit = deal["amount"] / len(tps)
            for tp in tps:
                attribution[tp["url"]] += credit
    return dict(attribution)


def time_decay_attribution(deals: list[dict], half_life_days: int = 7) -> dict[str, float]:
    """
    More credit to touchpoints closer to close date.
    Uses exponential decay with configurable half-life.
    """
    import math

    attribution = defaultdict(float)
    for deal in deals:
        tps = deal.get("touchpoints", [])
        close_date = deal.get("close_date", "")
        if not tps or not close_date:
            continue

        try:
            close_dt = datetime.strptime(close_date, "%Y-%m-%d")
        except ValueError:
            continue

        # Calculate decay weights
        weights = []
        for tp in tps:
            try:
                tp_dt = datetime.strptime(tp["timestamp"][:10], "%Y-%m-%d")
                days_before = (close_dt - tp_dt).days
                weight = math.pow(0.5, days_before / half_life_days)
                weights.append(weight)
            except (ValueError, KeyError):
                weights.append(0.1)

        total_weight = sum(weights) or 1
        for tp, weight in zip(tps, weights):
            attribution[tp["url"]] += deal["amount"] * (weight / total_weight)

    return dict(attribution)


ATTRIBUTION_MODELS = {
    "first-touch": first_touch_attribution,
    "last-touch": last_touch_attribution,
    "linear": linear_attribution,
    "time-decay": time_decay_attribution,
}


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_attribution_report(
    deals: list[dict],
    ga4_data: list[dict],
    model: str = "linear",
) -> dict:
    """Generate a full attribution report."""
    # Run attribution
    model_func = ATTRIBUTION_MODELS.get(model, linear_attribution)
    attribution = model_func(deals)

    # Enrich with GA4 data
    ga4_by_path = {}
    for row in ga4_data:
        path = row["page_path"]
        if path not in ga4_by_path:
            ga4_by_path[path] = {"sessions": 0, "users": 0, "conversions": 0}
        ga4_by_path[path]["sessions"] += row["sessions"]
        ga4_by_path[path]["users"] += row["users"]
        ga4_by_path[path]["conversions"] += row["conversions"]

    # Build content performance table
    content_performance = []
    for url, revenue in sorted(attribution.items(), key=lambda x: -x[1]):
        ga4 = ga4_by_path.get(url, {"sessions": 0, "users": 0, "conversions": 0})
        content_type = classify_content_type(url)
        funnel_stage = classify_funnel_stage(url)

        content_performance.append({
            "url": url,
            "content_type": content_type,
            "funnel_stage": funnel_stage,
            "attributed_revenue": round(revenue, 2),
            "sessions": ga4["sessions"],
            "users": ga4["users"],
            "conversions": ga4["conversions"],
            "revenue_per_session": round(revenue / ga4["sessions"], 2) if ga4["sessions"] else 0,
            "deals_touched": sum(
                1 for d in deals if any(tp["url"] == url for tp in d.get("touchpoints", []))
            ),
        })

    # Aggregate by content type
    by_type = defaultdict(lambda: {"revenue": 0, "sessions": 0, "conversions": 0, "pieces": 0})
    for cp in content_performance:
        t = cp["content_type"]
        by_type[t]["revenue"] += cp["attributed_revenue"]
        by_type[t]["sessions"] += cp["sessions"]
        by_type[t]["conversions"] += cp["conversions"]
        by_type[t]["pieces"] += 1

    type_summary = []
    for content_type, stats in sorted(by_type.items(), key=lambda x: -x[1]["revenue"]):
        type_summary.append({
            "content_type": content_type,
            "total_revenue": round(stats["revenue"], 2),
            "total_sessions": stats["sessions"],
            "total_conversions": stats["conversions"],
            "piece_count": stats["pieces"],
            "avg_revenue_per_piece": round(stats["revenue"] / stats["pieces"], 2) if stats["pieces"] else 0,
        })

    # Summary
    total_revenue = sum(d["amount"] for d in deals)
    total_deals = len(deals)

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "attribution_model": model,
        "summary": {
            "total_revenue": total_revenue,
            "total_deals": total_deals,
            "avg_deal_size": round(total_revenue / total_deals, 2) if total_deals else 0,
            "content_pieces_with_attribution": len(content_performance),
            "avg_touchpoints_per_deal": round(
                sum(len(d.get("touchpoints", [])) for d in deals) / total_deals, 1
            ) if total_deals else 0,
        },
        "top_content": content_performance[:20],
        "by_content_type": type_summary,
    }

    return report


def calculate_cpa(report: dict, costs: dict) -> dict:
    """
    Calculate cost-per-acquisition by content type.

    costs should be: {"blog": 15000, "video": 8000, "podcast": 3000, ...}
    representing total spend on each content type in the period.
    """
    cpa_report = []
    for type_data in report["by_content_type"]:
        ct = type_data["content_type"]
        cost = costs.get(ct, 0)
        revenue = type_data["total_revenue"]
        conversions = type_data["total_conversions"]

        cpa_report.append({
            "content_type": ct,
            "total_cost": cost,
            "total_revenue": revenue,
            "conversions": conversions,
            "cpa": round(cost / conversions, 2) if conversions else None,
            "roi": round((revenue - cost) / cost, 2) if cost else None,
            "roi_multiple": f"{round(revenue / cost, 1)}x" if cost else "N/A",
        })

    cpa_report.sort(key=lambda x: (x["roi"] or 0), reverse=True)
    return {"cpa_by_content_type": cpa_report}


def find_content_gaps(deals: list[dict]) -> dict:
    """
    Identify funnel stages with no or low content attribution.
    """
    stage_coverage = defaultdict(lambda: {"urls": set(), "deals": 0, "revenue": 0})

    for deal in deals:
        stages_hit = set()
        for tp in deal.get("touchpoints", []):
            stage = classify_funnel_stage(tp["url"])
            stage_coverage[stage]["urls"].add(tp["url"])
            stages_hit.add(stage)

        for stage in stages_hit:
            stage_coverage[stage]["deals"] += 1
            stage_coverage[stage]["revenue"] += deal["amount"] / len(stages_hit)

    # Check for gaps
    expected_stages = ["awareness", "consideration", "decision"]
    gaps = []
    for stage in expected_stages:
        data = stage_coverage.get(stage, {"urls": set(), "deals": 0, "revenue": 0})
        total_deals = len(deals)
        coverage_pct = round(data["deals"] / total_deals * 100, 1) if total_deals else 0

        if coverage_pct < 30:
            severity = "critical" if coverage_pct < 10 else "moderate"
            gaps.append({
                "stage": stage,
                "coverage_percent": coverage_pct,
                "deals_with_stage": data["deals"],
                "content_pieces": len(data["urls"]),
                "severity": severity,
                "recommendation": _gap_recommendation(stage, coverage_pct),
            })

    stage_summary = []
    for stage in expected_stages:
        data = stage_coverage.get(stage, {"urls": set(), "deals": 0, "revenue": 0})
        stage_summary.append({
            "stage": stage,
            "content_pieces": len(data["urls"]),
            "deals_touched": data["deals"],
            "attributed_revenue": round(data["revenue"], 2),
            "top_urls": list(data["urls"])[:5],
        })

    return {
        "gaps": gaps,
        "stage_summary": stage_summary,
        "total_deals_analyzed": len(deals),
    }


def _gap_recommendation(stage: str, coverage_pct: float) -> str:
    """Generate a recommendation for a content gap."""
    recs = {
        "awareness": "Create more top-of-funnel content (blog posts, videos, podcasts) targeting high-volume keywords. Focus on educational content that introduces the problem your product solves.",
        "consideration": "Build comparison pages, case studies, and webinars that help prospects evaluate solutions. This is where you prove credibility and differentiation.",
        "decision": "Add pricing pages, ROI calculators, free trials, and demo CTAs. Make it easy for ready-to-buy prospects to take action.",
    }
    return recs.get(stage, f"Create content for the {stage} stage to improve coverage from {coverage_pct}%.")


# ---------------------------------------------------------------------------
# Output Formatting
# ---------------------------------------------------------------------------

def print_report(report: dict) -> None:
    """Print attribution report in human-readable format."""
    s = report["summary"]
    print(f"\n{'='*70}")
    print(f"  CONTENT REVENUE ATTRIBUTION REPORT")
    print(f"  Model: {report['attribution_model']}")
    print(f"  Generated: {report['generated_at']}")
    print(f"{'='*70}")

    print(f"\n  📊 Summary")
    print(f"     Total Revenue:          ${s['total_revenue']:,.0f}")
    print(f"     Total Deals:            {s['total_deals']}")
    print(f"     Avg Deal Size:          ${s['avg_deal_size']:,.0f}")
    print(f"     Content w/ Attribution: {s['content_pieces_with_attribution']}")
    print(f"     Avg Touchpoints/Deal:   {s['avg_touchpoints_per_deal']}")

    print(f"\n  📈 Revenue by Content Type")
    print(f"  {'Type':<16} {'Revenue':>12} {'Sessions':>10} {'Pieces':>8} {'Avg/Piece':>12}")
    print(f"  {'-'*58}")
    for ct in report["by_content_type"]:
        print(
            f"  {ct['content_type']:<16} "
            f"${ct['total_revenue']:>10,.0f} "
            f"{ct['total_sessions']:>10,} "
            f"{ct['piece_count']:>8} "
            f"${ct['avg_revenue_per_piece']:>10,.0f}"
        )

    print(f"\n  🏆 Top Content by Revenue")
    print(f"  {'URL':<45} {'Revenue':>12} {'Sessions':>10} {'Type':<12}")
    print(f"  {'-'*79}")
    for cp in report["top_content"][:10]:
        url_display = cp["url"][:43] + ".." if len(cp["url"]) > 45 else cp["url"]
        print(
            f"  {url_display:<45} "
            f"${cp['attributed_revenue']:>10,.0f} "
            f"{cp['sessions']:>10,} "
            f"{cp['content_type']:<12}"
        )

    print()


def print_gaps(gaps_report: dict) -> None:
    """Print content gap analysis."""
    print(f"\n{'='*70}")
    print(f"  CONTENT GAP ANALYSIS")
    print(f"{'='*70}")

    print(f"\n  📊 Funnel Stage Coverage ({gaps_report['total_deals_analyzed']} deals)")
    for stage in gaps_report["stage_summary"]:
        print(f"\n  {stage['stage'].upper()}")
        print(f"     Content Pieces: {stage['content_pieces']}")
        print(f"     Deals Touched:  {stage['deals_touched']}")
        print(f"     Revenue:        ${stage['attributed_revenue']:,.0f}")

    if gaps_report["gaps"]:
        print(f"\n  ⚠️  Gaps Identified")
        for gap in gaps_report["gaps"]:
            print(f"\n  [{gap['severity'].upper()}] {gap['stage'].upper()} — {gap['coverage_percent']}% coverage")
            print(f"  → {gap['recommendation']}")
    else:
        print(f"\n  ✅ No significant gaps found")

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Map content to revenue with multi-touch attribution.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --report
  %(prog)s --report --model time-decay
  %(prog)s --cpa --costs content_costs.json
  %(prog)s --gaps
  %(prog)s --report --start 2025-01-01 --end 2025-03-31 --json
        """,
    )

    parser.add_argument("--report", action="store_true", help="Generate attribution report")
    parser.add_argument("--gaps", action="store_true", help="Identify content gaps in buyer journey")
    parser.add_argument("--cpa", action="store_true", help="Calculate cost-per-acquisition by content type")

    parser.add_argument("--model", choices=["first-touch", "last-touch", "linear", "time-decay"],
                        default="linear", help="Attribution model (default: linear)")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (default: 90 days ago)")
    parser.add_argument("--end", help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--costs", help="JSON file with content costs by type (for --cpa)")

    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--output", "-o", help="Write output to file")

    args = parser.parse_args()

    if not (args.report or args.gaps or args.cpa):
        parser.error("At least one of --report, --gaps, or --cpa is required")

    # Date range
    end_date = args.end or datetime.utcnow().strftime("%Y-%m-%d")
    start_date = args.start or (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")

    print(f"Fetching data for {start_date} to {end_date}...", file=sys.stderr)

    # Fetch data
    ga4_data = fetch_ga4_page_data(start_date, end_date)
    deals = fetch_hubspot_deals(start_date, end_date)

    output = {
        "date_range": {"start": start_date, "end": end_date},
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    if args.report:
        report = generate_attribution_report(deals, ga4_data, model=args.model)
        output["attribution_report"] = report
        if not args.json:
            print_report(report)

    if args.cpa:
        if not args.report:
            report = generate_attribution_report(deals, ga4_data, model=args.model)
            output["attribution_report"] = report

        costs = {}
        if args.costs:
            costs_path = Path(args.costs)
            if costs_path.exists():
                costs = json.loads(costs_path.read_text())
            else:
                print(f"WARNING: Costs file not found: {args.costs}. Using empty costs.", file=sys.stderr)

        cpa_data = calculate_cpa(output["attribution_report"], costs)
        output["cpa"] = cpa_data

        if not args.json:
            print(f"\n{'='*70}")
            print(f"  COST PER ACQUISITION BY CONTENT TYPE")
            print(f"{'='*70}")
            print(f"  {'Type':<16} {'Cost':>10} {'Revenue':>12} {'CPA':>10} {'ROI':>8}")
            print(f"  {'-'*56}")
            for row in cpa_data["cpa_by_content_type"]:
                cpa_str = f"${row['cpa']:,.0f}" if row["cpa"] is not None else "N/A"
                roi_str = row["roi_multiple"]
                print(
                    f"  {row['content_type']:<16} "
                    f"${row['total_cost']:>8,} "
                    f"${row['total_revenue']:>10,.0f} "
                    f"{cpa_str:>10} "
                    f"{roi_str:>8}"
                )
            print()

    if args.gaps:
        gaps_data = find_content_gaps(deals)
        output["gaps"] = gaps_data
        if not args.json:
            print_gaps(gaps_data)

    if args.json:
        print(json.dumps(output, indent=2, default=str))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, indent=2, default=str))
        if not args.json:
            print(f"✅ Output written to {args.output}")


if __name__ == "__main__":
    main()
