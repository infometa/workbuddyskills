# 下载发票附件

## 什么时候读取

用户要把发票附件下载到本地文件，或已经给出 `fid` 和 `fileId` 时读取本文件。

## Operation

| Operation | 固定规则 |
| --- | --- |
| `invoice.download` | 先校验 `fileId` 属于目标 `fid`，拒绝覆盖输出文件 |

## 示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.download --input-json '{"fid":"12345","fileId":"67890","output":"./invoice-12345.pdf"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.download --input-json '{"fid":"12345","fileId":"67890","output":"./invoice-12345.pdf"}'
```

## 注意

下载附件不会把文件内容发送给大模型；但如果后续要读取、解析、OCR 或转传下载后的附件，必须先提醒用户文件内容可能进入大模型上下文或外部解析服务，并等待用户明确确认。

如果用户没有 `fileId`，先用 `invoice.get` 查看详情里的 `flist`。`output` 已存在时 CLI 会失败，不要自动覆盖用户文件。
