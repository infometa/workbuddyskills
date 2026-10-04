# Connection and recovery

## Prerequisites

- This is a Windows-only local connector, not a remotely hosted MCP service.
- Tested native NVIDIA App: 11.0.9.528. Do not assume every production release includes its MCP components. Obtain a compatible release through an authorized NVIDIA distribution channel.
- The user completes NVIDIA App setup and enables Settings -> AI Agents and App Connections -> Allow Agents to control NVIDIA App, if the compatible build exposes this control.
- The shipped config expects `C:\Program Files\NVIDIA Corporation\NVIDIA App\McpServer\NvAppMcpServer.exe`. A different install drive/path needs a separately verified config; do not download a replacement automatically.
- The bridge relays to the existing NVIDIA service. No arguments, Node.js, Python, npm package, or installer are required by the connector.
- WorkBuddy configuration fields require 4.24.0 or newer. The installed WorkBuddy 5.7.0 was inspected, but marketplace installation and end-to-end UI testing remain separate acceptance tests.

## Credentials

WorkBuddy's Token form collects `NVAPP_MCP_TOKEN` as a password. `mcp.json` passes it only in the native child process environment using `${NVAPP_MCP_TOKEN}`. It is not a normal MCP tool argument, cloud API key, OAuth token, or permanent personal access token.

For the tested NVIDIA build, the user obtains the current `token` from the protected file:

```text
%LOCALAPPDATA%\NVIDIA Corporation\NVIDIA App\McpServer\server.json
```

Have the user enter it directly into WorkBuddy's credential form, not into a conversation. Do not display or read the whole discovery file into chat or logs. Avoid shared/cloud-synced clipboards and credential screenshots. The NVIDIA server generates a new session token on restart. Update the stored form value and reconnect; this package has no automatic refresh or OAuth flow.

The supplied upstream skill described a different discovery directory and HTTP default for another build. Those values are not used by this package. The tested endpoint was loopback port 47985, but the connector uses stdio and therefore does not hardcode a network port.

## Recovery

1. Missing tools: ask the user to install/connect the NVIDIA App connector in WorkBuddy and approve its local process/tool access. Importing the skill alone cannot establish that connection.
2. Missing executable: verify a compatible NVIDIA App was installed in the stated location. This package does not install or redistribute it.
3. `service_disabled` or missing discovery file: ask the user to check the NVIDIA MCP setting. Do not start services, edit registries, or reinstall applications without a separate request.
4. Stale token / authorization failure: update the Token form from the fresh local discovery file and reconnect. Do not replace the token with an empty value.
5. Successful MCP connection but Overlay failures: Overlay readiness is separate; ask the user to check NVIDIA Overlay settings.

Use WorkBuddy's managed MCP tools for normal tasks. This skill intentionally does not grant permission to edit `%USERPROFILE%\.workbuddy\mcp.json`, generated marketplace connector files, or to create an HTTP fallback. A specifically requested configuration task is separate from ordinary driver/capture queries.

## Security limitation to disclose

Earlier read-only probes against this native server succeeded without a token on loopback. Requiring a Token form here does not alter that server-side behavior. Do not claim all native MCP access is authenticated, or that removal of this connector revokes access from every local process. NVIDIA's server access model and WorkBuddy marketplace acceptance need review before broad distribution.

Adapted for this tested build; upstream attribution is in attribution.md.
