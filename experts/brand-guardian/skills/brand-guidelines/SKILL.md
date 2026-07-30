---
name: brand-guidelines
description: Applies Anthropic's official brand colors and typography to any sort of artifact that may benefit from having Anthropic's look-and-feel. Use it when brand colors or style guidelines, visual formatting, or company design standards apply.
description_zh: "应用 Anthropic 品牌配色和排版到设计产物"
description_en: "Apply Anthropic brand colors and typography to design artifacts"
license: Complete terms in LICENSE.txt
---

# Anthropic Brand Styling

## Overview

To access Anthropic's official brand identity and style resources, use this skill.

**Keywords**: branding, corporate identity, visual identity, post-processing, styling, brand colors, typography, Anthropic brand, visual formatting, visual design

## Brand Guidelines

### Colors

**Main Colors:**

- Dark: `#141413` - Primary text and dark backgrounds
- Light: `#faf9f5` - Light backgrounds and text on dark
- Mid Gray: `#b0aea5` - Secondary elements
- Light Gray: `#e8e6dc` - Subtle backgrounds

**Accent Colors:**

- Orange: `#d97757` - Primary accent
- Blue: `#6a9bcc` - Secondary accent
- Green: `#788c5d` - Tertiary accent

### Typography

- **Headings**: Poppins (with Arial fallback)
- **Body Text**: Lora (with Georgia fallback)
- **Note**: Fonts should be pre-installed in your environment for best results

## Features

### Smart Font Application

- Applies Poppins font to headings (24pt and larger)
- Applies Lora font to body text
- Automatically falls back to Arial/Georgia if custom fonts unavailable
- Preserves readability across all systems

### Text Styling

- Headings (24pt+): Poppins font
- Body text: Lora font
- Smart color selection based on background
- Preserves text hierarchy and formatting

### Shape and Accent Colors

- Non-text shapes use accent colors
- Cycles through orange, blue, and green accents
- Maintains visual interest while staying on-brand

## Technical Details

### Font Management

- Uses system-installed Poppins and Lora fonts when available
- Provides automatic fallback to Arial (headings) and Georgia (body)
- No font installation required - works with existing system fonts
- For best results, pre-install Poppins and Lora fonts in your environment

### Color Application

- Uses RGB color values for precise brand matching
- Applied via python-pptx's RGBColor class
- Maintains color fidelity across different systems

## Extended Brand Standards

Beyond Anthropic's own palette above, this skill includes reusable, generic brand-system references for building or auditing any brand's visual identity. Load them when the task goes beyond applying Anthropic styling:

- **`references/color-palette-management.md`** — Color-system hierarchy, WCAG 2.1 contrast ratios & luminance formula, 60/30/10 usage ratios, and brand-compliance validation rules.
- **`references/logo-usage-rules.md`** — Logo variants, clear-space & minimum-size rules, background compatibility, co-branding layouts, file formats, and platform-specific sizing.
- **`references/typography-specifications.md`** — Type scale (Major Third), font weights, line-height & letter-spacing tables, responsive adjustments, and CSS/Tailwind implementation.
- **`references/brand-guideline-template.md`** — A fill-in template for authoring a complete brand-guidelines document (color, typography, logo, voice, imagery).

Use these when you need quantitative, checkable standards (e.g. verifying contrast, defining a type scale, or writing logo-usage rules) rather than only Anthropic's look-and-feel.
