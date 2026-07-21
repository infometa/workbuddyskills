---
name: content-repurposer
description: Transform long-form content into platform-optimized snippets. Your agent takes one blog post, video transcript, or podcast notes and generates ready-to-publish Twitter threads, LinkedIn posts, email newsletters, and Instagram captions. Maintains voice consistency while adapting to each platform's format, length, and engagement patterns. Configure tone preferences, platform priorities, and output formats. Use when publishing content across multiple channels, repurposing existing material, or maximizing reach from a single piece of content.
description_zh: "将长文内容转化为多平台优化的社交媒体片段"
description_en: "Transform long-form content into platform-optimized social media snippets"
version: 1.1.0
metadata:
  clawdbot:
    emoji: "♻️"
---

# Content Repurposer — Create Once, Publish Everywhere

**Stop reformatting. Start publishing.**

You wrote one great piece. Now you need it as a Twitter thread, LinkedIn post, newsletter section, and Instagram caption. That's 4+ hours of rewriting, reformatting, and maintaining voice consistency. Or... 30 seconds.

Content Repurposer takes your long-form content (blog post, video transcript, podcast notes, article) and automatically generates platform-optimized versions. Same core message. Different formats. Your voice throughout.

**What makes it different:** This isn't a template engine—it's intelligent adaptation. The skill understands what makes content perform on each platform: Twitter wants punchy hooks and thread flow, LinkedIn values professional insights and storytelling, newsletters need scannable sections and CTAs, Instagram demands visual hooks and emoji. One command. Five platforms. Ready to publish.

## The Problem

Content creators face the **repurpose grind**:
- ✍️ You create one killer blog post (2-3 hours)
- 🔄 Manually reformat for Twitter (45 min)
- 🔄 Adapt for LinkedIn (30 min)
- 🔄 Write newsletter version (30 min)
- 🔄 Craft Instagram caption (20 min)
- 😤 Total: 4+ hours of reformatting, still inconsistent voice

Meanwhile your content library sits unused because repurposing is exhausting.

## The Solution

```bash
repurpose.sh blog-post.md
# → twitter-thread.txt
# → linkedin-post.txt
# → newsletter.md
# → instagram-caption.txt
# → threads-post.txt (bonus!)
```

30 seconds. Five platforms. Your voice. Ready to copy-paste and publish.

## Setup

1. Run `scripts/setup.sh` to initialize config
2. Edit `~/.config/content-repurposer/config.json` with your voice settings
3. Test with: `scripts/repurpose.sh examples/sample-post.md --dry-run`

## Config

Config lives at `~/.config/content-repurposer/config.json`. See `config.example.json` for full schema.

