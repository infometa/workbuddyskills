---
name: listing-description-writer
description: 生成 Amazon listing 的长描述（productDescription，没有 A+ 时显示这块）。
  根据 rule 决定写"3-段叙事"还是"列表式"或"问答式"。是 L4 写作的次要 Skill
  （不开 A+ 的 listing 才显示，但 A+ 文本块也复用这条产出）。
  Use when pipeline enters L4 phase. Internal Skill, called by playbook.
---

# Listing · Description Writer

## Core Concepts

L4 写作的"补充阵地"。Amazon 不开 A+ 时显示长描述，开了 A+ 也会作为 SEO 文本被搜索引擎索引。
本 Skill 把"标题 + 五点已经讲完的卖点"展开为长文本，重点是 SEO（埋长尾词 + 人群词）和
品牌故事建立（用户从五点跳到这里通常是已经考虑购买但还有疑虑）。

## Copy Specs

- 长描述 ≤1000 字符（含空格与基础 HTML 标签）。
- 推荐 2-4 段，符合 Amazon 后台格式。
- 支持基础 HTML 标签：`<br>`、`<p>`、`<strong>`、`<b>`；禁止复杂样式、脚本、链接和促销 CTA。
- 不逐句复制五点；只展开有证据的场景、材质、规格、兼容、安装/护理信息。

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
  - name: format_style
    type: enum
    required: false
    default: auto
    values: [auto, narrative, listicle, qa, scenario]
    description: "auto=由 rule.soft 推断"
  - name: seed
    type: int

outputs:
  - name: description
    type: string
  - name: meta
    type: DescriptionGenerationMeta

side_effects:
  - write_draft_description_to_asin_context
  - increment_draft_version
```

## Dependencies

- 内部 LLM 调用
- 不调 Tier 1

## Execution Playbook

```
1. 加载 + 缓存检查
   ctx = runtime.state_reader.load(batch_id, row_index)
   cache_key = f"desc:{asin}:{rule_version}:{title_hash}:{bullets_hash}"
   if first_draft and cached := runtime.cache.get(cache_key):
       return cached

2. 决定 format_style（如果 auto）
   if format_style == 'auto':
       style = infer_style_from(
           rule.soft.brand_voice,
           target.bulletPoints,
           target_category,
       )
       # 启发式：
       # - brand_voice 含 'narrative/story' → narrative
       # - 高客单价品类 (>$50) → narrative
       # - 工具/配件类 → listicle
       # - 母婴/家居 → scenario
       # - 默认 narrative

3. 长尾词分配
   # 标题用过 Top 10，五点用过 11-25
   # 描述用 26-50 的长尾词
   used_in_title = extract_keywords(title)
   used_in_bullets = extract_keywords_array(bullets)
   description_keywords = [
       kw for kw in ctx.target_keywords.scored_table[25:60]
       if kw.text not in used_in_title and kw.text not in used_in_bullets
   ]

4. 构建 prompt（按 style 分支）
   prompt = render_prompt_by_style(style, ...)

5. 调 LLM
   raw_output = llm.generate(prompt, temperature=0.7, seed=seed)

6. 后处理
   # 字符数
   if not in_range(len(desc), rule.hard.charset.description):
       retry_with_feedback(...)
   
   # 禁用词
   if any banned_terms in desc: retry
   
   # 关键词覆盖
   if keyword_hit_count < 10:
       warn but accept (description 关键词埋入是软目标)
   
   # 段落结构（narrative 需要 ≥ 3 段）
   if style == 'narrative' and paragraph_count < 3:
       retry_with_feedback("narrative 风格至少 3 段")
   
   # HTML 转义检查（Amazon 后台支持有限的 HTML）
   sanitize_html_tags(desc, allowed=['<br>', '<p>', '<strong>', '<b>'])

7. 写入 + 缓存
   ctx.draft.description = desc
   runtime.state_writer.save(ctx, emit_phase='description_written')
