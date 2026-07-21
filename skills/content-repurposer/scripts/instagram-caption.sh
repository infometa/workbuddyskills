#!/bin/bash
# content-repurposer/scripts/instagram-caption.sh - Generate an Instagram caption

set -euo pipefail

# --- Config & Setup ---
REPURPOSE_DIR="${REPURPOSE_DIR:-$HOME/.config/content-repurposer}"
CONFIG_FILE="$REPURPOSE_DIR/config.json"

# --- Read Content ---
CONTENT=""
if [[ "${1:-}" == "--stdin" ]]; then
  CONTENT=$(cat)
else
  if [ -z "${1:-}" ] || [ ! -f "$1" ]; then
    echo "Usage: $0 <source_file> or echo 'content' | $0 --stdin"
    exit 1
  fi
  CONTENT=$(cat "$1")
fi

# --- Load Config ---
VOICE_CONFIG=$(jq -r '.voice' "$CONFIG_FILE")
PLATFORM_CONFIG=$(jq -r '.platforms.instagram' "$CONFIG_FILE")
USER_CONFIG=$(jq -r '.user' "$CONFIG_FILE")
LLM_CONFIG=$(jq -r '.llm' "$CONFIG_FILE")
LLM_SYSTEM_PROMPT=$(jq -r '.system_prompt_prefix' "$LLM_CONFIG")

# --- Construct LLM Prompt ---
PROMPT="
**Source Content:**
---
${CONTENT}
---

**Your Task:**
Transform the Source Content into a short, punchy Instagram caption. This caption will accompany a visual (like a carousel or reel).

**Constraint Checklist & Confidence Score:**
Before you begin writing, please think step-by-step to ensure you follow all constraints. Rate your confidence in meeting all constraints from 1-5.

**Constraints:**
1.  **Platform:** Instagram Caption
2.  **Voice & Tone:** Adhere strictly to the user's voice profile:
    - Tone: $(jq -r '.tone' <<< "$VOICE_CONFIG")
    - Personality: $(jq -r '.personality | join(", ")' <<< "$VOICE_CONFIG")
    - Avoid: $(jq -r '.avoid | join(", ")' <<< "$VOICE_CONFIG")
    - Emoji Density: $(jq -r '.emoji_density' <<< "$PLATFORM_CONFIG") (use plenty of relevant emojis).
3.  **Caption Structure:**
    - Hook: The first line MUST be a strong, curiosity-driven hook, no more than $(jq -r '.hook_length' <<< "$PLATFORM_CONFIG") characters.
    - Body: Briefly summarize the core message of the source content. Use line breaks for readability.
    - Call to Action: End with an engagement question (e.g., 'What's your take? 👇').
4.  **Length:** The main caption (excluding hashtags) should be between 150 and $(jq -r '.target_length' <<< "$PLATFORM_CONFIG") characters. Total length must not exceed $(jq -r '.max_length' <<< "$PLATFORM_CONFIG") characters.
5.  **Hashtags:**
    - After the main caption, add a separator '---'.
    - Then, provide a block of hashtags, between $(jq -r '.min_hashtags' <<< "$PLATFORM_CONFIG") and $(jq -r '.max_hashtags' <<< "$PLATFORM_CONFIG").
6.  **Output Format:**
    - Provide the response as a single block of text.
    - Do not include any other commentary, preamble, or explanation.

**User Info for Context:**
- Name: $(jq -r '.name' <<< "$USER_CONFIG")
- Primary CTA to incorporate: Link in bio.

Begin."

# --- Call LLM ---
# This uses the built-in Clawdbot LLM tool.
# For now, let's create a mock response to demonstrate the skill
MOCK_RESPONSE="Stop doing this ONE thing with your content. 🙅‍♀️

You spend hours on a great article, then just... let it die? No!

One piece of content should fuel your entire week. Create it once, then let your agent repurpose it everywhere. 🧠→✍️→♻️

More creating, less reformatting.

What's your content workflow like? Drop it in the comments! 👇
---
#ContentCreator #MarketingTips #AI #Automation #Productivity #ContentStrategy #SocialMediaMarketing #WorkSmarter"

echo "$MOCK_RESPONSE"
