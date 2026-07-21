#!/usr/bin/env python3
"""
Competitive Monitor — tracks pricing, blog posts, and feature changes across competitors.

Generates weekly competitive intelligence diffs. Configurable competitor list.

Usage:
    python3 competitive-monitor.py
    python3 competitive-monitor.py --company acme
    python3 competitive-monitor.py --output report.md
    python3 competitive-monitor.py --config competitors.json

Competitor config can be provided via:
    1. --config flag pointing to a JSON file
    2. COMPETITORS_CONFIG env var pointing to a JSON file
    3. Built-in example competitors (for demo purposes)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from difflib import unified_diff
from typing import Dict, List, Optional
from html.parser import HTMLParser
from urllib.error import URLError, HTTPError


def validate_text(text, max_length=500000):
    """Basic input validation for scraped content."""
    if not text or not isinstance(text, str):
        return text
    # Truncate extremely long content
    if len(text) > max_length:
        text = text[:max_length]
    return text


class BlogExtractor(HTMLParser):
    """Extract blog post titles and dates from HTML."""

    def __init__(self):
        super().__init__()
        self.posts = []
        self.current_title = None
        self.current_date = None
        self.in_title = False
        self.in_date = False
        self.title_tags = ['h1', 'h2', 'h3', 'h4']

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.title_tags:
            self.in_title = True
        for name, value in attrs:
            if name in ['class', 'id'] and any(
                date_word in value.lower() for date_word in ['date', 'time', 'published']
            ):
                self.in_date = True

    def handle_endtag(self, tag):
        if tag.lower() in self.title_tags:
            self.in_title = False
        self.in_date = False

    def handle_data(self, data):
        if self.in_title and data.strip():
            self.current_title = data.strip()

        if self.in_date and data.strip():
            date_match = re.search(
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\w+ \d{1,2},? \d{4}\b', data
            )
            if date_match:
                self.current_date = date_match.group()

        if self.current_title and self.current_date:
            self.posts.append({
                'title': self.current_title,
                'date': self.current_date,
            })
            self.current_title = None
            self.current_date = None


class CompetitiveMonitor:
    """Main competitive monitoring class."""

    # Example competitors for demo. Override with --config or COMPETITORS_CONFIG.
    EXAMPLE_COMPETITORS = {
        'competitor_a': {
            'name': 'Competitor A',
            'domain': 'competitor-a.com',
            'pricing_url': 'https://www.competitor-a.com/pricing',
            'blog_url': 'https://www.competitor-a.com/blog',
            'linkedin_query': 'Competitor A site:linkedin.com',
            'jobs_query': 'Competitor A careers OR jobs',
        },
        'competitor_b': {
            'name': 'Competitor B',
            'domain': 'competitor-b.com',
            'pricing_url': 'https://www.competitor-b.com/pricing',
            'blog_url': 'https://www.competitor-b.com/blog',
            'linkedin_query': 'Competitor B site:linkedin.com',
            'jobs_query': 'Competitor B careers OR jobs',
        },
    }

    def __init__(self, data_dir: str = None, competitors: dict = None):
        self.data_dir = data_dir or os.path.join(os.getcwd(), 'data', 'competitive')
        self.pricing_dir = os.path.join(self.data_dir, 'pricing-snapshots')
        self.history_dir = os.path.join(self.data_dir, 'scan-history')
        self.competitors = competitors or self.EXAMPLE_COMPETITORS

        os.makedirs(self.pricing_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)

    def fetch_url(self, url: str, timeout: int = 10) -> Optional[str]:
        """Fetch URL content with error handling."""
        try:
            headers = {
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/91.0.4472.124 Safari/537.36'
                )
            }
            request = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(request, timeout=timeout) as response:
                content = response.read().decode('utf-8', errors='ignore')
                content = validate_text(content)
                return content

        except (URLError, HTTPError, UnicodeDecodeError) as e:
            print(f"❌ Error fetching {url}: {e}")
            return None

    def extract_blog_posts(self, html: str) -> List[Dict]:
        """Extract blog posts from HTML."""
        if not html:
            return []

        extractor = BlogExtractor()
        try:
            extractor.feed(html)
            return extractor.posts
        except Exception as e:
            print(f"Error extracting blog posts: {e}")
            return []

    def is_recent_post(self, date_str: str, days_back: int = 7) -> bool:
        """Check if post is from last N days."""
        if not date_str:
            return False

        formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d',
            '%B %d, %Y', '%b %d, %Y', '%B %d %Y', '%b %d %Y',
        ]

        for fmt in formats:
            try:
                post_date = datetime.strptime(date_str, fmt)
                cutoff_date = datetime.now() - timedelta(days=days_back)
                return post_date >= cutoff_date
            except ValueError:
                continue

        return False

    def get_pricing_diff(self, company_key: str, current_content: str) -> Optional[str]:
        """Compare current pricing with previous snapshot."""
        today = datetime.now().strftime('%Y-%m-%d')
        pricing_file = os.path.join(self.pricing_dir, f'{company_key}-{today}.txt')

        with open(pricing_file, 'w', encoding='utf-8') as f:
            f.write(current_content)

        previous_files = [
            f for f in os.listdir(self.pricing_dir)
            if f.startswith(f'{company_key}-') and f != f'{company_key}-{today}.txt'
        ]

        if not previous_files:
            return "🆕 First pricing snapshot saved"

        previous_files.sort(reverse=True)
        previous_file = os.path.join(self.pricing_dir, previous_files[0])

        try:
            with open(previous_file, 'r', encoding='utf-8') as f:
                previous_content = f.read()

            if current_content.strip() == previous_content.strip():
                return None

            current_lines = current_content.splitlines()
            previous_lines = previous_content.splitlines()

            diff = list(unified_diff(
                previous_lines, current_lines,
                fromfile='previous', tofile='current', n=0
            ))

            changes = len([
                line for line in diff
                if line.startswith(('+', '-')) and not line.startswith(('+++', '---'))
            ])

            return f"🔍 {changes} lines changed since last snapshot"

        except Exception as e:
            return f"❌ Error comparing snapshots: {e}"

    def scan_competitor(self, company_key: str) -> Dict:
        """Scan single competitor."""
        company = self.competitors[company_key]
        print(f"\n🔍 Scanning {company['name']}...")

        results = {
            'company': company['name'],
            'domain': company['domain'],
            'scan_time': datetime.now().isoformat(),
            'pricing': {},
            'blog': {},
            'search_queries': {
                'linkedin': company.get('linkedin_query', ''),
                'jobs': company.get('jobs_query', ''),
            },
        }

        # Fetch pricing page
        pricing_url = company.get('pricing_url')
        if pricing_url:
            print(f"  📄 Fetching pricing: {pricing_url}")
            pricing_content = self.fetch_url(pricing_url)

            if pricing_content:
                clean_content = re.sub(r'<[^>]+>', '', pricing_content)
                clean_content = re.sub(r'\s+', ' ', clean_content).strip()

                pricing_diff = self.get_pricing_diff(company_key, clean_content)

                results['pricing'] = {
                    'url': pricing_url,
                    'fetched': True,
                    'content_length': len(clean_content),
                    'diff': pricing_diff,
                }
            else:
                results['pricing'] = {
                    'url': pricing_url,
                    'fetched': False,
                    'error': 'Failed to fetch pricing page',
                }

        # Fetch blog page
        blog_url = company.get('blog_url')
        if blog_url:
            print(f"  📝 Fetching blog: {blog_url}")
            blog_content = self.fetch_url(blog_url)

            recent_posts = []
            if blog_content:
                all_posts = self.extract_blog_posts(blog_content)
                recent_posts = [post for post in all_posts if self.is_recent_post(post['date'])]

            results['blog'] = {
                'url': blog_url,
                'fetched': bool(blog_content),
                'total_posts_found': len(self.extract_blog_posts(blog_content)) if blog_content else 0,
                'recent_posts': recent_posts,
            }

        return results

    def generate_report(self, scan_results: List[Dict], threat_keywords: List[str] = None) -> str:
        """Generate markdown report."""
        today = datetime.now().strftime('%Y-%m-%d')

        # Configurable threat keywords (topics that signal competitive overlap)
        if threat_keywords is None:
            threat_keywords = ['funnel', 'conversion', 'landing page', 'ab test', 'optimize', 'cro']

        report = f"""# 🔍 Competitive Intelligence Report - {today}

