# analysis user-tag-member export

Stream the native full tag-member download as an async gzip artifact. Read `analysis_data_retrieval.md` first.

Do not use this command for an inline sample or filtered keyword search; use `user-tag-member run` for preview behavior.

Flags: `--project-id`, `--tag-name` required. Optional: `--snapshot-date`, `--property-names`, `--request-id`, `--artifact-format jsonl|csv`, `--timeout-seconds`. The default format is `jsonl`.

If you provide `--request-id`, use `cli_<32 lowercase hex>`. Omit it unless you need to correlate logs or cancel a known running query.

Export does not accept `--offset`, `--fields`, `--query`, or `--use-cache`. Common executes the native current-tag or history-tag full-download SQL once and streams result rows directly as `jsonl.gz` or `csv.gz`; it does not concatenate preview pages. The existing full-download ceiling still applies.

```bash
ae-cli analysis user-tag-member export --project-id <project_id> --tag-name user_level --artifact-format jsonl
ae-cli analysis run inspect --run-id <run_id>
ae-cli analysis artifact download --run-id <run_id> --artifact-id <artifact_id> --output tag-members.jsonl.gz
```
