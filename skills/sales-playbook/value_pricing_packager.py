#!/usr/bin/env python3
"""
Value-Based Pricing: Tiered Package Builder

Input a target deal size and services → auto-generates S/M/L + performance-based
pricing tiers using value-based pricing principles.

Psychology: Anchor high (Powerhouse), present the real target second (Value),
create a floor (Baseline), and offer skin-in-the-game (Performance).

Usage:
    python3 value_pricing_packager.py --target-monthly 80000 --services "seo,cro,content,paid"
    python3 value_pricing_packager.py --target-monthly 50000 --services "seo,content" --current-spend 10000
    python3 value_pricing_packager.py --target-monthly 80000 --services "seo,cro,content,paid" --format json
"""

import argparse
import json
import math
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Service Deliverable Definitions
# ---------------------------------------------------------------------------
# Each service has deliverables scaled by tier multiplier.
# Format: (deliverable_name, base_quantity, unit, scales_with_tier)

SERVICE_DELIVERABLES = {
    "seo": {
        "name": "Search Engine Optimization",
        "deliverables": [
            ("Technical SEO audits", 1, "per quarter", False),
            ("Keyword strategy & mapping", 50, "keywords/mo", True),
            ("On-page optimization", 15, "pages/mo", True),
            ("Link building / digital PR", 10, "placements/mo", True),
            ("Competitive gap analysis", 1, "per month", False),
            ("Monthly performance reporting", 1, "report/mo", False),
            ("Strategic SEO roadmap", 1, "per quarter", False),
        ],
        "base_cost_pct": 0.30,  # Percentage of tier price allocated to this service
    },
    "cro": {
        "name": "Conversion Rate Optimization",
        "deliverables": [
            ("CRO audit & heatmap analysis", 1, "per quarter", False),
            ("A/B test design & execution", 3, "tests/mo", True),
            ("Landing page optimization", 4, "pages/mo", True),
            ("Funnel analysis & recommendations", 1, "per month", False),
            ("User behavior analysis", 1, "per month", False),
            ("Conversion lift reporting", 1, "report/mo", False),
        ],
        "base_cost_pct": 0.20,
    },
    "content": {
        "name": "Content Marketing",
        "deliverables": [
            ("Content strategy & editorial calendar", 1, "per month", False),
            ("Long-form blog posts (2000+ words)", 8, "posts/mo", True),
            ("Content briefs with keyword targeting", 10, "briefs/mo", True),
            ("Content refresh & optimization", 5, "posts/mo", True),
            ("Social content repurposing", 10, "pieces/mo", True),
            ("Thought leadership pieces", 2, "pieces/mo", True),
        ],
        "base_cost_pct": 0.25,
    },
    "paid": {
        "name": "Paid Media Management",
        "deliverables": [
            ("Campaign strategy & setup", 1, "per quarter", False),
            ("Ad creative development", 10, "creatives/mo", True),
            ("Audience research & targeting", 1, "per month", False),
            ("Bid management & optimization", 1, "ongoing", False),
            ("A/B testing (ad copy & creative)", 5, "tests/mo", True),
            ("Cross-channel attribution reporting", 1, "report/mo", False),
            ("Budget allocation optimization", 1, "per month", False),
        ],
        "base_cost_pct": 0.25,
    },
}

# ---------------------------------------------------------------------------
# Tier Definitions
# ---------------------------------------------------------------------------

