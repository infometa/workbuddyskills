# Memory Template - Netlify Deploy

Create `~/netlify-deploy/memory.md` with this structure:

```markdown
# Netlify Deploy Memory

## Status
status: ongoing
version: 1.0.0
last: YYYY-MM-DD
integration: pending

## Context
- Preferred deploy mode: preview first
- Default project path:
- Typical package manager:
- Typical publish directory:

## Project Notes
- repo-or-site-name: short operational notes

## Constraints
- Required approval gates before `--prod`
- Any environment variable or branch rules

## Notes
- Observed preferences from real usage

---
*Updated: YYYY-MM-DD*
```

## Status Values

| Value | Meaning | Behavior |
|-------|---------|----------|
| `ongoing` | Still learning defaults | Keep collecting deploy patterns |
| `complete` | Core defaults known | Execute with minimal clarification |
| `paused` | User postponed setup details | Use safe defaults and avoid extra setup prompts |
| `never_ask` | User does not want setup questions | Operate with explicit per-task confirmations |
