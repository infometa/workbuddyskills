# Content Calendar — Advanced Patterns

**By The Agent Ledger** — [theagentledger.com](https://theagentledger.com)

---

## Content Batching

Batching is the biggest leverage move for solo creators. Instead of writing one piece per session, produce multiple pieces of similar type at once.

### Batching protocol

Add to your weekly review:

```markdown
## Content Batching Sessions
- **Monday:** LinkedIn posts — write all 3 for the week in one 45-min session
- **Tuesday:** Long-form — single 2h block for newsletter or blog post
- **Thursday:** X threads — 2-3 threads drafted in 30 min
```

Tell your agent before a batching session:
> "I'm batching LinkedIn posts today. Pull my top 3 ideas from the backlog ranked by effort and relevance."

Your agent will surface ideas, check the topic cluster balance, and suggest angles based on what's already published.

### Batch templates

Create reusable templates in `content/templates/` for each format:

```markdown
# LinkedIn Post Template

**Hook:** [Bold statement or surprising fact]

**Setup:** [1-2 sentences of context]

**3 key points:**
1. [Point with brief explanation]
2. [Point with brief explanation]
3. [Point with brief explanation]

**Close:** [Insight or takeaway]

**CTA:** [Question to prompt comments, or link to deeper content]
```

---

## Content Series Planning

Running a series keeps readers coming back and reduces ideation fatigue.

### Series tracker

Add to `content/CALENDAR.md`:

```markdown
## Active Series

| Series Name | Channel | Cadence | Episode | Status |
|-------------|---------|---------|---------|--------|
| "Systems That Scale" | Newsletter | Weekly | #4 of ? | Active |
| "AI Tool Breakdown" | Blog | Monthly | #2 of 6 | Active |
```

### Series rules
- Define the series arc upfront (how many episodes, what each covers)
- Every series should end — open-ended series tend to get abandoned
- Cross-link between episodes ("Missed Part 1? [link]")

---

## Content Audit Protocol

Run a quarterly content audit to find what's working and prune what isn't.

### Audit checklist (quarterly)

1. **List all content published in the last 90 days** by channel
2. **Identify top performers** — what got the most shares/replies/traffic?
3. **Identify underperformers** — what got zero response?
4. **Pattern analysis:** What do top performers have in common? Format? Topic? Length?
5. **Cadence review:** Did you hit your planned cadence? If not, what slipped?
6. **Repurpose review:** Which top performers haven't been repurposed yet?
7. **Prune:** Are there channels that consistently underperform? Consider dropping or reducing.

Output: A 1-page `content/audit-[YYYY-Q#].md` summarizing findings and adjustments to cadence/focus for next quarter.

---

## Evergreen Content System

Some content stays relevant for years. Track it separately.

### Evergreen folder

```
content/
└── evergreen/
    ├── getting-started-with-X.md
    ├── ultimate-guide-to-Y.md
    └── INDEX.md
```

`INDEX.md` lists all evergreen pieces with a refresh schedule:

```markdown
# Evergreen Content Index

| Title | Channel | Published | Last Refreshed | Refresh Due |
|-------|---------|-----------|----------------|-------------|
| [Title] | Blog | 2025-09 | 2026-01 | 2026-07 |
```

Add a heartbeat check:
```markdown
## Evergreen Refresh (Quarterly)
- Check content/evergreen/INDEX.md
- Flag any pieces where Refresh Due is within 30 days
```

---

## Multi-Platform Scheduling Logic

When you have tight publishing windows, your agent can help sequence across platforms to maximize impact.

### Sequencing strategy

For a major piece of content (e.g., big blog post):

```
Day 0: Publish blog post
Day 1: LinkedIn post — pull the main insight (link to blog)
Day 2: X thread — expand the 3 key points
Day 5: Newsletter mention — brief reference + link
Day 14: Repurpose check — is there a Part 2 angle here?
```

Create a `content/templates/launch-sequence.md` and tell your agent to apply it whenever you publish long-form content.

---

## Content Gap Analysis

Your agent can spot calendar gaps before they become emergencies.

### Gap detection prompt

Ask your agent once a week:
> "Scan my content calendar for the next 14 days. Where do I have gaps by channel? What backlog ideas fit those slots best?"

Your agent will cross-reference the Publishing Cadence table against what's actually Scheduled, surface gaps, and propose matches from the Backlog.

### Rolling 30-day view

Ask monthly:
> "Give me a rolling 30-day content view. What's published, what's scheduled, what's missing?"

This gives you the bird's-eye view to adjust cadence before you fall behind.

---

## Content Collaboration Workflow

If you work with collaborators (ghostwriters, editors, VAs):

### Collaboration status stages

Extend the pipeline with collaboration stages:

```
Idea → Outline → [Assigned to: Name] → Draft → [Review: Name] → Final → Scheduled → Published
```

Add a `Assigned To` column to the pipeline table and flag pieces awaiting external input.

### Handoff notes

Create `content/drafts/[slug]-handoff.md` with instructions for collaborators — this is your brief. Keep it to 1 page max: goal, audience, tone, must-include points, what to avoid, word count target.

---

## Content Revenue Tracking

For monetized content (affiliate links, paid newsletters, sponsored posts):

Add an optional Revenue column to the pipeline:

```markdown
| ID | Title | ... | Revenue Type | Expected | Actual |
|----|-------|-----|--------------|----------|--------|
| C045 | [Title] | ... | Affiliate | $50 | $32 |
| C046 | [Title] | ... | Sponsored | $200 | $200 |
```

Tell your agent to include a monthly content revenue summary in the business review (pairs with solopreneur-assistant skill).

---

## Burnout Prevention

Consistent content creation is a long game. Build rest into the system.

### Scheduled buffer weeks

Add to your cadence table:
```markdown
| Channel | Frequency | ... | Notes |
|---------|-----------|-----|-------|
| Newsletter | Weekly | Thu | Skip first week of each month = buffer |
```

### Content debt tracking

If you miss a scheduled piece, log it:
```markdown
## Content Debt Log
- [Date]: Missed [Channel] [Title] — reason: [brief note]
  → Decision: [catch up next week / skip / merge with next issue]
```

Don't let debt accumulate silently. One missed piece is fine. Five missed pieces is a cadence problem.

---

*Content Calendar (Advanced Patterns) — by The Agent Ledger*
*Subscribe at [theagentledger.com](https://theagentledger.com)*
*License: CC-BY-NC-4.0*
