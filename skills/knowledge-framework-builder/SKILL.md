---
name: knowledge-framework-builder
version: 1.0.0
description: |
  课程知识框架梳理工具 — 把课程主题或教材资料提炼成结构化知识脉络图，支持三档深度输出与多格式导出。
  UseWhen:
  1. 用户需要把课程/教材/笔记整理成知识框架或思维导图
  2. 用户需要了解某门课的知识脉络、核心知识点、概念依赖关系
  3. 用户提到"知识框架"、"知识脉络"、"章节脉络"、"课程梳理"、"知识梳理"、"核心知识点"、"重点提炼"
  4. 用户提到"前置课程"、"概念依赖"、"教材目录梳理"、"教材结构图"、"笔记重组"
  5. 用户提到"学科地图"、"学习地图"、"复习框架"、"考点框架"、"Markmap 生成"、"OPML 导出"
  6. 用户提到 syllabus to mind map、study framework、textbook outline、course mind map、knowledge framework
display_name: 知识框架梳理
display_name_en: Knowledge Framework Builder
description_zh: 课程知识框架梳理工具，支持输入课程主题或教材资料（Markdown / DOCX / PDF / 图片截图 / URL），自动生成三档深度知识脉络图（框架 / 重点讲解 / 全节点讲解），含核心知识点提炼、概念依赖关系图、防幻觉溯源标注，多格式输出（Markdown / Markmap / Mermaid / OPML / PDF）。
description_en: Course knowledge framework builder that ingests a course topic or teaching materials (Markdown, DOCX, PDF, images, URLs) and outputs a three-depth knowledge map (skim / guided / deep), with key-point extraction, concept dependency graph, hallucination-prevention provenance, and multi-format export (Markdown, Markmap, Mermaid, OPML, PDF).
author: TPD
---

# 知识框架梳理（Knowledge Framework Builder）

> 面向**大学生 / 教师 / 自学者**的三档深度 + 核心知识点提炼 + 概念依赖 + 节点级防幻觉溯源的知识脉络图生成 Skill。
> 支持多种输入格式（Markdown / DOCX / PDF / 图片截图 / URL），多种输出格式（Markdown / Markmap / Mermaid / OPML / PDF）。

---

## 何时触发

- 用户说："帮我把『大学英语 / 高数 / 机器学习 / 408』梳理成知识框架 / 知识脉络"
- 用户说："这本书的目录给你，帮我画成思维导图 / 重组成知识框架"
- 用户贴了一份 Markdown / DOCX 笔记 + 提了"帮我整理成框架"
- 用户问："这门课先学什么再学什么？/ XX 概念依赖什么？/ 哪些是核心知识点？"
- 用户说："我看书越看越乱 / 知识点太散记不住 / 想要一张清晰的知识框架"

**不触发**：
- 视频 / 音频内容（不支持，请先转为文字）
- 整本书 RAG 问答（超出范围，建议分章节提交）
- 通用 brainstorm 思维导图（请补充具体课程主题）
- 单次超过 1 门课程（请分课提交）

> 💡 **支持多种输入格式**：Markdown / DOCX / 纯文本 / PDF（文本层）/ 图片截图（OCR 识别）/ URL 网页。图像层 PDF / 扫描件质量较低时会提示用户确认，但不强制拒绝。

---

## 核心原则

1. **三档深度自动切换**：用户**不选档**，Skill 按输入内容自动判断：
   - 仅提供课程主题 → **skim**（3-5 层知识框架 + AI 推荐 3 个延伸问题）
   - 含重点话题 / 学习目标 / 初学者标记 → **skim + guided**（追加 5-10 重点节点 200-500 字讲解 + **核心知识点提炼与总结**）
   - 含 `deep_explain: true` → **skim + guided + deep**（追加叶子节点讲解；单批 ≤ 15，分批生成，超出时询问继续）
   - `preferences.depth_hint` 可强制覆盖（force_skim / force_guided / force_deep）

