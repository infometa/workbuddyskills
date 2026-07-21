#!/bin/bash
# content-repurposer/scripts/linkedin-post.sh - Generate a LinkedIn post

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
PLATFORM_CONFIG=$(jq -r '.platforms.linkedin' "$CONFIG_FILE")
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
Transform the Source Content into a high-engagement LinkedIn post.

**Constraint Checklist & Confidence Score:**
Before you begin writing, please think step-by-step to ensure you follow all constraints. Rate your confidence in meeting all constraints from 1-5.

**Constraints:**
1.  **Platform:** LinkedIn Post
2.  **Voice & Tone:** Adhere strictly to the user's voice profile:
    - Tone: $(jq -r '.tone' <<< "$VOICE_CONFIG")
    - Personality: $(jq -r '.personality | join(", ")' <<< "$VOICE_CONFIG")
    - Avoid: $(jq -r '.avoid | join(", ")' <<< "$VOICE_CONFIG")
    - Emoji Level: $(jq -r '.emoji_level' <<< "$VOICE_CONFIG")
    - Use First Person: $(jq -r '.first_person' <<< "$VOICE_CONFIG")
3.  **Post Structure:**
    - Hook: Start with a compelling '$(jq -r '.hook_style' <<< "$PLATFORM_CONFIG")' to encourage clicks on '...see more'.
    - Body: Elaborate on the key points from the source content. Use short paragraphs and bullet points for readability. $(if [[ $(jq -r '.include_story' <<< "$PLATFORM_CONFIG") == "true" ]]; then echo "Weave in a personal story or professional insight if possible."; fi)
    - Focus: Maintain a $(if [[ $(jq -r '.b2b_focus' <<< "$PLATFORM_CONFIG") == "true" ]]; then echo "strong B2B/professional focus."; else echo "general audience focus."; fi)
    - Conclusion: End with a clear Call to Action or an engaging question for the comments.
4.  **Length:** The total post length should be between $(jq -r '.min_length' <<< "$PLATFORM_CONFIG") and $(jq -r '.max_length' <<< "$PLATFORM_CONFIG") characters.
5.  **Formatting:**
    - Do NOT include any links in the main body of the post.
    - Use whitespace and line breaks effectively to make the post scannable.
6.  **Hashtags:**
    - Include a block of $(jq -r '.max_hashtags' <<< "$PLATFORM_CONFIG") relevant hashtags at the very end of the post.
7.  **Output Format:**
    - Provide the response as a single block of text.
    - Do not include any other commentary, preamble, or explanation.

**User Info for Context:**
- Name: $(jq -r '.name' <<< "$USER_CONFIG")
- Brand: $(jq -r '.brand' <<< "$USER_CONFIG")
- Primary CTA to incorporate in the conclusion: $(jq -r '.primary_cta' <<< "$USER_CONFIG")

Begin."

# --- Call LLM ---
# This uses the built-in Clawdbot LLM tool.
# For now, let's create a mock response to demonstrate the skill
MOCK_RESPONSE="The biggest bottleneck in content isn't creation, it's distribution.

You can spend 4 hours on a killer blog post, but that's just the start. Then comes the 'repurpose grind': manually reformatting that same piece for Twitter, LinkedIn, your newsletter...

It's a soul-crushing time sink, and the result is often inconsistent messaging across platforms.

I've been building an agent-based solution to this problem. The concept is simple: 'Create Once, Publish Everywhere'.

Here's how it works:
→ You feed it one piece of long-form content (blog post, transcript, etc.).
→ The agent analyzes the core message and your unique voice.
→ It then generates optimized snippets for every major platform, automatically.

It understands the nuances:
• Twitter gets a punchy, multi-tweet thread.
• LinkedIn gets a professional, story-driven post (like this one).
• Your newsletter gets scannable, value-packed sections.

The goal is to turn one piece of content into a week's worth of high-quality posts, saving creators hours of manual work. It's not about replacing creativity; it's about automating the mechanical parts so we can focus on the big ideas.

What's your biggest time-sink when it comes to content?

#ContentMarketing #AI #Automation #Productivity #Marketing"

echo "$MOCK_RESPONSE"
