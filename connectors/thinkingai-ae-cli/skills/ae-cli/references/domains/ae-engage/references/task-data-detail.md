# engage-task.task-data.detail

Query a task detail report through the L3 Capability Gateway.

Mapped command: `ae-cli engage-task data-detail query`

Capability ID: `engage-task.task-data.detail`

Required input: `project_id`, `task_id`, `detail_type`, `start_time`, `end_time`. `detail_type` is `time`, `instance`, or `instance_daily`; the last form also requires `task_instance_id`.

```bash
ae-cli engage-task data-detail query \
  --project-id 1 \
  --task-id task_123 \
  --detail-type time \
  --start-time 2026-04-01 \
  --end-time 2026-04-07
```
