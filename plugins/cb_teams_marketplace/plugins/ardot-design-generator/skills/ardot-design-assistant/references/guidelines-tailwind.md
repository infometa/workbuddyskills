# Tailwind v4 Implementation Guidelines

This document provides Tailwind v4 specific guidelines for implementing .ardot designs in code.

**NOTE**: These guidelines are specific to Tailwind v4. If you are deliberately using an older version of Tailwind (v3 or earlier), you may bypass the v4-specific syntax rules (such as `@import "tailwindcss";` vs `@tailwind` directives) and adapt accordingly.

## Core Principle

**Use Tailwind classes exclusively throughout - NEVER use inline styles for any property (sizing, colors, spacing, typography, etc.).**

## CSS Variables Setup

### Structure of globals.css

Your `globals.css` should follow this structure:

```css
@import "tailwindcss";

:root {
  /* Design variables from .ardot file - ONLY single values */
  --color-primary: #3b82f6;
  --color-secondary: #8b5cf6;
  --spacing-base: 16px;
  /* DO NOT store font stacks here */
}

@layer base {
  html, body {
    height: 100%;
  }

  /* Font family utilities - Define font stacks directly here */
  .font-primary {
    font-family: "Inter", sans-serif;
  }

  .font-secondary {
    font-family: "JetBrains Mono", monospace;
  }
}
```

### Guidelines

