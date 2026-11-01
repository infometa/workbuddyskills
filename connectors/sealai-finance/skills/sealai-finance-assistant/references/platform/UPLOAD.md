# WorkBuddy 原件上传辅助流程

本文件是现有财务助手的内部上传适配，不是独立上架 Skill。所有业务、权限、幂等、原件核对、预览和逐步确认规则保持不变。

用户已选定文件并授权当前业务材料范围后，将原始文件的本地绝对路径写入会话目录中的 JSON 数组文件。不要遍历目录、上传额外文件或向用户索取 OAuth Token。上传目的地为当前 SealAI MCP 元数据 issuer，先核对企业与域名。读取/上传仅限用户选定原件。文件路径 JSON 不含凭据；上传计划文件包含短期凭证，应以0600权限创建并在执行后删除，不放入对话、版本库或日志。

1. 使用包内 Node.js 脚本 `scripts/upload-files.mjs inspect --paths <paths.json>` 获取 `files` 元数据。脚本不上传文件，输出 name、size、sha256 和 mime_type。不要让模型生成 Base64 或文件字节。
2. 发现真实 `finance_file_upload_prepare` MCP 工具，原样传 `files`。工具不可用或权限拒绝就停止，不绕过连接器。将 structuredContent 的结果作为本地计划文件（0600）；不要索取、读取或导出 WorkBuddy 保存的 OAuth Token。
3. 执行 `node scripts/upload-files.mjs upload --paths <paths.json> --plan <plan.json> --origin <已核对的SealAI HTTPS Origin> --result <新结果文件.json>`。相对脚本路径以入口 Skill 目录为基准；保持原始绝对路径，不执行 Shell 拼接或 Base64 转码。脚本逐文件直传，禁止重定向；使用后删除短期计划。
4. 结果中的 `uri` 是 SealAI 受管引用，不是公开下载 URL。`uri→url/file_ref`，`text→name/display_name`，`mimeType→mimeType/mime_type`。保留真实 file_id、大小与摘要，不猜扩展名和MIME。原引用不得向其他企业或用户共享。SealAI 按当前用户与租户校验；文件在后端私有存储，业务层重新签发内部下载地址，不依赖上传凭证的有效期。
5. 报销草稿仍把原件放入模板真实 ATTACHMENT 字段，必须核对保存返回的文件名和数量。受管 url 保存后可能变为后端签名URL，应以 file_id（如果返回）、文件名、数量和业务工具保存结果核对，不要求签名URL逐字等于上传时的受管引用。发票/小票与对话材料将 uri 传为既有 `file_ref`，不改业务工具。
6. 完成不确定、部分失败或网络超时时，使用 `finance_file_upload_status(file_ids)` 核对已完成结果；不要自动重新申请/重复提交。状态未完成则仅对失败文件重新 inspect/prepare，经用户范围确认后重传。旧凭证10分钟失效，不能用于普通MCP或公开下载。已上传文件使用受管引用，不在草稿保存后自动删除；未完成上传记录与对象按服务端运维策略清理，不能承诺自动清理已经生效。
7. 文件总数每批1–10，单文件1字节–20MB。支持 PDF、PNG、JPEG、WEBP、GIF、UTF-8 TXT/CSV 和 OOXML DOCX/XLSX/PPTX。文件扩展名、实际字节、大小和SHA-256必须与计划一致；上传成功不保证该业务工具支持此文档类型或识别成功。先用 inspect 中真实声明的MIME，不把全部文件改成PDF。
8. 不存在上传工具/Node运行时、无法安全写入计划或类型不支持时，明确停止对应附件流程。不得使用豆包 FileBatchUpload、虚构HTTPS链接、本地 file/blob URI 或OCR文本替代原件。

上传支持稳定引用不代表审核已通过；保存草稿不等于提交。提交具体 revision、规则发布和评论写回仍分别要求用户确认。