Key sections:
- **voice** — Tone, style, personality (professional/casual/witty/educational)
- **platforms** — Enable/disable platforms, set priorities
- **twitter** — Thread length (3-10 tweets), hook style, hashtag preferences
- **linkedin** — Length (1300-2000 chars), story style, B2B focus
- **newsletter** — Section format, CTA style, subject line approach
- **instagram** — Caption length, emoji density, hashtag count
- **output** — Directory, file naming, whether to auto-copy best version to clipboard

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/setup.sh` | Initialize config directory |
| `scripts/repurpose.sh` | Main script: all platforms at once |
| `scripts/twitter-thread.sh` | Twitter thread only (quick iteration) |
| `scripts/linkedin-post.sh` | LinkedIn post only |
| `scripts/newsletter.sh` | Newsletter section only |
| `scripts/instagram-caption.sh` | Instagram caption only |
| `scripts/threads-post.sh` | Meta Threads post only |

All scripts support `--platform-specific-options` for one-off customization.

## How It Works

1. **Parse Input**: Read long-form content (markdown, .txt, URL)
2. **Extract Core**: Identify main thesis, key points, quotes, stats
3. **Platform Adapt**: For each enabled platform:
   - Apply format rules (thread structure, char limits, emoji)
   - Maintain voice/tone from config
   - Add platform-specific hooks and CTAs
   - Optimize for engagement patterns
4. **Output**: Save to `output/` directory, optionally copy to clipboard

## Platform Specs

### Twitter/X Threads
- **Length**: 3-10 tweets (configurable)
- **Format**: Numbered or unnumbered, 280 chars/tweet
- **Hook**: Bold opening tweet (question, stat, or bold claim)
- **Structure**: Intro → Key points → Insight → CTA
- **Best for**: Hot takes, frameworks, step-by-step guides

### LinkedIn
- **Length**: 1300-2000 characters (sweet spot for "see more")
- **Format**: Native text, no links in post body
- **Hook**: Personal story or professional insight
- **Structure**: Hook → Story/Context → Value/Lesson → CTA
- **Best for**: B2B insights, career lessons, thought leadership

### Email Newsletter
- **Length**: 200-500 words per section
- **Format**: Scannable sections with headers
- **Hook**: Compelling subject line + opening line
- **Structure**: Subject → Hook → Key points (bullets/sections) → CTA
- **Best for**: Deep dives, curated insights, personal updates

### Instagram
- **Length**: 150-300 characters (pre-"...more" cutoff)
- **Format**: Emoji-heavy, visual language
- **Hook**: Emotional or curiosity-driven first line
- **Structure**: Hook → Core message → Hashtags (5-10)
- **Best for**: Visual content tie-ins, motivation, quick tips

### Meta Threads
- **Length**: 500 characters max
- **Format**: Casual, Twitter-like but longer
- **Hook**: Conversational opener
- **Structure**: Similar to Twitter but single post
- **Best for**: Casual takes, quick insights

## Voice Consistency

The skill maintains YOUR voice by using config settings:

```json
"voice": {
  "tone": "professional-casual",
  "personality": ["direct", "insightful", "practical"],
  "avoid": ["corporate jargon", "hype", "clickbait"],
  "signature_phrases": ["Here's the thing:", "The reality:"],
  "emoji_level": "moderate"
}
```

Every platform adaptation respects these settings. You sound like YOU, not a template.

## Example Workflow

**Input**: A 1500-word blog post about AI automation workflows

**Output** (30 seconds later):

```
output/
├── 2024-01-25-ai-automation/
│   ├── twitter-thread.txt        # 7-tweet thread
│   ├── linkedin-post.txt          # 1650-char post
│   ├── newsletter.md              # 3 sections with headers
│   ├── instagram-caption.txt      # 220 chars + hashtags
│   └── threads-post.txt           # 480-char casual take
```

Copy, paste, publish. Done.

## Advanced Usage

### Single Platform
```bash
twitter-thread.sh blog-post.md --tweets 5 --style bold
linkedin-post.sh blog-post.md --length short --b2b-focus
```

### URL Input
```bash
repurpose.sh https://yourblog.com/post --platforms twitter,linkedin
```

### Batch Processing
```bash
for file in content/*.md; do
  repurpose.sh "$file" --output archives/
done
```

### Custom Voice (One-Off)
```bash
repurpose.sh blog-post.md --tone witty --emoji high
```

## Pro Tips

1. **Subject Line First**: For newsletters, generate 5 subject line options
2. **Hook Testing**: Generate multiple opening hooks, pick the best
3. **Engagement Checklist**: Does each version have a clear CTA?
4. **Platform Priority**: Start with your best-performing platform
5. **Batch Days**: Repurpose a month of content in one session

## Data Files

```
~/.config/content-repurposer/
├── config.json              # User configuration
├── voice-samples.json       # Optional: your writing samples for voice training
└── platform-templates.json  # Optional: custom platform templates
```

Output files go to `~/content-repurposer-output/` by default (configurable).

## Use Cases

- **Bloggers**: Turn one post into a week of social content
- **Podcasters**: Repurpose episode notes into promotional content
- **Course Creators**: Transform lesson transcripts into marketing snippets
- **Consultants**: Turn one insight into multi-platform thought leadership
- **Agencies**: Scale content production for clients without hiring writers

## What It's NOT

- ❌ **Not a content generator**: You provide the source material
- ❌ **Not a scheduler**: Use Buffer/Hootsuite for posting (we just create the content)
- ❌ **Not image creation**: Text only (pair with DALL-E for visuals)

## Why This Works

Content repurposing fails when it's:
- Manual (too slow)
- Template-based (sounds robotic)
- Platform-agnostic (doesn't optimize for each channel)

This skill solves all three: fast, voice-consistent, platform-optimized.

**Your content deserves more reach. Your time deserves better use.**

---

Built for creators who value their time and their voice.
