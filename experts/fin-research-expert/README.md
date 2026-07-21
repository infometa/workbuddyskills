# WorkBuddy Tongzhou Equity Research Expert

WorkBuddy single-expert package for public equity research through the Tongzhou MCP Gateway connector.

This package is intended to be mounted in `fin-agent-platform` as:

```text
products/workbuddy-fin-research-expert
```

## Scope

v1 packages one WorkBuddy expert, displayed as `同舟股市投研专家`, for approved public equity research workflows:

- Sector and industry move attribution
- Listed-company and stock debate research
- Policy/event impact analysis and evidence-backed HTML playbook pages
- Research-report digest and institution viewpoint comparison
- 同舟投研 content lookup and summarization

## WorkBuddy Ecosystem Mapping

This package follows the WorkBuddy product whitepaper's four-module model:

| WorkBuddy module | Package implementation |
|---|---|
| Connector | Tongzhou MCP Gateway provides governed public-market data, document, graph, and Tongzhou research access. The standard package declares one `tongzhou-fin-research` dependency in `.codebuddy-plugin/plugin.json`; WorkBuddy native OAuth is the primary credential path. |
| Skill | `skills/fin-mcp-gateway` teaches credential binding and safe gateway calls; bundled `skills/layer1-*` entries provide public-market tool contracts; `skills/layer2-*` entries provide reusable research and presentation modules; reviewed `skills/layer3-*` entries own complete user stories such as industry windvane and event interpretation. |
| Expert | `agents/fin-research-expert.md` is the single user-facing expert role. |
| Playbook | `playbooks/cases/` contains sidecar WorkBuddy case assets for Discover/Playbook review and publishing. They are not part of the standard Expert package. |

## Single Connector Authentication

The current expert declares one `tongzhou-fin-research` Connector dependency. First use opens the gateway's browser authorization page through WorkBuddy native OAuth; the user approves once, then WorkBuddy completes the exact PKCE callback and retries the original call. The renewable OAuth session is stored by WorkBuddy, so new conversations and restarts do not require four repeated API Key entries.

The canonical remote MCP is `/mcp/tongzhou-research`. Its tools retain stable service namespaces for market data, documents, graph, and Tongzhou research. Existing four-entry API-Key configurations remain supported only as an explicit migration/rollback path and are not automatically removed or revoked.

The standard expert zip references the approved Connector by dependency name but excludes Connector source and root `.mcp.json`. Local unpublished validation installs the Connector separately; this preserves independent Expert and Connector review boundaries.

Internal route names such as `layer1-*`, `layer2-*`, and `layer3-*` are implementation labels. Marketplace text, quick prompts, and normal answers should use user-facing scene names such as 个股分析、行业异动、事件解读、研报挖掘、证据页. Approved public-market L1/L2/L3 skills are packaged with the expert; candidate Playbook templates and business/private-account skills remain excluded.

v1 intentionally excludes:

- `layer2-sales-*`
- `layer2-care-*`
- `layer2-pa-*`
- `layer1-sales-*`
- `layer1-pa-*`
- customer profile tools
- sales RAG tools
- strategy recommendation tools
- personal account holdings workflows
- personal trade-history workflows
- event backtesting or prediction workflows
- chart insertion workflows without a matching MCP/artifact contract

## Local Reference Materials

Large or local-only reference files can be staged here while drafting the expert package:

```bash
mkdir -p reference-materials/local
```

Examples:

- WorkBuddy product whitepaper
- WorkBuddy expert development specification
- WorkBuddy Playbook / inspiration module guide
- WorkBuddy Skill ecosystem guide
- WorkBuddy Connector developer guide
- 同舟 skill spreadsheet
- WorkBuddy expert-manager skill references
- Screenshots from local WorkBuddy inspiration pages

`reference-materials/local/` is ignored by git. Approved WorkBuddy partner
references are converted to Markdown under `reference-materials/workbuddy-docs/`
for repo-side maintenance only; the standard Expert zip still excludes the full
reference-materials tree. Runtime requirements should be summarized into
`agents/`, `skills/`, tests, and Playbook metadata.

## Local Validation

WorkBuddy ships expert-manager scripts in the app bundle:

```bash
EXPERT_MANAGER="/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/builtin-skills/expert-manager"
python3 "$EXPERT_MANAGER/scripts/validate_expert.py" .
```

After implementation, this package should also provide:

