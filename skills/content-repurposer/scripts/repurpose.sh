#!/bin/bash
# content-repurposer/scripts/repurpose.sh — Main repurposing script

set -euo pipefail

# --- Config & Setup ---
REPURPOSE_DIR="${REPURPOSE_DIR:-$HOME/.config/content-repurposer}"
CONFIG_FILE="$REPURPOSE_DIR/config.json"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_DIR="$SKILL_DIR/scripts"

# --- Helper Functions ---
function print_usage() {
  echo "Usage: $0 <source_file_or_url> [options]"
  echo ""
  echo "Options:"
  echo "  --platforms <p1,p2>   Repurpose for specific platforms (e.g., twitter,linkedin)"
  echo "  --output-dir <path>     Override output directory"
  echo "  --dry-run               Print prompts instead of executing them"
  echo "  --help                  Show this help message"
}

function slugify() {
  echo "$1" | iconv -t ascii//TRANSLIT | sed -r s/[^a-zA-Z0-9]+/-/g | sed -r s/^-+\|-+$//g | tr A-Z a-z
}

# --- Argument Parsing ---
if [[ "$#" -eq 0 || "$1" == "--help" ]]; then
  print_usage
  exit 0
fi

SOURCE_INPUT="$1"
shift

PLATFORMS_OVERRIDE=""
OUTPUT_DIR_OVERRIDE=""
DRY_RUN=false

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --platforms) PLATFORMS_OVERRIDE="$2"; shift ;;
    --output-dir) OUTPUT_DIR_OVERRIDE="$2"; shift ;;
    --dry-run) DRY_RUN=true ;;
    *) echo "Unknown parameter passed: $1"; print_usage; exit 1 ;;
  esac
  shift
done

# --- Pre-flight Checks ---
if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ Error: Config file not found at $CONFIG_FILE"
  echo "Run 'scripts/setup.sh' first."
  exit 1
fi

# --- Read Source Content ---
CONTENT=""
if [[ "$SOURCE_INPUT" =~ ^https?:// ]]; then
  echo "🌐 Fetching content from URL: $SOURCE_INPUT"
  # Use Clawdbot's web_fetch tool if available, otherwise fallback to curl
  if command -v clawdbot &> /dev/null && clawdbot tool-exists web_fetch; then
    CONTENT=$(clawdbot web_fetch --url "$SOURCE_INPUT" --extractMode text)
  else
    CONTENT=$(curl -sL "$SOURCE_INPUT" | html2text) # requires html2text
  fi
  SOURCE_SLUG=$(slugify "$(basename "$SOURCE_INPUT")")
else
  if [ ! -f "$SOURCE_INPUT" ]; then
    echo "❌ Error: Source file not found at $SOURCE_INPUT"
    exit 1
  fi
  echo "📄 Reading content from file: $SOURCE_INPUT"
  CONTENT=$(cat "$SOURCE_INPUT")
  SOURCE_SLUG=$(slugify "$(basename "${SOURCE_INPUT%.*}")")
fi

if [ -z "$CONTENT" ]; then
  echo "❌ Error: Could not read content from source."
  exit 1
fi

# --- Load Config & Prepare Output ---
OUTPUT_DIR=$(jq -r '.output.directory' "$CONFIG_FILE")
if [ -n "$OUTPUT_DIR_OVERRIDE" ]; then
  OUTPUT_DIR="$OUTPUT_DIR_OVERRIDE"
fi
OUTPUT_DIR="${OUTPUT_DIR/#\~/$HOME}" # Expand tilde

DATE_SLUG=$(date +"%Y-%m-%d")
FINAL_DIR="$OUTPUT_DIR/${DATE_SLUG}-${SOURCE_SLUG}"
mkdir -p "$FINAL_DIR"

echo "♻️  Starting content repurposing..."
echo "Source: $SOURCE_INPUT"
echo "Outputting to: $FINAL_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"

# --- Determine Platforms to Run ---
ENABLED_PLATFORMS=()
if [ -n "$PLATFORMS_OVERRIDE" ]; then
    IFS=',' read -r -a ENABLED_PLATFORMS <<< "$PLATFORMS_OVERRIDE"
else
    # Read enabled platforms from config
    while IFS= read -r p; do
        ENABLED_PLATFORMS+=("$p")
    done < <(jq -r '.platforms | to_entries[] | select(.value.enabled == true) | .key' "$CONFIG_FILE")
fi

# --- Main Repurposing Loop ---
for platform in "${ENABLED_PLATFORMS[@]}"; do
  PLATFORM_SCRIPT="${SCRIPT_DIR}/${platform}-post.sh"
  # twitter special case
  if [ "$platform" == "twitter" ]; then
    PLATFORM_SCRIPT="${SCRIPT_DIR}/twitter-thread.sh"
  elif [ "$platform" == "newsletter" ]; then
     PLATFORM_SCRIPT="${SCRIPT_DIR}/newsletter.sh"
  fi

  if [ ! -f "$PLATFORM_SCRIPT" ]; then
    echo "⚠️  Warning: Script for platform '$platform' not found at $PLATFORM_SCRIPT. Skipping."
    continue
  fi

  echo "➡️  Processing for: $platform"

  if $DRY_RUN; then
    echo "DRY RUN: Would execute..."
    echo "cat <<EOF | $PLATFORM_SCRIPT --stdin"
    echo "$CONTENT"
    echo "EOF"
    echo "-------------------------"
  else
    OUTPUT_FILE="$FINAL_DIR/${platform}.txt"
    if [ "$platform" == "newsletter" ]; then
      OUTPUT_FILE="$FINAL_DIR/${platform}.md"
    fi

    # Pass content via stdin to the platform script
    RESULT=$(echo "$CONTENT" | "$PLATFORM_SCRIPT" --stdin)

    if [ -n "$RESULT" ]; then
      echo "$RESULT" > "$OUTPUT_FILE"
      echo "✓ Saved to $(basename "$OUTPUT_FILE")"
    else
      echo "❌ Failed to generate content for $platform"
    fi
  fi
done

echo ""
echo "✅ Repurposing complete!"
echo "Find your content in: $FINAL_DIR"

# Optional: copy to clipboard
COPY_BEHAVIOR=$(jq -r '.output.copy_to_clipboard' "$CONFIG_FILE")
if [[ "$COPY_BEHAVIOR" != "none" && "$DRY_RUN" == false ]]; then
    # Find the highest priority platform that was generated
    HIGHEST_PRIORITY_PLATFORM=$(jq -r '[.platforms | to_entries[] | select(.value.enabled == true) | {key: .key, priority: .value.priority}] | sort_by(.priority) | .[0].key' "$CONFIG_FILE")
    
    if [[ " ${ENABLED_PLATFORMS[*]} " =~ " ${HIGHEST_PRIORITY_PLATFORM} " ]]; then
        FILE_TO_COPY="$FINAL_DIR/${HIGHEST_PRIORITY_PLATFORM}.txt"
         if [ "$HIGHEST_PRIORITY_PLATFORM" == "newsletter" ]; then
            FILE_TO_COPY="$FINAL_DIR/${HIGHEST_PRIORITY_PLATFORM}.md"
         fi
        
        if command -v pbcopy &> /dev/null && [ -f "$FILE_TO_COPY" ]; then
            cat "$FILE_TO_COPY" | pbcopy
            echo "📋 Copied content for '$HIGHEST_PRIORITY_PLATFORM' to clipboard."
        fi
    fi
fi
