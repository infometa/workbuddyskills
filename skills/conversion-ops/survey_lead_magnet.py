#!/usr/bin/env python3
"""
Survey-to-Lead-Magnet Engine
==============================
Takes survey response data (CSV), segments respondents by pain point clusters,
ranks segments by size and commercial potential, and auto-generates lead magnet
briefs targeting each segment.

Usage:
    python survey_lead_magnet.py --csv survey_responses.csv
    python survey_lead_magnet.py --csv survey.csv --pain-columns "biggest_challenge" "top_frustration"
    python survey_lead_magnet.py --csv survey.csv --top-segments 5 --json
    python survey_lead_magnet.py --csv survey.csv --output lead_magnets.json
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Columns that likely contain pain point / challenge responses
PAIN_COLUMN_PATTERNS = re.compile(
    r"(challenge|pain|frustrat|struggle|problem|difficult|obstacle|"
    r"barrier|concern|issue|blocker|worry|fear|hard|tough|"
    r"biggest|main|top|primary|key|major|worst)",
    re.IGNORECASE,
)

# Words that signal commercial intent / buying readiness
COMMERCIAL_SIGNALS = re.compile(
    r"\b(budget|cost|price|invest|spend|pay|afford|roi|revenue|"
    r"software|tool|platform|solution|vendor|agency|consultant|"
    r"hire|outsource|automate|scale|grow|implement|upgrade|"
    r"need|want|looking for|searching|evaluating|considering)\b",
    re.IGNORECASE,
)

# Lead magnet format heuristics
FORMAT_KEYWORDS = {
    "guide": ["understand", "learn", "how", "why", "strategy", "approach", "framework", "concept", "complex"],
    "checklist": ["process", "steps", "workflow", "setup", "launch", "implement", "execute", "routine", "daily"],
    "template": ["create", "write", "build", "design", "plan", "proposal", "email", "message", "document"],
    "calculator": ["cost", "budget", "roi", "numbers", "forecast", "estimate", "pricing", "revenue", "metrics"],
    "swipe_file": ["examples", "inspiration", "copy", "ads", "headlines", "subject lines", "creative", "ideas"],
}

# Stopwords for clustering (extend sklearn's default)
EXTRA_STOPWORDS = [
    "really", "just", "like", "thing", "things", "lot", "also",
    "get", "getting", "got", "know", "dont", "don't", "can't",
    "want", "need", "think", "feel", "make", "much", "many",
    "very", "would", "could", "should", "way", "able",
    "one", "two", "first", "new", "good", "bad", "hard",
    "well", "time", "still", "even", "right", "going",
]


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class PainSegment:
    segment_id: int
    theme: str
    top_keywords: list
    respondent_count: int
    respondent_pct: float
    commercial_score: float  # 0-100
    sample_responses: list
    representative_quotes: list


@dataclass
class LeadMagnetBrief:
    segment_id: int
    segment_theme: str
    title: str
    format: str  # guide, checklist, template, calculator, swipe_file
    hook: str
    outline: list
    target_cta: str
    distribution_channel: str
    viral_potential: int  # 0-100
    conversion_potential: int  # 0-100
    combined_score: float
    implementation_notes: str


@dataclass
class AnalysisResult:
    total_respondents: int
    columns_analyzed: list
    segments: list
    lead_magnets: list
    implementation_roadmap: list


# ---------------------------------------------------------------------------
# Data Ingestion
# ---------------------------------------------------------------------------

def load_survey_data(csv_path: str) -> pd.DataFrame:
    """Load survey CSV. Tries multiple encodings."""
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            return df
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    raise ValueError(f"Could not read CSV file: {csv_path}")


def detect_pain_columns(df: pd.DataFrame) -> list:
    """Auto-detect columns that likely contain pain point / challenge data."""
    pain_cols = []
    for col in df.columns:
        if PAIN_COLUMN_PATTERNS.search(col):
            pain_cols.append(col)

    # If no pattern matches, look for open-text columns (long average text)
    if not pain_cols:
        for col in df.columns:
            if df[col].dtype == object:
                avg_len = df[col].dropna().astype(str).str.len().mean()
                if avg_len > 30:  # likely free-text responses
                    pain_cols.append(col)

    return pain_cols


def extract_responses(df: pd.DataFrame, pain_columns: list) -> list:
    """Extract and combine text responses from pain columns."""
    responses = []
    for _, row in df.iterrows():
        parts = []
        for col in pain_columns:
            val = row.get(col)
            if pd.notna(val) and str(val).strip():
                parts.append(str(val).strip())
        combined = " ".join(parts)
        if combined:
            responses.append(combined)
    return responses


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

def preprocess_text(text: str) -> str:
    """Clean and normalize text for clustering."""
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def cluster_responses(responses: list, n_clusters: Optional[int] = None) -> tuple:
    """
    Cluster responses using TF-IDF + KMeans.
    Returns (labels, vectorizer, tfidf_matrix, n_clusters).
    """
    if len(responses) < 5:
        # Too few responses — treat as single cluster
        return [0] * len(responses), None, None, 1

    cleaned = [preprocess_text(r) for r in responses]

    # Build TF-IDF matrix
    stop_words = list(TfidfVectorizer(stop_words="english").get_stop_words()) + EXTRA_STOPWORDS
    vectorizer = TfidfVectorizer(
        max_features=500,
        stop_words=stop_words,
        min_df=2 if len(responses) > 20 else 1,
        max_df=0.85,
        ngram_range=(1, 2),
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(cleaned)
    except ValueError:
        # All responses too similar or empty after preprocessing
        return [0] * len(responses), None, None, 1

    # Auto-determine cluster count if not specified
    if n_clusters is None:
        max_k = min(10, len(responses) // 3, tfidf_matrix.shape[0] - 1)
        max_k = max(2, max_k)

        best_k = 3
        best_score = -1

        for k in range(2, max_k + 1):
            try:
                km = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = km.fit_predict(tfidf_matrix)
                score = silhouette_score(tfidf_matrix, labels)
                if score > best_score:
                    best_score = score
                    best_k = k
            except ValueError:
                continue

        n_clusters = best_k

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(tfidf_matrix)

    return labels, vectorizer, tfidf_matrix, n_clusters


def extract_cluster_keywords(
    vectorizer: TfidfVectorizer,
    tfidf_matrix,
    labels: list,
    cluster_id: int,
    top_n: int = 8,
) -> list:
    """Get top keywords for a specific cluster."""
    if vectorizer is None:
        return ["general"]

    mask = np.array(labels) == cluster_id
    cluster_matrix = tfidf_matrix[mask]

    if cluster_matrix.shape[0] == 0:
        return []

    mean_tfidf = cluster_matrix.mean(axis=0).A1
    feature_names = vectorizer.get_feature_names_out()
    top_indices = mean_tfidf.argsort()[-top_n:][::-1]

    return [feature_names[i] for i in top_indices if mean_tfidf[i] > 0]


def generate_theme_label(keywords: list) -> str:
    """Generate a human-readable theme label from top keywords."""
    if not keywords:
        return "General Challenges"

    # Take top 2-3 keywords and create a label
    top = keywords[:3]
    # Capitalize and join
    theme = " & ".join(word.replace("_", " ").title() for word in top)
    return theme


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_commercial_potential(responses: list) -> float:
    """Score how commercially valuable a segment is (0-100)."""
    if not responses:
        return 0

    total_signals = 0
    for resp in responses:
        matches = COMMERCIAL_SIGNALS.findall(resp)
        total_signals += len(matches)

    # Normalize: avg signals per response, scaled to 0-100
    avg_signals = total_signals / len(responses)
    score = min(100, avg_signals * 25)  # 4+ avg signals = 100
    return round(score, 1)


def recommend_format(keywords: list, responses: list) -> str:
    """Recommend the best lead magnet format based on pain cluster."""
    combined_text = " ".join(keywords) + " " + " ".join(responses[:10])
    combined_lower = combined_text.lower()

    scores = {}
    for fmt, trigger_words in FORMAT_KEYWORDS.items():
        score = sum(1 for word in trigger_words if word in combined_lower)
        scores[fmt] = score

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "guide"  # default
    return best


def score_viral_potential(title: str, fmt: str, segment_size_pct: float) -> int:
    """Score how likely a lead magnet is to be shared (0-100)."""
    score = 30  # baseline

    # Larger segments = more sharing potential
    score += min(25, segment_size_pct * 1.5)

    # Templates and checklists are more shareable
    format_boost = {
        "template": 15,
        "checklist": 12,
        "swipe_file": 18,
        "calculator": 10,
        "guide": 5,
    }
    score += format_boost.get(fmt, 0)

    # Titles with numbers or specific outcomes
    if re.search(r"\d+", title):
        score += 10
    if re.search(r"(ultimate|complete|definitive|proven|secret)", title, re.IGNORECASE):
        score += 5

    return min(100, int(score))


def score_conversion_potential(commercial_score: float, segment_size_pct: float, fmt: str) -> int:
    """Score how likely a lead magnet is to convert to leads/customers (0-100)."""
    score = 20  # baseline

    # Commercial intent is the strongest signal
    score += commercial_score * 0.4

    # Segment size matters but with diminishing returns
    score += min(15, segment_size_pct * 0.8)

    # Some formats convert better
    conversion_boost = {
        "calculator": 15,
        "template": 12,
        "checklist": 10,
        "guide": 5,
        "swipe_file": 8,
    }
    score += conversion_boost.get(fmt, 0)

    return min(100, int(score))


# ---------------------------------------------------------------------------
# Lead Magnet Brief Generator
# ---------------------------------------------------------------------------

FORMAT_LABELS = {
    "guide": "Comprehensive Guide",
    "checklist": "Actionable Checklist",
    "template": "Ready-to-Use Template",
    "calculator": "Interactive Calculator",
    "swipe_file": "Swipe File Collection",
}


def generate_title(theme: str, fmt: str, keywords: list) -> str:
    """Generate a lead magnet title."""
    templates = {
        "guide": [
            f"The Complete Guide to {theme}",
            f"How to Solve {theme}: A Step-by-Step Guide",
            f"{theme} Mastery: Everything You Need to Know",
        ],
        "checklist": [
            f"The {theme} Checklist: {min(15, 5 + len(keywords))} Steps to Success",
            f"Your {theme} Pre-Launch Checklist",
            f"{theme}: The Essential Checklist",
        ],
        "template": [
            f"{theme} Template Pack: Copy, Customize, Launch",
            f"The {theme} Template That Saves 10+ Hours/Week",
            f"Plug-and-Play {theme} Templates",
        ],
        "calculator": [
            f"{theme} Calculator: Know Your Numbers in 5 Minutes",
            f"The {theme} ROI Calculator",
            f"Calculate Your {theme} Score",
        ],
        "swipe_file": [
            f"50+ {theme} Examples That Actually Work",
            f"The {theme} Swipe File: Steal These Ideas",
            f"Best-in-Class {theme} Examples (Curated Collection)",
        ],
    }

    options = templates.get(fmt, templates["guide"])
    return options[0]


def generate_hook(theme: str, keywords: list, sample_responses: list) -> str:
    """Generate a compelling hook for the lead magnet."""
    # Extract a pain point from sample responses for the hook
    pain_phrase = ""
    if sample_responses:
        # Find the most representative short phrase
        for resp in sample_responses[:5]:
            if 20 < len(resp) < 150:
                pain_phrase = resp
                break

    if pain_phrase:
        return (
            f"If you've ever thought \"{pain_phrase[:80]}{'...' if len(pain_phrase) > 80 else ''}\" "
            f"— this is for you. We analyzed hundreds of responses and found the exact "
            f"patterns that separate those who overcome {keywords[0] if keywords else 'this challenge'} "
            f"from those who stay stuck."
        )
    else:
        return (
            f"Most teams waste months trying to figure out {theme.lower()} on their own. "
            f"This resource distills proven strategies into actionable steps you can "
            f"implement today."
        )


def generate_outline(theme: str, fmt: str, keywords: list) -> list:
    """Generate a content outline for the lead magnet."""
    sections = [f"Section 1: Why {theme} Matters Now (The Landscape)"]

    if fmt == "guide":
        sections.extend([
            f"Section 2: The Core Framework for {keywords[0].title() if keywords else 'Success'}",
            f"Section 3: Common Mistakes (And How to Avoid Them)",
            f"Section 4: Step-by-Step Implementation Plan",
            f"Section 5: Tools & Resources You'll Need",
            f"Section 6: Case Studies — What Good Looks Like",
            f"Section 7: Quick-Start Action Plan",
        ])
    elif fmt == "checklist":
        sections.extend([
            f"Section 2: Pre-Work — What to Have Ready",
            f"Section 3: Phase 1 — Foundation ({keywords[0].title() if keywords else 'Setup'})",
            f"Section 4: Phase 2 — Execution ({keywords[1].title() if len(keywords) > 1 else 'Build'})",
            f"Section 5: Phase 3 — Optimization & Measurement",
            f"Section 6: Common Gotchas to Watch For",
        ])
    elif fmt == "template":
        sections.extend([
            f"Section 2: How to Use This Template",
            f"Section 3: Template A — {keywords[0].title() if keywords else 'Standard'} Version",
            f"Section 4: Template B — Advanced Version",
            f"Section 5: Customization Guide",
            f"Section 6: Real Examples (Filled-In Templates)",
        ])
    elif fmt == "calculator":
        sections.extend([
            f"Section 2: Key Metrics You Need to Track",
            f"Section 3: Input Your Numbers",
            f"Section 4: Understanding Your Results",
            f"Section 5: Benchmarks — How You Compare",
            f"Section 6: Action Steps Based on Your Score",
        ])
    elif fmt == "swipe_file":
        sections.extend([
            f"Section 2: What Makes These Examples Work",
            f"Section 3: Category A — {keywords[0].title() if keywords else 'Top Performers'}",
            f"Section 4: Category B — {keywords[1].title() if len(keywords) > 1 else 'Rising Stars'}",
            f"Section 5: How to Adapt These for Your Business",
            f"Section 6: Blank Templates to Get Started",
        ])

    return sections


def generate_cta(fmt: str, theme: str) -> str:
    """Generate the target CTA for the lead magnet landing page."""
    ctas = {
        "guide": f"Download the Free {theme} Guide",
        "checklist": f"Get Your Free {theme} Checklist",
        "template": f"Grab the Free {theme} Templates",
        "calculator": f"Try the Free {theme} Calculator",
        "swipe_file": f"Download {theme} Swipe File",
    }
    return ctas.get(fmt, f"Get Free {theme} Resource")


def recommend_distribution(fmt: str, segment_size_pct: float) -> str:
    """Recommend primary distribution channel."""
    if segment_size_pct > 25:
        return "Homepage popup + dedicated landing page + paid social"
    elif segment_size_pct > 15:
        return "Blog content upgrade + email nurture sequence"
    elif segment_size_pct > 8:
        return "Targeted blog posts + LinkedIn organic"
    else:
        return "Niche community posts + targeted email segment"


def build_lead_magnet_brief(segment: PainSegment) -> LeadMagnetBrief:
    """Generate a complete lead magnet brief for a pain segment."""
    fmt = recommend_format(segment.top_keywords, segment.sample_responses)
    title = generate_title(segment.theme, fmt, segment.top_keywords)
    hook = generate_hook(segment.theme, segment.top_keywords, segment.sample_responses)
    outline = generate_outline(segment.theme, fmt, segment.top_keywords)
    cta = generate_cta(fmt, segment.theme)
    channel = recommend_distribution(fmt, segment.respondent_pct)

    viral = score_viral_potential(title, fmt, segment.respondent_pct)
    conversion = score_conversion_potential(
        segment.commercial_score, segment.respondent_pct, fmt,
    )
    combined = (viral * 0.4 + conversion * 0.6)

    impl_notes = (
        f"Target segment: {segment.respondent_count} respondents ({segment.respondent_pct:.1f}% of total). "
        f"Commercial intent score: {segment.commercial_score}/100. "
        f"Recommended format: {FORMAT_LABELS.get(fmt, fmt)}. "
        f"Estimated production time: {'1-2 days' if fmt in ('checklist', 'template') else '3-5 days'}."
    )

    return LeadMagnetBrief(
        segment_id=segment.segment_id,
        segment_theme=segment.theme,
        title=title,
        format=FORMAT_LABELS.get(fmt, fmt),
        hook=hook,
        outline=outline,
        target_cta=cta,
        distribution_channel=channel,
        viral_potential=viral,
        conversion_potential=conversion,
        combined_score=round(combined, 1),
        implementation_notes=impl_notes,
    )


# ---------------------------------------------------------------------------
# Analysis Pipeline
# ---------------------------------------------------------------------------

def analyze_survey(
    csv_path: str,
    pain_columns: Optional[list] = None,
    top_segments: int = 5,
) -> AnalysisResult:
    """Full analysis pipeline: load → cluster → score → generate briefs."""

    # Load data
    df = load_survey_data(csv_path)
    total_respondents = len(df)

    # Detect or use specified pain columns
    if pain_columns:
        # Validate columns exist
        missing = [c for c in pain_columns if c not in df.columns]
        if missing:
            # Try fuzzy match
            actual_cols = []
            for pc in pain_columns:
                matches = [c for c in df.columns if pc.lower() in c.lower()]
                if matches:
                    actual_cols.append(matches[0])
                else:
                    raise ValueError(f"Column not found: '{pc}'. Available: {list(df.columns)}")
            pain_columns = actual_cols
    else:
        pain_columns = detect_pain_columns(df)
        if not pain_columns:
            raise ValueError(
                "Could not auto-detect pain point columns. "
                "Use --pain-columns to specify which columns contain challenge/pain responses.\n"
                f"Available columns: {list(df.columns)}"
            )

    print(f"Analyzing columns: {pain_columns}", file=sys.stderr)

    # Extract responses
    responses = extract_responses(df, pain_columns)
    if not responses:
        raise ValueError("No non-empty responses found in the specified columns")

    print(f"Found {len(responses)} responses from {total_respondents} respondents", file=sys.stderr)

    # Cluster
    labels, vectorizer, tfidf_matrix, n_clusters = cluster_responses(
        responses, n_clusters=min(top_segments, len(responses) // 2) if len(responses) < 30 else None,
    )

    # Build segments
    segments = []
    for cluster_id in range(n_clusters):
        mask = [i for i, l in enumerate(labels) if l == cluster_id]
        cluster_responses_list = [responses[i] for i in mask]

        keywords = extract_cluster_keywords(vectorizer, tfidf_matrix, labels, cluster_id)
        theme = generate_theme_label(keywords)
        commercial = score_commercial_potential(cluster_responses_list)

        # Pick representative quotes (medium length, most representative)
        quotes = sorted(
            cluster_responses_list,
            key=lambda r: abs(len(r) - 80),  # prefer ~80 char responses
        )[:3]

        segment = PainSegment(
            segment_id=cluster_id + 1,
            theme=theme,
            top_keywords=keywords,
            respondent_count=len(mask),
            respondent_pct=round(len(mask) / len(responses) * 100, 1),
            commercial_score=commercial,
            sample_responses=cluster_responses_list[:5],
            representative_quotes=quotes,
        )
        segments.append(segment)

    # Sort by size × commercial score
    segments.sort(key=lambda s: s.respondent_count * (s.commercial_score + 10), reverse=True)

    # Limit to top N
    segments = segments[:top_segments]

    # Re-number after sorting
    for i, seg in enumerate(segments):
        seg.segment_id = i + 1

    # Generate lead magnet briefs
    lead_magnets = []
    for seg in segments:
        brief = build_lead_magnet_brief(seg)
        lead_magnets.append(brief)

    # Sort briefs by combined score
    lead_magnets.sort(key=lambda b: b.combined_score, reverse=True)

    # Implementation roadmap
    roadmap = []
    for i, lm in enumerate(lead_magnets, 1):
        roadmap.append({
            "priority": i,
            "title": lm.title,
            "format": lm.format,
            "segment_size": f"{lm.segment_theme} ({segments[lm.segment_id - 1].respondent_pct:.1f}%)",
            "combined_score": lm.combined_score,
            "estimated_effort": "1-2 days" if "Checklist" in lm.format or "Template" in lm.format else "3-5 days",
        })

    return AnalysisResult(
        total_respondents=total_respondents,
        columns_analyzed=pain_columns,
        segments=[asdict(s) for s in segments],
        lead_magnets=[asdict(lm) for lm in lead_magnets],
        implementation_roadmap=roadmap,
    )


# ---------------------------------------------------------------------------
# Output Formatters
# ---------------------------------------------------------------------------

def format_analysis_text(result: AnalysisResult) -> str:
    """Format analysis as human-readable text."""
    lines = []
    lines.append("=" * 70)
    lines.append("  SURVEY-TO-LEAD-MAGNET ANALYSIS")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  Total respondents: {result.total_respondents}")
    lines.append(f"  Columns analyzed: {', '.join(result.columns_analyzed)}")
    lines.append(f"  Segments identified: {len(result.segments)}")
    lines.append("")

    # Segments
    lines.append("-" * 70)
    lines.append("  PAIN POINT SEGMENTS (ranked by opportunity)")
    lines.append("-" * 70)

    for seg in result.segments:
        lines.append("")
        lines.append(f"  Segment #{seg['segment_id']}: {seg['theme']}")
        lines.append(f"  Respondents: {seg['respondent_count']} ({seg['respondent_pct']}%)")
        lines.append(f"  Commercial Score: {seg['commercial_score']}/100")
        lines.append(f"  Top Keywords: {', '.join(seg['top_keywords'][:5])}")
        lines.append("")
        lines.append("  Representative Quotes:")
        for q in seg["representative_quotes"]:
            lines.append(f"    \"{q[:100]}{'...' if len(q) > 100 else ''}\"")
        lines.append("")

    # Lead Magnet Briefs
    lines.append("=" * 70)
    lines.append("  LEAD MAGNET BRIEFS (ranked by combined score)")
    lines.append("=" * 70)

    for lm in result.lead_magnets:
        lines.append("")
        lines.append(f"  📦 {lm['title']}")
        lines.append(f"  Format: {lm['format']}")
        lines.append(f"  Segment: {lm['segment_theme']}")
        lines.append(f"  Viral Potential: {lm['viral_potential']}/100  |  Conversion Potential: {lm['conversion_potential']}/100")
        lines.append(f"  Combined Score: {lm['combined_score']}/100")
        lines.append("")
        lines.append(f"  Hook: {lm['hook'][:200]}{'...' if len(lm['hook']) > 200 else ''}")
        lines.append("")
        lines.append("  Outline:")
        for section in lm["outline"]:
            lines.append(f"    • {section}")
        lines.append("")
        lines.append(f"  CTA: {lm['target_cta']}")
        lines.append(f"  Distribution: {lm['distribution_channel']}")
        lines.append(f"  Notes: {lm['implementation_notes']}")
        lines.append("")
        lines.append("  " + "-" * 50)

    # Roadmap
    lines.append("")
    lines.append("=" * 70)
    lines.append("  IMPLEMENTATION ROADMAP")
    lines.append("=" * 70)
    lines.append("")

    for item in result.implementation_roadmap:
        lines.append(f"  #{item['priority']}  [{item['estimated_effort']}]  {item['title']}")
        lines.append(f"       Format: {item['format']}  |  Segment: {item['segment_size']}  |  Score: {item['combined_score']}")
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Survey-to-Lead-Magnet Engine — Turn survey data into targeted lead magnet briefs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python survey_lead_magnet.py --csv survey_responses.csv
  python survey_lead_magnet.py --csv survey.csv --pain-columns "biggest_challenge" "frustrations"
  python survey_lead_magnet.py --csv survey.csv --top-segments 3 --json --output briefs.json

CSV Format:
  Questions as column headers, one respondent per row.
  Works with exports from Typeform, Google Forms, SurveyMonkey, etc.
        """,
    )
    parser.add_argument("--csv", required=True, help="Path to survey responses CSV")
    parser.add_argument(
        "--pain-columns", nargs="+",
        help="Column names containing pain point / challenge responses (auto-detected if not specified)",
    )
    parser.add_argument(
        "--top-segments", type=int, default=5,
        help="Number of top segments to analyze (default: 5)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", help="Save output to file")

    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"Error: File not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    try:
        result = analyze_survey(
            csv_path=args.csv,
            pain_columns=args.pain_columns,
            top_segments=args.top_segments,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    if args.json:
        output = json.dumps(asdict(result), indent=2, default=str)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Output saved to {args.output}", file=sys.stderr)
        else:
            print(output)
    else:
        text_output = format_analysis_text(result)
        if args.output:
            with open(args.output, "w") as f:
                f.write(text_output)
            print(f"Output saved to {args.output}", file=sys.stderr)
        else:
            print(text_output)


if __name__ == "__main__":
    main()
