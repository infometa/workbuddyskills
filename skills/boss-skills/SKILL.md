---
name: boss-skills
description: "Distill a real boss into an AI skill, or generate a boss skill from famous entrepreneur archetypes (Elon Musk, Steve Jobs, Jeff Bezos, Jensen Huang). Use when user wants boss analysis, managing-up guidance, persona extraction, or entrepreneur-style decision simulation."
description_zh: "蒸馏老板或生成企业家原型 Skill，模拟管理风格与决策模式"
description_en: "Distill bosses or generate entrepreneur archetype Skills for management simulation"
version: "1.1.0"
homepage: https://github.com/vogtsw/boss-skills
allowed-tools: Read, Write, Edit, Bash
---

# Create Boss

Use this skill in two modes:

1. `real boss mode`
   Turn real chat logs, meeting notes, emails, comments, and project artifacts into a boss skill.
2. `archetype mode`
   Generate a boss skill inspired by a public entrepreneur operating style.

## Trigger phrases

- `/create-boss`
- `/list-bosses`
- `/boss-rollback`
- `/delete-boss`
- "create a boss skill"
- "analyze my boss"
- "build a Musk-style boss"
- "make a Steve Jobs style leader"
- "give me a Bezos-style management model"
- "list boss archetypes"

## Tools

- Parse imported material with the files in [`tools/`](tools).
- Write or update generated boss skills with [`tools/skill_writer.py`](tools/skill_writer.py).
- Read template prompts from [`prompts/`](prompts) when working from real source material.
- Read bundled entrepreneur templates from [`archetypes/`](archetypes) when working in archetype mode.

These scripts are internal implementation details for the agent.
Do not ask the user to run Python commands manually unless they explicitly want a developer workflow.

## Workflow

### Mode 1: Real Boss

1. Ask for the boss name, baseline profile, and initial management impression.
2. Ask for source material: chats, meeting notes, docs, email, or pasted text.
3. Distill three outputs:
   - `judgment.md`
   - `management.md`
   - `persona.md`
4. Run the writer script yourself to write the boss bundle into `bosses/{slug}/`.
5. Show the generated commands:
   - `/{slug}`
   - `/{slug}-judgment`
   - `/{slug}-management`
   - `/{slug}-persona`

### Mode 2: Entrepreneur Archetype

1. If the user asks for an entrepreneur-style boss, infer the best matching archetype or offer a short list:
   - `elon-musk`
   - `steve-jobs`
   - `jeff-bezos`
   - `jensen-huang`
2. Run the writer script yourself to generate the skill. Do not expose the internal command as the primary UX.
3. Tell the user the generated trigger command, for example:
   - `/elon-musk`
   - `/steve-jobs`
4. If the user asks to browse or inspect templates, summarize the available archetypes in natural language instead of telling them to run a script.

## Management Commands

When the user asks for boss management operations, handle them internally with the bundled scripts:

- `/list-bosses`
  Run `tools/skill_writer.py --action list` and summarize the available boss skills.
- `/boss-rollback {slug} {version}`
  Confirm the target slug and version, then run `tools/version_manager.py --action rollback`.
- `/delete-boss {slug}`
  Confirm before deletion, then run `tools/skill_writer.py --action delete --slug {slug}`.

Do not tell normal users to copy these commands manually. Execute the workflow yourself and report the result.

## Bundled Archetypes

- `elon-musk`: first-principles, speed, technical pressure
- `steve-jobs`: taste, simplicity, product clarity
- `jeff-bezos`: mechanism design, customer obsession, written thinking
- `jensen-huang`: platform strategy, technical depth, constructive intensity

## Files Created

Every generated boss skill should include:

- `SKILL.md`
- `judgment.md`
- `management.md`
- `persona.md`
- `meta.json`
- `judgment_skill.md`
- `management_skill.md`
- `persona_skill.md`

## Safety Framing

- Treat entrepreneur presets as public-style archetypes, not claims of exact private impersonation.
- Prefer management patterns, decision rules, and communication norms over catchphrases.
- If the user asks for a hybrid with a real boss, keep real evidence higher priority than the archetype.
