---
name: property-saas
description: 连接 V8 智慧物业云平台。用于业主/租户检索（search_owner）、业主档案查询（query_owner_detail）、欠费查询（query_owner_arrears）、报修工单查询（query_owner_repair）与缴费核销（owner_payment）。调用缴费前必须向用户二次确认。含企业编码、费用项 ID、工单状态枚举等关键上下文。
---

# 物业 SaaS 连接器使用指南

本连接器对接 V8 智慧物业云平台，面向物业客服、收费、工程等人员。**业主与租户共用同一张客户表**，用「客户类型」区分，统一称为「客户」。

## 认证前置条件

- 使用前，用户在 WorkBuddy「连接」时需通过 **OAuth 授权码流程**登录：输入**企业编码** + **用户名** + **密码**。
- 企业编码是物业公司在登录页输入的组织标识（如 `6101010128`），不同企业不同。登录成功后 token 自动注入，AI 无需手动传凭证。
- 鉴权失败时接口返回错误，引导用户重新连接/授权即可。

## 工具调用顺序（重要）

通常按 `search_owner → query_owner_detail / query_owner_arrears / query_owner_repair → owner_payment` 的顺序使用：

1. 先用 **search_owner** 定位客户，拿到 `customerId` 和 `roomId`。
2. 再用 **query_owner_detail** 看档案、**query_owner_arrears** 查欠费、**query_owner_repair** 查报修。
3. 只有在用户明确要求缴费、且欠费信息已确认时，才调用 **owner_payment**（高危写操作，见后）。

---

## 工具 1：search_owner — 检索业主/租户

**用途**：按姓名、身份证号、项目或房间定位客户，返回客户 ID、姓名、类型、联系方式（脱敏）及所属房间（含 roomId）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 否* | 姓名（模糊匹配，最常用） |
| idcard | string | 否* | 身份证号（模糊匹配） |
| areaId | string | 否* | 项目/小区 ID |
| roomId | string | 否* | 房间 ID（精确匹配） |

*四项至少提供一个；优先用 name。

**示例**：`search_owner({ "name": "高婷婷" })`

**返回**：`匹配数量` + `客户列表`。每项含 `业主ID`、`姓名`、`客户类型`（个人业主/单位租户等）、`手机号`（脱敏）、`房号`、`房间ID`、`项目`、`楼宇`、`单元` 等。

> 拿到结果后，记下 `业主ID`（即 customerId）和 `房间ID`（即 roomId），供后续工具使用。

---

## 工具 2：query_owner_detail — 客户档案详情

**用途**：根据客户 ID 查完整档案：基本信息、联系方式（脱敏）、证件、入伙日期、房产、车位车辆、同住人等。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| customerId | string | 是 | 客户 ID（来自 search_owner，即业主/租户 ID） |

**示例**：`query_owner_detail({ "customerId": "20260818001" })`

**返回**：客户对象 JSON。

---

## 工具 3：query_owner_arrears — 查询欠费

**用途**：查指定房间各计费期的收费项目欠费金额（物业费、水费、电费、停车费等）及欠费合计，用于催缴、对账。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| roomId | string | 是 | 房间 ID（来自 search_owner，后端按房间定位欠费） |
| customerId | string | 否 | 客户 ID（来自 search_owner） |
| costDate | string | 否 | 计费期 `yyyy-MM`，如 `2026-08`（查该月及以前欠费） |
| chargeItemIds | string[] | 否 | 收费项目 ID 列表，用于筛选特定费用项 |

**示例**：`query_owner_arrears({ "roomId": "5969", "costDate": "2026-08" })`

**返回**：`总欠费金额` + `欠费明细`（按计费期分组，每项含 `收费项目`、`欠费金额`、`单价`、`使用量`）。

> ⚠️ 后端该接口查询较慢（实测 20~30 秒），属正常现象，不要视为超时失败。

---

## 工具 4：query_owner_repair — 查询报修工单

