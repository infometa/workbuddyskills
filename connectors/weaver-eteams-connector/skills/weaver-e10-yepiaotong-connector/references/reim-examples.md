# 完整端到端示例

> 所有操作通过 `weaver-work-cli --profile eteams --json invoice run <operation> --input-json '<json>'` 执行。
> 认证由 `weaver-work-cli auth` 管理，无需手动传 token/eteamsId。
> 复杂 JSON 建议先写入 UTF-8 文件再用 `--input <path>` 传入。

---

## 示例0：用户提供 fileId → 发票识别 → 自动报销

用户说："帮我报销这个文件 1290156133724692482,1290156133724692483"

### Step 0: 文件ID转发票识别

切割 fileId，调用 `invoice.reim.file-ocr.preview`：

**命令：**

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.file-ocr.preview --input-json '{"fileIds":["1290156133724692482","1290156133724692483"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.file-ocr.preview --input-json '{"fileIds":["1290156133724692482","1290156133724692483"]}'
```

**返回：**

```json
{
  "code": 200,
  "msg": "接口返回成功",
  "status": true,
  "data": [
    {
      "fileId": "1290156133724692482",
      "fileName": "滴滴出行电子发票.pdf",
      "status": "success",
      "errorMsg": "识别成功",
      "invoiceId": "1290156159548506113",
      "invoiceType": "增值税电子普通发票",
      "invoiceTypeCode": 3,
      "amount": "85.60",
      "consumeContent": "*运输服务*客运服务费",
      "invoiceDate": "2026-07-28",
      "invoiceNumber": "36901200",
      "buyerName": "上海亘岩网络科技有限公司",
      "sellerName": "北京滴滴出行科技有限公司",
      "expenseType": "市内交通"
    },
    {
      "fileId": "1290156133724692483",
      "fileName": "如家酒店发票.pdf",
      "status": "success",
      "errorMsg": "识别成功",
      "invoiceId": "1290156159548506114",
      "invoiceType": "增值税电子普通发票",
      "invoiceTypeCode": 3,
      "amount": "380.00",
      "consumeContent": "*住宿服务*住宿费",
      "invoiceDate": "2026-07-29",
      "invoiceNumber": "36901201",
      "buyerName": "上海亘岩网络科技有限公司",
      "sellerName": "如家酒店管理有限公司",
      "expenseType": "住宿"
    }
  ],
  "fail": false
}
```

过滤 `status="success"` 的数据，得到 2 张发票。

### 后续流程

已获取发票数据 → **跳过 Step 1A**（不调用 `invoice.list`）

利用发票的 `invoiceDate`（2026-07-28 ~ 2026-07-29）筛选事前申请：
- `cusCreateDateStart` = "2026-04-29"（往前推90天）
- `cusCreateDateEnd` = "2026-07-29"

→ 继续 Step 1B → Step 2 匹配 → Step 2.5 → Step 3 → Step 4 → Step 5（流程同示例1/2）

---

## 示例1：单张发票 + 有事前申请（完整流程）

### Step 1A: 获取发票

**第一步：按内联公式计算最近一周时间戳参数**

AI 直接计算（UTC+8）：begin = 今天00:00:00秒时间戳 - 7*86400, end = 今天23:59:59秒时间戳

生成 `invoice.list` 入参（只传必要字段；`sreim`/`bill_type` 由 CLI 默认）：

```json
{
  "page_size": 10,
  "start_pos": 0,
  "date_begin": 1786291200,
  "date_end": 1786982399
}
```

**第二步：调用 CLI 查询发票**

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0,"date_begin":1786291200,"date_end":1786982399}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0,"date_begin":1786291200,"date_end":1786982399}'
```

**返回（CLI 信封中列表在 `data.items`，下面是单条票面结构）：**

