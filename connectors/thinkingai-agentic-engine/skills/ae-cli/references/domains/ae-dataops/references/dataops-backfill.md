---
name: dataops-backfill
version: 1.0.0
description: "Backfill job lifecycle: discover eligible PROD flows, create or update drafts, delete jobs, run jobs, inspect plans, stop running jobs, and rerun complete jobs."
metadata:
  requires:
    bins: ["ae-cli"]
---

# DataOps Backfill Jobs

> **Prerequisites:** Read [`ae-dataops/SKILL.md`](../SKILL.md) for authentication, output, and safety rules.

A backfill job is a persistent operations object that runs one PROD task flow for multiple base dates. It is not a single manual flow execution and is not a retry of an existing failed flow instance.

## Lifecycle

### 1. Discover an eligible PROD flow

```bash
ae-cli dataops_operations +list_backfill_flows --spaceCode "${spaceCode}"
```

Use only a returned flow whose `completeDataInfo.canRun` is true. When `completeDataInfo.hasSt` is true, pass `--stTime` while creating the job.

### 2. Create a draft

Always pass the backfill date range. For manual selection, also pass `--completeDates`; every selected date must be inside that inclusive range.

```bash
# Range mode
ae-cli dataops_operations +create_backfill_job --spaceCode "${spaceCode}" \
  --jobName "August backfill" --flowCode ${flowCode} \
  --startDate "2026-08-01" --endDate "2026-08-07"

# Custom-date mode
ae-cli dataops_operations +create_backfill_job --spaceCode "${spaceCode}" \
  --jobName "Selected dates" --flowCode ${flowCode} \
  --startDate "2026-08-01" --endDate "2026-08-07" \
  --completeDates '["2026-08-01","2026-08-03"]'
```

Creation returns a `DRAFT` job and does not run it. Defaults are `jobType=TASK_ALL`, `failureStrategy=END`, `parallel=true`, `reverse=false`, `step=1`, and `unit=DAY`. For `TASK_ONLY`, `TASK_PRE`, or `TASK_POST`, also pass `--startNode`.

### 3. Update a draft when needed

Update is a complete replacement, not a partial patch. Inspect the DRAFT job first, then pass `--jobId`, `--jobName`, `--flowCode`, and the complete date and strategy configuration just as for creation. Updating does not run the job.

```bash
ae-cli dataops_operations +update_backfill_job --spaceCode "${spaceCode}" \
  --jobId ${jobId} --jobName "Revised August backfill" --flowCode ${flowCode} \
  --startDate "2026-08-01" --endDate "2026-08-10" \
  --failureStrategy END --parallel true --reverse false
```

### 4. Run the draft explicitly

```bash
ae-cli dataops_operations +run_backfill_job --spaceCode "${spaceCode}" \
  --jobId ${jobId}
```

### 5. Search jobs and inspect plans

```bash
ae-cli dataops_operations +search_backfill_jobs --spaceCode "${spaceCode}" \
  --status "RUNNING,FAIL,SUCCESS" --pageNum 1 --pageSize 20

ae-cli dataops_operations +get_backfill_job_detail --spaceCode "${spaceCode}" \
  --jobId ${jobId}
```

Detail returns the job and its plans together. A draft has an empty plan list.

### 6. Stop, rerun, or delete

Stopping affects every unfinished plan in the running job. Inspect the job, preview the request, obtain explicit confirmation, and then pass `--yes`.

```bash
ae-cli dataops_operations +stop_backfill_job --spaceCode "${spaceCode}" \
  --jobId ${jobId} --dry-run
# After explicit confirmation, execute the same target; the CLI prompts before dispatch.
ae-cli dataops_operations +stop_backfill_job --spaceCode "${spaceCode}" \
  --jobId ${jobId}
```

Rerun applies to every plan only when the job is `FAIL` or `STOP`. A `SUCCESS` job cannot be rerun. Rerun reuses the same job and does not create a new backfill job. The CLI does not support rerunning only failed plans.

```bash
ae-cli dataops_operations +rerun_backfill_job --spaceCode "${spaceCode}" \
  --jobId ${jobId} --dry-run
ae-cli dataops_operations +rerun_backfill_job --spaceCode "${spaceCode}" \
  --jobId ${jobId}
```

Deletion is high-risk. The server accepts only supported `DRAFT`, `FAIL`, or `SUCCESS` jobs. Inspect the exact target and preview the scoped request before confirmation; the CLI sends only `spaceCode` and `jobId` and does not pre-query or guess state.

```bash
ae-cli dataops_operations +delete_backfill_job --spaceCode "${spaceCode}" \
  --jobId ${jobId} --dry-run
ae-cli dataops_operations +delete_backfill_job --spaceCode "${spaceCode}" \
  --jobId ${jobId}
```

## Command Reference

| Command | Purpose | Flags |
|---|---|---|
| `+list_backfill_flows` | List eligible PROD flows | `--spaceCode` |
| `+create_backfill_job` | Create a draft | `--spaceCode` `--jobName` `--flowCode` `--startDate` `--endDate`; optional in-range `--completeDates`, scope, failure, parallel, order, and ST flags |
| `+update_backfill_job` | Replace a DRAFT job's complete configuration | `--spaceCode` `--jobId` `--jobName` `--flowCode` and the same complete configuration as create |
| `+delete_backfill_job` | Delete a supported job | `--spaceCode` `--jobId`; high-risk, requires confirmation or `--yes` |
| `+run_backfill_job` | Run a draft | `--spaceCode` `--jobId` |
| `+search_backfill_jobs` | Search jobs | `--spaceCode` plus optional keyword, date, type, status, owner, sort, and paging filters |
| `+get_backfill_job_detail` | Get job and plans | `--spaceCode` `--jobId` |
| `+stop_backfill_job` | Stop a running job | `--spaceCode` `--jobId`; high-risk, requires confirmation or `--yes` |
| `+rerun_backfill_job` | Rerun the complete job | `--spaceCode` `--jobId` |

Statuses are `DRAFT`, `RUNNING`, `STOP`, `FAIL`, `SUCCESS`, and `READY_STOP`. Range units are `DAY`, `WEEK`, and `MONTH`. Custom dates must be a non-empty JSON array of unique `yyyy-MM-dd` strings inside the configured date range.

## Transport Status

Transition status: transitional

Owning module: Gaia operations

Current transport: DataOps CLI REST

Covered tools: `operations_list_backfill_flows`, `operations_create_backfill_job`, `operations_update_backfill_job`, `operations_delete_backfill_job`, `operations_run_backfill_job`, `operations_search_backfill_jobs`, `operations_get_backfill_job_detail`, `operations_stop_backfill_job`, and `operations_rerun_backfill_job`

Gateway target: TBD after the DataOps operations Capability Gateway schema review

Review after: 2026-11-20

Exit condition: Migrate these commands after Gaia exposes equivalent capabilities and the command contract tests pass against the Capability Gateway transport.
