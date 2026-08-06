# Design Rules & Forbidden Patterns

## Baseline Configuration

| Dial | Default | Range |
|------|---------|-------|
| DESIGN_VARIANCE | 8 | 1=Symmetry, 10=Asymmetric |
| MOTION_INTENSITY | 6 | 1=Static, 10=Cinematic |
| VISUAL_DENSITY | 4 | 1=Airy, 10=Packed |

## Architecture Conventions

- **DEPENDENCY VERIFICATION:** Check `package.json` before importing. Output install command if missing.
- **Framework:** React/Next.js default. Server Components by default, `"use client"` for interactive leaf.
- **Styling:** Tailwind CSS. Check version — NEVER mix v3/v4 syntax.
- **ANTI-EMOJI POLICY:** NEVER use emojis. Use Phosphor or Radix icons.
- **Viewport:** `min-h-[100dvh]` not `h-screen`. CSS Grid not flex percentage math.
- **Layout:** `max-w-[1400px] mx-auto` or `max-w-7xl`.

## Design Rules

| Rule | Directive |
|------|-----------|
| Typography | Headlines: `text-4xl md:text-6xl tracking-tighter`. Body: `text-base leading-relaxed max-w-[65ch]`. **NEVER** Inter — use Geist/Outfit/Satoshi. **NEVER** Serif on dashboards. |
| Color | Max 1 accent, saturation < 80%. **NEVER** AI purple/blue. One palette. |
| Layout | **NEVER** centered heroes when VARIANCE > 4. Force split-screen or asymmetric. |
| Cards | **NEVER** generic cards when DENSITY > 7. Use `border-t`, `divide-y`, or spacing. |
| States | **ALWAYS**: Loading (skeleton), Empty, Error, Tactile feedback (`scale-[0.98]`). |
| Forms | Label above input. Error below. `gap-2` for input blocks. |

## Anti-Slop Techniques

- **Liquid Glass:** `backdrop-blur` + `border-white/10` + `shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]`
- **Magnetic Buttons:** `useMotionValue`/`useTransform` — never `useState` for continuous animations
- **Perpetual Motion:** INTENSITY > 5→ infinite micro-animations (Pulse, Float, Shimmer)
- **Layout Transitions:** Framer `layout` and `layoutId`
- **Stagger:** `staggerChildren` or CSS `animation-delay: calc(var(--index) * 100ms)`

## Forbidden Patterns

| Category | Banned |
|----------|--------|
| Visual | Neon glows, pure black (#000), oversaturated accents, gradient text on headers, custom cursors |
| Typography | Inter font, oversized H1s, Serif on dashboards |
| Layout | 3-column equal card rows, floating elements with awkward gaps |
| Components | Default shadcn/ui without customization |

## Creative Arsenal

| Category | Patterns |
|----------|----------|
| Navigation | Dock magnification, Magnetic button, Gooey menu, Dynamic island, Radial menu |
| Layout | Bento grid, Masonry, Chroma grid, Split-screen scroll, Curtain reveal |
| Cards | Parallax tilt, Spotlight border, Glassmorphism, Holographic foil, Swipe stack |
| Scroll | Sticky stack, Horizontal hijack, Locomotive sequence, Zoom parallax |
| Text | Kinetic marquee, Text mask reveal, Scramble effect, Gradient stroke |
| Micro | Particle explosion, Skeleton shimmer, Directional hover, Ripple click, Mesh gradient |

## Bento Paradigm

- **Palette:** Background `#f9fafb`, cards pure white with `border-slate-200/50`
- **Surfaces:** `rounded-[2.5rem]`, diffusion shadow
- **Typography:** Geist/Satoshi, `tracking-tight` headers
- **Animation:** Spring physics (`stiffness: 100, damping: 20`), infinite loops, `React.memo` isolation

## Copywriting Frameworks

**AIDA** (landing pages, emails):
- ATTENTION: Bold headline (promise or pain)
- INTEREST: Elaborate problem
- DESIRE: Show transformation
- ACTION: Clear CTA

**PAS** (pain-driven):
- PROBLEM → AGITATE → SOLUTION

**FAB** (differentiation):
- FEATURE → ADVANTAGE → BENEFIT

## CTA Formula
[Action Verb] + [What They Get] + [Urgency/Ease]

Bad: Submit, Click here, Learn more
Good: "Start my free trial", "Get the template now"

## Springs & Easings

| Feel | Framer Config |
|------|---------------|
| Snappy | `stiffness: 300, damping: 30` |
| Smooth | `stiffness: 150, damping: 20` |
| Bouncy | `stiffness: 100, damping: 10` |
| Heavy | `stiffness: 60, damping: 20` |

| CSS Easing | Value |
|------------|-------|
| Smooth decel | `cubic-bezier(0.16, 1, 0.3, 1)` |
| Elastic | `cubic-bezier(0.34, 1.56, 0.64, 1)` |

## Brand Override (when active)

- Dark: `#141413`, Light: `#faf9f5`, Mid: `#b0aea5`
- Accents: Orange `#d97757`, Blue `#6a9bcc`, Green `#788c5d`
- Fonts: Poppins (headings), Lora (body)
