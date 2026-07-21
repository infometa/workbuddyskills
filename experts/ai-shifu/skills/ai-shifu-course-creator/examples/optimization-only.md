# Optimization Only Example

> Note: Outputs in this example are illustrated in English for clarity. Actual output language follows `references/data-contracts.md#language-resolution` (e.g., Chinese invocation → Chinese output).

## Minimal Input

```json
{
  "existing_teaching_prompt": "## Objective\nUnderstand retry policy.\n---\n?[%{{answer}} yes | no]\n---\nGreat job.",
  "course_material": "Learner must differentiate transient vs permanent failure and choose a matching retry stop rule.",
  "course_author_name": "Priya Shah",
  "target_language": "en-US",
  "interaction_policy": {
    "mode": "enabled",
    "purposes": ["pre_content_thinking"]
  },
  "optimization_constraints": {
    "max_interactions": 4,
    "require_branching_feedback": true
  },
  "course_profile": {
    "audience_level": "beginner"
  }
}
```

## Output Snapshot

```json
{
  "risk_and_issue_report": {
    "overall_risk": "medium",
    "blocking_issues": ["interaction_no_branching"],
    "suggestions": ["add explicit stop-condition task"]
  },
  "change_list": [
    {
      "issue_class": "interaction_no_branching",
      "change": "remove the throwaway variable, branch feedback by learner option, and add next-step action"
    }
  ]
}
```

```md
Differentiate transient and permanent failures before choosing retry policy.
---
?[transient failure | permanent failure]
---
If the learner chooses transient failure, apply bounded retries with backoff.
If the learner chooses permanent failure, stop retries and open a corrective task.
```

### Course Prompt Artifact

The `course_prompt` string is the complete content below.

```markdown
# Role

- You are Priya Shah.
- You specialize in reliability engineering and are a professional teacher in the field of retry policy design.

# Task

- The current course is *Safe Retry Policy*. Your goal is to help the user master distinguishing transient from permanent failures and choosing a matching retry stop rule.
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

## Degraded Input

Degraded-input handling for this phase (missing source material, high-risk report, minimal safe edits): see `examples/fallback-mode.md` → Optimization Fallback.

## Acceptance Notes

- Syntax stays runnable after edits.
- Coverage and meaning are closer to source material.
- Runtime safety fixes are applied first.
- Edits stay minimal and avoid broad rewrites.
- The Course Prompt preserves the complete fillable template with course-specific placeholders resolved.
