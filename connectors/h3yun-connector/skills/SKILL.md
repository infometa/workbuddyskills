---
name: h3yun-form-workflow
description: Use when a user needs to find or operate H3Yun applications, forms, business records, organization units, attachments, to-dos, or workflow approvals.
version: "1.0.0"
author: H3Yun
---

# 氚云表单与流程 Skill

使用本 Skill 操作当前登录用户有权限访问的氚云应用、表单、业务数据、附件、待办和审批。

## 使用原则

- 所有工具返回 `{ errorCode, errorMessage, data }`。仅当 `errorCode` 为 `0` 时使用 `data`；失败时向用户说明可读的 `errorMessage`。
- 用户只提供应用、表单、人员、部门或记录名称时，先检索并使用返回的编码或 ID；不要猜测 `appCode`、`schemaCode`、字段编码或业务数据 ID。
- 读写业务数据前，调用 `getBizObjectSchema` 确认字段编码、控件类型和子表结构；新增、更新、删除前，还应调用 `getBizObjectSchemaAcl` 确认表单和字段权限。
- 创建时 `submit: false` 保存草稿，`submit: true` 创建生效数据；流程表单会发起流程。
- **【执行前确认】** 所有写入或修改业务数据的工具——新增（`createBizObject` / `createBizObjects`）、更新（`updateBizObject`）、删除（`removeBizObject` / `removeBizObjects`）、审批（`batchApprove`）——在执行前必须完成两步：**① 向用户明确声明**即将执行的操作（含目标表单、记录 ID 或批量记录数、将写入/变更的关键字段值）；**② 等待用户明确回复「确认 / 同意」**后方可真正调用写入接口。未获确认前不得执行。删除与审批属不可逆操作，须逐条/逐项确认。
- 批量新增、删除、审批均可能部分成功。逐项检查成功和失败 ID，只重试失败项，避免重复写入。
- 所有人员、部门、关联记录均应使用 ID。附件或图片先用 `transferFile` 转存，再把返回的 `fileId` 写入对应字段。

## 推荐调用流程

| 用户意图 | 调用顺序 |
| --- | --- |
| 查找应用或表单 | `searchApps` / `listApps` → `searchFormNode` → `getBizObjectSchema` |
| 新增或更新记录 | `getBizObjectSchema` → `getBizObjectSchemaAcl` → 解析人员、部门或附件 → **向用户声明并等待确认** → 写入工具 |
| 删除记录 | `getBizObjectSchemaAcl`（确认删除权限）→ 取得待删记录 ID → **向用户声明并等待确认** → `removeBizObject` / `removeBizObjects` |
| 查询记录 | `getBizObjectSchema` → `queryBizObjectList`；已知记录 ID 时使用 `getBizObject` |
| 处理待办 | `getTodoList` → 用户明确确认审批动作和意见 → `batchApprove` |

## 可用工具

### listApps - 获取可访问应用

分页获取当前用户有权限访问的应用。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| pageIndex | number | 是 | 页码，从 1 开始 |
| pageSize | number | 是 | 每页数量 |

**返回值**：`data: { total: number, data: AppDetail[] }`。

**示例**：`{ "pageIndex": 1, "pageSize": 20 }`

### searchApps - 按名称搜索可访问应用

按应用名称关键字分页查询当前用户有权限访问的应用。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| pageIndex | number | 是 | 页码，从 0 开始 |
| pageSize | number | 是 | 每页数量 |
| keyword | string | 是 | 应用名称关键字 |

**返回值**：`data: { total: number, data: AppDetail[] }`。

**示例**：`{ "pageIndex": 0, "pageSize": 20, "keyword": "CRM" }`

### searchFormNode - 搜索表单

按名称关键字分页查询可访问表单；已知应用时传 `appCode` 缩小范围。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| pageIndex | number | 是 | 页码，从 0 开始 |
| pageSize | number | 是 | 每页数量 |
| keyword | string | 是 | 表单名称关键字 |
| appCode | string | 否 | 应用编码 |

**返回值**：`data: { total: number, data: FunctionNode[] }`。

**示例**：`{ "pageIndex": 0, "pageSize": 20, "keyword": "请假", "appCode": "APP_DEMO" }`

### getBizObjectSchema - 获取表单定义

获取表单字段及子表定义。业务数据读写前必须调用，以返回的字段编码作为 `bizObject` 的键。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |

**返回值**：`data: BizObjectSchema`。

**示例**：`{ "schemaCode": "D0000001" }`

### getBizObjectSchemaAcl - 获取表单权限

获取当前用户的表单新增、编辑、删除权限和字段级权限。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |

**返回值**：`data: SchemaPermissionResult`。

**示例**：`{ "schemaCode": "D0000001" }`

### createBizObject - 新增单条业务数据

创建一条记录；流程表单且 `submit: true` 时会发起流程。

