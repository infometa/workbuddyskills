#!/usr/bin/env python3
"""Fail-open skill-usage tracking backed by the self-hosted umami instance.

Every function here must never raise into the caller and never block the CLI:
tracking is strictly best-effort (short timeout, all exceptions swallowed),
mirroring the fail-open contract of skill_update.py.

What is sent per event: event name (CLI command), skill name/version, host
agent (Claude Code / opencode / codex / ...), OS/arch/Python version, and a
distinct id (platform user_id when logged in, otherwise a random anonymous
UUID persisted in ~/.ai-shifu/analytics-id). No course content, titles, file
paths, or tokens are ever sent. Set AI_SHIFU_SKILL_TELEMETRY=off to disable.
"""

from __future__ import annotations

import base64
import json
import os
import platform
import re
import subprocess
import uuid
from pathlib import Path

import requests

SKILL_NAME = "ai-shifu-course-creator"
SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_ROOT / "SKILL.md"
ENV_FILE = SKILL_ROOT / ".env"

# The umami website id is a public identifier — the same value the ai-shifu
# web frontend exposes to every visitor in <script data-website-id> — not a
# secret. Skill events deliberately share the main-site website so that one
# user_bid links skill and website sessions; skill traffic stays separable
# via hostname/url/data.skill.
UMAMI_URL = "https://umami.ai-shifu.cn/api/send"
WEBSITE_ID = "f3108c8f-6898-4404-b6d7-fd076ad011db"

# hostname is a logical label for the umami website (no DNS resolution needed).
HOSTNAME = "skills.ai-shifu.cn"

ANALYTICS_ID_FILE = Path.home() / ".ai-shifu" / "analytics-id"

REQUEST_TIMEOUT = 3
# umami limits payload.id (distinct id) to 50 characters.
DISTINCT_ID_MAX = 50

_OPT_OUT_VALUES = frozenset({"off", "0", "false", "no"})

# Host-agent env markers, checked in order. The generic AI_AGENT convention
# (checked first in detect_agent) usually carries name + version already.
_AGENT_ENV_MARKERS = (
    ("CLAUDECODE", "claude-code"),
    ("CLAUDE_CODE", "claude-code"),
    ("OPENCODE_CLIENT", "opencode"),
    ("OPENCODE", "opencode"),
    ("CODEX_SANDBOX", "codex"),
    ("CODEX_THREAD_ID", "codex"),
    ("CODEX_CI", "codex"),
    ("GEMINI_CLI", "gemini-cli"),
    ("CURSOR_AGENT", "cursor"),
    ("COPILOT_CLI", "copilot"),
    ("AUGMENT_AGENT", "augment"),
    ("AMP_CURRENT_THREAD_ID", "amp"),
    ("ANTIGRAVITY_AGENT", "antigravity"),
    ("KIRO_AGENT_PATH", "kiro"),
    ("REPL_ID", "replit"),
)

# Fallback for agents without a known env marker (e.g. WorkBuddy): matched
# against ancestor process names, lowercased.
_AGENT_PROCESS_PATTERN = re.compile(
    r"claude|opencode|codex|workbuddy|codebuddy|cursor|gemini|copilot"
    r"|windsurf|aider|goose|amp"
)
_PROCESS_WALK_MAX_DEPTH = 10


def _skill_version() -> str:
    """Read `version:` from SKILL.md frontmatter; '0.0.0' when unreadable."""
    try:
        lines = SKILL_MD.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0].strip() != "---":
            return "0.0.0"
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip().strip("\"'") or "0.0.0"
    except OSError:
        pass
    return "0.0.0"


def _jwt_user_id(token: str) -> str | None:
    """Extract user_id from the ai-shifu JWT payload (no verification)."""
    try:
        encoded = token.split(".")[1]
        encoded = encoded.replace("-", "+").replace("_", "/")
        encoded += "=" * ((4 - len(encoded) % 4) % 4)
        payload = json.loads(base64.b64decode(encoded))
        user_id = payload.get("user_id")
        if isinstance(user_id, str) and user_id:
            return user_id
    except Exception:
        pass
    return None


def _token_from_env_file() -> str | None:
    """Read SHIFU_TOKEN from the skill's .env without requiring dotenv."""
    try:
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == "SHIFU_TOKEN":
                value = value.strip().strip("\"'")
                return value or None
    except OSError:
        pass
    return None


def _anonymous_id() -> str:
    """Read or create the per-machine anonymous UUID (never tied to identity)."""
    try:
        existing = ANALYTICS_ID_FILE.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except OSError:
        pass
    generated = str(uuid.uuid4())
    try:
        ANALYTICS_ID_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        ANALYTICS_ID_FILE.write_text(generated + "\n", encoding="utf-8")
        os.chmod(ANALYTICS_ID_FILE, 0o600)
    except OSError:
        pass
    return generated


