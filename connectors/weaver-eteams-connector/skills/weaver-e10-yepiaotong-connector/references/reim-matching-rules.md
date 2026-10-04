# 发票与事前申请匹配规则

本文档定义发票与事前申请流程的智能匹配逻辑。匹配的目的是将每张发票绑定到最合适的事前申请，为后续填单提供绑定关系数据。

---

## 核心时间关系

> **事前申请日期一定在开票日期之前。**
> 即：`事前申请.createTime ≤ 发票.invoiceDate`

这是匹配和预筛选的基础约束。

---

## 匹配入口场景

### 场景A：先有发票（含用户直接提供的发票数据）→ 筛选并匹配事前申请

1. 已有发票数据（通过 `invoice.list` 获取，**或用户直接提供**，含 `invoiceDate`, `amount`, `expenseType`, `sellerName` 等）
  - 如果用户已直接给出发票数据，无需调用 `invoice.list`
2. **预筛选**：利用发票日期缩小事前申请查询范围
  - 提取发票数据中最早和最晚的 `invoiceDate`
  - 事前申请日期必然 ≤ 开票日期，因此：
    - `cusCreateDateEnd` = 最晚 invoiceDate
    - `cusCreateDateStart` = 最早 invoiceDate 往前推 90 天
3. 调用 `invoice.reim.requests.list`（带日期筛选条件）获取候选列表
4. 执行匹配算法，输出绑定关系

### 场景B：先有事前申请 → 筛选并匹配发票

1. 已获取事前申请列表（含 `requestname`, `createTime`, `creatorId` 等）
2. **预筛选**：利用事前申请日期缩小发票查询范围（使用**开票日期** `date_begin` / `date_end`）
  - 提取事前申请列表中最早的 `createTime`
  - 开票日期必然 ≥ 事前申请日期，因此：
    - `date_begin` = 最早 createTime 对应的秒级时间戳（00:00:00）
    - `date_end` = 当前日期 23:59:59 的秒级时间戳
3. 调用 `invoice.list`（带开票日期筛选条件）获取候选列表
4. 执行匹配算法，输出绑定关系

### 场景C：并行获取

两者并行获取时不做预筛选，获取全量数据后在匹配阶段统一过滤。

三种场景使用相同的匹配规则，仅数据获取和预筛选策略不同。

---

## 匹配维度（按优先级排序）

### 维度1：费用类型匹配（权重最高）

根据发票的 `expenseType` 或 `consumeContent` 与事前申请的 `requestname` / `requestnametitle` 进行费用类型关联。


| 发票线索                                                  | 匹配的事前申请关键词                    |
| ----------------------------------------------------- | ----------------------------- |
| expenseType 含"交通"/"市内交通" 或 sellerName 含"滴滴"/"曹操"/"高德" | requestname 含"交通"/"差旅"        |
| expenseType 含"住宿" 或 sellerName 含"酒店"/"宾馆"/"民宿"        | requestname 含"住宿"/"差旅"        |
| expenseType 含"餐饮" 或 sellerName 含"餐饮"/"饭店"/"美团"        | requestname 含"餐饮"/"招待"/"业务招待" |
| expenseType 含"办公" 或 consumeContent 含"办公用品"/"文具"       | requestname 含"办公"/"采购"        |
| expenseType 含"通讯" 或 sellerName 含"中国移动"/"中国联通"/"中国电信"  | requestname 含"通讯"/"话费"        |


### 维度2：时间范围匹配

> **前提：事前申请日期一定在开票日期之前（或同日）。**

```
判定规则：
  事前申请发起日期 = createTime 的日期部分
  发票日期 = invoiceDate
  
  硬约束：invoiceDate >= createTime（发票日期不早于事前申请日期）
  → 不满足此条件的直接排除，不参与评分
  
  匹配条件（满足硬约束后）：
  invoiceDate 在 [createTime, createTime + 90天] 范围内
  
  更精确的匹配（如 requestnametitle 中包含日期范围信息）：
  invoiceDate 在 [起始日期, 结束日期 + 7天] 范围内
  
  时间距离越近，匹配分越高：
  - invoiceDate 在 createTime 后 7 天内 → 加满分
  - invoiceDate 在 createTime 后 7~30 天 → 加大部分分
  - invoiceDate 在 createTime 后 30~90 天 → 加少量分
```

### 维度3：金额校验

发票金额不应大幅超出事前申请中的预算金额。

```
判定规则：
  从 requestnametitle 中提取"报销总金额"字段
  如果能提取到金额：invoice.amount <= 预算金额 * 1.2（允许20%浮动）
  如果无法提取金额：跳过此维度
```

### 维度4：部门/人员匹配

发票所属人员应与事前申请的发起人一致或同部门。

```
判定规则：
  当前用户 = 事前申请.creatorId → 自动满足
  不同用户时需额外确认
```

---

## 匹配算法

### 计分规则


