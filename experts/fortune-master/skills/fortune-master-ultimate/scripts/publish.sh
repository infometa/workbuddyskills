#!/usr/bin/env bash
# ============================================================
# publish.sh — ClawHub Skill Auto-Publish Script
#
# Features:
#   - Auto version bump (patch/minor/major) from current version
#   - Timeout retry with configurable attempts
#   - Syncs version across _meta.json, package.json, SKILL.md
#   - Calls `clawhub publish` with correct CLI arguments
#
# Usage:
#   ./scripts/publish.sh                          # auto bump patch
#   ./scripts/publish.sh --bump minor             # bump minor
#   ./scripts/publish.sh --version 2.0.0          # explicit version
#   ./scripts/publish.sh --name 命理大师           # with display name
#   ./scripts/publish.sh --retries 5 --timeout 120
# ============================================================

set -euo pipefail

# ── Colors ───────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ── Defaults ─────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION=""
BUMP="patch"          # patch | minor | major
DISPLAY_NAME=""
DRY_RUN=false
SKIP_GIT=false
SKIP_CHECKS=false
MAX_RETRIES=3         # max publish retry attempts
RETRY_DELAY=5         # seconds between retries
TIMEOUT=60            # timeout per publish attempt (seconds)
SLUG=""               # optional --slug override
CHANGELOG=""          # optional --changelog text
FORK_OF=""            # optional --fork-of
TAGS=""               # optional --tags

# ── Helper Functions ─────────────────────────────────────────
info()    { echo -e "${CYAN}ℹ${NC}  $*"; }
success() { echo -e "${GREEN}✔${NC}  $*"; }
warn()    { echo -e "${YELLOW}⚠${NC}  $*"; }
error()   { echo -e "${RED}✖${NC}  $*" >&2; }
fatal()   { error "$*"; exit 1; }

banner() {
  echo ""
  echo -e "${BOLD}☯️  ClawHub Skill Publisher${NC}"
  echo -e "   ${CYAN}fortune-master-ultimate${NC}"
  echo "   ─────────────────────────────"
  echo ""
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Version Options (mutually exclusive):
  --version <semver>   Explicit version to publish (e.g. 2.0.0)
  --bump <level>       Auto bump: patch (default), minor, or major

Publish Options:
  --name <name>        Display name (e.g. --name 命理大师)
  --slug <slug>        Skill slug override
  --changelog <text>   Changelog text
  --fork-of <slug>     Mark as fork of existing skill
  --tags <tags>        Comma-separated tags (default: "latest")

Retry Options:
  --retries <n>        Max publish retry attempts (default: 3)
  --timeout <sec>      Timeout per attempt in seconds (default: 60)
  --retry-delay <sec>  Delay between retries in seconds (default: 5)

Other Options:
  --dry-run            Simulate without making changes
  --skip-git           Skip git commit and tag
  --skip-checks        Skip pre-flight checks
  -h, --help           Show this help message

Examples:
  $(basename "$0")                                  # auto bump patch, publish
  $(basename "$0") --bump minor --name 命理大师      # bump minor version
  $(basename "$0") --version 2.0.0 --name 命理大师   # explicit version
  $(basename "$0") --retries 5 --timeout 120        # more retries, longer timeout
EOF
  exit 0
}

# ── Semver Bump Function ─────────────────────────────────────
# Usage: bump_version "1.2.3" "patch" => "1.2.4"
#        bump_version "1.2.3" "minor" => "1.3.0"
#        bump_version "1.2.3" "major" => "2.0.0"
bump_version() {
  local ver="$1"
  local level="$2"

  # Strip leading 'v' if present
  ver="${ver#v}"

  # Extract major.minor.patch (strip any pre-release suffix)
  local base="${ver%%-*}"
  IFS='.' read -r major minor patch <<< "$base"

  # Default to 0 if empty
  major="${major:-0}"
  minor="${minor:-0}"
  patch="${patch:-0}"

  case "$level" in
    major)
      major=$((major + 1))
      minor=0
      patch=0
      ;;
    minor)
      minor=$((minor + 1))
      patch=0
      ;;
    patch)
      patch=$((patch + 1))
      ;;
    *)
      fatal "Invalid bump level: '$level' (expected: patch, minor, major)"
      ;;
  esac

  echo "${major}.${minor}.${patch}"
}

