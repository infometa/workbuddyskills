# Code Development Workflow Expert · 代码开发流程专家

A CodeBuddy expert plugin that provides **structured coding workflow guidance** — planning, step-by-step implementation, verification, and testing — for clean, reliable software development. It guides rather than auto-executes: the user stays in full control of every step.

## What it does

- **Requirement planning** — breaks multi-file or multi-component requests into steps with a clear output and an independent test for each.
- **Execution guidance** — executes one approved step at a time, reports results, and waits for the user before proceeding; pauses on errors or decisions.
- **Full verification** — suggests tests per function, self-checked screenshots for UI changes, real endpoint output for APIs, and the full suite before delivery.
- **Multi-task state tracking** — numbers concurrent requests (R1/R2/R3) with DONE/WIP/Q status so progress stays visible; new work joins a queue until prioritized.
- **Preference memory** — saves only preferences the user explicitly asks to remember, into `~/code/memory.md`.

## How it works

```
Request -> Plan -> Execute -> Verify -> Deliver
```

- Checks `~/code/memory.md` first for stated preferences (creates `~/code/` on first use).
- Plans before coding; verifies after every change.
- Never auto-executes, never makes network requests, never acts without the user's awareness.

## Requirements

- No API keys, no network access needed — this is a guidance workflow.
- Optional: a `~/code/` directory for storing explicitly requested preferences.

## Privacy

- Stores only what the user explicitly asks to save, and only in `~/code/memory.md`.
- Makes no network requests and never modifies its own skill files.

## Categories & tags

- **Category:** `02-Engineering`
- **Tags:** Coding Workflow · Task Planning · Code Verification
