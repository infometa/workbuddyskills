# engage-task.task-data.metric-detail

Query a task metric detail report through the L3 Capability Gateway.

Mapped command: `ae-cli engage-task effect query`

Capability ID: `engage-task.task-data.metric-detail`

Required input: `project_id`, `task_id`, `start_time`, `end_time`. Optional input includes `request_id`, `push_language_code`, `metric_id_list`, `group_type`, and `show_time_zone`.

```bash
ae-cli engage-task effect query \
  --project-id 1 \
  --task-id task_123 \
  --start-time 2026-04-01 \
  --end-time 2026-04-07 \
  --metric-id-list '["metric_1"]'
```
