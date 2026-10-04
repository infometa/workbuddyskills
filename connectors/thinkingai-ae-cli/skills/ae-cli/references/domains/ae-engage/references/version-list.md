# engage-flow version list

List current, historical, new, update, and test versions for a flow.

> Capability id: `engage-flow.version.list` · Domain: `engage`.

```bash
ae-cli engage-flow version list --project-id <project-id> --flow-id <flow-id>
```

## Parameters

- `--project-id`, `-p`: Numeric project ID.
- `--flow-id`: Flow ID whose versions should be listed.

## Output

Returns `items` containing flow version metadata and `total` containing the number of returned versions.
