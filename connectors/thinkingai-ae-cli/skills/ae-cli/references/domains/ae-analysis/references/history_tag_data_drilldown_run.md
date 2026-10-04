# analysis history-tag-data-drilldown run

Run a bounded inline user drilldown for one value/bucket returned by `history-tag-data run/export`.

Do not use it for complete or unknown-size drilldown data. Output contains only the bounded inline user result; use export when truncation would change the answer.

Flags: `--project-id`, `--tag-name`, `--snapshot-date`, `--group-col`, `--view` required. Optional: `--property-names`, `--fields`, `--query`, `--use-cache`, `--request-id`, `--preview-rows`, `--timeout-seconds`.

Use the same `--view` that produced the statistic row. `--group-col` must be the exact statistic value or bucket label. Use export for full drilldown users; this command has no next-page contract.

```bash
ae-cli analysis history-tag-data-drilldown run --project-id <project_id> --tag-name user_level --snapshot-date 2026-07-01 --group-col VIP --view '{"recent_day":"0-31","time_particle_size":"T1","first_day_of_week":1,"interval_type":"default","array_group_type":"array_item_group"}' --preview-rows 100
```
