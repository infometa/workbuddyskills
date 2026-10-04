# analysis run wait

Resume client-side waiting for an asynchronous run and optionally download its
completed artifact.

Use this after an export was submitted without `--wait`, or when a previous
wait was interrupted, detached, reached its client or server deadline, or
stopped after persistent transient network failures. Do not use it for
synchronous `run` results, and do not treat it as a cancellation command.

```bash
ae-cli analysis run wait --run-id <run_id> [--wait-timeout-seconds <n>] [--output <file>] [--force]
```

Input:

- `--run-id`: exact run ID returned by the original async export.
- `--wait-timeout-seconds`: optional local wait bound, `1..21600`; default
  `600`. Expiry does not cancel the remote run.
- `--output`: optional destination. When present, download begins only after
  run `SUCCEEDED` and artifact `COMPLETED`.
- `--force`: optional atomic replacement of an existing `--output`; invalid
  without `--output`.

The command polls with repeated short inspect requests and internal adaptive
backoff. Local waiting stops at the earlier of `--wait-timeout-seconds` and the
server lifecycle deadline, with a short artifact-materialization grace. Ctrl-C
or a local wait failure never cancels the remote run. The error returns the
latest lifecycle state plus `remote_run_canceled=false` and `resume_command`.
Use `analysis query cancel --run-id <run_id>` only when cancellation is
explicitly intended.

Without `--output`, the response is the successful terminal run descriptor.
With `--output`, success additionally guarantees a complete atomically
published local file and returns `output_path`, `bytes`, and content headers.
Run/artifact failure, unknown protocol states, 404, or authorization failure
returns a non-zero structured error; do not turn those outcomes into success.
