# 三步翻译模块（核心算法）

**直译 → 反思 → 雅化**，每段都要走完，不可跳步（除非用户在 Preflight P2 选了"快速"或"标准"模式）。

> 设计要点：直译保忠实、反思校学术规范与术语一致性、雅化追求顶会风格。三步解耦让模型在每一步只关注一个目标，避免"为流畅而丢精度"。

## 全局不变量（每个 Step 都不可违反）

1. **Provenance 不变**：每段译文的 `segment_id` / `source_page` / `source_section` / `source_excerpt` 一字不改
2. **公式 / 引用 / 数字 不变**：`<FORMULA_X>` `<CITE_X>` `<REF_X>` 等占位符在 Step 1-3 全程不变；最终输出前才用 `scripts/preserve_latex.py --restore` 还原
3. **段落 1:1 对应**：Step 1 → Step 2 → Step 3 段落数严格相等，每段独立可追溯

---

## Step 1 — 直译

**输入**：input-router 产出的 `segments[]`（含 `masked_text` 已掩码公式/引用）。

**输出**：每段补上 `step1_literal` 字段。

### 直译 Prompt（送给 LLM）

```
你是一位精通{源语言}和{目标语言}的学术翻译专家，正在做学术论文逐句直译。

【源语言】{en | zh}
【目标语言】{zh | en}
【段落类型】{narrative | abstract | caption | ...}
【章节】{section_path}

【翻译规则】
1. **忠实优先**：完全忠于原意，不增删任何信息，**不追求流畅**
2. **保持句子边界**：原文是 5 句，译文也必须是 5 句，标点保持对应
3. **占位符严禁触碰**：所有 <FORMULA_X> <CITE_X> <REF_X> <ALGORITHM_X> 等占位符**原样保留**，不解读不改动不翻译
4. **专业术语**：优先使用提供的术语库；术语库未覆盖的，**保留原文 + 括号附译法**，例如 "embedding（嵌入）"
5. **数字、单位、化学式、算法名、数据集名**原样保留
6. **不解释、不评论、不省略**，直接输出译文

【可用术语库】
{glossary_yaml}

【原文】（含掩码占位符）
{masked_text}

【直译输出】
（仅输出译文，不要任何说明）
```

### 直译后的自动校验

每段 Step 1 输出后，**自动**运行：

```python
def validate_step1(original_masked, translation, segment):
    checks = {
        "placeholders_preserved": all(
            f"<{kind}_{i}>" in translation
            for tag, content in segment.preserved_tokens.items()
        ),
        "sentence_count_match": abs(count_sentences(original_masked) - count_sentences(translation)) <= 1,
        "no_truncation": len(translation) > 0.3 * len(original_masked),  # 防偷懒截断
        "no_translation_of_placeholder": not re.search(r'\b(formula|citation|reference|equation)_\d', translation, re.I),
    }
    return checks
```

任一 check 失败 → 重试一次（最多 2 次）→ 仍失败 → 标记 `step1_failed: true`，跳过此段进入 Step 2 但提示用户。

---

## Step 2 — 反思（学术规范 + Chinglish 校正 + 术语一致性 + 去 AI 味）

**输入**：`segments[]` 含 `step1_literal`。

**输出**：每段补上 `step2_academic` 字段 + `reflection_diffs`（Step 1 → Step 2 的修改清单）。

### 反思 Prompt

```
你是一位严格的学术写作审校，需要对一段直译初稿进行**学术规范化**和**Chinglish 校正**。

【目标语言】{zh | en}
【目标会议域】{ml | nlp | cv | ir | general | none}（用户未指定时为 none）
【章节类型】{abstract | intro | method | exp | conclusion | other}

【4 维反思清单】

**维度 1：学术规范**（参考 refs/section-conventions.md）
- {section} 章节是否符合该章节的写作惯例？
- 时态、语态是否符合学术英文/中文规范？
- 主语视角是否一致（we / our method / the model）？

**维度 2：Chinglish 校正**（仅中→英时启用，参考 refs/chinglish-patterns.md）
- 是否有"in recent years"等被滥用的直译？
- 是否有"play an important role"这类空洞表达？
- 是否有"discuss about"这类英文不正确的搭配？
- 主谓一致 / 单复数 / 冠词 是否正确？

**维度 3：术语一致性**（参考下方"全文术语表"）
- 同一术语在不同段落是否被译为不同词？
- 是否使用了术语库的标准译法？

**维度 4：去 AI 味**（参考 refs/anti-ai-patterns.md）
- "在本文中"、"我们提出了"等开篇套话是否过多？
- 列表化、模板化语言是否过重？
- 修辞是否自然（不是模型典型的"首先...其次...最后..."框架）？

【全文术语表】（前面段落已确认的术语映射，必须沿用）
{full_paper_glossary_yaml}

【原文】
{source_text}（已含掩码占位符）

【Step 1 直译】
{step1_literal}

【输出格式】
```yaml
step2_academic: |
  （修订后的译文，占位符保持不变）
