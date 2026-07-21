#!/usr/bin/env python3
"""
Content Attack Brief Generator

Synthesizes your content library, Ahrefs keyword data, GSC performance,
and competitor gaps into a weekly prioritized keyword brief.

Usage:
    # Set environment variables (see .env.example)
    python content_attack_brief.py

    # Or export inline
    AHREFS_TOKEN="..." YOUR_DOMAIN="example.com" python content_attack_brief.py
"""

import json
import os
import sys
import re
import glob
import importlib.util
import math
import requests
from datetime import datetime, timedelta, date
from collections import Counter, defaultdict
from pathlib import Path

# ─────────────────────────────────────────────
# Config (all from environment variables)
# ─────────────────────────────────────────────
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONTENT_DIR = Path(os.environ.get("CONTENT_DIR", "./content"))
# Directory containing your content files (markdown, JSON atoms, etc.)

AHREFS_TOKEN = os.environ.get("AHREFS_TOKEN", "")
AHREFS_BASE = "https://api.ahrefs.com/v3"
AHREFS_HEADERS = lambda: {"Authorization": f"Bearer {AHREFS_TOKEN}"}

YOUR_DOMAIN = os.environ.get("YOUR_DOMAIN", "example.com")
COMPETITORS = [c.strip() for c in os.environ.get("COMPETITORS", "").split(",") if c.strip()]

# ─────────────────────────────────────────────
# 1. CONTENT FINGERPRINT
# ─────────────────────────────────────────────

STOPWORDS = {
    "the","a","an","is","are","was","were","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might","shall",
    "and","but","or","nor","for","yet","so","at","by","for","in","of","on","to",
    "with","as","that","this","these","those","it","its","i","we","you","they",
    "he","she","him","her","our","their","your","my","what","which","who","when",
    "where","how","not","all","also","more","very","just","from","about","into",
    "than","then","there","so","up","out","if","no","can","one","time","like",
    "get","got","use","used","make","made","work","well","way","new","good",
    "go","going","know","think","want","need","see","look","come","give",
    "take","say","even","most","much","such","here","now","over","any","some",
    "them","us","first","two","other","his","her","its",
}

# Customize these topic keywords to match your content verticals
TOPIC_KEYWORDS = {
    "AI agents": ["ai agent", "ai agents", "agent fleet", "autonomous agent", "llm agent", "multi-agent"],
    "Claude/OpenAI": ["claude", "openai", "gpt", "anthropic", "gemini", "chatgpt"],
    "SEO/AEO": ["seo", "aeo", "search engine", "organic", "keyword", "serp", "ranking", "backlink", "gsc"],
    "Content marketing": ["content", "blog", "article", "post", "write", "writing", "publishing"],
    "Marketing agency": ["agency", "client", "service", "campaign", "marketing"],
    "Lead generation": ["lead gen", "leads", "pipeline", "outbound", "inbound", "funnel", "prospect"],
    "AI automation": ["automation", "automate", "automated", "workflow", "script", "cron", "pipeline"],
    "Revenue/ROI": ["revenue", "roi", "growth", "profit", "income", "mrr", "arr", "monetize"],
    "Sales": ["sales", "deal", "close", "outreach", "cold email", "crm"],
    "Social media": ["instagram", "tiktok", "youtube", "twitter", "linkedin", "social media", "viral"],
    "B2B SaaS": ["saas", "b2b", "software", "product", "platform"],
    "Strategy": ["strategy", "strategic", "plan", "roadmap", "framework", "playbook"],
    "Analytics/Data": ["analytics", "data", "metrics", "kpi", "ga4", "mixpanel", "dashboard"],
}

# Override with environment variable if set (JSON format)
_custom_topics = os.environ.get("TOPIC_KEYWORDS_JSON")
if _custom_topics:
    try:
        TOPIC_KEYWORDS = json.loads(_custom_topics)
    except json.JSONDecodeError:
        print("  [WARN] Invalid TOPIC_KEYWORDS_JSON, using defaults", file=sys.stderr)


