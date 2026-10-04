---
name: cjt-tc-meta-mcp-guide
description: 畅捷通 T+Cloud MCP 使用指导 - 查询/管理销售订单、采购订单、库存单据、生产工单、财务凭证、报表及基础档案。使用 T+ MCP 前请先阅读此技能。
version: "1.0.0"
author: "畅捷通"
capabilities:
  tools:
    - chanjet_search
    - chanjet_execute
    - chanjet_column_info
    - chanjet_reportinfo
    - chanjet_bizcodelist
    - chanjet_help
tags:
  - ERP
  - 财务
  - 进销存
  - 生产管理
---

# 畅捷通 T+Cloud MCP 工具完整汇总

## 一、核心工具（6 个）

### 1. chanjet_search — 搜索服务和操作（起点工具）

**用途：** 通过关键词搜索 T+Cloud 中可用的服务和操作，返回服务名、操作列表、调用示例。

**参数：**
- `keyword`（必填）：搜索关键词，如 "销售订单"、"inventory"、"报表"
- `category`（可选）：过滤类别 — `all`（默认）/ `voucher`（单据）/ `archive`（档案）/ `report`（报表）/ `special`（特殊）

**返回内容：**
- 服务名称（service）
- 中文名称
- 可用操作列表（operation）
- 调用示例（chanjet_execute 语法）

**使用场景：** 每次查询前先用它确认正确的 service 和 operation，避免路径错误。

---

### 2. chanjet_execute — 万能执行器

**用途：** 执行 T+Cloud 任意 API 操作，是所有业务操作的最终执行通道。

**参数：**
- `service`（必填）：服务名称，如 `SaleOrderOpenApi`、`inventory`、`reportQuery`
- `operation`（必填）：操作名称，如 `Create`、`FindVoucherList`、`GetReportData`
- `body`（可选）：请求体 JSON，格式因操作类型而异

**支持的操作类型：**
- **查询类：** FindVoucherList、Query、QueryPage、GetReportData
- **创建类：** Create、CreateAsync、CreateBatch
- **修改类：** Update、UpdateBatch
- **审核类：** Audit、UnAudit
- **删除类：** Delete、DeleteBatch、BatchDelete
- **状态类：** Close、Open、Change、ManualFinish
- **报表类：** GetReportData、GetBalanceSumRpt、FindTaxTable

---

### 3. chanjet_column_info — 获取单据字段定义

**用途：** 获取单据业务编码对应的真实字段名，**新建、修改或筛选前必须先调用，不可猜测字段名**。

**参数：**
- `bizCode`（必填）：单据业务编码，如 `SA04`（销货单）、`SO`（销售订单）、`POO`（采购订单）
- `kind`（可选）：获取内容 — `search`（查询筛选项，默认）/ `custom`（自定义字段）/ `all`（全部）

**返回内容：** 字段名列表（FieldName）、字段类型、是否必填、是否可筛选等

**⚠️ 重要性：** 字段名错误是调用失败的最常见原因之一。即使 chanjet_execute 内置了自动字段映射（best-effort），关键流程仍应优先使用此工具返回的真实 FieldName。

---

### 4. chanjet_reportinfo — 查询报表名称和字段

**用途：** 查询 T+Cloud 业务报表名称和字段定义，为 GetReportData 做准备。

**调用方式：**
- 第一步：`chanjet_reportinfo(keyword="销售")` → 列出所有含"销售"的报表（Title + Name + MenuCode）
- 第二步：`chanjet_reportinfo(reportTitle="销售毛利分析表")` → 返回该报表的筛选项、栏目、分组项

**注意：** 资产负债表/利润表/现金流量表不在此系统中（属于 FormReport 套表），改用 `chanjet_execute` 调用 `TaxOpenAPI/FindTaxTable`。

---

### 5. chanjet_bizcodelist — 单据业务编码对照表

**用途：** 获取 T+Cloud 单据业务编码对照表（如 SA04=销货单、SO=销售订单、POO=采购订单）。

**参数：**
- `keyword`（可选）：关键词筛选，支持中文名称或编码模糊匹配，如 "销售"、"采购"、"SA"

**使用场景：** 不知道 bizCode 时先调用此工具，再用 bizCode 调用 chanjet_column_info。

---

### 6. chanjet_help — 帮助信息

**用途：** 获取 T+Cloud MCP 工具帮助，包括工作流示例和常见错误。

**参数：**
- `topic`（可选）：帮助主题
  - `overview`：工具概览（默认）
  - `workflow`：工作流示例
  - `errors`：常见错误
  - `schema`：字段查询

---

## 二、标准工作流

### 工作流 1：查单据列表 + 详情

```
步骤 1: chanjet_search("销售")
        → 找到 SaleOrderOpenApi 服务，操作：FindVoucherList、GetVoucherDTO

步骤 2: chanjet_execute(
          service="SaleOrderOpenApi",
          operation="FindVoucherList",
          body={"pageIndex":0, "pageSize":10, "paramDic":{}}
        )
        → 返回单据列表（仅包含 id, code, externalcode, ts）

步骤 3: chanjet_execute(
          service="SaleOrderOpenApi",
          operation="GetVoucherDTO",
          body={"param":{"voucherID":"<id>", "voucherTypeCode":"SO"}}
        )
        → 返回完整单据详情（含表头、明细行、业务字段）
```

**⚠️ 注意：** FindVoucherList 只返回基础字段，业务字段（如客户、金额、数量等）必须通过 GetVoucherDTO 获取。

---

### 工作流 2：创建单据（以销货单为例）

```
步骤 1: chanjet_column_info(bizCode="SA04")
        → 获取销货单的真实字段名

步骤 2: 查关联档案获取真实 Code:
        - chanjet_execute(service="partner", operation="Query", body='{"param":{"Name":"XX公司"}}')
          → 取得客户 Code（填入 Vendor.Code 或 Partner.Code）
        - chanjet_execute(service="inventory", operation="Query", body='{"param":{"Name":"产品A"}}')
          → 取得存货 Code（填入明细行 Inventory.Code）
        - chanjet_execute(service="warehouse", operation="Query", body='{"param":{}}')
          → 取得仓库 Code（填入 Warehouse.Code）

步骤 3: chanjet_execute(
          service="SaleDeliveryOpenApi",
          operation="Create",
          body={"dto":{
            "Vendor":{"Code":"C001"},
            "Date":"2026-05-15",
            "Details":[{
              "Inventory":{"Code":"M001"},
              "Quantity":100,
              "Price":25.50
            }]
          }}
        )
        → 返回创建结果（含 voucherID）

步骤 4: chanjet_execute(
          service="SaleDeliveryOpenApi",
          operation="Audit",
          body={"param":{"voucherID":"<id>"}}
        )
        → 审核单据
```

