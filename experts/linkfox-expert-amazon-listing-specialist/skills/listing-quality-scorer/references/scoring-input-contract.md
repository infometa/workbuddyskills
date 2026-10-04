# Canonical scoring input contract

语义判断只产出有证据的扣分项；脚本负责计算。输入示例：

```json
{
  "dimensions": {
    "compliance_risk": {"evidence": [], "deductions": []},
    "fact_trust": {"evidence": [], "deductions": []},
    "semantic_discoverability": {"evidence": [], "deductions": []},
    "title_first_screen": {"evidence": [], "deductions": []},
    "decision_support": {"evidence": [], "deductions": []},
    "ai_answerability": {"evidence": [], "deductions": []},
    "localization": {"evidence": [], "deductions": []},
    "competitive_safety": {"evidence": [], "deductions": []}
  },
  "dimension_caps": {"title_first_screen": 59},
  "hard_gates": [
    {"key": "compliance_high_risk", "triggered": false, "evidence": []}
  ],
  "ai_context": {
    "four_pillars": {"what": "pass", "who_scene": "weak"},
    "questions": [],
    "question_coverage": {"answered": 14, "total": 20},
    "external_probe": {"probed": false}
  },
  "top_issues": [],
  "quick_fixes": [],
  "rewrite_brief": {"field_actions": []},
  "data_confidence": {}
}
```

## Dimension keys

只允许 `score_quality.py` 声明的 8 个 key。缺失或 `state=na` 的维度按 N/A 处理，不参与 overall。

每个 deduction 至少包含：

```json
{
  "points": 10,
  "reason": "核心品类词未出现在标题前段",
  "field": "title",
  "evidence": ["title characters 1-45: ..."],
  "action": "把已验证的核心品类词前置"
}
```

`points` 必须符合 rubric 的扣分范围。不要同时传人工计算的维度 score；脚本按 `100-sum(deductions.points)` 计算，并应用客观 `dimension_caps`。

## check-report 机检并入（存在即必传）

有 `validate_fields.py` 的 `check-report.json` 时，用 `--check-report /abs/check-report.json`
（或在 payload 里放 `check_report` 对象）把机检结论并入评分。并入规则固定且只压不抬：

| 机检命中 | 后果 |
|---|---|
| `title.over_limit` | `title_first_screen` 上限 59 |
| `item_highlights.over_limit` | `title_first_screen` 上限 69 |
| `bullets.over_limit` / `bullet_count` | `decision_support` 上限 69 |
| `description.over_limit` | `ai_answerability` 上限 79 |
| `search_terms.over_limit` | `semantic_discoverability` −10 |
| `search_terms.front_dup` / `front_dup_excess` | `semantic_discoverability` 每词 −2（上限 −12）、超阈值再 −8 |
| 任意字段 `competitor_brand` | 触发 `competitor_brand_trademark` 门禁 |
| 任意字段 `banned_term`（字段 fail） | 触发 `compliance_high_risk` 门禁；仅 warn 时 `compliance_risk` −8/次（上限 −24） |
| 任意字段 `special_symbol` | `compliance_risk` −5/次（上限 −15） |
| 核心字段 `missing_field` / `empty_field` | 触发 `missing_core_fields`；highlights 缺失触发 `title_without_highlights` |
| `coverage.title_core_hit` 覆盖率 | <20% 上限 69；<40% 上限 79；<60% 上限 89 |
| `coverage.bullets_scene_pain_pct < 60` | `semantic_discoverability` −6 |
| `fact_faithfulness.unsupported_claims` | `fact_trust` 每项 −6（上限 −24）且该维度上限 79 |

补充约定：

- 机检扣分带 `source: "check_report"`，与语义扣分并列展示，按 (reason, evidence) 去重，重复运行结果一致。
- 只有机检证据的维度会被**创建为可评分维度**——把维度写成 `state: "na"` 不能规避机检处罚。
- 任一字段 `status=fail` 时 `pass=false`，失败字段列在 `scorePanel.mechanicalFieldFailures`。
- `unsupported_claims` 是启发式（数字+单位不在 facts 原文），因此只扣分并压上限，不自动触发 `unsupported_critical_fact` 门禁；确认是编造时由评估者显式传该门禁。

