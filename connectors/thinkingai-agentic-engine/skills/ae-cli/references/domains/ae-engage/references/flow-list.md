# ae-cli engage-flow flow list


Query the flow list.

Mapped command: `ae-cli engage-flow flow list`

## Response shape

The result is `{ data: { items, total } }`. Each item recursively uses snake_case fields,
for example `data.items[].flow_id`, `data.items[].flow_uuid`, and `data.items[].mapping_status`.

## Flags

| Flag | Type | Required | Description |
|------|------|------|------|
| `--project-id` / `-p` | number | Yes | Project ID |

## Examples

```bash
ae-cli engage-flow flow list --project-id 1
```
