# 资产领用

## 什么时候读取

用户要提交资产领用申请（多条领用明细）时读取本文件。

## Operation

`asset.use`（风险 `high-risk-write`）。必须 `prepare -> apply`：第一次调用不带 `confirm` 返回 continuation 与预览，用户确认后第二次调用带 `confirm:true` 与 `continuation` 执行。

## 输入要点

以 `weaver-work-cli asset schema` 为准。必填：`detail1`（数组，至少一条；每条 `apply_info` 必填，`asset_spec`、`asset_remark`、`asset_type`、`use_count` 可选）。可选：`use_location`（领用后地点 ID，经 `asset.resolve.location` 解析）、`purpose`。

`detail1[].asset_type` 为资产类型 ID。

## 示例

Windows PowerShell：

```powershell
# prepare（返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.use --input-json '{"detail1":[{"apply_info":"EXAMPLE_APPLY_INFO","asset_type":"EXAMPLE_TYPE_ID","use_count":1}],"use_location":"EXAMPLE_LOCATION_ID","purpose":"EXAMPLE_PURPOSE"}'
# apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.use --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
# prepare（返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.use --input-json '{"detail1":[{"apply_info":"EXAMPLE_APPLY_INFO","asset_type":"EXAMPLE_TYPE_ID","use_count":1}],"use_location":"EXAMPLE_LOCATION_ID","purpose":"EXAMPLE_PURPOSE"}'
# apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.use --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

## 返回

`apply` 成功返回统一结构：`resultCode`、`resultMsg`、`actionData`、`responseData`、`customData`，以及提到顶层的 **`mainTable`**（= `responseData.customData.mainTable`）。

关键字段在 `mainTable`：

| 业务含义 | 字段 | 用途 |
| --- | --- | --- |
| 领用流程 ID | `lcID` | **作为「查看详情」链接（scene=`asset_use`）的 dataID** |
| 流程标题 | `lcbt` | 回报给用户 |
| 领用单号 | `lybh`（具体 key 以运行时为准） | 领用单号，回报给用户的关键标识 |

建单后按 `asset.viewlink` 的 `asset_use` 场景拼链接：

```powershell
weaver-work-cli --profile eteams --json asset run asset.viewlink --input-json '{"scene":"asset_use","ids":["<上一步返回的 lcID>"]}'
```

单号可能为回填中（空值），此时不要重试建单；链接解析失败只说明「链接暂不可用」，不影响领用单本身。

## 注意

- 不要把中文地点名称作为 `use_location`，先走 `asset.resolve.location`。
- 出现 `partial/write_uncertain` 时停止，不要重复提交 apply。