2. **节点级防幻觉溯源**：含数字 / 专名 / 公式 / 名词的节点，
   - 用户材料模式：必须能 ngram 匹配到原文 → 标注来源文件 + 章节 + 原文片段
   - 纯主题模式：所有节点标注为 AI 推断，**顶部强制 ⚠️ banner**："本框架完全为 AI 推断，建议核对教材"
   - 推断字段（如"难点提示""易混点""考点分布"）**必须**单独标注

3. **概念依赖关系必须"克制"挖掘**：
   - 限制条数：≤ 总节点数 × 0.3（防止过度连线）
   - 每条必带置信度（高 / 中 / 低），保守策略下只输出高置信度
   - 类型必须是 6 类之一：前置条件 / 归纳关系 / 细化关系 / 对比关系 / 应用关系 / 工具关系
   - **严禁**生成 "A 和 B 有关系" 这种空话；每条必须给出**具体**依赖原因

4. **重点节点选择必须可解释**：
   - 频次策略：用户材料中出现次数 ≥ 阈值（仅材料模式有效）
   - 中心度策略：依赖图中入度 / 出度排名前 N（默认，最稳健）
   - 混合策略：两种各取一半

5. **节点讲解 200-500 字**：按用户水平调整：
   - 初学者 → 多用比喻 + 例子 + 类比生活
   - 中级（默认）→ 平衡术语和解释
   - 高级 → 直接用术语 + 强调难点和易混点

6. **多格式输出**：
   - 默认输出 Markdown + Markmap（最通用，浏览器双击即开）
   - Mermaid 用于 GitHub / Notion / IDE 原生渲染
   - OPML 用于一键导入 XMind / 幕布精修
   - PDF 用于打印 / 分享 / 手机查看（生成完成后询问）
   - CDN 不可达时 markmap.html 自动降级为静态 SVG

7. **中文原生**：中国用户为主，反馈全中文；保留 Markmap / Mermaid / OPML 等专有名词英文。

8. **多格式输入支持**：支持 Markdown / DOCX / 纯文本 / PDF（文本层优先）/ 图片截图（OCR 识别）/ URL 网页（抓取正文）。图像层 PDF / 扫描件识别质量较低时，**提示用户确认**是否继续；识别结果标注为 `ocr_extracted`，提醒用户核对。

9. **单次处理上限 1 门课**：超过 1 门课 / 节点数 > 100 → 拒绝并建议分课处理或按一级分支拆分。

10. **关键决策处人类确认（防自主失控）**：以下 4 个高风险节点**必须**暂停等用户回应，绝不静默继续：
    - **CP-A · 模式确认**（Step 0 后）：当仅有课程主题（无材料）且属于常见教材类（大学英语 / 高数 / 408 / 考研政治等），提示 "这是高幻觉风险模式，建议补充教材目录；继续 / 补充材料 / 取消" 三选一；用户选「继续」才进入 Step 1。
    - **CP-B · 触顶警示**（Step 3 后 / Step 5 后）：若节点数 ≥ 90 或依赖条数 ≥ 总节点数 × 0.25，暂停并展示当前规模 + "继续生成 / 拆分课程 / 收紧策略" 三选一。
    - **CP-C · 溯源高失配**（Step 7 后）：当 >30% 节点无法匹配到材料原文，暂停并展示失配节点列表 + "材料不全请补充 / 接受当前 AI 推断标注 / 重新选材料范围" 三选一；绝不静默把多数节点标为 AI 推断。
    - **CP-D · HTML 报告询问**（Step 0 完成后立即询问，不等到最后）：主动询问用户是否需要 HTML 报告；默认选「是」（HTML 体验更好）；用户选「否」则仅输出 framework.md，不再追问。
    - 检查点统一原则：① 提供 ≤ 3 个枚举选项；② 用户沉默 / 任何拒绝 → 走默认安全路径（CP-A 默认取消，CP-B 默认拆分，CP-C 默认补充材料，**CP-D 默认生成 HTML**）；③ 不重复追问。

---

## framework.md 内容规范

framework.md 是主资产，**内容必须与 HTML 报告对等**，不得是只有标题树的空壳。

必须包含以下节（按顺序）：

