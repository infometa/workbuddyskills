---
name: listing-bullet-writer
description: >-
  生成 Amazon listing 的 5 条五点描述（bullet points），按 rule 指定的结构
  （STAR/PAS/FABE/custom）+ keyword scored table + reviews 洞察 + anti-clustering 综合产出。
  Use when pipeline enters L4 phase. Internal Skill, called by playbook.
  Accepts generation_mode：'first_draft' | 'retry_after_diff_fail' | 'manual_revise'.
---

# Listing · Bullet Writer

## Core Concepts

L4 写作层的"说服力武器"。标题决定能不能被搜到 + 被点击，五点决定能不能把点击变成下单。
本 Skill 同时满足结构合规（STAR/PAS/FABE）、关键词二次覆盖（标题埋不下的中价值词）、
痛点回应（review 挖到的 cons/unmet_needs）、批次差异化（cluster 上下文）。

## Copy Specs

> 以下为 Layer B 默认规格。调用方提供用户 spec（`save_bullets_output.py --spec spec.json`）时，
> 条数/单条区间/合计区间按 spec 执行（平台底线：单条 ≤500、合计 ≤2500 不可突破）。

- 五点描述必须恰好 5 条。
- 单条五点默认交付上限 ≤255 字符（平台外层上限 ≤500）；建议 150-200 字符，201-255 只提示、不触发重写。
- 五点合计 ≤1275 字符（255×5）。
- 默认使用 FABE/BAF：Benefit 开头，接 Advantage，最后用 Feature/Evidence 落地。
- 自然埋入高价值词，不堆砌，不重复 Title 或 Item Highlights 原句。

## Invoke Schema

```yaml
inputs:
  - name: batch_id
    type: string
    required: true
  - name: row_index
    type: int
    required: true
  - name: generation_mode
    type: enum
    default: first_draft
    values: [first_draft, retry_after_diff_fail, manual_revise]
  - name: manual_feedback
    type: string
    required: false
  - name: batch_cluster_context
    type: BatchClusterContext
    required: false
  - name: title_already_generated
    type: string
    required: false
    description: "标题已生成时传入，五点要跟标题呼应不要重复信息"
  - name: item_highlights_already_generated
    type: string
    required: false
    description: "Item Highlights 已生成时传入，五点不重复 Highlights 已写的场景/收益"
  - name: seed
    type: int
    required: false

outputs:
  - name: bullets
    type: array<string>
    description: "恰好 5 条"
  - name: meta
    type: BulletGenerationMeta

side_effects:
  - write_draft_bullets_to_asin_context
  - increment_draft_version
```

## Dependencies

- 内部 LLM 调用
- 不直接调 Tier 1

## Execution Playbook

