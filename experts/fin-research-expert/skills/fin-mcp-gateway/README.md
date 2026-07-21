# Fin MCP Gateway Skill

This skill is the WorkBuddy-side companion for the Tongzhou public MCP Gateway. It teaches the expert how to use the single OAuth Connector, route public-market research questions, and avoid direct or unsafe MCP bypasses.

## Quick Start

1. Call the `tongzhou-fin-research` dependency Connector for the original research request.
2. If WorkBuddy opens the OAuth page, ask the user to approve it on mobile.
3. Retry the original Connector tool once.
4. Continue only after that business call succeeds.

Do not run Shell, npm, Node, a credential preflight, or a local MCP bridge before normal research. This skill intentionally does not ship `gateway_api.cjs` and does not read local API-Key files or environment variables.

## Runtime Tools

Use only tools exposed under the single `tongzhou-fin-research` connection:

- `fin_data__<tool>`
- `doc_search__<tool>`
- `fin_graph__<tool>`
- `same_boat__<tool>`

Read the matching Layer 1 contract before choosing parameters. Never translate a Connector tool call into a shell command.

## Service Entry

The OAuth success page contains the mobile community handoff. Users can reopen the Connector authorization page from WorkBuddy settings or visit `https://mcp-gateway.textmind-gz.com/login` for product feedback and service questions.

## References

- `references/binding.md`: WorkBuddy/Codex OAuth flow.
- `references/connector.md`: Connector boundary and namespaced tool contract.
- `references/layered-capabilities.md`: approved Layer 1/Layer 2 capability map.
- `references/playbook-style.md`: WorkBuddy Playbook output rules.
- `references/safety.md`: public-market safety and excluded private workflows.
