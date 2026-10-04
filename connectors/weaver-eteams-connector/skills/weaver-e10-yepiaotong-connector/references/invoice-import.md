# 导入发票文件

## 什么时候读取

用户要把本地发票文件或远程发票 URL 导入票夹时读取本文件。开始前也读取共享高风险协议：`../../weaver-e10-shared-connector/references/high-risk-write.md`。

## Operation

| 阶段 | Operation | 必填输入 |
| --- | --- | --- |
| 识别预览 | `invoice.ocr.preview` | `file` 或 `url` |
| 准备导入 | `invoice.import.prepare` | `file` 或 `url`，以及 `validate`、`syncToOa` |
| 确认导入 | `invoice.import.apply` | 与 prepare 相同的 `file` 或 `url`，以及 `continuation`、`confirm=true` |

## 示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.ocr.preview --input-json '{"file":"./invoice.pdf"}'

weaver-work-cli --profile eteams --json invoice run invoice.import.prepare --input-json '{"file":"./invoice.pdf","validate":true,"syncToOa":true,"filedMap":{"projectName":"示例项目"}}'

weaver-work-cli --profile eteams --json invoice run invoice.import.apply --input-json '{"file":"./invoice.pdf","filedMap":{"projectName":"示例项目"},"continuation":"PREPARE_CONTINUATION","confirm":true}'

weaver-work-cli --profile eteams --json invoice run invoice.import.prepare --input-json '{"url":"https://example.com/invoice.pdf","validate":true,"syncToOa":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.ocr.preview --input-json '{"file":"./invoice.pdf"}'

weaver-work-cli --profile eteams --json invoice run invoice.import.prepare --input-json '{"file":"./invoice.pdf","validate":true,"syncToOa":true,"filedMap":{"projectName":"示例项目"}}'

weaver-work-cli --profile eteams --json invoice run invoice.import.apply --input-json '{"file":"./invoice.pdf","filedMap":{"projectName":"示例项目"},"continuation":"PREPARE_CONTINUATION","confirm":true}'

weaver-work-cli --profile eteams --json invoice run invoice.import.prepare --input-json '{"url":"https://example.com/invoice.pdf","validate":true,"syncToOa":true}'
```

## 注意

导入前必须先提醒用户：发票附件/图片/文件内容可能被上传到 E10 业票通、OCR/查验服务，并可能进入当前大模型上下文用于理解和处理；只有用户明确确认后才执行 `invoice.import.prepare/apply`。用户仅提供文件路径或文件名不等于同意导入或解析。

导入本地发票文件的正常业务链路是：先 OCR 预览票面 -> 再导入并查验 -> 最后回查导入结果。Agent 不要因为用户只说“上传/导入发票”就默认跳过查验。

`validate` 和 `syncToOa` 必须显式传布尔值。默认推荐 `validate=true`、`syncToOa=true`；`validate=true` 分支由服务端固定同步 OA，不能设置 `syncToOa=false`。只有用户明确要求跳过发票查验或离线导入时，才传 `validate=false`；`validate=false` 表示跳过查验，不能描述为“查验通过”。

`fieldKey`/`fieldValue` 可给成功发票设置单个字段，两个参数必须同时提供。`filedMap` 用于批量设置成功发票字段；它在 `inputSchema` 和 `--input-json` 中必须保持 JSON 对象，例如 `"filedMap":{"projectName":"示例项目"}`，不要提前转成字符串。CLI 会在提交 `/api/app/inc/biz/addInvoiceByFile` 的 multipart 表单时再序列化为字符串。

`.prepare` 返回 `preview`、`continuation`、`expiresInSeconds` 和 `workflow.state="AWAITING_CONFIRMATION"`。展示风险后等待用户明确确认，再调用 `.apply`。