TIER_CONFIGS = {
    "powerhouse": {
        "name": "Powerhouse",
        "subtitle": "Maximum growth, maximum impact",
        "multiplier_range": (1.30, 1.50),
        "deliverable_scale": 2.0,
        "description": "Full-service engagement with senior strategic involvement, dedicated team, and aggressive growth targets. For companies ready to dominate their market.",
        "extras": [
            "Dedicated senior strategist (weekly 1:1)",
            "C-suite quarterly business reviews",
            "Priority support (4-hour SLA)",
            "Custom dashboard & real-time reporting",
            "Competitive intelligence briefings (monthly)",
        ],
        "excluded": [],
    },
    "value": {
        "name": "Value",
        "subtitle": "The sweet spot: high impact, smart investment",
        "multiplier_range": (1.0, 1.0),
        "deliverable_scale": 1.0,
        "description": "Our recommended engagement. Covers all critical growth levers with a proven team and methodology. Where most of our successful clients land.",
        "extras": [
            "Senior strategist oversight (bi-weekly)",
            "Monthly executive summary",
            "Standard support (24-hour SLA)",
        ],
        "excluded": [
            "Dedicated senior strategist 1:1s (Powerhouse only)",
            "Real-time custom dashboard (Powerhouse only)",
        ],
    },
    "baseline": {
        "name": "Baseline",
        "subtitle": "Foundation for growth",
        "multiplier_range": (0.40, 0.50),
        "deliverable_scale": 0.5,
        "description": "Focused engagement on your highest-impact channels. Ideal for proving the model before scaling, or for companies with some in-house capability.",
        "extras": [
            "Monthly strategy call",
            "Standard reporting",
        ],
        "excluded": [
            "Senior strategist involvement (Value+ only)",
            "Multi-channel optimization (Value+ only)",
            "Competitive intelligence (Powerhouse only)",
            "A/B testing programs (Value+ only)",
        ],
    },
    "performance": {
        "name": "Performance",
        "subtitle": "We eat what we kill",
        "multiplier_range": (0.30, 0.40),  # Base is lower
        "deliverable_scale": 0.75,
        "description": "Lower base investment + performance bonuses tied to outcomes. We put skin in the game. Aligns incentives so we only win when you win.",
        "extras": [
            "Performance bonus triggers tied to KPIs",
            "Monthly strategy call",
            "Transparent KPI dashboard",
        ],
        "excluded": [
            "Senior strategist 1:1s (Powerhouse only)",
            "Guaranteed deliverable volumes (see performance tiers)",
        ],
        "bonus_triggers": [
            {"trigger": "Organic traffic increases 50%+ from baseline", "bonus_pct": 0.15},
            {"trigger": "Conversion rate improves 25%+ from baseline", "bonus_pct": 0.10},
            {"trigger": "Revenue attributed to organic exceeds 3x monthly investment", "bonus_pct": 0.20},
            {"trigger": "Rank #1-3 for 5+ target money keywords", "bonus_pct": 0.10},
        ],
    },
}


def _scale_deliverables(service_key: str, scale: float, tier_price: float) -> list:
    """Scale service deliverables based on tier."""
    service = SERVICE_DELIVERABLES[service_key]
    scaled = []
    for name, base_qty, unit, scales in service["deliverables"]:
        qty = math.ceil(base_qty * scale) if scales else base_qty
        scaled.append({"deliverable": name, "quantity": qty, "unit": unit})
    return scaled


def _calculate_roi_projection(monthly_price: float, services: list) -> dict:
    """Generate ROI projection based on investment level and services."""
    # Conservative multiplier based on service combination
    base_multiplier = 3.0
    if "seo" in services and "cro" in services:
        base_multiplier += 1.5  # Compounding effect
    if "content" in services and "seo" in services:
        base_multiplier += 1.0
    if len(services) >= 3:
        base_multiplier += 0.5  # Full-stack bonus

    annual_investment = monthly_price * 12
    projected_return = annual_investment * base_multiplier

    return {
        "monthly_investment": monthly_price,
        "annual_investment": annual_investment,
        "projected_annual_return": round(projected_return, 0),
        "roi_multiple": round(base_multiplier, 1),
        "payback_period_months": round(12 / base_multiplier, 1),
        "projection_basis": "Based on median outcomes across similar engagements (anonymized). Individual results vary based on market, competition, and execution.",
    }


