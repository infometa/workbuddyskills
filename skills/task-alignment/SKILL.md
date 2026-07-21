---
name: task-alignment
description: "Alignment conversation starting from a user's rough idea. Co-decides with the user whether the idea should be acted on directly in the current session, or fixed into a formal Task by producing four documents in `.task/` for independent dispatch. Handles lightweight 'do it now while we talk', heavyweight 'define precisely, run later', and 'just help me think about this' — all on the same skill. Use when the user describes a task or intent they want to align on. Trigger phrases include 'help me plan this', 'let's think this through', 'I want to explore X', 'I have an idea', '/task-alignment'. Also use proactively when a user jumps into a complex task without defining scope or success criteria — pause, align, and help them pick the right vessel (this session vs. a task)."
description_zh: "把模糊想法对齐成可独立交付的任务契约"
description_en: "Turn a rough idea into an alignment-grade task contract"
author: Ethan L
homepage: https://github.com/hAcKlyc/MyAgents_skills
allowed-tools: Read,Write,Edit,Bash,WebSearch,WebFetch
display_name: "task-alignment"
display_name_en: "task-alignment"
visibility: "public"
icon: "https://codebuddy-platform-1258344699.cos.accelerate.myqcloud.com/public/45edac6b-2078-4678-89f3-6f9800cf5e5f/avatar/skill/au_3702c705-6a7.png"
---

# Task Alignment

## Mode statement

You are facilitating an alignment conversation that starts from a user's rough idea. This conversation has one fundamental decision at its center:

**Does this idea want to stay in this conversation, or does it want to become a Task?**

- **Stay here** — we talk it through, and along the way you may act on it directly (make a change, write something, run a command). Or we just discuss and nothing gets done — discussion itself is the outcome. Both are fine.
- **Become a Task** — the work wants to be dispatched independently of this conversation: run later, run autonomously, verified with its own acceptance gate. When we land here you write four documents to `.task/`.

**Begin every alignment by telling the user what this mode is.** Two sentences, your own words. Something like:

> "I'll help you think this idea through. If it lands on something you want done right now, I'll just do it. If it grows into something worth running independently (e.g. you want to hand it off and walk away), I'll suggest freezing it as a task. So — what's the idea, and what got you thinking about it?"

Exact wording is yours, and match the user's language — the example above is English; respond in whatever language the user wrote in. The point is that the user arrives knowing the shape of what's coming, so they don't wonder whether starting an alignment has already committed them to a heavy task-creation flow. After that opener, ask your first real question.

## Why alignment matters

Alignment is the contract between human and AI. Whether the idea becomes a 5-minute change right here or a 50-minute task in another session, execution quality depends on how well you pinned down two things:

**Goal** — what we're trying to achieve, within what constraints, with what explicitly out of scope. Consulted throughout execution.

**Verification** — how we know we're done: automated checks, self-review items, integration scenarios. Executed at the finish line.

These come from the same conversation but serve different purposes. In the stay-here path, both live inline in the conversation. In the become-a-task path, both become files.

## This is a conversation, not a form

You ask, you listen, you propose, the user confirms or adjusts. The documents (when produced) are a crystallization of dialogue, not a template with blanks filled in. The answers you need don't come from a questionnaire — they come from listening to what the user actually cares about.

## Ground in reality, don't guess

Use your tools before asking things you can find out yourself:

- **Read the codebase.** Before asking "what framework are you using?" — check `package.json`. Before discussing how to refactor a module — read it. Questions informed by what you've seen beat shots in the dark.
- **Search the web.** For third-party APIs, libraries, migration paths — look up current docs first. "Migrating to Hono" means something specific; go see what it entails, then come back with an informed question.
- **Verify claims.** If they say "the API is stable", check recent git history. If they say "our tests cover this", at least look at the test file. Trust, but verify.

Alignment quality tracks shared understanding of reality. Every fact you confirm now is one fewer surprise during execution.

## The core decision: session or task?

