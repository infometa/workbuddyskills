# 会员域 — 会员导入写操作契约

> 概念知识：`references/domains/member-concepts.md`（会员导入导出任务口径），状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-import-export.md`；导入前确认无进行中任务、任务轮询与导出（URL 型）见 `member-import-export-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.member.import 导入会员 🔴 · member.member.import-blacklist 导入黑名单 🔴

---

## ✅ 导入会员 — ops.member.member.import

- 🔴 批量建会员——执行前向用户复述文件名与预期导入量
- **传输形态特例**：multipart 文件上传

### 入参（multipart 文件）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件 | ✅ | .xlsx（服务端仅校验扩展名，无显式大小校验——大小上限为部署层默认 multipart 限制，通常 10MB）；模板列：`手机号*`（必填，1[3-9] 开头 11 位）+ `昵称（选填）`。模板文件从管理后台下载（⛔ Agent 无模板下载能力），可让用户在后台取模板填好后提供文件路径 |

### 出参（原始返回）

**异步受理**（非同步完成）：立即返回 `taskId` + `status=0`（处理中），实际导入后台执行——用 `import-task.status` 轮询至 1（已完成）或 2（失败）。

### 业务规则（服务端）

- **同租户同时仅允许一个进行中的会员导入任务**：重复提交返回业务错误（先以 `import-task.latest` 确认无进行中任务）
- 行数上限 **50,000**：超限任务直接置为失败（errorMessage 提示拆分文件）
- 文件内手机号重复 → 该行失败；**已存在的手机号 → 该行失败**（已注销账号除外，允许重新导入）
- 失败行进入失败明细文件（`hasFailureDetail=true`，仅管理后台可下载——Agent 只能报告失败数量，无法取回明细内容）
- 导入成功的会员自动补 memberNo/uid 并初始化积分与成长值资产账户

### 调用示例

```json
{"capability":"ops.member.member.import","input":{"file":"uploads/批量导入模板.xlsx", "fileType":"excel"},"summary":"导入会员文件"}
```

---

## ✅ 导入黑名单 — ops.member.member.import-blacklist

- 🔴 用户资产类批量操作——黑名单会员无法交易，执行前复述文件名与预期数量
- **传输形态特例**：multipart 文件上传

### 入参（multipart 文件）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件 | ✅ | .xlsx（服务端仅校验扩展名，无显式大小校验——同上）；模板列：`会员编号` / `UID` / `手机号`（三列，任一可定位会员） |

### 出参（原始返回）

**同步执行**（数据量小，黑名单导入不走异步）：直接返回完整计数（`totalCount`/`successCount`/`failureCount`/`hasFailureDetail`），`status=1`（已完成）。

### 调用示例

```json
{"capability":"ops.member.member.import-blacklist","input":{"file":"uploads/批量导入模板.xlsx", "fileType":"excel"},"summary":"导入黑名单文件（需配合运行时文件上传通道）"}
```
