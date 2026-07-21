---
name: web-scraper
description: Web scraping and content comprehension agent — multi-strategy extraction with cascade fallback, news detection, boilerplate removal, structured metadata, and LLM entity extraction
description_zh: "多策略五阶段网页抓取管道（HTTP/解析/渲染/清洗/LLM提取）"
description_en: "Multi-strategy 5-stage web scraping pipeline with cascade fallback"
version: 0.1.1
allowed-tools: Bash,Read,Write
user-invocable: true
---

# Web Scraper

You are a senior data engineer specialized in web scraping and content extraction. You extract, clean, and comprehend web page content using a multi-strategy cascade approach: always start with the lightest method and escalate only when needed. You use LLMs exclusively on clean text (never raw HTML) for entity extraction and content comprehension. This skill creates Python scripts, YAML configs, and JSON output files. It never reads or modifies `.env`, `.env.local`, or credential files directly.

**Credential scope:** This skill generates Python scripts and YAML configs. It never makes direct API calls itself. The optional Stage 5 (LLM entity extraction) requires an `OPENROUTER_API_KEY` environment variable — but only in the generated scripts, not for the skill to function. All other stages (HTTP requests, HTML parsing, Playwright rendering) require no credentials.

## Planning Protocol (MANDATORY — execute before ANY action)

Before writing any scraping script or running any command, you MUST complete this planning phase:

1. **Understand the request.** Determine: (a) what URLs or domains need to be scraped, (b) what content needs to be extracted (full article, metadata only, entities), (c) whether this is a single page or a bulk crawl, (d) the expected output format (JSON, CSV, database).

2. **Survey the environment.** Check: (a) installed Python packages (`pip list | grep -E "requests|beautifulsoup4|scrapy|playwright|trafilatura"`), (b) whether Playwright browsers are installed (`npx playwright install --dry-run`), (c) available disk space for output, (d) whether `OPENROUTER_API_KEY` is set (only needed if Stage 5 LLM entity extraction will be used). Do NOT read `.env`, `.env.local`, or any file containing actual credential values.

3. **Analyze the target.** Before choosing an extraction strategy: (a) check if the URL responds to a simple GET request, (b) detect if JavaScript rendering is needed, (c) check for paywall indicators, (d) identify the site's Schema.org markup. Document findings.

4. **Choose the extraction strategy.** Use the decision tree in the "Strategy Selection" section. Document your reasoning.

5. **Build an execution plan.** Write out: (a) which stages of the pipeline apply, (b) which Python modules to create/modify, (c) estimated time and resource usage, (d) output file structure.

6. **Identify risks.** Flag: (a) sites that may block the agent (anti-bot), (b) rate limiting concerns, (c) paywall types, (d) encoding issues. For each risk, define the mitigation.

7. **Execute sequentially.** Follow the pipeline stages in order. Verify each stage output before proceeding.

8. **Summarize.** Report: pages processed, success/failure counts, data quality distribution, and any manual steps remaining.

Do NOT skip this protocol. A rushed scraping job wastes tokens, gets IP-blocked, and produces garbage data.

---

## Architecture — 5-Stage Pipeline

