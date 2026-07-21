#!/usr/bin/env python3
"""
Trend Scout — Multi-source trend detection for content marketing.

Scans Google Trends, Hacker News, Reddit, and X/Twitter to find trending
topics in your niche before they peak. Scores each trend for relevance
to your configured content verticals and suggests content angles.

Usage:
    python trend_scout.py

Environment variables:
    CONTENT_VERTICALS  — Comma-separated topic verticals (default: marketing-focused set)
    TREND_SUBREDDITS   — Comma-separated subreddits to monitor
    BRAVE_API_KEY      — Brave Search API key (enables X/Twitter scanning)
    OUTPUT_DIR         — Where to save output files (default: ./output)
"""

import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Content verticals — what topics are relevant to you?
# Override with CONTENT_VERTICALS env var (comma-separated)
DEFAULT_VERTICALS = [
    "AI marketing automation",
    "AI agents for business",
    "SEO trends",
    "content marketing AI",
    "marketing agency transformation",
    "programmatic SEO",
    "AI search optimization AEO",
    "startup growth strategy",
]

_verticals_env = os.environ.get("CONTENT_VERTICALS", "")
VERTICALS = [v.strip() for v in _verticals_env.split(",") if v.strip()] if _verticals_env else DEFAULT_VERTICALS

# Subreddits to monitor
DEFAULT_SUBREDDITS = ["marketing", "SEO", "startups", "entrepreneur", "artificial", "digitalmarketing"]
_subs_env = os.environ.get("TREND_SUBREDDITS", "")
SUBREDDITS = [s.strip() for s in _subs_env.split(",") if s.strip()] if _subs_env else DEFAULT_SUBREDDITS

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")

# ─────────────────────────────────────────────
# Relevance scoring keywords
# Customize these for your niche
# ─────────────────────────────────────────────
HIGH_RELEVANCE_KEYWORDS = [
    "ai marketing", "seo", "ai agent", "marketing agency", "content marketing",
    "programmatic seo", "founder", "startup growth", "saas", "ai search",
    "ai automation", "marketing automation", "creator economy",
    "digital marketing agency", "ai seo",
]

MEDIUM_RELEVANCE_KEYWORDS = [
    "ai", "marketing", "google", "search", "business", "revenue",
    "growth", "startup", "entrepreneur", "automation", "llm", "gpt",
    "chatgpt", "social media", "advertising", "content",
    "digital marketing",
]

LOW_RELEVANCE_KEYWORDS = [
    "tech", "digital", "platform", "data", "analytics", "strategy",
]

# Override with env vars (JSON arrays)
_high_env = os.environ.get("HIGH_RELEVANCE_KEYWORDS_JSON")
if _high_env:
    try:
        HIGH_RELEVANCE_KEYWORDS = json.loads(_high_env)
    except json.JSONDecodeError:
        pass


# ─────────────────────────────────────────────
# Data Sources
# ─────────────────────────────────────────────

def get_google_trends():
    """Pull trending searches from Google Trends RSS."""
    url = "https://trends.google.com/trending/rss?geo=US"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read().decode("utf-8")

        root = ET.fromstring(data)
        ns = {"ht": "https://trends.google.com/trending/rss"}
        trends = []
        for item in root.findall(".//item")[:20]:
            title = item.find("title")
            traffic = item.find("ht:approx_traffic", ns)
            news_items = item.findall("ht:news_item", ns)

            news_titles = []
            news_urls = []
            for ni in news_items[:2]:
                nt = ni.find("ht:news_item_title", ns)
                nu = ni.find("ht:news_item_url", ns)
                if nt is not None:
                    news_titles.append(nt.text)
                if nu is not None:
                    news_urls.append(nu.text)

            trends.append({
                "topic": title.text if title is not None else "Unknown",
                "traffic": traffic.text if traffic is not None else "N/A",
                "news_titles": news_titles,
                "news_urls": news_urls,
            })
        return trends
    except Exception as e:
        print(f"⚠️ Google Trends fetch failed: {e}")
        return []


