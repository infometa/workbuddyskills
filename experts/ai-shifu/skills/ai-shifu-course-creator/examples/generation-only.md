# Generation Only Example

> Note: Outputs in this example are illustrated in English for clarity. Actual output language follows `references/data-contracts.md#language-resolution` (e.g., Chinese invocation → Chinese output).

## Minimal Input

```json
{
  "course_material": "structured_lesson_segments",
  "interaction_policy": {
    "mode": "enabled",
    "purposes": ["pre_content_thinking"]
  },
  "teaching_constraints": {
    "max_interactions": 4,
    "require_visual_text_pair": true
  },
  "course_profile": {
    "audience_level": "beginner",
    "lesson_duration_minutes": 10
  }
}
```

Structured segments provided:

```json
[
  {
    "lesson_id": "L02",
    "core_question": "How do you verify that a fix removed the bottleneck?",
    "segment_ids": ["S21", "S22"]
  }
]
```

## Output Snapshot

```json
{
  "lesson_id": "L02",
  "lesson_title": "Verify the Fix",
  "teaching_prompt": "Open with a recent-fix scenario in which latency improves briefly but the suspected bottleneck remains.\n\nBefore explaining verification criteria, ask the learner to choose the fastest signal that would prove the fix works.\n---\n?[p95 latency trend | error-rate slope | lock-wait drop]\n---\nAfter the learner answers, place the selected signal first in a comparison slide with three columns: p95 latency trend, error-rate slope, and lock-wait drop. Explain why the selected signal is the primary checkpoint for this case; for every column, show the expected movement after a successful fix and one misleading interpretation.\n\nExplain that a useful verification signal must respond to the changed mechanism, move within the observation window, and have a clear failure threshold.\n\nHave the learner write a one-sentence verification rule containing the signal, expected movement, observation window, and stop condition. Close by restating that a fix is not complete until its expected effect is observed.",
  "used_variables": [],
  "depends_on_lessons": ["L01"]
}
```

Rendered `teaching_prompt` value:

```md
Open with a recent-fix scenario in which latency improves briefly but the suspected bottleneck remains.

Before explaining verification criteria, ask the learner to choose the fastest signal that would prove the fix works.
---
?[p95 latency trend | error-rate slope | lock-wait drop]
---
After the learner answers, place the selected signal first in a comparison slide with three columns: p95 latency trend, error-rate slope, and lock-wait drop. Explain why the selected signal is the primary checkpoint for this case; for every column, show the expected movement after a successful fix and one misleading interpretation.

Explain that a useful verification signal must respond to the changed mechanism, move within the observation window, and have a clear failure threshold.

Have the learner write a one-sentence verification rule containing the signal, expected movement, observation window, and stop condition. Close by restating that a fix is not complete until its expected effect is observed.
```

## No-Interaction Variant

When Course Design Intake explicitly resolves to no interactions, the same lesson uses a worked application instead of forcing the default interaction:

```json
{
  "interaction_policy": {
    "mode": "disabled",
    "purposes": []
  },
  "lesson_teaching_prompts": [
    {
      "lesson_id": "L02",
      "lesson_title": "Verify the Fix",
      "teaching_prompt": "Open with a failed-fix scenario in which latency briefly improves but the suspected bottleneck remains.\n\nCreate a comparison slide with three columns: p95 latency trend, error-rate slope, and lock-wait drop. For each column, show the expected movement after a successful fix and one misleading interpretation.\n\nExplain that a useful verification signal must respond to the changed mechanism, move within the observation window, and have a clear failure threshold.\n\nWalk through a worked verification decision for a lock-contention fix: use lock-wait drop as the primary checkpoint, then explain why p95 latency and error rate are secondary corroborating signals.\n\nPresent a reusable one-sentence verification rule containing the signal, expected movement, observation window, and stop condition. Close by restating that a fix is not complete until its expected effect is observed.",
      "used_variables": [],
      "depends_on_lessons": ["L01"]
    }
  ]
}
```

This variant contains no `?[]` block, learner-answer request, answer-dependent branch, or learner-answer variable. Its loop is setup → explanation → worked application → close.

## Degraded Input

Degraded-input handling for this phase (fallback lesson JSON with `fallback_mode` / `assumptions` / `upgrade_notes`): see `examples/fallback-mode.md` → Generation Fallback.

## Acceptance Notes

- In the `enabled` snapshot, the selected interaction drives current-lesson text changes.
- Core idea includes visual-plus-text explanation in final script.
- Interaction count stays within declared limits.
- The no-interaction variant satisfies the alternative teaching loop without adding interaction syntax or learner-answer variables.
