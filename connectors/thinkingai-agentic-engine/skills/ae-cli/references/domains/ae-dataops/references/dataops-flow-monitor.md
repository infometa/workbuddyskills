---
name: dataops-flow-monitor
version: 1.0.0
description: "Flow execution and monitoring: view execution instances, inspect instance DAGs and task logs, manually execute/stop flows. Trigger keywords: execute flow, running instance, monitor, logs, stop, troubleshoot, instance, flow instance."
metadata:
  requires:
    bins: ["ae-cli"]
---

# DataOps Flow Execution and Monitoring

> **Prerequisites:** Read [`ae-dataops/SKILL.md`](../SKILL.md) for general rules.

Use `dataops_flow` to execute and control flows. Use `dataops_operations` for space-level operations instance search, instance DAG inspection, and task logs.

**Core Concepts:**
- **executeId** — Execution ID returned immediately by `dataops_flow +execute_flow`; useful for stopping before the scheduler instance is available
- **flowInstanceId** — Operations workflow instance ID returned by `dataops_operations +search_flow_instances`; use it for operations detail, task logs, and stop
- **Instance list queries PROD environment by default** (unlike other tools which default to DEV)

---

## Workflow A: Find and View Flow Execution Status

```bash
# Step 1: List/search current-space flows and get flowCode
ae-cli dataops_flow +list_flows --spaceCode "${spaceCode}" --keyword "etl" --pageSize 20

# Optional: find frequently released flows in the last 30 days
ae-cli dataops_flow +list_high_frequency_release_flows --spaceCode "${spaceCode}" \
  --days 30 --topN 10 --status SUCCESS

# Optional: get one-environment overview by exact name or flowCode
ae-cli dataops_flow +get_flow_overview --spaceCode "${spaceCode}" \
  --flowName "etl" --env "PROD"

# Step 2: Search operation instances across the whole space, with statistics
ae-cli dataops_operations +search_flow_instances --spaceCode "${spaceCode}" \
  --keyword "${flowKeyword}" --startDate "${startDate}" --endDate "${endDate}" --pageSize 20

# Step 3: Inspect one instance DAG and task statuses
ae-cli dataops_operations +get_flow_instance_detail --spaceCode "${spaceCode}" \
  --flowCode ${flowCode} --flowInstanceId ${flowInstanceId}
```

---

## Workflow B: Troubleshoot Task Failures

```bash
# Step 1: Inspect one workflow instance and locate the failed task
ae-cli dataops_operations +get_flow_instance_detail --spaceCode "${spaceCode}" \
  --flowCode ${flowCode} --flowInstanceId ${flowInstanceId}

# Step 2: View task detail and logs
ae-cli dataops_operations +get_task_instance_detail --spaceCode "${spaceCode}" \
  --flowCode ${flowCode} --flowInstanceId ${flowInstanceId} \
  --taskInstanceId ${taskInstanceId} --includeLog true

# Step 3: Re-execute after fixing
ae-cli dataops_flow +execute_flow --spaceCode "${spaceCode}" \
  --flowCode ${flowCode}
```

---

## Workflow C: Manual Execution and Stop

```bash
# Manually trigger PROD execution
ae-cli dataops_flow +execute_flow --spaceCode "${spaceCode}" \
  --flowCode ${flowCode}
# Returns executeId

# Monitor recent executions
ae-cli dataops_operations +search_flow_instances --spaceCode "${spaceCode}" \
  --keyword "${flowKeyword}" --startDate "${startDate}" --endDate "${endDate}" --pageSize 20

# Stop execution if necessary (irreversible)
ae-cli dataops_operations +stop_flow_instance --spaceCode "${spaceCode}" \
  --flowCode ${flowCode} --executeId ${executeId}
```

---

## Workflow D: View Flow Structure

```bash
# View agent-friendly flow overview for one environment
ae-cli dataops_flow +get_flow_overview --spaceCode "${spaceCode}" \
  --flowName "etl" --env "DEV"

# The current schedule is included in +get_flow_overview output as "schedule".
```

---

## Command Quick Reference

