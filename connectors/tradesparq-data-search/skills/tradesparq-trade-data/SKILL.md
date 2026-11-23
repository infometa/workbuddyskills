---
name: tradesparq-trade-data
description: 全球海关与提单贸易数据检索。用于查公司工商信息与贸易画像、按 HS 编码/国家/港口/交易伙伴做分组统计与趋势、下钻交易明细。触发场景：用户询问某家企业的进出口情况、某 HS 编码的进出口国排行、某国某商品进口趋势、买卖双方交易对手分析、海关提单明细查询。
---

# Tradesparq · Trade Data

基于全球海关提单数据的贸易事实检索服务。所有查询通过本连接器的 18 个 MCP Tool 完成。

## 何时使用

- 「XX 公司从中国出口到美国的量和买家有哪些」
- 「2025 年锂电池进口量 Top 10 国家」
- 「华为的供应商主要来自哪些国家」
- 「这个统一社会信用代码对应的公司信息」
- 「帮我查具体提单记录 / 成交明细」
- 「帮我找 XX 公司在数据里的 id / 这家公司在不在数据里」

## 认证

首次调用若提示未授权，直接告知用户需要在连接器面板完成授权（服务端走标准 OAuth 流程，打开浏览器登录即可），无需用户提供 Token。遇到 `401` / `unauthorized` 时，提示用户重新连接连接器后重试，不要反复重试。

---

## 核心概念：两类查询族

**A. 市场/全局查询**（不依赖公司 ID）——分析市场，也用于从贸易数据中查找公司
`search_record` / `search_stats_overview` / `search_stats_trend` / `search_stats_filter` / `search_stats_hs_code` / `search_stats_com` / `search_stats_others`

**B. 公司贸易查询**（指定 com_id/com_uid + com_role）——分析数据中的某个公司实体
`search_company_record` / `search_company_stats_overview` / `search_company_stats_partner` / `search_company_stats_partner_stats` / `search_company_stats_partner_growth` / `search_company_stats_trend` / `search_company_stats_filter` / `search_company_stats_hs_code` / `search_company_stats_others`

公司基本档案用 `company_info`，需要已有的 `com_id` 或 `com_uid`；中国工商登记用 `company_reg_cn`，可按中文名或统一社会信用代码查询，但不能据此假定已取得贸易数据中的公司 ID。

### 关键链路：先查贸易数据中的公司，再使用其 ID

**不能把用户给出的公司名直接换成 `com_id`。** 公司名只是检索与核对线索，必须先在贸易数据中找到实际公司实体，再使用查询结果明确返回的 `com_id` 或 `com_uid` 调用公司查询工具。不要编造、推算 ID，也不要把名称文本当作 ID。

| 用户给了什么 | 用哪个 Tool | 说明 |
|---|---|---|
| 只有公司名，想查贸易情况 | `search_stats_com`，必要时配合 `search_record` | 按时间、数据源、国家、商品等已知范围查询数据里的买家/供应商，核对实际公司名称与主体，再从结果中取得明确的公司 ID。名称过滤仅在工具支持且名称能匹配数据记录时使用，不保证任意语种名称都能命中 |
| 已有贸易查询返回的 `com_id` / `com_uid` | `company_info` / `search_company_*` | 保留 ID 来源及对应公司名称、角色，按工具实际参数使用 |
| 公司中文名，且只要工商信息（法人/注册资本/成立日期等） | `company_reg_cn` | 入参 `com_name`（纯中文，2–20 字）或 `xy_code`（18 位统一社会信用代码）。仅覆盖部分中国公司；工商主体与贸易数据中的公司实体需要另行核对 |

### 从数据定位公司的流程

1. 根据用户的问题确定时间、市场/数据源、商品和买家或供应商角色；缺少影响查询的关键条件时再询问。
2. 读取枚举资源，使用 `search_stats_com` 按 `buyer` 或 `supplier` 查询该范围内的公司；需要核对交易中的公司信息时，用 `search_record` 少量抽样。入参以当前工具定义为准。
3. 从实际返回的数据中核对公司名称，以及可用的国家、地址、交易角色等信息。用户提供的简称、中文名、品牌名或集团名不能直接视为数据中的同一法律主体；名称过滤应依据数据中的写法。
4. 只采用响应中明确标识为公司 ID 的值。若分组结果使用 `val` 等通用字段，必须先确认字段含义，不能直接认定它是 `com_id`。若当前结果只给公司名，没有公司 ID，可继续查相关交易记录；仍没有明确 ID 时，说明暂时无法进入公司级查询。
5. 唯一且明确匹配的实体可继续查询；多个候选存在歧义时，列出实际公司名称与匹配依据，让用户确认后再下钻。调用 `search_company_*` 时使用该实体的 ID 和对应的 `com_role`。