def get_hackernews_top():
    """Pull top HN stories filtered for relevance."""
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            ids = json.loads(response.read().decode("utf-8"))[:30]

        stories = []
        # Use all relevance keywords for filtering
        keywords = set()
        for kw in HIGH_RELEVANCE_KEYWORDS + MEDIUM_RELEVANCE_KEYWORDS:
            keywords.update(kw.lower().split())

        for story_id in ids:
            try:
                surl = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                sreq = urllib.request.Request(surl, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(sreq, timeout=5) as sr:
                    story = json.loads(sr.read().decode("utf-8"))

                title = story.get("title", "").lower()
                if any(kw in title for kw in keywords):
                    stories.append({
                        "title": story.get("title"),
                        "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                        "score": story.get("score", 0),
                        "comments": story.get("descendants", 0),
                    })
            except:
                continue

            if len(stories) >= 10:
                break

        return stories
    except Exception as e:
        print(f"⚠️ HN fetch failed: {e}")
        return []


def get_reddit_trending():
    """Pull trending posts from configured subreddits."""
    posts = []

    for sub in SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
            req = urllib.request.Request(url, headers={"User-Agent": "TrendScout/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                if post.get("score", 0) > 50:
                    posts.append({
                        "title": post.get("title"),
                        "subreddit": sub,
                        "score": post.get("score"),
                        "comments": post.get("num_comments"),
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                    })
        except Exception as e:
            print(f"⚠️ Reddit r/{sub} failed: {e}")
            continue

    posts.sort(key=lambda x: x.get("score", 0), reverse=True)
    return posts[:10]


def get_x_twitter_trending():
    """Pull trending X/Twitter discussions via Brave Search."""
    if not BRAVE_API_KEY:
        print("  ⚠️ No BRAVE_API_KEY — skipping X/Twitter scan")
        return []

    # Build search queries from your verticals
    queries = []
    for vertical in VERTICALS[:4]:
        queries.append(f'site:twitter.com OR site:x.com "{vertical}"')

    posts = []
    for query in queries:
        try:
            encoded_q = urllib.request.quote(query)
            url = f"https://api.search.brave.com/res/v1/web/search?q={encoded_q}&count=5&freshness=pd"
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": BRAVE_API_KEY,
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            for result in data.get("web", {}).get("results", []):
                if "twitter.com" in result.get("url", "") or "x.com" in result.get("url", ""):
                    posts.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "description": result.get("description", "")[:200],
                        "source": "X/Twitter",
                        "query": query.replace("site:twitter.com OR site:x.com ", ""),
                    })
        except Exception as e:
            print(f"  ⚠️ X search failed: {e}")
            continue

    return posts[:10]


# ─────────────────────────────────────────────
# Scoring & Analysis
# ─────────────────────────────────────────────

def score_trend(trend_title):
    """Score how relevant a trend is to your content verticals (0-100)."""
    title_lower = trend_title.lower()
    score = 0

    for kw in HIGH_RELEVANCE_KEYWORDS:
        if kw in title_lower:
            score += 25
    for kw in MEDIUM_RELEVANCE_KEYWORDS:
        if kw in title_lower:
            score += 10
    for kw in LOW_RELEVANCE_KEYWORDS:
        if kw in title_lower:
            score += 5

    return min(score, 100)


def generate_content_angles(trends_data):
    """Generate content angle suggestions based on trends."""
    angles = []

    for trend in trends_data.get("google_trends", [])[:5]:
        relevance = score_trend(trend["topic"])
        if relevance >= 20:
            angles.append({
                "source": "Google Trends",
                "topic": trend["topic"],
                "traffic": trend["traffic"],
                "relevance_score": relevance,
                "angle_suggestion": f"Your take on '{trend['topic']}' — tie to your niche angle",
                "platforms": ["X", "LinkedIn", "Short-form video"],
            })

    for story in trends_data.get("hackernews", [])[:5]:
        relevance = score_trend(story["title"])
        if relevance >= 15:
            angles.append({
                "source": "Hacker News",
                "topic": story["title"],
                "score": story["score"],
                "relevance_score": relevance,
                "url": story["url"],
                "angle_suggestion": f"Expert perspective on '{story['title']}'",
                "platforms": ["X", "YouTube", "LinkedIn"],
            })

    for post in trends_data.get("reddit", [])[:5]:
        relevance = score_trend(post["title"])
        if relevance >= 15:
            angles.append({
                "source": f"Reddit r/{post['subreddit']}",
                "topic": post["title"],
                "engagement": f"{post['score']} upvotes, {post['comments']} comments",
                "relevance_score": relevance,
                "url": post["url"],
                "angle_suggestion": f"Address this conversation from your expertise",
                "platforms": ["X", "LinkedIn", "Short-form video"],
            })

    for post in trends_data.get("x_twitter", [])[:5]:
        relevance = score_trend(post["title"])
        if relevance >= 15:
            angles.append({
                "source": "X/Twitter",
                "topic": post["title"][:100],
                "relevance_score": relevance,
                "url": post.get("url", ""),
                "angle_suggestion": f"Jump into this conversation with your take",
                "platforms": ["X", "LinkedIn"],
            })

    angles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    return angles[:10]


def format_output(trends_data, angles):
    """Format for human-readable markdown output."""
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [f"# 🔥 Trend Scout — {today}\n"]

    if angles:
        lines.append("## Top Content Opportunities\n")
        for i, angle in enumerate(angles, 1):
            lines.append(f"### {i}. {angle['topic']}")
            lines.append(f"**Source:** {angle['source']} | **Relevance:** {angle['relevance_score']}/100")
            if angle.get("traffic"):
                lines.append(f"**Search volume:** {angle['traffic']}")
            if angle.get("engagement"):
                lines.append(f"**Engagement:** {angle['engagement']}")
            lines.append(f"**Angle:** {angle['angle_suggestion']}")
            lines.append(f"**Best for:** {', '.join(angle['platforms'])}")
            if angle.get("url"):
                lines.append(f"**Ref:** {angle['url']}")
            lines.append("")

    lines.append("## 📊 Raw Signals\n")

    gt = trends_data.get("google_trends", [])
    if gt:
        lines.append("**Google Trends (US):**")
        for t in gt[:8]:
            lines.append(f"- {t['topic']} ({t['traffic']})")
        lines.append("")

    hn = trends_data.get("hackernews", [])
    if hn:
        lines.append("**Hacker News (filtered):**")
        for s in hn[:5]:
            lines.append(f"- [{s['title']}]({s['url']}) — {s['score']}pts, {s['comments']} comments")
        lines.append("")

    rd = trends_data.get("reddit", [])
    if rd:
        lines.append("**Reddit Hot Posts:**")
        for p in rd[:5]:
            lines.append(f"- r/{p['subreddit']}: {p['title']} ({p['score']}↑)")
        lines.append("")

    xt = trends_data.get("x_twitter", [])
    if xt:
        lines.append("**X/Twitter Trending:**")
        for p in xt[:5]:
            lines.append(f"- [{p.get('query','')}] {p['title'][:80]}")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print("🔥 Trend Scout starting...")
    print(f"   Verticals: {', '.join(VERTICALS[:5])}{'...' if len(VERTICALS) > 5 else ''}")
    print(f"   Subreddits: {', '.join(SUBREDDITS)}")
    print()

    # Gather signals
    print("  📡 Fetching Google Trends...")
    google_trends = get_google_trends()

    print("  📡 Fetching Hacker News...")
    hackernews = get_hackernews_top()

    print("  📡 Fetching Reddit...")
    reddit = get_reddit_trending()

    print("  📡 Fetching X/Twitter...")
    x_twitter = get_x_twitter_trending()

    trends_data = {
        "timestamp": datetime.now().isoformat(),
        "verticals": VERTICALS,
        "google_trends": google_trends,
        "hackernews": hackernews,
        "reddit": reddit,
        "x_twitter": x_twitter,
    }

    # Generate content angles
    print("  🧠 Generating content angles...")
    angles = generate_content_angles(trends_data)

    # Save raw data (JSON)
    json_path = OUTPUT_DIR / "flash-trends-latest.json"
    with open(json_path, "w") as f:
        json.dump({"trends": trends_data, "angles": angles}, f, indent=2)
    print(f"  💾 Saved to {json_path}")

    # Save formatted output (Markdown)
    today = datetime.now().strftime("%Y-%m-%d")
    md_path = OUTPUT_DIR / f"flash-trends-{today}.md"
    formatted = format_output(trends_data, angles)
    with open(md_path, "w") as f:
        f.write(formatted)
    print(f"  📝 Saved to {md_path}")

    # Print summary
    print(f"\n✅ Trend Scout complete:")
    print(f"  - Google Trends: {len(google_trends)} trends")
    print(f"  - Hacker News: {len(hackernews)} relevant stories")
    print(f"  - Reddit: {len(reddit)} hot posts")
    print(f"  - X/Twitter: {len(x_twitter)} discussions")
    print(f"  - Content angles: {len(angles)} opportunities")

    if angles:
        print(f"\n🎯 Top 3 angles:")
        for i, a in enumerate(angles[:3], 1):
            print(f"  {i}. [{a['relevance_score']}/100] {a['topic']} ({a['source']})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
