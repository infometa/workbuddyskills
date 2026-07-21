#!/bin/bash
# =============================================================================
# skill-tracker: track.sh
# A zero-dependency, platform-adaptive shell script for reporting skill usage
# events to Beacon.
#
# Runtime behavior:
#   - On CodeBuddy: Hooks handle most reporting automatically (100%).
#     This script serves as supplement for custom business events.
#   - On OpenClaw/BoxAI/others: This script is the primary reporting mechanism.
#
# Requirements: bash + curl (available on all platforms)
#
# Usage:
#   bash ./track.sh <app_key> <skill_name> <event_name> [json_data]
#
# Examples:
#   bash ./track.sh "<APP_KEY>" "my-skill" "skill_invoked"
#   bash ./track.sh "<APP_KEY>" "my-skill" "task_done" '{"status":"success"}'
#
# Exit codes:
#   0 - Always returns 0 (never blocks the caller)
# =============================================================================

set -o pipefail

# --- Configuration ---
BEACON_URL="https://otheve.beacon.qq.com/analytics/v2_upload"
SDK_ID="js"
SDK_VERSION="4.3.4-web"
APP_VERSION="1.0.0"
PLATFORM_ID="3"
TIMEOUT_SECONDS=3

# --- Input validation ---
APP_KEY="${1:-}"
SKILL_NAME="${2:-}"
EVENT_NAME="${3:-}"
CUSTOM_DATA="${4:-}"
USER_ID="${5:-}"

if [ -z "$APP_KEY" ] || [ -z "$SKILL_NAME" ] || [ -z "$EVENT_NAME" ]; then
    echo "Usage: bash scripts/track.sh <app_key> <skill_name> <event_name> [json_data]" >&2
    exit 0
fi

# --- Privacy opt-out ---
if [ "${SKILL_TRACKING_DISABLED:-}" = "1" ] || [ "${SKILL_TRACKING_DISABLED:-}" = "true" ]; then
    exit 0
fi

# --- Guard: reject placeholder app_key ---
if [ "$APP_KEY" = "APP_KEY_NOT_CONFIGURED" ] || [ "$APP_KEY" = "your_app_key" ] || [ "$APP_KEY" = "YOUR-APP-KEY" ]; then
    echo "[skill-tracker] WARNING: app_key is not configured (got '$APP_KEY'). Skipping event '$EVENT_NAME'." >&2
    echo "[skill-tracker] Please provide a valid Beacon Appkey via your tracking platform or administrator." >&2
    exit 0
fi

# --- Helper: Replace special characters per Beacon API requirements ---
replace_symbol() {
    local value="$1"
    value="${value//|/%7C}"
    value="${value//&/%26}"
    value="${value//=/%3D}"
    value="${value//+/%2B}"
    echo "$value"
}

# --- Generate anonymous device identifier (A2) ---
# Public-safe mode: do NOT read hostname, username, machine-id, MachineGuid, IOPlatformUUID, or MAC address.
# A random local UUID is generated once and stored locally only for anonymous usage counting.
generate_a2() {
    local did_dir="${SKILL_TRACKER_STATE_DIR:-$HOME/.tencent-campus-recruit}"
    local did_file="$did_dir/anonymous-id"
    local anonymous_id=""

    if [ -f "$did_file" ]; then
        anonymous_id=$(cat "$did_file" 2>/dev/null | tr -d '[:space:]')
    fi

    if [ -z "$anonymous_id" ]; then
        if command -v uuidgen &>/dev/null; then
            anonymous_id=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]')
        elif command -v python3 &>/dev/null; then
            anonymous_id=$(python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null)
        elif command -v python &>/dev/null; then
            anonymous_id=$(python -c "import uuid; print(uuid.uuid4())" 2>/dev/null)
        elif [ -f /proc/sys/kernel/random/uuid ]; then
            anonymous_id=$(cat /proc/sys/kernel/random/uuid 2>/dev/null)
        else
            anonymous_id="anon-$(date +%s)-$$"
        fi
        mkdir -p "$did_dir" 2>/dev/null && echo "$anonymous_id" > "$did_file" 2>/dev/null
    fi

    if command -v md5sum &>/dev/null; then
        echo -n "$anonymous_id" | md5sum | cut -c1-32
    elif command -v md5 &>/dev/null; then
        echo -n "$anonymous_id" | md5 -q
    elif command -v openssl &>/dev/null; then
        echo -n "$anonymous_id" | openssl md5 | sed 's/.*= //'
    elif command -v python3 &>/dev/null; then
        echo -n "$anonymous_id" | python3 -c "import hashlib,sys; print(hashlib.md5(sys.stdin.buffer.read()).hexdigest())" 2>/dev/null
    elif command -v python &>/dev/null; then
        echo -n "$anonymous_id" | python -c "import hashlib,sys; print(hashlib.md5(sys.stdin.buffer.read()).hexdigest())" 2>/dev/null
    else
        local ck
        ck=$(echo -n "$anonymous_id" | cksum | awk '{print $1}')
        printf '%032s' "$ck" | tr ' ' '0'
    fi
}

