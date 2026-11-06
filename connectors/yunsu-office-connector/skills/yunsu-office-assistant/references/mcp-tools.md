# MCP 工具说明

本文档详细说明企业办公助手依赖的四个 MCP 工具的参数和返回值。

## 工具列表

| 工具名称 | 功能 | 用途 |
|---------|------|------|
| `get_current_identity` | 获取当前登录身份 | 确认"我是谁" |
| `fs_find_todo` | 查询待办消息 | 获取待办事项和通知提醒 |
| `fs_process_list` | 查询流程列表 | 获取流程审批任务列表 |
| `fs_process_detail` | 查询流程详情 | 获取单个流程的完整信息 |

## 重要：工具调用方式

本技能依赖的工具是**延迟加载工具**，必须先查询 schema 再调用：

**步骤 1：查询工具 schema**

```
使用 tools/list 方法查询工具列表，获取工具的 inputSchema
```

**步骤 2：调用工具**

```
使用 tools/call 方法调用工具，传入符合 schema 的参数
```

## 1. get_current_identity（获取当前登录身份）

### 功能描述

获取当前登录用户的身份信息，用于确认"我是谁"。

### 参数说明

无参数。

### 返回值说明

返回当前用户的身份信息：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `userId` | string | 用户唯一标识 |
| `userName` | string | 用户姓名 |
| `dept` | string | 部门名称 |

### 使用场景

- 确认当前登录用户身份
- 验证认证是否成功

## 2. fs_find_todo（查询待办消息）

### 功能描述

获取当前用户在企业办公平台中的待办消息和通知提醒，支持按状态、来源系统、来源模块过滤，以及分页查询。

### 参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `status` | integer | 否 | 消息状态：1-待办；2-已办；3-待阅；4-已阅。不传则查询所有状态 |
| `appName` | string | 否 | 来源系统标识，用于过滤特定系统的消息 |
| `moduleName` | string | 否 | 来源模块标识，用于进一步细化过滤 |
| `offset` | integer | 否 | 分页偏移量，默认0 |
| `pageSize` | integer | 否 | 每页条数，默认100，最大1000 |

### 返回值说明

返回消息列表，每条消息包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `todoId` | string | 消息唯一标识 |
| `subject` | string | 消息标题 |
| `link` | string | 处理链接 |
| `status` | integer | 消息状态（1-待办，2-已办，3-待阅，4-已阅） |
| `todoLevel` | integer | 紧急程度（1-紧急，2-急，3-一般） |
| `createTime` | long | 接收时间（毫秒时间戳） |
| `finishTime` | long | 处理完成时间（毫秒时间戳，仅已办/已阅有值） |
| `ownerName` | string | 接收人姓名 |
| `creatorName` | string | 发起人姓名 |

### 分页说明

- 默认 `pageSize=100`，如果返回的 `totalSize` 大于实际返回条数，需要翻页查询
- 翻页方式：增加 `offset` 值（如 `offset=100`、`offset=200`）

### 使用场景

- **每日工作概览**：查询所有待办事项（`status=1`）
- **紧急任务筛选**：查询待办事项后按 `todoLevel` 排序
- **历史追溯**：查询已办事项（`status=2`）
- **通知阅读**：查询待阅通知（`status=3`）
- **跨系统过滤**：只查看特定系统的待办（`appName="hr-system"`）

## 3. fs_process_list（查询流程列表）

### 功能描述

查询当前用户在流程引擎中的审批任务列表，支持多种查询类型（我的待办/已办/发起/跟踪等）、标题关键词模糊查询，以及分页查询。

### 参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `queryType` | string | 否 | 查询类型，默认 myApproving。可选值：myApproving（我的待办）、myApproved（我的已办）、myCreated（我发起的）、myFollowed（流程跟踪）、myReading（流程送阅）、myDraft（我的草稿）、flow（流程库） |
| `keyword` | string | 否 | 标题关键词，用于模糊查询流程标题 |
| `offset` | integer | 否 | 分页偏移量，默认0 |
| `pageSize` | integer | 否 | 每页条数，默认20 |

