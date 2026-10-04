# 人员解析

## 何时使用

发消息前确定接收人 uid/cid、把消息/群成员里的 uid 翻译成姓名、查某人的 uid 和部门。覆盖：

| operation | 用途 |
| --- | --- |
| `im.person.resolve` | 按姓名/工号/手机/邮箱**模糊**查询在职员工 → uid/cid/部门 |
| `im.person.resolveByIds` | 按 uid 批量解析 → 姓名/部门/岗位/cid（一次最多 100，超出自动分批） |

## 输入要点

- `person.resolve` 的 `name` 是模糊关键字，**多人命中必须列出候选让用户选**，不得自动取第一条。
- `person.resolveByIds` 入参字段是 **`ids`**（uid 列表，不要写成 `uids`）；uid 是 uint64，必须按字符串传；一次最多 100，超出自会分批（CLI 保证）。
- 消歧展示、未匹配处理、上下文传递契约见 [`field-resolution.md`](field-resolution.md)。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.person.resolve --input-json '{"name":"初四十九"}'
weaver-work-cli --profile eteams --json im run im.person.resolveByIds --input-json '{"ids":["100234","100235"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.person.resolve --input-json '{"name":"初四十九"}'
weaver-work-cli --profile eteams --json im run im.person.resolveByIds --input-json '{"ids":["100234","100235"]}'
```

## 注意

- **人名解析一律走 hrm**（`/api/hrm/common/getEmployeeByIds`），禁止使用 IM 群成员接口返回的 `name` 字段展示姓名，也不得本地拼表。
- 返回的 uid/cid 直接用于发消息/拉单聊（作为 `fromUid`/`toUid` 等）。
- 模糊命中多人时按 `person.resolve` 返回列表向用户确认；重名场景以用户指定的工号/部门为准确认。
- **未匹配（`total=0`）直接告知用户姓名可能有误并停止**，禁止翻历史会话/相似名模糊搜索去猜人。

## 失败处理

- 无命中：`data.employees` 为空，告知用户换关键字（可尝试工号/手机号）。
- 只读操作，安全；认证失败参照共享规则。
