# 资产查询（列表 / 详情 / 领用 / 报修 / 采购）

## 什么时候读取

用户要查询资产列表、资产详情、我的领用列表、我的报修列表或采购申请列表时读取本文件。

## Operation 与固定规则

| Operation | 固定规则 |
| --- | --- |
| `asset.list` | 资产台账列表，按 `mainTable` 字段筛选 |
| `asset.detail` | 资产详情，至少传 `id` / `asset_number` / `asset_name` 之一 |
| `asset.uselist` | 领用列表，`person_id` 缺省时查询当前登录人 |
| `asset.repaillist` | 报修列表，`person_id` 缺省时查询当前登录人 |
| `asset.purchaselist` | 采购申请列表，`person_id` 缺省时查询当前登录人；`purchaser` 为采购员 ID |

所有查询默认走版本门禁（见 `ziguanjia-agent-entry.md`）。

## 输入要点

字段以 `weaver-work-cli asset schema` 为准。常用筛选字段：

- `asset.list`：`asset_name`、`asset_number`、`stateid`（状态 ID）、`asset_type_browse`（类型 ID）、`location_browse`（地点 ID）、`admin_istrator`（管理人 ID）、`resourceid`（使用人 ID）、`page_no`、`page_size`
- `asset.detail`：`id`、`asset_number`、`asset_name`
- `asset.uselist` / `repaillist`：`person_id`（缺省当前登录人）、`page_no`、`page_size`
- `asset.purchaselist`：`person_id`、`purchaser`、`page_no`、`page_size`

`stateid` / `asset_type_browse` / `location_browse` 是浏览字段 ID，先通过 `asset.resolve.*` 按名称解析，不要把中文名称直接当字段值。

## 示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json asset run asset.list --input-json '{"page_size":10}'
weaver-work-cli --profile eteams --json asset run asset.detail --input-json '{"asset_number":"EXAMPLE_NUMBER"}'
weaver-work-cli --profile eteams --json asset run asset.uselist --input-json '{"page_size":5}'
weaver-work-cli --profile eteams --json asset run asset.purchaselist --input-json '{"purchaser":"EXAMPLE_PURCHASER_ID","page_size":5}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json asset run asset.list --input-json '{"page_size":10}'
weaver-work-cli --profile eteams --json asset run asset.detail --input-json '{"asset_number":"EXAMPLE_NUMBER"}'
weaver-work-cli --profile eteams --json asset run asset.uselist --input-json '{"page_size":5}'
weaver-work-cli --profile eteams --json asset run asset.purchaselist --input-json '{"purchaser":"EXAMPLE_PURCHASER_ID","page_size":5}'
```

## 返回

列表返回 `items`（数组）、`count`。详情返回 `items` 中命中的资产主表。分页时递增 `page_no`，保持筛选条件不变。

## 注意

- 空筛选条件直接省略，不要把空字符串传给字段；`page_size` 不传时按各 operation 默认（列表默认 10，个人列表默认 5）。
- 不要把中文状态 / 类型 / 地点名称直接作为 `stateid` / `asset_type_browse` / `location_browse` 的值，先走 `asset.resolve.*`。
- 门禁未通过时查询会直接返回版本门禁错误，此时不要重试业务查询。
- **查看详情链接**：`list` / `detail` / `uselist` / `repaillist` / `purchaselist` 默认（`with_view_link:true`）为每条记录附带 `view_link` 字段（卡片链接 `/sp/ebdfpage/card/0/{表单ID}/{数据ID}`，表单ID 经两步 tag 接口实时解析）；传 `with_view_link:false` 可关闭。链接解析失败只会在返回里带 `view_link_warning`，不影响主查询结果，不要因此重试查询。
- `status` 字段是**字符串** `"true"` / `"false"`（不是布尔）；为 `"false"` 表示查询失败，不能当成「无结果」。
- 人员名称需先经 `weaver-e10-hrm-connector` 解析为人员 ID 再传入 `person_id`；不要把姓名直接当 ID。查「我」的列表（uselist / repaillist / purchaselist）省略 `person_id` 即可，CLI 自动用当前登录人。
- 列表返回的 `stateid` / `asset_type_browse` / `location_browse` 可能是 ID；回报用户前按 `asset.resolve.*` 反查为名称展示，不要暴露原始 ID。
