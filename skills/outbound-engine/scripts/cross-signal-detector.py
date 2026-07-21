#!/usr/bin/env python3
"""
Cross-Signal Detector — finds overlapping signals across multiple data sources.

When your SEO data and sales data both flag the same company, that's a cross-signal
worth acting on. This script scans agent outputs and data files for company names,
industry verticals, and keyword clusters, then finds overlaps.

Usage:
    python3 cross-signal-detector.py
    python3 cross-signal-detector.py --data-dir ./data/agent-outputs
    python3 cross-signal-detector.py --hours 48
    python3 cross-signal-detector.py --output cross-signals.json

Environment variables:
    DATA_DIR — directory containing agent output files to scan
    OUTPUT_FILE — where to write the signal detection results
"""

import argparse
import json
import os
import re
import glob
from datetime import datetime, timedelta, timezone
from collections import defaultdict


# Words to exclude from company name extraction (common English words that look like names)
STOP_WORDS = {
    'The', 'This', 'That', 'What', 'How', 'Why', 'When', 'Where',
    'For', 'From', 'With', 'About', 'Into', 'Over', 'After',
    'Before', 'Between', 'Under', 'During', 'Through',
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
    'Saturday', 'Sunday', 'January', 'February', 'March',
    'April', 'May', 'June', 'July', 'August', 'September',
    'October', 'November', 'December',
    'None', 'True', 'False', 'Error', 'Warning',
}

# Configurable: add your own team names / internal terms to exclude
CUSTOM_STOP_WORDS = set(os.environ.get('SIGNAL_STOP_WORDS', '').split(',')) if os.environ.get('SIGNAL_STOP_WORDS') else set()


