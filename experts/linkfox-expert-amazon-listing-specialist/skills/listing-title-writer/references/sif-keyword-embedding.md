# SIF 流量词埋词规则（低成本接入）

> **何时读取**：执行 title-writer 前必读，与 `amazon-title-policy-2026.md` 同一轮读取。
> **一句话**：埋词只消费**已有**关键词数据，本 Skill 默认**不发起**任何付费检索。

## 为什么要埋 SIF 词

75 字符 Title + 125 字符 Item Highlights 一共只有 200 字符，字字要换流量。
凭产品事实写出来的词是「卖家语言」，SIF 给的是买家真实搜过、真实成交的词
（搜索量排名、自然位、点击转化率、增长标志）。埋词不再是堆砌，而是**用真实流量数据
决定这 200 个字符先给谁**。

## 关键词四维分流（对齐 AI 导购的四个问题）

| 桶 | 定义 | 目标字段 | 典型形态 |
|----|------|---------|---------|
| **核心词 core** | 品类本体，回答「你是什么」 | **Title**（必埋 1 个） | `dog water bottle`、`gan usb-c charger` |
| **属性词 attribute** | 规格 / 材质 / 兼容 / 数量 | Title 埋 1 个最关键，其余进 **Highlights** | `19 oz`、`stainless steel`、`usb-c`、`bpa free` |
| **场景词 scenario** | 场景 / 人群 / 用途，回答「适合谁」 | **Item Highlights** | `for hiking`、`for small dogs`、`travel` |
| **痛点词 pain** | 问题 / 顾虑，回答「解决什么」 | **五点**（交接 `listing-bullet-writer`），Highlights 最多带 1 个 | `leakproof`、`no spill`、`easy to clean` |

铁律：
- Title 只放 core + 最多 1 个 attribute（+ 可选 1 个场景锚点），**绝不并列多个场景词**。
- 痛点词不进 Title。硬塞痛点词是老版堆词思维，会挤掉品类词、拉低 AI 对品类的判定信心。
- 一个词只埋一次。Title 出现过的词，Highlights 不再重复同一短语。
- 埋词不得改变产品事实：SIF 词与商品事实冲突时**丢词，不改事实**。

## 成本策略（默认路径 = 0 次额外调用）

| 场景 | 关键词来源 | 额外检索成本 |
|------|-----------|------------|
| 完整 Listing 链路（listing-core） | 上游 `listing-keyword-matrix-build` 已落盘的 `scored_table` | **0** |
| 调用方直接传 `keyword_plan` / `keywords_top` | 直接消费 | **0** |
| 批量表格 fast path | 分块级 `keyword_plan_cache`，同 ASIN / 同款只规划一次 | **0** |
| 只有 ASIN、无任何关键词数据 | `keyword_source_policy` 决定，默认 `reuse_only` → 降级 | **0** |
| 用户明确同意补词 | `keyword_source_policy=fetch_if_missing`，按**去重后的 ASIN** 各调一次 matrix | 每个 ASIN ≤1 次 |

强制约束：

1. **禁止在本 Skill 内调用外部关键词服务或网络网关**；需要补词时由宿主提供
   `listing-keyword-matrix-build`（它自带 24h 缓存与 SellerSprite backup）。
2. **retry 不重新取词**。字符超限、禁用词命中等 retry 一律复用同一份 `keyword_plan`。
3. **批量默认 `reuse_only`**。50 行表格若每行都取词就是 50 次付费调用；需要补词时先向用户
   报「去重后 N 个 ASIN、预计 N 次检索」，得到确认再执行，且一次性批量取完。
4. **无数据不编造**。降级时 `keyword_source="heuristic"`，从 `legacy_title` / `product_facts`
   抽词，`used_keywords[].source` 标 `heuristic`，禁止伪造搜索量、排名或 value_score。

## 分桶脚本（本地、无网络）

规则化分桶不占用 LLM 轮次，也把喂给模型的词表从 50 行压到 ~20 行：

```bash
python3 scripts/plan_keywords.py <keyword-matrix.json> \
  --top 6 --brand "PawGo" --banned "best,cheapest" --exclude-brand "HYDAWAY" \
  --out reports/title_writer_keyword_plan_<asin>.json
```

- 输入：`listing-keyword-matrix-build` 的 `Saved full response` 路径（也接受
  `{"keywords":[...]}` 或裸数组）。
- 输出（stdout 紧凑 JSON）：`keyword_plan{core,attribute,scenario,pain}`、
  `primary_keyword`、`title_pool` / `highlights_pool` / `bullets_pool`、`stats`。
- 直接把这段 JSON 填进 prompt 的 `{keyword_plan_block}`；`--out` 落盘后可被 retry 与
  同款行复用。
- `stats.numeric_signals_available=false`（category_seed 等）时，prompt 里不要展示搜索量口径，
  只用词本身。

## 埋词自检（写完后必须做，成本为 0）

1. Title 是否含 `primary_keyword` 或其等价核心词？（缺失 → `title_missing_core_keyword`）
2. Title 前 50 字符是否已说清品类？
3. Highlights 是否至少埋 1 个场景词 / 1 个属性词，且不与 Title 重复短语？
4. `used_keywords` 是否标清 `field`（title / highlights）与 `source`（sif / sellersprite_backup /
   category_seed / heuristic）？
5. 未被采用但高价值的痛点词，是否放进 `handoff_keywords.bullets` 交给五点？

## 与下游的交接

```yaml
strategy.keyword_plan:        # 本次实际采用的分桶（精简版）
strategy.handoff_keywords:
  bullets: [...]              # 痛点词 → listing-bullet-writer
  backend: [...]              # 未上前台的长尾 → listing-search-terms-writer
meta.keyword_source: sif | sellersprite_backup | category_seed | heuristic | none
meta.keyword_fetch_count: 0   # 本 Skill 触发的额外检索次数，默认必须是 0
```

`listing-search-terms-writer` 做前台去重时，Title + Item Highlights 已埋的词不再进后台
搜索词；`handoff_keywords.backend` 是它的候选输入。
