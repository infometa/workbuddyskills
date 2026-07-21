#!/usr/bin/env python3
"""
Quote Mining Engine — Extract viral-worthy quotes from podcasts and notes.

Scans RSS feeds and local markdown/text files to extract the most quotable,
contrarian, and viral-worthy moments. Outputs scored candidates ready to publish.

Usage:
    python quote-mining-engine.py --days 90 --top 50 --min-score 60
    python quote-mining-engine.py --feeds feeds.json --notes-dir ./notes/
"""

import argparse
import json
import os
import re
import sys
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from html import unescape

import feedparser

# ── Configuration ──

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = Path(os.environ.get("CONTENT_OPS_DATA_DIR", PROJECT_DIR / "data"))
OUTPUT_PATH = DATA_DIR / "quote-mining-latest.json"

# Configure feeds via environment variable or JSON file
# Format: {"Feed Name": "https://feed-url.com/rss", ...}
FEEDS_FILE = os.environ.get("QUOTE_MINING_FEEDS_FILE", str(PROJECT_DIR / "config" / "feeds.json"))

# Directory containing meeting notes / transcripts (markdown files)
NOTES_DIR = os.environ.get("QUOTE_MINING_NOTES_DIR", "")

# Speaker name to look for in meeting notes (configurable)
SPEAKER_NAME = os.environ.get("QUOTE_MINING_SPEAKER", "")

# ── Viral scoring heuristics ──

CONTRARIAN_SIGNALS = [
    r"\b(?:wrong|myth|lie|dead|overrated|underrated|nobody|everyone)\b",
    r"\b(?:stop|quit|don\'t|never|avoid|mistake|fail)\b",
    r"\b(?:secret|hidden|overlooked|surprising|counterintuitive)\b",
    r"\b(?:actually|truth|reality|real reason)\b",
    r"\b(?:unpopular opinion|hot take|controversial)\b",
]

SPECIFICITY_SIGNALS = [
    r"\$[\d,.]+[MBKmk]?",
    r"\b\d{1,3}%\b",
    r"\b\d+x\b",
    r"\b(?:doubled|tripled|10x|100x)\b",
    r"\b\d{4,}\b",
    r"\b(?:case study|example|data|study|research)\b",
]

EMOTIONAL_TRIGGERS = [
    r"\b(?:fear|afraid|scared|worried|anxious)\b",
    r"\b(?:love|hate|obsessed|passionate)\b",
    r"\b(?:shocking|insane|crazy|wild|unbelievable|mindblowing)\b",
    r"\b(?:broke|rich|wealthy|millionaire|billionaire)\b",
    r"\b(?:fired|hired|quit|resigned)\b",
    r"\b(?:AI|artificial intelligence|ChatGPT|GPT|automation)\b",
]

SHAREABILITY_SIGNALS = [
    r"\b(?:how to|step.by.step|framework|playbook|strategy)\b",
    r"\b(?:lesson|learned|mistake|regret)\b",
    r"\b(?:why (?:most|nobody|everyone))\b",
    r"\b(?:the (?:one|only|best|worst|biggest))\b",
    r"\bhack\b",
]


def score_text(text: str) -> dict:
    """Score a text blob for viral potential. Returns breakdown + total."""
    t = text.lower()

    def count_matches(patterns):
        return sum(1 for p in patterns if re.search(p, t, re.I))

    contrarian = min(count_matches(CONTRARIAN_SIGNALS) * 15, 35)
    specificity = min(count_matches(SPECIFICITY_SIGNALS) * 12, 30)
    emotional = min(count_matches(EMOTIONAL_TRIGGERS) * 12, 25)
    shareability = min(count_matches(SHAREABILITY_SIGNALS) * 12, 25)

    words = len(text.split())
    if words <= 15:
        length_bonus = 10
    elif words <= 30:
        length_bonus = 5
    else:
        length_bonus = 0

    question_bonus = 8 if re.search(r"\?", text) else 0
    number_bonus = 8 if re.search(r"\b\d+\b", text) else 0
    howto_bonus = 8 if re.search(r"^(?:how|why|what|when|the\s+\d)", text, re.I) else 0

    total = min(contrarian + specificity + emotional + shareability + length_bonus + question_bonus + number_bonus + howto_bonus, 100)
    return {
        "contrarian": contrarian,
        "specificity": specificity,
        "emotional": emotional,
        "shareability": shareability,
        "total": total,
    }


def suggest_platform(score_breakdown: dict, text: str) -> str:
    """Suggest X, LinkedIn, or both based on content characteristics."""
    if score_breakdown["specificity"] >= 15 and score_breakdown["shareability"] >= 10:
        return "both"
    if score_breakdown["emotional"] >= 15 or len(text.split()) <= 20:
        return "X"
    if score_breakdown["specificity"] >= 10 or score_breakdown["shareability"] >= 10:
        return "LinkedIn"
    if score_breakdown["total"] >= 60:
        return "both"
    return "X"


