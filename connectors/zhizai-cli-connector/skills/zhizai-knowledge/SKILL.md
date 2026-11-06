---
name: zhizai-knowledge
version: 1.0.0
description: 查询和管理智在记录笔记集。
---

# 智在记录笔记集

| 意图 | 命令 |
|---|---|
| 我创建的笔记集 | `zhizai knowledge list -o json` |
| 我收到的笔记集 | `zhizai knowledge list --received -o json` |
| 笔记集详情 | `zhizai knowledge get <id> -o json` |
| 集内笔记 | `zhizai knowledge notes <id> -o json` |
| 新建笔记集 | `zhizai knowledge create --name <名称>`（后端待开放） |

字段说明见 `skills/zhizai-open-platform/references/knowledge.md`。
