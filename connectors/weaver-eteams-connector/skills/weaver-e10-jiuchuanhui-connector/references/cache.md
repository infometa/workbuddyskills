# 缓存说明（cache）

缓存保存应用发现、接口配置、字段选项、关联数据和行政区划，按租户和人员隔离。缓存无 TTL：文件存在即命中，刷新时覆盖写入。

## 何时使用

首次使用、缓存缺失、用户要求刷新或重新加载、需要版本/配置/选项/objId 时，先读本文件，再按需运行初始化脚本。

## 文件位置

| 文件 | 内容 |
|---|---|
| `~/.weaver-e10-jiuchuanhui-connector/{tenantKey}/{userId}/weaver-e10-jiuchuanhui-connector.json` | 主缓存：`discovery`、`ebuilder`、`options`、`region` |
| `~/.weaver-e10-jiuchuanhui-connector/{tenantKey}/{userId}/config/{pk}.json` | 单接口配置：创建/更新类 `{cfgId,objId,detail}`，搜索类 `{cfgId,objId,searchParams}` |

`tenantKey`、`userId`、`baseUrl` 和认证头均由 `weaver-work-cli auth` 提供。缓存文件是 Agent 本地状态，不随 Skill 打包、不入库。

## 主缓存结构

```json
{
  "discovery": {},
  "ebuilder": {},
  "options": {},
  "region": {}
}
```

| 命名空间 | 内容 | 典型 key |
|---|---|---|
| `discovery` | 应用、表单对象、版本校验 | `appId:jch-crm-project`、`objId:uf_jch_customer`、`spVersion:jch-crm-project` |
| `ebuilder` | Ebuilder 关联数据 | `customer_type`、`customer_status`、`sale_stage` |
| `options` | Select/RadioBox/CheckBox 选项 | `options:{fieldId}:*:1` |
| `region` | 行政区划全路径 ID | `administrativeDivision:{name}` |

接口配置的 `cfgId` 存在对应 `config/{pk}.json` 中，业务按 `pk` 读取；主缓存不保存单独的 cfgId 索引。

## 初始化常量

| 常量 | 值 |
|---|---|
| 应用标签 | `jch-crm-project` |
| 模块表单标签 | `uf_jch_customer`、`uf_jch_sale`、`uf_jch_clue`、`uf_jch_contact`、`uf_jch_customer_open_sea`、`uf_jch_remind`、`uf_jch_rival`、`uf_jch_sale_process`、`uf_jch_sale_stage`、`uf_jch_clue_pool`、`uf_jch_lose_reason`、`uf_jch_customer_cmt`、`uf_jch_sale_cmt` |
| 创建类 pk | `customer_create_api`、`sale_create_api`、`ebclue_ai_create_api`、`contact_create_api`、`ebcontact_plan_create_api` |
| 搜索类 pk | `ebcustomer_search_api`、`ebsale_search_api`、`ebclue_ai_search_api` |
| 更新类 pk | `customer_update_api`、`sale_update_api`、`ebclue_ai_update_api`、`contact_update_api` |
| `interface_pk` 转 `cfgId` | `4F6E1A9702864666803CCA6B77B86227` |
| 字段 ID 转 `data_key` | `10351A4DC8D4454A9F1957FBE647CD9F` |
| 行政区划查询 | `7EC1639D5AC24B4DBCEE8D2CB85D4025` |
| 行政区划预取城市 | 成都市 |
| Ebuilder 分页大小 | `pageSize=500` |
| 选项层级 | `optionLevel=1` |
| 版本基线 | `>= 1.5.11` |

## 初始化/刷新

