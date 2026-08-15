---
name: beisen-knowledge
version: 1.0.9
description: "北森企业知识库搜索。本 Skill 用于搜索和查询企业知识库中的制度、政策、流程文档等。当用户询问知识库、制度、政策、流程、规定、手册等企业知识相关问题时触发。仅支持只读搜索，不涉及文档编辑或发布。员工和管理者均可使用。"
category: 人力资源/企业知识
author: beisen
agent_created: false
allowed-tools: Bash, Read
---

# 企业知识

**CRITICAL — 开始前 MUST 读取 [../beisen-shared/SKILL.md](../beisen-shared/SKILL.md)**

## 路由优先级

本 Skill 处理：企业知识库中的制度政策查询（只读搜索）

不归本 Skill 处理：
- 办事入口 / 业务操作 → [../beisen-service-portal/SKILL.md](../beisen-service-portal/SKILL.md)
- 组织架构信息 → [../beisen-organization/SKILL.md](../beisen-organization/SKILL.md)
- 员工业务数据查询（考勤、绩效等） → 对应业务域 Skill

## 命令速查

| 场景 | CLI 命令 | 说明 |
|------|---------|------|
| 查企业知识制度 | `beisen-cli knowledge retrieve searchKnowledge --data '{"queries":["<问题>"]}'` | 按改写后的独立问题搜索知识库 |

## 命令示例

```bash
# 搜索知识库（queries 为结合上下文改写后的独立问题数组，必填）
beisen-cli knowledge retrieve searchKnowledge --data '{"queries":["年假政策是什么"]}'
```

## 执行原则

- `queries` 为结合历史上下文和用户输入改写后的几个独立问题，必填
- 结果较多时优先返回相关度最高的前几条，提示用户可继续查看
- 员工和管理者均可使用（安全等级 L0-L1）
- 搜索结果属于 L0-L1 公开/内部数据，正常展示
- 如果用户查询的是具体业务数据（如"我有多少年假"），应路由到对应数据查询 Skill，而非知识库搜索

## 返回字段说明

返回结构为 `{code, message, payload: {hitKnowledgeList: [...]}}`，`hitKnowledgeList` 为命中知识数组。每条记录常见关注字段：

| 字段 | 说明 |
|------|------|
| `title` | 文档标题 |
| `summary` | 内容摘要 |
| `category` | 文档分类 |
| `url` | 文档链接（如有） |
| `update_time` | 更新时间 |

> 实际字段名以 CLI 返回为准；上述为常见关注字段。

## Playbook 案例

### 案例 1：查询年假政策

用户问："公司的年假政策是什么？"

执行步骤：
1. 前置检查
2. 执行 `beisen-cli knowledge retrieve searchKnowledge --data '{"queries":["年假政策是什么"]}'`
3. 展示匹配的制度文档标题和摘要
4. 如返回结果较多，提示"还有更多相关文档，是否继续查看？"

### 案例 2：查询入职流程

用户问："新员工入职流程是什么？"

执行步骤：
1. 前置检查
2. 执行 `beisen-cli knowledge retrieve searchKnowledge --data '{"queries":["新员工入职流程"]}'`
3. 展示匹配的流程文档
4. 如文档中有办事入口指引，引导用户使用 [beisen-service-portal](../beisen-service-portal/SKILL.md)

### 案例 3：路由判断

用户问："我有多少年假？"

此为业务数据查询（非知识库搜索），应路由到 [beisen-attendance-leave](../beisen-attendance-leave/SKILL.md) 而非本 Skill。

## 详细参考

- [references/policy-search.md](references/policy-search.md)：政策搜索命令详细参数与返回格式

## 不在本 Skill 范围

- 唤起办事入口 → [../beisen-service-portal/SKILL.md](../beisen-service-portal/SKILL.md)
- 具体业务数据的查询 → 各对应业务域 Skill
- 文档编辑或发布 → 走后台管理
