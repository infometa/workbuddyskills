# 📊 L2C 漏斗分析引擎

本文件定义了如何利用 Cordys CRM 统计 API 进行 L2C 管道分析和漏斗计算。

---

## 1. 核心统计 API

### 1.1 首页统计

| 端点 | 用途 | 响应 |
|------|------|------|
| `POST /home/statistic/lead` | 线索统计 | 本年/本月/本周/本日的新增线索数 |
| `POST /home/statistic/opportunity` | 商机统计 | 本年/本月/本周/本日的商机数 + 金额 |
| `POST /home/statistic/opportunity/success` | 赢单统计 | 本年/本月/本周/本日的赢单商机数 + 金额 |
| `POST /home/statistic/opportunity/underway` | 进行中商机 | 本年/本月/本周/本日进行中的商机数 + 金额 |

**请求体**（`HomeStatisticBaseSearchRequest`）：

```json
{
  "searchType": "SELF",
  "deptIds": ["dept_id_1"],
  "timeField": "CREATE_TIME",
  "userField": "OWNER",
  "priorPeriodEnable": true
}
```

**角色映射**：

| 角色 | searchType | deptIds |
|------|-----------|---------|
| 销售 | `SELF` | 空 |
| 经理 | `DEPARTMENT` | Cordys.md 中的 `{departmentId}`（展开子部门） |
| 高管 | `ALL` | 空 |
| 财务 | `ALL` | 空 |

### 1.2 模块统计

| 端点 | 用途 | 响应 |
|------|------|------|
| `POST /contract/statistic` | 合同统计 | `{amount, averageAmount}` |
| `POST /contract/payment-record/statistic` | 回款统计 | `{amount, averageAmount}` |
| `POST /opportunity/statistic` | 商机统计 | `{amount, averageAmount}` |
| `POST /order/statistic` | 订单统计 | `{amount, averageAmount}` |

**请求体**（`BaseCondition`）：

```json
{
  "viewId": "ALL",
  "combineSearch": {
    "searchMode": "AND",
    "conditions": [
      {"value": "MONTH", "operator": "DYNAMICS", "name": "startTime", "type": "TIME_RANGE_PICKER"}
    ]
  }
}
```

### 1.3 客户级统计

| 端点 | 响应 |
|------|------|
| `GET /account/contract/statistic/{accountId}` | `{totalAmount}` |
| `GET /account/contract/payment-plan/statistic/{accountId}` | `{totalPlanAmount}` |
| `GET /account/contract/payment-record/statistic/{accountId}` | `{totalAmount, receivedAmount, pendingAmount}` |
| `GET /account/invoice/statistic/{accountId}` | `{contractAmount, uninvoicedAmount, invoicedAmount}` |

### 1.4 合同级统计

| 端点 | 响应 |
|------|------|
| `GET /contract/invoice/statistic/{contractId}` | `{contractAmount, uninvoicedAmount, invoicedAmount}` |

---

## 2. 漏斗查询

### 2.1 销售视角

```bash
cordys.sh crm stat-home lead
cordys.sh crm stat-home opportunity
cordys.sh crm stat contract '{"viewId":"SELF","combineSearch":{"conditions":[{"value":"MONTH","operator":"DYNAMICS","name":"startTime","type":"TIME_RANGE_PICKER"}]}}'
```

### 2.2 经理视角

```bash
cordys.sh crm stat-home lead '{"searchType":"DEPARTMENT","deptIds":["id1","id2"],"timeField":"CREATE_TIME","userField":"OWNER","priorPeriodEnable":true}'
```

### 2.3 高管视角

```bash
cordys.sh crm stat-home lead '{"searchType":"ALL","timeField":"CREATE_TIME","userField":"OWNER","priorPeriodEnable":true}'
```

---

## 3. 漏斗输出格式

输出格式见 `core/output-engine.md` §9。

`HomeStatisticSearchResponse` 字段：

```json
{ "value": 45, "priorPeriodCompareRate": 0.18 }
```

→ 输出：`线索 45 条（📈 +18% vs 上期）`

---

## 4. 管道预测

```bash
# 进行中商机总金额
cordys.sh crm stat-home opportunity/underway '{"searchType":"ALL","timeField":"CREATE_TIME","userField":"OWNER"}'

# 全公司待回款金额
cordys.sh crm stat-home opportunity/success '{"searchType":"ALL","timeField":"CREATE_TIME","userField":"OWNER"}'
```

---

## 5. API 速查表

| 场景 | API |
|------|-----|
| 我的线索数 | `crm stat-home lead` |
| 部门线索数 | `crm stat-home lead '{"searchType":"DEPARTMENT",...}'` |
| 合同金额汇总 | `crm stat contract` |
| 回款汇总 | `crm stat contract/payment-record` |
| 客户回款概览 | `crm acct-sub payment-record-stat {id}` |
| 客户开票概览 | `crm acct-sub invoice-stat {id}` |
| 商机管道金额 | `crm stat-home opportunity/underway` |
