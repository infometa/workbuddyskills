# analysis run inspect

Inspect an async analysis capability-gateway run returned by export commands.

Use for `analysis adhoc export`, `analysis report-data export`, `analysis dashboard-report-data export`, `analysis bi-panel-page-data export`, and other analysis exports that return `run_id`.

Legacy transport `request_id` values are outside this skill's execution path. This command accepts only the capability-gateway `run_id`; if the caller has only a legacy request ID, report that it cannot be inspected or canceled here.

Input:

- `run_id`: required async run ID returned by the export response.

Use the exact `run_id` from the same export response that supplied the artifact; do not substitute a request ID, invocation ID, path segment, or an older run ID.

```bash
ae-cli analysis run inspect --run-id <run_id>
```

Input sends `run_id`.

Output is the gateway run descriptor with run status, artifact status, and error fields when the run failed. Keep the `run_id` from the same export result; do not invent or reuse it across artifacts.

State interpretation:

- Continue only while run or artifact status is `RUNNING`.
- Treat only run `SUCCEEDED` plus artifact `COMPLETED` as downloadable success.
- Treat run or artifact `FAILED`/`CANCELED` as terminal failure.
- After success, download with `ae-cli analysis artifact download --run-id <run_id> --artifact-id <artifact_id> --output <file>`.

For managed polling and resumability, use `ae-cli analysis run wait --run-id
<run_id> [--output <file>]` instead of scripting an unbounded inspect loop.
