---
name: listing-diff-meter
description: 评估生成的 listing 跟对标 ASIN 的差异度，返回标题/五点/描述三段的量化分数
  + 不达标字段定位 + 重写建议。是防侵权的核心质量门——铺货卖家被判抄袭最直接的指标。
  Use when pipeline finishes L4 writing. Output gate decides whether to ship or recycle.
  NOT for cross-batch comparison (use listing-batch-novelty-report instead).
---

# Listing · Diff Meter

## Core Concepts

L5 质量门的核心 Skill，也是 listing 工具最重要的差异化能力之一。给铺货卖家提供
"复刻安全度"的量化指标，让他们敢按下"开始批量"的按钮。算法上是字符 n-gram + 关键词 overlap +
句式 embedding 的综合分；产品上是直接对应到亚马逊"判定为重复 listing 的内部阈值"的代理指标。

## Invoke Schema

```yaml
inputs:
  - name: batch_id
    type: string
    required: true
  - name: row_index
    type: int
    required: true
  - name: fields_to_check
    type: array<enum>
    required: false
    default: [title, bullets, description]
    values: [title, bullets, description, search_terms]
  - name: comparison_targets
    type: array<string>
    required: false
    description: "对标 ASIN 列表，省略=只跟当前 row 的 target_detail 比对"
  - name: metric
    type: enum
    required: false
    default: difference
    values: [difference, similarity]
    description: "阈值语义。difference=差异度下限（现有行为，score≥threshold 通过）；
      similarity=相似度/重复率上限（用户说『重复率≤30%』时用，等价 diff_threshold=0.70，
      由调用方或本 skill 内部换算，报告中按用户语义回显）"
  - name: per_field_thresholds
    type: object
    required: false
    description: "字段级阈值覆盖，如 {title: 0.30, bullets: 0.30, description: 0.30}
      （metric=similarity 语义）。省略的字段回退 overall 阈值。来源：用户 spec
      （plan_source=user_flow 时由用户流程直接给出）"

outputs:
  - name: diff_report
    type: DiffReport
  - name: pass
    type: boolean
    description: "overall_score >= rule.hard.diff_threshold"

events:
  - name: diff_failed
    payload: { row_index, overall_score, threshold, weakest_field }

side_effects:
  - write_diff_score_to_asin_context
  - log_qa_attempt
```

## Dependencies

- 当前 harness 的本地 Python 执行能力：跑相似度计算（n-gram + embedding cosine）
- 内部 embedding 服务

## Execution Playbook

