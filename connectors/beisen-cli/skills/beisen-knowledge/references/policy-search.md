# 企业知识 - 知识搜索命令参考

## searchKnowledge — 查询企业知识

```bash
beisen-cli knowledge retrieve searchKnowledge --data '{"queries":["<问题1>","<问题2>"]}'
```

### 参数（通过 --data 传入 JSON）

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|:----:|
| `queries` | array | 结合历史上下文和用户输入改写后的几个独立问题 | 是 |

### 返回结构

```json
{
  "code": "200",
  "message": "提示消息",
  "payload": {
    "hitKnowledgeList": [ { "..." : "命中知识" } ]
  }
}
```

- `code` 为状态码；`payload.hitKnowledgeList` 为命中知识的相关信息数组
- 每条记录的字段由知识库配置决定，常见关注字段见下表

### 关注字段（从 hitKnowledgeList 条目中提取）

| 字段 | 说明 |
|------|------|
| `title` | 文档标题 |
| `summary` | 内容摘要（匹配问题的片段） |
| `category` | 文档分类（如"考勤制度""薪酬政策""入职流程"等） |
| `url` | 文档链接（如有） |
| `update_time` | 文档最后更新时间 |

> 实际字段名以 CLI 返回为准；上述为常见关注字段。

### 注意事项

- 搜索企业知识库中的制度、政策、流程文档
- 安全等级 L0-L1，员工和管理者均可使用
- 若用户查询的是具体业务数据（如"我有多少年假"），应路由到对应数据查询 Skill，而非知识库搜索
