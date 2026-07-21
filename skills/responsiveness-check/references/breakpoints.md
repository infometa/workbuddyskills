# Breakpoints Reference

## Standard Breakpoints (8)

| Width | Device Context | What Typically Breaks |
|-------|---------------|----------------------|
| 320px | Small phone (iPhone SE, Galaxy S) | Everything — if it works here, mobile is solid |
| 375px | Standard phone (iPhone 14/15, Pixel) | Minor text overflow, touch target sizing |
| 768px | Tablet portrait (iPad) | Navigation transition zone, sidebar visibility |
| 1024px | Tablet landscape / small laptop | Grid column counts, content width constraints |
| 1280px | Laptop (13-14") | Max-width containers, wide table layouts |
| 1440px | Desktop (15-16") | Content centering, hero section proportions |
| 1920px | Full HD monitor | Ultra-wide whitespace, content lost in space |
| 2560px | 4K / ultra-wide | Maximum stretch — most sites need max-width containment |

## Sweep Breakpoints (15)

Every 160px from 320 to 2560:

| Width | Transition Zone |
|-------|----------------|
| 320px | Mobile baseline |
| 480px | Large phone / small phablet |
| 640px | Phablet — Tailwind `sm:` starts here |
| 800px | Between tablet and desktop — often overlooked |
| 960px | Common nav hamburger → full switch point |
| 1120px | Sidebar appearance zone |
| 1280px | Tailwind `xl:` — laptop standard |
| 1440px | Common `max-w-7xl` container width |
| 1600px | Wide desktop |
| 1760px | Transition to ultra-wide |
| 1920px | Full HD — Tailwind `2xl:` |
| 2080px | Ultra-wide territory |
| 2240px | Max-width containers should be capping by now |
| 2400px | Extreme width — tests containment |
| 2560px | 4K upper bound |

## Trouble Zones

These width ranges are where responsive bugs hide:

| Range | Why It Breaks |
|-------|--------------|
| **768–1024px** | Tablet no-man's land. Mobile layouts are too cramped, desktop layouts don't fit. Nav transitions happen here. Many sites have NO breakpoint between 768 and 1024. |
| **1024–1280px** | Sidebar visibility zone. Content needs to decide: stack or side-by-side? Grid columns usually jump from 2 to 3 here. |
| **1440–1920px** | Wide screen gap. Sites with `max-w-7xl` (1280px) containers leave massive margins. Hero sections and full-bleed elements need attention. |
| **1920–2560px** | Ultra-wide. Text line lengths become unreadable without containment. Background images may not cover. Grid gaps look enormous. |

## Default Height

Use **900px** viewport height for all tests. This matches a typical laptop/desktop viewport and provides a consistent baseline for above-fold comparisons. Only vary height if specifically testing vertical responsiveness (rare).

## Tailwind v4 Default Breakpoints

For reference when diagnosing where CSS breakpoints are set:

| Prefix | Min Width |
|--------|-----------|
| `sm:` | 640px |
| `md:` | 768px |
| `lg:` | 1024px |
| `xl:` | 1280px |
| `2xl:` | 1536px |
