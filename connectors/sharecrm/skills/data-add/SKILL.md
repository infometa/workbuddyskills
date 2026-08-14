---
name: "data-add"
description: "自然语言创建、录入、登记、添加、保存、生成或写入 CRM 对象数据记录。用于新建客户、创建线索、录入联系人、登记商机、添加订单/报价/产品/产品组合/组合/等业务对象，或用户表达“帮我建一条/新增一条/写入一条/保存到系统/创建记录/录入数据”等意图。"
apiName: "data_add_mcp"
---
# data-add

把用户的自然语言变成一条可落库的 CRM 记录。整条链路是一个串行的解析过程：

```
准备新建表单 → 组装 object_data → 保存 → 返回结果
```

每一步都依赖上一步的真实返回值。这条 skill 的核心风险只有一个：**在信息还没确定时就往下猜**——猜错对象、猜错业务类型、给只读字段回填值、编造关联记录 ID。这些都会写出一条错误的脏数据，而且用户往往要事后才发现。所以下面每一步的约束，本质都是在回答同一个问题：*“我现在掌握的信息，足够让我安全地走下一步吗？”* 信息不足时，宁可停下来问用户，也不要编造。

## 工作流总览

| 步骤 | 目的 | 走下一步的前提 |
|---|---|---|
| 0 对象专属逻辑（命中即先读） | 优先处理专属逻辑 | 必要数据已准备充足 |
| 1 准备新建表单 | 一步完成识别对象、确定业务类型、获取新建表单 | 已拿到唯一 `object_api_name`、唯一 `record_type` 和 `form` |
| 2 组装 object_data | 构造提交数据 | 命中对象有专属引用文件时已读；关联字段已解析到唯一 ID |
| 3 保存 | 写入系统 | object_data 已组装完成 |
| 4 返回结果 | 回传创建结果 | — |

一个贯穿全程的原则：**用户中途改了任何会影响结果的信息（对象、业务类型、字段值、关联记录、明细），就从受影响的最早步骤重新走一遍，不要复用旧的表单元数据。**

## 步骤 0：对象专属逻辑（命中即先读）

有些对象有超出通用规则的特殊构造逻辑。组装前先按下表判断是否需要读引用文件：

| 目标对象 `apiName` | 必须先读的引用文件 |
|---|---|
| `NewOpportunityObj` | `{Current agent directory}/skill/{skillApiName}/references/NewOpportunityObj.md` |
| `QuoteObj` | `{Current agent directory}/skill/{skillApiName}/references/QuoteObj.md` |
| `SaleContractObj` | `{Current agent directory}/skill/{skillApiName}/references/SaleContractObj.md` |
| `SalesOrderObj` | `{Current agent directory}/skill/{skillApiName}/references/SalesOrderObj.md` |
| `ActiveRecordObj` | `{Current agent directory}/skill/{skillApiName}/references/ActiveRecordObj.md` |
| `ScheduleObj` | `{Current agent directory}/skill/{skillApiName}/references/ScheduleObj.md` |
| `BomCoreObj` | `{Current agent directory}/skill/{skillApiName}/references/BomCoreObj.md` |

命中时先读对应文件并应用其约束，再构造 `object_data`。引用文件里的特殊构造逻辑优先于通用规则；但可写字段、必填状态、枚举提交值仍以本次新建表单返回为准。

## 步骤 1：准备新建表单

**先做语义拆分。** 用户一句话里常同时含两类信息：①对象类型（要建哪类记录，如“客户 / 商机 / 联系人”），②记录本身的名称或字段值（如“大麦网”“王小二”）。对象识别阶段只使用对象类型词；记录名称和字段值留到步骤 2 处理。

| 用户输入 | 用于对象识别的对象名称 |
|---|---|
| 新建一个客户：大麦网 | `客户` |
| 录入联系人张三 | `联系人` |

如果一句话里识别不出明确的对象类型词，不要把记录名硬当对象名传进去，先向用户确认要建哪一类对象。

### 1.1 识别对象

对象 apiName 未知时，调用对象识别工具：

```json
{
  "apiName": "IdentifyObjectWithDescribe",
  "query": "<对象名称>",
  "include_simple_describe": false
}
```

处理规则：

- `resolution_status = RESOLVED` 且仅 1 个候选：采用该 `object_api_name`
- `resolution_status = AMBIGUOUS`：把 `object_candidates` 交给用户确认
- `resolution_status = NO_MATCH` 或无可用候选：请用户更换对象名称或确认对象是否存在

对象 apiName 已明确时，直接跳过对象识别。

### 1.2 确定业务类型

调用业务类型列表工具：

```json
{
  "apiName": "getRecordTypeList",
  "object_api_name": "<object_api_name>"
}
```

