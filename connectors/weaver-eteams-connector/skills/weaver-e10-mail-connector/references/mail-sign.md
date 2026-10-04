# 邮件签名（prepare → apply 确认链，更新/删除/默认/二维码）

风险等级：保存类 `write`；`mail.sign.qrcode` 为 `read`。

## 签名保存（prepare → apply）

| operation | 字段 |
|---|---|
| `mail.sign.save.prepare` | `id`（编辑时填）、`signName`、`clobContent`（签名内容，base64）、`signDesc`、`defaultUse`、`signType`（默认 "0"）、`electronSignEnable`、`confirm`、`continuation` |
| `mail.sign.save.apply` | 同上（apply 必带 `continuation` + `confirm:true`） |

`clobContent` 为签名内容，CLI 内部做 base64 编码。

## 签名编辑（GET 全量 + 保存）

`mail.sign.update` 字段：`id`、`signName`、`clobContent`、`signDesc`、`defaultUse`、`signType`、`electronSignEnable`。先 `getMailSignForm` 取全量再全量回写。

## 签名删除 / 设为默认

| operation | 字段 |
|---|---|
| `mail.sign.delete` | `id` |
| `mail.sign.default` | `id` |

## 二维码名片（read）

`mail.sign.qrcode` 字段：`id`（签名 id，二选一）、`userName`、`jobtitle`、`email`、`signLocation`、`mobile`、`telephone`、`fax`、`selected`。给定 `id` 时从签名表单解析姓名等；否则按传入字段生成。

## 要点

- 保存类必须 prepare 先查全量；apply 前重新校验 continuation 与上下文。
- 编辑/删除/默认为即时写，确认目标 id。
- 写请求已发出后遇到不确定结果，停止重试，按共享 `high-risk-write.md` 处理。
