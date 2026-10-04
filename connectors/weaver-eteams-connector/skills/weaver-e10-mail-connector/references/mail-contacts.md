# 联系人 / 分组（prepare → apply 确认链，删除单步）

风险等级：`write`。保存类走 prepare→apply 确认链；删除单步执行。

## 联系人保存（prepare → apply）

| operation | 字段 |
|---|---|
| `mail.contacts.save.prepare` | `id`（编辑时填）、`mailUserName`、`mailAddress`、`mailUserTel`、`mailUserCompany`、`mailUserDesc`、`groupId`、`confirm`、`continuation` |
| `mail.contacts.save.apply` | 同上（apply 必带 `continuation` + `confirm:true`） |

prepare 调用 `getMailContactsForm` 取全量表单并输出摘要（不保存）；apply 执行保存。新增不传 `id`，编辑传 `id`。

## 联系人删除

`mail.contacts.delete` 字段：`id`。单步执行，删除前确认。

## 分组保存（prepare → apply）

| operation | 字段 |
|---|---|
| `mail.contacts.group.save.prepare` | `id`（编辑时填）、`groupName`、`confirm`、`continuation` |
| `mail.contacts.group.save.apply` | 同上（apply 必带 `continuation` + `confirm:true`） |

## 分组删除

`mail.contacts.group.delete` 字段：`id`。单步执行，删除前确认。

## 要点

- 保存类必须 prepare 先取全量表单，避免覆盖用户已有字段；apply 前 CLI 重新校验 continuation 与上下文。
- 删除为单步即时写，执行前确认 id 与目标。
- 写请求已发出后遇到不确定结果，停止重试，按共享 `high-risk-write.md` 处理。