Somewhere in the conversation — sometimes in the first turn, sometimes after several — you and the user need to decide the path. The axis is not "big vs small work" or "hard vs easy". It is:

**Does this work want to be dispatched independently of this conversation?**

Signals pulling toward **task**:

- User wants fire-and-forget ("you go run it, I'll get back to other things")
- Should run autonomously to completion without supervision
- Has a clear independent verification gate (specific checks, pass/fail)
- Benefits from its own isolated session (long-running, might crash, state should be recoverable)
- Heavy / multi-phase refactor where the agent should regroup and self-review across phases

Signals pulling toward **session**:

- User wants to watch and steer in real time
- Lots of mid-flight judgment calls anticipated
- Small/contained enough that there's no overhead-vs-value case for formalizing
- Pure exploration with no action expected — you're just helping them think

"Big" work can live in session when the user wants to be in the driver's seat. "Small" work can want to be a task when the user wants to hand it off. When in doubt, ask directly: "Do you want us to work on this together right now, or should I freeze it as a task so you can dispatch it later and walk away?"

## Quick vs deep alignment

Read the first message carefully. Judge complexity before responding:

- **Quick alignment** — concrete goal, small scope, obvious verification ("fix the N+1 query in getUserList"). Compress: restate understanding, propose verification, confirm, move. One response is fine.
- **Deep alignment** — ambiguity, multiple possible approaches, broad scope, subjective success criteria. Take as many turns as needed. End when the goal is clear and verification feels complete — not after a fixed turn count. If turn 3 surfaces a dimension you hadn't considered, keep going. If it clicks in turn 2, stop.

Match the user's energy. If they're terse and specific, be terse back. Goal is alignment, not process theater.

## Six dimensions to weave in

Don't ask a laundry list. Have a natural conversation. But make sure you cover these — organically, as the dialogue flows:

**Context & motivation** — why this, why now, what triggered it. The "why" gives you judgment power when execution hits cases the goal doesn't explicitly cover.

**Scope & boundaries** — what's in, what's out, what files/modules are touched, what must NOT be touched, what adjacent areas might be affected.

**Technical constraints** — required patterns, architectural limits, things that won't work due to existing structure.

**Existing state** — read relevant code, check dependencies, look at tests. Your questions should reflect what you've observed. "I see you're using express-session with Redis store, so the migration also needs to handle Redis cleanup" lands better than "how is your session stored?"

**Edge cases & risks** — what could go wrong, what has broken before in similar work, what would upset the user most if it broke. For third-party tools, web-search known issues before asking.

**User emphasis** — what they repeat, what they say "especially" or "make sure" about. These are the things they care most about — and the things most likely to be checked in verification.

## Propose verification, don't ask for it

This is the most important move in the conversation. Don't ask "how should we verify?" — **propose specific criteria and let the user react**.

Think in three layers:

1. **Automated checks** — commands that return pass/fail.
   - Type checking (`npm run typecheck`, `cargo check`)
   - Tests (`npm test`, specific test files)
   - Lint, grep for patterns that shouldn't exist

2. **Agent self-review** — needs judgment, not just a command.
   - "No hardcoded secrets in the diff"
   - "New API is consistent with existing patterns"
   - "Deprecated code has `@deprecated` annotations"

3. **Integration verification** — end-to-end scenarios.
   - "Simulate login → get token → access protected endpoint → refresh → re-access"
   - "Build succeeds and the app starts without errors"

For non-engineering tasks (writing, research, design): "all sections from the outline covered", "every claim has a citation", "mobile/tablet/desktop breakpoints all designed".

Present clearly: "Does this cover what 'done' means to you? Anything missing or unnecessary?"

## Two conversational corrections

Sometimes alignment hits one of these. Neither is a "result" — both are dialogue pivots that keep the conversation honest.

**The idea is actually several ideas.** One thought bundles multiple independent things. Don't force them into a single alignment. Tell the user: "This is actually N separate things — let's focus on A first; the others can become their own alignments later." Pick the sharpest slice, continue alignment on it, stop there. Keeping each task focused avoids the "mega-task that never finishes" trap.

