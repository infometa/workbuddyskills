# Frontend Interface Expert · 前端界面开发专家

A CodeBuddy expert plugin for **production-grade frontend interfaces** built with React, Next.js and Tailwind CSS. It applies seven non-negotiable rules — mobile-first, intentional typography, purposeful color, feedback on every interaction, accessibility, performance from the start, and one memorable element — to ship landing pages, dashboards, forms, and component libraries that hold up at production polish.

## What it does

- **Mobile-first always** — starts from the mobile layout and enhances upward; every grid collapses to a single column; touch targets ≥ 44×44px; tables become cards, sidebars become drawers.
- **Intentional typography** — rejects Inter, Roboto, Arial; pairs a distinctive display face with a refined body face; uses dramatic (2×+) type jumps for hierarchy; body text ≥ 16px.
- **Purposeful color** — follows the 70-20-10 rule; semantic CSS variables for light/dark; depth via gradients, noise, and glassmorphism; never flat white/gray backgrounds; high-contrast CTAs.
- **Feedback on every interaction** — acknowledges taps within 100ms; optimistic updates; loading states past 1s; **preserves user input on errors**.
- **Accessibility non-negotiable** — contrast 4.5:1 (text) / 3:1 (UI); visible focus states; semantic HTML; full keyboard navigation; respects `prefers-reduced-motion`.
- **Performance from the start** — lazy loading below the fold; image placeholders to prevent layout shift; code-split heavy components; targets LCP < 2.5s, CLS < 0.1.
- **One memorable element** — every page commits to a single unforgettable design choice.

## Recommended stack

| Layer | Choice |
|-------|--------|
| Framework | Next.js 14+ (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Components | shadcn/ui |
| Animation | Framer Motion |
| Forms | React Hook Form + Zod |
| State | Zustand / Jotai |

## Anti-patterns it refuses

- Generic fonts (Inter, Roboto, Arial, Open Sans, system fonts).
- Solid white or flat gray backgrounds.
- Clearing user input on form errors.
- Mobile as an afterthought.
- Missing loading / error states for async operations.

## Example engagement

> **Build a SaaS landing page** — dark editorial theme. Cabinet Grotesk (display) + Plus Jakarta Sans (body); near-black background with copper accent; full-bleed hero with scroll-reveal text; features grid, pricing table, FAQ accordion, newsletter footer. Mobile-first, then enhance.

…delivered as runnable Next.js + Tailwind code where type, color, motion, and layout all serve one coherent vision.

## Requirements

- A Node.js project (Next.js recommended) and a browser to preview output.
- Internet access if loading web fonts or external assets.
- Review generated install commands and package versions before running.

## Categories & tags

- **Category:** `02-Engineering`
- **Tags:** Responsive UI · React & Next.js · Design Systems

## Notes

- This expert provides read-only design and implementation guidance; it makes no network requests and stores no data.
- Generated code is production-grade but should be reviewed for dependency provenance, version pinning, and accessibility compliance before shipping.
