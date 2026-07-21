#!/usr/bin/env python3
"""
Content Quality Scorer — Automated content scoring engine.

Scores drafts against configurable voice patterns BEFORE they publish.
Five scoring dimensions: voice similarity, specificity, AI slop detection,
length appropriateness, and engagement potential.

Input: JSON file with drafts array
Output: scored drafts with pass/fail recommendations

Usage:
    python content-quality-scorer.py --input drafts.json --verbose
    python content-quality-scorer.py --input drafts.json --threshold 75
    python content-quality-scorer.py --init-weights  # Create default weights file
"""

import json
import re
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import math

# ── Configuration (all paths relative/configurable) ──

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = Path(os.environ.get("CONTENT_OPS_DATA_DIR", PROJECT_DIR / "data"))

DRAFTS_FILE = DATA_DIR / "content-drafts-latest.json"
WEIGHTS_FILE = DATA_DIR / "quality-scorer-weights.json"
LOG_FILE = DATA_DIR / "quality-scores-log.json"

# Default scoring threshold (adjustable)
DEFAULT_THRESHOLD = 60

# Platform character limits
PLATFORM_LIMITS = {
    "x": {"min": 50, "max": 280, "optimal_min": 150, "optimal_max": 260},
    "linkedin": {"min": 200, "max": 1500, "optimal_min": 500, "optimal_max": 1200},
    "youtube_short": {"min": 100, "max": 800, "optimal_min": 200, "optimal_max": 600},
    "newsletter": {"min": 300, "max": 2000, "optimal_min": 800, "optimal_max": 1600},
}

# Banned AI words — penalized in scoring
BANNED_WORDS = [
    "leverage", "synergy", "ecosystem", "holistic", "at the end of the day",
    "delve", "tapestry", "landscape", "multifaceted", "nuanced", "pivotal",
    "realm", "robust", "seamless", "testament", "transformative", "underscore",
    "utilize", "whilst", "keen", "embark", "comprehensive", "intricate",
    "commendable", "meticulous", "paramount", "groundbreaking", "innovative",
    "cutting-edge", "paradigm", "Additionally", "crucial", "enduring",
    "enhance", "fostering", "garner", "highlight", "interplay", "intricacies",
    "showcase", "vibrant", "valuable", "profound", "renowned", "breathtaking",
    "nestled", "stunning", "I'm excited to share", "I think maybe",
    "It could potentially", "dive into", "game-changer", "unlock"
]

# AI patterns to detect
AI_PATTERNS = [
    (r"pivotal moment|is a testament|stands as", "significance_inflation"),
    (r"boasts|vibrant|commitment to", "promotional_language"),
    (r"experts believe|industry reports|studies show", "vague_attribution"),
    (r"despite.{1,50}continues to", "formulaic_structure"),
    (r"serves as|acts as|functions as", "copula_avoidance"),
    (r"it's not just .{1,30}, it's", "negative_parallelism"),
    (r"could potentially|might possibly|may perhaps", "excessive_hedging"),
    (r"the future looks bright|exciting times ahead|stay tuned", "generic_conclusion"),
]

# Voice markers — configurable positive signals for your brand voice
# Override these by setting VOICE_MARKERS_FILE env var pointing to a JSON file
VOICE_MARKERS = [
    # Numbers with specificity
    (r'\$[\d,]+[KkMmBb]?(?:\+)?', 2.0, "revenue_markers"),
    (r'\d+%', 1.5, "percentage_stats"),
    (r'\d+x', 1.5, "multiplier_stats"),
    (r'\d+ (?:hours?|minutes?|days?|weeks?|months?|years?)', 1.0, "time_specifics"),
    (r'\d+ (?:pages?|pieces?|tools?|agents?|companies|founders?|members)', 1.0, "count_specifics"),
    # Personal framing
    (r'I (?:built|found|asked|remember|had lunch)', 2.0, "personal_framing"),
    (r'Here\'s what happened|A friend who|I asked \d+', 1.5, "story_framing"),
    # Contrarian hooks
    (r'Most people .{1,50} wrong|Everyone says .{1,30} That\'s', 2.0, "contrarian_hooks"),
    (r'Harsh reality:', 1.5, "harsh_reality"),
    # Engagement patterns
    (r'What\'s your take\?|What did I miss\?|What would you do', 1.0, "engagement_cta"),
    # Short sentences (under 15 words)
    (r'[.!?]\s+[A-Z][^.!?]{1,75}[.!?]', 0.5, "short_sentences"),
]

