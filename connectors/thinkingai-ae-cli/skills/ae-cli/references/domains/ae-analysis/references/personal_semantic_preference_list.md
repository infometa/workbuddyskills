# personal-semantic-preference list

List the authenticated user's active personal semantic preference catalog for one project.

Use this command once per host, authenticated user, project, and conversation after resolving the project. Keep the returned directory in conversation context for later questions where user-specific wording or preferences may change interpretation.

Command:

```bash
ae-cli personal-semantic-preference list --project-id <project_id>
```

Input uses `project_id` only. Do not add pagination parameters: the backend returns a compact catalog intended for agent context.

Do not use this command for shared knowledge, metadata catalogs, report/dashboard lists, or complete asset discovery. It only returns the current user's personal semantic preferences in the current project.

Output is the gateway envelope. `data.items[]` contains only `id`, `context_type`, `title`, truncated `summary`, limited `keywords`, `resource_ref_count`, distinct `resource_types`, and `revision`; it deliberately omits content, full asset references, heat, and timestamps. `data.returned_count` is at most 200, `data.truncated` says whether entries were omitted, and `data.selection_policy` is `HOT_160_PLUS_RECENT_40`: up to 160 highest-heat items plus up to 40 recently changed items not already selected. The backend may return fewer items to keep the data payload within 64 KiB.

If one returned item is actually adopted to interpret the user's request, call `ae-cli personal-semantic-preference get --project-id <project_id> --id <preference_id> --mark-used` before using its full content. Do not mark an item used when it was only inspected or rejected.
