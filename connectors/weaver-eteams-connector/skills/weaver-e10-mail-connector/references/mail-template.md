# 邮件模板（prepare → apply 确认链，更新/删除/默认）

风险等级：`write`。保存类走 prepare→apply；update 为 GET 全量 + 保存单步；delete/default 单步。

## 模板保存（prepare → apply）

| operation | 字段 |
|---|---|
| `mail.template.save.prepare` | `id`（编辑时填）、`templateType`、`subject`、`mailSubject`、`clobContent`（正文，base64）、`templateDesc`、`defaultUse`、`contentId`、`confirm`、`continuation` |
| `mail.template.save.apply` | 同上（apply 必带 `continuation` + `confirm:true`） |

`clobContent` 为正文内容，CLI 内部做 base64 编码；`contentId` 默认 `"null"`，编辑时取原值。

## 模板编辑（GET 全量 + 保存）

`mail.template.update` 字段：`id`、`subject`、`clobContent`、`templateDesc`、`defaultUse`、`templateType`。先 `getMailTemplateInfo` 取全量再全量回写。

## 模板删除 / 设为默认

| operation | 字段 |
|---|---|
| `mail.template.delete` | `id` |
| `mail.template.default` | `id` |

均为单步执行，执行前确认 id 与目标。

## 要点

- 保存类必须 prepare 先查全量；apply 前重新校验 continuation 与上下文。
- 编辑/删除/默认为即时写，确认目标 id。
- 写请求已发出后遇到不确定结果，停止重试，按共享 `high-risk-write.md` 处理。
