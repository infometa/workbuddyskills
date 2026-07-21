# Resume Progress Card

Use this when the user says continue, returns to a prior manuscript, or has just
received a first-value result that should be easy to resume later.

## User-Visible Rules

- Start by stating that progress has been preserved or summarized.
- Show only two or three next actions.
- Do not ask again for context that is already present in the current progress
  card, chapter map, or material summary.
- If no saved runtime card exists, create a visible response-level progress
  card instead of guessing hidden state.

## Recommended Fields

```json
{
  "cardType": "resume_progress_card",
  "progressId": "example-progress-whitepaper-001",
  "bookTitle": "AI+HR Industry Whitepaper",
  "currentStage": "first_value_completed",
  "currentBranch": "continue_chapter",
  "wordCount": 12800,
  "chapterCount": 8,
  "completedCount": 3,
  "chapterStatus": [
    {
      "chapterId": "chapter_1",
      "status": "drafted"
    },
    {
      "chapterId": "chapter_2",
      "status": "next_best"
    }
  ],
  "lastCompletedOutput": "chapter_route_map_and_sample_opening",
  "nextBestOptionScores": [
    {
      "branch": "continue_chapter",
      "score": 0.92,
      "reason": "The route map is ready and the next chapter has enough material."
    }
  ],
  "reopenIntakeAllowed": false,
  "stopCondition": "continued_use_completed",
  "resumeHint": "Next time, say continue plus the target chapter or finishing step.",
  "nextOptions": [
    "Continue the next chapter",
    "Run de-AI polish and quality review",
    "Run format and export precheck"
  ]
}
```

## Minimum Action

1. Summarize current stage.
2. Name what is already done.
3. Offer two or three next branches.
4. Provide a reusable resume prompt.
5. Keep service-readable progress fields available for host metadata or debug
   output, but do not expose raw orchestration JSON in ordinary prose.
