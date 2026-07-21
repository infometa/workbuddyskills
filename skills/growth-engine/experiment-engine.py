#!/usr/bin/env python3
"""
Experiment Engine — Autonomous growth experimentation for AI agents.

Inspired by Karpathy's autoresearch pattern: create experiments with hypotheses,
log data points, run statistical analysis (bootstrap CI + Mann-Whitney U),
auto-promote winners to a living playbook, and suggest next experiments.

Supports batch mode (up to 10 variants simultaneously).

Usage:
  # Create a new experiment
  python3 experiment-engine.py create --agent content --hypothesis "Thread posts get 2x impressions vs single posts" \
    --variable "format" --variants '["thread", "single"]' --metric "impressions" --cycle-hours 8

  # Log a data point for a running experiment
  python3 experiment-engine.py log --agent content --experiment-id EXP-001 --variant "thread" \
    --metrics '{"impressions": 4500, "clicks": 120, "replies": 8}'

  # Score an experiment (auto-promotes winner if criteria met)
  python3 experiment-engine.py score --agent content --experiment-id EXP-001

  # List active experiments for an agent
  python3 experiment-engine.py list --agent content

  # Get current best practices (promoted winners)
  python3 experiment-engine.py playbook --agent content

  # Suggest next experiment based on gaps
  python3 experiment-engine.py suggest --agent content
"""
import argparse, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import stats

# ── Configuration ──────────────────────────────────────────────────────────────
# Base directory for experiment data. Override with GROWTH_ENGINE_DATA_DIR env var.
BASE_DIR = Path(os.environ.get("GROWTH_ENGINE_DATA_DIR", "./data/experiments"))

# Define your agent/channel taxonomy. High-volume channels need fewer samples
# per variant because data arrives faster. Adjust to match your setup.
HIGH_VOLUME_AGENTS = set(os.environ.get("HIGH_VOLUME_AGENTS", "content,email").split(","))
LOW_VOLUME_AGENTS = set(os.environ.get("LOW_VOLUME_AGENTS", "seo,linkedin,blog").split(","))

# Batch mode: allow up to this many variants simultaneously (vs simple A/B)
BATCH_MODE_MAX_VARIANTS = int(os.environ.get("BATCH_MODE_MAX_VARIANTS", "10"))

# Map agent names to their marketing channels. Customize for your org.
AGENT_CHANNEL = {
    "content":  "social",
    "email":    "email",
    "linkedin": "linkedin",
    "seo":      "seo",
    "blog":     "blog",
}

# Statistical parameters
BOOTSTRAP_ITERATIONS = int(os.environ.get("BOOTSTRAP_ITERATIONS", "1000"))
P_WINNER = float(os.environ.get("P_WINNER", "0.05"))    # p-value threshold for declaring a winner
P_TREND = float(os.environ.get("P_TREND", "0.10"))      # p-value threshold for "trending" status
LIFT_WIN = float(os.environ.get("LIFT_WIN", "15.0"))     # minimum % lift required for "keep" decision


def get_min_samples(agent: str, override: int | None = None) -> int:
    """Return minimum samples per variant before scoring.
    High-volume channels (email, social) need fewer samples (10).
    Low-volume channels (SEO, blog) need more (30) for reliable signal.
    Explicit override wins if > 3.
    """
    if override is not None and override > 3:
        return override
    return 10 if agent in HIGH_VOLUME_AGENTS else 30


def bootstrap_lift_ci(a_vals, b_vals, n_iter=BOOTSTRAP_ITERATIONS, ci=95):
    """Bootstrap confidence interval for lift = (mean(b) - mean(a)) / mean(a) * 100.
    Returns (lower_bound, upper_bound) as percentages, or (None, None) if baseline is zero.
    """
    a = np.array(a_vals, dtype=float)
    b = np.array(b_vals, dtype=float)
    lifts = []
    rng = np.random.default_rng(42)
    for _ in range(n_iter):
        sa = rng.choice(a, size=len(a), replace=True)
        sb = rng.choice(b, size=len(b), replace=True)
        baseline_mean = sa.mean()
        if baseline_mean == 0:
            continue
        lifts.append((sb.mean() - baseline_mean) / baseline_mean * 100)
    if not lifts:
        return None, None
    lo = float(np.percentile(lifts, (100 - ci) / 2))
    hi = float(np.percentile(lifts, 100 - (100 - ci) / 2))
    return round(lo, 1), round(hi, 1)


