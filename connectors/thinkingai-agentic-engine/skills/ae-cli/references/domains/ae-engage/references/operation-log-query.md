# engage-flow operation-log query

Use this command to query aggregated operation records and application logs for a flow canvas.

> Capability id: `engage-flow.operation-log.query` · Domain: `engage`.

```bash
ae-cli engage-flow operation-log query --project-id <project-id> --flow-id <flow-id>
```

The result contains `operation_record_list` and `app_log_list`, grouped by flow version.
