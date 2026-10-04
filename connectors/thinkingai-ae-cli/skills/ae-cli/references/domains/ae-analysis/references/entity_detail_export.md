# analysis entity-detail export

Submit a bounded entity detail query as an async gzip artifact.

Read `analysis_data_retrieval.md` first. The submit response returns `run_id` and `artifact_id`; poll with `analysis run inspect`, then download with `analysis artifact download`.

Use this command for full or unknown-size entity detail data. Common reads backend batches internally and writes one artifact.

```bash
ae-cli analysis entity-detail export \
  --project-id <project_id> \
  --definition '{"entity":"user","cohort":{"relation":"and","items":[{"field":{"name":"level","type":"user_property"},"operator":"gte","values":[1]}]}}' \
  --artifact-format jsonl
```

Input:
- `--project-id` numeric project ID.
- `--definition` same bounded entity detail shape as `entity-detail run`.
- `--request-id` optional `cli_<32 lowercase hex>` lifecycle ID.
- `--use-cache` optional boolean.
- `--zone-offset` optional number.
- `--artifact-format` `jsonl` or `csv`; default `jsonl`.
- `--timeout-seconds` optional async runtime guard.

Do not pass `--limit`; async export rejects inline limits. Use `--artifact-format`, not global `--format`, for artifact format.

Export does not accept `--limit` or `--offset`; backend batching is internal.

For `entity="user"`, every artifact row includes `#user_id`, `#account_id`, and `#distinct_id` plus requested user properties. For a custom entity, omit `properties`; the artifact contains only the entity value column and rejects additional properties. When presenting user artifacts, Agents should display account ID and visitor ID instead of exposing internal `#user_id` as the only visible identity.

Output:

Returns an async descriptor with opaque `run_id` / `artifact_id`, lifecycle status, expiration, and effective timeout/deadline fields. JSONL artifacts start with metadata and schema lines; CSV artifacts start directly with the header and contain only valid CSV records.
