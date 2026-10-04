# OCR 预览

## 什么时候读取

用户要识别发票文件内容，但没有明确要求入票夹或保存发票时读取本文件。

## Operation

| Operation | 固定规则 |
| --- | --- |
| `invoice.ocr.preview` | 固定 `flag=13`、`is_sync=1`、`is_save=1`、`operate_type=0`；CLI 返回 `saved=false` |

## 输入

支持 `file`、`url` 或 `upload` 三种来源，三者选一个。`upload` 必须是 `invoice.upload` 返回的对象。

## 示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.ocr.preview --input-json '{"file":"./invoice.pdf"}'

weaver-work-cli --profile eteams --json invoice run invoice.ocr.preview --input-json '{"upload":{"id":"UPLOAD_FILE_ID","fileType":"pdf","fileName":"invoice.pdf"}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.ocr.preview --input-json '{"file":"./invoice.pdf"}'

weaver-work-cli --profile eteams --json invoice run invoice.ocr.preview --input-json '{"upload":{"id":"UPLOAD_FILE_ID","fileType":"pdf","fileName":"invoice.pdf"}}'
```

## 失败后的处理

如果上传已成功但 OCR 失败，CLI 会返回 `partial/artifact_uploaded`，其中包含 `data.upload`。不要自动重复上传同一个文件；若用户要求继续 OCR，复用返回的 `upload` 对象。

## 注意

OCR 前必须先提醒用户：发票附件/图片/文件内容可能被上传到 E10 业票通和 OCR 服务，并可能进入当前大模型上下文用于理解和处理；只有用户明确确认后才执行 `invoice.ocr.preview` 或复用已上传的 `upload` 对象继续 OCR。

`saved=false` 表示 CLI 不把 OCR 预览描述为已入票夹。用户要导入时走 `invoice.import.prepare -> invoice.import.apply`。