def extract_fingerprint():
    """Read content files from CONTENT_DIR, count topic frequencies."""
    topic_counts = Counter()
    phrase_counts = Counter()

    # Load JSON content atoms (if available)
    atom_files = sorted(glob.glob(str(CONTENT_DIR / "content-atoms-*.json")))
    if atom_files:
        latest = atom_files[-1]
        try:
            with open(latest) as f:
                d = json.load(f)
            atoms = d.get("atoms", [])
            for atom in atoms:
                text = (atom.get("content", "") + " " + " ".join(atom.get("tags", []))).lower()
                _score_text(text, topic_counts, phrase_counts)
        except Exception as e:
            print(f"  [WARN] Content atoms load error: {e}", file=sys.stderr)

    # Load markdown files (last 30 days by filename prefix)
    cutoff = date.today() - timedelta(days=30)
    if CONTENT_DIR.exists():
        for f in sorted(CONTENT_DIR.glob("**/*.md")):
            m = re.match(r"(\d{4}-\d{2}-\d{2})", f.name)
            if m:
                try:
                    file_date = date.fromisoformat(m.group(1))
                    if file_date < cutoff:
                        continue
                except ValueError:
                    pass
            try:
                text = f.read_text(errors="ignore").lower()
                _score_text(text, topic_counts, phrase_counts)
            except Exception:
                pass

    return topic_counts, phrase_counts


def _score_text(text, topic_counts, phrase_counts):
    """Score text against topic keywords and count phrase frequencies."""
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            count = text.count(kw)
            if count > 0:
                topic_counts[topic] += count

    # Count meaningful 2-3 word phrases
    words = re.findall(r'\b[a-z][a-z\-]{2,}\b', text)
    words = [w for w in words if w not in STOPWORDS and len(w) > 3]
    for i in range(len(words)-1):
        bigram = f"{words[i]} {words[i+1]}"
        phrase_counts[bigram] += 1
        if i < len(words)-2:
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            phrase_counts[trigram] += 1


# ─────────────────────────────────────────────
# 2. KEYWORD SEEDS from fingerprint
# ─────────────────────────────────────────────

# Map topics to seed keywords for Ahrefs research
# Customize these for your industry/niche
TOPIC_TO_SEEDS = {
    "AI agents": [
        "ai agents for marketing", "ai agent platform", "marketing ai agents",
        "ai agents b2b", "autonomous ai agents", "ai agent tools",
        "build ai agents", "ai agents for business",
    ],
    "Claude/OpenAI": [
        "claude ai for business", "openai for marketing", "chatgpt marketing",
        "gpt for content marketing", "ai writing tools",
    ],
    "SEO/AEO": [
        "seo agency", "ai seo tools", "seo for ai", "aeo optimization",
        "answer engine optimization", "seo content strategy", "technical seo services",
        "seo reporting tools", "enterprise seo agency",
    ],
    "Content marketing": [
        "content marketing agency", "content marketing strategy", "b2b content marketing",
        "content marketing roi", "content marketing tools", "ai content marketing",
        "content marketing services", "content strategy agency",
    ],
    "Marketing agency": [
        "digital marketing agency", "performance marketing agency", "b2b marketing agency",
        "marketing agency pricing", "hire marketing agency", "marketing agency services",
        "best marketing agencies", "saas marketing agency",
    ],
    "Lead generation": [
        "b2b lead generation", "lead generation agency", "lead generation strategy",
        "b2b lead gen tools", "outbound lead generation", "lead generation services",
        "demand generation agency", "lead generation for saas",
    ],
    "AI automation": [
        "marketing automation ai", "ai workflow automation", "automate marketing tasks",
        "ai marketing automation tools", "marketing automation platform",
    ],
    "Revenue/ROI": [
        "marketing roi", "content marketing roi", "seo roi", "digital marketing roi",
        "revenue driven marketing", "roi tracking marketing",
    ],
    "Sales": [
        "ai sales tools", "sales automation software", "cold email software",
        "outbound sales automation", "ai cold email", "sales engagement platform",
    ],
    "B2B SaaS": [
        "saas marketing agency", "b2b saas marketing", "saas seo strategy",
        "saas content marketing", "saas growth marketing",
    ],
    "Analytics/Data": [
        "marketing analytics tools", "seo analytics platform", "content analytics",
        "marketing data analytics",
    ],
    "Strategy": [
        "digital marketing strategy", "content strategy consulting",
        "marketing strategy agency", "growth strategy consulting",
    ],
}

# Override with environment variable if set (JSON format)
_custom_seeds = os.environ.get("TOPIC_TO_SEEDS_JSON")
if _custom_seeds:
    try:
        TOPIC_TO_SEEDS = json.loads(_custom_seeds)
    except json.JSONDecodeError:
        print("  [WARN] Invalid TOPIC_TO_SEEDS_JSON, using defaults", file=sys.stderr)


