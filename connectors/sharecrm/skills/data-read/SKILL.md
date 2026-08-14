---
name: "data-read"
description: |
  CRM 数据只读操作的最终兜底执行技能（最低优先级），覆盖对象识别、对象/字段描述、关系查看与记录读取。
  自然语言 CRM 查询、语义解析与统计报表优先使用 semantic-interpreter，本技能仅在其不可用、或请求已是包含 apiName 的结构化读取、或已选能力明确要求回退时使用。
  不处理语义解释、统计聚合、报表分析、多跳关系推断及写操作。
  所有工具调用通过 template-mcp 连接器执行，每个工具需传入固定 apiName 参数标识真实执行操作。
apiName: "data_read_mcp"
---
# CRM data 基础只读操作

## 路由与使用原则

读取本技能不代表允许执行。在调用任何工具前，先完成以下检查：

1. 自然语言 CRM 数据查询默认由 semantic-interpreter 承担；若其在当前技能清单中，优先使用之，不得直接调用下方工具。
2. 只根据当前会话已提供的技能 name 和 description 判断，不逐个加载候选技能试探；存在其他明确覆盖本次请求的查询/分析能力时，改用该能力。
3. 仅当技能清单中无更匹配能力、或已选能力已尝试但明确无法完成、或请求已是包含 apiName 的结构化读取时，才执行下方工具。
4. 仅处理对象识别、对象描述、直接关系查看与记录读取；不执行或发现写操作和 SQL；语义解释、统计聚合、报表分析、多跳关系推断、原因分析均不属于本技能。
5. 使用最短有效调用链，当前结果已经能够回答用户时立即停止。

## 使用原则

1. 仅处理对象识别、对象描述、直接关系查看和记录读取；不执行或发现写操作和 SQL。
2. 只做单步或短链路基础读取；需要多跳拼装、跨记录证据核对或解释性结论时，不属于本技能。
3. 使用最短有效调用链，当前结果已经能够回答用户时立即停止。

## 复用已有上下文

按以下顺序确定对象：

1. 用户当前请求明确提供 `objectApiName` 时，直接使用。
2. 用户只提供业务对象名称时，只有当前对话、已有工具结果或运行时上下文中存在该名称到 `objectApiName` 的精确映射，才直接复用；否则将该名称作为 `identify-with-describe` 的线索，且最多识别一次。
3. 未提供对象信息时，使用用户原始问题调用一次 `data_describe_identify-with-describe`。

用户当前输入优先于已有上下文。存在多个候选或对象指代无法唯一确定时，向用户澄清，不猜测。

已知 `objectApiName` 时，不再调用 `data_describe_identify-with-describe`。只有后续查询需要字段信息且现有描述不足时，才调用 `data_describe_get`。已有描述包含所需字段时，不重复获取描述。

## 选择最短工具

| 查询目标 | MCP 工具 | 固定 apiName |
|---|---|---|
| 识别业务对象 | `data_describe_identify-with-describe` | `IdentifyObjectWithDescribe` |
| 获取对象描述 | `data_describe_get` | `GetObjectDescribe` |
| 查看对象关联范围 | `data_describe_list-related` | `ListRelatedObjects` |
| 查询两个对象的关系路径 | `data_describe_query-relation-paths` | `QueryRelationPaths` |
| 按名称查询候选记录 | `data_record_query-by-name` | `QueryRecordByName` |
| 按名称查询记录 ID | `data_record_query-id-by-name` | `QueryRecordIdByName` |
| 按对象和 ID 获取详情 | `data_record_get-by-id` | `GetRecordById` |
| 按字段条件查询记录 | `data_record_query-by-fields` | `QueryRecordsByFields` |

前一个工具的结果已经能够回答用户时，不调用后续工具。

> **重要**：每个 MCP 工具调用时必须传入 `apiName` 参数，值为上表中对应的固定标识，否则工具无法正确执行。

## 对象描述与关系

