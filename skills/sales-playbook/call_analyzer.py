#!/usr/bin/env python3
"""
Value-Based Pricing: Post-Call Deal Analyzer

Feed in a sales call transcript → extracts signals, scores the call against
the value-based pricing framework, and identifies upsell opportunities.

Usage:
    python3 call_analyzer.py --transcript call.txt
    cat call.txt | python3 call_analyzer.py
    python3 call_analyzer.py --transcript call.txt --format json
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# LLM Integration Stubs
# ---------------------------------------------------------------------------
# To use real LLM analysis:
# 1. Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable
# 2. The stub below will be replaced with actual API calls
# 3. Anthropic docs: https://docs.anthropic.com/en/api
# 4. OpenAI docs: https://platform.openai.com/docs/api-reference


def _call_llm(prompt: str, system_prompt: str = "") -> str:
    """
    Stub: Call LLM for transcript analysis.

    In production, call:
        POST https://api.anthropic.com/v1/messages
        POST https://api.openai.com/v1/chat/completions
    """
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if anthropic_key:
        # TODO: Implement real Anthropic API call
        # import requests
        # resp = requests.post(
        #     "https://api.anthropic.com/v1/messages",
        #     headers={"x-api-key": anthropic_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        #     json={"model": "claude-sonnet-4-20250514", "max_tokens": 4096, "system": system_prompt, "messages": [{"role": "user", "content": prompt}]},
        # )
        # return resp.json()["content"][0]["text"]
        pass

    if openai_key:
        # TODO: Implement real OpenAI API call
        # import requests
        # messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}] if system_prompt else [{"role": "user", "content": prompt}]
        # resp = requests.post(
        #     "https://api.openai.com/v1/chat/completions",
        #     headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
        #     json={"model": "gpt-4o", "messages": messages, "max_tokens": 4096},
        # )
        # return resp.json()["choices"][0]["message"]["content"]
        pass

    # Fallback: rule-based analysis (no LLM available)
    return None


# ---------------------------------------------------------------------------
# Rule-Based Signal Detection (fallback when no LLM available)
# ---------------------------------------------------------------------------

BUYING_SIGNAL_PATTERNS = {
    "budget_confirmed": {
        "patterns": [
            r"budget\s+(?:is|of|around)\s+\$?[\d,]+",
            r"we(?:'ve| have)\s+(?:allocated|set aside|budgeted)",
            r"spend(?:ing)?\s+(?:about|around|roughly)\s+\$?[\d,]+",
            r"our\s+budget\s+(?:for|this)",
        ],
        "weight": 25,
        "description": "Budget discussed or confirmed",
    },
    "timeline_established": {
        "patterns": [
            r"(?:start|launch|begin|kick off)\s+(?:in|by|before|next)\s+(?:Q[1-4]|January|February|March|April|May|June|July|August|September|October|November|December|\d+\s+(?:weeks?|months?))",
            r"(?:need|want)\s+(?:this|results|something)\s+(?:by|before|in)",
            r"(?:timeline|timeframe|deadline)\s+(?:is|would be)",
            r"ASAP|as soon as possible|urgent",
        ],
        "weight": 20,
        "description": "Timeline or urgency established",
    },
    "decision_maker_present": {
        "patterns": [
            r"I\s+(?:can|will|am able to)\s+(?:make|approve|sign off)",
            r"(?:CEO|CMO|VP|CRO|founder|owner|partner)\s+(?:here|speaking|on the call)",
            r"I\s+(?:don't|do not)\s+need\s+(?:anyone else|approval)",
            r"the\s+decision\s+(?:is|rests)\s+with\s+me",
        ],
        "weight": 20,
        "description": "Decision maker is present on the call",
    },
    "competitive_urgency": {
        "patterns": [
            r"competitor[s]?\s+(?:is|are|has|have)\s+(?:doing|beating|ahead|winning|ranking)",
            r"(?:losing|lost)\s+(?:market share|traffic|rankings|customers)\s+to",
            r"(?:we need to|have to|must)\s+(?:catch up|compete|keep up)",
            r"(?:they|competitor)\s+(?:just|recently)\s+(?:launched|started|hired)",
        ],
        "weight": 15,
        "description": "Competitive urgency expressed",
    },
    "pain_stated": {
        "patterns": [
            r"(?:struggling|frustrated|disappointed|unhappy)\s+with",
            r"(?:not getting|haven't seen|can't get)\s+(?:results|ROI|traffic|leads)",
            r"(?:our|the)\s+(?:current|existing)\s+(?:agency|vendor|team)\s+(?:isn't|is not|hasn't)",
            r"(?:we're|we are)\s+(?:behind|falling behind|not where we)",
        ],
        "weight": 20,
        "description": "Prospect stated their pain/frustration",
    },
}

OBJECTION_PATTERNS = {
    "price": {
        "patterns": [
            r"(?:too\s+)?(?:expensive|pricey|costly|much|high)",
            r"(?:can't|cannot)\s+(?:afford|justify|spend)\s+that",
            r"(?:over|above|exceeds)\s+(?:our|the)\s+budget",
            r"(?:less|lower|cheaper|discount|negotiate)",
        ],
        "description": "Price objection",
    },
    "timing": {
        "patterns": [
            r"(?:not|bad)\s+(?:the right|a good)\s+time",
            r"(?:next|after)\s+(?:quarter|year|Q[1-4])",
            r"(?:need|want)\s+(?:to wait|more time|to think)",
            r"(?:revisit|circle back|touch base)\s+(?:later|in|next)",
        ],
        "description": "Timing objection",
    },
    "authority": {
        "patterns": [
            r"(?:need|have)\s+to\s+(?:check|ask|run it by|discuss with|get approval)",
            r"(?:my|the)\s+(?:boss|CEO|board|team|partner)\s+(?:needs to|has to|would need)",
            r"(?:not|can't)\s+(?:my|the)\s+(?:decision|call)\s+(?:alone|to make)",
        ],
        "description": "Authority objection (not the decision maker)",
    },
    "need": {
        "patterns": [
            r"(?:not sure|don't know)\s+(?:if|that)\s+we\s+(?:need|require)",
            r"(?:already|currently)\s+(?:doing|have|using)\s+(?:something|a|an)",
            r"(?:what|how)\s+(?:is|would be)\s+(?:different|better)\s+(?:than|from)",
        ],
        "description": "Need objection (don't see the value)",
    },
    "competition": {
        "patterns": [
            r"(?:also|already)\s+(?:talking to|evaluating|looking at)\s+(?:other|another)",
            r"(?:comparing|comparison|vs|versus)\s+(?:other|another|your competitors)",
            r"(?:got|received|have)\s+(?:other|another|competing)\s+(?:proposals?|quotes?|bids?)",
        ],
        "description": "Competition objection (evaluating others)",
    },
}

# ---------------------------------------------------------------------------
# Pricing Framework Scoring
# ---------------------------------------------------------------------------

FRAMEWORK_CRITERIA = {
    "showed_data_before_pitching": {
        "max_points": 20,
        "description": "Did they show data before pitching?",
        "patterns": [
            r"(?:let me|I want to)\s+(?:show|share|pull up)\s+(?:some|the|your)\s+(?:data|numbers|metrics)",
            r"(?:before|let me start|first)\s+.*(?:data|research|analysis|numbers)",
            r"(?:I|we)\s+(?:pulled|looked at|analyzed)\s+(?:your|the)\s+(?:data|metrics|rankings|traffic)",
        ],
    },
    "presented_tiered_options": {
        "max_points": 20,
        "description": "Did they present tiered options?",
        "patterns": [
            r"(?:three|3|four|4|multiple)\s+(?:options?|tiers?|packages?|levels?)",
            r"(?:option|tier|package)\s+(?:one|two|three|A|B|C|1|2|3)",
            r"(?:baseline|value|powerhouse|premium|standard|performance)",
        ],
    },
    "anchored_high_first": {
        "max_points": 15,
        "description": "Did they anchor high first?",
        "patterns": [
            r"(?:first|top|premium|highest|most comprehensive)\s+(?:option|tier|package)",
            r"(?:start|begin)\s+with\s+(?:the|our)\s+(?:most|top|full|comprehensive)",
            r"(?:if you want|for maximum|the full)\s+.*(?:\$[\d,]+)",
        ],
    },
    "tied_price_to_value": {
        "max_points": 15,
        "description": "Did they tie price to value/ROI?",
        "patterns": [
            r"(?:ROI|return|value)\s+(?:of|would be|is)\s+(?:about|roughly|around)?\s*\$?[\d,]+",
            r"(?:for every|per)\s+\$[\d,]+\s+(?:you|invested)",
            r"(?:traffic|leads|revenue)\s+(?:worth|valued at|equivalent)\s+\$[\d,]+",
            r"(?:payback|pays for itself|break even)\s+(?:in|within)\s+\d+",
        ],
    },
    "used_competitive_triggers": {
        "max_points": 15,
        "description": "Did they use competitive triggers?",
        "patterns": [
            r"(?:your|the)\s+competitor\s+(?:is|has|ranks|gets)",
            r"(?:they|CompetitorA|competitor)\s+(?:rank|are)\s+(?:#|number)\s*\d+",
            r"(?:gap|behind|ahead)\s+(?:of|from|vs)\s+(?:your|the)\s+competitor",
            r"(?:losing|left behind|falling behind)\s+.*(?:competitor|market)",
        ],
    },
    "prospect_stated_own_pain": {
        "max_points": 15,
        "description": "Did they get the prospect to state their own pain?",
        "patterns": [
            r"(?:what|where)\s+(?:are|is)\s+(?:your|the)\s+biggest\s+(?:challenge|pain|frustration|problem)",
            r"(?:tell me|walk me through|describe)\s+.*(?:challenge|struggle|issue|problem)",
            r"(?:what|how)\s+(?:would|does)\s+(?:success|ideal|better)\s+look like",
            # These detect the PROSPECT responding with pain
            r"(?:we're|we are|I'm|I am)\s+(?:struggling|frustrated|worried|concerned)",
        ],
    },
}


def _detect_patterns(text: str, patterns: list) -> list:
    """Find all pattern matches in text."""
    matches = []
    text_lower = text.lower()
    for pattern in patterns:
        found = re.findall(pattern, text_lower)
        matches.extend(found)
    return matches


def analyze_transcript_rules(transcript: str) -> dict:
    """Analyze transcript using rule-based pattern matching (no LLM)."""
    # Detect buying signals
    buying_signals = []
    for signal_key, config in BUYING_SIGNAL_PATTERNS.items():
        matches = _detect_patterns(transcript, config["patterns"])
        if matches:
            buying_signals.append({
                "signal": signal_key,
                "description": config["description"],
                "weight": config["weight"],
                "evidence_count": len(matches),
                "sample_evidence": matches[:3],
            })

    # Detect objections
    objections = []
    for obj_key, config in OBJECTION_PATTERNS.items():
        matches = _detect_patterns(transcript, config["patterns"])
        if matches:
            objections.append({
                "category": obj_key,
                "description": config["description"],
                "evidence_count": len(matches),
                "sample_evidence": matches[:3],
            })

    # Score pricing framework
    framework_scores = {}
    total_score = 0
    for criterion_key, config in FRAMEWORK_CRITERIA.items():
        matches = _detect_patterns(transcript, config["patterns"])
        score = min(config["max_points"], len(matches) * (config["max_points"] // 2))
        framework_scores[criterion_key] = {
            "description": config["description"],
            "max_points": config["max_points"],
            "score": score,
            "evidence_found": len(matches) > 0,
            "evidence_count": len(matches),
        }
        total_score += score

    # Deal probability estimate
    signal_weight = sum(s["weight"] for s in buying_signals)
    objection_penalty = len(objections) * 10
    deal_probability = min(95, max(5, signal_weight + (total_score // 2) - objection_penalty))

    # Recommended next steps
    next_steps = _generate_next_steps(buying_signals, objections, framework_scores, total_score)

    # Upsell opportunities
    upsell_opps = _identify_upsell_opportunities(transcript, buying_signals)

    return {
        "buying_signals": buying_signals,
        "objections": objections,
        "framework_scores": framework_scores,
        "total_framework_score": total_score,
        "deal_probability": deal_probability,
        "next_steps": next_steps,
        "upsell_opportunities": upsell_opps,
        "analysis_method": "rule-based (set ANTHROPIC_API_KEY or OPENAI_API_KEY for LLM-powered analysis)",
    }


def _generate_next_steps(buying_signals: list, objections: list, framework_scores: dict, total_score: int) -> list:
    """Generate recommended next steps based on analysis."""
    steps = []
    signal_keys = {s["signal"] for s in buying_signals}
    objection_keys = {o["category"] for o in objections}

    # Address objections first
    if "price" in objection_keys:
        steps.append({
            "priority": "high",
            "action": "Send ROI analysis",
            "detail": "Prospect raised price concerns. Send a detailed ROI breakdown showing the cost-of-inaction vs. investment. Include competitive data showing what they're leaving on the table.",
        })
    if "authority" in objection_keys:
        steps.append({
            "priority": "high",
            "action": "Identify and engage decision maker",
            "detail": "Prospect indicated they need approval from someone else. Request an intro to the decision maker and offer to present directly. Prepare an executive summary.",
        })
    if "timing" in objection_keys:
        steps.append({
            "priority": "medium",
            "action": "Create urgency with competitive data",
            "detail": "Prospect wants to delay. Send competitive intelligence showing what competitors are doing NOW. Frame the cost of waiting in terms of lost ground.",
        })
    if "competition" in objection_keys:
        steps.append({
            "priority": "high",
            "action": "Differentiate with case study",
            "detail": "Prospect is evaluating other options. Send a relevant case study and offer a reference customer call. Emphasize your unique methodology and results.",
        })

    # Build on buying signals
    if "budget_confirmed" in signal_keys:
        steps.append({
            "priority": "high",
            "action": "Send tiered proposal within 24 hours",
            "detail": "Budget is confirmed. Strike while warm. Send the proposal with tiers anchored around the confirmed budget.",
        })
    if "competitive_urgency" in signal_keys:
        steps.append({
            "priority": "high",
            "action": "Send competitive gap report",
            "detail": "Prospect expressed competitive anxiety. Send a detailed competitive analysis showing exactly where they're falling behind and the trajectory if nothing changes.",
        })

    # Framework improvement suggestions
    if total_score < 50:
        steps.append({
            "priority": "medium",
            "action": "Schedule follow-up with better framework execution",
            "detail": f"Framework score was {total_score}/100. Key gaps: {', '.join(k for k, v in framework_scores.items() if not v['evidence_found'])}. Schedule a follow-up call and lead with data + tiered options.",
        })

    # Default follow-up
    if not steps:
        steps.append({
            "priority": "medium",
            "action": "Send summary email with next steps",
            "detail": "Send a concise recap of the conversation, key takeaways, and propose a clear next step (proposal, follow-up call, or pilot).",
        })

    return steps


def _identify_upsell_opportunities(transcript: str, buying_signals: list) -> list:
    """Identify potential upsell opportunities from conversation."""
    opportunities = []
    text_lower = transcript.lower()

    if any(term in text_lower for term in ["content", "blog", "articles", "thought leadership"]):
        opportunities.append({
            "opportunity": "Content Marketing Add-On",
            "signal": "Prospect mentioned content needs during the call",
            "suggested_approach": "Position content as a compound multiplier for SEO results. 'The SEO work creates the foundation, but content is the fuel. Without it, you're leaving 40-60% of the potential on the table.'",
        })

    if any(term in text_lower for term in ["conversion", "convert", "leads", "pipeline", "funnel"]):
        opportunities.append({
            "opportunity": "CRO / Conversion Optimization",
            "signal": "Prospect discussed conversion or lead generation challenges",
            "suggested_approach": "Position CRO as the force multiplier. 'Getting more traffic is half the equation. If your conversion rate goes from 2% to 4%, you just doubled pipeline without spending another dollar on traffic.'",
        })

    if any(term in text_lower for term in ["paid", "ads", "google ads", "ppc", "media spend", "ad spend"]):
        opportunities.append({
            "opportunity": "Paid Media Management",
            "signal": "Prospect mentioned paid channels",
            "suggested_approach": "Position organic + paid as complementary. 'Most companies overspend on paid because their organic isn't pulling its weight. We optimize both so you're not paying for clicks you could be earning.'",
        })

    if any(term in text_lower for term in ["strategy", "strategic", "advisor", "consulting", "leadership"]):
        opportunities.append({
            "opportunity": "Strategic Involvement Upsell",
            "signal": "Prospect values strategic guidance",
            "suggested_approach": "Position senior strategic involvement as the premium lever. 'Same team, same execution. Add a dedicated senior strategist who joins your leadership meetings and aligns marketing with business objectives. That's the difference between execution and transformation.'",
        })

    if any(term in text_lower for term in ["international", "global", "multiple markets", "expansion"]):
        opportunities.append({
            "opportunity": "International / Multi-Market Expansion",
            "signal": "Prospect has international or multi-market ambitions",
            "suggested_approach": "Position multi-market SEO as a separate workstream. 'International SEO is a different discipline. We can layer that on with dedicated regional keyword research and localized content strategy.'",
        })

    return opportunities


def format_scorecard(analysis: dict) -> str:
    """Format analysis as a readable scorecard."""
    lines = []
    lines.append("# 📊 Sales Call Scorecard")
    lines.append(f"*Analysis method: {analysis['analysis_method']}*")
    lines.append("")

    # Top-line metrics
    score = analysis["total_framework_score"]
    prob = analysis["deal_probability"]
    score_emoji = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
    prob_emoji = "🟢" if prob >= 60 else "🟡" if prob >= 30 else "🔴"

    lines.append(f"## {score_emoji} Framework Score: {score}/100")
    lines.append(f"## {prob_emoji} Deal Probability: {prob}%")
    lines.append("")

    # Framework breakdown
    lines.append("## Pricing Framework Breakdown")
    lines.append("")
    lines.append("| Criterion | Score | Max | Status |")
    lines.append("|-----------|-------|-----|--------|")
    for key, fs in analysis["framework_scores"].items():
        status = "✅" if fs["evidence_found"] else "❌"
        lines.append(f"| {fs['description']} | {fs['score']} | {fs['max_points']} | {status} |")
    lines.append("")

    # Buying signals
    lines.append("## 🟢 Buying Signals Detected")
    if analysis["buying_signals"]:
        for s in analysis["buying_signals"]:
            lines.append(f"- **{s['description']}** (weight: {s['weight']}, evidence: {s['evidence_count']})")
    else:
        lines.append("- No clear buying signals detected. Consider whether the prospect is truly qualified.")
    lines.append("")

    # Objections
    lines.append("## 🔴 Objections Raised")
    if analysis["objections"]:
        for o in analysis["objections"]:
            lines.append(f"- **{o['description']}** ({o['category']}, evidence: {o['evidence_count']})")
    else:
        lines.append("- No objections detected (or they weren't surfaced).")
    lines.append("")

    # Upsell opportunities
    if analysis["upsell_opportunities"]:
        lines.append("## 💡 Upsell Opportunities")
        for u in analysis["upsell_opportunities"]:
            lines.append(f"### {u['opportunity']}")
            lines.append(f"*Signal:* {u['signal']}")
            lines.append(f"*Approach:* {u['suggested_approach']}")
            lines.append("")

    # Next steps
    lines.append("## ⏭️ Recommended Next Steps")
    for i, step in enumerate(analysis["next_steps"], 1):
        priority_icon = "🔴" if step["priority"] == "high" else "🟡" if step["priority"] == "medium" else "🟢"
        lines.append(f"{i}. {priority_icon} **{step['action']}** [{step['priority']}]")
        lines.append(f"   {step['detail']}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Value-Based Pricing: Post-Call Deal Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 call_analyzer.py --transcript call.txt
  cat call.txt | python3 call_analyzer.py
  python3 call_analyzer.py --transcript call.txt --format json
        """,
    )
    parser.add_argument("--transcript", help="Path to transcript file (reads from stdin if not provided)")
    parser.add_argument("--format", choices=["markdown", "json", "both"], default="markdown", help="Output format (default: markdown)")

    args = parser.parse_args()

    # Read transcript
    if args.transcript:
        try:
            with open(args.transcript, "r") as f:
                transcript = f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {args.transcript}", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        transcript = sys.stdin.read()
    else:
        print("Error: Provide --transcript FILE or pipe transcript via stdin", file=sys.stderr)
        sys.exit(1)

    if not transcript.strip():
        print("Error: Empty transcript", file=sys.stderr)
        sys.exit(1)

    # Try LLM analysis first, fall back to rule-based
    llm_result = _call_llm(
        prompt=f"Analyze this sales call transcript against a value-based pricing framework:\n\n{transcript[:8000]}",
        system_prompt="You are a sales call analyzer. Extract buying signals, objections, and score the call against value-based pricing principles.",
    )

    # Use rule-based analysis (LLM stubs not yet implemented)
    analysis = analyze_transcript_rules(transcript)
    analysis["generated_at"] = datetime.now().isoformat()
    analysis["transcript_length"] = len(transcript)
    analysis["transcript_word_count"] = len(transcript.split())

    if args.format == "json":
        print(json.dumps(analysis, indent=2))
    elif args.format == "both":
        print(format_scorecard(analysis))
        print("\n---\n## Raw JSON\n")
        print(json.dumps(analysis, indent=2))
    else:
        print(format_scorecard(analysis))


if __name__ == "__main__":
    main()
