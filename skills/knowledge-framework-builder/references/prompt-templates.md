# prompt-templates.md —— LLM Prompt 模板库

> **文档定位**:SKILL.md 8 步工作流中,LLM 在 Step 3 / 4 / 5 / 6 创作内容时的**可复用 Prompt 模板**。
> 这些模板是与 `scripts/` 配套的"内功心法":scripts 负责装配 / 校验 / 渲染,模板负责保证 LLM 每次产出都符合 `framework-rubric.md` 与 `provenance-spec.md` 的契约。
> 模板均**自包含**(含输入变量 + 约束 + 输出 schema + 自检 checklist),可直接拷贝到 LLM 调用。

---

## 0. 通用约束(所有 Prompt 共享)

> **System 段**(放在 messages[0]):

```
你是「知识框架梳理 Skill」的内核 LLM。你的任务是为用户生成结构化、可追溯、防幻觉的知识框架。

不变量(违反任意一条都重新生成):
1. 输出严格符合本 Prompt 给出的 JSON schema(不加多余字段、不省必填字段)
2. 节点 id 命名规则: 根 = "n0", 大模块 = "n{1-9}", 二级 = "n{大}.{小}", 三级 = "n{大}.{中}.{小}"
3. 单课程节点总数 ≤ 100,层数 ≤ 5(参考 references/framework-rubric.md §2.7)
4. 每个节点必带 evidence_source ∈ {user_material, ai_inference, curated_syllabus},参考 references/provenance-spec.md §1
5. 中文为默认输出语言;术语首次出现时括号附英文
6. 禁用 AI 套话("非常重要"、"至关重要"、"综上所述"等),参考 references/framework-rubric.md §3.5
```

---

## 1. Step 3 · skim 骨架生成 Prompt

### 1.1 模板

```
=== 输入 ===
课程主题: {course_topic}
用户材料:
{material_files_or_none}
用户上下文:
- focus_topics: {focus_topics_or_null}
- learning_goal: {learning_goal_or_null}
- user_level: {user_level_or_null}
模式: {mode}             # topic_only / material_first / hybrid
深度: skim
最大层数: {max_levels}    # 默认 5
最大节点数: 100

=== 任务 ===
按以下顺序产出 framework_tree:
1. 列出 4-7 个顶层模块(覆盖该课程的核心维度,符合 MECE)
2. 每个模块下列 2-7 个二级子模块
3. 每个二级下列 0-5 个三级叶子节点(必要时可不展开)
4. 给每个节点标 evidence_source:
   - mode=topic_only → 全部 ai_inference
   - mode=material_first → 优先 user_material(如能从材料定位则填 evidence_locator)
   - mode=hybrid → 视情况混用

=== 输出 schema ===
{
  "framework_tree": {
    "id": "n0",
    "title": "{course_topic}",
    "level": 0,
    "evidence_source": "ai_inference|user_material",
    "children": [
      {
        "id": "n1",
        "title": "一、xxx",
        "level": 1,
        "evidence_source": "...",
        "children": [...]
      }
    ]
  },
  "recommended_questions": [
    {
      "id": "q1",
      "q": "用户可能问的下一个问题",
      "why": "触发什么深度升档 / 什么字段",
      "expected_depth_after_followup": ["skim", "guided"]
    }
  ]
}

=== 自检 checklist(产出前必跑)===
[ ] 顶层模块 4-7 个? 同层兄弟 MECE?
[ ] 总节点数 ≤ 100? 最大层数 ≤ {max_levels}?
[ ] 每节点 title ≤ 30 字符? 命名风格平行?
[ ] 节点 id 严格按规则命名?
[ ] recommended_questions 恰好 3 条?(覆盖升档 / 概念依赖 / 跨课程对比)
[ ] mode=topic_only 时所有 evidence_source = ai_inference?
```

### 1.2 调用例(对应 fixture topic-only-cet)

输入:
- course_topic = "大学英语"
- material_files_or_none = "(无)"
- mode = topic_only
- focus_topics / learning_goal / user_level 全 null

期望输出:见 `demos/knowledge-framework-builder/result-fixtures/topic-only-cet/result.json` 的 `framework_tree` + `recommended_questions`。

---

## 2. Step 4 · guided 重点节点选择 + 200-500 字讲解 Prompt

### 2.1 模板

