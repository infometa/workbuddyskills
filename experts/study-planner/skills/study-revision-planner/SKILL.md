---
name: study-revision-planner
description: Convert a syllabus, exam scope, or course notes into a revision calendar
  with spaced review, mock tests, and weak-point loops.
version: 1.1.0
metadata:
  openclaw:
    requires:
      bins:
      - python3
    emoji: 🧰
---

# Study Revision Planner

## Purpose

Convert a syllabus, exam scope, or course notes into a revision calendar with spaced review, mock tests, and weak-point loops.

## Trigger phrases

- 复习计划
- exam revision planner
- 课程大纲变计划
- spaced repetition schedule
- 安排模拟测试

## Ask for these inputs

- syllabus or topics
- exam date
- weekly availability
- difficulty by topic
- preferred study block length

## Workflow

1. Split the scope into study units and estimate effort.
2. Generate a calendar with learn, review, and test phases.
3. Insert spaced review loops and buffer days.
4. Highlight overload weeks and propose tradeoffs.
5. Return a printable plan and a concise today-next checklist.

## Output contract

- revision calendar
- topic effort table
- mock test schedule
- today-next checklist

## Files in this skill

- Script: `{baseDir}/scripts/revision_schedule.py`
- Resource: `{baseDir}/resources/study_plan_template.csv`

## Operating rules

- Be concrete and action-oriented.
- Prefer preview / draft / simulation mode before destructive changes.
- If information is missing, ask only for the minimum needed to proceed.
- Never fabricate metrics, legal certainty, receipts, credentials, or evidence.
- Keep assumptions explicit.

## Suggested prompts

- 复习计划
- exam revision planner
- 课程大纲变计划

## Use of script and resources

Use the bundled script when it helps the user produce a structured file, manifest, CSV, or first-pass draft.
Use the resource file as the default schema, checklist, or preset when the user does not provide one.

## Boundaries

- This skill supports planning, structuring, and first-pass artifacts.
- It should not claim that files were modified, messages were sent, or legal/financial decisions were finalized unless the user actually performed those actions.


## Compatibility notes

- Directory-based AgentSkills/OpenClaw skill.
- Runtime dependency declared through `metadata.openclaw.requires`.
- Helper script is local and auditable: `scripts/revision_schedule.py`.
- Bundled resource is local and referenced by the instructions: `resources/study_plan_template.csv`.