# Default scoring weights
DEFAULT_WEIGHTS = {
    "voice_similarity": 0.35,
    "specificity": 0.25,
    "slop_penalty": 0.20,
    "length_appropriateness": 0.10,
    "engagement_potential": 0.10,
}


def load_weights():
    """Load scoring weights from file or return defaults."""
    if WEIGHTS_FILE.exists():
        try:
            with open(WEIGHTS_FILE) as f:
                data = json.load(f)
                weights = data.get("weights", DEFAULT_WEIGHTS)
                threshold = data.get("threshold", DEFAULT_THRESHOLD)
                return weights, threshold
        except Exception as e:
            print(f"⚠ Error loading weights: {e}, using defaults")
    return DEFAULT_WEIGHTS, DEFAULT_THRESHOLD


def save_weights(weights, threshold):
    """Save scoring weights and threshold to file."""
    data = {
        "weights": weights,
        "threshold": threshold,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0"
    }
    WEIGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WEIGHTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def log_score(draft_id, platform, scores, passed, reasons):
    """Log scoring results for analysis."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "draft_id": draft_id,
        "platform": platform,
        "scores": scores,
        "total_score": sum(scores.values()),
        "passed": passed,
        "failure_reasons": reasons,
    }

    log_data = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE) as f:
                log_data = json.load(f)
        except Exception:
            log_data = []

    log_data.append(log_entry)

    # Keep only last 1000 entries
    if len(log_data) > 1000:
        log_data = log_data[-1000:]

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=2)


def score_voice_similarity(draft_text):
    """Score how well draft matches voice patterns (0-100)."""
    score = 0
    matches = {}

    for pattern, weight, category in VOICE_MARKERS:
        pattern_matches = re.findall(pattern, draft_text, re.IGNORECASE)
        if pattern_matches:
            match_count = len(pattern_matches)
            category_score = min(weight * math.log(match_count + 1) * 10, weight * 25)
            score += category_score
            matches[category] = matches.get(category, 0) + match_count

    # Bonus for short punchy sentences
    sentences = re.split(r'[.!?]+', draft_text)
    short_sentences = [s for s in sentences if len(s.split()) <= 15 and len(s.split()) >= 3]
    sentence_ratio = len(short_sentences) / max(len(sentences), 1)
    score += sentence_ratio * 15

    return min(score, 100), matches


def score_specificity(draft_text):
    """Score specificity — real numbers, examples, named entities (0-100)."""
    score = 0

    number_patterns = [
        r'\$[\d,]+[KkMmBb]?(?:\+)?',
        r'\d+%',
        r'\d+x',
        r'\d+[\.,]?\d*\s*(?:hours?|minutes?|days?|weeks?|months?|years?)',
        r'\d+\s*(?:pages?|pieces?|tools?|agents?|companies|founders?|members)',
    ]

    total_numbers = 0
    for pattern in number_patterns:
        matches = re.findall(pattern, draft_text, re.IGNORECASE)
        total_numbers += len(matches)

    word_count = len(draft_text.split())
    number_density = total_numbers / max(word_count / 50, 1)
    score += min(number_density * 30, 50)

    # Named entities and specific examples
    entity_patterns = [
        r'[A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)*',
        r'@[A-Za-z0-9_]+',
        r'(?:Apple|Google|Meta|Microsoft|Amazon|Tesla|ChatGPT|Claude|OpenAI)',
    ]

    entity_count = 0
    for pattern in entity_patterns:
        matches = re.findall(pattern, draft_text)
        entity_count += len(matches)

    score += min(entity_count * 10, 30)

    # Before/after comparisons
    comparison_patterns = [
        r'\d+.*→.*\d+',
        r'from \d+.*to \d+',
        r'before.*\d+.*after.*\d+',
        r'used to.*now.*'
    ]

    for pattern in comparison_patterns:
        if re.search(pattern, draft_text, re.IGNORECASE):
            score += 10
            break

    return min(score, 100)


def score_slop_penalty(draft_text):
    """Detect and penalize AI slop and banned phrases (0-100, higher = less slop)."""
    score = 100
    detected_issues = []

    text_lower = draft_text.lower()

    banned_found = []
    for word in BANNED_WORDS:
        if word.lower() in text_lower:
            banned_found.append(word)
            score -= 10

    if banned_found:
        detected_issues.append(f"Banned words: {', '.join(banned_found[:3])}")

    ai_patterns_found = []
    for pattern, pattern_name in AI_PATTERNS:
        matches = re.findall(pattern, draft_text, re.IGNORECASE)
        if matches:
            ai_patterns_found.append(pattern_name)
            score -= 8

    if ai_patterns_found:
        detected_issues.append(f"AI patterns: {', '.join(ai_patterns_found[:3])}")

    # Em dash overuse
    em_dash_count = draft_text.count('—')
    word_count = len(draft_text.split())
    if em_dash_count > word_count / 200:
        score -= 5
        detected_issues.append("Excessive em dash usage")

    # Corporate speak
    corporate_patterns = [
        r'I\'m excited to share',
        r'it is important to note',
        r'in order to',
        r'we are pleased to announce',
        r'stay tuned for',
    ]

    for pattern in corporate_patterns:
        if re.search(pattern, draft_text, re.IGNORECASE):
            score -= 15
            detected_issues.append("Corporate speak detected")
            break

    return max(score, 0), detected_issues


def score_length_appropriateness(draft_text, platform):
    """Score if content length is appropriate for platform (0-100)."""
    char_count = len(draft_text)
    limits = PLATFORM_LIMITS.get(platform, PLATFORM_LIMITS["x"])

    if char_count < limits["min"]:
        shortfall_ratio = char_count / limits["min"]
        return max(shortfall_ratio * 100, 20)
    elif char_count > limits["max"]:
        excess_ratio = limits["max"] / char_count
        return max(excess_ratio * 100, 30)
    elif limits["optimal_min"] <= char_count <= limits["optimal_max"]:
        return 100
    else:
        return 85


def score_engagement_potential(draft_text, platform):
    """Score engagement potential based on CTAs and hooks (0-100)."""
    score = 0

    cta_patterns = {
        "x": [r'What\'s your take\?', r'What did I miss\?', r'Reply with'],
        "linkedin": [r'What would you do', r'What do you think', r'Drop .* below', r'curious.*your'],
        "youtube_short": [r'Comment.*and I\'ll', r'Follow for more'],
        "newsletter": [r'subscribe', r'read more', r'check it out'],
    }

    platform_ctas = cta_patterns.get(platform, cta_patterns["x"])
    for pattern in platform_ctas:
        if re.search(pattern, draft_text, re.IGNORECASE):
            score += 25
            break

    # Strong hooks (first 100 characters)
    hook = draft_text[:100]
    hook_patterns = [
        r'^\d+.*\.',
        r'^Most people.*wrong',
        r'^I (?:built|found|asked)',
        r'^Harsh reality:',
        r'^Here\'s what',
    ]

    for pattern in hook_patterns:
        if re.search(pattern, hook, re.IGNORECASE):
            score += 25
            break

    # Question-based engagement
    question_count = len(re.findall(r'\?', draft_text))
    if question_count >= 1:
        score += min(question_count * 15, 30)

    # Debate invitation
    debate_patterns = [
        r'Agree or disagree',
        r'What\'s your experience',
        r'Change my mind',
    ]

    for pattern in debate_patterns:
        if re.search(pattern, draft_text, re.IGNORECASE):
            score += 20
            break

    return min(score, 100)


def score_draft(draft, weights, threshold):
    """Score a single draft against all criteria."""
    platform = draft.get("platform", "x")
    draft_text = draft.get("draft", "")

    voice_score, voice_matches = score_voice_similarity(draft_text)
    specificity_score = score_specificity(draft_text)
    slop_score, slop_issues = score_slop_penalty(draft_text)
    length_score = score_length_appropriateness(draft_text, platform)
    engagement_score = score_engagement_potential(draft_text, platform)

    scores = {
        "voice_similarity": voice_score,
        "specificity": specificity_score,
        "slop_penalty": slop_score,
        "length_appropriateness": length_score,
        "engagement_potential": engagement_score,
    }

    total_score = sum(scores[key] * weights[key] for key in scores.keys())
    total_score = round(total_score, 1)

    passed = total_score >= threshold

    failure_reasons = []
    if voice_score < 50:
        failure_reasons.append("Low voice match - lacks brand voice patterns")
    if specificity_score < 40:
        failure_reasons.append("Not specific enough - needs real numbers/examples")
    if slop_score < 70:
        failure_reasons.append("Contains AI slop - " + "; ".join(slop_issues))
    if length_score < 60:
        failure_reasons.append(f"Length issue for {platform}")
    if engagement_score < 40:
        failure_reasons.append("Weak engagement - needs better CTA/hook")

    result = {
        "draft_id": draft.get("id"),
        "platform": platform,
        "total_score": total_score,
        "scores": scores,
        "passed": passed,
        "failure_reasons": failure_reasons,
        "voice_matches": voice_matches,
        "slop_issues": slop_issues,
        "char_count": len(draft_text),
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }

    log_score(draft.get("id"), platform, scores, passed, failure_reasons)
    return result


def score_drafts_file(file_path=None, output_path=None, threshold_override=None, verbose=False):
    """Score all drafts in a file."""
    input_file = Path(file_path) if file_path else DRAFTS_FILE

    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        return None

    with open(input_file) as f:
        data = json.load(f)

    drafts = data.get("drafts", [])
    if not drafts:
        print("❌ No drafts found in input file")
        return None

    weights, threshold = load_weights()
    if threshold_override:
        threshold = threshold_override
        print(f"📊 Using threshold override: {threshold}")

    print(f"📊 Scoring {len(drafts)} drafts with threshold {threshold}")
    if verbose:
        print(f"📊 Weights: {weights}")

    results = []
    passed_count = 0

    for i, draft in enumerate(drafts):
        result = score_draft(draft, weights, threshold)
        results.append(result)

        if result["passed"]:
            passed_count += 1

        if verbose:
            print(f"\n[{i+1}/{len(drafts)}] {result['platform']} | Score: {result['total_score']}/100")
            if result["passed"]:
                print(f"  ✅ PASS")
            else:
                print(f"  ❌ FAIL: {'; '.join(result['failure_reasons'])}")

    total_scores = [r["total_score"] for r in results]
    avg_score = sum(total_scores) / len(total_scores)
    pass_rate = (passed_count / len(results)) * 100

    summary = {
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "total_drafts": len(drafts),
        "passed_count": passed_count,
        "pass_rate": round(pass_rate, 1),
        "average_score": round(avg_score, 1),
        "threshold": threshold,
        "weights": weights,
        "results": results,
    }

    if output_path:
        output_file = Path(output_path)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = DATA_DIR / f"quality-scores-{timestamp}.json"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    latest_file = DATA_DIR / "quality-scores-latest.json"
    with open(latest_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*60}")
    print(f"QUALITY SCORING RESULTS")
    print(f"{'='*60}")
    print(f"Total drafts: {len(drafts)}")
    print(f"Passed: {passed_count} ({pass_rate:.1f}%)")
    print(f"Failed: {len(drafts) - passed_count}")
    print(f"Average score: {avg_score:.1f}/100")
    print(f"Threshold: {threshold}/100")
    print(f"\nSaved to: {output_file}")
    print(f"Saved to: {latest_file}")

    if verbose:
        print(f"\n🏆 TOP SCORING DRAFTS:")
        top_drafts = sorted(results, key=lambda x: x["total_score"], reverse=True)[:3]
        for i, result in enumerate(top_drafts):
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"  {i+1}. {result['platform']} | {result['total_score']}/100 | {status}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Score content drafts for quality")
    parser.add_argument("--input", type=str, help="Input drafts JSON file")
    parser.add_argument("--output", type=str, help="Output scores JSON file")
    parser.add_argument("--threshold", type=float, help="Scoring threshold override")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--init-weights", action="store_true", help="Initialize default weights file")
    args = parser.parse_args()

    if args.init_weights:
        save_weights(DEFAULT_WEIGHTS, DEFAULT_THRESHOLD)
        print(f"✅ Initialized weights file: {WEIGHTS_FILE}")
        return

    score_drafts_file(
        file_path=args.input,
        output_path=args.output,
        threshold_override=args.threshold,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
