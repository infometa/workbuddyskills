# 会议与会议室查询

## 何时使用

查今天的会议 / 会议列表、探测环境模式、建会前置判断、会议室与占用、会议类型。

## 输入要点

- 时间格式统一 `yyyy-MM-dd HH:mm`；日期 `yyyy-MM-dd`。
- 长 id（会议室/会议/人员）超 2^53 必须字符串。
- `meeting.list` 的接口 body 过滤实测不生效：CLI 采用空 body 拉全量 + 客户端 `filterDate` 过滤，**不要尝试给 body 塞过滤字段**。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json meeting run meeting.env.detect --input-json '{}'
weaver-work-cli --profile eteams --json meeting run meeting.list --input-json '{"filterDate":"2026-09-11"}'
weaver-work-cli --profile eteams --json meeting today
weaver-work-cli --profile eteams --json meeting run meeting.room.list --input-json '{"beginDate":"2026-09-11 09:00","endDate":"2026-09-11 10:00","onlyAvailable":true}'
weaver-work-cli --profile eteams --json meeting run meeting.type.list --input-json '{"name":"项目","includeCount":true}'
weaver-work-cli --profile eteams --json meeting run meeting.room.usage --input-json '{"roomid":"1297870848451641350","bywhat":4,"currentdate":"2026-09-11"}'
weaver-work-cli --profile eteams --json meeting run meeting.calendar.base --input-json '{}'
weaver-work-cli --profile eteams --json meeting run meeting.detail.field --input-json '{"id":"1305624900858404950"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json meeting run meeting.env.detect --input-json '{}'
weaver-work-cli --profile eteams --json meeting run meeting.list --input-json '{"filterDate":"2026-09-11"}'
weaver-work-cli --profile eteams --json meeting today
weaver-work-cli --profile eteams --json meeting run meeting.room.list --input-json '{"beginDate":"2026-09-11 09:00","endDate":"2026-09-11 10:00","onlyAvailable":true}'
weaver-work-cli --profile eteams --json meeting run meeting.type.list --input-json '{"name":"项目","includeCount":true}'
weaver-work-cli --profile eteams --json meeting run meeting.room.usage --input-json '{"roomid":"1297870848451641350","bywhat":4,"currentdate":"2026-09-11"}'
weaver-work-cli --profile eteams --json meeting run meeting.calendar.base --input-json '{}'
weaver-work-cli --profile eteams --json meeting run meeting.detail.field --input-json '{"id":"1305624900858404950"}'
```

## 输出处理

- `meeting.list` 返回 `meetings[]`（含 `id`/`name`/`beginDatetime`/`endDatetime`/`address`/`mtStatus`），按开始时间升序输出 Markdown 表格；CLI 自动翻页拉全量后做客户端 `filterDate` 过滤。
- `meeting.room.list` 返回 `rooms[]`（`disabled` 已归一化为布尔）与 `availableRooms[]`；带时间范围时 `disabled=true` 即该时段已被占用。
- `meeting.calendar.base` 返回 `createBaseData`：`onlyFlowCreate`（0=可手动建会 1=只能流程建会）、`workFlowBaseIds`、`repeatWorkFlowBaseIds`、`existWorkFlow`。
- `meeting.env.detect` 返回 `mode: "eb" | "standard"` + `fromCache`：
  - **默认按 baseUrl 读缓存**（第一次探测成功后固化到 CLI 状态目录），命中时不发网络请求；
  - `refresh: true` 强制重新冒烟并更新缓存（用户说"重新探测/刷新模式"时用）；
  - 标准版回退时附带 `ebSmokeError`（EB 冒烟失败原因，用于诊断）；
  - 两者冒烟均失败时报 `env_unavailable`（环境未配置完整，禁止强行执行）。

## 注意

- 示例中的 id 均为 `PLACEHOLDER_VALUE`，实际调用替换为真实查询结果。
- 标准 `weaver-work-cli --profile eteams --json` 输出 envelope：成功 `ok=true`；失败看 `error.type/subtype/message`。

## 失败处理

- `env_unavailable`：提示环境会议应用未安装或接口未配置完整，停止。
- `permission_denied`（HTTP 403 语义）：提示联系管理员开通接口权限。
- `session_expired`：登录态失效，引导用户断开并重新连接本连接器。