处理规则：

- 只有 1 个业务类型：直接采用其 `value`
- 有多个业务类型：把候选列给用户选
- 没有可用业务类型：停止并告知无法继续创建

### 1.3 获取新建表单

调用新建表单工具：

```json
{
  "apiName": "getCreateFormContext",
  "object_api_name": "<object_api_name>",
  "record_type_apiName": "<record_type>"
}
```

返回中的以下三部分是后续组装数据的唯一真相：

- `form_fields`
- `field_metadata`
- `initial_object_data`

**同一对象 + 同一业务类型可复用上一份表单，不要重复请求。** 如果本轮对话里刚刚已经为某个对象拉过同一 `record_type` 的表单，直接复用上一次返回的 `form`。

## 步骤 2：组装 object_data

以 `initial_object_data` 为初始值，写入步骤 1 已确定的 `record_type`，再合并从用户输入解析出的字段值。只认步骤 1 返回的这份表单，三条铁律：

1. **只读字段是雷区。** `form_fields` 中 `is_readonly=true` 的字段原样保留 `initial_object_data` 里的值，绝不写入用户值、默认补值、推断值或计算值。
2. **必填以 `is_required` 为准。** 必填字段缺用户输入又没有默认值时不要编造，先向用户补问。
3. **选项字段只认提交值。** `field_metadata` 里带 `options` 的是选项类字段，必须写其中的合法 value 而非展示名；映射不唯一时先确认。

### 2.1 关联对象字段（必须解析到唯一 ID）

关联记录的解析只在这一步做，前提是表单里确实存在这个关联字段。先在 `form_fields` / `field_metadata` 里确认该字段存在，并拿到它的真实 `field_name` 和关联对象 `apiName`。

当字段类型是 `object_reference`，或元数据表明该字段要关联已有记录时，必须先解析成唯一可提交的记录 ID 再写入。

解析路径：

- 用户直接给了符合字段要求的明确 ID：可直接用
- 用户给的是名称 / 编号 / 手机号 / 公司名 / 联系人名等文本：从该字段 `field_metadata` 中读取关联对象 apiName，再调用按名称查询记录 ID 工具

```json
{
  "apiName": "QueryRecordIdByName",
  "query": "<关键词>",
  "apiNames": ["<关联对象apiName>"]
}
```

需要查看候选详情再让用户判断时，再调用按名称查询候选记录工具：

```json
{
  "apiName": "QueryRecordByName",
  "name": "<关键词>",
  "object_api_names": ["<关联对象apiName>"]
}
```

处理规则：

- 查到 1 条：可用
- 查到多条：交给用户选择
- 查不到 / 无法判断：停下来，不要编造 ID 或默认选第一条

### 2.2 各字段类型的写法

| 字段类型 | 写法 | 示例 |
|---|---|---|
| `owner` | 数组 | `{"owner": ["1016"]}` |
| `date` | 日期字符串 `yyyy-MM-dd` | `"close_date": "2026-06-08"` |
| `date_time` | 日期时间字符串 `yyyy-MM-dd HH:mm:ss` | `"meeting_time": "2026-06-08 14:30:00"` |
| `select_one` | 元数据中的合法提交值 | `"sales_stage": "1"` |
| `select_many` | 数组，元素为合法提交值 | `"crm__c": ["Salesforce"]` |
| `percentile` | 提交值是百分号前的数值 | `"discount_rate": 90` |
| `object_reference` | 唯一命中或用户确认后的记录 ID 字符串 | `"account_id": "69e9a174..."` |
| `record_type` | 步骤 1 已确定的业务类型提交值 | `"record_type": "default__c"` |

## 步骤 3：保存数据

object_data 组装完成后，直接调用创建记录工具。格式校验、必填校验等都交给保存接口负责。

仅主对象：

```json
{
  "apiName": "CreateRecordsByData",
  "object_api_name": "<apiName>",
  "object_data": {
    "...": "..."
  }
}
```

带从对象明细：

```json
{
  "apiName": "CreateRecordsByData",
  "object_api_name": "<apiName>",
  "object_data": {
    "...": "..."
  },
  "details": {
    "<DetailObjectApiName>": [
      {
        "...": "..."
      }
    ]
  }
}
```

## 步骤 4：返回结果

调用创建工具后，先判断接口返回，只有记录确实创建成功时才作为成功返回。

- 需要二次确认：把系统要求确认的内容如实转达给用户，等用户确认后再重新提交
- 用户明确拒绝本次创建：立即终止整个操作
- 权限 / 禁止执行 / 当前对象不支持：立即终止，不重试
- 保存失败 / 报错：把失败原因如实告诉用户；仅当错误明确指出某个可修正字段问题时，修正后至多重试一次