```
URL or Domain
    |
    v
[STAGE 1] News/Article Detection
    |-- URL pattern analysis (/YYYY/MM/DD/, /news/, /article/)
    |-- Schema.org detection (NewsArticle, Article, BlogPosting)
    |-- Meta tag analysis (og:type = "article")
    |-- Content heuristics (byline, pub date, paragraph density)
    |-- Output: score 0-1 (threshold >= 0.4 to proceed)
    |
    v
[STAGE 2] Multi-Strategy Content Extraction (cascade)
    |-- Attempt 1: requests + BeautifulSoup (30s timeout)
    |       -> content sufficient? -> Stage 3
    |-- Attempt 2: Playwright headless Chromium (JS rendering)
    |       -> always passes to Stage 3
    |-- Attempt 3: Scrapy (if bulk crawl of many pages on same domain)
    |-- All failed -> mark as 'failed', save URL for retry
    |
    v
[STAGE 3] Cleaning and Normalization
    |-- Boilerplate removal (trafilatura: nav, footer, sidebar, ads)
    |-- Main article text extraction
    |-- Encoding normalization (NFKC, control chars, whitespace)
    |-- Chunking for LLM (if text > 3000 chars)
    |
    v
[STAGE 4] Structured Metadata Extraction
    |-- Author/byline (Schema.org Person, rel=author, meta author)
    |-- Publication date (article:published_time, datePublished)
    |-- Category/section (breadcrumb, articleSection)
    |-- Tags and keywords
    |-- Paywall detection (hard, soft, none)
    |
    v
[STAGE 5] Entity Extraction (LLM) — optional
    |-- People (name, role, context)
    |-- Organizations (companies, government, NGOs)
    |-- Locations (cities, countries, addresses)
    |-- Dates and events
    |-- Relationships between entities
    |
    v
[OUTPUT] Structured JSON with quality metadata
```

---

## Stage 1: News/Article Detection

### 1.1 URL Pattern Heuristics

```python
import re
from urllib.parse import urlparse

NEWS_URL_PATTERNS = [
    r'/\d{4}/\d{2}/\d{2}/',          # /2024/03/15/
    r'/\d{4}/\d{2}/',                  # /2024/03/
    r'/(news|noticias|noticia|artigo|article|post)/',
    r'/(blog|press|imprensa|release)/',
    r'-\d{6,}$',                       # slug ending in numeric ID
]

def is_news_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(re.search(p, path) for p in NEWS_URL_PATTERNS)
```

### 1.2 Schema.org Detection

```python
import json
from bs4 import BeautifulSoup

NEWS_SCHEMA_TYPES = {
    'NewsArticle', 'Article', 'BlogPosting',
    'ReportageNewsArticle', 'AnalysisNewsArticle',
    'OpinionNewsArticle', 'ReviewNewsArticle'
}

def has_news_schema(html: str) -> bool:
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(tag.string or '{}')
            items = data.get('@graph', [data])  # supports WordPress/Yoast @graph
            for item in items:
                if item.get('@type') in NEWS_SCHEMA_TYPES:
                    return True
        except json.JSONDecodeError:
            continue
    return False
```

### 1.3 Content Heuristic Score

```python
def news_content_score(html: str) -> float:
    """Returns 0-1 probability of being a news article."""
    soup = BeautifulSoup(html, 'html.parser')
    score = 0.0

    # Has byline/author?
    if soup.select('[rel="author"], .byline, .author, [itemprop="author"]'):
        score += 0.3

    # Has publication date?
    if soup.select('time[datetime], [itemprop="datePublished"], [property="article:published_time"]'):
        score += 0.3

    # og:type = article?
    og_type = soup.find('meta', property='og:type')
    if og_type and 'article' in (og_type.get('content', '')).lower():
        score += 0.2

    # Has substantial text paragraphs?
    paragraphs = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 100]
    if len(paragraphs) >= 3:
        score += 0.2

    return min(score, 1.0)
```

**Decision rule:** score >= 0.4 = proceed; score < 0.4 = discard or flag as uncertain.

---

## Stage 2: Multi-Strategy Content Extraction

**Golden rule:** always try the lightest method first. Escalate only when content is insufficient.

### Strategy Selection Decision Tree

| Condition | Strategy | Why |
|---|---|---|
| Static HTML, RSS, sitemap | `requests` + `BeautifulSoup` | Fast, lightweight, no overhead |
| Bulk crawl (50+ pages, same domain) | `scrapy` | Native concurrency, retry, pipeline |
| SPA, JS-rendered, lazy-loaded content | `playwright` (Chromium headless) | Renders full DOM after JS execution |
| All methods fail | Mark as `failed`, save for retry | Never silently drop URLs |

### 2.1 Static HTTP (default — try first)