**调用 CLI operation `jiuchuanhui.cache.init` 执行完整初始化**（`weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.cache.init`），或在仓库根运行 `node src/shortcuts/jiuchuanhui/scripts/cache-init.mjs`（薄包装，转发同一 operation）。依赖有效 E10 登录态。支持 `dryRun`（只拉取不写入）/ `verbose`。用户要求初始化、刷新或重新加载缓存时，覆盖旧缓存。返回摘要含各命名空间条目数、objId/cfgId 计数、版本校验结果（`spVersion`，version.passed=false 时应停止业务调用）。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.cache.init --input-json '{}'            # 完整初始化
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.cache.init --input-json '{"dryRun":true}'  # 只拉取不写入
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.cache.init --input-json '{"verbose":true}' # 打印步骤明细
node src/shortcuts/jiuchuanhui/scripts/cache-init.mjs            # 薄包装（等价完整初始化）
node src/shortcuts/jiuchuanhui/scripts/cache-init.mjs --dry-run  # 只拉取不写入
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.cache.init --input-json '{}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.cache.init --input-json '{"dryRun":true}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.cache.init --input-json '{"verbose":true}'
node src/shortcuts/jiuchuanhui/scripts/cache-init.mjs
node src/shortcuts/jiuchuanhui/scripts/cache-init.mjs --dry-run
```

初始化流程（operation 内 7 步，复用 CLI 的 E10 认证链直连接口）：

1. **发现接口**：`jiuchuanhui.app.discovery`（`tag=jch-crm-project`）取 `data[0]` 为 `appId`；对 13 个模块表单标签调 `jiuchuanhui.form.discovery`，优先取 `formId` 非空且非 `"0"` 的记录 `id` 为 `objId`，否则回退 `data[0]`；读取 `spVersion`（`commitVersion`+`passed`），版本必须 `>= 1.5.11`，否则停止业务调用。
2. **获取 cfgId**：对 12 个 pk 调 `jiuchuanhui.config.id.by.pk`（`mainTable.interface_pk`），取 `mainTable.cfgId`。**该接口走 ESB 动作流，必须 POST JSON body + `uniqueIndent=4F6E1A9702864666803CCA6B77B86227`**；若以 GET query 调用会返回 HTTP 405。
3. **创建/更新接口配置**：对 5 个创建类 pk 和 4 个更新类 pk 调 `jiuchuanhui.rest.cfg.detail`（`apid={appId}&id={cfgId}`）；仅保留 `isInput=1` 的 `mainFields` 和 `detailFields[].fields`，空明细组丢弃；收集 `fieldid` 调 `jiuchuanhui.field.info.by-ids` 合并 `data_key`、`title`、`component_type`；注入对应表单 `objId`；精简存储（`detail` 顶层仅保留 `id`、`interfacePk`、`interfaceName`、`datasNumber`、`datasSize`、`mainFields`、`detailFields`、`interfaceType`、`relevanceForm`；字段元素仅保留 `fieldid`、`isRequired`、`isInput`、`data_key`、`title`、`component_type`）。写入 `config/{pk}.json`。
4. **Ebuilder 关联数据**：对 8 类选项（客户公海、商机阶段、销售过程、线索池、输单原因、客户行业、客户类型、客户状态）调对应搜索 operation（`customer.open-sea.search` / `sale.stage.search` / `sale.process.search` / `clue.pool.search` / `sale.lose-reason.search` / `customer.industry.search` / `customer.type.search` / `customer.status.search`），归一化为 `{id,name}` 写入 `ebuilder`；商机阶段额外带 `sale_process`。
5. **字段选项**：对 `config/{pk}.json` 中 `component_type` 为 `Select`/`RadioBox`/`CheckBox` 的字段调 `jiuchuanhui.field.options`（`fieldName`+`objId`+`groupId`），写入 `options.options:{fieldId}:*:1 = {lable,lableTitle,value}`，并按 `fieldid` 把 `value` 复制到相关 `config/{pk}.json` 字段的 `optionList`。失败不阻塞：保留旧缓存 `options`，业务侧可读字段 `optionList` 或主缓存 `options` 兜底。
6. **搜索参数**：对 3 个搜索类 pk 调 `jiuchuanhui.rest.cfg.detail`，解析 `conditions.datas[]` 的 `{param}` 提取 URL 参数 key，组装 `{key,text,fieldType,compType,func,fieldid}` 写入 `config/{pk}.json.searchParams`。
7. **行政区划**：预取 22 个常用城市（北京市、上海市、天津市、重庆市、成都市、广州市、深圳市、东莞市、杭州市、南京市、苏州市、武汉市、长沙市、西安市、郑州市、济南市、青岛市、厦门市、福州市、合肥市、沈阳市、大连市），通过 ESB 动作流（`uniqueIndent=7EC1639D5AC24B4DBCEE8D2CB85D4025`、`moduleType=administrativeDivision`、`name=城市名`、`fromType=agentSkill`）查询，`resultCode===200` 才写入 `region.administrativeDivision:{name}`；单城失败跳过，保留旧缓存 `region`。

## 读取规则

- 创建/更新接口直接读 `config/{pk}.json.detail`，用字段 `data_key` 组装 `mainTable` 和明细数组。
- 搜索接口直接读 `config/{pk}.json.searchParams`，不得使用未定义的搜索 key。
- Select/RadioBox/CheckBox 优先读字段 `optionList`（缺失时读主缓存 `options.options:{fieldId}:*:1`）。
- Ebuilder 关联字段读 `ebuilder` 命名空间。
- 行政区划读 `region`；运行时查询到的新行政区划可覆盖写入。
- 缓存为空、主文件或接口级文件缺失时，执行初始化或单项刷新，再继续业务调用。

## 刷新规则

| 方式 | 场景 | 处理 |
|---|---|---|
| 全量刷新 | 用户要求初始化、刷新、重新加载缓存 | 重新调用 `jiuchuanhui.cache.init`（或 `node src/shortcuts/jiuchuanhui/scripts/cache-init.mjs`），覆盖主缓存和接口级配置 |
| 单项刷新 | 某接口、字段、选项或行政区划缺失/变更 | 只重新查询对应 CLI operation 并覆盖对应 key 或 `config/{pk}.json` |

## 失败处理

- 版本校验 `< 1.5.11`：停止业务调用并告知用户。
- `jiuchuanhui.config.id.by.pk` 返回 HTTP 405：确认以 POST + JSON body 调用（EsbReadOperation），不要用 GET query 方式调用该 ESB 动作流。
- `jiuchuanhui.field.options` 返回 HTTP 400：已知问题（GetQueryOperation 未注入 `sourceType=FORM` 时可能 400）；保留旧缓存 options，业务侧用字段 `optionList` / 主缓存 `options` 兜底。
- 缓存缺失：先调用 `jiuchuanhui.cache.init` 完成初始化，再继续业务调用。
