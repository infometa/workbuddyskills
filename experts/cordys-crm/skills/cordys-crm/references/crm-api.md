# CORDYS CRM API 参考

> CLI 命令构建细节请见 `../core/cli-spec.md`。本文件专注于原始 API 端点和请求/响应结构。
>
> **目录**
>
> 1. [模块概览](#1-模块概览)
> 2. [通用请求结构](#2-通用请求结构)
> 3. [常用 HTTP 端点](#3-常用-http-端点)
> 4. [请求示例](#4-请求示例)
> 5. [响应解析](#5-响应解析)
> 6. [错误处理建议](#6-错误处理建议)
> 7. [最佳实践](#7-最佳实践)
> 8. [附录：字段/filters 例子](#8-附录字段filters-例子)

---

## 1. 模块概览
| 模块 | 描述                             |
| --- |--------------------------------|
| `lead` | 潜在客户（线索）记录，用于销售团队初步跟进。         |
| `account` | 客户/公司基础信息，包含行业、地点、负责人等。        |
| `opportunity` | 商机（机会）记录，表示销售流程中的具体案子。         |
| `contract` | 合同及其回款、发票等子资源，用于追踪签署后的收款与交付状态。 |
| `lead-pool` | 线索池，用于共享线索。                    |
| `account-pool` | 公海，用于共享客户。                     |

你在自然语言中提到的模块名，转换成命令时就能直接定位到本文档中所列的模块。

`contract` 模块还有几个常用的二级资源：`contract/payment-plan`（回款计划）、`invoice`、`contract/business-title`（工商抬头）、`contract/payment-record` 以及 `opportunity/quotation`，CLI 仍然沿用 `page`/json 的方式访问它们。

---

## 2. 通用请求结构

> 完整的 JSON Body 模板及字段说明见 `../core/cli-spec.md#2-分页默认结构`。本节仅补充 API 层面的注意事项。

关键字段简述：
- `current`：页码（从 1 开始）
- `pageSize`：每页条数，默认 30，建议 ≤200
- `sort`：排序对象，例如 `{"followTime":"desc"}`
- `combineSearch.conditions`：组合筛选条件
- `keyword`：全局关键词，模糊匹配名称/说明/电话等
- `viewId`：ALL（全部）/ SELF（我的）/ CUSTOMER_COLLABORATION（协作客户，仅 account）
- `filters`：精细字段级过滤

---

## 3. 常用 HTTP 端点
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/{module}/view/view` | 
| `GET` | `/{module}/{id}` | 获取单条记录详情。 |
| `POST` | `/{module}/page` | 发送上面模型的 JSON 进行分页查询（支持复杂过滤 + 关键词）。 |
| `POST` | `/search/{module}` | 全局搜索，JSON body 结构同上，但会额外在多个字段里查关键词。 |

> `cordys raw {METHOD} {PATH}` 就是让你任意组合上述请求，并手动填写 body/headers。

---

## 跟进计划与记录 API
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/{module}/follow/plan/page` | 查询某条资源的跟进计划，必须带 `sourceId`，支持 `status`、`myPlan`、`keyword` 等字段。|
| `POST` | `/{module}/follow/record/page` | 查询某条资源的跟进记录，以 `sourceId` 为主，并可额外筛 `keyword`。|

`module` 目前常用 `lead`、`account`、`opportunity` 等。需要查计划时请填 `status`（推荐 `ALL` / `UNFINISHED` / `FINISHED`），`myPlan` 表示是否只看本人创建的计划，`keyword` 和 `combineSearch` 仅用于模糊匹配；如果只传 `keyword` 将不带 `sourceId`，接口会返回空内容。

`page_payload` 只会补 `current` / `pageSize` / `sort` / `filters`，所以任何需要的 `sourceId` / `status` / `myPlan` 都必须在 JSON body 里显式提供。


## 4. 请求示例
### 分页列出商机（默认结构）
```bash
cordys.sh crm page opportunity "{\"current\":1,\"pageSize\":20,\"keyword\":\"线索\"}"
```
会调用 `POST /opportunity/page`，body 同上。

### 二级模块支持
Cordys CRM 里有一些隐藏在 `contract`｜ `opportunity` 模块下的二级资源（比如回款计划、发票等），`cordys` CLI 通过接受包含斜杠路径的模块名来访问它们。

- `cordys crm page contract/payment-plan`：查询回款计划的分页列表，支持传入关键词/JSON body，实际上调用的是 `POST /contract/payment-plan/page`。
- `cordys crm page invoice`：查询发票的分页列表，通过 `POST /invoice/page` 获取，每个条件都可以通过 `filters` 精细控制。
- `cordys crm page contract/business-title`：检索工商抬头列表，同样支持关键词/filters。
- `cordys crm page contract/payment-record`：查看回款记录列表，可结合关键词、`filters` 或 `viewId` 进行精细筛选。
- `cordys crm page opportunity/quotation`：查看报价单列表，可结合关键词、`filters` 或 `viewId` 进行精细筛选。

对这些二级模块的查询依旧遵循 `page_payload` 结构（`current`/`pageSize`/`sort`/`filters`）和关键字补全，因此你只需提供想要筛选的字段，AI 会自动补上分页元数据。

需要更专业的筛选能力时，可以直接把完整 JSON body 透传给 `cordys crm page contract/payment-plan '{…}'`，也可以用 `cordys raw` 指定路径（例如 `cordys raw POST /contract/payment-record/page '{...}'`）来跳过 CLI 结构化限制。

### 高级 search（带 filters + sort）
```bash
cordys.sh crm search account '{
  "current":1,
  "pageSize":40,
  "keyword":"云",
  "sort":{"followTime":"desc"},
  "combineSearch":{
    "searchMode":"AND",
    "conditions":[
      {"name":"industry","operator":"EQUALS","value":"科技","type":"INPUT"}
    ]
  },
  "filters":[
    {"field":"province","operator":"equals","value":"广东"}
  ]
}'
```
CLI 会请求 `/search/account`，按关键词+filters 精确过滤。

### 高级 search（和时间相关的动态搜索）
```bash
cordys.sh crm search account '{
  "current":1,
  "pageSize":40,
  "keyword":"云",
  "sort":{},
  "combineSearch":{
    "searchMode":"AND",
    "conditions":[
      {"value": "WEEK","operator": "DYNAMICS","name": "createTime","multipleValue": false,"type": "TIME_RANGE_PICKER"}
    ]
  },
  "filters":[]
}'
```
在combineSearch.conditions参数结构中，operator为DYNAMICS时，value为时间常量。

> 完整时间常量表见 `../core/cli-spec.md#5-动态时间过滤`。

如果查询n天前，value的值可以写成["CUSTOM,"+n+",BEFORE_DAY"]。
如果要查询两个时间段中间的数据，value可以写[较早的毫秒级时间戳，较晚的毫秒级时间戳]，同时operator为BETWEEN。

### 获取某条记录
```
cordys crm get lead 987654321
```
等价于 `GET /lead/987654321`。

---

### 跟进计划/记录请求示例
```bash
cordys.sh crm raw POST /lead/follow/record/page '{"sourceId":"927627065163785","current":1,"pageSize":10,"keyword":"回访"}'
cordys.sh crm raw POST /account/follow/plan/page '{"sourceId":"1751888184018919","current":1,"pageSize":10,"status":"ALL","myPlan":false}'
```
响应返回同样的分页结构，`data.list` 含 `planTime`、`status`、`ownerName`、`content` 等字段，例如：
```json
{
  "code":100200,
  "data":{
    "list":[
      {"id":"plan-1","planTime":"2026-02-28T14:00:00","status":"UNFINISHED","content":"跟进沟通需求"},
      {"id":"plan-2","planTime":"2026-02-26T10:00:00","status":"FINISHED","content":"确认资料"}
    ],
    "current":1,"pageSize":10,"total":2
  }
}

```

## 5. 响应解析
所有调用返回统一结构：
```json
{
  "code": 100200,
  "message": null,
  "messageDetail": null,
  "data": {
    "list": [ ... ],
    "total": 13,
    "pageSize": 30,
    "current": 1
  }
}
```
正常响应 `code=100200`。异常时会返回 `ACCESS_DENIED`、`INVALID_KEY`、`INVALID_REQUEST` 等，`message` 字段含具体原因。

---

## 6. 错误处理建议
1. **Token/密钥错误**：`INVALID_KEY`、`ACCESS_DENIED` → 检查 `CORDYS_ACCESS_KEY`/`CORDYS_SECRET_KEY`。
2. **参数问题**：`INVALID_REQUEST`、`INVALID_FILTER` → 检查 JSON 格式、字段名拼写。
3. **404/资源不存在**：要么 `id` 写错，要么没有访问权限。
4. **500+**：建议记录 `messageDetail` 并稍后重试。

对于任何非 `100200` 响应，我会把 `code`+`message` 反馈给你。

---

## 7. 最佳实践
- **分页不要太大**：大于 200 会容易超时。
- **关键词 + filters 组合**：先用 `keyword` 粗筛，再在 `combineSearch.conditions` 中加精确字段。
- **排序字段稳定**：使用 `sort` 降序 `followTime` 或 `createTime`，避免每次结果顺序浮动。
- **多条件用 `combineSearch`**：传多个 `conditions` 会自动 AND（或 OR，取决于 `searchMode`）。
- **控制层级**：JSON body 里按模块字段命名（大小写敏感）。

---

## 8. 附录：字段/filters 例子
| 字段 | 描述 | 示例值 |
| --- | --- | --- |
| `name` | 名称/标题 | `"Acme 商机"` |
| `stage` | 商机阶段 | `"Qualification"` |
| `owner` | 负责人 ID | `"user123"` |
| `industry` | 行业 | `"科技"` |
| `province` | 省份 | `"上海"` |

过滤示例：
```
{"field":"stage","operator":"equals","value":"Closed Won"}
```
更多字段可以在 CLI 输出的 `moduleFields` 里查看或用 `cordys raw GET /settings/fields?module={module}` 查询。

> **字段类型与操作符映射**：构造 `combineSearch.conditions` 时，每个 condition 的 `type` 字段必须正确填写目标字段的字段类型，`operator` 必须为该字段类型支持的操作符。详细映射表见 `core/cli-spec.md §5.4 字段类型 → 支持的操作符映射`。

---

## 9. 审批 API

审批模块是独立于 CRM 标准模块的专用 API，不走 `/module/page` 模式。

### 9.1 审批代办端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/approval-todo/pending/page` | POST | 待我审批分页 |
| `/approval-todo/processed/page` | POST | 我已处理的审批分页 |
| `/approval-todo/initiated/page` | POST | 我发起的审批分页 |
| `/approval-todo/cc/page` | POST | 抄送我的审批分页 |
| `/approval-todo/pending/count` | GET | 待审批统计 |

请求体（POST）使用标准 `page_payload` 结构（current/pageSize/sort/combineSearch/viewId/filters），外加 `resourceType` 字段（ALL/QUOTATION/CONTRACT/ORDER/INVOICE）。

### 9.2 审批操作端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/approval-action/approve` | POST | 同意 |
| `/approval-action/reject` | POST | 驳回 |
| `/approval-action/back` | POST | 退回 |
| `/approval-action/sign` | POST | 加签 |
| `/approval-action/revoke` | POST | 撤回 |
| `/approval-action/batch-approve` | POST | 批量同意 |
| `/approval-action/batch-reject` | POST | 批量驳回 |

### 9.3 审批资源端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/approval-resource/push` | POST | 提审 |
| `/approval-resource/revoke` | POST | 撤销 |
| `/approval-resource/simple-detail/{resourceId}` | GET | 列表详情 |
| `/approval-resource/detail/{resourceId}` | GET | 完整记录详情（含审批流进度） |

### 9.4 审批流设置端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/approval-flow/page` | POST | 审批流列表 |
| `/approval-flow/add` | POST | 新建审批流 |
| `/approval-flow/update` | POST | 更新审批流 |
| `/approval-flow/get/{id}` | GET | 审批流详情 |
| `/approval-flow/delete/{id}` | GET | 删除审批流 |
| `/approval-flow/enable/{id}` | GET | 启用/禁用（?enable=true\|false） |
| `/approval-flow/get-by-form-type/{formType}` | GET | 按表单类型获取审批流 |
| `/approval-flow/status-permission/setting/{formType}` | GET | 状态权限配置 |
| `/approval-flow/webhook/test` | POST | webhook 测试 |

### 9.5 完整命令示例

```bash
# 待我审批（只看合同类）
cordys.sh crm approval todo pending '{"current":1,"pageSize":30,"resourceType":"CONTRACT"}'

# 审批统计
cordys.sh crm approval todo count

# 同意审批
cordys.sh crm approval action approve '{"resourceId":"xxx","remark":"同意"}'

# 驳回
cordys.sh crm approval action reject '{"resourceId":"xxx","remark":"金额不符，请修改后重新提交"}'

# 退回（退回上一个节点）

cordys.sh crm approval action back '{"resourceId":"xxx","backNodeId":"node1","remark":"请补充附件"}'

# 加签
cordys.sh crm approval action sign '{"resourceId":"xxx","signUserIds":["user123"],"remark":"需要法务审核"}'

# 查看审批进度
cordys.sh crm approval resource detail RESOURCE_ID

# 提审
cordys.sh crm approval resource push '{"resourceId":"xxx"}'

# 撤销审批
cordys.sh crm approval resource revoke '{"resourceId":"xxx"}'

# 查看审批流配置
cordys.sh crm approval flow list '{"current":1,"pageSize":30}'

# 原始 API（等价）
cordys.sh raw POST /approval-todo/pending/page '{"current":1,"pageSize":30}'
cordys.sh raw GET /approval-todo/pending/count
```

### 9.6 审批响应结构

审批代办列表返回 `ApprovalTodoItemResponse` 对象，主要字段：

| 字段 | 说明 |
|------|------|
| `resourceId` | 审批资源ID |
| `resourceName` | 审批标题/名称 |
| `resourceType` | 资源类型（QUOTATION/CONTRACT/ORDER/INVOICE） |
| `status` | 审批状态 |
| `initiatorName` | 发起人 |
| `createTime` | 创建时间 |
| `currentApproverName` | 当前审批人 |

审批记录详情 `ApprovalInstanceDetail` 包含完整的审批流节点历史。

---

后续扩展，在 `references/` 下添加更多模块的字段列表（例如 `contacts.md`、`tasks.md`）或写出常用 JSON 模板。

---

## 10. L2C 链路 API 说明

### 10.1 统计 API（推荐优先使用）

> 使用 `cordys.sh crm stat`、`crm stat-home`、`crm acct-sub` 命令调用。

#### 首页统计

| 端点 | 用途 | 请求体 |
|------|------|--------|
| `POST /home/statistic/lead` | 线索统计 | `HomeStatisticBaseSearchRequest` |
| `POST /home/statistic/opportunity` | 商机统计 | 同上 |
| `POST /home/statistic/opportunity/success` | 赢单统计 | 同上 |
| `POST /home/statistic/opportunity/underway` | 进行中商机统计 | 同上 |
| `GET /home/statistic/department/tree` | 用户部门权限树 | — |

`HomeStatisticBaseSearchRequest`：
```json
{
  "searchType": "SELF",          // ALL | SELF | DEPARTMENT
  "deptIds": ["dept_id"],        // DEPARTMENT 时必填
  "timeField": "CREATE_TIME",    // CREATE_TIME | EXPECTED_END_TIME | ACTUAL_END_TIME
  "userField": "OWNER",          // CREATE_USER | OWNER
  "priorPeriodEnable": true      // 返回上期数据做环比
}
```

响应（`HomeClueStatistic`）：
```json
{
  "todayClue":     { "value": 3,  "priorPeriodCompareRate": 0.5 },
  "thisWeekClue":  { "value": 12, "priorPeriodCompareRate": 0.2 },
  "thisMonthClue": { "value": 45, "priorPeriodCompareRate": 0.18 },
  "thisYearClue":  { "value": 120, "priorPeriodCompareRate": 0.26 }
}
```

响应（`HomeOpportunityStatistic`，含金额字段）：
```json
{
  "todayOpportunity":              { "value": 1, "priorPeriodCompareRate": 0 },
  "thisWeekOpportunity":           { "value": 5, "priorPeriodCompareRate": 0.25 },
  "thisMonthOpportunity":          { "value": 18, "priorPeriodCompareRate": 0.12 },
  "thisYearOpportunity":           { "value": 60, "priorPeriodCompareRate": 0.3 },
  "todayOpportunityAmount":        { "value": 50000, "priorPeriodCompareRate": -1.0 },
  "thisWeekOpportunityAmount":     { "value": 320000, "priorPeriodCompareRate": 0.4 },
  "thisMonthOpportunityAmount":    { "value": 1200000, "priorPeriodCompareRate": 0.15 },
  "thisYearOpportunityAmount":     { "value": 5000000, "priorPeriodCompareRate": 0.35 }
}
```

> **字段含义**：`value` 为数值（线索是条数，商机金额单位是分），`priorPeriodCompareRate` 是较上期变化率（0.2=+20%，-0.1=-10%）。

#### 模块级统计

| 端点 | 请求体 | 响应 |
|------|--------|------|
| `POST /contract/statistic` | `BaseCondition` | `{amount, averageAmount}` |
| `POST /contract/payment-record/statistic` | `ContractPaymentRecordStatisticRequest` | `{amount, averageAmount}` |
| `POST /opportunity/statistic` | `OpportunitySearchStatisticRequest` | `{amount, averageAmount}` |
| `POST /order/statistic` | `BaseCondition` | `{amount, averageAmount}` |

#### 客户子资源统计

| 端点 | 响应 |
|------|------|
| `GET /account/contract/statistic/{accountId}` | `{totalAmount}` |
| `GET /account/contract/payment-plan/statistic/{accountId}` | `{totalPlanAmount}` |
| `GET /account/contract/payment-record/statistic/{accountId}` | `{totalAmount, receivedAmount, pendingAmount}` |
| `GET /account/invoice/statistic/{accountId}` | `{contractAmount, uninvoicedAmount, invoicedAmount}` |
| `GET /contract/invoice/statistic/{contractId}` | 同上 |

### 10.2 客户子资源 API（Customer 360 核心）

| 端点 | 方法 | 用途 |
|------|------|------|
| `POST /account/contract/page` | POST | 客户名下合同列表 |
| `POST /account/opportunity/page` | POST | 客户名下商机列表 |
| `POST /account/order/page` | POST | 客户名下订单列表 |
| `POST /account/contract/payment-plan/page` | POST | 客户回款计划列表 |
| `POST /account/contract/payment-record/page` | POST | 客户回款记录列表 |
| `POST /account/invoice/page` | POST | 客户发票列表 |

### 10.3 全局搜索增强

| 端点 | 用途 |
|------|------|
| `GET /global/search/module/count?keyword=X` | 全局搜索各模块命中计数 |
| `POST /advanced/search/account` | 高级搜索-客户 |
| `POST /advanced/search/lead` | 高级搜索-线索 |
| `POST /advanced/search/opportunity` | 高级搜索-商机 |

### 10.4 订单模块

Cordys CRM 存在订单（Order）模块，L2C 链路扩展为：

```
合同 → 订单 → 发票
```

| 端点 | 用途 |
|------|------|
| `POST /order/page` | 订单列表 |
| `POST /order/statistic` | 订单统计 |
| `POST /account/order/page` | 客户订单列表 |

### 10.5 仪表板

| 端点 | 用途 |
|------|------|
| `POST /dashboard/page` | 仪表板列表 |
| `GET /dashboard/detail/{id}` | 仪表板详情（含 resourceUrl） |
| `POST /dashboard/add` | 创建仪表板 |

> 💡 仪表板可以在 Cordys CRM 前端创建 L2C 漏斗报表，然后通过 API 获取。