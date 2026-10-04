# 文件输入与上传协议

遇到本地文件、`file://`、Base64、格式限制、页数/大小限制或批量上传时读取本文。

## 输入判定

| 输入形态 | MCP v0.1.4 的实际识别 | 动作 |
|---|---|---|
| `http://`、`https://` | 解析/抽取工具识别为 `file_url` | 直接传给目标工具 |
| Windows 盘符绝对路径 | 上传工具识别为本地文件 | 先上传 |
| `./`、`../`、`.\\`、`..\\`、`/`、`\\` 开头的路径 | 上传工具识别为本地文件 | 先上传 |
| `file://` | 只有上传工具识别为本地文件 | 先上传 |
| 裸相对路径，如 `invoice.pdf` | 上传工具不会识别为本地文件 | 先解析为明确路径 |
| Base64 或 data URL | 非 URL 字符串会被当作 Base64 | 单次处理可直传；复用时可上传 |

不要把本地路径直接传给解析/抽取工具；它会被当作 Base64。不要把 HTTP(S) URL 传给上传工具；它同样会被当作 Base64。

在上传本地文件前先确定区域。`upload_temporary_file` 的 Schema 没有 `accept_language`，它只能读取 Connector 进程的 `ADP_ACCEPT_LANGUAGE`，缺省走中国区。目标为全球区时，只有已确认该环境变量为 `en` 才执行上传；否则停止并请用户配置全球区 Connector，或改为提供 HTTP(S)/Base64。当前 WorkBuddy Connector 的默认配置只注入 API Key，不能通过工具参数临时切区。

## `upload_temporary_file` 契约

每次只调用一个文件：

```json
{
  "chunk": "D:\\documents\\invoice.pdf"
}
```

只传 `chunk`。虽然上传 OpenAPI 还公开可选 `application_id` 和 `sharing_scope`，当前 MCP Schema 不暴露它们，并且本 Skill 明确不要求它们。

成功后读取：

```json
{
  "code": "success",
  "message": "",
  "data": {
    "id": "...",
    "file_name": "invoice.pdf",
    "file_size": 12345,
    "content_type": "application/pdf",
    "download_url": "https://..."
  }
}
```

只有 `code` 成功且 `data.download_url` 非空时，才把该值作为后续工具的 `file`。`data.status` 不是后端必然字段，不要要求它存在。

## 文件名与内存

- 本地路径上传会保留路径的 basename。
- Base64 上传固定使用文件名 `chunk`，会丢失原始文件名和扩展名。
- MCP Node 进程先把本地文件整体读入内存，再创建 Blob；上传后端也先 `await chunk.read()` 把整个文件读入内存。
- 优先使用本地路径而不是 Base64，避免约 33% 的 Base64 体积膨胀和额外内存复制。
- 不要同时并发上传大量接近上限的文件。

## 大小、页数和格式要分层表述

不要把“上传存储成功”等同于“后续解析一定支持”。

- 上传 OpenAPI 只要求 `chunk`，没有公开格式、页数或上传并发限制。
- 当前后端默认上传存储配额是单文件 200 MiB、单用户 2,000 个未删除文件、总计 15 GiB；这些是可部署配置，不是公有云永久 SLA。
- 中国区产品文档当前写每份文档不超过 260 页、50 MB；英文产品文档仍写 100 页、50 MB。跨区域或套餐未知时，采用更保守的 **100 页、50 MB**；明确中国区时可按当前中文合同提示 **260 页、50 MB**。
- Web 产品页的“单批最多 10 份”不是 MCP 单次批量参数；MCP 每次工具调用仍只处理一个文件。

保守格式路由：

| 格式 | 建议工具 |
|---|---|
| PDF、JPG/JPEG、PNG、BMP、TIFF | 解析和对应专用抽取工具 |
| WEBP | MCP 产品页列为支持；服务拒绝时停止，不要重复重试 |
| DOC/DOCX、XLS/XLSX、PPT/PPTX | 优先 `parse_document`；专用票据/证件工具优先使用 PDF 或图片 |
| OFD | 只路由到 `parse_document` 或 `extract_china_invoice`；不要用于其他专用工具 |

服务端拒绝格式时要求用户转换为 PDF 或受支持图片；不要仅改扩展名。

## 并发

明确区分两层：

1. **上传并发**：MCP 没有客户端并发锁，上传路由也没有独立 semaphore 或固定并发承诺，因此技术上可以发起多个并行调用，但不能声称上传接口保证某个并发数。
2. **文档处理并发**：默认最多 10 个并发。该数字用于整个上传后处理流水线的安全上限，不是上传路由的源码上限。

执行策略：

- 默认：最多 10 个小文件并行进入流水线。
- 接近 50 MB：上传保持 1～2 并发，即使付费账户也不要一次并发 10 个大文件。
- 大批次按窗口分组；前一窗口释放处理槽位后再提交下一窗口。
- 429 时尊重 `Retry-After`，只重新排队失败项，不回滚成功项。

## 重试与生命周期

- MCP 客户端没有自动重试。
- 上传后端对部分非业务异常内部最多尝试 2 次，间隔约 0.2 秒；业务错误不会自动重试。
- Agent 额外重试最多一次。每次上传都会生成新的文件 ID，失败响应也可能发生在文件已写入之后，因此不能把重试描述为幂等。
- 后续处理失败时优先复用已有 `download_url`，不要自动重新上传。
- 返回 URL 来自文件存储，具体过期时间由部署配置决定且当前上传响应不返回；将它作为任务中间产物，不做永久存储承诺。

## 官方参考

- [文件上传 OpenAPI](https://adp-doc.laiye.com/api-reference/adp-api/工作流文件/文件上传.md)
- [ADP MCP 支持格式](https://adp-doc.laiye.com/products/adp-mcp.md#支持的文件格式)
- [ADP 操作手册](https://adp-doc.laiye.com/index.md)
- [OFD 更新说明](https://adp-doc.laiye.com/updatelog.md#开箱即用文档解析和国内通用票据新增ofd格式识别)
