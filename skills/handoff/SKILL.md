---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up. Use when user wants to hand off work, summarize progress, or prepare context for a new session.
description_zh: "将当前对话压缩为交接文档，供下一个 Agent 无缝接续工作"
description_en: "Summarise current conversation into a handoff doc for a fresh agent to continue the work"
version: 1.0.0
homepage: https://github.com/mattpocock/skills
allowed-tools: Read,Write,Bash
---

# Handoff

## What to do

Write a handoff document summarising the current conversation so a fresh agent can continue the work.

**File path**: Save to `docs/handoff-<timestamp>.md`. If `docs/` doesn't exist, save to the project root instead. Get the timestamp with Bash: `date +%Y%m%d-%H%M%S`.

Before writing, use Read to scan for existing artifacts (PRDs, ADRs, open issues, recent diffs) so you can reference rather than duplicate them.

Do not duplicate content already captured in other artifacts. Reference them by relative path or URL instead.

If the user passed arguments, treat them as a description of what the next session will focus on — use that to weight the "Next steps" section accordingly.

## Handoff document structure

```markdown
# Handoff: <brief description of what was worked on>

## Current state
What was accomplished in this session. Key decisions made, code written, problems solved.
Be specific but concise — bullet points preferred. Include file paths changed if relevant.

## Next steps
What the next session should tackle, in priority order.
If user provided a focus argument, lead with that.

## Relevant artifacts
Links or paths to artifacts that provide context — don't inline their content here:
- `docs/prd-*.md` — PRD if one exists
- `docs/adr/*.md` — relevant ADRs
- Issue URLs — open tickets
- Branch / PR — if a diff exists

## Suggested skills
Skills the next session should load. For each, one line explaining why:
- `diagnose` — if there is an unresolved bug to investigate
- `tdd` — if the next task is implementing a feature with tests
- `to-issues` — if a plan needs to be broken into tickets
- `grill-me` or `grill-with-docs` — if a design decision still needs to be resolved
- `zoom-out` — if the next session will enter unfamiliar code
- `handoff` — if the session will need to hand off again
Only list skills relevant to the actual next steps; omit the rest.
```

## Tools

- **Read**: Scan existing artifacts before writing, to avoid duplicating content
- **Write**: Write the handoff document to disk
- **Bash**: Get the current timestamp (`date +%Y%m%d-%H%M%S`) for the filename
