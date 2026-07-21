---
description: Analyze a website for design inspiration (colors, fonts, patterns)
allowed-tools:
  - Skill
  - AskUserQuestion
  - mcp__claude-in-chrome__tabs_context_mcp
  - mcp__claude-in-chrome__tabs_create_mcp
  - mcp__claude-in-chrome__navigate
  - mcp__claude-in-chrome__computer
  - mcp__claude-in-chrome__read_page
  - mcp__claude-in-chrome__get_page_text
  - mcp__claude-in-chrome__find
  - mcp__claude-in-chrome__resize_window
---

# Analyze Website for Inspiration

You are analyzing a website to extract design inspiration.

## Usage

```
/frontend-design-pro:analyze-site [URL]
```

Example:
```
/frontend-design-pro:analyze-site https://linear.app
```

## Workflow

### Step 1: Get URL

If URL not provided as argument, ask:

"What website would you like me to analyze for design inspiration?"

### Step 2: Browser Setup

```javascript
// Get browser context
tabs_context_mcp({ createIfEmpty: true })
tabs_create_mcp()
```

### Step 3: Navigate and Capture

```javascript
// Navigate to the URL
navigate({ url: "[URL]", tabId: tabId })

// Wait for load, then screenshot
computer({ action: "screenshot", tabId: tabId })
```

### Step 4: Capture Multiple Views

**Desktop view (default):**
- Above-fold hero section
- Scroll and capture 2-3 more sections
- Capture navigation hover states if possible

**Mobile view:**
```javascript
resize_window({ width: 375, height: 812, tabId: tabId })
computer({ action: "screenshot", tabId: tabId })
```

### Step 5: Analyze Elements

From screenshots, identify:

**Colors:**
- Primary brand color
- Background color(s)
- Text colors
- Accent colors
- Note approximate hex codes

**Typography:**
- Heading font (style, weight)
- Body font (style, weight)
- Size relationships
- Line height observations

**Layout:**
- Grid structure
- Section patterns
- White space usage
- Container widths

**UI Components:**
- Button styles
- Card treatments
- Navigation style
- Footer structure
- Any distinctive elements

**Motion/Interaction:**
- Hover effects observed
- Scroll animations
- Transitions

### Step 6: Generate Report

Create a structured analysis:

```markdown
## Website Analysis: [URL]

### Overview
[Brief description of the site and its design approach]

### Color Palette
| Role | Hex (Approx) | Usage |
|------|--------------|-------|
| Primary | #xxx | [Where used] |
| Background | #xxx | [Where used] |
| Text | #xxx | [Where used] |
| Accent | #xxx | [Where used] |

### Typography
- **Headlines**: [Font/style] at [size], [weight]
- **Body**: [Font/style] at [size], [weight]
- **Line height**: [Observation]
- **Letter spacing**: [Observation]

### Layout Patterns
- **Grid**: [Description]
- **Container**: [Max width observation]
- **Sections**: [How sections are structured]
- **White space**: [Philosophy]

### UI Elements
- **Buttons**: [Shape, style, states]
- **Cards**: [Treatment]
- **Navigation**: [Style]
- **Icons**: [Style if present]

### Distinctive Features
1. [What makes this design unique]
2. [Interesting pattern to note]
3. [Technique worth replicating]

### Key Takeaways
What to borrow from this design:
- [Takeaway 1]
- [Takeaway 2]
- [Takeaway 3]

### What to Avoid
- [Any overused patterns to skip]
```

## Fallback Mode

If browser tools are unavailable:

"I can't access the website directly. Could you:
1. Share a screenshot of the site
2. Describe what you like about the design
3. Note any visible font names or colors

I'll analyze whatever you can provide."

## Multiple Sites

If user provides multiple URLs:
1. Analyze each separately
2. Create individual reports
3. Summarize common themes
4. Note contrasting approaches
5. Recommend which elements to combine

## Output

The analysis should provide actionable insights:
- Specific hex codes to use
- Font names to search
- Layout patterns to replicate
- Techniques to try
- Clear direction for implementation