**⚠️ 规则：** body 中涉及存货/仓库/往来单位/部门等关联字段，必须先查档案取得真实 Code，禁止猜测编码。

---

### 工作流 3：查询报表数据

```
步骤 1: chanjet_reportinfo(keyword="销售")
        → 找到报表列表，如 "销售毛利分析表" (SA_GrossProfitAnalysisRpt)

步骤 2: chanjet_reportinfo(reportTitle="销售毛利分析表")
        → 获取该报表的筛选项、栏目、分组项定义

步骤 3: chanjet_execute(
          service="reportQuery",
          operation="GetReportData",
          body={
            "reportName": "SA_GrossProfitAnalysisRpt",
            "pageIndex": 1,
            "pageSize": 100,
            "param":{
              "BeginDate": "2026-01-01",
              "EndDate": "2026-05-15"
            }
          }
        )
        → 返回报表数据
```

**⚠️ 注意：** GetReportData 的 pageIndex 从 **1** 开始（不是 0！传 0 会报"非第一页查询"错误）。第 2 页及以后必须携带第 1 页响应中的 TaskSessionID 和 SolutionID。

---

### 工作流 4：创建存货（档案）

```
步骤 1: chanjet_execute(service="inventoryClass", operation="Query", body='{"param":{}}')
        → 取得存货分类 Code（填入 InventoryClass.Code）

步骤 2: chanjet_execute(service="Unit", operation="Query", body='{"param":{}}')
        → 取得计量单位 Code（填入 MainUnit.Code）

步骤 3: chanjet_execute(
          service="McpMetaService",
          operation="GetArchiveSelectFields",
          body='{"service":"inventory","operation":"Query"}'
        )
        → 查看存货档案允许的 SelectFields 范围

步骤 4: chanjet_execute(
          service="inventory",
          operation="Create",
          body={"dto":{
            "Code":"M001",
            "Name":"产品A",
            "InventoryClass":{"Code":"01"},
            "MainUnit":{"Code":"PCS"}
          }}
        )
        → 创建存货
```

---

### 工作流 5：查询现存量

```
chanjet_execute(
  service="currentStock",
  operation="Query",
  body={"param":{}}
)
→ 返回当前库存状况（存货、仓库、现存量、可用量、结存金额等）

chanjet_execute(
  service="currentStock",
  operation="QueryByTime",
  body={"param":{"Date":"2026-05-15"}}
)
→ 返回指定日期的库存快照
```

---

## 三、Body 格式规则（重要！）

### 档案查询

| 档案类型 | Body 格式 | 说明 |
|----------|-----------|------|
| 大部分档案（inventory、partner、warehouse 等） | `{"param":{}}` | PascalCase 字段名（Code/Name/Disabled），分页用 PageSize 放在 param 内（最大1000），无 pageIndex |
| department / person / Account / SettleStyle | `{"dto":{}}` | 特殊格式，注意区分 |
| 模糊查询 | `{"param":{"Name":"%关键词%"}}` | Name/Code 可使用 `%KEYWORD%` 做 LIKE 模糊匹配 |
| 指定返回列 | 先调用 `McpMetaService/GetArchiveSelectFields` | 查看该档案允许的 SelectFields 范围 |

**示例：**
```json
// 查询所有存货（分页 100 条）
{"param":{"PageSize":100}}

// 模糊查询名称含"绿萝"的存货
{"param":{"Name":"%绿萝%"}}

// 模糊查询编码含"A01"的存货
{"param":{"Code":"%A01%"}}

// 查询指定名称的往来单位
{"param":{"Name":"XX公司"}}
```

### 单据操作

| 操作类型 | Body 格式 | 说明 |
|----------|-----------|------|
| Create / Update | `{"dto":{...}}` | 关联字段需先查档案取真实 Code |
| Audit / UnAudit | `{"param":{"voucherID":"<id>"}}` | 审核/反审核 |
| Delete | `{"param":{"voucherID":"<id>"}}` | 删除单据 |
| GetVoucherDTO | `{"param":{"voucherID":"<id>","voucherTypeCode":"<bizCode>"}}` | bizCode 如 SA04；已知服务可省略（MCP 自动注入） |
| FindVoucherList | `{"pageIndex":0,"pageSize":10,"paramDic":{}}` | pageIndex 从 0 开始 |

### 档案删除

| 档案类型 | Body 格式 |
|----------|-----------|
| bom / Expense 等 | `{"dto":{"ID":"xxx"}}` |
| doc（会计凭证） | `{"doc":{"ExternalCode":"xxx"}}` |

---

## 四、全模块分类详解

### 1. 销售管理（9 个服务 / 47 个接口）

**模块定位：** 覆盖销售业务全链路 — 从订单到出库到开票。

#### 单据服务

| 服务名 | 中文名 | bizCode | 操作 | 说明 |
|--------|--------|---------|------|------|
| SaleOrderOpenApi | 销售订单 | SO | Create / CreateAsync / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete / Close / Open / Change | 销售业务的起点，可关联生产和采购执行 |
| SaleDeliveryOpenApi | 销货单 | SA04 | Create / CreateAsync / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete / GetSaleDeliveryTrace | 实际发货凭证，触发库存减少和应收生成 |
| SaleDispatchOpenApi | 销售出库单 | — | Create / CreateAsync / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete | 仓库出库执行凭证 |
| SaleInvoiceOpenApi | 销售发票 | — | Create / FindVoucherList / GetVoucherDTO / UpdateSaleInvoiceInfo / Audit / Unaudit / Delete | 税务开票凭证 |

#### 档案服务

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| SalePrice | 销售价格 | Query | 查询客户/存货的价格体系 |

#### 简易服务

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| saleOrder | 销售订单(简易) | Create / CreateBatch / Close / Delete / QueryExecuting | 快捷创建销售订单 |
| saleDispatch | 销售出库(简易) | Create | 快捷创建销售出库单 |

#### 报表服务

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| SAReportQuery | 销售报表查询 | CustomerCreditQuery | 客户信用查询 |
| reportQuery | 通用报表查询 | GetReportData / GetBalanceSumRpt / GetGroupInfosByReportTitle / GetReportInfosExt / GetSearchItemsByReportTitle / GetTableColsByReportTitle | 所有销售类报表的数据查询 |

