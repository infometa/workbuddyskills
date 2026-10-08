---
name: ae-system
version: 1.2.0
description: "AE Agent system administration CLI for root and agent administrators. Use when the user asks to manage Agent members, sandboxes and shared tools, company model visibility/defaults/pricing, usage statistics and exports, cost quotas, balance alerts, IM channels, channel routing, WhatsApp Web linking, or Feishu user bindings. Must use ae-cli system commands, discover real IDs before writes, and never attempt to bypass a permission denial."
---

# ae-system

Use the `system` domain for Agent system administration:

```bash
ae-cli system +<command> [options]
ae-cli system <resource> <action> [options]
```

## Mandatory Rules

- These commands are only for users whose Agent role is `root` or `agent_admin`.
- The te-agent `/api/admin/**` and `/api/cli/channel/v1/**` endpoints are the final authorization boundaries. A member receives a permission error (HTTP 403). Do not retry login or attempt a different endpoint after a 403.
- Run `ae-cli auth login --host <host>` before using this domain. System administration requires a valid user CLI-token session; sandbox identity headers are not an authorization substitute.
- `+npm-install` is the exception that must also run inside a Linux te-agent sandbox because it packages the installed Linux files. It still requires the logged-in user to be `root` or `agent_admin`.
- Discover real IDs with a list command before any update or delete. Never guess a user, sandbox, model, quota rule, or channel ID.
- Before every write, run `--dry-run`, show the target and effect, and obtain explicit user confirmation. The CLI itself prompts only for `high-risk-write`; `--yes` can bypass that prompt and is not a security boundary.
- Use `--dry-run` to inspect method, path, query, and redacted body without executing.
- JSON inputs accept inline JSON, `@file`, or `-` for stdin. Prefer `@file` for channel credentials and other sensitive values.
- Successful output is JSON by default. Use `--format table` only when a human-readable table is more useful.
- After each command, check stderr and `_notice.host_compat`. If present, show the version warning and its update commands before the business result.
- Do not treat an absent ae-cli command as proof that an HTTP endpoint is unreachable. An Agent with Bash/network access can construct requests directly; server authentication, role checks, company isolation, and resource ownership are the actual controls.
- Do not call `DELETE /api/admin/members?openId=...` or `/api/internal/sandboxes/**` through ad-hoc HTTP. They are intentionally excluded from this Skill because other systems own those integration contracts.

## Command Groups

### Members

| Command | Risk | Purpose |
| --- | --- | --- |
| `+list-member-candidates` | read | List TE company users that can be added. |
| `+list-members` | read | List Agent members in the current company. |
| `+add-members` | write | Add one or more TE users, optionally binding a quota rule or creating sandboxes. |
| `+set-member-status` | write | Enable or disable a member. |
| `+set-member-role` | write | Change a non-root member between `agent_admin` and `member`. |
| `+remove-member` | high-risk-write | Remove a non-root member. |
| `+get-member-stats` | read | Get one member's token usage and recent conversation count. |

Examples:

```bash
ae-cli system +list-members --status enabled --page 1 --page-size 20

ae-cli system +add-members \
  --members '[{"openId":"ou_x","loginName":"alice","displayName":"Alice"}]' \
  --create-sandbox true

ae-cli system +set-member-role --user-id <user-id> --role agent_admin
```

`+list-members` filters:

- `--q`: login/display name search.
- `--status`: `all | enabled | disabled`.
- `--page`, `--page-size`: page size is 1-100.
- `--all`: return all matches.
- `--sort-field periodUsedAmount`, `--sort-dir asc|desc`: central usage sort.

`+add-members --members` schema:

```json
[
  {
    "openId": "required",
    "loginName": "optional",
    "displayName": "optional"
  }
]
```

Optional flags are `--rule-id` and `--create-sandbox true|false`.

### Sandboxes

| Command | Risk | Purpose |
| --- | --- | --- |
| `+list-sandboxes` | read | List company sandboxes. |
| `+get-sandbox-config` | read | Read feature status and create/active seat limits. |
| `+batch-create-sandboxes` | write | Create personal sandboxes for 1-100 users. |
| `+update-sandbox` | write | Update a sandbox description. |
| `+set-sandbox-enabled` | write | Enable or disable a sandbox. |
| `+start-sandbox` | write | Start a sandbox container. |
| `+stop-sandbox` | write | Stop a sandbox container. |
| `+list-sandbox-users` | read | List users bound to a sandbox. |
| `+bind-sandbox-user` | write | Bind a member to a sandbox. |
| `+unbind-sandbox-user` | high-risk-write | Remove a sandbox user binding. |
| `+remove-sandbox` | high-risk-write | Delete a sandbox and its bindings. |

Examples:

