# agent +update-automation (Update Automation)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Automations / write**

```text
Transition status: transitional
Owning module: te-claude automation
Current transport: PATCH /api/sandbox/agent/automations/:id
Gateway target: TBD (no equivalent Gateway capability is currently registered)
Review after: 2026-10-07
Exit condition: Migrate when the Gateway exposes equivalent workspace-scoped automation updates.
```

## Use Cases
- Update an existing Agent automation task's name, instruction, schedule, enabled state, or conversation mode.
- Used to pause (`--enabled false`) or resume (`--enabled true`) an automation, or to change its schedule/message.
- Obtain the automation `id` via `+list-automations` — never guess.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real ID via `+list-automations` — do not guess.
- Pass the same `--agent-space-id` used to discover the task, or the `automation.agentSpaceId` returned by creation. Omitting it targets the personal default workspace, including legacy tasks with no workspace ID.
- The workspace ID is sent as a query parameter to select the task's existing workspace. It is not an update field and cannot move an automation between workspaces; providing it alone is not a valid update.
- On servers without workspace support, omit `--agent-space-id` and update by the original task ID. Missing workspace fields in older responses do not prevent updates; do not invent an ID or rely on older servers to enforce the new workspace query parameter.
- Agent Team scheduled task IDs are not automation IDs and cannot be used with this command.
- At least one update field must be provided (`--name`, `--message`, `--enabled`, `--reuse-conversation`, `--cron`, or a `--schedule-kind` with its time/day fields).
- `--cron` and `--schedule-kind` are mutually exclusive.
- This is an ordinary `write` operation and does not require CLI confirmation.
- Do not surface raw automation IDs, raw JSON, or concrete detail paths in user-facing replies.

## Schedule Kinds (when updating schedule)
| `--schedule-kind` | Required fields | Notes |
|---|---|---|
| `hourly` | `--minute` (optional, 0–59) | Runs every hour at the given minute |
| `daily` | `--time HH:mm` | Runs once a day at the given time |
| `weekly` | `--time HH:mm`, `--weekday 0-6` | `0` = Sunday |
| `monthly` | `--time HH:mm`, `--day-of-month 1-28` | Day 1–28 only |

## Command
```bash
# Pause an automation
ae-cli agent +update-automation --id <automation-id> --enabled false

# Pause an automation in a specific workspace
ae-cli agent +update-automation --id <automation-id> --agent-space-id <workspace-id> --enabled false

# Resume an automation
ae-cli agent +update-automation --id <automation-id> --enabled true

# Reuse the most recent valid conversation on future runs
ae-cli agent +update-automation --id <automation-id> --reuse-conversation true

# Return to creating a new conversation for every run
ae-cli agent +update-automation --id <automation-id> --reuse-conversation false

# Rename and change the instruction
ae-cli agent +update-automation \
  --id <automation-id> \
  --name "Daily AI Brief v2" \
  --message "Summarize yesterday's AI news and trends"

# Change the schedule to weekly on Sunday
ae-cli agent +update-automation \
  --id <automation-id> \
  --schedule-kind weekly \
  --time 10:00 \
  --weekday 0

# Switch to a cron expression
ae-cli agent +update-automation --id <automation-id> --cron "0 9 * * 1-5"

# Dry-run to inspect the request before executing
ae-cli agent +update-automation --dry-run --id <automation-id> --enabled false
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Automation task ID from `+list-automations` |
| `--agent-space-id` | No | Existing workspace ID; omitted means the personal default workspace. Does not move the task |
| `--name` | No | New automation task name |
| `--message` | No | New instruction sent to the Agent |
| `--enabled` | No | `true` to enable, `false` to pause |
| `--reuse-conversation` | No | `true` to reuse one conversation, `false` to create one per run; omit to keep unchanged |
| `--cron` | No | Cron expression (mutually exclusive with `--schedule-kind`) |
| `--schedule-kind` | No | `hourly` \| `daily` \| `weekly` \| `monthly` |
| `--time` | No | Time in `HH:mm` for daily/weekly/monthly |
| `--minute` | No | Minute 0–59 for hourly schedules |
| `--weekday` | No | Weekday 0–6 for weekly schedules; `0` is Sunday |
| `--day-of-month` | No | Day 1–28 for monthly schedules |

## Decision Rules
- If the user wants to pause/resume, use `--enabled false` / `--enabled true` (no other fields needed).
- If the user wants future runs to share one conversation, use `--reuse-conversation true`; use `false` to restore one conversation per run.
- If the user wants to change the schedule, provide `--schedule-kind` with its required time/day fields, or `--cron`.
- At least one update field is required; a bare `--id` is rejected.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `AUTOMATION_NOT_FOUND`: verify the task ID and workspace ID together. Do not retry across other workspaces automatically.
- `至少提供一个更新字段`: add at least one of `--name` / `--message` / `--enabled` / `--reuse-conversation` / `--cron` / `--schedule-kind`.
- `必须提供 --cron 或 --schedule-kind`: if schedule detail flags (`--time` / `--minute` / `--weekday` / `--day-of-month`) are present, a `--schedule-kind` (or `--cron`) must accompany them.
- `--time 格式必须是 HH:mm`: use 24-hour `HH:mm` (e.g. `09:00`).

## Recommended Chaining
- `+list-automations` → `+update-automation`
