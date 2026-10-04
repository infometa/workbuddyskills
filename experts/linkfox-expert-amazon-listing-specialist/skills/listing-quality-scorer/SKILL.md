---
name: listing-quality-scorer
description: 对已生成或已提供的 Amazon Listing 做证据化质量评分，输出统一 scorePanel、扣分证据和 AI 导购准备度，是唯一评分事实源。用户要求打分、质量报告、before/after 对比，或 listing-audit 需要基础质量分时触发。路由判断：只回答「多少分、差在哪个维度」用本 Skill；要回答「为什么没流量、为什么不转化」并给出改哪些字段和文案之外的运营动作用 listing-audit；要产出新文案用 listing-core mode=rewrite。普通 listing-core 生成只跑本地基础质量门，不默认调用本 Skill。即使输入数据不完整也可输出 N/A 维度，但不得编造分数。
---

# Listing Quality Scorer

本 Skill 是唯一评分事实源。`listing-audit`、独立评分报告和 before/after 对比必须复用本 Skill；其他 Skill 不得维护第二套权重、hard gate、grade 或 overall 算法。

## 边界

- Core 基础 QA 负责 pass/fail，不等同于本 Skill 的数字评分。
- 本 Skill 评价 Listing 使用准备度，不承诺真实 CTR、CVR、收录或平台推荐。
- Alexa 问答实测(计费)未执行时，`aiReadiness.external_probe.probed=false`。
- 报告语言默认中文：`deductions[].reason` / `action`、`evidence[]` 的说明文字、`topIssues`、`quickFixes`、`gradeText` 和对话摘要一律中文；被评的 Listing 原文、关键词和字段名保留原文。被评 Listing 是英文不构成用英文出报告的理由，只有用户明确要求时才切换。
- 用户只要求评分时不调用 writer；需要改写时输出结构化修复方向供 `listing-core mode=rewrite` 消费。

## 输入

- `listing`：Title、Item Highlights、Bullets、Description、Search Terms。**外部 Listing（ASIN 抓取、用户粘贴文案）必须先跑 `scripts/normalize_listing_input.py` 归一化**，用它产出的 `listing` / `field_provenance` / `field_metrics` 三块作为输入；不得手工拆字段。
- 可选证据：`product_facts`、`keyword_matrix`、`compliance_report`、`diff_report`、`competitor_context`、`buyer_questions`、`marketplace`。
- `scoring_mode=full|report_only|before_after`。

缺数据维度必须 N/A。进入评分前读取 [scoring-rubric.md](references/scoring-rubric.md)；生成扣分 JSON 和运行脚本时读取 [scoring-input-contract.md](references/scoring-input-contract.md)。

## Canonical 8 Dimensions

1. 平台合规与风险
2. 商品事实与声明可信度
3. 搜索匹配与语义可发现性
4. 标题点击与首屏识别质量
5. 五点转化与购买决策支持
6. 信息完整度与 AI 导购可回答性
7. 语言质量与站点本地化
8. 差异化与竞争安全

AI 导购“推荐准备度”是以上维度的派生状态，不是第九个重复计权维度。检索能力来自维度 3，可回答性来自维度 6，推荐准备度综合合规、事实、检索、决策支持和可回答性。

## Execution

1. 标准化字段并建立每类证据的 `verified|partial|unavailable`：

```bash
python scripts/normalize_listing_input.py <来源.json> --out listing-normalized.json \
  --source-kind auto --asin B0XXXXXXXX --marketplace US
```

   Title 逐字取来源的单一标题字段，**禁止按 `|`、`-` 等分隔符把一条标题拆成 Title + Item Highlights**；
   来源没有独立的 Item Highlights 字段时该字段就是 `unavailable`，不允许从标题切一段来「承接」。
   字符数由脚本按来源字段实测写入 `field_metrics`，`score_quality.py` 据此直接施加标题维度上限
   （超 Title 上限 → 59；超 Highlights 上限 → 69；标题超限且无 Highlights 承接 → `title_without_highlights` 门禁）。
2. 按 rubric 只生成有证据的 `deductions[]`、`evidence[]` 和修复建议；不得直接手算 overall。
3. 客观门禁来自字段校验、合规报告和事实证据；禁止根据语气猜测门禁。合规维度必须有机检产物（`compliance_report` / `compliance_scan` / `check-report`）才允许给数字分——人工通读文案数极限词不算合规证据；产物全缺时脚本强制 `compliance_unavailable` 门禁并把该维度封顶 79，评估者无法绕过。
4. 运行：

```bash
python scripts/score_quality.py deductions.json --out score-result.json \
  --check-report /abs/03-write/check-report.json
python scripts/save_quality_score_output.py score-result.json
```

落盘产物 `linkfox-listing-quality-scorer-<ts>.json`（会话目录 `data/`），载荷自带 `kind=listingQualityScore`、`schema_version=1`；stdout 保留 `Saved full response:` 行（`listing-core/references/output-schema.md` §3.6b）。一次 Bash 输出只允许一行该前缀。

`score_quality.py` 是权重、N/A 归一、hard gate、grade 和 `aiReadiness` 的唯一计算实现。
调用方直接消费 canonical JSON，或把摘要写入 Markdown；本 Skill 不生成 HTML 或 Excel。

**只要存在 `check-report.json` 就必须传 `--check-report`**：字符/字节超限、五点条数、受限词、竞品品牌、特殊符号、前后台重复、标题核心词覆盖率和未证实数字事实由机检直接定分，不依赖评估者自觉写进 `deductions`。机检结论只压不抬：命中项按 rubric 施加维度上限或扣分，任一字段 fail 时 `pass=false`，并写入 `scorePanel.mechanicalFieldFailures`。把维度标成 `na` 也躲不掉——机检证据本身就是可评分证据。

## 输出

- `scorePanel`：canonical rubric v2。
- `aiReadiness`：`discoverability`、`answerability`、`recommendation_readiness`、问题覆盖和 Alexa 问答实测(计费)状态。
- `pass`：overall ≥80 且无触发 hard gate。
- `requiresHumanReview`：高危合规、关键事实或商标风险触发。
- `rewrite_brief`：字段、证据、目标、约束和优先级；不直接改写。

## Guardrails

- 不使用固定兜底分；不把关键词 `value_score` 当质量分。
- 没有关键词矩阵时，维度 3 N/A；没有商品事实时，维度 2 N/A。
- 合规结论必须带检测边界，不输出“保证合规/平台一定通过”。
- 合规扫描/字段机检没跑就如实走 `compliance_unavailable`，不得用手工文本检查顶替；在 `data_confidence` 里把合规标成 `verified` 不改变脚本判定。
- Title / Item Highlights 的字段归属只由来源决定：来源是单一 `title` 字段就按一条标题评分，不得为了让它落进 75c 而拆分、截断或改写后再评。
- 图片缺失不直接扣文案分；视觉问题由 Audit 作为独立诊断视角处理。
- 用户可见内容不暴露 legacy、scorePanel 兼容源或内部脚本名。
- `before_after` 必须使用同一 rubric、同一证据快照和同一 hard gate，避免比较口径变化。
