# 示例：AI 工具调研笔记

> 这是一个示例输出，展示 material-organizer v2.0 处理 6 个 AI 工具相关链接后的完整结果。
> 包含：需求确认交互 → 批次处理 → 结构化文档 → 关键词索引 → 文件保存。

---

## 示例交互流程

**用户输入**：
```
帮我整理这些 AI 工具链接：
1. https://sspai.com/post/xxxxx（Notion AI 评测）
2. https://medium.com/xxxxx（Claude vs ChatGPT 对比）
3. https://github.blog/xxxxx（Copilot 年度报告）
4. https://juejin.cn/post/xxxxx（Cursor 深度体验）
5. https://openai.com/blog/xxxxx（GPT-4o 发布）
6. https://example.com/paywalled（付费墙文章）
```

**Skill 回复（Step 0 需求确认）**：
```
📋 已收到 6 项素材，开始整理前请确认：

1. 分类方式：希望按什么维度分类？
   - 🏷️ 自动聚类（默认，AI 根据内容自动分组）
   - 📅 按时间线
   - 🔧 按技术栈 / 主题
   - 📌 按重要程度
   - 其他（请说明）

2. 输出详细程度：
   - 📄 详细（含核心观点 + 摘录 + 标签，默认）
   - 📝 简洁（仅标题 + 核心观点）
   - 📋 仅摘要（每条一句话）

3. 是否保存为文件？（默认：是，保存到当前目录）

如无特殊要求，直接回复「开始」即可按默认设置处理。
```

**用户回复**：`开始`

---

> ✅ 第 1/1 批处理完成（已处理 6 项，剩余 0 项）→ 生成研究笔记...

---

# 📚 研究笔记：AI 效率工具调研

> 🗓️ 生成时间：2025-05-07 14:30　　📦 素材总数：6 项　　✅ 成功处理：5 项

---

## 📊 提炼总览

| 项目 | 数值 |
|:-----|-----:|
| 原始素材 | 6 项 |
| 成功处理 | 5 项 |
| 去重合并 | 1 项 |
| 最终条目 | 4 项 |
| 主题分类 | 2 个 |
| 生成时间 | 2025-05-07 14:30 |

**📑 分类目录**：

