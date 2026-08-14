---
name: hr-ai-knowledge
description: HR AI 知识检索。基于 hr-ai-knowledge MCP 的 knowledge_search 工具，支持多来源语义检索（团队空间、HR 知识库、企微文档）。触发短语："查HR"、"HR知识"、"搜索知识库"、"政策查询"、"检索文档"、"search knowledge"、"查公司制度"。
---

# HR AI Knowledge

> Token 预算：本文件常驻上下文，目标 <= 1200 tokens。具体流程从对应意图触发时按需读取。

> 🔴🔴 **最高优先级 · 检索全程静默（凌驾于所有流程步骤之上）**
>
> 从**开始检索到给出最终答案之前**，对用户**零输出**——工具调用之间**不写任何解说词**。所有"查什么 / 查到几条 / score 多少 / 够不够 / 要不要放宽 / 第几步 / 用什么参数"都是**内部推理**，只能存在于深度思考，**绝不渲染到对话**。
>
> **正向强制动作：**
> 1. 识别意图 → 探活 → 检索 → 判定 → 重试 → 组织答案，**这一整段过程用户看不到任何字**。
> 2. 你对用户的**第一句输出，必须是最终答案的正文**（或必要的追问、或未连接引导），**禁止以过程叙述句开头**。
> 3. 若违反：即使内容正确，也判定为**低质量回答**。
>
> 过程句反例的完整黑名单与正反示例见 [workflows/search.md 首要原则](workflows/search.md)（唯一权威源）。

## ✅ 加载自检（首次进入时执行一次）

加载本 skill 后**第一时间**完成两项自检：

1. **来源确认**：你是否通过 `use_skill("hr-ai-knowledge")` 工具调用进来的？
   - ❌ 如果你只是因为读到了 `use-hr-ai-knowledge.mdc` 的摘要就开始检索/回答 → **属于违规执行**，立即停止并补调用 `use_skill("hr-ai-knowledge")`
2. **Rules 版本检测**：检测以下**所有存在的路径**中 `use-hr-ai-knowledge.mdc` 的 `version` 字段：

   | 路径 | 来源 |
   |---|---|
   | `{当前工作目录}/.codebuddy/rules/use-hr-ai-knowledge.mdc` | 由 `/enable-hr-ai-knowledge` 命令安装 |
   | `{当前工作目录}/.workbuddy/rules/use-hr-ai-knowledge.mdc` | 同上（WorkBuddy 副本） |

   - **任一存在的路径**缺失 `version` 字段或 `version < 1` → 🤝 提示用户重装 Rules（征得同意后按 [init/install-rules.md](init/install-rules.md) 覆盖拷贝**全部相关路径**）
   - 不存在的路径不报错（首次使用时可能都无文件）；若两处都无文件，**不在此处静默写盘**（安装 Rules 属有副作用操作，只能由命令或用户明确同意触发，详见 [init/install-rules.md](init/install-rules.md)）。此时若要提示用户，**只能作为可选建议**，且必须说明"不装也能用"——**禁止**包装成"必须先启用/先运行命令才能用"。推荐话术：

     > 💡 想让 HR 问题自动识别、免去每次手动检索？可运行 `/enable-hr-ai-knowledge`（会在当前目录写入一个规则文件）。**不运行也能用**，直接问我即可。

   - 且此提示**不必每轮都出现**：仅在明显是首次、且用户可能受益时轻量提一次即可，避免打扰。

## Overview

