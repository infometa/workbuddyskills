# analysis-governance asset-authentication update

Use to authenticate or revoke an explicit set of typed project assets.

Do not use it with guessed identities or as a rule engine; derive an explicit typed set from `list` or `export` first.

Inline command:

```bash
ae-cli analysis-governance asset-authentication update --project-id <project_id> --authentication-status 1 --asset-refs '[{"resource_type":"dashboard","resource_key":"4350"}]'
```

Large file command:

```bash
ae-cli analysis-governance asset-authentication update --project-id <project_id> --authentication-status 1 --asset-file /tmp/selected-assets.jsonl --expected-snapshot-hash <snapshot_hash> --dry-run
```

Capability id: `governance.asset_authentication.update`.

Choose exactly one identity input:

- `--asset-refs` for an inline typed array.
- `--asset-file` for JSONL rows containing `resource_type` and `resource_key`; extra export columns are ignored.
- `--asset-type` with `--asset-ids` as a same-type convenience form.

The CLI always normalizes the request to `asset_refs[]`. A bare `asset_ids[]` array is never sent to Common. When `expected_snapshot_hash` differs from the current authentication set, the complete update is rejected with `SNAPSHOT_CONFLICT`.

The response includes requested, resolved, changed, unchanged, and failed counts; retry only the returned failures.

## analysis-meta asset-authentication update

The legacy `--payload` entry remains available for one release cycle.

```bash
ae-cli analysis-meta asset-authentication update --project-id <project_id> --payload '{"authentication_status":1,"asset_list":[{"asset_name":"4350","asset_type":"dashboard"}]}'
```

Legacy Input is `project_id` plus `payload`. Legacy Output is the new structured batch result, although the input shape remains deprecated.