def generate_packages(target_monthly: int, services: list, current_spend: int = 0) -> dict:
    """Generate all 4 pricing tiers."""
    packages = {"generated_at": datetime.now().isoformat(), "target_monthly": target_monthly, "services": services, "current_spend": current_spend, "tiers": {}}

    for tier_key, config in TIER_CONFIGS.items():
        low, high = config["multiplier_range"]
        multiplier = (low + high) / 2
        monthly_price = int(round(target_monthly * multiplier, -2))  # Round to nearest 100

        # Build deliverables per service
        tier_deliverables = {}
        for svc in services:
            if svc in SERVICE_DELIVERABLES:
                tier_deliverables[svc] = {
                    "service_name": SERVICE_DELIVERABLES[svc]["name"],
                    "deliverables": _scale_deliverables(svc, config["deliverable_scale"], monthly_price),
                }

        tier = {
            "name": config["name"],
            "subtitle": config["subtitle"],
            "description": config["description"],
            "monthly_price": monthly_price,
            "annual_price": monthly_price * 12,
            "vs_target": f"{multiplier * 100:.0f}%",
            "deliverables_by_service": tier_deliverables,
            "included_extras": config["extras"],
            "not_included": config["excluded"],
            "roi_projection": _calculate_roi_projection(monthly_price, services),
        }

        # Add performance bonus info
        if tier_key == "performance":
            tier["bonus_structure"] = {
                "base_monthly": monthly_price,
                "triggers": config["bonus_triggers"],
                "max_monthly_with_bonuses": round(monthly_price * 1.55, -2),
                "note": "Bonuses are additive. If all triggers hit, total monthly = base + sum of bonus percentages applied to base.",
            }

        # Add context vs current spend
        if current_spend > 0:
            tier["vs_current_spend"] = {
                "current": current_spend,
                "proposed": monthly_price,
                "difference": monthly_price - current_spend,
                "increase_pct": round((monthly_price - current_spend) / current_spend * 100, 0),
            }

        packages["tiers"][tier_key] = tier

    return packages