```bash
ae-cli system +batch-create-sandboxes \
  --user-ids '["<user-id-1>","<user-id-2>"]' \
  --description "Data team"

ae-cli system +set-sandbox-enabled --id <sandbox-id> --enabled true
ae-cli system +bind-sandbox-user --id <sandbox-id> --user-id <user-id>
```

Use Agent database user IDs from `+list-members`, not TE openIds, for sandbox commands.

### Shared Sandbox Tools

| Command | Risk | Purpose |
| --- | --- | --- |
| `+upload-sandbox-tool` | write | Validate, ZIP, and upload an existing tool directory. |
| `+npm-install` | write | Install one exact npm CLI version in a temporary sandbox directory, generate `tool.json`, and upload it. |
| `+list-sandbox-tools` | read | List preset and custom tools for the current company. |
| `+sync-sandbox-tools` | write | Synchronize preset tools from the server manifest. |
| `+get-sandbox-tool-distribution` | read | Read the sandboxes currently receiving one tool. |
| `+set-sandbox-tool-enabled` | write | Enable or disable one registered tool. |
| `+remove-sandbox-tool` | high-risk-write | Delete a fully reclaimed tool registration. |
| `+activate-sandbox-tools` | write | Activate selected commands on selected or all running sandboxes. |
| `+deactivate-sandbox-tools` | write | Remove managed command shims from selected or all running sandboxes. |
| `+refresh-sandbox-tool-status` | write | Refresh observed tool state on target sandboxes. |
| `+list-sandbox-tool-operations` | read | List activation/deactivation history. |

Uploaded tools are registered for the current company with `enabled=false`. Upload does not activate the tool in any running sandbox. Review and enable/activate it through sandbox tool management after upload.

For activate/deactivate/status operations:

```bash
ae-cli system +activate-sandbox-tools \
  --target-mode selected \
  --sandbox-ids '["<sandbox-id>"]' \
  --tool-ids '["<tool-id>"]'
```

- `--target-mode selected` requires 1-50 `--sandbox-ids`; `all-running` forbids them.
- `--tool-ids` contains 1-20 real IDs from `+list-sandbox-tools`.
- `--command-names-by-tool-id` optionally limits an operation to named commands.
- `--expected-tool-snapshots-by-id` carries the version/package/command snapshot returned by the server for optimistic concurrency checks.
- JSON maps accept inline JSON, `@file`, or stdin. Use dry-run and user confirmation before distribution changes.

#### Preferred npm Flow

Run this inside the target Linux te-agent sandbox:

```bash
ae-cli auth login --host <host>
ae-cli system +npm-install --package eslint@9.32.0
```

For a scoped package or a custom shared-tool identifier:

```bash
ae-cli system +npm-install \
  --package @scope/example-cli@1.2.3 \
  --name example-cli
```

Requirements and behavior:

- `--package` must be an exact registry package version. Tags, ranges, URLs, Git sources, npm aliases, and local paths are rejected.
- The installed package must expose at least one `package.json` `bin` entry. Each bin becomes one tool command.
- The default tool name is the unscoped package name. Use `--name` only when a different valid lowercase tool identifier is required.
- npm lifecycle scripts are disabled with `--ignore-scripts` by default. Use `--allow-scripts true` only after reviewing and trusting the package and all transitive dependencies.
- The command calls the admin upload-policy endpoint before starting npm. A disabled feature, expired session, or non-admin role fails before installation.
- Installation uses a temporary prefix with development dependencies omitted. Temporary installation and ZIP files are removed whether upload succeeds or fails.
- npm-created `node_modules/.bin` symlinks are converted to regular executable wrappers in the ZIP. All other symlinks, special files, and links resolving outside the package root are rejected.
- Pure JavaScript Node.js CLIs are the supported baseline. Packages that require native addons, downloaded platform binaries, build tools, system libraries, or lifecycle setup may fail when scripts are disabled or when activated in a different runtime image.
- If lifecycle scripts are necessary, install and upload from the same Linux sandbox image family that will execute the tool. Upload never makes an incompatible native artifact portable.

#### Existing Directory Flow

Use the low-level command when the tool is already installed or assembled:

```bash
ae-cli system +upload-sandbox-tool --path /absolute/path/to/tool-root
```

The directory root must contain exactly one `tool.json`. An external manifest is allowed only when the root has no `tool.json`:

```bash
ae-cli system +upload-sandbox-tool \
  --path /absolute/path/to/tool-root \
  --manifest /absolute/path/to/tool.json
```

Minimal manifest:

```json
{
  "schemaVersion": 1,
  "name": "example-cli",
  "displayName": "Example CLI",
  "description": "Optional description",
  "version": "1.2.3",
  "commands": [
    {
      "name": "example",
      "entry": "node_modules/example-cli/bin/example.js",
      "runtime": "node"
    }
  ]
}
```

