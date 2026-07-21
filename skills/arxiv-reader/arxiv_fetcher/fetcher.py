"""
ArXiv Fetcher — fetch recent papers and their LaTeX source.

Strategy (in order):
  1. RSS feed   – fast, gives today's new listings directly
  2. arxiv API  – fallback, get the most recent N papers (no date filter)

Uses direct HTTP download for LaTeX source files.
"""

from __future__ import annotations

import gzip
import io
import re
import tarfile
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Optional

import arxiv
import requests

import config
from utils.helpers import extract_arxiv_id
from utils.logger import get_logger

logger = get_logger(__name__)

# arXiv RSS namespaces
_RSS_NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rss": "http://purl.org/rss/1.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "taxo": "http://purl.org/rss/1.0/modules/taxonomy/",
}


class ArxivFetcher:
    """Fetch paper listings and LaTeX source from arXiv."""

    def __init__(self):
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=3,
        )
        self.categories = config.ARXIV_CATEGORIES
        self.max_results = config.ARXIV_MAX_RESULTS

    # ── Paper listing ─────────────────────────────────────────

    def fetch_single_paper(self, arxiv_id_or_url: str) -> Optional[dict]:
        """
        Fetch a single paper by arxiv_id or URL.
        
        Parameters
        ----------
        arxiv_id_or_url : str
            Can be:
            - arxiv_id: "2401.12345"
            - abs URL: "https://arxiv.org/abs/2401.12345"
            - pdf URL: "https://arxiv.org/pdf/2401.12345.pdf"
        
        Returns
        -------
        dict or None
            Paper metadata dict, or None if not found.
        """
        # Extract arxiv_id from URL if needed
        arxiv_id = extract_arxiv_id(arxiv_id_or_url)
        if not arxiv_id:
            logger.error(f"Invalid arxiv_id or URL: {arxiv_id_or_url}")
            return None
        
        logger.info(f"Fetching single paper: {arxiv_id}")
        
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            results = list(self.client.results(search))
            
            if not results:
                logger.error(f"Paper not found: {arxiv_id}")
                return None
            
            paper = self._result_to_dict(results[0])
            logger.info(f"  Found: {paper['title'][:60]}...")
            return paper
            
        except Exception as e:
            logger.error(f"Failed to fetch {arxiv_id}: {e}")
            return None

    def fetch_papers(
        self,
        target_date: Optional[date] = None,
        is_known_fn: Optional[Callable[[str], bool]] = None,
    ) -> list[dict]:
        """
        Fetch recent papers from arXiv.

        Strategy:
        1. Try RSS feeds for each category (today's new listings).
        2. If RSS yields nothing, fall back to the arxiv API.

        Stop conditions (both RSS and API):
          - Paper already in DB (is_known_fn returns True) → stop / filter out
          - Paper older than (today - 1 day) → stop

        Parameters
        ----------
        target_date : date, optional
            Unused currently but kept for interface compatibility.
        is_known_fn : callable, optional
            Function that takes an arxiv_id and returns True if the
            paper is already tracked in the local DB.
        """
        # ── Method 1: RSS feeds ──
        logger.info(
            f"Fetching papers via RSS from [{', '.join(self.categories)}] ..."
        )
        papers = self._fetch_via_rss()
        if papers:
            # Dedup by arxiv_id (a paper can appear in multiple category feeds)
            papers = self._dedup_papers(papers)
            logger.info(f"RSS: got {len(papers)} unique papers")

            # Filter out papers already in DB
            if is_known_fn:
                before = len(papers)
                papers = [p for p in papers if not is_known_fn(p["arxiv_id"])]
                skipped = before - len(papers)
                if skipped:
                    logger.info(
                        f"  RSS: filtered out {skipped} papers already in DB, "
                        f"{len(papers)} new papers remaining"
                    )

            if self.max_results and len(papers) > self.max_results:
                papers = papers[: self.max_results]
            return papers

        # ── Method 2: arxiv API (fallback) ──
        logger.info("RSS returned nothing, falling back to arxiv API ...")
        return self._fetch_via_api(is_known_fn=is_known_fn)

    # ── RSS fetching ──────────────────────────────────────────

    def _fetch_via_rss(self) -> list[dict]:
        """Fetch today's new papers from arXiv RSS feeds."""
        all_papers: list[dict] = []

        for cat in self.categories:
            url = f"https://rss.arxiv.org/rss/{cat}"
            logger.info(f"  RSS: {url}")
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                papers = self._parse_rss(resp.text, cat)
                all_papers.extend(papers)
                logger.info(f"    → {len(papers)} papers from {cat}")
            except Exception as e:
                logger.warning(f"  RSS failed for {cat}: {e}")

        return all_papers

    def _parse_rss(self, xml_text: str, category: str) -> list[dict]:
        """Parse an arXiv RSS feed XML into paper dicts."""
        papers: list[dict] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.warning(f"  RSS XML parse error: {e}")
            return papers

        # arXiv RSS uses RDF/RSS 1.0 format
        items = root.findall(".//rss:item", _RSS_NS)
        if not items:
            # Try plain RSS 2.0 fallback
            items = root.findall(".//item")

        for item in items:
            paper = self._rss_item_to_dict(item, category)
            if paper:
                papers.append(paper)

        return papers

    def _rss_item_to_dict(self, item: ET.Element, default_cat: str) -> Optional[dict]:
        """Convert a single RSS <item> to our paper dict."""
        # Try RDF namespace first, then plain
        title_el = item.find("rss:title", _RSS_NS) or item.find("title")
        link_el = item.find("rss:link", _RSS_NS) or item.find("link")
        desc_el = item.find("rss:description", _RSS_NS) or item.find("description")
        creator_el = item.find("dc:creator", _RSS_NS)

        if title_el is None or link_el is None:
            return None

        raw_title = (title_el.text or "").strip()
        link = (link_el.text or "").strip()
        raw_desc = (desc_el.text or "").strip() if desc_el is not None else ""

        # Skip "UPDATED" entries, focus on new submissions
        # arXiv RSS titles look like: "Title (arXiv:2401.12345v1 [cs.AI])"
        # or sometimes: "Title. (arXiv:2401.12345v1 [cs.AI] UPDATED)"
        is_updated = "UPDATED" in raw_title

        # Extract arxiv ID from link: https://arxiv.org/abs/2401.12345
        arxiv_id = extract_arxiv_id(link) if link else ""
        if not arxiv_id:
            return None

        # Clean title: remove the trailing "(arXiv:...)" part
        title = re.sub(r"\s*\(arXiv:[^)]+\)\s*$", "", raw_title).strip()
        title = re.sub(r"\.\s*$", "", title)  # remove trailing period

        # Parse abstract from description (may contain HTML)
        abstract = self._clean_html(raw_desc)
        # arXiv RSS description often starts with "<p>Abstract: ..."
        abstract = re.sub(r"^Abstract:\s*", "", abstract, flags=re.IGNORECASE).strip()

        # Parse authors
        authors: list[str] = []
        if creator_el is not None and creator_el.text:
            # Format: "<a href='...'>Author1</a>, <a href='...'>Author2</a>"
            author_text = self._clean_html(creator_el.text)
            authors = [a.strip() for a in author_text.split(",") if a.strip()]

        # Extract categories from title bracket part
        cat_match = re.search(r"\[([^\]]+)\]", raw_title)
        categories = (
            [c.strip() for c in cat_match.group(1).split(",")]
            if cat_match
            else [default_cat]
        )

        return {
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "categories": categories,
            "published": date.today(),
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
            "is_updated": is_updated,
        }

    # ── API fallback ──────────────────────────────────────────

    def _fetch_via_api(
        self, is_known_fn: Optional[Callable[[str], bool]] = None,
    ) -> list[dict]:
        """
        Fallback: fetch most recent papers via the arxiv API.

        Papers are sorted newest-first. Early-stop when:
          1. Paper already in local DB → all older papers should also be known
          2. Paper published before yesterday → we only care about today + yesterday
        """
        cat_query = " OR ".join(f"cat:{cat}" for cat in self.categories)
        search = arxiv.Search(
            query=cat_query,
            max_results=self.max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        # Only look at today and yesterday (1 day lookback)
        cutoff_date = date.today() - timedelta(days=config.FETCH_LOOKBACK_DAYS)

        papers: list[dict] = []
        total_scanned = 0
        logger.info(
            f"  API: fetching up to {self.max_results} papers "
            f"(cutoff date: {cutoff_date}, stop on first known paper) ..."
        )

        for result in self.client.results(search):
            total_scanned += 1
            paper = self._result_to_dict(result)

            # ── Early stop 1: paper older than yesterday ──
            if paper["published"] < cutoff_date:
                logger.info(
                    f"  ■ Stop: reached paper from {paper['published']} "
                    f"(cutoff {cutoff_date}). Scanned {total_scanned}."
                )
                break

            # ── Early stop 2: paper already in DB → we've fetched up to here ──
            if is_known_fn and is_known_fn(paper["arxiv_id"]):
                logger.info(
                    f"  ■ Stop: paper {paper['arxiv_id']} already in DB. "
                    f"All older papers should be known too. Scanned {total_scanned}."
                )
                break

            papers.append(paper)
            if len(papers) >= self.max_results:
                break

        logger.info(f"  API: got {len(papers)} new papers (scanned {total_scanned})")
        return papers

    # ── LaTeX source fetching ─────────────────────────────────

    def fetch_latex_source(self, arxiv_id: str) -> Optional[str]:
        """
        Fetch the LaTeX source of a paper.

        1. Try `arxiv_to_prompt` library (if installed).
        2. Fall back to downloading the e-print tar/gz from arXiv.
        """
        # ── Method 1: arxiv_to_prompt ──
        try:
            from arxiv_to_prompt import process_latex_source

            logger.info(f"  Fetching source via arxiv_to_prompt: {arxiv_id}")
            return process_latex_source(arxiv_id, keep_comments=False)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"arxiv_to_prompt failed for {arxiv_id}: {e}")
        
        return None

    @staticmethod
    def _find_main_tex(tar: tarfile.TarFile) -> Optional[str]:
        """Find the main .tex file in a tar archive."""
        tex_files: list[tuple[str, str]] = []

        for member in tar.getmembers():
            if member.name.endswith(".tex") and not member.name.startswith("."):
                f = tar.extractfile(member)
                if f:
                    content = f.read().decode("utf-8", errors="ignore")
                    tex_files.append((member.name, content))

        if not tex_files:
            return None

        # Prefer the file containing \begin{document}
        for name, content in tex_files:
            if "\\begin{document}" in content:
                return content

        # Fall back to largest tex file
        tex_files.sort(key=lambda x: len(x[1]), reverse=True)
        return tex_files[0][1]

    @staticmethod
    def _result_to_dict(result: arxiv.Result) -> dict:
        """Convert an arxiv.Result to a plain dict."""
        return {
            "arxiv_id": extract_arxiv_id(result.entry_id),
            "title": result.title.replace("\n", " ").strip(),
            "abstract": result.summary.replace("\n", " ").strip(),
            "authors": [a.name for a in result.authors],
            "categories": list(result.categories),
            "published": result.published.date(),
            "pdf_url": result.pdf_url or "",
        }

    @staticmethod
    def _dedup_papers(papers: list[dict]) -> list[dict]:
        """Remove duplicate papers by arxiv_id, keeping the first."""
        seen: set[str] = set()
        unique: list[dict] = []
        for p in papers:
            if p["arxiv_id"] not in seen:
                seen.add(p["arxiv_id"])
                unique.append(p)
        return unique

    @staticmethod
    def _clean_html(text: str) -> str:
        """Strip HTML tags from text."""
        text = re.sub(r"<[^>]+>", "", text)
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&quot;", '"').replace("&#39;", "'")
        return text.strip()
