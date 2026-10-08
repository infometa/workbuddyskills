# analysis user-tag update

Update a user tag. Discover the exact `tag_name` first.

Do not use it for ID-file value replacement or to create a missing tag. Supplying `--definition-request` automatically starts recomputation after the definition is updated; do not call `user-tag refresh` afterward. Updating only `--display-name` or `--remark` does not recompute. A schedule-only update changes periodic refresh without starting immediate recomputation. `--auto-refresh-cron` or `--auto-refresh-schedule` can enable periodic refresh directly, including on a previously disabled tag. A successful update means the definition was saved, not that the new result is complete. Record the current `refresh_time` before updating, then poll `user-tag get` until `progress=100` and `refresh_time` advances before using `users_num` or querying members.

The response distinguishes both paths. A definition update returns `computation.triggered_automatically=true`, `result_freshness.is_stale=true`, and normally `next_action=poll_get` with an exact capability/input pair. A display-name/remark-only update returns `computation.status=not_triggered`, `result_freshness.status=fresh`, and `next_action=none`.

Flags: `--project-id`, `--tag-name` required. Optional: `--display-name`, `--definition-request`, `--authenticated-only`, `--remark`, `--zone-offset`, `--enable-auto-refresh`, `--auto-refresh-schedule`, `--auto-refresh-cron`. The tag type comes from `definition_request.type` when the definition changes.

`display_name` is at most 80 characters and `remark` is at most 400 characters. The CLI rejects violations before dispatch. `tag_name` is an existing exact identifier and cannot be renamed by update.

Read `user_tag_models.md` before changing the definition. The backend validates and compiles `definition_request` inside update and refuses to modify the tag if clarification is required.

```bash
ae-cli analysis user-tag update --project-id <project_id> --tag-name user_level --display-name "User Level v2"

ae-cli analysis user-tag update --project-id <project_id> --tag-name user_level --auto-refresh-cron '0 30 2 * * ? *'
```

Omitting scheduling flags preserves the existing enable state and schedule, including during a definition update. Omitting `--zone-offset` preserves the saved tag timezone. `--enable-auto-refresh true` can reuse an existing saved plan; if none exists, provide a new schedule. `--enable-auto-refresh false` disables periodic refresh. Do not combine false with a schedule or pass both schedule forms. Structured schedule fields and timezone rules are described in [user_tag_create.md](user_tag_create.md).

```bash
# Enable daily refresh in one update
ae-cli analysis user-tag update --project-id <project_id> --tag-name user_level --auto-refresh-schedule '{"frequency":"daily","time":"02:30"}'

# Disable periodic refresh
ae-cli analysis user-tag update --project-id <project_id> --tag-name user_level --enable-auto-refresh false
```

Read `user-tag get` after updating to verify `enable_auto_refresh` (1=enabled, 0=disabled), `scheduler_ui_config`, and `cluster_zone_offset`. Schedule-only updates return `computation.status=not_triggered` and `next_action=none`.
