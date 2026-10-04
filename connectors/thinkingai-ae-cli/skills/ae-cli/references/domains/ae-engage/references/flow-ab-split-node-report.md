# engage-flow.report.ab-split-node

Query an AB split node report through the L3 Capability Gateway.

Mapped command: `ae-cli capability run engage-flow.report.ab-split-node --input '<json>'`

## Input

- Required: `project_id`, `report_type`, `node_uuid`, `start_time`, `end_time`.
- Provide at least one of `flow_id` or `flow_uuid`.
- `report_type` is `overview` or `detail`.
- Optional: `request_id`, `push_language_code`, `indicators_uuid`, `show_time_zone`.

## Example

```bash
ae-cli capability run engage-flow.report.ab-split-node --input \
  '{"project_id":1,"flow_uuid":"flow_uuid_123","node_uuid":"node_123","report_type":"overview","start_time":"2026-04-01","end_time":"2026-04-07"}'
```
