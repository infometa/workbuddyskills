# framework-rubric.md —— 骨架质量评分规则

> **文档定位**:LLM 在 SKILL.md Step 3(skim 骨架生成)/ Step 4(guided 节点讲解)/ Step 6(deep 全叶子讲解)产出内容前后,**自检的硬性标准**。
> `scripts/assemble_result.py` 只校验**数量约束**(节点数 ≤ 100 / 层级 ≤ max_levels);**质量**由本文档 + LLM 自评保证。
> 与姐妹 skill `paper-quick-reader/references/summary-card-rubric.md` 同源,但单元从 "summary card" 换为 "tree node"。

---

## 1. 三档深度的差异化标准

| 档位 | 单元 | 字数 | 触发条件 | 主要评分维度 |
|---|---|---|---|---|
| `skim` | 节点 title | ≤ 30 字 | 默认 | 广度 / 层级 / MECE / 命名 |
| `guided` | 节点 title + explanation | 200-500 字 | context 升档 | skim + 讲解清晰度 / 易混点 / 例子 |
| `deep` | 全叶子节点 title + explanation + drill | 300-800 字 | force_deep 或 deep_explain | guided + 错点 / 例题 / 常考考点 |

---

## 2. skim 骨架评分(7 维)

### 2.1 广度(Breadth)· 必满足

- **2-7 子节点 / 父节点**:每层不少于 2(否则降为单链)、不多于 7(米勒数字 7±2)
- **6 大模块感**:对一门完整课程,顶层模块通常 4-7 个(本 fixture「大学英语」= 6,合规)
- ❌ 反例:顶层只有 2 个模块"理论"+"实践" → 抽象度过高,几乎无信息量

### 2.2 层级(Depth)· 必满足

- **3-5 层结构**:层数 = `max_depth + 1`,目标 4 层(根 → 模块 → 子模块 → 叶子知识点)
- skim 模式叶子层 ≤ 3 层(level=3),除非用户显式 `max_levels=5`
- ❌ 反例:6 层嵌套且每层只 2 子 → 退化为单链,失去"骨架"语义

### 2.3 MECE 互斥穷尽 · 必满足

- **同层兄弟节点不重叠**(M = Mutually Exclusive)
  - ❌ 反例:语法层既有"虚拟语气"又有"if 条件句"——后者是前者子集,应嵌套
- **覆盖父概念全部子领域**(CE = Collectively Exhaustive)
  - ❌ 反例:听力下只有"短对话 + 长对话",漏了"听写"和"复合式"
- **MECE 自检 prompt**:每个父节点列完子节点后问自己"是否还有第 N+1 类被漏掉?是否有两个子节点其实可以合并?"

### 2.4 命名简洁(Concision)· 应满足

- 单节点 title ≤ 30 字符(中英混合)
- 优先用学科术语 + 括号补英文(如 `名词性从句(Nominal Clauses)`)
- ❌ 反例:`一种用于表达说话者主观意愿的特殊语法形式叫做虚拟语气`

### 2.5 平行结构(Parallelism)· 应满足

- 同层兄弟节点采用**一致的语法结构**
  - ✓ 同为名词短语:`议论文` / `应用文` / `图表作文`
  - ❌ 混合:`议论文` / `怎么写应用文` / `图表 → 文字转换`(动词 / 介词混用)

### 2.6 命名一致性(Consistency)· 应满足

- 编号风格一致:全用 `1.1.1` 或全用 `①②③`,不混用
- 中英括号风格一致:全 `中文(English)` 或全 `中文 (English)`

### 2.7 节点数自洽 · 必满足(脚本强校)

- `total_nodes ≤ 100` —— `scripts/assemble_result.py` 强校
- 单父节点子数 ≤ 9
- 单 fixture 推荐 30-90 节点(< 30 太稀疏,> 90 应分课)

---

## 3. guided 节点讲解评分(5 维)

### 3.1 选节点(Selection)

LLM 在 guided 模式下挑选 **5-10 个高 ROI 节点**做讲解,选择标准(按权重):

| 权重 | 维度 | 含义 |
|---:|---|---|
| 0.30 | 用户上下文匹配 | `focus_topics` 命中 / `learning_goal` 关键词出现 |
| 0.25 | 概念基础性 | 该节点是否多个其它节点的 prerequisite |
| 0.20 | 易错率 | 学科常见混淆点(如 affect/effect、虚拟语气) |
| 0.15 | 考查频率 | (v1.1+ 命中真题年份后启用) |
| 0.10 | 用户级别匹配 | beginner 偏底层,advanced 偏综合 |

### 3.2 讲解长度(Length)· 必满足

- **200-500 字 / 节点**(中文计字符,英文按 word × 1.6)
- < 200 字 → 信息密度过低
- > 500 字 → 偏向 deep 模式,留待升档

### 3.3 讲解结构(Structure)· 应满足

每段讲解推荐三段式:

