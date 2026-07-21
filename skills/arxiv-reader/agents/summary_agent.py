"""
Summary Agent — quick abstract-only summary for uncategorized papers.
"""

from __future__ import annotations

from typing import Any, Dict

import config

from agents.base_agent import create_agent
from utils.logger import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = config.PROJECT_ROOT / "prompts"


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


SUMMARY_SYSTEM_PROMPT = _load_prompt("summary_system.md")


class SummaryAgent:
    """Generate quick summaries from title + abstract only."""

    def __init__(self, skill_config: Dict[str, Any]):
        reading_prompt = skill_config.get("reading_prompt", "")
        system_prompt = SUMMARY_SYSTEM_PROMPT.format(
            reading_prompt=reading_prompt
        )
        self.chain = create_agent(system_prompt, temperature=0.2, max_tokens=4000)

    def summarize(self, paper_info: dict) -> str:
        """Generate a summary note for one paper."""
        title = paper_info["title"]
        abstract = paper_info["abstract"]
        authors = ", ".join(paper_info.get("authors", [])[:5])
        arxiv_id = paper_info["arxiv_id"]

        user_input = (
            f"请对以下论文进行快速总结：\n\n"
            f"**标题**: {title}\n"
            f"**作者**: {authors}\n"
            f"**ArXiv ID**: {arxiv_id}\n\n"
            f"**摘要**:\n{abstract}"
        )

        try:
            result = self.chain.invoke({"messages": [{"role": "user", "content": user_input}]})
            body = result["messages"][-1].content
        except Exception as e:
            logger.error(f"Summary failed for '{title[:50]}': {e}")
            body = f"*自动总结失败: {e}*\n\n## 摘要\n\n{abstract}"

        return self._format_note(paper_info, body)

    # ------------------------------------------------------------------

    @staticmethod
    def _format_note(paper_info: dict, body: str) -> str:
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
skill_category: "general"
pdf_url: "{paper_info.get('pdf_url', '')}"
---

# {paper_info['title']}

> **ArXiv**: [{arxiv_id}](https://arxiv.org/abs/{arxiv_id}) | **Authors**: {authors}

"""
        return header + body
