# engage-task indicator-user

Build SQL, query inline users, or export the users behind an engagement-task report indicator.

> Capability ids: `engage-task.indicator-user.sql`, `engage-task.indicator-user.run`, and `engage-task.indicator-user.export` · Domain: `engage` · Risk: read-only.

## Commands

```bash
# Build and validate SQL without executing it
ae-cli engage-task indicator-user sql \
  --project-id 1 \
  --task-id task_123 \
  --indicator main \
  --start-time 2026-04-01 \
  --end-time 2026-04-07

# Query a bounded inline user list
ae-cli engage-task indicator-user run \
  --project-id 1 \
  --task-id task_123 \
  --indicator secondary \
  --secondary-index 2 \
  --start-time 2026-04-01 \
  --end-time 2026-04-07 \
  --limit 100

# Export a custom metric's users
ae-cli engage-task indicator-user export \
  --project-id 1 \
  --task-id task_123 \
  --indicator metric \
  --metric-id metric_1 \
  --start-time 2026-04-01 \
  --end-time 2026-04-07 \
  --artifact-format csv
```

Use `sql` to obtain the generated user-detail SQL, `run` for a small inline result, and `export` for a downloadable full result.

## Required input

All commands require `--project-id`, `--task-id`, `--indicator`, `--start-time`, and `--end-time`.

Dates use `yyyy-MM-dd`, and the start date must not be later than the end date. The task must exist under the specified project.

`--indicator` maps to the report population as follows:

| Value | Report population | Usage note |
|---|---|---|
| `original_trigger` | Original triggered users | Triggered tasks only |
| `plan` | Planned-delivery users | Task delivery funnel |
| `actual_trigger` | Actual-trigger/actual-delivery users | Task delivery funnel |
| `trigger_success` | Successfully triggered/delivered users | Task delivery funnel |
| `view` | Users who produced the configured view event | Requires view-event data |
| `click` | Users who produced the configured click event | Requires click-event data |
| `main` | Main conversion-indicator users | Combine with `--retention-type` for converted/lost users |
| `secondary` | Nth secondary conversion-indicator users | Requires `--secondary-index` |
| `metric` | Users behind a configured custom metric | Requires `--metric-id` |
| `click_activate` | Click activation users | Used in experiment activation reports |
| `main_activate` | Main-indicator activation users | Used in experiment activation reports |
| `secondary_activate` | Nth secondary-indicator activation users | Requires `--secondary-index`; used in experiment activation reports |

## Conditional input

- `secondary` and `secondary_activate` require `--secondary-index 1..10`. Other indicators reject this flag.
- `metric` requires `--metric-id`; obtain the ID with `ae-cli engage-task metric list`. Other indicators reject this flag.
- `main`, `secondary`, `main_activate`, and `secondary_activate` must reference a conversion indicator configured on the task.
- `click_activate`, `main_activate`, and `secondary_activate` use `source=experiment` and `group-by=experiment`; explicitly supplied values must also be `experiment`. The task must have an activation event configured. `click_activate` additionally requires a click-event experiment.
- Non-metric indicators grouped by experiment use `source=experiment`, and the task must be an experiment task. Metric indicators continue to use `source=metric`.
- Explicit `--source experiment` always requires an experiment task, even with date, batch, or trigger grouping.
- `--group-by experiment --is-summary false` requires `--exp-group-id`. The `plan` indicator never accepts `--exp-group-id`; when grouped by experiment, it supports summary queries only.
- `--group-by batch` is supported only by non-triggered tasks. A non-summary batch segment requires `--task-instance-id`.
- `--group-by trigger` and `original_trigger` are supported only by triggered tasks.
- `--retention-type lost` supports `actual_trigger`, `trigger_success`, `view`, `click`, `main`, and `secondary`; it also supports `plan` for triggered tasks. It is rejected for `original_trigger`, `metric`, all activate indicators, and `plan` on non-triggered tasks.

## Optional report context

- `--group-by` selects `batch`, `date`, `trigger`, or `experiment`; it defaults to `experiment` for activate indicators and `date` otherwise.
- `--is-summary` defaults to `true`. Set it to `false` when reproducing a drilled-down batch or experiment row.
- `--retention-type` selects `retention` or `lost`; the default is `retention`. See the supported combinations above.
- `--source` selects `task`, `experiment`, or `metric`. It defaults to `metric` for metric indicators, `experiment` for activate indicators or experiment grouping, and `task` otherwise.
- `--task-instance-id` narrows a non-triggered task to one execution instance.
- `--exp-group-id` narrows an experiment report to one group.
- `--push-language-code`, `--user-time-zone`, and `--show-time-zone` reproduce the corresponding task-report filters. Copy their values from the report context when needed.
- `--push-language-code` accepts `all`, `default`, `ar`, `az`, `bs`, `ca`, `zh-Hans`, `zh-Hant`, `hr`, `cs`, `da`, `nl`, `en`, `et`, `fi`, `fr`, `ka`, `bg`, `de`, `el`, `hi`, `he`, `hu`, `id`, `it`, `ja`, `ko`, `lv`, `lt`, `ms`, `nb`, `fa`, `pl`, `pt`, `pa`, `ro`, `ru`, `sr`, `sk`, `es`, `sv`, `th`, `tr`, `uk`, or `vi`.
- `--user-time-zone` accepts `all` or a decimal offset from `-12` through `14` that exists in the task's execution details. An unavailable value is rejected instead of falling back to all users.
- `--show-time-zone` accepts offsets from `-12` through `14`. Omit it or pass `99` to use the backend server's default time zone.

## Execution input and output

- `sql` returns `sql` and `indicator` and does not execute the query.
- `run` accepts `--request-id`, `--limit`, and `--timeout-seconds`. The default limit is `100` and the maximum is `1000`; the default timeout is `120` seconds and the maximum is `180` seconds. It returns `#user_id`, `#account_id`, and `#distinct_id` for each user.
- `export` accepts `--request-id`, `--artifact-format jsonl|csv`, and `--timeout-seconds`. The default format is `jsonl`; the maximum timeout is six hours. It returns `run_id` and `artifact_id`.
- For cross-user data sources, `#account_id` and `#distinct_id` are empty strings.

Use the query lifecycle commands to inspect and download an export:

```bash
ae-cli engage-query run inspect --run-id <run_id>
ae-cli engage-query artifact download --artifact-id <artifact_id> --output ./task-indicator-users.csv.gz
```

`--artifact-format` controls the exported file. The global `--format json|table` only controls CLI display output.
