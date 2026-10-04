# analysis event-detail export

Submit a bounded event detail query as an async gzip artifact.

Read `analysis_data_retrieval.md` first. The submit response returns `run_id` and `artifact_id`; poll with `analysis run inspect`, then download with `analysis artifact download`.

Use this command for full or unknown-size event detail data. Common reads backend batches internally and writes one artifact.

```bash
ae-cli analysis event-detail export \
  --project-id <project_id> \
  --definition '{"event":"login","time_range":{"mode":"relative","relative_date_range":"0-7"}}' \
  --artifact-format jsonl
```

Input:
- `--project-id` numeric project ID.
- `--definition` same AI-facing shape as `event-detail run`.
- `--request-id` optional `cli_<32 lowercase hex>` lifecycle ID.
- `--use-cache` optional boolean.
- `--zone-offset` optional number.
- `--artifact-format` `jsonl` or `csv`; default `jsonl`.
- `--timeout-seconds` optional async runtime guard.

Do not pass `--limit`; async export rejects inline limits. Use `--artifact-format`, not global `--format`, for artifact format.

Export does not accept `--limit` or `--offset`; backend batching is internal.

`definition.properties` uses the same exact projection as `event-detail run`. The artifact may include required system event columns, but it must not expand to every visible event property.

Output:

Returns an async descriptor with opaque `run_id` / `artifact_id`, lifecycle status, expiration, and effective timeout/deadline fields. JSONL artifacts start with metadata and schema lines; CSV artifacts start directly with the header and contain only valid CSV records.
