# Responsiveness Report Template

Use this structure when writing responsiveness check reports.

## Report Structure

```markdown
# Responsiveness Check: [URL]

**Date**: YYYY-MM-DD
**Mode**: Standard / Sweep / Targeted (range)
**Breakpoints tested**: [list widths]
**Browser tool**: playwright-cli / Playwright MCP / Chrome MCP

## Summary

| Width | Status | Issues |
|-------|--------|--------|
| 320px | Fail | 2 critical, 1 high |
| 375px | Fail | 1 high |
| 768px | Warn | 1 medium |
| 1024px | Pass | — |
| 1280px | Pass | — |
| 1440px | Pass | — |
| 1920px | Warn | 1 medium |
| 2560px | Fail | 1 high |

**Overall**: X issues across Y breakpoints. [1-sentence summary of the main finding.]

## Critical & High Issues

### [Issue title] — [Severity]

**Width(s)**: 320px, 375px
**Check**: Horizontal overflow

[Description: what's happening, what element is affected]

[Screenshot reference or inline image]

**Fix suggestion**: [CSS/HTML fix if obvious]

---

[Repeat for each critical/high issue]

## Transition Analysis

| Transition | Observed At | Clean? | Notes |
|-----------|-------------|--------|-------|
| Nav: hamburger → full | ~960px | Yes | Smooth transition, no flicker |
| Grid: 1-col → 2-col | ~700px | No | Cards overlap briefly at 680-720px |
| Sidebar appears | ~1100px | Yes | Content reflows cleanly |
| Footer: stacked → inline | ~640px | Yes | — |

## Per-Breakpoint Notes

Only include breakpoints with findings. Skip clean ones.

### 320px — Fail

- **[Critical]** Hero text overflows viewport, horizontal scroll appears
- **[High]** CTA button text wraps to 3 lines, looks broken
- Nav hamburger works correctly

### 375px — Fail

- **[High]** Service cards stack but images overflow container by ~20px

### 1920px+ — Warn

- **[Medium]** Content area maxes out at 1280px, leaving 320px margins each side — feels disconnected

## Recommendations

Group by effort:

### Quick Fixes (CSS only)
- Add `overflow-x: hidden` on hero container
- Set `max-width: 100%` on service card images
- Add `max-w-[1600px]` container for ultra-wide

### Structural Changes
- Add a breakpoint between 768–1024px for tablet-specific layout
- Rethink grid gap scaling for 1920px+
```

## Status Definitions

| Status | Meaning |
|--------|---------|
| **Pass** | No layout issues at this width |
| **Warn** | Minor issues (medium/low severity) — usable but not polished |
| **Fail** | Critical or high severity issues — layout is broken or significantly degraded |

## Writing Guidelines

- **Findings-first**: Lead with what's broken, not what works
- **Be specific**: "Hero h1 overflows at 320px by ~40px" not "text overflow issues"
- **Include the width**: Every finding must state which width(s) it affects
- **Screenshot at failures**: Screenshots make the report actionable
- **Skip clean breakpoints**: Don't write "1280px — everything looks great" — only note breakpoints with issues
- **Group fixes by effort**: CSS-only fixes vs structural changes helps prioritise