def get_agent_dir(agent):
    d = BASE_DIR / agent
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_json(path, default=None):
    if path.exists():
        return json.loads(path.read_text())
    return default if default is not None else {}


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, default=str))


def next_id(agent):
    d = get_agent_dir(agent)
    experiments = load_json(d / "experiments.json", [])
    return f"EXP-{agent.upper()}-{len(experiments)+1:03d}"


def cmd_create(args):
    d = get_agent_dir(args.agent)
    experiments = load_json(d / "experiments.json", [])

    exp_id = next_id(args.agent)
    min_s = get_min_samples(args.agent, args.min_samples if args.min_samples != 3 else None)

    variants = json.loads(args.variants)
    batch_mode = getattr(args, "batch_mode", False)
    if batch_mode and len(variants) > BATCH_MODE_MAX_VARIANTS:
        print(f"⚠️  Batch mode capped at {BATCH_MODE_MAX_VARIANTS} variants (got {len(variants)})")
        variants = variants[:BATCH_MODE_MAX_VARIANTS]

    experiment = {
        "id": exp_id,
        "agent": args.agent,
        "channel": AGENT_CHANNEL.get(args.agent, "unknown"),
        "hypothesis": args.hypothesis,
        "variable": args.variable,
        "variants": variants,
        "primary_metric": args.metric,
        "cycle_hours": args.cycle_hours,
        "min_samples": min_s,
        "batch_mode": batch_mode,
        "max_variants": BATCH_MODE_MAX_VARIANTS if batch_mode else 2,
        "status": "running",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data_points": [],
        "baseline_variant": variants[0],
        "result": None,
        "winner": None
    }

    experiments.append(experiment)
    save_json(d / "experiments.json", experiments)

    # Update active experiments index
    active = load_json(d / "active.json", [])
    active.append({"id": exp_id, "variable": args.variable, "variants": experiment["variants"],
                    "current_variant_idx": 0})
    save_json(d / "active.json", active)

    mode_str = f"BATCH ({len(variants)} variants)" if batch_mode else "A/B"
    print(f"✅ Created {exp_id}: {args.hypothesis}")
    print(f"   Channel: {experiment['channel']} | Variable: {args.variable} | Mode: {mode_str}")
    print(f"   Variants: {experiment['variants']}")
    print(f"   Metric: {args.metric} | Cycle: {args.cycle_hours}h | Min samples/variant: {min_s}")
    return exp_id


def cmd_log(args):
    d = get_agent_dir(args.agent)
    experiments = load_json(d / "experiments.json", [])

    for exp in experiments:
        if exp["id"] == args.experiment_id:
            dp = {
                "variant": args.variant,
                "metrics": json.loads(args.metrics),
                "logged_at": datetime.now(timezone.utc).isoformat(),
                "notes": args.notes or ""
            }
            exp["data_points"].append(dp)
            save_json(d / "experiments.json", experiments)
            print(f"✅ Logged data point for {args.experiment_id} variant '{args.variant}': {dp['metrics']}")
            return

    print(f"❌ Experiment {args.experiment_id} not found")
    sys.exit(1)