def get_recent_files(directory, hours=24):
    """Get files modified in the last N hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = []
    if not os.path.isdir(directory):
        return recent
    for f in glob.glob(os.path.join(directory, "*")):
        if os.path.isfile(f):
            mtime = datetime.fromtimestamp(os.path.getmtime(f), tz=timezone.utc)
            if mtime > cutoff:
                recent.append(f)
    return recent


def extract_companies(text):
    """Extract company names (capitalized words, common patterns)."""
    companies = set()
    all_stop = STOP_WORDS | CUSTOM_STOP_WORDS
    for match in re.findall(
        r'\b([A-Z][a-zA-Z]+(?:\.[a-zA-Z]+)?(?:\s+(?:AI|Inc|Corp|Labs|Tech|io))?)\b',
        text
    ):
        if len(match) > 2 and match not in all_stop:
            companies.add(match)
    return companies


def extract_keywords(text):
    """Extract keyword themes from marketing/business text."""
    keywords = set()
    patterns = [
        r'(?:ai|artificial intelligence)\s+(?:marketing|agent|tool|saas|automation)',
        r'(?:seo|content|digital)\s+(?:marketing|strategy|optimization|growth)',
        r'(?:b2b|saas|enterprise)\s+(?:marketing|growth|sales)',
        r'(?:social media|linkedin|twitter|youtube)\s+(?:marketing|growth|strategy)',
        r'(?:email|outbound|cold)\s+(?:marketing|outreach|campaign)',
        r'(?:paid|ppc|google)\s+(?:ads|advertising|media)',
    ]
    text_lower = text.lower()
    for p in patterns:
        match = re.search(p, text_lower)
        if match:
            keywords.add(match.group())
    return keywords


def extract_verticals(text):
    """Extract industry verticals."""
    verticals = set()
    vertical_keywords = {
        'fintech': ['fintech', 'financial', 'banking', 'payments'],
        'healthtech': ['healthtech', 'health tech', 'healthcare', 'medical'],
        'edtech': ['edtech', 'education', 'learning platform'],
        'ai_saas': ['ai saas', 'ai tool', 'ai agent', 'ai platform', 'artificial intelligence'],
        'ecommerce': ['ecommerce', 'e-commerce', 'shopify', 'dtc', 'd2c'],
        'cybersecurity': ['cybersecurity', 'security', 'infosec'],
        'martech': ['martech', 'marketing tech', 'marketing tool'],
        'hr_tech': ['hr tech', 'hiring', 'recruiting', 'talent'],
    }
    text_lower = text.lower()
    for vertical, kws in vertical_keywords.items():
        if any(kw in text_lower for kw in kws):
            verticals.add(vertical)
    return verticals


def read_file_safe(filepath):
    """Read file content safely."""
    try:
        with open(filepath) as f:
            return f.read()
    except Exception:
        return ""


def categorize_file(filepath, agent_patterns=None):
    """Categorize a file by agent/source based on filename patterns.

    Override with agent_patterns dict: {"pattern": "agent_name"}
    """
    basename = os.path.basename(filepath).lower()

    # Default patterns — customize these for your setup
    default_patterns = {
        'seo': 'seo',
        'oracle': 'seo',
        'content': 'content',
        'flash': 'content',
        'trend': 'content',
        'deal': 'deal',
        'cold': 'cold_outbound',
        'outbound': 'cold_outbound',
        'recruit': 'recruiting',
        'hiring': 'recruiting',
    }

    patterns = agent_patterns or default_patterns

    for pattern, agent in patterns.items():
        if pattern in basename:
            return agent

    return 'other'


def detect_signals(data_dir, additional_data_dirs=None, hours=48, agent_patterns=None):
    """Main detection logic.

    Args:
        data_dir: Primary directory to scan for agent output files
        additional_data_dirs: Dict of {"agent_name": "glob_pattern"} for extra data
        hours: How far back to look for files
        agent_patterns: Dict of {"filename_pattern": "agent_name"} for categorization
    """
    recent_files = get_recent_files(data_dir, hours=hours)
    if not recent_files:
        # Fallback to 7 days
        recent_files = get_recent_files(data_dir, hours=168)

    # Categorize by agent/source
    agent_data = defaultdict(lambda: {
        "files": [], "companies": set(), "keywords": set(), "verticals": set(), "text": ""
    })

    for f in recent_files:
        agent = categorize_file(f, agent_patterns)
        text = read_file_safe(f)

        agent_data[agent]["files"].append(f)
        agent_data[agent]["companies"].update(extract_companies(text))
        agent_data[agent]["keywords"].update(extract_keywords(text))
        agent_data[agent]["verticals"].update(extract_verticals(text))
        agent_data[agent]["text"] += text + "\n"

    # Scan additional data directories
    if additional_data_dirs:
        for agent, pattern in additional_data_dirs.items():
            files = sorted(glob.glob(pattern))[-1:]  # latest only
            for f in files:
                text = read_file_safe(f)
                agent_data[agent]["companies"].update(extract_companies(text))
                agent_data[agent]["keywords"].update(extract_keywords(text))
                agent_data[agent]["verticals"].update(extract_verticals(text))

    # Find overlaps
    signals = []
    agents_list = list(agent_data.keys())

    # 1. Company overlap
    for i, a1 in enumerate(agents_list):
        for a2 in agents_list[i + 1:]:
            common_companies = agent_data[a1]["companies"] & agent_data[a2]["companies"]
            if common_companies:
                confidence = min(95, 60 + len(common_companies) * 10)
                signals.append({
                    "confidence": confidence,
                    "type": "company_overlap",
                    "agents": [a1, a2],
                    "signal": f"Company overlap: {', '.join(list(common_companies)[:5])} appearing in both {a1} and {a2}",
                    "recommended_play": f"Cross-reference {a1} and {a2} data for these companies — coordinate outreach/content",
                    "entities": list(common_companies)[:10],
                })

    # 2. Vertical overlap
    for i, a1 in enumerate(agents_list):
        for a2 in agents_list[i + 1:]:
            common_verticals = agent_data[a1]["verticals"] & agent_data[a2]["verticals"]
            if common_verticals:
                confidence = min(90, 50 + len(common_verticals) * 15)
                signals.append({
                    "confidence": confidence,
                    "type": "vertical_alignment",
                    "agents": [a1, a2],
                    "signal": f"Vertical alignment: {', '.join(common_verticals)} trending across {a1} + {a2}",
                    "recommended_play": f"Coordinated push into {', '.join(common_verticals)}: content + outbound + SEO",
                    "entities": list(common_verticals),
                })

    # 3. Keyword cluster overlap
    for i, a1 in enumerate(agents_list):
        for a2 in agents_list[i + 1:]:
            common_kw = agent_data[a1]["keywords"] & agent_data[a2]["keywords"]
            if common_kw:
                confidence = min(88, 55 + len(common_kw) * 12)
                signals.append({
                    "confidence": confidence,
                    "type": "keyword_cluster",
                    "agents": [a1, a2],
                    "signal": f"Keyword cluster overlap: {', '.join(list(common_kw)[:3])}",
                    "recommended_play": "Target these keywords in content and outbound simultaneously",
                    "entities": list(common_kw),
                })

    # Deduplicate and sort by confidence
    signals.sort(key=lambda x: x["confidence"], reverse=True)

    output = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "agents_analyzed": list(agent_data.keys()),
        "files_scanned": sum(len(d["files"]) for d in agent_data.values()),
        "signals": signals[:20],  # top 20
    }

    return output


def main():
    parser = argparse.ArgumentParser(
        description='Cross-Signal Detector — find overlapping signals across data sources'
    )
    parser.add_argument('--data-dir', default=os.environ.get('DATA_DIR', './data/agent-outputs'),
                        help='Directory containing agent output files')
    parser.add_argument('--output', default=os.environ.get('OUTPUT_FILE', './data/cross-signals-latest.json'),
                        help='Output file path')
    parser.add_argument('--hours', type=int, default=48,
                        help='How far back to look for files (default: 48)')
    args = parser.parse_args()

    output = detect_signals(data_dir=args.data_dir, hours=args.hours)

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    signals = output.get("signals", [])
    print(f"Cross-signal detection complete: {len(signals)} signals found")
    print(f"Output: {args.output}")
    if signals:
        print(f"Top signal (confidence {signals[0]['confidence']}): {signals[0]['signal'][:100]}")


if __name__ == "__main__":
    main()