例如，用户要查「宁德时代向美国出口的主要买家」，先在对应时间与数据源的贸易数据中查找供应商，核对结果中哪些公司实体属于用户所指的企业，再使用这些记录明确返回的公司 ID 查询买家。不能仅凭「宁德时代」或自行翻译的英文名生成 ID。

**公司实体与名称变体：** 数据中可能存在不同写法、子公司或分支机构。保留各候选实体及其 ID，不因名称相似就自动合并，也不把第一条匹配当作整个集团。需要汇总多个主体时，先明确汇总范围并注意交易去重。

**查不到时：** 检查时间、数据源与贸易角色；根据已有线索调整国家/商品范围，查看数据里实际出现的公司名称。不要把中文名或自行翻译的名称零命中视为公司不存在，也不要反复调用假定的名称转 ID 接口。仅需中国工商信息时可独立使用 `company_reg_cn`。

### com_role 必须显式指定

每次调用 `search_company_*` 都需要 `com_role`：

- `buyer` ——该公司作为**采购商/进口商**查询；交易伙伴分析对应它的**供应商**。
- `supplier` ——该公司作为**供应商/出口商**查询；交易伙伴分析对应它的**采购商**。

角色应与定位该实体时的贸易记录及用户问题一致。信息不足时先用 A 族查询核对，仍有歧义再询问。`company_info` 和 `company_reg_cn` 按各自参数调用，不套用公司贸易查询的 `com_role` 要求。

---

## 通用参数规则（所有工具都适用）

### 硬性约束，违反会直接报错

1. **日期跨度 ≤ 3 年**。`date: ["20230101", "20260331"]` 合法，`["20180101","20260331"]` 非法。跨更长区间必须拆成多次查询后自行汇总。
2. **至少一个正向严格约束条件**。只传 `date` 会被拒绝。必须至少给一个过滤字段（如 `hs_code`、`buyer`、`supplier`、`prod_desc`、`data_source`、`orig_country_code` 等）。
3. **`***_excl` 排除参数不能单独使用**。若传 `hs_code_excl`，必须同时传对应的正向 `hs_code`。
4. 日期格式 `yyyyMMdd`，如 `["20250101", "20251231"]`，起始 ≤ 截止。

### source_type 数据集选择（重要）

- `1`（默认）—— 当前集，**2022 年及以后**
- `2` —— 历史集，**2022 年之前**

跨 2022 年的查询需要分别查两次。默认值是 1，不要臆造其他值。

### 数值范围参数

`weight` / `quantity` / `price` / `amount` / `teu` 格式统一为 `[min, max]`：
- `[100, 500]` 闭区间
- `[100, null]` 大于等于 100
- `[null, 500]` 小于等于 500
- 不能两端同时为 null，下限 ≤ 上限

### 文本类参数

`prod_desc` / `buyer` / `supplier` / 港口名 / 品牌等支持：
- 短语精确匹配：双引号包裹，如 `["\"ACME CORP\""]`
- 通配符：`?` 单字符，`*` 任意长度

不要把用户口语直接塞进去。如「锂电池」应转为 `prod_desc: ["lithium battery*"]`；「中国」应转为 `orig_country_code: ["CN"]`（国家一律用两位码）。

### 排除条件用 neg_fl

除`*_excl` 系列外，还有 `neg_fl` 数组（1–5 项）。传入字段名会把该字段的整体查询逻辑反转为 NOT，同时仍需保留正向条件。可选值：

```
prod_desc, hs_code, buyer, buyer_addr, supplier, supplier_addr,
log_consignee, log_shipper, orig_country_code, dest_country_code,
orig_port_id, orig_port_t, dest_port_id, dest_port_t,
trans_type_code, incoterms, brand
```

例：查「非 FOB 的中国出口越南records」→ `supplier: ["*"]`, `orig_country_code: ["CN"]`, `dest_country_code: ["VN"]`, `incoterms: ["FOB"]`, `neg_fl: ["incoterms"]`。

### data_source 数据源选择

`data_source` 是**国别 + 数据类型**的 4 字母码，最多 250 个。取值含义必须读资源文件确认（见下）。常用：

- `USIB` / `USEB` —— 美国 进口 / 出口
- `VNIC` / `VNEC` —— 越南 进口 / 出口
- `MXIS` / `MXES` —— 墨西哥提单 进口 / 出口
- `MXIA` / `MXEA` —— 墨西哥关单 进口 / 出口
- `DEIE` —— 德国 进口
- `GDIC` —— 全球贸易
- `SPIB` —— 航运数据；`EAIC` —— 过境数据
- `GOIB` / `GOID` —— 全球航运 装货 / 卸货