```
1. 加载
   ctx = runtime.state_reader.load(batch_id, row_index)
   draft = ctx.draft
   targets = [ctx.target_detail] if not comparison_targets else load_targets(comparison_targets)
   # 阈值解析：用户 spec > rule_snapshot。metric=similarity 时先换算 diff = 1 - sim
   thresholds = resolve_thresholds(
       per_field=inputs.per_field_thresholds,   # 用户字段级阈值（可缺）
       metric=inputs.metric or 'difference',
       fallback=ctx.rule_snapshot.hard.diff_threshold,
   )
   # 用户流程给出的阈值不受 rule-resolver [0.5, 0.95] 区间限制，
   # 仅要求换算后 diff 阈值落在 (0, 1)；换算与来源写入 diff_report.threshold_meta

2. 缓存检查
   cache_key = f"diff:{draft_hash}:{target_hashes}"
   if cached := runtime.cache.get(cache_key):
       return cached

3. 文本归一化
   def normalize(text):
       text = text.lower()
       text = remove_punctuation(text)
       text = stem_words(text)        # running → run
       text = remove_stopwords(text)
       return text
   
   for field in fields_to_check:
       draft_norm[field] = normalize(draft[field])
       target_norm[field] = normalize(targets[field])  # 多对标时拼接

4. 三种相似度计算

   4.1 字符 n-gram Jaccard（5-gram）
       def ngram_jaccard(a, b, n=5):
           grams_a = set(get_ngrams(a, n))
           grams_b = set(get_ngrams(b, n))
           return len(grams_a & grams_b) / len(grams_a | grams_b) if grams_a | grams_b else 0

   4.2 关键词 overlap 比率
       def keyword_overlap(a, b):
           kws_a = extract_top_keywords(a, top=20)
           kws_b = extract_top_keywords(b, top=20)
           return len(set(kws_a) & set(kws_b)) / len(set(kws_a) | set(kws_b))

   4.3 句式 embedding 相似度（cosine）
       def sentence_similarity(a, b):
           emb_a = embed(a)
           emb_b = embed(b)
           return cosine(emb_a, emb_b)

5. 综合分数（每个字段独立算）
   for field in fields_to_check:
       n_score = ngram_jaccard(draft_norm[field], target_norm[field])
       k_score = keyword_overlap(draft_norm[field], target_norm[field])
       s_score = sentence_similarity(draft[field], target[field])  # 不归一化以保留语义
       
       similarity = 0.4 * n_score + 0.4 * k_score + 0.2 * s_score
       diff_score = 1 - similarity
       
       diff_report[field] = {
           score: diff_score,
           pass: diff_score >= thresholds[field],   # 字段级阈值；未指定的字段用 overall 阈值
           breakdown: { ngram: 1-n_score, keyword: 1-k_score, sentence: 1-s_score },
       }

6. 五点的特殊处理（per-bullet diff）
   for i, bullet in enumerate(draft.bullets):
       # 跟对标每条 bullet 比，取最高相似度（最危险的对比）
       max_sim = max(
           combined_similarity(bullet, target_bullet)
           for target_bullet in target.bulletPoints
       )
       per_bullet[i] = { score: 1 - max_sim, pass: ... }
   
   bullets_overall = min([b.score for b in per_bullet])  # 木桶原理：最低的算总分

7. 标记冲突片段
   for field in fields_to_check:
       conflict_segments = find_consecutive_overlaps(
           draft[field], target[field],
           min_length=6  # 连续 ≥ 6 字符与对标重叠的片段
       )
       diff_report[field].conflict_segments = conflict_segments

8. 综合 pass 判定
   overall_score = weighted_avg({
       title: 0.4,
       bullets: 0.4,
       description: 0.2,
   })
   overall_pass = overall_score >= thresholds.overall and all(f.pass for f in diff_report.fields)

9. 生成 recycle_advice（如果 fail）
   if not overall_pass:
       weakest = min(fields, by=score)
       advice = generate_advice(weakest, conflict_segments[weakest])
       # 例: "标题中 'premium HEPA 13 filter' (字符 12-32) 跟对标完全一致，
       #      建议换成 'medical-grade HEPA filtration' 或 '13-grade purification core'"

10. 写入 + 记录
    ctx.diff_score = diff_report
    ctx.qa_log.append({
        attempt: ctx.draft_version,
        stage: 'diff_meter',
        pass: overall_pass,
        details: diff_report,
        timestamp: now()
    })
    runtime.state_writer.save(ctx, emit_phase='diff_measured')
    runtime.cache.set(cache_key, diff_report, ttl=infinity)
    
    if not overall_pass:
        emit diff_failed
```

## 输出 schema 示例

```json
{
  "title": {
    "score": 0.62,
    "pass": false,
    "breakdown": { "ngram": 0.55, "keyword": 0.68, "sentence": 0.72 },
    "conflict_segments": [
      {
        "text": "premium HEPA 13 filter",
        "draft_position": [12, 34],
        "target_position": [8, 30],
        "similarity": 1.0
      }
    ]
  },
  "bullets": {
    "score": 0.71,
    "pass": true,
    "per_bullet": [
      { "idx": 0, "score": 0.68, "pass": false, "conflicts": [...] },
      { "idx": 1, "score": 0.82, "pass": true, "conflicts": [] },
      { "idx": 2, "score": 0.75, "pass": true, "conflicts": [] },
      { "idx": 3, "score": 0.79, "pass": true, "conflicts": [] },
      { "idx": 4, "score": 0.69, "pass": false, "conflicts": [...] }
    ]
  },
  "description": {
    "score": 0.78,
    "pass": true,
    "breakdown": { "ngram": 0.82, "keyword": 0.71, "sentence": 0.81 }
  },
  "overall_score": 0.69,
  "pass": false,
  "weakest_field": "title",
  "recycle_advice": "标题里 'premium HEPA 13 filter'（字符 12-34）跟对标 1:1 重叠，建议换成 'medical-grade HEPA filtration' 或 '13-grade purification core'。五点第 1、5 条也有局部 6+ 字符重叠，需要打散改写。"
}
```