```
[定义]      —— 1-2 句 What
[展开]      —— 2-4 句 How / Why,含 1 个具体例子
[易错点]    —— 1-2 句 Pitfall(可省,但有则加分)
```

### 3.4 用户级别匹配(Level Adaptation)

| user_level | 讲解风格 |
|---|---|
| `beginner` | 类比 + 大白话 + 避免学科术语堆砌 |
| `intermediate` | 标准定义 + 1-2 例子 + 简短易混对比 |
| `advanced` | 假设已知基础 + 直击边界场景 / 与其它知识的关联 |

### 3.5 防 AI 味(Anti-AI-Flavor)

借鉴 `resume-assistant/references/ai-phrase-blacklist.md`,讲解中避免:

- 通用空话:"非常重要"、"至关重要"、"在很多场景下都有应用"
- 模板套语:"接下来让我们看看"、"综上所述"、"以上就是"
- 过度抽象:用具体例子替换抽象修饰

---

## 4. deep 全叶子讲解评分

deep 模式产出 **全部叶子节点的 explanation + drill**(钻取):

```
[explanation]   —— 与 guided 同结构,但 300-800 字
[drill]         —— 1-3 个易混点 + 1-2 道例题(可选)
[cross_ref]     —— 同框架内强相关节点的 id 列表(供概念依赖挖掘)
```

约束:
- 单 fixture 总讲解字数 ≤ 30,000 字(否则 LLM 输出截断风险)
- 若 leaf_count > 50,自动降级为"分批 deep"(每批 ≤ 20 叶子,提示用户分次调用)

---

## 5. 自评 checklist(LLM 在 Step 3 / 4 / 6 末尾必跑)

### skim 阶段 self-check

```
[ ] total_nodes ≤ 100?(脚本会强校,但提前算)
[ ] max_depth + 1 ≤ max_levels(默认 5)?
[ ] 顶层 4-7 个模块?
[ ] 每个父节点 2-7 子?
[ ] 同层兄弟 MECE 互斥穷尽?
[ ] 平行结构(同语法形式)?
[ ] 命名风格一致(编号 / 括号)?
```

### guided 阶段 self-check

```
[ ] 选了 5-10 个节点?
[ ] 每个讲解 200-500 字?
[ ] 含定义 + 例子 + 易错点(三段式)?
[ ] 匹配 user_level(beginner/intermediate/advanced)?
[ ] 无 AI 味套语?
[ ] 与 focus_topics / learning_goal 强相关?
```

### deep 阶段 self-check

```
[ ] 覆盖全部叶子节点?(leaf_count == len(node_explanations))
[ ] 总字数 ≤ 30,000?
[ ] 每个叶子有 explanation + (可选) drill + cross_ref?
[ ] cross_ref 中的 node_id 都真实存在于 framework_tree?
```

---

## 6. 升档判定(scripts vs LLM 协同)

`scripts/validate_input.py` 已经按 `context` 字段决定 `depth_used`,但 LLM 在 Step 3 完成 skim 后,**仍可主动建议升档**,通过 `recommended_questions[*].expected_depth_after_followup` 字段回传:

```json
{
  "id": "q1",
  "q": "我目标 6 个月通过 CET-4,该重点投入哪几个分支?",
  "why": "触发 guided + learning_goal",
  "expected_depth_after_followup": ["skim", "guided"]
}
```

用户在下一轮交互中带上 `learning_goal` 字段后,validate_input.py 自动升档,LLM 接着做 guided。

---

## 7. 与 scripts 的分工

| 校验项 | scripts 负责 | 本文档 / LLM 自评负责 |
|---|---|---|
| 节点数上限 | ✅ assemble_result.py | — |
| 层级上限 | ✅ assemble_result.py | — |
| 单父节点子数 | — | ✅ rubric §2.1 |
| MECE | — | ✅ rubric §2.3(LLM 自评) |
| 平行结构 / 命名 | — | ✅ rubric §2.5-2.6 |
| 讲解字数 | 部分(可加 length 校验)| ✅ rubric §3.2 / §4 |
| AI 味检测 | — | ✅ rubric §3.5 |
| Provenance 标注 | ✅ verify_provenance.py | — |

> **不变量**:scripts 只做"机器能严校的"(数量 / schema / ngram);质量校验靠本文档 + LLM 自评。

---

## 8. 与姐妹 skill 的关系

| 姐妹 skill | 对应 rubric | 共享设计 |
|---|---|---|
| `paper-quick-reader` | `summary-card-rubric.md` | 三段式结构、用户级别适配、防 AI 味 |
| `resume-assistant` | `bullet-formulas.md` | 字数约束、平行结构、防套语 |
| `english-exam-writing-reviewer` | (官方档次描述符) | 自评 checklist 模式 |

> 共享设计的好处:跨 Skill 调用时,LLM 已熟悉评分逻辑,无需重新学习。
