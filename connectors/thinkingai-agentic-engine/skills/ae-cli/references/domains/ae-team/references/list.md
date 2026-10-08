# team +list (List Teams)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Team discovery**

## Use Cases
- List all AI Agent teams visible to the current user.
- Returns an array of team summaries; key fields include `id`, `name`, `description`, `scope`, `enabled`, `config`.
- Use this as the first step before any run or update operation to confirm the target `team_id`.

## Mandatory Rules (MUST)
- Do not guess team IDs. Always call `+list` first to discover real team IDs.
- If the user references a team by name, match the name against the returned list before proceeding.

## Command
```bash
ae-cli team +list
ae-cli team +list --format table
ae-cli team +list --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| None | — | No parameters required |

## Decision Rules
- When the user says "show me the teams", "what teams do I have", or needs a `team_id` for a subsequent command and none is in context, call this first.
- If many teams are returned, summarize by `id`, `name`, `scope`, and `enabled` to help the user pick the right one.
- Once a team is confirmed in the current conversation, reuse its ID without calling `+list` again unless the user switches teams.

## Next Steps on Failure
- Empty result: confirm account permissions and host environment.
- Auth error: run `ae-cli auth login`.

## Recommended Chaining
- `+list` → user confirms `team_id` → `+run-start` or `+run-chat`
- `+list` → `+update` or `+delete`