**业务场景：**
- 销售订单 → 销货单 → 销售出库单 → 销售发票（标准销售流程）
- 销售订单可关联生产加工单（按单生产）或采购订单（以销定购）
- 支持订单关闭/打开/变更等状态管理

---

### 2. 采购管理（6 个服务 / 32 个接口）

**模块定位：** 覆盖采购业务全链路 — 从订单到入库到开票。

#### 单据服务

| 服务名 | 中文名 | bizCode | 操作 | 说明 |
|--------|--------|---------|------|------|
| PurchaseOrderOpenApi | 采购订单 | POO | Create / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete / Close / Open | 采购业务的起点，可关联入库执行 |
| PurchaseArrivalOpenApi | 进货单 | — | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 实际收货凭证（不入库） |
| PurchaseReceiveOpenApi | 采购入库单 | — | Create / CreateAsync / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete | 仓库入库执行凭证 |
| PurchaseInvoiceOpenApi | 采购发票 | — | Create / FindVoucherList / GetVoucherDTO / Audit / Unaudit / Delete | 进项税发票凭证 |

#### 简易服务

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| purchaseOrder | 采购订单(简易) | Create | 快捷创建采购订单 |
| purchaseReceive | 采购入库(简易) | Create | 快捷创建采购入库单 |
| purchaseArrival | 进货(简易) | Create | 快捷创建进货单 |

**业务场景：**
- 采购订单 → 进货单 → 采购入库单 → 采购发票（标准采购流程）
- 支持以销定购（销售订单关联采购订单）
- 采购订单支持关闭/打开状态管理

---

### 3. 库存管理（21 个服务 / 77 个接口）

**模块定位：** 覆盖库存全业务 — 出入库、调拨、盘点、成本核算。

#### 出入库单据

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| TransVoucherOpenApi | 调拨单 | Create / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete | 仓库间调拨，源仓库出库+目标仓库入库 |
| CheckVoucherOpenApi | 盘点单 | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 库存盘点，生成盘盈盘亏 |
| MaterialDispatchOpenApi | 材料出库单 | Create / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete | 生产领料出库 |
| OtherDispatchOpenApi | 其他出库单 | Create / CreateAsync / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete | 非标准出库（损耗、赠送等） |
| OtherReceiveOpenApi | 其他入库单 | Create / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete | 非标准入库（盘盈、退货等） |
| ProductReceiveOpenApi | 产成品入库单 | Create / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete | 生产完工入库 |
| AdjustCostOutOpenApi | 出库调整单 | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 调整出库成本 |
| AdjustCostInOpenApi | 入库调整单 | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 调整入库成本 |

#### 简易出入库服务

| 服务名 | 操作 | 说明 |
|--------|------|------|
| materialDispatch | Create | 快捷材料出库 |
| otherDispatch | Create | 快捷其他出库 |
| otherReceive | Create | 快捷其他入库 |
| productReceive | Create | 快捷产成品入库 |

#### 存货档案

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| inventory | 存货 | Create / CreateBatch / Update / UpdateBatch / UpdateImage / Query / QueryPage / QueryInventoryPriceWithoutFormula | 商品/物料主数据 |
| inventoryClass | 存货分类 | Create / Query | 存货分类体系 |
| inventoryUnit | 存货计量单位 | Query | 存货的计量单位设置 |
| InvMutiCode | 存货多编码 | Query | 一个存货对应多个编码 |

#### 价格档案

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| CustomerInventoryPriceWithoutFormula | 客户存货价格 | Query | 客户专属价格（不含公式） |
| InventoryCountLevelPrice | 存货批次级价格 | Query | 按批次定价 |
| VendorInventoryPriceWithoutFormula | 供应商存货价格 | Query | 供应商供货价格（不含公式） |

#### 库存查询

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| currentStock | 现存量 | Query / QueryByTime | 查询当前/历史库存状况 |

#### 成本核算

| 服务名 | 操作 | 说明 |
|--------|------|------|
| InventoryCostingOpenApi | GetIndividualPriceForAPI / RestartCostring | 获取个别计价成本 / 重新核算成本 |

**业务场景：**
- 采购入库 → 库存持有 → 销售出库（标准库存流转）
- 调拨单：仓库 A → 仓库 B
- 盘点单：定期盘点，生成盘盈/盘亏调整
- 成本核算：支持移动平均、个别计价等成本算法

---

### 4. 生产管理（5 个服务 / 28 个接口）

**模块定位：** 覆盖生产计划到执行全过程。

#### 生产单据

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| ManufactureOrderOpenApi | 生产加工单 | Create / CreateAsync / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete / Close / Open / Change / ManualFinish | 生产核心单据，关联 BOM 和工艺路线 |
| QualityProcessInspectOpenApi | 生产过程检验单 | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 生产过程中的质量检验 |
| MaterialRequestOpenApi | 领料申请单 | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 生产领料申请 |

#### 生产档案

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| process | 工序 | Create / Query | 生产工序定义 |
| routing | 工艺路线 | Create / Query | 工序的先后顺序和资源配置 |

**⚠️ 重要约束：** 生产加工单 Create/Update 时，PreStartDate（预开工日）和 PreFinishDate（预完工日）必须 >= VoucherDate（单据日期），否则后端返回 999 错误 "预开工日不能早于单据日期！"

**业务场景：**
- 销售订单 → 生产加工单 → 领料申请 → 生产检验 → 产成品入库
- 支持按单生产（MTO）和按库生产（MTS）
- 支持手动完工（ManualFinish）

---

### 5. 委外管理（3 个服务 / 21 个接口）

**模块定位：** 覆盖委外加工业务全链路。

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| OutSourceOrderOpenApi | 委外加工单 | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 委外业务起点，定义委外产品和数量 |
| DelegateDispatchOpenApi | 委外发料单 | Create / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete | 向委外商发送原材料 |
| DelegateReceiveOpenApi | 委外入库单 | Create / CreateAsync / FindVoucherList / GetVoucherDTO / Update / Audit / UnAudit / Delete | 委外加工完成入库 |

**业务场景：**
- 委外加工单 → 委外发料单 → 委外商加工 → 委外入库单
- 委外发料会扣减原材料库存
- 委外入库会增加产成品库存

---

### 6. 财务管理（10 个服务 / 38 个接口）

