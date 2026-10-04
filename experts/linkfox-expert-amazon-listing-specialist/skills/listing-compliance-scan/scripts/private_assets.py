"""Resolve Listing Agent rule data from a non-Skill sibling container."""

import os
from pathlib import Path


ENV_PRIVATE_ASSETS_DIR = "LINKFOX_LISTING_PRIVATE_ASSETS_DIR"


def private_assets_dir() -> Path:
    """Return the agent-private directory containing compliance rule libraries."""
    override = os.environ.get(ENV_PRIVATE_ASSETS_DIR, "").strip()
    if override:
        return Path(override).expanduser().resolve()

    skill_dir = Path(__file__).resolve().parent.parent
    return skill_dir.parent / "_listing-private-assets" / "data"
