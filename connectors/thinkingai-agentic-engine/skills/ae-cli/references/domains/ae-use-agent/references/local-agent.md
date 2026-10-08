# Local Agent command guide

This guide is included in ae-use-agent; installing ae-agent is optional. Use Node.js 20+
and a local client that can run shell commands and read files.

## Setup and recovery

Run `ae-cli --version`. If the command is missing, obtain the AE host and supported CLI
version from the user's environment administrator. Give the appropriate installation
command with that version substituted; do not install automatically:

```bash
# Customer/public distribution
npm install -g @thinkingai/ae-cli@<supported-version>
# Internal ThinkingData distribution
npm install -g @tant/ae-cli@<supported-version> --registry=https://npm.thinkingdata.cn:3443
```

Use the environment URL supplied by the user or configured in ae-cli; never guess a host.
Keep that original host on every request, including authentication:

```bash
ae-cli auth status --host <original-host>
ae-cli auth login --host <original-host>
ae-cli agent +get-agent-context --help
```

Login is needed only when the session is missing or expired. Let the user complete the
browser login; never request tokens in chat. If the command is unknown, the CLI is too old.
For the public package, `ae-cli update --dry-run` previews host-compatible updates;
perform an update only under the client's existing permissions. Internal builds use the
internal registry above. If the host-supported release lacks this command or endpoint,
ask the environment administrator for a compatible deployment; do not repeatedly update.

## Discover and load

```bash
ae-cli agent +list-agents --q <agent-name> --host <original-host>
ae-cli agent +get-agent-context --id <agent-id> --host <original-host>
```

Default JSON output is `{ "ok": true, "data": ... }`. Check `ok` before reading `data`.
Name search results are in `data.agents`. Match name, scope and description; ask the user
when ambiguous. Search by name instead of assuming an unfiltered list contains every Agent.
An explicit ID can go directly to the context command. Ordinary members can read their
own personal Agents and shared Agents visible to their account; no admin role is required.

Context fields are `data.schema_version`, `data.context_version`, `data.agent.instructions`,
`data.model`, `data.dependencies.skills`, `data.dependencies.mcps` and `data.summary`.
This guide supports schema version 1; stop and obtain matching documentation for other
versions. Use your current client model. An unavailable platform model does not block it.
`availability=available` means visible metadata, not a working local dependency.

## Read required Skill files

For an available Skill, use its `id` and `files` descriptors. No extra list-skills call is
needed. Each descriptor has `executable` and `argv`; pass arguments separately, never as
interpolated shell code. Append `--host <original-host>`. Supported read commands are:

```bash
ae-cli agent +get-skill-content --id <skill-id> --host <original-host>
ae-cli agent +list-skill-references --id <skill-id> --host <original-host>
ae-cli agent +list-skill-scripts --id <skill-id> --host <original-host>
ae-cli agent +list-skill-assets --id <skill-id> --host <original-host>
ae-cli agent +read-skill-reference --id <skill-id> --path <relative-path> --host <original-host>
ae-cli agent +read-skill-script --id <skill-id> --path <relative-path> --host <original-host>
ae-cli agent +read-skill-asset --id <skill-id> --path <relative-path> --output <local-file> --host <original-host>
```

Skill body is in `data.item.content`; directory entries are in `data.items`. Text file
reads return `data.content`. Use a path returned by the corresponding directory listing;
`--path` is relative to references, scripts or assets, without that directory prefix.
All three read commands support `--output <local-file>` to preserve binary bytes. Use a
new workspace file path and inspect scripts before any execution. Check reported versions
against the context and re-fetch if they change. An empty listing does not prove that a
file required by the Skill is unnecessary: report a missing required file and stop that step.

## MCP dependencies and failures

If the user explicitly requests exporting current-user MCP credentials, use:

```bash
ae-cli agent +get-agent-context --id <agent-id> --include-mcp-credentials --host <original-host>
```

This is sensitive output: do not quote it in chat or logs, or commit it. Put the connection
only in the intended local client configuration. Require `data.credentials_included=true`;
its absence means an older server, not success. For each MCP, check `connection_config`:
`exported` supplies `connection_name` and the same `connection` configuration shown in the
current user's MCP market: `type`, `url`, `headers` for remote MCPs, or `type`, `command`,
`args`, `env` for stdio. Header and environment keys are unchanged; system URLs use the AE
host. `credential_expires_at=null` means expiry is not exposed. `unavailable` supplies a safe
`connection_error`. No refresh tokens or platform-internal keys are included. Re-export
after credentials expire or are revoked. Platform managed bridges require the platform
runtime. Do not assume a successful export proves connectivity.


Use `ae-cli agent +mcp-tools --id <mcp-id> --host <original-host>` for platform tool metadata.
For OAuth MCPs only, `ae-cli agent +mcp-auth-status --id <mcp-id> --host <original-host>`
reports platform authentication. Neither establishes a local connection. Reuse an existing
local capability when suitable; otherwise obtain connection setup through the client's
normal credential flow. Do not ask for secrets in chat or claim platform OAuth transfers.

- 401/auth error: log in on the same host and retry once; stop if authentication still fails.
- 403: permission denied; do not refresh repeatedly or require an admin account by default.
- 404 on context: run `ae-cli agent +get-agent --id <agent-id> --host <original-host>`.
  If it also fails, verify the ID/account/host. If it succeeds, verify endpoint deployment
  with the administrator. Raw Agent configuration is not a complete context fallback.
- 409 `invalid_agent_configuration`: ask the Agent owner to repair dependency configuration.
- 500/network error: report the failed step and host; no silent success or fallback.
- Unavailable dependency or file: stop only the step that needs it; explain what is missing.

Never claim the full Agent is ready from prompt loading alone. Context is live metadata,
not a frozen package; re-fetch it for a new task.
