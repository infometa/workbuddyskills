# analysis user-tag refresh

Explicitly recompute an existing user tag by exact `tag_name` without changing its definition.

Use this only when an unchanged definition must be run again, such as an explicit retry or a recomputation against changed source data. Do not call it after `user-tag create` or an update containing `--definition-request`; those commands already start computation automatically. Do not use it to refresh one history snapshot. Output means recomputation was submitted, not completed. Poll `user-tag get` and verify the new computation before using `users_num` or querying members.

The response marks this as an explicit trigger: `computation.triggered_by_command=true`, `computation.triggered_automatically=false`, `computation.status=submitted`, and `result_freshness.is_stale=true`. Follow the returned `next_action`, `next_capability_id`, and `next_input` to poll.

Flags: `--project-id`, `--tag-name` required.

```bash
ae-cli analysis user-tag refresh --project-id <project_id> --tag-name user_level
```