**模块定位：** 覆盖收付款、费用、零售结算等财务业务。

#### 收付款单据

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| ReceivePaymentVoucherOpenApi | 收/付款单 | NewCreate / Audit / UnAudit / NewDelete / GetVoucherDTO | 实际收付款凭证 |
| ReceiveVoucherOpenApi | 收/付款单查询 | FindVoucherList | 收付款单列表查询 |
| PaymentVoucherOpenApi | 付款单 | FindVoucherList | 付款单列表查询 |
| ArapPrepaymentRequisitionOpenApi | 付款申请单 | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 付款审批流程 |

#### 应收应付单据

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| OtherReceiveVoucherOpenApi | 其他应收单 | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 非销售产生的应收（押金、赔款等） |
| OtherPaymentVoucherOpenApi | 其他应付单 | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 非采购产生的应付 |

#### 其他财务单据

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| expenseVoucher | 费用单 | Create / CreateAsync / CreateExpenseVoucher / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 费用报销/支出 |
| RetailSettleOpenApi | 零售结算单 | FindVoucherList / GetVoucherDTO | 零售业务结算 |

#### 简易服务

| 服务名 | 操作 | 说明 |
|--------|------|------|
| receiveVoucher | Create / Delete | 快捷收款单 |
| retail | Create | 快捷零售单 |

**业务场景：**
- 销货单 → 其他应收单 → 收/付款单（收款流程）
- 采购入库单 → 其他应付单 → 收/付款单（付款流程）
- 费用单独立于采购/销售，用于日常费用管理

---

### 7. 会计凭证（2 个服务 / 7 个接口）

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| doc | 会计凭证 | Create / CreateBatch / Delete / DeleteBatch / Query / ReturnCodeCreate | 手工凭证录入 |
| DocType | 凭证类别 | Query | 凭证类型（收款/付款/转账等） |

**业务场景：**
- 业务单据自动生成凭证（系统对接）
- 手工录入调整凭证
- 凭证类别管理

---

### 8. 基础档案（29 个服务 / 84 个接口）

**模块定位：** 企业基础数据管理，是所有业务单据的数据支撑。

#### 往来单位

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| partner | 往来单位 | Create / CreateBatch / Update / Delete / Combine / Query / QueryPage | 客户 + 供应商统一管理 |
| partnerClass | 往来单位分类 | Create / Query | 往来单位分类体系 |

#### 存货相关

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| inventory | 存货 | Create / CreateBatch / Update / UpdateBatch / UpdateImage / Query / QueryPage / QueryInventoryPriceWithoutFormula | 商品/物料主数据 |
| inventoryClass | 存货分类 | Create / Query | 存货分类体系 |
| inventoryUnit | 存货计量单位 | Query | 存货计量单位 |

#### 组织档案

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| warehouse | 仓库 | Create / Query | 仓库档案 |
| department | 部门 | Create / Query | 部门档案（body 格式特殊：`{"dto":{}}`） |
| person | 员工 | Create / Update / Query | 员工档案（body 格式特殊：`{"dto":{}}`） |

#### 财务档案

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| Account | 科目 | Query | 会计科目表（body 格式特殊：`{"dto":{}}`） |
| Income | 收入科目 | Create / Delete / Update / Query | 收入类科目 |
| Expense | 费用科目 | Create / Delete / Update / Query | 费用类科目 |
| SettleStyle | 结算方式 | Query | 结算方式（现金/银行/承兑等，body 格式特殊：`{"dto":{}}`） |

#### 计量档案

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| Unit | 计量单位 | Create / Delete / Update / Query | 基本计量单位 |
| UnitGroup | 计量单位组 | Create / Delete / Query | 计量单位组（如：箱/件/个的换算关系） |

#### 生产档案

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| bom | 物料清单 | Create / Update / Delete / Audit / UnAudit / Query / QueryPage | BOM 结构定义 |
| process | 工序 | Create / Query | 工序定义 |
| routing | 工艺路线 | Create / Query | 工艺路线定义 |

#### 项目档案

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| ProjectClass | 项目分类 | Create / Query | 项目分类 |
| Project | 项目 | Create / Update / Query2 | 项目档案 |

#### 会员档案

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| member | 会员 | CreateBatch / CreateMember / Query / Update / 会员类型变更 / 会员档案 / 储值卡列表 | 会员主数据 |
| integral | 会员积分 | Create / Query | 会员积分管理 |
| membertype | 会员类型 | Query | 会员等级/类型 |
| memberStorage | 会员储值 | Create / CreateMemberStorage / CheckMemberStorageByExternalCode | 会员储值卡管理 |

#### 费用档案

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| ExpenseAgreementForOuter | 费用协议 | Create / Query | 外部费用协议 |
| ExpensePlanForOuter | 费用方案 | Create / Query | 外部费用方案 |

#### 自定义档案

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| userDefineArchiveAPI | 自定义档案 | Query / QueryArchive | 用户自定义档案 |
| freeItem | 自由项 | Create / Query | 自由项定义 |

#### 系统辅助

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| PartnersAccountRpt | 往来账报表 | Query | 往来账查询 |
| UserDefineItemAPI | 自定义项模板 | QueryUserdefInfo | 自定义项查询 |
| EnumRest | 枚举档案 | AddEnum / AddEnumItem / DeleteEnumAndEnumItemsByIdEnum / DeleteEnumItem / GetEnumByName / GetEnumByTitle | 枚举值管理 |
| basicarchivesreference | 档案引用 | CreateBatch / DeleteBatch | 档案批量引用 |
| AccountAux | 辅助核算 | ApplyAuxList | 辅助核算应用 |
| ScmCommon | 单据自定义项更新 | UpdateVoucherDetailUserDef / UpdateVoucherPriUserDef | 单据自定义项 |
| attres | 附件管理 | ApiGetAttachment / ApiUploadAttachmentUrl | 附件上传/下载 |

---

### 9. 价格管理（2 个服务 / 12 个接口）

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| CustomerAdjustPriceOpenApi | 客户价格本调价单 | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 调整客户专属价格 |
| VendorAdjustPriceOpenApi | 供应商价格本调价单 | Create / FindVoucherList / GetVoucherDTO / Audit / UnAudit / Delete | 调整供应商供货价格 |

**业务场景：**
- 客户价格本：不同客户不同价格体系
- 供应商价格本：不同供应商不同采购价
- 调价单审核后生效

---

