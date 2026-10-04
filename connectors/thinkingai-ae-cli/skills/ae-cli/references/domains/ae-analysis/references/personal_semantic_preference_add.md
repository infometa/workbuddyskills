# personal-semantic-preference add

Add one personal semantic preference for the authenticated user in one project.

Use this when the user explicitly asks to save a personal semantic preference, or when the current project task contains an explicit stable statement, correction, or confirmation that should become a reusable current-user preference. A current-user working definition remains eligible even when the same content may benefit other users. A second "save" confirmation is not required after that evidence gate is met, unless the target meaning is ambiguous.

Command:

```bash
ae-cli personal-semantic-preference add --project-id <project_id> --context-type <context_type> --title <title> --summary <summary> --content <content> [--keywords '["keyword"]'] [--resource-refs '[{"resource_type":"report","resource_key":"101","display_name":"Revenue daily report"}]'] [--fresh-until-at "yyyy-MM-dd HH:mm:ss"] [--request-id <id>]
```

Use `preference` for durable interpretation/output preferences, `asset_context` for durable wording or intent bound to exact assets, `experience` for confirmed reusable work methods, and `background` for stable personal context. `--resource-refs` is required and non-empty only for `asset_context`; for every other type it must be absent or empty.

`--resource-refs` accepts 1 to 50 ordered objects. Each object contains exactly `resource_type`, string `resource_key`, and `display_name`; `(resource_type, resource_key)` must be unique. `resource_type` is generic lower snake_case rather than a report-only enum, so events, properties, metrics, tags, clusters, reports, dashboards, data tables, and later asset types share the same shape. Array order is the user's intended priority.

`--request-id` is an idempotency key; omit it for ordinary interactive use and the CLI will generate one.

This command creates only a current-user preference. Do not reject an otherwise valid personal preference merely because the same content may benefit other users, and do not imply that the saved preference is shared authority.

Store only the present working preference. Do not append future governance or lifecycle instructions. Do not use this command for company knowledge, standalone metadata facts, reports, dashboards, transient task details, one-off analysis results, or automatic stale/expired preference handling.

Output is the gateway envelope. `data.preference` contains the full created preference, current revision, and complete ordered `resource_refs`. A separate readback is unnecessary unless a later step needs to refresh the record.
