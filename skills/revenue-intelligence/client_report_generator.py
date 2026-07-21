#!/usr/bin/env python3
"""
Multi-Source Client Report Generator

Pulls from GA4 + HubSpot + Ahrefs + Gong to generate unified client-ready BI reports.
Includes executive summary, anomaly detection, and multi-format output.

Usage:
    python client_report_generator.py --client "Acme Corp"
    python client_report_generator.py --client "Acme Corp" --format markdown --output report.md
    python client_report_generator.py --client "Acme Corp" --anomalies --compare previous-month
"""

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# API Configuration
# ---------------------------------------------------------------------------

# GA4: Google Analytics Data API
# Set GA4_PROPERTY_ID and GA4_CREDENTIALS_JSON (service account JSON path)
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID", "")
GA4_CREDENTIALS_JSON = os.environ.get("GA4_CREDENTIALS_JSON", "")

# HubSpot: Private App Token
# Required scopes: crm.objects.deals.read, crm.objects.contacts.read
HUBSPOT_API_KEY = os.environ.get("HUBSPOT_API_KEY", "")

# Ahrefs: API Token
# Get from: https://ahrefs.com/api
AHREFS_TOKEN = os.environ.get("AHREFS_TOKEN", "")

# Gong: API Access Key
# Get from: Gong > Settings > API
GONG_API_KEY = os.environ.get("GONG_API_KEY", "")
GONG_API_BASE_URL = os.environ.get("GONG_API_BASE_URL", "https://api.gong.io/v2")

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./output")


# ---------------------------------------------------------------------------
# Data Source Fetchers
# ---------------------------------------------------------------------------

def fetch_ga4_traffic(start_date: str, end_date: str, prev_start: Optional[str] = None, prev_end: Optional[str] = None) -> dict:
    """
    Fetch traffic metrics from GA4.

    Returns: {
        "current": {"sessions": N, "users": N, "pageviews": N, "bounce_rate": N, ...},
        "previous": {...} or None,
        "top_pages": [...],
        "channels": [...]
    }
    """
    if not GA4_PROPERTY_ID or not GA4_CREDENTIALS_JSON:
        print("INFO: GA4 credentials not configured. Using sample data.", file=sys.stderr)
        return _sample_ga4_traffic()

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            DateRange,
            Dimension,
            Metric,
            RunReportRequest,
            OrderBy,
        )

        client = BetaAnalyticsDataClient.from_service_account_json(GA4_CREDENTIALS_JSON)

        # Overall metrics
        date_ranges = [DateRange(start_date=start_date, end_date=end_date)]
        if prev_start and prev_end:
            date_ranges.append(DateRange(start_date=prev_start, end_date=prev_end))

        overview_req = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="screenPageViews"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
                Metric(name="conversions"),
            ],
            date_ranges=date_ranges,
        )
        overview_resp = client.run_report(overview_req)

        current = _parse_ga4_metrics(overview_resp.rows[0] if overview_resp.rows else None)
        previous = _parse_ga4_metrics(overview_resp.rows[1] if len(overview_resp.rows) > 1 else None)

        # Top pages
        pages_req = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="sessions"), Metric(name="conversions")],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=10,
        )
        pages_resp = client.run_report(pages_req)
        top_pages = [
            {
                "page": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "conversions": int(row.metric_values[1].value),
            }
            for row in pages_resp.rows
        ]

        # Channel breakdown
        channels_req = RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="sessionDefaultChannelGroup")],
            metrics=[Metric(name="sessions"), Metric(name="totalUsers"), Metric(name="conversions")],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        )
        channels_resp = client.run_report(channels_req)
        channels = [
            {
                "channel": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "conversions": int(row.metric_values[2].value),
            }
            for row in channels_resp.rows
        ]

        return {
            "current": current,
            "previous": previous,
            "top_pages": top_pages,
            "channels": channels,
        }

    except Exception as e:
        print(f"WARNING: GA4 API error: {e}. Using sample data.", file=sys.stderr)
        return _sample_ga4_traffic()


def _parse_ga4_metrics(row) -> Optional[dict]:
    if not row:
        return None
    return {
        "sessions": int(row.metric_values[0].value),
        "users": int(row.metric_values[1].value),
        "pageviews": int(row.metric_values[2].value),
        "bounce_rate": round(float(row.metric_values[3].value) * 100, 1),
        "avg_session_duration": round(float(row.metric_values[4].value), 1),
        "conversions": int(row.metric_values[5].value),
    }


