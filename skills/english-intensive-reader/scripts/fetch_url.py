#!/usr/bin/env python3
"""
fetch_url.py — english-intensive-reader
Fetch article text from a URL using readability-lxml or trafilatura.
Falls back gracefully and reports errors without guessing content.

Usage:
    python fetch_url.py --url "https://example.com/article" [--output article.txt]
"""

import sys
import argparse
import json
from typing import Optional


def fetch_with_trafilatura(url: str) -> Optional[str]:
    """Primary fetcher using trafilatura (better for news sites)."""
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return None
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        return text
    except ImportError:
        return None
    except Exception:
        return None


def fetch_with_readability(url: str) -> Optional[str]:
    """Fallback fetcher using readability-lxml."""
    try:
        import requests
        from readability import Document

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        doc = Document(resp.text)
        title = doc.title()
        # Strip HTML tags from summary
        import re
        content = re.sub(r"<[^>]+>", " ", doc.summary())
        content = re.sub(r"\s+", " ", content).strip()

        return f"{title}\n\n{content}" if title else content

    except ImportError:
        return None
    except Exception:
        return None


def count_words(text: str) -> int:
    """Count words in text."""
    import re
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    return len(words)


def fetch_article(url: str) -> dict:
    """
    Fetch article from URL. Returns a result dict with:
    - success: bool
    - text: str (article text, empty on failure)
    - title: str
    - word_count: int
    - error: str (error message on failure)
    """
    result = {
        "success": False,
        "url": url,
        "text": "",
        "title": "",
        "word_count": 0,
        "error": "",
        "fetcher_used": "",
    }

    # Validate URL format
    if not url.startswith(("http://", "https://")):
        result["error"] = f"Invalid URL format: must start with http:// or https://"
        return result

    # Try trafilatura first (better quality)
    text = fetch_with_trafilatura(url)
    if text and len(text.strip()) > 100:
        result["success"] = True
        result["text"] = text.strip()
        result["word_count"] = count_words(text)
        result["fetcher_used"] = "trafilatura"
        # Extract title from first line if available
        lines = text.strip().split("\n")
        if lines:
            result["title"] = lines[0][:100]
        return result

    # Fallback to readability-lxml
    text = fetch_with_readability(url)
    if text and len(text.strip()) > 100:
        result["success"] = True
        result["text"] = text.strip()
        result["word_count"] = count_words(text)
        result["fetcher_used"] = "readability-lxml"
        lines = text.strip().split("\n")
        if lines:
            result["title"] = lines[0][:100]
        return result

    # Both failed — report error, DO NOT guess content (NEVER N5)
    result["error"] = (
        "无法抓取该 URL（可能原因：反爬限制 / 需要登录 / 网络问题 / 内容为空）。\n"
        "请复制文章文本后粘贴，我来帮你精读。"
    )
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Fetch article text from a URL for english-intensive-reader"
    )
    parser.add_argument("--url", required=True, help="Article URL to fetch")
    parser.add_argument("--output", help="Output file path (optional, default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = fetch_article(args.url)

    if args.json:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        if result["success"]:
            output = result["text"]
        else:
            output = f"ERROR: {result['error']}"
            print(output, file=sys.stderr)
            sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"✅ Article saved to {args.output} ({result['word_count']} words)")
    else:
        print(output)


if __name__ == "__main__":
    main()
