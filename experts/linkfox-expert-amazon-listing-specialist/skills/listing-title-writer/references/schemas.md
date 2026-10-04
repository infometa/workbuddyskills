# Schema 参考

## Invoke Schema（摘要）

见 `SKILL.md` §Invoke。关键输入：

- `task_mode`: `generate` | `rewrite` | `migrate` | `revise` | `classic`
- `source_mode`: `generate` | `split_legacy`，仅向后兼容
- `legacy_title`: 原标题或上一版本；rewrite/migrate/revise 必填
- `platform` / `target_platform`: 目标平台；非 Amazon 值自动路由到 classic
- `title_only=true` 或 `include_item_highlights=false`: 自动路由到 classic
- `policy.title_max`: classic 标题上限，正整数，默认 200
- `title_split_hints`: `{ must_keep_in_title[], must_migrate_to_highlights[], preserve_word_order }`
- `generation_mode`: `first_draft` | `retry_after_diff_fail` | `manual_revise`

埋词相关输入（详见 `sif-keyword-embedding.md`）：

- `keyword_plan`: `scripts/plan_keywords.py` 的输出对象，最高优先级
- `keyword_plan_path`: 已缓存的埋词计划文件路径（批量与 retry 复用）
- `keyword_matrix_path`: `listing-keyword-matrix-build` 落盘 JSON 路径，本 Skill 用
  `plan_keywords.py` 本地分桶，不发起检索
- `keywords_top`: 兼容旧调用的扁平词表
- `keyword_source_policy`: `reuse_only`（默认） | `fetch_if_missing` | `none`
  - `reuse_only`：无关键词数据时降级为 `heuristic`，**不发起任何付费检索**
  - `fetch_if_missing`：仅在用户明确同意后使用；按去重 ASIN 各调一次
    `listing-keyword-matrix-build`，retry 阶段一律禁止

路由优先级：显式 `task_mode` → 显式 `source_mode=split_legacy` → 非 Amazon
平台或单标题信号 → 非空 `legacy_title` → generate。自然语言中的“Temu、
老版标题、单标题、只写 Title、不拆 Highlights”必须在构造调用参数前转换为
classic，不要求用户提供内部枚举值。

## TitleOutput（generate）

```yaml
title: string              # max 75（非 Media）
item_highlights: string    # max 125
used_keywords: array       # min 2；每项 { kw, position, field, bucket, source }
keyword_plan_used: object? # { core[], attribute[], scenario[] }
handoff_keywords: object?  # { bullets[], backend[] }
ai_question_coverage: array? # [{ question, hit_field, covered }]，建议 2-3 条
rationale: string          # max 300
```

- `bucket`: `core` | `attribute` | `scenario` | `pain`
- `source`: `sif` | `sellersprite_backup` | `category_seed` | `heuristic`

## TitleSplitOutput（split_legacy）

```yaml
title: string
item_highlights: string
migration_map: array   # min 1；to ∈ title|highlights|bullets|backend_attributes|aplus|dropped
used_keywords: array
handoff_keywords: object?
ai_question_coverage: array?
rationale: string
```

`migration_map[].to=dropped` 必须给出可丢原因（重复 / 促销语 / 无事实依据）；
硬规格（尺寸、容量、功率、材质、兼容型号、数量）不允许落到 `dropped`。

## ClassicTitleOutput（单标题）

```yaml
task_mode: classic
title: string             # max policy.title_max，默认 200
item_highlights: ""       # 必须为空
used_keywords: array
rationale: string
```

## TitleGenerationMeta

```yaml
source_mode: enum
title_char_count: int
item_highlights_char_count: int
keyword_hit: array<{ keyword, position, field, value_score }>
keyword_coverage_score: float
migration_coverage: float       # split_legacy
migration_lost_segments: string[]
used_templates: array
anti_cluster_applied: boolean
keyword_source: sif | sellersprite_backup | category_seed | heuristic | none
keyword_fetch_count: int        # 本 Skill 触发的额外检索次数，默认必须为 0
keyword_bucket_coverage: object # { core, attribute, scenario, pain } 各自的埋词数
ai_question_coverage_rate: float
brand_voice_match_score: float
confidence: float
retry_count: int
amazon_title_policy: compact_75 | classic_title_only | legacy_200 | media_exempt
```

## 固定输出

保存脚本把上述 LLM 内容归一化为
`linkfox-listing-title-workbench/v1`。单条和批量的信封一致，差别仅在
`rows[]` 数量；字段定义见 `references/output-schema.md`。

## confidence 算法

`keyword_coverage` 按四维分桶折算：Title 命中 core=0.5、Highlights 命中 scenario=0.25、
Highlights 命中 attribute=0.25；`keyword_source=heuristic` 时该项最高按 0.6 计。

```
keyword_coverage * 0.30
+ migration_coverage * 0.25   # generate 时按 1.0
+ char_compliance * 0.25
+ brand_voice_match * 0.10
+ anti_cluster_success * 0.10
```

## Failure Modes

| 错误 | 处理 |
|------|------|
| title_char_out_of_range | retry ≤2 |
| highlights_char_out_of_range | retry ≤2 |
| highlights_empty_on_split | retry |
| classic_title_out_of_range | retry ≤2 |
| classic_highlights_not_empty | failed；重写时只保留 Title |
| title_missing_core_keyword | warning；下一次 retry 优先修复，不单独触发 retry |
| title_highlights_duplicate_phrase | warning；建议改写 Highlights |
| highlights_missing_scenario | warning |
| keyword_source_unavailable | warning；标记 keyword_source=heuristic，禁止编造搜索数据 |
| migration_incomplete | retry + lost_segments |
| required_terms_missing | retry |
| banned_terms_hit | retry |
| anti_cluster_violation | retry |
| all_retries_exhausted | status=failed |
