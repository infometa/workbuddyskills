# 新增资产

## 什么时候读取

用户要新增一条固定资产记录时读取本文件。

## Operation

`asset.create`（风险 `high-risk-write`）。必须 `prepare -> apply`：第一次调用不带 `confirm` 返回 continuation 与预览，用户确认后第二次调用带 `confirm:true` 与 `continuation` 执行。

## 输入要点

以 `weaver-work-cli asset schema` 为准。必填：`asset_name`、`asset_type_browse`（资产类型 ID，先经 `asset.resolve.type` 解析）。可选：`asset_spec`、`stockindate`（默认今天）、`startprice`、`original_value`、`image_id`（裸 file_id，不接受文件上传）、`asset_data_attr`（默认 `0`）、`admin_istrator`（默认当前操作人）、`blongdepartment`、`resourceid`、`stateid`。

`asset_type_browse` 必须是已解析的类型 ID，不要传中文类型名。

## 示例

Windows PowerShell：

```powershell
# prepare（返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.create --input-json '{"asset_name":"EXAMPLE_ASSET","asset_type_browse":"EXAMPLE_TYPE_ID"}'
# apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.create --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
# prepare（返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.create --input-json '{"asset_name":"EXAMPLE_ASSET","asset_type_browse":"EXAMPLE_TYPE_ID"}'
# apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.create --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

## 返回

`apply` 成功返回 `dataIds`（新增资产数据 ID 列表）、`count` 与 `mainTable`。失败时见写操作失败决策树。

## 注意

- `image_id` 仅接受已通过文件上传能力得到的裸 file_id；CLI 不内置图片上传，需要上传时走外部文件上传模块。
- 不要手工构造 continuation；它绑定本次提交的主表内容，过期或篡改会被拒绝。
- 出现 `partial/write_uncertain` 时停止，先做一次 `asset.detail` 只读回查，不要重复提交 apply。
