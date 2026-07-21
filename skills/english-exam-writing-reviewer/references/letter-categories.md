# 考研 A 节书信功能性分类库（Letter Category Library）

> v1.6.0 新增。考研英语一/二 A 节 `task_subtype = letter` 的功能性细分，用于绑定**专属套话、功能段落结构、常见失误**。

---

## 一、10 种功能性子类

| `letter_category` | 中文 | 真题频次 | 核心功能 |
|------------------|-----|---------|---------|
| `inquiry` | 咨询信 | ⭐⭐⭐⭐⭐ 每 2-3 年考 | 问信息、问建议 |
| `application` | 申请信 | ⭐⭐⭐⭐⭐ 固定 | 求职、求学、申请活动 |
| `recommendation` | 推荐信 | ⭐⭐⭐⭐ 常考 | 推荐书/影/课/地点 |
| `suggestion` | 建议信 | ⭐⭐⭐⭐ 常考 | 对机构/活动给建议 |
| `invitation` | 邀请信 | ⭐⭐⭐⭐ 常考 | 邀请参加活动 |
| `reply` | **回复信** | ⭐⭐⭐⭐ 常考（2015、2018 英二） | 回应前次通讯 |
| `complaint` | **投诉信** | ⭐⭐⭐ 中频（2010 英一） | 对服务/产品投诉 |
| `apology` | 致歉信 | ⭐⭐⭐ 中频 | 为失约/失误道歉 |
| `thank` | 感谢信 | ⭐⭐⭐ 中频 | 感谢帮助 |
| `other` | 其它 | 兜底 | 上述以外的特殊信函 |

**`letter_category` 仅当 `task_subtype = letter` 时必填；否则为 `null`。**

---

## 二、识别规则（Skill 从 Directions 自动判定）

| Directions 关键词 | 判为 |
|------------------|------|
| "to inquire about" / "seeking information" / "asking for" | `inquiry` |
| "to apply for" / "applying for the position of" | `application` |
| "to recommend" / "recommending a ... to ..." | `recommendation` |
| "to make suggestions" / "suggest" | `suggestion` |
| "to invite" / "inviting ... to ..." | `invitation` |
| "in reply to" / "responding to" / "in answer to" | `reply` |
| "to complain about" / "expressing dissatisfaction" | `complaint` |
| "to apologize" / "to apologise for" | `apology` |
| "to express gratitude" / "to thank" | `thank` |

若 Directions 含多个功能（如"邀请 + 告知"）→ 选主功能，次功能在 `note` 中注明。

---

## 三、每类的专属套话 + 常见失误

### 3.1 `inquiry` 咨询信

**开头**：

> I am writing to **inquire about** the details of + 名词短语.
> I would be **much obliged if** you could furnish me with + 名词短语.

**正文标记词**：I wonder whether / I would like to know / Could you kindly inform me of

**结尾**：I look forward to **your prompt reply**. / Your early response would be **greatly appreciated**.

**常见失误**：

| 失误 | 严重度 |
|------|-------|
| 开头用 "I want to ask you" | warning（语域不够正式）|
| 没有具体问题列表 | warning（信息不明确）|
| 结尾缺"期待回复"套话 | tip |

### 3.2 `application` 申请信

**开头**：

> I am writing to **apply for** the position of + 职位 / **to express my keen interest in** + 活动.

**核心段落**：**资格展示**（With + academic / professional background / 具体经历）

**结尾**：I would be grateful if you could **grant me an interview** / consider my application.

**常见失误**：

| 失误 | 严重度 |
|------|-------|
| 没有资格证明段 | critical（任务完成度低）|
| 用真实姓名（违反 Li Ming 规则）| critical（signature_violation）|

### 3.3 `recommendation` 推荐信

**开头**：

> I am writing to **wholeheartedly recommend** + 对象 **to** + 接收方.

**核心段落**：**推荐理由**（3 点）+ **预期收益**

**常见失误**：

| 失误 | 严重度 |
|------|-------|
| 推荐理由少于 2 条 | warning |
| 只夸推荐对象，不说为何适合接收方 | warning |

### 3.4 `suggestion` 建议信

**开头**：

> I am writing to **put forward some suggestions regarding** + 议题.

**核心段落**：**建议 1 + 理由 / 建议 2 + 理由**（并列或递进）

**结尾**：I trust these humble suggestions will **merit your consideration**. / Hoping this would be **helpful to your decision**.

**常见失误**：

| 失误 | 严重度 |
|------|-------|
| 建议不具体（如 "make it better"）| critical |
| 语气命令式（如 "You must..."）| warning（语域不当）|

### 3.5 `invitation` 邀请信

**开头**：

> I am writing to **cordially invite** you to + 活动.

