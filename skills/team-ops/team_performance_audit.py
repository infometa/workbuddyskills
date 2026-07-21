#!/usr/bin/env python3
"""
Team Performance Audit — The "Elon Algorithm"

A ruthless, structured team performance evaluation framework.
5-step analysis → individual scorecards → stack rank → recommended actions.

The 5 Steps:
  1. Question every requirement — is this role/task actually necessary?
  2. Delete redundant processes — flag overlap between team members
  3. Simplify — identify overcomplicated workflows
  4. Accelerate — find bottlenecks slowing the team
  5. Automate — flag tasks that AI/automation could handle

Usage:
  # Analyze from JSON input
  python3 team_performance_audit.py --input team_data.json --output report.md

  # Analyze from CSV
  python3 team_performance_audit.py --input team_data.csv --output report.md

  # Dry run (print to stdout, no LLM calls)
  python3 team_performance_audit.py --input team_data.json --dry-run

  # JSON output instead of markdown
  python3 team_performance_audit.py --input team_data.json --format json --output report.json

Input format (JSON):
  {
    "team_members": [
      {
        "name": "Alice Chen",
        "role": "Senior Engineer",
        "role_description": "Owns backend API development and database optimization",
        "okrs": [
          {"objective": "Reduce API latency", "key_result": "P95 < 200ms", "progress": 0.85}
        ],
        "metrics": {
          "tasks_completed": 47,
          "tasks_assigned": 52,
          "avg_completion_days": 3.2,
          "quality_score": 92,
          "peer_feedback_score": 4.5,
          "initiatives_proposed": 3,
          "initiatives_shipped": 2
        },
        "deliverables": [
          {"name": "API v2 Migration", "status": "completed", "date": "2024-02-15"},
          {"name": "DB Index Optimization", "status": "completed", "date": "2024-03-01"}
        ]
      }
    ],
    "org_context": {
      "company_goals": ["Ship v3 by Q2", "Reduce infrastructure costs 30%"],
      "team_size": 12,
      "evaluation_period": "Q1 2024"
    }
  }

Input format (CSV):
  name,role,tasks_completed,tasks_assigned,avg_completion_days,quality_score,peer_feedback_score,initiatives_proposed,initiatives_shipped
  Alice Chen,Senior Engineer,47,52,3.2,92,4.5,3,2
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# LLM Integration (stubs with real API structure)
# ---------------------------------------------------------------------------

def call_llm(prompt: str, system_prompt: str = "") -> str:
    """
    Call the configured LLM provider for analysis.

    Supports Anthropic (Claude) and OpenAI (GPT-4).
    Set LLM_PROVIDER env var to 'anthropic' or 'openai'.
    Set the corresponding API key env var.

    Returns the LLM response text, or a placeholder if no API key is set.
    """
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    model = os.getenv("LLM_MODEL", "")

    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            return _fallback_analysis(prompt)

        # --- Anthropic API call ---
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=model or "claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt or "You are an expert organizational analyst and management consultant.",
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except ImportError:
            print("Warning: 'anthropic' package not installed. Using fallback analysis.", file=sys.stderr)
            return _fallback_analysis(prompt)
        except Exception as e:
            print(f"Warning: Anthropic API error: {e}. Using fallback analysis.", file=sys.stderr)
            return _fallback_analysis(prompt)

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return _fallback_analysis(prompt)

        # --- OpenAI API call ---
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model or "gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt or "You are an expert organizational analyst and management consultant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except ImportError:
            print("Warning: 'openai' package not installed. Using fallback analysis.", file=sys.stderr)
            return _fallback_analysis(prompt)
        except Exception as e:
            print(f"Warning: OpenAI API error: {e}. Using fallback analysis.", file=sys.stderr)
            return _fallback_analysis(prompt)

    else:
        print(f"Warning: Unknown LLM provider '{provider}'. Using fallback.", file=sys.stderr)
        return _fallback_analysis(prompt)


def _fallback_analysis(prompt: str) -> str:
    """Fallback when no LLM API is available. Returns a notice."""
    return (
        "[LLM analysis unavailable — set ANTHROPIC_API_KEY or OPENAI_API_KEY]\n"
        "The quantitative scores below are computed locally. "
        "For qualitative analysis (redundancy detection, simplification recommendations, "
        "automation opportunities), configure an LLM provider."
    )


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_json_input(filepath: str) -> dict:
    """Load team data from a JSON file."""
    with open(filepath, "r") as f:
        data = json.load(f)

    if "team_members" not in data:
        raise ValueError("JSON input must contain a 'team_members' array.")
    return data


def load_csv_input(filepath: str) -> dict:
    """
    Load team data from a CSV file.

    Expected columns: name, role, tasks_completed, tasks_assigned,
    avg_completion_days, quality_score, peer_feedback_score,
    initiatives_proposed, initiatives_shipped
    """
    team_members = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            member = {
                "name": row.get("name", "Unknown"),
                "role": row.get("role", "Unknown"),
                "role_description": row.get("role_description", ""),
                "okrs": [],
                "metrics": {
                    "tasks_completed": int(row.get("tasks_completed", 0)),
                    "tasks_assigned": int(row.get("tasks_assigned", 0)),
                    "avg_completion_days": float(row.get("avg_completion_days", 0)),
                    "quality_score": float(row.get("quality_score", 0)),
                    "peer_feedback_score": float(row.get("peer_feedback_score", 0)),
                    "initiatives_proposed": int(row.get("initiatives_proposed", 0)),
                    "initiatives_shipped": int(row.get("initiatives_shipped", 0)),
                },
                "deliverables": [],
            }
            team_members.append(member)

    return {"team_members": team_members, "org_context": {}}


def load_input(filepath: str) -> dict:
    """Load team data from JSON or CSV based on file extension."""
    if filepath.endswith(".csv"):
        return load_csv_input(filepath)
    else:
        return load_json_input(filepath)


# ---------------------------------------------------------------------------
# Scoring Engine
# ---------------------------------------------------------------------------

# Weight configuration for the composite score
SCORE_WEIGHTS = {
    "output_velocity": 0.30,   # Speed and throughput
    "quality": 0.30,           # Quality of deliverables
    "independence": 0.20,      # Self-direction, low management overhead
    "initiative": 0.20,        # Proactive contributions beyond assigned work
}

# Tier thresholds
TIER_THRESHOLDS = {
    "A": 80,    # A-player: top performers, promote/retain
    "B": 55,    # B-player: solid contributors, coach to A or maintain
    "C": 0,     # C-player: underperforming, reassign or exit
}


def compute_output_velocity(metrics: dict) -> float:
    """
    Score output velocity (0-100).

    Factors:
    - Task completion rate (completed / assigned)
    - Speed (inverse of avg_completion_days, normalized)
    """
    completed = metrics.get("tasks_completed", 0)
    assigned = metrics.get("tasks_assigned", 1)  # avoid division by zero
    avg_days = metrics.get("avg_completion_days", 5)

    # Completion rate: 0-60 points
    completion_rate = min(completed / max(assigned, 1), 1.0)
    completion_score = completion_rate * 60

    # Speed: 0-40 points (faster = better, assumes <2 days is excellent, >10 is poor)
    if avg_days <= 1:
        speed_score = 40
    elif avg_days >= 10:
        speed_score = 0
    else:
        speed_score = max(0, 40 * (1 - (avg_days - 1) / 9))

    return round(completion_score + speed_score, 1)


def compute_quality(metrics: dict) -> float:
    """
    Score quality (0-100).

    Factors:
    - Quality score from reviews/metrics (0-100 scale expected)
    - Peer feedback score (1-5 scale, normalized to 0-100)
    """
    quality_raw = metrics.get("quality_score", 50)
    peer_score = metrics.get("peer_feedback_score", 3.0)

    # Quality component: 60% weight
    quality_component = min(quality_raw, 100) * 0.6

    # Peer feedback: 40% weight (1-5 scale → 0-100)
    peer_normalized = max(0, min((peer_score - 1) / 4 * 100, 100))
    peer_component = peer_normalized * 0.4

    return round(quality_component + peer_component, 1)


def compute_independence(metrics: dict) -> float:
    """
    Score independence (0-100).

    Heuristic based on:
    - High completion rate (doesn't need hand-holding)
    - Low avg_completion_days relative to task volume
    - Peer feedback as proxy for collaboration without dependency

    Note: For richer scoring, add fields like 'escalations_to_manager',
    'blockers_raised', 'self_unblocked_count' to your input data.
    """
    completed = metrics.get("tasks_completed", 0)
    assigned = metrics.get("tasks_assigned", 1)
    peer_score = metrics.get("peer_feedback_score", 3.0)

    # Completion without escalation proxy: 60% weight
    completion_rate = min(completed / max(assigned, 1), 1.0)
    completion_component = completion_rate * 60

    # Peer score as collaboration proxy: 40% weight
    peer_normalized = max(0, min((peer_score - 1) / 4 * 100, 100))
    peer_component = peer_normalized * 0.4

    return round(completion_component + peer_component, 1)


def compute_initiative(metrics: dict) -> float:
    """
    Score initiative (0-100).

    Factors:
    - Initiatives proposed (ideas beyond assigned work)
    - Initiatives shipped (executed, not just suggested)
    - Ship rate (proposed → shipped conversion)
    """
    proposed = metrics.get("initiatives_proposed", 0)
    shipped = metrics.get("initiatives_shipped", 0)

    # Volume: 0-50 points (caps at 5+ proposed)
    volume_score = min(proposed / 5, 1.0) * 50

    # Ship rate: 0-30 points
    if proposed > 0:
        ship_rate = min(shipped / proposed, 1.0)
        ship_score = ship_rate * 30
    else:
        ship_score = 0

    # Shipped count bonus: 0-20 points (caps at 3+ shipped)
    shipped_bonus = min(shipped / 3, 1.0) * 20

    return round(volume_score + ship_score + shipped_bonus, 1)


def compute_composite_score(metrics: dict) -> dict:
    """Compute all dimension scores and weighted composite."""
    velocity = compute_output_velocity(metrics)
    quality = compute_quality(metrics)
    independence = compute_independence(metrics)
    initiative = compute_initiative(metrics)

    composite = (
        velocity * SCORE_WEIGHTS["output_velocity"]
        + quality * SCORE_WEIGHTS["quality"]
        + independence * SCORE_WEIGHTS["independence"]
        + initiative * SCORE_WEIGHTS["initiative"]
    )

    # Determine tier
    if composite >= TIER_THRESHOLDS["A"]:
        tier = "A"
    elif composite >= TIER_THRESHOLDS["B"]:
        tier = "B"
    else:
        tier = "C"

    return {
        "output_velocity": velocity,
        "quality": quality,
        "independence": independence,
        "initiative": initiative,
        "composite": round(composite, 1),
        "tier": tier,
    }


def recommend_action(tier: str, scores: dict) -> str:
    """Generate recommended action based on tier and score profile."""
    if tier == "A":
        if scores["initiative"] >= 80:
            return "PROMOTE — High performer with strong initiative. Leadership candidate."
        return "RETAIN & REWARD — Top performer. Ensure compensation and growth path are competitive."

    elif tier == "B":
        weakest = min(
            ["output_velocity", "quality", "independence", "initiative"],
            key=lambda k: scores[k],
        )
        weak_labels = {
            "output_velocity": "speed/throughput",
            "quality": "deliverable quality",
            "independence": "self-direction",
            "initiative": "proactive contribution",
        }
        return f"COACH — Solid contributor. Focus development on {weak_labels[weakest]} (score: {scores[weakest]})."

    else:  # C
        if scores["composite"] < 30:
            return "EXIT — Significant underperformance across dimensions. Consider transition plan."
        return "REASSIGN or PIP — Underperforming in current role. Evaluate fit for different position."


# ---------------------------------------------------------------------------
# Elon Algorithm: 5-Step Analysis (LLM-powered)
# ---------------------------------------------------------------------------

def run_elon_algorithm(data: dict) -> str:
    """
    Run the 5-step Elon Algorithm analysis using LLM.

    Steps:
    1. Question every requirement
    2. Delete redundant processes
    3. Simplify workflows
    4. Accelerate bottlenecks
    5. Automate what's possible
    """
    team_summary = []
    for m in data["team_members"]:
        team_summary.append(
            f"- {m['name']} ({m['role']}): {m.get('role_description', 'No description')}"
        )

    org_ctx = data.get("org_context", {})
    goals = org_ctx.get("company_goals", ["Not specified"])

    prompt = f"""Analyze this team using the Elon Algorithm — a ruthless 5-step organizational optimization framework.

## Team ({len(data['team_members'])} members)
{chr(10).join(team_summary)}

## Company Goals
{chr(10).join(f'- {g}' for g in goals)}

## Evaluation Period
{org_ctx.get('evaluation_period', 'Current quarter')}

## Full Team Data
{json.dumps(data['team_members'], indent=2, default=str)}

---

For each of the 5 steps below, provide SPECIFIC, ACTIONABLE findings (not generic advice):

### Step 1: Question Every Requirement
For each role, ask: Is this role necessary? Is every task they do necessary? Could the team function without this position? Which tasks they perform have no clear connection to company goals?

### Step 2: Delete Redundant Processes
Identify: Overlapping responsibilities between team members. Duplicate efforts. Roles that could be consolidated. Meetings or processes that exist by inertia.

### Step 3: Simplify
Find: Overcomplicated workflows. Multi-step processes that could be 1-2 steps. Unnecessary approval chains. Reports nobody reads.

### Step 4: Accelerate
Identify bottlenecks: Who/what is the slowest link? Where do tasks get stuck? What dependencies create wait times? What would unblock the most throughput?

### Step 5: Automate
Flag tasks ripe for AI/automation: Data entry, reporting, scheduling, template-based work, monitoring, routing, classification. Estimate effort saved.

Be specific. Name names. Reference actual data. This is a performance audit, not a feel-good exercise."""

    return call_llm(
        prompt,
        system_prompt=(
            "You are a ruthless organizational efficiency consultant. "
            "Your job is to find waste, redundancy, and inefficiency. "
            "Be direct, specific, and actionable. Name names when the data supports it. "
            "Do not hedge or soften findings."
        ),
    )


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_scorecards(data: dict) -> list[dict]:
    """Score every team member and return sorted scorecards."""
    scorecards = []
    for member in data["team_members"]:
        metrics = member.get("metrics", {})
        scores = compute_composite_score(metrics)
        action = recommend_action(scores["tier"], scores)

        # OKR progress summary
        okrs = member.get("okrs", [])
        okr_avg = 0.0
        if okrs:
            okr_avg = sum(o.get("progress", 0) for o in okrs) / len(okrs)

        scorecards.append({
            "name": member["name"],
            "role": member["role"],
            "scores": scores,
            "action": action,
            "okr_progress": round(okr_avg * 100, 1),
            "deliverables": member.get("deliverables", []),
        })

    # Sort by composite score descending (stack rank)
    scorecards.sort(key=lambda x: x["scores"]["composite"], reverse=True)

    # Add rank
    for i, sc in enumerate(scorecards, 1):
        sc["rank"] = i

    return scorecards


def format_markdown_report(scorecards: list[dict], elon_analysis: str, data: dict) -> str:
    """Generate the full markdown report."""
    org_ctx = data.get("org_context", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# Team Performance Audit",
        f"",
        f"**Generated:** {now}",
        f"**Team Size:** {len(scorecards)}",
        f"**Period:** {org_ctx.get('evaluation_period', 'Current')}",
        f"",
    ]

    # --- Executive Summary ---
    a_count = sum(1 for s in scorecards if s["scores"]["tier"] == "A")
    b_count = sum(1 for s in scorecards if s["scores"]["tier"] == "B")
    c_count = sum(1 for s in scorecards if s["scores"]["tier"] == "C")
    avg_composite = sum(s["scores"]["composite"] for s in scorecards) / max(len(scorecards), 1)

    lines.extend([
        "## Executive Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Team Average Score | {avg_composite:.1f}/100 |",
        f"| A-Players | {a_count} ({a_count/max(len(scorecards),1)*100:.0f}%) |",
        f"| B-Players | {b_count} ({b_count/max(len(scorecards),1)*100:.0f}%) |",
        f"| C-Players | {c_count} ({c_count/max(len(scorecards),1)*100:.0f}%) |",
        "",
    ])

    # Health assessment
    if a_count / max(len(scorecards), 1) >= 0.3:
        lines.append("**Assessment:** Strong team core. Focus on coaching B-players up and addressing C-players decisively.")
    elif c_count / max(len(scorecards), 1) >= 0.3:
        lines.append("**Assessment:** ⚠️ Significant underperformance. Org restructuring recommended.")
    else:
        lines.append("**Assessment:** Average team composition. Targeted development can move the needle.")

    lines.append("")

    # --- Stack Rank ---
    lines.extend([
        "## Stack Rank",
        "",
        "| Rank | Name | Role | Composite | Tier | Action |",
        "|------|------|------|-----------|------|--------|",
    ])
    for sc in scorecards:
        tier_emoji = {"A": "🟢", "B": "🟡", "C": "🔴"}[sc["scores"]["tier"]]
        lines.append(
            f"| {sc['rank']} | {sc['name']} | {sc['role']} | "
            f"{sc['scores']['composite']} | {tier_emoji} {sc['scores']['tier']} | "
            f"{sc['action'].split(' — ')[0]} |"
        )
    lines.append("")

    # --- Elon Algorithm Analysis ---
    lines.extend([
        "## Elon Algorithm — 5-Step Analysis",
        "",
        elon_analysis,
        "",
    ])

    # --- Individual Scorecards ---
    lines.extend([
        "## Individual Scorecards",
        "",
    ])

    for sc in scorecards:
        tier_emoji = {"A": "🟢", "B": "🟡", "C": "🔴"}[sc["scores"]["tier"]]
        scores = sc["scores"]
        lines.extend([
            f"### #{sc['rank']} — {sc['name']} ({sc['role']})",
            "",
            f"**Tier:** {tier_emoji} {scores['tier']}-Player | **Composite:** {scores['composite']}/100",
            "",
            f"| Dimension | Score |",
            f"|-----------|-------|",
            f"| Output Velocity | {scores['output_velocity']}/100 |",
            f"| Quality | {scores['quality']}/100 |",
            f"| Independence | {scores['independence']}/100 |",
            f"| Initiative | {scores['initiative']}/100 |",
            "",
        ])

        if sc["okr_progress"] > 0:
            lines.append(f"**OKR Progress:** {sc['okr_progress']}%")
            lines.append("")

        if sc["deliverables"]:
            lines.append("**Recent Deliverables:**")
            for d in sc["deliverables"]:
                status_emoji = "✅" if d.get("status") == "completed" else "🔄"
                lines.append(f"- {status_emoji} {d.get('name', 'Unknown')} ({d.get('status', 'unknown')}, {d.get('date', 'no date')})")
            lines.append("")

        lines.append(f"**Recommended Action:** {sc['action']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # --- Org-Level Recommendations ---
    lines.extend([
        "## Org-Level Recommendations",
        "",
        f"1. **Immediate:** Address {c_count} C-player(s) — each underperformer costs the team velocity.",
        f"2. **Short-term:** Invest in coaching for {b_count} B-player(s) — targeted development on their weakest dimension.",
        f"3. **Strategic:** Retain and challenge {a_count} A-player(s) — they leave when bored, not when overworked.",
    ])

    if avg_composite < 60:
        lines.append("4. **Warning:** Team average below 60. Consider structural changes, not just individual coaching.")

    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by Team Performance Audit (Elon Algorithm)*")

    return "\n".join(lines)


def format_json_report(scorecards: list[dict], elon_analysis: str, data: dict) -> str:
    """Generate the full JSON report."""
    org_ctx = data.get("org_context", {})
    report = {
        "generated": datetime.now().isoformat(),
        "team_size": len(scorecards),
        "evaluation_period": org_ctx.get("evaluation_period", "Current"),
        "summary": {
            "average_composite": round(
                sum(s["scores"]["composite"] for s in scorecards) / max(len(scorecards), 1), 1
            ),
            "tier_distribution": {
                "A": sum(1 for s in scorecards if s["scores"]["tier"] == "A"),
                "B": sum(1 for s in scorecards if s["scores"]["tier"] == "B"),
                "C": sum(1 for s in scorecards if s["scores"]["tier"] == "C"),
            },
        },
        "stack_rank": scorecards,
        "elon_algorithm_analysis": elon_analysis,
    }
    return json.dumps(report, indent=2, default=str)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Team Performance Audit — The Elon Algorithm",
        epilog="Scores team members on velocity, quality, independence, and initiative. "
               "Stack ranks with A/B/C tiers and generates actionable recommendations.",
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to team data file (JSON or CSV). See --help for format details.",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip LLM calls. Only compute quantitative scores.",
    )
    parser.add_argument(
        "--weights",
        type=str,
        help='Custom score weights as JSON: \'{"output_velocity":0.4,"quality":0.3,"independence":0.15,"initiative":0.15}\'',
    )

    args = parser.parse_args()

    # Apply custom weights if provided
    if args.weights:
        try:
            custom_weights = json.loads(args.weights)
            for key in SCORE_WEIGHTS:
                if key in custom_weights:
                    SCORE_WEIGHTS[key] = float(custom_weights[key])
            # Validate weights sum to ~1.0
            total = sum(SCORE_WEIGHTS.values())
            if abs(total - 1.0) > 0.01:
                print(f"Warning: Weights sum to {total}, not 1.0. Normalizing.", file=sys.stderr)
                for key in SCORE_WEIGHTS:
                    SCORE_WEIGHTS[key] /= total
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing --weights: {e}", file=sys.stderr)
            sys.exit(1)

    # Load data
    try:
        data = load_input(args.input)
    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Invalid input file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"📊 Loaded {len(data['team_members'])} team members", file=sys.stderr)

    # Compute scorecards
    scorecards = generate_scorecards(data)
    print(f"✅ Scored and ranked all members", file=sys.stderr)

    # Run Elon Algorithm (LLM analysis)
    if args.dry_run:
        elon_analysis = "[Dry run — LLM analysis skipped. Quantitative scores only.]"
        print("⏭️  Dry run — skipping LLM analysis", file=sys.stderr)
    else:
        print("🤖 Running Elon Algorithm analysis...", file=sys.stderr)
        elon_analysis = run_elon_algorithm(data)
        print("✅ Analysis complete", file=sys.stderr)

    # Generate report
    if args.format == "json":
        report = format_json_report(scorecards, elon_analysis, data)
    else:
        report = format_markdown_report(scorecards, elon_analysis, data)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"📝 Report written to {args.output}", file=sys.stderr)
    else:
        print(report)

    # Summary to stderr
    a_count = sum(1 for s in scorecards if s["scores"]["tier"] == "A")
    b_count = sum(1 for s in scorecards if s["scores"]["tier"] == "B")
    c_count = sum(1 for s in scorecards if s["scores"]["tier"] == "C")
    print(f"\n🏆 Results: {a_count}A / {b_count}B / {c_count}C players", file=sys.stderr)


if __name__ == "__main__":
    main()