```bash
python -m pytest tests -q
python3 scripts/validate_local.py --source .
python3 scripts/package_expert.py --source . --output-dir dist
python3 scripts/install_local.py --source . --marketplace "$HOME/.workbuddy/plugins/marketplaces/my-experts"
```

## Customer Onboarding Flow

The first customer task is connecting the single WorkBuddy Connector. If the expert cannot verify that connection, it must stop instead of answering with cached, direct-MCP, or model-memory data.

For a complete customer, WorkBuddy, Codex, and operations runbook, see
[`docs/mcp-gateway-usage.md`](docs/mcp-gateway-usage.md).

1. The customer clicks `连接` for the `同舟金融研究` Connector in WorkBuddy.
2. WorkBuddy opens the gateway browser authorization page. The customer signs in if needed and clicks `允许连接`.
3. WorkBuddy completes OAuth/PKCE, stores the renewable session, and loads the canonical `tongzhou-fin-research` tools without an API Key form. Retry the original research request once.
4. The expert calls namespaced tools under that Connector directly; it does not run a separate Shell, npm, Node, or local credential check.
5. The current WorkBuddy and Codex packages do not include `gateway_api.cjs` and do not read local API-Key files or environment variables.
6. Only after the original Connector business call succeeds may the expert continue the research request.

## Playbook Cases

Per the WorkBuddy whitepaper model, Playbook cases are Discover/Playbook proof assets, while the standard Expert package is the runtime capability layer. `scripts/package_expert.py`, `scripts/install_local.py`, and local WorkBuddy validation copies intentionally exclude the whole `playbooks/` directory from the standard package.

The repository keeps these reviewed sidecar cases under `playbooks/cases/` for separate Playbook review/publishing:

- `event-factor-impact-brief` - 事件因子解读
- `industry-long-short-signal` - 行业多空风向标

Additional candidate cases may exist in the source tree while they are being prepared, but they must go through the separate WorkBuddy Discover/Playbook review path and must not be bundled into the standard Expert zip.

Each Playbook case contains `case.json`, `output.html`, official landscape
`cover.png`, supplemental `cover-portrait.png`, and `review.md`. They are
intended for WorkBuddy Playbook "做同款" review and must not include sales, care,
PA, private-account, holdings, or trade-history workflows.

Export the two reviewed WorkBuddy inspiration cases with:

```bash
python3 scripts/export_playbook_cases.py --source . --output-dir dist/playbooks
```

The export zip contains only the reviewed `event-factor-impact-brief` and
`industry-long-short-signal` case directories. It normalizes `case.json` to the
official submission shape with `cover.png` as the 720x400 primary cover, while
keeping `cover-portrait.png` as a supplemental long-page preview.

The HTML samples use source-review links returned by MCP whenever available; when event backtesting, win-rate, or other statistical data is not returned, omit that module instead of filling in invented values.

Playbook HTML samples must read like finished research artifacts, not capability
brochures: the first viewport should show the clear result, evidence window,
confidence/gaps, and key metrics. Each sample also includes a `源头复核入口`
section with clickable review links for returned source URLs or clearly labeled
public review entry points. Market snapshots, financial metrics, and graph facts
that do not have article-level URLs should be attributed in the methodology as
同舟行情库、同舟财务指标库、同舟行业图谱等来源类型; do not render them as broken source
cards or missing-link warnings.

## Avatar

`plugin.json` points to `avatars/expert-v2.png`. The repository includes a 512x512 PNG avatar so local validation and release packaging produce a complete expert package. The avatar can be replaced before marketplace publication, but the replacement must remain PNG/JPG, square, and under 500KB.

## Release Package

Every production gateway release should build a matching expert zip:

```bash
python3 scripts/validate_local.py --source .
python3 scripts/package_expert.py --source . --output-dir dist
```

The generated zip excludes local references, `.env*`, `.sms_key`, virtual environments, caches, and git metadata.
It also excludes `playbooks/`, because Playbook cases are reviewed and published as separate Discover/Playbook assets rather than as standard Expert runtime files.

Gitea Actions packages and publishes releases on `main` and `v*` tags when these
repository secrets exist:

```text
OSS_ACCESS_KEY_ID
OSS_ACCESS_KEY_SECRET
```

For local manual testing, `scripts/publish_oss_release.py` also accepts the
legacy aliases `OssAccessKeyId` and `OssAccessKeySecret`.

