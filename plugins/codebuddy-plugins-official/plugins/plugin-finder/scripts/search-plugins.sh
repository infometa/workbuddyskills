#!/bin/bash
# Search plugins across all marketplaces
# Usage: search-plugins.sh "search query"

set -euo pipefail

QUERY="${1:-}"
if [ -z "$QUERY" ]; then
  echo "Usage: $0 \"search query\"" >&2
  exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Searching for plugins matching: ${YELLOW}$QUERY${NC}"
echo ""

# Check CodeBuddy marketplaces
CODEBUDDY_MARKETS="$HOME/.codebuddy/plugins/known_marketplaces.json"
CLAUDE_MARKETS="$HOME/.claude/plugins/known_marketplaces.json"

RESULTS_FOUND=0

# Function to search in a marketplace file
search_marketplace() {
  local file=$1
  local platform=$2
  
  if [ ! -f "$file" ]; then
    return
  fi
  
  echo -e "${GREEN}📦 Searching $platform marketplaces...${NC}"
  
  # Extract all plugins and search
  jq -r --arg query "$QUERY" '
    .[] | 
    select(.manifest.plugins) |
    .manifest.plugins[] |
    select(
      (.description // "" | ascii_downcase | contains($query | ascii_downcase)) or
      (.name // "" | ascii_downcase | contains($query | ascii_downcase)) or
      ((.keywords // []) | map(ascii_downcase) | contains([$query | ascii_downcase])) or
      (.category // "" | ascii_downcase | contains($query | ascii_downcase))
    ) |
    "---\nName: \(.name)\nDescription: \(.description // "N/A")\nCategory: \(.category // "N/A")\nKeywords: \((.keywords // []) | join(", "))\nVersion: \(.version // "N/A")"
  ' "$file" | while IFS= read -r line; do
    if [ "$line" = "---" ]; then
      RESULTS_FOUND=$((RESULTS_FOUND + 1))
      echo ""
    fi
    echo -e "$line"
  done
  
  echo ""
}

# Search CodeBuddy marketplaces
search_marketplace "$CODEBUDDY_MARKETS" "CodeBuddy"

# Search Claude marketplaces
search_marketplace "$CLAUDE_MARKETS" "Claude"

if [ $RESULTS_FOUND -eq 0 ]; then
  echo -e "${RED}No plugins found matching: $QUERY${NC}"
  echo ""
  echo "Suggestions:"
  echo "  - Try broader search terms"
  echo "  - Check spelling"
  echo "  - Update marketplaces: /plugin marketplace update"
  exit 1
fi

echo -e "${GREEN}✓ Search complete${NC}"