```
=== 输入 ===
已生成的 framework_tree:
{framework_tree_json}
用户上下文:
- focus_topics: {focus_topics}
- learning_goal: {learning_goal}
- user_level: {user_level}     # beginner / intermediate / advanced

=== 任务 ===
1. 从 framework_tree 选 5-10 个高 ROI 节点(参考 framework-rubric.md §3.1 选择权重)
2. 为每个选中节点写 200-500 字 explanation,三段式:
   [定义] 1-2 句 What
   [展开] 2-4 句 How / Why,含 1 个具体例子
   [易错点] 1-2 句 Pitfall(可省)
3. 按 user_level 调整语气:
   - beginner: 类比 + 大白话 + 避免术语堆砌
   - intermediate: 标准定义 + 例子 + 简短易混对比
   - advanced: 假设已知基础 + 边界场景 + 与其它知识关联

=== 输出 schema ===
{
  "node_explanations": [
    {
      "node_id": "n2.4",          # 必须是 framework_tree 中已存在的 id
      "title": "2.4 虚拟语气",     # 冗余字段,便于校验
      "selection_reason": "属于 focus_topics 中的『语法』+ 是 if 三类 / wish 等多个节点的 prerequisite",
      "explanation": "[定义] 虚拟语气是 ...\n\n[展开] 在英语中常见 ...\n\n[易错点] suggest 后接 should + do,但...",
      "user_level_match": "intermediate",
      "word_count": 320
    }
  ]
}

=== 自检 checklist ===
[ ] 选中节点数 5-10?
[ ] 每个 explanation 200-500 字(中文按字符,英文按 word × 1.6)?
[ ] 三段式结构齐全(定义+展开+易错点)?
[ ] 用户级别一致?
[ ] 无 AI 套话?
[ ] 每个 node_id 在 framework_tree 中真实存在?
```

### 2.2 选择权重提示词(给 LLM 的内部计算指引)

```
对每个候选节点 n,计算 ROI = sum(weights):
  + 0.30 if n 命中 focus_topics 之一
  + 0.25 if n 是其它节点的 prerequisite(预估)
  + 0.20 if n 是学科常见易混点
  + 0.15 if n 是学科高频考点(v1.1+)
  + 0.10 if n 与 user_level 匹配
取 top 5-10。
```

---

## 3. Step 5 · 概念依赖挖掘 Prompt

### 3.1 模板

```
=== 输入 ===
framework_tree(节选 + 全节点 id 列表):
{tree_json}
策略: {strategy}             # conservative / aggressive
节点总数: {total_nodes}
边数预算:
  conservative: ≤ {total_nodes * 0.15} 条,只挖 prerequisite + contrast
  aggressive:   ≤ {total_nodes * 0.30} 条,6 类全开

=== 任务 ===
按 references/concept-dependency-taxonomy.md 的 6 类定义挖掘节点之间的依赖边:
1. prerequisite (先修) - A 不学懂,B 学不下去
2. contrast (对比/易混) - A 与 B 表面相似,需对比学
3. application (理论→应用) - A 是 B 的方法/工具
4. generalization (总→分) - 跨子树的总分关系
5. specialization (分→总) - generalization 的反向
6. tool (主题→工具) - 配套工具

约束:
- DAG (无环), 反向边互斥, 双向 contrast 按 from<to 存
- 每条边 rationale 必须具体(禁套话)

=== 输出 schema ===
{
  "concept_dependencies": [
    {
      "from": "n2.1",
      "to": "n2.4",
      "type": "prerequisite",
      "weight": 1.0,
      "rationale": "虚拟语气的形式(was/were、had done)建立在时态体系上,不掌握时态难以理解",
      "evidence_source": "ai_inference",
      "evidence_locator": null
    }
  ]
}

=== 自检 checklist ===
[ ] 边数在预算内?
[ ] 所有 from/to 节点 id 在 framework_tree 中存在?
[ ] 6 类 type 互斥使用?
[ ] DAG 校验? (没有 prerequisite 环)
[ ] rationale 具体, 不含 "紧密相关" / "息息相关" 之类套话?
```

---

## 4. Step 6 · deep 全叶子讲解 Prompt

### 4.1 模板

```
=== 输入 ===
framework_tree:
{tree_json}
所有叶子节点 id 列表(共 {leaf_count} 个):
{leaf_ids}
user_level: {user_level}

=== 任务 ===
为**所有叶子节点**(leaf_count 个)各写一段 300-800 字的深度讲解:
- explanation: 与 guided 同结构,但更长更细
- drill: 1-3 个易混点 + 1-2 道例题(可选)
- cross_ref: 该叶子的 1-3 个最相关节点 id(供 Step 5 概念依赖挖掘加权)

=== 截断规则(防爆内容)===
- 总字数 ≤ 30,000 字
- 若 leaf_count > 50,告警 "建议分批 deep, 当前批次只覆盖前 N 个叶子",
  在 result.json.warnings[] 加 medium 级 DEEP_BATCH_TRUNCATED

=== 输出 schema ===
{
  "node_explanations": [
    {
      "node_id": "n2.4.1",
      "title": "if 条件句三类",
      "explanation": "[定义]...\n[展开]...\n[易错点]...",
      "drill": {
        "confusables": ["与 wish 句型的区别", "与 it's time 句型的区别"],
        "examples": [
          "If I were you, I would not go.  (与现在事实相反)",
          "If he had studied harder, he would have passed.  (与过去事实相反)"
        ]
      },
      "cross_ref": ["n2.1.1", "n2.4.2", "n2.4.3"],
      "word_count": 450
    }
  ]
}

=== 自检 checklist ===
[ ] 覆盖了全部 {leaf_count} 个叶子?
[ ] 每个 explanation 300-800 字?
[ ] 总字数 ≤ 30,000?
[ ] 所有 cross_ref 中的 node_id 在 framework_tree 中存在?
[ ] drill 中的例子简短且具体, 无填充内容?
```