```json
{
  "infos": [
    {
      "info": {
        "id": "1295366637717012482",
        "fid": "1295366637717012482",
        "code": "",
        "number": "36901189",
        "ext": "{\"content\":\"*运输服务*客运服务费\",\"products\":[{\"name\":\"*运输服务*客运服务费\",\"amount\":\"108.2\"}],\"category\":\"增值税电子普通发票\"}",
        "fylx": "897092516517920775",
        "currency": "CNY",
        "province": "上海市",
        "modify_info": { "ctm": 1786168444, "utm": 1786168444, "cstm": 1722268800, "source": 4 },
        "comm_info": {
          "pro": { "cname": "增值税电子普通发票", "type": 3, "date": "2026-07-30", "status": 0 },
          "price": { "amount": "102.08", "total": "108.2" },
          "buyer": { "tcode": "xxx", "company": "上海亘岩网络科技有限公司" },
          "payer": { "tcode": "xxx", "company": "北京滴滴出行科技有限公司" }
        },
        "relative_fids": [],
        "bill_type": 0
      },
      "ret": { "trace": "", "ret": 0, "message": "执行成功" },
      "is_valid": 0
    }
  ],
  "res_base": { "trace": "", "ret": 0, "message": "执行成功" }
}
```

**字段映射提取：**
- `invoiceId` = `info.fid` = `"1295366637717012482"`
- `invoiceNumber` = `info.number` = `"36901189"`
- `invoiceType` = `info.comm_info.pro.cname` = `"增值税电子普通发票"`
- `invoiceTypeCode` = `info.comm_info.pro.type` = `3`
- `invoiceDate` = `info.comm_info.pro.date` = `"2026-07-30"`
- `amount` = `info.comm_info.price.total` = `"108.2"`
- `buyerName` = `info.comm_info.buyer.company` = `"上海亘岩网络科技有限公司"`
- `sellerName` = `info.comm_info.payer.company` = `"北京滴滴出行科技有限公司"`
- `consumeContent` = `JSON.parse(ext).content` = `"*运输服务*客运服务费"`
- `expenseType` = 根据 `info.fylx` 查名称 → `"市内交通"`

### Step 1C: 展示发票汇总，等待用户确认

> 用户说"帮我报销"，未指定日期 → 使用默认最近一周范围，**必须告知用户查询范围**

**AI 展示给用户：**

```markdown
已为您查询最近一周（2026-07-24 ~ 2026-07-30）的发票数据，共找到 1 张未报销发票，汇总金额 ¥108.20：

| # | 发票类型 | 开票日期 | 发票号码 | 金额 | 销方名称 | 费用类型 |
|---|----------|----------|----------|------|----------|----------|
| 1 | 增值税电子普通发票 | 2026-07-30 | 36901189 | ¥108.20 | 北京滴滴出行科技有限公司 | 市内交通 |

请确认是否使用以上发票进行报销？如需查询其他日期范围的发票，请告诉我。
```

用户回复"确认" → 继续后续流程

### Step 1B: 获取事前申请（基于发票日期预筛选）

> 已知发票 invoiceDate = "2026-07-30"
> 事前申请日期一定在开票日期之前 → cusCreateDateEnd = "2026-07-30"
> 往前推90天 → cusCreateDateStart = "2026-05-01"

