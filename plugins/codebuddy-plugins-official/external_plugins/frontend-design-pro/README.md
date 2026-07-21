# Frontend Design Pro Plugin

An advanced frontend design plugin for Claude Code with interactive wizard, trend research, moodboard creation, browser-based inspiration analysis, and color/typography selection.

## Features

- **6 Skills** for comprehensive design workflow
- **3 Commands** for common design tasks
- **Browser Integration** via claude-in-chrome for live analysis
- **Fallback Mode** when browser unavailable
- **Anti-Pattern Detection** to avoid generic "AI slop"
- **WCAG Accessibility** built into every design

## Installation

Add to your Claude Code settings:

```json
{
  "plugins": [
    "https://github.com/davepoon/buildwithclaude/tree/main/plugins/frontend-design-pro"
  ]
}
```

## Skills

### trend-researcher

Research latest UI/UX trends from Dribbble and design communities.

**Topics covered:**
- Trending design patterns
- Color trends
- Typography trends
- Layout patterns
- What to avoid

### moodboard-creator

Create visual moodboards from collected inspiration with iterative refinement.

**Topics covered:**
- Synthesizing research
- Color direction
- Typography direction
- UI patterns
- Mood keywords

### design-wizard

Interactive wizard that guides through a complete design process.

**Topics covered:**
- Discovery questions
- Aesthetic selection
- Color mapping
- Typography pairing
- Code generation
- Self-review

### inspiration-analyzer

Analyze websites for design inspiration using browser automation.

**Topics covered:**
- Color palette extraction
- Typography identification
- Layout patterns
- UI element analysis
- Motion detection

### color-curator

Browse and select color palettes from Coolors or curated fallbacks.

**Topics covered:**
- Coolors integration
- Color psychology
- Palette mapping
- Tailwind config generation
- Accessibility compliance

### typography-selector

Browse and select fonts from Google Fonts or curated pairings.

**Topics covered:**
- Google Fonts integration
- Font pairing strategies
- Type scale
- Performance optimization
- Tailwind config generation

## Commands

### /frontend-design-pro:design

Full interactive design workflow.

```
/frontend-design-pro:design
```

Guides you through:
1. Discovery questions
2. Trend research (optional)
3. Moodboard creation
4. Color selection
5. Typography selection
6. Code generation
7. Quality review

### /frontend-design-pro:analyze-site

Quick website analysis for inspiration.

```
/frontend-design-pro:analyze-site https://linear.app
```

Extracts:
- Color palette
- Typography
- Layout patterns
- UI elements
- Key takeaways

### /frontend-design-pro:review

Review generated designs for quality.

```
/frontend-design-pro:review ./landing-page.html
```

Checks:
- Anti-patterns
- Design principles
- Accessibility
- Provides fix recommendations

## Directory Structure

```
frontend-design-pro/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── trend-researcher/
│   │   └── SKILL.md
│   ├── moodboard-creator/
│   │   └── SKILL.md
│   ├── design-wizard/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── design-principles.md
│   │       ├── aesthetics-catalog.md
│   │       ├── anti-patterns.md
│   │       └── accessibility-guidelines.md
│   ├── inspiration-analyzer/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── extraction-techniques.md
│   ├── color-curator/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── color-theory.md
│   └── typography-selector/
│       ├── SKILL.md
│       └── references/
│           └── font-pairing.md
├── commands/
│   ├── design.md
│   ├── analyze-site.md
│   └── review.md
└── README.md
```

## Comparison with Official Plugin

| Feature | Official | frontend-design-pro |
|---------|----------|---------------------|
| Skills | 1 | 6 |
| Commands | 0 | 3 |
| Interactive wizard | ❌ | ✅ |
| Trend research | ❌ | ✅ Dribbble |
| Moodboard creation | ❌ | ✅ |
| Website analysis | ❌ | ✅ Browser |
| Color selection | ❌ | ✅ Coolors |
| Font selection | ❌ | ✅ Google Fonts |
| Self-review | ❌ | ✅ |
| Fallback mode | N/A | ✅ |
| Accessibility guide | Brief | ✅ Full WCAG |
| Anti-patterns | Brief list | ✅ Detailed + code |
| Aesthetic catalog | Mentioned | ✅ 11 styles + code |

## Anti-Patterns Detected

The plugin helps you avoid:

- ❌ Hero badges/pills ("New", "AI-Powered")
- ❌ Generic fonts (Inter, Roboto, Arial)
- ❌ Purple/blue gradients on white
- ❌ Decorative blob shapes
- ❌ Excessive rounded corners
- ❌ Predictable template layouts
- ❌ Generic tech startup aesthetics

## Aesthetic Directions

Choose from 11+ curated aesthetics:

**Modern:**
- Dark & Premium
- Glassmorphism
- Neobrutalism
- Bento Grid

**Retro:**
- Brutalist/Editorial
- Y2K/Cyber

**Cultural:**
- Swiss Typography
- Scandinavian Minimal
- Japanese Zen

**Stripped-Down:**
- Statement Hero
- Type-Only

## Usage Examples

### Quick Landing Page

```
User: Create a landing page for my developer tool
/frontend-design-pro:design
```

Claude will:
1. Ask about your project and audience
2. Research current design trends
3. Create a moodboard for approval
4. Help select colors from Coolors
5. Help select fonts from Google Fonts
6. Generate production-ready HTML
7. Review for anti-patterns and accessibility

### Analyze Competition

```
User: I like Linear's design, analyze it for me
/frontend-design-pro:analyze-site https://linear.app
```

Claude will:
1. Visit the site in browser
2. Take screenshots
3. Extract colors, fonts, patterns
4. Document key design decisions
5. Provide actionable takeaways

### Review Existing Design

```
User: Check my design for issues
/frontend-design-pro:review ./my-landing-page.html
```

Claude will:
1. Check for anti-patterns
2. Validate design principles
3. Audit accessibility
4. Provide score and recommendations

## Browser Requirements

For full functionality, install the [Claude in Chrome](https://chromewebstore.google.com/detail/claude-in-chrome) extension.

Without browser access, the plugin:
- Still runs interactive wizard
- Uses curated color palettes
- Uses curated font pairings
- Skips live website analysis
- Provides all code generation features

## Output Format

All generated designs are:
- Single HTML file with Tailwind CDN
- Custom Tailwind config for colors/fonts
- Google Fonts imports
- Mobile-responsive
- WCAG accessible
- Production-ready quality

## Contributing

Contributions welcome! Please follow the existing skill structure and include:
- SKILL.md with frontmatter and core content
- References for detailed documentation
- Examples with working code patterns

## License

MIT
