"""
Shared utilities for multi-platform Hook scripts.

Supports CodeBuddy, Claude Code (claude-internal), and other AI platforms.
Provides consistent Beacon reporting, device fingerprint generation,
platform auto-detection, and special character escaping across all hooks.

This module ensures the A2 fingerprint algorithm is identical to
skill_tracker/fingerprint.py, so Hook reports and Python SDK reports
produce the same user identifier.
"""

import json
import hashlib
import time
import os
import urllib.request

BEACON_URL = "https://otheve.beacon.qq.com/analytics/v2_upload"

# Placeholder values that indicate app_key has not been configured.
_PLACEHOLDER_APP_KEYS = {"APP_KEY_NOT_CONFIGURED", "your_app_key", "YOUR-APP-KEY", ""}

# Module-level directory resolution (computed once, reused by multiple functions)
_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_HOOKS_DIR)


def replace_symbol(value):
    """Replace special characters per Beacon API requirements."""
    if not isinstance(value, str):
        value = str(value)
    return (
        value.replace("|", "%7C")
        .replace("&", "%26")
        .replace("=", "%3D")
        .replace("+", "%2B")
    )


def generate_a2():
    """Generate a public-safe anonymous device identifier.

    This function does not read hostname, OS machine IDs, MachineGuid,
    IOPlatformUUID, MAC address, or username. It creates a random local UUID once
    and hashes it for anonymous usage counting.
    """
    import uuid

    state_dir = os.environ.get(
        "SKILL_TRACKER_STATE_DIR",
        os.path.join(os.path.expanduser("~"), ".tencent-campus-recruit"),
    )
    anon_file = os.path.join(state_dir, "anonymous-id")
    anonymous_id = ""

    try:
        if os.path.isfile(anon_file):
            with open(anon_file, "r", encoding="utf-8") as f:
                anonymous_id = f.read().strip()
    except Exception:
        anonymous_id = ""

    if not anonymous_id:
        anonymous_id = str(uuid.uuid4())
        try:
            os.makedirs(state_dir, exist_ok=True)
            with open(anon_file, "w", encoding="utf-8") as f:
                f.write(anonymous_id)
        except Exception:
            pass

    return hashlib.md5(anonymous_id.encode("utf-8")).hexdigest()

def _collect_skill_user():
    """Collect person-level user identifier.

    Public-safe mode: default to anonymous; only use explicit opt-in override.
    """
    return os.environ.get("SKILL_TRACKER_USER", "anonymous")

def _collect_skill_os():
    """Collect OS name (e.g. Darwin, Linux, Windows)."""
    try:
        import platform as _plat
        return _plat.system() or "unknown"
    except Exception:
        return "unknown"


def _detect_platform():
    """Detect the current runtime platform.

    Returns "codebuddy", "claude-code", "openclaw", "boxai", or "unknown".
    """
    # Claude Code indicators
    if os.environ.get("CLAUDE_CODE_ENTRYPOINT") or os.environ.get("CLAUDE_SKILL_DIR"):
        return "claude-code"
    # Also check for .claude directory (Claude Code project marker)
    if os.path.isdir(os.path.join(_SKILL_DIR, ".claude")):
        return "claude-code"

    # CodeBuddy indicators
    if (os.environ.get("CODEBUDDY_PROJECT_DIR")
            or os.environ.get("CODEBUDDY_ENV")
            or os.environ.get("CODEBUDDY_VERSION")):
        return "codebuddy"
    # NOTE: We intentionally do NOT fall back to a `.codebuddy/` directory
    # check - its presence only means the project once used CodeBuddy hooks,
    # not that the current runtime is CodeBuddy. Runtime env vars are the
    # only trustworthy signal.

    # Other platforms
    # OPENCLAW_SHELL is OpenClaw's officially documented exec-context marker
    # (e.g. OPENCLAW_SHELL=exec) and is more reliable than OPENCLAW_ENV/VERSION.
    if (os.environ.get("OPENCLAW_SHELL")
            or os.environ.get("OPENCLAW_ENV")
            or os.environ.get("OPENCLAW_VERSION")):
        return "openclaw"
    if os.environ.get("BOXAI_ENV") or os.environ.get("BOXAI_VERSION"):
        return "boxai"

    return "unknown"


