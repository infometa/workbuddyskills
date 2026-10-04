---
name: listing-search-terms-writer
description: 生成 Amazon 后台的搜索词字段（Search Terms / Backend Keywords），
  填写前台 listing 没用上的低搜索量长尾词、同义词、拼写变体、人群词。
  Use when pipeline enters L4 phase. Internal Skill, called by playbook.
  Output goes to Flat File's `generic_keyword` column.
---

# Listing · Search Terms Writer

## Core Concepts

后台搜索词是 Amazon listing 的"隐藏关键词"——不展示给用户，但影响搜索匹配。
本 Skill 把"Title/Item Highlights/Bullets/Description 前台用过的关键词"取补集，加上同义词、拼写变体、人群词，
填入后台 ≤250 字符限制。是埋词链路的最后一环，"前台精准词 + 后台长尾词"组合
最大化覆盖搜索流量。

## Invoke Schema

```yaml
inputs:
  - name: batch_id
    type: string
    required: true
  - name: row_index
    type: int
    required: true
  - name: strategy
    type: enum
    required: false
    default: long_tail_complement
    values: [long_tail_complement, synonym_focus, persona_focus, mixed]
  - name: include_typos
    type: boolean
    required: false
    default: true
    description: "是否包含常见拼写变体（如 wifi/wi-fi/wi fi）"
  - name: include_competitor_brand_terms
    type: boolean
    required: false
    default: false
    description: "是否埋入对标品牌词（有侵权风险，默认 false）"

outputs:
  - name: search_terms
    type: string
    description: "空格分隔的关键词字符串，<=250 字符"
  - name: meta
    type: SearchTermsGenerationMeta

side_effects:
  - write_draft_search_terms_to_asin_context
```

## Dependencies

- 内部 LLM 调用（用于同义词扩展 + 拼写变体生成）
- 不调 Tier 1

## Execution Playbook

```
1. 加载 + 缓存
   ctx = runtime.state_reader.load(batch_id, row_index)
   cache_key = f"search_terms:{asin}:{rule_version}:{front_text_hash}"
   if cached := runtime.cache.get(cache_key):
       return cached

2. 收集已用关键词（前台）
   front_text = (
       ctx.draft.title + ' ' +
       (ctx.draft.item_highlights or '') + ' ' +
       '\n'.join(ctx.draft.bullets) + ' ' +
       ctx.draft.description
   )
   used_kws = extract_keywords(front_text)
   used_kws_normalized = [normalize(kw) for kw in used_kws]  # 大小写、单复数归一

3. 候选词池构建
   pool = []
   
   # 3.1 scored_table 里没埋的低价值长尾
   for kw in ctx.target_keywords.scored_table[30:]:  # 30 名以后是长尾
       if normalize(kw.text) not in used_kws_normalized:
           pool.append({text: kw.text, source: 'long_tail', score: kw.value_score})
   
   # 3.2 同义词扩展（LLM 生成）
   synonyms = llm_generate_synonyms(
       seed_keywords=[kw.text for kw in scored_table[:10]],
       language=rule.context.language,
       max_count=30
   )
   for syn in synonyms:
       if normalize(syn) not in used_kws_normalized:
           pool.append({text: syn, source: 'synonym', score: 50})
   
   # 3.3 拼写变体（如启用）
   if include_typos:
       variants = generate_spelling_variants(
           seed=[kw.text for kw in scored_table[:5]],
           lang=rule.context.language
       )
       for v in variants:
           pool.append({text: v, source: 'typo_variant', score: 30})
   
   # 3.4 人群词（来自 reviews.buyer_personas 或 rule.context.target_audience）
   if ctx.target_reviews and ctx.target_reviews.buyer_personas:
       persona_kws = extract_persona_keywords(ctx.target_reviews.buyer_personas)
       for pk in persona_kws:
           if normalize(pk) not in used_kws_normalized:
               pool.append({text: pk, source: 'persona', score: 60})
   
   # 3.5 场景词
   if ctx.target_reviews and ctx.target_reviews.use_scenarios:
       scenario_kws = extract_scenario_keywords(ctx.target_reviews.use_scenarios)
       for sk in scenario_kws:
           if normalize(sk) not in used_kws_normalized:
               pool.append({text: sk, source: 'scenario', score: 55})

4. 按 strategy 加权排序
   if strategy == 'long_tail_complement':
       boost = {long_tail: 1.5, synonym: 1.0, persona: 1.0, scenario: 0.8, typo_variant: 0.5}
   elif strategy == 'synonym_focus':
       boost = {synonym: 1.5, long_tail: 1.0, ...}
   elif strategy == 'persona_focus':
       boost = {persona: 1.5, scenario: 1.3, ...}
   
   for item in pool:
       item.weighted = item.score * boost[item.source]
   
   pool.sort(key=lambda x: x.weighted, reverse=True)

5. 过滤
   pool = [
       item for item in pool
       if normalize(item.text) not in rule.hard.banned_terms_normalized
       if normalize(item.text) not in ctx.compliance.extreme_terms_found_normalized
       if not (item.text == competitor_brand and not include_competitor_brand_terms)
   ]
   
   # 内部去重（同义词组取代表）
   pool = dedupe_by_normalized_form(pool)

6. 贪心填充到 ≤250 字符
   selected = []
   char_used = 0
   max_char = min(rule.hard.charset.search_terms_max, 250)
   
   for item in pool:
       # Amazon 后台搜索词以空格分隔，每个词不重复词根
       cost = len(item.text) + 1  # +1 for space
       if char_used + cost > max_char:
           continue
       if shares_root_word_with_any(item.text, selected):
           continue  # Amazon 不奖励重复词根
       selected.append(item)
       char_used += cost
   
   search_terms = ' '.join([item.text for item in selected])

7. 写入
   ctx.draft.search_terms = search_terms
   runtime.state_writer.save(ctx, emit_phase='search_terms_written')
   runtime.cache.set(cache_key, {search_terms, meta}, ttl=infinity)
```

