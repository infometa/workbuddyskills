# 附件上传 / 下载

## mail.attachment.upload — 上传附件（三步）

风险等级：`write`（含文件上传，敏感数据处理，执行前须取得用户对“文件内容可能进入大模型/外部服务”的明确确认）。

字段：`file`（本地文件路径）、`name`（附件名）。

流程：预检（`preUploadCheck`）→ 上传（`module/upload`，multipart 上传文件 Blob）→ 绑定权限（`addPermissionFile`），返回 `fileid`。后续发送时在 `mail.send.prepare/apply` 的 `files` 传入该 fileid。

```text
weaver-work-cli --profile eteams --json mail run mail.attachment.upload --input-json '{"file":"./quarterly.pdf","name":"quarterly.pdf"}'
```

## mail.attachment.download — 批量下载附件

风险等级：`write`（落本地文件，确认输出目录避免覆盖）。

字段：`ids`（附件 id，逗号分隔）、`output`（输出目录）。

## mail.attachment.center — 附件中心

风险等级：`read`。字段：`keyword`、`page`、`size`。

## 要点

- 上传/下载前必须向用户说明：文件内容可能被上传到 E10 邮件系统，并可能进入当前大模型上下文。
- 下载会落本地 `output` 目录，执行前确认目录与文件名，避免覆盖。
- 用户未明确确认前，不执行上传、解析或下载命令。
- 写请求已发出后遇到不确定结果，停止重试，按共享 `high-risk-write.md` 处理。
