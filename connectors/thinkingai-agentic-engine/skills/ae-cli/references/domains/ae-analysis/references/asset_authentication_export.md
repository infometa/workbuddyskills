# analysis-governance asset-authentication export

Use for complete offline processing of project asset-authentication rows.

Do not use it for interactive preview or let the CLI loop over `list`; this command invokes the complete export capability once.

Command:

```bash
ae-cli analysis-governance asset-authentication export --project-id <project_id> --asset-types '["dashboard","report"]' --output /tmp/assets.jsonl
```

Capability id: `governance.asset_authentication.export`.

The command does not accept `limit` or `offset` and performs exactly one complete server export call. It validates `complete`, `total`, `stat_as_of`, and `snapshot_hash`, then atomically publishes both:

- `<output>`: private-mode JSONL rows.
- `<output>.meta.json`: `complete`, `project_id`, `total`, `stat_as_of`, `snapshot_hash`, and the local file SHA-256 `checksum`.

Export projection always retains `resource_type`, `resource_key`, `display_name`, `authentication_status`, `heat_count90d`, `user_count90d`, and `impact_degree`; `--fields` can add or remove only optional descriptive and owner fields.

Use the sidecar `snapshot_hash` with `update --expected-snapshot-hash` when the selected asset set was derived from this export.
