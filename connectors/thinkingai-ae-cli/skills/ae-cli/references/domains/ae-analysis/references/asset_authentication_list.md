# analysis-governance asset-authentication list

Use for bounded online preview, search, and filtering of project asset-authentication rows.

This command filters on the server before sorting and pagination. Use `export` for a complete offline dataset and `update` for an explicit typed asset set.

Do not use it to synthesize a complete catalog by paging or to change authentication state.

Command:

```bash
ae-cli analysis-governance asset-authentication list --project-id <project_id> --asset-types '["dashboard","report"]' --authentication-status 0 --heat-count-gt 50 --user-count-gt 5 --match any --limit 100
```

Capability id: `governance.asset_authentication.list`.

`match=any|all` combines only the supplied numeric thresholds. Asset types, authentication status, and keyword queries are always AND filters. `queries` matches any supplied keyword.

Output uses `data.items[]`, `total`, `limit`, `offset`, `has_more`, and `next_offset`. Row identity is always `resource_type + resource_key`; dashboard and report keys are numeric IDs encoded as strings, while metadata assets use business names.

## analysis-meta asset-authentication list

The legacy command remains available for one release cycle and returns the old row shape.

```bash
ae-cli analysis-meta asset-authentication list --project-id <project_id> --limit 50 --offset 0
```

Legacy Input is `project_id`, `limit`, and `offset`. Legacy Output uses the same directory envelope with the old asset field names.
