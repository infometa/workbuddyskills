# Common HTML Playbook Rules

Read this file for every HTML Playbook. The calling Layer 3 workflow reads its own `references/playbook.md`; this file contains only the shared rendering contract.

## Evidence Boundary

- Only transform already-evidenced research into HTML. The page must be based on 已取证 material from the relevant research workflow.
- Do not replace or skip gateway setup. This skill 不要替代 `fin-mcp-gateway` 认证 and must not call business tools by itself.
- 不得新增事实, invent links, invent statistics, or hide missing evidence behind confident wording.
- If the evidence package is incomplete, say which evidence family is needed and return to the research workflow before producing HTML.

## HTML Contract

- Produce one standalone HTML document with inline CSS and necessary interaction inline. Use the phrase 必要交互内联 as the operating rule.
- Do not load external rendering assets: no `<script src>`, no `<link href>`, no remote `<img src>`, no external fonts, and no `@import`.
- Use WorkBuddy-friendly tabs as `<button data-target="...">` with a tiny `scrollIntoView` handler. Do not use `href="#section-id"` or any `javascript:` link.
- All major sections must be visible without JavaScript. Never hide content with `.section { display: none; }`.
- Keep text readable on mobile and desktop. Set stable widths, wrapping, and line heights so text 不能溢出 cards, buttons, chips, or chart labels.
- Follow Mainland China market color semantics for every directional value, factor, evidence label, chart, legend, and scenario: red is positive/up/`+`/bullish/supporting; green is negative/down/`-`/bearish/risk or opposing. Neutral structure uses blue/teal/gray, while mixed, missing, or pending evidence uses amber. Do not use the international green-up/red-down convention.

## Source Review

- Source-review links are allowed only when the evidence contains a real public URL, announcement PDF, mini-program link, or report link.
- Every external source anchor must use `target="_blank"` and `rel` containing `noopener`.
- Do not show internal field names such as `source_url`, `pdf_url`, `original_url`, or `document_url`.
- If market, financial, graph, or viewpoint data has no article-level URL, do not create a fake source card. Attribute it in body copy or methodology by 来源类型, for example 同舟行情库、同舟财务指标库、同舟行业图谱、同舟观点.
- For structured data without article-level links, show 来源类型和源 ID only in 数据口径 or evidence notes; 不要生成假链接 or fake source-review cards.
- Authentication success is not source verification. Login pages, OAuth authorization pages, account consoles, support/feedback pages, search pages, and portal homepages must never be used as article links or source-review anchors.
- For selected Same Boat content, use a real article-level URL returned by the evidence or the `url_link` returned by the Layer 1 source-link procedure. If neither exists, keep a non-clickable source-type label and do not render “同舟认证证据”“认证查看” or an equivalent substitute card.

## Identity Evidence

- When an industry/theme workflow used a resolver result, preserve a user-readable identity block or data口径 line with `canonical_id`, selected `source_ids`, and `coverage_gaps`.
- The page should explain which source IDs were used for Same Boat, fin-data, market/index data, 行业图谱, and 产业链图谱 when those fields are available.
- If `coverage_gaps` shows a missing source family, say that the source was not covered in this evidence package; 不要用宽基指数、示例行业或假 ID 替代.
- Identity evidence is not a clickable source unless the upstream evidence includes a real review URL. Use source type and ID labels instead.

## Forbidden User-Facing Copy

Do not expose raw tool or backend details in the HTML:

- raw JSON, backend IDs, graph node IDs, search scores, API keys, SMS codes, phone numbers, account IDs, holdings, or trade history.
- `layer1-*`, `layer2-*`, `layer3-*`, MCP tool names, backend parameter names, or implementation route labels.
- 技术错误状态 such as 工具调用失败、接口失败、超时、外部数据源暂不可用、未返回可用数据、permission denied, or stack traces.

## Safety

- Add a clear 非投资建议 note.
- Do not output buy/sell advice, target price, position sizing, guaranteed returns, or account-specific diagnosis.
- Separate facts, interpretation, risks, and verification items so the page feels source-backed rather than promotional.
