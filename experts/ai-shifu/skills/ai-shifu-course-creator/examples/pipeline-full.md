# Full Pipeline Example (Segmentation → Orchestration → Generation → Optimization)

> Note: Outputs in this example are illustrated in English for clarity. Actual output language follows `references/data-contracts.md#language-resolution` (e.g., Chinese invocation → Chinese output).

## Input Payload (example)

```json
{
  "course_material": "Module transcript: observe metric drift, classify causes, apply one fix, review impact.",
  "course_author_name": "Maya Chen",
  "interaction_policy": {
    "mode": "enabled",
    "purposes": ["pre_content_thinking"]
  },
  "generation_constraints": {
    "persona": "practical coach",
    "lesson_granularity": "short"
  },
  "course_profile": {
    "audience_level": "beginner",
    "lesson_duration_minutes": 10,
    "lesson_count_target": 3,
    "assessment_mode": "project"
  },
  "delivery_constraints": {
    "must_cover_topics": ["diagnosis", "verification"]
  },
  "target_language": "en-US"
}
```

## Segmentation Output

```json
{
  "structured_segments_json": [
    {
      "segment_id": "S01",
      "segment_type": "concept",
      "core_point": "Metric drift signals a systemic shift, not just noise.",
      "preserve_block": false,
      "source_span": {"source_id": "course_material", "start": 0, "end": 39},
      "transfer_signals": {
        "learner_hook": "Start from a metric that changed unexpectedly.",
        "visual_cue": "Show a baseline metric line followed by a sustained shift.",
        "visual_text_pair_cue": "Explain how persistence separates drift from random noise."
      }
    },
    {
      "segment_id": "S02",
      "segment_type": "concept",
      "core_point": "Classify causes before applying fixes.",
      "preserve_block": false,
      "source_span": {"source_id": "course_material", "start": 41, "end": 71},
      "transfer_signals": {
        "concept_conflict": "Jumping to a fix before classifying the cause can hide the real bottleneck.",
        "interaction_intent_cue": "Ask the learner to choose the highest-signal diagnostic check.",
        "action_cue": "Run one focused verification before applying a fix."
      }
    }
  ],
  "preserve_block_index": [],
  "lesson_cut_candidates": [
    {
      "lesson_id": "L01",
      "segment_ids": ["S01", "S02"],
      "core_question": "Which signal separates symptom from root cause?"
    }
  ]
}
```

## Orchestration + Generation Output

```json
{
  "course_index": [
    {
      "lesson_id": "L01",
      "lesson_title": "Observe and Classify",
      "core_question": "Which signal separates symptom from root cause?",
      "source_span_map": [{"source_id": "course_material", "start": 0, "end": 71}]
    }
  ],
  "global_variable_table": [
    {
      "name": "diagnosis_choice",
      "collected_in": "L01",
      "used_in": ["L01", "L02"],
      "effect_scope": "cross_lesson"
    }
  ]
}
```

```markdown
Open with a production metric that changed unexpectedly and ask the learner to identify the highest-signal diagnostic step before explaining how to classify the drift.
---
?[%{{diagnosis_choice}} check workload shape | check lock wait | check cache hit ratio]
---
The learner's diagnosis choice is {{diagnosis_choice}}. Create a slide that shows a stable baseline followed by a sustained metric shift, with the selected diagnostic branch first and visually emphasized among workload shape, lock wait, and cache hit ratio.

Explain that persistence separates drift from noise, while classification prevents the learner from applying a plausible fix to the wrong cause. Based on the learner's choice, run one focused verification before suggesting a fix, and carry the choice into the next lesson's worked example.

Have the learner write a one-sentence verification plan naming the signal, expected movement, and stop condition. Close by summarizing the sequence: observe, classify, verify, then fix.
```

## Optimization Output

```json
{
  "risk_and_issue_report": {
    "overall_risk": "low",
    "blocking_issues": [],
    "suggestions": ["add boundary framing after diagnosis interaction"]
  },
  "change_list": [
    {
      "issue_class": "explanation_clarity",
      "change": "add brief boundary note after diagnosis selection"
    }
  ]
}
```

### Course Prompt Artifact

The `course_prompt` string is the complete content below; no template instruction
is summarized or replaced by an ellipsis.

```markdown
# Role

- You are Maya Chen.
- You specialize in production observability and are a professional teacher in the field of metric drift diagnosis.

# Task

- The current course is *Metric Drift Diagnosis*. Your goal is to help the user master an observe, classify, verify, and fix workflow for production metric drift.
- Teach one-on-one, address the learner only as "you", and do not use group-addressing terms such as "everyone", "class", or "students".
- Do not introduce yourself.
- Do not greet the user.
- Do not proactively guide the user to the next step at the end.

# Teaching Techniques

- Treat the current user message as authoritative for the lesson's teaching method, explanation path, content sequence, pacing, examples, practice, interactions, feedback, and close.
- Follow those instructions faithfully. Do not replace, reorder, omit, or supplement them with a generic course-level teaching framework.
- Limit the Course Prompt's teaching contribution to the presentation layer: adjust tone, wording, formatting, and slide presentation without changing the user message's pedagogical intent or lesson flow.

# Writing Style

- Use a conversational, natural, and engaging tone, like a clear-minded person explaining something face to face.
- Keep the language restrained, clear, and warm.

# Format

- Output in Markdown format.
- Do not output headings of any level, such as #, ##, or ###.
- Use bold formatting for key steps, cognitive turning points, core conclusions, and common misconceptions.
- Only bold truly important information. Do not bold an entire paragraph.
- Add a space between Chinese and English, and between Chinese and numbers.

# Slides

- Only create a slide, PPT, visual page, or classroom projection page when the current user message explicitly requests one. Do not proactively create visuals.
- Follow the current user message's delivery mode and slide-text relationship. Do not add AI narration, a full text explanation, or presenter notes unless that user message requests them.
- Create a presentation-style slide rather than a standalone illustration.
- In-slide option labels must not be interactive.
- Keep in-slide text concise and prompt-like. Make every element fully visible, avoid overlap, and use a simple hierarchy.
- When the current user message requests text alongside a slide, treat the slide as a structural prompt and follow it with a complete text explanation that assumes the learner has not seen the slide.
```

## Acceptance Notes

- All four phases executed end-to-end.
- One core question per lesson, every learner-answer variable has a corresponding variable-backed interaction and metadata entry.
- The Course Prompt preserves all six sections and every non-placeholder template instruction.
- Optimization pass found no blockers, only enhancement suggestions.
