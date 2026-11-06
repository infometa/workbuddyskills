# 原连接器通用文件上传与合同登记

不新增本地MCP服务、OAuth客户端、Token文件或常驻进程。云托管连接器仍可调用原业务工具；本地原始文件PUT依赖当前终端已有文件执行能力，移动端不可用时引导电脑端。

## 计算与准备

仅读取用户指定附件，用本地工具计算真实字节数，以及原始字节MD5的标准Base64（16字节摘要，不是整个文件内容Base64）。不让模型猜摘要，不把文件原始内容放入对话。文件名只含名称，不含目录。默认 `directory=attachment`，合同可用 `contract`；目录限1～64位字母、数字、下划线、短横线。

通过 `prepareFileUpload` 平铺传 `directory`、`fileName`、`fileSize`、`contentMd5`；`fileSize` 是正整数。返回 `uploadId/fileCos/fileName/fileType/uploadUrl/contentType/contentMd5/fileSize/expiresAt/referenceExpiresAt`。上传与业务引用有效期独立，以响应时间为准；不要硬编码永久可用。通用层支持PDF及照片等，不意味着后续合同接口接受照片。

## 实际上传

使用已有本地执行能力将同一文件原始字节PUT到响应 `uploadUrl`。请求头使用返回的 `Content-Type`、`Content-MD5`、`Content-Length`；检查本地命令退出码和HTTP200。不得向COS发送音为有数OAuth Token，不跟随重定向、不自动重试，不打印签名地址或启用verbose。把文件路径和响应值当数据安全传参，不能拼接成可执行代码。

上传链接含单对象临时授权，勿展示给用户或写入日志、文档、Skill。仅准备成功、拿到fileCos或调用命令本身都不表示PUT成功。失败时停止业务登记；超时状态不明时保留引用并按平台已有核验方式处理，不盲目重复上传。

## 合同登记

实际上传成功后，调用 `importCopyrightContractFile`：

- 优先传 `fileName`、`fileCos`，均取同一次上传响应；或者只传 `uploadId`。fileName若填写必须与原记录一致。
- `fileCos` 是租户内相对文件引用，不是完整COS key或HTTP地址。不能借用其他账号、租户、环境的引用。
- 已完成PUT而登记超时，可使用相同 `uploadId` 恢复登记；服务端复用同引用结果，不把它扩大成所有创建操作都具备强幂等。
- 兼容下载链接方式：只传 `fileName` 和用户提供的 `fileUrl`，与COS引用方式二选一。必须是实际可下载PDF地址，不能凭空生成公网链接。
- 合同仅接受PDF，并额外校验权限和业务大小上限。返回 `fileId/fileName/archiveUrl/message`，按message如实描述识别及后续流程，不宣称费用申请完成。

工具服务端合同登记超时为120秒，包中请求超时也设为120秒；实际WorkBuddy与网关超时以运行时为准。客户端超时不表示服务端没有写入。
