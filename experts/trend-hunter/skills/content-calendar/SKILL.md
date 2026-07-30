---
name: content-calendar
version: "1.0.0"
description: Plan, schedule, and track content across channels — newsletters, social media, blog posts, and videos. Manages pipeline stages, publishing cadence, and repurposing opportunities. For solopreneurs and creators who want a system, not a spreadsheet.
tags: [content, calendar, newsletter, social-media, blog, publishing, scheduling, content-strategy, creator, solopreneur, pipeline, repurposing]
platforms: [openclaw, cursor, windsurf, generic]
category: productivity
author: The Agent Ledger
license: CC-BY-NC-4.0
url: https://github.com/theagentledger/agent-skills
---

# Content Calendar

**By The Agent Ledger** — [theagentledger.com](https://theagentledger.com)

Plan, schedule, and track your content pipeline across every channel — without the spreadsheet chaos. This skill gives your agent a structured system for managing content from idea to published, and flagging what's falling behind.

---

## What This Skill Does

Your agent will:
- Maintain a **content pipeline** organized by stage (Idea → Draft → Review → Scheduled → Published)
- Track **publishing cadence** per channel (newsletter, blog, LinkedIn, X, etc.)
- Surface **what needs attention** — overdue pieces, gaps in the schedule, idle ideas
- Flag **repurposing opportunities** — where existing content can be adapted for new channels
- Provide a **weekly content brief** summarizing the next 7 days

---

## Setup (5 Steps)

### Step 1: Create your content workspace

Create a file called `content/CALENDAR.md` in your agent workspace. Paste this starter template:

```markdown
# Content Calendar

_Last updated: [date]_

## Active Pipeline

| ID | Title | Type | Channel | Stage | Due Date | Notes |
|----|-------|------|---------|-------|----------|-------|
| C001 | | | | Idea | | |

## Publishing Cadence

| Channel | Frequency | Day/Time | Status |
|---------|-----------|----------|--------|
| Newsletter | Weekly | Thursday | Active |
| Blog | Bi-weekly | Monday | Active |
| LinkedIn | 3x/week | Mon/Wed/Fri | Active |
| X/Twitter | Daily | 9am | Active |

## Content Backlog (Unscheduled Ideas)

- [ ] [idea title] — [brief description]

## Published Archive

_Completed pieces move here after publishing._
```

### Step 2: Define your channels

Edit the Publishing Cadence table above to match your actual channels. Remove what you don't use. Add what's missing. Be honest about cadence — if you realistically post once a week, put that.

### Step 3: Tell your agent about content types

Add a note at the top of CALENDAR.md listing your content types and typical word counts or formats:

```markdown
## Content Types
- **Newsletter** — ~800 words, personal tone, one main idea + links
- **Blog Post** — 1,200–2,000 words, SEO-focused, structured headers
- **LinkedIn Post** — 150–300 words, story format, one insight
- **X Thread** — 5–10 tweets, hook + value + CTA
- **YouTube Script** — 800–1,500 words, conversational
```

### Step 4: Create the content folder structure

```
content/
├── CALENDAR.md          ← pipeline overview (this file)
├── ideas/               ← rough idea notes
├── drafts/              ← in-progress pieces
├── published/           ← archive of completed work
└── repurpose/           ← repurposing queue
```

Your agent will reference this structure when looking for content to work on.

### Step 5: Activate the skill

Tell your agent:

> "Read the content-calendar skill and set up my content system. Use the files in `content/`."

Or trigger it via heartbeat by adding to `HEARTBEAT.md`:

```markdown
## Content Calendar (every Monday)
- Review content/CALENDAR.md
- Flag anything due this week
- Surface 2-3 backlog ideas worth developing
- Check for pieces stuck in Draft >7 days
```

---

## Pipeline Stages

Each piece of content moves through these stages:

| Stage | Description | Typical Duration |
|-------|-------------|-----------------|
| **Idea** | Just a title/concept, not started | Indefinite |
| **Outline** | Structure exists, no full draft | 1–3 days |
| **Draft** | Full draft exists, not reviewed | 1–5 days |
| **Review** | Ready for final edits/approval | 1–2 days |
| **Scheduled** | Written, set to publish on a date | Done |
| **Published** | Live — move to archive | Archive |

**Stall flag:** Any piece in Draft or Review for >7 days gets flagged in status reports.

---

## Weekly Content Brief Format

When asked for a content brief, your agent will produce:

```
CONTENT BRIEF — Week of [date]

PUBLISHING THIS WEEK
━━━━━━━━━━━━━━━━━━━
• [Day] — [Channel]: [Title] (Stage: Scheduled ✅)
• [Day] — [Channel]: [Title] (Stage: Draft — needs ~2h to finish ⚠️)

OVERDUE / AT RISK
━━━━━━━━━━━━━━━━
• [Title] — [Channel] — was due [date], stuck in [Stage] for [X] days
  → Recommended action: [complete / reschedule / cut]

SCHEDULE GAPS
━━━━━━━━━━━━
• [Channel] has no content scheduled for [date range]
  → Backlog options: [list 2-3 relevant ideas]

REPURPOSE OPPORTUNITIES
━━━━━━━━━━━━━━━━━━━━━━
• "[Title]" (published [date]) → could become [format] for [channel]

NEXT WEEK PREVIEW
━━━━━━━━━━━━━━━━
• [Channel]: [Title] (Stage: Outline — on track)
• [Channel]: [TBD — needs idea]

RECOMMENDED ACTION TODAY
━━━━━━━━━━━━━━━━━━━━━━━
1. [Most urgent thing]
2. [Second thing]
3. [Third thing]
```

---

## Repurposing Tracker

Good content does more than one job. Tell your agent to check for repurposing opportunities by looking at anything published in the last 60 days:

**Common repurposing patterns:**
- Newsletter issue → LinkedIn post (pull the main insight)
- Blog post → X thread (break into 5-8 key points)
- Long blog → Short blog (split into 2 pieces)
- Video script → Blog post (light reformatting)
- Newsletter → Blog post (add SEO metadata and headers)

To flag a piece for repurposing, add a row in `content/repurpose/queue.md`:

```markdown
| Original | Original Channel | Repurpose As | Target Channel | Status |
|----------|-----------------|--------------|----------------|--------|
| [Title] | Newsletter | Thread | X/Twitter | Todo |
```

---

## Content Idea Capture

Drop rough ideas into `content/ideas/` as simple text files. Naming convention:

```
[topic-slug].md
```

Minimum viable idea note:

```markdown
# [Idea Title]

**Angle:** [One sentence on the specific take]
**Channel:** [Best fit channel]
**Why now:** [Why this is relevant/timely]
**Hook:** [Draft hook if you have one]
**Related:** [Links to existing content it connects to]
```

Your agent can help expand ideas into outlines on request.

---

## Customization Options

### Change the stall threshold
Default is 7 days. To adjust, add to CALENDAR.md:
```markdown
## Settings
- Stall threshold: 5 days
- Overdue warning: 2 days before due date
```

### Topic clusters
Group your content by theme to ensure balanced coverage:
```markdown
## Topic Clusters
- Business Systems (40%)
- AI / Automation (30%)
- Personal Productivity (20%)
- Industry News (10%)
```
Your agent will flag if any cluster is underrepresented over a rolling 4-week period.

### Seasonal content flags
Mark pieces as time-sensitive:
```markdown
| ID | Title | ... | Notes |
|----|-------|-----|-------|
| C012 | Year-end recap | ... | ⏰ SEASONAL: must publish Dec 28-30 |
```

### Minimum viable cadence mode
If you're overwhelmed, tell your agent:
> "Switch content calendar to minimum viable cadence."

It will prioritize your single highest-traffic channel and flag everything else as optional.

---

## Integration with Other Agent Ledger Skills

| Skill | Integration |
|-------|-------------|
| **Daily Briefing** | Include "Content due today" in morning briefing |
| **Project Tracker** | Content launches tracked as projects (e.g., "Issue #5") |
| **Solopreneur Assistant** | Content calendar reviewed in weekly business review |
| **Research Assistant** | Research briefs feed directly into content ideas |
| **Inbox Triage** | Reader replies/feedback captured for content improvement |

---

## Troubleshooting

**"My calendar is getting out of date"**
Add a heartbeat check. Weekly is usually right for most creators. Daily if you publish daily.

**"Too many ideas, can't prioritize"**
Use the scoring rubric in `references/advanced-patterns.md` to rank ideas by effort vs. impact.

**"I keep missing my publishing schedule"**
Run a cadence audit: count how many pieces you actually published in the last 30 days vs. how many you planned. Adjust your cadence table to match reality, not aspirations. A realistic cadence beats an optimistic one every time.

**"Agent keeps forgetting what I've published"**
Move published pieces to `content/published/` and update the archive section of CALENDAR.md. Periodically tell your agent: "Update the content archive from the published folder."

**"I want to track performance metrics"**
This skill tracks pipeline, not analytics. For performance data, track metrics manually in a `content/published/[slug]-metrics.md` file and reference them in repurposing decisions.

---

## Triggers

This skill activates when you say things like:
- "What content do I have due this week?"
- "Give me a content brief"
- "What's in my content pipeline?"
- "I have a new content idea: [idea]"
- "What content is overdue?"
- "What can I repurpose from last month?"
- "Review my content calendar"

---

*Content Calendar — by The Agent Ledger*
*Subscribe at [theagentledger.com](https://theagentledger.com) for new skills and the weekly newsletter on building AI-powered systems.*
*License: CC-BY-NC-4.0*

> *DISCLAIMER: This skill was created by an AI agent. It is provided "as is" for informational and educational purposes only. It does not constitute professional, financial, legal, or technical advice. Review all generated files before use. The Agent Ledger assumes no liability for outcomes resulting from use. Use at your own risk.*
