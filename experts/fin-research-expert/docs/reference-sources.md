# Reference Sources

This file records source materials used to design the WorkBuddy financial research expert package.

## WorkBuddy Product Whitepaper

Local source:

```text
reference-materials/local/workbuddy-product-whitepaper.docx
```

Usage:

- Expert, Skill, Connector, and Discover/Playbook positioning.
- WorkBuddy marketplace quality and red-line expectations.
- Playbook entries as reusable output/task examples.
- Same-brand content should normally stay behind a single clear official entry unless the user group and core function are materially different.
- Skill describes how to do the work; Connector provides service access; Expert is the user-facing role; Discover/Playbook shows reusable proof artifacts.

Policy:

- Do not commit the raw whitepaper unless redistribution is explicitly approved.
- Summarize relevant requirements in package docs and tests.

## 同舟 Skill Spreadsheet

Local source:

```text
reference-materials/local/tongzhou-skill-mapping.xlsx
```

Usage:

- Capability discovery for 同舟小程序, 智能投顾, and 研报数据平台.
- Launch/partial/future mapping to approved non-sales Layer 2 workflows.
- The sanitized 39-item coverage matrix is committed in `skills/fin-mcp-gateway/references/layered-capabilities.md`.

Policy:

- Do not commit the raw spreadsheet by default.
- Commit only sanitized capability mappings required for package operation.

## WorkBuddy Expert Manager

Local source:

```text
/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/builtin-skills/expert-manager
```

Usage:

- `plugin.json` schema and expert metadata rules.
- Agent markdown frontmatter rules.
- Local validation, registration, and package scripts.

Policy:

- Do not copy bundled WorkBuddy source into this repository.
- Use the bundled scripts for local validation.

## WorkBuddy Partner Docs

Converted Markdown references:

```text
reference-materials/workbuddy-docs/workbuddy-playbook-inspiration.md
reference-materials/workbuddy-docs/workbuddy-skill-ecosystem.md
reference-materials/workbuddy-docs/workbuddy-connector-developer-guide.md
reference-materials/workbuddy-docs/workbuddy-expert-development-spec.md
reference-materials/workbuddy-docs/workbuddy-product-ecosystem-whitepaper.md
```

Usage:

- Playbook/inspiration submission shape: `case.json`, one output file, `cover.png` at 720x400, a one-shot "制作我的版本" prompt, and linked Expert/Skill/Connector capabilities.
- Skill ecosystem expectations: clear capability boundaries, executable instructions, references for API details, Chinese-friendly copy, no hard-coded secrets, and at least one Playbook case for stronger distribution.
- Connector developer expectations: standalone Connector packages use `connector-meta.json`, `mcp.json`, optional Skill docs, icons, token-mode `token-schema.json`, HTTPS production URLs, and performance-review material.
- Expert development expectations: Agent packages keep `agents/`, `skills/`, and optional `bin/` at the plugin root; Agent frontmatter must not declare `tools`; embedded MCP dependencies may be declared through `dependencies.mcpServers` plus root `.mcp.json`; tokenSchema keys must match header placeholders and real tokens must never be packaged.
- Whitepaper governance expectations: Expert, Skill, Connector, and Discover/Playbook are separate ecosystem roles; same-brand content should normally keep one official user-facing entry unless the target users, core function, and naming are materially different; updates that change core scope require review.

Policy:

- These converted docs are committed as repository references under `reference-materials/` and are excluded from the standard WorkBuddy Expert zip.
- Runtime constraints must be summarized in `agents/`, `skills/`, tests, and Playbook case metadata rather than shipping the full partner docs to users.
- Official Playbook submission bundles should normalize to `case.json`, the single output artifact, and 720x400 `cover.png`; any long-page preview images are supplemental repository assets.

## Gateway and Layered Capability Specs

Platform sources:

```text
specs/061-workbuddy-mcp-gateway-expert-onboarding/
skill-packs/_sources/ly-skills/
services/mcp-*/skills/layer1-*/SKILL.md
services/min-mcp-gateway/
```

Usage:

- Public gateway key governance and portal contract.
- Approved Layer 1 service list.
- Approved non-sales Layer 2 route list.
- WorkBuddy credential binding and troubleshooting behavior.

## Playbook Entries

Committed Playbook cases are sanitized examples only:

- `event-factor-impact-brief`: event factor attribution template with objective data, industry-chain exposure, core business weight, and historical similar-event return windows.
- `industry-long-short-signal`: industry long/short signal dashboard template with horizon split, factor contributions, historical win-rate samples, and calculation notes.

The `playbooks/cases/` directory keeps the WorkBuddy Discover/Playbook case shape: `case.json`, `output.html`, primary `cover-portrait.png` for long HTML pages, fallback `cover.png`, and `review.md`.

These entries are sidecar proof assets designed for WorkBuddy "做同款" review and are not bundled into the standard Expert package. They contain no raw gateway responses, no API keys, no private account data, and no sales/private workflow claims. When a future capability such as historical event backtesting is not returned by MCP, the sample must omit that module or describe the evidence boundary in 数据口径 instead of fabricating win rates or returns.

## Packaging Interpretation

The current package intentionally uses one Expert plus one connector companion Skill:

- The user-facing entry remains `同舟股市投研专家`.
- The Tongzhou MCP Gateway is treated as the Connector layer.
- `fin-mcp-gateway` is the Skill layer that teaches safe authentication, route selection, and output constraints.
- `playbooks/cases/` is a sidecar Discover/Playbook case layer for review and publishing; the standard Expert zip excludes it.

Do not split the current public research package into multiple same-brand experts for 个股、行业、研报, or 事件 unless WorkBuddy review has accepted a separate user group and a materially different core function.
