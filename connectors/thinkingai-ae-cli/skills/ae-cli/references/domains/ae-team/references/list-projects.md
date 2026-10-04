# team +list-projects (List Available Projects)

> **Prerequisite:** Follow the Global AE CLI Rules in [`../SKILL.md`](../SKILL.md).

Domain: **Project discovery**

## Use Cases
- List all projects the current user has access to, sourced from the authentication endpoint.
- Returns an array of `{ projectId, projectName }` objects.
- Use this before `+run-start` when you need to populate `--project-ids` or `--project-names` but don't know the available project IDs.

## Mandatory Rules (MUST)
- Do not guess project IDs or project names. Call `+list-projects` first to discover real values.
- If the user references a project by name, match it against the returned list before passing it to `+run-start`.

## Command
```bash
ae-cli team +list-projects
ae-cli team +list-projects --format table
ae-cli team +list-projects --dry-run
```

## Parameters
| Parameter | Required | Description |
|---|---|---|
| None | — | No parameters required |

## Response Shape
```json
[
  { "projectId": 1, "projectName": "项目A" },
  { "projectId": 2, "projectName": "项目B" }
]
```

## Decision Rules
- When the user wants to start a run and mentions a project by name or says "关联项目", call `+list-projects` first to resolve the correct `projectId`.
- Once project IDs are confirmed in the current conversation, reuse them without calling `+list-projects` again unless the user switches projects.

## Next Steps on Failure
- Empty result: the current account may have no associated projects; confirm account permissions with the administrator.
- Auth error: run `ae-cli auth login`.

## Recommended Chaining
- `+list-projects` → user confirms `projectId` → `+run-start --project-ids '[<id>]'`
