# 档案基本信息

## 什么时候读取

需要查看单条档案的年度/案卷号/起止件号/文件日期/保管期限/密级/库位等基本信息时读取本文件。

## Operation

| Operation | 必填输入 | 说明 |
| --- | --- | --- |
| `archive.info.get` | `arcDangan`（`{档案ID}_{表单ID}`）或 `dataId` + `formId` | 返回档案基本信息行 |

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json archive run archive.info.get --input-json '{"arcDangan":"1252600626189156465_1190991330335571989"}'

weaver-work-cli --profile eteams --json archive run archive.info.get --input-json '{"dataId":"1252600626189156465","formId":"1190991330335571989"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json archive run archive.info.get --input-json '{"arcDangan":"1252600626189156465_1190991330335571989"}'

weaver-work-cli --profile eteams --json archive run archive.info.get --input-json '{"dataId":"1252600626189156465","formId":"1190991330335571989"}'
```

## 注意

- `arcDangan` 与 `dataId`+`formId` 二选一即可，两者都在时以 `arcDangan` 为准。
- `arcDangan` 必须严格是 `{档案ID}_{表单ID}` 的数字 ID 对，格式错误会返回 `validation/arc_id_invalid`，此时不要重试，先修正输入。
- 返回的库位、密级、保管期限等字段用于向用户说明档案状态；不要把内部字段直接暴露给终端用户。
