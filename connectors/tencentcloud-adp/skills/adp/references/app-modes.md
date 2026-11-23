# Application modes (`adp init --app-mode`)

Integer enum on `CreateApp` / `adp.jsonc` `app_mode`:

| `app_mode` | Name | Instructions live on | Mount Skills | Typical use |
| ---: | --- | --- | --- | --- |
| 1 | Standard | App-level `role_description` | No | FAQ / knowledge QA. No `agent_id`; `CreateAgent` is rejected. A query that matches no workflow (or knowledge) is answered by the model under `role_description`, not by a fallback workflow — write the fallback behaviour into `role_description`. |
| 2 | Multi-Agent (`adp init` default) | Agent `Instructions` (`ModifyAgent`) | No | Team + handoff / workflow orchestration |
| 3 | Single workflow | App-level role description | No | Fixed pipeline, lowest token |
| 4 | Claw | App-level role description | **Yes** | Autonomous coding / general agent |

## Switching

- `1` / `2` / `3` can switch among themselves via `ModifyApp` / `adp app update` (mode change is not a v1 flag; create a new app if unsure).
- **Claw (`4`) is isolated.** Switching an existing app into or out of Claw requires a **new** app.

## Two layers (easy to mix up)

1. **Application mode** = `app_mode` on the app (this table).
2. **Collaboration sub-mode** = only inside `app_mode=2`. Set `mode.multi_agent.collaboration_mode` in `adp.jsonc`: `1` free-handoff, `2` workflow orchestration, `3` Plan-and-Execute. That is **not** `--app-mode`.

## AgentSpec

- Claw (`4`) only releases with a Claw-scene model: `adp models --scene 18 --space-id <id> --format json`. Any other `agent.model.model_id` fails `adp deploy` with `4600005`. Details: [pitfalls.md](pitfalls.md).
- `adp.jsonc` `agent.skill_ids` is meaningful for Claw (`4`). For mode `2`, leave it empty; the platform rejects skill mounts.
- `agent.tools` is `{ plugin_id, tool_id }` (optional `tool_source`: 0 plugin / 1 workflow). `agent.plugin_ids` / `agent.plugins` enable plugins; `agent.connector_ids` are connectors (same `PluginList` on the wire). Do not stuff connector ids into `plugin_ids`.
- Greeting, memory, web search, shared KBs, and Claw team prompt live on the **app**, not the agent: `greeting`, `memory`, `web_search`, `shared_kb_ids`, `mode.claw`.
- **Claw sub-agents.** `app_mode` 4 has 1 main agent (`AgentProfile.Role=0`, stored as `adp.jsonc` `agent` / `agent_id`) and up to 19 sub-agents (`Role=1`). `CreateAgent` with `Role=0` is idempotent and returns the existing main agent (`AgentAlreadyExists` from the CLI). Add a sub-agent with `adp agent create --role 1` (`--description` is when the main agent should delegate). `ParentAgentId` is read-only on list/get. `mode.claw.team_enabled` and `mode.claw.team_prompt` turn on optional team collaboration; the default is one-way delegation from the main agent. Details: [../create/TOPIC.md](../create/TOPIC.md).
- Default-KB documents: `adp kb doc import --file …` (KB id defaults to `app_id`). Create shared KBs with `adp kb create`; bind them with `shared_kb_ids`.
- **`shared_kb_ids` is full-overwrite.** Omitting the key leaves bindings untouched;
  `[]` unbinds everything; a list replaces the whole set. Always read `adp app get`
  first and push the complete target set. Ids are plain numeric strings, no `kb_`
  prefix. Details: [pitfalls.md](pitfalls.md).
- Sub-agents are not Tools. Never put a child `agent_id` into a plugin/tool list.
- Binding an existing canvas workflow: `mode.single_workflow.workflow_id`. `adp workflow`
  (same profile keys on the public cloud and the independent site) can also list, get, deploy, enable, disable, export, import, remove, and async-run (`workflow run`, mode 3 with an entry workflow)
  canvases; `adp app export` / `adp app import` move a released app as a package. The default export includes workflows, connectors, knowledge bases, agents, and skills (`--include` / `--exclude` / `--no-kb` narrow it; a selected workflow keeps the connectors and knowledge bases it references). A mode 3 copy whose package has no workflow files still needs its entry workflow exported, imported, and bound — see [../create/TOPIC.md](../create/TOPIC.md) §Workflows.
