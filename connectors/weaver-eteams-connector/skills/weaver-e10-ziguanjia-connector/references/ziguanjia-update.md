# 修改资产

## 什么时候读取

用户要修改已存在资产的字段（名称、状态、管理人、使用人、地点、单价、价值等）时读取本文件。

## Operation

`asset.update`（风险 `high-risk-write`）。必须 `prepare -> apply`：第一次调用不带 `confirm` 返回 continuation 与变更摘要，用户确认后第二次调用带 `confirm:true` 与 `continuation` 执行。

## 输入要点

以 `weaver-work-cli asset schema` 为准。定位目标（三选一）：`id`（资产数据 ID）、`asset_number`、`asset_name`（后两者用于查询定位，命中多条会要求改用 ID）。变更内容放 `changes`，至少包含一个字段：`asset_name`、`stateid`、`admin_istrator`、`resourceid`、`location_browse`、`unit_price`、`value`。

`stateid` / `location_browse` 必须是已解析的 ID。

## 示例

Windows PowerShell：

```powershell
# prepare（返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.update --input-json '{"id":"EXAMPLE_ASSET_ID","changes":{"stateid":"EXAMPLE_STATUS_ID"}}'
# apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.update --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
# prepare（返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.update --input-json '{"id":"EXAMPLE_ASSET_ID","changes":{"stateid":"EXAMPLE_STATUS_ID"}}'
# apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.update --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

## 返回

`apply` 成功返回 `dataIds`、`count` 与目标 `id`。

## 注意

- `changes` 只提交需要变更的字段，不要传空值覆盖其它字段。
- 不要修改 `id` 等内部控制字段。
- 出现 `partial/write_uncertain` 时停止，先做一次 `asset.detail` 只读回查，不要重复提交 apply。
