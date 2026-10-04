# engage-task.task-data.experiment-report

Query a task experiment report through the L3 Capability Gateway.

Mapped command: `ae-cli capability run engage-task.task-data.experiment-report --input '<json>'`

Required input: `project_id`, `task_id`, `report_type`, `start_time`, `end_time`. `report_type` is `overview` or `detail`.

```bash
ae-cli capability run engage-task.task-data.experiment-report --input '{"project_id":1,"task_id":"task_123","report_type":"overview","start_time":"2026-04-01","end_time":"2026-04-07"}'
```
