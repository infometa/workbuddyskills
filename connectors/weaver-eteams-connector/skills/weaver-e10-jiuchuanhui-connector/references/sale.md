# 商机管理（sale）

## 何时使用

用户表达商机相关意图：新建商机、商机详情、搜索商机、修改商机、销售阶段/销售过程查询、商机转移/负责人变更、暂停、重启、赢单、输单、无效、关联联系人、商机联系记录、对手/友商查询、输单原因查询。

## 可用 operation

| Operation | 风险 | 输入要点 |
|---|---|---|
| `jiuchuanhui.sale.create.prepare/apply` | 高风险写 | `form`: `{mainTable, detail1?, ...}` |
| `jiuchuanhui.sale.get` | 只读 | `id` |
| `jiuchuanhui.sale.search` | 只读 | 搜索条件走 query，`count:true` 并行取总数 |
| `jiuchuanhui.sale.update.prepare/apply` | 高风险写 | `form`：主表修改 |
| `jiuchuanhui.sale.stage.search` / `sale.process.search` / `sale.lose-reason.search` | 只读 | 阶段/销售过程/输单原因选项，分页字段 |
| `jiuchuanhui.rival.search` | 只读 | 对手/友商列表 |
| `jiuchuanhui.sale.win.prepare/apply` | 高风险写 | `saleId`；赢单不可逆 |
| `jiuchuanhui.sale.lose.prepare/apply` | 高风险写 | `saleid`、`reasonids`（输单原因，**单选**，传一个原因 ID）；可选 `money`（单位为**元**）、`rivals`（对手 ID，**多选**逗号分隔）、`desc`；输单必须先确定原因 |
| `jiuchuanhui.sale.invalid.prepare/apply` | 高风险写 | `saleId`；无效不可逆 |
| `jiuchuanhui.sale.pause.prepare/apply` | 高风险写 | `saleId`、`pauseReason`（必填，暂停原因描述）；可选 `restartDate`（**预计重启日期**，格式 `yyyy-MM-dd`） |
| `jiuchuanhui.sale.restart.prepare/apply` | 高风险写 | `saleChanceId`（**仅可重启已暂停的商机**）；确认商机已暂停再操作 |
| `jiuchuanhui.sale.manager-change.prepare/apply` | 高风险写 | `saleChanceId`、`managerId`（目标负责人）；转移/负责人变更共用；**仅本人或本人下级商机可操作**，权限不足返回 HTTP 204 |
| `jiuchuanhui.sale.link-contacts.prepare/apply` | 高风险写 | `salechanceId`（注意小写 c）、`contactIds`；确认联系人与商机关联关系 |
| `jiuchuanhui.sale.contact-record.create.prepare/apply` | 高风险写 | `saleId`、`comment_content`（必填）；可选 `type`/`rating`/`contact_information`/`contacts`/`next_time`/`next_content`/`next_contact_information`/`next_contacts`/`rel_remind`。`type` 为**联系类型**（例行联系等，默认 `0`），与客户联系记录的 `type`（评论类型）**取值体系不同，勿混用** |

## 输入要点

- 创建/修改前读缓存 `config/sale_create_api.json`（或 `sale_update_api.json`）的 `detail.mainFields`（与 `detail.detailFields`，商机明细按需组装），按 `data_key` 组装，`isRequired:"1"` 缺失时追问。
- Select/RadioBox/CheckBox 传选项 ID；关联客户传 `customer`（客户数据 ID）；负责人传 `manager`（人员 ID）。
- 搜索商机：默认小页；需要总数时 `count:true` 与列表**并行**发起。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.search --input-json '{"sale_name":"示例","pageNo":1,"pageSize":10,"count":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.get --input-json '{"id":"200001"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.win.prepare --input-json '{"mainTable":{"saleId":"200001"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.win.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.lose.prepare --input-json '{"mainTable":{"saleid":"200001","reasonids":"400001"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.link-contacts.prepare --input-json '{"mainTable":{"salechanceId":"200001","contactIds":"300001,300002"}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.search --input-json '{"sale_name":"示例","pageNo":1,"pageSize":10,"count":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.get --input-json '{"id":"200001"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.win.prepare --input-json '{"mainTable":{"saleId":"200001"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.win.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.lose.prepare --input-json '{"mainTable":{"saleid":"200001","reasonids":"400001"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.sale.link-contacts.prepare --input-json '{"mainTable":{"salechanceId":"200001","contactIds":"300001,300002"}}'
```

## 输出处理

- 赢单/输单/无效等 ESB 操作以 `resultCode===200` 为成功标志，不额外发起查询验证。
- 商机名称渲染为可点击链接，`objId` 取缓存 `discovery["objId:uf_jch_sale"]`。

## 注意

- 赢单、输单、无效是高影响状态变更，执行前必须提示不可逆或关键影响。
- 输单要先确定输单原因（`sale.lose-reason.search` 取 ID）；暂停必须有暂停原因；重启需确认目标商机处于可重启状态。
- 商机转移和负责人变更共用 `sale.manager-change`。
- 关联联系人前要确认商机和联系人均唯一，且联系人属于该客户/商机关系链。
- 商机阶段推进（stage-advance）属于 Skill 编排层组合逻辑，不暴露为 CLI operation；可用 `sale.update` + `sale.stage.search` 组合实现。

## 失败处理

- 参数缺失/不支持：说明具体问题并停止。
- `partial/write_uncertain`：停止重试，补一次 `sale.get` 回查。
