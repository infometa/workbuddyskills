---
name: fastmoss
display_name: FastMoss TikTok Shop 数据分析助手
display_name_en: FastMoss TikTok Shop Analytics
description_zh: 使用 FastMoss MCP 查询和分析 TikTok Shop 商品、达人、店铺及内容数据。
description_en: Query and analyze TikTok Shop product, creator, shop, and content data with FastMoss MCP.
version: 1.0.0
author: FastMoss
category: ecommerce-analytics
description: >
  Use when working with FastMoss MCP data for TikTok Shop product scouting,
  creator discovery or outreach, competitor comparison, shop diagnosis, viral
  attribution, video deconstruction, or short-video content strategy.
---

# FastMoss Skills

FastMoss Skills is the runtime routing layer for FastMoss MCP. Use this entrypoint first, then load the matching reference document from `references/`.

## Prerequisite: FastMoss MCP Required

This skill depends on the FastMoss MCP service for live TikTok Shop business data. The skill itself only provides routing, business judgment, and answer-format guidance; it does not contain the live product, creator, shop, video, livestream, market, or document data.

Before using the business workflows below, confirm that the AI client has the FastMoss MCP server installed, configured, and available as callable tools. If FastMoss MCP is not installed or the tools are unavailable, do not fabricate data. Tell the user to install or enable FastMoss MCP first and point them to the setup guide: `https://developers.fastmoss.com/mcp/overview.html`.

## Required Flow

1. Confirm FastMoss MCP tools are available in the current AI client. If not, stop and guide the user to install or enable FastMoss MCP first.
2. Read @references/PRINCIPLES.md first. It defines the shared answer structure, data-transparency rules, FastMoss hyperlink rules, language behavior, and preference handling.
3. Match the user's intent to one primary business workflow below and read that reference file.
4. Follow `PRINCIPLES.md` plus the selected workflow reference. If the request spans multiple workflows, start with the closest match and follow any hand-off guidance in the reference.
5. When you need a FastMoss or TikTok Shop term, metric, lifecycle label, L0-L6 tier, creator-Level rule, channel-attribution rule, or the shared leading-indicator judgment method, read @references/GLOSSARY.md.

## Business Workflow Routing

| Reference | Use when the user wants to... | Example phrasings |
|---|---|---|
| `references/fm-product-scout.md` | Find products to sell, judge a product's stage, evaluate follow-selling timing, or identify blue-ocean opportunities. | "what should I sell", "is this product too late", "find growth-stage products" |
| `references/fm-creator-outreach.md` | Find creators for a product, see who is already selling a product, vet one creator, or write creator outreach copy. | "find creators", "who is selling this", "is this creator worth partnering with" |
| `references/fm-competitor-batch.md` | Compare several competitor products, shops, or creators, or explain why something suddenly became popular. | "compare these competitors", "why did this product blow up" |
| `references/fm-store-diagnosis.md` | Diagnose one shop's sales structure, product mix, traffic channels, concentration risk, or recent decline. | "analyze this shop", "why is my shop slipping" |
| `references/fm-video-brief.md` | Build a video strategy, deconstruct a viral video, write hooks, or produce a creator shooting brief. | "how should we shoot this", "deconstruct this video", "write a video brief" |

## MCP Tool Use Rules

- Use FastMoss MCP tools for live business data. Search or resolve IDs first, then call detail, trend, list, and analysis tools.
- If a tool call fails because FastMoss MCP is missing, disabled, unauthenticated, or unreachable, state that FastMoss MCP must be installed or reconnected before live analysis can continue.
- For category work, call `search_category_by_words` before category-specific product, market, or leaderboard tools.
- For object links, prefer any returned `fastmoss_url`; otherwise call `fastmoss_detail_url_examples` and build FastMoss-site links from the returned templates.
- Treat empty tool results as "data not retrieved" rather than proof that no market activity exists; retry with another window or tool when useful.
- Respond in the user's language unless the user asks otherwise.

## Notes

- Runtime documentation lives in `references/`.
- Human-facing installation and tool-list documentation lives in `README.md` and `README.zh-CN.md`; it is not required at runtime.
