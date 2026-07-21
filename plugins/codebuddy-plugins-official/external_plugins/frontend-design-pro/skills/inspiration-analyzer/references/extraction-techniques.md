# Extraction Techniques

Advanced techniques for extracting design elements from websites.

---

## Color Extraction

### From Visual Inspection

**Primary Color Detection:**
- Look at the main CTA button color
- Check the logo/brand mark color
- Look at link colors
- Check active/selected state colors

**Background Color Detection:**
- Inspect the main `<body>` background
- Check section alternating colors
- Look at card/modal backgrounds
- Note navigation background

**Text Color Detection:**
- Inspect heading colors
- Check body text color
- Look at muted/secondary text
- Check placeholder text color

### Common Color Locations

```html
<!-- Primary color often found in: -->
<button class="bg-[PRIMARY]">...</button>
<a class="text-[PRIMARY]">...</a>
<div class="border-[PRIMARY]">...</div>

<!-- Background colors: -->
<body class="bg-[BACKGROUND]">...</body>
<section class="bg-[SURFACE]">...</section>

<!-- Text colors: -->
<h1 class="text-[HEADING]">...</h1>
<p class="text-[BODY]">...</p>
<span class="text-[MUTED]">...</span>
```

### Approximating Hex Values

When exact values aren't visible, approximate from visual:

| Visual Appearance | Approximate Hex |
|-------------------|-----------------|
| Pure white | #ffffff |
| Off-white/cream | #faf8f5 or #f5f5f0 |
| Light gray | #e5e5e5 |
| Medium gray | #a3a3a3 |
| Dark gray | #525252 |
| Near black | #171717 |
| Pure black | #000000 |

---

## Typography Extraction

### Identifying Google Fonts

Look for Google Fonts in the page source:

```html
<link href="https://fonts.googleapis.com/css2?family=Font+Name:wght@400;700&display=swap">
```

Common patterns:
- `family=Inter` → Inter
- `family=Outfit` → Outfit
- `family=Fraunces:opsz,wght@9..144,400;9..144,700` → Fraunces

### Identifying Font Characteristics

**Serif vs Sans-Serif:**
- Serif: Has small decorative strokes (Times, Georgia, Playfair)
- Sans-serif: Clean lines without serifs (Inter, Helvetica, Arial)

**Font Weight Classification:**
- Thin/Light: 100-300
- Regular: 400
- Medium: 500
- Semi-bold: 600
- Bold: 700
- Black: 800-900

**Tracking (Letter Spacing):**
- Tight: Headlines often use tighter tracking
- Normal: Body text standard
- Wide: All-caps text, labels

### Type Scale Analysis

Note the approximate scale between elements:

```
Hero headline: ~80px (5rem)
Section heading: ~48px (3rem)
Subheading: ~24px (1.5rem)
Body text: ~16-18px (1rem - 1.125rem)
Caption/small: ~14px (0.875rem)
```

---

## Layout Extraction

### Grid Analysis

**Counting Columns:**
1. Look at feature grids (usually 2-4 columns)
2. Check card layouts
3. Inspect navigation items
4. Note breakpoint changes

**Common Grid Patterns:**
- 12-column fluid
- 3-column features
- 2-column split
- Single column content
- Bento (mixed sizes)

### Spacing Analysis

**Vertical Rhythm:**
- Note spacing between sections
- Check margins around headings
- Observe padding in cards
- Look at form field spacing

**Common Spacing Scale:**
```
xs: 4px
sm: 8px
md: 16px
lg: 24px
xl: 32px
2xl: 48px
3xl: 64px
4xl: 96px
```

### Container Width

- Full-width sections: 100%
- Content container: ~1200px (max-w-7xl)
- Narrow content: ~720px (max-w-2xl)
- Reading width: ~65ch (max-w-prose)

---

## UI Component Extraction

### Button Patterns

Analyze button characteristics:

```markdown
Shape:
- [ ] Rounded (rounded-lg, ~8px)
- [ ] Pill (rounded-full)
- [ ] Square/Sharp (rounded-none or rounded)

Size:
- Padding: px-[X] py-[Y]
- Font size: text-[size]
- Height: h-[value] or auto

States:
- Hover: color change, shadow, scale?
- Focus: ring visible?
- Active: pressed effect?

Variants:
- Primary: filled with brand color
- Secondary: outlined or muted
- Ghost: transparent background
```

### Card Patterns

```markdown
Border:
- [ ] No border
- [ ] Subtle border (border-gray-200)
- [ ] Strong border (border-black, 2px+)

Shadow:
- [ ] No shadow
- [ ] Subtle (shadow-sm)
- [ ] Medium (shadow-md)
- [ ] Strong (shadow-lg)

Corners:
- [ ] Sharp (rounded-none)
- [ ] Slight (rounded, rounded-lg)
- [ ] Heavy (rounded-2xl, rounded-3xl)

Background:
- [ ] White on gray page
- [ ] Gray on white page
- [ ] Gradient fill
- [ ] Image background
```

### Navigation Patterns

```markdown
Position:
- [ ] Fixed top
- [ ] Sticky
- [ ] Absolute
- [ ] Static

Style:
- [ ] Transparent over hero
- [ ] Solid background
- [ ] Blurred/glass

Items:
- [ ] Horizontal links
- [ ] Dropdown menus
- [ ] Hamburger menu (mobile)
- [ ] Full-page mobile menu
```

---

## Animation Extraction

### Identifying Motion

Look for:
- Hover state transitions
- Scroll-triggered animations
- Loading state animations
- Micro-interactions

### Common Animation Patterns

```css
/* Hover transitions */
transition-all duration-200 ease-in-out
transition-colors duration-300
transition-transform duration-200

/* Entrance animations */
animate-fade-in (opacity 0 → 1)
animate-slide-up (translateY + opacity)
animate-scale-in (scale + opacity)

/* Hover effects */
hover:scale-105
hover:shadow-lg
hover:-translate-y-1
```

---

## Responsive Analysis

### Breakpoint Detection

Resize viewport to identify breakpoints:

| Width | Typical Breakpoint |
|-------|-------------------|
| 320-639px | Mobile (sm) |
| 640-767px | Large mobile |
| 768-1023px | Tablet (md) |
| 1024-1279px | Desktop (lg) |
| 1280px+ | Large desktop (xl) |

### What Changes

Note what adapts at each breakpoint:
- Grid columns collapse
- Navigation becomes hamburger
- Font sizes reduce
- Padding decreases
- Hidden/shown elements

---

## Quick Reference

### Element Checklist

```
[ ] Primary color (CTA buttons)
[ ] Secondary color (icons, accents)
[ ] Background color (page, sections)
[ ] Text colors (heading, body, muted)
[ ] Heading font + weight
[ ] Body font + weight
[ ] Container width
[ ] Section padding
[ ] Grid columns
[ ] Button style
[ ] Card style
[ ] Border radius consistency
[ ] Shadow usage
[ ] Animation patterns
```

### Output Format

For each analyzed element, provide:

1. **What**: The specific element/pattern
2. **How**: CSS/Tailwind approximation
3. **Where**: Which pages/sections use it
4. **Why**: What effect it creates