**命令：**

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.requests.list --input-json '{"pageNo":1,"pageSize":20,"cusCreateDateStart":"2026-05-01","cusCreateDateEnd":"2026-07-30"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.requests.list --input-json '{"pageNo":1,"pageSize":20,"cusCreateDateStart":"2026-05-01","cusCreateDateEnd":"2026-07-30"}'
```

**返回：**

```json
{
  "code": 200,
  "data": [
    {
      "requestid": "1298294241967177729",
      "workflowid": "1181057526276915214",
      "requestname": "交通费报销-后端开发111-2026-07-25",
      "requestnametitle": "交通费报销-后端开发111-2026-07-25 (相关客户:, 相关项目:, 承担主体: , 流程编号:Weaver-FYBX202607000069, 报销总金额:14.47 , 费用承担公司:)",
      "flowStatus": 6,
      "creatorId": "1201729946891231232",
      "creatorName": "后端开发111",
      "creatorDepartmentId": "1201729461554241537",
      "nodeid": "1181057741029220917",
      "createTime": "2026-07-25 10:30:00"
    }
  ]
}
```

### Step 2: 匹配绑定

根据匹配规则分析（硬约束：invoiceDate >= createTime）：
- 时间硬约束：invoiceDate "2026-07-30" >= createTime "2026-07-25" → ✅ 满足
- 费用类型匹配：发票 expenseType="市内交通" ↔ 事前申请 requestname 含"交通费" → +40
- 时间匹配：invoiceDate 在 createTime 后 5 天（7天内） → +30
- 同一申请人 → +10
- 总分 80 → confidence = "high"

匹配结果：

```json
{
  "matchResults": [
    {
      "invoiceId": "1295366637717012482",
      "preApprovalId": "1298294241967177729",
      "preApprovalWorkflowId": "1181057526276915214",
      "matchConfidence": "high",
      "matchScore": 80,
      "matchReasons": ["费用类型匹配：交通费", "时间匹配：开票日期在事前申请后5天内", "同一申请人"]
    }
  ],
  "unmatchedInvoices": [],
  "unmatchedApprovals": []
}
```

### Step 2.5: 获取报销单工作流ID

**命令：**

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.workflow.resolve --input-json '{"requestIds":["1298294241967177729"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.workflow.resolve --input-json '{"requestIds":["1298294241967177729"]}'
```

**返回：**

```json
{
  "code": 200,
  "data": {
    "requestWorkflowMap": {
      "1298294241967177729": {
        "workFlowId": "1181057526276915214",
        "workFlowName": "交通费报销"
      }
    }
  }
}
```

**决策：** 有事前申请 → 直接取 `workFlowId = "1181057526276915214"`

### Step 3: 获取表单结构

**命令：**

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.form.structure --input-json '{"workflowId":"1181057526276915214"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.form.structure --input-json '{"workflowId":"1181057526276915214"}'
```

**返回（简化）：**

```json
{
  "code": 200,
  "data": {
    "mainFormId": "1181057741029226975",
    "mainFields": [
      {"fieldId": "1181057741029227445", "fieldName": "申请人", "fieldType": "Employee", "single": true, "marked": true},
      {"fieldId": "1181057741029227446", "fieldName": "部门", "fieldType": "Department", "single": true, "marked": true},
      {"fieldId": "1181057741029227447", "fieldName": "报销日期", "fieldType": "DateComponent", "single": true, "marked": false},
      {"fieldId": "1181057741029227454", "fieldName": "报销方式", "fieldType": "Select", "single": true, "marked": false, "options": [
        {"optionId": "1181057741029227903", "optionName": "银行（个人报销）", "optionValue": "7"},
        {"optionId": "1181057741029227900", "optionName": "冲销借款", "optionValue": "4"},
        {"optionId": "1181057741029227904", "optionName": "银行（付公司）", "optionValue": "6"}
      ]},
      {"fieldId": "1181057741029227456", "fieldName": "报销事由", "fieldType": "TextArea", "single": false, "marked": false},
      {"fieldId": "1181057741029227470", "fieldName": "相关流程", "fieldType": "Workflow", "single": false, "marked": true}
    ],
    "subTables": [
      {
        "subFormId": "1181057741029227992",
        "subFormName": "费用明细",
        "subFields": [
          {"fieldId": "1181057741029227449", "fieldName": "相关客户", "fieldType": "Ebuilder", "single": true, "marked": true},
          {"fieldId": "1181057741029227450", "fieldName": "相关项目", "fieldType": "Ebuilder", "single": true, "marked": true},
          {"fieldId": "1181057741029227459", "fieldName": "实报金额", "fieldType": "Money", "single": true, "marked": false},
          {"fieldId": "1181057741029227463", "fieldName": "费用类型（科目）", "fieldType": "RelateBrowser", "single": true, "marked": true},
          {"fieldId": "1181057741029227464", "fieldName": "费用说明", "fieldType": "Text", "single": false, "marked": false},
          {"fieldId": "1181057741029227465", "fieldName": "附件数", "fieldType": "NumberComponent", "single": true, "marked": false},
          {"fieldId": "1181057741029227467", "fieldName": "费用日期", "fieldType": "DateComponent", "single": true, "marked": false},
          {"fieldId": "1181057741029227468", "fieldName": "相关发票", "fieldType": "EinvoiceComponent", "single": false, "marked": false},
          {"fieldId": "1181057741029227469", "fieldName": "相关凭证", "fieldType": "EinvoiceComponent", "single": true, "marked": false}
        ]
      }
    ]
  }
}
```

### Step 3.5: 获取预填信息 + 费用科目匹配

> **自动填单时不调用 `invoice.reim.field.search`**，费用科目通过 `invoice.reim.row-info` 返回的 subjectId 或静态科目列表匹配获取。

**调用 `invoice.reim.row-info` 获取预填信息：**

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.row-info --input-json '{"invoiceId":"1295366637717012482","requestid":"1298294241967177729","cdzt":"1201729946891231232"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.row-info --input-json '{"invoiceId":"1295366637717012482","requestid":"1298294241967177729","cdzt":"1201729946891231232"}'
```

