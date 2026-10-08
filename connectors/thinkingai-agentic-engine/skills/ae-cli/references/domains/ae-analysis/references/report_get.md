# analysis report get

Use when the user needs one saved report definition as AI QP without executing the report.

Do not use as a workaround after a builder-supported ad-hoc QP builder fails. For builder failure, stop and handle the structured error or ask for clarification.

Command:

```bash
ae-cli analysis report get --project-id <project_id> --report-id <report_id>
```

Input sends `project_id` and `report_id`.

This command reads saved definition metadata and deliberately has no `--use-cache` option. Cache selection applies to `report-data run/export`, not to definition reads.

Output is the gateway envelope. `data` contains `version`, `model_type`, `definition`, report metadata, and dashboard membership in snake_case. Use `data.version` as `--report-version` when updating the same report. Raw frontend `events`, `event_view`, `visual_view`, and raw QP are not returned.

For a saved non-SQL report with a time granularity, `data.definition` returns the agent-facing `time_particle_size` spelling, such as `day`, `hour`, or `total`; internal `T0` through `T9` codes must never leak. If `time_particle_size` is absent, the saved definition has no readable granularity. Do not infer a granularity from the number of result rows; execute the saved report as-is or use an explicit ad-hoc definition when the user requires a specific granularity.

This read is mandatory before applying report-data overrides. Branch on `data.model_type`:

- `sql`: only `--sql-params` is valid. Every override name must already exist in `data.definition.params`; time values may be overridden only through a saved `part_date` or time parameter. A saved PartDate definition exposes boolean `use_timezone` (default `false`); it is definition metadata and cannot be overridden by report-data.
- non-SQL analysis models: use `--filters`, `--group-by`, `--start-time`, `--end-time`, or `--time-granularity`; do not send `--sql-params`.
- `tag`: report-data executes the saved tag definition. For a different tag view, use `analysis history-tag-data run/export`.