> ⚠️ **执行前必须确认**：调用前须向用户声明将写入的字段与值（`bizObject`），并明确请求「确认」后再执行。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObject | WriteBizObject | 是 | 字段编码到字段值的对象 |
| submit | boolean | 是 | `false` 创建草稿；`true` 创建生效数据或发起流程 |

**返回值**：`data: { bizObjectId: string }`。

**示例**：

```json
{
  "schemaCode": "D0000001",
  "bizObject": {
    "F0000002": "年假申请",
    "F0000003": "2",
    "F0000010": ["user_001"]
  },
  "submit": true
}
```

### createBizObjects - 批量新增业务数据

批量创建记录。检查返回的失败项；不要将部分成功表述为全部成功。

> ⚠️ **执行前必须确认**：调用前须向用户声明批量条数及每条关键字段值，并明确请求「确认」后再执行。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectArray | WriteBizObject[] | 是 | 待创建的数据列表 |

**返回值**：`data: { successBizObjectIds: string[], failedBizObjectIds: string[] }`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectArray": [{ "F0000002": "记录一" }] }`

### removeBizObject - 删除单条业务数据

删除指定业务数据。删除属不可逆操作。

> ⚠️ **执行前必须确认**：调用前须向用户声明目标记录 ID（`bizObjectId`）与所属表单，并明确请求「确认」后再执行；未获确认不得删除。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectId | string | 是 | 业务数据 ID |

**返回值**：`data: {}`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectId": "bo_001" }`

### removeBizObjects - 批量删除业务数据

批量删除记录，属不可逆操作。调用前确认完整 ID 列表，并检查成功与失败项。

> ⚠️ **执行前必须确认**：调用前须向用户声明全部待删 ID 列表与所属表单，并明确请求「确认」后再执行。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectIds | string[] | 是 | 待删除记录 ID 列表 |

**返回值**：`data: { successBizObjectIds: string[], failedBizObjectIds: string[] }`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectIds": ["bo_001", "bo_002"] }`

### updateBizObject - 更新单条业务数据

更新指定记录。只传要更新的字段；字段值遵循 `WriteBizObject` 规则。

> ⚠️ **执行前必须确认**：调用前须向用户声明目标记录 ID（`bizObjectId`）与将变更字段，并明确请求「确认」后再执行。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectId | string | 是 | 业务数据 ID |
| bizObject | WriteBizObject | 是 | 待更新字段对象 |

**返回值**：`data: {}`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectId": "bo_001", "bizObject": { "F0000003": "3" } }`

### getBizObject - 查询单条业务数据

根据表单编码和业务数据 ID 查询一条记录。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectId | string | 是 | 业务数据 ID |

**返回值**：`data: { schemaCode: string, valueTable: SingleQueryBizObject }`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectId": "bo_001" }`

### queryBizObjectList - 筛选业务数据

使用 SQL 查询单表数据。不支持子表字段；SQL 表名必须为 `i_${schemaCode}`，并且必须带 `LIMIT`。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| sql | string | 是 | 单表查询 SQL |

**返回值**：`data: BatchQueryBizObject[]`。

**示例**：

```json
{
  "schemaCode": "D0000001",
  "sql": "SELECT * FROM i_D0000001 LIMIT 20"
}
```

### getBizObjectNamesByIds - 按 ID 获取业务数据名称

批量解析业务数据 ID 为名称。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectIds | string[] | 是 | 业务数据 ID 列表 |

**返回值**：`data: Array<{ name: string, id: string }>`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectIds": ["bo_001", "bo_002"] }`

### getOrgNamesByIds - 按 ID 获取人员或部门名称

批量解析人员或部门 ID。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| ids | string[] | 是 | 人员或部门 ID 列表 |

**返回值**：`data: Array<{ name: string, id: string, type: "user" | "dept" }>`。

**示例**：`{ "ids": ["user_001", "dept_001"] }`

### getBizObjectIdsByNames - 按名称获取业务数据 ID

在指定表单内按名称查找记录。名称可能不唯一，返回多个候选时请用户确认。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| names | string[] | 是 | 业务数据名称列表 |

**返回值**：`data: Array<{ name: string, bizObjectId: string }>`。

**示例**：`{ "schemaCode": "D0000001", "names": ["张三"] }`

### getOrgIdByName - 按名称获取人员或部门 ID

按名称查找一个人员或部门。存在同名结果或用户指代不明确时，请求用户确认，不要自行选择。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| name | string | 是 | 人员或部门名称 |
| type | string | 是 | `user` 表示人员；`dept` 表示部门 |

**返回值**：`data: { orgId: string }`。

**示例**：`{ "name": "人力资源部", "type": "dept" }`

### transferFile - 转存附件

