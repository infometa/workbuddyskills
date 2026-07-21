#!/usr/bin/env python3
"""
Meeting-to-Action Extractor

Takes meeting transcripts and extracts structured action items, decisions,
follow-ups, and insights using LLM analysis.

Usage:
  # Single transcript
  python3 meeting_action_extractor.py --transcript meeting.txt

  # Output as JSON
  python3 meeting_action_extractor.py --transcript meeting.txt --format json

  # Output as markdown (default)
  python3 meeting_action_extractor.py --transcript meeting.txt --format markdown

  # Batch mode — process a directory of transcripts
  python3 meeting_action_extractor.py --batch ./transcripts/ --output ./actions/

  # Read from stdin (pipe or paste)
  cat meeting.txt | python3 meeting_action_extractor.py --stdin

  # Push action items to HubSpot as tasks
  python3 meeting_action_extractor.py --transcript meeting.txt --push-hubspot

  # Dry run (no LLM calls, shows what would be processed)
  python3 meeting_action_extractor.py --transcript meeting.txt --dry-run
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# LLM Integration
# ---------------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """You are an expert meeting analyst. Your job is to extract structured information from meeting transcripts with high accuracy.

You must return ONLY valid JSON (no markdown, no explanation) matching this exact schema:

{
  "meeting_title": "string — inferred from context",
  "meeting_date": "string — date if mentioned, else 'Unknown'",
  "attendees": ["string — names mentioned as present"],
  "decisions": [
    {
      "decision": "string — what was decided",
      "made_by": "string — who made or drove the decision",
      "context": "string — brief context/reasoning",
      "confidence": 0.0-1.0
    }
  ],
  "action_items": [
    {
      "action": "string — specific task to be done",
      "owner": "string — person responsible",
      "deadline": "string — deadline if mentioned, else null",
      "priority": "high|medium|low",
      "is_implicit": false,
      "source_quote": "string — the relevant quote from transcript",
      "confidence": 0.0-1.0
    }
  ],
  "open_questions": [
    {
      "question": "string — unresolved question or topic",
      "raised_by": "string — who raised it, if clear",
      "context": "string — brief context",
      "confidence": 0.0-1.0
    }
  ],
  "key_insights": [
    {
      "insight": "string — notable observation, data point, or quotable moment",
      "speaker": "string — who said it",
      "quote": "string — direct quote if available",
      "confidence": 0.0-1.0
    }
  ],
  "follow_up_meetings": [
    {
      "topic": "string — what needs follow-up discussion",
      "suggested_attendees": ["string"],
      "urgency": "high|medium|low",
      "confidence": 0.0-1.0
    }
  ]
}

RULES:
- Detect implicit commitments. Phrases like "I'll handle that", "let me look into it", "I can take care of that", "we should probably..." are action items.
- Assign confidence scores: 1.0 = explicitly stated, 0.8 = strongly implied, 0.5-0.7 = inferred from context, <0.5 = uncertain.
- For priority: high = mentioned as urgent/blocking/deadline-sensitive. medium = important but not blocking. low = nice-to-have or background task.
- If someone says "I'll do X by Friday" — that's an action item with owner and deadline.
- If a question is asked and not answered in the transcript, it's an open question.
- Be exhaustive. Missing an action item is worse than including a low-confidence one."""


def call_llm(prompt: str, system_prompt: str = "") -> str:
    """
    Call the configured LLM provider.
    Set LLM_PROVIDER to 'anthropic' or 'openai'.
    """
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    model = os.getenv("LLM_MODEL", "")

    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            return _fallback_extraction()

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=model or "claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except ImportError:
            print("Warning: 'anthropic' package not installed. Using fallback.", file=sys.stderr)
            return _fallback_extraction()
        except Exception as e:
            print(f"Warning: Anthropic API error: {e}. Using fallback.", file=sys.stderr)
            return _fallback_extraction()

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return _fallback_extraction()

        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model or "gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except ImportError:
            print("Warning: 'openai' package not installed. Using fallback.", file=sys.stderr)
            return _fallback_extraction()
        except Exception as e:
            print(f"Warning: OpenAI API error: {e}. Using fallback.", file=sys.stderr)
            return _fallback_extraction()

    else:
        print(f"Warning: Unknown LLM provider '{provider}'.", file=sys.stderr)
        return _fallback_extraction()


def _fallback_extraction() -> str:
    """Return a placeholder when no LLM is available."""
    return json.dumps({
        "meeting_title": "Unknown (LLM unavailable)",
        "meeting_date": "Unknown",
        "attendees": [],
        "decisions": [],
        "action_items": [],
        "open_questions": [],
        "key_insights": [],
        "follow_up_meetings": [],
        "_error": "No LLM API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.",
    })


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_from_transcript(transcript: str) -> dict:
    """
    Send a transcript to the LLM and parse the structured extraction.
    """
    # Truncate extremely long transcripts to avoid token limits
    max_chars = 100_000  # ~25k tokens
    if len(transcript) > max_chars:
        print(
            f"Warning: Transcript truncated from {len(transcript)} to {max_chars} chars.",
            file=sys.stderr,
        )
        transcript = transcript[:max_chars] + "\n\n[TRANSCRIPT TRUNCATED]"

    prompt = f"""Extract all decisions, action items, open questions, key insights, and follow-up meetings from this meeting transcript.