**返回：**

```json
{
  "code": 200,
  "status": true,
  "data": {
    "date": "2026-07-30",
    "fysm": "交通运输服务",
    "itinerary": "",
    "subjectId": "100502270000000006"
  }
}
```

`invoice.reim.row-info` 返回 `subjectId = "100502270000000006"`（市内交通费）→ 直接使用。

> 如果 `subjectId` 为空，则按 [expense-subject-rules.md](reim-expense-subject-rules.md) 静态科目列表匹配：
> `sellerName` 含"滴滴" → `"100502270000000173"`；`expenseType`="市内交通" → `"100502270000000006"`；匹配不到 → 兜底 `"100502270000000104"`。

### Step 4: 组装填单 JSON

```json
{
  "work_flow_id": "1181057526276915214",
  "mainFormId": "1181057741029226975",
  "request_name": "交通费报销-后端开发111-2026-08-04（共1笔）",
  "main_fields": [
    {"fieldId": "1181057741029227445", "value": "1201729946891231232", "fieldName": "申请人"},
    {"fieldId": "1181057741029227446", "value": "1201729461554241537", "fieldName": "部门"},
    {"fieldId": "1181057741029227447", "value": "2026-08-04", "fieldName": "报销日期"},
    {"fieldId": "1181057741029227454", "optionValue": "7", "fieldName": "报销方式"},
    {"fieldId": "1181057741029227456", "value": "2026-07-30 市内交通 - 滴滴出行", "fieldName": "报销事由"},
    {"fieldId": "1181057741029227470", "value": "1298294241967177729", "fieldName": "相关流程"}
  ],
  "detail_rows": [
    {
      "dataIndex": 1,
      "subFormId": "1181057741029227992",
      "invoiceId": "1295366637717012482",
      "fields": [
        {"fieldId": "1181057741029227467", "value": "2026-07-30", "fieldName": "费用日期"},
        {"fieldId": "1181057741029227459", "value": "108.2", "fieldName": "实报金额"},
        {"fieldId": "1181057741029227463", "value": "100502270000000006", "fieldName": "费用类型（科目）"},
        {"fieldId": "1181057741029227464", "value": "交通运输服务", "fieldName": "费用说明"},
        {"fieldId": "1181057741029227465", "value": "1", "fieldName": "附件数"},
        {"fieldId": "1181057741029227468", "value": "1295366637717012482", "fieldName": "相关发票"},
        {"fieldId": "1181057741029227449", "value": "100504500000311504", "fieldName": "相关客户"}
      ]
    }
  ],
  "need_user_confirm": [],
  "unable_to_fill": [
    {"fieldId": "1181057741029227450", "fieldName": "相关项目", "reason": "事前申请中无相关项目信息"}
  ]
}
```

