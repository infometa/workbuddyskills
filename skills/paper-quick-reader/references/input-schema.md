# 输入契约（Input Schema）

> 本 Skill 的 v0.1 输入 schema。Skill 从 v1.0 起锁定契约（不做 breaking change）。

## Contents

- [一、顶层结构](#一顶层结构)
- [二、PaperInput 字段详解](#二paperinput-字段详解)
- [三、context 字段](#三context-字段)
- [四、preferences 字段](#四preferences-字段)
- [五、校验规则](#五校验规则)

---

## 一、顶层结构

```json
{
  "mode": "single | compare",
  "papers": [ { /* PaperInput */ } ],
  "compare_dimensions": [ "method", "dataset", ... ],
  "context": {
    "my_direction": "...",
    "specific_question": "..."
  },
  "preferences": {
    "language": "zh | en | bilingual",
    "depth_hint": "auto | force_skim | force_deep",
    "max_connection_points": 5,
    "max_recommended_questions": 3,
    "citation_style": "inline | footnote"
  }
}
```

---

## 二、字段详解

### 2.1 `mode`（必填）

| 值 | 语义 | 约束 |
|---|---|---|
| `single` | 单篇模式 | `papers` 长度必须 = 1 |
| `compare` | 多篇对比 | `papers` 长度 2–10 且 `compare_dimensions` 非空 |

**校验规则**：
- `papers` 缺失或为空 → 报错 `MISSING_PAPERS`
- `mode=single` 但 `papers.length > 1` → 报错 `MODE_MISMATCH`
- `mode=compare` 但 `papers.length < 2` → 报错 `INSUFFICIENT_PAPERS`
- `papers.length > 10` → 报错 `TOO_MANY_PAPERS`，建议分批或改用文献综述 Skill

### 2.2 `papers[i]`（必填）

```json
{
  "source": "pdf_path | docx_path | pasted_text | image_path",
  "content": "...",
  "label": "（可选）PaperA / LLaMA3-paper"
}
```

| `source` | `content` 的语义 | 处理 |
|---|---|---|
| `pdf_path` | 本地 PDF 绝对/相对路径 | `scripts/parse_pdf.py` 抽取 (text, page, section) |
| `docx_path` | 本地 Word 文档路径 | `python-docx` 解析；页码降级为段落编号 |
| `pasted_text` | 用户粘贴的原文 | **必须追问**"这段来自论文的第几页/段？"无答则 `page = null`，精读功能降级 |
| `image_path` | ❌ **拒绝** | 直接报错 `IMAGE_OCR_NOT_SUPPORTED` |

**`label`**：可选的论文代号，默认按 `papers[0]` → `PaperA`，`papers[1]` → `PaperB` 依序分配。

### 2.3 `compare_dimensions`（`mode=compare` 必填）

数组，元素来自以下枚举（≥ 1 项，≤ 8 项避免表格过宽）：

- `research_question` —— 研究问题 / claim
- `method` —— 方法 / 模型架构 / 算法
- `dataset` —— 数据集（含规模、语言、领域）
- `baseline` —— 对比 baseline 选取
- `metric` —— 评估指标（含新提出 vs 沿用）
- `results` —— 关键实验结果（数字）
- `novelty` —— 宣称的创新点
- `limitations` —— 作者承认的 + AI 补充的隐含局限
- `dataset_size` —— 样本数 / 训练规模
- `compute_cost` —— 算力 / 训练时长（若论文披露）
- `future_work` —— 作者展望的未来方向
- `reproducibility` —— 开源代码 / 权重 / 数据的可获得性
- `custom:<字段名>` —— 用户自定义，如 `custom:中文数据占比`

维度详细定义见 [comparison-dimensions.md](comparison-dimensions.md)。

### 2.4 `context`（可选，决定深度档位组合）

```json
{
  "my_direction": "模糊研究方向，如：多模态大模型的幻觉评估",
  "specific_question": "具体问题，如：本文的 52K 指令数据是怎么采样的？"
}
```

| `my_direction` | `specific_question` | 深度档位组合 |
|:---:|:---:|---|
| ❌ | ❌ | `[skim]` |
| ✅ | ❌ | `[skim, guided]` |
| ❌ | ✅ | `[skim, deep]` |
| ✅ | ✅ | `[skim, guided, deep]` |

**校验**：
- `my_direction` 长度 < 5 字 → 追问"请至少给 2 个关键词 + 1 个子问题"
- `specific_question` 空字符串 / 标点堆砌 → 视为未提供

### 2.5 `preferences`（可选，全部有默认值）

| 字段 | 枚举 / 范围 | 默认 | 说明 |
|---|---|---|---|
| `language` | `zh` / `en` / `bilingual` | `zh` | 反馈语言 |
| `depth_hint` | `auto` / `force_skim` / `force_deep` | `auto` | 强制覆盖档位推断 |
| `max_connection_points` | 3–7 | 5 | 引导关联点条数上限 |
| `max_recommended_questions` | 2–5 | 3 | 推荐问题条数 |
| `citation_style` | `inline` / `footnote` | `inline` | 报告中引用原文的呈现方式 |

**`depth_hint` 行为**：
- `force_skim` → 即使 `context` 有值也只做裸读（适合批量 pre-screen 场景）
- `force_deep` → 即使没 `specific_question` 也尝试精读，AI 自拟 5 个最值得问的问题

---

## 三、完整示例

### 3.1 裸读单篇（最简）

```json
{
  "mode": "single",
  "papers": [
    { "source": "pdf_path", "content": "./papers/self-instruct.pdf" }
  ]
}
```

### 3.2 引导 + 精读（三档叠加）

```json
{
  "mode": "single",
  "papers": [
    { "source": "pdf_path", "content": "./papers/self-instruct.pdf", "label": "PaperA" }
  ],
  "context": {
    "my_direction": "多模态大模型的幻觉评估",
    "specific_question": "52K 指令数据是怎么采样和过滤的？"
  },
  "preferences": {
    "language": "zh",
    "max_connection_points": 5
  }
}
```

### 3.3 多篇对比（5 维度 + 用户方向）

```json
{
  "mode": "compare",
  "papers": [
    { "source": "pdf_path", "content": "./papers/self-instruct.pdf", "label": "A" },
    { "source": "pdf_path", "content": "./papers/instruct-gpt.pdf", "label": "B" },
    { "source": "pdf_path", "content": "./papers/lima.pdf", "label": "C" }
  ],
  "compare_dimensions": [
    "research_question",
    "method",
    "dataset",
    "results",
    "limitations"
  ],
  "context": {
    "my_direction": "低资源中文指令微调"
  },
  "preferences": {
    "language": "zh"
  }
}
```

### 3.4 作为子 Skill 被调用（最小契约）

```python
invoke_skill("paper-quick-reader", inputs={
    "mode": "compare",
    "papers": [
        {"source": "pdf_path", "content": p, "label": f"P{i}"}
        for i, p in enumerate(paper_paths)
    ],
    "compare_dimensions": ["method", "dataset", "results", "limitations"],
    "context": {"my_direction": user_research_topic},
    "preferences": {"language": "zh"}
})
```

---

## 四、错误码清单

| 错误码 | 含义 | 处理 |
|---|---|---|
| `MISSING_PAPERS` | `papers` 字段缺失或为空 | 追问用户提供 PDF 路径或粘贴文本 |
| `MODE_MISMATCH` | `mode` 与 `papers` 数量不符 | 提示用户选择正确 mode |
| `INSUFFICIENT_PAPERS` | compare 模式但 < 2 篇 | 建议补充论文或改为 single 模式 |
| `TOO_MANY_PAPERS` | > 10 篇 | 建议分批或改用文献综述 Skill |
| `IMAGE_OCR_NOT_SUPPORTED` | `source = image_path` | 明确拒绝，要求文本层 PDF |
| `PDF_IMAGE_LAYER_ONLY` | PDF 无文本层（扫描件）| `scripts/parse_pdf.py` 抛出后退出 |
| `PDF_ENCRYPTED` | PDF 加密无法解析 | 建议解密后重试 |
| `COMPARE_DIMS_MISSING` | compare 模式未提供 `compare_dimensions` | 让用户从 12 个内置维度多选 |
| `DIRECTION_TOO_VAGUE` | `my_direction` < 5 字 | 追问细化 |
| `SPECIFIC_QUESTION_EMPTY` | `specific_question` 为空白字符串 | 视为未提供，降级为裸读/引导 |
