# Memory Template — Competitor Monitoring

## Main Memory (~/competitor-monitoring/memory.md)

Create with this structure:

```markdown
# Competitor Monitoring Memory

## Status
status: ongoing
version: 1.0.0
last: YYYY-MM-DD
integration: pending | done | declined

## Monitoring Preferences
<!-- How the user wants to be alerted -->
frequency: weekly | on-demand | real-time
alert_threshold: critical-only | high | all
batch_alerts: true | false

## Active Competitors
<!-- List of companies being tracked -->
- Company A (primary)
- Company B (primary)
- Company C (secondary)

## User Context
<!-- Their positioning, what they care about -->
differentiation: What makes them different
vulnerabilities: Where they're at risk
priorities: What competitive signals matter most

## Notes
<!-- Internal observations -->

---
*Updated: YYYY-MM-DD*
```

## Status Values

| Value | Meaning | Behavior |
|-------|---------|----------|
| `ongoing` | Still learning landscape | Ask about new competitors when relevant |
| `complete` | Has full picture | Monitor and report |
| `paused` | User said "not now" | Don't proactively monitor |

---

## Competitor Dossier Template (~/competitor-monitoring/competitors/{company}.md)

Create one file per tracked competitor:

```markdown
# {Company Name} — Competitor Dossier

## Overview
website: https://...
category: Direct competitor | Indirect | Emerging
last_checked: YYYY-MM-DD
threat_level: High | Medium | Low

## What They Do
<!-- One paragraph: who they are, who they serve -->

## Pricing
<!-- Current pricing structure -->
| Tier | Price | Notes |
|------|-------|-------|
| ... | ... | ... |

### Pricing History
- YYYY-MM-DD: Changed from X to Y

## Features
### Core
- Feature 1
- Feature 2

### Recent Additions
- YYYY-MM-DD: Added feature X

### Missing (vs us)
- What they don't have that we do

## Positioning
### Messaging
<!-- Their main value prop, taglines -->

### Target Market
<!-- Who they're going after -->

### Differentiation Claims
<!-- What they say makes them different -->

## Strengths
<!-- Be honest -->
- Strength 1
- Strength 2

## Weaknesses
<!-- Opportunities to exploit -->
- Weakness 1
- Weakness 2

## Recent Moves (Last 90 Days)
- YYYY-MM-DD: What happened

## Watch List
<!-- What to monitor for this competitor -->
- Their pricing page
- Their changelog
- Their job postings

---
*Last updated: YYYY-MM-DD*
```

---

## Alert Log Template (~/competitor-monitoring/alerts/YYYY-MM-DD.md)

```markdown
# Alerts — YYYY-MM-DD

## Critical
<!-- Requires immediate attention -->

## High
<!-- Important but not urgent -->

## Medium
<!-- Worth knowing -->

## Acknowledged
<!-- User has seen these -->
- [time] Alert description → User response

---
```

---

## Analysis Template (~/competitor-monitoring/analysis/{topic}.md)

```markdown
# {Analysis Title}

## Date
YYYY-MM-DD

## Type
Head-to-Head | Landscape | Trend | Gap

## Summary
<!-- One paragraph conclusion -->

## Detailed Analysis
<!-- The actual analysis -->

## Recommendations
<!-- What to do based on this -->
1. Action 1
2. Action 2

## Sources
<!-- Where the data came from -->

---
```

## Key Principles

- **No config keys visible** — use natural language
- **Update dossiers after every mention** — keep them fresh
- **Date everything** — competitive intelligence decays fast
- **Be honest about strengths** — don't sugarcoat competitor advantages
