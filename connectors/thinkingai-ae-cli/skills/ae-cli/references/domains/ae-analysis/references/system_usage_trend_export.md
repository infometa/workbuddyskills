# system usage-trend export

Use when the user needs the complete usage-trend result as a cancellable gzip JSONL artifact.

Do not use it for a small inline result; use `ae-cli system usage-trend query` instead.

Command:

```bash
ae-cli system usage-trend export --company-id <company_id> --metric <metric> --start-time <yyyy-MM-dd> --end-time <yyyy-MM-dd> --time-granularity <day_or_week_or_month>
```

Capability id: `system.usage_trend.export`.

The submit response returns the `run_id` for this exact export. Preserve it and poll:

```bash
ae-cli analysis run inspect --run-id <run_id>
```

When the run succeeds, preserve its `artifact_id` and download the same run-scoped artifact:

```bash
ae-cli analysis artifact download --run-id <run_id> --artifact-id <artifact_id> --output <output_path>
```

The artifact format is fixed gzip-compressed JSONL (`.jsonl.gz`); this command intentionally has no `--artifact-format`. Cancel an unfinished export with `ae-cli analysis query cancel --run-id <run_id>`.

The response uses `ok`, `data`, and `meta`. Empty exported data is success when `ok=true`; preserve `request_id` and `invocation_id`.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--metric` | Yes | One supported usage metric; `apollo_token` is not implemented. |
| `--start-time` | Yes | Inclusive start date in `yyyy-MM-dd`. |
| `--end-time` | Yes | Inclusive end date in `yyyy-MM-dd`. |
| `--time-granularity` | Yes | `day`, `week`, or `month`. |
| `--scope` | No | `company` or `project`; project scope requires `--project-ids`. |
| `--project-ids` | No | Project ID JSON array. |
| `--data-type` | No | `all`, `event`, or `user` for project-scoped total event volume. |
| `--request-id` | No | Caller-supplied `cli_<32 lowercase hex>` lifecycle ID; generated when omitted. |
| `--timeout-seconds` | No | Maximum runtime, `1..21600`; default `21600`. |
