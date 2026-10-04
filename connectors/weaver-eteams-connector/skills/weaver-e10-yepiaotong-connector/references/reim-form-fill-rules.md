# 表单字段填充规则与填单 JSON 组装

本文档定义如何根据发票数据、事前申请数据和表单字段结构，组装最终的填单结构化 JSON。

> **⚠️ 数据完整性规则适用于本文档所有操作，详见 [reim-workflow.md 顶部](reim-workflow.md#️️️-最高优先级规则严禁篡改任何原始数据值-️️️)。**

---

## 最终输出结构

```json
{
  "work_flow_id": "需要填单的工作流ID",
  "mainFormId": "报销单主表formId",
  "request_name": "流程标题（按规则生成）",
  "main_fields": [
    {"fieldId": "xxx", "value": "值或ID", "fieldName": "字段名"},
    {"fieldId": "xxx", "optionValue": "选项值", "fieldName": "字段名"}
  ],
  "detail_rows": [
    {
      "dataIndex": 1,
      "subFormId": "明细表ID",
      "invoiceId": "对应发票ID",
      "fields": [
        {"fieldId": "xxx", "value": "值或ID", "fieldName": "字段名"},
        {"fieldId": "xxx", "optionValue": "选项值", "fieldName": "字段名"}
      ]
    }
  ],
  "need_user_confirm": [
    {
      "fieldId": "xxx",
      "fieldName": "字段名",
      "dataIndex": null,
      "reason": "模糊搜索返回多个候选",
      "candidates": [{"id": "xxx", "name": "xxx"}]
    }
  ],
  "unable_to_fill": [
    {
      "fieldId": "xxx",
      "fieldName": "字段名",
      "reason": "无法填写的原因"
    }
  ]
}
```

---

## 各部分说明

### work_flow_id

目标报销流程的工作流ID，**来自 Step 2.5 调用 `invoice.reim.workflow.resolve` 获取**：

| 场景 | 来源 |
|------|------|
| 有事前申请 | `requestWorkflowMap[requestId].workFlowId` |
| 无事前申请，候选只有1个 | `candidateWorkflows[0].workFlowId` |
| 无事前申请，候选多个 | 根据发票/事前数据自动匹配最相关的 `workFlowId` |

### mainFormId

报销单主表formId，**来自 Step 3 调用 `invoice.reim.form.structure` 返回的 `mainFormId`**。

### request_name 生成规则

| 场景 | 格式 | 示例 |
|------|------|------|
| 有事前申请 | `{事前申请关键词}报销-{用户名}-{日期}（共N笔）` | `"北京出差报销-张三-2026-08-04（共2笔）"` |
| 无事前申请 | `{费用类型汇总}报销-{用户名}-{日期}（共N笔）` | `"交通费+住宿费报销-张三-2026-08-04（共3笔）"` |
| 单张发票 | `{费用类型}报销-{用户名}-{日期}` | `"交通费报销-张三-2026-08-04"` |

- 日期使用当前日期
- N = 明细行总数（发票数量）
- 从事前申请标题中提取核心关键词（去掉"申请"后缀）
- 标题不超过 30 个字

---

## main_fields 填充规则

来自 `invoice.reim.form.structure` 返回的 `mainFields`，逐个字段推断值。

每条记录格式：

```json
{"fieldId": "xxx", "value": "值或ID", "fieldName": "字段名称"}
```

或（Select 下拉选项型）：

```json
{"fieldId": "xxx", "optionValue": "选项值", "fieldName": "字段名称"}
```

**value 和 optionValue 二选一**：有 options 的字段用 `optionValue`，其他用 `value`。

---

## detail_rows 填充规则

来自 `invoice.reim.form.structure` 返回的 `subTables[0].subFields`（**只填第一个明细表**）。

- **只填写 `subTables` 中第一个明细表（`subTables[0]`）的字段，其他明细表不用填值**
- `dataIndex` 从 1 开始递增
- `subFormId` = `subTables[0].subFormId`

### 过滤红冲发票（前置处理第一步）

获取到发票列表后，**必须先过滤掉全额红冲发票**（`info.comm_info.pro.status == 8`），这类发票不允许报销。过滤后的发票才进入后续分类。

### 发票与相关凭证分类（前置处理第二步）

过滤后的发票列表，**按 `invoiceTypeCode`（即 `info.comm_info.pro.type`）分类**，再组装明细行。

> 完整的发票类型 ID 与名称映射见 [reim-api-reference.md - 发票类型 ID 映射表](reim-api-reference.md#发票类型-id-映射表)

| 分类 | invoiceTypeCode | 示例 | 填单行为 |
|------|-----------------|------|----------|
| **发票** | 除 17/18/57/58 以外 | 增值税发票(1/2/3/4)、电子发票(28/32/33)、火车票(12/47)、出租车发票(9) 等 | 每张发票 = 一行明细 |
| **相关凭证** | 17, 18, 57, 58 | 小票/水单(17)、滴滴行程单(18)、支付凭证(57)、其他票据凭证(58) | **不能独立成行**，必须与对应发票配对放在同一行 |

> **注意区分**：type=18 是滴滴的支付行程凭证（不能独立成行）；滴滴开具的增值税电子普通发票 type=3，是正式发票，可独立成行。

### 凭证与发票配对规则

相关凭证必须找到对应的发票，配对后放入同一行明细。

> **⚠️ 前提条件：相关凭证的金额不能比对应发票的金额大（凭证 `amount` ≤ 发票 `amount`），不满足此条件的不能配对。**

配对策略（按优先级）：

1. **金额匹配**：凭证 `amount` ≤ 发票 `amount`，且金额一致或接近
2. **日期匹配**：凭证 `invoiceDate` 与发票 `invoiceDate` 接近（前后 7 天内）
3. **销方匹配**：凭证 `sellerName` 与发票 `sellerName` 相同或相关（如同一交通平台）
4. **费用类型匹配**：凭证 `expenseType` 与发票 `expenseType` 同属一类

> 如果凭证找不到可配对的发票，则跳过该凭证（不单独成行），并在结果中提示用户。

### 明细行中的两个 EinvoiceComponent 字段

`subTables[0].subFields` 中存在两个 `EinvoiceComponent` 类型的字段：

| 字段 | fieldType | single | 填入内容 |
|------|-----------|--------|----------|
| **相关发票** | `EinvoiceComponent` | `false` | 发票的 `invoiceId`（**必填**） |
| **相关凭证** | `EinvoiceComponent` | `true` | 配对凭证的 `invoiceId`（**有则必填，无则不填**） |

### 填值规则

| 场景 | 相关发票（single=false） | 相关凭证（single=true） |
|------|------------------------|----------------------|
| 发票有配对凭证 | 发票的 `invoiceId` | 凭证的 `invoiceId`（**必填**） |
| 发票无配对凭证 | 发票的 `invoiceId` | **不填此字段** |

### 示例：有配对凭证

```json
{
  "dataIndex": 1,
  "subFormId": "100003690000000011",
  "invoiceId": "1298798990831517697",
  "fields": [
    {"fieldId": "100003720000000228", "value": "100.0", "fieldName": "实报金额"},
    {"fieldId": "100003720000000419", "value": "2026-07-29", "fieldName": "费用日期"},
    {"fieldId": "100003720000052200", "value": "100001050000000001", "fieldName": "币种"},
    {"fieldId": "100003720000077896", "value": "1298798990831517697", "fieldName": "相关发票"},
    {"fieldId": "100003720000077897", "value": "1298798990831518001", "fieldName": "相关凭证"}
  ]
}
```

### 示例：无配对凭证（只填相关发票，不填相关凭证）

```json
{
  "dataIndex": 1,
  "subFormId": "100003690000000011",
  "invoiceId": "1298798990831517697",
  "fields": [
    {"fieldId": "100003720000000228", "value": "100.0", "fieldName": "实报金额"},
    {"fieldId": "100003720000000419", "value": "2026-07-29", "fieldName": "费用日期"},
    {"fieldId": "100003720000052200", "value": "100001050000000001", "fieldName": "币种"},
    {"fieldId": "100003720000077896", "value": "1298798990831517697", "fieldName": "相关发票"}
  ]
}
```

### invoiceId 必须出现的位置

> 1. `detail_rows` 的顶层 `invoiceId` 字段 — 填发票（非凭证）的 ID
> 2. `fields` 中 `EinvoiceComponent`+`single=false` 的字段 — 填发票的 `invoiceId`（必填）
> 3. `fields` 中 `EinvoiceComponent`+`single=true` 的字段 — 有配对凭证时填凭证的 `invoiceId`，无凭证则不填
>
> 位置 1 和 2 必须有值，位置 3 仅在有配对凭证时才填！

---

## 字段值填充策略

### 策略1：marked=false 且有 options（下拉选项型）

从 `options` 列表中选择最匹配的 `optionValue`，用 `optionValue` 字段输出。

```
输入：fieldName="报销方式", options=[{optionName:"银行（个人报销）",optionValue:"7"}, ...]
推断：默认选"银行（个人报销）" → optionValue = "7"
输出：{"fieldId":"xxx", "optionValue":"7", "fieldName":"报销方式"}
```

**optionValue 填的是选项的 optionValue 值，不是 optionName。**

### 策略2：marked=false 且无 options（文本/日期/金额型）

根据 `fieldName` 语义从已知数据中提取或生成值，用 `value` 字段输出。

| fieldType | value 格式 | 示例 |
|-----------|------------|------|
| DateComponent | yyyy-MM-dd | `"2026-08-04"` |
| Text | 文本字符串 | `"差旅报销说明"` |
| TextArea | 文本字符串 | `"2026-07-31 交通费 - 滴滴出行"` |
| Money | 数字字符串 | `"108.20"` |
| NumberComponent | 数字字符串 | `"1"` |

### 策略3：marked=true（需要数据 ID）

必须填写数据 ID，用 `value` 字段输出。

> **自动填单时（Step 4），`marked=true` 的字段只从上下文已有数据中获取 ID，不调用 `invoice.reim.field.search`。**

来源（上下文已有 ID）：

| 字段 | ID 来源 | 是否必填 |
|------|---------|----------|
| 报销人/申请人/提单人员/人员ID | 事前申请的 `creatorId`，或当前用户 ID | 有数据就填 |
| 部门/报销部门/部门ID/承担人部门 | 事前申请的 `creatorDepartmentId`，或当前用户部门 ID | 有数据就填 |
| 相关流程/事前申请 | 事前申请的 `requestid` | 有数据就填 |
| **承担主体** | **当前用户 ID（`creatorId`）** | **⚠️ 必填，永远不能为空** |
| **报销人上级** | **`invoice.reim.employee-superiors` 返回的 `allSuperiors[0].id`（直接上级 ID，直接赋值）** | **⚠️ 必填，永远不能为空** |
| **承担人直接上级** | **`invoice.reim.employee-superiors` 返回的 `allSuperiors[0].id`（直接上级 ID，直接赋值）** | **⚠️ 必填，永远不能为空** |
| **承担人所有上级** | **`invoice.reim.employee-superiors` 返回的 `allSuperiors` 所有 `id` 用逗号拼接（如 `"id1,id2,id3"`）** | **⚠️ 必填，永远不能为空** |
| **费用类型（科目）** | **优先 `invoice.reim.row-info` 返回的 `subjectId`；为空时按 [expense-subject-rules.md](reim-expense-subject-rules.md) 匹配，匹配不到用兜底 `"100502270000000104"`** | **⚠️ 必填，永远不能为空** |
| 相关发票 | `invoiceId` | 必填 |
| **相关客户（主表）** | **非出差**：固定值 `"100504500000311504"`（泛微上海）；**出差流程**：必须由用户提供具体客户，见下方「出差流程相关客户」 | **⚠️ 必填；出差流程未提供则不允许报销** |
| 币种 | 固定 `"100001050000000001"`（人民币） | 必填 |
| 上下文中找不到 ID 的其他字段 | 放入 `unable_to_fill` | — |

> **⚠️ 以下字段绝不放入 `unable_to_fill`，必须有值：**
> - **费用类型（科目）**：按科目匹配规则匹配，所有策略都无法匹配时用兜底科目 `"100502270000000104"`（其他-管理费用）
> - **相关客户（非出差）**：固定填 `"100504500000311504"`（泛微上海）
> - **相关客户（出差流程）**：必须由用户提供具体客户后再填，未提供则**暂停且不允许调用 `invoice.reim.flow.create.prepare/apply`**，不能用固定值顶替
> - **合同编号**：固定填 `"20260999"`，不需要从其他来源提取
> - **承担主体**：使用当前用户 ID（`creatorId`）
> - **报销人上级**：`invoice.reim.employee-superiors` 返回的 `allSuperiors[0].id`
> - **承担人直接上级**：`invoice.reim.employee-superiors` 返回的 `allSuperiors[0].id`
> - **承担人所有上级**：`invoice.reim.employee-superiors` 返回的 `allSuperiors` 所有 `id` 用逗号拼接

### 出差流程相关客户（硬拦截）

> **出差报销必须由用户填写具体相关客户。未提供则不允许报销，禁止调用 `invoice.reim.flow.create.prepare/apply`。**

**如何判断是出差流程（满足任一即可）：**

| 判断依据 | 条件 |
|----------|------|
| 报销工作流名称 `workFlowName` | 含「差旅」或「出差」 |
| 事前申请名称 `requestname` | 含「出差」或「差旅」 |
| 用户表述 | 明确说「出差报销」「差旅报销」 |

**填单规则：**

| 流程类型 | 相关客户怎么填 | 未提供时 |
|----------|----------------|----------|
| **出差 / 差旅** | 暂停询问用户具体客户名称；用户给出后用 `invoice.reim.field.search` 搜索 ID，唯一结果直接填，多候选让用户选 | **不允许报销**，不创建报销单 |
| **非出差** | 固定填 `"100504500000311504"`（泛微上海） | 不适用 |

**出差流程操作步骤：**

1. 识别为出差后，**在 Step 5 调用 `invoice.reim.flow.create.prepare/apply` 之前必须暂停**
2. 明确提醒用户：「当前为出差报销，必须填写相关客户。请提供具体客户名称，否则无法继续报销。」
3. 用户给出客户名称 → 调用 `invoice.reim.field.search` 搜索 ID → 填入主表和明细表的「相关客户」字段
4. 用户拒绝、取消、或不提供具体客户 → **结束报销流程，禁止调用 `invoice.reim.flow.create.prepare/apply`**
5. **禁止**用固定值 `"100504500000311504"` 顶替出差的相关客户
6. **禁止**把出差相关客户放入 `unable_to_fill` 后继续创建报销单

---

## 字段名称 → 数据来源映射表

### 主表字段映射

| fieldName 关键词 | 数据来源 | value 取值 |
|------------------|----------|------------|
| 申请人/报销人/创建人 | 事前申请 | `creatorId` |
| 部门/报销部门/申请人部门 | 事前申请 | `creatorDepartmentId` |
| 报销日期/申请日期 | 系统当前日期 | 当天日期 yyyy-MM-dd |
| 报销方式 | options 默认选项 | 默认选"银行（个人报销）"的 optionValue |
| 报销事由/摘要 | AI生成 | `"{日期} {费用类型} - {销方简称}"`（**禁止包含 `*` 号**） |
| 相关流程/事前申请 | 事前申请 | `requestid`（marked=true） |
| 相关人员 | 事前申请 | `creatorName` |
| **相关客户** | **按是否出差分流** | **非出差**：固定填 `"100504500000311504"`（泛微上海）。**出差流程**：必须提醒用户填写具体客户，拿到客户名称后搜索 ID 再填；用户未提供则不允许报销 |
| **合同编号** | **固定值** | **固定填 `"20260999"`，不从其他来源提取，不能留空或放入 unable_to_fill** |
| **承担主体** | **事前申请/当前用户** | **`creatorId`（marked=true），不能留空或放入 unable_to_fill** |
| **报销人上级** | **`invoice.reim.employee-superiors`** | **`allSuperiors[0].id`（直接上级 ID，直接赋值），不能留空或放入 unable_to_fill** |
| **承担人直接上级** | **`invoice.reim.employee-superiors`** | **`allSuperiors[0].id`（直接上级 ID，直接赋值），不能留空或放入 unable_to_fill** |
| **承担人所有上级** | **`invoice.reim.employee-superiors`** | **`allSuperiors` 所有 `id` 用逗号拼接赋值（如 `"id1,id2,id3"`），不能留空或放入 unable_to_fill** |
| 币种 | options 默认选项 | 默认选"人民币"的 optionValue |
| 申请金额/人民币金额 | 发票 | 发票金额合计（所有**发票**的 `amount` 之和，不含相关凭证） |

### 明细表字段映射

> **⚠️ 标注"`invoice.reim.row-info` 优先"的字段：先取 `invoice.reim.row-info` 返回值，为空/null 时才回退到 AI 推断。**

| fieldName 关键词 | 数据来源 | value 取值 |
|------------------|----------|------------|
| 费用日期/发生日期 | **`invoice.reim.row-info` 优先** → 发票 | 优先 `invoice.reim.row-info` 返回的 `date`，回退 `invoiceDate` |
| 实报金额 | 发票 | `amount` |
| **申请金额** | **发票** | **`amount`（与实报金额一致，不能遗漏）** |
| 报销金额/人民币金额/含税金额及其他 `fieldType="Money"` 字段 | 发票 | `amount` |
| 费用说明/摘要 | **`invoice.reim.row-info` 优先** → 发票 | **交通类发票**：只填 `{出发地精简}-{目的地精简}`，见下方规则；**其他发票**：优先 `invoice.reim.row-info` 返回的 `fysm`，回退从 `consumeContent` 提取（**必须去掉所有 `*` 号**，如 `*交通运输服务*客运服务费` → `交通运输服务客运服务费`），**不能包含逗号和 `*` 号** |
| **费用类型/费用科目** | **`invoice.reim.row-info` 优先** → 发票+事前申请 | 优先 `invoice.reim.row-info` 返回的 `subjectId`，回退按 [expense-subject-rules.md](reim-expense-subject-rules.md) 匹配，**必须填值，匹配不到用兜底 `"100502270000000104"`** |
| **相关客户** | **按是否出差分流** | **非出差**：固定填 `"100504500000311504"`。**出差流程**：与主表一致，填用户确认后的客户 ID；用户未提供则不允许报销 |
| 相关项目 | 事前申请标题 | marked=true时搜索提取的项目名称获取ID |
| 相关流程 | 匹配绑定关系 | 该发票绑定的 `preApprovalId`（requestid） |
| 币种 | 默认固定值 | `"100001050000000001"`（人民币） |
| 附件数 | 默认 | `"1"` |
| **相关发票**（`EinvoiceComponent`, `single=false`） | **发票** | **发票的 `invoiceId`（必填）** |
| **相关凭证**（`EinvoiceComponent`, `single=true`） | **`invoice.reim.row-info` 优先** → 凭证配对 | 优先 `invoice.reim.row-info` 返回的 `itinerary`，回退到凭证配对逻辑；**无凭证则不填** |

> **⚠️ 明细行金额字段填写规则（重要，容易遗漏）：**
> 明细表中 `fieldType="Money"` 的字段，无论 `fieldName` 叫什么名字（实报金额、报销金额、申请金额、人民币金额、含税金额等），**全部统一填该行发票的 `amount`**。
> 遍历 `subFields` 时，只要 `fieldType="Money"`，就填 `amount`，不要因为字段名不是"实报金额"就跳过。

### 交通类发票费用说明特殊规则

当发票为交通类时（判断条件：`expenseType` 含"交通"/"出行"/"打车"，或 `consumeContent` 含"客运服务费"/"运输服务"，或 `sellerName` 含"滴滴"/"享道"/"高德"/"曹操"等），需要**额外调用 `invoice.get`** 获取出发地和目的地（详见 [reim-api-reference.md](reim-api-reference.md#57-获取发票详情交通类发票行程信息)），然后将精简后的行程拼入费用说明。

**费用说明格式**：`{出发地精简}-{目的地精简}`（交通类发票**只填行程**，不需要前面的费用类型描述）

### 地名精简规则

**1. 去掉冗余修饰词**：方位后缀（"西北侧"/"东侧"/"南侧"/"出发层"等）、"股份有限公司"/"有限公司"等企业后缀

**2. 保留核心地名和关键标识**：门店名、品牌名、航站楼编号、车站名等

**3. 括号内容处理**：
- 括号内是核心补充信息（如区域名、业务中心名）→ 精简后保留
- 括号内是方位/门号等冗余信息（如"南门"/"西2门"）→ 视情况保留关键部分或去掉
- 去掉门牌号（如"30号"/"3419号"）

**4. 长度控制**：每个地名精简后控制在 10 字以内

```
示例：
  from = "北京SKP（西2门）西北侧"
  → 精简 = "北京SKP西2门"
  （去掉"西北侧"冗余方位，括号内"西2门"是关键标识保留）

  from = "泛微网络科技股份有限公司（北方大区业务运营中心）"
  → 精简 = "泛微网络（北方运营中心）"
  （去掉"科技股份有限公司"，括号内精简为核心部分）

  from = "仁济医院南院区门诊部(南门)南侧", to = "浦江瑞和城柒街区30号"
  → 费用说明 = "仁济医院南院-浦江瑞和城"
  （去掉"门诊部""南门""南侧""柒街区30号"）

  from = "虹桥机场T2航站楼出发层", to = "北京南站"
  → 费用说明 = "虹桥机场T2-北京南站"
  （去掉"航站楼出发层"，T2是关键标识保留）

  from = "上海市闵行区三鲁公路3419号", to = "浦东国际机场T1航站楼到达层"
  → 费用说明 = "三鲁公路-浦东机场T1"
  （去掉门牌号"3419号"、"国际""航站楼到达层"）
```

> **注意**：交通类发票的费用说明**忽略** `invoice.reim.row-info` 返回的 `fysm` 和 `consumeContent`，只使用 `{出发地精简}-{目的地精简}`。如果 `invoice.get` 未返回 from/to，则回退到常规费用说明逻辑。

---

## need_user_confirm 触发场景

| 场景 | reason | candidates |
|------|--------|------------|
| 模糊搜索返回多个匹配项 | `"模糊搜索返回多个候选"` | 填充所有候选 `[{id, name}]` |
| 字段值需要用户选择确认 | `"需要用户选择确认"` | 填充可选列表 |

> **注意**：费用科目/费用类型字段**不放入 need_user_confirm**，始终自动选择最相关的科目。详见 [expense-subject-rules.md](reim-expense-subject-rules.md)。

`dataIndex` 说明：
- 主表字段：`dataIndex = null`
- 明细表字段：`dataIndex = 对应行号（从1开始）`

---

## unable_to_fill 触发场景

| 场景 | reason 示例 |
|------|-------------|
| 缺少必要数据源 | `"无相关数据，无法确定开户行"` |
| 模糊搜索无结果 | `"搜索'XX'无匹配结果"` |
| 数据不匹配 | `"发票数据中无对应信息"` |
| 需要用户输入 | `"无历史数据，需人工输入"` |

---

## 组装流程（Step 4 核心逻辑）

> **⚠️ 创建多个报销单时，每个报销单都必须独立执行以下完整流程，不能省略任何步骤或字段。**

0. **⚠️ 过滤红冲发票**：先过滤掉 `info.comm_info.pro.status == 8` 的全额红冲发票，不允许报销
1. **分类**：按 `invoiceTypeCode` 将列表分为"发票"和"相关凭证"（17/18/57/58），将凭证与发票配对
1.5. **⚠️ 禁止 `*` 号**：所有填入报销单的文本值（费用说明、报销事由等）**禁止包含 `*` 符号**。从 `consumeContent` 等字段取值时必须先去掉所有 `*` 号（如 `*交通运输服务*客运服务费` → `交通运输服务客运服务费`）
2. 设置 `work_flow_id` + `mainFormId` + 生成 `request_name`
2.5. **⚠️ 出差流程拦截相关客户**：若判定为出差/差旅，先提醒用户填写具体相关客户；用户未提供则**停止组装，不允许进入 Step 5**。非出差才填固定值 `"100504500000311504"`
3. 遍历 `mainFields` → 推断值 → 有值加入 `main_fields`，多候选→`need_user_confirm`，无法推断→`unable_to_fill`
4. **⚠️ 对每张发票调用 `invoice.reim.row-info` 获取预填信息**（详见 [reim-api-reference.md](reim-api-reference.md#56-获取发票明细行预填信息)）：
   - 入参：`cdzt`=当前用户ID，`requestid`=匹配到的事前申请ID（无则留空），`invoiceId`=发票ID
   - 返回的 `date`、`fysm`、`itinerary`、`subjectId` **优先使用**，只有返回为空/null时才回退到 AI 推断
5. 每张**发票**（非凭证）= 一行明细（`dataIndex` 从 1 递增），**完整遍历 `subTables[0].subFields` 的每个字段**推断值
6. **每行必须填写**：费用类型（科目）、所有金额字段、费用日期、费用说明、相关发票等
7. **每行必须将发票 `invoiceId` 赋值到 `EinvoiceComponent`+`single=false` 的字段**
8. **相关凭证**：优先使用 `invoice.reim.row-info` 返回的 `itinerary`；如无返回，使用原有凭证配对逻辑
9. `marked=true` 字段从上下文取 ID，取不到放 `unable_to_fill`（不调用 `invoice.reim.field.search`）
10. **⚠️ 最终检查**：检查每行明细的"费用类型（科目）"字段是否有值，如果为空，**立即填 `"100502270000000104"`**
11. 返回完整 JSON

> **`invoice.reim.row-info` 返回值优先级规则**：
>
> | 明细字段 | `invoice.reim.row-info` 返回字段 | 有值时 | 为空/null时 |
> |----------|-------------------|--------|-------------|
> | 费用日期 | `date` | **直接使用** | 回退到发票 `invoiceDate` |
> | 费用说明 | `fysm` | **直接使用** | 回退到 AI 从 `consumeContent` 提取（**去掉所有 `*` 号**） |
> | 相关凭证 | `itinerary` | **直接使用**（多值逗号分隔） | 回退到原有凭证配对逻辑 |
> | 费用类型（科目） | `subjectId` | **直接使用** | 回退到 [expense-subject-rules.md](reim-expense-subject-rules.md) 匹配，匹配不到用兜底 |
>
> **⚠️ 费用类型（科目）是强制保底：无论来源是 `invoice.reim.row-info` 还是 AI 推断，最终都不能为空，匹配不到直接填 `"100502270000000104"`。**

---

## 补充说明

### Select 类型
`optionValue` 填的是选项的 `optionValue`（如 `"7"`），不是 `optionName`（如 "银行（个人报销）"）。

### marked=true 字段
必须填数据 ID，不能填名称文本。**自动填单时**从上下文取 ID，取不到放 `unable_to_fill`。**用户修改时**（`invoice.reim.flow.update.prepare/apply` 场景）才调用 `invoice.reim.field.search` 将文本转 ID。