### Step 5: 调用 CLI 创建报销单（prepare → 用户确认 → apply）

**第一步：prepare（将 Step 4 的 JSON 写入文件后传入）**

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.flow.create.prepare --input .\reim-create.json
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.flow.create.prepare --input ./reim-create.json
```

> prepare 返回 `continuation` token 和 `preview` 摘要，展示给用户确认。

**第二步：用户确认后，调用 apply**

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.flow.create.apply --input .\reim-create-apply.json
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.flow.create.apply --input ./reim-create-apply.json
```

> apply 的 JSON 需包含与 prepare 一致的顶层报销单字段、`continuation`（prepare 返回的 token）、`confirm: true`。

**返回：**

```json
{
  "code": 200,
  "msg": "接口返回成功",
  "status": true,
  "data": {
    "requestId": "1300266422434136064"
  }
}
```

**AI 展示给用户：**

```markdown
✅ 报销单创建成功！

---

**报销标题**：交通费报销-后端开发111-2026-08-04（共1笔）
**报销事由**：2026-07-30 市内交通 - 滴滴出行
**汇总金额**：¥108.20
**查看链接**：[点击查看报销单](viewUrl)

| # | 发票号码 | 发票金额 | 费用类型 | 发生地点 | 关联凭证 |
|---|----------|----------|----------|----------|----------|
| 1 | 36901189 | ¥108.20 | 市内交通 | 仁济医院南院→浦江瑞和城 | ❌ 无凭证 |

---

⚠️ 以下字段无法自动填写，请手动补充：
- **相关项目**：事前申请中无相关项目信息
```

---

## 示例2：多张发票 + 有事前申请（要点说明）

> 与示例1 流程一致，此处仅说明多发票场景的差异点。

**场景**：2 张发票（交通+住宿）均匹配到同一条出差事前申请。

**出差拦截**：`workFlowName` 含「差旅」或事前申请名称含「出差」→ **必须先提醒用户填写相关客户**。

```markdown
当前为出差报销，必须填写相关客户。请提供本次出差对应的具体客户名称，否则无法继续报销。
```

用户给出客户名称（如「XX科技」）→ `invoice.reim.field.search` 搜索到唯一 ID → 填入主表和明细「相关客户」→ 才允许调用 `invoice.reim.flow.create.prepare/apply`。
用户不提供 → **不允许报销，不创建报销单**。

**填单 JSON 关键点**：

```json
{
  "work_flow_id": "来自 invoice.reim.workflow.resolve",
  "request_name": "北京出差报销-张三-2026-08-04（共2笔）",
  "main_fields": [
    {"fieldId": "...", "value": "事前申请的creatorId", "fieldName": "申请人"},
    {"fieldId": "...", "value": "事前申请的requestid", "fieldName": "相关流程"}
  ],
  "detail_rows": [
    {
      "dataIndex": 1, "subFormId": "...", "invoiceId": "INV001",
      "fields": [
        {"fieldId": "...", "value": "INV001", "fieldName": "相关发票（EinvoiceComponent+single=false）"},
        {"fieldId": "...", "value": "76.80", "fieldName": "实报金额"}
      ]
    },
    {
      "dataIndex": 2, "subFormId": "...", "invoiceId": "INV002",
      "fields": [
        {"fieldId": "...", "value": "INV002", "fieldName": "相关发票（EinvoiceComponent+single=false）"},
        {"fieldId": "...", "value": "480.00", "fieldName": "实报金额"}
      ]
    }
  ]
}
```

**要点**：
- `dataIndex` 从 1 递增，两行 `subFormId` 相同
- 两行都绑定同一个事前申请 requestid
- 每行 `invoiceId` 必须同时写入 `fields` 中 `EinvoiceComponent`+`single=false` 的字段

---

## 示例3：无事前申请（要点说明）

**场景**：无事前申请，`invoice.reim.workflow.resolve` 传空 requestIds `[]`，返回候选工作流列表。

