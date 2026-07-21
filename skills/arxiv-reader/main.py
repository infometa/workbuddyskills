#!/usr/bin/env python3
"""Single arXiv paper reader entrypoint.

Usage:
    python main.py --list
    python main.py --arxiv-id 2401.12345
    python main.py --arxiv-id https://arxiv.org/abs/2401.12345
    python main.py --arxiv-id 2401.12345 --category rag_and_retrieval
"""

from __future__ import annotations

import argparse
import sys

# Ensure project root is on sys.path
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from arxiv_fetcher.fetcher import ArxivFetcher
from skills.loader import load_all_skills
from agents.classifier_agent import ClassifierAgent
from agents.reader_agent import ReaderAgent
from agents.summary_agent import SummaryAgent
from paper_reader.latex_parser import parse_latex
from utils.logger import get_logger

logger = get_logger("daily-arxiv")


def process_single_paper(arxiv_id_or_url: str, category: str | None = None) -> str:
    """Read one paper and return raw markdown text."""
    logger.info("=" * 60)
    logger.info("Single Paper Mode")
    logger.info("=" * 60)

    skills = load_all_skills()
    if not skills:
        raise RuntimeError("No skills loaded. Please check the skills/ directory.")

    fetcher = ArxivFetcher()

    logger.info(f"Fetching paper: {arxiv_id_or_url}")
    paper = fetcher.fetch_single_paper(arxiv_id_or_url)
    if not paper:
        raise RuntimeError("Failed to fetch paper.")

    selected_category = category
    if selected_category is None:
        classifier = ClassifierAgent(skills)
        selected_category = classifier.classify(paper["title"], paper.get("abstract", ""))

    if selected_category not in skills:
        valid = ", ".join(sorted(skills.keys()))
        raise ValueError(f"Unknown category '{selected_category}'. Available: {valid}")

    # Build agents
    reader_agents: dict[str, ReaderAgent] = {}
    for skill_name, skill_config in skills.items():
        if skill_name != "general":
            reader_agents[skill_name] = ReaderAgent(skill_name, skill_config)
    summary_agent = SummaryAgent(skills.get("general", {"reading_prompt": ""}))

    logger.info(f"Processing as category: {selected_category}")

    if selected_category != "general" and selected_category in reader_agents:
        notes = _deep_read(
            fetcher,
            reader_agents[selected_category],
            paper,
            summary_agent,
        )
        return notes

    return summary_agent.summarize(paper)


def _deep_read(
    fetcher: ArxivFetcher,
    reader: ReaderAgent,
    paper: dict,
    fallback_agent: SummaryAgent,
 ) -> str:
    """
    Attempt deep two-pass reading.
    """
    arxiv_id = paper["arxiv_id"]

    # Fetch LaTeX source
    latex_source = fetcher.fetch_latex_source(arxiv_id)
    if not latex_source:
        logger.warning(f"  No LaTeX source for {arxiv_id}, falling back to summary.")
        return fallback_agent.summarize(paper)

    # Parse LaTeX
    parsed = parse_latex(latex_source)

    if not parsed.abstract and not parsed.sections:
        logger.warning(f"  LaTeX parsing yielded nothing for {arxiv_id}, falling back.")
        return fallback_agent.summarize(paper)

    # Two-pass reading
    return reader.read_paper(paper, parsed)


# ── CLI ───────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Single arXiv paper reader"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available paper categories (skills)",
    )
    parser.add_argument(
        "--arxiv-id",
        type=str,
        default=None,
        help="Read a single paper by arXiv ID or URL",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Optional: force a specific category (skill folder name)",
    )
    args = parser.parse_args()

    skills = load_all_skills()

    if args.list:
        for name in sorted(skills.keys()):
            print(name)
        return

    if not args.arxiv_id:
        parser.error("--arxiv-id is required unless --list is used")

    notes = process_single_paper(args.arxiv_id, category=args.category)
    print(notes)


if __name__ == "__main__":
    main()
