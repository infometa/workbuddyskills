# CloudMall analysis connector assets

Imported from `agent-group/ai-buddy-backend/skills/ecommerce-analyst-v3` in this repository. `source-manifest.json` records SHA-256 of every upstream file at import. All domain knowledge, SQL templates, scenes, schemas, report plugins, gates and analysis methods are retained. Runtime documentation is adapted for the 当前 Agent local file/Bash environment and 当前运行时的 Capability 分析执行器.

Reproduction: copy upstream `references/`, `scripts/`, and `SKILL.md`; preserve all knowledge files; apply the connector adaptations recorded in the committed diff. No dependency download is needed. The contract tests compare preserved assets directly to upstream and verify script behavior. Refreshing from upstream requires reviewing the recorded hashes and retaining the tool/local-path adaptations, not blindly copying the old runtime entrypoints.

Changes: replace runtime query invocation with action/input; SQL encoding is file-only UTF-8 standard Base64; reports use local paths and a Python entrypoint; Node/Puppeteer/Chromium are optional existing PDF dependencies; no automatic installation. Fixed cap 1/2/3 and dynamic reports are enabled. Calendar date offsets are corrected for yesterday and inclusive 7/30 day periods. Existing HTML/chart generators use remote Chart.js CDN; offline charts must not be claimed complete.

Run tests from `agent-group/ai-cloudmall-open`: `npx vitest run tests/contract/analysis-skill.test.ts`. Fixture reports are synthetic smoke data, never live operating evidence.

Security adaptations: report charts use script-safe JSON and typed options with trusted callback mappings; waterfall colors are data arrays. PDF requires real Chart instances and no page errors. D-10 and user detail templates explicitly require availability checks and are unavailable under the current server whitelist. These two template/plugin adaptations are deliberate exceptions to byte-identical source copies.

All report rich-text fields and table cells pass a formatting-only HTML allowlist; business names are escaped at plugin interpolation sites and plain headings are escaped by the renderer. The three plugins are intentionally adapted rather than byte-identical. Encoder input is bounded at 32769 bytes and rejects NUL to match the server.