---

## 5. recommended_questions 生成提示词(Step 3 末尾、Step 4/6 后)

### 5.1 模板

```
=== 任务 ===
基于当前 framework_tree(及深度档位)生成恰好 3 条用户最可能下一个问的问题。
3 条覆盖三种"升档诱因":
1. **学习路径类** —— 触发 guided 升档
   "我目标是 X,基础 Y,该重点投入哪几个分支?"
2. **依赖关系类** —— 触发 concept_dependency_strategy 启用
   "节点 A / B / C,先学哪个最划算?"
3. **跨课程对比类** —— 引向 v1.1 路线图
   "能给我课程 X vs Y 的对比框架吗?"

=== 输出 schema ===
[
  {
    "id": "q1",
    "q": "...",
    "why": "触发 ... 字段 / 模式",
    "expected_depth_after_followup": ["skim", "guided" | "deep"]
  }
]

=== 自检 ===
[ ] 恰好 3 条? 三类各 1 条?
[ ] 每条 why 明确指向用户该填哪个 input 字段?
[ ] q 短而具体, 不抽象 ("如何更好地学习" 算 BAD)?
```

---

## 6. user_level 适配语气速查表

| user_level | 例:讲解"虚拟语气" |
|---|---|
| `beginner` | "虚拟语气就是『假设』的特殊用法。例如『如果我是你』英文不说 If I am you,要说 If I were you——这种『改时态来表示假设』的就叫虚拟。重点记三套搭配..." |
| `intermediate` | "虚拟语气(Subjunctive Mood)用于表达与事实相反、未发生或愿望的情形。三类条件句:与现在(were/did + would do)、与过去(had done + would have done)、与未来(should do/were to do + would do)。常考: suggest/demand/insist 后..." |
| `advanced` | "虚拟语气是一种 mood marker(与 indicative/imperative 并列),其形式在英语中已大幅 retreat,主要保留在三类条件句、wish/would rather/it's high time、动词后宾语从句(suggest/demand/insist 等 mandative subjunctive)。注意:美式英语中 mandative 常省略 should,英式英语保留..." |

---

## 7. 何时调用何模板(决策树)

```
用户输入到达 →
  ↓
[scripts/validate_input.py] 出 build_plan.json,告知 mode + depth_used
  ↓
LLM 接 build_plan.json:
  ├─ "skim" 单档 → 套用 §1 (skim) + §5 (recommended_questions)
  ├─ "skim + guided" → §1 + §2 (guided 5-10 节点) + §5
  ├─ "skim + guided + deep" → §1 + §2 + §4 (全叶子 deep) + §5
  └─ 若 strategy != off → 追加 §3 (依赖挖掘)
  ↓
[scripts/assemble_result.py] 装配 → result.json
  ↓
[scripts/verify_provenance.py] 审计 → provenance-audit.json
  ↓
[scripts/render_outputs.py] 渲染 4 格式
```

---

## 8. 与 fixture 的对照(few-shot 锚点)

| Step | 模板 | 已落地 fixture 例 |
|---|---|---|
| Step 3 skim | §1 | `demos/.../topic-only-cet/result.json` 的 framework_tree |
| Step 3 questions | §5 | 同上的 recommended_questions(q1/q2/q3 三类齐全)|
| Step 4 guided | §2 | (规划)`topic-with-focus-cet/node-explanations/` |
| Step 5 依赖 | §3 | (规划)`hybrid-deep-with-deps/concept-dependencies.md` |
| Step 6 deep | §4 | (规划)`personal-notes-ml/node-explanations/` |

---

## 9. Prompt 工程的反模式(避坑)

| 反模式 | 为何不好 | 替代 |
|---|---|---|
| "请尽可能详细地写..." | 容易超字数,挤爆 ngram audit | 给具体范围 200-500 字 |
| "请确保结构清晰" | 抽象,LLM 自己也不知道何为清晰 | 列具体 schema + checklist |
| 把所有 Step 合并成 1 个超长 Prompt | LLM 单次输出 ~4K tokens 时割裂 | 分 Step 调用 + 中间产物存盘 |
| 把 framework-rubric.md 全文塞进 Prompt | 浪费 token,LLM 也读不细 | 只挑 §2.X 关键约束嵌入,完整规则放 references 让 LLM 自查 |
| 让 LLM 自己决定深度档位 | 决策不一致,scripts 校验难 | scripts/validate_input.py 决定 + LLM 服从 |
