# 查验预览

## 什么时候读取

用户要查验已有发票，但没有明确要求把查验结果回写票夹时读取本文件。

## Operation

| Operation | 固定规则 |
| --- | --- |
| `invoice.validate.preview` | 先取详情，固定 `flag=100`、`is_save=1`、`needLog=true`，不回写查验结果 |

## 输入

必须提供 `fid` 和 `scope`。`scope` 只能是 `personal` 或 `enterprise`。

## 示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.validate.preview --input-json '{"fid":"12345","scope":"personal"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.validate.preview --input-json '{"fid":"12345","scope":"personal"}'
```

## 注意

`invoice.validate.preview` 只做预览。`saved=false` 表示没有回写票夹；不要把预览结果描述为已更新发票。
