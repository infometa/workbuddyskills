# agent +list-skill-shares (List Skill Shares)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skill Share (peer-to-peer) / read**

## Use Cases
- List Skill shares (received by default; use `--direction sent` for outgoing).
- Endpoint: `GET /api/sandbox/agent/skills/shares`.
- Sharing is Skill-only — MCP has no share flow.
- Use this to find a share ID before `+accept-skill-share` / `+reject-skill-share`.

## Mandatory Rules (MUST)
- `--direction` must be one of the share directions (see below) when provided.
- `--status` must be one of the share statuses (see below) when provided.
- Do not guess share IDs. Always call `+list-skill-shares` first when a share ID is needed.

## Share Directions
`received | sent`

## Share Statuses
`pending | accepted | rejected`

## Command
```bash
ae-cli agent +list-skill-shares
ae-cli agent +list-skill-shares --direction received --status pending --format table
ae-cli agent +list-skill-shares --direction sent
ae-cli agent +list-skill-shares --dry-run --direction received
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--direction` | No | `received` (default) \| `sent` |
| `--status` | No | Filter by status (see above) |

## Decision Rules
- By default, lists shares the current user has **received**; use `--direction sent` to list outgoing shares.
- `--status pending` filters to shares awaiting action.
- Capture the share `id` for `+accept-skill-share` / `+reject-skill-share`.

## Next Steps on Failure
- `--direction must be one of...`: use `received` or `sent`.
- `--status must be one of...`: use one of the share statuses.
- Empty result: no shares match the filter.

## Recommended Chaining
- `+list-skill-shares --direction received --status pending` → confirm share `id` → `+accept-skill-share` / `+reject-skill-share`
