# 扣分规则（完整实现）

> 服务于 [scoring-workflow.md](scoring-workflow.md) 的 Step 5。
> 规则来源：[official-rubric.md](official-rubric.md) 第四节 + 五、六节综合。

---

## 一、字数扣分（按短缺比例）

### CET-4：要求 120-180 词

### CET-6：要求 150-200 词

### 扣分公式

```
effective_words = total_raw_words - given_sentences_words
shortfall = max(0, requirement_min - effective_words)
shortfall_ratio = shortfall / requirement_min

IF shortfall_ratio == 0:
  deduction = 0
ELIF shortfall_ratio ≤ 0.10:      # 短缺 ≤ 10%
  deduction = 0 OR 1              # 酌情，倾向 0
ELIF shortfall_ratio ≤ 0.25:      # 短缺 10-25%
  deduction = 1 OR 2
ELIF shortfall_ratio ≤ 0.50:      # 短缺 25-50%
  deduction = 2 OR 3
ELSE:                             # 短缺 > 50%
  deduction = 3+
  # 可能触发降档：原 band 降一档后再结算
```

### 字数统计细则（官方规则）

| 情况 | 是否计入 |
|------|---------|
| 正文内容 | ✅ 计入 |
| 题目给出的**主题句、起始句、结束句** | ❌ **不计入** |
| 作者姓名 / 日期 / 签名 | ❌ 不计入 |
| 标题 | 一般不计入（若题目要求自拟标题则计入）|
| 连字符词（eg. well-known） | ✅ 计 1 个 |
| 缩略词（eg. don't, I'm） | ✅ 计 1 个 |
| 阿拉伯数字（eg. 2026） | ✅ 计 1 个 |
| 英文数字（eg. twenty-six） | ✅ 计 1 个 |

由 `scripts/word_count.py` 实现。

### 超字数处理

- 官方**未规定超字数处罚**
- 若 `effective_words > requirement_max`：
  - **不扣分**
  - 但在 rationale 中提示："超过字数上限（180/200 词），考场实际卷面可能显得拥挤。"

---

## 二、书写扣分

### 规则

```
IF 书写极差，影响阅卷员辨认（手写卷主要影响）:
  band = max(0_band_level, current_band - 1)   # 降一档
  reason = "书写较差，降低一个档次"
```

### 说明

- 这是**降档**而不是扣分数
- 降档后在新档内重新做 Step 4（档内 ±1）
- 电子提交的作文默认**不触发**本规则（除非用户明确说"我是手写扫描稿，书写糟糕"）

---

## 三、内容缺失扣分

### 规则

题目通常会给出 2-3 个要点（如"描述现象 + 分析原因 + 提出建议"）。按覆盖比例扣分：

| 要点覆盖 | 扣分动作 |
|---------|---------|
| 全部覆盖 | 0 |
| 遗漏 1 个次要要点 | 可能仅影响档内调节（-1）|
| 遗漏 1 个主要要点 | 扣 1-2 分 |
| 遗漏 ≥ 50% 要点 | 扣 2-3 分 **且可能触发降档**（"切题"→"基本切题"）|

### 特殊情况：图表作文

- 未描述关键趋势 / 关键对比 → 要点缺失扣分
- 未给出结论或个人观点（若题目要求）→ 要点缺失扣分

---

## 四、0 分特殊情况（慎判）

### 触发条件（任一）

1. **白卷 / 未作答**
2. **只有几个孤立的词**（无法构成任何表达思想的句子）
3. **作文与主题完全无关**（完全跑题，非部分偏题）

### 慎判要求

- 部分偏题（如题目"环保"，写成了"健康"）→ 属 5/8 档"基本切题"，**不是 0 分**
- 字数极少但句子完整且切题 → 按字数扣分处理，**不是 0 分**
- 抄题 / 复述题目 → 属 2 档"条理不清"，**不是 0 分**
- **只有当阅卷员能明确判断"没有任何有效内容"时才给 0 分**

### 记录

若判 0 分，`rationale_trace` 必须明确：
```json
{
  "claim": "判 0 分",
  "evidence": ["全文仅 5 个孤立词：'Good, environment, pollution, people, bad'"],
  "rubric_ref": "0 分（特殊情况）：只有几个孤立的词"
}
```

---

## 五、特殊扣分（部分题型）

### CET 图表作文

- 数据描述错误（读错图表）→ 按严重错误计数
- 遗漏关键趋势 → 要点缺失扣分

### CET 看图作文

- 仅描述图画、无评论（题目要求 describe + comment）→ 属"基本切题"，降到 8 档

### 题目给了开头/结尾句

- 起始句、结束句**不计入字数**
- 若考生只写了开头结尾没写正文 → 严重字数不足 + 要点缺失

---

## 六、扣分叠加规则

扣分按以下顺序应用，**每一步后都要重算**：

```
Step A  定 band（Step 3 结果）
Step B  档内 ±1（Step 4 结果）→ raw_score ∈ {1..15}
Step C  书写差？→ band 降一档 → 在新档内重新做 Step B
Step D  字数扣分 → raw_score -= word_deduction
Step E  内容缺失扣分 → raw_score -= content_deduction
Step F  final_score = max(0, raw_score)

若触发 0 分特殊情况 → 跳过 B/C/D/E，直接 final_score = 0
```

**示例**：

```
作文定档 11 档 → raw = 11
档内 +1（语言更精确）→ raw = 12
字数 105（短缺 12.5%）→ deduction = 1 → raw = 11
内容遗漏 1 个要点（1 分）→ raw = 10
final_score = 10 → 报告分 = 71.0
```

---

## 七、输出格式

`deductions` 字段为数组，**每条扣分独立记录**：

```json
{
  "deductions": [
    {
      "type": "word_count",
      "amount": 1,
      "reason": "有效字数 105，要求 120-180，短缺 12.5%"
    },
    {
      "type": "content_missing",
      "amount": 1,
      "reason": "题目要求'原因 + 建议'，仅写了原因，未给出建议"
    }
  ]
}
```

`type` 枚举：
- `word_count`：字数不足
- `handwriting`：书写差（降档，`amount` 记为等价分数 3）
- `content_missing`：内容缺失
- `zero_trigger`：触发 0 分特殊情况

---

## 八、常见错误做法（NEVER）

| ❌ NEVER | ✅ DO |
|---------|------|
| 字数超标扣分 | 不扣，只提示 |
| 部分偏题直接判 0 分 | 按 5/8 档"基本切题"处理 |
| 书写差时扣分数 | 应**降档**（整体降一档） |
| 扣分后出现半分（10.5） | 所有扣分必须整数；出现分数小数说明叠加逻辑错误 |
| 扣分为负数（final < 0） | 永远 `max(0, ...)` |
| 不记录扣分理由 | 每条扣分必须有 `reason` 字段引用大纲规则 |
