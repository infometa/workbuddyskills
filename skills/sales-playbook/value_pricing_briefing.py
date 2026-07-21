#!/usr/bin/env python3
"""
Value-Based Pricing: Pre-Call Briefing Generator

Takes a prospect's domain + competitor domains and outputs everything a
salesperson needs to anchor the conversation on value, not cost.

Usage:
    python3 value_pricing_briefing.py --domain acme.com --competitors "comp1.com,comp2.com"
    python3 value_pricing_briefing.py --domain acme.com --competitors "comp1.com" --industry saas --deal-target 80000
    python3 value_pricing_briefing.py --domain acme.com --competitors "comp1.com" --format json
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# API Stubs — Replace with real Ahrefs/SEMrush API calls when keys are available
# ---------------------------------------------------------------------------
# To integrate real APIs:
# 1. Set AHREFS_API_KEY or SEMRUSH_API_KEY environment variables
# 2. Replace the stub functions below with actual API calls
# 3. Ahrefs API docs: https://ahrefs.com/api
# 4. SEMrush API docs: https://developer.semrush.com/api/


def _fetch_domain_metrics(domain: str) -> dict:
    """
    Stub: Fetch domain authority, backlinks, and traffic estimates.

    In production, call:
        GET https://api.ahrefs.com/v3/site-explorer/domain-rating
        GET https://api.semrush.com/?type=domain_ranks&key=KEY&domain=DOMAIN
    """
    api_key = os.environ.get("AHREFS_API_KEY") or os.environ.get("SEMRUSH_API_KEY")
    if api_key:
        # TODO: Implement real API call here
        # import requests
        # resp = requests.get(f"https://api.ahrefs.com/v3/...", headers={"Authorization": f"Bearer {api_key}"})
        # return resp.json()
        pass

    # Stub data — deterministic seed from domain for consistency
    seed = sum(ord(c) for c in domain)
    rng = random.Random(seed)
    return {
        "domain": domain,
        "domain_authority": rng.randint(15, 85),
        "monthly_organic_traffic": rng.randint(5000, 500000),
        "total_keywords": rng.randint(500, 50000),
        "total_backlinks": rng.randint(1000, 200000),
        "top_keywords": [
            {"keyword": f"{domain.split('.')[0]} solutions", "position": rng.randint(1, 20), "volume": rng.randint(500, 10000), "cpc": round(rng.uniform(2.0, 25.0), 2)},
            {"keyword": f"best {domain.split('.')[0]} alternative", "position": rng.randint(5, 50), "volume": rng.randint(200, 5000), "cpc": round(rng.uniform(3.0, 30.0), 2)},
            {"keyword": f"{domain.split('.')[0]} pricing", "position": rng.randint(1, 30), "volume": rng.randint(300, 8000), "cpc": round(rng.uniform(5.0, 40.0), 2)},
            {"keyword": f"{domain.split('.')[0]} vs competitor", "position": rng.randint(3, 40), "volume": rng.randint(100, 3000), "cpc": round(rng.uniform(4.0, 35.0), 2)},
            {"keyword": f"{domain.split('.')[0]} reviews", "position": rng.randint(2, 25), "volume": rng.randint(400, 6000), "cpc": round(rng.uniform(1.5, 15.0), 2)},
        ],
    }


def _estimate_traffic_value(volume: int, current_pos: int, target_pos: int, cpc: float) -> dict:
    """Estimate additional traffic and value from ranking improvement."""
    # CTR curves by position (approximate)
    ctr_by_pos = {1: 0.32, 2: 0.24, 3: 0.18, 4: 0.13, 5: 0.10, 6: 0.07, 7: 0.05, 8: 0.04, 9: 0.03, 10: 0.025}
    current_ctr = ctr_by_pos.get(current_pos, max(0.005, 0.025 - (current_pos - 10) * 0.001))
    target_ctr = ctr_by_pos.get(target_pos, max(0.005, 0.025 - (target_pos - 10) * 0.001))
    current_traffic = int(volume * current_ctr)
    target_traffic = int(volume * target_ctr)
    additional_traffic = max(0, target_traffic - current_traffic)
    monthly_value = round(additional_traffic * cpc, 2)
    return {
        "current_position": current_pos,
        "target_position": target_pos,
        "search_volume": volume,
        "current_monthly_traffic": current_traffic,
        "projected_monthly_traffic": target_traffic,
        "additional_monthly_traffic": additional_traffic,
        "cpc": cpc,
        "monthly_paid_equivalent": monthly_value,
        "annual_paid_equivalent": round(monthly_value * 12, 2),
    }


# ---------------------------------------------------------------------------
# Briefing Generation
# ---------------------------------------------------------------------------

CONVERSATION_HOOKS = [
    "What's your current strategy for [top_keyword]? I noticed some interesting gaps there.",
    "When you look at your competitive landscape for organic search, what concerns you most?",
    "If you could rank #1 for one keyword tomorrow, which would move the revenue needle most?",
    "How much are you currently spending on paid search for terms you could be ranking organically?",
    "What would it mean for your pipeline if you captured even 20% of the traffic your top competitor gets?",
    "I pulled some data before our call. Mind if I share what I found about your organic presence vs. [competitor]?",
    "Your competitor just passed you on [keyword]. Have you noticed the traffic shift?",
    "What does your content production look like right now? I want to understand where the bottleneck is.",
]

OBJECTION_RESPONSES = {
    "price_too_high": {
        "objection": "That's more than we were expecting to spend.",
        "response": "I hear you. Let me reframe: your competitor is capturing $X/mo in organic traffic value that you're not. The question isn't whether $Y/mo is expensive; it's whether leaving $X/mo on the table is more expensive. Let me show you the math.",
        "key_principle": "Redirect from cost to cost-of-inaction",
    },
    "need_to_think": {
        "objection": "We need to think about it / discuss internally.",
        "response": "Absolutely. To help that internal conversation, I'll send over the competitive analysis we reviewed. One thing worth noting: [competitor] is actively investing in the keywords we discussed. Every month of deliberation is a month they're building a wider moat.",
        "key_principle": "Create urgency with competitor data, not pressure",
    },
    "already_doing_seo": {
        "objection": "We already have someone doing SEO.",
        "response": "Great. What are they focused on? The reason I ask is that the data shows [specific gap]. If that's being addressed, fantastic. If not, it might be worth a conversation about where the current strategy is leaving value on the table.",
        "key_principle": "Don't attack their current vendor; question the results",
    },
    "can_do_internally": {
        "objection": "We think we can handle this in-house.",
        "response": "In-house is great when you have the bandwidth. The gap we identified represents [X keywords / $Y in traffic value]. To close it, you'd need roughly [estimate] hours/month of specialized work. Hiring for that takes 3-6 months. We can bridge the gap while you build the team, or complement what you have.",
        "key_principle": "Bridge offer + acknowledge their capability",
    },
    "show_me_results": {
        "objection": "Can you show me results from similar companies?",
        "response": "Absolutely. We have a client in a similar space who went from ranking for ~Z keywords to over [Z*3] in 8 months. Their organic traffic value went from $A/mo to $B/mo. Happy to connect you with them if that would help.",
        "key_principle": "Reference customer drop with specific (anonymized) numbers",
    },
    "budget_locked": {
        "objection": "Our budget is already allocated for this quarter.",
        "response": "Understood. Two thoughts: first, our baseline tier starts at [$X], which might fit within discretionary budget. Second, if we start with a focused engagement on your top 3 keyword gaps, I can show ROI within 60 days that makes the case for a larger Q2 investment. Sometimes the best way to unlock budget is to prove the model.",
        "key_principle": "Offer a smaller entry point tied to provable ROI",
    },
}


def generate_briefing(domain: str, competitors: list, industry: str = None, deal_target: int = 50000) -> dict:
    """Generate a complete pre-call briefing."""
    # Fetch metrics for all domains
    prospect_metrics = _fetch_domain_metrics(domain)
    competitor_metrics = [_fetch_domain_metrics(c) for c in competitors]

    # Build anchor data points
    anchors = []
    for comp in competitor_metrics:
        keyword_gap = comp["total_keywords"] - prospect_metrics["total_keywords"]
        traffic_gap = comp["monthly_organic_traffic"] - prospect_metrics["monthly_organic_traffic"]
        if keyword_gap > 0:
            anchors.append({
                "type": "keyword_gap",
                "message": f"You rank for {prospect_metrics['total_keywords']:,} keywords. {comp['domain']} ranks for {comp['total_keywords']:,}. Gap: {keyword_gap:,} keywords.",
                "severity": "high" if keyword_gap > 5000 else "medium",
            })
        if traffic_gap > 0:
            anchors.append({
                "type": "traffic_gap",
                "message": f"{comp['domain']} gets ~{comp['monthly_organic_traffic']:,} organic visits/mo vs. your ~{prospect_metrics['monthly_organic_traffic']:,}. That's {traffic_gap:,} visits you're leaving on the table.",
                "severity": "high" if traffic_gap > 50000 else "medium",
            })

    # Build competitive triggers
    triggers = []
    for comp in competitor_metrics:
        for kw in comp["top_keywords"]:
            # Find matching keyword in prospect
            for pkw in prospect_metrics["top_keywords"]:
                if pkw["keyword"].split()[-1] == kw["keyword"].split()[-1]:
                    if kw["position"] < pkw["position"]:
                        triggers.append({
                            "keyword": kw["keyword"],
                            "competitor": comp["domain"],
                            "competitor_position": kw["position"],
                            "prospect_position": pkw["position"],
                            "message": f"{comp['domain']} is #{kw['position']} for '{kw['keyword']}'. You're #{pkw['position']}.",
                        })

    # Build value calculations
    value_calcs = []
    for kw in prospect_metrics["top_keywords"]:
        if kw["position"] > 5:
            target_pos = min(3, kw["position"])
            calc = _estimate_traffic_value(kw["volume"], kw["position"], target_pos, kw["cpc"])
            calc["keyword"] = kw["keyword"]
            if calc["monthly_paid_equivalent"] > 100:
                value_calcs.append(calc)

    # Sort value calcs by monthly value
    value_calcs.sort(key=lambda x: x["monthly_paid_equivalent"], reverse=True)

    # Total value opportunity
    total_monthly_value = sum(v["monthly_paid_equivalent"] for v in value_calcs)
    total_annual_value = sum(v["annual_paid_equivalent"] for v in value_calcs)

    # Select conversation hooks (pick 4 most relevant)
    hooks = random.Random(sum(ord(c) for c in domain)).sample(CONVERSATION_HOOKS, min(4, len(CONVERSATION_HOOKS)))
    # Personalize hooks
    if competitor_metrics:
        hooks = [h.replace("[competitor]", competitors[0]) for h in hooks]
    if value_calcs:
        hooks = [h.replace("[top_keyword]", value_calcs[0]["keyword"]) for h in hooks]

    # Build objection pre-empts based on deal size
    relevant_objections = {}
    if deal_target >= 50000:
        relevant_objections["price_too_high"] = OBJECTION_RESPONSES["price_too_high"]
        relevant_objections["need_to_think"] = OBJECTION_RESPONSES["need_to_think"]
    if deal_target >= 30000:
        relevant_objections["can_do_internally"] = OBJECTION_RESPONSES["can_do_internally"]
        relevant_objections["show_me_results"] = OBJECTION_RESPONSES["show_me_results"]
    relevant_objections["already_doing_seo"] = OBJECTION_RESPONSES["already_doing_seo"]
    relevant_objections["budget_locked"] = OBJECTION_RESPONSES["budget_locked"]

    # Fill in dynamic values in objection responses
    for key, obj in relevant_objections.items():
        obj = dict(obj)  # copy
        if total_monthly_value > 0:
            obj["response"] = obj["response"].replace("$X/mo", f"${total_monthly_value:,.0f}/mo")
            obj["response"] = obj["response"].replace("$Y/mo", f"${deal_target:,}/mo")
        relevant_objections[key] = obj

    briefing = {
        "generated_at": datetime.now().isoformat(),
        "prospect": {
            "domain": domain,
            "industry": industry,
            "deal_target": deal_target,
            "metrics": prospect_metrics,
        },
        "competitors": [{"domain": c, "metrics": m} for c, m in zip(competitors, competitor_metrics)],
        "anchor_data_points": anchors,
        "competitive_triggers": triggers,
        "value_calculations": value_calcs,
        "total_opportunity": {
            "monthly_paid_equivalent": round(total_monthly_value, 2),
            "annual_paid_equivalent": round(total_annual_value, 2),
            "roi_multiple": round(total_annual_value / (deal_target * 12), 1) if deal_target > 0 else 0,
        },
        "conversation_hooks": hooks,
        "objection_preempts": relevant_objections,
    }

    return briefing


def format_markdown(briefing: dict) -> str:
    """Format briefing as readable markdown."""
    lines = []
    p = briefing["prospect"]
    lines.append(f"# Pre-Call Briefing: {p['domain']}")
    lines.append(f"*Generated: {briefing['generated_at']}*")
    lines.append(f"*Target deal: ${p['deal_target']:,}/mo | Industry: {p.get('industry') or 'Not specified'}*")
    lines.append("")

    # Prospect snapshot
    m = p["metrics"]
    lines.append("## Prospect Snapshot")
    lines.append(f"- **Domain Authority:** {m['domain_authority']}")
    lines.append(f"- **Monthly Organic Traffic:** {m['monthly_organic_traffic']:,}")
    lines.append(f"- **Total Keywords:** {m['total_keywords']:,}")
    lines.append(f"- **Total Backlinks:** {m['total_backlinks']:,}")
    lines.append("")

    # Competitor comparison
    if briefing["competitors"]:
        lines.append("## Competitor Comparison")
        lines.append("| Metric | " + p["domain"] + " | " + " | ".join(c["domain"] for c in briefing["competitors"]) + " |")
        lines.append("|--------|" + "--------|" * (1 + len(briefing["competitors"])))
        lines.append(f"| DA | {m['domain_authority']} | " + " | ".join(str(c["metrics"]["domain_authority"]) for c in briefing["competitors"]) + " |")
        lines.append(f"| Traffic | {m['monthly_organic_traffic']:,} | " + " | ".join(f"{c['metrics']['monthly_organic_traffic']:,}" for c in briefing["competitors"]) + " |")
        lines.append(f"| Keywords | {m['total_keywords']:,} | " + " | ".join(f"{c['metrics']['total_keywords']:,}" for c in briefing["competitors"]) + " |")
        lines.append("")

    # Anchor data points
    if briefing["anchor_data_points"]:
        lines.append("## 🎯 Anchor Data Points")
        lines.append("*Lead with these. Let the gaps sell the urgency.*")
        lines.append("")
        for a in briefing["anchor_data_points"]:
            icon = "🔴" if a["severity"] == "high" else "🟡"
            lines.append(f"- {icon} {a['message']}")
        lines.append("")

    # Competitive triggers
    if briefing["competitive_triggers"]:
        lines.append("## ⚡ Competitive Triggers")
        lines.append("*Use these to activate competitive instinct.*")
        lines.append("")
        for t in briefing["competitive_triggers"]:
            lines.append(f"- **{t['keyword']}**: {t['message']}")
        lines.append("")

    # Value calculations
    if briefing["value_calculations"]:
        lines.append("## 💰 Value Calculations")
        lines.append("*Make the ROI visual and obvious.*")
        lines.append("")
        for v in briefing["value_calculations"]:
            lines.append(f"### '{v['keyword']}'")
            lines.append(f"- Current: position #{v['current_position']} → {v['current_monthly_traffic']:,} visits/mo")
            lines.append(f"- Target: position #{v['target_position']} → {v['projected_monthly_traffic']:,} visits/mo")
            lines.append(f"- **Additional traffic: +{v['additional_monthly_traffic']:,} visits/mo**")
            lines.append(f"- **Paid equivalent: ${v['monthly_paid_equivalent']:,.0f}/mo (${v['annual_paid_equivalent']:,.0f}/yr)**")
            lines.append("")

        opp = briefing["total_opportunity"]
        lines.append(f"### Total Opportunity")
        lines.append(f"- Monthly traffic value: **${opp['monthly_paid_equivalent']:,.0f}/mo**")
        lines.append(f"- Annual traffic value: **${opp['annual_paid_equivalent']:,.0f}/yr**")
        lines.append(f"- ROI multiple at ${p['deal_target']:,}/mo investment: **{opp['roi_multiple']}x**")
        lines.append("")

    # Conversation hooks
    lines.append("## 🎣 Conversation Hooks")
    lines.append("*Opening questions to surface pain and anchor on value.*")
    lines.append("")
    for i, h in enumerate(briefing["conversation_hooks"], 1):
        lines.append(f"{i}. \"{h}\"")
    lines.append("")

    # Objection pre-empts
    lines.append("## 🛡️ Objection Pre-Empts")
    lines.append("")
    for key, obj in briefing["objection_preempts"].items():
        lines.append(f"### \"{obj['objection']}\"")
        lines.append(f"**Response:** {obj['response']}")
        lines.append(f"*Principle: {obj['key_principle']}*")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Value-Based Pricing: Pre-Call Briefing Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 value_pricing_briefing.py --domain acme.com --competitors "comp1.com,comp2.com"
  python3 value_pricing_briefing.py --domain acme.com --competitors "comp1.com" --industry saas --deal-target 80000
  python3 value_pricing_briefing.py --domain acme.com --competitors "comp1.com" --format json
        """,
    )
    parser.add_argument("--domain", required=True, help="Prospect's domain (e.g., acme.com)")
    parser.add_argument("--competitors", required=True, help="Comma-separated competitor domains (e.g., 'comp1.com,comp2.com')")
    parser.add_argument("--industry", default=None, help="Prospect's industry (e.g., saas, ecommerce, fintech)")
    parser.add_argument("--deal-target", type=int, default=50000, help="Target monthly deal size in dollars (default: 50000)")
    parser.add_argument("--format", choices=["markdown", "json", "both"], default="markdown", help="Output format (default: markdown)")

    args = parser.parse_args()
    competitors = [c.strip() for c in args.competitors.split(",") if c.strip()]

    briefing = generate_briefing(
        domain=args.domain,
        competitors=competitors,
        industry=args.industry,
        deal_target=args.deal_target,
    )

    if args.format == "json":
        print(json.dumps(briefing, indent=2))
    elif args.format == "both":
        print(format_markdown(briefing))
        print("\n---\n## Raw JSON\n")
        print(json.dumps(briefing, indent=2))
    else:
        print(format_markdown(briefing))


if __name__ == "__main__":
    main()