### 10. 报表分析（4 个服务 / 10 个接口）

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| reportQuery | 通用报表查询 | GetReportData / GetBalanceSumRpt / GetGroupInfosByReportTitle / GetReportInfosExt / GetSearchItemsByReportTitle / GetTableColsByReportTitle | 所有业务报表数据查询 |
| SAReportQuery | 销售报表查询 | CustomerCreditQuery | 客户信用分析 |
| SNReportQuery | 序列号报表 | SNInfo / SNTrace | 序列号查询和追溯 |
| TaxOpenAPI | 税务/三大财务报表 | FindTaxTable | 资产负债表、利润表、现金流量表 |

**⚠️ 注意：** 资产负债表/利润表/现金流量表不在此系统（FormReport 套表），改用 `chanjet_execute` 调用 `TaxOpenAPI/FindTaxTable`。

---

### 11. 系统服务（5 个服务 / 20 个接口）

| 服务名 | 中文名 | 操作 | 说明 |
|--------|--------|------|------|
| serialNumber | 序列号 | GetSnAccountDetailDtos | 序列号库存明细 |
| VoucherAPIService | 通用单据服务 | Audit / BatchUpdateSysVouDefField / CreateReference / Delete / DeleteReference / GetColumnSetByBizCode / GetDefVoucherDTO / GetSearchItemByBizCode / GetVoucherInfoByBizCode / Save / SendCustomMessage / UnAudit / Update | 通用单据操作（跨业务类型） |
| InventoryCostingOpenApi | 库存成本核算 | GetIndividualPriceForAPI / RestartCostring | 个别计价成本查询 / 重新核算 |
| purchaseArrival | 进货(简易) | Create | 快捷进货单 |
| memberStorage | 会员储值 | Create / CreateMemberStorage / CheckMemberStorageByExternalCode | 会员储值管理 |

---

## 五、总览

| 模块 | 服务数 | 接口数 | 核心功能 |
|------|--------|--------|----------|
| 销售管理 | 9 | 47 | 销售订单→销货单→出库→开票 |
| 采购管理 | 6 | 32 | 采购订单→进货→入库→开票 |
| 库存管理 | 21 | 77 | 出入库、调拨、盘点、成本核算 |
| 生产管理 | 5 | 28 | 生产加工、检验、领料、工艺路线 |
| 委外管理 | 3 | 21 | 委外加工、发料、入库 |
| 财务管理 | 10 | 38 | 收付款、费用、零售结算 |
| 会计凭证 | 2 | 7 | 手工凭证、凭证类别 |
| 基础档案 | 29 | 84 | 往来单位、存货、仓库、部门、员工、科目、BOM、会员等 |
| 价格管理 | 2 | 12 | 客户/供应商价格本调价 |
| 报表分析 | 4 | 10 | 通用报表、销售报表、序列号报表、三大财务报表 |
| 系统服务 | 5 | 20 | 序列号、通用单据、成本核算、会员储值 |
| **总计** | **96** | **376** | 覆盖销售、采购、库存、生产、委外、财务全链路 |

---

## 六、核心报表清单（100+ 张）

### 销售类报表（31 张）

| 报表名称 | 英文名 | 用途 |
|----------|--------|------|
| 销售毛利分析表 | SA_GrossProfitAnalysisRpt | 按存货/客户/部门分析销售毛利 |
| 销售订单明细表 | SA_SaleOrderDetailRpt | 销售订单逐笔明细 |
| 销售订单执行表 | SA_SaleOrderExecuteRpt | 订单执行进度（出库/开票/收款） |
| 销售订单统计表 | SA_SaleOrderSumRpt | 订单汇总统计 |
| 销售出库单明细表 | ST_SaleDispatchDetailRpt | 出库单逐笔明细 |
| 销售出库单统计表 | ST_SaleDispatchSumRpt | 出库单汇总统计 |
| 销售发票明细表 | SA_SaleInvoiceDetailRPT | 发票逐笔明细 |
| 销售发票统计表 | SA_SaleInvoiceSumRPT | 发票汇总统计 |
| 销售价格波动分析表 | SA_PriceFluctuationRpt | 价格变化趋势分析 |
| 销售综合统计分析表 | SA_SaleSumAnalysisRpt | 多维度销售综合分析 |
| 销售排行榜 | SA_SaleOrderRankRpt | 按金额/数量排名 |
| 商品销售综合排行榜 | SA_SalesComprehensiveRankRpt | 商品维度综合排名 |
| 销售成本构成明细表 | CO_SAConstituteDetailRpt | 销售成本结构分析 |
| 销售成本还原明细表 | CO_SARecoveryDetailRpt | 成本还原分析 |
| 销售出库成本情况 | CO_SARecoverySaleOutDetailRpt | 出库成本明细 |
| 销售收入成本配比表 | ST_RevenueCostAnalysisRpt | 收入成本匹配分析 |
| 销售交款 | ARAP_InstantReceiveRpt | 销售收款情况 |
| 销售日报 | SA_DailySaleRpt | 每日销售汇总 |
| 销售备货预警 | SA_UseDeliveryWarningRpt | 缺货/备货不足预警 |
| 销售订单生产进度表 | SA_SaleOrderMPTrackRpt | 订单关联生产进度 |
| 销售订单采购执行统计表 | SA_SaleOrderPurchaseExecuteSumRpt | 订单关联采购进度 |
| 销售发票收款执行表 | SA_SaleInvoiceExecuteRPT | 发票收款进度 |
| 销售出库开单执行表 | SA_SaleDispatchBilledExecuteRpt | 出库开票执行进度 |
| 经营毛利统计表 | SA_BusinessGrossProfitSumRpt | 经营毛利汇总 |
| 终端销售分析表 | DI_TerminalSaleAnalysisRpt | 终端销售分析 |
| 项目销售业绩明细表 | RE_SalesPerformanceDetailRpt | 按项目统计销售业绩 |
| 项目销售业绩汇总表 | RE_SalesPerformanceSumRpt | 项目销售业绩汇总 |
| 销售情况查询 | SA_SalesReportMessageRpt | 销售情况综合查询 |
| 销售订单执行情况 | SA_SaleOrderOverViewExecuteRpt | 订单执行总览 |
| 有销售新客户 | CM_NewCustomerHasSaleRpt | 新客户销售分析 |
| 产品正向追溯销售出库信息明细表 | QT_QualityTraceByProductRDRecordInfoDetailRpt | 质量追溯 |

---

### 采购类报表（14 张）

