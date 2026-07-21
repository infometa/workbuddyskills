# Provenance 校验规则（防幻觉核心）

> 本 Skill 的**第一护城河**：页码级 provenance 防幻觉。
> 所有含数字 / 专名 / 方法名 / 数据集名 / 页码引用的 claim，都必须通过 **ngram 匹配校验**。
> 校验脚本：`scripts/verify_provenance.py`

## Contents

- [一、ngram 匹配策略](#一ngram-匹配策略)
- [二、置信度分级](#二置信度分级)
- [三、zh-paraphrase 与 confidence_degraded](#三zh-paraphrase-与-confidence_degraded)
- [四、幻觉判定阈值](#四幻觉判定阈值)
- [五、provenance-audit.json 输出格式](#五provenance-auditjson-输出格式)

---

## 一、被校验的 claim 类别

### 1.1 强校验（ngram 必须匹配，否则 `hallucination_risk: high`）

- `papers[i].summary_card.key_results[*]`（含数字的结果陈述）
- `papers[i].deep_dive_answers[*].original_excerpts[*].text`（原文引用）
- `papers[i].deep_dive_answers[*].original_excerpts[*].page` + `section`（必须在 parse_pdf 的 `(text, page, section)` 索引中存在）
- `comparison.table[*].rows[label].content`（对比表每格内容）
- `comparison.cross_paper_answer.per_paper_evidence[*].excerpt`

### 1.2 中校验（匹配失败降级为 `hallucination_risk: medium`，可通过但要 warning）

- `papers[i].summary_card.research_question / method / dataset / contributions / limitations`（通过 `provenance_map` 的 page 反查）
- `papers[i].connection_points[*].evidence_pages`（页码必须在论文总页数内）

### 1.3 弱校验（仅检查类型 / 枚举 / 非空，不做 ngram）

- `recommended_questions[*].q / why`（主观推荐，无需原文锚定）
- `differences_narrative[*].summary`（跨论文叙述，难以单点匹配）
- `critical_analysis.agree_with / question / complement`（AI 主观分析）

---

## 二、ngram 匹配算法

### 2.1 预处理

对原文 + claim 同样做：
1. **Unicode 归一化**（NFC）
2. **去空白** → 单空格
3. **小写化**（英文）
4. **移除常见标点**：`.,;:()[]{}""''`
5. **保留数字**原样（`52K` / `33%` / `4.6`）

### 2.2 双粒度匹配

| 粒度 | 用途 | 匹配逻辑 |
|---|---|---|
| **5-gram** | 主匹配（高置信）| claim 中的任意连续 5 词在原文中连续出现 |
| **3-gram** | 兜底（中置信）| 5-gram 失败时，至少 2 个连续 3-gram 独立命中 |

### 2.3 特殊 token 处理

- **数字**：必须**精确匹配**（`33%` 不能匹配 `32%`）
- **专有名词**（首字母大写 / 驼峰）：精确匹配（`HaluEval` / `GPT-3`）
- **技术术语**（如 `Transformer` / `ROUGE-L`）：精确匹配，允许 `-` / `_` 互换

### 2.4 置信度分级

| `ngram_match_confidence` | 判定标准 |
|---|---|
| `high` | 5-gram 全中，且所有数字 / 专名精确匹配 |
| `medium` | 5-gram 部分中 + 3-gram 兜底，数字 / 专名匹配 |
| `low` | 仅 3-gram 兜底，数字 / 专名有 ≥ 1 处失配 |
| `failed` | 3-gram 也未能兜底 |

### 2.5 跨语言 paraphrase 放宽（本 Skill 特有）

当 **claim 含 CJK 字符** 但 **论文主体是英文**（paper_cjk_ratio < 0.2）时，
ngram 自然无法对齐（英文 5-gram vs 中文 token），但**数字 / 专名应当全部命中**：

| 条件 | 最终 confidence |
|---|---|
| 数字 + 专名命中数 ≥ 2 且无失配 | 最低 `medium`（原为 failed / low 时自动上浮）|
| 数字 + 专名命中数 ≥ 1 且无失配 | 最低 `low` |
| 任一数字或专名失配 | 按原规则判（通常 failed → 高风险）|

判定逻辑位于 `scripts/verify_provenance.py` → `match_details.cross_language_paraphrase = true` 时生效。

**设计理由**：中文用户总结英文论文是本 Skill 最常见场景；若硬性要求 ngram 命中会误伤合法改写。
关键数字 / 专名（如 `52K` / `ROUGE-L` / `GPT-3`）的精确匹配已足够保证非幻觉。

---

## 三、`hallucination_risk` 判定

| 条件 | `hallucination_risk` |
|---|---|
| `ngram_match_confidence == high` 且所有关键 token 命中 | `low` |
| `ngram_match_confidence == medium` | `medium` |
| `ngram_match_confidence == low` 或有数字失配 | `high` |
| `ngram_match_confidence == failed` | `high`（触发错误分支）|

**高风险处理**：
- 强校验类 claim 高风险 → 从 `result.json` 中**移除**，在 `warnings` 加 `HALLUCINATED_EXCERPT`
- 中校验类 claim 高风险 → 保留但在 `warnings` 加 `LOW_PROVENANCE_CONFIDENCE`

---

## 四、专门规则

### 4.1 页码引用（`page`）校验

```
claim 的 page 必须 ∈ [1, paper.total_pages]
否则：hallucination_risk = high，移除该 claim
```

### 4.2 章节名（`section`）校验

```
claim 的 section 必须在 parse_pdf 识别到的 sections 列表中
  - 允许前缀匹配（如 "3.2" 可匹配 "3.2 Dataset Construction"）
  - 允许大小写差异
否则：降级为 medium 并 warning
```

### 4.3 数字的严格性

任何含**具体数字**的 claim：
- 数字必须在原文 text 中**精确出现**
- 允许格式差异（`52,002` / `52002` / `52K` 视为同一数字）
- 允许相对表达（原文 `46.2 vs 34.6` → claim `"提升 33%"` 算作推算，需 AI 在 `provenance_map[key_results[*]].note` 标注 `"基于原文 46.2 - 34.6 计算"`）

### 4.4 相对数字的例外

若 claim 是**推算的相对数字**（如 "提升 33%"），原文可能只有绝对值：
- 允许 claim 带 `note: "推算自原文 X - Y"`
- 必须在 `provenance_map` 中标明推算
- 否则仍视为高风险

---

## 五、实现清单（`scripts/verify_provenance.py` 的职责）

```
1. 读取 result.json + 每篇 paper 的 parse_pdf 输出（paper_*.json）
2. 对每篇 paper 建立 ngram 索引（3-gram + 5-gram 两层）
3. 遍历 result.json 的所有 claim（按 §1 分类）
4. 执行 §2 匹配算法
5. 按 §3 判定 hallucination_risk
6. 按 §4 专门规则补充校验
7. 输出 provenance-audit.json（§六）
8. 若有强校验失败 → 修改 result.json 并在 warnings 中记录
```

---

## 六、`provenance-audit.json` 输出结构

```json
{
  "audit_version": "0.1",
  "audit_timestamp": "2026-04-23T10:16:00Z",
  "total_claims_checked": 23,
  "breakdown": {
    "strong_checked": 15,
    "medium_checked": 8,
    "weak_skipped": 0
  },
  "match_distribution": {
    "high": 20,
    "medium": 3,
    "low": 0,
    "failed": 0
  },
  "claims": [
    {
      "id": "c-001",
      "claim_type": "deep_dive.original_excerpts",
      "paper_label": "A",
      "claim_text": "We start with 175 seed instructions and use 8 human-written + 2 model-generated as in-context examples",
      "claimed_location": { "page": 5, "section": "3.2 Dataset Construction" },
      "ngram_match_confidence": "high",
      "match_details": {
        "5gram_hit_ratio": 0.95,
        "3gram_hit_ratio": 1.0,
        "numbers_matched": ["175", "8", "2"],
        "names_matched": []
      },
      "hallucination_risk": "low",
      "action_taken": "kept"
    },
    {
      "id": "c-002",
      "claim_type": "summary_card.key_results",
      "paper_label": "A",
      "claim_text": "在 SuperNI 上相对 GPT-3 vanilla 提升 33%",
      "claimed_location": { "page": 7, "section": "5.1 Main Results" },
      "ngram_match_confidence": "medium",
      "match_details": {
        "5gram_hit_ratio": 0.60,
        "3gram_hit_ratio": 0.85,
        "numbers_matched": ["33"],
        "names_matched": ["SuperNI", "GPT-3"],
        "note": "claim 为中文陈述，ngram 匹配度按数字/专名为主"
      },
      "hallucination_risk": "low",
      "action_taken": "kept"
    }
  ],
  "removed_claims": [],
  "flagged_for_user_review": []
}
```

---

## 七、常见错误与处理（NEVER）

- **NEVER** 跳过 Step 7（`verify_provenance.py`）—— 这是防幻觉闭环的核心
- **NEVER** 让强校验失败的 claim 留在 `result.json` 里 —— 必须删除 + warning
- **NEVER** 用"模糊匹配"（edit distance / fuzzy match）代替 ngram —— 容易假阳性
- **NEVER** 对 `pasted_text` 模式做**章节名**校验（pasted_text 无可靠章节结构，降级为仅做 ngram 文本匹配）
- **NEVER** 对 `force_skim` 模式跳过 provenance 校验（裸读的 `provenance_map` 也要验证 page 范围）
- **NEVER** 把 `hallucination_risk: high` 的 claim 用 "仅警告不处理" 的方式放过 —— 强校验类必须移除

---

## 八、整篇置信度降级（v0.4.0 / P0-B）

> 单条 claim 的 `hallucination_risk` 已经按 §三处理；但当**整篇论文**的通过率系统性偏低时，
> 用户应在打开报告**第一眼**就被警示——避免被「看起来都有页码」骗到。

### 8.1 触发阈值（任一命中即整篇降级）

| 触发条件 | reason | 含义 |
|---|---|---|
| `removed_claims_count > 0` | `claims_removed` | 强校验失败被强制删除（最严重）|
| `failed >= 3` | `failed_count_exceeds` | 至少 3 条 claim 完全无法定位原文 |
| `total > 0 且 high_ratio < 0.60` | `high_ratio_below_threshold` | 高置信占比不足六成 |

reason 优先级：`claims_removed > failed_count_exceeds > high_ratio_below_threshold`（取首个命中）。

### 8.2 写入位置

`scripts/verify_provenance.py --in-place` 时，把以下结构写到 `result.meta.confidence_degraded`：

```json
{
  "is_degraded": true,
  "reason": "claims_removed",
  "stats": { "high": 4, "medium": 6, "low": 5, "failed": 3, "total": 18 },
  "high_ratio": 0.22,
  "threshold": 0.60,
  "removed_claims_count": 2,
  "advice_zh": "本次抽取的页码引用整体可信度偏低；建议在 deep 模式下重读关键段落，或重新粘贴更长上下文。"
}
```

未触发降级时 `is_degraded: false`，其它字段仍填出（便于 dashboard 取数）。

### 8.3 渲染契约

`scripts/render_report.py` 在 HTML / Markdown 顶部读取 `result.meta.confidence_degraded`：
- `is_degraded == true` → 红色高亮 banner，含 reason / stats / advice_zh
- `is_degraded == false` → 不渲染 banner（保持简洁）
- 缺少该字段 → 视同 `is_degraded == false`（向后兼容旧 result.json）