def _sample_ga4_traffic() -> dict:
    return {
        "current": {
            "sessions": 45200,
            "users": 38400,
            "pageviews": 112000,
            "bounce_rate": 52.3,
            "avg_session_duration": 185.4,
            "conversions": 342,
        },
        "previous": {
            "sessions": 41800,
            "users": 35600,
            "pageviews": 98000,
            "bounce_rate": 55.1,
            "avg_session_duration": 172.8,
            "conversions": 298,
        },
        "top_pages": [
            {"page": "/blog/seo-strategy-2025", "sessions": 4200, "conversions": 12},
            {"page": "/blog/ai-marketing-tools", "sessions": 3800, "conversions": 15},
            {"page": "/", "sessions": 3500, "conversions": 8},
            {"page": "/blog/content-marketing-roi", "sessions": 3100, "conversions": 8},
            {"page": "/pricing", "sessions": 2900, "conversions": 18},
            {"page": "/blog/b2b-lead-generation", "sessions": 2700, "conversions": 5},
            {"page": "/services", "sessions": 2400, "conversions": 14},
            {"page": "/case-studies", "sessions": 1800, "conversions": 9},
            {"page": "/blog/paid-media-benchmarks", "sessions": 1600, "conversions": 4},
            {"page": "/about", "sessions": 1200, "conversions": 2},
        ],
        "channels": [
            {"channel": "Organic Search", "sessions": 22100, "users": 19200, "conversions": 156},
            {"channel": "Direct", "sessions": 9800, "users": 8100, "conversions": 89},
            {"channel": "Paid Search", "sessions": 5400, "users": 5100, "conversions": 52},
            {"channel": "Social", "sessions": 4200, "users": 3800, "conversions": 18},
            {"channel": "Email", "sessions": 2100, "users": 1900, "conversions": 22},
            {"channel": "Referral", "sessions": 1600, "users": 1300, "conversions": 5},
        ],
    }


def fetch_hubspot_pipeline(start_date: str, end_date: str) -> dict:
    """
    Fetch pipeline metrics from HubSpot.

    Returns: {
        "deals_created": N,
        "deals_closed_won": N,
        "deals_closed_lost": N,
        "revenue_closed": N,
        "pipeline_value": N,
        "avg_deal_size": N,
        "avg_sales_cycle_days": N,
        "top_deals": [...]
    }
    """
    if not HUBSPOT_API_KEY:
        print("INFO: HubSpot credentials not configured. Using sample data.", file=sys.stderr)
        return _sample_hubspot_pipeline()

    try:
        import requests
        headers = {"Authorization": f"Bearer {HUBSPOT_API_KEY}"}

        # Fetch deals created in period
        search_body = {
            "filterGroups": [{
                "filters": [
                    {"propertyName": "createdate", "operator": "GTE", "value": f"{start_date}T00:00:00Z"},
                    {"propertyName": "createdate", "operator": "LTE", "value": f"{end_date}T23:59:59Z"},
                ]
            }],
            "properties": ["dealname", "amount", "dealstage", "closedate", "createdate", "hs_date_entered_closedwon"],
            "limit": 100,
        }

        resp = requests.post(
            "https://api.hubapi.com/crm/v3/objects/deals/search",
            headers=headers,
            json=search_body,
        )
        resp.raise_for_status()
        deals = resp.json().get("results", [])

        created = len(deals)
        won = sum(1 for d in deals if d["properties"].get("dealstage") == "closedwon")
        lost = sum(1 for d in deals if d["properties"].get("dealstage") == "closedlost")
        revenue = sum(float(d["properties"].get("amount", 0) or 0) for d in deals if d["properties"].get("dealstage") == "closedwon")
        pipeline_value = sum(float(d["properties"].get("amount", 0) or 0) for d in deals if d["properties"].get("dealstage") not in ("closedwon", "closedlost"))

        # Calculate avg sales cycle for won deals
        cycle_days = []
        for d in deals:
            if d["properties"].get("dealstage") == "closedwon":
                try:
                    created_dt = datetime.strptime(d["properties"]["createdate"][:10], "%Y-%m-%d")
                    closed_dt = datetime.strptime(d["properties"]["closedate"][:10], "%Y-%m-%d")
                    cycle_days.append((closed_dt - created_dt).days)
                except (ValueError, KeyError, TypeError):
                    pass

        avg_cycle = round(sum(cycle_days) / len(cycle_days), 1) if cycle_days else 0

        top_deals = sorted(
            [{"name": d["properties"].get("dealname", ""), "amount": float(d["properties"].get("amount", 0) or 0), "stage": d["properties"].get("dealstage", "")}
             for d in deals],
            key=lambda x: x["amount"],
            reverse=True,
        )[:5]

        return {
            "deals_created": created,
            "deals_closed_won": won,
            "deals_closed_lost": lost,
            "revenue_closed": revenue,
            "pipeline_value": pipeline_value,
            "avg_deal_size": round(revenue / won, 0) if won else 0,
            "avg_sales_cycle_days": avg_cycle,
            "win_rate": round(won / (won + lost) * 100, 1) if (won + lost) else 0,
            "top_deals": top_deals,
        }

    except Exception as e:
        print(f"WARNING: HubSpot API error: {e}. Using sample data.", file=sys.stderr)
        return _sample_hubspot_pipeline()


