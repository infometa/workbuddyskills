# engage-flow.report.node-overview

Query the overview report for all nodes in a flow through the L3 Capability Gateway.

Mapped command: `ae-cli capability run engage-flow.report.node-overview --input '<json>'`

## Input

- Required: `project_id`, `start_time`, `end_time`.
- Provide at least one of `flow_id` or `flow_uuid`.
- Optional: `request_id`, `push_language_code`, `data_dim_type`, `show_time_zone`.
- Dates use `yyyy-MM-dd`; `data_dim_type` is `uv` or `pv`.

## Example

```bash
ae-cli capability run engage-flow.report.node-overview --input \
  '{"project_id":1,"flow_uuid":"flow_uuid_123","start_time":"2026-04-01","end_time":"2026-04-07"}'
```