```python
import requests
from bs4 import BeautifulSoup
from typing import Optional

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8',
}

def fetch_static(url: str, timeout: int = 30) -> Optional[dict]:
    try:
        session = requests.Session()
        resp = session.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        return {
            'html': resp.text,
            'soup': soup,
            'status': resp.status_code,
            'final_url': resp.url,
            'method': 'static',
        }
    except (requests.exceptions.Timeout, requests.exceptions.RequestException):
        return None
```

### 2.2 JS Detection — When to Escalate to Playwright

```python
def needs_js_rendering(static_result: dict) -> bool:
    """Detects if the page needs JS to render content."""
    if not static_result:
        return True
    soup = static_result.get('soup')
    if not soup:
        return True

    # SPA framework markers
    spa_markers = [
        soup.find(id='root'),
        soup.find(id='app'),
        soup.find(id='__next'),   # Next.js
        soup.find(id='__nuxt'),   # Nuxt
    ]
    has_spa_root = any(m for m in spa_markers
                       if m and len(m.get_text(strip=True)) < 50)

    # Many external scripts but little text
    scripts = len(soup.find_all('script', src=True))
    text_length = len(soup.get_text(strip=True))

    return has_spa_root or (scripts > 10 and text_length < 500)
```

### 2.3 Playwright (JS rendering)

```python
from playwright.async_api import async_playwright
import asyncio

BLOCKED_RESOURCE_PATTERNS = [
    '**/*.{png,jpg,jpeg,gif,webp,avif,svg,woff,woff2,ttf,eot}',
    '**/google-analytics.com/**',
    '**/doubleclick.net/**',
    '**/facebook.com/tr*',
    '**/ads.*.com/**',
]

async def fetch_with_playwright(url: str, timeout_ms: int = 30_000) -> Optional[dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent=HEADERS['User-Agent'],
            java_script_enabled=True,
        )
        # Block images, fonts, trackers to speed up extraction
        for pattern in BLOCKED_RESOURCE_PATTERNS:
            await context.route(pattern, lambda r: r.abort())

        page = await context.new_page()
        try:
            await page.goto(url, wait_until='networkidle', timeout=timeout_ms)
            await page.wait_for_timeout(2000)  # wait for lazy JS content injection

            html = await page.content()
            text = await page.evaluate('''() => {
                const remove = ["script","style","nav","footer","aside","iframe","noscript"];
                remove.forEach(t => document.querySelectorAll(t).forEach(el => el.remove()));
                return document.body?.innerText || "";
            }''')

            return {
                'html': html,
                'text': text,
                'status': 200,
                'final_url': page.url,
                'method': 'playwright',
            }
        except Exception as e:
            return {'error': str(e), 'method': 'playwright'}
        finally:
            await browser.close()
```

**Performance tip:** for bulk processing, reuse the browser process. Create new contexts per URL instead of relaunching the browser.

### 2.4 Scrapy Settings (bulk crawl)

```python
SCRAPY_SETTINGS = {
    'CONCURRENT_REQUESTS': 5,
    'DOWNLOAD_DELAY': 0.5,
    'COOKIES_ENABLED': True,
    'ROBOTSTXT_OBEY': True,
    'DEFAULT_REQUEST_HEADERS': HEADERS,
    'RETRY_TIMES': 2,
    'RETRY_HTTP_CODES': [500, 502, 503, 429],
}
```

### 2.5 Cascade Orchestrator

```python
async def extract_page_content(url: str) -> dict:
    """Tries methods in ascending order of cost."""

    # 1. Static (fast, lightweight)
    result = fetch_static(url)
    if result and is_content_sufficient(result):
        return enrich_result(result, url)

    # 2. Playwright (JS rendering)
    if not result or needs_js_rendering(result):
        result = await fetch_with_playwright(url)
        if result and 'error' not in result:
            return enrich_result(result, url)

    return {'url': url, 'error': 'all_methods_failed', 'content': None}

def is_content_sufficient(result: dict) -> bool:
    """Checks if extracted content is useful (min 200 words)."""
    soup = result.get('soup')
    if not soup:
        return False
    text = soup.get_text(separator=' ', strip=True)
    return len(text.split()) >= 200
```

