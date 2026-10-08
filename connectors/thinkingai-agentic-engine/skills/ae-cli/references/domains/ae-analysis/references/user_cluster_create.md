# analysis user-cluster create

Create a condition or SQL user cluster directly from an AI-facing definition request.

Do not use it for uploaded-ID clusters or result-derived clusters; use `user-cluster create-id` or `query create-result-cluster`. A successful create automatically starts the initial computation; it does not mean the result is already complete. Do not call `user-cluster refresh` afterward. Poll `user-cluster get` until `progress=100` and `refresh_end_time` is not older than `update_time` before using `users_num` or querying members.

The response reports this directly: `computation.triggered_automatically=true`, `computation.status=submitted`, and `result_freshness.is_stale=true`. Follow `next_action`; when it is `poll_get`, invoke `next_capability_id` with the exact `next_input` returned by the command.

Flags: `--project-id`, `--cluster-name`, `--display-name`, `--definition-request` required. Optional: `--authenticated-only`, `--zone-offset`, `--entity-id`. The cluster type comes from `definition_request.type`.

`cluster_name` is a machine identifier: 1-80 characters, starts with a letter, and contains only letters, digits, or underscores. `display_name` is 1-80 characters. The CLI rejects violations before dispatch.

Read `user_cluster_models.md` before constructing `--definition-request`. Create does not accept `--remark`; set it later with `user-cluster update` when needed.

The backend validates and compiles the definition inside the create operation; if metadata is ambiguous or missing, creation fails without creating the cluster. Condition clusters are saved as mixed-condition clusters (`clusterType=CONDITION`, `clusterSubType=MIX_CONDITION`).

```bash
ae-cli analysis user-cluster create --project-id <project_id> --cluster-name retained_users --display-name "Retained Users" --definition-request '{"type":"condition","conditions":{"relation":"and","items":[{"type":"user","field":{"name":"country","type":"user_property"},"operator":"eq","values":["US"]}]}}'
```
