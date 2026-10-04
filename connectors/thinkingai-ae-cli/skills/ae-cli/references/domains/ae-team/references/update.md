# team +update (Update Team)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Team management / write**

## Use Cases
- Partially update an existing team (PATCH semantics — only the fields you pass are changed).
- Common uses: rename a team, update its config, disable/enable it, change scope.

## Mandatory Rules (MUST)
- `--id` is required. Obtain the real team ID via `+list` — do not guess.
- At least one optional field must be provided in addition to `--id`.
- `--config` replaces the entire TeamConfig; provide the complete new config, not a partial patch.
- `--scope` must be `personal` or `company` if provided.
- This is an ordinary `write` operation and does not require CLI confirmation.

## Command
```bash
ae-cli team +update --id <team_id> --name "新名称"
ae-cli team +update --id <team_id> --enabled false
ae-cli team +update --id <team_id> --config '<full_new_config_json>'
ae-cli team +update --dry-run --id <team_id> --name "Test"
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--id` | Yes | Team ID |
| `--name` | No | New team name |
| `--config` | No | New complete TeamConfig JSON |
| `--description` | No | New description |
| `--scope` | No | `personal` \| `company` |
| `--enabled` | No | `true` \| `false` |

## Decision Rules
- If the user wants to modify only the name or description, pass only those flags — the server keeps all other fields unchanged.
- If the user wants to update the config, first call `+list` with `--jq` to extract the current config, modify it, then pass the updated config to `+update`.
- `--enabled false` disables the team without deleting it.

## Next Steps on Failure
- `404`: team ID not found — re-run `+list` to verify.
- `409`: there may be active runs; wait for them to complete or cancel them with `+run-cancel` first.

## Recommended Chaining
- `+list` → confirm `id` → `+update`
- `+update --enabled false` → `+delete` (when ready to delete)