# ── Read Current Version ─────────────────────────────────────
read_current_version() {
  if [[ -f "$PROJECT_DIR/_meta.json" ]]; then
    python3 -c "import json; print(json.load(open('$PROJECT_DIR/_meta.json')).get('version', '0.0.0'))" 2>/dev/null || echo "0.0.0"
  elif [[ -f "$PROJECT_DIR/package.json" ]]; then
    python3 -c "import json; print(json.load(open('$PROJECT_DIR/package.json')).get('version', '0.0.0'))" 2>/dev/null || echo "0.0.0"
  else
    echo "0.0.0"
  fi
}

# ── Parse Arguments ──────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      VERSION="$2"
      shift 2
      ;;
    --bump)
      BUMP="$2"
      shift 2
      ;;
    --name)
      DISPLAY_NAME="$2"
      shift 2
      ;;
    --slug)
      SLUG="$2"
      shift 2
      ;;
    --changelog)
      CHANGELOG="$2"
      shift 2
      ;;
    --fork-of)
      FORK_OF="$2"
      shift 2
      ;;
    --tags)
      TAGS="$2"
      shift 2
      ;;
    --retries)
      MAX_RETRIES="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    --retry-delay)
      RETRY_DELAY="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --skip-git)
      SKIP_GIT=true
      shift
      ;;
    --skip-checks)
      SKIP_CHECKS=true
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      warn "Unknown argument: $1"
      shift
      ;;
  esac
done

# ── Resolve Version ─────────────────────────────────────────
banner

CURRENT_VERSION=$(read_current_version)

if [[ -z "$VERSION" ]]; then
  # Auto bump from current version
  VERSION=$(bump_version "$CURRENT_VERSION" "$BUMP")
  info "Auto bump: v${CURRENT_VERSION} → v${VERSION} (${BUMP})"
else
  # Validate explicit semver format
  if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$'; then
    fatal "Invalid version format: '$VERSION' (expected semver, e.g. 1.0.1)"
  fi
  info "Explicit version: v${CURRENT_VERSION} → v${VERSION}"
fi

echo ""
info "Project directory: ${BOLD}$PROJECT_DIR${NC}"
info "Target version:    ${BOLD}v$VERSION${NC}"
if [[ -n "$DISPLAY_NAME" ]]; then
  info "Display name:      ${BOLD}$DISPLAY_NAME${NC}"
fi
info "Retry config:      ${BOLD}${MAX_RETRIES} attempts, ${TIMEOUT}s timeout, ${RETRY_DELAY}s delay${NC}"
if $DRY_RUN; then
  warn "DRY RUN mode — no files will be modified"
fi
echo ""

