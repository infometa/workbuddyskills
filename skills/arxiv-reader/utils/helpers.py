"""Utility helpers for text processing, truncation, etc."""

import re
from datetime import date, timedelta


def sanitize_filename(title: str, max_len: int = 80) -> str:
    """Convert a paper title into a safe filename slug."""
    safe = re.sub(r"[^\w\s-]", "", title)
    safe = re.sub(r"\s+", "-", safe).strip("-")
    return safe[:max_len]


def truncate_text(text: str, max_chars: int = 60000) -> str:
    """Truncate text to fit within a character budget, keeping the beginning."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n...[内容因超出长度限制被截断]..."


def get_target_dates() -> list[date]:
    """Return today and yesterday as candidate dates."""
    today = date.today()
    return [today, today - timedelta(days=1)]


def extract_arxiv_id(entry_id: str) -> str:
    """Extract clean arxiv id from a full entry URL.
    e.g. 'http://arxiv.org/abs/2401.12345v1' -> '2401.12345'
    """
    raw = entry_id.rstrip("/").split("/")[-1]
    # Remove version suffix
    return re.sub(r"v\d+$", "", raw)
