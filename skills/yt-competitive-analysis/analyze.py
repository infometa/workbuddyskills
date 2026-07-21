#!/usr/bin/env python3
"""
YouTube Competitive Analysis — Outlier Detection

Analyzes YouTube channels to find outlier videos (2x+ average views)
and extract packaging patterns from winners.

Usage:
    python3 analyze.py <API_KEY> [--channels @h1,@h2] [--set ai|business|both] [--days 30] [--output console|json]
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
import re
import os
from collections import Counter
from datetime import datetime, timezone, timedelta

AI_CHANNELS = {
    "Jeff Su": "@jeffsu",
    "Alex Finn": "@AlexFinnOfficial",
    "Riley Brown": "@RileyBrown",
    "Dan Martell": "@danmartell",
    "Matt Wolfe": "@mreflow",
    "Nate Herk": "@nateherk",
    "Grace Leung": "@graceleungyl",
    "Matt Berman": "@matthew_berman",
}

BIZ_CHANNELS = {
    "Alex Hormozi": "@AlexHormozi",
    "Gary Vaynerchuk": "@garyvee",
    "Patrick Bet-David": "@PatrickBetDavid",
    "Codie Sanchez": "@CodieSanchezCT",
    "Leila Hormozi": "@LeilaHormozi",
    "Iman Gadzhi": "@ImanGadzhi",
    "Sam Parr": "@MyFirstMillionPod",
}


def api_get(api_key, endpoint, params):
    """Make a YouTube Data API v3 request."""
    params["key"] = api_key
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def resolve_channel(api_key, handle):
    """Resolve a YouTube handle to a channel ID and metadata."""
    data = api_get(api_key, "search", {"q": handle, "type": "channel", "part": "snippet", "maxResults": 1})
    if not data.get("items"):
        return None, None
    ch_id = data["items"][0]["snippet"]["channelId"]
    stats = api_get(api_key, "channels", {"id": ch_id, "part": "statistics,snippet,contentDetails"})
    if not stats.get("items"):
        return ch_id, None
    return ch_id, stats["items"][0]


def get_recent_videos(api_key, channel_id, cutoff, max_results=100):
    """Get all videos from a channel published after the cutoff date."""
    ch_data = api_get(api_key, "channels", {"id": channel_id, "part": "contentDetails"})
    uploads_id = ch_data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    videos = []
    page_token = None
    done = False
    while not done and len(videos) < max_results:
        params = {"playlistId": uploads_id, "part": "snippet,contentDetails", "maxResults": 50}
        if page_token:
            params["pageToken"] = page_token
        data = api_get(api_key, "playlistItems", params)
        for item in data.get("items", []):
            pub = item["snippet"]["publishedAt"]
            pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if pub_dt < cutoff:
                done = True
                break
            videos.append(item["contentDetails"]["videoId"])
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    if not videos:
        return []
    all_details = []
    for i in range(0, len(videos), 50):
        batch = videos[i:i + 50]
        vdata = api_get(api_key, "videos", {"id": ",".join(batch), "part": "snippet,statistics,contentDetails"})
        all_details.extend(vdata.get("items", []))
    return [v for v in all_details if datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00")) >= cutoff]


def parse_duration(dur):
    """Parse ISO 8601 duration to seconds."""
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', dur)
    if not m:
        return 0
    h, mi, s = m.groups()
    return int(h or 0) * 3600 + int(mi or 0) * 60 + int(s or 0)


def analyze_channels(api_key, channels, days, set_name="Custom"):
    """Analyze a set of channels and find outlier videos."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    results = {"set": set_name, "channels": {}, "outliers": {"long": [], "short": []}}

    for name, handle in channels.items():
        print(f"  Analyzing {name}...", file=sys.stderr)
        try:
            ch_id, ch_info = resolve_channel(api_key, handle)
            if not ch_id or not ch_info:
                continue
            subs = int(ch_info["statistics"].get("subscriberCount", 0))
            videos = get_recent_videos(api_key, ch_id, cutoff, 100)

            longs, shorts = [], []
            for v in videos:
                dur_sec = parse_duration(v["contentDetails"]["duration"])
                views = int(v["statistics"].get("viewCount", 0))
                entry = {
                    "channel": name, "handle": handle, "subs": subs,
                    "title": v["snippet"]["title"],
                    "format": "Short" if dur_sec <= 60 else "Long",
                    "views": views,
                    "likes": int(v["statistics"].get("likeCount", 0)),
                    "comments": int(v["statistics"].get("commentCount", 0)),
                    "duration_min": round(dur_sec / 60, 1),
                    "published": v["snippet"]["publishedAt"][:10],
                    "url": f"https://youtube.com/watch?v={v['id']}",
                }
                (shorts if entry["format"] == "Short" else longs).append(entry)

            long_avg = sum(v["views"] for v in longs) / len(longs) if longs else 0
            short_avg = sum(v["views"] for v in shorts) / len(shorts) if shorts else 0

            for v in longs:
                v["avg"] = round(long_avg)
                v["multiplier"] = round(v["views"] / long_avg, 1) if long_avg > 0 else 0
                if v["views"] > long_avg * 2:
                    results["outliers"]["long"].append(v)
            for v in shorts:
                v["avg"] = round(short_avg)
                v["multiplier"] = round(v["views"] / short_avg, 1) if short_avg > 0 else 0
                if v["views"] > short_avg * 2:
                    results["outliers"]["short"].append(v)

            results["channels"][name] = {
                "handle": handle, "subs": subs,
                "total_30d": len(longs) + len(shorts),
                "longs": len(longs), "shorts": len(shorts),
                "long_avg": round(long_avg), "short_avg": round(short_avg),
                "per_week": round((len(longs) + len(shorts)) / (days / 7), 1),
            }
        except Exception as e:
            print(f"    Error: {e}", file=sys.stderr)

    results["outliers"]["long"].sort(key=lambda x: -x["multiplier"])
    results["outliers"]["short"].sort(key=lambda x: -x["multiplier"])

    return results