**不要凭记忆猜这个码。** 用户说「美国的海关数据」时，若不确定该国具体有哪些可用数据源，先读取资源文件确认后再拼参数。

---

## 枚举值资源（调用前必读）

服务提供一个 MCP Resource：

- URI：`resource://params/enums.json`
- 内容字段：`data_source`、`country_code`、`trans_type`、`incoterms`、`aggs.s`、`aggs.f`、`sort`

**每次需要用到 `data_source`、`aggs.f`、`aggs.s`、`sort` 的具体取值时，先读取这个资源**，不要凭印象填。资源里的中文说明是权威的。

关键取值速记：

- `country_code`：ISO 两位码，`CN` 中国、`US` 美国、`VN` 越南、`DE` 德国、`MX` 墨西哥。港澳台分别为 `HK` / `MO` / `TW`。
- `trans_type`：`SEA` 海运、`AIR` 空运、`SEA CONTAINERIZED` 海运集装箱、`RAILWAY` 铁路、`ROAD` 公路、`MULTI-MODAL` 多式联运
- `sort`：`score` 相关度、`date` 日期、`weight` 重量、`amount` 金额

---

## 统计工具的选择与 aggs 参数

### aggs.f —— 分组维度

| 工具 | aggs.f 可选值 |
|---|---|
| `search_stats_filter` / `search_stats_others` | `orig_country` 原产国、`dest_country` 目的国、`orig_port` 起运港、`dest_port` 目的港、`trans_type` 运输方式、`incoterms` 成交方式 |
| `search_stats_hs_code` | `hs_code_6` 6位、`hs_code_8` 8位 |
| `search_stats_com` | `buyer` 采购商、`supplier` 供应商 |
| `search_company_stats_*`（公司族） | 上述全部，另加 `trade_country`（com_role=buyer 时为原产国，supplier 时为目的国）、`trade_port`（对应港口）、`buyer_l` / `supplier_l` |

### aggs.s —— 统计指标

`sum_amount` 总金额、`sum_weight` 总重量、`sum_quantity` 总数量、`num_partner` 合作伙伴数、`num_buyer` 采购商数、`num_supplier` 供应商数、`num_orig_country` 原产国数、`num_dest_country` 目的国数、`min_date` 首次交易日期、`max_date` 最新交易日期

用于 `search_stats_overview`、`search_stats_trend`、`search_stats_hs_code`、`search_stats_com`、`search_stats_others` 及公司族对应工具。

### 分页

- `search_record`：`page`（1–1000，默认 1）+ `page_size`（10 / 20 / 50，默认 10）+ `merge`（合并相似记录，布尔）+ `sort` + `order`（`desc` / `asc`）
- `search_stats_filter`：`aggs.fc.page_size`（20 / 50 / 100 / 200 / 500 / 1000）

### 排序约束

带排名的统计类工具中，`sort` 的值必须是 `count` 或 `aggs.s` 中实际传入的值。例如传了 `aggs.s: ["sum_amount"]`，则 `sort` 只能填 `count` 或 `sum_amount`。

---

## 工具清单

### 公司信息

| Tool | 入参 | 用途 |
|---|---|---|
| `company_info` | `com_id` 或 `com_uid`（二选一） | 公司基本档案 |
| `company_reg_cn` | `com_name` 或 `xy_code`（至少一个） | 中国公司工商登记信息 |

### 市场级交易查询

| Tool | 必填 | 用途 |
|---|---|---|
| `search_record` | `date` | 交易记录明细，支持分页与排序 |
| `search_stats_overview` | `date` | 总体统计：命中条数 + 指定指标 |
| `search_stats_trend` | `date` | 月度趋势 |
| `search_stats_filter` | `date` + `aggs.f` | 快速分组排行（按次数） |
| `search_stats_hs_code` | `date` | HS 编码分组排行 |
| `search_stats_com` | `date` | 按采购商/供应商分组排行 |
| `search_stats_others` | `date` | 通用分组排行 |

### 公司级查询（均需 `date` + `com_role` + `com_id`/`com_uid`）