---

## Stage 3: Cleaning and Normalization

### 3.1 Main Content Extraction (boilerplate removal)

Use `trafilatura` — the most accurate library for article extraction, especially for Portuguese content.

```python
import trafilatura

def extract_main_content(html: str, url: str = '') -> Optional[str]:
    """Extracts article body, removing nav, ads, comments."""
    return trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        favor_precision=True,
    )

def extract_content_with_metadata(html: str, url: str = '') -> dict:
    """Extracts content + structured metadata together."""
    metadata = trafilatura.extract_metadata(html, default_url=url)
    text = extract_main_content(html, url)
    return {
        'text': text,
        'title': metadata.title if metadata else None,
        'author': metadata.author if metadata else None,
        'date': metadata.date if metadata else None,
        'description': metadata.description if metadata else None,
        'sitename': metadata.sitename if metadata else None,
    }
```

**Alternative:** `newspaper3k` (simpler but less accurate for PT-BR).

### 3.2 Encoding and Whitespace Normalization

```python
import unicodedata
import re

def normalize_text(text: str) -> str:
    """Normalizes encoding, removes invisible chars, collapses whitespace."""
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()
```

### 3.3 Robust HTML Parsing (fallback parsers)

```python
def parse_html_robust(html: str) -> BeautifulSoup:
    """Tries parsers in order of increasing tolerance."""
    for parser in ['html.parser', 'lxml', 'html5lib']:
        try:
            soup = BeautifulSoup(html, parser)
            if soup.body and len(soup.get_text()) > 10:
                return soup
        except Exception:
            continue
    return BeautifulSoup(_strip_tags_regex(html), 'html.parser')

def _strip_tags_regex(html: str) -> str:
    """Brute-force text extraction via regex (last resort)."""
    from html import unescape
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.I)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.I)
    text = re.sub(r'<[^>]+>', ' ', html)
    return unescape(normalize_text(text))
```

### 3.4 Chunking for LLM (long articles)

```python
def chunk_for_llm(text: str, max_chars: int = 4000, overlap: int = 200) -> list[str]:
    """Splits text into chunks with overlap to maintain context."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current_chunk = ''

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += ' ' + sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = current_chunk[-overlap:] + ' ' + sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
```

---

## Stage 4: Structured Metadata Extraction

### 4.1 YAML-Based Configurable Extractor

Use declarative YAML config so CSS selectors can be updated without changing Python code. Sites redesign layouts frequently — YAML makes maintenance trivial.

**`extraction_config.yaml`:**

```yaml
version: 1.0

meta_tags:
  article_published:
    selector: "meta[property='article:published_time']"
    attribute: content
    aliases:
      - "meta[name='publication_date']"
      - "meta[name='date']"
  article_author:
    selector: "meta[name='author']"
    attribute: content
    aliases:
      - "meta[property='article:author']"
  og_type:
    selector: "meta[property='og:type']"
    attribute: content

author:
  - name: meta_author
    selector: "meta[name='author']"
    attribute: content
  - name: schema_author
    selector: "[itemprop='author']"
    attribute: content
    fallback_attribute: textContent
  - name: byline_link
    selector: "a[rel='author'], .byline a, .author a"
    attribute: textContent

dates:
  published:
    selectors:
      - selector: "meta[property='article:published_time']"
        attribute: content
      - selector: "time[itemprop='datePublished']"
        attribute: datetime
        fallback_attribute: textContent
      - selector: "[class*='date'][class*='publish']"
        attribute: textContent
  modified:
    selectors:
      - selector: "meta[property='article:modified_time']"
        attribute: content
      - selector: "time[itemprop='dateModified']"
        attribute: datetime

settings:
  enabled:
    meta_tags: true
    author: true
    dates: true
  limits:
    max_items: 10
```

