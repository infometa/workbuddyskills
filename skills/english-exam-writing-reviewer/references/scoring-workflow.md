# 6 步批改流程（详细版）

> 对应 SKILL.md 中的"快速工作流"，本文件展开每步的具体操作、产出物、质量门。

---

## Step 1 · 输入校验 & 字数统计

### 1.1 必填项校验

```
IF exam_level 为空:
  追问用户: "请确认这是四级（CET-4）还是六级（CET-6）？样卷难度基准不同，不能合并判定。"
  STOP
IF prompt 为空:
  追问用户: "请提供题目原文。看图/图表作文请一并附上图片描述或数据表。"
  STOP
IF essay 为空:
  追问用户: "请粘贴作文正文。"
  STOP
```

### 1.2 字数统计

调用 `scripts/word_count.py`：

```bash
python scripts/word_count.py --essay "<作文文本>" \
                             --given "<起始句1>" "<结束句1>" \
                             --exam-level CET4
```

输出 JSON：

```json
{
  "total_raw": 156,
  "given_sentences_deducted": 14,
  "effective": 142,
  "requirement_min": 120,
  "requirement_max": 180,
  "within_range": true,
  "shortfall_ratio": 0.0
}
```

**质量门**：
- `effective < requirement_min` → 标记 `penalty_triggered=true`，记录 `shortfall_ratio`
- `effective > requirement_max` → **不扣分**（官方未规定超字数处罚），但在 rationale 中提示用户注意

---

## Step 2 · 加载官方 rubric

**必读**：
1. [official-rubric.md](official-rubric.md) — 档次描述原文
2. [cet4-vs-cet6.md](cet4-vs-cet6.md) — 找到对应级别的样卷难度基准

**不读**：其他 references 文件（Step 3/5/6 再按需加载）

---

## Step 3 · 定档（5 档判定）

### 3.1 读取判定规则

必读 [band-decision-rules.md](band-decision-rules.md)，**边界判定清单**是关键。

### 3.2 逐档比对

从最高档往下扫描：

```
check_14_band(essay):
  - 是否"切题"？（是/否）
  - 是否"表达思想清楚"？（是/否）
  - 是否"文字通顺、连贯"？（是/否）
  - 是否"基本上无语言错误，仅个别小错"？（是/否）
  如果 4 项都为"是" → band = 14, goto Step 4

check_11_band(essay):
  - 是否"切题"？
  - 是否"表达思想清楚"？
  - 是否"文字连贯"？
  - 是否"有少量语言错误"？（不是"基本无错"，也不是"相当多"）
  如果 4 项都为"是" → band = 11, goto Step 4

check_8_band(essay):
  - 是否"基本切题"（降一档）？
  - 是否"有些地方表达思想不够清楚"？
  - 是否"文字勉强连贯"？
  - 是否"语言错误相当多，且有一些严重错误"？
  如果 4 项都为"是" → band = 8, goto Step 4

check_5_band(essay):
  - 是否"基本切题"？
  - 是否"表达思想不清楚"（已不是"不够清楚"）？
  - 是否"连贯性差"？
  - 是否"较多严重语言错误"？
  如果 4 项都为"是" → band = 5, goto Step 4

check_2_band(essay):
  - 是否"条理不清、思路紊乱"？
  - 是否"语言支离破碎或大部分句子有错"？
  - 是否"多数为严重错误"？
  如果 3 项都为"是" → band = 2, goto Step 4

check_0(essay):
  - 白卷 / 仅孤立词 / 完全离题？
  → band = 0 (慎用，必须在 rationale 中说明)
```

### 3.3 边界仲裁

当在两档边缘难以判定时，查 [band-decision-rules.md](band-decision-rules.md) 的 "4 个边界判定清单"：
- 14 vs 11
- 11 vs 8
- 8 vs 5
- 5 vs 2

### 3.4 产出物

```json
{
  "band": 11,
  "boundary_decision": {
    "compared_with_higher": "与 14 档差距：...",
    "compared_with_lower": "明显优于 8 档：..."
  }
}
```

