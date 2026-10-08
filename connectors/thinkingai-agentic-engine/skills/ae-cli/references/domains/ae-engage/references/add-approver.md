# ae-engage engage-setting approval-approver add


Batch add approvers.

Mapped command: `ae-cli engage-setting approval-approver add`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--approvers` | json | Yes | approver open ID JSON array |

## Safety Constraints

This command is a **write operation** and and modifies the project approver configuration.

## Examples

```bash
ae-cli engage-setting approval-approver add --project-id 1 --approvers '["ou_xxx","ou_yyy"]'
```
