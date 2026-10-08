# analysis-meta catalog export

## Use

Export the complete permission-filtered analysis metadata catalog for conversation-local reuse.

Do not use it for ordinary discovery, bounded search, or when compiler candidates already exist; use `catalog list` for the one aggregate online search.

```bash
ae-cli analysis-meta catalog export \
  --project-id <project_id> \
  --output <conversation_catalog_dir>/catalog.jsonl
```

Capability id: `metadata.catalog.export`.

## Input

The gateway input contains only `project_id`. The response must contain every accessible event, metric, event property, user property, cluster, and tag row with `complete=true` and `total` equal to the row count.

## Output

The CLI validates completeness, publishes the JSONL atomically with mode `0600`, and writes the adjacent `catalog.meta.json` last. Search the file locally and keep full rows out of model context. Reuse a valid snapshot only for the same host, project, principal, and conversation.

| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--output` | Yes | Conversation-local `.jsonl` path. |
