# 🔗 L2C 链路追踪引擎

本文件定义了 Cordys CRM 中 **Lead-to-Cash 全链路** 的模块关联关系和追踪方法。

---

## 1. L2C 链路模型

```
线索(Lead) ──转化API──▶ 客户(Account)
                             │
                             ├──▶ 联系人(Contact)
                             │
                             └──▶ 商机(Opportunity) ──customerId──▶ 客户
                                       │
                                       ├──▶ 报价单(Quotation) ──opportunityId──▶ 商机
                                       │
                                       └──▶ 合同(Contract) ──customerId──▶ 客户
                                                │
                                                ├──▶ 回款计划(PaymentPlan) ──contractId──▶ 合同
                                                │     └──▶ 回款记录(PaymentRecord) ──paymentPlanId──▶ 计划
                                                │
                                                ├──▶ 订单(Order) ──contractId──▶ 合同
                                                │
                                                └──▶ 发票(Invoice) ──contractId──▶ 合同
```

> **重要发现**：Lead 没有 `accountId` 字段，转化通过 `POST /lead/transition/account` API 完成。Contract 没有 `opportunityId` 字段，合同通过 `customerId` 关联客户。

---

## 2. 已验证关联字段表

| 源模块 | 目标模块 | 字段名（已验证） | 方向 |
|--------|---------|-----------------|------|
| Lead | Account | 无字段 — 使用 `POST /lead/transition/account` 转化 | API 操作 |
| Opportunity | Account | `customerId` | 商机→客户 |
| Contract | Account | `customerId` | 合同→客户 |
| Order | Account | `customerId` | 订单→客户 |
| Order | Contract | `contractId` | 订单→合同 |
| Quotation | Opportunity | `opportunityId` | 报价单→商机 |
| PaymentPlan | Contract | `contractId` | 回款计划→合同 |
| PaymentRecord | Contract | `contractId` | 回款记录→合同 |
| PaymentRecord | PaymentPlan | `paymentPlanId` | 回款记录→计划 |
| Invoice | Contract | `contractId` | 发票→合同 |

### 常用字段名速查

| 模块 | 字段 | Schema 来源 |
|------|------|------------|
| Contract | `approvalStatus` | ContractListResponse |
| Contract | `startTime` | ContractListResponse（合同开始时间） |
| Contract | `endTime` | ContractListResponse（合同结束时间） |
| PaymentPlan | `planStatus` | ContractPaymentPlanListResponse |
| PaymentPlan | `planAmount` | ContractPaymentPlanListResponse |
| PaymentPlan | `planEndTime` | ContractPaymentPlanListResponse（计划回款日期） |
| PaymentRecord | `recordAmount` | ContractPaymentRecordResponse |
| PaymentRecord | `recordEndTime` | ContractPaymentRecordResponse（实际回款日期） |

---

## 3. 链路追踪策略

### 3.1 L2C 实际链路

由于 Contract 没有 `opportunityId`，实际的追踪路径为：

```
起点: lead/{id}
  ├─ 线索详情：cordys.sh crm get lead {id}
  ├─ 线索→客户转化通过 POST /lead/transition/account（无字段关联）
  ├─ 客户名下商机：cordys.sh crm acct-sub opportunity {accountId}
  ├─ 客户名下合同：cordys.sh crm acct-sub contract {accountId}
  ├─ 客户回款统计：cordys.sh crm acct-sub payment-record-stat {accountId}
  └─ 客户开票统计：cordys.sh crm acct-sub invoice-stat {accountId}
```

### 3.2 Customer 360（公司全景）

```
关键词: 华星科技
  ├─ 1. cordys.sh crm glocount 华星科技 → 各模块命中计数
  ├─ 2. 锁定 account ID
  ├─ 3. 并行调用客户子资源：
  │     ├─ cordys.sh crm acct-sub contract {id}           → 客户合同列表
  │     ├─ cordys.sh crm acct-sub opportunity {id}         → 客户商机列表
  │     ├─ cordys.sh crm acct-sub order {id}               → 客户订单列表
  │     ├─ cordys.sh crm acct-sub contract-stat {id}       → 合同总额(一行)
  │     ├─ cordys.sh crm acct-sub payment-record-stat {id} → 回款概览(一行)
  │     └─ cordys.sh crm acct-sub invoice-stat {id}        → 开票概览(一行)
  └─ 4. 输出 360 视图
```

### 3.3 合同全线追踪

```
起点: contract/{id}
  ├─ cordys.sh crm get contract {id}          → 合同详情
  ├─ cordys.sh crm get account {customerId}   → 通过 customerId 追溯到客户
  ├─ cordys.sh crm acct-sub opportunity {customerId} → 客户名下商机
  ├─ cordys.sh crm contract-sub invoice-stat {id}     → 开票统计
  ├─ cordys.sh crm stat contract/payment-record '{...contractId...}' → 回款统计
  └─ cordys.sh crm page contract/payment-plan '{...contractId...}'   → 回款计划
```