| # | 分类 | 条目数 |
|---|------|:------:|
| 1 | [🛠️ AI 写作与内容生成工具](#AI写作与内容生成工具) | 2 |
| 2 | [🔬 AI 编程辅助工具](#AI编程辅助工具) | 2 |

---

## ✅ 可操作项汇总（Action Items）

> 汇总所有条目中标记为 TODO / Question / Idea 的内容，优先展示。

- [ ] `✅ TODO` [来自条目#1] 建议评估 Notion AI 月费 $10 是否符合团队使用频率
- [ ] `❓Question` [来自条目#2] Claude 与 ChatGPT 的事实准确性差异是否有最新测评数据？
- [ ] `✅ TODO` [来自条目#3] 关注 Copilot Workspace 全流程任务规划功能，安排试用
- [ ] `💡 Idea` [来自条目#4] Cursor 的多文件上下文能力可引入当前项目重构流程

---

## 🛠️ AI 写作与内容生成工具（2条）

> 📌 主题简介：专注于文本生成、内容创作和写作辅助的 AI 工具

### 1. Notion AI 功能深度评测

| 字段 | 内容 |
|------|------|
| **来源** | [少数派 - Notion AI 评测](https://sspai.com/post/xxxxx) |
| **作者/机构** | 少数派编辑部 |
| **发布日期** | 2024-11 |

**核心观点**：
1. Notion AI 深度集成工作区，无需切换工具即可完成写作辅助 `🟢 High`
2. 支持多语言摘要、改写、续写，中文效果优于同类产品 `🟡 Medium`
3. 月费 $10 对重度用户性价比高，轻度用户建议按需购买 `🟡 Medium`

**关键摘录**：
> "Notion AI 最大的优势不在于生成质量，而在于它与工作流的无缝融合——你不需要离开当前文档就能完成 80% 的写作辅助需求。"

**标签**：`#AI写作` `#效率工具` `#Notion` `#内容生成`

---

### 2. Claude vs ChatGPT 长文写作对比

| 字段 | 内容 |
|------|------|
| **来源** | [Medium - Long-form Writing Comparison](https://medium.com/xxxxx) |
| **作者/机构** | John Smith |
| **发布日期** | 2025-01 |

**核心观点**：
1. Claude 在长文连贯性和逻辑结构上优于 GPT-4 `🟡 Medium`
2. ChatGPT 在创意写作和风格多样性上更灵活 `🟡 Medium`
3. 两者在事实准确性上均需人工核查 `🟢 High`

**关键摘录**：
> "For documents exceeding 5,000 words, Claude maintains narrative coherence significantly better, rarely losing track of earlier context or contradicting itself."

**标签**：`#Claude` `#ChatGPT` `#长文写作` `#AI对比`

---

## 🔬 AI 编程辅助工具（2条）

> 📌 主题简介：面向开发者的 AI 编程助手和代码生成工具

### 3. GitHub Copilot 2025 年度报告

| 字段 | 内容 |
|------|------|
| **来源** | [GitHub Blog](https://github.blog/xxxxx) |
| **作者/机构** | GitHub 官方 |
| **发布日期** | 2025-02 |

**核心观点**：
1. Copilot 用户平均代码编写速度提升 55% `🟢 High`
2. 新增 Copilot Workspace 支持全流程任务规划 `🟢 High`
3. 企业版新增安全漏洞自动检测功能 `🟢 High`

**关键摘录**：
> "Developers using Copilot report completing tasks 55% faster on average, with the biggest gains in boilerplate code and test generation."

**标签**：`#GitHub-Copilot` `#AI编程` `#开发效率` `#研究报告`

---

### 4. Cursor vs VS Code + Copilot 实测对比

| 字段 | 内容 |
|------|------|
| **来源** | [掘金 - Cursor 深度体验](https://juejin.cn/post/xxxxx) |
| **作者/机构** | 前端小王 |
| **发布日期** | 2025-03 |

**核心观点**：
1. Cursor 的多文件上下文理解能力显著优于 Copilot `🟡 Medium`
2. Cursor 对大型项目的重构支持更完善 `🟡 Medium`
3. VS Code + Copilot 生态更成熟，插件兼容性更好 `🟢 High`

- **合并说明**：`🔀 已与条目 #5 合并（相似度 78%）`

**关键摘录**：
> "Cursor 在处理跨文件重构时，能够理解整个代码库的依赖关系，而不仅仅是当前打开的文件。"

**标签**：`#Cursor` `#VS-Code` `#AI编程` `#工具对比`

---

## 📌 跨主题关键洞察

> 以下观点在多个来源中反复出现，值得重点关注：

1. **AI 工具的价值在于融入工作流**：多个来源强调，AI 工具的核心竞争力不是生成质量，而是与现有工作流的集成深度（来源：条目#1、#3、#4）
2. **事实准确性仍需人工核查**：所有 AI 生成内容均存在幻觉风险，不可完全依赖（来源：条目#2、#3）
3. **专业场景 > 通用场景**：针对特定场景优化的工具（如 Copilot 针对编程）效果优于通用 AI（来源：条目#1、#3、#4）

---

## ⚠️ 处理异常记录

| 条目 | 原始输入 | 异常类型 | 处理方式 |
|:----:|---------|:-------:|:-------:|
| #6 | https://example.com/paywalled | 需要登录/付费墙 | 已跳过，仅保留 URL |

---

## 🔑 关键词索引

> 按出现频次降序排列，便于快速定位相关条目。

| 关键词 | 出现条目 | 频次 |
|--------|:-------:|:----:|
| `#AI编程` | #3, #4 | 2 |
| `#效率工具` | #1, #3 | 2 |
| `#AI对比` | #2, #4 | 2 |
| `#AI写作` | #1 | 1 |
| `#Notion` | #1 | 1 |
| `#内容生成` | #1 | 1 |
| `#Claude` | #2 | 1 |
| `#ChatGPT` | #2 | 1 |
| `#长文写作` | #2 | 1 |
| `#GitHub-Copilot` | #3 | 1 |
| `#开发效率` | #3 | 1 |
| `#研究报告` | #3 | 1 |
| `#Cursor` | #4 | 1 |
| `#VS-Code` | #4 | 1 |
| `#工具对比` | #4 | 1 |

---

<div align="center">

*📎 由 material-organizer v2.0 自动生成 · 如有修改建议请告知*

</div>

---

```
📎 研究笔记已生成！
   📄 已保存至：research-notes-AI效率工具调研-20250507.md
   🔑 关键词索引：keyword-index-AI效率工具调研-20250507.md

您可以继续：
  [A] 重新保存到指定路径
  [B] 按新维度重新分类（请告诉我分类方式）
  [C] 深入精读某条目（请告诉我条目编号）
  [D] 补充更多素材（继续追加）
  [E] 生成知识框架图（调用 knowledge-framework-builder）
  [F] 导出为其他格式（PDF / HTML / Excel）
