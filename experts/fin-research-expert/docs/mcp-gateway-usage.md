# MCP Gateway Usage Guide

## Current Default

WorkBuddy uses one `tongzhou-fin-research` Connector with native browser OAuth and PKCE. Codex uses one registered MCP server backed by the npm stdio OAuth proxy. Both call the canonical `/mcp/tongzhou-research` resource and neither package ships an API-Key bridge.

This guide covers OAuth authorization, installation, connection checks, capability boundaries, and release artifacts.

## Audience

- Customer success and operations teams helping users activate `同舟股市投研专家`.
- WorkBuddy users installing the expert package.
- Codex users importing the matching plugin.
- Engineers debugging package release, OSS download, or OAuth connection issues.

## Package Relationship

| Package | Target | Artifact |
|---|---|---|
| WorkBuddy expert | WorkBuddy marketplace / local expert directory | `fin-research-expert-VERSION.zip` |
| Codex plugin | Codex local plugin import | `tongzhou-fin-research-expert-VERSION-codex-plugin.zip` |

Both packages use the same Gateway account and OAuth boundary. WorkBuddy declares one Connector dependency through `.codebuddy-plugin/plugin.json`; Codex registers one stdio OAuth proxy.

## WorkBuddy Authorization Flow

1. Click `连接` for `同舟金融研究` in WorkBuddy.
2. WorkBuddy discovers Gateway OAuth metadata and opens the browser authorization page.
3. Sign in if needed, review the public-research scope, and click `允许连接`.
4. WorkBuddy receives the native callback, exchanges the PKCE authorization code, and stores the renewable session.
5. Retry the original Connector business call once.

The business call itself is the connection check. Do not run Shell, npm, Node, a local credential preflight, or an API-Key helper first.

## WorkBuddy Install

Preferred path:

1. Install or open `同舟股市投研专家`.
2. Let WorkBuddy resolve the `tongzhou-fin-research` dependency.
3. Approve browser OAuth if requested.
4. Retry the original research request once.

For local developer validation:

```bash
python3 scripts/validate_local.py --source .
python3 scripts/package_expert.py --source . --output-dir dist
python3 scripts/install_local.py \
  --source . \
  --marketplace "$HOME/.workbuddy/plugins/marketplaces/my-experts"
```

## Codex Install

The Codex plugin is packaged from:

```text
codex/plugins/tongzhou-fin-research-expert
```

Build it locally:

```bash
python3 scripts/package_codex_plugin.py \
  --source codex/plugins/tongzhou-fin-research-expert \
  --output-dir dist
```

Install or upgrade through npm:

```bash
npx --yes tongzhou-fin-research-expert@latest setup --target codex
```

The installer registers one `tongzhou-fin-research` stdio OAuth proxy. The archive contains no raw `.mcp.json`, bearer token, API Key, or `gateway_api.cjs`.

## Runtime Tool Surface

The canonical connection exposes four namespaced families:

- `fin_data__<tool>`
- `doc_search__<tool>`
- `fin_graph__<tool>`
- `same_boat__<tool>`

WorkBuddy and Codex call these tools through their configured `tongzhou-fin-research` connection. Do not translate tool calls into shell commands or call unrelated direct MCP servers.

## OAuth Repair

Normal research does not run a credential preflight. If Codex setup or authorization needs explicit repair outside a research turn:

```bash
npx --yes tongzhou-fin-research-expert@latest auth status
npx --yes tongzhou-fin-research-expert@latest auth login
```

WorkBuddy repair always uses Connector settings and the browser authorization page. Never request or paste OAuth tokens, authorization codes, SMS codes, or API Keys into chat.

## Smoke Checks

For WorkBuddy, invoke one narrow business tool through `tongzhou-fin-research`; a successful result proves the protected OAuth connection is usable.

For Codex, verify that the registered MCP server exposes the namespaced tools above, then call one narrow tool. Do not build a local HTTP/MCP bridge.

## Capability Boundary

The public package exposes only public-market research workflows:

- company and stock evidence briefs;
- industry or sector move attribution;
- announcement, policy, and event interpretation;
- research report digest and institution viewpoint comparison;
- Tongzhou market news and viewpoint lookup;
- evidence ledger, transmission chain, red-team review, visuals, and HTML playbook output after evidence retrieval.

It does not expose sales workflows, customer profiles, private holdings, trade-history review, personal portfolio optimization, suitability advice, or deterministic buy/sell recommendations.

## Service Entry

OAuth authorization success exposes the mobile community handoff. WorkBuddy users can reopen the Connector authorization page from settings or visit `https://mcp-gateway.textmind-gz.com/login`.

Codex and other npm-installed clients can request a short-lived service URL with:

```bash
npx --yes tongzhou-fin-research-expert@latest support
```

## Release And Download

Gitea Actions builds and publishes releases from `main` or `v*` tags. Required repository secrets:

```text
OSS_ACCESS_KEY_ID
OSS_ACCESS_KEY_SECRET
```

Release outputs include the WorkBuddy zip, Codex plugin zip, Layer 1 skill zip, npm package, `oss-release.json`, matching SHA256 files, installation prompts, upgrade prompts, and `manifest.json`.

WorkBuddy and Codex package versions must match. CI checks this before publishing.

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| WorkBuddy opens authorization repeatedly | Approval was incomplete, callback failed, or the renewable session was revoked | Reopen Connector authorization and retry the original request once |
| Codex registered MCP is unavailable | Proxy setup/auth is incomplete or Codex has not reloaded config | Run npm setup/auth outside the research turn and restart Codex if config changed |
| Prior-turn data exists after auth failure | Conversation contains old evidence | Do not reuse it; authorize and rerun the query |
| 401 | OAuth session is no longer accepted | Reauthorize; do not request tokens |
| 403 | Account lacks the server/tool grant | Ask operations to inspect grants |
| 429 | Minute/day quota exceeded | Follow `Retry-After` |
| 503/504 | Gateway dependency or upstream is unavailable | Stop after the documented retry limit and state the temporary gap |
| Token or code appears in chat/logs | Secret handling mistake | Revoke the affected session and remove exposed content where possible |

If a computed tag already exists, the `main` workflow skips publishing to avoid overwriting an existing release. A manual `v*` tag push creates or updates the matching Gitea Release and refreshes OSS assets.
