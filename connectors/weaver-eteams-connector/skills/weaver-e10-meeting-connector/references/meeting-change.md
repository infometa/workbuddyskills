# 会议变更（改期 / 改地点 / 改参会人）— prepare/apply 确认链

## 何时使用

修改已有会议的时间、会议室/地点、参会人、类型、召集人/联系人等主表字段。

> **术语与分流**：业务上叫「变更」。CLI 会按会议当前状态**自动选择服务端操作类型**，调用方无需也不应自行指定：
> - **草稿**会议（`mtStatus="草稿"`）→ `operateType=UPDATE`（更新）
> - **正常**会议（`mtStatus="未开始"/"进行中"` 等）→ `operateType=CHANGE`（变更）
>
> 依据源码 `MeetingBaseServiceUtils.getShowButtons`：草稿给按钮 `do_edit`，正常且未结束给按钮 `do_change`。

## 输入要点

- 必填 `id`，再给出**至少一个**要修改的字段（否则报 `no_changes`）。
- 可改字段：`name` / `beginDatetime` / `endDatetime` / `address` / `customizeAddress` / `mtType` / `hrmMembers` / `orgMembers` / `otherMembers` / `crmMembers` / `totalMember` / `caller` / `contacter`。
- 时间格式 `yyyy-MM-dd HH:mm`；长 id 用字符串；人员/部门/客户字段用逗号分隔 id 串。
- **只提交显式给出的字段**：`preview.changedFields` 列出本次将提交的字段；未列出的主表字段是否保持原值由服务端决定（源码只确认提醒/议题/服务会按 id 回填）。若担心覆盖，请把需要保持不变的主表字段一并显式传入。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json meeting run meeting.change.prepare --input-json '{\"id\":\"1305624900858404950\",\"beginDatetime\":\"2026-09-18 15:00\",\"endDatetime\":\"2026-09-18 16:00\"}'
# 用户确认后（continuation 与字段都保持一致）：
weaver-work-cli --profile eteams --json meeting run meeting.change.apply --input-json '{\"confirm\":true,\"continuation\":\"<prepare返回>\",\"id\":\"1305624900858404950\",\"beginDatetime\":\"2026-09-18 15:00\",\"endDatetime\":\"2026-09-18 16:00\"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json meeting run meeting.change.prepare --input-json '{"id":"1305624900858404950","beginDatetime":"2026-09-18 15:00","endDatetime":"2026-09-18 16:00"}'
weaver-work-cli --profile eteams --json meeting run meeting.change.apply --input-json '{"confirm":true,"continuation":"<prepare返回>","id":"1305624900858404950","beginDatetime":"2026-09-18 15:00","endDatetime":"2026-09-18 16:00"}'
```

## 输出处理

- `prepare` 返回 `AWAITING_CONFIRMATION` + `preview`：
  - `currentStatus`（会议当前状态原文）、`operateType`（`UPDATE`/`CHANGE`）与 `operateTypeReason`（分流原因）；
  - `changedFields`（本次将提交的字段）与 `body`（完整提交体）；
  - `continuation`（10 分钟有效）。
- 向用户摘要「会议名 + 当前状态 + 走的是更新还是变更 + 改了哪些字段」后再确认。
- `apply` 返回 `COMPLETE` + `operateType`；随后 `meeting.list` 回查新时间/地点。

## 权限与提示（重要）

- **权限判定完全由服务端负责**（`MeetingPermissionEvent` 按会议状态 + 会议基础设置 + 召集人/监控权限判定按钮）。CLI **不做**权限预判。
- 无权限时服务端返回本地化原文提示，CLI 原样透传，**必须完整转达用户**，例如：
  - `您没有变更权限！`（正常会议不允许变更）
  - `您没有取消权限！` / `您没有删除权限！` / `您没有提前结束权限！`
  - `您没有读取权限！`
- 不要把这类提示改写成"操作失败"之类模糊说法，也不要建议用户绕过 CLI 自行拼接口。

## 注意

- 变更、取消、删除都是**写操作**：`apply` 的字段必须与 `prepare` 完全一致（不一致报 `target_changed`）。
- 会议状态在 prepare 与 apply 之间发生变化（如正常→草稿或已结束），CLI 会报 `target_changed` 并要求重新 prepare。
- 改期不会自动做冲突检测——需要时应先跑 `meeting.conflict.room` / `meeting.conflict.member` 核对目标时间段。
- 示例中的 id 为 `PLACEHOLDER_VALUE`。

## 失败处理

- `meeting_not_found`：列表中定位不到该会议（id 错误或当前账号不可见）。
- `no_changes`：没有提供任何可改字段。
- `confirmation.required` / `target_changed` / `continuation_expired`：补 `confirm: true`，或重新 prepare 并再次确认。
- 写请求发出后网络中断 → `partial/write_uncertain`：**禁止自动重试**，先 `meeting.list` 回查是否已生效。