# ── Pre-flight Checks ───────────────────────────────────────
if ! $SKIP_CHECKS; then
  info "Running pre-flight checks..."

  # 1. Check clawhub CLI
  if command -v clawhub &>/dev/null; then
    CLAWHUB_VER=$(clawhub --version 2>/dev/null || echo "unknown")
    success "clawhub CLI available ($CLAWHUB_VER)"
  else
    fatal "clawhub CLI not found. Install it first: npm install -g @clawhub/cli"
  fi

  # 2. Check required files exist
  REQUIRED_FILES=("SKILL.md" "package.json" "_meta.json")
  for f in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$PROJECT_DIR/$f" ]]; then
      fatal "Required file missing: $f"
    fi
  done
  success "Required files present (SKILL.md, package.json, _meta.json)"

  # 3. Check scripts directory
  if [[ ! -d "$PROJECT_DIR/scripts" ]]; then
    fatal "Scripts directory missing"
  fi
  SCRIPT_COUNT=$(find "$PROJECT_DIR/scripts" -name "*.js" -o -name "*.py" | wc -l | tr -d ' ')
  success "Scripts directory OK ($SCRIPT_COUNT scripts found)"

  # 4. Check references directory
  if [[ ! -d "$PROJECT_DIR/references" ]]; then
    fatal "References directory missing"
  fi
  REF_COUNT=$(find "$PROJECT_DIR/references" -name "*.md" | wc -l | tr -d ' ')
  success "References directory OK ($REF_COUNT framework files found)"

  # 5. Node.js dependencies — intentionally ignored during publish.
  # node_modules is excluded via .clawhubignore; the ClawHub runtime installs
  # required packages on demand. We keep this check informational only.
  if [[ -f "$PROJECT_DIR/package.json" ]]; then
    if [[ -d "$PROJECT_DIR/node_modules" ]]; then
      info "node_modules present locally (ignored by .clawhubignore — not published)"
    else
      info "node_modules absent (OK — installed on demand by runtime)"
    fi
  fi

  # 6. Check git status
  if command -v git &>/dev/null && [[ -d "$PROJECT_DIR/.git" ]]; then
    DIRTY_FILES=$(cd "$PROJECT_DIR" && git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$DIRTY_FILES" -gt 0 ]]; then
      warn "Working directory has $DIRTY_FILES uncommitted change(s)"
    else
      success "Git working directory clean"
    fi
  fi

  echo ""
fi

# ── Sync Versions Across Files ───────────────────────────────
info "Syncing version to v$VERSION across all files..."

# Update _meta.json
if ! $DRY_RUN; then
  python3 -c "
import json
path = '$PROJECT_DIR/_meta.json'
with open(path, 'r') as f:
    data = json.load(f)
data['version'] = '$VERSION'
with open(path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
"
  success "_meta.json → v$VERSION"
else
  success "_meta.json → v$VERSION (dry-run)"
fi

# Update package.json
if ! $DRY_RUN; then
  python3 -c "
import json
path = '$PROJECT_DIR/package.json'
with open(path, 'r') as f:
    data = json.load(f)
data['version'] = '$VERSION'
with open(path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
"
  success "package.json → v$VERSION"
else
  success "package.json → v$VERSION (dry-run)"
fi

# Update SKILL.md
if ! $DRY_RUN; then
  if grep -q "^version:" "$PROJECT_DIR/SKILL.md"; then
    sed -i '' "s/^version: .*/version: $VERSION/" "$PROJECT_DIR/SKILL.md"
    success "SKILL.md → v$VERSION"
  else
    warn "No version field found in SKILL.md — skipped"
  fi
else
  success "SKILL.md → v$VERSION (dry-run)"
fi

# Update display name if provided
if [[ -n "$DISPLAY_NAME" ]]; then
  if ! $DRY_RUN; then
    if grep -q "^name:" "$PROJECT_DIR/SKILL.md"; then
      sed -i '' "s/^name: .*/name: $DISPLAY_NAME/" "$PROJECT_DIR/SKILL.md"
      success "SKILL.md name → $DISPLAY_NAME"
    fi
    python3 -c "
import json
path = '$PROJECT_DIR/package.json'
with open(path, 'r') as f:
    data = json.load(f)
data['displayName'] = '$DISPLAY_NAME'
with open(path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
"
    success "package.json displayName → $DISPLAY_NAME"
  fi
fi

echo ""

# ── Git Operations ───────────────────────────────────────────
if ! $SKIP_GIT && ! $DRY_RUN; then
  if command -v git &>/dev/null && [[ -d "$PROJECT_DIR/.git" ]]; then
    info "Committing version bump..."
    (
      cd "$PROJECT_DIR"
      git add _meta.json package.json SKILL.md
      git commit -m "chore: release v$VERSION" -m "Published as: ${DISPLAY_NAME:-fortune-master-ultimate}" --allow-empty
    )
    success "Committed: chore: release v$VERSION"

    info "Creating git tag v$VERSION..."
    (
      cd "$PROJECT_DIR"
      # Delete existing tag if present (for retries on same version)
      git tag -d "v$VERSION" 2>/dev/null || true
      git tag -a "v$VERSION" -m "Release v$VERSION — ${DISPLAY_NAME:-fortune-master-ultimate}"
    )
    success "Tagged: v$VERSION"
  else
    warn "Git not available or not a git repo — skipping git operations"
  fi
elif $DRY_RUN; then
  info "Git commit & tag (dry-run, skipped)"
fi

echo ""

# ── Publish with Retry ───────────────────────────────────────
info "Publishing to ClawHub..."
echo ""

# Build the clawhub publish command
CMD=(clawhub publish "$PROJECT_DIR" --version "$VERSION")
[[ -n "$DISPLAY_NAME" ]] && CMD+=(--name "$DISPLAY_NAME")
[[ -n "$SLUG" ]]         && CMD+=(--slug "$SLUG")
[[ -n "$CHANGELOG" ]]    && CMD+=(--changelog "$CHANGELOG")
[[ -n "$FORK_OF" ]]      && CMD+=(--fork-of "$FORK_OF")
[[ -n "$TAGS" ]]          && CMD+=(--tags "$TAGS")

# Display the command
echo -e "  ${BOLD}\$ ${CMD[*]}${NC}"
echo ""

if $DRY_RUN; then
  info "Dry run — skipping actual publish"
  echo ""
else
  ATTEMPT=0
  PUBLISH_SUCCESS=false

  while [[ $ATTEMPT -lt $MAX_RETRIES ]]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo -e "  ${CYAN}⏳${NC} Attempt ${BOLD}${ATTEMPT}/${MAX_RETRIES}${NC} (timeout: ${TIMEOUT}s)..."

    # Run clawhub publish with timeout
    set +e
    if command -v gtimeout &>/dev/null; then
      # macOS with coreutils (brew install coreutils)
      TIMEOUT_CMD="gtimeout"
    elif command -v timeout &>/dev/null; then
      # Linux / GNU timeout
      TIMEOUT_CMD="timeout"
    else
      # Fallback: no timeout command available, use background + wait
      TIMEOUT_CMD=""
    fi

    if [[ -n "$TIMEOUT_CMD" ]]; then
      OUTPUT=$("$TIMEOUT_CMD" "$TIMEOUT" "${CMD[@]}" 2>&1)
      EXIT_CODE=$?
    else
      # Manual timeout using background process
      "${CMD[@]}" &
      PID=$!
      ELAPSED=0
      while kill -0 "$PID" 2>/dev/null && [[ $ELAPSED -lt $TIMEOUT ]]; do
        sleep 1
        ELAPSED=$((ELAPSED + 1))
      done
      if kill -0 "$PID" 2>/dev/null; then
        kill -9 "$PID" 2>/dev/null
        wait "$PID" 2>/dev/null
        EXIT_CODE=124  # simulate timeout exit code
        OUTPUT="Timeout after ${TIMEOUT}s"
      else
        wait "$PID"
        EXIT_CODE=$?
        OUTPUT=""
      fi
    fi
    set -e

    if [[ $EXIT_CODE -eq 0 ]]; then
      PUBLISH_SUCCESS=true
      echo -e "  ${GREEN}✔${NC}  Publish succeeded on attempt ${ATTEMPT}!"
      [[ -n "$OUTPUT" ]] && echo "$OUTPUT"
      break
    elif [[ $EXIT_CODE -eq 124 ]]; then
      # Timeout
      warn "Attempt ${ATTEMPT} timed out after ${TIMEOUT}s"
    else
      # Other error
      warn "Attempt ${ATTEMPT} failed (exit code: ${EXIT_CODE})"
      [[ -n "$OUTPUT" ]] && echo -e "     ${RED}${OUTPUT}${NC}"
    fi

    if [[ $ATTEMPT -lt $MAX_RETRIES ]]; then
      info "Retrying in ${RETRY_DELAY}s..."
      sleep "$RETRY_DELAY"
    fi
  done

  echo ""

  if ! $PUBLISH_SUCCESS; then
    error "All ${MAX_RETRIES} publish attempts failed!"
    echo ""
    echo -e "  ${YELLOW}Suggestions:${NC}"
    echo "  1. Check your network connection"
    echo "  2. Verify clawhub login: clawhub whoami"
    echo "  3. Try with longer timeout: --timeout 180"
    echo "  4. Try with more retries: --retries 5"
    echo "  5. Manual publish: ${CMD[*]}"
    echo ""
    exit 1
  fi
fi

# ── Summary ──────────────────────────────────────────────────
echo "  ─────────────────────────────────────────"
echo -e "  ${GREEN}${BOLD}☯️  Published successfully!${NC}"
echo ""
echo -e "  Skill:   ${BOLD}fortune-master-ultimate${NC}"
echo -e "  Name:    ${BOLD}${DISPLAY_NAME:-命理大师}${NC}"
echo -e "  Version: ${BOLD}v$VERSION${NC}"
echo -e "  URL:     ${CYAN}https://clawhub.com/skills/fortune-master-ultimate${NC}"
echo "  ─────────────────────────────────────────"
echo ""

if $DRY_RUN; then
  warn "This was a dry run. No changes were made."
  echo ""
fi