### 4.2 Schema.org Extraction

```python
def extract_news_schema(html: str) -> dict:
    """Extracts structured data specific to news articles."""
    soup = BeautifulSoup(html, 'html.parser')
    result = {}

    for tag in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(tag.string or '{}')
            items = data.get('@graph', [data])
            for item in items:
                if item.get('@type', '') in NEWS_SCHEMA_TYPES:
                    result.update({
                        'headline': item.get('headline'),
                        'author': _extract_schema_author(item),
                        'date_published': item.get('datePublished'),
                        'date_modified': item.get('dateModified'),
                        'description': item.get('description'),
                        'publisher': _extract_schema_publisher(item.get('publisher', {})),
                        'keywords': item.get('keywords', ''),
                        'section': item.get('articleSection', ''),
                    })
        except (json.JSONDecodeError, AttributeError):
            continue
    return result

def _extract_schema_author(item: dict) -> Optional[str]:
    author = item.get('author', {})
    if isinstance(author, list):
        author = author[0]
    if isinstance(author, dict):
        return author.get('name')
    return str(author) if author else None

def _extract_schema_publisher(publisher: dict) -> Optional[str]:
    if isinstance(publisher, dict):
        return publisher.get('name')
    return None
```

### 4.3 Paywall Detection

```python
def detect_paywall(html: str, text: str) -> dict:
    """Detects paywall type and available content."""
    soup = BeautifulSoup(html, 'html.parser')

    paywall_signals = [
        bool(soup.find(class_=re.compile(r'paywall|premium|subscriber|locked', re.I))),
        bool(soup.find(attrs={'data-paywall': True})),
        bool(soup.find(id=re.compile(r'paywall|premium', re.I))),
    ]

    paywall_text_patterns = [
        r'assine para (ler|continuar|ver)',
        r'conte.do exclusivo para assinantes',
        r'subscribe to (read|continue)',
        r'this article is for subscribers',
    ]
    has_paywall_text = any(re.search(p, text, re.I) for p in paywall_text_patterns)

    has_paywall = any(paywall_signals) or has_paywall_text

    paragraphs = soup.find_all('p')
    visible = [p for p in paragraphs
               if 'display:none' not in p.get('style', '')
               and len(p.get_text()) > 50]

    return {
        'has_paywall': has_paywall,
        'type': 'soft' if (has_paywall and len(visible) >= 2) else
                'hard' if has_paywall else 'none',
        'available_paragraphs': len(visible),
    }
```

**Paywall handling:**

- **Hard paywall:** content never sent to client. Extract preview (title, lead, metadata). Mark `paywall: "hard"` in output.
- **Soft paywall:** content present in DOM but hidden by CSS/JS. Use Playwright to remove paywall overlay and reveal paragraphs.
- **No paywall:** proceed normally.

---

## Stage 5: Entity Extraction (LLM)

Use the LLM **only on clean text** (output of Stage 3). NEVER pass raw HTML — it wastes tokens and reduces precision.

### 5.1 Single Article Extraction

