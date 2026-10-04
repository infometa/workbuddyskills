# personal-semantic-preference update

Update one personal semantic preference using optimistic locking.

Use this when the user explicitly asks to change an existing personal preference, or when the current project task provides an explicit stable correction or confirmation that should replace a matching saved current-user preference. A current-user working definition remains eligible even when the same content may benefit other users. First read the matched current item with `personal-semantic-preference get --mark-used` and pass the returned revision as `--expected-revision`.

Command:

```bash
ae-cli personal-semantic-preference update --project-id <project_id> --id <preference_id> --expected-revision <revision> --context-type <context_type> --title <title> --summary <summary> --content <content> [--keywords '["keyword"]'] [--resource-refs '[{"resource_type":"event","resource_key":"$login","display_name":"Login event"}]'] [--fresh-until-at "yyyy-MM-dd HH:mm:ss"] [--request-id <id>]
```

The update replaces all editable fields. Include the full intended `title`, `summary`, `content`, keywords, and asset bindings rather than a partial patch. `asset_context` requires 1 to 50 complete ordered `resource_refs`; other context types cannot contain non-empty refs.

This command updates only the current-user preference. Do not block the update merely because the same content may benefit other users, and do not imply that the saved preference is shared authority.

Keep future governance and lifecycle handling out of the stored content. Do not use this command for shared knowledge, standalone metadata facts, reports, dashboards, transient task details, one-off analysis results, or automatic stale/expired preference handling.

Output is the gateway envelope. `data.preference` contains the full updated preference and new revision. If the revision is stale, read the latest record and ask the user how to merge rather than overwriting silently.
