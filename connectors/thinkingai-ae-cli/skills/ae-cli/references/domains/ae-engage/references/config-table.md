# engage-setting config-table

> Capability ids: `engage-setting.config-table.{upload,save,list,query-data,update-data,delete}` · Domain: `engage`.

## Commands

```bash
# 1. Upload and parse a config table file (base64 content) → caches rows under request-id
ae-cli engage-setting config-table upload \
  --project-id <project_id> --request-id <request_id> --file-name data.csv \
  --file-content "$(base64 -i data.csv)"

# 2. Persist the parsed rows as a new config table
ae-cli engage-setting config-table save \
  --project-id <project_id> --request-id <request_id> --info-name <table_name>

# List config tables
ae-cli engage-setting config-table list --project-id <project_id>

# Query rows of a config table
ae-cli engage-setting config-table query-data --project-id <project_id> --info-id <info_id>

# Replace an existing config table's data with a freshly uploaded file
ae-cli engage-setting config-table update-data \
  --project-id <project_id> --request-id <request_id> --info-name <table_name> --info-id <info_id>

# Delete a config table and its data (high-risk)
ae-cli engage-setting config-table delete --project-id <project_id> --info-id <info_id> --yes
```

## Parameters

### upload

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--request-id` | Yes | Client-supplied request id used to cache parsed rows for the subsequent save/update-data. |
| `--file-name` | Yes | Original file name including extension (.csv/.xlsx). |
| `--file-content` | Yes | Base64-encoded file content. |

### save

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--request-id` | Yes | Request id returned by a prior upload. |
| `--info-name` | Yes | Config table name. |

### list

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |

### query-data

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--info-id` | Yes | Config table ID. |

### update-data

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--request-id` | Yes | Request id returned by a prior upload. |
| `--info-name` | Yes | Config table name. |
| `--info-id` | Yes | Config table ID to update. |

### delete

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--info-id` | Yes | Config table ID to delete. |

## Output

- `upload`: `data.file_name`, `data.data_num` (parsed row count), `data.data_list` (preview of up to 10 rows, each with `data_key`, `data_value`).
- `save`: `data.info_id` — created config table ID.
- `list`: `data.items` (each with `id`, `project_id`, `info_id`, `info_name`, `creator_open_id`, `login_name`, `create_time`, `update_time`) and `data.total`.
- `query-data`: `data.items` (each with `project_id`, `info_id`, `data_key`, `data_value`) and `data.total`.
- `update-data` / `delete`: `data.success`.

## Decision Rules

- Creating or replacing a config table is a two-step flow: `upload` (parse + cache by `request-id`) then `save` (new table) or `update-data` (replace existing). Always use a fresh `--request-id` per upload.
- The upload cache is keyed by `project-id` + `request-id`, expires after 10 minutes, and is consumed after a successful `save` or `update-data`.
- Discover existing `info_id` values with `config-table list` first; never invent them.
- `delete` is `high-risk-write` and requires `--yes` (or interactive confirmation).