将可访问 URL 的文件转存到氚云，返回可写入附件或图片字段的 `fileId`。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| fileUrl | string | 是 | 待转存文件的 URL |

**返回值**：`data: { fileId: string }`。

**示例**：`{ "fileUrl": "https://example.com/files/contract.pdf" }`

### getTodoList - 获取用户待办

分页获取当前用户的待办工作项。处理审批前必须调用，以确认工作项及其状态。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| pageIndex | number | 是 | 页码，从 0 开始 |
| pageSize | number | 是 | 每页数量 |

**返回值**：`data: WorkItem[]`。

**示例**：`{ "pageIndex": 0, "pageSize": 20 }`

### getTodosCount - 获取用户待办数量

仅需要待办数量时调用。

**参数**：无。

**返回值**：`data: number`。

**示例**：`{}`

### batchApprove - 批量审批业务数据

对待办集合执行同意或不同意操作；单次最多 10 条。审批属不可逆操作。

> ⚠️ **执行前必须确认**：调用前须向用户声明每条待审批工作项、动作（`Submit` / `Reject`）与意见，并明确请求「确认」后再执行。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| workItemIds | string[] | 是 | 工作项 ID 列表，最多 10 项 |
| comment | string | 是 | 审批意见 |
| action | string | 是 | `Submit`（同意）或 `Reject`（不同意） |

**返回值**：`data: { successWorkItemIds: string[], failedWorkItemIds: string[] }`。

**示例**：

```json
{
  "workItemIds": ["wi_001", "wi_002"],
  "comment": "同意",
  "action": "Submit"
}
```

## 关键类型与写入规则

### BizObjectSchema 与权限

- `BizObjectSchema`：`{ schemaCode, displayName, description, fields }`；字段定义提供字段编码、显示名、描述和控件类型。
- `SchemaAcl`：`addable`、`editable`、`removable` 分别表示是否可新增、编辑、删除。
- `SchemaPermissionResult.fieldPermissions` 给出当前权限上下文下字段的 `visible`、`editable` 与 `required`。

### WriteBizObject

`WriteBizObject` 是 `{ [fieldCode: string]: value }`。字段键以 `getBizObjectSchema` 返回的字段编码为准。

| 控件 | 写入类型 | 规则 |
| --- | --- | --- |
| 文本、数字、日期、下拉、单选、单关联 | string | 数字与日期同样传字符串 |
| 复选框 | string | 多值用英文分号拼接，如 `"A;B"` |
| 是/否 | boolean | 使用 `true` / `false` |
| 人员、部门、拥有者、所属部门 | string / string[] | 单选传单个 ID，多选传 ID 数组 |
| 关联表单多选 | string[] | 传关联业务数据 ID 数组 |
| 地址、定位 | string | 分别传对应对象序列化后的 JSON 字符串 |
| 子表 | WriteBizObject[] | 数组的每个元素是一行子表数据 |

### 查询结果

- `getBizObject` 返回 `SingleQueryBizObject`：人员、部门、创建人、拥有者及所属部门的直接字段值可为 `{ id, name, type }`，多选字段为该对象数组。结果也可能带 `${fieldCode}Object` 扩展对象，含 `ObjectId`、`Name`、`EntryId`；优先使用直接字段值，兼容读取扩展字段。
- `queryBizObjectList` 返回 `BatchQueryBizObject[]`：不支持子表字段，也不返回组织机构扩展字段。
- `WorkItem` 包含 `workItemId`、`schemaCode`、`bizObjectId`、`activityName`、`summary`、`taskState`、`originatorName` 与 `fastApprove` 等信息。

## 常见错误及处理

| 错误码 | 处理建议 |
| --- | --- |
| 100100 | 检查网络后重试。 |
| 100200 | 请求过于频繁，稍后重试。 |
| 100300-100307 | 检查参数、分页、业务数据结构、筛选或排序格式。 |
| 100400、100401 | 提示用户重新登录或刷新登录凭证。 |
| 100402 | 告知用户无权执行此操作。 |
| 100500-100502 | 服务或上游暂不可用，稍后重试。 |
| 200104、200204、200206、200302 | 应用、表单、业务数据或待办不存在；重新确认标识。 |
| 200105、200205、200303 | 用户无相应的访问或处理权限。 |
| 200201、200207、200208 | 补全必填字段，并按表单定义校验字段值。 |
| 200202、200203 | 当前记录不可删除，或字段不允许修改。 |
| 200210、200211 | 修正业务数据筛选或排序条件。 |
| 200304、200305、200306 | 待办不可处理、动作不合法或部分审批失败；重新查询待办并逐项处理。 |
| 200401 | 未找到人员或部门；重新确认名称和类型。 |
| 200501 | 未找到匹配地址信息。 |
| 200601、200602 | 文件 URL 不可访问或转存失败；确认 URL 后重试。 |