```

## 落盘（强制）

```bash
python3 scripts/save_description_output.py <<'EOF'
{"description":"...","style":"narrative","meta":{}}
EOF
```

落盘产物 `linkfox-listing-description-writer-<ts>.json`（会话目录 `data/`），载荷自带 `kind=listingDescription`、`schema_version=1`；stdout 保留 `Saved full response:` 行（`listing-core/references/output-schema.md` §3.4）。一次 Bash 输出只允许一行该前缀。

## Style 模板差异

### narrative（叙事型）

```
开头：场景引入或痛点共情
  "After a long day at work, the last thing you want is..."

中段：转折 + 解决方案（产品）
  "That's where {product} comes in. Designed for..."

收尾：信任建立 + CTA
  "Backed by {warranty}. Trusted by {social_proof}."

特点：2-4 段，第二人称，故事感强
适用：品牌精品、母婴、礼品、高客单价
```

### listicle（列表型）

```
开头：1-2 句产品定位

主体：用 <br><br> 分隔的功能点列表
  "✓ Fast Charging: 100W PD3.0..."
  "✓ Universal Compatibility..."
  "✓ Premium Build Quality..."

收尾：保障 + 兼容性

特点：紧凑、扫读友好
适用：3C、工具、配件、技术型产品
```

### qa（问答型）

```
预设 4-6 个购买决策问题：
  "Q: Will this fit my [device]?"
  "A: This is compatible with..."
  
  "Q: How long does the battery last?"
  "A: Up to 12 hours of continuous use..."

特点：直接回应购买犹豫
适用：技术参数复杂的品类（医疗器械、电子）
```

### scenario（场景型）

```
开头：定义目标用户
  "For busy parents who..."

主体：3-4 个使用场景描述
  "Morning routine: ..."
  "On the go: ..."
  "Bedtime: ..."

收尾：场景全覆盖的总结

特点：人群导向、场景具象
适用：家居、母婴、宠物、生活方式
```

## DescriptionGenerationMeta

```yaml
total_char: int
paragraph_count: int
style_used: string
keyword_coverage:
  total_hits: int
  by_value_tier: { high: int, medium: int, low: int }
review_quote_count: int        # 引用了几条 review 原话
banned_terms_hit: int
html_tags_used: array<string>
confidence: float
retry_count: int
```

## Failure Modes

| 错误 | 触发 | 处理 |
|---|---|---|
| char_out_of_range | 字符越界 | retry 带反馈 |
| paragraph_count_low | narrative < 3 段 | retry |
| banned_terms_hit | 禁用词命中 | retry |
| html_invalid | 不支持的 HTML 标签 | 自动清洗（不 retry） |
| keyword_coverage_critical | 完全没埋词 | warn 但接受 |
| style_inference_failed | format_style=auto 推断失败 | 用 narrative 兜底 |

## Cache Strategy

```
key: desc:{asin}:{rule_version}:{title_hash}:{bullets_hash}
value: { description, meta }
ttl: infinity
```

description 依赖 title 和 bullets 已生成（要呼应、不重复），所以两者的 hash 都进 key。

## Not Applicable

- A+ 模块化内容生成（Amazon A+ 是布局+图片+文本块，不是纯文本，需要专门的
  `listing-a-plus-writer` Skill 处理布局）
- HTML 富文本（Amazon 后台描述支持有限 HTML，本 Skill 输出已限制 tag）

## 设计权衡

**为什么 description 不进 anti-cluster**：长描述天然差异化大（通常 500-1000 字），cluster 内
相互雷同的概率低，不值得为这个加复杂度。如果检测到 description.diff_score 偏低，
diff-meter 会触发 retry，足够兜底。

**为什么用 4 种 style 而不是 1 种**：rule.soft.brand_voice 自由文本本身就涵盖大量风格诉求，
但落到长描述写作时需要"结构选择"——这是 narrative vs listicle 这种宏观结构层面的决策，
不是文字风格层面的。所以暴露 4 个 style 作为"结构骨架"，brand_voice 作为"文字风格"，
两者正交。
