# 资产归还

## 什么时候读取

用户要归还资产时读取本文件。流程是：先查询可归还候选（只读），再执行归还（需确认链）。

## Operation

| Operation | 风险 | 说明 |
| --- | --- | --- |
| `asset.return.query` | read-before-write | 查询可归还资产候选，返回候选数据；不写数据、不返回 continuation |
| `asset.return.create` | high-risk-write | 执行归还，需 `confirm:true` + `continuation` |

## 输入要点

`asset.return.query`：可选 `return_type`（`0`=全部归还，`1`=部分归还）、`detail1`（按 `asset_name` 过滤的候选列表）。

`asset.return.create`：必填 `data_ids`（半角逗号拼接的确认资产数据 ID，来自 `return.query` 的候选）；需 `prepare -> apply`。

## 示例

Windows PowerShell：

```powershell
# 1) 只读查询候选
weaver-work-cli --profile eteams --json asset run asset.return.query --input-json '{"return_type":"0"}'
# 2) prepare（返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.return.create --input-json '{"data_ids":"EXAMPLE_DATA_ID_1,EXAMPLE_DATA_ID_2"}'
# 3) apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.return.create --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
# 1) 只读查询候选
weaver-work-cli --profile eteams --json asset run asset.return.query --input-json '{"return_type":"0"}'
# 2) prepare（返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.return.create --input-json '{"data_ids":"EXAMPLE_DATA_ID_1,EXAMPLE_DATA_ID_2"}'
# 3) apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.return.create --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

## 返回

`return.query` 返回候选：统一含 `resultCode`、`resultMsg`、`mainTable`、`customData`、`responseData`（业务数据在 `mainTable`，等价于 `responseData.customData.mainTable`）。

`return.create` 成功返回同样的统一结构，关键字段在 **`mainTable`**：

| 业务含义 | 字段 | 用途 |
| --- | --- | --- |
| 归还流程 ID | `lcID` | **作为「查看详情」链接（scene=`asset_return`）的 dataID** |
| 流程标题 | `lcbt` | 回报给用户 |
| 归还编号 | `ghbh` | 归还单号，回报给用户的关键标识 |

建单后按 `asset.viewlink` 的 `asset_return` 场景拼链接：

```powershell
weaver-work-cli --profile eteams --json asset run asset.viewlink --input-json '{"scene":"asset_return","ids":["<上一步返回的 lcID>"]}'
```

要点：
- `lcID` 可能在建单返回时为回填中（空值），此时不要判定失败、不要重试建单；可先用 `weaver-e10-workflow-connector` 读回补齐，或如实说明「归还单号生成中、链接暂不可用」。
- 链接解析失败只说明「链接暂不可用」，**不影响归还单本身**，绝不因此重试 `return.create`。

## 注意

- `data_ids` 必须是 `return.query` 返回的候选数据 ID，不要凭空构造。
- `return.query` 是只读，不带 `confirm` 也不返回 continuation；只有 `return.create` 走确认链。
- 出现 `partial/write_uncertain` 时停止，先做一次只读回查，不要重复提交 apply。