| 维度     | 匹配                                 | 得分   |
| ------ | ---------------------------------- | ---- |
| 费用类型匹配 | 完全匹配                               | +40  |
| 费用类型匹配 | 部分匹配（同大类）                          | +20  |
| 时间范围匹配 | invoiceDate 在 createTime 后 7 天内    | +30  |
| 时间范围匹配 | invoiceDate 在 createTime 后 7~30 天  | +20  |
| 时间范围匹配 | invoiceDate 在 createTime 后 30~90 天 | +10  |
| 时间范围匹配 | invoiceDate < createTime（不满足硬约束）   | 直接排除 |
| 金额校验   | 不超预算                               | +20  |
| 金额校验   | 超预算20%以内                           | +10  |
| 部门匹配   | 同一人                                | +10  |


### 置信度等级


| 总分    | 置信度    | 处理方式            |
| ----- | ------ | --------------- |
| ≥ 70  | high   | 直接绑定，展示给用户确认    |
| 40-69 | medium | 建议绑定，高亮提示"建议核实" |
| < 40  | low    | 不自动绑定，放入未匹配列表   |


---

## 匹配约束

1. **一对多关系**：一条事前申请可绑定多张发票，但一张发票只能绑定一条事前申请
2. **不强制匹配**：不确定时宁可不匹配，让用户手动选择
3. **优先级冲突**：当一张发票可匹配多条事前申请时，选择总分最高的；分数相同时选时间最接近的
4. **无事前申请**：发票可以不绑定事前申请，直接用于报销（`preApprovalId` 为 null）

---

## 匹配输出格式

```json
{
  "matchResults": [
    {
      "invoiceId": "1295366637717012482",
      "invoiceInfo": "滴滴出行 ¥108.2 2024-12-30",
      "preApprovalId": "1298294241967177729",
      "preApprovalWorkflowId": "1181057526276915214",
      "preApprovalName": "交通费报销-后端开发111-2026-07-31",
      "matchConfidence": "high",
      "matchScore": 85,
      "matchReasons": ["费用类型匹配：交通费", "时间范围匹配", "同一申请人"]
    }
  ],
  "unmatchedInvoices": [
    {
      "invoiceId": "INV003",
      "invoiceInfo": "文具 ¥35.00 2026-07-28",
      "reason": "未找到匹配的事前申请"
    }
  ],
  "unmatchedApprovals": [
    {
      "requestId": "REQ003",
      "requestName": "采购申请-XXX",
      "reason": "无匹配的发票"
    }
  ]
}
```

---

## 匹配流程伪代码

```
function matchInvoicesWithApprovals(invoices, approvals):
    results = []
    unmatchedInvoices = []
    
    for each invoice in invoices:
        bestMatch = null
        bestScore = 0
        
        for each approval in approvals:
            score = 0
            reasons = []
            
            // 维度1：费用类型
            if matchExpenseType(invoice, approval):
                score += 40
                reasons.push("费用类型匹配")
            elif partialMatchExpenseType(invoice, approval):
                score += 20
                reasons.push("费用类型部分匹配")
            
            // 维度2：时间范围
            if invoiceDateInRange(invoice.invoiceDate, approval):
                score += 30
                reasons.push("时间范围匹配")
            elif invoiceDateInFloatRange(invoice.invoiceDate, approval, 3):
                score += 15
                reasons.push("时间范围浮动匹配")
            
            // 维度3：金额校验
            budgetAmount = extractBudget(approval.requestnametitle)
            if budgetAmount and invoice.amount <= budgetAmount * 1.2:
                score += 20
                reasons.push("金额校验通过")
            elif budgetAmount and invoice.amount <= budgetAmount * 1.5:
                score += 10
                reasons.push("金额略超预算")
            
            // 维度4：同一申请人
            if currentUserId == approval.creatorId:
                score += 10
                reasons.push("同一申请人")
            
            if score > bestScore:
                bestScore = score
                bestMatch = {approval, score, reasons}
        
        if bestScore >= 40:
            confidence = "high" if bestScore >= 70 else "medium"
            results.push({invoice, bestMatch, confidence})
        else:
            unmatchedInvoices.push(invoice)
    
    return {results, unmatchedInvoices}
```

---

## 从 requestnametitle 提取信息

事前申请的 `requestnametitle` 格式通常为：

```
交通费报销-后端开发111-2026-07-31 (相关客户:XXX, 相关项目:XXX, 承担主体: XXX, 流程编号:Weaver-FYBX202607000069, 报销总金额:14.47 , 费用承担公司:XXX)
```

可提取的信息：


| 信息    | 提取方式                 | 用途     |
| ----- | -------------------- | ------ |
| 费用类型  | 标题开头（如"交通费报销"→"交通费"） | 费用类型匹配 |
| 申请人   | 标题第二段（如"后端开发111"）    | 人员校验   |
| 日期    | 标题第三段（如"2026-07-31"） | 时间匹配   |
| 相关客户  | 非出差：固定填 `"100504500000311504"`（泛微上海）；**出差流程：必须由用户提供具体客户，未提供不允许报销** | 填单时使用  |
| 相关项目  | 括号内"相关项目:"后面的值       | 填单时使用  |
| 报销总金额 | 括号内"报销总金额:"后面的数字     | 金额校验   |
| 流程编号  | 括号内"流程编号:"后面的值       | 参考信息   |