| 报表名称 | 英文名 | 用途 |
|----------|--------|------|
| 采购订单明细表 | PU_PurchaseOrderDetailRpt | 采购订单逐笔明细 |
| 采购订单执行表 | PU_PurchaseOrderExecuteRpt | 订单执行进度（入库/开票/付款） |
| 采购订单统计表 | PU_PurchaseOrderSumRpt | 订单汇总统计 |
| 采购综合统计分析表 | PU_PurchaseIntegratedSumRpt | 多维度采购综合分析 |
| 采购入库单明细表 | ST_PurchaseReceiveDetailRpt | 入库单逐笔明细 |
| 采购入库单统计表 | ST_PurchaseReceiveSumRpt | 入库单汇总统计 |
| 采购发票明细表 | PU_PurchaseInvoiceDetailRPT | 发票逐笔明细 |
| 采购发票统计表 | PU_PurchaseInvoiceSumRPT | 发票汇总统计 |
| 采购价格波动分析表 | AA_PurchasePriceFluctuationRpt | 采购价格变化趋势 |
| 采购进货预警 | SA_UsePurchaseWarningRpt | 进货延期预警 |
| 采购发票付款执行表 | PU_PurchaseInvoiceExecuteRPT | 发票付款进度 |
| 采购入库单执行表 | ST_RDSTempValueRpt | 入库执行进度 |
| 销售订单采购执行统计表 | SA_SaleOrderPurchaseExecuteSumRpt | 销售订单关联采购进度 |
| 销售订单采购生产执行统计表 | SA_SaleOrderPurManuExecuteRPT | 销售订单关联采购+生产进度 |

---

### 库存类报表（14 张）

| 报表名称 | 英文名 | 用途 |
|----------|--------|------|
| 库存状况表 ⭐ | ST_CurStockStatusOfInvRpt | 各仓库存货现存量、可用量、结存金额 |
| 库存台账 | ST_RDSRunningAccountRpt | 存货出入库流水账 |
| 收发存汇总表 ⭐ | ST_RDSSummaryRpt | 期初+入库+出库=期末 汇总 |
| 库存周转率分析表 | ST_MaterialTurnoverRpt | 存货周转天数/周转率 |
| 呆滞存货分析表 | ST_ObsoleteMaterialRpt | 长期无动态的呆滞存货 |
| 库存资金占用分析表 | ST_CapitalOccupancyRpt | 库存占用的资金分析 |
| 最高库存预警 | ST_UseOutOfStockWarning | 超储预警 |
| 最低库存预警 | ST_UseShortOfStockWarning | 缺货预警 |
| 库存日报 | ST_RDSDailyPaperRpt | 每日库存变动 |
| 库存期初汇总表 | ST_PeriodStartOfStockRpt | 期初库存汇总 |
| 跨机构库存查询 | ST_CrossCurrentStockRpt | 多仓库/多机构库存汇总 |
| 库存存货毛利预估表 | AA_StoctInventoryGrossProfitEstimateRpt | 库存毛利预估 |
| 库存销量上报分析表 | DI_StockSalesAnalysisRpt | 库存与销售关联分析 |
| 库存销量上报明细表 | DI_StockSalesDetailRpt | 库存与销售明细 |

---

### 应收应付报表（17 张）

| 报表名称 | 英文名 | 用途 |
|----------|--------|------|
| 应收明细账 | ARAP_ReceiveAccountDetailRpt | 应收逐笔明细 |
| 应收总账 | ARAP_ReceiveAccountSumRpt | 应收汇总 |
| 应收账龄分析 | ARAP_ReceiveAgeAnalysisSumRpt | 应收账龄分段（30天/60天/90天+） |
| 应收账龄分析明细表 | GL_CustomerAgeAnalysisDetailRpt | 账龄分析逐笔明细 |
| 应收核销明细表 | ARAP_ReceiveCancelDetailRpt | 应收核销记录 |
| 应收日报 | ARAP_ReceiveDailyRpt | 每日应收变动 |
| 应付明细账 | ARAP_PaymentAccountDetailRpt | 应付逐笔明细 |
| 应付总账 | ARAP_PaymentAccountSumRpt | 应付汇总 |
| 应付账龄分析 | ARAP_PaymentAgeAnalysisSumRpt | 应付账龄分段 |
| 应付账龄分析明细表 | GL_SupplierAgeAnalysisDetailRpt | 账龄分析逐笔明细 |
| 应付核销明细表 | ARAP_PaymentCancelDetailRpt | 应付核销记录 |
| 其他应收单明细表 | CS_OtherReceiveVoucherDetailRpt | 其他应收逐笔明细 |
| 其他应收单统计表 | CS_OtherReceiveVoucherSumRpt | 其他应收汇总 |
| 其他应付单明细表 | CS_OtherPaymentVoucherDetailRpt | 其他应付逐笔明细 |
| 其他应付单统计表 | CS_OtherPaymentVoucherSumRpt | 其他应付汇总 |
| 往来资金预测表 | ARAP_AmountForecastSumRpt / GL_AmountForecastSumRpt | 未来资金流入/流出预测 |

---

### 生产类报表（15 张）

| 报表名称 | 英文名 | 用途 |
|----------|--------|------|
| 生产加工单执行表 | MP_ManufactureOrderExecuteRpt | 生产进度（完工/领料/检验） |
| 生产加工单材料明细表 | MP_ManufactureOrderMaterialDetailRpt | 生产领料逐笔明细 |
| 生产加工单材料统计表 | MP_ManufactureOrderMaterialSumRpt | 生产领料汇总 |
| 生产加工单工序明细表 | MP_ManufactureOrderProcessDetailRpt | 工序汇报明细 |
| 生产加工单工序统计表 | MP_ManufactureOrderProcessSumRpt | 工序汇报汇总 |
| 生产加工单产成品明细表 | MP_ManufactureOrderDetailRpt | 产成品入库明细 |
| 生产加工单产成品统计表 | MP_ManufactureOrderSumRpt | 产成品入库汇总 |
| 生产领用耗用结存表 | MP_ManufactureBalanceRpt | 材料领用/耗用/结存 |
| 生产成本构成明细表 | CO_ProductionCostReductionDetailRpt | 生产成本结构分析 |
| 生产成本还原明细表 | CO_ProductionReductionCompareDetailRpt | 成本还原对比分析 |
| 生产备料分析明细表 | MP_PraMaterialDetailRpt | 生产备料需求分析 |
| 生产完工预警 | MP_ManufactureOrderFinishAlarmRpt | 延期完工预警 |
| 销售订单生产进度表 | SA_SaleOrderMPTrackRpt | 销售订单关联生产进度 |
| 销售订单采购生产执行统计表 | SA_SaleOrderPurManuExecuteRPT | 销售订单关联采购+生产 |
| 产品正向追溯生产过程信息明细表 | QT_QualityTraceByProductStageInfoDetailRpt | 质量追溯 |

