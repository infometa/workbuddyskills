# analysis-meta datatable version-get

Use when the user needs to get data table version detail.

Do not use it for the current table definition without a verified version ID; list versions first.

Command:

```bash
ae-cli analysis-meta datatable version-get --project-id <project_id> --version-id <version_id>
ae-cli analysis-meta datatable version-get --dry-run
```

Capability id: `metadata.data_table_version.get`.

Input sends `project_id`, `version_id`.

Output `data.version` contains the selected historical version detail.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--version-id` | Yes | Data table version ID. |