reflection_diffs:
  - dimension: chinglish
    before: "in recent years"
    after: "recently"
    reason: "在 Introduction 章节滥用，且非必要时间标记"
  - dimension: terminology
    before: "嵌入向量"
    after: "嵌入"
    reason: "全文已统一为「嵌入」，保持一致"
```
```

### 反思的特殊规则

- **MUST**：反思后的占位符数量 = Step 1 的占位符数量（完整性校验）
- **MUST**：反思后的句子数 与 Step 1 相差不超过 ±2（不允许大段重写）
- **MUST**：每个 `reflection_diff` 必须能在 Step 1 中找到 `before` 文本

---

## Step 3 — 雅化（信达雅 + 顶会风格 + 段落级流动）

**输入**：`segments[]` 含 `step2_academic`。

**输出**：每段补上 `step3_polished` + `polish_diffs`。

### 雅化 Prompt

```
你正在做学术论文的最终雅化润色，目标是达到**投稿/发表级**的语言质量。
基础是 Step 2 的学术规范译文，**不要改变任何技术内容**，只在表达层面做以下提升。

【目标语言】{zh | en}
【目标会议域】{ml | nlp | cv | ir | general}
【章节类型】{abstract | intro | method | exp | conclusion | other}

【3 维雅化】

**维度 1：信达雅**
- "信"：忠实保留 Step 2 的全部技术内容（公式、引用、数字、术语 一字不动）
- "达"：句子流畅，逻辑清晰，无翻译腔
- "雅"：用词得体，节奏感好，符合该章节的语气

**维度 2：顶会风格**（参考 refs/word-choice-table.md）
- 简洁优先：utilize → use, demonstrate → show, a plethora of → many
- 移除填充：it is worth noting that → 删除, in order to → to
- Hedging 校准：not just "may"，要根据证据强度选择 ("may" / "can" / "does")
- 主动态优先（除非主体不重要）：The model was trained → We trained the model

**维度 3：段落级流动**
- 加逻辑连接词（however / thus / nonetheless / in contrast）
- 消除"句子的水滴"（一连串短句无连接）
- 保持段落主题句一致

【上一段终稿】（用于段落间衔接）
{previous_step3 | "（首段）"}

【Step 2 学术规范版】
{step2_academic}

【输出格式】
```yaml
step3_polished: |
  （最终雅化译文，占位符仍保持不变）
polish_diffs:
  - dimension: top_venue_style
    before: "we utilize a plethora of methods to demonstrate"
    after: "we use many methods to show"
    reason: "顶会偏好简洁动词；utilize / a plethora of / demonstrate 均可降级"
```
```

### 雅化的不可省略检查

雅化输出后**自动**运行：

```python
def validate_step3(step2_text, step3_text, preserved_tokens):
    checks = {
        # 关键不变量
        "placeholders_intact": all(
            tag in step3_text
            for tag in re.findall(r'<\w+_\d+>', step2_text)
        ),
        # 数字保留（雅化绝对不可改数字）
        "numbers_preserved": set(re.findall(r'\d+\.?\d*%?', step2_text)) ==
                             set(re.findall(r'\d+\.?\d*%?', step3_text)),
        # 段落数不变
        "paragraph_count_match": step2_text.count('\n\n') == step3_text.count('\n\n'),
        # 长度合理（雅化不应该把 200 字段精简到 50 字）
        "length_reasonable": 0.6 * len(step2_text) < len(step3_text) < 1.4 * len(step2_text),
    }
    return checks
```

任一失败 → 阻断输出当前段，回退到 Step 2，提示用户「雅化失败，使用学术规范版」。

---

## 模式控制（Preflight P2 的"输出深度"映射）

| 用户选择 | 实际执行 | 输出文件 |
|---|---|---|
| **快速** | 仅 Step 1 | `01-step1-literal.md` |
| **标准** | Step 1 + Step 2 | `01-step1-literal.md` + `02-step2-academic.md` |
| **精翻** | Step 1 + Step 2 + Step 3 | 三档全产 + 双栏 + LaTeX + self-check |

> ⚠️ **NEVER 跳 Step**：精翻必须三步全跑。即使 Step 1 看起来已经很好，也必须走 Step 2 反思以保证术语一致性和 Chinglish 校正。

---

## 终段还原 — 占位符还原回真实公式

三步翻译完成后，**最后**一步是还原占位符：

```python
import json
from pathlib import Path

def restore_all(segments, step):  # step = 'step1_literal' | 'step2_academic' | 'step3_polished'
    restored = []
    for seg in segments:
        text = seg[step]
        for tag, content in seg['preserved_tokens_map'].items():
            text = text.replace(tag, content)
        restored.append({**seg, f'{step}_restored': text})
    return restored
```

调用 `scripts/preserve_latex.py --restore` 完成此步骤，输出最终干净文本。

详细规则见 [../refs/formula-preservation.md](../refs/formula-preservation.md)。
