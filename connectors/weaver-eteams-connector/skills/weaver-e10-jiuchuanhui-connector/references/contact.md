# 联系人管理（contact）

## 何时使用

用户表达联系人相关意图：新建联系人、联系人详情、修改联系人、按客户或商机查询联系人。

## 可用 operation

| Operation | 风险 | 输入要点 |
|---|---|---|
| `jiuchuanhui.contact.create.prepare/apply` | 高风险写 | `form`: `{mainTable, detail1?, ...}`；联系人随客户创建（客户 `detail2`）时勿重复调用 |
| `jiuchuanhui.contact.get` | 只读 | `id` |
| `jiuchuanhui.contact.update.prepare/apply` | 高风险写 | `form`：主表修改，按配置 `data_key` 组装 |
| `jiuchuanhui.contact.by-entity.search` | 只读 | 按 `customerId` 或 `saleChanceId`（URL Query 传递，至少传一个），支持分页；body 的 `mainTable` 必传空对象 `{}` |

## 输入要点

- 创建/修改前读缓存 `config/contact_create_api.json`（或 `contact_update_api.json`）的 `detail.mainFields`（`detail.detailFields` 在联系人无明细表时仅组装主表）；只使用 `isInput:"1"` 字段，按 `data_key` 组装。
- `contact_name`（姓名）必填；`customer`（所属客户）与 `salechance`（所属商机）**二选一必填**（至少传一个归属），`rel_sales` 可多选（逗号分隔）。
- 只给联系人姓名未指明所属事项时，先 `contact.by-entity.search` 或搜索候选并让用户选择，不要猜归属。
- 关联字段传选项/事项 ID（RelateBrowser 通过 `browser-option.search` 查自定义浏览选项）。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact.by-entity.search --input-json '{"customerId":"100001","pageNo":1,"pageSize":10}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact.get --input-json '{"id":"300001"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact.create.prepare --input-json '{"form":{"mainTable":{"contact_name":"王五","position":"采购经理"}}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact.create.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact.by-entity.search --input-json '{"customerId":"100001","pageNo":1,"pageSize":10}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact.get --input-json '{"id":"300001"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact.create.prepare --input-json '{"form":{"mainTable":{"contact_name":"王五","position":"采购经理"}}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.contact.create.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

## 输出处理

- 创建成功返回 `datajson.dataIds`；`by-entity.search` 返回联系人列表。
- 联系人名称渲染为可点击链接，`objId` 取缓存 `discovery["objId:uf_jch_contact"]`。

## 注意

- 客户创建时通过 `detail2` 提交的联系人会同步写入联系人模块，不要再调用 `contact.create`。
- 写操作必须展示摘要并取得用户确认。

## 失败处理

- 参数缺失/不支持：说明具体问题并停止。
- `partial/write_uncertain`：停止重试，补一次 `contact.get` 回查。