def format_markdown(packages: dict) -> str:
    """Format packages as a proposal-ready markdown document."""
    lines = []
    lines.append("# Investment Options")
    lines.append(f"*Prepared: {packages['generated_at'][:10]}*")
    lines.append(f"*Services: {', '.join(s.upper() for s in packages['services'])}*")
    lines.append("")

    if packages["current_spend"] > 0:
        lines.append(f"> Current monthly investment: ${packages['current_spend']:,}")
        lines.append("")

    # Summary table
    lines.append("## Package Overview")
    lines.append("")
    lines.append("| | Powerhouse | Value ⭐ | Baseline | Performance |")
    lines.append("|---|---|---|---|---|")

    tiers = packages["tiers"]
    lines.append(f"| Monthly | ${tiers['powerhouse']['monthly_price']:,} | ${tiers['value']['monthly_price']:,} | ${tiers['baseline']['monthly_price']:,} | ${tiers['performance']['monthly_price']:,} base |")
    lines.append(f"| Annual | ${tiers['powerhouse']['annual_price']:,} | ${tiers['value']['annual_price']:,} | ${tiers['baseline']['annual_price']:,} | ${tiers['performance']['annual_price']:,}+ |")
    lines.append(f"| ROI Multiple | {tiers['powerhouse']['roi_projection']['roi_multiple']}x | {tiers['value']['roi_projection']['roi_multiple']}x | {tiers['baseline']['roi_projection']['roi_multiple']}x | {tiers['performance']['roi_projection']['roi_multiple']}x+ |")
    lines.append("")

    # Detailed tiers
    for tier_key in ["powerhouse", "value", "baseline", "performance"]:
        tier = tiers[tier_key]
        star = " ⭐ Recommended" if tier_key == "value" else ""
        lines.append(f"---")
        lines.append(f"## {tier['name']}{star}")
        lines.append(f"### *{tier['subtitle']}*")
        lines.append(f"**${tier['monthly_price']:,}/mo** (${tier['annual_price']:,}/yr)")
        lines.append("")
        lines.append(tier["description"])
        lines.append("")

        # Deliverables
        for svc_key, svc_data in tier["deliverables_by_service"].items():
            lines.append(f"#### {svc_data['service_name']}")
            for d in svc_data["deliverables"]:
                lines.append(f"- {d['deliverable']}: **{d['quantity']} {d['unit']}**")
            lines.append("")

        # Extras
        if tier["included_extras"]:
            lines.append("**Also included:**")
            for e in tier["included_extras"]:
                lines.append(f"- ✅ {e}")
            lines.append("")

        # Not included
        if tier["not_included"]:
            lines.append("**Not included in this tier:**")
            for e in tier["not_included"]:
                lines.append(f"- ❌ {e}")
            lines.append("")

        # Performance bonus details
        if tier_key == "performance" and "bonus_structure" in tier:
            bs = tier["bonus_structure"]
            lines.append("**Performance Bonus Triggers:**")
            for bt in bs["triggers"]:
                lines.append(f"- 🎯 {bt['trigger']} → +{bt['bonus_pct'] * 100:.0f}% of base")
            lines.append(f"- Max monthly (all bonuses): **${bs['max_monthly_with_bonuses']:,}**")
            lines.append("")

        # ROI
        roi = tier["roi_projection"]
        lines.append(f"**ROI Projection:**")
        lines.append(f"- Annual investment: ${roi['annual_investment']:,}")
        lines.append(f"- Projected annual return: ${roi['projected_annual_return']:,.0f}")
        lines.append(f"- ROI multiple: {roi['roi_multiple']}x")
        lines.append(f"- Payback period: {roi['payback_period_months']} months")
        lines.append(f"- *{roi['projection_basis']}*")
        lines.append("")

        # Vs current spend
        if "vs_current_spend" in tier:
            vs = tier["vs_current_spend"]
            lines.append(f"**vs. Current Spend:**")
            direction = "increase" if vs["difference"] > 0 else "decrease"
            lines.append(f"- Current: ${vs['current']:,}/mo → Proposed: ${vs['proposed']:,}/mo ({vs['increase_pct']:+.0f}% {direction})")
            lines.append("")

    # Pricing philosophy note
    lines.append("---")
    lines.append("## Why These Tiers?")
    lines.append("")
    lines.append("We believe pricing should reflect value, not hours. Each tier is designed around outcomes:")
    lines.append("- **Powerhouse** is for companies ready to make an aggressive move and want senior strategic involvement at every level.")
    lines.append("- **Value** is where most of our successful clients land. It covers all critical growth levers without over-investing before proving the model.")
    lines.append("- **Baseline** is a focused starting point. Prove the ROI, then scale.")
    lines.append("- **Performance** aligns our incentives with yours. We only win when you win.")
    lines.append("")
    lines.append("*We recommend starting the conversation with what success looks like for your business, then working backward to the right investment level.*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Value-Based Pricing: Tiered Package Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 value_pricing_packager.py --target-monthly 80000 --services "seo,cro,content,paid"
  python3 value_pricing_packager.py --target-monthly 50000 --services "seo,content" --current-spend 10000
  python3 value_pricing_packager.py --target-monthly 80000 --services "seo,cro,content,paid" --format json
        """,
    )
    parser.add_argument("--target-monthly", type=int, required=True, help="Target monthly deal size in dollars")
    parser.add_argument("--services", required=True, help="Comma-separated services (seo,cro,content,paid)")
    parser.add_argument("--current-spend", type=int, default=0, help="Prospect's current monthly marketing spend")
    parser.add_argument("--format", choices=["markdown", "json", "both"], default="markdown", help="Output format (default: markdown)")

    args = parser.parse_args()
    services = [s.strip().lower() for s in args.services.split(",") if s.strip()]

    # Validate services
    valid_services = set(SERVICE_DELIVERABLES.keys())
    invalid = [s for s in services if s not in valid_services]
    if invalid:
        print(f"Error: Unknown services: {', '.join(invalid)}", file=sys.stderr)
        print(f"Valid services: {', '.join(sorted(valid_services))}", file=sys.stderr)
        sys.exit(1)

    packages = generate_packages(
        target_monthly=args.target_monthly,
        services=services,
        current_spend=args.current_spend,
    )

    if args.format == "json":
        print(json.dumps(packages, indent=2))
    elif args.format == "both":
        print(format_markdown(packages))
        print("\n---\n## Raw JSON\n")
        print(json.dumps(packages, indent=2))
    else:
        print(format_markdown(packages))


if __name__ == "__main__":
    main()
