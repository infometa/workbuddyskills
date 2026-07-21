# Fallback Mode Example

> Note: Outputs in this example are illustrated in English for clarity. Actual output language follows `references/data-contracts.md#language-resolution` (e.g., Chinese invocation → Chinese output).

Demonstrates degraded-input handling across the four phases. This file is the single home for fallback scenarios; the phase-only examples cover standard mode and point here.

## Segmentation Fallback: Conflicting Sources

```json
{
  "course_material": "doc-a: retries should stop after 3 attempts...\ndoc-b: retries can continue until queue drains...\ndoc-c: [image:failure-matrix.png]",
  "course_profile": {
    "audience_level": "intermediate",
    "lesson_duration_minutes": 15
  },
  "delivery_constraints": {
    "must_cover_topics": ["stop condition design"],
    "non_negotiable_fragments": ["[image:failure-matrix.png]"]
  }
}
```

Output includes uncertainty markers and rerun hints; preserved blocks survive even under fallback:

```json
{
  "structured_segments_json": [
    {
      "segment_id": "S10",
      "segment_type": "concept",
      "core_point": "Retry stop conditions differ across sources.",
      "preserve_block": false,
      "source_span": {"source_id": "course_material", "start": 0, "end": 96},
      "transfer_signals": {
        "concept_conflict": "The sources disagree on whether retries stop at a fixed count or when the queue drains.",
        "boundary_cue": "Do not choose a stop condition until the authoritative policy is confirmed."
      },
      "uncertainty": "high"
    },
    {
      "segment_id": "S11",
      "segment_type": "image",
      "core_point": "Failure matrix image preserved",
      "preserve_block": true,
      "source_span": {"source_id": "course_material", "start": 104, "end": 130},
      "transfer_signals": {
        "visual_cue": "Preserve the failure matrix as the visual comparison surface.",
        "visual_text_pair_cue": "Explain which cells support each proposed retry boundary."
      },
      "uncertainty": "low"
    }
  ],
  "rerun_hints": [
    "Provide authoritative policy for max retry attempts.",
    "Confirm whether queue-drain mode is allowed in this course."
  ]
}
```

## Orchestration Fallback: Incomplete Input

```json
{
  "course_material": "doc-1: classify by latency tiers\n\ndoc-2: classify by resource contention\n\ndoc-3: missing section ordering",
  "generation_constraints": {
    "lesson_granularity": "medium"
  }
}
```

Pipeline produces partial but runnable output:

```json
{
  "course_index": [
    {
      "lesson_id": "L03",
      "lesson_title": "Choose a Classification Axis",
      "core_question": "When should you prefer latency tiers over contention classes?",
      "source_span_map": [
        {"source_id": "course_material", "start": 0, "end": 32},
        {"source_id": "course_material", "start": 34, "end": 72}
      ],
      "uncertainty": "medium"
    }
  ],
  "rerun_plan": {
    "lessons_to_rerun": ["L03"],
    "reason": "conflicting taxonomy across doc-1 and doc-2"
  }
}
```

```md
Ask the learner to select a first-pass classification rule before comparing the two taxonomies.
---
?[latency first | contention first]
---
Current evidence is partial; confirm one canonical taxonomy before final pass.
```

## Generation Fallback: Minimal Segments

```json
{
  "course_material": "structured_lesson_segments",
  "interaction_policy": {
    "mode": "enabled",
    "purposes": ["pre_content_thinking"]
  },
  "teaching_constraints": {
    "max_interactions": 2,
    "must_use_viewpoint_check": true,
    "allow_cross_lesson_dependency": false
  },
  "delivery_constraints": {
    "platform_limits": ["markdown_only"]
  }
}
```

```json
{
  "lesson_id": "L07",
  "lesson_title": "Pick a Rollback Trigger",
  "teaching_prompt": "Pick a rollback trigger that minimizes blast radius.\n---\n?[latency spike threshold | error budget burn threshold]\n---\nAfter the learner answers, define one immediate rollback condition and one follow-up diagnostic for the selected trigger.",
  "used_variables": [],
  "depends_on_lessons": [],
  "fallback_mode": true,
  "assumptions": [
    "No cross-lesson variable carryover is used.",
    "One viewpoint check is enough for this pass."
  ],
  "upgrade_notes": [
    "Add richer evidence chain after full source context is available."
  ]
}
```

Rendered `teaching_prompt` value:

```md
Pick a rollback trigger that minimizes blast radius.
---
?[latency spike threshold | error budget burn threshold]
---
After the learner answers, define one immediate rollback condition and one follow-up diagnostic for the selected trigger.
```

## Optimization Fallback: No Source Material

```json
{
  "existing_teaching_prompt": "## Goal\nPick a fix.\n---\n?[%{{fix_choice}} option A | option B]\n---\n?[%{{choose_fix}} option A | option B]\n---\nUse {{fix_context}} now.",
  "course_material": "",
  "optimization_constraints": {
    "fallback_mode": true,
    "minimize_scope": true
  },
  "delivery_constraints": {
    "platform_limits": ["markdown_only"]
  }
}
```

```json
{
  "risk_and_issue_report": {
    "overall_risk": "high",
    "blocking_issues": [
      "variable_or_syntax_risk",
      "semantic_duplicate_interactions"
    ],
    "coverage_status": "unknown_without_source"
  },
  "change_list": [
    {
      "issue_class": "variable_or_syntax_risk",
      "change": "remove the learner-answer reference with no collection contract and keep one canonical no-variable interaction"
    }
  ],
  "follow_up": [
    "Provide source material for full coverage and meaning audit."
  ]
}
```

Corrected script (smallest safe edit):

```md
Pick one safe first fix.
---
?[option A | option B]
---
After the learner answers, apply one verification step before rollout.
```

## Acceptance Notes

- Each phase degrades gracefully instead of failing hard.
- Uncertainty is marked explicitly, never silently merged.
- Rerun hints guide the user toward resolution.
- Output schemas remain compatible across standard and fallback modes.
- The `course_prompt` artifact is omitted when `course_material` is empty (per `../references/optimization-workflow.md#validation`).
