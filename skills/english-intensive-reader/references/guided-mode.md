# Guided Mode — english-intensive-reader
# references/guided-mode.md

> 渐进式精读模式（`mode=guided`）的完整执行规范。
> 融合自 gaokao-english-tutor 的四步教学法，适合想**深度理解**文章的用户。
> SKILL.md Step 3 激活此模式时，必须加载本文件。

---

## 一、模式定位

| 维度 | standard 模式 | guided 模式 |
|------|-------------|------------|
| 适合人群 | 自学用户，想快速获取分析结果 | 想深度理解、主动思考的用户 |
| 输出方式 | 直接输出完整 `sentence_unit` | 四步引导，每步可暂停追问 |
| 词义获取 | 直接给出释义 | 先引导用户用上下文线索推断，再给正式释义 |
| 交互轮次 | 1 轮（输入→输出）| 多轮（每步一个来回）|

---

## 二、四步推进流程

### Step A：词汇扫除

**开场白**（逐字输出）：
```
先别急着分析，你先读一遍这段文字，
把不认识的单词标出来，咱们先解决词汇问题。
有哪些词不认识？
```

**执行规则**：
1. 等待用户列出不认识的词
2. 对每个生词，**先**引导用户用上下文线索推断词义（见第三节）
3. 用户推断后，给出正式释义 + 构词法拆解（如有）
4. **NEVER 在用户推断前直接给出释义**（N12）

**构词法拆解格式**：
```
ubiquitous = ubi-（拉丁语：到处）+ -quit-（去）+ -ous（形容词后缀）
→ 字面义：到处都去的 → 引申义：无处不在的
```

**常见前缀速查**：

| 前缀 | 含义 | 示例 |
|------|------|------|
| `un-` / `in-` / `im-` | 否定 | unhappy / invisible / impossible |
| `re-` | 再次 | reconsider / rebuild |
| `pre-` | 之前 | predict / precede |
| `over-` | 过度 | overestimate / overwhelm |
| `under-` | 不足 | undermine / underestimate |
| `inter-` | 之间 | interact / international |
| `trans-` | 跨越 | transform / transmit |
| `mis-` | 错误 | misunderstand / mislead |

**常见后缀速查**：

| 后缀 | 词性 | 示例 |
|------|------|------|
| `-tion` / `-sion` | n. | information / decision |
| `-ment` | n. | development / achievement |
| `-ness` | n. | happiness / awareness |
| `-ity` | n. | ability / diversity |
| `-ous` / `-ious` | adj. | dangerous / ambitious |
| `-ive` | adj. | effective / creative |
| `-ize` / `-ise` | v. | realize / organize |
| `-fy` | v. | simplify / clarify |
| `-ly` | adv. | quickly / significantly |

---

### Step B：句子结构

**开场白**（逐字输出）：
```
词汇问题解决了，很好。
现在咱们来理解这个句子。
你试着用中文说说这句话的意思。
注意句子结构：主语是谁？谓语是什么？宾语/表语是什么？
```

**执行规则**：
1. 等待用户尝试翻译或描述句子结构
2. 对用户的回答给出反馈（正确/部分正确/需要调整）
3. 输出完整 `sentence_analysis`：
   - `backbone`：主干（必须是原句子集）
   - `modifiers`：修饰成分列表（含 role + note）
   - `grammar_tags`：语法标签（来自 `grammar-tag-taxonomy.md` 枚举）
4. 长难句额外标注**从句层次**：
   ```
   主句：[主干]
   └── 第1层从句：[从句类型] [从句文本]
       └── 第2层从句：[从句类型] [从句文本]
   ```

**长难句拆解示例**：
```
原句：The report, which was published last year by researchers who had spent
      a decade studying the phenomenon, concluded that the effects were irreversible.

主句：The report concluded that the effects were irreversible.
└── 第1层非限制性定语从句（which）：which was published last year by researchers
    └── 第2层限制性定语从句（who）：who had spent a decade studying the phenomenon
```

---

### Step C：段落逻辑

**开场白**（逐字输出）：
```
句子理解了，很好。
现在看这一段的整体结构：
- 这段的主旨句在哪里？（第几句？）
- 支撑论据是什么？
- 和上一段是什么关系？（递进 / 转折 / 举例 / 因果）
```

