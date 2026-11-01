# MatRouter MCP Setup

Use this runbook when MatRouter is not connected, client authorization fails,
or a requested data source reports that configuration is required.

## Connection Flow

1. Check whether the client exposes the MatRouter tools through MCP
   `tools/list`. If they are present, start with `matrouter_search_materials` or
   `matrouter_get_thermochemical_entries`; call `matrouter_inspect_sources` only when source scope
   or configuration is uncertain.
2. If the tools are absent, connect the `matrouter` server packaged with this
   plugin. Hosts that cannot consume the plugin may configure the remote
   Streamable HTTP endpoint directly:
   `https://cmpdc.iphy.ac.cn/matrouter/mcp`.
3. Restart the client when its MCP configuration changes, then verify the
   connection through `tools/list`. Do not treat a successful HTTP request as
   proof that every data source is configured, healthy, or scientifically
   sufficient.
4. If the MCP connection returns an authorization failure, use the client's
   authorization flow. Do not request a bearer token or place credentials,
   identities, cookies, or authentication headers in MCP tool arguments.

Do not bypass MatRouter MCP by calling provider HTTP APIs. Do not install or
launch a local MatRouter runtime as a substitute for the packaged server,
process local files to imitate missing tools, or guess data that MCP did not
return.

## Manual Configuration

Portable Agent Plugin configuration:

```json
{
  "mcpServers": {
    "matrouter": {
      "type": "streamable-http",
      "url": "https://cmpdc.iphy.ac.cn/matrouter/mcp"
    }
  }
}
```

OpenAI local-plugin adapter:

```json
{
  "mcpServers": {
    "matrouter": {
      "type": "http",
      "url": "https://cmpdc.iphy.ac.cn/matrouter/mcp"
    }
  }
}
```

Codex TOML fallback:

```toml
[mcp_servers.matrouter]
url = "https://cmpdc.iphy.ac.cn/matrouter/mcp"
enabled = true
tool_timeout_sec = 300
```

For other clients, choose their remote or Streamable HTTP transport and keep
the endpoint unchanged. Do not add fixed authorization headers, tokens,
`oauth_resource`, or provider credentials to shared configuration.

## Source Configuration

Use `matrouter_inspect_sources` to identify the exact route state. Follow only returned
`next_cursor` values as `cursor`, omitting `sources` and `evidence_kind` on
continuations. If a requested route reports `requires_configuration`, report
the missing capability and direct the user to the service's supported account
or authorization path. The remote server owns provider configuration; client
environment variables and local dotenv files do not configure it.

Continue with public sources when they satisfy the request and state the
resulting coverage. Keep route readiness separate from execution outcome and
scientific sufficiency.

## Retry and Troubleshooting Boundaries

- Retry only when a structured MCP error or returned attempt explicitly marks
  the failure retryable. Use `matrouter_retry_sources` only with returned retryable
  `attempt_ref` values.
- Acquisitions with the same explicit base Bundle and identical request reuse
  their cached result while that Bundle is active. A root acquisition without
  a base creates a new context; do not automatically replay it if its response
  is lost. `matrouter_retry_sources` intentionally creates a new attempt.
- Follow structured `code`, `message`, `retryable`, `field`, and
  `corrective_action`. Refs can expire after process restart, TTL, or eviction;
  repeat the originating action when instructed and copy new refs rather than
  reconstructing them.
- Treat HTTP 401 or 403 as an authorization problem for the client flow, not a
  request for credentials in chat.
- Treat missing tools as a packaging, client-reload, or server-version issue;
  compare against `tools/list` instead of inventing a tool call.
- Treat `ready` as configured, not as proof of source health, completeness, or
  scientific support.
- A failed source is failed, not a verified empty result.
- On this remote server, `matrouter_download_source_file` writes only to the server's
  filesystem and cannot be used as a client download path. Prefer typed
  acquisition or an explicit HTTP `download_url` returned by a tool.
