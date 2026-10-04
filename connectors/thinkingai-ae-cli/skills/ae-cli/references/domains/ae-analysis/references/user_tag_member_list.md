# analysis user-tag-member list

Run a bounded inline tag member query. Read `analysis_data_retrieval.md` before choosing list vs export.

Do not use it for complete/unknown-size membership retrieval or history statistics. Output contains at most the requested inline limit and has no caller pagination contract.

Flags: `--project-id`, `--tag-name` required. Optional: `--snapshot-date`, `--property-names`, `--fields`, `--query`, `--use-cache`, `--request-id`, `--preview-rows`, `--timeout-seconds`.

When `--fields` is omitted, each member row returns `#user_id`, `#account_id`, `#distinct_id`, and the stable logical `tag_value`. Internal calculated tag column names are never part of the public response. The sync timeout defaults to 120 seconds and accepts an explicit value up to 180 seconds.
Omit `--preview-rows` to return at most 1000 rows, matching the UI member query. Explicit values must be between 1 and 100000; use a smaller preview when only a sample is needed.

If you provide `--request-id`, use `cli_<32 lowercase hex>`. Omit it unless you need to correlate logs or cancel a known running query.

For full or unknown-size member data, use `user-tag-member export`; the list command has no next-page contract.

```bash
ae-cli analysis user-tag-member list --project-id <project_id> --tag-name user_level --preview-rows 100
ae-cli analysis user-tag-member list --project-id <project_id> --tag-name user_level --snapshot-date 2026-07-01 --property-names '["country"]' --fields '["#user_id","#account_id","#distinct_id","tag_value","country"]' --preview-rows 50
```
