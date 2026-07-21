"""
Classifier Agent — decides which skill category a paper belongs to.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

import config

from agents.base_agent import create_agent
from skills.loader import get_categories_description
from utils.logger import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = config.PROJECT_ROOT / "prompts"


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


CLASSIFIER_SYSTEM_PROMPT = _load_prompt("classifier_system.md")


class ClassifierAgent:
    """Classify papers into skill categories."""

    def __init__(self, skills: Dict[str, Any]):
        self.skills = skills
        categories_desc = get_categories_description(skills)
        self.category_names = [
            name for name in skills.keys() if name != "general"
        ]
        system_prompt = CLASSIFIER_SYSTEM_PROMPT.format(
            categories=categories_desc
        )
        self.chain = create_agent(system_prompt, temperature=0.1)

    def classify(self, title: str, abstract: str) -> str:
        """Return the category name for a single paper."""
        user_input = (
            f"请对以下论文进行分类：\n\n"
            f"**标题**: {title}\n\n"
            f"**摘要**: {abstract}"
        )
        try:
            result = self.chain.invoke({"messages": [{"role": "user", "content": user_input}]})
            text = result["messages"][-1].content
            parsed = self._parse_json(text)
            category = parsed.get("category", "general")
            confidence = float(parsed.get("confidence", 0))

            if category not in self.category_names or confidence < 0.4:
                category = "general"

            logger.info(
                f"  [{category}] (conf={confidence:.2f}) {title[:60]}..."
            )
            return category

        except Exception as e:
            logger.warning(f"Classification failed for '{title[:50]}': {e}")
            return "general"

    # ------------------------------------------------------------------
    def classify_batch(self, papers: list[dict]) -> dict[str, str]:
        """Classify a list of papers. Returns {arxiv_id: category}."""
        results: dict[str, str] = {}
        for paper in papers:
            cat = self.classify(paper["title"], paper["abstract"])
            results[paper["arxiv_id"]] = cat
        return results

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Robustly extract JSON from LLM output."""
        # Try direct parse
        text = text.strip()
        # Remove possible ```json ... ``` wrapping
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in text
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"category": "general", "confidence": 0, "reasoning": "parse error"}
