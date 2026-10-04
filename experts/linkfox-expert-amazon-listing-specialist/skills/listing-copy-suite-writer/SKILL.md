---
name: listing-copy-suite-writer
description: Listing Core 的完整文案写作步骤。一次生成 Title、Item Highlights、5 条 Bullets、Description、Search Terms、Subject Matter、结构化属性及 AI 买家问题映射；不负责检索、校验或导出。
---

# Listing Copy Suite Writer

本 Skill 是 `listing-core` 的 S4 Writer，不是独立编排流程。

## 输入

- `product_facts`：唯一可用于商品参数、材质、认证、兼容和效果主张的事实源。
- `spec`：由 `build_spec.py` 生成，包含限值、站点、字段职责、关键词和品牌边界。
- Product Detail 的顶部客户评论摘要、SIF Top N、`buyer_questions`、`competitor_context`、`banned_terms`、可选现有 Listing。
- `mode=rewrite` 可带 `spec.rewrite_contract`：来自 Audit 的字段动作、锁定字段和经营动作。经营动作不进入文案。

缺少最小商品事实时停止；竞品事实不得移植到本品。

## 写作规则

1. 一次规划全部字段，保持核心词、场景、痛点、证据和边界一致。
2. 首稿按 `spec.generation_targets` 写作，为语言修订和多字节词预留余量；`spec.limits` 仍是不可越过的硬上限。bullets 必须恰好 5 条且非空。`item_highlights[]` 必须且只能包含 **1 个字符串**：内容写成一行，不换行，不加 `•`、`-`、序号等 Bullet Point 前缀。
3. 核心词自然连续进入 Title；场景/痛点词进入 bullets；属性词进入 highlights/attributes。严格按 `spec.search_terms_contract.generation_order` 最后生成 Search Terms：对最终 Title + Bullets 做契约指定的归一化，删除所有重复词元；`reserved_front_tokens` 是生成前即可排除的最低集合，不能等 QA 失败后再替换。
4. 每条 bullet 回答至少一个买家问题；无法证实的问题标记未覆盖。
5. 不复制竞品句子，不写竞品品牌、受限词或无证据主张。逐项遵守 `spec.claim_policy`；图片观察和竞品评论不得推出内部填充、承重/稳固、人体工学、护理、耐用、认证或价格优势，除非本品事实段明确给出。
6. `profile=fast` 时在同一次调用中先从 Product Detail 评论摘要形成买家问题，再生成文案和 `question_coverage`；禁止另起洞察模型调用。
7. 存在 `rewrite_contract` 时只改 `field_actions` 指定字段；`locked_fields` 和未受影响字段逐字保持不变。报表证据只能解释改写目标，不能成为材质、规格、认证或效果声明的事实源。
8. **语言分层**：Listing 文案字段（Title、Item Highlights、Bullets、Description、Search Terms、Subject Matter）一律用 `spec.output_language`，由目标站点决定。本 Skill 只产出文案字段，不产出面向用户的说明性文字；`question_coverage` 的未覆盖说明等解释性内容用中文，引用的原文关键词保留原文。
9. **置信度如实标注**：`data_confidence` 必须反映真实证据强度，写作前读取 `../listing-core/references/data-confidence-protocol.md`。关键词矩阵降级为 `keyword_data_unavailable`、`sif_no_data` 或 `category_seed` 时，不得在文案或 `question_coverage` 里呈现搜索量、排名或引用率，也不得把推导词表述为 SIF 实证词。

## 输出

只输出 `listing-core` 定义的 `listing-draft.json` 对象，不附加 Markdown：Title、单元素 `item_highlights[]`、5 条 `bullets[]`、Description、Search Terms、`subject_matter[]`、`structured_attributes`、`question_coverage`、`four_pillars`、`data_confidence`。fast 的 `question_coverage` 同时作为 buyer questions 结构化来源。

`subject_matter` 是可选后台字段：`spec.limits.subject_matter_max` 为 `null` 时不做字数裁定，但仍会被安检禁词、竞品品牌和特殊符号；`spec.field_roles.subject_matter` 是它的唯一职责口径。

之后必须走字段安检，本 Skill 不声明质量通过，也不自行裁切字段。两个入口按调用方选择，二者共用同一份 `listing-core/scripts/validate_fields.py`，判定口径一致：

- **单条交互链路**（listing-core Stage 3）走 `listing-core/scripts/run_full.py finish`，它串起 `validate_fields.py` → `finalize_listing.py`，退出码 2 表示字段安检未过、stdout 直接列出要重写的字段。
- **Core 批量链路**不维护第二套校验器：每行仍由 `listing-core/scripts/run_full.py finish` 执行同一套 validate → finalize，并保留局部重写回环；批量层只在所有行结算后合并已通过的 `listing-final.json`。

## 产物与落盘

本 skill 只把 `listing-draft.json` 对象交回 `listing-core`，由 `run_full.py finish` 统一走 `validate_fields.py` → `finalize_listing.py` 落盘定稿。草稿本身不是交付物，写作未过安检前不得对外展示。

- 不产生独立 UI 产物，也**不要**为它单独调 `save-json-artifact.mjs` 造一份中间文件。
- 传输层与命名的完整规则见 `listing-core/references/output-schema.md` §1。
