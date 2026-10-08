# ae-cli engage-flow flow delete


Batch delete flows.

Mapped command: `ae-cli engage-flow flow delete`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--flow-uuid-list` | json | Yes | Flow UUID JSON array |

## Safety Constraints

This command is a **write operation** and and deletes flows.

## Examples

```bash
ae-cli engage-flow flow delete --project-id 1 --flow-uuid-list '["flow_uuid_1"]'
```