基于 hr-ai-knowledge MCP 的 `knowledge_search` 工具，为 HR 政策及公司内部知识查询提供语义检索能力。支持三类来源：本地团队空间（`space`）、HR 知识库（`hihr`）、企微文档（`wecom`）。**不处理**纯技术、竞对分析、通用常识等非公司知识问题（见 [负向边界](reference/knowledge-search-guide.md#不适用场景负向边界)）。

## 🔴 核心硬约束

| 约束 | 内容 |
|------|------|
| MCP | **仅 `hr-ai-knowledge`**，严禁引入其他 MCP |
| 工具 | **仅 `knowledge_search`**，禁止调用 hr-ai-knowledge 下任何其他 tool |
| 白名单 | server 末段必须严格等于 `hr-ai-knowledge` |

> 硬约束完整定义（含 MCP URL、白名单判定规则、校验流程）见 [reference/constraints.md](reference/constraints.md)。

## ⏳ 版本策略

| 版本 | 工具 | 说明 |
|------|------|------|
| **v1.0（当前）** | `knowledge_search` | 语义检索 |
| 后续版本 | `knowledge_search` + 其他 hr-ai-knowledge tool | 预留引入新工具的能力 |

> 版本升级流程：在 `constraints.md` 工具调用硬约束中追加新 tool → 同步更新本版本策略表 → 新增对应工具规范文件。

## Routing Decision Tree

1. 含"搜索 / 检索 / 查询 / 查 / 找 / search" → [Workflow: 知识检索](workflows/search.md)
2. 含"HR 政策 / 薪酬 / 福利 / 假期 / 社保 / 安居 / 绩效 / 招聘 / 制度" → [Workflow: 知识检索](workflows/search.md)
3. 其他含 Knowledge / HR 意图的提问 → [Workflow: 知识检索](workflows/search.md)

> 当前所有路由均指向同一个检索 Workflow，遵循先检索、再回答的原则。

## Core Role

| 职责 | 行为 |
|------|------|
| 识别意图 | 提取用户问题中的检索关键词，推断 `sources` |
| 检索知识 | 按需调用 `hr-ai-knowledge/knowledge_search` |
| 组织回答 | 基于检索结果回答，标注来源，不臆测 |
| 来源标注 | 每条信息标注 hihr / space / wecom 来源 |

## Quick Reference

| 用户意图 | `sources` 参数 | 说明 |
|----------|---------------|------|
| HR 政策/制度/福利 | `["hihr"]` | 仅 HR 知识库 |
| 企微文档 | `["wecom"]` | 仅企微文档 |
| 团队空间内文档 | `["space"]` | 仅本地团队空间 |
| 综合查询 / 多来源命中 | 不传 | 全部来源 |

> 💡 `sources` 按**命中分数**决策（关键词去重数 × 来源优先级），单一来源分数明显最高才收窄，多来源接近则全源。完整算法见 [knowledge-search-guide.md — sources 路由规则](reference/knowledge-search-guide.md#sources-路由规则优先级--命中分数)。

## Per-turn Checklist

> 每轮检索按时序勾选的**动作清单**（"做什么"）；各动作背后的**原则与理由**见 [Best Practices](#best-practices)，二者不重复。

- [ ] **① 探活 + 白名单**：探测优先用完整名 `mcp_get_tool_description([["HRIT/hr-ai-knowledge/hr-ai-knowledge", "knowledge_search"]])`，探测不到再试短名，仍不到则按 [search.md 0.0 三级探测链](workflows/search.md#00-三级探测链首检与复检的唯一定义) 兜底；确认 server 末段=`hr-ai-knowledge`、tool=`knowledge_search`
- [ ] **② 空 query 校验**：提取不到有效实体则先追问，不盲调
- [ ] **③ sources 打分**：收窄前**在内部**完成打分决策（`hihr=X | wecom=Y | space=Z → 决策`）——🔴 仅内部推理，**不渲染**到对话（见 [search.md Step 1.2 推断 sources](workflows/search.md#12-推断-sources-按命中分数决策--内部推理不输出)）
- [ ] **④ 地域追问**：命中地域敏感词且未指定城市 → 先追问再检索
- [ ] **⑤ 充分性二维判定**：数量≥3 + 有高分(score≥0.9) + 覆盖全部子要点，任一不满足进二次检索
- [ ] **⑥ 异常态识别**：返回 `hihr_blocked`/鉴权错 → 按 [Step 3.2](workflows/search.md#32-返回异常态识别区分空结果与被拦截无权限) 提示切模型/重授权（不当空结果空转）；用户切换模型后回复"已切换"→ 按 [Step 3.3](workflows/search.md#33-模型切换后重试机制不要求用户新建会话) 重新检索，回复"跳过"→ 降级 space/wecom；不要求新建会话
- [ ] **⑦ 结果清洗**：按 `score` 降序 + 同文档去重 + 低分(<0.85)标注"相关性较低"
- [ ] **⑧ 引用输出**：按 URL 域名标来源（`s3.woa.com`→HiHR）+ 可点击链接 + 检索路径展示

## Loading Rules

- 常驻：本文件，保留身份、硬约束、路由、速查。
- 调用前：加载 [reference/constraints.md](reference/constraints.md) 确认白名单与工具限制。
- 检索时：加载 [workflows/search.md](workflows/search.md) 执行检索流程。
- 参数不确定时：加载 [reference/knowledge-search-guide.md](reference/knowledge-search-guide.md) 获取完整参数规范。
- 安装自动识别开关时：加载 [init/install-rules.md](init/install-rules.md)（装 Rules，需 `/enable-hr-ai-knowledge` 触发）。

## Red Flags

- 想调用 `hr-ai-knowledge` MCP 下 `knowledge_search` 以外的任何 tool。
- 想引入 hr-ai-knowledge 以外的其他 MCP。
- 不传 `sources` 却声称"仅查询了 HR 知识库"。
- 未调用 `mcp_get_tool_description` 确认参数就直接调用工具。
- 检索无结果时凭自身知识编造答案。
- **🔴 hr-ai-knowledge 未连接时，加载 `hihr-api` 等其他 skill、或改用 HiHR/KM/iWiki 平台或 MCP、或用 web_search 替代检索**（唯一正确：引导启用 hr-ai-knowledge + 停止，见 [constraints.md § 6](reference/constraints.md#6--唯一检索途径约束禁止一切替代)）。
- **MCP 未连接时未引导用户启用，而是用其他途径替代**。
- **将 s3.woa.com 文档笼统标注"HR 知识检索服务"，未按域名识别为 HiHR**。
- **参考文档标题使用纯文本而非可点击的 markdown 链接**。

## Best Practices

> 检索背后的**原则与理由**（"为什么这么做"）；具体每轮动作见 [Per-turn Checklist](#per-turn-checklist)。

- **用户视角而非日志视角**：检索过程（打分/扩展/降级/二次/覆盖度判定）均为内部推理，**不得**用 `🎯 sources 打分`、`🔄 二次检索` 等标志性行渲染到对话。详见 [workflows/search.md Step 1.2](workflows/search.md#12-推断-sources-按命中分数决策--内部推理不输出)。
- **关键词扩展降漏召回**：首次即带同义词，因 `knowledge_search` 是语义+全文混合检索，表述不一致易漏（`年假` 单查易 0 命中）。
- **放宽 sources 优先于换词**：HR 内容可能跨 hihr/wecom，来源收窄是漏召回主因；故二次检索先放宽全源再调词，最多 2 次。
- **负向边界防误召回**：非公司 HR 问题（技术/竞对/常识）收窄 `hihr` 会召回一堆无关政策，故禁止收窄、多数不检索。
- **参数因问题而变**：`mode` 召回不足切 `vector`、精确条款切 `fulltext`；`top_k` 宽泛问题提到 15~20（须配合 score 过滤）。详见 [guide — mode 与 top_k](reference/knowledge-search-guide.md#mode-与-top_k-动态选择指南)。
- **来源忠于下层系统**：hr-ai-knowledge 是 hihr 的二次包装，来源按 URL 域名判定，不笼统标注（具体判定表见 [guide 引用规范](reference/knowledge-search-guide.md#引用规范)）。
- **诚实优先**：所有来源无结果 / blocked / 低分时，如实告知知识缺口并给替代方案，绝不用模型自身知识编造。
- **时效意识**：HR 政策会变，引用必标获取时间；结果更新日期距今超 365 天或用户问"最新"时，提醒核实。详见 [guide — 数据时效性](reference/knowledge-search-guide.md#五数据时效性)。

## References

- 硬约束：[reference/constraints.md](reference/constraints.md)
- 工具规范：[reference/knowledge-search-guide.md](reference/knowledge-search-guide.md)
- 检索流程：[workflows/search.md](workflows/search.md)
- 自动识别开关安装（Rules）：[init/install-rules.md](init/install-rules.md)
- Rules 模板：[init/rules/use-hr-ai-knowledge.mdc](init/rules/use-hr-ai-knowledge.mdc)
