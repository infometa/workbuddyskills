---
name: listing-core
description: 平台无关的 Amazon Listing 主编排。基于用户或宿主已提供的商品事实、参考文案、关键词和评论证据，生成、改写、本地化或批量处理完整 Listing，并执行本地校验与定稿。
---

# Listing Core

这是完整 Listing 的唯一主编排。它不抓取外部数据、不连接店铺、不刊登、不上传文件，也不生成
特定平台的 UI 或 HTML。宿主负责把外部来源转换为本 Skill 可消费的文件或结构化输入。

## 模式

- `create`：根据已提供的本品事实从零生成。
- `rewrite`：根据现有 Listing 和修复目标改写。
- `benchmark`：参考用户提供的竞品文案结构，但不得移植竞品事实。
- `batch`：逐行执行相同流程，并在完成屏障后生成批次 JSON。

## 最低输入

- `product_facts`：本品可声明事实。`create` 必需。
- `source_listing`：现有文案。`rewrite` 必需。
- `reference_listing`：参考文案。`benchmark` 必需；只有 ASIN 不算证据。
- `keyword_matrix`：可选。没有真实关键词证据时，用 `listing-keyword-matrix-build` 生成
  `category_seed`，并保留“未经流量验证”的声明。
- `buyer_questions`、`review_evidence`：可选，只能消费已提供内容。

## 流程

1. `plan`：创建 run manifest，记录模式、站点、语言和证据边界。
2. `ingest`：载入本品事实、参考文本、关键词矩阵和可选评论证据。
3. `prepare-write`：生成写作规格，明确字段限制、品牌边界和禁用词。
4. 调用 `listing-copy-suite-writer` 生成 `listing-draft.json`。
5. `finish`：运行 `validate_fields.py`、本地合规扫描和事实校验；失败时只返回需修字段。
6. 校验通过后由 `finalize_listing.py` 输出 `listing-final.json`、`listing-final.md`、
   `ai-readiness.json` 和 manifest。评分仅在提供 deductions 时生成。

常用入口：

```bash
python3 scripts/run_pipeline.py plan --run-dir ./listing-run --mode create --own-facts ./facts.json
python3 scripts/run_pipeline.py ingest --run-dir ./listing-run --own-facts ./facts.json --keyword-matrix ./keywords.json
python3 scripts/run_pipeline.py prepare-write --run-dir ./listing-run --insight-bundle ./insight.json
python3 scripts/run_pipeline.py finish --run-dir ./listing-run --draft ./listing-draft.json --facts ./facts.json
```

## 数据置信度

- 用户或宿主提供且可追溯的事实可标记为 `provided`。
- 从商品事实推导的关键词标记为 `category_seed`，不得填充虚构的搜索量、排名或转化数据。
- 缺失规格保持缺失；不得从参考 Listing 复制材质、尺寸、认证、兼容性或性能数字。

## 输出

- `listing-final.json`：宿主集成的权威结构化产物。
- `listing-final.md`：人类可读文案。
- `ai-readiness.json`：本地内容完整度检查，不代表平台在线实测。
- `score-result.json`：可选的八维质量评分。
- `listing-batch-final.json`：批量完成后的结构化汇总。

本包不提供 XLSX、HTML、文件上传、商品库写回或刊登动作。宿主可自行基于 JSON 构建这些能力。

## 相关参考

- 数据边界：[references/data-confidence-protocol.md](references/data-confidence-protocol.md)
- 输出结构：[references/output-schema.md](references/output-schema.md)
- 批量执行：[references/batch-execution.md](references/batch-execution.md)
- 审计回喂：[references/audit-rewrite-handoff.md](references/audit-rewrite-handoff.md)
