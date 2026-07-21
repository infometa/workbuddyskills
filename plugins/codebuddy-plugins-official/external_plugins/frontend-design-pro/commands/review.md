---
description: Review generated design against anti-patterns, design principles, and accessibility guidelines
allowed-tools:
  - Read
  - Glob
  - Grep
  - AskUserQuestion
  - Skill
---

# Design Review

You are reviewing a generated design for quality, anti-patterns, and accessibility.

## Usage

```
/frontend-design-pro:review [file-path]
```

Example:
```
/frontend-design-pro:review ./landing-page.html
```

## Workflow

### Step 1: Get File

If no file path provided, ask:

"Which HTML file would you like me to review?"

Or search for recent HTML files:
```
Glob: **/*.html
```

### Step 2: Read the File

```
Read: [file-path]
```

### Step 3: Anti-Pattern Check

Search for common anti-patterns:

**Hero Badges/Pills:**
```
Grep for patterns like:
- "rounded-full.*px-.*text-sm" near headlines
- Badge/pill components above h1
- Words like "New", "AI-Powered", "Introducing", "Beta" in small elements
```

**Generic Fonts:**
```
Check for:
- font-family.*Inter
- font-family.*Roboto
- font-family.*Arial
- font-family.*Open.Sans
- font-sans without custom config
```

**Purple/Blue Gradients on White:**
```
Check for:
- bg-gradient.*purple.*blue on bg-white
- from-purple.*to-blue
- from-violet.*to-indigo
```

**Decorative Blobs:**
```
Check for:
- blur-3xl or blur-[100px] on colored divs
- "blob" in class names
- Large rounded-full with bg-{color}-200/300
```

**Excessive Rounded Corners:**
```
Check if rounded-3xl or rounded-full used everywhere
```

### Step 4: Design Principles Check

**Visual Hierarchy:**
- Is there clear size difference between h1, h2, h3?
- Are CTAs visually distinct?
- Is there one focal point per section?

**Alignment:**
- Is alignment consistent within sections?
- Are elements aligned to a grid?

**Contrast:**
- Text on background ratio (check color values)
- CTA stands out from surroundings?

**White Space:**
- Adequate padding on sections (p-8+)?
- Max-width on content containers?
- Breathing room between elements?

**Consistency:**
- Same button styles throughout?
- Same card treatments?
- Consistent spacing scale?

### Step 5: Accessibility Check

**Structure:**
```
Check for:
- <header>, <main>, <nav>, <footer>
- Skip link (a href="#main-content" or similar)
- lang="en" on <html>
```

**Headings:**
```
Verify:
- Exactly one <h1>
- Sequential heading levels (h1 → h2 → h3)
- No skipped levels
```

**Focus States:**
```
Check for:
- focus:ring or focus:outline classes
- No focus:outline-none without replacement
```

**Images:**
```
Check for:
- alt="" on decorative images
- Descriptive alt text on meaningful images
```

**Reduced Motion:**
```
Check for:
- @media (prefers-reduced-motion)
- motion-reduce: classes
```

**Color Contrast:**
```
Analyze:
- Text color vs background color
- Estimate contrast ratio
- Flag any obvious low-contrast text
```

### Step 6: Generate Report

Create a comprehensive review:

```markdown
## Design Review Report

### File: [path]

---

## Anti-Pattern Check

| Pattern | Status | Details |
|---------|--------|---------|
| Hero badges | ✅ Pass / ❌ Found | [Details] |
| Generic fonts | ✅ Pass / ❌ Found | [Details] |
| Purple-blue gradient | ✅ Pass / ❌ Found | [Details] |
| Decorative blobs | ✅ Pass / ❌ Found | [Details] |
| Excessive rounding | ✅ Pass / ❌ Found | [Details] |
| Template layout | ✅ Pass / ❌ Found | [Details] |

---

## Design Principles Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Visual hierarchy | ✅ / ⚠️ / ❌ | [Notes] |
| Alignment | ✅ / ⚠️ / ❌ | [Notes] |
| Contrast | ✅ / ⚠️ / ❌ | [Notes] |
| White space | ✅ / ⚠️ / ❌ | [Notes] |
| Consistency | ✅ / ⚠️ / ❌ | [Notes] |

---

## Accessibility Check

| Requirement | Status | Notes |
|-------------|--------|-------|
| Semantic HTML | ✅ / ❌ | [Notes] |
| Skip link | ✅ / ❌ | [Notes] |
| Heading order | ✅ / ❌ | [Notes] |
| Focus states | ✅ / ❌ | [Notes] |
| Image alt text | ✅ / ❌ | [Notes] |
| Reduced motion | ✅ / ❌ | [Notes] |
| Color contrast | ✅ / ⚠️ / ❌ | [Notes] |

---

## Summary

**Score: [X]/[Total] checks passed**

### Critical Issues
[List any blockers that must be fixed]

### Recommended Improvements
[List nice-to-have improvements]

### Positive Notes
[What the design does well]
```

### Step 7: Offer Fixes

If issues found, offer to fix them:

"I found [N] issues in your design. Would you like me to:
1. Fix all issues automatically
2. Fix critical issues only
3. Provide guidance for manual fixes
4. Skip fixes for now"

## Quick Mode

For a fast check, focus on:
1. Hero badges (the #1 AI slop indicator)
2. Generic fonts
3. Accessibility basics (skip link, headings)

## Output

The review provides:
- Clear pass/fail for each check
- Specific line numbers or locations
- Actionable fixes
- Overall quality score