def cmd_score(args):
    d = get_agent_dir(args.agent)
    experiments = load_json(d / "experiments.json", [])

    for exp in experiments:
        if exp["id"] == args.experiment_id and exp["status"] in ("running", "active", "trending"):
            # Group data points by variant
            variant_data = {}
            for dp in exp["data_points"]:
                v = dp["variant"]
                if v not in variant_data:
                    variant_data[v] = []
                variant_data[v].append(dp["metrics"].get(exp["primary_metric"], 0))

            baseline_v = exp["baseline_variant"]
            min_samples = exp.get("min_samples",
                                  get_min_samples(exp["agent"]) if "agent" in exp else 15)

            # Enforce per-variant sample floor
            insufficient = []
            for v, data in variant_data.items():
                if len(data) < min_samples:
                    insufficient.append((v, len(data)))

            if insufficient:
                for v, n in insufficient:
                    print(f"⏳ {exp['id']}: Variant '{v}' has {n}/{min_samples} samples. Need more data.")
                # Check for trending signal even with fewer samples (need at least 15)
                all_counts = {v: len(data) for v, data in variant_data.items()}
                min_count = min(all_counts.values()) if all_counts else 0
                if min_count >= 15 and baseline_v in variant_data:
                    baseline_vals = variant_data[baseline_v]
                    best_trend_v, best_trend_p = None, 1.0
                    for v, vals in variant_data.items():
                        if v == baseline_v or len(vals) < 15:
                            continue
                        _, p = stats.mannwhitneyu(baseline_vals, vals, alternative="less")
                        if p < P_TREND and p < best_trend_p:
                            best_trend_p = p
                            best_trend_v = v
                    if best_trend_v:
                        exp["status"] = "trending"
                        save_json(d / "experiments.json", experiments)
                        lift = (np.mean(variant_data[best_trend_v]) - np.mean(baseline_vals)) / np.mean(baseline_vals) * 100 if np.mean(baseline_vals) else 0
                        print(f"📈 {exp['id']}: TRENDING — '{best_trend_v}' p={best_trend_p:.3f}, lift={lift:.1f}% (needs more samples to confirm)")
                return

            if not variant_data:
                print(f"⏳ {exp['id']}: No data points yet.")
                return

            baseline_vals = np.array(variant_data.get(baseline_v, []), dtype=float)
            if len(baseline_vals) < min_samples:
                print(f"⏳ {exp['id']}: Baseline variant '{baseline_v}' has {len(baseline_vals)}/{min_samples} samples.")
                return

            # Evaluate all non-baseline variants
            results = []
            for v, vals in variant_data.items():
                if v == baseline_v:
                    continue
                arr = np.array(vals, dtype=float)
                baseline_mean = baseline_vals.mean()
                variant_mean  = arr.mean()
                lift = ((variant_mean - baseline_mean) / baseline_mean * 100) if baseline_mean != 0 else 0

                # Mann-Whitney U test (non-parametric, no normality assumption)
                _, p_two = stats.mannwhitneyu(baseline_vals, arr, alternative="two-sided")
                _, p_less = stats.mannwhitneyu(baseline_vals, arr, alternative="less")

                ci_lo, ci_hi = bootstrap_lift_ci(baseline_vals.tolist(), arr.tolist())

                if p_less < P_WINNER and lift >= LIFT_WIN:
                    status = "keep"
                elif p_two < P_WINNER and lift < 0:
                    status = "crash" if lift <= -LIFT_WIN else "discard"
                elif p_less < P_TREND and len(vals) >= 15:
                    status = "trending"
                else:
                    status = "running"

                results.append({
                    "variant": v,
                    "mean": round(float(variant_mean), 2),
                    "lift_pct": round(lift, 1),
                    "p_value": round(float(p_less), 4),
                    "ci_95": [ci_lo, ci_hi],
                    "n": len(vals),
                    "status": status
                })

            baseline_mean = float(baseline_vals.mean())
            overall_result = {
                "baseline": baseline_v,
                "baseline_mean": round(baseline_mean, 2),
                "baseline_n": len(baseline_vals),
                "variants": results,
                "scored_at": datetime.now(timezone.utc).isoformat(),
                "min_samples": min_samples,
                "thresholds": {"p_winner": P_WINNER, "p_trend": P_TREND, "lift_pct_required": LIFT_WIN}
            }

            winners  = [r for r in results if r["status"] == "keep"]
            crashes  = [r for r in results if r["status"] in ("crash", "discard")]
            trending = [r for r in results if r["status"] == "trending"]

            if winners:
                best = max(winners, key=lambda r: r["lift_pct"])
                exp["status"] = "keep"
                exp["winner"] = best["variant"]
                exp["result"] = overall_result
                save_json(d / "experiments.json", experiments)

                # Auto-promote to playbook
                playbook = load_json(d / "playbook.json", {})
                playbook[exp["variable"]] = {
                    "best": best["variant"],
                    "metric": exp["primary_metric"],
                    "avg": best["mean"],
                    "improvement": best["lift_pct"],
                    "p_value": best["p_value"],
                    "ci_95": best["ci_95"],
                    "experiment_id": exp["id"],
                    "promoted_at": datetime.now(timezone.utc).isoformat()
                }
                save_json(d / "playbook.json", playbook)

                # Remove from active index
                active = load_json(d / "active.json", [])
                active = [a for a in active if a["id"] != exp["id"]]
                save_json(d / "active.json", active)

                print(f"🏆 {exp['id']}: KEEP — '{best['variant']}' +{best['lift_pct']}% lift "
                      f"(p={best['p_value']}, 95% CI [{best['ci_95'][0]}, {best['ci_95'][1]}]%)")
                print(f"   📖 Playbook updated: {exp['variable']} → '{best['variant']}'")

            elif all(r["status"] in ("crash", "discard") for r in results) and results:
                worst = min(results, key=lambda r: r["lift_pct"])
                exp["status"] = "discard"
                exp["result"] = overall_result
                save_json(d / "experiments.json", experiments)
                active = load_json(d / "active.json", [])
                active = [a for a in active if a["id"] != exp["id"]]
                save_json(d / "active.json", active)
                print(f"💀 {exp['id']}: DISCARD — baseline wins. Best variant: '{worst['variant']}' "
                      f"at {worst['lift_pct']}% (p={worst['p_value']})")

            elif trending:
                exp["status"] = "trending"
                exp["result"] = overall_result
                save_json(d / "experiments.json", experiments)
                best_t = max(trending, key=lambda r: r["lift_pct"])
                print(f"📈 {exp['id']}: TRENDING — '{best_t['variant']}' +{best_t['lift_pct']}% "
                      f"(p={best_t['p_value']}, n={best_t['n']}). Keep collecting data.")

            else:
                exp["status"] = "running"
                exp["result"] = overall_result
                save_json(d / "experiments.json", experiments)
                for r in results:
                    print(f"⏳ {exp['id']}: '{r['variant']}' {r['lift_pct']:+.1f}% lift, p={r['p_value']} — running")
            return

    print(f"❌ Active experiment {args.experiment_id} not found")