def generate_hook(quote: str) -> str:
    """Generate a punchy X-ready opening line from a quote."""
    q = quote.strip().rstrip(".")
    words = q.split()
    if len(words) <= 20:
        return q + "."
    short = " ".join(words[:15])
    for sep in [". ", ", ", " — ", " - ", ": "]:
        idx = short.rfind(sep)
        if idx > 20:
            return short[: idx + len(sep)].strip().rstrip(",") + "..."
    return short + "..."


def strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def make_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:10]


def load_feeds() -> dict:
    """Load RSS feed configuration."""
    feeds_path = Path(FEEDS_FILE)
    if feeds_path.exists():
        try:
            with open(feeds_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"  ⚠ Error loading feeds config: {e}")

    # Check environment variable for inline JSON
    feeds_env = os.environ.get("QUOTE_MINING_FEEDS", "")
    if feeds_env:
        try:
            return json.loads(feeds_env)
        except Exception:
            pass

    print("  ⚠ No feeds configured. Set QUOTE_MINING_FEEDS_FILE or QUOTE_MINING_FEEDS env var.")
    print("  Example feeds.json: {\"My Podcast\": \"https://feeds.example.com/rss\"}")
    return {}


# ── RSS Feed Processing ──

def fetch_feed_quotes(feed_name: str, feed_url: str, since: datetime) -> list:
    """Parse an RSS feed and extract quotable candidates."""
    print(f"  Fetching {feed_name}...")
    feed = feedparser.parse(feed_url)
    candidates = []

    for entry in feed.entries:
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if not pub:
            continue
        pub_dt = datetime(*pub[:6], tzinfo=timezone.utc)
        if pub_dt < since:
            continue

        title = entry.get("title", "").strip()
        desc = strip_html(entry.get("description", "") or entry.get("summary", ""))
        date_str = pub_dt.strftime("%Y-%m-%d")

        if title:
            scores = score_text(title + " " + desc[:200])
            context_sentence = desc[:200].split(".")[0].strip() + "." if desc else title

            candidates.append({
                "id": make_id(title + date_str),
                "quote_text": title,
                "source": f"{feed_name} — {title} ({date_str})",
                "viral_score": scores["total"],
                "score_breakdown": scores,
                "suggested_platform": suggest_platform(scores, title),
                "hook_version": generate_hook(title),
                "context": context_sentence,
                "type": "podcast_title",
            })

        if desc and len(desc) > 50:
            sentences = re.split(r"(?<=[.!?])\s+", desc)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) < 30 or len(sent) > 300:
                    continue
                if any(skip in sent.lower() for skip in [
                    "subscribe", "leave a review", "click here", "sign up",
                    "sponsor", "brought to you", "check out", "visit us",
                    "follow us", "download", "episode is", "links mentioned",
                    "get a free", "use code", "http", "www.", ".com/",
                ]):
                    continue
                s = score_text(sent)
                if s["total"] >= 30:
                    candidates.append({
                        "id": make_id(sent + date_str),
                        "quote_text": sent,
                        "source": f"{feed_name} — {title} ({date_str})",
                        "viral_score": s["total"],
                        "score_breakdown": s,
                        "suggested_platform": suggest_platform(s, sent),
                        "hook_version": generate_hook(sent),
                        "context": f"From episode: {title}",
                        "type": "podcast_description",
                    })

    print(f"    → {len(candidates)} candidates from {feed_name}")
    return candidates


# ── Notes Processing ──

