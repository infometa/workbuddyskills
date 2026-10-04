# 邮件查询类 operation

全部风险等级：`read`。只读，不修改数据。

## mail.list — 邮件列表

```text
weaver-work-cli --profile eteams --json mail run mail.list --input-json '{"folder":"0","keyword":"","unread":true,"star":false,"todo":false,"hasFile":false,"startDate":"","endDate":"","page":1,"size":10}'
```

字段（均为可选）：

| 字段 | 说明 |
|---|---|
| `folder` | 文件夹：0 收件箱 / -1 已发送 / -2 草稿箱 / -3 垃圾箱 / -4 已删除 / -10 全部。默认按命令约定 |
| `keyword` | 主题关键字 |
| `from` | 发件人 |
| `to` | 收件人 |
| `unread` | true 仅未读 |
| `star` | true 仅星标 |
| `todo` | true 仅待办 |
| `hasFile` | true 仅带附件 |
| `startDate` / `endDate` | 时间范围 YYYY-MM-DD |
| `page` / `size` | 分页，默认小页 |

## mail.contact.list — 往来邮件

某联系人与我之间的往来邮件（对方发来 + 我发给对方）。字段：`name`（姓名/工号）、`page`、`size`。

## mail.view.info — 邮件详情

含正文与附件列表。字段：`id`（邮件 id）。若正文为空会自动回退取正文接口。

## mail.view.content — 邮件正文

字段：`id`。仅返回正文（clobContent）。

## mail.unread.count — 未读统计

五箱统计：收件箱 / 已删除 / 垃圾箱 / 待办 / 星标。无输入字段。

## mail.config.get — 邮件配置

返回发送开关、附件限制等配置。无输入字段。

## 收件人解析（Agent 辅助，发送前用）

| operation | 字段 | 说明 |
|---|---|---|
| `mail.person.search` | `keyword` | 内部人员/部门搜索（返回 id 供发送解析） |
| `mail.dep.search` | `keyword` | 部门树定位（返回部门 id 与成员展开入口） |
| `mail.address.search` | `keyword` | 外部邮箱搜索 |

注意：发送时也可直接在 `mail.send.prepare` 传 `--to`/`--to-dep`/`--to-id`/`--external` 让 CLI 解析；同名人员会要求确认唯一性。

## mail.contacts.list / group.list / group.detail

| operation | 字段 | 说明 |
|---|---|---|
| `mail.contacts.list` | `keyword`,`page`,`size` | 联系人列表/搜索 |
| `mail.contacts.group.list` | 无 | 联系人分组列表 |
| `mail.contacts.group.detail` | `id` | 分组详情（含统计） |

## mail.template.list / sign.list / blacklist.list / attachment.center / clearlog.list

| operation | 字段 | 说明 |
|---|---|---|
| `mail.template.list` | 无 | 模板列表 |
| `mail.sign.list` | 无 | 签名列表 |
| `mail.blacklist.list` | 无 | 黑名单列表 |
| `mail.attachment.center` | `keyword`,`page`,`size` | 附件中心列表/搜索 |
| `mail.clearlog.list` | `page`,`size` | 邮件清理日志列表 |

## mail.sign.qrcode — 二维码名片

风险等级：`read`。字段：`id`（签名 id，二选一）、`userName`、`jobtitle`、`email`、`signLocation`、`mobile`、`telephone`、`fax`、`selected`。给定 `id` 时从签名表单解析姓名等；否则按传入字段生成。
