# engage-flow flow update-remark

Update a flow version remark.

> Capability id: `engage-flow.version.update-remark` · Domain: `engage`.

```bash
ae-cli engage-flow flow update-remark --project-id <project-id> --flow-uuid <flow-uuid> --flow-version-desc <remark>
```

## Parameters

- `--project-id`, `-p`: Numeric project ID.
- `--flow-uuid`: Flow version UUID whose remark should be updated.
- `--flow-version-desc`: Updated flow version remark. Pass an empty string to clear it.

## Output

Returns `success`, `flow_uuid`, and `flow_version_desc`.