**用途**：查报修工单，返回工单号、报修内容、报修人、联系电话、房号、报修地址、报事分类、当前状态、接单人、创建时间。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| status | string | 是 | 工单状态数字 code（见下表） |
| keyword | string | 否 | 模糊关键字：工单号 / 房号 / 报修内容 |
| areaId | string | 否 | 项目/小区 ID |
| startDate | string | 否 | 起始日期 `yyyy-MM-dd` |
| endDate | string | 否 | 结束日期 `yyyy-MM-dd` |
| page | number | 否 | 页码，默认 1 |
| pageSize | number | 否 | 每页条数，默认 20，最大 100 |

**状态枚举**：`2000`临时工单 `2001`待分派 `2002`待接单 `2003`暂停中 `2004`待处理 `2005`处理中 `2006`已完工 `2011`已归档 `2012`无效工单 `2021`已删除 `2023`已回退 `2007`已回访 `2008`已评价。

**示例**：`query_owner_repair({ "status": "2005", "areaId": "xxx", "page": 1 })`

> ⚠️ `status` 必填——后端未传状态会报空指针 500。keyword 只匹配工单号/房号/报修内容，**不匹配报修人姓名**。

---

## 工具 5：owner_payment — 缴费核销（⚠️ 高危写操作）

**用途**：为业主/租户名下房产的欠费执行缴费核销（生成缴费订单并冲销欠费）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| customerId | string | 是 | 客户 ID（来自 search_owner） |
| paymentMethod | string | 是 | 支付方式：微信 / 支付宝 / 现金 / 银行转账 |
| roomId | string | 否 | 缴费房产 ID；单房可省略，多房需指定 |
| costDate | string | 否 | 计费期 `yyyy-MM`，如 `2026-08` |
| chargeItemIds | string[] | 否 | 收费项目 ID 列表（来自 query_owner_arrears） |

### ⚠️ 硬性二次确认规则（必须遵守）

本工具会**真实改变账务数据**（核销欠费、生成缴费订单），不是预下单。**调用前必须完成以下二次确认**，缺一不可：

1. 向用户复述 **缴费对象**（姓名）和 **房产**（房号/项目/楼宇）。
2. 复述 **计费期**、**收费项目** 和 **欠费金额**（来自 query_owner_arrears 返回）。
3. 复述 **支付方式**（paymentMethod）。
4. 明确告知「本操作将核销欠费并生成缴费订单，不可撤销」，获得用户**明确同意**。

> 未获用户明确确认，**禁止**调用 owner_payment。用户有含糊或犹豫时，先展示欠费明细让其决定。

**示例流程**：
1. `query_owner_arrears({ "roomId": "5969" })` → 得到欠费合计 ¥856.40。
2. 向用户确认：「将为 1 幢 101 高婷婷核销 2026-06 ~ 2026-08 物业费共 ¥856.40，微信支付，将生成缴费订单并冲销欠费，确认吗？」
3. 用户确认后：`owner_payment({ "customerId": "...", "paymentMethod": "微信", "roomId": "5969", "costDate": "2026-08", "chargeItemIds": ["..."] })`

---

## 常见错误与恢复

| 现象 | 原因 | 处理 |
|---|---|---|
| 返回 401 / 鉴权失败 | token 失效或未授权 | 引导用户重新「连接」走 OAuth 登录 |
| query_owner_arrears 很慢 | 后端接口本身慢（20~30s） | 正常，等待即可，勿重复调用 |
| query_owner_repair 报 500 | 未传 `status` | 补必填的 `status` 后重试 |
| search_owner 返回 0 条 | 关键条件漏传或输入有误 | 换姓名/房号重试，或补 areaId |
| owner_payment 参数缺失 | 未带 customerId / paymentMethod | 补全参数，且先完成二次确认 |

## 输出约定

- 对用户的输出使用**中文业务名称**（房间台账、楼宇档案、工单、欠费等），不要暴露底层表名或接口字段。
- 敏感字段（手机号、固话、证件号、车牌）默认脱敏展示。
- 大结果集建议用表格呈现，必要时提示导出。
