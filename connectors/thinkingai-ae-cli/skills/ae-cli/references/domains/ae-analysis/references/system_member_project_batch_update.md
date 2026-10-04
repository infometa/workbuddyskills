# system member-project batch-update

Use when the user needs to batch update and remove a member project assignments.

Do not use it outside the system member-project operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli system member-project batch-update --dry-run --company-id <company-id> --target-open-id <target-open-id>
ae-cli system member-project batch-update --company-id <company-id> --target-open-id <target-open-id> --yes
```

Capability id: `system.member_project.batch_update`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--target-open-id` | Yes | Target member open ID. |
| `--project-updates` | No | Project update array: project_id, role_names, and optional data_power_id. |
| `--project-removals` | No | Project removal and handover array. |