- Read design variables using `fetch_variables`
- Convert to CSS custom properties in `:root` block for single values only (colors, numbers, keywords)
- Map all design variables using exact names from design file
- **IMPORTANT**: Use `:root` block for design variables (NOT `@theme` - Tailwind v4's `@theme` only supports custom properties and `@keyframes`)
- **DO NOT add manual resets** - `@import "tailwindcss";` includes Preflight automatically
- **CRITICAL for Next.js projects**: If using `next/font` loaders, DO NOT re-wrap their CSS variables (like `--font-geist`) in your `:root` block. Instead, reference them directly in `@layer base` utility classes (see Font Loading section)

## Font Implementation

### Core Rules

**CSS variables work for single values only** (colors, numbers, keywords). **DO NOT use them for font stacks.**

❌ **WRONG**:
```css
:root {
  --font-primary: "JetBrains Mono", monospace;  /* Breaks with comma-separated values */
}
```

✅ **CORRECT**: Define fonts in `@layer base` utility classes:
```css
@layer base {
  .font-primary {
    font-family: "JetBrains Mono", monospace;
  }
  
  .font-secondary {
    font-family: "Inter", sans-serif;
  }
}
```

### Next.js Font Loaders

When using `next/font/google` or `next/font/local`:

❌ **NEVER wrap Next.js font variables in `:root`**:
```css
/* WRONG - nested var() references break */
:root {
  --font-primary: var(--font-geist);
}
```

✅ **DO reference them directly in utility classes**:
```css
@layer base {
  .font-primary {
    font-family: var(--font-jetbrains-mono), "JetBrains Mono", monospace;
  }
}
```

### Implementation Workflow

1. Read font names from design using `fetch_variables`
2. Load fonts via `<link>` tags OR Next.js font loaders in layout.tsx
3. Create utility classes in `@layer base` (`.font-primary`, `.font-secondary`)
4. Use classes in components: `className="font-primary"`
5. **NEVER use** `font-[var(--font-name)]` or inline styles for fonts

## Font Loading

### Tailwind v4 Requirements

❌ **NEVER in Tailwind v4**:
- `@import url()` in CSS files
- `font-[family-name:var(...)]` syntax
- `--turbopack` flag

✅ **Load fonts via**:
- `<link>` tags in layout.tsx `<head>`, OR
- Next.js font loaders (`next/font/google`, `next/font/local`)

### Examples

**Option 1: Manual loading**
```tsx
// layout.tsx
<head>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
</head>
```

**Option 2: Next.js font loaders**
```tsx
// layout.tsx
import { JetBrains_Mono } from "next/font/google";

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export default function RootLayout({ children }) {
  return (
    <html>
      <body className={jetbrainsMono.variable}>
        {children}
      </body>
    </html>
  );
}
```

```css
/* globals.css */
@layer base {
  .font-primary {
    font-family: var(--font-jetbrains-mono), "JetBrains Mono", monospace;
  }
}
```

## Icon Font Setup

- **If design uses `icon_font` nodes**:
  1. Add Google Fonts link in layout.tsx `<head>` (following the Font Loading Rules above)
  2. Add utility class in `@layer base` section of globals.css with appropriate font-feature-settings
  3. Render as `<span>` elements with icon name as text content
  4. Use inline styles for font-weight if needed (e.g., `style={{ fontWeight: 100 }}`)
  5. **NEVER use `@font-face`** - Always use CDN links

## Viewport Setup

- Add `height: 100%` to `html` and `body` in `@layer base` section of globals.css (as shown in CSS Variables Setup example)
- Add `h-full` class to `<html>` and `<body>` in layout.tsx
- Ensures viewport-relative sizing works throughout app
- Design dimensions are specifications, not fixed constraints
- **DO NOT use wildcard selectors** - use the `@layer base` approach shown above

## Tailwind v4 Import and Preflight

### Correct Import Syntax

**Tailwind v4 uses a simplified import syntax** in `globals.css`:

```css
@import "tailwindcss";
```

This single import automatically includes:
- Base styles (Preflight reset)
- Component classes
- Utility classes

**DO NOT use the old v3 syntax**:
```css
/* ❌ WRONG - This is v3 syntax */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Preflight Reset Behavior

The `@import "tailwindcss";` automatically includes Preflight, which:
- Removes margins and padding from all elements
- Sets `box-sizing: border-box` on all elements
- Resets headings and lists (they inherit font properties)
- Makes images block-level with responsive sizing

### Critical Rules

- **NEVER manually add global resets** - Preflight handles everything
- **NEVER use wildcard selectors** like `* { margin: 0; padding: 0; }` in globals.css
- **DO NOT duplicate Preflight functionality** - it's already included
- Use `@layer base { ... }` ONLY for additional custom base styles that don't conflict with Preflight

## Layout Conversion

### Container Sizing

- Root containers: `h-full w-full` or `h-screen w-screen` (NOT fixed dimensions)
- Fixed dimensions only for specific elements (e.g., sidebar: `w-[280px]`)

### fill_container Translation

- In flex containers: use `flex-1`
- For explicit sizing: `w-full` (width), `h-full` (height)
- **IMPORTANT**: `h-full` requires parent chain has height set
- For scrollable containers: `flex-1 overflow-auto`
- **NEVER use inline styles** for sizing
- **Multiple fill_container Children**:
  * In flex containers, multiple children with `fill_container` → each needs `flex-1`
  * Applies to both horizontal and vertical flex layouts
  * Distributes space equally among children
- **Height fill_container**:
  * ANY component with `height: "fill_container"` MUST have `h-full` class
  * Applies universally regardless of component type or parent layout
  * Verify every `fill_container` height has corresponding `h-full` class

### hug_contents Translation

- Use `w-fit` (width), `h-fit` (height)
- NEVER use inline styles

### Flex Context

- Parent must be flex container for `flex-1` to work
- Use `min-h-0` on flex children that need to shrink below content size
- Scrollable flex children: `flex-1 overflow-auto`

### Verification

- Check ALL `fill_container`/`hug_contents` converted to Tailwind classes
- Ensure NO inline styles for width/height

## Style Implementation

Use **Tailwind classes exclusively** (NO inline styles) for all styling:

### 1. Layout

- Position: `relative`, `absolute`, `fixed`, `sticky`
- Display: `flex`, `flex-col`, `grid`, `block`, `inline-block`
- Alignment: `items-center`, `justify-between`, etc.
- Gap: `gap-4`, `gap-[16px]` (match design exactly)

### 2. Spacing

Match design values exactly:
- Padding: `p-4`, `px-6`, `pt-[12px]`, etc.
- Margin: `m-4`, `mx-auto`, `mt-[8px]`, etc.
- Use arbitrary values `[Npx]` when needed

### 3. Dimensions

- Width: `w-[280px]` (fixed), `w-full` or `flex-1` (fill_container), `w-fit` (hug_contents)
- Height: `h-[48px]` (fixed), `h-full` or `flex-1` (fill_container), `h-fit` (hug_contents)
- Min/max: `min-w-[200px]`, `max-h-[600px]`
- **CRITICAL**: Never use inline styles for dimensions

### 4. Colors and Borders

- Background: `bg-[var(--color-name)]` - NO hardcoded hex values
- Border: `border`, `border-2`, `border-[var(--color-border)]`
- Border radius: `rounded`, `rounded-lg`, `rounded-[12px]`
- Text: `text-[var(--color-text)]`
- Shadows: `shadow-sm`, `shadow-[custom]`

### 5. Typography

- **Font family**: Use utility classes defined in `@layer base` (see "CSS Custom Properties and Font Stacks" section above)
  - ✅ Correct: `className="font-primary"`
  - ❌ NEVER: `font-[var(--font-primary)]` (arbitrary value syntax doesn't work with CSS variables)
  - ❌ NEVER: `style={{ fontFamily: 'var(--font-primary)' }}` (avoid inline styles unless necessary)
  - For Next.js font loaders: Create utility classes that reference the Next.js variables, then use those classes
- Font size: `text-sm`, `text-[14px]`
- Font weight: `font-medium`, `font-[500]`
- Line height: `leading-normal`, `leading-[24px]`
- Letter spacing: `tracking-normal`, `tracking-[0.02em]`

### 6. Interactive States

- Hover: `hover:bg-[var(--color-hover)]`, `hover:opacity-80`
- Active: `active:scale-95`
- Disabled: `disabled:opacity-50`, `disabled:cursor-not-allowed`
- Focus: `focus:outline-none`, `focus:ring-2`

## SVG Styling

For SVG path extraction and implementation workflow, see guidelines-code.md "SVG Path Implementation" section.

### Tailwind-Specific SVG Styling

When styling SVG elements with Tailwind:

- **Fill colors**: Use `fill-[var(--color-name)]` with CSS variables
  - Example: `fill-[var(--primary)]`
- **Stroke colors**: Use `stroke-[var(--color-name)]`
  - Example: `stroke-[var(--border)]`
- **Stroke width**: Use `stroke-[2]` or arbitrary values `stroke-[1.5px]`
- **SVG sizing**: Use standard sizing classes `w-6 h-6` or arbitrary `w-[24px] h-[24px]`
- **NEVER use inline styles** - always use Tailwind classes or className with CSS variables

Example:
```tsx
<svg className="w-6 h-6 fill-[var(--icon-primary)]" viewBox="0 0 24 24">
  <path d="M12 2L2 7l10 5 10-5-10-5z" />
</svg>
```
