---
name: jingbei-business
description: Use when a user asks about Jingbei (经贝管家) goods and inventory — product search by name/code with prices and per-warehouse availability, and real-time stock checks for specific product×warehouse pairs. Covers inventory inquiry scenarios such as "这商品还有多少库存"、"哪些商品快缺货了"、"这个商品够不够卖 N 台". This connector exposes Jingbei's inventory data; other Jingbei capabilities (经营账/费用/预算/应收/单据) are not open yet.
version: "1.2.0"
author: "经贝数字科技"
capabilities:
  tools:
    - jingbei_company_list
    - jingbei_goods_search
    - jingbei_stock_check
    - jingbei_discover
    - jingbei_invoke
tags:
  - 进销存
  - 库存
  - 商品
  - 查询
---

# 经贝管家 Skill

经贝管家是业财一体化 SaaS 平台（覆盖经营账、财务账、费控预算、进销存等）。

**本连接器当前开放的只有「商品 + 库存」的只读查询 —— 即经贝管家的进销存数据（实时）。**
品牌是经贝，能力面是进销存；其余能力（经营账/报表、费用报销、预算、应收账龄、单据、开单）尚未开放。

> 注意措辞：用户问"经贝能做什么"时，说**当前开放的是商品与库存查询**，
> 不要因为品牌叫"经贝"就暗示能做财务/预算 —— 那会误导，也会让审核与用户预期落空。

## 能力边界（重要，务必遵守）

可以做：

- 列出当前已授权的机构（公司主体）
- 按名称/编码搜索商品，返回售价、规格、分类、单位，以及**各仓库的实时可用量**
- 查询指定「商品 × 仓库」的库存、占用与可用量，并判断某数量是否够卖

**不能做**（尚未开放，没有对应工具）：经营账/报表、费用报销、预算、应收账款账龄、单据查询与开单、采购销售单据的创建。

遇到超出边界的提问时：**直接说明当前连接器只支持商品与库存查询**，并建议用户在经贝管家客户端里查看；**不得**用现有工具拼凑或用经验数字冒充答案。示例话术：

> 我目前只能查商品和库存（经贝连接器当前开放的能力范围）。经营账/预算/应收/开单这类问题需要到经贝管家系统里看，我这边帮不上，抱歉。

**只读**：本连接器不会创建或修改任何单据，不要向用户承诺"帮你开单/改单"。

## 使用原则

- 所有工具返回统一外壳 `{ code, message, requestId, data }`。**仅当 `code` 为 `0` 时使用 `data`**；失败时把 `message` 转述给用户，必要时附 `requestId` 便于排查。
- **机构（`company_id`）是数据边界**：取值来自 `jingbei_company_list` 返回的 **`company_id`（机构对外编码）**。
  注意分层——**一个合作方（如校管家）下可以有多个机构**（快乐学、邦德华纳…），它们共用一个连接；`appId` 只是归属，**不要把它当机构用**。
  `company_id` **是可选参数**，省略时服务端按"默认机构"查询。
  用户授权时勾了哪几个机构，就**只能**看到/查询哪几个——勾选之外的机构（哪怕同属一个合作方）会被服务端拒绝，不要尝试。
  - 只有 1 个机构：省略即可，不必追问。
  - 用户**明确说了机构**（"快乐学的库存"）：直接传对应的 `company_id`，不必问、也不必先列机构。
  - 多机构 + 用户**没指明** + **本会话还没定过**当前机构：**先列出机构让用户选一次**（展示 `institution`），选完作为本会话默认；后续沿用，**不要每个问题都问**。
  - 用户中途说"那 X 呢 / 切换到 X"：直接换该机构，不要再确认。
  - 用户要"两家都看"：**逐机构分别回答，每段标注机构名**；不要合并成一条（口径会乱），也不要用别的机构的结果顶替。
- **结果首行是机构信息**：`goods_search` / `stock_check` 的返回文本第一行形如
  `【机构】快乐学（编码 184198）`（若因未指定而用了默认机构，会追加"，未指定机构时用的默认机构"），
  第二行起才是业务 JSON。回答时**必须带上机构名**，让用户看得出这条数据属于哪家。