**差异点**：
- 候选只有1个 → 直接使用；多个 → 自动匹配最相关的
- `相关流程`字段留空
- 其他流程与示例1 一致

---

## 示例4：模糊搜索返回多个候选

> **注意：非出差流程的相关客户固定填 `"100504500000311504"`（泛微上海）。出差/差旅流程必须先让用户提供具体客户，未提供则不允许报销。以下以"相关项目"字段为例说明多候选处理。**

当搜索"相关项目"字段返回多个结果时：

**搜索命令：**

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.field.search --input-json '{"keywords":"智慧园区","fieldId":"1181057741029227450","workflowId":"1181057526276915214"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.field.search --input-json '{"keywords":"智慧园区","fieldId":"1181057741029227450","workflowId":"1181057526276915214"}'
```

**返回：**

```json
{
  "code": 200,
  "data": [
    {"name": "智慧园区一期", "id": "P001", "value": "P001"},
    {"name": "智慧园区二期", "id": "P002", "value": "P002"},
    {"name": "智慧园区运维", "id": "P003", "value": "P003"}
  ]
}
```

**处理方式**：该字段不放入 main_fields/detail_rows 的 fields 中，而是放入 `need_user_confirm`：

```json
{
  "need_user_confirm": [
    {
      "fieldId": "1181057741029227450",
      "fieldName": "相关项目",
      "dataIndex": 1,
      "reason": "模糊搜索返回多个候选",
      "candidates": [
        {"id": "P001", "name": "智慧园区一期"},
        {"id": "P002", "name": "智慧园区二期"},
        {"id": "P003", "name": "智慧园区运维"}
      ]
    }
  ]
}
```

用户选择后，将选中的 `id` 作为 `value` 补充到对应的 fields 中。

---

## 示例5：多候选报销单工作流自动匹配

无事前申请，`invoice.reim.workflow.resolve` 返回 3 个候选工作流。

**自动匹配过程**（已有发票 expenseType="市内交通"）：
1. "报销流程666【活动版本V1】" — 无关键词命中
2. "差旅费用报销" — "差旅"与交通类费用强相关 → **命中**
3. "日常费用报销" — "日常"弱相关

→ 自动选择 `workFlowId = "1250064959163990031"`（差旅费用报销），继续后续流程。

---

## 示例6：创建后更新报销单（Step 6 update）

假设 Step 5 `invoice.reim.flow.create.apply` 成功，返回 `requestId = "1250065066476052001"`。

AI 已向用户展示可点击链接，使用 CLI 返回的 `viewUrl`。

### 场景A：用户确认 need_user_confirm 中的字段

Step 5 创建时，"相关项目"字段有多个候选，放入了 `need_user_confirm`：

```json
{
  "need_user_confirm": [
    {
      "fieldId": "1181057741029227450",
      "fieldName": "相关项目",
      "dataIndex": 1,
      "reason": "模糊搜索返回多个候选",
      "candidates": [
        {"id": "P001", "name": "智慧园区一期"},
        {"id": "P002", "name": "智慧园区二期"}
      ]
    }
  ]
}
```

用户选择了"智慧园区一期"（id=P001），调用 `invoice.reim.flow.update.prepare` → 用户确认 → `invoice.reim.flow.update.apply` 补充：

> 将以下 JSON 写入 `reim-update.json`，然后执行 `weaver-work-cli --profile eteams --json invoice run invoice.reim.flow.update.prepare --input ./reim-update.json`，用户确认后再执行 `.apply`（传入顶层更新字段 + continuation + confirm:true）。

```json
{
  "requestId": 1300266422434136064,
  "mainFormId": "1181057741029226975",
  "detail_rows": [
    {
      "subFormId": "1181057741029227992",
      "dataIndex": 1,
      "fields": [
        {"fieldId": "1181057741029227450", "fieldName": "相关项目", "value": "P001"}
      ]
    }
  ]
}
```

### 场景B：用户要求修改金额 + 删除第2行明细

用户说"第1行金额改成 120 元，第2行明细删掉"：

```json
{
  "requestId": 1300266422434136064,
  "mainFormId": "1181057741029226975",
  "deleteDetailRows": [
    {"subFormId": "1181057741029227992", "dataIndex": 2}
  ],
  "detail_rows": [
    {
      "subFormId": "1181057741029227992",
      "dataIndex": 1,
      "fields": [
        {"fieldId": "1181057741029227459", "fieldName": "实报金额", "value": "120.00"}
      ]
    }
  ]
}
```

### 场景C：用户补充 unable_to_fill 中的主表字段

Step 5 创建时，"报销事由"无法自动推断：

```json
{"unable_to_fill": [{"fieldId": "1181057741029227456", "fieldName": "报销事由", "reason": "无法推断报销事由"}]}
```

用户提供了报销事由"7月份上海出差交通费"：

```json
{
  "requestId": 1300266422434136064,
  "mainFormId": "1181057741029226975",
  "main_fields": [
    {"fieldId": "1181057741029227456", "fieldName": "报销事由", "value": "7月份上海出差交通费"}
  ]
}
```

### 场景D：删除某明细表全部行后重新填写

```json
{
  "requestId": 1300266422434136064,
  "mainFormId": "1181057741029226975",
  "deleteDetailRows": [
    {"subFormId": "1181057741029227992", "dataIndex": -1}
  ],
  "detail_rows": [
    {
      "subFormId": "1181057741029227992",
      "dataIndex": 1,
      "fields": [
        {"fieldId": "1181057741029227467", "fieldName": "费用日期", "value": "2026-07-30"},
        {"fieldId": "1181057741029227459", "fieldName": "实报金额", "value": "108.20"},
        {"fieldId": "1181057741029227468", "fieldName": "相关发票", "value": "1295366637717012482"}
      ]
    }
  ]
}
```

### 返回结果

```json
{
  "code": 200,
  "status": true,
  "msg": "更新成功",
  "data": {
    "requestId": "1300266422434136064",
    "deleteDetailSuccess": true,
    "updateFormSuccess": true
  }
}
```

---

## 示例7-10：多轮对话与组合条件（精简）

> 以下示例说明多轮对话和上下文复用的处理逻辑。

### 示例7：先查发票再报销

| 轮次 | 用户 | AI 操作 |
|------|------|---------|
| 1 | "查下我最近的发票" | 内联计算最近一周时间戳 → 调用 `invoice.list`，无结果则扩大到一个月 → 告知用户查询范围，展示发票列表，**不进入报销流程** |
| 2 | "帮我报销" | 上下文已有发票 → 跳过 1A，展示发票汇总（Step 1C）→ 用户确认 → 用发票日期筛选事前申请 → Step 2 → 2.5 → 3 → 4 → 5 |

### 示例8：查事前申请 → 查发票 → 报销

| 轮次 | 用户 | AI 操作 |
|------|------|---------|
| 1 | "查下我的事前申请" | 调用 `invoice.reim.requests.list`，展示列表 |
| 2 | "查下对应的发票" | 复用事前申请日期，`date_begin` = 最早 createTime 的秒级时间戳，调用 `invoice.list` 展示 |
| 3 | "报销吧" | 上下文已有两组数据 → 跳过 1A/1B，直接 Step 2 → 2.5 → 3 → 4 → 5 |

### 示例9：查询后选部分报销

| 轮次 | 用户 | AI 操作 |
|------|------|---------|
| 1 | "查下我的发票" | 查到 5 张发票并展示 |
| 2 | "只报第1张和第3张" | 从上下文取第 1、3 张发票 → 用其日期筛选事前申请 → Step 1B → 2 → ... → 5 |

### 示例10：组合条件报销

用户说："报销上个月滴滴和住宿的发票"

AI 操作：
1. 内联计算 2026-07-01 ~ 2026-07-31 的秒级时间戳，并设置 `content="滴滴"` 组装请求参数
2. 调用 `invoice.list` 查询（CLI 支持服务端筛选，减少返回数据量）
3. 展示发票汇总（Step 1C），用户确认后走 Step 1B → 2 → 2.5 → 3 → 4 → 5

### 示例11：默认查询 fallback（一周无结果，自动扩到一个月）

用户说："帮我报销"

AI 操作：
1. 内联计算最近一周时间戳参数
2. 调用 `invoice.list` → 返回空（无结果）
3. 自动内联计算最近一个月时间戳参数
4. 再次调用 `invoice.list` → 返回 3 张发票
5. 展示 Step 1C：

```markdown
最近一周（2026-08-10 ~ 2026-08-17）未找到发票，已自动扩大到最近一个月（2026-07-18 ~ 2026-08-17），共找到 3 张未报销发票，汇总金额 ¥1,288.20：