---

## Step 4 · 档内调节（±1）

### 4.1 规则

- 每档区间 3 分（14 档 = 13/14/15）
- 默认给档中分（14/11/8/5/2）
- 与当次考试的档内样卷比较：
  - **稍优** → +1（给 15/12/9/6/3）
  - **相当** → 0（给 14/11/8/5/2）
  - **稍劣** → -1（给 13/10/7/4/1）

### 4.2 判定依据（三选一）

1. **语言精度**：在档内语言错误数量/严重度上的位置
2. **内容深度**：论证/例证/思辨的充分程度
3. **表达地道程度**：词汇丰富度、句式多样性

### 4.3 CET4/CET6 差异

同一档内：
- CET6 的"稍优"门槛比 CET4 高（因为六级样卷整体水平高）
- 对"少量语言错误"的容忍度：CET6 更严

### 4.4 产出物

```json
{
  "intra_band_adjustment": {
    "delta": 1,
    "reason": "与 14 档样卷相比，用词更地道（remarkable / derive），且几乎无错误（仅 1 处代词指代） → +1"
  },
  "raw_score": 15
}
```

---

## Step 5 · 扣分检查

必读 [deduction-rules.md](deduction-rules.md)。

### 5.1 字数扣分

```
IF shortfall_ratio ≤ 0.10:        # 短缺 ≤ 10%
  deduction_words = 0 or 1
ELIF shortfall_ratio ≤ 0.25:      # 短缺 10-25%
  deduction_words = 1 or 2
ELIF shortfall_ratio ≤ 0.50:      # 短缺 25-50%
  deduction_words = 2 or 3
ELSE:                             # 短缺 > 50%
  deduction_words = 3+ (可能触发降档)
```

### 5.2 书写/内容扣分

```
IF 书写极差影响交际:
  band -= 1  # 降一档，对应分数 -3
IF 题目要点遗漏 ≥ 50%:
  deduction_content = 2 or 3
```

### 5.3 0 分触发

```
IF 白卷 OR 仅孤立词 OR 完全离题:
  final_score = 0
  rationale_trace 必须明确触发条件
  SKIP Step 6
```

### 5.4 产出物

```json
{
  "deductions": [
    { "type": "word_count", "amount": 1, "reason": "有效字数 108 < 120，短缺 10%" }
  ],
  "final_score": 10
}
```

---

## Step 6 · 升级路径 + 输出

### 6.1 升级路径

必读 [upgrade-paths.md](upgrade-paths.md)，按"当前档 → 下一档"取对应模板，填入**针对本文作文的 3-5 条具体改动**。

```json
{
  "upgrade_path": {
    "current": 11,
    "target": 14,
    "actions": [
      "消除 3 处语法错误（主谓一致、时态）至'个别小错'",
      "至少 2 处用高级词替换（great → remarkable）",
      "引入 1-2 个具体支撑例证（当前过于泛泛）"
    ]
  }
}
```

### 6.2 错误清单

按 [error-taxonomy.md](error-taxonomy.md) 分类：
- **机械错**（拼写、标点、大小写）
- **语法错**（时态、主谓一致、代词指代、搭配）
- **词汇错**（用词不当、重复、中式英语）
- **结构错**（段落划分、衔接、主题句缺失）

每条错误给 severity：`critical` / `warning` / `tip`

### 6.3 输出 JSON

按 [output-schema.md](output-schema.md) 组装完整 JSON。

### 6.4 （可选）渲染 HTML 报告

```bash
python scripts/render_report.py review.json --output ./review-reports/report.html
```

### 6.5 向用户呈现

**顺序**（对齐教练式反馈原则）：
1. 总分 + 档次 + 报告分（一句话）
2. 档次判定理由（引用官方描述符 + 作文证据）
3. 4 个维度诊断（短段落，不出独立分值）
4. 档内 ±1 调整理由（判定依据）
5. **扣分明细**（若有扣分项，必须逐条列出：扣分类型 + 金额 + 理由；并注明 final_score = raw_score - 扣分合计；**不得省略此节或列了扣分但 final_score 仍接近满分**）
6. 错误清单（按严重度分组）
7. 升级路径（3-5 条具体改动）
8. （可选）HTML 报告链接

