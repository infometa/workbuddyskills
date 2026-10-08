# ae-cli engage-flow flow modify-base-info


Modify the basic information of a flow canvas.

Mapped command: `ae-cli engage-flow flow modify-base-info`

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--flow-uuid` | string | Yes | Flow UUID |
| `--flow-name` | string | No | new flow name |
| `--flow-desc` | string | No | new flow description |
| `--group-id` | number | No | new group ID |

## Safety Constraints

This command is a **write operation** and modifies the basic information of a flow.

## Examples

```bash
ae-cli engage-flow flow modify-base-info --project-id 1 --flow-uuid flow_uuid_123 --flow-name "New Name"
```
