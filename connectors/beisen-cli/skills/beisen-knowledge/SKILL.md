---
name: beisen-knowledge
version: 3.2.1
description: "北森企业知识库搜索。本 Skill 用于搜索和查询企业知识库中的制度、政策、流程文档等。当用户询问知识库、制度、政策、流程、规定、手册等企业知识相关问题时触发。仅支持只读搜索，不涉及文档编辑或发布。员工和管理者均可使用。"
author: beisen
display_name: "北森企业知识库"
display_name_en: "Beisen Knowledge Base"
description_zh:  "北森企业知识库搜索。本 Skill 用于搜索和查询企业知识库中的制度、政策、流程文档等。当用户询问知识库、制度、政策、流程、规定、手册等企业知识相关问题时触发。仅支持只读搜索，不涉及文档编辑或发布。员工和管理者均可使用。"
description_en: "Beisen enterprise knowledge-base search. This Skill searches and queries policies, rules, and process documents in the enterprise knowledge base. Trigger when the user asks knowledge-related questions about the knowledge base, rules, policies, processes, regulations, or handbooks. Read-only search only; document editing or publishing is not involved. Available to both employees and managers."
category: productivity
requires-skills:
  - beisen-shared
---

# 企业知识

**CRITICAL — 开始前 MUST 读取 [references/beisen-shared.md](references/beisen-shared.md)**

## 路由优先级

本 Skill 处理：企业知识库中的制度政策查询（只读搜索）

不归本 Skill 处理：
- 办事入口 / 业务操作 → [../beisen-service-portal/SKILL.md](../beisen-service-portal/SKILL.md)
- 组织架构信息 → [../beisen-organization/SKILL.md](../beisen-organization/SKILL.md)
- 员工业务数据查询（考勤、绩效等） → 对应业务域 Skill

## 工具的读取与加载

- **工具发现**：在北森连接器当前已注册的工具清单中，按名称与描述匹配"知识库搜索/企业知识检索"类工具。
- **参数构造**：检索词应为**结合历史上下文和用户输入改写后的一组独立问题**（必填），完全按该工具 inputSchema 的结构传入。
- **结果解读**：返回为命中知识列表，通常含文档标题、内容摘要、文档分类、文档链接（如有）、更新时间等；实际字段与成功/失败判断以工具 outputSchema 与返回说明为准。

## 执行原则

- 结果较多时优先返回相关度最高的前几条，提示用户可继续查看
- 员工和管理者均可使用（安全等级 L0-L1），搜索结果正常展示
- 文档链接必须来自工具返回，严禁编造
- 如果用户查询的是具体业务数据（如"我有多少年假"），应路由到对应数据查询 Skill，而非知识库搜索
- 如果查询内容中返回了文件的链接，直接返回文件的链接即可，不用尝试打开链接获取原文件

## Playbook 案例

### 案例 1：查询年假政策

用户问："公司的年假政策是什么？"

执行步骤：
1. 以改写后的独立问题（如"年假政策是什么"）调用知识库搜索工具
2. 展示匹配的制度文档标题和摘要
3. 如返回结果较多，提示"还有更多相关文档，是否继续查看？"

### 案例 2：查询入职流程

用户问："新员工入职流程是什么？"

执行步骤：
1. 以"新员工入职流程"检索知识库
2. 展示匹配的流程文档
3. 如文档中有办事入口指引，引导用户使用 [beisen-service-portal](../beisen-service-portal/SKILL.md)

### 案例 3：路由判断

用户问："我有多少年假？"

此为业务数据查询（非知识库搜索），应路由到 [beisen-attendance-leave](../beisen-attendance-leave/SKILL.md) 而非本 Skill。

## 不在本 Skill 范围

- 唤起办事入口 → [../beisen-service-portal/SKILL.md](../beisen-service-portal/SKILL.md)
- 具体业务数据的查询 → 各对应业务域 Skill
- 文档编辑或发布 → 走后台管理