Return ONLY valid JSON matching the schema in your instructions.

---
TRANSCRIPT:
{transcript}
---"""

    raw_response = call_llm(prompt, system_prompt=EXTRACTION_SYSTEM_PROMPT)

    # Parse JSON from response (handle potential markdown wrapping)
    try:
        # Try direct parse first
        return json.loads(raw_response)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        if "```json" in raw_response:
            json_str = raw_response.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        elif "```" in raw_response:
            json_str = raw_response.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)
        else:
            print("Error: Could not parse LLM response as JSON.", file=sys.stderr)
            return {
                "meeting_title": "Parse Error",
                "decisions": [],
                "action_items": [],
                "open_questions": [],
                "key_insights": [],
                "follow_up_meetings": [],
                "_error": f"Failed to parse LLM response. Raw: {raw_response[:500]}",
            }


# ---------------------------------------------------------------------------
# Output Formatting
# ---------------------------------------------------------------------------

def format_markdown(extraction: dict, source_file: Optional[str] = None) -> str:
    """Format extraction results as readable markdown."""
    lines = []
    title = extraction.get("meeting_title", "Meeting Notes")
    date = extraction.get("meeting_date", "Unknown")

    lines.extend([
        f"# {title}",
        "",
        f"**Date:** {date}",
        f"**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ])

    if source_file:
        lines.append(f"**Source:** {source_file}")

    attendees = extraction.get("attendees", [])
    if attendees:
        lines.append(f"**Attendees:** {', '.join(attendees)}")

    lines.append("")

    # --- Decisions ---
    decisions = extraction.get("decisions", [])
    if decisions:
        lines.extend(["## Decisions Made", ""])
        for i, d in enumerate(decisions, 1):
            conf = d.get("confidence", 0)
            conf_bar = "🟢" if conf >= 0.8 else "🟡" if conf >= 0.5 else "🔴"
            lines.append(f"{i}. **{d.get('decision', 'Unknown')}**")
            lines.append(f"   - Made by: {d.get('made_by', 'Unknown')}")
            lines.append(f"   - Context: {d.get('context', 'N/A')}")
            lines.append(f"   - Confidence: {conf_bar} {conf:.0%}")
            lines.append("")

    # --- Action Items ---
    actions = extraction.get("action_items", [])
    if actions:
        lines.extend(["## Action Items", ""])

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        actions_sorted = sorted(actions, key=lambda a: priority_order.get(a.get("priority", "medium"), 1))

        for i, a in enumerate(actions_sorted, 1):
            priority = a.get("priority", "medium")
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
            implicit_tag = " *(implicit)*" if a.get("is_implicit") else ""
            deadline = a.get("deadline") or "No deadline"
            conf = a.get("confidence", 0)

            lines.append(f"{i}. {priority_emoji} **{a.get('action', 'Unknown')}**{implicit_tag}")
            lines.append(f"   - Owner: **{a.get('owner', 'Unassigned')}**")
            lines.append(f"   - Deadline: {deadline}")
            lines.append(f"   - Confidence: {conf:.0%}")
            if a.get("source_quote"):
                lines.append(f'   - Source: "{a["source_quote"]}"')
            lines.append("")

    # --- Open Questions ---
    questions = extraction.get("open_questions", [])
    if questions:
        lines.extend(["## Open Questions", ""])
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. **{q.get('question', 'Unknown')}**")
            if q.get("raised_by"):
                lines.append(f"   - Raised by: {q['raised_by']}")
            if q.get("context"):
                lines.append(f"   - Context: {q['context']}")
            lines.append("")

    # --- Key Insights ---
    insights = extraction.get("key_insights", [])
    if insights:
        lines.extend(["## Key Insights", ""])
        for i, ins in enumerate(insights, 1):
            lines.append(f"{i}. **{ins.get('insight', 'Unknown')}**")
            if ins.get("speaker"):
                lines.append(f"   - Speaker: {ins['speaker']}")
            if ins.get("quote"):
                lines.append(f'   - Quote: "{ins["quote"]}"')
            lines.append("")

    # --- Follow-up Meetings ---
    followups = extraction.get("follow_up_meetings", [])
    if followups:
        lines.extend(["## Follow-up Meetings Needed", ""])
        for i, fu in enumerate(followups, 1):
            urgency_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(fu.get("urgency", "medium"), "⚪")
            lines.append(f"{i}. {urgency_emoji} **{fu.get('topic', 'Unknown')}**")
            attendees_list = fu.get("suggested_attendees", [])
            if attendees_list:
                lines.append(f"   - Attendees: {', '.join(attendees_list)}")
            lines.append("")

    # --- Summary Stats ---
    lines.extend([
        "---",
        "",
        "### Extraction Summary",
        f"- Decisions: {len(decisions)}",
        f"- Action Items: {len(actions)} ({sum(1 for a in actions if a.get('priority') == 'high')} high priority)",
        f"- Open Questions: {len(questions)}",
        f"- Key Insights: {len(insights)}",
        f"- Follow-up Meetings: {len(followups)}",
        "",
        "*Generated by Meeting-to-Action Extractor*",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HubSpot Integration (stub with real API structure)
# ---------------------------------------------------------------------------

def push_to_hubspot(extraction: dict) -> dict:
    """
    Push action items to HubSpot as tasks.

    Requires HUBSPOT_API_KEY env var.
    Creates a task for each action item with owner, deadline, and priority.

    Returns a summary of created/failed tasks.
    """
    api_key = os.getenv("HUBSPOT_API_KEY", "")
    if not api_key:
        return {
            "success": False,
            "error": "HUBSPOT_API_KEY not set. Cannot push to HubSpot.",
            "created": 0,
            "failed": 0,
        }

    actions = extraction.get("action_items", [])
    if not actions:
        return {"success": True, "created": 0, "failed": 0, "message": "No action items to push."}

    # --- HubSpot Task Creation ---
    # Uses the HubSpot CRM API v3 to create tasks (engagements)
    # Docs: https://developers.hubspot.com/docs/api/crm/tasks

    import requests  # only imported when actually pushing

    results = {"created": 0, "failed": 0, "errors": []}
    hubspot_url = "https://api.hubapi.com/crm/v3/objects/tasks"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Map priority to HubSpot priority values
    priority_map = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}

    for action in actions:
        # Build the task payload
        task_body = action.get("action", "Meeting action item")
        owner_name = action.get("owner", "Unassigned")
        deadline = action.get("deadline")
        priority = priority_map.get(action.get("priority", "medium"), "MEDIUM")

        meeting_title = extraction.get("meeting_title", "Meeting")
        task_subject = f"[{meeting_title}] {task_body[:100]}"

        payload = {
            "properties": {
                "hs_task_subject": task_subject,
                "hs_task_body": (
                    f"Action: {task_body}\n"
                    f"Owner: {owner_name}\n"
                    f"Source: Meeting transcript extraction\n"
                    f"Confidence: {action.get('confidence', 'N/A')}"
                ),
                "hs_task_status": "NOT_STARTED",
                "hs_task_priority": priority,
            }
        }

        # Add due date if we have a deadline
        if deadline and deadline.lower() not in ("none", "no deadline", "null", "tbd"):
            payload["properties"]["hs_timestamp"] = deadline  # HubSpot expects ISO format

        try:
            resp = requests.post(hubspot_url, headers=headers, json=payload, timeout=10)
            if resp.status_code in (200, 201):
                results["created"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Task '{task_body[:50]}': HTTP {resp.status_code}")
        except requests.RequestException as e:
            results["failed"] += 1
            results["errors"].append(f"Task '{task_body[:50]}': {str(e)}")

    results["success"] = results["failed"] == 0
    return results


# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------

def process_batch(directory: str, output_dir: Optional[str], fmt: str, push_hs: bool) -> list[dict]:
    """
    Process all transcript files in a directory.

    Supports .txt, .md, and .json files.
    """
    transcript_files = []
    for ext in ("*.txt", "*.md", "*.json"):
        transcript_files.extend(glob.glob(os.path.join(directory, ext)))

    transcript_files.sort()

    if not transcript_files:
        print(f"No transcript files found in {directory}", file=sys.stderr)
        return []

    print(f"📂 Found {len(transcript_files)} transcripts to process", file=sys.stderr)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    results = []
    for i, filepath in enumerate(transcript_files, 1):
        filename = os.path.basename(filepath)
        print(f"\n[{i}/{len(transcript_files)}] Processing: {filename}", file=sys.stderr)

        with open(filepath, "r") as f:
            transcript = f.read()

        extraction = extract_from_transcript(transcript)
        extraction["_source_file"] = filepath

        if fmt == "markdown":
            output = format_markdown(extraction, source_file=filename)
            ext = ".md"
        else:
            output = json.dumps(extraction, indent=2, default=str)
            ext = ".json"

        if output_dir:
            out_filename = Path(filename).stem + f"_actions{ext}"
            out_path = os.path.join(output_dir, out_filename)
            with open(out_path, "w") as f:
                f.write(output)
            print(f"  ✅ Saved to {out_path}", file=sys.stderr)
        else:
            print(output)
            print("\n" + "=" * 80 + "\n")

        if push_hs:
            hs_result = push_to_hubspot(extraction)
            print(
                f"  📤 HubSpot: {hs_result.get('created', 0)} created, "
                f"{hs_result.get('failed', 0)} failed",
                file=sys.stderr,
            )

        results.append(extraction)

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Meeting-to-Action Extractor — Extract decisions, action items, and follow-ups from meeting transcripts.",
        epilog="Supports single transcripts, stdin, and batch processing of entire directories.",
    )

    # Input source (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--transcript", "-t",
        help="Path to a single transcript file (.txt, .md).",
    )
    input_group.add_argument(
        "--batch", "-b",
        help="Directory of transcript files to process in batch.",
    )
    input_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read transcript from stdin.",
    )

    # Output options
    parser.add_argument(
        "--output", "-o",
        help="Output file (single mode) or directory (batch mode).",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown).",
    )

    # Integration options
    parser.add_argument(
        "--push-hubspot",
        action="store_true",
        help="Push action items to HubSpot as tasks (requires HUBSPOT_API_KEY).",
    )

    # Execution options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without making LLM calls.",
    )

    args = parser.parse_args()

    # --- Single transcript mode ---
    if args.transcript:
        if not os.path.exists(args.transcript):
            print(f"Error: File not found: {args.transcript}", file=sys.stderr)
            sys.exit(1)

        with open(args.transcript, "r") as f:
            transcript = f.read()

        if args.dry_run:
            word_count = len(transcript.split())
            print(f"📄 Would process: {args.transcript} ({word_count} words, {len(transcript)} chars)")
            print(f"   Format: {args.format}")
            print(f"   HubSpot push: {'yes' if args.push_hubspot else 'no'}")
            return

        print(f"📄 Processing: {args.transcript}", file=sys.stderr)
        extraction = extract_from_transcript(transcript)

        if args.format == "markdown":
            output = format_markdown(extraction, source_file=args.transcript)
        else:
            output = json.dumps(extraction, indent=2, default=str)

        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"✅ Written to {args.output}", file=sys.stderr)
        else:
            print(output)

        if args.push_hubspot:
            hs_result = push_to_hubspot(extraction)
            print(
                f"📤 HubSpot: {hs_result.get('created', 0)} tasks created, "
                f"{hs_result.get('failed', 0)} failed",
                file=sys.stderr,
            )

        # Print summary to stderr
        actions = extraction.get("action_items", [])
        decisions = extraction.get("decisions", [])
        print(
            f"\n📊 Extracted: {len(decisions)} decisions, {len(actions)} action items "
            f"({sum(1 for a in actions if a.get('priority') == 'high')} high priority)",
            file=sys.stderr,
        )

    # --- Batch mode ---
    elif args.batch:
        if not os.path.isdir(args.batch):
            print(f"Error: Directory not found: {args.batch}", file=sys.stderr)
            sys.exit(1)

        if args.dry_run:
            files = []
            for ext in ("*.txt", "*.md", "*.json"):
                files.extend(glob.glob(os.path.join(args.batch, ext)))
            print(f"📂 Would process {len(files)} files from {args.batch}:")
            for f in sorted(files):
                print(f"   - {os.path.basename(f)}")
            return

        results = process_batch(args.batch, args.output, args.format, args.push_hubspot)

        # Batch summary
        total_actions = sum(len(r.get("action_items", [])) for r in results)
        total_decisions = sum(len(r.get("decisions", [])) for r in results)
        print(
            f"\n📊 Batch complete: {len(results)} transcripts → "
            f"{total_decisions} decisions, {total_actions} action items",
            file=sys.stderr,
        )

    # --- Stdin mode ---
    elif args.stdin:
        if args.dry_run:
            print("📄 Would process transcript from stdin")
            return

        print("📄 Reading transcript from stdin...", file=sys.stderr)
        transcript = sys.stdin.read()

        if not transcript.strip():
            print("Error: Empty input.", file=sys.stderr)
            sys.exit(1)

        extraction = extract_from_transcript(transcript)

        if args.format == "markdown":
            output = format_markdown(extraction)
        else:
            output = json.dumps(extraction, indent=2, default=str)

        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"✅ Written to {args.output}", file=sys.stderr)
        else:
            print(output)

        if args.push_hubspot:
            hs_result = push_to_hubspot(extraction)
            print(
                f"📤 HubSpot: {hs_result.get('created', 0)} tasks created",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