def scan_notes(notes_dir: str, since: datetime, speaker: str = "") -> list:
    """Scan meeting notes/transcripts for quotable moments."""
    notes_path = Path(notes_dir)
    if not notes_path.exists():
        print(f"    ⚠ Notes directory not found: {notes_dir}, skipping.")
        return []

    print(f"  Scanning notes in {notes_dir}...")
    candidates = []

    for fpath in sorted(notes_path.glob("**/*.md")):
        m = re.match(r"(\d{4}-\d{2}-\d{2})", fpath.name)
        if m:
            file_date = datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if file_date < since:
                continue
        else:
            # If no date in filename, include by default
            file_date = datetime.now(timezone.utc)

        try:
            text = fpath.read_text(errors="replace")
        except Exception:
            continue

        meeting_name = fpath.stem.replace("_", " ").lstrip("0123456789- ")

        notable_lines = []
        for line in text.split("\n"):
            line = line.strip()
            if not line or len(line) < 30:
                continue

            # Match lines attributed to configured speaker
            if speaker and re.match(rf"(?:{re.escape(speaker)})\s*:", line, re.I):
                content = re.sub(rf"^(?:{re.escape(speaker)})\s*:\s*", "", line, flags=re.I)
                notable_lines.append(content.strip())
            # Grab bullet points with viral signals
            elif re.match(r"[\*\-]\s+", line):
                bullet = re.sub(r"^[\*\-]\s+", "", line).strip()
                if len(bullet) > 30 and any(
                    re.search(p, bullet, re.I)
                    for p in CONTRARIAN_SIGNALS + SPECIFICITY_SIGNALS + EMOTIONAL_TRIGGERS
                ):
                    notable_lines.append(bullet)

        for line in notable_lines:
            if len(line) < 20 or len(line) > 500:
                continue
            if any(skip in line.lower() for skip in [
                "let me share my screen", "can you hear me", "hold on",
                "one second", "sorry about that", "let me pull up",
                "next slide", "any questions", "sounds good",
            ]):
                continue

            s = score_text(line)
            if s["total"] >= 25:
                date_str = file_date.strftime("%Y-%m-%d")
                candidates.append({
                    "id": make_id(line + date_str),
                    "quote_text": line,
                    "source": f"Notes — {meeting_name} ({date_str})",
                    "viral_score": s["total"],
                    "score_breakdown": s,
                    "suggested_platform": suggest_platform(s, line),
                    "hook_version": generate_hook(line),
                    "context": f"From: {meeting_name}",
                    "type": "meeting_notes",
                })

    print(f"    → {len(candidates)} candidates from notes")
    return candidates


# ── Main ──

def main():
    parser = argparse.ArgumentParser(description="Quote Mining Engine")
    parser.add_argument("--days", type=int, default=90, help="Look back N days (default: 90)")
    parser.add_argument("--top", type=int, default=50, help="Return top N quotes (default: 50)")
    parser.add_argument("--min-score", type=int, default=40, help="Minimum viral score (default: 40)")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH), help="Output JSON path")
    parser.add_argument("--feeds", type=str, help="Path to feeds JSON config file")
    parser.add_argument("--notes-dir", type=str, help="Directory of meeting notes to scan")
    parser.add_argument("--speaker", type=str, help="Speaker name to extract from notes")
    args = parser.parse_args()

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    print(f"🔍 Quote Mining Engine — scanning last {args.days} days (since {since.strftime('%Y-%m-%d')})\n")

    all_candidates = []

    # 1. Podcast RSS feeds
    feeds_file = args.feeds or FEEDS_FILE
    if args.feeds:
        os.environ["QUOTE_MINING_FEEDS_FILE"] = args.feeds

    feeds = load_feeds() if not args.feeds else json.load(open(args.feeds))
    if feeds:
        print("📡 Fetching podcast feeds...")
        for name, url in feeds.items():
            try:
                all_candidates.extend(fetch_feed_quotes(name, url, since))
            except Exception as e:
                print(f"    ⚠ Error fetching {name}: {e}")

    # 2. Meeting notes
    notes_dir = args.notes_dir or NOTES_DIR
    speaker = args.speaker or SPEAKER_NAME
    if notes_dir:
        print("\n📝 Scanning meeting notes...")
        try:
            all_candidates.extend(scan_notes(notes_dir, since, speaker))
        except Exception as e:
            print(f"    ⚠ Error scanning notes: {e}")

    # 3. Deduplicate
    seen = set()
    unique = []
    for c in all_candidates:
        if c["id"] not in seen:
            seen.add(c["id"])
            unique.append(c)
    all_candidates = unique

    # 4. Filter by min score
    filtered = [c for c in all_candidates if c["viral_score"] >= args.min_score]

    # 5. Sort and take top N
    filtered.sort(key=lambda x: x["viral_score"], reverse=True)
    top = filtered[: args.top]

    # 6. Clean output
    output = []
    for c in top:
        output.append({
            "quote_text": c["quote_text"],
            "source": c["source"],
            "viral_score": c["viral_score"],
            "suggested_platform": c["suggested_platform"],
            "hook_version": c["hook_version"],
            "context": c["context"],
        })

    # 7. Save
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    # 8. Summary
    print(f"\n{'='*60}")
    print(f"📊 QUOTE MINING SUMMARY")
    print(f"{'='*60}")
    print(f"  Total candidates found:  {len(all_candidates)}")
    print(f"  Above min score ({args.min_score}):    {len(filtered)}")
    print(f"  Top quotes saved:        {len(output)}")
    print(f"  Output: {args.output}")
    print()

    if output:
        print(f"🏆 Top 10 Quotes:")
        print(f"{'-'*60}")
        for i, q in enumerate(output[:10], 1):
            print(f"  {i:2d}. [{q['viral_score']:3d}] {q['quote_text'][:80]}")
            print(f"      → {q['source'][:60]}")
            print(f"      Platform: {q['suggested_platform']} | Hook: {q['hook_version'][:50]}...")
            print()
    else:
        print("  ⚠ No quotes met the minimum score threshold.")
        print(f"    Try lowering --min-score (currently {args.min_score})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
