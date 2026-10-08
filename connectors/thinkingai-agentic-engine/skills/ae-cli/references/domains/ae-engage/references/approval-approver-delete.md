# engage-setting approval-approver delete

> Capability id: `engage-setting.approval-approver.delete` · Domain: `engage`.

## Command

```bash
ae-cli engage-setting approval-approver delete --project-id <project_id> --approver <open_id> --yes
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--approver` | Yes | OpenID of the approver to remove. |

## Output

- `data.success`: whether the approver was removed.

## Decision Rules

- Use this command when the user asks to remove/delete an approver from a project.
- Discover the real approver OpenID with `ae-cli engage-setting approval-approver list --project-id <project_id>` first; never invent an OpenID.
- Risk is `high-risk-write`; the CLI confirmation gate requires `--yes` (or interactive confirmation) before executing.
