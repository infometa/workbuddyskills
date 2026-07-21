"""
Reader Agent — performs two-pass deep reading of a full paper.

Pass 1: Abstract + Introduction + Preliminaries + Contributions + Limitations
         → initial summary
Pass 2: Initial summary + main body (excluding refs/appendix/Pass-1 sections)
         → detailed notes, plus a decision on whether to read the appendix
Pass 3 (optional): Previous notes + appendix → updated notes
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from agents.base_agent import create_agent
import config
from paper_reader.latex_parser import ParsedPaper
from utils.helpers import truncate_text
from utils.logger import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = config.PROJECT_ROOT / "prompts"


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


# ── Prompt templates ──────────────────────────────────────────

READER_SYSTEM_PROMPT = _load_prompt("reader_system.md")
FIRST_PASS_USER = _load_prompt("reader_first_pass_user.md")
SECOND_PASS_USER = _load_prompt("reader_second_pass_user.md")
APPENDIX_PASS_USER = _load_prompt("reader_appendix_pass_user.md")


class ReaderAgent:
    """Two-pass deep reading agent for a specific skill category."""

    def __init__(self, skill_name: str, skill_config: Dict[str, Any]):
        self.skill_name = skill_name
        self.reading_prompt = skill_config.get("reading_prompt", "")
        system_prompt = READER_SYSTEM_PROMPT.format(
            reading_prompt=self.reading_prompt
        )
        self.chain = create_agent(system_prompt, max_tokens=16000)

    # ------------------------------------------------------------------

    def read_paper(
        self, paper_info: dict, parsed_paper: ParsedPaper
    ) -> str:
        """
        Execute the full reading pipeline and return Markdown notes.
        """
        title = paper_info["title"]
        authors = ", ".join(paper_info.get("authors", []))
        arxiv_id = paper_info["arxiv_id"]

        # ── Pass 1 ─────────────────────────────────────────
        logger.info(f"  [Pass 1] {title[:60]}...")
        first_pass_text = truncate_text(parsed_paper.first_pass_text, 30000)
        user_msg_1 = FIRST_PASS_USER.format(
            title=title,
            authors=authors,
            arxiv_id=arxiv_id,
            first_pass_content=first_pass_text,
        )
        result_1 = self.chain.invoke({"messages": [{"role": "user", "content": user_msg_1}]})
        initial_summary = result_1["messages"][-1].content

        # ── Pass 2 ─────────────────────────────────────────
        logger.info(f"  [Pass 2] {title[:60]}...")
        main_body = truncate_text(parsed_paper.main_body_text, 50000)
        if not main_body.strip():
            # Paper has no extractable main body → return Pass 1 result
            return self._format_final_notes(paper_info, initial_summary)

        user_msg_2 = SECOND_PASS_USER.format(
            initial_summary=initial_summary,
            main_body=main_body,
        )
        result_2 = self.chain.invoke({"messages": [{"role": "user", "content": user_msg_2}]})
        detailed_notes = result_2["messages"][-1].content

        # ── Pass 3 (optional: appendix) ────────────────────
        if self._should_read_appendix(detailed_notes) and parsed_paper.has_appendix:
            logger.info(f"  [Pass 3 - Appendix] {title[:60]}...")
            appendix = truncate_text(parsed_paper.appendix_text, 30000)
            user_msg_3 = APPENDIX_PASS_USER.format(
                current_notes=detailed_notes,
                appendix_content=appendix,
            )
            result_3 = self.chain.invoke({"messages": [{"role": "user", "content": user_msg_3}]})
            appendix_notes = result_3["messages"][-1].content.strip()
            # 将增量内容追加到第二次笔记后（跳过无补充的情况）
            if appendix_notes and "附录无重要补充内容" not in appendix_notes:
                detailed_notes = detailed_notes + "\n\n" + appendix_notes
            return self._format_final_notes(paper_info, detailed_notes)

        return self._format_final_notes(paper_info, detailed_notes)

    # ------------------------------------------------------------------

    @staticmethod
    def _should_read_appendix(notes: str) -> bool:
        """Check if the model decided to read the appendix."""
        match = re.search(r"APPENDIX_NEEDED:\s*(YES|NO)", notes, re.IGNORECASE)
        if match:
            return match.group(1).upper() == "YES"
        return False

    @staticmethod
    def _format_final_notes(paper_info: dict, notes_body: str) -> str:
        """Wrap notes with YAML front-matter for Obsidian."""
        notes_body = notes_body.strip()

        authors = ", ".join(paper_info.get("authors", [])[:5])
        categories = ", ".join(paper_info.get("categories", []))
        arxiv_id = paper_info["arxiv_id"]

        header = f"""\
---
title: "{paper_info['title']}"
arxiv_id: "{arxiv_id}"
authors: "{authors}"
categories: "{categories}"
date_read: "{paper_info.get('date_read', '')}"
skill_category: "{paper_info.get('skill_category', '')}"
pdf_url: "{paper_info.get('pdf_url', '')}"
---

# {paper_info['title']}

> **ArXiv**: [{arxiv_id}](https://arxiv.org/abs/{arxiv_id}) | **Authors**: {authors}

"""
        return header + notes_body
