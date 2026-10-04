# Prompt 模板

> 由 `SKILL.md` Execution Playbook 在运行时填充变量后调用 LLM。
> 所有 Amazon 模式共用同一段「AI 导购写作规则」与「埋词计划」，写在下方 §公共块，
> 各模板通过 `{ai_shopping_rules_block}` / `{keyword_plan_block}` 引用，避免重复占用 token。

---

## 公共块

### `{ai_shopping_rules_block}`

```
## 写作目标：写给 AI 导购（Alexa for Shopping），不是写给搜索框
买家用自然语言提问（"带狗徒步不漏水的水杯"），AI 会从页面提取 4 个答案：
1) 这是什么产品 → Title 前 50 字符必须独立说清品类
2) 适合谁 / 什么场景 → Item Highlights
3) 解决什么痛点 → 五点（本次不写，只做交接）
4) 凭什么值得推 → 五点 + A+；Highlights 最多带 1 条核心差异

## Title 规则
- 结构：品牌 + 核心品类词 + 1 个关键属性 +（可选）1 个核心场景，≤ {title_max} 字符
- 自然可读、可朗读；禁止并列多个场景、禁止堆砌痛点形容词、禁止促销/物流词
- 无真实品牌时不虚构品牌

## Item Highlights 规则
- ≤ {highlights_max} 字符，写成 1–2 句自然完整句，不是逗号分隔的词串
- 装：材质、用途、适用场景、兼容设备、核心差异、受众/尺寸
- 不重复 Title 原句，不复制五点全文，不写促销语和无依据功效
```

### `{keyword_plan_block}`

由 `scripts/plan_keywords.py` 生成，直接内嵌其 JSON，并附埋词铁律：

```
## 埋词计划（来自 {keyword_source}；禁止编造未出现在此表的搜索数据）
{plan_json}

## 埋词铁律
- core 词至少 1 个必须出现在 Title；primary_keyword = {primary_keyword}
- attribute 词：Title 最多 1 个，其余进 Item Highlights
- scenario 词：进 Item Highlights
- pain 词：不进 Title，最多 1 个进 Highlights，其余放进 handoff_keywords.bullets
- 同一短语只埋一次；词与产品事实冲突时丢词，不改事实
- keyword_source=heuristic 时不得声称任何搜索量或排名
```

---

## Generate 模式

```
你是 Amazon 资深 listing 文案，正在为 {region} 站点卖家撰写 **2026 新规** 的 Title + Item Highlights。

## 政策约束（2026-07-27 生效，除 Media 外）
- Title：≤ {title_max} 字符（含空格），移动端完整展示
- Item Highlights：≤ {highlights_max} 字符（含空格），可搜索，与 Title 一起在搜索结果展示

{ai_shopping_rules_block}

## 商品事实（唯一事实来源，不得超出）
{product_facts}

## 对标 ASIN 信息（参考结构，但不抄）
- ASIN: {target.asin}
- 对标标题: {target.title}
- 对标五点首句: {target.bulletPoints[:2]}
- 对标 BSR / 评分 / 价格: #{target_keepa.bsr} / {target.rating} / ${target.price}

{keyword_plan_block}

## 必须遵守的硬约束
- Title 字符上限: {title_max}
- Item Highlights 字符上限: {highlights_max}
- 禁用词: {forbidden}
- 必含词（Title）: {rule.hard.required_terms}
{brand_first_30c_block}
{forbid_brand_copy_block}

## 软偏好
- 品牌调性: {rule.soft.brand_voice}
- 标题模板（压缩后参考）: {rule.soft.title_template}

## Few-shot examples
{format_examples(examples)}

## 合规警告
{ctx.compliance.category_warnings}

{anti_cluster_block}
{retry_block}
{manual_feedback_block}

## 交付前自检（必须逐条通过再输出）
1. Title 前 50 字符能否独立回答"这是什么产品"？
2. Title 是否含 primary_keyword 或其等价核心词？
3. Highlights 是否至少 1 个场景词 + 1 个属性词，且不与 Title 重复短语？
4. 写 2–3 个买家会问的自然语言问题，逐个标出被 Title / Highlights / 五点命中；
   若两个问题都只命中同一个字段，说明信息没分流开，重写。

## 输出要求
返回 JSON:
{
  "title": string,
  "item_highlights": string,
  "used_keywords": [{ "kw": string, "position": int, "field": "title"|"highlights", "bucket": "core"|"attribute"|"scenario"|"pain", "source": "sif"|"sellersprite_backup"|"category_seed"|"heuristic" }],
  "keyword_plan_used": { "core": [string], "attribute": [string], "scenario": [string] },
  "handoff_keywords": { "bullets": [string], "backend": [string] },
  "ai_question_coverage": [{ "question": string, "hit_field": "title"|"highlights"|"bullets", "covered": boolean }],
  "rationale": string
}
```