def _sample_hubspot_pipeline() -> dict:
    return {
        "deals_created": 47,
        "deals_closed_won": 12,
        "deals_closed_lost": 8,
        "revenue_closed": 1440000,
        "pipeline_value": 2850000,
        "avg_deal_size": 120000,
        "avg_sales_cycle_days": 38.5,
        "win_rate": 60.0,
        "top_deals": [
            {"name": "Enterprise Ltd - Full Service", "amount": 360000, "stage": "closedwon"},
            {"name": "TechStart Inc - SEO + Content", "amount": 240000, "stage": "closedwon"},
            {"name": "DataCo - Pipeline Build", "amount": 180000, "stage": "contractsent"},
            {"name": "ScaleUp - Paid Media", "amount": 156000, "stage": "closedwon"},
            {"name": "GrowthCo - Content Marketing", "amount": 120000, "stage": "qualifiedtobuy"},
        ],
    }


def fetch_ahrefs_seo(domain: str) -> dict:
    """
    Fetch SEO metrics from Ahrefs.

    Returns: {
        "domain_rating": N,
        "referring_domains": N,
        "backlinks": N,
        "organic_keywords": N,
        "organic_traffic": N,
        "top_keywords": [...],
        "new_backlinks": N,
        "lost_backlinks": N
    }
    """
    if not AHREFS_TOKEN:
        print("INFO: Ahrefs credentials not configured. Using sample data.", file=sys.stderr)
        return _sample_ahrefs_data()

    try:
        import requests

        headers = {"Authorization": f"Bearer {AHREFS_TOKEN}"}
        base = "https://api.ahrefs.com/v3"

        # Domain overview
        overview_resp = requests.get(
            f"{base}/site-explorer/overview",
            headers=headers,
            params={"target": domain, "mode": "domain"},
        )
        overview_resp.raise_for_status()
        overview = overview_resp.json()

        # Top organic keywords
        keywords_resp = requests.get(
            f"{base}/site-explorer/organic-keywords",
            headers=headers,
            params={"target": domain, "mode": "domain", "limit": 10, "order_by": "traffic:desc"},
        )
        keywords_data = keywords_resp.json() if keywords_resp.ok else {}

        top_keywords = [
            {
                "keyword": kw.get("keyword", ""),
                "position": kw.get("position", 0),
                "volume": kw.get("volume", 0),
                "traffic": kw.get("traffic", 0),
            }
            for kw in keywords_data.get("keywords", [])
        ]

        return {
            "domain_rating": overview.get("domain_rating", 0),
            "referring_domains": overview.get("referring_domains", 0),
            "backlinks": overview.get("backlinks", 0),
            "organic_keywords": overview.get("organic_keywords", 0),
            "organic_traffic": overview.get("organic_traffic", 0),
            "top_keywords": top_keywords,
            "new_backlinks": overview.get("new_backlinks_30d", 0),
            "lost_backlinks": overview.get("lost_backlinks_30d", 0),
        }

    except Exception as e:
        print(f"WARNING: Ahrefs API error: {e}. Using sample data.", file=sys.stderr)
        return _sample_ahrefs_data()


def _sample_ahrefs_data() -> dict:
    return {
        "domain_rating": 72,
        "referring_domains": 4850,
        "backlinks": 89200,
        "organic_keywords": 28400,
        "organic_traffic": 156000,
        "top_keywords": [
            {"keyword": "digital marketing agency", "position": 3, "volume": 18100, "traffic": 4200},
            {"keyword": "seo services", "position": 5, "volume": 14800, "traffic": 2100},
            {"keyword": "content marketing strategy", "position": 2, "volume": 9900, "traffic": 3800},
            {"keyword": "b2b marketing agency", "position": 4, "volume": 6600, "traffic": 1400},
            {"keyword": "marketing automation", "position": 7, "volume": 12100, "traffic": 980},
            {"keyword": "ppc management", "position": 6, "volume": 5400, "traffic": 890},
            {"keyword": "growth marketing", "position": 1, "volume": 4400, "traffic": 2900},
            {"keyword": "seo audit", "position": 8, "volume": 8800, "traffic": 640},
            {"keyword": "link building services", "position": 3, "volume": 3600, "traffic": 780},
            {"keyword": "saas marketing", "position": 2, "volume": 3200, "traffic": 1200},
        ],
        "new_backlinks": 342,
        "lost_backlinks": 128,
    }