def cmd_list(args):
    d = get_agent_dir(args.agent)
    experiments = load_json(d / "experiments.json", [])

    status_filter = args.status or "all"
    icons = {
        "running": "🔬", "active": "🔬",
        "trending": "📈",
        "keep": "🏆", "promoted": "🏆",
        "discard": "💀", "killed": "💀",
        "crash": "🔴",
        "inconclusive": "🤷"
    }
    for exp in experiments:
        s = exp["status"]
        if status_filter != "all" and s != status_filter:
            aliases = {"active": "running", "promoted": "keep", "killed": "discard"}
            if aliases.get(s) != status_filter and s != status_filter:
                continue
        dp_count = len(exp.get("data_points", []))
        icon = icons.get(s, "❓")
        ch = exp.get("channel", AGENT_CHANNEL.get(exp["agent"], "?"))
        print(f"{icon} {exp['id']}: {exp['hypothesis']}")
        print(f"   Variable: {exp['variable']} | Channel: {ch} | Status: {s} | Data points: {dp_count}")
        if exp.get("winner"):
            result = exp.get("result", {})
            lift = ""
            if isinstance(result, dict):
                for vr in result.get("variants", []):
                    if vr["variant"] == exp["winner"]:
                        lift = f" ({vr['lift_pct']:+.1f}% lift, p={vr['p_value']})"
                        break
            print(f"   Winner: {exp['winner']}{lift}")
        print()


def cmd_playbook(args):
    d = get_agent_dir(args.agent)
    playbook = load_json(d / "playbook.json", {})

    if not playbook:
        print(f"📖 No playbook entries for {args.agent} yet. Run some experiments!")
        return

    print(f"📖 {args.agent.upper()} PLAYBOOK — Empirically Proven Best Practices\n")
    for variable, entry in playbook.items():
        p_str = f", p={entry['p_value']}" if "p_value" in entry else ""
        ci_str = f", 95% CI {entry['ci_95']}" if "ci_95" in entry else ""
        print(f"  {variable}: '{entry['best']}' (+{entry['improvement']}% on {entry['metric']}{p_str}{ci_str})")
        print(f"    Source: {entry['experiment_id']} | Promoted: {entry['promoted_at'][:10]}")
        print()


