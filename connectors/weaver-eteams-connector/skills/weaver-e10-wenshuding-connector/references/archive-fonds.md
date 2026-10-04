# 全宗与预归档电子文件库节点

## 什么时候读取

需要确定档案所属全宗、需要预归档上传的 `treeId`，或用户提到“全宗/收集库/管理库/预归档库”时读取本文件。

## Operation

| Operation | 必填输入 | 说明 |
| --- | --- | --- |
| `archive.fonds.list` | 无；可选 `menuSign`（`collectLib`/`manageLib`，默认 `collectLib`） | 返回全宗 `id`、`fonds_name`、`fonds_code` 等 |
| `archive.prelib.tree` | 无 | 返回预归档树中识别出的电子文件库节点（`id` 形如 `{appId}_{appId}`） |

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json archive run archive.fonds.list --input-json '{"menuSign":"collectLib"}'

weaver-work-cli --profile eteams --json archive run archive.prelib.tree --input-json '{}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json archive run archive.fonds.list --input-json '{"menuSign":"collectLib"}'

weaver-work-cli --profile eteams --json archive run archive.prelib.tree --input-json '{}'
```

## 注意

- 全宗 `id` 是后续上传（`archive.upload.prelib.prepare` 的 `fondsId`）和档案树查询的输入，必须原样复用，不要用 `fonds_code` 代替。
- 电子文件库节点 `id` 即上传用的 `treeId`。`archive.prelib.tree` 只返回识别出的电子文件库节点；存在多个时必须让用户明确选择后再传 `treeId`，不要自行猜测。
- 用户没有说明收集库/管理库时，默认使用 `collectLib`；只有在用户明确提到管理库时才传 `manageLib`。
