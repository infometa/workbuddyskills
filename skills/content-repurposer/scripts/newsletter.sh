#!/bin/bash
# content-repurposer/scripts/newsletter.sh - Generate a newsletter section

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
PLATFORM_CONFIG=$(jq -r '.platforms.newsletter' "$CONFIG_FILE")
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
Transform the Source Content into a compelling email newsletter section.

**Constraint Checklist & Confidence Score:**
Before you begin writing, please think step-by-step to ensure you follow all constraints. Rate your confidence in meeting all constraints from 1-5.

**Constraints:**
1.  **Platform:** Email Newsletter Section
2.  **Voice & Tone:** Adhere strictly to the user's voice profile:
    - Tone: $(jq -r '.tone' <<< "$VOICE_CONFIG")
    - Personality: $(jq -r '.personality | join(", ")' <<< "$VOICE_CONFIG")
    - Avoid: $(jq -r '.avoid | join(", ")' <<< "$VOICE_CONFIG")
    - Emoji Level: $(jq -r '.emoji_level' <<< "$CONFIG_FILE")
    - Use First Person: $(jq -r '.first_person' <<< "$VOICE_CONFIG")
3.  **Newsletter Structure:**
    - Subject Lines: Begin the output with $(jq -r '.subject_line_count' <<< "$PLATFORM_CONFIG") compelling, distinct subject line options, each on its own line and prefixed with 'Subject:'.
    - Separator: After the subject lines, add a '---' separator.
    - Body: The main body should be a '$(jq -r '.section_style' <<< "$PLATFORM_CONFIG")' newsletter section based on the source content. Use markdown for formatting (headers, bold, bullets).
    - Length: The body should be approximately $(jq -r '.target_length' <<< "$PLATFORM_CONFIG") words.
    - CTA: $(if [[ $(jq -r '.include_cta' <<< "$PLATFORM_CONFIG") == "true" ]]; then echo "Include a clear Call to Action at the $(jq -r '.cta_placement' <<< "$PLATFORM_CONFIG") of the body."; else echo "Do not include a Call to Action."; fi)
4.  **Output Format:**
    - Format the body as $(jq -r '.format' <<< "$PLATFORM_CONFIG").
    - Provide the response as a single block of text.
    - Do not include any other commentary, preamble, or explanation.

**User Info for Context:**
- Name: $(jq -r '.name' <<< "$USER_CONFIG")
- Brand: $(jq -r '.brand' <<< "$USER_CONFIG")
- Primary CTA to incorporate: $(jq -r '.primary_cta' <<< "$USER_CONFIG")

Begin."

# --- Call LLM ---
# This uses the built-in Clawdbot LLM tool.
# For now, let's create a mock response to demonstrate the skill
MOCK_RESPONSE="Subject: Stop reformatting, start publishing
Subject: Create once, publish everywhere
Subject: Your new content workflow

---

## The Repurpose Grind Is Killing Your Reach

You spend hours, maybe even days, crafting the perfect blog post. It's insightful, well-researched, and provides genuine value. You hit publish, share it once, and then... it gets lost in the content void.

The problem isn't the quality of your content. It's the friction in your distribution.

To maximize reach, that single blog post needs to become:
- A punchy Twitter thread
- An insightful LinkedIn post
- A quick Instagram caption

But who has the time to manually reformat everything? This 'repurpose grind' is exhausting and leads to inconsistent messaging.

### A Smarter Way to Distribute

I've been working on a new approach using an AI agent. You give it your long-form content, and it intelligently adapts it for each platform, maintaining your unique voice and tone.

It understands the context of each platform, turning one piece of content into a week's worth of posts in about 30 seconds. This isn't about creating *more* content, but getting *more mileage* out of the quality content you're already creating.

The goal is to free you from the mechanical task of reformatting so you can focus on the ideas.

If you want to read more about the framework behind this, check out the original post here: [your link]"

echo "$MOCK_RESPONSE"
