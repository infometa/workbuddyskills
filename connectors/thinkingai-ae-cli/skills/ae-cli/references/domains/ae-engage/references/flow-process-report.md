# engage-flow.report.process

Query a process-level flow report through the L3 Capability Gateway.

Mapped command: `ae-cli capability run engage-flow.report.process --input '<json>'`

## Input

- Required: `project_id`, `report_type`.
- Provide at least one of `flow_id` or `flow_uuid`.
- `report_type`: `overview`, `detail`, `exit_detail`, or `push_detail`.
- Optional: `request_id`, `push_language_code`, `data_dim_type`, `start_time`, `end_time`, `show_time_zone`.
- Detail report types require both dates; overview accepts no dates or a complete date pair.

## Example

```bash
ae-cli capability run engage-flow.report.process --input \
  '{"project_id":1,"flow_uuid":"flow_uuid_123","report_type":"overview"}'
```
