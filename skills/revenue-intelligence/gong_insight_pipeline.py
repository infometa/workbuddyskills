#!/usr/bin/env python3
"""
Gong-to-Insight Pipeline

Extracts structured intelligence from sales call transcripts:
- Objections (pricing, timing, competition, authority, need)
- Buying signals (budget, timeline, decision maker, champion)
- Competitive mentions (who, context)
- Pricing discussions
- Content topic suggestions from recurring patterns
- Personalized follow-up drafts

Works with Gong API or plain transcript files.

Usage:
    python gong_insight_pipeline.py --file transcript.txt
    python gong_insight_pipeline.py --dir ./transcripts/
    python gong_insight_pipeline.py --gong --days 7
    python gong_insight_pipeline.py --file transcript.txt --content-topics --follow-ups
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Gong API client
# ---------------------------------------------------------------------------

# To use the Gong API:
# 1. Set GONG_API_KEY (your Gong access key)
# 2. Set GONG_API_BASE_URL (default: https://api.gong.io/v2)
# 3. Generate API credentials in Gong > Settings > API

GONG_API_KEY = os.environ.get("GONG_API_KEY", "")
GONG_API_BASE_URL = os.environ.get("GONG_API_BASE_URL", "https://api.gong.io/v2")


def _gong_headers() -> dict:
    """Build authorization headers for Gong API."""
    if not GONG_API_KEY:
        print("ERROR: GONG_API_KEY not set. Export it or pass --file/--dir instead.", file=sys.stderr)
        sys.exit(1)
    return {
        "Authorization": f"Bearer {GONG_API_KEY}",
        "Content-Type": "application/json",
    }


def fetch_calls_from_gong(days: int = 7, call_id: Optional[str] = None) -> list[dict]:
    """
    Fetch call transcripts from Gong API.

    Returns list of dicts: [{"id": ..., "title": ..., "transcript": ..., "participants": [...]}]

    NOTE: This uses the Gong v2 API. You need:
    - API credentials with 'api:calls:read:transcript' scope
    - Calls must be processed (transcription complete)
    """
    try:
        import requests
    except ImportError:
        print("ERROR: 'requests' required for Gong API. Run: pip install requests", file=sys.stderr)
        sys.exit(1)

    headers = _gong_headers()
    calls = []

    if call_id:
        # Fetch a specific call
        # Step 1: Get call metadata
        resp = requests.get(f"{GONG_API_BASE_URL}/calls/{call_id}", headers=headers)
        resp.raise_for_status()
        call_data = resp.json()

        # Step 2: Get transcript
        transcript_resp = requests.post(
            f"{GONG_API_BASE_URL}/calls/transcript",
            headers=headers,
            json={"filter": {"callIds": [call_id]}},
        )
        transcript_resp.raise_for_status()
        transcript_data = transcript_resp.json()

        transcript_text = _assemble_transcript(transcript_data.get("callTranscripts", []))
        calls.append({
            "id": call_id,
            "title": call_data.get("metaData", {}).get("title", "Unknown"),
            "transcript": transcript_text,
            "participants": [p.get("name", "") for p in call_data.get("parties", [])],
        })
    else:
        # Fetch recent calls
        from_dt = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        to_dt = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Step 1: List calls in date range
        list_resp = requests.post(
            f"{GONG_API_BASE_URL}/calls",
            headers=headers,
            json={"filter": {"fromDateTime": from_dt, "toDateTime": to_dt}},
        )
        list_resp.raise_for_status()
        call_list = list_resp.json().get("calls", [])

        if not call_list:
            print(f"No calls found in the last {days} days.", file=sys.stderr)
            return []

        call_ids = [c["id"] for c in call_list]

        # Step 2: Batch fetch transcripts (Gong supports up to 100 per request)
        for batch_start in range(0, len(call_ids), 100):
            batch = call_ids[batch_start : batch_start + 100]
            transcript_resp = requests.post(
                f"{GONG_API_BASE_URL}/calls/transcript",
                headers=headers,
                json={"filter": {"callIds": batch}},
            )
            transcript_resp.raise_for_status()
            transcripts_by_id = {}
            for ct in transcript_resp.json().get("callTranscripts", []):
                cid = ct.get("callId")
                text = "\n".join(
                    f"{s.get('speakerName', 'Unknown')}: {' '.join(sent.get('text', '') for sent in s.get('sentences', []))}"
                    for s in ct.get("transcript", [])
                )
                transcripts_by_id[cid] = text

            for c in call_list:
                if c["id"] in transcripts_by_id:
                    calls.append({
                        "id": c["id"],
                        "title": c.get("title", "Unknown"),
                        "transcript": transcripts_by_id[c["id"]],
                        "participants": [p.get("name", "") for p in c.get("parties", [])],
                    })

    return calls


def _assemble_transcript(call_transcripts: list) -> str:
    """Assemble transcript text from Gong API response format."""
    lines = []
    for ct in call_transcripts:
        for segment in ct.get("transcript", []):
            speaker = segment.get("speakerName", "Unknown")
            text = " ".join(s.get("text", "") for s in segment.get("sentences", []))
            lines.append(f"{speaker}: {text}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Transcript analysis engine
# ---------------------------------------------------------------------------

# Objection patterns — maps regex patterns to objection categories
OBJECTION_PATTERNS = {
    "pricing": [
        r"(?i)(too expensive|over budget|can't afford|cost(s)? too|cheaper|lower price|discount|pricing is|budget.*tight|price.*high|expensive)",
        r"(?i)(what('s| is) the (price|cost|pricing)|how much (does|will|would)|investment.*significant)",
        r"(?i)(need to.*justify.*cost|hard to.*justify|roi.*unclear|not sure.*worth)",
    ],
    "timing": [
        r"(?i)(not the right time|bad timing|next quarter|next year|revisit.*later|too soon|not ready|circle back|table this)",
        r"(?i)(busy.*right now|other priorities|roadmap.*full|backlog|bandwidth|tied up)",
        r"(?i)(maybe (in|after) (q[1-4]|january|february|march|april|may|june|july|august|september|october|november|december))",
    ],
    "competition": [
        r"(?i)(already (using|working with|have)|current (vendor|provider|partner|agency)|locked in|contract.*with|compared to|vs\.?\s)",
        r"(?i)(what makes you different|why.*switch|competitor|alternative|other option|looking at.*other)",
    ],
    "authority": [
        r"(?i)(need to (talk to|run.*by|check with|get approval|ask) (my|the|our))",
        r"(?i)(not my (decision|call)|someone else|boss|manager|board|committee|stakeholder.*approve)",
        r"(?i)(decision.*committee|buying committee|multiple stakeholders|procurement)",
    ],
    "need": [
        r"(?i)(don't (need|see the need|think we need)|not a priority|we're (fine|good|okay) (with|as)|status quo)",
        r"(?i)(what problem.*solve|why would we|not sure.*fit|doesn't apply|not relevant)",
        r"(?i)(happy with.*current|no pain|working well enough)",
    ],
}

# Buying signal patterns
BUYING_SIGNAL_PATTERNS = {
    "budget_confirmed": [
        r"(?i)(budget.*approved|have.*budget|allocated.*budget|budget (is|of) \$|earmarked|set aside.*for)",
        r"(?i)(can.*invest|willing to (spend|invest|pay)|comfortable with.*price)",
    ],
    "timeline_mentioned": [
        r"(?i)(want.*by (q[1-4]|end of|january|february|march|april|may|june|july|august|september|october|november|december))",
        r"(?i)(need.*live by|launch.*by|deadline|go.?live|start (date|asap|immediately|next week|this month))",
        r"(?i)(sooner.*better|asap|urgent|time.?sensitive|quickly)",
    ],
    "decision_maker_engaged": [
        r"(?i)(ceo|cmo|cfo|cto|vp|vice president|chief|director|head of|svp|evp).*(?:join|call|meeting|asked me)",
        r"(?i)(brought.*my (boss|manager|ceo|cmo)|loop(ed|ing) in|invited.*leadership)",
        r"(?i)(decision maker|final say|sign.*off|authorize)",
    ],
    "champion_identified": [
        r"(?i)(love (this|it|what)|really (like|impressed|excited)|sold on|big fan|advocate)",
        r"(?i)(push.*internally|sell.*internally|convince.*team|champion|sponsor|rally|get.*buy.?in)",
        r"(?i)(exactly what we need|this solves|perfect fit|game.?changer)",
    ],
    "next_steps_agreed": [
        r"(?i)(next step|follow.?up|send.*proposal|schedule.*demo|set up.*call|let's (do|move|proceed))",
        r"(?i)(send.*contract|nda|msa|sow|statement of work|proposal|agreement)",
    ],
}

# Competitive mention patterns — extend with your actual competitors
KNOWN_COMPETITORS = [
    # Add your competitors here. These are common B2B marketing/agency competitors as examples.
    "HubSpot", "Marketo", "Salesforce", "Drift", "6sense", "Demandbase",
    "ZoomInfo", "Apollo", "Outreach", "Salesloft", "Gartner", "Forrester",
    "WebFX", "Wpromote", "Tinuiti", "Power Digital", "Directive",
]

PRICING_DISCUSSION_PATTERNS = [
    r"(?i)\$[\d,]+(\.\d{2})?(\s*(k|K|thousand|million|per month|/mo|/month|annually|per year))?",
    r"(?i)(pricing (model|structure|tier|plan)|pay.*per|subscription|retainer|flat fee|hourly rate)",
    r"(?i)(proposal|quote|estimate|ballpark|range|starting at|minimum.*engagement)",
    r"(?i)(roi|return on investment|payback|break.?even|cost.*benefit)",
]


def analyze_transcript(text: str, source_id: str = "unknown") -> dict:
    """
    Analyze a single transcript and return structured insights.

    Returns dict with: objections, buying_signals, competitive_mentions,
    pricing_discussions, raw_quotes
    """
    lines = text.strip().split("\n")
    insights = {
        "source_id": source_id,
        "analyzed_at": datetime.utcnow().isoformat() + "Z",
        "objections": [],
        "buying_signals": [],
        "competitive_mentions": [],
        "pricing_discussions": [],
    }

    for i, line in enumerate(lines):
        context_window = " ".join(lines[max(0, i - 1) : min(len(lines), i + 2)])

        # --- Objections ---
        for category, patterns in OBJECTION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    insights["objections"].append({
                        "category": category,
                        "quote": line.strip(),
                        "match": match.group(),
                        "line_number": i + 1,
                        "context": context_window.strip(),
                    })
                    break  # One match per category per line

        # --- Buying Signals ---
        for signal_type, patterns in BUYING_SIGNAL_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    insights["buying_signals"].append({
                        "type": signal_type,
                        "quote": line.strip(),
                        "match": match.group(),
                        "line_number": i + 1,
                    })
                    break

        # --- Competitive Mentions ---
        for competitor in KNOWN_COMPETITORS:
            if re.search(r"\b" + re.escape(competitor) + r"\b", line, re.IGNORECASE):
                # Determine context sentiment (basic heuristic)
                sentiment = "neutral"
                neg_words = ["problem", "issue", "bad", "worse", "hate", "frustrat", "limit", "lack", "miss", "fail", "leaving", "switch"]
                pos_words = ["good", "great", "love", "like", "happy", "better", "best", "strong"]
                line_lower = line.lower()
                if any(w in line_lower for w in neg_words):
                    sentiment = "negative"
                elif any(w in line_lower for w in pos_words):
                    sentiment = "positive"

                insights["competitive_mentions"].append({
                    "competitor": competitor,
                    "context_sentiment": sentiment,
                    "quote": line.strip(),
                    "line_number": i + 1,
                })

        # --- Pricing Discussions ---
        for pattern in PRICING_DISCUSSION_PATTERNS:
            match = re.search(pattern, line)
            if match:
                insights["pricing_discussions"].append({
                    "quote": line.strip(),
                    "match": match.group(),
                    "line_number": i + 1,
                })
                break

    # Deduplicate (same quote can match multiple patterns)
    insights["objections"] = _dedupe_by_line(insights["objections"])
    insights["buying_signals"] = _dedupe_by_line(insights["buying_signals"])
    insights["competitive_mentions"] = _dedupe_by_line(insights["competitive_mentions"])
    insights["pricing_discussions"] = _dedupe_by_line(insights["pricing_discussions"])

    # Summary stats
    insights["summary"] = {
        "total_objections": len(insights["objections"]),
        "objection_categories": dict(Counter(o["category"] for o in insights["objections"])),
        "total_buying_signals": len(insights["buying_signals"]),
        "signal_types": dict(Counter(s["type"] for s in insights["buying_signals"])),
        "competitors_mentioned": list(set(c["competitor"] for c in insights["competitive_mentions"])),
        "has_pricing_discussion": len(insights["pricing_discussions"]) > 0,
        "deal_temperature": _score_deal_temperature(insights),
    }

    return insights


def _dedupe_by_line(items: list) -> list:
    """Remove duplicate entries for the same line number."""
    seen = set()
    deduped = []
    for item in items:
        key = item.get("line_number", id(item))
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def _score_deal_temperature(insights: dict) -> str:
    """
    Score deal temperature based on signals vs objections.
    Returns: hot, warm, cool, cold
    """
    signal_count = len(insights["buying_signals"])
    objection_count = len(insights["objections"])

    # Weighted scoring
    score = 0
    for sig in insights["buying_signals"]:
        weights = {
            "budget_confirmed": 3,
            "decision_maker_engaged": 3,
            "timeline_mentioned": 2,
            "champion_identified": 2,
            "next_steps_agreed": 2,
        }
        score += weights.get(sig["type"], 1)

    for obj in insights["objections"]:
        penalties = {
            "need": -3,  # No need = worst signal
            "authority": -1,
            "timing": -1,
            "pricing": -1,
            "competition": -2,
        }
        score += penalties.get(obj["category"], -1)

    if score >= 6:
        return "hot"
    elif score >= 3:
        return "warm"
    elif score >= 0:
        return "cool"
    else:
        return "cold"


# ---------------------------------------------------------------------------
# Content topic generator
# ---------------------------------------------------------------------------

def generate_content_topics(all_insights: list[dict]) -> list[dict]:
    """
    Analyze recurring objections across multiple calls to suggest content topics.
    Returns list of content topic suggestions.
    """
    objection_quotes = defaultdict(list)
    for insight in all_insights:
        for obj in insight.get("objections", []):
            objection_quotes[obj["category"]].append(obj["quote"])

    topics = []

    # Map objection categories to content strategies
    content_strategies = {
        "pricing": {
            "topic_template": "ROI Calculator: How {product} Pays for Itself in {timeframe}",
            "content_types": ["blog post", "interactive calculator", "case study"],
            "angle": "Address pricing objections with concrete ROI proof",
        },
        "timing": {
            "topic_template": "The Cost of Waiting: What Happens When You Delay {solution}",
            "content_types": ["blog post", "email sequence", "one-pager"],
            "angle": "Create urgency with cost-of-inaction framing",
        },
        "competition": {
            "topic_template": "{product} vs {competitor}: Honest Comparison for {use_case}",
            "content_types": ["comparison page", "blog post", "battle card"],
            "angle": "Win competitive deals with transparent comparison content",
        },
        "authority": {
            "topic_template": "How to Build the Business Case for {product} (Template Included)",
            "content_types": ["template", "guide", "executive summary"],
            "angle": "Arm your champion with materials to sell internally",
        },
        "need": {
            "topic_template": "Why Top {role}s Are Prioritizing {category} in {year}",
            "content_types": ["thought leadership", "industry report", "webinar"],
            "angle": "Build awareness and urgency around the problem",
        },
    }

    for category, quotes in objection_quotes.items():
        count = len(quotes)
        if count == 0:
            continue

        strategy = content_strategies.get(category, {})
        topics.append({
            "category": category,
            "frequency": count,
            "sample_quotes": quotes[:3],  # Top 3 examples
            "suggested_topic": strategy.get("topic_template", f"Content addressing {category} objections"),
            "recommended_content_types": strategy.get("content_types", ["blog post"]),
            "strategic_angle": strategy.get("angle", ""),
            "priority": "high" if count >= 5 else "medium" if count >= 2 else "low",
        })

    topics.sort(key=lambda t: t["frequency"], reverse=True)
    return topics


# ---------------------------------------------------------------------------
# Follow-up generator
# ---------------------------------------------------------------------------

def generate_follow_ups(insights: dict) -> list[dict]:
    """
    Generate personalized follow-up suggestions based on call insights.
    """
    follow_ups = []

    # Address top objections
    for obj in insights.get("objections", [])[:3]:
        templates = {
            "pricing": {
                "subject": "Quick thought on the investment discussion",
                "body": "Following up on our pricing conversation. I put together a quick ROI model based on what you shared about {context}. The numbers suggest a {x}x return in the first year. Want me to walk through it?",
                "asset": "ROI calculator or case study with similar company metrics",
            },
            "timing": {
                "subject": "Timing + what others in your position did",
                "body": "I hear you on timing. Quick data point: companies that started in a similar position to yours saw {metric} within the first 90 days. Happy to share the case study if helpful.",
                "asset": "Quick-win case study showing fast time-to-value",
            },
            "competition": {
                "subject": "Honest take on {competitor} vs us",
                "body": "You mentioned you're also looking at {competitor}. Totally fair. Here's where we genuinely win and where they might be a better fit. I'd rather you make the right call than the easy one.",
                "asset": "Competitive battle card or comparison one-pager",
            },
            "authority": {
                "subject": "Materials for your team's review",
                "body": "I know you need to loop in {stakeholder}. I put together a one-page executive summary that hits the points they'll care about most: ROI, timeline, and risk. Want me to send it over?",
                "asset": "Executive summary one-pager, tailored to stakeholder concerns",
            },
            "need": {
                "subject": "Something that might change the calculus",
                "body": "I appreciated the honest pushback on whether this is a priority right now. One thing I didn't get to share: {relevant_insight}. Might be worth a 10-minute follow-up if you're open to it.",
                "asset": "Industry report or benchmark data showing peer adoption",
            },
        }

        template = templates.get(obj["category"], {})
        follow_ups.append({
            "type": "objection_response",
            "objection_category": obj["category"],
            "trigger_quote": obj["quote"],
            "suggested_subject": template.get("subject", f"Following up on {obj['category']} discussion"),
            "suggested_body": template.get("body", "Following up on our conversation..."),
            "recommended_asset": template.get("asset", ""),
            "timing": "Send within 24 hours of call",
        })

    # Capitalize on buying signals
    for sig in insights.get("buying_signals", [])[:2]:
        if sig["type"] == "champion_identified":
            follow_ups.append({
                "type": "champion_enablement",
                "signal": sig["quote"],
                "suggested_subject": "Ammo for your internal pitch",
                "suggested_body": "You clearly get the value here. I want to make sure you have everything you need to bring the team along. Here's a deck you can customize + the key metrics that usually close the deal internally.",
                "recommended_asset": "Internal pitch deck template + metrics cheat sheet",
                "timing": "Send within 12 hours",
            })
        elif sig["type"] == "next_steps_agreed":
            follow_ups.append({
                "type": "momentum_keeper",
                "signal": sig["quote"],
                "suggested_subject": "Recap + next steps locked in",
                "suggested_body": "Great call. Here's what we agreed on: {next_steps}. I'll have {deliverable} ready by {date}. Let me know if anything changes on your end.",
                "recommended_asset": "Meeting summary with action items",
                "timing": "Send within 2 hours of call",
            })

    return follow_ups


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def load_transcript_file(filepath: str) -> dict:
    """Load a transcript from a text file."""
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    text = path.read_text(encoding="utf-8")
    return {"id": path.stem, "title": path.stem, "transcript": text, "participants": []}


def load_transcript_dir(dirpath: str) -> list[dict]:
    """Load all .txt transcript files from a directory."""
    path = Path(dirpath)
    if not path.is_dir():
        print(f"ERROR: Directory not found: {dirpath}", file=sys.stderr)
        sys.exit(1)
    files = sorted(path.glob("*.txt"))
    if not files:
        print(f"WARNING: No .txt files found in {dirpath}", file=sys.stderr)
        return []
    return [load_transcript_file(str(f)) for f in files]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_summary(insights: dict) -> None:
    """Print a human-readable summary of insights."""
    s = insights["summary"]
    print(f"\n{'='*60}")
    print(f"  Call: {insights['source_id']}")
    print(f"  Temperature: {s['deal_temperature'].upper()}")
    print(f"{'='*60}")

    if s["total_objections"]:
        print(f"\n  🚫 Objections ({s['total_objections']}):")
        for cat, count in sorted(s["objection_categories"].items(), key=lambda x: -x[1]):
            print(f"     {cat}: {count}")
        for obj in insights["objections"][:3]:
            print(f"     → [{obj['category']}] \"{obj['quote'][:80]}...\"" if len(obj['quote']) > 80 else f"     → [{obj['category']}] \"{obj['quote']}\"")

    if s["total_buying_signals"]:
        print(f"\n  ✅ Buying Signals ({s['total_buying_signals']}):")
        for sig_type, count in sorted(s["signal_types"].items(), key=lambda x: -x[1]):
            print(f"     {sig_type}: {count}")

    if s["competitors_mentioned"]:
        print(f"\n  ⚔️  Competitors: {', '.join(s['competitors_mentioned'])}")

    if s["has_pricing_discussion"]:
        print(f"\n  💰 Pricing discussed: Yes ({len(insights['pricing_discussions'])} mentions)")

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract structured insights from sales call transcripts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file transcript.txt
  %(prog)s --dir ./transcripts/ --content-topics
  %(prog)s --gong --days 7 --follow-ups
  %(prog)s --file call.txt --output insights.json
        """,
    )

    # Input sources (mutually exclusive)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="Path to a single transcript file (.txt)")
    source.add_argument("--dir", help="Path to directory of transcript files (.txt)")
    source.add_argument("--gong", action="store_true", help="Pull transcripts from Gong API")

    # Gong options
    parser.add_argument("--days", type=int, default=7, help="Days of history to pull from Gong (default: 7)")
    parser.add_argument("--call-id", help="Specific Gong call ID to analyze")

    # Output options
    parser.add_argument("--output", "-o", help="Write JSON output to file")
    parser.add_argument("--json", action="store_true", help="Output raw JSON to stdout")
    parser.add_argument("--content-topics", action="store_true", help="Generate content topics from recurring objections")
    parser.add_argument("--follow-ups", action="store_true", help="Generate follow-up suggestions")

    args = parser.parse_args()

    # Load transcripts
    calls = []
    if args.file:
        calls = [load_transcript_file(args.file)]
    elif args.dir:
        calls = load_transcript_dir(args.dir)
    elif args.gong:
        calls = fetch_calls_from_gong(days=args.days, call_id=args.call_id)

    if not calls:
        print("No transcripts to analyze.", file=sys.stderr)
        sys.exit(1)

    # Analyze
    all_insights = []
    for call in calls:
        insights = analyze_transcript(call["transcript"], source_id=call.get("id", "unknown"))
        insights["title"] = call.get("title", "")
        all_insights.append(insights)

        if not args.json:
            print_summary(insights)

    # Content topics
    content_topics = []
    if args.content_topics and len(all_insights) > 0:
        content_topics = generate_content_topics(all_insights)
        if not args.json:
            print(f"\n{'='*60}")
            print("  📝 Content Topics from Recurring Objections")
            print(f"{'='*60}")
            for topic in content_topics:
                print(f"\n  [{topic['priority'].upper()}] {topic['category']} (mentioned {topic['frequency']}x)")
                print(f"  Topic: {topic['suggested_topic']}")
                print(f"  Types: {', '.join(topic['recommended_content_types'])}")
                print(f"  Angle: {topic['strategic_angle']}")

    # Follow-ups
    all_follow_ups = []
    if args.follow_ups:
        for insights in all_insights:
            follow_ups = generate_follow_ups(insights)
            all_follow_ups.extend(follow_ups)
            if not args.json:
                print(f"\n{'='*60}")
                print(f"  📧 Follow-up Suggestions for: {insights['source_id']}")
                print(f"{'='*60}")
                for fu in follow_ups:
                    print(f"\n  Type: {fu['type']}")
                    print(f"  Subject: {fu['suggested_subject']}")
                    print(f"  Timing: {fu['timing']}")
                    if fu.get("recommended_asset"):
                        print(f"  Asset: {fu['recommended_asset']}")

    # Build output
    output = {
        "analyzed_at": datetime.utcnow().isoformat() + "Z",
        "total_calls": len(all_insights),
        "calls": all_insights,
    }
    if content_topics:
        output["content_topics"] = content_topics
    if all_follow_ups:
        output["follow_ups"] = all_follow_ups

    # Aggregate stats
    output["aggregate"] = {
        "total_objections": sum(i["summary"]["total_objections"] for i in all_insights),
        "total_buying_signals": sum(i["summary"]["total_buying_signals"] for i in all_insights),
        "all_competitors": list(set(c for i in all_insights for c in i["summary"]["competitors_mentioned"])),
        "temperature_distribution": dict(Counter(i["summary"]["deal_temperature"] for i in all_insights)),
    }

    # Output
    if args.json:
        print(json.dumps(output, indent=2))

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, indent=2))
        if not args.json:
            print(f"\n✅ Output written to {args.output}")


if __name__ == "__main__":
    main()