对象无法从已有上下文确定时，使用用户原始问题识别对象。对象已知但缺少下一步所需字段信息时，获取简版描述。

### 识别业务对象 — `data_describe_identify-with-describe`

根据用户输入的对象术语、简称或业务短语识别对应业务对象；结果唯一收敛时同时返回简版描述。

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `apiName` | string | 是 | 固定值 `IdentifyObjectWithDescribe` |
| `query` | string | 否 | 待识别的对象术语、简称或短句，例如 `客户`、`联系人` |
| `include_simple_describe` | boolean | 否 | 是否补充简版对象描述，默认 `true` |
| `object_api_names` | string[] | 否 | 候选对象范围，用于减少歧义 |
| `include_few_shots` | boolean | 否 | 是否返回 few-shot 示例 |
| `few_shot_type` | string | 否 | few-shot 类型过滤 |

调用示例：

```json
{
  "apiName": "IdentifyObjectWithDescribe",
  "query": "<用户原始问题>",
  "include_simple_describe": true
}
```

返回 `resolution_status` 为 `RESOLVED` 时表示唯一识别；`AMBIGUOUS` 时需向用户澄清。

### 获取对象描述 — `data_describe_get`

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `apiName` | string | 是 | 固定值 `GetObjectDescribe` |
| `object_api_name` | string | 否 | 业务对象唯一标识，例如 `AccountObj` |
| `simple_describe` | boolean | 否 | 传 `true` 返回轻量 `field_list`，过滤禁用字段和选项 |
| `include_few_shots` | boolean | 否 | 是否返回 few-shot 示例 |
| `few_shot_type` | string | 否 | few-shot 类型过滤 |

调用示例：

```json
{
  "apiName": "GetObjectDescribe",
  "object_api_name": "<ObjectApiName>",
  "simple_describe": true
}
```

### 查看对象关联范围 — `data_describe_list-related`

返回指定对象可直接联查的关联对象边信息。

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `apiName` | string | 是 | 固定值 `ListRelatedObjects` |
| `objectApiName` | string | 否 | 当前已确认的主对象 apiName |

调用示例：

```json
{
  "apiName": "ListRelatedObjects",
  "objectApiName": "<ObjectApiName>"
}
```

### 查询关系路径 — `data_describe_query-relation-paths`

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `apiName` | string | 是 | 固定值 `QueryRelationPaths` |
| `source_object_api_name` | string | 是 | 起点对象 apiName |
| `target_object_api_name` | string | 是 | 目标对象 apiName |
| `question` | string | 否 | 用户原始问题，辅助判断关系链路 |

调用示例：

```json
{
  "apiName": "QueryRelationPaths",
  "source_object_api_name": "<SourceObjectApiName>",
  "target_object_api_name": "<TargetObjectApiName>",
  "question": "<用户原始问题>"
}
```

## 记录读取

按名称查询记录时，优先传入已经确认的对象范围。对象范围未知时，先识别对象。

### 按名称查询记录 — `data_record_query-by-name`

将实体名称归一到具体业务记录，按名称模糊匹配返回候选记录列表。

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `apiName` | string | 是 | 固定值 `QueryRecordByName` |
| `name` | string | 否 | 待归属的记录名称 |
| `object_api_names` | string[] | 否 | 候选对象范围 |

调用示例：

```json
{
  "apiName": "QueryRecordByName",
  "name": "<记录名称>",
  "object_api_names": ["<ObjectApiName>"]
}
```

### 按名称查询记录 ID — `data_record_query-id-by-name`

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `apiName` | string | 是 | 固定值 `QueryRecordIdByName` |
| `query` | string | 是 | 对象数据名称关键词 |
| `apiNames` | string[] | 否 | CRM 对象 apiName 列表 |

调用示例：

```json
{
  "apiName": "QueryRecordIdByName",
  "query": "<名称关键词>",
  "apiNames": ["<ObjectApiName>"]
}
```

