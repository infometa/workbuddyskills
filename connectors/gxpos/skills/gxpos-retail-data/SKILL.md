---
name: gxpos-retail-data
display_name: 弓鲸XPOS 零售数据
display_name_en: GXPOS Retail Data
description: 弓鲸XPOS 零售 ERP 数据查询与调拨操作。当用户提到 弓鲸、XPOS、零售明细、销售报表、店铺日报、门店销售、完成率、库存查询、库存分布、店仓、调拨单、转仓、补货、款号、条码、SKU、连单率、折扣率、导购业绩 等意图时，优先使用本 skill。支持：零售单据明细与汇总查询、门店日/月销售与目标完成率、商品库存列表与按店仓/颜色/尺码的库存分布、店仓名称解析、款号与SKU规格解析，以及调拨单的创建草稿、审核过账、列表与详情查询。
description_zh: 查询弓鲸XPOS 的零售明细、店铺日报、库存与店仓，并可创建、审核调拨单。
description_en: Query GXPOS retail sales detail, store daily metrics, stock and warehouses; create and settle transfer orders.
version: "1.0.0"
author: 弓鲸XPOS
category: business
visibility: public
---

# 弓鲸XPOS 零售数据 使用指南

通过本连接器查询弓鲸XPOS 的零售、库存、店仓数据，并执行调拨单操作。

## 前置条件

- **认证完全由连接器托管（OAuth 2.0 授权码 + PKCE）**。用户点「连接」时，WorkBuddy 会自动打开弓鲸提供的登录页，让用户输入 XPOS 的**企业编码、账号、密码**。**不要引导用户执行任何安装、登录或配置凭证的命令**，也不要把账号密码写进命令或配置文件。
- **连接器服务端不保存用户密码**：密码只在登录页提交一次，用于当场换取访问令牌。AI 不得在回复中复述用户的密码或令牌。
- **令牌有效期 1 小时**，到期后 WorkBuddy 会自动重新拉起登录页，用户重登一次即可继续，无需重新配置。
- 若工具返回「未授权 / 令牌失效」类错误：提示用户重新连接本连接器并在登录页重新登录一次，然后重试刚才的提问，**不要反复重试同一参数**。
- 若用户反馈「点连接后浏览器没弹出」：让用户手动打开 `https://erp.ebosserp.cn/mcp/authorize` 是不行的（缺少 OAuth 参数，会报 400）。正确做法是重新点一次「连接」。
- 日期统一使用 `YYYY-MM-DD`；用户说「昨天」「上周」时，请先按当前日期换算出具体区间再传参，不要把相对时间原样传下去。

## 可用工具

共 10 个工具，分四组：零售、库存、店仓/商品、调拨。

### 一、零售数据

#### retail_report_list — 零售明细/报表查询

按日期区间、店铺、款号、状态、关键字查询零售单据明细与汇总。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| date | string | 否 | 开始日期 YYYY-MM-DD |
| dateend | string | 否 | 结束日期 YYYY-MM-DD |
| storeid | string | 否 | 单个店铺 ID |
| storeids | string | 否 | 多个店铺 ID，逗号分隔 |
| status | string | 否 | 单据状态 |
| styleids | string | 否 | 款号 ID，逗号分隔 |
| searchkey | string | 否 | 关键字：单号 / 款号 / 导购等 |
| sort | string | 否 | 排序字段，默认 `billdate_desc` |
| page | number | 否 | 页码，默认 1 |
| pagesize | number | 否 | 每页条数，默认 20（做汇总统计时可放大到 5000 以上） |

**返回**：`summary`（合计：笔数 / 件数 / 原额 / 实收）与 `list`（明细行）。

明细行常用字段：`billdate` 单据日期、`masterid` 单号、`storeid` 门店、`style` 款号、`stylename` 款名、`sku` 条码、`qty` 数量、`fprice` 原价、`rprice` 实价、`famount` 原额、`ramount` 实收、`image` 图片、`seller` 导购。

**示例**：查 2026-10-01 ~ 2026-10-07 销售额 Top 10 的款 → 传 `date`/`dateend`，`pagesize: 5000`，拿到明细后自行按 `style` 聚合 `ramount` 再排序。

#### store_daily_report — 店铺日报

按日期与店铺查询各门店销售额、目标与完成率等日度指标。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| date | string | 否 | 查询日期 YYYY-MM-DD，留空默认当天 |
| storeids | string | 否 | 店铺 ID，逗号分隔，留空查全部 |
| sort | string | 否 | 排序字段，默认 `store_asc` |
| page / pagesize | number | 否 | 分页，默认 1 / 20 |

**返回**：`summary`（合计）与 `list`（各店铺日/月指标行）。

**注意**：本接口的日/月**目标类字段实测可能返回 0**，此时不要据此断言「门店没完成目标」，应直接告知用户该指标取不到，或改用 `retail_report_list` 自行计算。

### 二、库存数据

#### stock_list — 库存列表查询

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| storeid | string/number | 否 | 店铺 ID，留空查全部 |
| keyword | string | 否 | 关键词：货号 / 条码 / 商品名称 |
| sort | string | 否 | `styleid_desc`(默认) / `qty_desc` / `qty_asc` / `dprice_desc` / `dprice_asc` |
| page / pagesize | number | 否 | 分页，默认 1 / 20 |

**返回**：`summary`（款数 / 库存 / 总额汇总）与 `list`（商品行）。列表里的 `marketdate` 是**上市日期**，可用于款龄分析。

#### stock_detail — 库存商品明细

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | string/number | **是** | 商品 ID，取自 `stock_list` 返回的 `list[].id` |