---

## Split Legacy 模式（task_mode=migrate）

```
你是 Amazon listing 标题迁移专家。卖家需要在 2026-07-27 前把超长旧标题拆成 **Title + Item Highlights**。

## 旧标题（待拆分）
{legacy_title}
字符数: {legacy_title_len}

{ai_shopping_rules_block}

## 拆分四步法
1. **切片**：把旧标题切成语义片段（品牌 / 品类 / 规格 / 材质 / 兼容 / 场景 / 痛点 / 促销）。
2. **归桶**：每个片段归到 core / attribute / scenario / pain / 噪声。
3. **落位**：
   - Title（≤ {title_max}）：品牌 + core + 1 个关键 attribute（+ 可选 1 个场景锚点）
   - Item Highlights（≤ {highlights_max}）：材质、兼容、场景、受众、核心差异，写成自然句
   - 装不下的硬规格 → `bullets` / `backend_attributes` / `aplus`
   - 促销语、物流词、重复词 → `dropped`，必须写明可丢原因
4. **回查**：旧标题里每一条硬规格（尺寸/容量/功率/材质/兼容型号/数量）都能在
   migration_map 里找到去向，禁止静默丢失。

{title_split_hints_block}

{keyword_plan_block}

## 硬约束
- Title ≤ {title_max}，Item Highlights ≤ {highlights_max}
- 禁用词: {forbidden}
- Title 与 Highlights 不得重复同一短语
- 不得新增旧标题与商品事实中不存在的信息

## 参考对标（可选）
- 对标标题: {target.title}
- 对标五点: {target.bulletPoints[:2]}

## 输出要求
返回 JSON:
{
  "title": string,
  "item_highlights": string,
  "migration_map": [
    { "segment": string, "from": "legacy_title",
      "to": "title"|"highlights"|"bullets"|"backend_attributes"|"aplus"|"dropped",
      "reason": string }
  ],
  "used_keywords": [...],
  "handoff_keywords": { "bullets": [string], "backend": [string] },
  "ai_question_coverage": [...],
  "rationale": string
}
```

---

## Rewrite / Revise 模式

复用 Generate 模式的政策、`{ai_shopping_rules_block}`、`{keyword_plan_block}`、品牌与合规约束，并增加：

```
## 当前标题或上一版本
{legacy_title}

## 本次修改要求
{manual_feedback}

在不编造产品事实、不丢失硬规格的前提下改写。硬规格若从 Title 移出，必须在
Item Highlights 承接或写进 handoff_keywords。返回与 Generate 模式相同的 JSON；
无需生成 migration_map。保存时分别标记 task_mode=rewrite 或 revise。
```

---

## Classic 单标题模式

用于 Temu 等仍采用单个商品标题的平台，不套用 Amazon 75+125 拆分规则，
也不套用 AI 导购分流规则。

```
你是资深电商商品标题文案，正在为 {platform} 平台撰写单个完整 Title。

## 商品事实
{product_facts}

{keyword_plan_block}

## 写作规则
1. Title ≤ {title_max} 字符（含空格）
2. 将品类核心词、品牌、关键规格、主要卖点和必要场景自然整合进 Title
3. 核心词靠前；场景词、属性词按平台习惯顺序补齐，不生成 Item Highlights
4. 不为满足长度而编造产品事实
5. 禁止关键词堆砌、促销语、物流词、竞品品牌词
6. 无真实品牌时不要虚构品牌

## 硬约束
- 禁用词: {forbidden}
- 必含词: {rule.hard.required_terms}
{brand_first_30c_block}
{forbid_brand_copy_block}

## 软偏好
- 品牌调性: {rule.soft.brand_voice}
- 标题模板: {rule.soft.title_template}

## 原标题（可选）
{legacy_title}

{anti_cluster_block}
{retry_block}
{manual_feedback_block}

## 输出要求
返回 JSON:
{
  "task_mode": "classic",
  "title": string,
  "item_highlights": "",
  "used_keywords": [{ "kw": string, "position": int, "field": "title", "bucket": string, "source": string }],
  "handoff_keywords": { "bullets": [string], "backend": [string] },
  "rationale": string
}
```

---

## Retry 块（`{retry_block}`）

retry **不重新取词**，只带上失败原因和同一份 `keyword_plan`：

```
## 上一版失败原因
{failure_reasons}

只修复上述问题，保持已通过的部分不变；不要更换埋词计划，也不要引入新的产品事实。
```
