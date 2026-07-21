#!/bin/sh
set -e

# run-cli.sh — Execute tencent-news-cli with --caller injected from SKILL.md.

fail() { echo "Error: $1" >&2; exit 1; }

resolve_command_cli_path() {
  resolved_path="$(command -v "$1" 2>/dev/null || true)"
  if [ -z "$resolved_path" ]; then
    return 1
  fi

  if "$resolved_path" help >/dev/null 2>&1; then
    printf '%s\n' "$resolved_path"
    return 0
  fi

  return 1
}

resolve_skill_caller() {
  skill_md_path="$(cd "$(dirname "$0")/.." && pwd)/SKILL.md"
  [ -f "$skill_md_path" ] || fail "SKILL.md not found: $skill_md_path"

  skill_name="$(awk '
    BEGIN { in_frontmatter = 0 }
    /^---[[:space:]]*$/ {
      if (in_frontmatter == 0) {
        in_frontmatter = 1
        next
      }
      exit
    }
    in_frontmatter && /^name:[[:space:]]*/ {
      sub(/^name:[[:space:]]*/, "", $0)
      print
      exit
    }
  ' "$skill_md_path" | tr -d '\r' | sed "s/^['\"]//; s/['\"]$//")"

  [ -n "$skill_name" ] || fail "name field not found in $skill_md_path"

  skill_version="$(awk '
    BEGIN { in_frontmatter = 0 }
    /^---[[:space:]]*$/ {
      if (in_frontmatter == 0) {
        in_frontmatter = 1
        next
      }
      exit
    }
    in_frontmatter && /^version:[[:space:]]*/ {
      sub(/^version:[[:space:]]*/, "", $0)
      print
      exit
    }
  ' "$skill_md_path" | tr -d '\r' | sed "s/^['\"]//; s/['\"]$//")"

  if [ -n "$skill_version" ]; then
    printf '%s_%s\n' "$skill_name" "$skill_version"
    return 0
  fi

  printf '%s\n' "$skill_name"
}

has_caller_flag() {
  for arg in "$@"; do
    case "$arg" in
      --caller|--caller=*)
        return 0
        ;;
    esac
  done
  return 1
}

normalize_version() {
  printf '%s' "$1" | tr -d '\r' | sed "s/^['\"]//; s/['\"]$//; s/^v//; s/-.*$//"
}

compare_versions() {
  left="$(normalize_version "$1")"
  right="$(normalize_version "$2")"

  [ -n "$left" ] || return 2
  [ -n "$right" ] || return 2

  left_major="$(printf '%s' "$left" | cut -d. -f1)"
  left_minor="$(printf '%s' "$left" | cut -d. -f2)"
  left_patch="$(printf '%s' "$left" | cut -d. -f3)"
  right_major="$(printf '%s' "$right" | cut -d. -f1)"
  right_minor="$(printf '%s' "$right" | cut -d. -f2)"
  right_patch="$(printf '%s' "$right" | cut -d. -f3)"

  [ "$left_minor" != "$left" ] || left_minor=0
  [ "$left_patch" != "$left" ] || left_patch=0
  [ "$right_minor" != "$right" ] || right_minor=0
  [ "$right_patch" != "$right" ] || right_patch=0

  case "$left_major.$left_minor.$left_patch.$right_major.$right_minor.$right_patch" in
    *[!0-9.]*)
      return 2
      ;;
  esac

  if [ "$left_major" -gt "$right_major" ]; then return 0; fi
  if [ "$left_major" -lt "$right_major" ]; then return 1; fi
  if [ "$left_minor" -gt "$right_minor" ]; then return 0; fi
  if [ "$left_minor" -lt "$right_minor" ]; then return 1; fi
  if [ "$left_patch" -ge "$right_patch" ]; then return 0; fi
  return 1
}

supports_caller_arg() {
  VERSION_OUTPUT="$("$CLI_PATH" version 2>&1)" && VERSION_EXIT=0 || VERSION_EXIT=$?
  [ "$VERSION_EXIT" -eq 0 ] || return 1

  echo "$VERSION_OUTPUT" | grep -q '"current_version"' || return 1
  current_version="$(printf '%s' "$VERSION_OUTPUT" | sed -n 's/.*"current_version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"
  [ -n "$current_version" ] || return 1

  compare_versions "$current_version" "1.0.12"
}

if [ $# -eq 0 ]; then
  fail "missing CLI command"
  exit 1
fi

has_caller_flag "$@" && fail "do not pass --caller manually; scripts/run-cli.sh injects it from SKILL.md"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLI_FILENAME="tencent-news-cli"
LOCAL_CLI_PATH="$SKILL_DIR/$CLI_FILENAME"
INSTALL_ROOT="${TENCENT_NEWS_INSTALL:-${HOME:-}/.tencent-news-cli}"
GLOBAL_CLI_PATH="$INSTALL_ROOT/bin/$CLI_FILENAME"
CLI_PATH="$(resolve_command_cli_path "$CLI_FILENAME" || true)"

if [ -z "$CLI_PATH" ]; then
  if [ -f "$GLOBAL_CLI_PATH" ]; then
    CLI_PATH="$GLOBAL_CLI_PATH"
  elif [ -f "$LOCAL_CLI_PATH" ]; then
    CLI_PATH="$LOCAL_CLI_PATH"
  else
    fail "cli not found. Run sh scripts/cli-state.sh to inspect installation state first."
  fi
fi

chmod +x "$CLI_PATH" 2>/dev/null || true
CALLER="$(resolve_skill_caller)"

if supports_caller_arg; then
  exec "$CLI_PATH" "$@" --caller "$CALLER"
fi

exec "$CLI_PATH" "$@"
