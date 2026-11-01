# Human interview

An interview project: the user writes questions, sends a link, and real people are interviewed by an AI interviewer on their own time. Use it when the user wants answers from real people, as an interview or a questionnaire.

Tools: `atypica_interview_*`. Every field is described on the tool itself.

## The flow

```
atypica_interview_create_project({ brief, questions })  → projectId
atypica_interview_generate_share_link({ projectId })    → shareUrl: give it to the user to distribute
later: atypica_interview_get_progress({ projectId })    → how many have answered
enough answers: atypica_interview_generate_stats({ projectId }), then atypica_interview_get_stats every 15 s
one person: atypica_interview_list_sessions → atypica_interview_get_session({ sessionId })
```

- People answer over hours or days. After sending the link there is nothing to poll; check progress when the user asks.
- Statistics are not automatic. `generate_stats` uses the account's credits and takes 30–90 s. `get_stats` has three states: `isGenerating: true` (poll again), `questionStats` filled (ready), both empty (never generated, call `generate_stats`).
- `atypica_interview_update_questions` replaces all questions and does not change interviews already started.

## Writing questions

| `questionType`    | `options` | Notes                                             |
| ----------------- | --------- | ------------------------------------------------- |
| `open` (default)  | none      | Text answer; the AI interviewer probes for detail |
| `single-choice`   | 2–50      | One pick                                          |
| `multiple-choice` | 2–50      | Several picks                                     |

`hint` tells the interviewer what to probe for. Images on a question: upload with `atypica_get_upload_credentials` (see SKILL.md), then `images` on the question, up to 4, 10 MB each.

## Delivering

- Progress: `completed` vs `inProgress`, split into `humanSessions` (real people) and `personaSessions` (AI-simulated participants, if the user ran any).
- Aggregated: `get_stats` gives, per question, categories with counts and ratios plus a summary.
- Individual: `list_sessions` (check `hasStructuredAnswers`), then `get_session` for answers, a summary and the transcript.