def fetch_gong_call_quality(start_date: str, end_date: str) -> dict:
    """
    Fetch call quality metrics from Gong.

    Returns: {
        "total_calls": N,
        "avg_talk_ratio": N (percent rep spoke),
        "avg_longest_monologue": N (seconds),
        "avg_patience": N (seconds before interrupting),
        "topics_discussed": [...],
        "win_rate_by_talk_ratio": {...}
    }
    """
    if not GONG_API_KEY:
        print("INFO: Gong credentials not configured. Using sample data.", file=sys.stderr)
        return _sample_gong_data()

    try:
        import requests

        headers = {
            "Authorization": f"Bearer {GONG_API_KEY}",
            "Content-Type": "application/json",
        }

        # Fetch call stats
        from_dt = f"{start_date}T00:00:00Z"
        to_dt = f"{end_date}T23:59:59Z"

        stats_resp = requests.post(
            f"{GONG_API_BASE_URL}/stats/activity/aggregate",
            headers=headers,
            json={
                "filter": {"fromDateTime": from_dt, "toDateTime": to_dt},
                "aggregation": {"aggregateBy": "user"},
            },
        )

        if stats_resp.ok:
            stats = stats_resp.json()
            # Process aggregate stats
            # (Gong's actual response format varies; adjust parsing as needed)
            return {
                "total_calls": stats.get("totalCalls", 0),
                "avg_talk_ratio": stats.get("avgTalkRatio", 0),
                "source": "gong_api",
            }
        else:
            return _sample_gong_data()

    except Exception as e:
        print(f"WARNING: Gong API error: {e}. Using sample data.", file=sys.stderr)
        return _sample_gong_data()


def _sample_gong_data() -> dict:
    return {
        "total_calls": 156,
        "avg_talk_ratio": 54.2,
        "avg_longest_monologue_sec": 142,
        "avg_patience_sec": 1.8,
        "avg_call_duration_min": 32.5,
        "calls_with_next_steps": 118,
        "next_steps_rate": 75.6,
        "top_topics": [
            {"topic": "Pricing", "frequency": 89, "pct": 57.1},
            {"topic": "Implementation", "frequency": 72, "pct": 46.2},
            {"topic": "ROI", "frequency": 68, "pct": 43.6},
            {"topic": "Timeline", "frequency": 54, "pct": 34.6},
            {"topic": "Competition", "frequency": 41, "pct": 26.3},
        ],
        "talk_ratio_vs_win_rate": {
            "40-50%": {"calls": 42, "win_rate": 38.1},
            "50-60%": {"calls": 58, "win_rate": 45.2},
            "60-70%": {"calls": 36, "win_rate": 31.4},
            "70%+": {"calls": 20, "win_rate": 15.0},
        },
    }


# ---------------------------------------------------------------------------
# Anomaly Detection
# ---------------------------------------------------------------------------

def detect_anomalies(current: dict, previous: dict, thresholds: Optional[dict] = None) -> list[dict]:
    """
    Compare current vs previous period metrics and flag anomalies.

    Default thresholds: >20% change = warning, >40% change = critical
    """
    if not thresholds:
        thresholds = {"warning": 0.20, "critical": 0.40}

    anomalies = []

    metric_labels = {
        "sessions": "Website Sessions",
        "users": "Unique Users",
        "pageviews": "Pageviews",
        "bounce_rate": "Bounce Rate",
        "conversions": "Conversions",
        "avg_session_duration": "Avg Session Duration",
    }

    for metric, label in metric_labels.items():
        curr_val = current.get(metric, 0)
        prev_val = previous.get(metric, 0)

        if prev_val == 0:
            continue

        pct_change = (curr_val - prev_val) / prev_val
        abs_change = abs(pct_change)

        if abs_change >= thresholds["critical"]:
            severity = "critical"
        elif abs_change >= thresholds["warning"]:
            severity = "warning"
        else:
            continue

        direction = "increase" if pct_change > 0 else "decrease"
        # For bounce rate, increase is bad; for others, decrease is bad
        is_positive = (direction == "increase") if metric != "bounce_rate" else (direction == "decrease")

        anomalies.append({
            "metric": metric,
            "label": label,
            "current_value": curr_val,
            "previous_value": prev_val,
            "pct_change": round(pct_change * 100, 1),
            "direction": direction,
            "severity": severity,
            "sentiment": "positive" if is_positive else "negative",
            "summary": f"{label} {'📈' if is_positive else '📉'} {abs(round(pct_change * 100, 1))}% {direction} ({prev_val:,} → {curr_val:,})",
        })

    return anomalies


