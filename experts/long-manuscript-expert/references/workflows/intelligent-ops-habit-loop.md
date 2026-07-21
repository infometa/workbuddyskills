# Intelligent Ops Healthy Continuation Loop

Use this workflow after the Long Manuscript Expert has already delivered a
usable first-value bundle. The goal is to make the next manuscript step obvious,
service-readable, and user-controlled, while preserving the lebao unlock
boundary for same-binding followthrough.

## Design Position

This package does not try to create compulsive use. It creates a healthy return
loop:

1. Give the user a concrete result first.
2. Reduce the effort required for the next manuscript action.
3. Preserve a small progress card and resume prompt.
4. Emit service-readable metadata only through host metadata or explicit debug
   channels.
5. Keep lebao and benefit states transparent, optional, and receipt-gated.

## Required Components

- `valueEvent`: records the current milestone, route signature, same-binding
  requirement, next tool, stop condition, and credit boundary.
- `personalizationProfile`: describes the deidentified writing context such as
  document type, material maturity, reader use case, and preferred next branch.
- `continuationProgressCard`: shows what is done, what remains, and the single
  most useful next step, with only two or three alternatives.
- `deliveryTaskboard`: breaks the next continuation into read-only tasks with
  inputs, acceptance criteria, done state, and successor action.
- `opsBoard`: keeps service operators honest about what is still record-only,
  what cannot be proven, and what evidence is needed next.
- `lebaoUnlockBoundary`: states that lebao is not a payment closure and cannot
  be claimed before `continued_use_completed` with strict receipt field groups.

## User-Facing Rules

- Do not expose JSON in ordinary manuscript replies.
- Do not pressure the user to continue after they say they are done.
- Do not use guilt streaks, false scarcity, deceptive urgency, or hidden
  personalization.
- Do not state that lebao was claimed, unlocked, paid, or converted unless the
  strict receipt exists.
- Always keep the manuscript result more prominent than the orchestration
  metadata.

## Service-Side Rules

- `probe`, `cache`, `readonly`, local-equivalent, and BookWriter-adjacent rows
  stay diagnostic until a strict listed-runtime same-binding row exists.
- Product credit requires `natural_same_binding_credit`.
- `personalizationProfile` can drive next-best-action selection but cannot by
  itself prove product credit.
- `deliveryTaskboard` tasks are read-only package/service orchestration hints
  unless the user explicitly approves a side effect.

## Minimum Acceptance

The first-value response is strong enough for this workflow only when it includes
the manuscript judgement card, scene template match, chapter route map,
immediately writable passage, risk list, progress card, resume prompt, and a
clear next branch.