Upload contract:

- `name` and command names must start with a lowercase letter and contain only lowercase letters, numbers, `.`, `_`, or `-`, with a maximum length of 64.
- Command names must not replace reserved runtime commands such as `node`, `npm`, `npx`, `bash`, `python`, `git`, `curl`, or `sudo`.
- Every command `entry` must be a regular file under the upload root. Use `runtime: "node"` for JavaScript entry files and `runtime: "native"` only for an executable compatible with the sandbox Linux image.
- Paths must be relative and normalized. Absolute paths, `..`, backslashes, control characters, empty segments, and a `current` path segment are rejected.
- ZIP limits are 50 MB compressed, 500 MB unpacked, 50 MB per file, and 10,000 files. The server publishes only after independently validating the same boundaries.
- Do not pre-create or write `/data/app/te_agent_ta/share/tools` from a sandbox. Sandboxes are read-only for that directory; the authenticated te-agent upload endpoint owns the final write and registration.
- A tool name can be registered only once per company in this first static-version flow. Choose the final name and version before upload.

### Models

| Command | Risk | Purpose |
| --- | --- | --- |
| `+list-system-models` | read | List system models and company visibility. |
| `+set-system-model-enabled` | write | Toggle a system model for the current company. |
| `+get-model-sync-settings` | read | Read the default visibility policy for newly synchronized system models. |
| `+set-model-sync-settings` | write | Update the new-system-model visibility policy. |
| `+get-system-model-price-rules` | read | Read one managed system model's stored pricing snapshot. |
| `+list-company-models` | read | List company models, including disabled models. |
| `+set-company-model-enabled` | write | Toggle a company model for all company users. |
| `+get-default-models` | read | Read the `AE_AGENT` and `AI_QA` default slots. |
| `+set-default-model` | write | Set one default model slot. |
| `+clear-default-model` | high-risk-write | Clear one default model slot. |

Examples:

```bash
ae-cli system +list-system-models
ae-cli system +set-system-model-enabled --model-id <model-id> --enabled false
ae-cli system +set-default-model --model-id <model-id> --biz-type AE_AGENT
```

`--biz-type` is `AE_AGENT | AI_QA` and defaults to `AE_AGENT`. Use the database `id` returned by a model list, not the provider model name.

### Usage

| Command | Risk | Purpose |
| --- | --- | --- |
| `+get-usage-summary` | read | Get token/cost summary for a relative or absolute range. |
| `+get-usage-details` | read | Get paginated usage grouped by user, model, date, or application type. |
| `+get-agent-tool-calls` | read | Get Agent tool-call count for a range, optionally refreshing the cache. |
| `+get-usage-combinations` | read | Drill one parent group into the remaining dimensions. |
| `+export-usage` | read | Stream filtered one-dimension usage groups to CSV. |
| `+export-usage-details` | read | Stream full or drill-down multi-dimension details to CSV. |

Examples:

```bash
ae-cli system +get-usage-summary --days 30
ae-cli system +get-usage-summary --days 30 --refresh true

ae-cli system +get-usage-details \
  --start-date 2026-07-01 \
  --end-date 2026-07-24 \
  --group-by user \
  --page 1 \
  --page-size 20

ae-cli system +get-usage-combinations \
  --start-date 2026-07-01 \
  --end-date 2026-07-24 \
  --parent-dimension user \
  --open-id <open-id>

ae-cli system +export-usage \
  --start-date 2026-07-01 \
  --end-date 2026-07-24 \
  --group-by user \
  --output ./system-usage.csv
```

Summary range:

- Use `--days 1..365`, or provide both `--start-date` and `--end-date`.
- Dates use `YYYY-MM-DD`.
- Do not combine `--days` with an absolute date pair.
- `--refresh true` is available on `+get-usage-summary` and `+get-agent-tool-calls` and bypasses the overview cache.

Details flags:

- `--start-date` and `--end-date` are required.
- `--group-by`: `user | model | date | app_type`.
- Optional filters: `--search`, `--open-id`, `--model-id`, `--model-scope`, `--app-type`.
- `--model-scope` requires `--model-id`.
- `--sort-by`: `totalTokens | cost | share | requestCount`.
- `--sort-dir`: `asc | desc`.

Combination drill-down requires exactly one parent selector:

- `user` → `--open-id` only.
- `model` → `--model-id` and `--model-scope` only.
- `app_type` → `--app-type` only.
- `date` → `--date` only, inside the selected range.

CSV exports require an explicit `--output`. The target is created exclusively: an existing file is never overwritten, and an HTTP or stream failure removes the incomplete file. The JSON result reports the absolute local path, bytes written, server filename, and content type.

### Cost Control