### 返回值说明

返回流程列表和分页信息：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `content` | array | 流程列表，每条流程包含以下字段 |
| `totalSize` | integer | 总条数 |
| `offset` | integer | 当前分页偏移 |
| `pageSize` | integer | 每页条数 |

**content 数组中每条流程的字段**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `fdId` | string | 流程实例ID（用于查询流程详情） |
| `fdSubject` | string | 流程标题 |
| `fdNumber` | string | 流程编号 |
| `fdCreateTime` | long | 创建时间（毫秒时间戳） |
| `fdCreator` | string | 创建人姓名 |
| `fdCreatorDept` | string | 创建人部门 |
| `fdProcessStatus` | string | 流程状态（20-待审，30-结束等） |
| `fdTemplate` | string | 流程模板名称 |
| `currentHandlerNames` | string | 当前处理人姓名 |
| `currentNodeNames` | string | 当前节点名称 |

### 分页说明

- 默认 `pageSize=20`，如果返回的 `totalSize` 大于实际返回条数，需要翻页查询
- 翻页方式：增加 `offset` 值（如 `offset=20`、`offset=40`）

### 使用场景

- **待办审批**：查询我的待办流程（`queryType=myApproving`）
- **历史追溯**：查询我的已办流程（`queryType=myApproved`）
- **发起流程跟踪**：查询我发起的流程（`queryType=myCreated`）
- **关键词搜索**：查询标题包含特定关键词的流程（`keyword="报销"`）
- **催办查询**：查询当前处理人和当前节点（提取 `currentHandlerNames` 和 `currentNodeNames`）

## 4. fs_process_detail（查询流程详情）

### 功能描述

根据流程实例ID查询单个流程的完整详细信息，包括表单数据、审批记录、流程模板等。

### 参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `fdId` | string | 是 | 流程实例ID，从 fs_process_list 返回的 fdId 字段获取 |

### 返回值说明

返回流程详细信息：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `fdId` | string | 流程实例ID |
| `fdSubject` | string | 流程标题 |
| `fdNumber` | string | 流程编号 |
| `fdCreateTime` | long | 创建时间（毫秒时间戳） |
| `fdLastModifiedTime` | long | 最后修改时间（毫秒时间戳） |
| `fdCreator` | object | 创建人信息（fdId、fdName） |
| `fdOwner` | object | 当前归属人信息（fdId、fdName） |
| `fdCreatorDept` | object | 创建人部门信息（fdId、fdName） |
| `fdProcessStatus` | string | 流程状态（00-废弃，10-草稿，11-驳回，12-撤回，20-待审，21-挂起，29-异常，30-结束） |
| `fdTemplate` | object | 流程模板信息（fdId、fdName、fdCode、fdSimpleName 等） |
| `dynamicProps` | object | 表单自定义字段（根据流程模板不同而变化） |

### 使用场景

- **查看流程详情**：根据流程ID查看完整信息
- **表单数据查看**：查看流程的自定义字段（如采购申请的物料明细）
- **审批历史追溯**：查看流程的审批记录
- **流程模板了解**：了解流程使用的模板配置

## 注意事项

1. **时间戳格式**：所有时间字段均为毫秒时间戳，需要转换为可读格式（使用 `scripts/transform.py` 或 AI 手动转换）
2. **身份自动注入**：所有工具调用都会自动注入当前认证用户的身份信息，无需手动传入用户标识
3. **分页查询**：建议分页查询时使用默认的 `pageSize`，避免单次返回过多数据
4. **错误处理**：如果工具调用失败，返回错误信息给用户，不要编造数据
5. **无数据处理**：如果查询结果为空，明确告知用户"没有找到相关数据"，不要编造数据