- **编码不要猜**。商品、仓库都必须先用 `jingbei_goods_search` 拿到 `productExternalId` / `warehouseExternalId`（后者在返回的 `data.items[].warehouses[]` 里），再用于 `jingbei_stock_check`。
- 金额是**含税售价**；注意 `uomName`（单位，如「台」）。不同仓库的可用量分别看，不要相加成"总库存"回答，除非用户明确要汇总。
- 用户只给机构名、没给 `company_id` 时，先 `jingbei_company_list`；机构名匹配不到就如实说没有该机构，不要用近似机构代替。

## 工具目录（3 个具名 + 2 个元工具）

### 1. jingbei_company_list — 列出已授权机构

**参数**：无。

**返回**：`{ total, companies: [{ appId, partnerName, institution, outCompanyId }], note }`
**其他工具的 `company_id` 就取这里的 `company_id`**（不是 `appId`，`appId` 只是它归属的合作方）；
`defaultCompanyId` 是省略 `company_id` 时用的默认机构。

**示例（实测）**

```json
{"total":2,
 "companies":[{"appId":"ccd9f61104c0401ea1ef","partnerName":"校管家","institution":"快乐学",
               "outCompanyId":"02F7FF5C-926B-4A97-A903-F7026BBDE3C6"},
              {"appId":"a1b2c3d4e5f60718293a","partnerName":"校管家","institution":"邦德华纳",
               "outCompanyId":"77A1B2C3-4D5E-6F70-8192-A3B4C5D6E7F8"}],
 "defaultCompanyId":"ccd9f61104c0401ea1ef",
 "note":"company_id 只能取以上 appId 范围内的值；省略该参数时按 defaultCompanyId 查询…"}
```

若某机构未配置 `outCompanyId`，查询会被拒绝并提示"未配置机构对外ID"——此时向用户说明该机构尚未在经贝侧完成机构编码配置。

### 2. jingbei_goods_search — 商品搜索（含各仓可用量）

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| `company_id` | string | 否 | 机构对外编码，取 `jingbei_company_list` 的 `company_id`；**省略则用默认机构**（要查的不是默认那家时必须显式传） |
| `keyword` | string | 否 | 商品编码/名称模糊匹配，如「电脑」「无人机」；省略则分页列出全部 |
| `pageNum` | integer | 否 | 页码，从 1 起（默认 1） |
| `pageSize` | integer | 否 | 每页条数（默认 20） |

**返回** `data`：`{ total, items[] }`，`items[]` 每项含：

`productExternalId`（供库存查询用）、`code`、`name`、`spec`、`salePrice`、`uomExternalId`/`uomName`、`categoryExternalId`/`categoryName`、`status`（1 启用 / 0 停用），以及 `warehouses[]`：

`warehouseExternalId`（供库存查询用）、`warehouseName`、`uomExternalId`/`uomName`、`purchasePrice`、`available`（该仓可用量）。

**示例（实测节选）**

```json
{"code":0,"message":"success","data":{"total":"4","items":[
 {"productExternalId":"2095803326567088130","code":"5","name":"电脑","spec":"",
  "salePrice":8050.0,"uomName":"台","categoryName":"电脑","status":1,
  "warehouses":[{"warehouseExternalId":"2074691215658004482","warehouseName":"洋湖仓库",
                 "uomName":"台","purchasePrice":8050.0,"available":1.0}]}]}}
```

### 3. jingbei_stock_check — 库存与"够不够卖"判定

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| `company_id` | string | 否 | 机构对外编码，取 `jingbei_company_list` 的 `company_id`；**省略则用默认机构** |
| `items` | array | 是 | 查询项列表，见下 |
| `items[].productExternalId` | string | 是 | 来自 `jingbei_goods_search` |
| `items[].warehouseExternalId` | string | 是 | 来自 `jingbei_goods_search` 的 `warehouses[]` |
| `items[].qty` | number | 是 | 想判断是否够用的数量 |

**返回** `data.items[]`：`productExternalId`、`warehouseExternalId`、`stock`（账面）、`reservedQty`（占用）、`available`（可用）、`enough`（`available >= qty` 时为 `true`）。

**示例（实测节选）**

