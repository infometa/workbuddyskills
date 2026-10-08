# engage-task operation-log query

Use this command to query an engagement task's operation records and runtime application logs.

> Capability id: `engage-task.operation-log.query` · Domain: `engage`.

```bash
ae-cli engage-task operation-log query --project-id <project-id> --task-id <task-id>
```

## Parameters

- `--project-id` / `-p`: Required numeric project ID.
- `--task-id`: Required engagement task ID.

## Output

The result contains two arrays:

- `operation_records`: User and system operations such as creation, modification, approval, sending, pausing, and completion. Each item contains `operation_type_name`, `operator_name`, `operate_time`, and optional `target_name`.
- `app_logs`: Runtime application logs for triggered tasks. Each item contains `operation_type`, `operation_type_name`, `operator_name`, and `operate_time`. This array is empty when the task has no runtime application logs.

The task must belong to the supplied project. This is a read-only command and supports `--dry-run`.