def cmd_suggest(args):
    d = get_agent_dir(args.agent)
    experiments = load_json(d / "experiments.json", [])
    playbook = load_json(d / "playbook.json", {})

    # Define testable categories per channel. Customize these for your business.
    categories = {
        "content": ["hook_style", "post_format", "cta_type", "post_time", "thread_length",
                     "emoji_usage", "data_vs_narrative", "question_vs_statement"],
        "email": ["subject_line_style", "opener_type", "email_length", "personalization_depth",
                   "cta_style", "send_time", "follow_up_timing", "social_proof_type"],
        "linkedin": ["inmail_opener", "role_framing", "company_pitch", "personalization_level",
                      "subject_line", "follow_up_cadence"],
        "blog": ["headline_style", "content_format", "platform_priority", "visual_style",
                  "posting_time", "content_length"],
        "seo": ["title_tag_format", "meta_description_style", "content_structure",
                 "internal_linking", "heading_format"]
    }

    tested = set(playbook.keys())
    tested.update(e["variable"] for e in experiments if e["status"] in ("running", "active", "trending"))
    agent_cats = categories.get(args.agent, [])
    untested = [c for c in agent_cats if c not in tested]
    min_s = get_min_samples(args.agent)
    ch = AGENT_CHANNEL.get(args.agent, "?")

    if untested:
        print(f"💡 Suggested next experiments for {args.agent} ({ch}, min {min_s} samples/variant):")
        for cat in untested[:3]:
            print(f"   → {cat}")
    else:
        print(f"✅ {args.agent} has tested all standard categories. Time for advanced experiments!")


def main():
    parser = argparse.ArgumentParser(description="Experiment Engine — Autonomous growth experimentation")
    sub = parser.add_subparsers(dest="command")

    p_create = sub.add_parser("create", help="Create a new experiment")
    p_create.add_argument("--agent", required=True, help="Agent/channel name (e.g., content, email, seo)")
    p_create.add_argument("--hypothesis", required=True, help="What you're testing and expected outcome")
    p_create.add_argument("--variable", required=True, help="The variable being tested (e.g., hook_style)")
    p_create.add_argument("--variants", required=True, help="JSON array of variant names")
    p_create.add_argument("--metric", required=True, help="Primary metric to optimize (e.g., impressions)")
    p_create.add_argument("--cycle-hours", type=int, default=24, help="Hours per experiment cycle (default: 24)")
    p_create.add_argument("--min-samples", type=int, default=3,
                          help="Override min samples/variant (default: auto based on channel volume)")
    p_create.add_argument("--batch-mode", action="store_true",
                          help="Enable batch mode: up to 10 variants simultaneously")

    p_log = sub.add_parser("log", help="Log a data point for a running experiment")
    p_log.add_argument("--agent", required=True)
    p_log.add_argument("--experiment-id", required=True)
    p_log.add_argument("--variant", required=True)
    p_log.add_argument("--metrics", required=True, help="JSON object of metric values")
    p_log.add_argument("--notes", default="")

    p_score = sub.add_parser("score", help="Score an experiment (auto-promotes winners)")
    p_score.add_argument("--agent", required=True)
    p_score.add_argument("--experiment-id", required=True)

    p_list = sub.add_parser("list", help="List experiments for an agent")
    p_list.add_argument("--agent", required=True)
    p_list.add_argument("--status", default="all", help="Filter by status (running/trending/keep/discard/all)")

    p_play = sub.add_parser("playbook", help="Show empirically proven best practices")
    p_play.add_argument("--agent", required=True)

    p_sug = sub.add_parser("suggest", help="Suggest next experiments based on gaps")
    p_sug.add_argument("--agent", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    {"create": cmd_create, "log": cmd_log, "score": cmd_score,
     "list": cmd_list, "playbook": cmd_playbook, "suggest": cmd_suggest}[args.command](args)


if __name__ == "__main__":
    main()