**正文必含**：**时间 + 地点 + 活动内容 + 期望参与的原因**

**结尾**：It would be **our great honour** if you could grace us with your presence.

**常见失误**：

| 失误 | 严重度 |
|------|-------|
| 漏 3 W 之一（When/Where/What）| critical（任务完成度）|

### 3.6 `reply` 回复信 ⭐ 新增重点

**开头**：

> I am writing **in reply to your letter of** [日期] **regarding** + 话题.
> Having received your inquiry **dated** + 日期, I am glad to **offer the following response**.

**核心段落**：**逐点回应**（若前信问了 3 点，回信必须对应 3 点）

**结尾**：I hope **the above suffices**. / Should you require further clarification, **please do not hesitate to contact me**.

**常见失误**：

| 失误 | 严重度 |
|------|-------|
| 没有回指前信（日期/话题）| critical（违反"回复"任务本质）|
| 前信问 3 点，只回 1-2 点 | warning（任务完成度不足）|
| 完全不提及前信发件人 | warning |

### 3.7 `complaint` 投诉信 ⭐ 新增重点

**开头**：

> I am writing to **express my deep dissatisfaction with** + 事由.
> I was **dismayed / disappointed** to find / learn that + 从句.

**核心段落**：**事实陈述**（时间 + 事件 + 损失）+ **诉求**（退款 / 道歉 / 改进）

**结尾**：I look forward to **a prompt resolution** to this matter / **your immediate attention** to this issue.

**常见失误**：

| 失误 | 严重度 |
|------|-------|
| 语气失控（"I am so angry!"）| critical（语域不当）|
| 只抱怨无诉求 | critical（任务不完整）|
| 细节不清（没时间、地点、订单号）| warning |

**关键语气要求**：投诉信应**坚定但克制**，用 "dismayed / disappointed / regrettable" 而非 "angry / furious"。

### 3.8 `apology` 致歉信

**开头**：

> I am writing to **offer / extend my sincerest apologies for** + 失误.
> Please accept my **heartfelt apology** for + 名词短语.

**核心段落**：**解释原因**（不找借口）+ **弥补方案**

**结尾**：Once again, my sincere apologies for the inconvenience caused.

**常见失误**：

| 失误 | 严重度 |
|------|-------|
| 找借口（"It wasn't my fault..."）| warning |
| 没补救方案 | warning |

### 3.9 `thank` 感谢信

**开头**：

> I am writing to **express my heartfelt gratitude for** + 事由.

**正文**：具体感谢事件 + 对方的付出带来的帮助

**结尾**：I shall always remain indebted to you. / **Your kindness means more to me than words can express**.

### 3.10 `other` 其它 / 兜底

用通用 letter 模板，不做功能性套话强制要求。

---

## 四、Letter 通用格式检查（所有类别共享）

| 检查项 | 合格 | 扣分 |
|--------|-----|------|
| Greeting（Dear + 称呼）| 有 | 无 → format_violation |
| Signature（Li Ming / Zhang Wei 按题目指定）| 按指定 | 用真实姓名 → signature_violation（critical）|
| Closing（Yours sincerely, / Yours faithfully,）| 有 | 无 → format_violation |
| 段落数（一般 2-4 段）| 2-4 段 | 1 段或无分段 → format_violation |

---

## 五、output 字段：`letter_category` 完整示例

```json
{
  "meta": {
    "exam_level": "Postgrad1A",
    "task_subtype": "letter",
    "letter_category": "reply",
    "letter_category_confidence": "high"
  },
  "dimension_diagnosis": {
    "format_register": {
      "format": "合规（greeting / body / closing / signature 齐全）",
      "register": "semi-formal（符合 reply 信函要求）",
      "signature_compliance": "符合（用 Li Ming）",
      "category_specific_check": {
        "category": "reply",
        "prev_letter_acknowledged": true,
        "all_points_addressed": true,
        "opening_pattern_match": "I am writing in reply to your letter of April 5th..."
      }
    }
  }
}
```

---

## 六、category 不明时的回退策略

当 Directions 功能不清晰（如 "write a letter to Mr. Smith"）：

1. Skill 优先尝试从内容推断（作文正文中出现 "in reply to" → `reply`）
2. 若仍不确定 → `letter_category = "other"` + `letter_category_confidence = "low"`
3. 在 `dimension_diagnosis.format_register.note` 中注明："category 不明，按通用 letter 规则评判"

---

## 七、参考

- [writing-vocabulary.md](writing-vocabulary.md) 第五节（应用文高频模板）为通用套话库
- [postgrad-official-rubric.md](postgrad-official-rubric.md) 第五节（Directions 原句照搬检测）
- 2005-2025 年考研英语（一/二）A 节真题
