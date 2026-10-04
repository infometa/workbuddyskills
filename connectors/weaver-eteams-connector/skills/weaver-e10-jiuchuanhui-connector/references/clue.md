# 线索管理（clue）

## 何时使用

用户表达线索相关意图：新建线索、线索详情、搜索线索、修改线索、线索状态变更（放弃/分配/转移/有效/无效）、新建线索跟进记录、线索转已有客户、线索池搜索。

## 可用 operation

| Operation | 风险 | 输入要点 |
|---|---|---|
| `jiuchuanhui.clue.create.prepare/apply` | 高风险写 | `form`: `{mainTable, detail1?, ...}` |
| `jiuchuanhui.clue.get` | 只读 | `id` |
| `jiuchuanhui.clue.search` | 只读 | 搜索条件走 query，`count:true` 并行取总数 |
| `jiuchuanhui.clue.pool.search` | 只读 | 线索池列表 |
| `jiuchuanhui.clue.update.prepare/apply` | 高风险写 | `form`：主表修改 |
| `jiuchuanhui.clue.status-change.prepare/apply` | 高风险写 | `clueid`（注意小写）、`type`（必须传数字 1/2/3/4，不可中文）；`type=1`放弃时必填 `desc`，`type=2`分配/转移时必填 `newmanager`，`type=4`无效时必填 `desc`；`type=2` 靠线索有无负责人区分意图 |
| `jiuchuanhui.clue.to-customer.prepare/apply` | 高风险写 | `clueId`、`customerId`（转已有客户） |
| `jiuchuanhui.clue.contact-record.create.prepare/apply` | 高风险写 | `clueId`（必填）、`content`、`clueStatus_MappingId`（必填，未传时按 `content` 自动判断：`3`=有效、`4`=无效；显式传入时优先用传入值） |

## 输入要点

- 创建/修改前读缓存 `config/ebclue_ai_create_api.json`（或 `ebclue_ai_update_api.json`）的 `detail.mainFields`（与 `detail.detailFields`），按 `data_key` 组装，`isRequired:"1"` 缺失时追问。
- 线索创建 `clue_pool`（线索池）为**必填**，需传线索池数据 ID（可由 `clue.pool.search` 获取）；`id` 由系统生成，请求体不携带。
- 线索行政区划字段使用 `standard_` 前缀（`standard_country`/`standard_province`/`standard_city`/`standard_district`），传全路径 ID 自动填充粗粒度；而线索搜索的行政区划传参 key 为 `country`/`province`/`city`/`district`（无前缀），两者角色不同勿混用。
- 状态变更 `type` **必须用数字 1/2/3/4**（不可中文，非缓存选项）：`1`=放弃（必填 `desc`）| `2`=分配或转移（必填 `newmanager`，有无负责人区分意图）| `3`=恢复有效 | `4`=无效（必填 `desc`）。先确认线索唯一、目标状态/人员明确，再 prepare -> 用户确认 -> apply。
- 线索转客户：用户指定转已有客户 -> `clue.to-customer`；转新客户 -> 走 `customer.create` 且传 `source_module_id=<clueId>`，成功后不要额外修改线索。
- 创建类型记录时根据联系记录内容自动判断线索状态（有效或无效）。
## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.clue.search --input-json '{"clue_name":"示例","pageNo":1,"pageSize":10,"count":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.clue.get --input-json '{"id":"500001"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.clue.status-change.prepare --input-json '{"mainTable":{"clueid":"500001","type":"2","newmanager":"USER_ID"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.clue.status-change.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.clue.to-customer.prepare --input-json '{"mainTable":{"clueId":"500001","customerId":"100001"}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.clue.search --input-json '{"clue_name":"示例","pageNo":1,"pageSize":10,"count":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.clue.get --input-json '{"id":"500001"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.clue.status-change.prepare --input-json '{"mainTable":{"clueid":"500001","type":"2","newmanager":"USER_ID"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.clue.status-change.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.clue.to-customer.prepare --input-json '{"mainTable":{"clueId":"500001","customerId":"100001"}}'
```

## 输出处理

- 创建成功返回 `datajson.dataIds`；状态变更成功以 `resultCode===200` 为标志，不额外验证。
- 线索名称渲染为可点击链接，`objId` 取缓存 `discovery["objId:uf_jch_clue"]`。

## 注意

- 线索状态变更覆盖放弃、分配、转移、有效、无效等动作；写入前必须让用户确认目标状态与人员。
- 转新客户成功后不要再调用线索修改接口。

## 失败处理

- 参数缺失/不支持：说明具体问题并停止。
- `partial/write_uncertain`：停止重试，补一次 `clue.get` 回查。
