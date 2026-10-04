# agent +reject-skill-share (Reject Skill Share)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skill Share (peer-to-peer) / write**

## Use Cases
- Reject a received Skill share.
- Endpoint: `POST /api/sandbox/agent/skills/shares/[id]/reject`.
- Sharing is Skill-only — MCP has no share flow.

## Mandatory Rules (MUST)
- `--id` is required and must reference a **share** record (CUID), not a Skill ID. Obtain it via `+list-skill-shares --direction received` — do not guess.
- This is an ordinary `write` operation and does not require CLI confirmation.
- Only `pending` shares can be rejected.

## Command
```bash
ae-cli agent +reject-skill-share --id <share-cuid>
ae-cli agent +reject-skill-share --dry-run --id <share-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Share record ID (CUID) |

## Decision Rules
- `--id` here is a share ID (not a Skill ID).
- Use this when the recipient does not want to accept a pending share.
- Cannot reject a share that is already `accepted` / `rejected`.

## Next Steps on Failure
- `404` / not found: re-run `+list-skill-shares --direction received --status pending` to verify the share ID.

## Recommended Chaining
- `+list-skill-shares --direction received --status pending` → confirm share `id` → `+reject-skill-share` (or `+accept-skill-share`)