**执行规则**：
1. 等待用户回答段落结构问题
2. 输出 PEAL 段落分析：

```json
{
  "paragraph_id": "p01",
  "function": "引入 | 论证 | 转折 | 举例 | 结论",
  "peal": {
    "point": "段落核心论点（一句话，来自原文）",
    "evidence": "支撑论点的关键句（原文引用 + sentence_id）",
    "analysis": "作者如何通过语言/结构实现这一效果（≤ 30 字）",
    "link": "与全文主旨或上下段的关联（≤ 20 字）"
  }
}
```

**段落功能枚举**：

| 功能 | 标志词/特征 |
|------|-----------|
| `引入` | 首段，提出话题/背景 |
| `论证` | 提出论点 + 给出证据 |
| `转折` | however / but / yet / on the contrary |
| `举例` | for example / for instance / such as / take ... as an example |
| `结论` | in conclusion / therefore / thus / in summary |

---

### Step D：全文脉络

**开场白**（逐字输出）：
```
很好，段落结构也清楚了。
最后，咱们来总结一下全文：
- 文章的核心观点是什么？
- 作者用了哪些论证方式？
- 有没有让你印象深刻的句型？
```

**执行规则**：
1. 等待用户总结（可选，用户可说"直接给我"跳过）
2. 输出底部汇总：
   - `article_summary`（3~5 句，每句 ≤ 40 字）
   - `key_patterns`（3 个值得背诵句型，含 source_id）
   - `upgrade_suggestions`（2 条句式升级建议）

---

## 三、词义推断线索（context_clues）

> 引导用户用上下文线索推断生词词义，是 guided 模式的核心教学法。

| 线索类型 | 标志词 | 推断方向 | 引导话术 |
|---------|--------|--------|---------|
| `转折` | but / however / yet / although | 生词与前文意思**相反** | "注意这里有个 but，前面说的是 X，那这个词可能是什么意思？" |
| `因果` | because / so / therefore / thus | 生词是前/后文的**原因或结果** | "这里有个 because，前面/后面说了什么？那这个词可能表示什么？" |
| `并列` | and / or / also / similarly | 生词与前文意思**相近** | "这里和 [已知词] 并列，它们应该是同类的，你猜这个词是什么意思？" |
| `举例` | for example / such as / like | 生词是例子的**上位概念** | "后面举了 [例子] 作为例子，那这个词应该是什么的总称？" |
| `解释` | that is / in other words / namely | 生词的**直接释义**在后文 | "后面用 'that is' 解释了，你看后面说的是什么？" |
| `对比` | while / whereas / on the contrary | 生词与对比项意思**相反** | "这里和 [对比词] 形成对比，[对比词] 是 X，那这个词可能是什么？" |

**context_clues 输出格式**：
```json
{
  "clue_type": "转折",
  "clue_word": "however",
  "inference": "前文说政策有效，however 后接此词，推断含义为'无效的/适得其反的'"
}
```

---

## 四、guided 模式 NEVER 规则

| # | 禁令 |
|---|------|
| G1 | **NEVER 在 Step A 用户推断前直接给出词义**（等待用户先尝试）|
| G2 | **NEVER 在 Step B 用户尝试前直接给出 backbone**（等待用户先描述句子结构）|
| G3 | **NEVER 跳过某个 Step**（即使用户说"快点"，也要完成当前 Step 再进入下一步）|
| G4 | **NEVER 在用户说"直接给我"时拒绝**（用户明确要求跳过引导时，直接输出结果）|
| G5 | **NEVER 对用户的错误推断直接否定**，应先肯定尝试，再引导修正（"思路对了，不过注意..."|

---

## 五、guided 模式触发条件

用户说以下任一表达时，自动切换到 guided 模式：
- "引导我理解"
- "一步一步来"
- "帮我深度理解"
- "教我怎么读"
- "我想学习这篇文章"
- `mode=guided`（显式参数）

用户说以下表达时，保持 standard 模式：
- "直接给我分析"
- "快速精读"
- "帮我生成笔记"