| Command | Purpose | Key Flags |
|---------|---------|-----------|
| `+list_flows` | List/search current-space flows | `--spaceCode` `[--keyword]` `[--pageNum]` `[--pageSize]` |
| `+list_high_frequency_release_flows` | List flows ranked by release count, not execution count | `--spaceCode` `[--days]` `[--topN]` `[--minCount]` `[--status]` |
| `+get_flow_overview` | DEV/PROD flow overview | `--spaceCode` (`--flowCode` or `--flowName`) `[--env]` |
| `+execute_flow` | Manual PROD execution | `--spaceCode` `--flowCode` `[--baseDate]` |
| `dataops_operations +search_flow_instances` | Search operations workflow instances | `--spaceCode` `[--keyword]` `[--startDate]` `[--endDate]` `[--status]` `[--pageNum]` `[--pageSize]` |
| `dataops_operations +get_flow_instance_detail` | Operations instance DAG and task statuses | `--spaceCode` `--flowCode` `--flowInstanceId` |
| `dataops_operations +get_task_instance_detail` | Operations task detail and optional logs | `--spaceCode` `--flowCode` `--flowInstanceId` (`--taskInstanceId` or `--taskCode` or `--taskName`) `[--includeLog]` |
| `dataops_operations +stop_flow_instance` | Stop a running execution | `--spaceCode` `--flowCode` exactly one of `--executeId` or `--flowInstanceId` |
| `+get_task_params` | DEV task parameter list | `--spaceCode` `--flowCode` `--taskCode` |
| `+update_flow` | Update DEV workflow name and/or remark | `--spaceCode` `--flowCode` `[--flowName]` `[--remark]` |

## Parameter Notes

- **Execution**: `+execute_flow` requires `--spaceCode` and `--flowCode`; `--baseDate` is optional and maps to runtime parameter `bd`. It always runs PROD and returns `action/result/status`; `result` includes `flowCode`, `executeId`, `operationStatus`, `nextAction`, and optional `flowInstanceId`.
- **Stop flow instance**: `dataops_operations +stop_flow_instance` requires `--spaceCode`, `--flowCode`, and exactly one of `--executeId` or `--flowInstanceId`. `--executeId` comes from `dataops_flow +execute_flow`; `--flowInstanceId` comes from `dataops_operations +search_flow_instances`. It returns `success`, `selector`, and selector-specific stop result fields.
- **Flow overview**: `+get_flow_overview` requires `--spaceCode` and either `--flowCode` or exact `--flowName`; `--flowCode` takes precedence. `--env` defaults to `DEV`; use `PROD` to include latest production instance fields when available. It returns `success`, `env`, `resolvedBy`, `flow`, `schedule`, `dag`, and `summary`.
- **Flow update**: `+update_flow` requires `--spaceCode`, `--flowCode`, and at least one of `--flowName` or `--remark`. It returns `action/result/status`; `result` is an array with items containing `flowCode`, `operationStatus`, `nameChanged`, and optional `flowName`.
- **High-frequency release flows**: `+list_high_frequency_release_flows` requires `--spaceCode`; `--days`, `--topN`, `--minCount`, and `--status` are optional. Defaults are `days=30`, `topN=10`, and `status=SUCCESS`. It returns `period`, `filters`, `flows`, `returnedCount`, and `nextAction`; flow items include `rank`, `flowCode`, `flowName`, `releaseCount`, `lastReleaseTime`, and `avgIntervalHours`.
- **Operations instance search**: `dataops_operations +search_flow_instances` requires `--spaceCode`; `--keyword`, `--startDate`, `--endDate`, `--status`, `--pageNum`, and `--pageSize` are optional. `--keyword` fuzzy-matches `flowName` or `flowCode`. `pageNum` defaults to `1`; `pageSize` defaults to `20` and maxes at `100`. It returns `totalCount`, `returnedCount`, `pageNum`, `pageSize`, `hasMore`, `instances`, `statusCounts`, `triggerTypeCounts`, and `ownerCounts`.
- **Task instance detail**: `dataops_operations +get_task_instance_detail` requires `--spaceCode`, `--flowCode`, `--flowInstanceId`, and one selector: `--taskInstanceId`, `--taskCode`, or exact `--taskName`. Prefer `--taskInstanceId` because retries can create multiple instances with the same task code/name. `--includeLog` is optional and defaults to `false`. It returns `success`, `flowInstanceId`, `taskCode`, `taskName`, `taskInstanceId`, `status`, `task`, `taskInstance`, `definition`, and `log` only when requested.
- **env**: `DEV` (development) | `PROD` (production, instance list defaults to PROD)
- **flow list paging**: `+list_flows` requires `--spaceCode`; `--keyword`, `--pageNum`, and `--pageSize` are optional. It returns `flows`, `totalCount`, `returnedCount`, `pageNum`, `pageSize`, and `hasMore`; flow items include `latestProductionInstance` only when available. `pageSize` defaults to `20` and maxes at `100`.
- **Task parameters**: `+get_task_params` requires `--spaceCode`, `--flowCode`, and `--taskCode`; it has no optional flags. It queries DEV and returns `data` as an array. Items include fields such as `paramKey`, `paramType`, `paramDataType`, `paramFrom`, and built-in flags like `isBd`.
- **Task Status**: `success` / `failure` / `running` / `waiting`
