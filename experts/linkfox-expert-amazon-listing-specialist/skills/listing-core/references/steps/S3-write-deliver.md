# S4–S5 写作、校验与交付

## 输入

- 只读 `03-write/writer-input.json`；它已包含本品事实投影、洞察、词表、模式/站点和字段限制。

## 操作

1. `prepare-write` 已生成自包含的 `writer-input.json` 与 `spec.json`；Writer 不再读取本 reference、Writer SKILL 或 facts/insight/keywords/spec 多份文件。
2. 调用 Writer 一次生成全字段到 `listing-draft.json`。存在 handoff 时只重写 `field_actions`，其余字段逐字保持不变。
3. 运行一次 `run_pipeline.py finish`：先确定性生成 Search Terms / Subject Matter，再对最终前后台六类字段运行完整受限词、声明与全局品牌词库复检，之后才进入字段校验与定稿。存在 block/fail 时仅重写 stdout 指出的失败字段一次，其余逐字不动；再失败则停止。不得把改写前的合规报告当作最终复检结果。
4. 用户要求评分或 HTML 报告时，先用 canonical scorer 生成 `score-result.json`，并把 `check-report.json` 传给 scorer。
5. `finish` 内部生成同一评分事实源下的 final JSON/MD、AI readiness、Excel 与可选 HTML；未要求报告时省略评分和 HTML 参数。
6. 正常交付直接使用 finish stdout，禁止回读 final 文件二次确认。
7. 交付说明、检查摘要、诊断结论与后续建议一律用中文表述；只有 Listing 文案字段本身使用目标站点语言。

## 输出

- `listing-final.json`：同时是 agent-listing Excel exporter 的结构化输入。
- `listing-final.md`、`check-report.json`、`ai-readiness.json`。
- 可选 `score-result.json`、`listing-report.html`：只在用户要求评分或 HTML 报告时生成。
- `linkfox-agent-listing-copy-xlsx-*.xlsx`：四 sheet Listing 文案表；首 Sheet 严格遵循业务模板 19 列，其余 Sheet 不输出 SKU 列。
- 更新后的 `run-manifest.json`。

## 用途

Markdown 供 Amazon 预览，JSON 供 UI 面板，既有 Excel 供下载和团队审核；不生成第二套 Flat File。

- **落盘**：所有产物路径写入 manifest；Excel 路径以 exporter 的 `XLSX artifact:` stdout 为准，HTML 路径以 renderer 的 `Rendered` stdout 为准。
- **读取**：交付时只读 manifest 和检查摘要，不回读整份 Excel。
- **判定**：QA 未通过时 Excel exporter 不得执行。
