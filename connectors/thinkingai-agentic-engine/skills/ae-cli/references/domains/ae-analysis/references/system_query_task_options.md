# system query-task options

Use before query-task list or export to discover every valid filter value exposed by the current environment.

Command:

```bash
ae-cli system query-task options --company-id <company_id>
```

Capability id: `system.query_task.options`.

The response maps:

- `statuses[].code` to the localized task status name.
- `content_types[].code` to the localized content type name.
- `task_types[].code` to the localized task type name.
- `projects[].project_id` and `workspaces[].space_code` to display names.
- `clusters[].cluster_name` to its query engine metadata.

Use the returned codes and names unchanged in `query-task list` or `query-task export`. Do not infer codes from UI labels or examples.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
