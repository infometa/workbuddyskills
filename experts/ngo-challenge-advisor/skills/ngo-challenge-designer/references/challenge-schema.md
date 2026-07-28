# Challenge schema

This is the submission contract. Use it only with the bundled public submission script; do not assume any database mapping or admin API.

Schema version: **1.0** — every exported challenge JSON must carry `schema_version: "1.0"`. Backends must reject unknown versions instead of silently misreading data.

```yaml
schema_version: "1.0"          # contract version, required on export
id: string | null              # assigned by the backend on import; null inside the Expert

publishable:
  title: string
  organization_name: string
  organization_intro: string | null
  primary_track: string
  track_tags: string[]
  pain_point: string
  current_situation: string
  current_method: string
  desired_outcome: string
  success_criteria: string[]
  materials: string[]
  boundaries: string[]
  baseline: string | null
  trial_scenario: string | null
  team_context: string | null

internal_metadata:
  solution_type_hint: skill | expert | either
  fit_status: pass | adapt | fail
  fit_reasons: string[]
  scope_warnings: string[]
  extraction_confidence: object
  confirmed_snapshot_id: string | null  # non-empty string required for direct submission; null only before confirmation

conversation_state:
  status: start | collecting_track | collecting_organization | collecting_pain | collecting_current_process | collecting_outcome | collecting_constraints | enriching | generating_draft | reviewing | awaiting_confirmation | ready_to_sync | syncing | synced | adapting_scope | editing | paused | sync_failed | archived
  answered_topics: string[]
  missing_topics: string[]
  contradictions: string[]
  current_question: string
  revision_history: object[]
  explicit_confirmation: boolean
  sync_status: string
```

## State rules

- `organization_name` is required for publication; use exactly `未公開機構` when the NGO opts out of disclosure.
- `archived` is a soft delete: hidden from public and default admin views, restorable; never hard-delete.
- Do not enter `ready_to_sync` without explicit confirmation.
- Return to `editing` after any preview change.
- Require confirmation again after editing.
- Create an immutable confirmed snapshot before synchronization.
- Preserve the confirmed snapshot after `sync_failed` so retry does not restart the interview.
- Keep raw conversation data outside `publishable`.