```
1. 加载 ASINContext + 准备输入
   ctx = runtime.state_reader.load(batch_id, row_index)
   rule = ctx.rule_snapshot
   target = ctx.target_detail
   reviews = ctx.target_reviews   # 可缺
   
   # 关键词分配（标题 + Highlights 用过的不重）
   used_in_title = extract_keywords_from_title(title_already_generated)
   used_in_highlights = extract_keywords_from_text(item_highlights_already_generated or '')
   bullet_keywords = [
       kw for kw in ctx.target_keywords.scored_table[:25]
       if kw.text.lower() not in used_in_title.lower()
       and kw.text.lower() not in used_in_highlights.lower()
   ][:20]

2. 缓存检查
   cache_key = f"bullets:{asin}:{rule_version}:{title_hash}:{cluster_hash}"
   if first_draft and (cached := runtime.cache.get(cache_key)):
       ctx.draft.bullets = cached.bullets
       return cached

3. 决定结构模板
   structure = rule.soft.bullet_structure or 'FABE'
   # STAR: Situation-Task-Action-Result
   # PAS: Problem-Agitate-Solution
   # FABE: Feature-Advantage-Benefit-Evidence
   # custom: 用户在 rule.soft 里指定具体节奏

4. 决定 5 条内容主题（这是 bullet writer 独有的"结构化策划"）
   themes = plan_bullet_themes(
       structure=structure,
       reviews=reviews,
       keywords=bullet_keywords,
       target_bullets=target.bulletPoints,
   )
   # 典型 5 条分配（FABE + review-driven）：
   # #1: 核心卖点（来自 reviews.top_pros 的第 1 项）
   # #2: 差异化优势（来自 reviews.unmet_needs，"我们做了竞品没做的"）
   # #3: 适用场景（来自 reviews.use_scenarios）
   # #4: 规格 + 兼容性（FABE 的 Feature）
   # #5: 售后保障 / 风险消除（来自 reviews.top_cons 的反向 Solution）

5. 构建主 prompt（见下方）

6. 调 LLM
   raw_output = llm.generate_structured(
       prompt=full_prompt,
       output_schema=BulletOutput,
       temperature=0.7,
       seed=seed,
   )

7. 后处理与校验
   bullets = raw_output.bullets
   
   # 必须恰好 5 条
   if len(bullets) != 5:
       retry_with_feedback(f"必须恰好 5 条，当前 {len(bullets)} 条")
   
   # 默认生成目标 150-200；默认交付上限 255、平台外层上限 500；5 条合计不超过 1275（255×5）
   for i, b in enumerate(bullets):
       min_c, max_c = rule.hard.charset.bullets or [0, 255]
       max_c = min(max_c, 500)
       if not (min_c <= len(b) <= max_c):
           retry_with_feedback(f"第 {i+1} 条字符 {len(b)}，目标 {min_c}-{max_c}")
   if sum(len(b) for b in bullets) > 1275:
       retry_with_feedback("五点合计字符超过 1275")
   
   # 首词动词强制（如 rule.soft.bullet_starter_pattern == 'verb'）
   if rule.soft.bullet_starter_pattern == 'verb':
       for i, b in enumerate(bullets):
           first_word = b.split()[0]
           if not is_verb(first_word):
               retry_with_feedback(f"第 {i+1} 条必须以动词开头，当前: {first_word}")
   
   # 禁用词扫描
   for b in bullets:
       for f in forbidden_terms:
           if f.lower() in b.lower():
               retry_with_feedback(f"禁用词 {f} 命中")
   
   # anti-cluster（如果 batch_cluster_context 存在）
   if batch_cluster_context:
       # 五点跟 sibling 雷同性以"每条首句"度量
       for sibling_bullets in batch_cluster_context.sibling_bullets:
           for i in range(5):
               if first_clause(bullets[i]) ≈ first_clause(sibling_bullets[i]):
                   retry_with_feedback(f"第 {i+1} 条首句跟 sibling 雷同")
   
   # 内部去重（5 条之间不能相互重复信息）
   if internal_redundancy(bullets) > 0.3:
       retry_with_feedback("5 条之间信息重复度高，每条应有独立主题")

8. 计算 meta
   meta = {
       per_bullet_char: [len(b) for b in bullets],
       structure_compliance: check_structure_match(bullets, structure),
       keyword_coverage: count_keyword_hits(bullets, bullet_keywords),
       review_driven_count: count_themes_from_reviews(bullets, reviews),
       anti_cluster_applied: bool(batch_cluster_context),
       confidence: ...
   }

9. 写入 + 缓存
   ctx.draft.bullets = bullets
   ctx.draft_version += 1
   runtime.state_writer.save(ctx, emit_phase='bullets_written')
   runtime.cache.set(cache_key, {bullets, meta}, ttl=infinity)
```

## 落盘（强制）

```bash
python3 scripts/save_bullets_output.py <<'EOF'
{"bullets":["...","...","...","...","..."],"themes_used":[],"keyword_distribution":[]}
EOF
```

stdout 保留 `Saved full response:` 行（`skills/listing-core/references/output-schema.md` §3.3）。

## Prompt 模板（FABE 结构示例）

