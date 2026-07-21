# 精读回答协议（Deep-Dive Protocol）

> 精读模式下，Skill 针对用户的 `specific_question` 产出**原文锚定 + 批判性分析**的回答。
> 每个回答包含 3 块：`answer` / `original_excerpts` / `critical_analysis`。

## Contents

- [一、回答三段结构](#一回答三段结构)
- [二、original_excerpts 规范](#二original_excerpts-规范)
- [三、critical_analysis 三子字段](#三critical_analysis-三子字段)
- [四、原文未涉及时的处理](#四原文未涉及时的处理)
- [五、peer_review 附加模块](#五peer_review-附加模块)

---

## 一、回答三段结构

### 1.1 `answer`（综合回答）

**格式要求**：
- 1–3 段中文
- 直接回答问题，不绕弯
- 必须**基于原文**，不能自由发挥
- 长度 100–400 字（按问题复杂度）

**开头模板**（推荐）：
- 描述性问题："根据原文，XX 是..."
- 比较性问题："本文 XX 与 YY 的差异在于..."
- 原因性问题："作者选择 XX 的理由是..."
- 评价性问题："从原文证据看..."

### 1.2 `original_excerpts`（原文引用，**硬约束必填**）

**格式要求**：
- **数组，非空**（否则视为幻觉，进入错误分支）
- 每条必含三元组 `{page, section, text}`
- `text` 必须是**原文的 ngram**（5-gram 以上可匹配）
- 保留原文语言（英文论文保留英文，不强行翻译）
- 每条 text 长度 30–200 字符

**示例**：

```json
"original_excerpts": [
  {
    "page": 5,
    "section": "3.2 Dataset Construction",
    "text": "We start with 175 seed instructions and use 8 human-written + 2 model-generated as in-context examples for each iteration..."
  },
  {
    "page": 5,
    "section": "3.3 Filtering",
    "text": "We filter out instructions with ROUGE-L > 0.7 similarity to any existing instruction."
  }
]
```

**引用条数**：
- 最少 1 条
- 最多 5 条（超过则挑最能支撑回答的）
- 同段多处引用 → 合并或标 `"..."` 截断

### 1.3 `critical_analysis`（批判性分析，三段式）

**结构**：

```json
"critical_analysis": {
  "agree_with": [ /* 可信 / 合理的部分 */ ],
  "question": [ /* 值得质疑 / 作者未讨论的 */ ],
  "complement": [ /* 对用户方向的补充视角 */ ]
}
```

**硬约束**：
- **至少填 2 段**（空段填 `[]`）
- 每段**数组**，每条 1 句，30–100 字

#### `agree_with`（同意 / 认可）

- 指出论文**可信 / 合理 / 设计得当**的地方
- 必须**具体**（不是"方法不错"这种空话）

正面示例：
```
"agree_with": [
  "采样流程设计合理，bootstrap + ROUGE-L 过滤形成闭环",
  "选择 175 条种子指令符合主流 instruction tuning 规模，便于复现"
]
```

#### `question`（质疑 / 追问）

- 指出论文**未充分讨论 / 设计不严谨 / 证据不足**的地方
- 包括：缺消融 / 阈值随意 / 数据偏差 / 结论过强

正面示例：
```
"question": [
  "ROUGE-L 0.7 的阈值没做消融实验，为什么不是 0.6 / 0.8？",
  "2 条模型生成样本的引入可能加剧自迭代偏差，作者未讨论",
  "仅用 GPT-3 base 做实验，结论是否 generalize 到 LLaMA / GLM 未验证"
]
```

#### `complement`（补充视角）

- **仅当** `context.my_direction` 存在时生效
- 把本文与用户方向**连起来**，指出如何应用 / 扩展 / 警惕
- 与 `connection_points` 的区别：`connection_points` 是论文**整体**对用户方向的关联；`complement` 是针对**这个具体问题**的额外视角

正面示例：
```
"complement": [
  "对你的方向：如果直接复用该流程生成『幻觉实例』，需注意 bootstrap 的偏差放大效应",
  "你的幻觉评估若引入 ROUGE-L 过滤，建议补做 0.5/0.6/0.7/0.8 消融以论证阈值选择"
]
```

---

## 二、特殊情况处理

### 2.1 论文未涉及用户问题

当 `specific_question` 的答案**在论文里找不到**时：

```json
{
  "question": "本文用了多大的 GPU？训练时长？",
  "answer": "原文未涉及具体 GPU 规格与训练时长的讨论。建议直接查看 GitHub repo 的 training script 或联系作者。",
  "original_excerpts": [],
  "critical_analysis": {
    "agree_with": [],
    "question": [
      "本文未披露训练成本（GPU 型号 / 时长 / token 数），影响复现成本评估"
    ],
    "complement": []
  }
}
```

**硬约束**：
- `original_excerpts = []` **允许**但必须在 `answer` 开头明说"原文未涉及"
- **严禁**编造页码 / 编造引用 / 编造回答

### 2.2 问题触碰图表 / 公式 / 代码

| 问题类型 | 处理 |
|---|---|
| 图表问题（"Figure 3 显示了什么"）| `section = "Figure 3 caption"` + 引 caption 原文 |
| 公式问题（"Eq. 5 的含义"）| `section = "Equation 5"` + 引公式前后文字描述 |
| 代码 / 算法问题（"Algorithm 1 第 7 行"）| `section = "Algorithm 1"` + 引该行伪代码 |

### 2.3 多子问题问题

用户问 "XX 是什么？YY 是什么？" → 在 `answer` 里分两段回答，`original_excerpts` 可以分别对应两个问题（允许 5 条以内混排）。

### 2.4 开放性问题（无唯一答案）

用户问 "你觉得这方法好吗？" → 转为批判性评价，重点在 `critical_analysis`，`answer` 字段给总体评价（必须基于原文证据）。

---

## 三、`force_deep` 模式：AI 自拟问题

当 `preferences.depth_hint = "force_deep"` 且 `context.specific_question` 未提供时，AI 自拟 **5 个最值得问的问题**分别精读。

**自拟规则**：
1. 从 `summary_card.limitations` 中挑 1 个"为什么没做 XX"的问题
2. 从 `summary_card.method` 中挑 1 个"关键设计选择的理由"问题
3. 从 `summary_card.key_results` 中挑 1 个"结果可否复现 / 泛化"问题
4. 从 `summary_card.dataset` 中挑 1 个"数据质量 / 偏差"问题
5. 1 个"方法能否迁移到 X 领域"的应用性问题

每个自拟问题按本文档 §1 格式产出完整回答，存入 `deep_dive_answers` 数组。

---

## 四、质量检查清单（AI 自检）

生成 `deep_dive_answers[i]` 后，AI **自检**：

- [ ] `answer` 是否直接回答了问题（不绕弯）？
- [ ] `original_excerpts` 是否**非空**（除非原文未涉及）？
- [ ] 每条 `excerpt.text` 是否能在 `parse_pdf.py` 输出的 text 中做 ngram 匹配？
- [ ] `critical_analysis` 三段是否**至少 2 段**非空？
- [ ] `agree_with` / `question` / `complement` 是否**具体**而非空话？
- [ ] 若原文未涉及该问题，是否在 `answer` 开头明说？

任一条不过 → 重写或降级为 `"原文未涉及"`。

---

## 五、常见错误（NEVER）

- **NEVER** 让 `original_excerpts = []` 同时 `answer` 却引用"论文提到"（自相矛盾，必然被 provenance 审计打回）
- **NEVER** 编造 excerpt 的 `text`（必须是原文 ngram，由 `verify_provenance.py` 校验）
- **NEVER** 编造 `page` 或 `section`（必须来自 `parse_pdf.py` 的 `(text, page, section)` 三元组）
- **NEVER** 把 `critical_analysis` 全填空（`[]` 只允许用于 `agree_with` 或 `complement`，不允许三段都空）
- **NEVER** 在 `complement` 里写泛泛的 "可以启发你的研究" —— 必须具体到**如何用 / 要避免什么**
- **NEVER** 一个回答引用 > 5 条 excerpt（信息过载，选最支撑的）
- **NEVER** 把原文英文**机翻**填到 `text`（保留原文英文，`answer` 中用中文概括即可）