def _collect_skill_version():
    """Collect skill version from config files.

    Priority: SKILL_VERSION env > pyproject.toml > package.json > VERSION file > empty
    """
    version = os.environ.get("SKILL_VERSION", "")
    if version:
        return version

    # Determine skill directory: hooks/ parent
    hooks_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(hooks_dir)

    # Try pyproject.toml
    if not version:
        pyproject = os.path.join(skill_dir, "pyproject.toml")
        if os.path.isfile(pyproject):
            try:
                import re
                with open(pyproject, "r") as f:
                    for line in f:
                        m = re.match(r'^version\s*=\s*["\']([^"\']+)["\']', line)
                        if m:
                            version = m.group(1)
                            break
            except Exception:
                pass

    # Try package.json
    if not version:
        pkg_json = os.path.join(_SKILL_DIR, "package.json")
        if os.path.isfile(pkg_json):
            try:
                with open(pkg_json, "r") as f:
                    pkg = json.loads(f.read())
                    version = pkg.get("version", "")
            except Exception:
                pass

    # Try VERSION file
    if not version:
        ver_file = os.path.join(_SKILL_DIR, "VERSION")
        if os.path.isfile(ver_file):
            try:
                with open(ver_file, "r") as f:
                    version = f.read().strip()
            except Exception:
                pass

    return version


def send_report(app_key, skill_name, event_code, extra_data=None, user_id=None):
    """Send event to Beacon API. Never raises exceptions.

    Args:
        app_key: Beacon app key.
        skill_name: Skill name for event grouping.
        event_code: Event identifier.
        extra_data: Optional dict of additional key-value data.
        user_id: Optional user identifier. If provided, written to common.A1.
    """
    if os.environ.get("SKILL_TRACKING_DISABLED", "").lower() in {"1", "true"}:
        return

    # Guard: skip reporting if app_key is a placeholder
    if app_key in _PLACEHOLDER_APP_KEYS:
        import sys
        print(
            f"[skill-tracker] WARNING: app_key is not configured (got '{app_key}'). "
            f"Skipping event '{event_code}'. "
            "Please provide a valid Beacon Appkey via your tracking platform or administrator.",
            file=sys.stderr,
        )
        return

    a2 = generate_a2()
    event_time = str(int(time.time() * 1000))

    # Resolve user_id: explicit parameter only. Do not read ambient user identifiers by default.
    resolved_user_id = user_id

    map_value = {
        "skill_name": replace_symbol(skill_name),
        "skill_platform": replace_symbol(_detect_platform()),
        "skill_user": replace_symbol(_collect_skill_user()),
        "skill_os": replace_symbol(_collect_skill_os()),
    }

    # skill_version: omit if not found
    skill_version = _collect_skill_version()
    if skill_version:
        map_value["skill_version"] = replace_symbol(skill_version)

    if extra_data:
        for k, v in extra_data.items():
            map_value[replace_symbol(str(k))] = replace_symbol(str(v))

    # Build common: A2 always present, A1 only when user_id is resolved
    common = {"A2": a2}
    if resolved_user_id:
        common["A1"] = replace_symbol(resolved_user_id)

    payload = {
        "appVersion": "1.0.0",
        "sdkId": "js",
        "sdkVersion": "4.3.4-web",
        "mainAppKey": replace_symbol(app_key),
        "platformId": 3,
        "common": common,
        "events": [
            {
                "eventCode": replace_symbol(event_code),
                "eventTime": event_time,
                "mapValue": {str(k): str(v) for k, v in map_value.items()},
            }
        ],
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            BEACON_URL,
            data=data,
            headers={"Content-Type": "application/json;charset=UTF-8"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass  # Never block the hook


# --- Session cache utilities ---
SESSION_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".tencent-campus-recruit", "sessions")


def save_session_start(session_id):
    """Cache session start time for duration calculation."""
    try:
        os.makedirs(SESSION_CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(SESSION_CACHE_DIR, f"{session_id}.start")
        with open(cache_file, "w") as f:
            f.write(str(time.time()))
    except Exception:
        pass


def get_session_duration(session_id):
    """Calculate session duration from cached start time. Returns seconds as string."""
    cache_file = os.path.join(SESSION_CACHE_DIR, f"{session_id}.start")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                start_time = float(f.read().strip())
            duration = str(int(time.time() - start_time))
            os.remove(cache_file)
            return duration
        except Exception:
            pass
    return "0"
