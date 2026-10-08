# metadata data-table download

> Capability id: `metadata.data_table.download` · Domain: `metadata`.

```bash
ae-cli metadata data-table download --project-id <project_id> --data-table-id <id>
ae-cli metadata data-table download --project-id <project_id> --data-table-id <id> --request-id cli_0123456789abcdef0123456789abcdef --timeout-seconds 120
ae-cli metadata data-table download --project-id <project_id> --data-table-id <id> --output <file>
```

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--data-table-id` | Yes | Data table ID. |
| `--request-id` | No | Optional `cli_<32 lowercase hex>` request ID. |
| `--timeout-seconds` | No | Remote runtime in seconds, 1 to 21600. |
| `--wait` | No | Wait for run `SUCCEEDED` and artifact `COMPLETED`. |
| `--output` | No | Wait, then stream and atomically publish the artifact to this file. |
| `--force` | No | Replace an existing `--output` file atomically; invalid without `--output`. |

Use this command when the user needs an exported data-table artifact. Plain
invocation submits only. `--output` implies `--wait`; resume an interrupted
wait with `ae-cli analysis run wait --run-id <run_id> [--output <file>]`.
Local interruption never cancels the remote run. Do not use this command for
inline data-table metadata; use `metadata data-table get` instead.
