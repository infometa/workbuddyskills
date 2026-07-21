---
name: goal-tracker
description: Track long-term goals with milestones, daily logging, and accountability. Use when users want to set goals, log daily progress, update milestones, generate weekly summaries, or view an HTML dashboard of their goal progress.
description_zh: "追踪长期目标、里程碑、每日记录与问责系统"
description_en: "Track long-term goals with milestones, daily logging, and accountability"
version: 1.0.0
---

# Goal Tracker Skill

Track long-term goals with milestones, daily logging, and accountability.

## Location
`/root/clawd/goal-tracker/`

## Commands

```bash
# Show status
/root/clawd/tracker status

# Log daily activity
/root/clawd/tracker log --trained --business --wins "Description"

# Update MRR
/root/clawd/tracker mrr 5000

# Mark milestone complete
/root/clawd/tracker milestone ironman "5km run"
/root/clawd/tracker milestone mrr_100k "first client"

# Weekly summary
/root/clawd/tracker week

# Generate HTML dashboard
/root/clawd/goal-tracker/generate-dashboard
```

## Data Files
- `data/goals.json` - Goal definitions and milestones
- `data/daily-log.json` - Daily check-ins
- `index.html` - Generated visual dashboard

## Integration with Alto

### During Evening Check-ins
Ask: "Did you train today? Work on business?"
Then log: `tracker log --trained --business` (or `--no-trained` etc.)

### When Wins Happen
Log them: `tracker log --wins "Landed new client"`

### When MRR Changes
Update: `tracker mrr 5000`

### When Milestones Complete
Mark: `tracker milestone ironman "5km"`

## Goals Tracked

### Ironman (by 2030)
Milestones:
1. Run 5km without stopping
2. Complete sprint triathlon
3. Complete Olympic distance
4. Complete Half Ironman (70.3)
5. Complete Full Ironman

### $100k MRR (by 2030)
Milestones:
1. First paying client
2. $5k MRR
3. $10k MRR
4. $25k MRR
5. $50k MRR
6. $100k MRR

## Weekly Rhythm
- Monday: Week planning (set priorities)
- Daily: Evening check-in (log training + business)
- Friday: Week review (score + adjust)

## Patterns to Watch
- 3+ days without training = gentle nudge
- Week score < 50% = check in on blockers
- Milestone dates approaching = increase urgency