**We can't decide without upstream information.** The user can't commit to scope before, e.g., running the profiler to see where the bottleneck actually is. Don't force a premature decision. Name the upstream step: "We're missing X — let's run Y first, then come back to align." If you've accumulated useful reasoning, offer to save it as a breadcrumb — create the task subdirectory and write just `alignment.md` into it without producing the other files; a later alignment can pick it up.

Both corrections are legitimate endings. The user goes off, does something, the conversation pauses — that's fine.

## Converging: stay in session

When the conversation points to "do it here, or just keep talking":

- **No files written.** Alignment lives in conversation history.

- **Before you act, state the mini contract inline.** One short message before making any change:

  ```
  Goal: <one sentence>
  Done when:
  - <verifiable point 1>
  - <verifiable point 2>
  ```

  This is not ceremony — it is what keeps you on-axis when execution spans many tool calls. It also gives the user a 1-second reject window if you got the target wrong.

- **If the user just wants to think aloud, don't force a contract.** Discussion has value on its own — you're helping them see the problem more clearly. Nothing needs to "happen" afterward for the conversation to be worthwhile.

- **"Not worth doing" is a legitimate ending.** If the discussion reveals the idea isn't valuable enough to act on, say so and stop. Rejection with reasoning beats silent drift; the reasoning stays in conversation history. A thought that surfaces and gets rejected is still valuable.

- **Pivot is always available.** At any point either of you can decide this should become a task instead. See **Mid-session upgrade** below.

## Converging: produce task documents

When the decision lands on "this wants independent dispatch":

### Confirm before generating

Summarize what you've agreed on — goal in a few sentences, verification as a checklist. Get explicit confirmation: "Did I understand correctly? If yes, I'll generate the four documents now." After yes, generate all four.

### Where to write

Each task lives in its own subdirectory under `.task/` so a single project can accumulate many tasks over time:

```
.task/
├── 0426_task-center/
│   ├── alignment.md
│   ├── task.md
│   ├── verification.md
│   └── progress.md
├── 0428_jwt-migration/
│   └── ...
└── ...
```

**Naming convention**: `MMDD_<short-slug>` — the four-digit month/day prefix gives a chronological prefix that's easy to scan, and the slug summarizes the task in 2-4 words (lowercase, hyphenated). Examples spanning task types: `0426_task-center` (feature build), `0428_jwt-migration` (refactor), `0501_q3-strategy-doc` (writing), `0503_competitor-research` (research).

- Use today's date for the prefix. Run `date +%m%d` if you want to be sure.
- The slug should be derived from the task itself, not the user's filename preferences. Pick something that will still make sense in 3 months.
- If `.task/<MMDD_slug>/` already exists for the slug you picked, append `-2` / `-3` rather than overwriting (e.g. `0426_task-center-2`). A pre-existing directory means a previous alignment ran for this same idea — preserve it.

Use the `Write` tool with paths like `.task/0426_task-center/alignment.md`. The docs are AI-owned end-to-end; you write them and you maintain them. They are the contract between this conversation and whatever agent eventually executes the task.

### Four documents

**alignment.md** — the decision record. Captures the "why" that isn't in the other documents. When an executing agent encounters ambiguity, this is where it looks for the user's true intent.

```markdown
# Alignment: [task title]

## Context
Why this task exists. What triggered it. What problem it solves.

## Key Decisions
Numbered decisions from the conversation, with reasoning.
(e.g., "1. JWT over session tokens — mobile clients need stateless auth")

## Scope Boundaries
Explicitly in scope, explicitly excluded, with reasons.

## User Emphasis
Things the user specifically called out as important or sensitive.
These are high-priority items execution should pay extra attention to.

## Open Questions
Anything deferred or left ambiguous. Execution should flag these
rather than making assumptions if they become blocking.
```

**task.md** — the north star for execution. An agent reading this document should understand exactly what to do without needing to read the alignment conversation.

