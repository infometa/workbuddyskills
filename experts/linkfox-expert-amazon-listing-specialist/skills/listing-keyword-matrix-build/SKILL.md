---
name: listing-keyword-matrix-build
description: 以当前商品为中心构建关键词布局：有成熟竞品 ASIN 时优先调用 SIF 拉取 16 维关键词布局，SIF 失败或无数据时用 SellerSprite 流量词备份；
  无 ASIN 的 create 新品/图片/表格场景，基于 Amazon 类目节点 + 商品事实生成 category_seed 关键词布局。
  产出 scored_table 供 listing-title-writer 等下游埋词。Use when need scored keyword candidates for a listing target.
  Claude Code 必须单脚本执行，禁止 curl/Bash 即兴 pipeline。
---

# Listing · 关键词布局构建

## Core Concepts

把"当前商品所在 Amazon 节点的候选词"变成 writer 可消费的关键词布局。

- 有成熟竞品 ASIN：优先走 `asin_sif`，SIF 提供真实搜索量、排名、转化和 16 维标志位；若 SIF 错误或空结果，自动走 `asin_sellersprite_backup`，使用 SellerSprite 的月搜索量、购买率、自然/广告排名和流量来源标签补齐关键词矩阵。
- 没有 ASIN：走 `category_seed`，从图片/规格/类目节点提炼核心词、功能词、场景词；不提供搜索量或数字评分。

本 Skill 是 L3 的核心价值转换器——决定 writer 该埋哪些词，比写作技巧本身更影响 listing 排名表现。

## Invoke Schema

```yaml
inputs:
  - name: asin
    type: string
    required: false
    description: "成熟竞品或已有商品 ASIN；无 ASIN 时必须提供 category_node/product_facts/seed_keywords"
  - name: category_node
    type: object
    required: false
    description: "Amazon 具体叶子节点，如 {path:[...], name:'Single-Serve Brewers', confidence:'medium'}"
  - name: product_facts
    type: object
    required: false
    description: "图片/OCR/规格文本提取的商品事实，用于 category_seed"
  - name: seed_keywords
    type: array<string|object>
    required: false
    description: "类目核心词、功能词、场景词；object 可含 keyword/source/field"
  - name: row_indices
    type: array<int>
    required: false
  - name: time_window
    type: enum
    required: false
    default: latelyDay_30
    values: [latelyDay_7, latelyDay_30, month, week]
    description: "SIF 数据时间窗口"
  - name: top_n_keywords
    type: int
    required: false
    default: 50
    description: "scored_table 输出条数"
  - name: scoring_weights
    type: object
    required: false
    default: { search_volume: 0.3, conversion: 0.3, natural_rank: 0.2, growth: 0.2 }

outputs:
  - name: built_count
    type: int
  - name: failed_rows
    type: array<{row_index, asin, error}>

events:
  - name: matrix_progress
    payload: { processed: int, total: int }
  - name: low_keyword_coverage_warning
    payload: { row_index, asin, raw_count: int }

side_effects:
  - write_target_keywords_to_asin_context
```

## Dependencies

- `linkfox-sif-asin-keywords`：有成熟 ASIN 时优先拉取 16 维标志位的关键词数据（由 `scripts/build_keyword_matrix.py` 内联调用，勿手写 curl）
- `linkfox-sellersprite-traffic-keyword`：SIF 返回错误或无关键词数据时的备份流量词数据源（同样由 `scripts/build_keyword_matrix.py` 内联调用，勿手写 curl）
- `scripts/score_keywords.py`：分层 + 打分纯逻辑（本地 import，非 sandbox）

## Claude Code 执行（强制）

本 skill **只有一条合法执行路径**：直接运行 `scripts/build_keyword_matrix.py`，stdout 原样保留。

### 付费检索预算

