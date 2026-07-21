"""
Global configuration module.
Loads all settings from .env file at project root.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Project Root ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.resolve()
load_dotenv(PROJECT_ROOT / ".env")

# ── LLM ──────────────────────────────────────────────────────
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "16000"))

# ── Skills ───────────────────────────────────────────────────
SKILLS_DIR = PROJECT_ROOT / "skills"
