# agent +create-automation (Create Automation)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Automations / write**

```text
Transition status: transitional
Owning module: te-claude automation
Current transport: POST /api/sandbox/agent/automations
Gateway target: TBD (no equivalent Gateway capability is currently registered)
Review after: 2026-10-07
Exit condition: Migrate when the Gateway exposes equivalent workspace-scoped automation creation.
```

## Use Cases
- Create an Agent automation task that runs on a schedule (hourly / daily / weekly / monthly or cron).
- Returns the newly created automation object including its `id` and initial `status`.
- Automations are **enabled by default**; pass `--enabled false` only when the user explicitly asks to create the task without enabling it.
- Automations create a new conversation for every run by default. Pass `--reuse-conversation true` only when the user explicitly wants future runs to continue in one conversation.

## Mandatory Rules (MUST)
- `--name` and `--message` are required.
- A schedule is required: provide either `--cron` or a `--schedule-kind` (with its time/day fields). `--cron` and `--schedule-kind` are mutually exclusive.
- `--agent-id` and `--agent-name` are mutually exclusive. Obtain a real Agent ID via `+list-agents` — do not guess.
- In a chat runtime, omitted `--conversation-id`, `--agent-id`, and `--model` values fall back to `TE_AGENT_CONVERSATION_ID`, `TE_AGENT_CURRENT_AGENT_ID`, and `TE_AGENT_CURRENT_MODEL_ID`. Explicit flags always take precedence; `--agent-name` intentionally suppresses the current Agent ID fallback.
- Workspace selection is independent of Agent selection: `--agent-space-id` explicitly selects the workspace. If omitted, the server inherits the accessible conversation's workspace when available, otherwise the personal default workspace. The CLI intentionally omits `agentSpaceId` in this case to preserve inheritance and compatibility with earlier servers.
- Workspace-aware servers return `automation.agentSpaceId`. Pass that ID to subsequent `+list-automations` and `+update-automation` calls; those commands otherwise use the personal default workspace, even when invoked from a conversation.
- On servers without workspace support, omit `--agent-space-id` and keep the original creation flow. If the response lacks `agentSpaceId`, omit the flag in later calls rather than inventing an ID. Older servers may ignore the new parameter; it does not add workspace isolation to them.
- This command creates Agent automations only. It does not create Agent Team scheduled tasks.
- JSON flags must be valid JSON strings, usually wrapped in single quotes in shell.
- This is an ordinary `write` operation and does not require CLI confirmation.
- Do not surface raw automation IDs, raw JSON, or concrete detail paths in user-facing replies.

## Schedule Kinds
| `--schedule-kind` | Required fields | Notes |
|---|---|---|
| `hourly` | `--minute` (optional, 0–59) | Runs every hour at the given minute |
| `daily` | `--time HH:mm` | Runs once a day at the given time |
| `weekly` | `--time HH:mm`, `--weekday 0-6` | `0` = Sunday |
| `monthly` | `--time HH:mm`, `--day-of-month 1-28` | Day 1–28 only |

## Command
```bash
# Enabled daily automation (default)
ae-cli agent +create-automation \
  --name "Daily AI Brief" \
  --schedule-kind daily \
  --time 09:00 \
  --message "Summarize yesterday's AI news"

# Create but keep paused when the user explicitly asks not to enable it
ae-cli agent +create-automation \
  --name "Daily AI Brief" \
  --schedule-kind daily \
  --time 09:00 \
  --message "Summarize yesterday's AI news" \
  --enabled false

# Keep future runs in one visible conversation
ae-cli agent +create-automation \
  --name "Daily AI Brief" \
  --schedule-kind daily \
  --time 09:00 \
  --message "Summarize yesterday's AI news" \
  --reuse-conversation true

# Weekly schedule on Sunday
ae-cli agent +create-automation \
  --name "Weekly Report" \
  --schedule-kind weekly \
  --time 10:00 \
  --weekday 0 \
  --message "Generate the weekly report"

# Cron expression
ae-cli agent +create-automation \
  --name "Cron Task" \
  --cron "0 9 * * 1-5" \
  --message "Weekday morning brief"

# Dry-run to inspect the request before executing
ae-cli agent +create-automation --dry-run --name "Test" --message "x" --schedule-kind daily --time 09:00

# Select a workspace explicitly
ae-cli agent +create-automation --name "Daily Report" --message "Prepare the report" \
  --agent-id <agent-id> --agent-space-id <workspace-id> --schedule-kind daily --time 09:00
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--name` | Yes | Automation task name |
| `--message` | Yes | Instruction sent to the Agent |
| `--cron` | No* | Cron expression (mutually exclusive with `--schedule-kind`) |
| `--schedule-kind` | No* | `hourly` \| `daily` \| `weekly` \| `monthly` |
| `--time` | No | Time in `HH:mm` for daily/weekly/monthly |
| `--minute` | No | Minute 0–59 for hourly schedules |
| `--weekday` | No | Weekday 0–6 for weekly schedules; `0` is Sunday |
| `--day-of-month` | No | Day 1–28 for monthly schedules |
| `--agent-id` | No | Agent ID; defaults to current conversation Agent |
| `--agent-name` | No | Agent name; use only after `+list-agents` discovery |
| `--model` | No | Model record ID; defaults to current selected model |
| `--enabled` | No | `true` (default) \| `false` |
| `--reuse-conversation` | No | `true` to continue in one conversation; `false` (default) to create one per run |
| `--conversation-id` | No | Conversation ID fallback for resolving the Agent and workspace |
| `--agent-space-id` | No | Explicit workspace ID; omit to inherit the conversation's workspace, otherwise use the personal default workspace |

\* One of `--cron` or `--schedule-kind` is required.

## Decision Rules
- If the user provides a natural-language schedule ("every day at 9am"), translate it to `--schedule-kind daily --time 09:00`.
- If the user wants a cron-only schedule not covered by the kinds, use `--cron`.
- If no Agent is specified, the automation targets the current conversation's Agent; verify with `+list-agents` when in doubt.
- Set `--reuse-conversation true` only when the user explicitly requests continuity across runs. The platform may rotate the underlying provider session while retaining the visible conversation history.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `必须提供 --cron 或 --schedule-kind`: provide one of the schedule flags.
- `--time 格式必须是 HH:mm`: use 24-hour `HH:mm` (e.g. `09:00`).
- `--agent-id 与 --agent-name 只能二选一`: pick one and remove the other.
- After success, capture the returned `automation.id` and, when present, `automation.agentSpaceId` for subsequent list/update calls. Omit the workspace flag when the ID is `null` or absent.

## Recommended Chaining
- `+list-agents` → `+create-automation` → `+list-automations` (verify) → `+update-automation` (edit)
