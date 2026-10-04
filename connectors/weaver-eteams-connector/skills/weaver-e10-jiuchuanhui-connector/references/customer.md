# 客户管理（customer）

## 何时使用

用户表达客户相关意图：新建客户、客户详情、搜索客户、修改客户、转移客户、客户查重、公海搜索/领取/释放、客户联系记录、批量联系记录、客户状态/类型/行业查询。

## 可用 operation

| Operation | 风险 | 输入要点 |
|---|---|---|
| `jiuchuanhui.customer.create.prepare/apply` | 高风险写 | `form`: `{mainTable, detail1?, detail2?, ...}`；`detail2` 提交后同步创建联系人，勿再调 `contact.create` |
| `jiuchuanhui.customer.get` | 只读 | `id` |
| `jiuchuanhui.customer.search` | 只读 | 搜索条件走 query；**必须显式传 `mine`/`all`/`customerSea`**（一个 `""` 其余 `-1`，默认 `mine=""`）；分页 `pageNo`/`pageSize`；`count:true` 并行取总数 |
| `jiuchuanhui.customer.type/status/industry.search` | 只读 | 分页字段，用于取选项 ID |
| `jiuchuanhui.customer.open-sea.search` | 只读 | 公海客户列表，条件走 query |
| `jiuchuanhui.customer.update.prepare/apply` | 高风险写 | `form`：主表+明细修改，按配置 `data_key` 组装 |
| `jiuchuanhui.customer.transfer.prepare/apply` | 高风险写 | `customerId`（必填）、`employee_MappingId`（目标人员 ID，优先）或 `employeeName`（人员名称），二者至少传一个；动作流 `uniqueIndent` 与触发人 `employeeId` 由 CLI 固定注入 |
| `jiuchuanhui.customer.open-sea.release.prepare/apply` | 高风险写 | `customerId`、`openSeaId`（均必填，缺一不可）；释放影响需用户确认；动作流 `uniqueIndent` 与触发人 `employeeId` 由 CLI 固定注入 |
| `jiuchuanhui.customer.open-sea.claim.prepare/apply` | 高风险写 | `customer_id`（注意下划线命名） |
| `jiuchuanhui.customer.duplicate.check` | 只读 | `mainTable.name`（原始名称）、`mainTable.simpleName`（归一化简称，均必填），动作流 `uniqueIndent=D5D0A1C30E7B404B842987C0AD3B749D` |
| `jiuchuanhui.customer.contact-record.create.prepare/apply` | 高风险写 | `customerId`、`comment_content`（必填）；可选 `type`/`rating`/`contact_information`/`contacts`/`next_time`/`next_content`/`next_contact_information`/`next_contacts`/`sync_salechance`/`rel_remind`。`type` 为**评论类型**（销售记录/外勤记录/系统记录/客服记录等），与商机联系记录的 `type`（联系类型）**取值体系不同，勿混用** |
| `jiuchuanhui.customer.contact-record.batch.prepare/apply` | 高风险写 | `entityList`（客户 ID 数组，一次最多 20 个）、`content`（统一联系内容，必填）；批量部分成功需人工核对 |

## 输入要点

- 创建/修改前先读缓存 `config/customer_create_api.json`（或 `customer_update_api.json`）的 `detail.mainFields`/`detail.detailFields`；只使用 `isInput:"1"` 字段，按 `data_key` 组装，`isRequired:"1"` 缺失时追问，禁止占位值。
- `manager`（客户经理）必填，默认当前操作人；`id` 由系统生成，**请求体不携带 `id`**。
- **修改（update）局部更新**：只传需要修改的字段（含 `id` 定位记录），未传入字段保持原值。以下系统字段**不可更新**（传了会被忽略）：`id`、`operator`、`creator`、`create_time`、`update_time`、`updater`、`data_status`、`customer_number`。
- **转移/释放公海权限不足返回 HTTP 204**：提示用户无对应权限，联系管理员；不可误报为"操作失败"。
- Select/RadioBox/CheckBox 字段传选项 ID（读字段 `optionList`）；Employee/RelateBrowser 字段传人员/事项 ID。
- 行政区划 `country`/`province`/`city`/`district` 传逗号分隔全路径 ID；传细粒度自动填充粗粒度。
- 搜索无 `scope` 快捷参数，`mine`/`all`/`customerSea` 三选一置空；日期范围用 `*_gt`/`*_lt` 字段；人员字段传人员 ID（如 `managerid`）。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.duplicate.check --input-json '{"mainTable":{"name":"示例科技有限公司","simpleName":"示例科技"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.create.prepare --input-json '{"form":{"mainTable":{"manager":"USER_ID","customer_name":"示例科技有限公司"}}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.create.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.search --input-json '{"customer_name":"小康","mine":"","all":"-1","customerSea":"-1","pageNo":1,"pageSize":10,"count":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.duplicate.check --input-json '{"mainTable":{"name":"示例科技有限公司","simpleName":"示例科技"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.create.prepare --input-json '{"form":{"mainTable":{"manager":"USER_ID","customer_name":"示例科技有限公司"}}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.create.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.search --input-json '{"customer_name":"小康","mine":"","all":"-1","customerSea":"-1","pageNo":1,"pageSize":10,"count":true}'
```

## 输出处理

- 创建成功返回 `datajson.dataIds`（ID 列表）与 `status`；搜索返回 `datajson.datas` 数组。
- 列表默认只取第一页 `pageNo=1`、`pageSize=10`；只有用户要求翻页才继续。
- 客户名称渲染为可点击链接 `https://{baseUrl}/sp/ebdfpage/card/0/{objId}/{dataId}`，`objId` 取缓存 `discovery["objId:uf_jch_customer"]`。

## 注意

- 新建客户前**必须先查重**；存在疑似重复时表格展示让用户确认；若客户在公海，提醒可领取并让用户确认。
- `detail2` 会同步创建联系人，不要重复调用 `contact.create`。
- 释放公海、转移客户前必须确认客户唯一并提示影响。

## 失败处理

- 参数缺失/不支持：说明具体问题并停止，不猜测、不替换、不重试。
- `partial/write_uncertain`：停止重试，补一次 `customer.get` 只读回查，给用户明确结论。
