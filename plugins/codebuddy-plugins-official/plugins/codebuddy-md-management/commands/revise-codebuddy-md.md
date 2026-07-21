---
description: Update CODEBUDDY.md with learnings from this session
allowed-tools: Read, Edit, Glob
---

Review this session for learnings about working with CodeBuddy Code in this codebase. Update CODEBUDDY.md with context that would help future CodeBuddy sessions be more effective.

## Step 1: Reflect

What context was missing that would have helped CodeBuddy work more effectively?
- Bash commands that were used or discovered
- Code style patterns followed
- Testing approaches that worked
- Environment/configuration quirks
- Warnings or gotchas encountered

## Step 2: Find CODEBUDDY.md Files

```bash
find . -name "CODEBUDDY.md" -o -name ".codebuddy.local.md" 2>/dev/null | head -20
```

Decide where each addition belongs:
- `CODEBUDDY.md` - Team-shared (checked into git)
- `.codebuddy.local.md` - Personal/local only (gitignored)

## Step 3: Draft Additions

**Keep it concise** - one line per concept. CODEBUDDY.md is part of the prompt, so brevity matters.

Format: `<command or pattern>` - `<brief description>`

Avoid:
- Verbose explanations
- Obvious information
- One-off fixes unlikely to recur

## Step 4: Show Proposed Changes

For each addition:

```
### Update: ./CODEBUDDY.md

**Why:** [one-line reason]

\`\`\`diff
+ [the addition - keep it brief]
\`\`\`
```

## Step 5: Apply with Approval

Ask if the user wants to apply the changes. Only edit files they approve.
