# engage-setting whitelist

> Capability ids: `engage-setting.whitelist.{add,update,delete,verify}` · Domain: `engage`.

## Commands

```bash
# Add whitelist entries
ae-cli engage-setting whitelist add \
  --project-id <project_id> --prop-code <prop_code> --column-name <column_name> \
  --column-type <column_type> \
  --whitelist-list '[{"entity_id":"u1","source_value":"v1","note_name":"n"}]'

# Update a whitelist entry's note name
ae-cli engage-setting whitelist update --project-id <project_id> --whitelist-id <id> --note-name <name>

# Delete whitelist entries (high-risk)
ae-cli engage-setting whitelist delete --project-id <project_id> --whitelist-ids '["wl-1","wl-2"]' --yes

# Verify property values against the whitelist
ae-cli engage-setting whitelist verify \
  --project-id <project_id> --prop-code <prop_code> --column-type <column_type> \
  --whitelist-prop-list '["v1","v2"]'
```

## Parameters

### add

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--prop-code` | Yes | Associated user property code. |
| `--column-name` | Yes | Associated user property field name. |
| `--column-type` | Yes | Associated user property field type. |
| `--whitelist-list` | Yes | JSON array of entries (`entity_id`, `source_value`, `note_name`). |

### update

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--whitelist-id` | Yes | Whitelist entry ID to modify. |
| `--note-name` | No | New note name. |

### delete

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--whitelist-ids` | Yes | JSON array of whitelist entry IDs. |

### verify

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--prop-code` | Yes | Associated user property code. |
| `--column-type` | Yes | Associated user property field type. |
| `--whitelist-prop-list` | Yes | JSON array of property values to verify. |

## Output

- `add`: `data.success_num` — number of entries successfully added.
- `update` / `delete`: `data.success` — whether the operation succeeded.
- `verify`: `data.items` (verified entries with `entity_id`, `source_value`, `note_name`, `fail_msg`) and `data.total`.

## Decision Rules

- Use these commands when the user asks to add / edit / delete / verify project whitelist entries.
- Discover existing whitelist IDs with `ae-cli engage-setting whitelist list --project-id <project_id>` first; never invent IDs.
- `delete` is `high-risk-write` and requires `--yes` (or interactive confirmation).
