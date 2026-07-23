# SLURM Job States and Queue Reasons

Consult this guide when interpreting `squeue`, `sacct`, or `scontrol show job` output.

## State Code Quick-Reference Table

| Short code (`squeue` ST) | Full name (`sacct` State) | Meaning |
|---------------------------|---------------------------|---------|
| `PD` | `PENDING` | Waiting for resources or scheduling |
| `R` | `RUNNING` | Currently executing |
| `CG` | `COMPLETING` | Finishing cleanup after execution |
| `CD` | `COMPLETED` | Finished successfully |
| `F` | `FAILED` | Ended with a non-zero exit condition |
| `CA` | `CANCELLED` | Cancelled by user or administrator |
| `TO` | `TIMEOUT` | Killed after reaching walltime limit |
| `NF` | `NODE_FAIL` | Interrupted due to node failure |
| `OOM` | `OUT_OF_MEMORY` | Exceeded memory limit |
| `PR` | `PREEMPTED` | Interrupted by higher-priority work |
| `S` | `SUSPENDED` | Execution paused |

## Common Pending Reasons

These appear in `NODELIST(REASON)` from `squeue` or in `scontrol show job` output.

| Reason | Meaning | Typical fix |
|--------|---------|-------------|
| `Resources` | Insufficient free resources right now | Wait, or reduce request |
| `Priority` | Waiting for higher-priority jobs | Wait |
| `Dependency` | Blocked until dependent jobs complete | Check upstream job status |
| `PartitionTimeLimit` | Requested walltime exceeds partition limit | Shorten `--time` or change partition |
| `QOSMaxCpuPerUserLimit` | Per-user QoS CPU limit reached | Wait for running jobs to finish |
| `AssocGrpCpuLimit` | Account CPU limit reached | Wait or request limit increase |
| `MaxMemPerNode` | Requested memory exceeds node capacity | Reduce `--mem` |
| `ReqNodeNotAvail` | Requested nodes unavailable, drained, or reserved | **In this elastic cluster, this often means no real compute nodes exist yet (only `dummynode`). This is normal — the auto-scaler will provision nodes shortly after job submission. Just wait.** If the job remains pending for an unusually long time (>10 min), then investigate further. |
| `BeginTime` | Job has a future start time (`--begin`) | Wait until begin time |
| `Reservation` | Resources reserved for another reservation | Use correct `--reservation` or wait |
| `InvalidAccount` | Specified account is invalid or missing | Provide correct `--account` |
| `JobHeldUser` | Job held by the user | `scontrol release <job_id>` |
| `JobHeldAdmin` | Job held by an administrator | Contact cluster admin |

## Interpreting Exit Codes

`ExitCode` in `sacct` is shown as `return_code:signal`.

| Example | Meaning |
|---------|---------|
| `0:0` | Program exited successfully |
| `1:0` | Application returned exit code 1 |
| `0:9` | Process received signal 9 (`SIGKILL`) |
| `0:15` | Process received signal 15 (`SIGTERM`) |
| `137:0` | Typically OOM-killed (128 + 9) |

When the state and exit code disagree at first glance, prefer the full accounting context from `sacct` and inspect stdout/stderr logs.

## Troubleshooting Heuristics

| Symptom | Investigation |
|---------|---------------|
| Pending with `Resources` | **First check if the cluster is in scaled-down state** (only `dummynode` visible in `sinfo`). If so, this is normal — the auto-scaler will provision nodes within minutes. If real nodes exist but the job is still pending, then reduce requested nodes/CPUs/memory, or wait. |
| Pending with `ReqNodeNotAvail` | **In this elastic cluster, this is usually normal** — it means no real compute nodes are available yet. Wait for auto-scaling to provision nodes (typically 2-5 minutes). Only investigate further if the job stays pending for an unusually long time (>10 min). |
| Pending with `PartitionTimeLimit` | Shorten `--time` or choose another partition |
| `OUT_OF_MEMORY` | Increase `--mem` or reduce workload memory footprint |
| `TIMEOUT` | Increase `--time` or optimize the job |
| `FAILED` with non-zero exit code | Inspect application logs and submission script |
| `NODE_FAIL` | Retry if appropriate; check cluster health notices (**but note that `dummynode` failures are not real node failures**) |
| `InvalidAccount` | Provide correct `--account` value |
| `Dependency` never resolves | Check if upstream job failed or was cancelled |
| `sinfo` shows only `dummynode` | **NOT a problem.** The cluster is idle and scaled to 0. Submit a job and nodes will be provisioned automatically. |
| `sinfo` shows 0 available nodes | **NOT a problem.** Same as above — this is the normal idle state of an elastic cluster. |
