# agent +del-agent (Delete Agent)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Agents / write**

## Use Cases
- Soft-delete an Agent (personal owner or company root/agent_admin; system Agents cannot be deleted).
- The Agent is marked deleted and its name is suffixed to free the unique index; no cascade deletion of related resources.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real Agent record ID (CUID) via `+list-agents` — do not guess.
- System Agents cannot be deleted via CLI.
- Prefer `--dry-run` before executing a destructive delete.
- This is a high-risk-write operation; never execute it before the dry-run impact is explicitly confirmed.

## Command
```bash
ae-cli agent +del-agent --id <agent-cuid> --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli agent +del-agent --id <agent-cuid> --yes
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Agent record ID (CUID) |

## Decision Rules
- Confirm the Agent ID with `+list-agents` before deleting.
- Deletion is soft — historical automations referencing the Agent may need re-pointing afterwards.
- Only `personal` Agents (owner) and `company` Agents (root/agent_admin) can be deleted; `system` returns `403`.

## Next Steps on Failure
- `404` / `Agent 不存在`: re-run `+list-agents` to verify the Agent ID.
- `403` / `系统 Agent 不允许删除` / `无权删除该 Agent`: system Agents are protected; company Agents require root/agent_admin.

## Recommended Chaining
- `+list-agents` → confirm `id` → `+del-agent` → `+list-agents` (verify gone)