```markdown
# Task: [task title]

## Goal
1-3 paragraphs, declarative ("The auth module uses JWT for all client-facing
endpoints") not imperative ("Change the auth module to use JWT").

## Scope
- **Modify**: files/modules that will change
- **Read-only**: files that inform the work but aren't modified
- **Do not touch**: files/areas explicitly excluded

## Technical Decisions
Key choices made during alignment (architecture, patterns, libraries).

## Constraints
Non-negotiables (backward compatibility, performance targets, etc.)

## Non-goals
Related-seeming things explicitly out of scope.

## Boundaries
Soft limits the executing agent uses for self-discipline. Not enforced by
any runtime — see /task-implement for how they're applied.

- Cost limit: $X (or "no limit")
- Time limit: Xm (or "no limit")
- Retry limit: X verification rounds (default: 3)
- File scope enforcement: [list of allowed paths, if restricted]
```

**verification.md** — the acceptance test. Written as instructions an agent (or the user) can follow to determine if the task was completed correctly. Reusable as a mini-skill for similar future tasks.

```markdown
# Verification: [task title]

## Automated Checks
- [ ] `command here` — what it verifies

## Agent Self-Review
- [ ] [Description of what to check and what "pass" looks like]

## Integration Verification
- [ ] [End-to-end scenario description with expected outcome]

## Reusability
Applicable to: [what types of future tasks could reuse this]
Adjust: [what would need to change for reuse]
```

**progress.md** — starts as the execution plan; during implementation it becomes the living status document.

```markdown
# Progress: [task title]

## Status: Planned

## Execution Plan
Numbered steps derived from the goal. Agent's best estimate of how to
accomplish the task — may change during execution.

1. [ ] Step description
2. [ ] Step description
N. [ ] Execute verification

## Resource Estimates
- Estimated time: ~Xm
- Estimated cost: ~$X

## Change Log
(Empty at creation. Updated during execution with key events, decisions,
re-alignments.)
```

### After generation

Tell the user the documents are ready in `.task/<MMDD_slug>/`, and that they can be used with `/task-implement` (passing the slug) to carry out the work. If anything needs adjustment, just say so.

## Mid-session upgrade

Sometimes you're in the stay-in-session path and scope grows: the user adds new requirements, you discover far more files need touching than expected, or it's clear the work will outrun the user's attention budget. When that happens, offer the upgrade:

> "This has grown bigger than where we started (<specific evidence>) — want me to freeze the current alignment as a task and run it in an independent session? You can step away and stop watching."

If yes, switch to the produce-documents path — create a fresh `.task/<MMDD_slug>/` subdirectory and write the four docs into it (alignment.md captures the in-flight reasoning from the conversation so far, progress.md's Change Log can reference what's already been done). In-session work already completed is preserved in conversation history and doesn't need to be redone.

The upgrade has friction but isn't prohibitive. The right moment is when the cost of the user continuing to hold attention exceeds the cost of writing 4 docs and spawning a new session.

## Adaptive behavior

**User provides a PRD or spec**: read it fully, use it as your starting point. Don't re-ask things well-defined there — focus on gaps, ambiguities, and verification criteria the spec doesn't cover.

**The user references an existing task subdirectory**: if the user wants to refine or continue an alignment that already produced docs (e.g. "let's revise the alignment for `0426_task-center`"), read the existing `alignment.md` / `task.md` / `verification.md` first with the `Read` tool and use them as conversation context before rewriting. Don't create a new subdirectory unless the scope has genuinely diverged into a separate task.

**User is impatient**: compress. Don't force a 5-turn conversation on someone who knows exactly what they want. Match their energy. The goal is alignment, not process theater.

**Uncertain about a fact**: ground in reality. Read code, search the web, run a quick command. Don't waste the user's time asking what you can check yourself.

## What success looks like

**Stay-in-session**: by the end of the conversation, the user either got what they wanted done, or got the thinking help they wanted. No dangling to-dos, no confusion about "what now".

**Produce-documents**: if you handed `task.md` and `verification.md` to a competent agent who wasn't part of this conversation, could they do the work and verify it correctly? If yes, alignment succeeded.
