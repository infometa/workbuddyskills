# 邮件 Skill 安全边界（已暂缓 / 禁用 operation）

本文件记录 `weaver-e10-mail-connector` 中**未纳入 CLI manifest** 的破坏性/缺口操作，以及高风险操作的安全约束。

## 已暂缓的 operation（withheldOperations）

| operation | 状态 | 原因 |
|---|---|---|
| `mail.delete.batch` | 暂缓 | 物理永久删除（`deleteMailResourceBatch`）不可逆、无法撤销，破坏性最强。常规 CLI 不提供；如确需执行，请在确认风险后以单独授权方式处理。 |
| `mail.resend` | 暂缓 | 重发邮件（`resendMail`）依赖「邮件发送日志 id」（`mailRemindLogId`），源技能未封装日志查询接口，无法获得该 id 时如实提示，不臆造。 |

Agent **不得**调用上述 operation，也不得用 `mail.delete.move`（逻辑删除）冒充物理永久删除。

## 高风险写操作约束

以下写操作会修改真实邮件数据，必须遵守共享规则 `../weaver-e10-shared-connector/references/high-risk-write.md`：

- 发送/回复/转发/存草稿：`mail.send.prepare` → 用户确认 → `mail.send.apply`（带 `continuation` + `confirm:true`）
- 联系人/分组保存：`mail.contacts.save.prepare` → 用户确认 → `mail.contacts.save.apply`
- 模板保存：`mail.template.save.prepare` → 用户确认 → `mail.template.save.apply`
- 签名保存：`mail.sign.save.prepare` → 用户确认 → `mail.sign.save.apply`
- 黑名单：`mail.blacklist.operate.prepare` → 用户确认 → `mail.blacklist.operate.apply`
- 单步写：标星、已读、全部已读、待办、移动、逻辑删除、文件夹新建/删除、撤回、联系人/分组/模板/签名删除与默认、附件上传/下载

通用约束：

1. 禁止输出或索取 Cookie、ETEAMSID、业务 Token、access token、app key、app secret。
2. 禁止读取、列出、打印、复制或解析用户主目录下的旧 `.e10-cli`、auth、config 或 Keychain 数据。
3. 禁止绕过 `weaver-work-cli` 直接 curl、fetch、浏览器自动化或访问 E10 邮件接口。
4. 写入/删除必须使用 CLI 确认流程；prepare→apply 时把 continuation 原样传给 apply，并在 apply 前取得用户明确确认。
5. 附件、图片上传或文件解析属敏感数据处理，即便 operation 风险等级非高风险写入，也必须先取得用户对“文件内容可能进入大模型/外部解析服务”的明确确认。
6. 写请求已发出后遇 `partial`/`write_uncertain`/网络中断/回查失败，立即停止，按 `high-risk-write.md` 决策树处理，不盲目重试。