## recycle_advice 生成规则

为下次重写的 writer 提供"可执行"的具体反馈：

```python
def generate_advice(weakest_field, conflicts):
    if weakest_field == 'title':
        worst_segment = max(conflicts, key=lambda c: c.similarity)
        return f"标题中 '{worst_segment.text}' 跟对标 1:1 重叠，建议替换为同义表达"
    
    elif weakest_field == 'bullets':
        failed_indices = [b.idx for b in per_bullet if not b.pass]
        return f"第 {failed_indices} 条五点跟对标相似度过高，按 {failed_themes} 主题重写"
    
    elif weakest_field == 'description':
        return f"描述段落 {paragraph_indices} 跟对标雷同，建议换用 {alt_style} 风格重写"
```

writer 收到这个建议作为 `retry_after_diff_fail` 模式的 input。

## Failure Modes

| 错误 | 触发 | 处理 |
|---|---|---|
| target_detail_missing | ctx.target_detail 为空 | skip diff 计算，emit diff_skipped_warning，pass=true 兜底 |
| embedding_service_down | 句式相似度计算失败 | 降级到仅 ngram + keyword（权重重分配为 0.6 + 0.4） |
| draft_empty | draft 某个字段为空 | 该字段 score=0, pass=false |
| sandbox_timeout | 沙箱超时 | retry 1 次，仍失败则该字段 fail |

## Cache Strategy

```
key: diff:{draft_hash}:{target_hashes_sorted}
value: 完整 DiffReport
ttl: infinity
```

draft_hash 和 target_hashes 都进 key，任一改变就失效。

## Not Applicable

- 跨 batch 整体新颖度评估（用 `listing-batch-novelty-report`）
- 实时编辑期间的 diff 预览（独立 Skill，本 Skill 是一次性评分）
- 检测 listing 是否"足够像对标"（反向需求，本 Skill 是检测"够不够不像"）

## 设计权衡

**为什么综合分数权重是 0.4/0.4/0.2 而不是均分**：n-gram 和 keyword 是 Amazon 算法层面
重要的两个信号（直接影响"是否判定为重复 listing"），sentence embedding 主要用于
"看起来雷同但措辞不同"的微妙场景，权重低。

**为什么五点用 min（木桶原理）而不是 avg**：5 条里有 1 条跟对标 1:1 重叠就足够构成
侵权指控，平均掉这条变成"整体看着 OK"是危险的虚假安全感。

**为什么默认 threshold 是 0.7 而不是 0.8**：0.7 是亚马逊算法判定为"明显重复"和"还能争辩"
的经验分界。0.8 太保守，导致 writer 无法借鉴对标的高效结构。0.7 是产业实践的标准值。

**为什么 recycle_advice 要生成可执行建议**：单纯告诉 writer "diff 太低重写吧"等于没说，
writer 不知道改哪里。具体到"哪个片段 1:1 重叠 + 建议替换为什么"，writer retry 的成功率
从 30% 提升到 80%+。

## 产物与落盘

本 skill 不依赖专用保存器。调用方可直接消费上方 schema，或在自己的工作目录中保存为
UTF-8 JSON；不得要求 LinkFox 会话目录、HTML 渲染器或上传服务。

Core batch 如显式启用跨商品反聚类，本 Skill 只能在所有成功行完成各自 Core finalize 后作为批次级附加检查；不得替代每行 QA，也不得阻断 `finalize_batch.py` 对 Core manifest 的完成校验。结果必须落盘并传递真实绝对路径。
