# 会员域 — 成长值任务查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-benefit.md`；任务保存（写操作）见 `growth-task-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.growth-task.list 成长值任务列表

---

## ✅ 成长值任务列表 — ops.member.growth-task.list

- 全量非分页（当前仅 1 条默认任务）

### 入参

无。

### 出参（原始返回）

`data` 为任务配置数组。**关键字段**：`taskId`（→ 保存时回传）、`taskType`（当前仅 `purchase`）、`taskName`（任务显示名称，服务端自动填充）、`enabled`、`taskConfig`（嵌套对象：`{taskType, perAmt, growthValue}`）。

### 调用示例

```json
{"capability":"ops.member.growth-task.list","input":{},"summary":"查询成长值任务配置"}
```