| Command | Risk | Purpose |
| --- | --- | --- |
| `+get-cost-summary` | read | Get company cost, quota, and usage summary. |
| `+get-balance` | read | Get the current model account balance and currency. |
| `+list-over-limit-users` | read | List members over cost or token quota limits. |
| `+get-balance-alert` | read | Get balance alert config and current status. |
| `+set-balance-alert` | write | Enable, update, or disable the balance alert. |
| `+list-quota-rules` | read | List cost/token quota rules. |
| `+create-quota-rule` | write | Create a company or user quota rule. |
| `+update-quota-rule` | write | Update a quota rule. |
| `+remove-quota-rule` | high-risk-write | Delete a quota rule. |
| `+bind-quota-rule-user` | write | Bind a quota rule to a TE user openId. |

Examples:

```bash
ae-cli system +set-balance-alert --enabled true --threshold 100

ae-cli system +create-quota-rule --rule @quota-rule.json
ae-cli system +bind-quota-rule-user --id <rule-id> --open-id <open-id>
```

Quota rule JSON:

```json
{
  "name": "Daily user quota",
  "subjectType": "USER",
  "periodType": "DAY",
  "quotaType": "TOKEN",
  "totalTokens": "10",
  "allowedModels": ["<model-id>"],
  "modelLimits": [
    {
      "modelId": "<model-id>",
      "limitTokens": "5"
    }
  ],
  "openIds": ["<open-id>"]
}
```

Rules:

- `subjectType`: `USER | COMPANY`.
- `periodType`: `DAY | WEEK | MONTH`.
- `quotaType`: `COST | TOKEN`.
- COST uses `budgetAmount`; TOKEN uses `totalTokens`. Token values are expressed in millions.
- `allowedModels` and `modelLimits` are optional according to the server rule type.
- Update accepts a partial rule object.

### Channels

For channel setup, routing, WhatsApp Web linking, or Feishu user binding, read [references/channel-management.md](references/channel-management.md) before taking action. It defines the two confirmation phases and the `ae-cli` plus Feishu OpenAPI MCP workflow.

| Command | Risk | Purpose |
| --- | --- | --- |
| `+list-channels` | read | List all configured channels. |
| `channel get` | read | Read one channel, its verification state, and endpoints. |
| `+create-channel` | write | Create one channel. |
| `+update-channel` | write | Update channel settings, credentials, model, prompt, or enabled state. |
| `+remove-channel` | high-risk-write | Delete a channel, unbind users, and stop its connection. |
| `channel verify` | write | Verify credentials and discover endpoints. |
| `channel routing get` | read | Read one endpoint's group message routing. |
| `channel routing set` | write | Replace one endpoint's group message routing. |
| `channel whatsapp-web status` | read | Read a WhatsApp Web link state and QR data. |
| `channel whatsapp-web start` | write | Start or resume WhatsApp Web QR linking. |
| `channel whatsapp-web unlink` | high-risk-write | Unlink WhatsApp Web and remove stored credentials. |
| `channel binding list` | read | List channel user bindings. |
| `channel binding bind-feishu` | write | Bind one Feishu user. |
| `+bind-feishu-users` | write | Bind 1-100 Feishu users and optionally assign Agents. |
| `channel binding unbind` | high-risk-write | Delete one channel user binding. |
| `channel binding set-agent` | write | Set or clear one binding's private-chat default Agent. |

Use canonical snake_case request fields. The four original commands also accept their legacy camelCase JSON fields for compatibility. Always use `@file` for credentials and batch rosters:

```bash
ae-cli system +create-channel --channel @channel.json
ae-cli system +update-channel --id <channel-id> --channel @channel-update.json
ae-cli system +bind-feishu-users \
  --channel-id <channel-id> \
  --endpoint-id <endpoint-id> \
  --bindings @bindings.json
```

## Permission Errors

A permission response looks like:

```json
{
  "ok": false,
  "error": {
    "type": "permission",
    "message": "..."
  }
}
```

On this response:

1. Do not retry with another admin path.
2. Do not recommend re-login unless the server returned 401 instead.
3. Tell the user that `root` or `agent_admin` is required.

An authenticated `root` or `agent_admin` is still scoped to their own company. The current service checks the database role and company against the session, and audited member, channel, sandbox-tool, and sandbox-management routes apply company/resource ownership checks. Never use that statement as a claim that every unreviewed admin route is safe.

## Transport Status

This is a Transitional domain backed by te-agent `/api/admin/**` and `/api/cli/channel/v1/**`.

- Maintainer: te-agent admin/channel-management routes and `src/commands/te-system/**`.
- Migration target: system and channel Capability Gateways.
- Review date: 2026-10-24.
- Exit condition: migrate after equivalent gateway schema, auth, risk, dry-run, and output contracts are stable.