- ASIN-SIF 与 SellerSprite backup 都是计费能力；同一会话同一 `asin + region + time_window + top_n + exclude_brand` 只允许执行一次。
- `scripts/build_keyword_matrix.py` 默认启用 24h 缓存，且会缓存 `sif_no_data` / `sif_error` / `all_filtered` 等空结果；除非用户明确同意额外消耗，禁止使用 `--no-cache`。
- 空结果或错误不是自动重试信号。脚本只允许在同次 matrix 构建内自动尝试一次 SellerSprite backup；若 SIF 与 SellerSprite 都无有效关键词，create 场景转 `category_seed`，benchmark/rewrite 场景走 data-confidence 门禁，不得换 ASIN/换时间窗连续试探。

### 路径 A：有成熟竞品 ASIN，走 SIF

```bash
python3 scripts/build_keyword_matrix.py <<'EOF'
{
  "asin": "B07JB964VX",
  "region": "US",
  "time_window": "latelyDay_30",
  "top_n": 50,
  "banned_terms": [],
  "exclude_competitor_brand": "HYDAWAY"
}
EOF
```

### 路径 B：无 ASIN / 新品 / 图片建 Listing，走 category seed

```bash
python3 scripts/build_keyword_matrix.py <<'EOF'
{
  "region": "US",
  "category_node": {
    "path": ["Home & Kitchen", "Kitchen & Dining", "Coffee, Tea & Espresso", "Single-Serve Brewers"],
    "name": "Single-Serve Brewers",
    "confidence": "medium"
  },
  "product_type": "capsule coffee machine",
  "product_facts": {
    "core_terms": ["capsule coffee machine", "pod coffee maker"],
    "features": ["one touch brewing", "compact countertop"],
    "use_scenarios": ["home office coffee", "small kitchen"]
  },
  "seed_keywords": [
    {"keyword": "single serve coffee maker", "source": "category_node", "field": "Title"}
  ],
  "top_n": 50
}
EOF
```

输出 `stats.source_mode=category_seed`、`stats.coverage_warning=seed_only`。这是 create 场景主路径，不是失败降级；禁止伪造搜索量、排名或 value_score。

### SIF backup 行为

- 默认 `enable_sellersprite_backup=true`。当 SIF 返回错误、业务错误或 `data=[]` 时，脚本自动调用 `linkfox-sellersprite-traffic-keyword` 对同一 ASIN/站点做一次备份反查。
- backup 成功时输出 `stats.source_mode=asin_sellersprite_backup`、`stats.sellersprite_backup_used=true`。下游可以展示真实的搜索量/排名/转化字段，但应标注数据源为 SellerSprite backup。
- backup 不支持的站点或也无数据时，仍输出空 `scored_table`，`coverage_warning=sif_no_data` / `sif_error`，交由上层 data-confidence 门禁处理。
- 调试专用：可传 `force_keyword_source=sellersprite` 跳过 SIF 直接验证归一化逻辑；正式编排不要使用。

### 硬约束

| 禁止 | 必须 |
|------|------|
| `curl` 直调 SIF / SellerSprite / tool-gateway | 只跑 `scripts/build_keyword_matrix.py` |
| `/tmp/*.json` + `python3 -c json.load` | 读 stdout 的 `Saved full response: <path>` |
| 无 ASIN 时强行调用 SIF 或因 `sif_no_data` 阻断 create | 先识别 Amazon 类目节点，再用 category seed |
| 本 skill 内写标题/五点/描述 | 产出 `scored_table` 后交给 `listing-title-writer` 等下游 |
| 再用外部 sandbox 重跑打分 | 打分已在本 Skill 的 `score_keywords.py` 完成 |
| wrapper / subprocess 吞 stdout | stdout 含 `Saved full response` 供 acpx-bridge 渲染 |
| `python3 -c` 打开落盘 JSON 看 Top 词 | `python3 scripts/peek_matrix_keywords.py <path> --top 20` |
| `--no-cache` 或失败后立即重试 SIF/SellerSprite | 复用 24h 缓存；空结果走门禁或 category_seed |

预览 Top 关键词：

```bash
python3 scripts/peek_matrix_keywords.py "<Saved full response 绝对路径>" --top 20
```