---

### 客户分析报表（12 张）

| 报表名称 | 英文名 | 用途 |
|----------|--------|------|
| 客户预警分析 | CM_CustomerWarningRpt | 客户异常预警 |
| 客户营销分析 | CM_CustomerMarketingAchievingRpt | 客户营销效果 |
| 活跃客户 | CM_ActiveCusAnalysisRpt | 近期有交易的活跃客户 |
| 新客户 | CM_NewCusAnalysisRpt | 新客户统计 |
| 高价值客户 | CM_HighValueCusAnalysisRpt | 高贡献客户识别 |
| 有销售新客户 | CM_NewCustomerHasSaleRpt | 已产生销售的新客户 |
| 即将流失客户 | CM_WillLostCusAnalysisRpt | 长期未交易客户预警 |
| 持续2月下滑客户 | CM_TowMontDeclineCusAnalysisRpt | 业绩连续下滑客户 |
| 动销品项数下滑客户 | CM_TowMontInvDeclineCusAnalysisRpt | 采购品类减少客户 |
| 订货周期异常客户 | CM_AbnormalOrderCycleCusAnalysisRpt | 订货周期异常客户 |
| 超期未跟进客户 | CM_OverdueVisitCusAnalysisRpt | 超过跟进期限客户 |
| 客户/供应商资质失效预警 | AA_PartnerCertificationAlarmRpt | 资质过期预警 |

---

### 资金类报表（5 张）

| 报表名称 | 英文名 | 用途 |
|----------|--------|------|
| 资金日报 | CS_FundDailyRpt | 每日资金变动 |
| 资金统计表 | CS_FundSumAccountRpt | 资金汇总统计 |
| 往来资金预测表 | ARAP_AmountForecastSumRpt / GL_AmountForecastSumRpt | 未来资金流入/流出预测 |

---

### 其他报表

| 报表名称 | 英文名 | 用途 |
|----------|--------|------|
| 零售毛利统计表 | RE_RetailGrossProfitSumRpt | 零售业务毛利分析 |
| 序列号报表 | SNReportQuery (SNInfo/SNTrace) | 序列号查询和追溯 |

---

## 七、关键规则与注意事项

### 1. 字段名不可猜测

| 场景 | 必须调用的工具 | 原因 |
|------|----------------|------|
| 单据字段 | `chanjet_column_info(bizCode="xxx")` | 每个单据的字段名不同，猜测极易出错 |
| 档案 SelectFields | `McpMetaService/GetArchiveSelectFields` | 查看档案允许的返回列范围 |
| 关联字段（存货/仓库/往来单位/部门） | 先查对应档案 Query | 必须使用真实 Code，不可用名称替代 |

**示例：**
```
❌ 错误: {"dto":{"InventoryName":"产品A"}}  // 字段名错误
✅ 正确: 先查 inventory Query 取得 Code "M001"，再填 {"dto":{"Inventory":{"Code":"M001"}}}
```

### 2. FindVoucherList 限制

- **只返回基础字段：** `[id, code, externalcode, ts]`
- **业务字段需用 GetVoucherDTO 获取：** 客户、金额、数量、明细行等
- **内置自动字段映射（best-effort）：** 会尝试把常见别名/中文标题/扁平键映射为真实 FieldName
- **关键流程优先用 chanjet_column_info：** 自动映射可能在元数据获取失败时按原样发送

### 3. GetReportData 注意事项

- **PageIndex 从 1 开始**（不是 0！传 0 会报"非第一页查询"错误，服务器虽会自动修正为 1，但应直接传 1）
- **第 2 页及以后必须携带：** TaskSessionID 和 SolutionID（从第 1 页响应中获取）
- **不要传 reportTitle：** 这是 MCP 内部字段，会自动剥离
- **数据量过大时分页：** 将多页数据存储在本地拼接

### 4. 常见错误

| 错误码 | 原因 | 解决方案 |
|--------|------|----------|
| EXERROR0001 | param 为 null | 用 `{"param":{}}` 而非 `{"param":null}` |
| HTTP 404 | 路径错误 | 用 chanjet_search 确认正确的 service 和 operation |
| HTTP 500 | 服务端错误 | 检查请求体格式，参考 chanjet_search 返回的示例 |
| 999 | 预开工日早于单据日期 | PreStartDate 和 PreFinishDate 必须 >= VoucherDate |

### 5. 生产加工单创建约束

- PreStartDate（预开工日）和 PreFinishDate（预完工日）必须 >= VoucherDate（单据日期）
- 否则后端返回 999 错误："预开工日不能早于单据日期！"

### 6. Body 格式特殊规则

- **大部分档案 Query：** `{"param":{}}` — 字段名 PascalCase（Code/Name/Disabled）
- **department/person/Account/SettleStyle Query：** `{"dto":{}}` — 特殊格式，注意区分
- **档案分页：** PageSize 放在 param 内（最大 1000），无 pageIndex
- **单据分页：** pageIndex 从 0 开始（FindVoucherList），pageSize 默认 10

---

## 八、查询策略速查

| 需求类型 | 工具路径 | 示例 |
|----------|----------|------|
| 查单据列表+详情 | search → execute(FindVoucherList) → execute(GetVoucherDTO) | 查销售订单列表和详情 |
| 创建单据 | column_info → 查档案取Code → execute(Create) → execute(Audit) | 新建销货单并审核 |
| 修改单据 | column_info → execute(GetVoucherDTO) → execute(Update) → execute(Audit) | 修改销售订单 |
| 删除单据 | execute(Delete) | 删除未审核单据 |
| 审核/反审核 | execute(Audit/UnAudit) | 审核销货单/反审核 |
| 关闭/打开单据 | execute(Close/Open) | 关闭已完成订单 |
| 查报表数据 | reportinfo(keyword) → reportinfo(reportTitle) → execute(GetReportData) | 查销售毛利分析表 |
| 查档案列表 | execute(service, "Query", '{"param":{}}') | 查所有存货 |
| 查档案（模糊） | execute(service, "Query", '{"param":{"Name":"%关键词%"}}') | 模糊查询存货 |
| 查现存量 | execute("currentStock", "Query" 或 "QueryByTime") | 查当前/历史库存 |
| 查三大报表 | execute("TaxOpenAPI", "FindTaxTable") | 查资产负债表/利润表/现金流量表 |
| 查序列号 | execute("SNReportQuery", "SNInfo" / "SNTrace") | 序列号查询/追溯 |
| 查往来账 | execute("PartnersAccountRpt", "Query", '{"param":{}}') | 往来账查询 |
| 创建存货 | 查分类/单位Code → execute("inventory", "Create") | 新建商品档案 |
| 创建往来单位 | execute("partner", "Create", '{"dto":{...}}') | 新建客户/供应商 |