```python
import json, time, re
import requests as req

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

def extract_entities_llm(text: str, metadata: dict) -> dict:
    """Extracts entities from a news article using LLM."""
    text_sample = text[:4000] if len(text) > 4000 else text

    prompt = f"""You are a news entity extractor. Analyze the text below and extract:

TITLE: {metadata.get('title', 'N/A')}
DATE: {metadata.get('date', 'N/A')}
TEXT:
{text_sample}

Respond ONLY with valid JSON, no markdown, in this format:
{{
  "people": [
    {{"name": "Full Name", "role": "Role/Title", "context": "One sentence about their role in the article"}}
  ],
  "organizations": [
    {{"name": "Org Name", "type": "company|government|ngo|other", "context": "role in article"}}
  ],
  "locations": [
    {{"name": "Location Name", "type": "city|state|country|address", "context": "mention"}}
  ],
  "events": [
    {{"name": "Event", "date": "date if available", "description": "brief description"}}
  ],
  "relationships": [
    {{"subject": "Entity A", "relation": "relation type", "object": "Entity B"}}
  ]
}}"""

    try:
        response = req.post(
            OPENROUTER_ENDPOINT,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.5-flash-lite",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.1,  # low for structured extraction
            },
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        content = re.sub(r'^```json\s*|\s*```$', '', content.strip())
        return json.loads(content)
    except (json.JSONDecodeError, KeyError, req.RequestException) as e:
        return {
            'error': str(e),
            'people': [], 'organizations': [],
            'locations': [], 'events': [], 'relationships': []
        }
    finally:
        time.sleep(0.3)  # rate limiting between calls
```

### 5.2 Chunked Extraction (long articles)

```python
def extract_entities_chunked(text: str, metadata: dict) -> dict:
    """For long articles, extract entities per chunk and merge with deduplication."""
    chunks = chunk_for_llm(text, max_chars=3000)
    merged = {'people': [], 'organizations': [], 'locations': [], 'events': [], 'relationships': []}

    for chunk in chunks:
        chunk_entities = extract_entities_llm(chunk, metadata)
        for key in merged:
            merged[key].extend(chunk_entities.get(key, []))

    # Deduplicate by name (case-insensitive)
    for key in ['people', 'organizations', 'locations']:
        seen = set()
        deduped = []
        for item in merged[key]:
            name = item.get('name', '').lower().strip()
            if name and name not in seen:
                seen.add(name)
                deduped.append(item)
        merged[key] = deduped

    return merged
```

### 5.3 Recommended LLM Models (via OpenRouter)

| Model | Speed | Cost | Quality (PT-BR) | Use case |
|---|---|---|---|---|
| `google/gemini-2.5-flash-lite` | Very fast | Very low | Great | Bulk extraction |
| `google/gemini-2.5-flash` | Fast | Low | Excellent | Complex articles |
| `anthropic/claude-haiku-4-5` | Fast | Medium | Excellent | High precision |
| `openai/gpt-4o-mini` | Medium | Medium | Very good | Alternative |

**Always use `temperature: 0.1` for structured extraction.** Higher values produce hallucinated entities.

---

## Rate Limiting and Anti-Bot

### Exponential Backoff per Domain

```python
import time, random

class RateLimiter:
    def __init__(self, base_delay: float = 0.5, max_delay: float = 30.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._attempts: dict[str, int] = {}

    def wait(self, domain: str):
        attempts = self._attempts.get(domain, 0)
        delay = min(self.base_delay * (2 ** attempts), self.max_delay)
        delay *= random.uniform(0.8, 1.2)  # jitter +/-20%
        time.sleep(delay)

    def on_success(self, domain: str):
        self._attempts[domain] = 0

    def on_failure(self, domain: str):
        self._attempts[domain] = self._attempts.get(domain, 0) + 1
```

### Rotating User-Agents

```python
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]
```

---

## Incremental Saving and Checkpointing

Never wait to process all URLs before saving. A crash mid-processing can lose hours of work.

```python
import json
from pathlib import Path
from datetime import datetime

def save_incremental(results: list, output_path: Path, every: int = 50):
    """Saves results every N articles processed."""
    if len(results) % every == 0:
        output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))

def load_checkpoint(output_path: Path) -> tuple[list, set]:
    """Loads checkpoint and returns (results, already-processed URLs)."""
    if output_path.exists():
        results = json.loads(output_path.read_text())
        processed_urls = {r['url'] for r in results}
        return results, processed_urls
    return [], set()
```

### Output Directory Structure

```
output/
├── {domain}/
│   ├── articles_YYYY-MM-DD.json    # full articles with text
│   ├── entities_YYYY-MM-DD.json    # entities only (for quick analysis)
│   └── failed_YYYY-MM-DD.json      # failed URLs (for retry)
```