## Listing 输入映射契约（外部 Listing 必跑）

评分前先用 `scripts/normalize_listing_input.py` 把来源归一化，产物的三个块直接进 payload：

```json
{
  "listing": {"title": "...", "item_highlights": null, "bullets": ["..."], "description": "...", "search_terms": null},
  "field_provenance": {
    "title": {"source_field": "products[0].title", "state": "verified", "reason": ""},
    "item_highlights": {"source_field": null, "state": "unavailable", "reason": "来源没有独立的 Item Highlights 字段；禁止从标题中拆分补齐"}
  },
  "field_metrics": {"title_chars": 186, "title_limit": 75, "title_over_limit": true, "bullets_total_chars": 1253}
}
```

固定映射（不靠试错）：

| 归一化字段 | Amazon 商品详情来源字段 |
|---|---|
| `title` | `products[].title`（逐字，不拆分、不截断） |
| `item_highlights` | 仅 `itemHighlights` / `item_highlights` / `aboutItemHighlights` / `highlights`；都没有即 `unavailable` |
| `bullets` | `aboutItemFivePoint` / `bulletPoints` / `bullets` |
| `description` | `productDescription`（A+ 结构取文本，只有图片时 `unavailable`） |
| `search_terms` | 前台不可见，恒为 `unavailable` |

`score_quality.py` 据此强制执行，评估者绕不过：

- `field_metrics.title_over_limit` → `title_first_screen` 上限 59；
- `field_metrics.item_highlights_over_limit` → `title_first_screen` 上限 69；
- 标题超限且没有 Item Highlights 承接 → 追加 `title_without_highlights` 门禁（overall_cap 79）；
- `listing.item_highlights` 有值但 `field_provenance.item_highlights.state != "verified"` → 直接 `ValueError`，
  拒绝评分。这条专门堵「把一条 186 字符的线上标题按 `|` 切成 Title 74c + Highlights 109c，
  于是 75c 门禁不触发」的路径。
- 没传 `field_metrics` 时脚本自己按 `listing` 重算，不采信调用方给的字符数。

字符上限来自双层规格模型（`listing_spec.py`）：缺省 Title 75 / Highlights 125 属 Layer B 写作规格，
可用 `--spec spec.json` 在平台底线内覆盖；Layer A 平台硬限制（Title 200）任何 spec 都不能放宽。

## 合规证据来源（缺失即强制门禁）

合规维度权重 20，脚本会检查证据来源，只认以下机检产物之一：

| payload key | 来源 |
|---|---|
| `compliance_report` | `listing-compliance-scan` 结果 |
| `compliance_scan` | 独立合规扫描结果 |
| `check_report` | `validate_fields.py` 的 check-report（含 banned_term / competitor_brand / special_symbol） |

三者全缺时，`score_quality.py` 无条件执行：

- `dimension_caps.compliance_risk = 79`（与评估者传入的 cap 取更严者）；
- 追加 `compliance_unavailable` 门禁（overall_cap 79，`pass=false`）；
- 合规维度 note 改写为「合规待终检：未接入合规扫描或字段机检，本项为待验证分」。

**不接受自我声明**：`data_confidence` 写 `verified`、`evidence[]` 里描述「已人工检查极限词」
都不构成合规证据。评估者手工通读文案得出的合规结论只能作为 `deductions` 的解释，不能替代机检。

## Hard-gate keys

- `compliance_high_risk`
- `unsupported_critical_fact`
- `competitor_brand_trademark`
- `missing_core_fields`
- `title_without_highlights`
- `compliance_unavailable`
- `product_facts_unavailable`

未知 key 会被脚本拒绝，防止各调用方发明新 cap。门禁必须来自校验报告或明确证据。

## AI readiness

- `discoverability`：维度 3 的派生状态。
- `answerability`：维度 6 的派生状态。
- `recommendation_readiness`：合规、事实、检索、决策支持和可回答性的派生状态，不承诺平台推荐。
- 没有 Alexa 问答实测(计费)结果时不传 `external_probe`，脚本固定输出 `probed=false`。
