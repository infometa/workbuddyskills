#!/usr/bin/env python3
"""
AutoGrowth Weekly Scorecard Generator

Reads experiment results and playbook data across all agents and generates
a weekly report showing wins, trends, running experiments, and discards.

Works with both JSON (from experiment-engine.py) and TSV data formats.

Usage:
  python3 autogrowth-weekly-scorecard.py                    # Current week
  python3 autogrowth-weekly-scorecard.py --weeks 2          # Two weeks back
  python3 autogrowth-weekly-scorecard.py --output report.md # Write to file
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# ── Configuration ──────────────────────────────────────────────────────────────
# Base directory for experiment data. Must match experiment-engine.py setting.
BASE_DIR = Path(os.environ.get("GROWTH_ENGINE_DATA_DIR", "./data/experiments"))

# Agent names to scan. Customize to match your agent taxonomy.
AGENTS = os.environ.get("GROWTH_ENGINE_AGENTS", "content,email,linkedin,seo,blog").split(",")

RESULTS_COLS = ["experiment_id", "variable", "variant", "metric_value", "sample_n", "status", "date", "description"]
PLAYBOOK_COLS = ["experiment_id", "agent", "channel", "rule", "lift_pct", "p_value", "date_added", "notes"]


def parse_tsv(filepath, expected_cols):
    """Parse a TSV file, return list of dicts. Gracefully handles missing/empty files."""
    rows = []
    if not filepath.exists():
        return rows
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return rows
        reader = csv.DictReader(content.splitlines(), delimiter="\t")
        if reader.fieldnames and reader.fieldnames[0].startswith("#"):
            return rows
        for row in reader:
            rows.append(dict(row))
    except Exception:
        pass
    return rows


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def week_range(weeks_back=1):
    """Return (start_date, end_date) for the target week (Mon-Sun)."""
    today = datetime.now().date()
    this_monday = today - timedelta(days=today.weekday())
    start = this_monday - timedelta(weeks=weeks_back - 1)
    end = start + timedelta(days=6)
    return start, end


def in_week(date_str, start, end):
    """Check if a date string falls within the week range."""
    if not date_str:
        return True
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            d = datetime.strptime(date_str.strip(), fmt).date()
            return start <= d <= end
        except ValueError:
            continue
    return True  # include if unparseable


def load_all_results(weeks_back=1):
    """Load all results TSV rows across agents, filtered by week."""
    start, end = week_range(weeks_back)
    all_rows = []
    for agent in AGENTS:
        filepath = BASE_DIR / agent.strip() / "results.tsv"
        rows = parse_tsv(filepath, RESULTS_COLS)
        for row in rows:
            row["_agent"] = agent.strip()
            date_val = row.get("date", "")
            if in_week(date_val, start, end):
                all_rows.append(row)
    return all_rows, start, end


def load_all_playbooks():
    """Load all playbook TSV rows across agents."""
    all_rows = []
    for agent in AGENTS:
        filepath = BASE_DIR / agent.strip() / "playbook.tsv"
        rows = parse_tsv(filepath, PLAYBOOK_COLS)
        for row in rows:
            row["_agent"] = agent.strip()
            all_rows.append(row)
    return all_rows


def generate_scorecard(weeks_back=1):
    results, start, end = load_all_results(weeks_back)
    playbook = load_all_playbooks()

    week_label = f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"
    lines = []

    lines.append(f"# AutoGrowth Weekly Scorecard — Week of {week_label}")
    lines.append("")

    # ── Summary ──────────────────────────────────────────────────────────────
    if not results:
        active = new = completed = kept = discarded = data_points = 0
    else:
        statuses = [r.get("status", "").strip().lower() for r in results]
        running_statuses = {"running", "active", "in_progress", "in progress"}
        keep_statuses = {"keep", "winner", "kept", "significant"}
        discard_statuses = {"discard", "discarded", "loser", "no_effect", "no effect"}
        new_statuses = {"new", "launched"}

        active = sum(1 for s in statuses if s in running_statuses)
        new = sum(1 for s in statuses if s in new_statuses)
        kept = sum(1 for s in statuses if s in keep_statuses)
        discarded = sum(1 for s in statuses if s in discard_statuses)
        completed = kept + discarded
        data_points = sum(safe_int(r.get("sample_n", 0)) for r in results)

    lines.append("## Summary")
    lines.append(f"- Total experiments active: {active}")
    lines.append(f"- New experiments launched: {new}")
    lines.append(f"- Experiments completed: {completed} ({kept} kept, {discarded} discarded)")
    lines.append(f"- Total data points collected: {data_points:,}")
    lines.append("")

    # ── Big Wins ─────────────────────────────────────────────────────────────
    lines.append("## 🏆 Big Wins (keep status this week)")
    keep_statuses_set = {"keep", "winner", "kept", "significant"}
    winners = [r for r in results if r.get("status", "").strip().lower() in keep_statuses_set]
    winners.sort(key=lambda r: safe_float(r.get("metric_value", 0)), reverse=True)

    if not winners:
        lines.append("No data yet")
    else:
        for r in winners:
            exp_id = r.get("experiment_id", "?")
            agent = r.get("_agent", "?")
            variable = r.get("variable", "?")
            variant = r.get("variant", "?")
            metric = safe_float(r.get("metric_value", 0))
            n = safe_int(r.get("sample_n", 0))
            desc = r.get("description", "")
            lines.append(f"### {exp_id} ({agent})")
            lines.append(f"- **Tested:** {variable} → variant: {variant}")
            lines.append(f"- **Metric value:** {metric:.4f} | **Sample n:** {n:,}")
            if desc:
                lines.append(f"- **Description:** {desc}")
            pb_match = [p for p in playbook if p.get("experiment_id", "") == exp_id]
            if pb_match:
                rule = pb_match[0].get("rule", "")
                lift = pb_match[0].get("lift_pct", "")
                p_val = pb_match[0].get("p_value", "")
                lines.append(f"- **Playbook rule:** {rule}")
                if lift:
                    lines.append(f"- **Lift:** {lift}% | **p-value:** {p_val}")
            lines.append("")

    # ── Trending ──────────────────────────────────────────────────────────────
    lines.append("## 📈 Trending (watch these)")
    trending_statuses = {"trending", "watch", "promising"}
    trending = [r for r in results if r.get("status", "").strip().lower() in trending_statuses]
    trending.sort(key=lambda r: safe_float(r.get("metric_value", 0)), reverse=True)

    if not trending:
        lines.append("No data yet")
    else:
        for r in trending:
            exp_id = r.get("experiment_id", "?")
            agent = r.get("_agent", "?")
            variant = r.get("variant", "?")
            metric = safe_float(r.get("metric_value", 0))
            n = safe_int(r.get("sample_n", 0))
            lines.append(f"- **{exp_id}** ({agent}) — variant `{variant}` leading at {metric:.4f} | {n:,} samples so far")
    lines.append("")

    # ── Running ───────────────────────────────────────────────────────────────
    lines.append("## 🔬 Running (in progress)")
    running_statuses_set = {"running", "active", "in_progress", "in progress"}
    running = [r for r in results if r.get("status", "").strip().lower() in running_statuses_set]

    if not running:
        lines.append("No data yet")
    else:
        for r in running:
            exp_id = r.get("experiment_id", "?")
            agent = r.get("_agent", "?")
            variable = r.get("variable", "?")
            variant = r.get("variant", "?")
            n = safe_int(r.get("sample_n", 0))
            lines.append(f"- **{exp_id}** ({agent}): testing `{variable}` → `{variant}` — {n:,} samples")
    lines.append("")

    # ── Discarded ─────────────────────────────────────────────────────────────
    lines.append("## ❌ Discarded (didn't work)")
    discard_statuses_set = {"discard", "discarded", "loser", "no_effect", "no effect"}
    discarded_rows = [r for r in results if r.get("status", "").strip().lower() in discard_statuses_set]

    if not discarded_rows:
        lines.append("No data yet")
    else:
        for r in discarded_rows:
            exp_id = r.get("experiment_id", "?")
            agent = r.get("_agent", "?")
            desc = r.get("description", "No significant effect found")
            lines.append(f"- **{exp_id}** ({agent}): {desc}")
    lines.append("")

    # ── Cumulative Playbook ───────────────────────────────────────────────────
    lines.append("## 📊 Cumulative Playbook")
    total_rules = len(playbook)
    lines.append(f"- Total rules in playbook across all agents: {total_rules}")
    lines.append("")

    if playbook:
        sorted_pb = sorted(playbook, key=lambda p: safe_float(p.get("lift_pct", 0)), reverse=True)
        lines.append("**Top 3 biggest lifts ever found:**")
        for i, p in enumerate(sorted_pb[:3], 1):
            exp_id = p.get("experiment_id", "?")
            agent = p.get("_agent", "?")
            rule = p.get("rule", "?")
            lift = p.get("lift_pct", "?")
            lines.append(f"{i}. **{exp_id}** ({agent}) — {lift}% lift: {rule}")
    else:
        lines.append("No playbook rules yet — experiments still running.")
    lines.append("")

    # ── Next Week ─────────────────────────────────────────────────────────────
    lines.append("## 📅 Next Week")
    next_start = end + timedelta(days=1)
    next_end = next_start + timedelta(days=6)
    lines.append(f"Week of {next_start.strftime('%b %d')} – {next_end.strftime('%b %d, %Y')}")
    lines.append("")

    planned_statuses = {"planned", "next", "queued", "upcoming"}
    all_results_unfiltered = []
    for agent in AGENTS:
        filepath = BASE_DIR / agent.strip() / "results.tsv"
        rows = parse_tsv(filepath, RESULTS_COLS)
        for row in rows:
            row["_agent"] = agent.strip()
            all_results_unfiltered.append(row)

    planned = [r for r in all_results_unfiltered if r.get("status", "").strip().lower() in planned_statuses]
    if not planned:
        lines.append("No new experiments scheduled yet. Add rows with status=planned to results.tsv files.")
    else:
        for r in planned:
            exp_id = r.get("experiment_id", "?")
            agent = r.get("_agent", "?")
            variable = r.get("variable", "?")
            variant = r.get("variant", "?")
            lines.append(f"- **{exp_id}** ({agent}): launch `{variable}` test → `{variant}`")
    lines.append("")

    lines.append("---")
    lines.append(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(l for l in lines)


def main():
    parser = argparse.ArgumentParser(description="AutoGrowth Weekly Scorecard Generator")
    parser.add_argument("--weeks", type=int, default=1, help="How many weeks back to report (default: 1 = current week)")
    parser.add_argument("--output", type=str, default=None, help="Write output to file instead of stdout")
    args = parser.parse_args()

    scorecard = generate_scorecard(weeks_back=args.weeks)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(scorecard)
        print(f"Scorecard written to {out_path}", file=sys.stderr)
    else:
        print(scorecard)


if __name__ == "__main__":
    main()