def derive_seeds(topic_counts):
    """Return ranked list of keyword seeds based on topic frequency."""
    seeds = []
    seen = set()
    for topic, _ in topic_counts.most_common():
        for seed in TOPIC_TO_SEEDS.get(topic, []):
            if seed not in seen:
                seeds.append(seed)
                seen.add(seed)
    # Add fallback seeds
    fallbacks = [
        "ai marketing", "seo services", "content marketing",
        "digital marketing agency", "marketing automation",
        "b2b lead generation", "marketing strategy",
    ]
    for s in fallbacks:
        if s not in seen:
            seeds.append(s)
            seen.add(s)
    return seeds[:150]


# ─────────────────────────────────────────────
# 3. AHREFS KEYWORDS EXPLORER
# ─────────────────────────────────────────────

def fetch_ahrefs_keywords(seeds):
    """Pull Ahrefs Keywords Explorer data in batches of 50."""
    if not AHREFS_TOKEN:
        print("  [WARN] No AHREFS_TOKEN — skipping keyword data", file=sys.stderr)
        return {}

    results = {}
    today = date.today()
    date_to = today.replace(day=1) - timedelta(days=1)
    date_from = (date_to.replace(day=1) - timedelta(days=335)).replace(day=1)

    batch_size = 50
    for i in range(0, len(seeds), batch_size):
        batch = seeds[i:i+batch_size]
        try:
            import urllib.parse
            qs = urllib.parse.urlencode({
                "country": "us",
                "keywords": ",".join(batch),
                "select": "keyword,volume,difficulty,cpc,traffic_potential,intents,volume_monthly_history",
                "volume_monthly_date_from": date_from.strftime("%Y-%m-%d"),
                "volume_monthly_date_to": date_to.strftime("%Y-%m-%d"),
            })
            resp = requests.get(
                f"{AHREFS_BASE}/keywords-explorer/overview?{qs}",
                headers=AHREFS_HEADERS(),
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                for kw_data in data.get("keywords", []):
                    kw = kw_data.get("keyword", "").lower()
                    if kw:
                        if "difficulty" in kw_data and "keyword_difficulty" not in kw_data:
                            kw_data["keyword_difficulty"] = kw_data["difficulty"]
                        intents = kw_data.get("intents", {})
                        if isinstance(intents, dict):
                            kw_data["is_commercial"] = intents.get("commercial", False)
                            kw_data["is_transactional"] = intents.get("transactional", False)
                        results[kw] = kw_data
            else:
                print(f"  [WARN] Ahrefs keywords batch {i//batch_size+1}: HTTP {resp.status_code}", file=sys.stderr)
        except Exception as e:
            print(f"  [WARN] Ahrefs keywords batch error: {e}", file=sys.stderr)

    return results


# ─────────────────────────────────────────────
# 4. AHREFS ORGANIC KEYWORDS
# ─────────────────────────────────────────────

def fetch_organic_keywords(domain, limit=1000):
    """Pull Ahrefs organic keywords for a domain."""
    if not AHREFS_TOKEN:
        return []

    today = date.today()
    first_of_month = today.replace(day=1).strftime("%Y-%m-%d")

    try:
        resp = requests.get(
            f"{AHREFS_BASE}/site-explorer/organic-keywords",
            headers=AHREFS_HEADERS(),
            params={
                "target": domain,
                "country": "us",
                "date": first_of_month,
                "select": "keyword,volume,best_position,keyword_difficulty,sum_traffic,is_commercial,is_transactional,best_position_url",
                "order_by": "volume:desc",
                "limit": limit,
                "mode": "subdomains",
            },
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json().get("keywords", [])
        else:
            print(f"  [WARN] Ahrefs organic {domain}: HTTP {resp.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"  [WARN] Ahrefs organic {domain} error: {e}", file=sys.stderr)
    return []


# ─────────────────────────────────────────────
# 5. COMPETITOR GAP ANALYSIS
# ─────────────────────────────────────────────

# Terms that indicate keywords are relevant to your business
# Customize this set for your niche
RELEVANT_TERMS = {
    "marketing","seo","content","agency","digital","growth","lead","analytics",
    "advertising","social","email","conversion","b2b","saas","strategy","ai",
    "search","traffic","keyword","backlink","campaign","funnel","inbound",
    "outbound","automation","crm","ppc","sem","cro","optimization",
    "brand","performance","demand","revenue","roi","reporting","tools",
    "software","platform","services","hire","consultant","pricing","best",
    "vs","alternative","guide","how to","enterprise","startup","ecommerce",
    "agent","aeo","answer engine","generative engine",
}

# Keywords to block from competitor gap results (noise)
GAP_BLOCKLIST = {
    "photo search","reverse video","image search","reverse image",
    "paragraph generator","paragraph writer","paragraph rewriter",
    "sentence rewriter","text rewriter","text humanizer","ai rewrite",
    "rewording tool","reword ai","paraphrasing tool","essay writer",
    "grammar checker","spell checker","word counter","character counter",
    "reviews","review","coupon","promo code","login","sign up","free trial",
    "what is","definition of","wikipedia",
}


def is_relevant_keyword(kw):
    """Check if a keyword is relevant to your business."""
    kw_lower = kw.lower()
    if not any(term in kw_lower for term in RELEVANT_TERMS):
        return False
    if any(blocked in kw_lower for blocked in GAP_BLOCKLIST):
        return False
    return True


def find_competitor_gaps(my_keywords, competitor_data):
    """Find keywords where competitors rank top 20 but you don't rank or rank >50."""
    my_positions = {}
    for item in my_keywords:
        kw = item.get("keyword", "").lower()
        pos = item.get("best_position", 999)
        my_positions[kw] = pos

    gaps = []
    seen_kws = set()

    for comp_domain, comp_keywords in competitor_data.items():
        for item in comp_keywords:
            kw = item.get("keyword", "").lower()
            if not kw or kw in seen_kws:
                continue
            if not is_relevant_keyword(kw):
                continue

            comp_pos = item.get("best_position", 999)
            my_pos = my_positions.get(kw, 999)

            if comp_pos <= 20 and my_pos > 50:
                seen_kws.add(kw)
                gaps.append({
                    "keyword": kw,
                    "volume": item.get("volume", 0),
                    "kd": item.get("keyword_difficulty", 0),
                    "competitor": comp_domain,
                    "comp_pos": comp_pos,
                    "your_pos": my_pos,
                    "is_commercial": item.get("is_commercial", False),
                    "is_transactional": item.get("is_transactional", False),
                })

    gaps.sort(key=lambda x: x.get("volume", 0), reverse=True)
    return gaps


# ─────────────────────────────────────────────
# 6. GSC DATA
# ─────────────────────────────────────────────

def fetch_gsc_data():
    """Import gsc_client and pull 28d + 90d query data."""
    try:
        # Try importing from same directory
        script_dir = Path(__file__).resolve().parent
        spec = importlib.util.spec_from_file_location("gsc_client", str(script_dir / "gsc_client.py"))
        gsc_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gsc_mod)
        gsc = gsc_mod.GSCClient()

        rows_28 = gsc.query(dimensions=["query"], row_limit=1000, days=28)
        rows_90 = gsc.query(dimensions=["query"], row_limit=1000, days=90)

        return rows_28, rows_90
    except Exception as e:
        print(f"  [WARN] GSC error: {e}", file=sys.stderr)
        return [], []


def find_decaying_pages(rows_28, rows_90):
    """Find queries that lost >30% clicks in 28d vs 90d per-day average."""
    clicks_28 = {}
    for row in rows_28:
        keys = row.get("keys", [])
        if keys:
            clicks_28[keys[0].lower()] = row.get("clicks", 0)

    clicks_90_norm = {}
    for row in rows_90:
        keys = row.get("keys", [])
        if keys:
            clicks_90_norm[keys[0].lower()] = row.get("clicks", 0) * (28 / 90)

    decaying = []
    for kw, c28 in clicks_28.items():
        c90 = clicks_90_norm.get(kw, 0)
        if c90 > 5:
            if c28 < c90 * 0.7:
                pct_loss = (c90 - c28) / c90 * 100
                decaying.append({
                    "keyword": kw,
                    "clicks_28d": round(c28),
                    "clicks_90d_avg": round(c90),
                    "pct_loss": round(pct_loss, 1),
                })

    decaying.sort(key=lambda x: x.get("pct_loss", 0), reverse=True)
    return decaying


# ─────────────────────────────────────────────
# 7 & 8. SCORING + TREND
# ─────────────────────────────────────────────

def compute_trend(history):
    """Compare first 3 months avg to last 3 months avg from volume_monthly_history."""
    if not history or len(history) < 3:
        return 0.0, "→ Stable"

    volumes = []
    try:
        if isinstance(history[0], dict):
            sorted_h = sorted(history, key=lambda x: x.get("date", x.get("month", "")))
            volumes = [h.get("volume", h.get("search_volume", 0)) for h in sorted_h]
        else:
            volumes = [int(v) for v in history]
    except Exception:
        return 0.0, "→ Stable"

    if len(volumes) < 6:
        return 0.0, "→ Stable"

    early_avg = sum(volumes[:3]) / 3
    late_avg = sum(volumes[-3:]) / 3

    if early_avg == 0:
        pct = 100.0 if late_avg > 0 else 0.0
    else:
        pct = (late_avg - early_avg) / early_avg * 100

    if pct > 50:
        label = "🔥 Surging"
    elif pct > 20:
        label = "📈 Rising"
    elif pct > 5:
        label = "↗️ Growing"
    elif pct >= -5:
        label = "→ Stable"
    elif pct >= -20:
        label = "↘️ Declining"
    else:
        label = "📉 Falling"

    return round(pct, 1), label


def make_sparkline(history):
    """ASCII sparkline from volume history."""
    SPARKS = "▁▂▃▄▅▆▇█"
    if not history:
        return ""
    try:
        if isinstance(history[0], dict):
            sorted_h = sorted(history, key=lambda x: x.get("date", x.get("month", "")))
            volumes = [h.get("volume", h.get("search_volume", 0)) for h in sorted_h]
        else:
            volumes = [int(v) for v in history]
    except Exception:
        return ""

    if not volumes or max(volumes) == 0:
        return "▁" * min(len(volumes), 12)

    mn, mx = min(volumes), max(volumes)
    rng = mx - mn or 1
    return "".join(SPARKS[min(7, int((v - mn) / rng * 7))] for v in volumes[-12:])


def funnel_stage(kw, is_commercial=False, is_transactional=False):
    """Classify keyword into funnel stage."""
    kw_lower = kw.lower()
    bofu_terms = ["agency", "services", "hire", "pricing", "tools", "software",
                  "best", " vs ", "alternative", "platform", "cost", "price",
                  "company", "firms", "consultant", "consultancy", "outsource"]
    mofu_terms = ["how to", "guide", "strategy", "examples", "case study",
                  "roi", "tutorial", "template", "checklist", "tips", "framework",
                  "what is", "explained", "overview", "comparison"]

    if is_commercial or is_transactional:
        return "BOFU"
    if any(t in kw_lower for t in bofu_terms):
        return "BOFU"
    if any(t in kw_lower for t in mofu_terms):
        return "MOFU"
    return "TOFU"


def execution_path(kd, current_pos, volume=0):
    """Determine execution path based on difficulty and current ranking."""
    has_page = current_pos < 999
    if kd <= 20 and not has_page:
        return "🤖 AUTO — create new content"
    if has_page and kd <= 50:
        return "🤖 AUTO — refresh existing content"
    if kd <= 40:
        return "🤖+👤 SEMI — AI drafts, team reviews"
    if kd <= 60:
        return "👤+🤖 TEAM — writes content, AI optimizes"
    return "👤 TEAM — expert content + link building"


def score_keyword(kw_data, current_pos=999, topic_counts=None):
    """Score a keyword dict with Impact × Confidence."""
    volume = kw_data.get("volume", 0) or 0
    kd = kw_data.get("keyword_difficulty", kw_data.get("kd", 50)) or 50
    cpc = float(kw_data.get("cpc", 0) or 0)
    history = kw_data.get("volume_monthly_history", [])
    is_commercial = kw_data.get("is_commercial", False)
    is_transactional = kw_data.get("is_transactional", False)
    kw = kw_data.get("keyword", "").lower()

    trend_pct, trend_label = compute_trend(history)
    sparkline = make_sparkline(history)
    stage = funnel_stage(kw, is_commercial, is_transactional)

    # ── Impact (0-10) ──
    impact = 0
    if volume >= 10000:
        impact += 3
    elif volume >= 2000:
        impact += 2
    elif volume >= 500:
        impact += 1

    if cpc >= 15:
        impact += 3
    elif cpc >= 5:
        impact += 2
    elif cpc >= 1:
        impact += 1

    if stage == "BOFU":
        impact += 2
    elif stage == "MOFU":
        impact += 1

    if trend_pct > 50:
        impact += 2
    elif trend_pct > 20:
        impact += 1

    impact = min(10, impact)

    # ── Confidence (0-10) ──
    confidence = 0
    if kd <= 10:
        confidence += 4
    elif kd <= 20:
        confidence += 3
    elif kd <= 35:
        confidence += 2
    elif kd <= 50:
        confidence += 1

    if current_pos <= 10:
        confidence += 3
    elif current_pos <= 30:
        confidence += 2
    elif current_pos <= 50:
        confidence += 1

    # Topic authority: check if keyword topic appears in content fingerprint
    if topic_counts:
        for topic, cnt in topic_counts.items():
            topic_seeds = TOPIC_TO_SEEDS.get(topic, [])
            if any(seed.lower() in kw or kw in seed.lower() for seed in topic_seeds):
                if cnt > 5:
                    confidence += 2
                break

    confidence = min(10, confidence)

    priority = impact * confidence

    exec_path = execution_path(kd, current_pos, volume)

    return {
        "keyword": kw,
        "volume": volume,
        "kd": kd,
        "cpc": round(cpc, 2),
        "traffic_potential": kw_data.get("traffic_potential", 0),
        "current_pos": current_pos if current_pos < 999 else None,
        "stage": stage,
        "trend_pct": trend_pct,
        "trend_label": trend_label,
        "sparkline": sparkline,
        "impact": impact,
        "confidence": confidence,
        "priority": priority,
        "exec_path": exec_path,
        "is_commercial": is_commercial,
        "is_transactional": is_transactional,
    }


# ─────────────────────────────────────────────
# OUTPUT FORMATTING
# ─────────────────────────────────────────────

def fmt_vol(v):
    if not v:
        return "—"
    if v >= 1000000:
        return f"{v/1000000:.1f}M"
    if v >= 1000:
        return f"{v/1000:.1f}K"
    return str(v)

def fmt_pos(p):
    if p is None:
        return "—"
    return f"#{p}"

def fmt_kd(k):
    if k is None:
        return "—"
    if k <= 20:
        return f"KD{k}🟢"
    if k <= 40:
        return f"KD{k}🟡"
    if k <= 60:
        return f"KD{k}🟠"
    return f"KD{k}🔴"

def fmt_cpc(c):
    if not c:
        return "—"
    return f"${c:.2f}"

def print_kw_row(scored, idx=None):
    prefix = f"  {idx:>2}. " if idx else "    "
    pos_str = fmt_pos(scored.get("current_pos"))
    trend = scored.get("trend_label", "→ Stable")
    spark = scored.get("sparkline", "")
    kw = scored.get("keyword", "")
    vol = fmt_vol(scored.get("volume"))
    kd = fmt_kd(scored.get("kd"))
    cpc = fmt_cpc(scored.get("cpc"))
    imp = scored.get("impact", 0)
    conf = scored.get("confidence", 0)
    pri = scored.get("priority", 0)
    stage = scored.get("stage", "TOFU")
    ep = scored.get("exec_path", "")

    print(f"{prefix}{kw}")
    print(f"       Vol:{vol}  {kd}  CPC:{cpc}  Pos:{pos_str}  [{stage}]")
    print(f"       Trend: {trend} {spark} ({scored.get('trend_pct', 0):+.0f}%)")
    print(f"       Impact:{imp}  Conf:{conf}  Priority:{pri}")
    print(f"       {ep}")
    print()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    today = date.today()
    week_str = today.strftime("%B %d, %Y")

    print("=" * 68)
    print(f"🎯 CONTENT ATTACK BRIEF — {YOUR_DOMAIN}")
    print("   Content Fingerprint × Ahrefs × GSC × Competitor Gaps")
    print(f"   Week of {week_str}")
    print("=" * 68)
    print()

    # ── Step 1: Topic fingerprint ──
    print("📡 Ingesting content library...", file=sys.stderr)
    topic_counts, phrase_counts = extract_fingerprint()

    print()
    print("🧬 TOPIC FINGERPRINT (30-day content)")
    print()
    if topic_counts:
        max_count = max(topic_counts.values())
        for topic, count in topic_counts.most_common(15):
            bar_len = max(1, int(count / max_count * 30))
            bar = "█" * bar_len
            print(f"   {topic:<25} {bar} {count}")
    else:
        print("   [No content found in CONTENT_DIR]")
    print()

    # ── Step 2: Seeds ──
    print("🔍 Deriving keyword seeds...", file=sys.stderr)
    seeds = derive_seeds(topic_counts)
    print(f"   Derived {len(seeds)} keyword seeds from topic fingerprint")
    print()

    # ── Step 3: Ahrefs keywords ──
    print("📊 Pulling Ahrefs keyword data...", file=sys.stderr)
    seeds_data = fetch_ahrefs_keywords(seeds)
    print(f"   Got data for {len(seeds_data)} keywords", file=sys.stderr)

    # ── Step 4: Your organic keywords ──
    print(f"🌐 Pulling {YOUR_DOMAIN} organic keywords...", file=sys.stderr)
    my_keywords = fetch_organic_keywords(YOUR_DOMAIN, limit=1000)
    print(f"   Got {len(my_keywords)} organic keywords", file=sys.stderr)

    my_positions = {}
    my_kw_data = {}
    for item in my_keywords:
        kw = item.get("keyword", "").lower()
        my_positions[kw] = item.get("best_position", 999)
        my_kw_data[kw] = item

    # ── Step 5: Competitor gaps ──
    competitor_gaps = []
    if COMPETITORS:
        print("🕵️ Pulling competitor keywords...", file=sys.stderr)
        competitor_data = {}
        for comp in COMPETITORS:
            print(f"   {comp}...", file=sys.stderr)
            competitor_data[comp] = fetch_organic_keywords(comp, limit=200)
        competitor_gaps = find_competitor_gaps(my_keywords, competitor_data)
        print(f"   Found {len(competitor_gaps)} competitor gap keywords", file=sys.stderr)

    # ── Step 6: GSC data ──
    print("📈 Pulling GSC data...", file=sys.stderr)
    rows_28, rows_90 = fetch_gsc_data()
    print(f"   GSC 28d: {len(rows_28)} queries, 90d: {len(rows_90)} queries", file=sys.stderr)
    decaying = find_decaying_pages(rows_28, rows_90)

    # ── Step 7: Score all keywords ──
    print("⚡ Scoring keywords...", file=sys.stderr)
    all_scored = []

    for kw, data in seeds_data.items():
        pos = my_positions.get(kw, 999)
        scored = score_keyword(data, current_pos=pos, topic_counts=topic_counts)
        all_scored.append(scored)

    for item in my_keywords:
        kw = item.get("keyword", "").lower()
        if kw not in seeds_data:
            pos = item.get("best_position", 999)
            scored = score_keyword(
                {
                    "keyword": kw,
                    "volume": item.get("volume", 0),
                    "keyword_difficulty": item.get("keyword_difficulty", 50),
                    "cpc": 0,
                    "is_commercial": item.get("is_commercial", False),
                    "is_transactional": item.get("is_transactional", False),
                },
                current_pos=pos,
                topic_counts=topic_counts,
            )
            all_scored.append(scored)

    # Deduplicate
    seen_kws = set()
    deduped = []
    for s in sorted(all_scored, key=lambda x: x["priority"], reverse=True):
        if s["keyword"] not in seen_kws:
            seen_kws.add(s["keyword"])
            deduped.append(s)
    all_scored = deduped

    # ── BOFU: Money Keywords ──
    bofu = [s for s in all_scored if s["stage"] == "BOFU"]
    bofu.sort(key=lambda x: x["priority"], reverse=True)

    print("💰 BOFU: MONEY KEYWORDS (top 12)")
    print()
    for i, s in enumerate(bofu[:12], 1):
        print_kw_row(s, i)

    # ── Trending ──
    trending = sorted(all_scored, key=lambda x: x.get("trend_pct", 0), reverse=True)
    trending = [t for t in trending if t.get("trend_pct", 0) > 5]

    print("🔥 TRENDING: Fastest-growing (top 10)")
    print()
    for i, s in enumerate(trending[:10], 1):
        print_kw_row(s, i)

    # ── Competitor Gaps ──
    if competitor_gaps:
        print("🕳️  COMPETITOR GAP (top 15 relevant)")
        print()
        for i, gap in enumerate(competitor_gaps[:15], 1):
            vol = fmt_vol(gap.get("volume", 0))
            kd = fmt_kd(gap.get("kd", 0))
            comp = gap.get("competitor", "")
            comp_pos = gap.get("comp_pos", "?")
            your_pos = gap.get("your_pos", 999)
            your_pos_str = "not ranking" if your_pos >= 999 else f"#{your_pos}"
            stage = funnel_stage(gap["keyword"], gap.get("is_commercial", False), gap.get("is_transactional", False))
            ep = execution_path(gap.get("kd", 50), your_pos)
            print(f"  {i:>2}. {gap['keyword']}")
            print(f"       Vol:{vol}  {kd}  [{stage}]  {comp} #{comp_pos}  You:{your_pos_str}")
            print(f"       {ep}")
            print()

    # ── Decay Alert ──
    print("📉 DECAY ALERT: Pages losing traffic (top 10)")
    print()
    if decaying:
        for i, d in enumerate(decaying[:10], 1):
            kw = d["keyword"]
            c28 = d["clicks_28d"]
            c90 = d["clicks_90d_avg"]
            loss = d["pct_loss"]
            pos = my_positions.get(kw)
            pos_str = fmt_pos(pos) if pos and pos < 999 else "?"
            print(f"  {i:>2}. {kw}")
            print(f"       28d clicks: {c28}  90d avg: {c90}  Loss: {loss:.0f}%  Pos: {pos_str}")
            print()
    else:
        print("  No significant decay detected (GSC may be unavailable)")
        print()

    # ── Execution Pipeline ──
    print("⚡ EXECUTION PIPELINE (crawl → walk → run)")
    print()
    pipeline = defaultdict(list)
    for s in all_scored:
        pipeline[s["exec_path"]].append(s)

    order = [
        "🤖 AUTO — create new content",
        "🤖 AUTO — refresh existing content",
        "🤖+👤 SEMI — AI drafts, team reviews",
        "👤+🤖 TEAM — writes content, AI optimizes",
        "👤 TEAM — expert content + link building",
    ]
    for path in order:
        items = pipeline.get(path, [])
        if not items:
            continue
        print(f"  {path} ({len(items)} keywords)")
        top = sorted(items, key=lambda x: x["priority"], reverse=True)[:5]
        for kw_item in top:
            vol = fmt_vol(kw_item["volume"])
            kd = kw_item["kd"]
            pri = kw_item["priority"]
            print(f"    • {kw_item['keyword']}  Vol:{vol}  KD:{kd}  Pri:{pri}")
        print()

    # ── Summary ──
    print("📊 SUMMARY")
    print()
    bofu_count = len([s for s in all_scored if s["stage"] == "BOFU"])
    mofu_count = len([s for s in all_scored if s["stage"] == "MOFU"])
    tofu_count = len([s for s in all_scored if s["stage"] == "TOFU"])
    auto_count = len(pipeline.get("🤖 AUTO — create new content", []))
    refresh_count = len(pipeline.get("🤖 AUTO — refresh existing content", []))
    surging = [s for s in all_scored if "Surging" in s.get("trend_label", "")]

    print(f"   Keywords analyzed:    {len(all_scored)}")
    print(f"   Competitor gaps:      {len(competitor_gaps)}")
    print(f"   Decaying pages:       {len(decaying)}")
    print(f"   BOFU / MOFU / TOFU:   {bofu_count} / {mofu_count} / {tofu_count}")
    print(f"   Auto-create ready:    {auto_count}")
    print(f"   Auto-refresh ready:   {refresh_count}")
    print(f"   Surging keywords:     {len(surging)}")
    print(f"   Top topics covered:   {', '.join(t for t, _ in topic_counts.most_common(5))}")
    print()
    print("=" * 68)

    # ── Save JSON ──
    json_output = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "week_of": week_str,
        "domain": YOUR_DOMAIN,
        "topic_fingerprint": dict(topic_counts.most_common(20)),
        "all_keywords": all_scored,
        "competitor_gaps": competitor_gaps[:30],
        "decaying_pages": decaying[:20],
        "summary": {
            "total_keywords": len(all_scored),
            "competitor_gaps": len(competitor_gaps),
            "decaying_pages": len(decaying),
            "bofu": bofu_count,
            "mofu": mofu_count,
            "tofu": tofu_count,
            "auto_create": auto_count,
            "auto_refresh": refresh_count,
            "surging": len(surging),
        },
    }

    output_path = OUTPUT_DIR / "content-attack-brief-latest.json"
    output_path.write_text(json.dumps(json_output, indent=2))
    print(f"\n✅ JSON saved to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