## 落盘（强制）

```bash
python3 scripts/save_search_terms_output.py <<'EOF'
{"search_terms":"word1 word2 word3","keywords_selected":[],"meta":{}}
EOF
```

落盘产物 `linkfox-listing-search-terms-writer-<ts>.json`（会话目录 `data/`），载荷自带 `kind=listingSearchTerms`、`schema_version=1`；stdout 保留 `Saved full response:` 行（`listing-core/references/output-schema.md` §3.5）。一次 Bash 输出只允许一行该前缀。

- **始终严格校验**：超过 250 bytes 时返回非零码，原文不变；只重写失败字段
- `--strict` 仅为兼容旧调用保留，当前默认即严格模式
- 字节校验：`python3 scripts/byte_count.py "你的搜索词"`
- **前台重复校验（强制）**：加 `--check-against-listing <前台 Listing 的文件路径或文本>`，脚本以 Unicode NFKC + casefold 归一化完整词元，检查 Title、Item Highlights、Bullets、Description 已出现的词；命中时返回非零码且不删除原词。可多次传入。这里不做英文式词干裁切，避免破坏德语、法语等站点词：

```bash
python3 scripts/save_search_terms_output.py \
  --check-against-listing "<title 落盘绝对路径>" \
  --check-against-listing "<bullets 落盘绝对路径>" \
  --check-against-listing "<description 落盘绝对路径>" <<'EOF'
{"search_terms":"word1 word2 word3"}
EOF
```

`--dedup-from-listing` 作为旧参数别名仍可用，但语义同样是只检查、不修改；stderr 打印重复词明细。

## Amazon Search Terms 规则（产品知识）

Amazon 后台对 generic_keyword 字段的算法约束：

```
- 最长 ≤ 250 字节（英文 ≈ 250 字符，日文/中文按字节数）
- 空格分隔的"词组"内部按词根索引（"running shoes" 和 "shoe runner" 等价于词根 run+shoe）
- 同一词根重复不奖励（"running shoes" + "trail runners" → 第二个 run 是浪费）
- 不要重复前台已用的精确词（前台已经索引过）
- 不要写标点、特殊符号（被算法忽略）
- 单数包含复数（"shoe" 包含 "shoes"，写单数即可）
- 不写品牌词（即使是自己的，前台已用过）
- 不写极限词（同前台规则）
```

本 Skill 在贪心填充时按这些规则过滤。

## SearchTermsGenerationMeta

```yaml
total_char: int
keyword_count: int
source_distribution:
  long_tail: int
  synonym: int
  persona: int
  scenario: int
  typo_variant: int
overlap_with_front: int      # 跟前台关键词重叠数（应该为 0）
banned_terms_filtered: int   # 过滤掉了多少违规词
char_efficiency: float       # 选中词/池子大小
```

## Failure Modes

| 错误 | 触发 | 处理 |
|---|---|---|
| empty_pool | 候选池为空（前台用光了所有词） | 返回空串 + warn |
| char_exceed_no_break | 单词 > 250 字符 | skip 该词，继续 |
| synonym_llm_failed | LLM 生成同义词失败 | 跳过同义词来源，仅用其他来源 |
| all_filtered | 全部候选被过滤 | warn，返回空串 |

## Cache Strategy

```
key: search_terms:{asin}:{rule_version}:{front_text_hash}
value: { search_terms, meta }
ttl: infinity
```

front_text_hash 是 title + bullets + description 拼接后的 hash。前台改动会失效后台。

## Not Applicable

- 前台 SEO 关键词（用 title/bullet/description writer）
- Sponsored Products 广告词（不是 listing 字段，是广告 campaign 配置，不归本 Skill）
- Amazon Brand Registry 的 brand-stories 关键词（独立字段，不归本 Skill）

## 设计权衡

**为什么默认 include_typos=true 但 include_competitor_brand_terms=false**：
- 拼写变体（如 "wifi" / "wi-fi"）是搜索习惯差异，埋了不违规
- 对手品牌词埋了有被对方投诉的风险（Amazon 会下架）

**为什么贪心算法而不是动态规划**：Amazon 后台搜索词排序对 SEO 影响不大（算法看的是词根
覆盖度而非顺序），贪心足够好。动态规划增加复杂度但提升有限。

**为什么 cache 不依赖 strategy**：strategy 切换重算成本极低（不调 Tier 1），不进 key
让常见的 strategy 微调不触发缓存失效。
