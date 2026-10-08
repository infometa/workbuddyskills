# analysis-meta asset-abnormal get

Use when the user needs to get abnormal reason for one asset.

Do not use it to list all abnormal assets or to inspect normal asset definitions; use `asset abnormal-list` or the asset's own get command.

Command:

```bash
ae-cli analysis-meta asset-abnormal get --project-id <project_id> --resource-type <resource_type> --resource-id <resource_id> --resource-name <resource_name> --table-type <table_type>
ae-cli analysis-meta asset-abnormal get --dry-run
```

Capability id: `metadata.asset_abnormal.get`.

Input sends `project_id`, `resource_type`, `resource_id`, `resource_name`, `table_type`.

Output `data.resource` contains the matched asset's abnormal detail/reason.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--resource-type` | Yes | Resource type. |
| `--resource-id` | No | Resource ID. |
| `--resource-name` | No | Resource name. |
| `--table-type` | No | Property table type when the resource is a property. |
