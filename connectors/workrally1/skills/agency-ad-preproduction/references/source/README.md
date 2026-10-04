# Advertising Agency Skills for Codex

A role-based advertising agency skill pack for Codex, built for real creative and strategy workflows.

This repository turns Codex into a structured agency collaboration system with clearly defined roles, responsibilities, output rules, and approval gates. Instead of using AI as a generic content generator, this skill pack lets you work with Codex more like a real agency team.

New users can start with [USAGE.md](USAGE.md) for a step-by-step guide written for people with no prior skill setup or agency workflow experience.

It includes six core roles:

- `account-executive`
- `strategy-director`
- `creative-director`
- `copywriter`
- `designer`
- `boss`

Together, they support end-to-end brand and campaign development across:

- brand strategy
- integrated marketing campaigns
- launch campaigns
- creative direction
- copywriting
- visual direction
- proposal development

## What makes this different

These skills are designed around how agency teams actually work.

- Each role has clear boundaries, methods, and expected outputs.
- Every stage requires user confirmation before moving to the next step.
- If required materials are missing, the skill must explicitly ask for them instead of guessing.
- Work flows in a structured sequence, from brief intake to strategy, creative alignment, copy, design, and final review.

## Workflow logic

The system is built around a real collaboration order:

`Account Executive -> Problem & Objective Alignment -> Research & Material Collection -> Strategy Director -> Creative Director -> Direction Confirmation -> Copywriter / Designer -> Review`

This makes the pack especially useful for people working on:

- brand proposals
- campaign planning
- creative ideation
- content systems
- social activation
- visual development
- internal agency workflows

## Who this is for

This repository is made for:

- advertising agencies
- strategists
- creative directors
- copywriters
- designers
- independent brand consultants
- anyone who wants Codex to behave more like a disciplined agency team

## Philosophy

The goal is not to generate more content.

The goal is to create better creative work through structure, judgment, role clarity, and collaboration.

## Installation

If you want Codex to discover these skills globally, copy the skill folders into your Codex skills directory:

```bash
cp -R skills/account-executive ~/.codex/skills/
cp -R skills/strategy-director ~/.codex/skills/
cp -R skills/creative-director ~/.codex/skills/
cp -R skills/copywriter ~/.codex/skills/
cp -R skills/designer ~/.codex/skills/
cp -R skills/boss ~/.codex/skills/
```

If the folders already exist, update them with:

```bash
cp -R skills/account-executive/. ~/.codex/skills/account-executive/
cp -R skills/strategy-director/. ~/.codex/skills/strategy-director/
cp -R skills/creative-director/. ~/.codex/skills/creative-director/
cp -R skills/copywriter/. ~/.codex/skills/copywriter/
cp -R skills/designer/. ~/.codex/skills/designer/
cp -R skills/boss/. ~/.codex/skills/boss/
```

## How to use

You can call a specific role directly when you already know what kind of output you need.

Examples:

- Use `account-executive` when you need to turn a rough client ask into a structured brief.
- Use `strategy-director` when you need positioning, diagnosis, audience insight, or a creative brief.
- Use `creative-director` when you need big idea selection, direction review, or proposal logic.
- Use `copywriter` when you need campaign lines, scripts, social copy, or conversion writing.
- Use `designer` when you need visual directions, key visual prompts, moodboards, or system thinking.
- Use `boss` when you want Codex to manage the whole agency workflow from brief to execution.

## Recommended prompts

Here are a few practical starting prompts:

### Account Executive

```text
Use $account-executive to turn this client message into a clean internal brief, a missing-information list, and a next-step action plan.
```

### Strategy Director

```text
Use $strategy-director to diagnose the real business problem behind this brief and produce a positioning direction plus a creative brief.
```

### Creative Director

```text
Use $creative-director to evaluate these campaign routes, identify the strongest big idea, and explain which one deserves to move forward.
```

### Copywriter

```text
Use $copywriter to write three campaign directions, one key visual line, and five social media hooks from this confirmed strategy and creative direction.
```

### Designer

```text
Use $designer to translate this confirmed campaign direction into a visual system, key visual description, and AI image prompts.
```

### BOSS

```text
Use $boss to run this brief through the full agency workflow, stopping for my confirmation after each role output and explicitly asking me for any missing materials.
```

## Approval model

This skill pack is intentionally built with review gates.

- Every role output must be shown to the user before moving to the next stage.
- Missing materials must be explicitly requested from the user.
- Later roles should not silently rewrite earlier strategic decisions.
- The system should pause when inputs are unclear, incomplete, or unapproved.

This is deliberate. It keeps the workflow usable for real client work instead of turning everything into uncontrolled auto-generation.

## Skill structure

```text
skills/
├── account-executive/
├── strategy-director/
├── creative-director/
├── copywriter/
├── designer/
└── boss/
```

Each skill contains:

- `SKILL.md` for role behavior, workflow, boundaries, and output rules
- `agents/openai.yaml` for display metadata and invocation defaults
- `references/` for templates, frameworks, rubrics, and supporting structures

## Example workflow

Here is a typical way to use the system:

1. Start with `boss` or `account-executive`.
2. Turn the raw client ask into a brief.
3. Confirm the problem and objectives.
4. Ask for missing research, audience, product, or brand materials.
5. Move into `strategy-director` once inputs are complete enough.
6. Confirm strategy before generating creative routes.
7. Move into `creative-director` for idea selection and direction setting.
8. Confirm the chosen direction.
9. Move into `copywriter` and `designer` for execution outputs.
10. Review everything before final packaging or delivery.

## Output style

The skills are built to support outputs such as:

- internal briefs
- strategy documents
- creative briefs
- campaign platforms
- social activation ideas
- key visual directions
- copy systems
- proposal structures
- AI image prompt kits

## Notes

- These skills are designed for practitioners, not for direct client-facing automation.
- They are especially useful when you want Codex to behave like a disciplined team, not a single all-purpose assistant.
- They work best when you provide real briefs, real constraints, and real approval feedback at each stage.

## License

Add your preferred license here.
