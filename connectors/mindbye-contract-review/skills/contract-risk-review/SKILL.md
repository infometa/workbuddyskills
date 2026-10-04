---
name: contract-risk-review
description: 使用明白律师合同风险审查服务审查中文合同（劳动、离婚、租赁、委托、买卖等），异步生成审查报告、修改建议和 Word 批注版。当用户要求审查/审核合同、识别合同风险、询问"合同能不能签"、出具审查意见或修改建议时使用。
---

# 明白律师·合同风险审查

异步合同审查服务，共 3 个工具：`contract_review_prepare_upload`（上传原件）→ `contract_review_submit`（提交任务）→ `contract_review_result`（轮询结果）。服务免鉴权直通，无需用户登录或配置凭证。

## 核心调用流程

### 场景一：用户提供了 docx 合同文件（推荐路径，可产出 Word 批注版）

1. 调用 `contract_review_prepare_upload` 申请上传凭证：
   - 必填 `fileName`（原始文件名，如「劳动合同.docx」）、`sizeBytes`（字节数，须 >0，最大 50MB）；
   - 建议同时传 `fileType`（扩展名，与文件名后缀一致）和 `mimeType`（docx 为 `application/vnd.openxmlformats-officedocument.wordprocessingml.document`）。
2. 按返回的 `uploadMethod` 与 `uploadHeaders`，将文件二进制 PUT 到返回的 `uploadUrl`。
   - 注意：`uploadUrl` 只用于 PUT 上传，**不要**把它填进后续 `sourceFile.downloadUrl`。
3. 调用 `contract_review_submit` 提交任务：
   - `contractText` 传**空字符串 `""`**（服务端会通过 `sourceFile.fileId` 自行解析文件）；
   - `sourceFile.fileId` 填 prepare_upload 返回的 `fileId`；
   - `docxProvided` 设为 `true`，并填写 `fileName`、`fileType`。
   - 切记：有原件时**不要**把合同全文粘进 `contractText`，否则服务端会跳过文件解析（`parsedFromFile=false`），导致无法生成 Word 批注版。
4. 拿到 `taskId` 后，按「轮询与耗时」一节查询结果。

### 场景二：用户只粘贴了纯文字合同（无文件）

直接调用 `contract_review_submit`，`contractText` 填合同全文。该场景无法生成 Word 批注版，可在交付时说明。

## 工具参数速查

### contract_review_prepare_upload

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| fileName | string | 是 | 原始文件名 |
| sizeBytes | integer | 是 | 文件字节大小，>0，最大 50MB |
| fileType | string | 否 | 扩展名，如 docx |
| mimeType | string | 否 | MIME 类型 |
| sha256 | string | 否 | 校验值 |
| source | string | 否 | 调用来源标识，可填 `workbuddy` |

### contract_review_submit

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| contractText | string | 是 | 有原件传 `""`；仅纯文本场景传全文 |
| sourceFile | object | 有原件时必填 | `fileId` 与 `downloadUrl` 至少提供一个；含 fileName / fileType / mimeType / sha256 / sizeBytes |
| docxProvided | boolean | 否 | 是否已提供 DOCX 原件 |
| fileName / fileType | string | 否 | 原文件名与类型，用于交付语境 |
| contractTypeHint | string | 否 | 合同类型提示，不确定留空；文件名含「离婚协议」会自动识别为离婚协议 |
| reviewPosition | string | 否 | 审查立场，如「甲方」「乙方」「承租方」；用户未说明可先询问或留空 |
| industry / region | string | 否 | 行业 / 适用地区，不确定留空 |
| userQuestion | string | 否 | 用户额外关注的问题（不是合同原文） |

### contract_review_result

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| taskId | string | 是 | submit 返回的任务 ID |
| includeArtifacts | boolean | 否 | 完成后是否返回附件列表，建议传 `true` |

## 轮询与耗时

- 审查为异步长任务：常规合同整体约 10 分钟（排队 + 审查，pending 状态可能持续 7 分钟以上）；离婚协议较快，约 2.5～4 分钟；委托合同约 10 分钟。
- 建议每 20～30 秒调用一次 `contract_review_result`，最长坚持轮询 15 分钟；pending 期间不要判定为失败。
- 完成后交付两样东西：
  1. 完整展示 `data.result.window_response_markdown`（审查报告正文，不要截断或过度摘要）；
  2. 列出 `data.result.artifacts` 或 `data.result.download_files` 中的全部下载链接（审查意见书 .docx、原文批注版 .docx 等）。
- 附件下载 URL 会 302 跳转到 OSS，下载时须跟随重定向（如 `curl -L`）。

## 注意事项与异常处理

- 「无对应原文」的风险批注：服务端会跳过原文定位，但仍保留在审查意见书中，向用户呈现时正常展示即可。
- 若 prepare_upload 返回的 `fileId` 长时间未使用（约 1 小时）可能过期，过期后重新申请上传凭证即可。
- 提交失败或参数错误时，接口会返回可读错误信息，按错误内容修正后重试；不要用编造的 taskId 查询。
- 本服务为只读审查，不会修改用户原件；向用户交付批注版文档前，确认对方希望保存/下载。
