# agent +get-agent-context

Read Agent instructions and dependency metadata for execution in a local client.
This differs from `+get-agent`, which returns the editable Agent configuration.

```bash
ae-cli agent +get-agent-context --id <agent-id>
```

Resolve names with `agent +list-agents`; ask the user to choose when names are ambiguous.
The only required flag is `--id`. The command is read-only. `--host` and `--dry-run`
follow the global CLI rules; dry-run previews the request without checking availability.

The result contains `schema_version`, `context_version`, `agent` (including
`instructions`), `model`, `dependencies.skills`, `dependencies.mcps`, `summary`, and `usage`.
Use the client's current model. Platform model defaults are reported, not resolved or applied.

Dependency `availability=available` means visible metadata, not local readiness.
Unavailable references remain in the list; missing, deleted, unpublished and inaccessible
assets are intentionally indistinguishable. An unavailable platform model does not block
execution with the client's own model. `configured_enabled` is the stored asset flag,
not an effective local capability or user credential status.

Skill `files.inventory=not_loaded` means file lists must be fetched on demand.
The response supplies `{ executable, argv }` descriptors for content and directory listing.
Read descriptors need `--path <path-from-listing>`; add `--output <local-file>` for binary
assets. Pass argv as separate arguments; never interpolate names, IDs or paths into shell
code. Use the same AE host for every follow-up (append `--host <original-host>` when needed).

MCP metadata includes transport, authentication mode, tool discovery and (OAuth only)
platform auth-status discovery. Connections and credentials are excluded by default.
When the user explicitly asks to export credentials for local configuration, run:

```bash
ae-cli agent +get-agent-context --id <agent-id> --include-mcp-credentials --host <original-host>
```

The sensitive response adds `credentials_included=true`. Each visible MCP has
`connection_config=exported` plus `connection_name` and the market configuration in
`connection` (`type`, `url`, `headers` for remote servers; `type`, `command`, `args`,
`env` for stdio),
`contains_credentials`, and `credential_expires_at`; or `connection_config=unavailable`
with a safe `connection_error` code. HTTP header and environment variable names are preserved
exactly. The same configuration builder and current-user token service as the MCP market
are used; system URLs use the requested AE host. `credential_expires_at=null` means the
market token API does not expose expiry, not that the credential never expires. Platform
managed bridge configurations still require the platform runtime; do not claim they work locally.
`summary.unavailable_connection_count` counts visible MCPs whose connections could not export.
Write credentials only into the intended local client configuration. Do not repeat them in
chat, logs, shared files, or source control. No OAuth refresh tokens or platform-internal
secrets are exported. Expiring or revoked credentials require reauthorization and a fresh
export. Exported configuration does not prove the client can connect or execute tools.
If the server omits `credentials_included`, it does not support this option; stop and request
a compatible deployment instead of assuming the connection has loaded.

The context version identifies returned metadata, not an immutable dependency bundle.
Re-fetch for a new task. Check Skill versions when fetching files; avoid mixing versions.
Nothing is installed, synchronized or executed by this command.

Errors: 401 requires CLI login; 404 means an unavailable Agent or an older server without
this endpoint (verify against `+get-agent` and server deployment); 409
`invalid_agent_configuration` requires fixing malformed dependency configuration;
500 is a server failure. Never silently fall back to incomplete raw configuration.

Transition status: transitional
Owning module: te-agent / agents
Current transport: CLI-token REST GET /api/cli/agent/v1/agents/{agentId}/context
Gateway target: TBD
Review after: 2026-12-09
Exit condition: When an equivalent gateway capability exists, reassess typed command value and migrate the transport or use capability discovery.
