# engage-workbench workbench

> Capability ids: `engage-workbench.workbench.{list,add,update,delete}` · Domain: `engage`.

Workbench — workbench metric slot management. Each user may configure up to 4 metric cards per project; slots are scoped to the current login user, so `update`/`delete` only affect the caller's own slots. The first `list` auto-initialises 4 default slots.

## Commands

```bash
# List the current user's workbench metric slots
ae-cli engage-workbench workbench list --project-id <project_id>

# Add a metric slot (metric + date range + order)
ae-cli engage-workbench workbench add --project-id <project_id> \
  --metric-type <metric_type> --date-type <date_type> [--order-id <1-4>]

# Update a slot (own slot only)
ae-cli engage-workbench workbench update --project-id <project_id> \
  --slot-id <slot_id> --metric-type <metric_type> --date-type <date_type> [--order-id <1-4>]

# Delete a slot (own slot only, high-risk)
ae-cli engage-workbench workbench delete --project-id <project_id> --slot-id <slot_id> --yes
```

## Parameters

| Command | Required flags | Notes |
|---|---|---|
| list | `--project-id` / `-p` | read; auto-inits 4 defaults on first access. |
| add | `--project-id`, `--metric-type`, `--date-type` | write; `--order-id` optional (1-4); max 4 slots. |
| update | `--project-id`, `--slot-id`, `--metric-type`, `--date-type` | write; own slot only; `--order-id` optional. |
| delete | `--project-id`, `--slot-id` | high-risk; requires `--yes`; no dry-run; soft-delete. |

- `--metric-type`: `WorkbenchSlotMetricTypeEnum` code (1-12), e.g. 1=PLAN, 2=PUSH_SUCCESS_PERSON, 5=NEW_USER_COUNT.
- `--date-type`: `WorkbenchSlotDateTypeEnum` code (1-13), e.g. 8=LAST_7_DAYS, 10=LAST_30_DAYS, 11=CURRENT.

## Output

- `list`: `data.slots` (array of slot cards: `slot_id`, `metric_code`, `metric_name`, `date_code`, `date_name`, `value`, `order_id`, `status`, ...).
- `add` / `update`: `data.slot` (the created/updated slot card).
- `delete`: `data.success`.

## Decision Rules

- Discover real `slot_id` via `list` first; never invent slot IDs.
- The same `(metric_type, date_type)` combination cannot be added twice for the same user+project.
- `add` fails once the user already has 4 slots; remove one with `delete` first.
- `delete` is `high-risk-write`; it requires `--yes` and does not support dry-run.
