# Segmentation Only Example

> Note: Outputs in this example are illustrated in English for clarity. Actual output language follows `references/data-contracts.md#language-resolution` (e.g., Chinese invocation → Chinese output).

## Minimal Input

```json
{
  "course_material": "Today we explain retry strategy... um... first rule is idempotency.\n```python\nretry(order_id)\n```\nThen we map transient vs permanent failure...",
  "chapter_hint": {
    "target_lessons": 2,
    "granularity": "medium"
  },
  "course_profile": {
    "audience_level": "beginner",
    "lesson_duration_minutes": 12,
    "assessment_mode": "project"
  },
  "delivery_constraints": {
    "must_cover_topics": ["idempotency", "failure taxonomy"]
  },
  "target_language": "en-US"
}
```

## Output Snapshot

```json
{
  "structured_segments_json": [
    {
      "segment_id": "S01",
      "segment_type": "concept",
      "core_point": "Idempotency is the precondition for safe retries.",
      "preserve_block": false,
      "source_span": {"source_id": "course_material", "start": 0, "end": 67},
      "transfer_signals": {
        "concept_conflict": "Retries are unsafe unless repeated execution is idempotent.",
        "interaction_intent_cue": "Ask the learner to identify the failure caused by retrying a non-idempotent operation."
      }
    },
    {
      "segment_id": "S02",
      "segment_type": "code",
      "core_point": "Retry call example",
      "preserve_block": true,
      "source_span": {"source_id": "course_material", "start": 68, "end": 97},
      "transfer_signals": {
        "evidence_type": "Executable retry example that must remain unchanged.",
        "action_cue": "Use the preserved call to test whether repeated execution is safe."
      }
    }
  ],
  "preserve_block_index": [
    {"block_id": "B01", "type": "code", "segment_id": "S02"}
  ],
  "lesson_cut_candidates": [
    {
      "lesson_id": "L01",
      "segment_ids": ["S01", "S02"],
      "core_question": "Why is idempotency required before retry logic?"
    }
  ]
}
```

## Degraded Input

Degraded-input handling for this phase (conflicting sources, uncertainty markers, rerun hints): see `examples/fallback-mode.md` → Segmentation Fallback.

## Acceptance Notes

- Meaning is preserved while filler phrases are removed.
- Code block text and fence language stay unchanged.
- Output schema remains compatible for downstream phases.