**返回**：`info`（款号 / 名称 / 图片 / 价格 / 描述）与 `stockByStore`（按店仓 → 颜色 → 尺码聚合，含小计与总计）。

**调用顺序**：先用 `stock_list` 定位商品拿到 `id`，再用本工具看分布。不要凭空构造 `id`。

### 三、店仓与商品解析

#### store_list — 店仓列表查询

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | 否 | 店仓名称或编码关键字 |
| type | number | 否 | 1=收货类店仓，2=发货类店仓；留空返回两类合并去重 |
| page / pagesize | number | 否 | 分页，默认 1 / 200 |

**用途**：把用户口中的店仓名（如「总仓」「万象城店」）解析为调拨单需要的 ID。**店仓有歧义或匹配不到时必须向用户确认，不要猜。**

#### goods_resolve — 商品解析

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | **是** | 款号或商品名称 |
| storeid | string/number | 否 | 店仓 ID；提供后若仅唯一匹配一个款，会一并返回该款的 SKU 规格列表（`skuid` / 颜色 / 尺码） |

**用途**：为调拨明细确定「款号 + 颜色 + 尺码 → skuid」。匹配到多个款时要让用户确认是哪一个。

### 四、调拨单（含写操作）

#### transfer_create — 创建调拨单草稿

> **仅保存草稿，不增减库存。**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| orig | string/number | **是** | 发货店仓：名称或 ID |
| dest | string/number | **是** | 收货店仓：名称或 ID |
| billdate | string | 否 | 单据日期 YYYY-MM-DD，默认今天 |
| remark | string | 否 | 备注 |
| items | array | **是** | 明细行数组，每行：`{ style, color?, size?, quantity }` |

工具会自动把店仓名称解析为 ID、把「款号 + 颜色 + 尺码」解析为 skuid。返回体里 `resolvedItems` 是成功解析的明细，`failedItems` 是解析失败的行与原因——**有 failedItems 时必须原样告知用户**，不能只说「已创建」。

明细里若只给款号不给颜色尺码，会解析不到唯一 SKU 而失败，需先补齐颜色/尺码。

#### transfer_submit — 审核过账调拨单

> **⚠️ 高风险：真实跨店仓增减库存，不可撤销（需另走作废流程）。**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | string/number | **是** | 调拨单 ID，来自 `transfer_create` 返回的 `id` |

**确认规则（必须遵守）**：调用前先把「发货店仓 / 收货店仓 / 单号 / 明细行（款号·颜色·尺码·数量）」完整列给用户，**得到用户明确同意后才可调用**。用户没明确说「确认过账 / 审核 / 提交」时，不要自行调用。

#### transfer_list — 调拨单列表查询

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| date / dateend | string | 否 | 日期区间 YYYY-MM-DD |
| status | string | 否 | 1 制单 / 2 审核 / 4 已出库 / 8 已验收，留空全部 |
| masterid | string | 否 | 单号关键字 |
| orig | string/number | 否 | 发货店仓 ID |
| dest | string/number | 否 | 收货店仓 ID |
| sort | string | 否 | `billdate_desc`(默认) / `billdate_asc` / `amount_desc` / `amount_asc` |
| page / pagesize | number | 否 | 分页，默认 1 / 20 |

**返回**：`list`（单号 / 店仓 / 时间 / 数量 / 金额 / 状态）、`total` 与 `summary`。

#### transfer_detail — 调拨单详情

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| id | string/number | **是** | 调拨单 ID |

**返回**：表头信息与商品明细 `items`。

## 典型调用链

| 用户意图 | 调用路径 |
|---|---|
| 「某段时间卖了多少钱」 | `retail_report_list`（按日期区间，放大 pagesize）→ 汇总 `ramount` |
| 「哪几个款卖得最好」 | `retail_report_list` → 按 `style` 聚合 `qty`/`ramount` → 排序 |
| 「今天各店完成率」 | `store_daily_report`（无 storeids 查全部门店） |
| 「某店某款还有多少库存」 | `stock_list`（传 storeid + keyword）→ 取 `list[].id` → `stock_detail` |
| 「把 X 件 A 款从甲店调到乙店」 | `store_list` 确认两个店仓 → `goods_resolve` 补颜色尺码 → **列清单给用户确认** → `transfer_create` → 用户确认后 `transfer_submit` |
| 「本周有哪些调拨单」 | `transfer_list` → 需要看某单细节时用 `transfer_detail` |

## 输出与口径要求

- 金额保留两位小数并加 `¥`；数量为整数；比率保留一位小数加 `%`。
- 排名类结果先给摘要前几名，再问用户是否要完整列表，不要把几百行明细直接铺开。
- 用户没指定日期区间时，先确认口径（今天 / 昨天 / 本周 / 本月），不要默认跑全量历史。
- 数据为空时明确说「该条件下没有查到数据」，并给出可能原因（日期区间、门店范围、款号关键字），不要编造数字。

## 错误处理

| 现象 | 处理 |
|---|---|
| 登录失败 / 令牌失效 | 提示用户重新连接连接器并核对企业编码、账号、密码；不要循环重试 |
| 未找到发货/收货店仓 | 用 `store_list` 带关键词重新检索，把候选列给用户选择 |
| 未匹配到款式 / SKU | 用 `goods_resolve` 按关键词重查，确认款号、颜色、尺码写法 |
| 请求超时 | 缩小日期区间或门店范围后重试一次；仍失败则告知用户服务端无响应 |
| 明细行部分失败 | 如实列出 `failedItems` 与原因，询问是否修正后重新创建 |