---

## 九、常用搜索关键词

| 搜索词 | 找什么 | 关联服务 |
|--------|--------|----------|
| "销售" | 销售订单、销货单、销售出库、销售发票、销售报表 | SaleOrderOpenApi、SaleDeliveryOpenApi、SAReportQuery |
| "采购" | 采购订单、进货单、采购入库、采购发票 | PurchaseOrderOpenApi、PurchaseArrivalOpenApi |
| "库存" | 存货档案、现存量、存货分类、库存成本 | inventory、currentStock、InventoryCostingOpenApi |
| "出库" | 材料出库、其他出库、销售出库、出库调整 | MaterialDispatchOpenApi、OtherDispatchOpenApi、SaleDispatchOpenApi |
| "入库" | 采购入库、产成品入库、其他入库、委外入库、入库调整 | PurchaseReceiveOpenApi、ProductReceiveOpenApi、DelegateReceiveOpenApi |
| "调拨" | 调拨单 | TransVoucherOpenApi |
| "盘点" | 盘点单 | CheckVoucherOpenApi |
| "生产" | 生产加工单、工序、工艺路线、生产报表 | ManufactureOrderOpenApi、process、routing |
| "委外" | 委外加工单、委外发料单、委外入库单 | OutSourceOrderOpenApi、DelegateDispatchOpenApi、DelegateReceiveOpenApi |
| "往来" | 往来单位、往来单位分类、往来账报表 | partner、partnerClass、PartnersAccountRpt |
| "应收" | 应收报表、其他应收单 | ARAP_* 报表、OtherReceiveVoucherOpenApi |
| "应付" | 应付报表、其他应付单 | ARAP_* 报表、OtherPaymentVoucherOpenApi |
| "收款/付款" | 收付款单、付款申请单、收款单(简易) | ReceivePaymentVoucherOpenApi、ArapPrepaymentRequisitionOpenApi |
| "费用" | 费用单、费用科目、费用协议 | expenseVoucher、Expense、ExpenseAgreementForOuter |
| "财务" | 三大财务报表 | TaxOpenAPI |
| "凭证" | 会计凭证、凭证类别 | doc、DocType |
| "科目" | 科目、收入科目、费用科目 | Account、Income、Expense |
| "仓库" | 仓库档案 | warehouse |
| "部门" | 部门档案 | department |
| "BOM" | 物料清单 | bom |
| "计量" | 计量单位、计量单位组、存货计量单位 | Unit、UnitGroup、inventoryUnit |
| "零售" | 零售单、零售结算 | retail、RetailSettleOpenApi |
| "客户" | 客户分析报表 | CM_* 报表 |
| "报表" | 通用报表、销售报表、财务报表 | reportQuery、SAReportQuery、TaxOpenAPI |
| "序列号" | 序列号查询、追溯 | serialNumber、SNReportQuery |
| "结算" | 结算方式、零售结算 | SettleStyle、RetailSettleOpenApi |
| "项目" | 项目、项目分类 | Project、ProjectClass |
| "成本" | 库存成本核算 | InventoryCostingOpenApi |
| "价格" | 价格本调价单、销售价格 | CustomerAdjustPriceOpenApi、VendorAdjustPriceOpenApi、SalePrice |
| "会员" | 会员、会员积分、会员类型、会员储值 | member、integral、membertype、memberStorage |
| "存货" | 存货档案、存货分类、存货价格、存货多编码 | inventory、inventoryClass、CustomerInventoryPriceWithoutFormula |
| "自定义" | 自定义档案、自由项、自定义项模板 | userDefineArchiveAPI、freeItem、UserDefineItemAPI |
| "附件" | 附件管理 | attres |
| "枚举" | 枚举档案 | EnumRest |
| "辅助核算" | 辅助核算 | AccountAux |
| "单据" | 通用单据服务、单据自定义项 | VoucherAPIService、ScmCommon |

---

## 十、业务单据流转关系

### 销售业务流
```
销售订单 → 销货单 → 销售出库单 → 销售发票
  ↓           ↓          ↓
其他应收单 → 收/付款单
```

### 采购业务流
```
采购订单 → 进货单 → 采购入库单 → 采购发票
  ↓           ↓          ↓
其他应付单 → 收/付款单
```

### 生产业务流
```
销售订单 → 生产加工单 → 领料申请单 → 材料出库单
                    ↓
              生产过程检验单
                    ↓
              产成品入库单 → 销货单
```

### 委外业务流
```
委外加工单 → 委外发料单 → 委外商加工 → 委外入库单
```

### 库存业务流
```
采购入库 → 库存持有 → 销售出库
    ↕              ↕
  调拨单         盘点单（盘盈/盘亏）
```

---

## 十一、快速参考卡片

### 创建单据 checklist
- [ ] 调用 chanjet_column_info 获取字段名
- [ ] 查询往来单位档案取得 Code
- [ ] 查询存货档案取得 Code
- [ ] 查询仓库档案取得 Code
- [ ] 查询部门档案取得 Code（如需要）
- [ ] 调用 Create 创建单据
- [ ] 调用 Audit 审核单据

### 查询报表 checklist
- [ ] 调用 chanjet_reportinfo(keyword) 找到报表
- [ ] 调用 chanjet_reportinfo(reportTitle) 获取字段定义
- [ ] 调用 GetReportData（pageIndex 从 1 开始）
- [ ] 数据量大时分页查询（携带 TaskSessionID 和 SolutionID）

### 常见错误 checklist
- [ ] param 不为 null（用 `{"param":{}}`）
- [ ] 字段名来自 chanjet_column_info（不猜测）
- [ ] 关联字段使用真实 Code（不猜编码）
- [ ] GetReportData 的 pageIndex 从 1 开始
- [ ] 生产加工单的日期 >= 单据日期
