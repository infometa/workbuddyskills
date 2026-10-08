---
name: ae-team
version: 1.0.0
description: "AE/TE/ThinkingEngine/ThinkingAI ae-cli manual for AI Agent Team tasks: managing teams (list, create, update, delete, AI-generate, templates) and executing TeamRuns (start, chat, cancel, reply, result, artifacts). Use when the user asks to find a team, run a team task, check run status, retrieve results or artifacts, or set up multi-agent workflows. Must use ae-cli, read the matching references/<command>.md before composing commands, and never guess team IDs, run IDs, config structures, or parameter formats."
---

# ae-team

> **CRITICAL — Before running any `+<command>` command, you MUST first read the corresponding `references/<command>.md`.** The reference filename equals the command name without the leading `+`, for example `+run-start` → `references/run-start.md`.
> **CRITICAL — Never guess team IDs, run IDs, or config JSON structures.** Always use `+list` or `+list-templates` to discover real resources first.
> **CRITICAL — For the core Agent workflow (find → start → poll → artifacts), follow Workflow A in the Typical Workflows section below.**

## Global AE CLI Rules

AE CLI (`ae-cli`) is the command-line tool for the AE / TE / ThinkingEngine analysis platform.

Global parameters:

| Parameter | Description |
|---|---|
| `--format <json\|table>` | Output format. Default is JSON. |
| `--jq <expr>` | jq filter expression for JSON output. |
| `--host <url>` | Override the active AE host. Available on every command and may be placed after the subcommand, e.g. `ae-cli team +<command> --host <url>`. |
| `--yes` | Skip confirmation for `high-risk-write` (delete) operations. |
| `--dry-run` | Show request details without executing. |

Output and errors:
- Successful commands return machine-readable JSON by default. Envelope may include optional `_notice.host_compat`.
- Failed commands return `{ "ok": false, "error": { "type": "...", "message": "...", "hint": "..." } }` and exit non-zero.
- **CRITICAL — Host compat (do this first):** If stderr or `_notice.host_compat` has a version warning, open the user reply with ⚠️ and **quote `npm i -g` / `npx skills add` (or update-cluster) lines verbatim**, then list projects/results. Never omit when summarizing. Soft tip; `ok: true` may still include the notice.

Safety constraints:
- Read commands (`+list`, `+list-templates`, `+list-projects`, `+run-result`, `+run-artifacts`, `+ai-generate`) can execute directly once required IDs are known.
- Ordinary `write` commands require explicit user intent but no CLI confirmation. Only `high-risk-write` commands use the confirmation gate and may receive `--yes` after explicit user authorization.
- Never invent team IDs, run IDs, `agentId` values, `mcpServerIds`, `skillIds`, `knowledgeBaseIds`, project IDs, or any resource identifiers. Discover them with list commands or accept them from the user.

## When to Use

Use `ae-team` for all AI Agent Team work:

- **Team management**: list available teams, create/update/delete a team, generate a team config draft with AI, browse templates.
- **TeamRun execution**: start a run, interact in chat mode, cancel a run, reply to a waiting run, poll result until completion, retrieve artifacts.

If the user's intent is data analysis, audience management, metadata governance, or DataOps, switch to `ae-analysis` / `ae-dataops` / `ae-engage`.

## Command Format

```bash
ae-cli team +<command> [options]
```

All commands live under the `team` service. Quick help:

```bash
ae-cli team --help
ae-cli team +list --help
ae-cli team +run-start --help
```

## Tool Groups (13)

### Team Management (7)

- `+list` ([doc](references/list.md)) — list all visible teams
- `+create` ([doc](references/create.md)) — create a new team with a TeamConfig
- `+update` ([doc](references/update.md)) — patch one or more fields of an existing team
- `+delete` ([doc](references/delete.md)) — delete a team (409 if runs are active)
- `+ai-generate` ([doc](references/ai-generate.md)) — AI-generate a team config draft from a goal description
- `+list-templates` ([doc](references/list-templates.md)) — browse built-in team templates
- `+list-projects` ([doc](references/list-projects.md)) — list projects available to the current user

### TeamRun Execution (7)

- `+run-start` ([doc](references/run-start.md)) — start a new TeamRun
- `+run-watch` ([doc](references/run-watch.md)) — stream a TeamRun via SSE (preferred over polling)
- `+run-chat` ([doc](references/run-chat.md)) — chat with a team (multi-turn, auto-resume)
- `+run-cancel` ([doc](references/run-cancel.md)) — cancel a running TeamRun
- `+run-reply` ([doc](references/run-reply.md)) — reply to a run in `waiting_user` state
- `+run-result` ([doc](references/run-result.md)) — get the full result of a TeamRun (fallback polling)
- `+run-artifacts` ([doc](references/run-artifacts.md)) — list artifacts produced by a TeamRun

## TeamRun Status Reference

| Status | Description |
|---|---|
| `pending` | Queued, waiting to start |
| `running` | Actively executing |
| `waiting_user` | Paused — `+run-watch` exits with code 2; read `pendingQuestion` from stdout, present to user, then call `+run-reply` |
| `waiting_approval` | Paused — waiting for approval |
| `paused` | Manually paused |
| `completed` | Finished successfully |
| `failed` | Execution failed |
| `cancelled` | Cancelled by user |

Terminal statuses: `completed`, `failed`, `cancelled`. Poll `+run-result` until one of these is reached.

## Typical Workflows

### Workflow A — Start an existing team and wait for results

```bash
# 1. Discover available teams
ae-cli team +list

# 2. (Optional) Discover project IDs if needed
ae-cli team +list-projects

# 3. Start a run
ae-cli team +run-start --team-id <team_id> --input "分析上周用户留存数据"

# 4. Stream until done (blocks; no polling needed)
ae-cli team +run-watch --id <run_id>
# exit 0 → completed/partial_success → go to step 5
# exit 1 → failed/cancelled → inspect errorMessage in output, report to user
# exit 2 → waiting_user → go to step 4a

# 4a. Handle waiting_user: read pendingQuestion from stdout, get user's answer, reply, re-watch
ae-cli team +run-reply --id <run_id> --input "<user_answer>"
ae-cli team +run-watch --id <run_id>   # repeat until exit 0 or 1

# 5. Retrieve artifacts
ae-cli team +run-artifacts --id <run_id> --include-content true
```

### Workflow B — AI-generate a config, then create and run

```bash
# 1. Generate a draft config
ae-cli team +ai-generate --prompt "需要一个分析用户行为并自动生成留存报告的团队"

# 2. Create the team (paste / adjust the returned config)
ae-cli team +create --name "留存分析团队" --config '<config_json>'

# 3. Start a run
ae-cli team +run-start --team-id <new_team_id> --input "分析本月留存"
```

### Workflow C — Multi-turn chat

```bash
# First turn
ae-cli team +run-chat --team-id <team_id> --input "帮我分析DAU趋势"

# If run status is waiting_user, reply:
ae-cli team +run-reply --id <run_id> --input "请重点分析周末下降原因"

# Continue same session
ae-cli team +run-chat --team-id <team_id> --session-id <session_id> --input "给出优化建议"
```

### Workflow D — Use a template to create a team

```bash
# 1. Browse templates
ae-cli team +list-templates --locale zh

# 2. Create from a template's config
ae-cli team +create --name "我的分析团队" --config '<template_config>'
```

## Quick Verification

```bash
ae-cli team --help
```
