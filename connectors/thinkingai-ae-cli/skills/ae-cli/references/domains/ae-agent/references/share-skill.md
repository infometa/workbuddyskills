# agent +share-skill (Share Skill Peer-to-Peer)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Skill Share (peer-to-peer) / write**

## Use Cases
- Share a personal Skill to another user in the same company.
- Endpoint: `POST /api/sandbox/agent/skills/[id]/share`.
- Sharing is Skill-only — MCP has no share flow.
- The recipient gets a pending share; accepting creates an independent personal copy for the recipient.
- Optional `--category` / `--icon-emoji` / `--icon-color` set the market meta proposed for the recipient's copy.

## Mandatory Rules (MUST)
- `--id` is required and must reference a **personal-scope** Skill (CUID). Obtain it via `+list-skills` — do not guess.
- `--to-user-id` is required — the recipient user ID (must be in the same company).
- `--category` must be one of the market category keys (see below) when provided.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Market Category Keys
`ae_preset | dev_tool | search_tool | data_query | content_gen | enterprise | life | automation | other`

## Command
```bash
ae-cli agent +share-skill --id <skill-cuid> --to-user-id <user-id>
ae-cli agent +share-skill --id <skill-cuid> --to-user-id <user-id> --category dev_tool --icon-emoji robot
ae-cli agent +share-skill --dry-run --id <skill-cuid> --to-user-id <user-id>
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Skill record ID (CUID, personal scope) |
| `--to-user-id` | Yes | Recipient user ID (same company) |
| `--category` | No | Market category key (see above) |
| `--icon-emoji` | No | Market icon emoji (e.g. `robot`) |
| `--icon-color` | No | Market icon color (e.g. `#1E76F0`) |

## Decision Rules
- `--id` here is a Skill ID (not a share ID) — `+accept-skill-share` / `+reject-skill-share` take a share ID instead.
- Only personal-scope Skills can be shared; the recipient must be in the same company.
- Do not guess `--to-user-id`; obtain it from the user or contact directory.
- Use `--dry-run` first to verify the request shape before executing.

## Next Steps on Failure
- `404` / not found: re-run `+list-skills --scope personal` to verify the Skill ID.
- Cross-company error: the recipient is not in the same company.

## Recommended Chaining
- `+list-skills` (personal) → `+share-skill` → recipient: `+list-skill-shares --direction received` → `+accept-skill-share` / `+reject-skill-share`