The release source of truth is `VERSION`. CI bumps it from Conventional Commits,
syncs `.codebuddy-plugin/plugin.json`, the Codex plugin manifest, and helper
clientInfo versions in the release commit, then creates tag `vVERSION` and
publishes in the same job:

- Gitea Release assets: WorkBuddy expert zip, standalone WorkBuddy Connector
  zip, Codex plugin zip, the standalone approved Layer 1 Skill zip, npm
  installer tgz, and `oss-release.json`.
- OSS assets under `mcp-gateway/releases/`: WorkBuddy expert zip, standalone
  WorkBuddy Connector zip, Codex plugin zip, standalone Layer 1 Skill zip,
  matching `.sha256` files, `prompts/install-workbuddy.md`,
  `prompts/install-codex.md`, `prompts/upgrade-workbuddy.md`,
  `prompts/upgrade-codex.md`, `prompts/install-layer1.md`,
  `prompts/upgrade-layer1.md`, optional npm-backed `prompts/install-agent.md` and
  `prompts/upgrade-agent.md`, and `manifest.json` for the self-service console
  install and upgrade prompts. The Layer 1 archive contains only
  `layer1-fin-data`, `layer1-doc-search`, `layer1-fin-graph`, and
  `layer1-same-boat`; it complements remote MCP connectivity and does not carry credentials.

If the computed tag already exists, the `main` workflow skips publishing to
avoid overwriting an existing release. A manual `v*` tag push will create or
update the matching Gitea Release and refresh OSS assets.

## Codex Plugin Package

The Codex import shape lives under:

```text
codex/plugins/tongzhou-fin-research-expert
```

It is a Codex plugin, not a standalone skill. The plugin contains `.codex-plugin/plugin.json`, a main `tongzhou-fin-research-expert` skill, bundled public-market Layer 1/Layer 2 skills, the two reviewed Layer 3 user-story skills, and the expert icon assets. It intentionally contains no local Gateway helper script.

Build the Codex plugin zip with:

```bash
python3 scripts/package_codex_plugin.py \
  --source codex/plugins/tongzhou-fin-research-expert \
  --output-dir dist
```

Codex uses the same Gateway account model through the npm stdio OAuth proxy; token storage and refresh are owned by that proxy and the operating-system credential backend.

Build the standalone Layer 1 package for ordinary MCP clients that support a
real Skill directory with:

```bash
python3 scripts/package_layer1_skills.py --source . --output-dir dist
```

Clients without a stable Skill mechanism should use the four remote MCP
connections without guessing an installation path.

Gitea Actions runs `.gitea/workflows/package-release.yml` on branch, PR, tag, and manual dispatch. It compiles scripts, runs package tests, validates the local package, builds the WorkBuddy expert zip, Codex plugin zip, and standalone Layer 1 Skill zip, then publishes release builds to Gitea Release and OSS from `main` or `v*` tags.

The console install and upgrade buttons prefer the OSS Markdown prompt docs
referenced by `manifest.json`. This keeps the copied prompt stable: operations
can update the Markdown docs under `mcp-gateway/releases/prompts/` and users who
copy a fresh prompt will follow the latest instructions without a frontend
rebuild.

## npm Quick Installer

The repository also ships a cross-platform npm installer. It resolves Windows
and Unix-like user directories without shell-specific path guessing, downloads
the current OSS release, verifies SHA256, backs up existing files, and installs
both MCP connectivity and the approved Layer 1 Agent Skills where the target
supports them.

```bash
npx --yes tongzhou-fin-research-expert install --target cursor
```

Supported targets are `workbuddy`, `codex`, `claude-code`, `cursor`, `windsurf`,
`opencode`, `gemini-cli`, `copilot-cli`, `vscode-copilot`, `cline`, and
`hermes-agent`. Run the following command
to inspect the live list:

```bash
npx --yes tongzhou-fin-research-expert targets
```

The default installer path configures one `tongzhou-fin-research` OAuth
connection. WorkBuddy uses its native Connector OAuth; supported remote clients
use direct OAuth, and the remaining clients use the npm stdio OAuth proxy. No
API Key is requested or written during the normal setup flow. The explicit
`--legacy-api-key` option remains only for rollback compatibility with old
four-server installations. The local `.npm_acc` file is ignored by Git and every
release packager. CI publishing uses a Gitea `NPM_TOKEN` secret instead of local
account credentials.

Before public marketplace publication, run the WorkBuddy expert-manager validator on macOS and replace the avatar placeholder with an approved versioned avatar path such as `avatars/expert-v2.png`.