# --- Runtime platform detection ---
# Detects the CURRENT runtime platform, not the development platform.
# This runs every time the script is called, adapting to wherever the
# skill is actually being used.
detect_platform() {
    local platform="unknown"

    # Method 1: Check environment variables set by platforms
    # Claude Code (claude-internal) indicators
    if [ -n "${CLAUDE_CODE_ENTRYPOINT:-}" ] || [ -n "${CLAUDE_SKILL_DIR:-}" ]; then
        platform="claude-code"
    # CodeBuddy indicators
    elif [ -n "${CODEBUDDY_PROJECT_DIR:-}" ] || [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
        platform="codebuddy"
    elif [ -n "${CODEBUDDY_ENV:-}" ] || [ -n "${CODEBUDDY_VERSION:-}" ]; then
        platform="codebuddy"
    elif [ -n "${OPENCLAW_SHELL:-}" ] || [ -n "${OPENCLAW_ENV:-}" ] || [ -n "${OPENCLAW_VERSION:-}" ]; then
        # OPENCLAW_SHELL is OpenClaw's officially documented marker set by the
        # exec context (e.g. OPENCLAW_SHELL=exec) — it's the most reliable
        # signal we can get, so keep it first among OpenClaw env checks.
        platform="openclaw"
    elif [ -n "${BOXAI_ENV:-}" ] || [ -n "${BOXAI_VERSION:-}" ]; then
        platform="boxai"
    fi

    # Method 2: Check parent process hints
    if [ "$platform" = "unknown" ]; then
        local parent_cmd=""
        parent_cmd=$(ps -o comm= -p $PPID 2>/dev/null || echo "")
        if echo "$parent_cmd" | grep -qi "claude"; then
            platform="claude-code"
        elif echo "$parent_cmd" | grep -qi "codebuddy"; then
            platform="codebuddy"
        elif echo "$parent_cmd" | grep -qi "openclaw"; then
            platform="openclaw"
        elif echo "$parent_cmd" | grep -qi "boxai"; then
            platform="boxai"
        fi
    fi

    # Method 3: Check for platform-specific directories in workspace.
    # Only .claude/ is trusted here — it is Claude Code's runtime workspace
    # marker. We intentionally do NOT fall back to a `.codebuddy/` directory:
    # its presence only means the project once used CodeBuddy hooks, not that
    # the current runtime is CodeBuddy. A user opening the same workspace in
    # OpenClaw would otherwise be misclassified as codebuddy.
    if [ "$platform" = "unknown" ]; then
        if [ -d ".claude" ]; then
            platform="claude-code"
        fi
    fi

    # Method 4: IDE/terminal hints
    if [ "$platform" = "unknown" ]; then
        if [ -n "${VSCODE_PID:-}" ] || [ -n "${TERM_PROGRAM:-}" ]; then
            platform="ide-${TERM_PROGRAM:-vscode}"
        fi
    fi

    echo "$platform"
}

# --- Enrich data based on runtime platform ---
# Public-safe mode: collect only coarse runtime information, never project paths or file counts.
collect_platform_context() {
    local platform="$1"
    local extra=""

    local os_info=""
    os_info=$(uname -s 2>/dev/null || echo "unknown")
    extra="\"skill_os\":\"$(replace_symbol "$os_info")\""

    if [ "$platform" = "codebuddy" ] || [ "$platform" = "claude-code" ]; then
        extra="$extra,\"hooks_active\":\"true\""
    fi

    echo "$extra"
}
# --- Collect skill_user (person-level UV) ---
# Public-safe mode: default to anonymous; only use explicit opt-in override.
collect_skill_user() {
    local user="${SKILL_TRACKER_USER:-anonymous}"
    echo "$user"
}

# --- Collect skill_version ---
# Priority: SKILL_VERSION env > pyproject.toml > package.json > VERSION file > empty
collect_skill_version() {
    local version="${SKILL_VERSION:-}"

    # Try pyproject.toml
    if [ -z "$version" ] && [ -f "$SKILL_DIR/pyproject.toml" ]; then
        version=$(grep -E '^version\s*=' "$SKILL_DIR/pyproject.toml" 2>/dev/null \
            | head -1 | sed 's/.*=\s*["'"'"']\(.*\)["'"'"'].*/\1/')
    fi

    # Try package.json
    if [ -z "$version" ] && [ -f "$SKILL_DIR/package.json" ]; then
        version=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$SKILL_DIR/package.json" 2>/dev/null \
            | head -1 | sed 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
    fi

    # Try VERSION file
    if [ -z "$version" ] && [ -f "$SKILL_DIR/VERSION" ]; then
        version=$(cat "$SKILL_DIR/VERSION" 2>/dev/null | tr -d '[:space:]')
    fi

    echo "$version"
}

# --- Resolve SKILL_DIR for version detection ---
# When called directly: SKILL_DIR is the parent of the directory containing track.sh (i.e. skill root)
# When called via report.sh: SKILL_DIR is already set by the caller
if [ -z "${SKILL_DIR:-}" ]; then
    SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

# --- Build event mapValue ---
build_map_value() {
    local skill_name="$1"
    local platform="$2"
    local platform_context="$3"
    local custom_data="$4"

    # Use skill_ prefix for platform/os/user to avoid Beacon reserved field conflict
    local map_value=""
    map_value="\"skill_name\":\"$(replace_symbol "$skill_name")\""
    map_value="$map_value,\"skill_platform\":\"$(replace_symbol "$platform")\""

    # skill_user: anonymous by default; explicit opt-in override only
    local skill_user=""
    skill_user=$(collect_skill_user)
    map_value="$map_value,\"skill_user\":\"$(replace_symbol "$skill_user")\""

    # skill_version: from config files (omit if not found)
    local skill_version=""
    skill_version=$(collect_skill_version)
    if [ -n "$skill_version" ]; then
        map_value="$map_value,\"skill_version\":\"$(replace_symbol "$skill_version")\""
    fi

    # Add platform context (includes skill_os, arch, etc.)
    if [ -n "$platform_context" ]; then
        map_value="$map_value,$platform_context"
    fi

    # Merge custom data if provided
    if [ -n "$custom_data" ]; then
        local stripped=""
        stripped=$(echo "$custom_data" | sed 's/^[[:space:]]*{//;s/}[[:space:]]*$//')
        if [ -n "$stripped" ]; then
            map_value="$map_value,$stripped"
        fi
    fi

    echo "{$map_value}"
}

# --- Main ---
main() {
    local a2=""
    a2=$(generate_a2)

    local platform=""
    platform=$(detect_platform)

    local platform_context=""
    platform_context=$(collect_platform_context "$platform")

    local event_time=""
    if date +%s%3N &>/dev/null 2>&1; then
        event_time=$(date +%s%3N 2>/dev/null)
        if echo "$event_time" | grep -q "N"; then
            event_time="$(date +%s)000"
        fi
    else
        event_time="$(date +%s)000"
    fi

    local map_value=""
    map_value=$(build_map_value "$SKILL_NAME" "$platform" "$platform_context" "$CUSTOM_DATA")

    # Build common: A2 always present, A1 only when USER_ID is set
    local common_fields=""
    if [ -n "$USER_ID" ]; then
        common_fields="\"A1\": \"$(replace_symbol "$USER_ID")\", \"A2\": \"${a2}\""
    else
        common_fields="\"A2\": \"${a2}\""
    fi

    local body=""
    body=$(cat <<EOF
{
    "appVersion": "${APP_VERSION}",
    "sdkId": "${SDK_ID}",
    "sdkVersion": "${SDK_VERSION}",
    "mainAppKey": "$(replace_symbol "$APP_KEY")",
    "platformId": ${PLATFORM_ID},
    "common": {
        ${common_fields}
    },
    "events": [
        {
            "eventCode": "$(replace_symbol "$EVENT_NAME")",
            "eventTime": "${event_time}",
            "mapValue": ${map_value}
        }
    ]
}
EOF
)

    curl -s -o /dev/null \
        --max-time "$TIMEOUT_SECONDS" \
        -X POST "$BEACON_URL" \
        -H "Content-Type: application/json;charset=UTF-8" \
        -d "$body" 2>/dev/null || true

    exit 0
}

main
