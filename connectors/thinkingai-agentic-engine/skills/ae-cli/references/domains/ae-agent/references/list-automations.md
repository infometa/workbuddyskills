# agent +list-automations (List Automations)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Automations / read**

```text
Transition status: transitional
Owning module: te-claude automation
Current transport: GET /api/sandbox/agent/automations
Gateway target: TBD (no equivalent Gateway capability is currently registered)
Review after: 2026-10-07
Exit condition: Migrate when the Gateway exposes equivalent workspace-scoped automation listing.
```

## Use Cases
- List the current user's Agent automation tasks in one workspace.
- Returns `items` containing automation summaries; key fields include `id`, `name`, `status`, `cronExpression`, `agentSpaceId`, and `agentSpaceName`.
- Agent Team scheduled tasks shown alongside automations in the workspace UI are a separate resource and are not returned by this command.
- Use this to discover a real automation ID before `+update-automation`.

## Mandatory Rules (MUST)
- Do not guess automation IDs. Always call `+list-automations` first when an automation ID is needed.
- Pass `--agent-space-id` for a non-default workspace. Omitting it lists the personal default workspace, including legacy tasks without a workspace ID; it does not list all workspaces or infer the current conversation's workspace.
- Keep the same workspace ID when calling `+update-automation`. An automation created from a conversation may belong to a non-default workspace; use the returned `automation.agentSpaceId` when verifying creation.
- On servers without workspace support, omit `--agent-space-id`. Listing retains its original user-scoped behavior and responses may lack `agentSpaceId`/`agentSpaceName`; neither field is required by the CLI. Older servers do not enforce the new workspace filter.
- Do not surface raw automation IDs, raw JSON, or concrete detail paths in user-facing replies — use the ID only internally for subsequent commands.

## Command
```bash
ae-cli agent +list-automations
ae-cli agent +list-automations --status active
ae-cli agent +list-automations --q "daily" --limit 20 --format table
ae-cli agent +list-automations --agent-space-id <workspace-id>
ae-cli agent +list-automations --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--agent-space-id` | No | Workspace ID; omitted means the personal default workspace |
| `--q` | No | Keyword for automation name or instruction |
| `--status` | No | `active` \| `paused` |
| `--limit` | No | Maximum number of automations to return, 1–10000 |

## Decision Rules
- When the user wants to pause, resume, rename, or edit an automation, call this first to find the target ID.
- `--status active` lists only enabled automations; `--status paused` lists paused ones.
- If many automations are returned, summarize by `name` and `status` to help the user pick the right one.

## Next Steps on Failure
- Empty result: check the active AE host and workspace ID before concluding there are no automations. This command does not include Agent Team scheduled tasks.
- Auth error: run `ae-cli auth login`.

## Recommended Chaining
- `+list-automations` → confirm `id` → `+update-automation`
