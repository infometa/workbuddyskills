# 上传发票文件

## 什么时候读取

用户只要求上传发票文件、获取上传文件 ID，或后续 OCR 需要先取得 `upload` 对象时读取本文件。

## Operation

| Operation | 固定规则 |
| --- | --- |
| `invoice.upload` | 固定上传 `ocr=0`，只取得文件 ID，不做上传阶段解析 |

## 文件来源

支持本地 `file` 或服务端可访问的 `url`，两者只能选一个。支持扩展名：`pdf`、`ofd`、`xml`、`png`、`jpg`、`jpeg`。

本地文件必须存在、非空且不超过 25 MiB。URL 只允许 `http/https`，不能包含账号密码。

## 示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.upload --input-json '{"file":"./invoice.pdf"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.upload --input-json '{"file":"./invoice.pdf"}'
```

## 返回

返回规范化后的 `upload` 对象，包含 `id`、`ids`、`fileType`、`fileName`、`totalPages`、`hasFanWei`、`ocrMap` 和 `fail=false`。后续 `invoice.ocr.preview` 可以直接复用这个对象；只有明确需要 OCR 预览时才调用 `invoice.ocr.preview`。

## 注意

上传前必须先提醒用户：发票附件/图片/文件内容可能被上传到 E10 业票通，并可能进入当前大模型上下文用于理解和处理；只有用户明确确认后才执行 `invoice.upload`。用户仅提供文件路径或文件名不等于同意上传。