可选参数：`--no-cache` 跳过 24h 缓存（仅用户确认额外消耗时使用）；`--inline` 额外打印完整 JSON。

### 落盘协议（skill-output-protocol）

传输层（stdout → acpx-bridge）：

```
Saved full response: <绝对路径>/linkfox/linkfox-listing-keyword-matrix-build-<ts>.json (<N> bytes)
```

载荷层（JSON 文件内容）：**裸 payload**，禁止 `type: "skill-output"` envelope。形状见 `references/output-schema.md`。

- 核心：`scored_table`（writer 用 `kw.text` / `kw.keyword`；category seed 行可用 `source/field/priority`）
- 前端表格：`keywords[]`（含 `keyword` + SIF 兼容字段）

## AgentStudio Runtime Playbook

```
1. 加载待处理行
   contexts = runtime.state_reader.load_batch(batch_id, row_indices)
   targets = [c for c in contexts if c.status == 'analyzing' and not c.target_keywords]

2. 命中缓存
   for ctx in targets:
       cache_key = f"keywords:{ctx.asin}:{region}:{time_window}:24h_bucket"
       cached = runtime.cache.get(cache_key)
       if cached:
           ctx.target_keywords = cached
           continue
       pending.append(ctx)

3. 调原子 Skill 拉数据
   for ctx in pending:
       sif_result = call_atomic_skill(
           'linkfox-sif-asin-keywords',
           {
               country: REGION_TO_COUNTRY_CODE[region],
               asin: ctx.asin,
               periodType: time_window.split('_')[0],
               periodValue: time_window.split('_')[1] or 30,
               pageSize: 100,    # 取足够多候选
               sortField: 'searchesRank',
           }
       )

4. 解析 SIF / SellerSprite 标志位 → KeywordMatrix
   matrix = {
       natural_traffic: filter(sif_result, isAccurateKw OR nfPosition),
       sp_ads: filter(sif_result, isSpAd),
       brand_ads: filter(sif_result, isBrandAd),
       conversion_top: filter(sif_result, isQualityKw),
       long_tail: filter(sif_result, isAccurateTailKw),
       growing: filter(sif_result, isSearchVolUpKw),
       declining: filter(sif_result, isSearchVolDownKw),
       multi_variant: filter(sif_result, isMultiVariantKw),
       ...
   }

5. 构建打分表（在 sandbox 里跑）
   sandbox_code = """
   import math
   
   def score_keyword(kw, weights):
       # 搜索量分（rank 越小越好，取 log 归一化）
       sv_score = 1 / (1 + math.log10(max(kw.searches_rank, 1))) * 100
       
       # 转化分（kw 上 ASIN 的转化占比，直接 0-1）
       conv_score = kw.conversion_score * 100 if hasattr(kw, 'conversion_score') else 50
       
       # 自然排名分（rank 越小越好）
       nr_score = 1 / (1 + math.log10(max(kw.natural_rank or 9999, 1))) * 100
       
       # 增长分（搜索量同比增长则加分）
       growth_score = 80 if kw.is_growing else (20 if kw.is_declining else 50)
       
       # 综合
       value = (
           weights['search_volume'] * sv_score +
           weights['conversion'] * conv_score +
           weights['natural_rank'] * nr_score +
           weights['growth'] * growth_score
       )
       
       reason = build_reason(kw, sv_score, conv_score, nr_score, growth_score)
       return {**kw, 'value_score': round(value, 1), 'reason': reason}
   
   scored = [score_keyword(kw, weights) for kw in all_keywords]
   scored.sort(key=lambda k: k['value_score'], reverse=True)
   return scored[:top_n]
   """
   
   scored_table = run_local_script('scripts/score_keywords.py', {
       data: {all_keywords: matrix_flat, weights: scoring_weights, top_n: top_n_keywords}
   })

6. 写入 context
   ctx.target_keywords = {
       natural_traffic: matrix.natural_traffic,
       sp_ads: matrix.sp_ads,
       conversion_top: matrix.conversion_top,
       long_tail: matrix.long_tail,
       growing: matrix.growing,
       declining: matrix.declining,
       scored_table: scored_table,   # ★ 核心产物
   }
   runtime.cache.set(cache_key, ctx.target_keywords, ttl=24h)
   runtime.state_writer.save(ctx, emit_phase='keyword_built')

7. 低覆盖率检测
   if len(scored_table) < 10:
       emit low_keyword_coverage_warning
       # writer 在这种情况下需要降级到 brainstorm mode
       # 编排 skill 必须读取 stats.coverage_warning 并走 data-confidence-protocol 门禁，禁止静默编造搜索量/评分
```