```markdown
# 📚 [课程名] 知识框架

> ⚠️ 本框架由 AI 推断生成（纯主题模式时加此 banner）
> 🗓️ 生成时间：YYYY-MM-DD　　📐 深度档位：框架档 / 框架+重点讲解档 / 全节点档

---

## 📊 框架总览

[知识框架树，用 Markdown 标题层级或缩进列表表示]
[重点节点用 ⭐ 标注]

---

## 🔍 重点知识讲解（guided / deep 档时必有）

### ① [重点节点名]
📍 位置：[一级分支] > [二级分支]

[200-500 字讲解，含比喻/例子/类比]

📌 **核心要点**：[该节点的核心知识点提炼，1-3 条]

---

### ② [重点节点名]
（同上格式）

---

## 🔗 知识点关联图

| 关系类型 | 知识点 A | 知识点 B | 关联说明 |
|---------|---------|---------|--------|
| 前置条件 | ... | ... | ... |

---

## 💡 延伸学习建议

1. **[问题/方向]**：[对用户的价值说明]
2. **[问题/方向]**：[对用户的价值说明]
3. **[问题/方向]**：[对用户的价值说明]
```

**禁止**：只输出标题树而不含讲解、关联图、延伸建议节；这些节在对应档位下是**必出**内容，不是可选项。

---

## 关键反模式（NEVER 列表）

- **NEVER 输出 "A 和 B 有关系" 这种空话依赖** — 每条依赖必须给出**具体**机制，置信度字段缺一不可。
  ```
  Bad:   { from: "前馈网络", to: "反向传播", reason: "两者有关系" }
  Good:  { from: "前馈网络", to: "反向传播", type: "前置条件", confidence: "高",
           reason: "反向传播是前馈网络训练算法的具体实现——前向计算输出 → 损失 → 反向链式法则求梯度" }
  ```

- **NEVER 在 force_skim 时偷讲解** — 用户说"只给框架别讲解"时即使有重点话题也不升档；讲解列表必须为空。
  ```
  Bad:   框架下每个一级模块附 1-2 行"小科普"
  Good:  纯标题树，node_explanations: []
  ```

- **NEVER 在溯源失配率 > 30% 时静默标 AI 推断** — 必须触发 CP-C 暂停并展示失配节点 Top 10，让用户三选一。
  ```
  Bad:   60% 节点匹配失败 → 全部默默改成 AI 推断后输出
  Good:  暂停 + 列出 10 条失配节点 + 请求用户决策
  ```

- **NEVER 对低质量 OCR 结果静默继续** — 乱码率 > 20% 时必须暂停并展示识别样本，让用户确认是否继续。
  ```
  Bad:   扫描件 OCR 错误率 40% → 静默生成一份乱码节点的知识框架
  Good:  展示识别样本 + "识别质量较低，建议提供文本层文件。是否仍然继续？"
  ```

- **NEVER 在节点 ≥ 90 触顶时静默截断或继续生成** — 必须触发 CP-B 让用户三选一。
  ```
  Bad:   生成 114 节点然后只保留前 100 输出
  Good:  CP-B 触顶警示 → 用户选 [1] 拆课 → 重做单课
  ```

- **NEVER 在 deep 模式下让单批超 15 叶子** — 上下文溢出会让后半批讲解质量明显下降，必须分批。
  ```
  Bad:   在一次回复里硬塞 30 个叶子讲解，后 15 个明显敷衍
  Good:  优先选高价值前 15 → 标注截断 → 询问用户"继续下一批？"
  ```

---

## 工作流（9 步）

收到框架梳理请求后，**严格按以下步骤**执行。详细规则见 `references/` 目录：

