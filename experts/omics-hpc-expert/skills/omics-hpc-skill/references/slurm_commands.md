# SLURM Command References

Detailed option reference for the most common SLURM commands. Consult this document when building commands or explaining output.

---

## `squeue` — Live Queue and Running Jobs

Inspect jobs that are currently pending, running, or otherwise visible in the scheduler queue.

### Common Options

| Option | Description |
|--------|-------------|
| `-u <user_list>` | Show jobs for one or more users |
| `-j <job_id>` | Show a specific job |
| `-p <partition_list>` | Restrict to partitions |
| `-t <state_list>` | Filter by state: `PENDING`, `RUNNING`, `SUSPENDED` |
| `-l` | Long format |
| `-o <format>` | Custom output format |
| `--parsable2` | Pipe-delimited output (no trailing delimiter) |

### Useful Format Strings

```
squeue -o "%.18i %.9P %.30j %.8u %.2t %.10M %.6D %R" -u <username>
```

Fields: `JOBID`, `PARTITION`, `NAME`, `USER`, `ST`, `TIME`, `NODES`, `NODELIST(REASON)`.

### Important Output Fields

- `JOBID`: job identifier
- `PARTITION`: partition / queue
- `NAME`: job name
- `ST`: short state code (`PD`, `R`, `CG`, etc.)
- `TIME`: elapsed time
- `NODES`: allocated or requested node count
- `NODELIST(REASON)`: assigned nodes or pending reason

---

## `sacct` — Historical and Accounting View

Inspect finished jobs and richer accounting information.

### Common Options

| Option | Description |
|--------|-------------|
| `-u, --user=<user_list>` | Jobs for specific users |
| `-j, --jobs=<job(.step)>` | Specific jobs |
| `-S, --starttime=<time>` | Jobs after a start time |
| `-E, --endtime=<time>` | Jobs before an end time |
| `-X, --allocations` | Allocation-level rows only |
| `--format=<fields>` | Control output columns |
| `--parsable2` | Pipe-delimited output |

### Useful Format Strings

```
sacct -j <job_id> --format=JobID,JobName,Partition,Account,State,ExitCode,Elapsed,MaxRSS --parsable2
```

### Important Output Fields

- `State`: terminal state (`COMPLETED`, `FAILED`, `CANCELLED`, `TIMEOUT`, `OUT_OF_MEMORY`)
- `ExitCode`: `return_code:signal` form
- `Elapsed`: total runtime
- `MaxRSS`: peak memory (if accounting is enabled)

---

## `sinfo` — Cluster, Partition, and Node Overview

Inspect partitions and node states.

### Common Options

| Option | Description |
|--------|-------------|
| `-l` | Detailed view |
| `-N` | Node-oriented output |
| `-p <partition>` | Restrict to a partition |
| `-o <format>` | Custom output |

### Common Node State Values

- `idle` — available
- `alloc` — fully allocated
- `mix` — partially allocated
- `down` — unavailable
- `drain` / `drng` — excluded from new work (draining)

### Elastic Auto-Scaling: `dummynode` Placeholder

This cluster operates in elastic auto-scaling mode. Key points when interpreting `sinfo` output:

- **`dummynode`** is a placeholder node configured to allow job submissions when the queue has scaled down to 0 real compute nodes. It is **NOT a real compute node** and its state (`down`, `drain`, etc.) should be **ignored** when assessing cluster health.
- When a queue is idle, `sinfo` may show only `dummynode` with 0 available nodes — this is **normal**, not an error.
- After a job is submitted, the auto-scaling system will automatically provision real compute nodes. The `sinfo` output will then show new nodes appearing.
- Do NOT report `dummynode` status as a problem. Do NOT recommend troubleshooting actions based on `dummynode` being in `down` or `drain` state.

---

## `scontrol` — Detailed Inspection and Management

### Inspection

| Command | Purpose |
|---------|---------|
| `scontrol show job <job_id>` | Full job detail (pending reason, resources, dependencies) |
| `scontrol show node <node>` | Node configuration and state |
| `scontrol show partition <part>` | Partition limits and defaults |

### Job Management

| Command | Purpose |
|---------|---------|
| `scontrol hold <job_id>` | Prevent a pending job from starting |
| `scontrol release <job_id>` | Allow a held job to be scheduled |

> **Note**: For partition/queue/node management (add, delete, modify), use the `tophpc` CLI through the `tophpc-operator` skill. Do not use `scontrol` for infrastructure-level changes.

---

## `sbatch` — Batch Submission

Submit a batch script that runs asynchronously. Options may be on the command line or embedded in the script with `#SBATCH` directives.

### Common Options

| Option | Description |
|--------|-------------|
| `-J, --job-name=<name>` | Job name |
| `-p, --partition=<part>` | Partition |
| `-A, --account=<account>` | Charge account (required on many clusters) |
| `-N, --nodes=<min[-max]>` | Node count |
| `-n, --ntasks=<N>` | Total task count |
| `--ntasks-per-node=<N>` | Tasks per node (common for MPI) |
| `-c, --cpus-per-task=<N>` | CPUs per task |
| `-t, --time=<time>` | Walltime limit |
| `--mem=<size>[units]` | Memory per node |
| `--gres=gpu:<count>` | GPUs |
| `-o, --output=<pattern>` | Stdout file |
| `-e, --error=<pattern>` | Stderr file |
| `-d, --dependency=<spec>` | Job dependency (e.g. `afterok:<id>`, `afterany:<id>`) |
| `-a, --array=<range>` | Job array index range (e.g. `0-9`, `1-100%10`) |

### Output

Successful submission returns: `Submitted batch job <job_id>`.

---

## `srun` — Direct Execution or Job Step Launch

Run a command directly or launch job steps inside a batch allocation.

### Common Options

| Option | Description |
|--------|-------------|
| `-N, --nodes=<N>` | Node count |
| `-n, --ntasks=<N>` | Task count |
| `-c, --cpus-per-task=<N>` | CPUs per task |
| `-p, --partition=<part>` | Partition |
| `-A, --account=<account>` | Charge account |
| `-t, --time=<time>` | Walltime |
| `--gres=gpu:<count>` | GPUs |

---

## `salloc` — Interactive Resource Allocation

Request an interactive allocation and run commands within it.

### Common Options

| Option | Description |
|--------|-------------|
| `-N, --nodes=<N>` | Node count |
| `-n, --ntasks=<N>` | Task count |
| `-c, --cpus-per-task=<N>` | CPUs per task |
| `-p, --partition=<part>` | Partition |
| `-A, --account=<account>` | Charge account |
| `-t, --time=<time>` | Walltime |
| `--mem=<size>` | Memory |
| `--gres=gpu:<count>` | GPUs |

---

## `scancel` — Job Cancellation

Signal or cancel jobs managed by SLURM.

### Common Options

| Option | Description |
|--------|-------------|
| `<job_id>` | Cancel one specific job |
| `-u, --user=<user>` | Restrict to a user |
| `-n, --name=<name>` | Restrict to a job name |
| `-p, --partition=<part>` | Restrict to a partition |
| `-t, --state=<state>` | Restrict to a state (`PENDING`, `RUNNING`) |
| `-s, --signal=<signal>` | Send a specific signal (`SIGTERM`, `SIGKILL`) |

### Safety Guidance

Always preview broad cancellations with `squeue` before executing. Prefer exact `job_id` cancellation whenever possible.