| Tool | 额外能力 |
|---|---|
| `search_company_record` | 该公司作为指定角色时的交易明细；可加 `partner_id` / `partner_uid`（最多一个）锁定对手方 |
| `search_company_stats_overview` | 命中条数 + 买家/卖家数、目的国/原产国数、总重量/金额/数量 |
| `search_company_stats_partner` | 交易伙伴 Top 排行（`sort` 必填，须为 `count` 或 `aggs.s` 传入值） |
| `search_company_stats_partner_stats` | 与指定伙伴（`partner_id`/`partner_uid`）之间的双边统计 |
| `search_company_stats_partner_growth` | 对比 `date` 与 `pre_date` 两期，输出伙伴**新增 / 流失 / 保持**名单 |
| `search_company_stats_trend` | 该公司月度趋势 |
| `search_company_stats_filter` | 快速分组排行（按次数） |
| `search_company_stats_hs_code` | HS 编码分组排行 |
| `search_company_stats_others` | 通用分组排行 |

---

## 标准工作流

### 场景一：分析一家公司的贸易情况

1. 检查是否已有贸易查询返回的公司 ID；只有公司名时，先按上文「从数据定位公司的流程」查询实际公司实体，核对主体并取得明确返回的 ID。存在歧义时先确认候选；没有 ID 时不调用公司级工具
2. `search_company_stats_overview` —— 先看整体规模，确定量级与活跃度
3. `search_company_stats_partner` —— 看主要交易伙伴
4. `search_company_stats_hs_code` —— 看主要商品结构
5. `search_company_stats_trend` —— 看走势
6. 需要具体单据时 `search_company_record` 抽样

定位公司时仅按需抽样少量记录；取得明确的公司 ID 后，先看整体统计，再按问题下钻明细。

### 场景二：摸一个市场

1. `search_stats_overview` 确认盘子多大
2. `search_stats_filter` 按 `orig_country` / `dest_port` 等切维度看结构
3. `search_stats_hs_code` 看商品结构
4. `search_stats_trend` 看趋势与季节性
5. `search_record` 抽样验证数据质量

### 场景三：客户/供应商开发

1. `search_stats_com` 按 `buyer` 或 `supplier` 维度拉目标国/目标品类下的实际公司清单，参数以工具定义和枚举资源为准
2. 核对候选公司及其明确返回的公司 ID，再用 `company_info` 补档案；仅有名称时先补查数据，不能把名称直接传给公司级工具
3. 用 `search_company_stats_partner` 判断其合作稳定性
4. 用 `search_company_stats_partner_growth` 找出新客户（本期新增的伙伴）

### 场景四：竞品对比

先分别从贸易数据中定位各公司的实体与 ID，再统一用 `search_company_stats_overview` + `search_company_stats_hs_code`，**保持 `date` 区间与 `data_source` 一致**，否则数字不可比。

---

## 输出与表达

- 金额单位通常为美元，重量常见 kg 或吨——**以返回结果中的字段名为准**，不要自行假设单位。
- 返回条数受 `page_size` 限制，向用户汇报时说明「Top N」而非全量。
- 排名类结果建议以简洁表格呈现，列出排名、名称、关键指标。
- 若某次查询返回为空，先检查：日期区间是否跨 2022（需切 `source_type`）、`data_source` 是否选对国别、是否误把排除参数当正向条件。
- 统计类数字是**估算参考**，用于趋势判断可以，不要当作精确财务数据呈现。
- 若用户的问题超出数据覆盖范围（如询问具体报关单号对应的完整报关单、税率、监管条件），明确说明本服务不覆盖，不要编造。

## 错误处理

| 现象 | 原因与处理 |
|---|---|
| `401` / `unauthorized` | 授权失效。提示用户重新连接连接器，不要自行重试超过一次 |
| 日期跨度超限 | 拆成多个 ≤3 年的区间分别查询，再汇总 |
| 「至少一个正向约束条件」 | 补充至少一个过滤字段 |
| `***_excl` 相关报错 | 补上对应的正向参数 |
| 无数据返回 | 检查 source_type、data_source、放宽 prod_desc 通配符、缩小日期区间 |
| `sort` 报错 | 改为 `count` 或已在 `aggs.s` 中传入的值 |
| 命中数异常大，或两次查询数字对不上 | **不传 `data_source` 时，服务端会按你的权限自动填满全部数据源。** 实测同一公司同一时间窗：限定 `USIB`+HS 8507 → 52,060 条；不传 → 813,989 条，差 15 倍。凡涉及跨公司/跨期对比，必须显式传 `data_source` |
| `aggs.s` 返回 `UNSUPPORTED_PARAMETER` | `search_company_stats_overview` 不支持 `aggs.s`，它固定返回买家数/卖家数/原产国数/目的国数/总重量/总金额/总数量，不要传 |
| 公司名查不到或无法取得公司 ID | 按「从数据定位公司的流程」核对数据源、时间、角色与数据中的实际公司名称；仅有名称或含义不明的分组值时，不调用公司级工具，也不判定公司不存在 |