| 文档 | 用于步骤 |
|---|---|
| `references/framework-rubric.md` | Step 3/4/6 内容质量自评 |
| `references/provenance-spec.md` | Step 7 节点级溯源数据模型 + ngram 阈值 |
| `references/concept-dependency-taxonomy.md` | Step 5 6 类依赖关系定义 |
| `references/prompt-templates.md` | Step 3/4/5/6 Prompt 模板 + 自检 checklist |
| `references/examples-index.md` | few-shot 锚点指引 |
| `references/outline-parsing-heuristics.md` | Step 2 材料解析启发式规则 |
| `references/input-schema.md` / `output-schema.md` | 完整 JSON Schema |

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 0  输入解析与模式判定                                        │
│   课程主题 必有 OR 材料文件 必有（≥ 1 个）                        │
│   都没提供 → 报错并给 3 个示例                                    │
│   无材料文件 → 纯主题模式（高幻觉风险，加 banner）                │
│   有材料文件 → 材料优先模式                                       │
│   两者都有 → 混合模式（材料优先 + 主题作为补全提示）              │
├─────────────────────────────────────────────────────────────────┤
│ ⏸ CP-A 模式确认（仅纯主题模式 + 常见教材类时）                    │
│   提示："检测到纯主题模式（高幻觉风险）。继续 / 补充材料 / 取消？"│
│   沉默 / 拒绝 → 默认取消；选「继续」才进 Step 1                   │
├─────────────────────────────────────────────────────────────────┤
│ ⏸ CP-D 输出格式询问（Step 0 完成后立即询问，不等到最后）           │
│   "📋 好的！开始梳理知识框架。需要同时生成 HTML 报告吗？           │
│    HTML 报告含折叠节点 + 重点讲解 + 知识点关联图，浏览器直接查看。 │
│    □ 是，生成 HTML 报告                                            │
│    □ 否，仅生成 Markdown 文档"                                     │
│   未选 / 沉默 → 默认「是」（主动生成 HTML，体验更好）              │
│   用户选「否」→ 仅输出 framework.md，不追问                        │
├─────────────────────────────────────────────────────────────────┤
│ Step 1  深度档位确认│   depth_hint != auto → 按 hint 强制                              │
│   depth_hint == auto → 按输入内容自动判断                         │
│   永远含 skim；guided / deep 按规则叠加                            │
├─────────────────────────────────────────────────────────────────┤
│ Step 2  材料解析（仅当有材料文件时）                               │
│   run: python scripts/parse_outline.py {input}                   │
│   markdown → ATX `#` + Setext `===`（零外部依赖）                │
│   docx → 标准库 zipfile + xml.etree + Heading 1-5 样式（降级）   │
│   txt / pasted_text → 7 套启发式回退（章节/数字/§/中文序号/字母）│
│   pdf（文本层）→ 提取文本后解析                                   │
│   image / 截图 → 调用 OCR 工具识别后解析（低质量时提示确认）      │
│   webpage / URL → 抓取正文后解析                                  │
│   video / audio → 拒绝，提示用户先转为文字                        │
│   见 references/outline-parsing-heuristics.md                    │
├─────────────────────────────────────────────────────────────────┤
│ Step 3  框架生成（skim，必出）                                     │
│   读 references/framework-rubric.md                               │
│   读 references/prompt-templates.md §1（skim 框架模板）           │
│   纯主题模式：LLM 生成 3-5 层框架                                 │
│   材料优先模式：以材料大纲为准 + AI 补全缺失子节点                │
│   混合模式：以材料为准 + 主题作为"是否漏了什么"的反向核对         │
│   生成延伸学习建议（默认 3 条）                                    │
│   每条延伸建议附说明（回答这个问题对用户的价值）                   │
├─────────────────────────────────────────────────────────────────┤
│ ⏸ CP-B 触顶警示（节点数 ≥ 90 时）                                  │
│   "框架已含 N 节点，逼近 100 上限。继续生成 / 拆分课程 /           │
│   收紧到 3 层？" 沉默 → 默认拆分课程并提示重提交                   │
├─────────────────────────────────────────────────────────────────┤
│ Step 4  重点节点选择与讲解（若深度含 guided）                      │
│   按重要度策略挑 5-10 个重点节点（默认中心度策略）                 │
│   用户指定重点话题时 → 优先在这些主题分支选                        │
│   每个重点节点写 200-500 字讲解，按用户水平调整语气                │
│   必含【核心要点】：该节点的核心知识点提炼与总结（必须具体）       │
│   严禁产出无具体内容的空泛节点                                     │
│   ⚠️ 报告输出规范（HTML 面向用户，不得暴露内部术语）：            │
│     · 讲解节点标题用 ①②③ 序号，不暴露内部字段名                 │
│     · 路径用 📍 前缀 + 自然语言描述                               │
│     · 章节标题用「重点知识讲解」                                   │
│     · 每条讲解末尾必须有绿色「📌 核心要点：」总结块               │
├─────────────────────────────────────────────────────────────────┤
│ Step 5  概念依赖关系挖掘（若策略 != off）                          │
│   读 references/concept-dependency-taxonomy.md                    │
│   读 references/prompt-templates.md §3（依赖挖掘模板）            │
│   LLM 跨分支挖掘 6 类依赖；限制 ≤ 总节点数 × 0.3                  │
│   保守策略：只输出高置信度；激进策略：输出中置信度及以上           │
│   每条必带具体依赖原因 + 来源标注 + 置信度                         │
│   材料模式：优先挖掘材料里相邻段落 / 章节的关系                    │
│   ⚠️ 报告输出规范（HTML 面向用户）：                              │
│     · 章节标题用「知识点关联图」                                   │
│     · 依赖类型在表格/图中用中文标签：                             │
│       前置条件 / 对比关系 / 细化关系 / 应用关系 / 归纳关系 / 工具关系│
│     · 表头用「关系类型/知识点A/知识点B/关联说明」                  │
├─────────────────────────────────────────────────────────────────┤
│ Step 6  deep 全节点讲解（若深度含 deep）                           │
│   目标：所有叶子节点都生成 200-500 字讲解                          │
│   分批约束：单批 ≤ 15 叶子；超过时按重要度优先选高价值节点         │
│     其余批次标注截断 + 提示用户"继续下一批？"                      │
│   可选结构化字段：                                                 │
│     · cross_ref：与其他节点的关联指针（易混点的客观化表达）        │
│     · drill：结构化练习题（含题目 + 参考答案）                     │
├─────────────────────────────────────────────────────────────────┤
│ Step 7  溯源审计（防幻觉闭环，内部执行，不输出给用户）             │
│   run: python scripts/verify_provenance.py                        │
│   规则见 references/provenance-spec.md                            │
│   材料优先 / 混合模式：每节点对材料做 ngram 校验                   │
│     · 匹配成功 → 标注来源文件 + 章节 + 原文片段                    │
│     · 匹配失败 → 标注 AI 推断 + 标记 ⚠️                           │
│   纯主题模式：所有节点标注为 AI 推断                               │
│     · 顶部加 banner："本框架完全为 AI 推断，建议核对教材"          │
│   推断字段（"难点提示""易混点"等）必须单独标注                    │
│   输出 provenance-audit.json（仅内部存档，不在 HTML 报告中展示）   │
│   ⚠️ HTML 报告中不得出现"溯源审计""ngram""失配率"等内部术语      │
│      纯主题模式的 AI 推断 banner 用用户语言：                      │
│      「⚠️ 本框架由 AI 根据课程主题推断生成，建议核对教材后使用」   │
├─────────────────────────────────────────────────────────────────┤
│ ⏸ CP-C 溯源高失配（失配率 > 30% 时）                               │
│   暂停并展示失配节点 Top 10 + "材料不全请补充 / 接受当前 AI 推断  │
│   标注 / 重新选材料范围？" 沉默 → 默认请用户补充材料               │
│   绝不静默把多数节点标 AI 推断后继续                               │
├─────────────────────────────────────────────────────────────────┤
│ Step 8  多格式渲染（按输出格式偏好）                               │
│   run: python scripts/render_outputs.py                           │
│   markdown   → framework.md（主资产）                             │
│   markmap    → framework.markmap.html（CDN + 离线降级）            │
│   mermaid    → framework.mermaid.md（mindmap + flowchart）         │
│   opml       → framework.opml（导入 XMind / 幕布）                │
│   默认输出 markdown + markmap                                      │
│   注：PDF 输出在 Step 9 CP-D 询问时提供选项                        │
├─────────────────────────────────────────────────────────────────┤
│ Step 9  HTML 报告渲染（若 CP-D 用户选「是」）                       │
│   模板：assets/report-template.html（占位符替换式渲染）             │
│   产物：./reports/framework-reports/<ts>-<slug>.html                │
│   若用户同时需要 PDF，在 HTML 生成后追加询问一次                    │
│   ⚠️ HTML 报告结构规范（面向用户，不含内部术语）：                 │
│     · Hero pills 用用户语言：「基于大纲原文生成」「框架+重点讲解」 │
│     · 目录 4 节：知识框架总览/重点知识讲解/知识点关联图/延伸学习   │
│     · 延伸学习（原延伸建议）放最后一节                              │
│     · 框架树中只用 ⭐ 重点 徽章，不用内部字段名标签                │
│     · 不含「溯源审计」「输入与配置摘要」两节                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三档深度速查

