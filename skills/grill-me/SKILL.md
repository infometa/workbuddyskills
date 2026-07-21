---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
description_zh: "深度追问式方案审查：逐层拆解设计决策，直到达成共识"
description_en: "Relentless interview to stress-test your plan, resolving each decision branch one by one"
version: 1.0.0
homepage: https://github.com/mattpocock/skills
allowed-tools: Read,Grep
---

# Grill Me

## What to do

Interview the user relentlessly about every aspect of their plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

**For each question**:
1. Provide your recommended answer before asking
2. Ask the question
3. Wait for the user's response before moving to the next question

If a question can be answered by exploring the codebase, use Read/Grep to answer it yourself — don't ask the user.

**How to structure the session**:
1. Start by listing the top-level decision branches you see in the plan (3–6 items)
2. Pick the most foundational branch first (others often depend on it)
3. Walk each branch to completion before moving to the next
4. Within a branch, resolve sub-decisions in dependency order

**When to stop**: The session is complete when all branches are resolved and there are no open "it depends" answers remaining. Close with a one-paragraph summary of the key decisions made.

## Difference from grill-with-docs

**grill-me** = pure conversational interrogation of a plan. No documentation is read or updated. Use when the plan is still conceptual and you just need to think it through.

**grill-with-docs** = interrogation anchored to the project's existing domain model (CONTEXT.md, ADRs). Terminology is challenged against the glossary, and decisions that crystallise are written into CONTEXT.md / ADRs in real time. Use when the project has an established domain model that the new plan must align with.

## When to use

Invoke this skill when:
- The user wants to stress-test a plan or design decision
- The user says "grill me" or "challenge my thinking"
- You need to surface hidden assumptions or unresolved trade-offs before implementation begins
- The project does NOT yet have a domain model / CONTEXT.md (if it does, prefer grill-with-docs)

## Tools

- **Read**: Read existing code, specs, or documentation to answer questions without asking the user
- **Grep**: Search the codebase to resolve factual questions about current behaviour
