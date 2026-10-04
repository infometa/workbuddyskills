# analysis history-tag-data run

Run a bounded inline history tag statistics query. Read `analysis_data_retrieval.md` before choosing run vs export.

Output is bounded history-tag statistics, not member rows. Use `history-tag-data-drilldown run/export` for users behind a returned value or bucket.

Flags: `--project-id`, `--tag-name`, `--view` required. Optional: `--request-id`, `--preview-rows`, `--timeout-seconds`.

If you provide `--request-id`, use `cli_<32 lowercase hex>`. Omit it unless you need to correlate logs or cancel a known running query.

`--view` is AI-facing history tag view JSON. It must include a history date range (`recent_day` or `start_time`/`end_time`) and `time_particle_size:"T1"`. Optional fields include `interval_type`, `property_range`, `time_particle`, `array_group_type`, and `column_splited_str`. Do not pass raw frontend wrapper DTOs.

```bash
ae-cli analysis history-tag-data run --project-id <project_id> --tag-name user_level --view '{"recent_day":"0-31","time_particle_size":"T1","first_day_of_week":1,"interval_type":"default","array_group_type":"array_item_group"}' --preview-rows 100
```
