# engage-task user-detail export

Export user details for one execution instance of a non-triggered engagement task.

> Capability id: `engage-task.user-detail.export` · Domain: `engage` · Output: asynchronous artifact.

```bash
ae-cli engage-task user-detail export \
  --project-id <project-id> \
  --task-id <task-id> \
  --task-instance-id <task-instance-id> \
  --user-status fail \
  --artifact-format csv
```

`--user-status` accepts English values only. The statuses below follow the task funnel from audience filtering to the final delivery result:

1. `deduplicate` — users removed because the configured push ID is duplicated.
2. `frequency_control` — users removed by the task-level frequency-control rules.
3. `sample` — users excluded by experiment-layer sampling before planned delivery.
4. `push_plan` — users retained in the planned-delivery population after deduplication, frequency control, and sampling.
5. `fatigue_control` — planned users removed by channel-level fatigue-control rules.
6. `push_actual` — users retained in the actual-delivery population after fatigue control.
7. `exp_skip_push` — actual-delivery users intentionally not sent because their experiment control group is configured to skip delivery.
8. `success` — users for whom delivery completed successfully.
9. `fail` — users for whom delivery was attempted but failed. This is the default value.

Use `--task-exec-detail-id` to narrow an instance to one execution detail. Triggered tasks are not supported in this version.
Each artifact contains at most 1,000,000 rows, matching the Hermes task export safety boundary.

The command returns `run_id` and `artifact_id`. Use `ae-cli engage-query run inspect` to inspect progress and `ae-cli engage-query artifact download` to download the completed artifact.
