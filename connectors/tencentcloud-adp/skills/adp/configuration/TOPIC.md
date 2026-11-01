# `adp.jsonc` configuration

Local source of truth, analogous to Wrangler `wrangler.jsonc`. `--env staging` merges `adp.env.staging.jsonc`.

## Schema

`adp init` writes:

```jsonc
{
  "$schema": "./node_modules/@tencentcloudadp/cli/config-schema.json"
}
```

If the file is invalid, the CLI hint is `adp docs config --format json`. That command prints `{ schemaPath }` for the packaged schema (global installs included). Do not invent field names; read that schema.

```bash
adp docs config --format json
adp schema --command dev --format json
```

## What belongs where

| Concern | `adp.jsonc` |
| --- | --- |
| Name, space, region, `app_mode` | top-level |
| Greeting / opening questions | `greeting` |
| App-level role (Standard / workflow) | `role_description` |
| Memory / web search | `memory` / `web_search` |
| Shared KBs | `shared_kb_ids` |
| Agent instructions / model | `agent` (`instructions_file` or `instructions`) |
| Plugin tools | `agent.tools` (`plugin_id` + `tool_id`) |
| Plugins / connectors | `agent.plugin_ids` / `agent.plugins` / `connector_ids` |
| Skill mounts | `agent.skill_ids` (Claw only) |
| Multi-agent collab | `mode.multi_agent.collaboration_mode` |
| Bind an existing workflow | `mode.single_workflow.workflow_id` |

When both are set, `agent.instructions_file` wins: the file is read and the inline `agent.instructions` is ignored. Keep only one of them.

Default-KB **documents** are not JSON fields. Use `adp kb doc import`.

## Sync vs publish

`adp.jsonc` syncs to the **draft** (`ModifyApp` + `ModifyAgent`). `adp deploy` then **publishes** (`CreateRelease`). `adp dev` writes the draft only. `adp chat` needs a published app (AppKey).

Mode details: [../references/app-modes.md](../references/app-modes.md). Product constraints: [../gotchas/TOPIC.md](../gotchas/TOPIC.md).