## 关键词价值打分算法

打分公式：

```
value_score = w_sv * search_volume_score
            + w_cv * conversion_score  
            + w_nr * natural_rank_score
            + w_gr * growth_score
```

各分项：

| 分项 | 计算 | 含义 |
|---|---|---|
| search_volume_score | 1 / (1 + log10(rank)) | 搜索量越大分越高 |
| conversion_score | 0-100 直接来自 SIF | 该词上该 ASIN 的转化占比 |
| natural_rank_score | 1 / (1 + log10(natural_rank)) | 自然排名越靠前分越高 |
| growth_score | 80/50/20 | 增长/平稳/下降 |

默认权重 `{0.3, 0.3, 0.2, 0.2}`，但 rule.context 可以调整：
- 抢窗口期场景 → 加大 growth_score 权重到 0.4
- 长尾铺货场景 → 加大 long_tail 关键词的额外加分
- 品牌精品场景 → 降低 search_volume，加大 conversion

## 关键词去重与冲突

```
- 大小写归一化（"USB-C" 和 "usb-c" 算同一词）
- 单复数归一化（cable / cables）
- 词序敏感（"red bag" vs "bag red" 不同词）
- 同义词识别（"earbuds" vs "earphones" 用 LLM 标记 is_synonym=true，但保留为两个独立 entry）
- 禁用词过滤（rule.hard.banned_terms 命中的直接剔除）
- 品牌词过滤（rule.hard.forbid_brand_copy=true 时，识别出的 brand keyword 剔除）
```

## Failure Modes

| 错误 | 触发 | 处理 |
|---|---|---|
| sif_no_data | SIF 与 SellerSprite backup 均没有该 ASIN 数据 | scored_table = [] + emit low_coverage |
| category_seed | 无 ASIN 的 create 场景 | 生成 seed_only 矩阵继续；禁止搜索量/排名/value_score |
| sif_timeout | SIF 调用超时 | 仅在同次构建内尝试 SellerSprite backup；失败则走门禁 |
| sandbox_error | 打分代码异常 | 降级到简单排序（按 search_volume_rank） |
| all_keywords_in_banned | 全部被禁用词过滤掉 | emit critical_coverage_warning，但仍写入空 table |
| region_not_supported | SIF 不支持该 region | warn，writer 走 brainstorm mode |

## Cache Strategy

```
key: keywords:{asin}:{region}:{time_window}:{24h_bucket}
value: KeywordMatrix 完整对象 (含 scored_table)
ttl: 24 小时
```

- scored_table 是缓存的核心，重算成本高（沙箱调用 + LLM 标同义词）
- rule.scoring_weights 不进 cache key（因为打分快速重算，原始 matrix 重用即可）
  → 严格来说应该进 key，但权重切换不频繁，简化处理

## Not Applicable

- 直接关键词发现（用 `linkfox-aba-data-mining`）
- 关键词竞品数量分析（用 `linkfox-sif-keyword-competition`）
- 长期趋势分析（用 `linkfox-google-trends`）

## 输出后下游消费

```
target_keywords.scored_table → 
  listing-title-writer (取 Top 5-10 埋标题)
  listing-bullet-writer (取 Top 15-25 分散到五点)
  listing-search-terms-writer (取剩余的低搜索量长尾词)

target_keywords.growing → 
  listing-title-writer (优先于平稳词)

target_keywords.conversion_top →
  listing-bullet-writer (作为 USP 提示)
```
