# agent +accept-skill-share (Accept Skill Share)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skill Share (peer-to-peer) / write**

## Use Cases
- Accept a received Skill share.
- Endpoint: `POST /api/sandbox/agent/skills/shares/[id]/accept`.
- Accepting creates an independent personal copy of the Skill for the recipient.
- Sharing is Skill-only — MCP has no share flow.

## Mandatory Rules (MUST)
- `--id` is required and must reference a **share** record (CUID), not a Skill ID. Obtain it via `+list-skill-shares --direction received` — do not guess.
- This is an ordinary `write` operation and does not require CLI confirmation.
- Only `pending` shares can be accepted.

## Command
```bash
ae-cli agent +accept-skill-share --id <share-cuid>
ae-cli agent +accept-skill-share --dry-run --id <share-cuid>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Share record ID (CUID) |

## Decision Rules
- `--id` here is a share ID (not a Skill ID) — `+share-skill` takes a Skill ID instead.
- Use this after receiving a share (`+list-skill-shares --direction received --status pending`).
- Accepting creates an independent personal copy; the source Skill is unaffected.
- Cannot accept a share that is already `accepted` / `rejected`.

## Next Steps on Failure
- `404` / not found: re-run `+list-skill-shares --direction received --status pending` to verify the share ID.

## Recommended Chaining
- `+list-skill-shares --direction received --status pending` → confirm share `id` → `+accept-skill-share` → `+list-skills` (verify the new copy)