### 按对象和 ID 获取详情 — `data_record_get-by-id`

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `apiName` | string | 是 | 固定值 `GetRecordById` |
| `object_api_name` | string | 是 | 对象唯一标识 |
| `id` | string | 是 | 目标记录的唯一 ID |

调用示例：

```json
{
  "apiName": "GetRecordById",
  "object_api_name": "<ObjectApiName>",
  "id": "<记录ID>"
}
```

`query-by-name` 返回的信息已经能够回答用户时，不再调用 `get-by-id`。只需要记录 ID 时，使用 `query-id-by-name`。

## 按字段条件查询

字段名称必须来自已有对象描述的 `field_list[].api_name`。只选择用户需要的字段，并设置较小且合理的 `limit`（建议默认 10）。

### 运算符适用范围

```text
text: eq/n/like/in
number/date/datetime: eq/n/gt/gte/lt/lte/between/in
boolean: eq/n
array: in
```

`n` 表示不等于。`in` 使用数组传入多个值，`between` 使用数组 `[起始值, 结束值]` 传入。多个字段条件默认使用 AND 连接。

### 按字段条件查询 — `data_record_query-by-fields`

参数说明：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `apiName` | string | 是 | 固定值 `QueryRecordsByFields` |
| `object_api_name` | string | 否 | 主对象 apiName |
| `select_fields` | string[] | 否 | 返回字段列表 |
| `search_template_query` | object | 否 | 结构化查询模板（见下方） |
| `need_count` | boolean | 否 | 是否返回总数 |

`search_template_query` 结构：

| 字段 | 类型 | 说明 |
|---|---|---|
| `filters` | array | 过滤条件列表 |
| `filters[].field_name` | string | 字段 apiName |
| `filters[].field_values` | string[] | 字段值数组（`in` 多值，`between` 双值） |
| `filters[].operator` | string | 运算符：eq/n/like/in/gt/gte/lt/lte/between |
| `filters[].connector` | string | 条件连接符：AND / OR |
| `filters[].value_type` | integer | 值类型标识 |
| `orders` | array | 排序条件列表 |
| `orders[].fieldName` | string | 排序字段 apiName |
| `orders[].isAsc` | boolean | `true` 升序，`false` 降序 |
| `limit` | integer | 返回条数限制 |

调用示例 — 按名称模糊查询客户：

```json
{
  "apiName": "QueryRecordsByFields",
  "object_api_name": "AccountObj",
  "select_fields": ["name", "owner"],
  "search_template_query": {
    "filters": [
      {
        "field_name": "name",
        "field_values": ["华为"],
        "operator": "like",
        "connector": "AND"
      }
    ],
    "limit": 10
  }
}
```

调用示例 — 多条件查询并排序：

```json
{
  "apiName": "QueryRecordsByFields",
  "object_api_name": "AccountObj",
  "select_fields": ["name", "owner", "created_at"],
  "search_template_query": {
    "filters": [
      {
        "field_name": "name",
        "field_values": ["华为"],
        "operator": "like",
        "connector": "AND"
      },
      {
        "field_name": "created_at",
        "field_values": ["2024-01-01", "2024-12-31"],
        "operator": "between",
        "connector": "AND"
      }
    ],
    "orders": [
      {
        "fieldName": "created_at",
        "isAsc": false
      }
    ],
    "limit": 10
  },
  "need_count": true
}
```

关联对象、人员和部门字段应先解析为可用 ID。枚举字段值必须来自对象描述中的合法选项。

## 错误处理

正文已经提供所需参数时，直接执行工具调用，不预先探查工具能力。

只有目标工具返回未知参数、不支持的格式或运行时版本不兼容错误时，才检查该工具的参数定义。不得枚举其他工具来试探能力。

查询成功但没有结果时，报告空结果并停止。不得放宽条件、更换对象、扩大时间范围或为了探索而重试。工具执行失败时，只针对明确错误修正参数，不得盲目重试。
