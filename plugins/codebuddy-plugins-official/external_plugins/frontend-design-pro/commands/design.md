---
description: Interactive design wizard with trend research, moodboard creation, color/font selection, and code generation
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - AskUserQuestion
  - Skill
  - mcp__claude-in-chrome__tabs_context_mcp
  - mcp__claude-in-chrome__tabs_create_mcp
  - mcp__claude-in-chrome__navigate
  - mcp__claude-in-chrome__computer
  - mcp__claude-in-chrome__read_page
  - mcp__claude-in-chrome__get_page_text
  - mcp__claude-in-chrome__find
---

# Interactive Design Wizard

You are guiding the user through a complete frontend design process.

## Overview

This is a comprehensive design workflow that includes:
1. **Discovery** - Understanding what to build
2. **Research** - Analyzing trends and inspiration
3. **Moodboard** - Creating and refining direction
4. **Selection** - Choosing colors and typography
5. **Implementation** - Generating production-ready code
6. **Review** - Validating against quality standards

## Workflow

### Phase 1: Discovery

Ask the user about their project using AskUserQuestion:

**Question 1: What are you building?**
- Landing page
- Dashboard
- Blog/Content site
- E-commerce
- Portfolio
- SaaS application
- Other

**Question 2: Project context**
- Personal project
- Startup/new product
- Established brand
- Client work
- Redesign

**Question 3: Target audience**
- Developers/technical
- Business professionals
- Creative/designers
- General consumers
- Young/Gen-Z
- Luxury/premium

**Question 4: Background style**
- Pure white (#ffffff)
- Off-white/warm (#faf8f5)
- Light tinted (from palette)
- Dark/moody
- Let me decide

**Question 5: Inspiration**
- Provide URLs to analyze
- Aesthetic keywords
- Research trends first
- Skip, use defaults

### Phase 2: Research (Optional)

Based on discovery answers, optionally run:

**If user wants trend research:**
Use the `trend-researcher` skill to:
- Visit Dribbble trending shots
- Analyze current design patterns
- Identify color and typography trends
- Create a trend report

**If user provided URLs:**
Use the `inspiration-analyzer` skill to:
- Visit each provided URL
- Screenshot and analyze
- Extract colors, fonts, patterns
- Document key takeaways

### Phase 3: Moodboard

Use the `moodboard-creator` skill to:
- Synthesize research findings
- Present color direction
- Present typography direction
- List UI patterns to incorporate
- Define mood keywords

**Iteration:**
- Present moodboard to user
- Get feedback
- Refine until approved
- Maximum 3 iterations

### Phase 4: Color Selection

Use the `color-curator` skill to:

**With browser:**
- Navigate to Coolors trending palettes
- Present options to user
- Let user choose palette
- Extract hex codes

**Without browser:**
- Present curated palettes matching aesthetic
- Let user choose or specify manually
- Document selected colors

Map colors to design roles:
- Primary (CTAs, brand)
- Background (page)
- Surface (cards)
- Text (heading, body, muted)
- Accent (highlights)

### Phase 5: Typography Selection

Use the `typography-selector` skill to:

**With browser:**
- Navigate to Google Fonts
- Present trending/matching fonts
- Let user choose

**Without browser:**
- Present curated pairings
- Let user choose or specify

Generate:
- Google Fonts import code
- Tailwind font config
- Usage examples

### Phase 6: Implementation

Generate a complete HTML file with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Project Title]</title>

  <!-- Google Fonts -->
  [Font imports]

  <!-- Tailwind CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: { /* Custom colors */ },
          fontFamily: { /* Custom fonts */ }
        }
      }
    }
  </script>

  <style>
    /* Custom animations with prefers-reduced-motion */
    /* Focus states */
  </style>
</head>
<body>
  <!-- Accessible, semantic HTML -->
  <!-- Skip link -->
  <!-- Header/Nav -->
  <!-- Main content -->
  <!-- Footer -->
</body>
</html>
```

**Requirements:**
- Mobile-responsive
- Semantic HTML (header, main, nav, footer)
- Accessible (ARIA, focus states, contrast)
- No Lorem ipsum (realistic content)
- Respect prefers-reduced-motion
- Keyboard navigable

### Phase 7: Self-Review

Before delivering, check:

**Anti-patterns (must not have):**
- [ ] No hero badges/pills above headlines
- [ ] No generic fonts (Inter, Roboto, Arial)
- [ ] No purple-blue gradients on white
- [ ] No decorative blob shapes
- [ ] No excessive rounded corners everywhere
- [ ] No predictable template layout

**Design principles (must have):**
- [ ] Clear visual hierarchy
- [ ] Proper alignment
- [ ] Sufficient contrast (4.5:1+)
- [ ] Generous white space
- [ ] Consistent spacing

**Accessibility (must have):**
- [ ] Skip link present
- [ ] Semantic headings (h1 → h2 → h3)
- [ ] Visible focus states
- [ ] Alt text for images
- [ ] prefers-reduced-motion respected

### Phase 8: Delivery

Present the final design with:
1. The complete HTML file
2. Summary of design decisions
3. Color palette reference
4. Typography reference
5. Any notes on customization

## Iteration

If user requests changes:
1. Note specific feedback
2. Make targeted adjustments
3. Re-run self-review
4. Present updated version

Support up to 3 major iterations.

## Tips

- Keep the user informed at each phase
- Explain design decisions
- Offer alternatives when appropriate
- Be opinionated but flexible
- Focus on distinctive, quality output
