# analysis user-cluster get

Get exact user cluster details after discovery.

Do not use it for fuzzy discovery or member data. Output contains saved cluster metadata/definition for the requested names.

After `user-cluster create` or an update containing `--definition-request`, use this command to observe the automatically started computation; do not trigger `user-cluster refresh`. Until `progress=100` and `refresh_end_time` is not older than `update_time`, `users_num` and member queries may still reflect the previous successful computation. Treat that state as stale data, not as evidence that the new definition was compiled or calculated incorrectly.

The raw backend value is returned under `result`. The response also provides aggregate and per-cluster `computation`, `result_freshness`, and `next_action`. `poll_get` includes an exact capability/input pair; `none` means the latest result is usable. `potentially_stale` with `is_stale=null` means `refresh_end_time` predates `update_time`, but the update may have changed metadata only; inspect the latest update instead of refreshing automatically.

Flags: `--project-id`, `--cluster-names` JSON array.

```bash
ae-cli analysis user-cluster get --project-id <project_id> --cluster-names '["retained_users"]'
```
