# 会员子域 — 会员导入导出流程

> 对应契约：`apis/member/member-import-export-query.md`（导出与任务查询）、`apis/member/member-import-export-action.md`（导入写操作）；概念知识：`references/domains/member-concepts.md`（会员导入导出任务口径），状态与枚举：`references/domains/member-enums.md`；写操作共同纪律（风险档位/超时不重试）见入口 Skill 护栏段。

**场景**：批量建会员 / 批量拉黑 / 按条件导出会员名单。

### 操作步骤

1. **导出** 🟡（含 PII）：
   - `ops.member.member.export`（筛选条件与 search 同口径；不传条件 = 全量）
   - 响应 `mode=sync`（≤5000 行）→ 直接取 `downloadUrl` 转告用户（60 分钟时效）
   - 响应 `mode=async`（>5000 行）→ 取 `taskId` 轮询 `ops.member.member.export-task.status` 至 `completed` 再取 `downloadUrl`；`expired` 表示文件已过 7 天保留期需重新导出
   - ⚠️ 导出内容含会员批量 PII：只转告 URL，不在答复中复述文件内容
2. **导入会员** 🔴（批量建会员，异步）：
   - 用户在管理后台下载「会员导入模板.xlsx」（⛔ Agent 无模板下载能力），填好后提供文件
   - 导入前以 `ops.member.member.import-task.latest` 确认无进行中任务（**同租户同时仅允许一个**）
   - `ops.member.member.import`（multipart）→ 立即返回 taskId（status=0 处理中）
   - 轮询 `ops.member.member.import-task.status`：1=已完成（报告 success/failure 计数）；2=失败（报告 errorMessage）
   - 失败明细文件仅管理后台可下载（Agent 只能报告失败数量）
3. **导入黑名单** 🔴（同步，批量拉黑）：`ops.member.member.import-blacklist`（multipart，模板列：会员编号/UID/手机号）→ 直接返回完整计数

### 参数数据流

```
export 响应 taskId（async）→ export-task.status 路径参数
import 响应 taskId → import-task.status 路径参数
export 响应 downloadUrl / export-task.status 响应 downloadUrl → 转告用户（60 分钟时效）
```

### 异常处理

- 导入提交报"已有进行中任务"：先查 `import-task.latest` / `import-task.list`，向用户说明当前任务状态，等完成后再试
- 任务长时间 status=0：导入为后台异步执行（上限 5 万行），如实说明并稍后再查，**不得重复提交**
- 导出任务 `expired`：文件 7 天保留期已过，需按原条件重新导出