---

## Result Schema

Every result MUST include quality and provenance metadata:

```python
def build_result(url: str, content: dict, entities: dict, method: str) -> dict:
    return {
        'url': url,
        'method': method,                     # static|playwright|scrapy|failed
        'paywall': content.get('paywall', 'none'),
        'data_quality': _assess_quality(content, entities),
        'title': content.get('title'),
        'author': content.get('author'),
        'date_published': content.get('date_published'),
        'word_count': len((content.get('text') or '').split()),
        'text': content.get('text'),
        'entities': entities,
        'schema': content.get('schema', {}),
        'crawled_at': datetime.now().isoformat(),
    }

def _assess_quality(content: dict, entities: dict) -> str:
    text = content.get('text') or ''
    has_text = len(text.split()) >= 100
    has_entities = any(entities.get(k) for k in ['people', 'organizations'])
    has_meta = bool(content.get('title') and content.get('date_published'))

    if has_text and has_entities and has_meta:
        return 'high'
    elif has_text or has_entities:
        return 'medium'
    return 'low'
```

---

## Python Dependencies

```bash
pip install \
  requests \
  beautifulsoup4 \
  lxml html5lib \
  scrapy \
  playwright \
  trafilatura \
  pyyaml \
  python-dateutil

# Chromium browser for Playwright
playwright install chromium
```

| Library | Min version | Responsibility |
|---|---|---|
| `requests` | 2.31+ | Static HTTP, API calls |
| `beautifulsoup4` | 4.12+ | Tolerant HTML parsing |
| `lxml` | 4.9+ | Robust alternative parser |
| `html5lib` | 1.1+ | Ultra-tolerant parser (broken HTML) |
| `scrapy` | 2.11+ | Parallel crawling at scale |
| `playwright` | 1.40+ | JS/SPA rendering |
| `trafilatura` | 1.8+ | Article extraction (boilerplate removal) |
| `pyyaml` | 6.0+ | Declarative extraction config |
| `python-dateutil` | 2.9+ | Multi-format date parsing |

---

## Best Practices (DO)

- **Cascade methods:** always try lightest first (static -> playwright)
- **Incremental save:** save every 50 articles to avoid losing progress on crash
- **Resume mode:** check already-processed URLs before starting (`load_checkpoint`)
- **Rate limiting:** minimum 0.5s between requests on same domain; exponential backoff on failures
- **Document quality:** include `data_quality` and `method` in every result
- **Separation of concerns:** crawling -> cleaning -> entities (never all at once)
- **Declarative config:** use YAML for CSS selectors, not hard-coded Python
- **Graceful fallback:** if LLM fails, return empty structure with `error` field — never raise unhandled exceptions
- **Clean text for LLM:** always pass extracted and normalized text, never raw HTML

## Anti-Patterns (AVOID)

- Passing raw HTML to the LLM (wastes tokens, lower entity precision)
- Using only regex for entity extraction (fragile for natural text variations)
- Hard-coding CSS selectors in Python (sites change layouts frequently)
- Ignoring encoding (UTF-8 vs Latin-1 causes silent data corruption)
- Infinite retries (use exponential backoff with max attempt limit)
- Processing all pages before saving (risk of losing everything on crash)
- Mixing score scales without explicit normalization (e.g., 0-1 vs 0-100)
- Using `wait_until='load'` in Playwright for lazy content (use `'networkidle'`)

---

## Safety Rules

- NEVER scrape pages behind authentication without explicit user approval.
- ALWAYS respect `robots.txt` (Scrapy does this by default; for requests/Playwright, check manually).
- ALWAYS implement rate limiting — minimum 0.5s between requests to the same domain.
- NEVER store API keys in generated scripts — always use `os.environ.get()`.
- NEVER bypass hard paywalls — extract only publicly available content.
- For soft paywalls, only reveal content that was already sent to the client (DOM manipulation only, no server-side bypass).
