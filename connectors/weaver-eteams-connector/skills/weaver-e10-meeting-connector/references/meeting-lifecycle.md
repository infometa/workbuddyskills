# 取消 / 删除会议（prepare/apply 确认链）

## 何时使用

取消一场会议（不开了）、彻底删除会议记录。

> 提前结束会议（`overMeeting`）**不在支持范围**：服务端该接口为空实现（service 调用被注释、直接返回成功），调用只会得到"假成功"但不生效。请引导用户在系统页面操作。

## 输入要点

- 两个动作都只需会议 `id`（长 id 用字符串）。
- prepare 阶段 CLI 会**回查会议存在性**（`getMeetingDetailField`）；回查失败直接报 `meeting_not_operable`，不做任何写入。
- **权限判定由服务端负责**（按会议状态 + 会议基础设置 + 召集人/监控权限）：无权限时服务端返回原文提示，CLI 原样透传，**必须完整转达用户**——`您没有取消权限！` / `您没有删除权限！` / `您没有提前结束权限！` / `您没有读取权限！`。不要改写成"操作失败"这类模糊说法。
- `continuation` 有效期 10 分钟，过期需重新 prepare。
- 传参方式按源码签名区分（已核对 `com.weaver.meeting.controller`）：
  - `cancel` → `operateMeetingByType`（`@RequestBody`，body 传 JSON）；
  - `delete` → `deleteMeetingDetail(Long id)`（**表单绑定，必须 query 传参**）。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json meeting run meeting.cancel.prepare --input-json '{\"id\":\"1305624900858404950\"}'
# 用户确认后（continuation 原样传入）：
weaver-work-cli --profile eteams --json meeting run meeting.cancel.apply --input-json '{\"confirm\":true,\"continuation\":\"<prepare返回>\",\"id\":\"1305624900858404950\"}'
weaver-work-cli --profile eteams --json meeting run meeting.delete.prepare --input-json '{\"id\":\"1305624900858404950\"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json meeting run meeting.cancel.prepare --input-json '{"id":"1305624900858404950"}'
weaver-work-cli --profile eteams --json meeting run meeting.cancel.apply --input-json '{"confirm":true,"continuation":"<prepare返回>","id":"1305624900858404950"}'
weaver-work-cli --profile eteams --json meeting run meeting.delete.prepare --input-json '{"id":"1305624900858404950"}'
```

## 输出处理

- `prepare` 返回 `AWAITING_CONFIRMATION` + `preview`（`action`/`id`/`body`/`note`）+ `continuation`。
- `apply` 返回 `COMPLETE` + `result`（接口原始返回）；随后用 `meeting.list` 回查确认。
- 两个动作的语义区别：
  - `cancel`：会议进入**取消状态**，占用/回执/签到随之失效；
  - `delete`：**彻底移除**会议记录（区别于取消），不可逆。

## 注意

- 两者都是**不可逆写操作**：apply 前必须向用户明确说明动作与后果并取得确认。
- 禁止跳过 prepare 直接 apply；apply 的 `id` 必须与 prepare 一致（不一致报 `target_changed`）。
- 示例中的 id 为 `PLACEHOLDER_VALUE`，实际使用请替换为真实查询结果。

## 失败处理

- `meeting_not_operable`：会议不存在或当前账号无权操作，停止并提示用户核对。
- `confirmation.required`：缺少 `confirm: true`，补上后重试。
- `continuation_expired` / `target_changed`：重新 prepare 并再次向用户确认。
- 写请求发出后网络中断 → `partial/write_uncertain`：**禁止自动重试**，先 `meeting.list` 回查会议状态（是否已取消/已删除），确未生效才重新 prepare。
