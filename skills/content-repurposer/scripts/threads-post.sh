#!/bin/bash
# content-repurposer/scripts/threads-post.sh - Generate a Meta Threads post

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
PLATFORM_CONFIG=$(jq -r '.platforms.threads' "$CONFIG_FILE")
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
Transform the Source Content into a single, casual post for Meta Threads.

**Constraint Checklist & Confidence Score:**
Before you begin writing, please think step-by-step to ensure you follow all constraints. Rate your confidence in meeting all constraints from 1-5.

**Constraints:**
1.  **Platform:** Meta Threads Post
2.  **Voice & Tone:** Adhere strictly to the user's voice profile:
    - Tone: $(jq -r '.tone' <<< "$VOICE_CONFIG")
    - Personality: $(jq -r '.personality | join(", ")' <<< "$VOICE_CONFIG")
    - Style: Must be '$(jq -r '.style' <<< "$PLATFORM_CONFIG")' and conversational.
3.  **Post Structure:**
    - Single post, not a thread.
    - Get straight to the point.
    - End with an open-ended question to encourage replies.
4.  **Length:** The post MUST be under $(jq -r '.max_length' <<< "$PLATFORM_CONFIG") characters.
5.  **Hashtags:** $(if [[ $(jq -r '.include_hashtags' <<< "$PLATFORM_CONFIG") == "true" ]]; then echo "Include 1-2 relevant hashtags."; else echo "Do not include any hashtags."; fi)
6.  **Output Format:**
    - Provide the response as a single block of text.
    - Do not include any other commentary, preamble, or explanation.

**User Info for Context:**
- Name: $(jq -r '.name' <<< "$USER_CONFIG")

Begin."

# --- Call LLM ---
# This uses the built-in Clawdbot LLM tool.
# For now, let's create a mock response to demonstrate the skill
MOCK_RESPONSE="Just had a thought about content creation. We spend 80% of our time on the core piece and then rush the distribution. It feels backward.

What if we automated the tedious reformatting part? Take one blog post and instantly get the Twitter thread, the LinkedIn version, etc., all in a consistent voice. Frees up so much time for the next big idea.

How much time do you all spend just re-sharing the same thing in different formats?"

echo "$MOCK_RESPONSE"