```json
{"code":0,"data":{"items":[
 {"productExternalId":"2095383799228334082","warehouseExternalId":"2074691160163168257",
  "stock":13.0,"reservedQty":0.0,"available":13.0,"enough":false}]}}
```

回答"够不够"时**必须引用 `enough`**，并把 `available` 与用户要的数量一起说清楚；`enough=false` 时给出可用量差额。

### 4. jingbei_discover — 搜索可用接口（元工具）

长尾只读查询优先用它，而不是等新工具上线。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| `keyword` | string | 否 | 业务关键词，如「库存」「分类」「仓库」 |
| `readOnlyOnly` | boolean | 否 | 默认 `true`（只看只读接口） |
| `limit` | integer | 否 | 返回条数上限，默认 10，最大 50 |

**返回** `items[]`：`apiCode`、`apiName`、`bizDesc`、`readOnly`、`params[]`（字段名/类型/必填/说明）。
只返回**该连接已授权**的接口。

### 5. jingbei_invoke — 按 apiCode 调用（元工具）

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| `apiCode` | string | 是 | 来自 `jingbei_discover` |
| `params` | object | 否 | 业务参数；**不要传 `outCompanyId`/`companyId`**（机构由服务端注入） |
| `requestId` | string | 否 | 幂等键（只读可省） |
| `company_id` | string | 否 | 机构；省略用默认机构 |

**三条硬约束**（服务端强制，不是提示词约定）：

1. 只能调用**该连接已授权**的接口，否则被拒；
2. 机构由服务端按当前授权**强制注入**——你传的 `outCompanyId` 一律被忽略，所以**不要试图用它换机构**；
3. **写操作类接口默认不开放**（`stock/deduct`、`sale/notify` 等会返回"只读模式"）。

## 推荐调用流程

| 用户意图 | 调用顺序 |
| --- | --- |
| 有哪些机构 / 能查哪个公司 | `jingbei_company_list` |
| 找商品 / 问价格 / 看规格 | `jingbei_company_list` → `jingbei_goods_search`（`keyword`） |
| 某商品还有多少库存 | `jingbei_company_list` → `jingbei_goods_search` → `jingbei_stock_check`（逐仓用 `warehouses[]`） |
| 这个商品够不够卖 N 台 | 同上，`qty = N`，引用 `enough` 回答 |
| 哪些商品快缺货了 | `jingbei_company_list` → `jingbei_goods_search`（放大 `pageSize`）→ 把各仓 `available` 偏低的列出来；**没有"安全库存线"数据，不要编造阈值**，请用户给判定标准 |
| 跨仓库比一比 | 对同一 `productExternalId` 的各仓库分别看 `available`，逐仓列出 |
| 具名工具覆盖不到、但已授权的只读查询 | `jingbei_discover`（找接口）→ `jingbei_invoke`（带 `apiCode` 与 `params`） |
| 具名工具与 discover 都覆盖不到（财务/预算/应收/开单…） | 按"能力边界"直接说明不支持，不要硬凑；写操作类接口默认未开放 |

## 错误处理

| 现象 | 处理 |
| --- | --- |
| `code != 0` | 把 `message` 转述用户；反复失败时附 `requestId` |
| `company_id 未授权（Token 授权范围外的机构），已拒绝访问` | 说明该机构不在本次授权范围内（错误信息里会列出可选机构），提示用户重新授权并勾选该机构 |
| 结果首行机构不是用户指的那家 | 你可能漏传 `company_id`（走了默认机构） | 用用户指定的机构重新调用，并在回答里明确机构名 |
| `写操作类接口未开放（当前为只读模式）` | 首版 invoke 不放行写接口 | 如实告知用户该操作暂不可用，不要换个 apiCode 重试 |
| `App 未授权接口 xxx` | 该接口不在本连接授权范围 | 如实说明需平台运营授权，不要改用别的接口顶替 |
| `App xxx 未配置机构对外ID(out_company_id)` | 该机构未完成机构编码配置，属经贝侧运营待补录 |
| 返回 `2001`（机构映射为空） | 该机构在经贝侧未建立外部机构映射，属配置问题，转述给用户 |
| 空结果但 `code=0` | 如实回答"没有匹配到"，不要用其它机构/其它关键字的结果替代 |