def distinct_id() -> str:
    """Stable per-person id: platform user_id first, anonymous UUID fallback.

    The logged-in value is the raw user_bid, exactly what the ai-shifu web
    frontend passes to umami.identify() — so the same person tracked from the
    skill and from the website shares one distinct id. Only the anonymous
    fallback carries an `a:` prefix.
    """
    token = os.environ.get("SHIFU_TOKEN") or _token_from_env_file()
    if token:
        user_id = _jwt_user_id(token)
        if user_id:
            return user_id[:DISTINCT_ID_MAX]
    return f"a:{_anonymous_id()}"[:DISTINCT_ID_MAX]


def _walk_parent_process_names(max_depth: int = _PROCESS_WALK_MAX_DEPTH):
    """Yield ancestor process basenames, nearest first (POSIX ps only)."""
    pid = os.getppid()
    for _ in range(max_depth):
        if pid <= 1:
            return
        try:
            out = subprocess.run(
                ["ps", "-o", "comm=", "-o", "ppid=", "-p", str(pid)],
                capture_output=True,
                text=True,
                timeout=2,
            ).stdout.strip()
        except Exception:
            return
        parts = out.rsplit(None, 1)
        if len(parts) != 2:
            return
        comm, ppid = parts
        yield Path(comm).name.lower()
        try:
            pid = int(ppid)
        except ValueError:
            return


def detect_agent() -> str:
    """Identify the host agent running this skill (best effort)."""
    generic = os.environ.get("AI_AGENT", "").strip()
    if generic:
        return generic[:50]
    for var, name in _AGENT_ENV_MARKERS:
        if os.environ.get(var):
            if name == "claude-code":
                entrypoint = os.environ.get(
                    "CLAUDE_CODE_ENTRYPOINT", ""
                ).strip()
                return f"claude-code/{entrypoint}" if entrypoint else name
            return name
    for proc_name in _walk_parent_process_names():
        match = _AGENT_PROCESS_PATTERN.search(proc_name)
        if match:
            return f"proc:{match.group(0)}"
    return "unknown"


# Words that umami's isbot filter matches anywhere in the UA. Verified live:
# "claude-code_2-1-215_agent" was silently discarded ({"beep":"boop"}) purely
# because of the "agent" substring; the same UA without it was accepted.
_ISBOT_RISKY_WORDS = re.compile(
    r"(?i)bot|agent|spider|crawl|scan|search|monitor|fetch|http|client"
)


def _ua_safe(value: str) -> str:
    """Strip isbot-triggering substrings before embedding a value in the UA."""
    cleaned = _ISBOT_RISKY_WORDS.sub("", value)
    cleaned = re.sub(r"[-_ ]{2,}", "-", cleaned).strip("-_ ")
    return cleaned or "unknown"


def _user_agent(agent: str) -> str:
    """Build a browser-shaped UA that passes umami's isbot filter.

    Requests without a User-Agent are dropped by umami, and UAs matching
    isbot patterns (python-requests/, curl/, "agent", ...) are silently
    discarded with HTTP 200 — hence the Mozilla/5.0 prefix, a parsable OS
    segment, and _ua_safe() on the embedded agent name. The raw agent value
    still travels in payload.tag and data.agent.
    """
    system = platform.system()
    machine = platform.machine()
    if system == "Darwin":
        mac_version = platform.mac_ver()[0].replace(".", "_") or "10_15_7"
        os_segment = f"Macintosh; Intel Mac OS X {mac_version}"
    elif system == "Windows":
        os_segment = f"Windows NT {platform.release()}"
    else:
        os_segment = f"X11; Linux {machine}"
    return (
        f"Mozilla/5.0 ({os_segment}) "
        f"AIShifuSkill/{_skill_version()} ({SKILL_NAME}; {_ua_safe(agent)})"
    )


def _opted_out() -> bool:
    return (
        os.environ.get("AI_SHIFU_SKILL_TELEMETRY", "").strip().lower()
        in _OPT_OUT_VALUES
    )


def track(event_name: str) -> None:
    """Send one umami event; silent no-op on any failure or when disabled.

    The payload is built entirely from module-generated fields — track()
    deliberately takes no free-form data, so the "never sends course
    content, titles, file paths, or tokens" promise is structural rather
    than a matter of call-site discipline.
    """
    try:
        if _opted_out():
            return
        website = os.environ.get("AI_SHIFU_SKILL_UMAMI_WEBSITE_ID") or WEBSITE_ID
        if not website:
            return
        url = os.environ.get("AI_SHIFU_SKILL_UMAMI_URL") or UMAMI_URL
        agent = detect_agent()
        payload = {
            "website": website,
            "hostname": HOSTNAME,
            "url": f"/{SKILL_NAME}/{event_name}",
            "name": event_name,
            "id": distinct_id(),
            "tag": agent,
            "data": {
                "skill": SKILL_NAME,
                "version": _skill_version(),
                "agent": agent,
                "os": platform.system().lower(),
                "arch": platform.machine(),
                "python": platform.python_version(),
            },
        }
        requests.post(
            url,
            json={"type": "event", "payload": payload},
            headers={"User-Agent": _user_agent(agent)},
            timeout=REQUEST_TIMEOUT,
        )
    except Exception:
        pass