| # | 发票类型 | 开票日期 | 发票号码 | 金额 | 销方名称 | 费用类型 |
|---|----------|----------|----------|------|----------|----------|
| 1 | 增值税电子普通发票 | 2026-07-25 | 36901189 | ¥108.20 | 北京滴滴出行科技有限公司 | 市内交通 |
| 2 | 电子发票（普通发票） | 2026-07-22 | 26467088 | ¥800.00 | 如家酒店管理有限公司 | 住宿 |
| 3 | 电子发票（铁路电子客票） | 2026-07-20 | 88990001 | ¥380.00 | 铁路客运 | 市内交通 |

请确认是否使用以上发票进行报销？如需查询其他日期范围，请告诉我。
```

6. 用户确认后 → Step 1B → 2 → 2.5 → 3 → 4 → 5

---

## 关键检查清单

组装填单 JSON 前确认：

1. [ ] `work_flow_id` 已设置（来自 Step 2.5 `invoice.reim.workflow.resolve` 返回）
2. [ ] `mainFormId` 已设置（来自 Step 3 `invoice.reim.form.structure` 返回的 `mainFormId`）
3. [ ] `request_name` 按规则生成，不超过30字
3. [ ] 所有字段的 `fieldId` 来自 `invoice.reim.form.structure` 返回，不能自己编造
4. [ ] Select 类型字段使用 `optionValue`（不是 `value`），值为选项的 optionValue
5. [ ] 非 Select 类型使用 `value`
6. [ ] marked=true 的字段 `value` 是数据ID，不是名称文本
7. [ ] detail_rows 的 `dataIndex` 从 1 开始递增
8. [ ] 每行明细的 `invoiceId` 对应正确的发票
9. [ ] 每行明细的 `invoiceId` 同时赋值到 `fields` 中 `fieldType="EinvoiceComponent"` 且 `single=false` 的字段
10. [ ] 模糊搜索多候选的字段放入 `need_user_confirm`
11. [ ] 无法推断的字段放入 `unable_to_fill` 并说明原因
11.5. [ ] **出差/差旅流程：相关客户已由用户提供具体名称并搜索到 ID；未提供则不允许调用 `invoice.reim.flow.create.prepare/apply`**
12. [ ] 非出差流程：相关客户填固定值 `"100504500000311504"`

调用 `invoice.reim.flow.update.prepare/apply` 前确认：

12. [ ] `requestId` 来自 `invoice.reim.flow.create.apply` 的返回结果
13. [ ] `mainFormId` 来自 `invoice.reim.form.structure` 返回的 `mainFormId`
14. [ ] `deleteDetailRows` 推荐使用 `{subFormId, dataIndex}` 对象数组格式
14. [ ] `detail_rows` 中每行必须包含 `subFormId`（明细表ID）
15. [ ] `dataIndex` 是 1-based，`-1` 表示删除该明细表全部行
16. [ ] 只传需要更新的字段，无需传完整表单
17. [ ] `fieldName` 仅用于可读性，不影响逻辑
18. [ ] `value` 为空 / `unable_to_fill=true` / `need_search=true` 的字段会被跳过