> ⚠️ **输出一致性硬规则**：文字描述中的得分、扣分必须与 JSON 字段严格一致。若 deductions 非空，文字中必须出现"扣分明细"一节，且文字 final_score == JSON final_score。违反即为输出错误，必须在发送给用户前自我修正。

---

## 质量门检查（输出前自检）

```
ASSERT band ∈ {0, 2, 5, 8, 11, 14}
ASSERT raw_score ∈ {0, 1, 2, ..., 15}  # 整数，无半分
ASSERT final_score ≥ 0 AND final_score ≤ 15
ASSERT band_description.official_text 逐字来自 official-rubric.md
ASSERT 每个 issue 有 location + original + suggestion + reason
ASSERT upgrade_path.target > current（除非 current = 14）
ASSERT rationale_trace 非空 且 每条含 evidence + rubric_ref
ASSERT 若 deductions 非空 → final_score == raw_score - sum(deductions[*].amount)
ASSERT 文字描述中的得分 == JSON final_score（三端一致性）
ASSERT 若 deductions 非空 → 文字批改包含"扣分明细"一节
```

任一断言失败 → 在输出前自我修正。

---

## Refs 加载窄边界白名单

> 主 agent 必须严格按下表"必读 / 可选 / 禁读"加载 refs。只读当前 Step 必需的文件，避免 18 个 refs 全量读取爆 context、分散判定。

| Step | 必读 refs（Required） | 可选 refs（On-Demand） | 禁读（Forbidden） |
|------|----------------------|-----------------------|-------------------|
| **Step 0** 确认级别 | 无（仅 SKILL.md §"Step 0 追问话术模板" + 解析规则表）| 无 | 全部 references/*.md |
| **Step 1** 字数 + 题型识别 | `exam-level-matrix.md` | `cet-subtypes.md`（CET 题型识别）/ `letter-categories.md`（A 节 letter）| 其他 16 个 |
| **Step 2** 加载 rubric | CET → `official-rubric.md` + `cet4-vs-cet6.md`；考研 → `postgrad-official-rubric.md` + `postgrad-vs-cet.md` + `postgrad1-vs-postgrad2.md` | 按 task_subtype：`cet-subtypes.md` / `postgrad1b-paragraph-rubric.md` / `chart-verbs.md` / `letter-categories.md` | 与本次 exam_level / task_subtype 无关的 rubric |
| **Step 3** 定档 | `band-decision-rules.md` | 上一 Step 已加载的 rubric（沿用）| 其他 |
| **Step 4** 档内调节 | 无（用 Step 3 已加载的 rubric + SKILL.md"档内调节"表）| `references/calibration/samples/`（同档锚点）| 其他 refs/*.md |
| **Step 5** 扣分检查 | `deduction-rules.md` | 考研 A 节 Directions 检测时再读题面 | 其他 |
| **Step 6** 升级 + 词汇 + 专项 | `upgrade-paths.md` + `writing-vocabulary.md` | 按 task_subtype 复用 Step 2 已加载文件；`error-taxonomy.md`（标注错误时） | 其他 |
| **Step 7** 询问 HTML | 无（仅 `output-schema.md` 用于组装 review.json）| `assets/report-template.html`（仅 render_report.py 内部使用）| 其他 refs/*.md |

**硬规则**：
1. 单个级别批改全程**最多读 5-7 个 refs**（≈ 18 个里的 1/3），多读视为冗余；
2. 多选 ≥ 2 个级别时，按级别**串行**走 Step 1-6（不要并行预读所有 refs，每开新级别清空 refs 上下文重新加载）；
3. `output-schema.md` 仅在 Step 6 组装 JSON 和 Step 7 渲染前读取，不在 Step 1 预读。