def print_console(results, days):
    """Print results in a human-readable console format."""
    print(f"\n{'=' * 80}")
    print(f"  {results['set']} — LAST {days} DAYS")
    print(f"{'=' * 80}")

    print("\n📊 CHANNEL SUMMARY:")
    for name, data in sorted(results["channels"].items(), key=lambda x: -x[1]["subs"]):
        print(f"  {name:25s} | {data['subs']:>10,} subs | {data['total_30d']:>3} videos ({data['per_week']}/wk) | L:{data['longs']:>3} S:{data['shorts']:>3}")

    print(f"\n🔥 LONG-FORM OUTLIERS (top 15):")
    for v in results["outliers"]["long"][:15]:
        print(f"  {v['multiplier']:.1f}x | {v['views']:>10,} | [{v['channel']}] {v['title'][:55]}")
        print(f"       {v['published']} | {v['url']}")

    print(f"\n⚡ SHORT-FORM OUTLIERS (top 15):")
    for v in results["outliers"]["short"][:15]:
        print(f"  {v['multiplier']:.1f}x | {v['views']:>10,} | [{v['channel']}] {v['title'][:55]}")
        print(f"       {v['published']} | {v['url']}")

    # Title pattern extraction
    all_titles = [v["title"] for v in results["outliers"]["long"] + results["outliers"]["short"]]
    words = []
    for t in all_titles:
        words.extend(re.findall(r'\b\w+\b', t.lower()))
    stopwords = {
        'the', 'a', 'an', 'i', 'you', 'my', 'your', 'this', 'that', 'it', 'is', 'are',
        'was', 'were', 'to', 'in', 'for', 'on', 'of', 'and', 'or', 'how', 'with', 'do',
        'not', 'dont', 'can', 'will', 'just', 'all', 'but', 'be', 'have', 'has', 'from',
        'at', 'by', 'if', 'so', 'no', 'what', 'when', 'why', 'who', 'which', 'their',
        'they', 'them', 'me', 'we', 'us', 'its', 'been', 'had', 'did', 'get', 'got',
        'than', 'into', 'these', 'those', 'very', 'more', 'most', 'about', 'up', 'out',
        'one', 'also', 'even', 'after', 'before', 'here', 'there', 'then', 'new', 'now',
        'way', 'may', 'like', 'over', 'only', 'any', 'such', 'make', 'each', 're', 've',
        'll', 'don', 't', 's', 'm', 'd'
    }
    filtered = [w for w in words if w not in stopwords and len(w) > 2]
    word_freq = Counter(filtered).most_common(15)

    print(f"\n📦 TOP TITLE PATTERNS:")
    for word, count in word_freq:
        print(f"  {count:>3}x  {word}")


def main():
    parser = argparse.ArgumentParser(description="YouTube Competitive Analysis — Outlier Detection")
    parser.add_argument("api_key", nargs="?", default=os.environ.get("YOUTUBE_API_KEY"),
                        help="YouTube Data API key (or set $YOUTUBE_API_KEY)")
    parser.add_argument("--channels", help="Comma-separated YouTube handles (e.g., @AlexHormozi,@garyvee)")
    parser.add_argument("--set", choices=["ai", "business", "both"], help="Predefined channel set")
    parser.add_argument("--days", type=int, default=30, help="Lookback period in days (default: 30)")
    parser.add_argument("--output", choices=["console", "json"], default="console",
                        help="Output format (default: console)")
    args = parser.parse_args()

    if not args.api_key:
        print("Error: Provide API key as argument or set $YOUTUBE_API_KEY", file=sys.stderr)
        sys.exit(1)

    # Build channel list
    channel_sets = {}
    if args.set in ["ai", "both"]:
        channel_sets["AI Creators"] = AI_CHANNELS
    if args.set in ["business", "both"]:
        channel_sets["Business Creators"] = BIZ_CHANNELS
    if args.channels:
        custom = {}
        for h in args.channels.split(","):
            h = h.strip()
            name = h.replace("@", "").title()
            custom[name] = h
        channel_sets["Custom"] = custom

    if not channel_sets:
        print("Error: Specify --channels or --set", file=sys.stderr)
        sys.exit(1)

    all_results = []
    for set_name, channels in channel_sets.items():
        print(f"\nAnalyzing {set_name}...", file=sys.stderr)
        results = analyze_channels(args.api_key, channels, args.days, set_name)
        all_results.append(results)

    if args.output == "json":
        print(json.dumps(all_results, indent=2))
    else:
        for results in all_results:
            print_console(results, args.days)


if __name__ == "__main__":
    main()