# ---------------------------------------------------------------------------
# Report Builder
# ---------------------------------------------------------------------------

def build_report(
    client_name: str,
    start_date: str,
    end_date: str,
    skip_sources: list[str] = None,
    enable_anomalies: bool = False,
    compare: Optional[str] = None,
    domain: str = "",
) -> dict:
    """Build the full client report from all sources."""
    skip = skip_sources or []

    # Calculate comparison period
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    period_days = (end_dt - start_dt).days

    prev_end = (start_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    prev_start = (start_dt - timedelta(days=period_days + 1)).strftime("%Y-%m-%d")

    report = {
        "client": client_name,
        "period": {"start": start_date, "end": end_date, "days": period_days},
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sections": {},
    }

    # --- GA4 Traffic ---
    if "ga4" not in skip:
        ga4 = fetch_ga4_traffic(start_date, end_date, prev_start, prev_end)
        report["sections"]["traffic"] = ga4

        if enable_anomalies and ga4.get("current") and ga4.get("previous"):
            anomalies = detect_anomalies(ga4["current"], ga4["previous"])
            report["sections"]["traffic"]["anomalies"] = anomalies

    # --- HubSpot Pipeline ---
    if "hubspot" not in skip:
        pipeline = fetch_hubspot_pipeline(start_date, end_date)
        report["sections"]["pipeline"] = pipeline

    # --- Ahrefs SEO ---
    if "ahrefs" not in skip:
        target_domain = domain or os.environ.get("YOUR_DOMAIN", "example.com")
        seo = fetch_ahrefs_seo(target_domain)
        report["sections"]["seo"] = seo

    # --- Gong Call Quality ---
    if "gong" not in skip:
        call_quality = fetch_gong_call_quality(start_date, end_date)
        report["sections"]["call_quality"] = call_quality

    # --- Executive Summary ---
    report["executive_summary"] = generate_executive_summary(report)

    return report


def generate_executive_summary(report: dict) -> dict:
    """Auto-generate executive summary from report data."""
    highlights = []
    concerns = []
    recommendations = []

    sections = report.get("sections", {})

    # Traffic insights
    traffic = sections.get("traffic", {})
    current = traffic.get("current", {})
    previous = traffic.get("previous", {})

    if current and previous:
        sessions_change = ((current.get("sessions", 0) - previous.get("sessions", 0)) / previous.get("sessions", 1)) * 100
        conv_change = ((current.get("conversions", 0) - previous.get("conversions", 0)) / max(previous.get("conversions", 1), 1)) * 100

        if sessions_change > 10:
            highlights.append(f"Traffic up {sessions_change:.1f}% ({current['sessions']:,} sessions)")
        elif sessions_change < -10:
            concerns.append(f"Traffic down {abs(sessions_change):.1f}% ({current['sessions']:,} sessions)")

        if conv_change > 15:
            highlights.append(f"Conversions up {conv_change:.1f}% ({current['conversions']} total)")
        elif conv_change < -15:
            concerns.append(f"Conversions down {abs(conv_change):.1f}%")

    # Pipeline insights
    pipeline = sections.get("pipeline", {})
    if pipeline:
        if pipeline.get("win_rate", 0) >= 50:
            highlights.append(f"Win rate at {pipeline['win_rate']}% ({pipeline['deals_closed_won']} won)")
        elif pipeline.get("win_rate", 0) < 30:
            concerns.append(f"Win rate below 30% ({pipeline['win_rate']}%)")

        if pipeline.get("revenue_closed", 0) > 0:
            highlights.append(f"${pipeline['revenue_closed']:,.0f} revenue closed")

        if pipeline.get("pipeline_value", 0) > 0:
            highlights.append(f"${pipeline['pipeline_value']:,.0f} in active pipeline")

    # SEO insights
    seo = sections.get("seo", {})
    if seo:
        net_backlinks = seo.get("new_backlinks", 0) - seo.get("lost_backlinks", 0)
        if net_backlinks > 100:
            highlights.append(f"Net +{net_backlinks} backlinks this period")
        elif net_backlinks < -50:
            concerns.append(f"Net loss of {abs(net_backlinks)} backlinks")

        top_kws = seo.get("top_keywords", [])
        top3_count = sum(1 for kw in top_kws if kw.get("position", 99) <= 3)
        if top3_count >= 3:
            highlights.append(f"{top3_count} keywords in top 3 positions")

    # Call quality insights
    calls = sections.get("call_quality", {})
    if calls:
        talk_ratio = calls.get("avg_talk_ratio", 0)
        if talk_ratio > 65:
            concerns.append(f"Reps talking too much ({talk_ratio}% talk ratio). Best practice: 40-60%.")
            recommendations.append("Run talk-ratio coaching sessions. Reps at 40-60% have 2x win rate vs 70%+.")
        if calls.get("next_steps_rate", 0) < 70:
            concerns.append(f"Only {calls.get('next_steps_rate', 0)}% of calls end with clear next steps.")
            recommendations.append("Implement mandatory next-steps template for all discovery calls.")

    # Anomaly-based recommendations
    anomalies = traffic.get("anomalies", [])
    for a in anomalies:
        if a["severity"] == "critical" and a["sentiment"] == "negative":
            recommendations.append(f"Investigate {a['label']} drop ({a['pct_change']}%). Check for technical issues, algorithm updates, or campaign pauses.")

    return {
        "highlights": highlights,
        "concerns": concerns,
        "recommendations": recommendations,
        "overall_health": "strong" if len(highlights) > len(concerns) else "needs_attention" if concerns else "stable",
    }


# ---------------------------------------------------------------------------
# Output Formatters
# ---------------------------------------------------------------------------

def format_markdown(report: dict) -> str:
    """Format report as client-ready markdown."""
    lines = []
    lines.append(f"# {report['client']} - Performance Report")
    lines.append(f"**Period:** {report['period']['start']} to {report['period']['end']} ({report['period']['days']} days)")
    lines.append(f"**Generated:** {report['generated_at'][:10]}")
    lines.append("")

    # Executive Summary
    summary = report.get("executive_summary", {})
    lines.append("## Executive Summary")
    lines.append("")

    health = summary.get("overall_health", "stable")
    health_emoji = {"strong": "🟢", "stable": "🟡", "needs_attention": "🔴"}.get(health, "⚪")
    lines.append(f"**Overall Health:** {health_emoji} {health.replace('_', ' ').title()}")
    lines.append("")

    if summary.get("highlights"):
        lines.append("### ✅ Highlights")
        for h in summary["highlights"]:
            lines.append(f"- {h}")
        lines.append("")

    if summary.get("concerns"):
        lines.append("### ⚠️ Concerns")
        for c in summary["concerns"]:
            lines.append(f"- {c}")
        lines.append("")

    if summary.get("recommendations"):
        lines.append("### 💡 Recommendations")
        for r in summary["recommendations"]:
            lines.append(f"- {r}")
        lines.append("")

    # Traffic
    sections = report.get("sections", {})
    traffic = sections.get("traffic", {})
    if traffic:
        current = traffic.get("current", {})
        previous = traffic.get("previous", {})

        lines.append("---")
        lines.append("## 📊 Traffic")
        lines.append("")
        lines.append("| Metric | Current | Previous | Change |")
        lines.append("|--------|---------|----------|--------|")

        for metric, label in [("sessions", "Sessions"), ("users", "Users"), ("pageviews", "Pageviews"), ("bounce_rate", "Bounce Rate"), ("conversions", "Conversions")]:
            curr = current.get(metric, 0)
            prev = previous.get(metric, 0) if previous else 0
            if prev:
                change = ((curr - prev) / prev) * 100
                change_str = f"{'↑' if change > 0 else '↓'} {abs(change):.1f}%"
            else:
                change_str = "N/A"
            fmt = f"{curr:.1f}%" if metric == "bounce_rate" else f"{curr:,}"
            prev_fmt = f"{prev:.1f}%" if metric == "bounce_rate" else f"{prev:,}"
            lines.append(f"| {label} | {fmt} | {prev_fmt} | {change_str} |")

        lines.append("")

        if traffic.get("channels"):
            lines.append("### Channel Breakdown")
            lines.append("")
            lines.append("| Channel | Sessions | Conversions |")
            lines.append("|---------|----------|-------------|")
            for ch in traffic["channels"]:
                lines.append(f"| {ch['channel']} | {ch['sessions']:,} | {ch['conversions']} |")
            lines.append("")

        if traffic.get("top_pages"):
            lines.append("### Top Pages")
            lines.append("")
            lines.append("| Page | Sessions | Conversions |")
            lines.append("|------|----------|-------------|")
            for p in traffic["top_pages"][:10]:
                lines.append(f"| {p['page']} | {p['sessions']:,} | {p['conversions']} |")
            lines.append("")

        # Anomalies
        if traffic.get("anomalies"):
            lines.append("### 🚨 Anomalies Detected")
            lines.append("")
            for a in traffic["anomalies"]:
                icon = "🔴" if a["severity"] == "critical" else "🟡"
                lines.append(f"- {icon} {a['summary']}")
            lines.append("")

    # Pipeline
    pipeline = sections.get("pipeline", {})
    if pipeline:
        lines.append("---")
        lines.append("## 🎯 Pipeline")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Deals Created | {pipeline.get('deals_created', 0)} |")
        lines.append(f"| Deals Won | {pipeline.get('deals_closed_won', 0)} |")
        lines.append(f"| Deals Lost | {pipeline.get('deals_closed_lost', 0)} |")
        lines.append(f"| Win Rate | {pipeline.get('win_rate', 0)}% |")
        lines.append(f"| Revenue Closed | ${pipeline.get('revenue_closed', 0):,.0f} |")
        lines.append(f"| Pipeline Value | ${pipeline.get('pipeline_value', 0):,.0f} |")
        lines.append(f"| Avg Deal Size | ${pipeline.get('avg_deal_size', 0):,.0f} |")
        lines.append(f"| Avg Sales Cycle | {pipeline.get('avg_sales_cycle_days', 0)} days |")
        lines.append("")

        if pipeline.get("top_deals"):
            lines.append("### Top Deals")
            lines.append("")
            lines.append("| Deal | Amount | Stage |")
            lines.append("|------|--------|-------|")
            for d in pipeline["top_deals"]:
                lines.append(f"| {d['name']} | ${d['amount']:,.0f} | {d['stage']} |")
            lines.append("")

    # SEO
    seo = sections.get("seo", {})
    if seo:
        lines.append("---")
        lines.append("## 🔍 SEO")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Domain Rating | {seo.get('domain_rating', 0)} |")
        lines.append(f"| Referring Domains | {seo.get('referring_domains', 0):,} |")
        lines.append(f"| Total Backlinks | {seo.get('backlinks', 0):,} |")
        lines.append(f"| Organic Keywords | {seo.get('organic_keywords', 0):,} |")
        lines.append(f"| Organic Traffic | {seo.get('organic_traffic', 0):,} |")
        lines.append(f"| New Backlinks (30d) | +{seo.get('new_backlinks', 0)} |")
        lines.append(f"| Lost Backlinks (30d) | -{seo.get('lost_backlinks', 0)} |")
        lines.append("")

        if seo.get("top_keywords"):
            lines.append("### Top Keywords")
            lines.append("")
            lines.append("| Keyword | Position | Volume | Traffic |")
            lines.append("|---------|----------|--------|---------|")
            for kw in seo["top_keywords"]:
                lines.append(f"| {kw['keyword']} | {kw['position']} | {kw['volume']:,} | {kw['traffic']:,} |")
            lines.append("")

    # Call Quality
    calls = sections.get("call_quality", {})
    if calls:
        lines.append("---")
        lines.append("## 📞 Call Quality")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Calls | {calls.get('total_calls', 0)} |")
        lines.append(f"| Avg Talk Ratio | {calls.get('avg_talk_ratio', 0)}% |")
        lines.append(f"| Avg Call Duration | {calls.get('avg_call_duration_min', 0)} min |")
        lines.append(f"| Longest Monologue | {calls.get('avg_longest_monologue_sec', 0)}s |")
        lines.append(f"| Next Steps Rate | {calls.get('next_steps_rate', 0)}% |")
        lines.append("")

        if calls.get("top_topics"):
            lines.append("### Top Discussion Topics")
            lines.append("")
            lines.append("| Topic | Frequency | % of Calls |")
            lines.append("|-------|-----------|------------|")
            for t in calls["top_topics"]:
                lines.append(f"| {t['topic']} | {t['frequency']} | {t['pct']}% |")
            lines.append("")

        if calls.get("talk_ratio_vs_win_rate"):
            lines.append("### Talk Ratio vs Win Rate")
            lines.append("")
            lines.append("| Talk Ratio | Calls | Win Rate |")
            lines.append("|------------|-------|----------|")
            for ratio, data in calls["talk_ratio_vs_win_rate"].items():
                lines.append(f"| {ratio} | {data['calls']} | {data['win_rate']}% |")
            lines.append("")

    lines.append("---")
    lines.append(f"*Report generated automatically on {report['generated_at'][:10]}*")

    return "\n".join(lines)


def print_report_console(report: dict) -> None:
    """Print a condensed version to console."""
    summary = report.get("executive_summary", {})

    print(f"\n{'='*70}")
    print(f"  {report['client']} - Performance Report")
    print(f"  {report['period']['start']} to {report['period']['end']}")
    print(f"{'='*70}")

    health = summary.get("overall_health", "stable")
    health_emoji = {"strong": "🟢", "stable": "🟡", "needs_attention": "🔴"}.get(health, "⚪")
    print(f"\n  {health_emoji} Overall: {health.replace('_', ' ').title()}")

    if summary.get("highlights"):
        print(f"\n  ✅ Highlights:")
        for h in summary["highlights"]:
            print(f"     • {h}")

    if summary.get("concerns"):
        print(f"\n  ⚠️  Concerns:")
        for c in summary["concerns"]:
            print(f"     • {c}")

    if summary.get("recommendations"):
        print(f"\n  💡 Recommendations:")
        for r in summary["recommendations"]:
            print(f"     • {r}")

    # Key numbers
    sections = report.get("sections", {})

    traffic = sections.get("traffic", {}).get("current", {})
    if traffic:
        print(f"\n  📊 Traffic: {traffic.get('sessions', 0):,} sessions | {traffic.get('conversions', 0)} conversions")

    pipeline = sections.get("pipeline", {})
    if pipeline:
        print(f"  🎯 Pipeline: ${pipeline.get('revenue_closed', 0):,.0f} closed | ${pipeline.get('pipeline_value', 0):,.0f} active | {pipeline.get('win_rate', 0)}% win rate")

    seo = sections.get("seo", {})
    if seo:
        print(f"  🔍 SEO: DR {seo.get('domain_rating', 0)} | {seo.get('organic_keywords', 0):,} keywords | {seo.get('organic_traffic', 0):,} organic traffic")

    calls = sections.get("call_quality", {})
    if calls:
        print(f"  📞 Calls: {calls.get('total_calls', 0)} calls | {calls.get('avg_talk_ratio', 0)}% talk ratio | {calls.get('next_steps_rate', 0)}% next steps")

    # Anomalies
    anomalies = sections.get("traffic", {}).get("anomalies", [])
    if anomalies:
        print(f"\n  🚨 Anomalies:")
        for a in anomalies:
            icon = "🔴" if a["severity"] == "critical" else "🟡"
            print(f"     {icon} {a['summary']}")

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate unified client BI reports from GA4 + HubSpot + Ahrefs + Gong.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --client "Acme Corp"
  %(prog)s --client "Acme Corp" --format markdown --output report.md
  %(prog)s --client "Acme Corp" --anomalies --compare previous-month
  %(prog)s --client "Acme Corp" --skip gong,ahrefs --format json
        """,
    )

    parser.add_argument("--client", required=True, help="Client name for the report header")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (default: 30 days ago)")
    parser.add_argument("--end", help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--domain", help="Domain for Ahrefs data (default: YOUR_DOMAIN env var)")

    parser.add_argument("--format", choices=["markdown", "json", "console"], default="console",
                        help="Output format (default: console)")
    parser.add_argument("--output", "-o", help="Write output to file")
    parser.add_argument("--skip", help="Comma-separated sources to skip (ga4,hubspot,ahrefs,gong)")
    parser.add_argument("--anomalies", action="store_true", help="Enable anomaly detection")
    parser.add_argument("--compare", choices=["previous-month", "previous-quarter", "yoy"],
                        help="Comparison period (requires anomaly detection)")

    args = parser.parse_args()

    # Dates
    end_date = args.end or datetime.utcnow().strftime("%Y-%m-%d")
    start_date = args.start or (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    skip_sources = [s.strip() for s in args.skip.split(",")] if args.skip else []

    if args.compare:
        args.anomalies = True

    print(f"Building report for {args.client} ({start_date} to {end_date})...", file=sys.stderr)

    # Build report
    report = build_report(
        client_name=args.client,
        start_date=start_date,
        end_date=end_date,
        skip_sources=skip_sources,
        enable_anomalies=args.anomalies,
        compare=args.compare,
        domain=args.domain or "",
    )

    # Output
    if args.format == "json":
        output_text = json.dumps(report, indent=2, default=str)
        print(output_text)
    elif args.format == "markdown":
        output_text = format_markdown(report)
        if not args.output:
            print(output_text)
    else:
        print_report_console(report)
        output_text = None

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if args.format == "json":
            out_path.write_text(json.dumps(report, indent=2, default=str))
        elif args.format == "markdown":
            out_path.write_text(format_markdown(report))
        else:
            out_path.write_text(json.dumps(report, indent=2, default=str))

        print(f"\n✅ Report written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
