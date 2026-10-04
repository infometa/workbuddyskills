# analysis user-tag get

Get exact user tag details after discovery.

Do not use it for fuzzy discovery, member data, or history statistics. Output contains saved tag metadata/definition for the requested names.

After `user-tag create` or an update containing `--definition-request`, use this command to observe the automatically started computation; do not trigger `user-tag refresh`. For create, wait until `progress=100` and `refresh_time` is present. For a definition update, record the previous `refresh_time` first and wait until `progress=100` and `refresh_time` advances. Until then, `users_num` and member queries may still reflect the previous successful computation; treat that as stale data, not as evidence that the new definition was compiled or calculated incorrectly.

The raw backend value is returned under `result`. The response also provides aggregate and per-tag `computation`, `result_freshness`, and `next_action`. `poll_get` includes an exact capability/input pair; `none` means the latest result is usable. `potentially_stale` with `is_stale=null` means `refresh_time` predates `update_time`, but the update may have changed metadata only; inspect the latest update instead of refreshing automatically.

Flags: `--project-id`, `--tag-names` JSON array.

```bash
ae-cli analysis user-tag get --project-id <project_id> --tag-names '["user_level"]'
```
