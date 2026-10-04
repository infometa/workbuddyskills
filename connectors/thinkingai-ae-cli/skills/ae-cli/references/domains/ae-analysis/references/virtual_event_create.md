# analysis-meta virtual-event create

Use when the user needs to create a virtual event from events and filters.

Do not use it for super-event creation.

Before constructing `--events` / `--filter`, validate the available events and properties with `analysis-meta event list` and `analysis-meta property list` in the same `project_id`.

Command:

```bash
ae-cli analysis-meta virtual-event create --project-id <project_id> --event-name ta@demo --event-desc demo --events '[{"event_name":"purchase"}]'
ae-cli analysis-meta virtual-event create --project-id <project_id> --event-name ta@demo2 --event-desc demo --remark demo --events '[{"event_name":"add_to_cart","filter":{"relation":"and","items":[{"field":{"name":"country","type":"user_property"},"operator":"eq","values":["US"]}]}}]' --override true
ae-cli analysis-meta virtual-event create --project-id <project_id> --override false --payload '{"event_name":"ta@qualified_purchase","event_desc":"Qualified purchase","rule":{"events":[...],"filter":{...}}}'
ae-cli analysis-meta virtual-event create --dry-run
```

Capability id: `metadata.virtual_event.create`.

Input sends `project_id`, `override`, and `payload`. When typed flags are used, ae-cli builds `payload` from `event_name`, `event_desc`, `remark`, and `rule.events/filter`.

Output data contains `v_event_id` and `event_name`. Use the returned `v_event_id` for `virtual-event get` or `virtual-event delete`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--override` | No | Whether to override an existing virtual event rule. |
| `--payload` | No | Full virtual-event DTO: `event_id?`, `event_name`, `event_desc?`, `remark?`, `rule` (`events` plus optional common `filter`), `replace_remark?`, `replace_suggestion?`. Common header fields are server-owned and must be omitted. |
| `--event-name` | No | Virtual event name. Must start with `ta@`. Required when `--payload` is omitted. |
| `--event-desc` | No | Virtual event display name. Required when `--payload` is omitted. |
| `--remark` | No | Optional virtual event remark. |
| `--events` | No | JSON array of `{event_name,event_desc?,filter?}`. Each filter uses `{relation:'and|or',items:[{field:{name,type?},operator,values?}]}`. Required when `--payload` is omitted. |
| `--filter` | No | Optional global AI-facing filter with the same `relation/items` shape. Raw `taFilters`, `junctionKind`, and `calcuSymbol` are rejected. Referenced properties must come from `analysis-meta property list`. |

## Decision Rules
- `events` / `filter` must not be handwritten by intuition alone; they must match real metadata in the same project.
- Use snake_case `event_name`; do not pass the legacy `eventName` spelling.
- Before calling `event list` / `property list`, read the corresponding reference documents.
- For first validation, pass only required typed parameters: `--project-id`, `--event-name`, `--event-desc`, and `--events`.
- Use `--payload` only when an exact virtual-event rule DTO is already available.
- This is an ordinary write operation; execute it without the high-risk confirmation flag.

## Recommended Chain
- `analysis-meta event list` -> `analysis-meta property list` -> `analysis-meta virtual-event create`