| 用户输入 | 自动档位 | 输出内容 |
|---|---|---|
| 仅课程主题 | 框架档 | 知识框架树 + 延伸学习建议 |
| 课程主题 + 重点话题 | 框架档 + 重点讲解档 | + 5-10 个重点节点讲解（含**核心知识点提炼**）+ 知识点关联图 |
| 课程主题 + 材料文件 | 框架档 + 重点讲解档* | + 全节点溯源标注 + 核心重点提炼 |
| 任一配置 + deep_explain: true | 框架档 + 重点讲解档 + 全节点档 | 叶子节点讲解（分批 ≤15；可选关联指针 + 练习题）|

*：有材料文件时默认升档到重点讲解档，因为材料提供了足够上下文

**强制覆盖**：
- `force_skim` → 即使提供了重点话题也只出框架
- `force_guided` → 即使没有重点话题，AI 自动挑 5 个高价值节点深入
- `force_deep` → 全叶子节点都讲解（分批 ≤15，超出询问继续）

---

## 输入规范

完整 schema 见 `references/input-schema.md`。核心字段：

| 字段 | 必填 | 说明 |
|---|:---:|---|
| `course_topic` | ⚠️ | 课程主题字符串（如 `"大学英语"`），与 `material_files` 至少一个 |
| `material_files` | ⚠️ | 数组；来源类型支持 markdown / docx / txt / pasted_text / pdf / image / url，与 `course_topic` 至少一个 |
| `context.focus_topics` | 可选 | 数组（如 `["语法", "听力技巧"]`），触发重点讲解档自动升档 |
| `context.learning_goal` | 可选 | 自然语言（如 `"通过 CET-4"`），影响讲解侧重 |
| `context.user_level` | 可选 | `beginner` / `intermediate`（默认）/ `advanced`，影响讲解语气 |
| `preferences.depth_hint` | 可选 | `auto`（默认）/ `force_skim` / `force_guided` / `force_deep` |
| `preferences.concept_dependency_strategy` | 可选 | `off` / `conservative`（默认）/ `aggressive` |
| `preferences.importance_strategy` | 可选 | `frequency` / `centrality`（默认）/ `mixed` |
| `preferences.output_formats` | 可选 | 数组，默认 `["markdown", "markmap"]`，可选 `mermaid` / `opml` / `pdf` |
| `preferences.language` | 可选 | `zh`（默认）/ `en` / `bilingual` |

---

## 输出结构

完整 schema 见 `references/output-schema.md`。

```
./framework-output/<timestamp>-<slug>/
├── result.json                      # 结构化总结果
├── framework.md                     # Markdown 大纲（主资产）
├── framework.markmap.html           # Markmap 单文件交互式思维导图
├── framework.mermaid.md             # Mermaid mindmap + flowchart 代码
├── framework.opml                   # OPML 2.0（导入 XMind / 幕布）
├── node-explanations/               # 重点讲解档 / 全节点档下的节点讲解
├── concept-dependencies.md          # 知识点关联图（表格 + Mermaid flowchart）
├── provenance-audit.json            # 节点级溯源审计（内部存档）
└── (按需) report.html               # 一体化 HTML 报告（Step 9 主动询问后生成）
```

`result.json` 顶层字段：`meta` / `inputs_summary` / `framework_tree` / `node_explanations` / `concept_dependencies` / `recommended_questions` / `provenance_summary` / `warnings` / `next_step_hint`。
