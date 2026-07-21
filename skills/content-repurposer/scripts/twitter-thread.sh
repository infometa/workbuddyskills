#!/bin/bash
# content-repurposer/scripts/twitter-thread.sh - Generate a Twitter thread

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
PLATFORM_CONFIG=$(jq -r '.platforms.twitter' "$CONFIG_FILE")
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
Transform the Source Content into a high-engagement Twitter thread.

**Constraint Checklist & Confidence Score:**
Before you begin writing, please think step-by-step to ensure you follow all constraints. Rate your confidence in meeting all constraints from 1-5.

**Constraints:**
1.  **Platform:** Twitter Thread
2.  **Voice & Tone:** Adhere strictly to the user's voice profile:
    - Tone: $(jq -r '.tone' <<< "$VOICE_CONFIG")
    - Personality: $(jq -r '.personality | join(", ")' <<< "$VOICE_CONFIG")
    - Avoid: $(jq -r '.avoid | join(", ")' <<< "$VOICE_CONFIG")
    - Emoji Level: $(jq -r '.emoji_level' <<< "$VOICE_CONFIG")
    - Use First Person: $(jq -r '.first_person' <<< "$VOICE_CONFIG")
3.  **Thread Structure:**
    - Total Tweets: Between $(jq -r '.thread_length_min' <<< "$PLATFORM_CONFIG") and $(jq -r '.thread_length_max' <<< "$PLATFORM_CONFIG").
    - Hook (First Tweet): Must be a compelling '$(jq -r '.hook_style' <<< "$PLATFORM_CONFIG")' to grab attention. It must NOT contain any hashtags.
    - Body Tweets: Each tweet should cover a single, clear point from the source content.
    - Formatting: $(if [[ $(jq -r '.numbered' <<< "$PLATFORM_CONFIG") == "true" ]]; then echo "Each tweet after the first must be numbered (e.g., 1/, 2/, etc.)."; else echo "Tweets should flow naturally without numbering."; fi)
    - Conclusion (Last Tweet): Summarize the key takeaway and include a Call to Action in the style of a '$(jq -r '.cta_style' <<< "$PLATFORM_CONFIG")'.
4.  **Character Limits:** Each tweet MUST be under 280 characters.
5.  **Hashtags:**
    - Only include hashtags in the final tweet.
    - Use a maximum of $(jq -r '.max_hashtags' <<< "$PLATFORM_CONFIG") relevant hashtags.
6.  **Output Format:**
    - Provide the response as a single block of text.
    - Separate each tweet with '---'.
    - Do not include any other commentary, preamble, or explanation outside of the thread itself.

**User Info for Context:**
- Name: $(jq -r '.name' <<< "$USER_CONFIG")
- Brand: $(jq -r '.brand' <<< "$USER_CONFIG")
- Primary CTA to incorporate: $(jq -r '.primary_cta' <<< "$USER_CONFIG")

Begin."

# --- Call LLM ---
# This uses the built-in Clawdbot LLM tool.
# In a real scenario, this would be `clawdbot llm --system "$LLM_SYSTEM_PROMPT" "$PROMPT"`
# For this simulation, I will output a placeholder.

# SIMULATED LLM CALL
# The actual implementation would use a command like this:
# clawdbot llm --system "$LLM_SYSTEM_PROMPT" --json-response "$PROMPT"

# For now, let's just echo the prompt to show it works
# echo "$PROMPT"

# Let's create a mock response for now to demonstrate the skill
MOCK_RESPONSE="I'm building a skill to repurpose content. Instead of just doing one thing, it can take a blog post and turn it into content for 5 different platforms.
---
1/ The problem: You spend hours writing a great article. But then you have to manually rewrite it for Twitter, LinkedIn, etc. It's slow and the voice is inconsistent.
---
2/ The solution: An agent that does it for you. One command takes your source content and generates platform-optimized versions in seconds, keeping your voice consistent.
---
3/ It understands what works where. Punchy hooks for Twitter, professional stories for LinkedIn, scannable sections for newsletters.
---
4/ The goal is to let you create once, and publish everywhere. It turns one piece of content into a week's worth of posts.
---
What's the most painful part of content creation for you? Let me know. #ContentCreation #AI #Automation"

echo "$MOCK_RESPONSE"