```
你是 Amazon 资深 listing 五点文案，正在为 {region} 站点的卖家写 5 条 bullet points。

## 对标参考
- 对标五点（参考节奏，不抄）:
{format_target_bullets(target.bulletPoints)}

## 已生成的标题（五点必须跟标题呼应）
{title_already_generated}

## 5 条主题规划（按此结构产出）
- 第 1 条 · 核心卖点: {themes[0]}
- 第 2 条 · 差异化优势: {themes[1]}
- 第 3 条 · 适用场景: {themes[2]}
- 第 4 条 · 规格与兼容: {themes[3]}
- 第 5 条 · 售后保障: {themes[4]}

## 关键词分配（每条尽量 3-4 个中价值词）
{format_keyword_allocation(bullet_keywords)}

## 用户评论洞察（写作时要用上）
- 用户最赞: {reviews.top_pros[:3]}
- 用户痛点: {reviews.top_cons[:3]}
- 未被满足的需求（差异化金矿）: {reviews.unmet_needs[:3]}
- 主要使用场景: {reviews.use_scenarios[:3]}
- 目标人群: {reviews.buyer_personas[:2]}

## 硬约束
- 每条字符: 默认交付上限 ≤255、平台外层上限 ≤500（建议 150-200，201-255 只提示）；5 条合计 ≤1275（255×5）
- 禁用词: {forbidden}
- 受监管物质及相关渠道/用途词（如 cannabis、marijuana、weed、cbd、thc、dispensary）不得出现在任何 bullet；即使它们来自关键词表、竞品文案或评论，也只能替换为与商品事实相符的中性使用场景。
{% if rule.soft.bullet_starter_pattern == 'verb' %}
- 每条必须以动词开头（如 Enjoy, Experience, Unlock, Eliminate）
{% endif %}

## 软偏好
- 结构: FABE (Feature → Advantage → Benefit → Evidence)
- 品牌调性: {rule.soft.brand_voice}

## Few-shot examples
{format_examples_bullets(examples)}

{% if batch_cluster_context %}
## Anti-clustering
本批次同 cluster 已生成 N 条，sibling 五点：
{batch_cluster_context.sibling_bullets}
→ 你的 5 条首句不能跟任何 sibling 雷同；卖点切入角度要选未被使用的
{% endif %}

## 输出
返回 JSON: {
  "bullets": [string * 5],
  "themes_used": [string * 5],
  "keyword_distribution": [array of keywords used per bullet]
}
```

## BulletGenerationMeta

```yaml
per_bullet_char: array<int>             # 5 个值
structure_compliance: 0-1               # 是否符合声明的 STAR/PAS/FABE 节奏
keyword_coverage:
  total_hits: int
  distribution: array<int>              # 每条命中数
  value_score_avg: float
review_driven_count: int                # 5 条里有几条来自 review 洞察
anti_cluster_applied: boolean
internal_redundancy: float              # 0-1, 5 条内部信息重复度
confidence: float
retry_count: int
```

## Failure Modes

| 错误 | 触发 | 处理 |
|---|---|---|
| not_exactly_5 | 产出 != 5 条 | retry |
| char_out_of_range | 任意条字符越界 | retry 带具体行号 + 目标 |
| starter_pattern_violation | 首词模式不匹配 | retry |
| banned_terms_hit | 禁用词命中 | retry |
| anti_cluster_violation | 与 sibling 雷同 | retry 强化提示 |
| internal_redundancy_high | 5 条相互重复 > 30% | retry |
| review_data_missing | reviews 缺失 | 降级到无 review 模式（仍可跑） |
| llm_invalid_json | LLM 输出错误 | retry |
| all_retries_exhausted | 3 次 retry 仍 fail | row=failed |

## Cache Strategy

```
key: bullets:{asin}:{rule_version}:{title_hash}:{cluster_hash}
value: { bullets, meta }
ttl: infinity
```

title_hash 进 key 是因为五点要跟标题呼应（标题改了五点也得重生成）。

## Not Applicable

- 标题（用 listing-title-writer）
- 长描述（用 listing-description-writer）
- 单条五点修改（仍调本 Skill，但传 manual_feedback 指定改第几条）
- 多语言并行（本 Skill 一次只产一种语言）

## 设计权衡

**为什么把"5 条主题规划"独立成 plan_bullet_themes 一步**：让 LLM 一次同时决定
"写什么"和"怎么写"会导致五条变成"五个角度切同一个卖点"。先做主题规划锁定结构，
再让 LLM 在确定的主题框架内发挥，产出质量稳定得多。

**为什么默认结构是 FABE 而不是 STAR**：STAR 更适合服务/解决方案，FABE 更适合实体商品。
铺货卖家 90% 是实体品，FABE 是合理默认值。

**review_data_missing 时不直接失败**：review-mine 是可选 Skill，bullet-writer 必须能
在没有 review 数据时也产出可用结果（虽然质量稍降）。降级方案是不让"第 2 条"
追求差异化（unmet_needs 来自 review），改为强化第 4-5 条的规格与保障。
