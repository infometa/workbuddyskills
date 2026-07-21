"""
Skill Loader — scans the skills/ directory structure and loads
category metadata + reading prompts for each sub-folder.
"""

from pathlib import Path
from typing import Dict, Any

import config
from utils.logger import get_logger

logger = get_logger(__name__)

METADATA_FILE = "_metadata.md"
READING_PROMPT_FILE = "reading_prompt.md"


def _read_md(path: Path) -> str:
    """Read a markdown file, return empty string if missing."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def load_all_skills() -> Dict[str, Dict[str, Any]]:
    """
    Load every skill category from the skills/ directory.

    Returns:
        {
            "agent_systems": {
                "name": "agent_systems",
                "metadata": "<content of _metadata.md>",
                "reading_prompt": "<content of reading_prompt.md>",
            },
            ...
        }
    """
    skills_dir = config.SKILLS_DIR
    skills: Dict[str, Dict[str, Any]] = {}

    if not skills_dir.exists():
        logger.warning(f"Skills directory not found: {skills_dir}")
        return skills

    for child in sorted(skills_dir.iterdir()):
        if child.is_dir() and not child.name.startswith("_"):
            metadata = _read_md(child / METADATA_FILE)
            reading_prompt = _read_md(child / READING_PROMPT_FILE)

            if not metadata:
                logger.warning(
                    f"Skill '{child.name}' has no {METADATA_FILE}, skipping."
                )
                continue

            skills[child.name] = {
                "name": child.name,
                "metadata": metadata,
                "reading_prompt": reading_prompt,
            }
            logger.info(f"Loaded skill: {child.name}")

    return skills


def get_categories_description(skills: Dict[str, Dict[str, Any]]) -> str:
    """
    Build a textual description of all categories (used by the classifier).
    """
    lines: list[str] = []
    for name, info in skills.items():
        if name == "general":
            continue  # general is the fallback, not a classification target
        lines.append(f"### {name}\n{info['metadata']}\n")
    return "\n".join(lines)