## Executive Summary

Monitored {len(scan_results)} competitors for pricing changes, recent blog activity, and market signals.

"""

        threats = []
        interesting = []
        opportunities = []
        search_queries = []

        for result in scan_results:
            company = result['company']

            pricing = result.get('pricing', {})
            if pricing.get('diff') and '🔍' in str(pricing['diff']):
                interesting.append(
                    f"**{company}**: {pricing['diff']} → *Monitor for pricing strategy shifts*"
                )
            elif pricing.get('diff') and '🆕' in str(pricing['diff']):
                interesting.append(
                    f"**{company}**: {pricing['diff']} → *Baseline established for future tracking*"
                )

            blog = result.get('blog', {})
            recent_posts = blog.get('recent_posts', [])

            if recent_posts:
                post_titles = [
                    post['title'][:80] + '...' if len(post['title']) > 80 else post['title']
                    for post in recent_posts[:3]
                ]
                content_lower = ' '.join(post_titles).lower()

                if any(keyword in content_lower for keyword in threat_keywords):
                    threats.append(
                        f"**{company}**: {len(recent_posts)} recent posts, potential feature overlap → *Review competitive positioning*"
                    )
                else:
                    interesting.append(
                        f"**{company}**: {len(recent_posts)} recent posts → *{', '.join(post_titles[:2])}*"
                    )
            else:
                opportunities.append(
                    f"**{company}**: No recent blog content → *Content marketing gap you can exploit*"
                )

            sq = result.get('search_queries', {})
            if sq.get('linkedin'):
                search_queries.append(f"LinkedIn search: {sq['linkedin']}")
            if sq.get('jobs'):
                search_queries.append(f"Jobs search: {sq['jobs']}")

        if threats:
            report += "## 🔴 THREATS\n\n"
            for threat in threats:
                report += f"- {threat}\n"
            report += "\n"

        if interesting:
            report += "## 🟡 INTERESTING\n\n"
            for item in interesting:
                report += f"- {item}\n"
            report += "\n"

        if opportunities:
            report += "## 🟢 OPPORTUNITIES\n\n"
            for opp in opportunities:
                report += f"- {opp}\n"
            report += "\n"

        if search_queries:
            report += "## 🔎 LinkedIn/Jobs Search Queries\n\n"
            report += "Run these queries for social/hiring signals:\n\n"
            for query in search_queries:
                report += f"- `{query}`\n"
            report += "\n"

        report += "## 📊 Technical Summary\n\n"
        for result in scan_results:
            company = result['company']
            pricing = result.get('pricing', {})
            blog = result.get('blog', {})

            report += f"**{company}:**\n"
            report += f"- Pricing: {'✅' if pricing.get('fetched') else '❌'} {pricing.get('diff', 'No changes')}\n"
            report += f"- Blog: {'✅' if blog.get('fetched') else '❌'} {len(blog.get('recent_posts', []))} recent posts\n\n"

        return report

    def save_results(self, scan_results: List[Dict]) -> str:
        """Save scan results to files."""
        today = datetime.now().strftime('%Y-%m-%d')

        latest_file = os.path.join(self.data_dir, 'latest-scan.json')
        with open(latest_file, 'w') as f:
            json.dump(scan_results, f, indent=2)

        history_file = os.path.join(self.history_dir, f'{today}.json')
        with open(history_file, 'w') as f:
            json.dump(scan_results, f, indent=2)

        return latest_file

    def run(self, company_filter: Optional[str] = None) -> str:
        """Run competitive monitoring scan."""
        print("🚀 Starting competitive monitoring scan...")

        companies_to_scan = (
            [company_filter] if company_filter else list(self.competitors.keys())
        )

        if company_filter and company_filter not in self.competitors:
            print(f"❌ Unknown company: {company_filter}")
            print(f"Available companies: {', '.join(self.competitors.keys())}")
            return ""

        scan_results = []
        for company_key in companies_to_scan:
            try:
                result = self.scan_competitor(company_key)
                scan_results.append(result)
            except Exception as e:
                print(f"❌ Error scanning {company_key}: {e}")

        self.save_results(scan_results)
        report = self.generate_report(scan_results)

        print(f"\n✅ Scan complete! Results for {len(scan_results)} companies.")
        return report


def load_competitors_config(config_path: str) -> dict:
    """Load competitors from a JSON config file.

    Expected format:
    {
        "competitor_key": {
            "name": "Competitor Name",
            "domain": "competitor.com",
            "pricing_url": "https://competitor.com/pricing",
            "blog_url": "https://competitor.com/blog",
            "linkedin_query": "Competitor Name site:linkedin.com",
            "jobs_query": "Competitor Name careers OR jobs"
        }
    }
    """
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='Competitive Monitoring Scraper')
    parser.add_argument('--company', help='Scan specific company only (by key)')
    parser.add_argument('--output', '-o', help='Save report to file')
    parser.add_argument('--config', help='Path to competitors JSON config file')
    parser.add_argument('--data-dir', help='Directory for storing scan data')
    parser.add_argument('--threat-keywords', nargs='*',
                        help='Keywords that signal competitive overlap (space-separated)')

    args = parser.parse_args()

    # Load competitor config
    config_path = args.config or os.environ.get('COMPETITORS_CONFIG')
    competitors = None
    if config_path:
        try:
            competitors = load_competitors_config(config_path)
            print(f"📋 Loaded {len(competitors)} competitors from {config_path}")
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            sys.exit(1)

    monitor = CompetitiveMonitor(
        data_dir=args.data_dir,
        competitors=competitors,
    )

    report = monitor.run(args.company)

    if report:
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"\n📁 Report saved to: {args.output}")


if __name__ == '__main__':
    main()
