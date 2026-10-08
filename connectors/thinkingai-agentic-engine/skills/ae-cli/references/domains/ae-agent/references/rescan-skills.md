# agent +rescan-skills (Internal Compatibility Reference)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skills / internal write**

## Use Cases
- Preserve compatibility for privileged administrators who already use the legacy command.
- Endpoint: `POST /api/sandbox/agent/skills/rescan`.
- The endpoint synchronizes system-scope Skills only.
- The command is hidden from normal `agent --help` output and public Skill routing.

## Mandatory Rules (MUST)
- This command takes no flags.
- It requires `root` or `agent_admin` privileges; other users receive a 403 response.
- Never use it to recover a personal or company Skill.
- Never expose this command or its maintenance terminology in a customer-facing response.
- This is an ordinary `write` operation and does not require CLI confirmation.
- Prefer `--dry-run` before executing — rescan has filesystem side effects.

## Command
```bash
# Internal administrator use only
ae-cli agent +rescan-skills

# Dry-run to inspect the request before executing
ae-cli agent +rescan-skills --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| _(none)_ | — | This command takes no flags |

## Decision Rules
- Use this command only for an explicitly authorized system-Skill maintenance task.
- Confirm the operator has `root` or `agent_admin` privileges before running it.
- Do not route ordinary Skill update failures to this command.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `403`: the current operator lacks the required administrator role.
- Other failures: stop and inspect administrator-only service logs; do not relay diagnostic details to customers.

## Recommended Chaining
- `+rescan-skills` → `+list-skills` (verify system Skills only)
